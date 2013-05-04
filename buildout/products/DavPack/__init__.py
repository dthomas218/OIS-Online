##############################################################################
#
# DavPack -- A set of patches for all things related to WebDAV
# Copyright (C) 2004-2007 Enfold Systems
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
# Some portions of this module are Copyright Zope Corporatioin and
# Contributors.
# The original copyright statement is reproduced below.
#
##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""
$Id: __init__.py 2341 2008-09-29 22:09:12Z sidnei $
"""

import sys
import marshal
import tempfile
import thread
import logging
import transaction
import webdav.Resource, webdav.Collection

from cgi import escape
from Acquisition import aq_base
from AccessControl import getSecurityManager
from ZODB.POSException import ConflictError

from webdav.WriteLockInterface import WriteLockInterface
from webdav import Lockable
from webdav.common import Locked, Conflict, PreconditionFailed
from webdav.common import absattr, isDavCollection
from webdav.common import urlfix, urlbase, urljoin, rfc1123_date
from webdav.davcmds import PropPatch, Lock, PropFind, DAVProps, safe_quote

# 3 levels of deprecation, woot!
try:
    from zope.contenttype import guess_content_type
except ImportError:
    try:
        from zope.app.content_types import guess_content_type
    except ImportError:
        from OFS.content_types import guess_content_type

from OFS import PropertySheets
from OFS.CopySupport import CopyError, eNotSupported
from ComputedAttribute import ComputedAttribute
from zExceptions import Unauthorized, Forbidden, NotFound
from zExceptions import BadRequest, MethodNotAllowed
from ZServer.HTTPResponse import ZServerHTTPResponse
from ZServer.Producers import file_part_producer
from ZPublisher.HTTPResponse import uncompressableMimeMajorTypes
from Products.DavPack.gzip_pipe_wrapper import GZipPipeWrapper

logger = logging.getLogger('DavPack')
log = logger.debug
_marker = []

def site_encoding(ctx, default='utf-8'):
    # Plone implements management_page_charset based on
    # site_properties -> default_charset setting, so this should work
    # through Zope and Plone.
    return getattr(ctx, 'management_page_charset', default)

# This is the same value used in zhttp_collector. It should turn into
# a ZConfig setting on zope.conf when it gets merged into Zope.
LARGE_FILE = 1 << 19

def PUT(self, REQUEST, RESPONSE):
    """Create a new non-collection resource."""
    self.dav__init(REQUEST, RESPONSE)

    name = self.__name__
    parent = self.__parent__

    ifhdr = REQUEST.get_header('If', '')
    if WriteLockInterface.isImplementedBy(parent) and parent.wl_isLocked():
        if ifhdr:
            parent.dav__simpleifhandler(REQUEST, RESPONSE, col=1)
        else:
            # There was no If header at all, and our parent is locked,
            # so we fail here
            raise Locked
    elif ifhdr:
        # There was an If header, but the parent is not locked
        raise PreconditionFailed

    # SDS: Only use BODY if the file size is smaller than LARGE_FILE,
    # otherwise read LARGE_FILE bytes from the file which should be
    # enough to trigger content_type detection, and possibly enough
    # for CMF's content_type_registry too.
    #
    # Note that body here is really just used for detecting the
    # content type and figuring out the correct factory. The correct
    # file content will be uploaded on ob.PUT(REQUEST, RESPONSE) after
    # the object has been created.
    #
    # A problem I could see is content_type_registry predicates that
    # do depend on the whole file being passed here as an
    # argument. There's none by default that does this though. If they
    # really do want to look at the file, they should use
    # REQUEST['BODYFILE'] directly.

    if int(REQUEST.get('CONTENT_LENGTH') or 0) > LARGE_FILE:
        file = REQUEST['BODYFILE']
        body = file.read(LARGE_FILE)
        file.seek(0)
    else:
        body = REQUEST.get('BODY', '')

    typ = REQUEST.get_header('content-type', None)
    if typ is None:
        typ, enc = guess_content_type(name, body)

    factory = getattr(parent, 'PUT_factory', self._default_PUT_factory)
    ob = factory(name, typ, body)
    if ob is None:
        ob = self._default_PUT_factory(name, typ, body)

    # We call _verifyObjectPaste with verify_src=0, to see if the
    # user can create this type of object (and we don't need to
    # check the clipboard.
    try:
        parent._verifyObjectPaste(ob.__of__(parent), 0)
    except Unauthorized:
        raise
    except:
        raise Forbidden, sys.exc_info()[1]

    # Delegate actual PUT handling to the new object,
    # SDS: But just *after* it has been stored.
    self.__parent__._setObject(name, ob)
    # Give the object a _p_jar, required for some operations like
    # renaming, and in theory harmless at this point in the call
    # stack.
    transaction.savepoint(optimistic=True)
    ob = self.__parent__._getOb(name)
    ob.PUT(REQUEST, RESPONSE)

    RESPONSE.setStatus(201)
    RESPONSE.setBody('')
    return RESPONSE


def COPY(self, REQUEST, RESPONSE):
    """Create a duplicate of the source resource whose state
    and behavior match that of the source resource as closely
    as possible. Though we may later try to make a copy appear
    seamless across namespaces (e.g. from Zope to Apache), COPY
    is currently only supported within the Zope namespace.
    """
    self.dav__init(REQUEST, RESPONSE)
    if not hasattr(aq_base(self), 'cb_isCopyable') or \
       not self.cb_isCopyable():
        raise MethodNotAllowed, 'This object may not be copied.'

    depth=REQUEST.get_header('Depth', 'infinity')
    if not depth in ('0', 'infinity'):
        raise BadRequest, 'Invalid Depth header.'

    dest=REQUEST.get_header('Destination', '')
    while dest and dest[-1]=='/':
        dest=dest[:-1]
    if not dest:
        raise BadRequest, 'Invalid Destination header.'

    try: path = REQUEST.physicalPathFromURL(dest)
    except ValueError:
        raise BadRequest, 'Invalid Destination header'

    name = path.pop()
    parent_path = '/'.join(path)

    oflag=REQUEST.get_header('Overwrite', 'F').upper()
    if not oflag in ('T', 'F'):
        raise BadRequest, 'Invalid Overwrite header.'

    try: parent=self.restrictedTraverse(path)
    except ValueError:
        raise Conflict, 'Attempt to copy to an unknown namespace.'
    except NotFound:
        raise Conflict, 'Object ancestors must already exist.'
    except:
        t, v, tb=sys.exc_info()
        raise t, v
    if hasattr(parent, '__null_resource__'):
        raise Conflict, 'Object ancestors must already exist.'
    # ---- Start Plone Hack ---------------------------------------
    # Plone-specific hack that can't just go into Zope. Can be removed
    # when ReplaceableWrapper has been removed from Plone.
    existing = True
    obj = getattr(aq_base(parent), name, _marker)
    if obj is _marker:
        if parent._getOb(name, None) is None:
            existing = False
    elif isinstance(obj, ComputedAttribute):
        existing = False
    # ---- End Plone Hack ---------------------------------------
    if existing and oflag=='F':
        raise PreconditionFailed, 'Destination resource exists.'
    try:
        parent._checkId(name, allow_dup=1)
    except:
        raise Forbidden, sys.exc_info()[1]
    try:
        parent._verifyObjectPaste(self)
    except Unauthorized:
        raise
    except:
        raise Forbidden, sys.exc_info()[1]

    # Now check locks.  The If header on a copy only cares about the
    # lock on the destination, so we need to check out the destinations
    # lock status.
    ifhdr = REQUEST.get_header('If', '')
    if existing:
        # The destination itself exists, so we need to check its locks
        destob = aq_base(parent)._getOb(name)
        if WriteLockInterface.isImplementedBy(destob) and \
           destob.wl_isLocked():
            if ifhdr:
                itrue = destob.dav__simpleifhandler(
                    REQUEST, RESPONSE, 'COPY', refresh=1)
                if not itrue:
                    raise PreconditonFailed
            else:
                raise Locked, 'Destination is locked.'
    elif WriteLockInterface.isImplementedBy(parent) and \
         parent.wl_isLocked():
        if ifhdr:
            parent.dav__simpleifhandler(REQUEST, RESPONSE, 'COPY',
                                        refresh=1)
        else:
            raise Locked, 'Destination is locked.'

    self._notifyOfCopyTo(parent, op=0)
    ob = self._getCopy(parent)
    ob._setId(name)

    if depth=='0' and isDavCollection(ob):
        for id in ob.objectIds():
            ob._delObject(id)

    if existing:
        object=getattr(parent, name)
        self.dav__validate(object, 'DELETE', REQUEST)
        parent._delObject(name)

    parent._setObject(name, ob)
    ob = parent._getOb(name)
    ob._postCopy(parent, op=0)
    ob.manage_afterClone(ob)
    # We remove any locks from the copied object because webdav clients
    # don't track the lock status and the lock token for copied resources
    ob.wl_clearLocks()

    RESPONSE.setStatus(existing and 204 or 201)
    if not existing:
        RESPONSE.setHeader('Location', dest)
    RESPONSE.setBody('')
    return RESPONSE


def MOVE(self, REQUEST, RESPONSE):
    """Move a resource to a new location. Though we may later try to
    make a move appear seamless across namespaces (e.g. from Zope
    to Apache), MOVE is currently only supported within the Zope
    namespace."""
    self.dav__init(REQUEST, RESPONSE)
    self.dav__validate(self, 'DELETE', REQUEST)
    if not hasattr(aq_base(self), 'cb_isMoveable') or \
       not self.cb_isMoveable():
        raise MethodNotAllowed, 'This object may not be moved.'

    dest=REQUEST.get_header('Destination', '')

    try: path = REQUEST.physicalPathFromURL(dest)
    except ValueError:
        raise BadRequest, 'No destination given'

    flag=REQUEST.get_header('Overwrite', 'F')
    flag=flag.upper()

    name = path.pop()
    parent_path = '/'.join(path)

    try: parent = self.restrictedTraverse(path)
    except ValueError:
        raise Conflict, 'Attempt to move to an unknown namespace.'
    except 'Not Found':
        raise Conflict, 'The resource %s must exist.' % parent_path
    except:
        t, v, tb=sys.exc_info()
        raise t, v
    if hasattr(parent, '__null_resource__'):
        raise Conflict, 'The resource %s must exist.' % parent_path
    # ---- Start Plone Hack ---------------------------------------
    # Plone-specific hack that can't just go into Zope. Can be removed
    # when ReplaceableWrapper has been removed from Plone.
    existing = True
    obj = getattr(aq_base(parent), name, _marker)
    if obj is _marker:
        if parent._getOb(name, None) is None:
            existing = False
    elif isinstance(obj, ComputedAttribute):
        existing = False
    # ---- End Plone Hack ---------------------------------------
    if existing and flag=='F':
        raise PreconditionFailed, 'Resource %s exists.' % dest
    try:
        parent._checkId(name, allow_dup=1)
    except:
        raise Forbidden, sys.exc_info()[1]
    try:
        parent._verifyObjectPaste(self)
    except Unauthorized:
        raise
    except:
        raise Forbidden, sys.exc_info()[1]

    # Now check locks.  Since we're affecting the resource that we're
    # moving as well as the destination, we have to check both.
    ifhdr = REQUEST.get_header('If', '')
    if existing:
        # The destination itself exists, so we need to check its locks
        destob = aq_base(parent)._getOb(name)
        if WriteLockInterface.isImplementedBy(destob) and \
           destob.wl_isLocked():
            if ifhdr:
                itrue = destob.dav__simpleifhandler(
                    REQUEST, RESPONSE, 'MOVE', url=dest, refresh=1)
                if not itrue:
                    raise PreconditionFailed
            else:
                raise Locked, 'Destination is locked.'
    elif WriteLockInterface.isImplementedBy(parent) and \
         parent.wl_isLocked():
        # There's no existing object in the destination folder, so
        # we need to check the folders locks since we're changing its
        # member list
        if ifhdr:
            itrue = parent.dav__simpleifhandler(REQUEST, RESPONSE, 'MOVE',
                                                col=1, url=dest, refresh=1)
            if not itrue:
                raise PreconditionFailed, 'Condition failed.'
        else:
            raise Locked, 'Destination is locked.'
    if Lockable.wl_isLocked(self):
        # Lastly, we check ourselves
        if ifhdr:
            itrue = self.dav__simpleifhandler(REQUEST, RESPONSE, 'MOVE',
                                              refresh=1)
            if not itrue:
                raise PreconditionFailed, 'Condition failed.'
        else:
            raise PreconditionFailed, 'Source is locked and no '\
                  'condition was passed in.'

    # try to make ownership explicit so that it gets carried
    # along to the new location if needed.
    self.manage_changeOwnershipType(explicit=1)

    self._notifyOfCopyTo(parent, op=1)
    ob = aq_base(self._getCopy(parent))
    self.aq_parent._delObject(absattr(self.getId()))
    ob._setId(name)
    if existing:
        object = parent._getOb(name)
        self.dav__validate(object, 'DELETE', REQUEST)
        parent._delObject(name)
    parent._setObject(name, ob)
    ob = parent._getOb(name)
    ob._postCopy(parent, op=1)

    # try to make ownership implicit if possible
    ob.manage_changeOwnershipType(explicit=0)

    RESPONSE.setStatus(existing and 204 or 201)
    if not existing:
        RESPONSE.setHeader('Location', dest)
    RESPONSE.setBody('')
    return RESPONSE


def xml_escape(value):
    from webdav.xmltools import escape
    if not isinstance(value, basestring):
        value = str(value)
    value = escape(value)
    return value

old_allprop = PropertySheets.PropertySheet.dav__allprop
def dav__allprop(self, propstat=old_allprop.func_defaults[-1]):
    enc = site_encoding(self, default='latin-1')

    # Warning: Evil hack here to inject a xml_escape function that
    # knows about the (possibly local) site encoding and encodes
    # values into that encoding.
    def xml_escape_encode(value, enc=enc):
        value = xml_escape(value)
        if isinstance(value, unicode):
            return value.encode(enc)
        return value
    old_allprop.im_func.func_globals['xml_escape'] = xml_escape_encode

    result = old_allprop(self, propstat=propstat)
    if isinstance(result, str):
        if enc == 'utf-8':
            # shortcut, no need to decode and re-encode if encoding is
            # the same.
            return result
        # decode into the portal encoding.
        result = result.decode(enc)
    # xml output will be utf-8
    return result.encode('utf-8')

old_propstat = PropertySheets.PropertySheet.dav__propstat
def dav__propstat(self, name, result,
                  propstat=old_propstat.func_defaults[-2],
                  propdesc=old_propstat.func_defaults[-1]):
    enc = site_encoding(self, default='latin-1')

    # Warning: Evil hack here to inject a xml_escape function that
    # knows about the (possibly local) site encoding and encodes
    # values into that encoding.
    def xml_escape_encode(value, enc=enc):
        value = xml_escape(value)
        if isinstance(value, unicode):
            return value.encode(enc)
        return value
    old_propstat.im_func.func_globals['xml_escape'] = xml_escape_encode

    old_propstat(self, name, result,
                 propstat=propstat, propdesc=propdesc)
    for key, items in result.items():
        for idx, value in enumerate(items):
            if isinstance(value, str) and enc != 'utf-8':
                # decode into the portal encoding and encode into utf-8
                # xml output will be utf-8
                items[idx] = value.decode(enc).encode('utf-8')
    return

old_PropPatch_apply = PropPatch.apply
def PropPatch_apply(self, obj):
    enc = site_encoding(obj, default='latin-1')
    # strval() has been` patched to return unicode strings, so we
    # re-encode into site-encoding for the object.
    for idx, value in enumerate(self.values):
        if len(value) > 2:
            name, ns, val, md = value
            if isinstance(val, unicode):
                val = val.encode(enc)
            if isinstance(name, unicode):
                name = name.encode(enc)
            if isinstance(ns, unicode):
                ns = ns.encode(enc)
            if md.has_key('__xml_attrs__'):
                new_attrs = {}
                attrs = md['__xml_attrs__']
                for k, v in attrs.items():
                    if isinstance(k, unicode):
                        k = k.encode(enc)
                    if isinstance(v, unicode):
                        v = v.encode(enc)
                    new_attrs[k] = v
                md['__xml_attrs__'] = new_attrs
            self.values[idx] = name, ns, val, md
    result = old_PropPatch_apply(self, obj)
    if hasattr(aq_base(obj), 'reindexObject'):
        # Check for 424 Failed Dependency, which signals that the
        # transaction has been aborted. Yuck.
        if not '424 Failed Dependency' in result:
            obj.reindexObject()
    return result

old_Lock_apply = Lock.apply
def Lock_apply(self, obj, creator=None, depth='infinity',
               token=None, result=None, url=None, top=1):
    enc = site_encoding(obj, default='latin-1')
    # strval() has been patched to return unicode strings, so we
    # re-encode into site-encoding for the object.
    if self.owner and isinstance(self.owner, unicode):
        self.owner = self.owner.encode(enc)
    if self.scope and isinstance(self.scope, unicode):
        self.scope = self.scope.encode(enc)
    if self.type and isinstance(self.type, unicode):
        self.type = self.type.encode(enc)
    if token and isinstance(token, unicode):
        token = token.encode(enc)
    return old_Lock_apply(self, obj, creator=creator,
                          depth=depth, token=token,
                          result=result, url=url, top=top)

def _propertyMap(self):
    # Return a tuple of mappings, giving meta-data for properties.
    # Some ZClass instances dont seem to have an _properties, so
    # we have to fake it...
    return self.p_self()._properties or ()

class ResponseIOWrapper:

    def __init__(self, response):
        self.response = response

    def write(self, chunk):
        self.response.write(chunk)

    def getvalue(self):
        return self.response

class SafePropFind(PropFind):
    """A PropFind implementation that tries it's best to return
    well-formed XML in face of possible exceptions.
    """

    def apply(self, obj, url=None, depth=0, result=None, top=1):
        if result is None:
            result=StringIO()
            depth=self.depth
            url=urlfix(self.request['URL'], 'PROPFIND')
            url=urlbase(url)
            result.write('<?xml version="1.0" encoding="utf-8"?>\n' \
                         '<d:multistatus xmlns:d="DAV:">\n')
        iscol=isDavCollection(obj)
        if iscol and url[-1] != '/': url=url+'/'
        result.write('<d:response>\n<d:href>%s</d:href>\n' % safe_quote(url))
        if hasattr(aq_base(obj), 'propertysheets'):
            propsets=obj.propertysheets.values()
            obsheets=obj.propertysheets
        else:
            davprops=DAVProps(obj)
            propsets=(davprops,)
            obsheets={'DAV:': davprops}
        if self.allprop:
            stats=[]
            for ps in propsets:
                if hasattr(aq_base(ps), 'dav__allprop'):
                    try:
                        stats.append(ps.dav__allprop())
                    except ConflictError:
                        raise
                    except:
                        logger.exception(
                            'Exception calling dav__allprop on %r (%r)',
                            ps, obj)
            stats=''.join(stats) or '<d:status>200 OK</d:status>\n'
            result.write(stats)
        elif self.propname:
            stats=[]
            for ps in propsets:
                if hasattr(aq_base(ps), 'dav__propnames'):
                    try:
                        stats.append(ps.dav__propnames())
                    except ConflictError:
                        raise
                    except:
                        logger.exception(
                            'Exception calling dav__propnames on %r (%r)',
                            ps, obj)
            stats=''.join(stats) or '<d:status>200 OK</d:status>\n'
            result.write(stats)
        elif self.propnames:
            rdict={}
            for name, ns in self.propnames:
                ps=obsheets.get(ns, None)
                got = False
                if ps is not None and hasattr(aq_base(ps), 'dav__propstat'):
                    try:
                        stat=ps.dav__propstat(name, rdict)
                        got = True
                    except ConflictError:
                        raise
                    except:
                        logger.exception(
                            'Exception calling dav__propstat on %r (%r)',
                            ps, obj)
                if not got:
                    prop='<n:%s xmlns:n="%s"/>' % (name, ns)
                    code='404 Not Found'
                    if not rdict.has_key(code):
                        rdict[code]=[prop]
                    else:
                        rdict[code].append(prop)
            keys=rdict.keys()
            keys.sort()
            for key in keys:
                result.write('<d:propstat>\n' \
                             '  <d:prop>\n' \
                             )
                map(result.write, rdict[key])
                result.write('  </d:prop>\n' \
                             '  <d:status>HTTP/1.1 %s</d:status>\n' \
                             '</d:propstat>\n' % key
                             )
        else:
            raise BadRequest('Invalid request')
        result.write('</d:response>\n')
        if depth in ('1', 'infinity') and iscol:
            try:
                objs = obj.listDAVObjects()
            except ConflictError:
                raise
            except:
                objs = ()
                logger.exception('Exception calling listDAVObjects on %r', obj)

            for ob in objs:
                if hasattr(ob,"meta_type"):
                    if ob.meta_type=="Broken Because Product is Gone":
                        continue
                dflag=hasattr(ob, '_p_changed') and (ob._p_changed == None)
                if hasattr(ob, '__locknull_resource__'):
                    # Do nothing, a null resource shouldn't show up to DAV
                    if dflag:
                        ob._p_deactivate()
                elif hasattr(ob, '__dav_resource__'):
                    uri = urljoin(url, absattr(ob.getId()))
                    depth = depth=='infinity' and depth or 0
                    self.apply(ob, uri, depth, result, top=0)
                    if dflag:
                        ob._p_deactivate()
        if not top:
            return result
        result.write('</d:multistatus>')
        return result.getvalue()

# Make PROPFIND stream down using RESPONSE.write(). We ignore Zope's
# hack for MSIE DAV bug.
def PROPFIND(self, REQUEST, RESPONSE):
    """Retrieve properties defined on the resource.
    """
    self.dav__init(REQUEST, RESPONSE)
    RESPONSE.setStatus(207)
    RESPONSE.setHeader('Content-Type', 'text/xml; charset="utf-8"')
    cmd = SafePropFind(REQUEST)
    # We have to do some upfront work here to deal with the fact that
    # we are passing result to apply.
    depth = cmd.depth
    url = urlfix(cmd.request['URL'], 'PROPFIND')
    url = urlbase(url)
    result = ResponseIOWrapper(RESPONSE)
    s = ('<?xml version="1.0" encoding="utf-8"?>\n'
         '<d:multistatus xmlns:d="DAV:">\n')
    result.write(s)
    cmd.apply(self, url=url, depth=depth, result=result)
    return RESPONSE

def OPTIONS(self, REQUEST, RESPONSE):
    """Retrieve communication options."""
    self.dav__init(REQUEST, RESPONSE)
    RESPONSE.setHeader('Public', ', '.join(self.__http_methods__))
    RESPONSE.setHeader('Allow', ', '.join(self.__http_methods__))
    RESPONSE.setHeader('Content-Length', 0)
    RESPONSE.setHeader('DAV', '1, 2', 1)
    RESPONSE.setStatus(200)
    return RESPONSE

def MKCOL_handler(self, name):
    """ Map MKCOL_handler to manage_addFolder for OFS.Folder
    """
    return self.manage_addFolder(name)

def manage_FTPget(self):
    """Return body for ftp."""
    RESPONSE = self.REQUEST.RESPONSE

    if self.ZCacheable_isCachingEnabled():
        result = self.ZCacheable_get(default=None)
        if result is not None:
            # We will always get None from RAMCacheManager but we will get
            # something implementing the IStreamIterator interface
            # from FileCacheManager.
            # the content-length is required here by HTTPResponse, even
            # though FTP doesn't use it.
            RESPONSE.setHeader('Content-Length', self.size)
            return result

    data = self.data
    if type(data) is type(''):
        RESPONSE.setBase(None)
        return data

    while data is not None:
        RESPONSE.write(data.data)
        data = data.next

    return ''

def manage_FTPstat(self, REQUEST):
    """Pseudo stat used for FTP listings
    """
    mode = 0040000
    from AccessControl.User import nobody
    # check to see if we are acquiring our objectValues or not
    method = self.objectValues
    if not getattr(method, 'im_self', None) is self:
        try:
            if getSecurityManager().validateValue(self.manage_FTPlist):
                mode = mode | 0770
        except: pass
        if nobody.allowed(self.manage_FTPlist, self.manage_FTPlist.__roles__):
            mode = mode | 0007
    mtime = self.bobobase_modification_time().timeTime()
    # get owner and group
    owner = group = 'Zope'
    for user, roles in self.get_local_roles():
        if 'Owner' in roles:
            owner = user
            break
    return marshal.dumps((mode, 0, 0, 1, owner, group, 0, mtime, mtime, mtime))

def should_wrap_pipe(response):
    # Not streaming, Return.
    if not response._streaming:
        return
    # gzip not requested? Return.
    if not response.use_HTTP_content_compression:
        return
    # Already wrapped. Return.
    if isinstance(response.stdout, GZipPipeWrapper):
        # This might happen if there's a conflict error and the
        # response is retried.
        return
    # use HTTP content encoding to compress body contents unless
    # this response already has another type of content encoding
    if not response.headers.get('content-encoding', 'gzip') == 'gzip':
        return
    # If there is a content-length header present, we cannot gzip the
    # content. Otherwise the content-length will different from the
    # actual response body and some clients (for example Firefox) will
    # freak out on us.
    if response.headers.get('content-length', ''):
        return
    # Should we compress this content-type? If not, return.
    content_type = response.headers.get('content-type', '')
    if content_type.split('/')[0] in uncompressableMimeMajorTypes:
        return
    # Alright, we got this far. That means we can operate our magik.
    response.setHeader('content-encoding', 'gzip')
    # Add a hint about who's gzipping the stream.
    response.setHeader('X-Stream-Gzipped-By', 'DavPack')
    # use_HTTP_content_compression == 1 if force was
    # NOT used in enableHTTPCompression().
    # If we forced it, then Accept-Encoding
    # was ignored anyway, so cache should not
    # vary on it. Otherwise if not forced, cache should
    # respect Accept-Encoding client header
    if response.use_HTTP_content_compression == 1:
        response.appendHeader('Vary', 'Accept-Encoding')
    return True

old_finish = ZServerHTTPResponse._finish
def HTTPResponse_finish(self):
    self._finished = True
    return old_finish(self)

def HTTPResponse_retry(self):
    """Return a response object to be used in a retry attempt
    """
    # This implementation is a bit lame, because it assumes that
    # only stdout stderr were passed to the constructor. OTOH, I
    # think that that's all that is ever passed.

    response=self.__class__(stdout=self.stdout, stderr=self.stderr)
    response.headers=self.headers
    response._http_version=self._http_version
    response._http_connection=self._http_connection
    response._server_version=self._server_version
    response._wrote = getattr(self, '_wrote', False)
    response._streaming = getattr(self, '_streaming', False)
    response._chunking = getattr(self, '_chunking', False)
    response.gzip_piping = getattr(self, 'gzip_piping', False)

    # We assume that if the request was streaming, and a ConflictError
    # happened (thus Zope retries) then that means that the data has
    # already been streamed and we mark the response as 'finished' so
    # that we don't write the response twice.
    finished = getattr(self, '_streaming', False)
    response._finished = getattr(self, '_finished', False) or finished

    self._retried_response = response
    return response

def HTTPResponse_write(self, data):
    # We have to duplicate some code here because the wrapper needs to
    # be hooked in just after the headers were written, but we still
    # need to set a header.

    # If retry() is called, we might have finished already so we check
    # that to avoid writing the response body twice.
    if getattr(self, '_finished', False):
        return

    if isinstance(data, unicode):
        # We assume utf-8 encoding for unicode.
        # XXX SdS: Investigate
        # webdav/davcmds.py", line 146, in apply
        #   map(result.write, rdict[key])
        data = data.encode('utf-8')

    if not isinstance(data, str):
        raise TypeError('Value must be a string: %s' % repr(data))

    if not self._wrote:
        l = self.headers.get('content-length', None)
        if l is not None:
            try:
                if isinstance(l, str):
                    l = int(l)
                if l > 128000:
                    self._tempfile=tempfile.TemporaryFile()
                    self._templock=thread.allocate_lock()
            except: pass

        self._streaming = 1
        # We need to do the check exactly here, otherwise the extra
        # headers will not get set.
        wrap = should_wrap_pipe(self)
        self.stdout.write(str(self))
        self._wrote = 1
        if wrap is not None:
            self.stdout = GZipPipeWrapper(self.stdout, self._chunking)
            self.gzip_piping = True

    if not data:
        return

    if self._chunking and not getattr(self, 'gzip_piping', False):
        data = '%x\r\n%s\r\n' % (len(data), data)

    l = len(data)

    t = self._tempfile
    if t is None or l < 200:
        self.stdout.write(data)
    else:
        b = self._tempstart
        e = b + l
        self._templock.acquire()
        try:
            t.seek(b)
            t.write(data)
        finally:
            self._templock.release()
        self._tempstart = e
        self.stdout.write(file_part_producer(t, self._templock, b, e), l)

def maybeFlagRequest():
    try:
        from Products.PluggableAuthService.plugins.RequestTypeSniffer \
            import RequestTypeSniffer
    except ImportError:
        log('Could not import RequestTypeSniffer, cannot enable request flagging')
        # Can't work here, do nothing.
        return
        
    from zope.interface import alsoProvides, Interface
    from ZPublisher import Publish
    from ZPublisher.HTTPRequest import HTTPRequest
    from ZServer.PubCore.ZRendezvous import ZRendevous

    sniffer = RequestTypeSniffer('sniffer')

    def snifAndApply(request):
        iface = sniffer.sniffRequestType(request)
        if iface is not None and issubclass(iface, Interface):
            if not iface.providedBy(request):
                alsoProvides(request, iface)

    orig_handle = ZRendevous.handle
    def handle(self, name, request, response):
        snifAndApply(request)
        return orig_handle(self, name, request, response)
    ZRendevous.handle = handle
    log('Patch applied to ZPublisher.ZRendezvous.handle')

    orig_init = HTTPRequest.__init__
    def __init__(self, stdin, environ, response, clean=0):
        orig_init(self, stdin, environ, response, clean=clean)
        snifAndApply(self)
    HTTPRequest.__init__ = __init__
    log('Patch applied to ZPublisher.HTTPRequest.__init__')

    orig_publish = Publish.publish
    def publish(*args, **kw):
        request = args[0]
        snifAndApply(request)
        return orig_publish(*args, **kw)
    Publish.publish = publish
    log('Patch applied to ZPublisher.Publish.publish')

def initialize(context):
    # Always apply those.
    from webdav.NullResource import NullResource
    NullResource.PUT = PUT
    log('Patch applied to webdav.NullResource.PUT.')

    from webdav.Resource import Resource
    from webdav.Collection import Collection

    Resource.PROPFIND = PROPFIND
    log('Enabling PROPFIND Streaming.')

    Resource.OPTIONS = OPTIONS
    log('Enabling "Public" Header in Options Response.')

    ZServerHTTPResponse.write = HTTPResponse_write
    ZServerHTTPResponse.retry = HTTPResponse_retry
    ZServerHTTPResponse._finish = HTTPResponse_finish
    log('Enabling gzip support for ZServer streaming.')

    import webdav.xmltools
    import webdav.davcmds
    import xmltools
    webdav.xmltools.XmlParser = xmltools.XmlParser
    webdav.davcmds.XmlParser = xmltools.XmlParser
    log('Patch applied to webdav.xmltools.XmlParser.')

    Resource.COPY = COPY
    log('Patch applied to webdav.Resource.COPY.')

    Resource.MOVE = MOVE
    log('Patch applied to webdav.Resource.MOVE.')

    PropPatch.apply = PropPatch_apply
    log('Patch applied to PropPatch.apply.')

    Lock.apply = Lock_apply
    log('Patch applied to Lock.apply.')

    PropertySheets.xml_escape = xml_escape
    log('Patch applied to OFS.PropertySheets.xmlescape.')

    PropertySheets.PropertySheet.dav__allprop = dav__allprop
    log('Patch applied to OFS..PropertySheet.dav__allprop.')

    PropertySheets.PropertySheet.dav__propstat = dav__propstat
    log('Patch applied to OFS..PropertySheet.dav__propstat.')

    PropertySheets.PropertySheet._propertyMap = _propertyMap
    log('Patch applied to OFS..PropertySheet._propertyMap.')

    from App.version_txt import getZopeVersion
    zope_version = getZopeVersion()

    from OFS.ObjectManager import ObjectManager
    ObjectManager.manage_FTPstat = manage_FTPstat
    log('Patch applied to ObjectManager..manage_FTPstat.')

    from OFS.Folder import Folder
    Folder.MKCOL_handler = MKCOL_handler
    log('Patch applied OFS.Folder..MKCOL_handler.')

    maybeFlagRequest()

    if zope_version < (2, 7, 8):
        from OFS.Image import File
        File.manage_FTPget = manage_FTPget
        log('Patch applied to OFS.Image.manage_FTPget')

    try:
        from Products.Archetypes.utils import getPkgInfo
        import Products.Archetypes
        at_info = getPkgInfo(Products.Archetypes)
    except ImportError:
        log('Archetypes not found. *NOT* applying AT patches.')
    except ValueError:
        log('Archetypes version could not be detected. '
            'Patches *NOT* applied.')
    else:
        at_version = at_info.numversion
        str_version = at_info.version
        if at_version > (1, 3, 7, 0):
            log('Archetypes %s. Patches *NOT* applied.' % str_version)
        else:
            log('Archetypes %s. Applying patches.' % str_version)
            from Products.DavPack import at

    try:
        from Products.Archetypes.interfaces import IWebDAVObjectInitializedEvent
        from Products.Archetypes.interfaces import IWebDAVObjectEditedEvent
    except ImportError:
        import Products.DavPack.at.webdav
        from Products.Archetypes.BaseObject import BaseObject
        from Products.Archetypes.BaseContent import BaseContent
        from Products.Archetypes.BaseFolder import BaseFolder

        BaseObject.markCreationFlag = Products.DavPack.at.webdav.markCreationFlag
        BaseContent.PUT = Products.DavPack.at.webdav.PUT
        BaseFolder.PUT = Products.DavPack.at.webdav.PUT
        BaseFolder.MKCOL_handler = Products.DavPack.at.webdav.MKCOL_handler
        log('Applied patch to Archetypes: '
            'Fire IWebDAVObject{Edited|Initialized}Event')

    try:
        import Products.CMFEditions
    except ImportError:
        pass
    else:
        try:
            from Products.CMFEditions.subscriber import webdavObjectEdited
        except ImportError:
            import Products.DavPack.cmfeditions
            Products.DavPack.cmfeditions.registerSubscribers()
            log('Applied patch to CMFEditions: '
                'Subscribe to IWebDAVObject{Edited|Initialized}Event)')

    try:
        from Products.CMFPlone import PloneFolder
    except ImportError:
        log('Plone not found. *NOT* applying Plone patches.')
    else:
        try:
            from Products.CMFPlone.utils import getFSVersionTuple
            plone_version = getFSVersionTuple()
        except ImportError:
            plone_version = (0, 0, 0, 'unknown', 0)
        str_version = '%s.%s.%s-%s-%s' % plone_version
        if not plone_version < (2, 0, 5, 0):
            log('Plone %s. Patches *NOT* applied.' % str_version)
        else:
            log('Plone %s. Applying patches.' % str_version)
            from Products.DavPack import plone
