# Enfold Desktop
# Copyright(C), 2004-2006, Enfold Systems, Inc. - ALL RIGHTS RESERVED

# Enfold Systems, Inc.
# 4617 Montrose Blvd., Suite C215
# Houston, Texas 77006 USA
# p. +1 713.942.2377 | f. +1 832.201.8856
# www.enfoldsystems.com
# info@enfoldsystems.com

# $Id: __init__.py 9001 2008-10-21 17:06:45Z sidnei $
# $HeadURL: https://svn.enfoldsystems.com/internal/ShellExServer/trunk/__init__.py $

import re
import posixpath
import transaction
import webdav.Resource
import webdav.Collection
import webdav.NullResource
import OFS.CopySupport
from webdav.common import rfc1123_date
from Acquisition import aq_base

from Products.CMFCore.permissions import AddPortalContent, ManagePortal, View
from Products.CMFCore.ContentTypeRegistry import registerPredicateType

try:
    from Products.CMFCore.exportimport.contenttyperegistry \
        import ContentTypeRegistryXMLAdapter as CTRXA
    def registerPredicateCracker(type_name, cracker):
        CTRXA._KNOWN_PREDICATE_TYPES[type_name] = cracker
except ImportError:
    def registerPredicateCracker(type_name, cracker):
        pass

try:
    from Products.CMFCore.permissions import setDefaultRoles
except:
    from Products.CMFCore.CMFCorePermissions import setDefaultRoles

from Products.ShellExServer.config import *
from Products.ShellExServer.normalize import normalizerFor

_marker = object()

# Make sure Install imports
from Products.ShellExServer.Extensions import Install as _Install
del _Install

def registerVocab(context, module, name, permission=ManagePortal):
    klass = getattr(module, name)
    constructor = getattr(module, 'manage_add%s' % name)
    context.registerClass(
        klass,
        meta_type='Vocabulary Provider: %s' % name,
        permission=permission,
        constructors=(constructor,),
        icon='www/vocab_provider.png'
        )
    constructor.setPermission(permission)

def marshall_register(schema, marshaller):
    try:
        # It's a soft dependency, if not available ignore it.
        from Products.Marshall import ControlledMarshaller
    except ImportError:
        pass
    else:
        # Check if not already wrapped.
        if not isinstance(marshaller, ControlledMarshaller):
            # Wrap into a ControlledMarshaller
            marshaller = ControlledMarshaller(marshaller)

    schema.registerLayer('marshall', marshaller)

# register the directories
from Products.CMFCore.DirectoryView import registerDirectory
registerDirectory('skins', GLOBALS)

################################################################
# fix Format in Plone

from Acquisition import aq_base
from Products.CMFCore.PortalFolder import PortalFolder
from Products.CMFCore.ContentTypeRegistry import ContentTypeRegistry
from Products.CMFCore.ContentTypeRegistry import ExtensionPredicate
from Products.CMFCore.utils import getToolByName, _checkPermission
from Products.CMFDefault.DublinCore import DefaultDublinCoreImpl
from Products.CMFDefault.Document import Document
from Products.CMFDefault.Link import Link

PATCH_ATTR = '__shellex_patched__'
PATTERN = '__shellex_%s__'

def patched(method):
    return getattr(method, PATCH_ATTR, False)

def patch(klass, mname, new_method):
    kname = klass.__name__
    old_method = getattr(klass, mname)
    new_name = PATTERN % mname
    if not patched(getattr(klass, mname)):
        setattr(klass, mname, new_method)
        setattr(klass, new_name, old_method)
        try:
            setattr(new_method, PATCH_ATTR, True)
        except AttributeError:
            # Not a method? Ignore.
            pass
        log('Patching %s.%s.' % (kname, mname))
    else:
        log('**NOT** patching %s.%s, already patched.' % (kname, mname))

def call(self, __name__, *args, **kw):
    return getattr(self, PATTERN % __name__)(*args, **kw)

def findTypeName(self, name, typ, body):
    """
    Perform a lookup over a collection of rules, returning the
    the name of the Type object corresponding to name/typ/body.
    Return None if no match found.
    """
    for predicate_id in self.predicate_ids:
        pred, typeObjectName = self.predicates[predicate_id]
        # Wrap it into acquisition
        pred = pred.__of__(self)
        if pred(name, typ, body):
            return typeObjectName

    return None

def PUT_factory( self, name, typ, body ):
    """
    Dispatcher for PUT requests to non-existent IDs.  Returns
    an object of the appropriate type (or None, if we don't
    know what to do).
    """
    registry = getToolByName( self, 'content_type_registry' )
    if registry is None:
        return None

    typeObjectName = registry.findTypeName( name, typ, body )
    if typeObjectName is None:
        return None

    try:
        # try to pass the format
        self.invokeFactory(typeObjectName, name, format=typ)
    except TypeError:
        # If that fails, object might already have been created.
        if name in self.objectIds():
            self._delObject(name)
        self.invokeFactory(typeObjectName, name)
        # what do we now?

    # XXX: this is butt-ugly.
    obj = aq_base( self._getOb( name ) )
    self._delObject( name )
    return obj

def setFormat( self, format ):
    """ Dublin Core element - resource format
    """
    self.format = format
    self.content_type = format

def doc_FTPget(self):
    return self.EditableBody()

def link_FTPget(self):
    return self.getRemoteUrl()

def listDAVObjects(self):
    # User with ManagePortal permission should see all the objects,
    # but only if 'show_portal_tools' is enabled.
    dp = None
    pp = getToolByName(self, 'portal_properties', None)
    if pp is not None:
        dp = getToolByName(pp, 'plone_desktop_uri', None)
    if _checkPermission(ManagePortal, self):
        show_tools = False
        if dp is not None:
            show_tools = dp.getProperty('show_portal_tools', False)
        if show_tools:
            return self.objectValues()

    # Next up: look for a list of types to be blacklisted for WebDAV.
    allowed_types = None
    bl_types = None
    tt = getToolByName(self, 'portal_types', None)
    if tt is not None:
        allowed_types = tt.listContentTypes()    

    if dp is not None:
        bl_types = dp.getProperty('blacklist_types', ('Topic',))

    # we'll keep this as a lookup list for things that may not implement
    # this... not sure what that is, but hey it also explains what
    # happens...
    lookupList = ["contentValues", "objectValues"]
    for attr in lookupList:
        objectValues = getattr(self, attr, None)
        if objectValues is not None:
            break

    if attr in ('contentValues',):
        if bl_types is not None and allowed_types is not None:
            func = objectValues
            allowed_types = [t for t in allowed_types if t not in bl_types]
            def objectValues(func=func, allowed_types=allowed_types):
                return func(filter={'portal_type':allowed_types})

    if objectValues is not None:
        res =  objectValues()
        return res

    return []

def ExtensionPredicate__call__(self, name, typ, body):
    """
    Return true if the rule matches, else false.
    """
    if self.extensions is None:
        return 0

    base, ext = os.path.splitext( name )
    if ext and ext[0] == '.':
        ext = ext[1:]

    return ext.lower() in [e.lower() for e in self.extensions]

patch(DefaultDublinCoreImpl, 'setFormat', setFormat)
patch(PortalFolder, 'PUT_factory', PUT_factory)
patch(Document, 'manage_FTPget', doc_FTPget)
patch(Link, 'manage_FTPget', link_FTPget)
patch(ContentTypeRegistry, 'findTypeName', findTypeName)
patch(ExtensionPredicate, '__call__', ExtensionPredicate__call__)

# Bug #128
# NOTE: This is fixed in CMF 1.5.x

from Products.CMFDefault.SkinnedFolder import SkinnedFolder
patch(SkinnedFolder, 'listDAVObjects', listDAVObjects)

# Now lets fix the root plone site...
from Products.CMFPlone.Portal import PloneSite
patch(PloneSite, 'listDAVObjects', listDAVObjects)

# Also fix the base folder implementation
from Products.CMFCore.PortalFolder import PortalFolderBase as PortalFolder
patch(PortalFolder, 'listDAVObjects', listDAVObjects)

# allow access to utils from presentation code
from AccessControl import allow_module
allow_module('Products.ShellExServer.utils')

# register 'ResourceLockedError' with Zope to return a '423 Locked'
# response status.
from ZPublisher.HTTPResponse import status_codes
if not status_codes.has_key('resourcelockederror'):
    log('Registering "ResourceLockedError" with ZPublisher '
        'to return a "423 Locked" response status.')
    status_codes['resourcelockederror'] = 423

# Now apply the license control to Enfold Desktop
from Products.EnfoldTools.LicenseManager.seat import desktop_acquire_license, LicenseError
from Products.EnfoldTools.LicenseManager.license import createToken

DESKTOP_RE = re.compile('Plone Desktop|Enfold Desktop')
def init_seat_management(context, REQUEST, RESPONSE):
    ua = REQUEST.get_header('User-Agent', '')
    if DESKTOP_RE.search(ua):
        # Do *not* do any kind of license check for a GET request.
        method = REQUEST.get('REQUEST_METHOD', 'GET').upper()
        if method == 'GET':
            return

        # 'X-Seat-Cookie' is backward-compatibility with 
        # Enfold Desktop 3.0 clients.
        #
        # 'X-Desktop-Cookie' is the new header for 
        # Enfold Desktop 4.0 clients.
        lic_id = REQUEST.get_header('X-Seat-Cookie', None)
        try:
            if isinstance(context, webdav.NullResource.NullResource):
                context = context.__parent__
            lic_id = desktop_acquire_license(context, lic_id)
        except LicenseError, e:
            # Desktop 3.0 did: 402: Payment Required, IIRC.
            # RESPONSE.setStatus(402, reason='License Error', lock=True)
            # 
            # New behaviour (as of Desktop 4.0): Do nothing, an Ad
            # will be displayed instead.
            pass
        else:
            # Desktop 4.0 gets a 'signed' token instead, and it's
            # always changing. We don't expect the desktop client to
            # send a token anymore.
            token = createToken(REQUEST['ACTUAL_URL'].rstrip('/'))
            RESPONSE.setHeader('X-Desktop-Cookie', token)
            RESPONSE.setHeader('X-Seat-Cookie', lic_id)

def enableWebDAVOnHTTPServer(clients='Plone Desktop|Enfold Desktop'):
    try:
        from App.config import getConfiguration
    except:
        # Zope version pre-ZConfig, bail out
        return

    from ZServer.HTTPServer import zhttp_server, zhttp_handler
    from ZServer.WebDAVSrcHandler import WebDAVSrcHandler
    _marker = []
    config = getConfiguration()
    # Is there any case where config doesn't have servers? Cameron has
    # found one.
    for server in getattr(config, 'servers', ()):
        if not isinstance(server, zhttp_server):
            continue
        port = server.port
        for handler in server.handlers:
            if isinstance(handler, WebDAVSrcHandler):
                # We don't want to muck with this one, it already does
                # what we want the http handler to do here.
                continue
            if not isinstance(handler, zhttp_handler):
                continue
            # Set webdav_source_clients regex.
            isSet = getattr(handler, '_wdav_client_reg', _marker) is not None
            if not isSet and hasattr(handler, 'set_webdav_source_clients'):
                log("Enabling WebDAV for clients matching "
                    "User-Agent '%s' on port: %s" % (clients, port))
                handler.set_webdav_source_clients(clients)

enableWebDAVOnHTTPServer()

# Enable HTTP compression for dav requests.
old_resource_init = webdav.Resource.Resource.dav__init
def resource_dav__init(self, request, response):
    # Remove 'Connection: close' header if dav__init added it.
    init_seat_management(self, request, response)
    title_fixup(self, request, response)
    existed = False
    for name in ('Connection', 'connection'):
        if getattr(response, 'headers', {}).get(name, '').lower() in ('close',):
            existed = True
    old_resource_init(self, request, response)
    if hasattr(response, 'enableHTTPCompression'):
        response.enableHTTPCompression(request)
    # Remove 'Connection: close' header and let Zope deal with it.
    if existed:
        return
    for name in ('Connection', 'connection'):
        if getattr(response, 'headers', {}).get(name, '').lower() in ('close',):
            del response.headers[name]

def collection_dav__init(self, request, response):
    # Init expected HTTP 1.1 / WebDAV headers which are not
    # currently set by the base response object automagically.
    #
    # Also, we sniff for a ZServer response object, because we don't
    # want to write duplicate headers (since ZS writes Date
    # and Connection itself).
    init_seat_management(self, request, response)
    title_fixup(self, request, response)
    if not hasattr(response, '_server_version'):
        response.setHeader('Date', rfc1123_date(), 1)

    # We are allowed to accept a url w/o a trailing slash
    # for a collection, but are supposed to provide a
    # hint to the client that it should be using one.
    # [WebDAV, 5.2]
    pathinfo = request.get('PATH_INFO', '')
    if pathinfo and pathinfo[-1] != '/':
        location='%s/' % request['URL1']
        response.setHeader('Content-Location', location)
    if hasattr(response, 'enableHTTPCompression'):
        response.enableHTTPCompression(request)

def VP__manage_FTPget(self, REQUEST=None, RESPONSE=None):
    """ Expose global vocabs via DAV/FTP
    """
    if REQUEST is None:
        REQUEST = self.REQUEST
    if RESPONSE is None:
        RESPONSE = REQUEST.RESPONSE
    return call(self, 'manage_FTPget', REQUEST, RESPONSE)

def title_fixup(ob, request, response):
    method = request.get('REQUEST_METHOD', 'GET').upper()
    if method not in ('MOVE', 'COPY', 'PUT', 'MKCOL'):
        # We don't want you. Duck off.
        return

    parents = request.get('PARENTS', ())
    if method in ('COPY', 'MOVE') and ob in parents:
        # Ignore if this is a COPY or MOVE and we're being called for
        # the source object instead of the destination object.
        return

    if getattr(aq_base(ob), 'setTitle', _marker) is _marker:
        # No setTitle, no dice.
        return

    if getattr(aq_base(ob), 'Title', _marker) is _marker:
        # No Title, even worse.
        return

    normalize = normalizerFor(ob)

    # Now the check. If the normalized title matches the original
    # filename then the title was bootstrapped from the filename and
    # never changed, so we change it to the new, but non-normalized
    # filename.
    orig_id = ob.getId()
    if method in ('COPY', 'MOVE'):
        for parent in parents:
            if getattr(aq_base(parent), 'getId', None) is None:
                continue
            orig_id = parent.getId()
            break

    # Get the original title before we start the dance.
    orig_title = ob.Title()

    # Alright, we've got to change the title here, fetch
    # the original filename from the response headers if
    # the new one has been normalized.
    #
    # Header name has to be in all lowercase.
    original_name = response.getHeader('x-renamed-from')

    # Get the normalized title for comparison with the original id, if
    # normalization is enabled. Otherwise use the original title for
    # comparison.
    if normalize is not None:
        normalized_title = normalize(orig_title)
    else:
        normalized_title = orig_title

    if normalized_title and not normalized_title == orig_id:
        if original_name is None:
            # Title has been changed from default already and no
            # normalization was performed during this operation.
            return

    if original_name is None:
        if method in ('MOVE', 'COPY'):
            # Otherwise fallback to the filename in the
            # 'Destination' header.
            dest = request.get_header('Destination', '')
            try:
                path = request.physicalPathFromURL(dest)
            except ValueError:
                # Ups, nothing we can do here.
                pass
            else:
                # Wee! We've got a Destination!
                original_name = path[-1]

        elif method in ('PUT', 'MKCOL'):
            # Do we really really care about it?
            path_info = request.get('PATH_INFO')
            if path_info:
                original_name = posixpath.basename(path_info)

    if original_name is not None:
        if orig_title:
            if (normalize and normalize(original_name) == original_name
                and not normalized_title == orig_id):
                # Normalizing the original name results in the same
                # string, so we don't want to change the title here.
                #
                # This happens if, after normalization, you change just
                # the ID but want to keep the original title. Otherwise,
                # the new title would end up as the new id and you would
                # lose the original title.
                return

        ob.setTitle(original_name)

        if method not in ('MKCOL', 'COPY', 'MOVE'):
            # Only those methods need a title reindex.
            return

        if getattr(aq_base(ob), 'reindexObject', _marker) is _marker:
            # Can't reindex? Too bad :(
            return

        ob.reindexObject(idxs=['Title'])

def MKCOL(self, REQUEST, RESPONSE):
    """Create a new collection resource.
    """
    ret = call(self, 'MKCOL', REQUEST, RESPONSE)
    ob = self.__parent__._getOb(self.__name__, None)
    if ob is None:
        return ret
    title_fixup(ob, REQUEST, RESPONSE)
    return ret

def _postCopy(self, container, op=0):
    ret = call(self, '_postCopy', container, op)
    REQUEST = self.REQUEST
    RESPONSE = REQUEST.RESPONSE
    title_fixup(self, REQUEST, RESPONSE)
    return ret

def MKCOL(self, REQUEST, RESPONSE):
    """Create a new collection resource.
    """
    ret = call(self, 'MKCOL', REQUEST, RESPONSE)
    ob = self.__parent__._getOb(self.__name__, None)
    if ob is None:
        return ret
    title_fixup(ob, REQUEST, RESPONSE)
    return ret


def initialize(context):
    # Initialize propsets
    from Products.ShellExServer import propsets
    del propsets

    # Register vocabularies
    from Products.ShellExServer import vocabs
    registerVocab(context, vocabs.dc.subject, 'Subject')
    registerVocab(context, vocabs.dc.language, 'Language')
    registerVocab(context, vocabs.dc.format, 'Format')
    registerVocab(context, vocabs.cmf.discussion, 'Discussion')
    registerVocab(context, vocabs.workflow.transitions, 'Transitions')
    registerVocab(context, vocabs.cmf.uri, 'URI')
    registerVocab(context, vocabs.enfold.actions, 'Actions')
    registerVocab(context, vocabs.enfold.users, 'Users')
    registerVocab(context, vocabs.enfold.groups, 'Groups')

    # Initialize Permissions
    from Products.ShellExServer import permissions

    # Fixup default roles for WebDAV permissions.
    from AccessControl import Permissions as perms
    DAV_PERMS_1 = (perms.webdav_lock_items,
                   perms.webdav_unlock_items)
    roles = ['Manager', 'Owner', 'Reviewer']
    for perm in DAV_PERMS_1:
        log('Changing default roles '
            'for %s to %s' % (perm, roles))
        setDefaultRoles(perm, roles)

    DAV_PERMS_2 = (perms.webdav_access,)
    roles = ['Authenticated', 'Manager', 'Owner', 'Reviewer']
    for perm in DAV_PERMS_2:
        log('Changing default roles '
            'for %s to %s' % (perm, roles))
        setDefaultRoles(perm, roles)

    try:
        from Products.Archetypes.public import listTypes
        # Change the content types from ATContentTypes to use our
        # marshall implementation.
        from Products.ATContentTypes import PROJECTNAME as ATCT_PROJECTNAME
        log('Changing marshall implementation for ATContentTypes')
        for t in listTypes(ATCT_PROJECTNAME):
            m = MARSHALLERS.get(t['name'], DEFAULT_MASHALLER)
            log('Changed marshaller for %s to %s' % (
                t['name'], m.__class__.__name__))
            marshall_register(t['schema'], m)
    except ImportError:
        pass

    try:
        # Enable sending container events for BaseObject if available
        from Products.Envy.container import classSendEvents
        from Products.Archetypes.public import BaseObject
        classSendEvents(BaseObject)
    except ImportError:
        pass

    # Register predicate type
    from Products.ShellExServer.ctr import HeaderPredicate
    from Products.ShellExServer.ctr import headerPredicateCracker
    for klass, cracker in ((HeaderPredicate, headerPredicateCracker),):
        registerPredicateType(klass.PREDICATE_TYPE, klass)
        registerPredicateCracker(klass.PREDICATE_TYPE, cracker)

    # Register a helper function as a 'constructor' so we can access
    # it through a URL.
    from Products.ShellExServer.utils import view_path
    from Products.ShellExServer.utils import get_roots
    from Products.ShellExServer.utils import get_roots
    from Products.ShellExServer.utils import getDesktopSessions
    from Products.ShellExServer.utils import getDesktopCommandSettings
    context.registerClass(
        object,
        meta_type='ShellExServer Helper',
        permission=View,
        constructors=(view_path, get_roots,
                      getDesktopSessions,
                      getDesktopCommandSettings),
        visibility=None,
        )

    # Initialize Seat Management
    patch(webdav.Resource.Resource, 'dav__init', resource_dav__init)
    patch(webdav.Collection.Collection, 'dav__init', collection_dav__init)
    log('Enabled Compression for WebDAV.')

    # Patch NullResource.MKCOL for fixing up title.
    patch(webdav.NullResource.NullResource, 'MKCOL', MKCOL)
    # Patch OFS.CopySupport.CopySource for fixing up title (it is
    # called by MOVE and COPY).
    patch(OFS.CopySupport.CopySource, '_postCopy', _postCopy)

    # More Seat Management, this time for the Vocabulary.
    from Products.CMFPropertySets.Vocabulary import VocabularyPredicate
    patch(VocabularyPredicate, 'manage_FTPget', VP__manage_FTPget)
    patch(VocabularyPredicate, 'manage_DAVget', VP__manage_FTPget)
    patch(VocabularyPredicate, '__call__', VP__manage_FTPget)
    patch(VocabularyPredicate, 'index_html', VP__manage_FTPget)

    # Initialize External Editor Callbacks
    from Products.ShellExServer.utils import setupExternalEditorCallback
    setupExternalEditorCallback()

    # Add ShellExServer version to SERVER_IDENT.
    from App.Common import package_home
    from ZServer import zhttp_server

    desktop_path = package_home({'__name__': 'Products.ShellExServer'})
    desktop_version = open(os.path.join(desktop_path, 'version.txt')).read()
    server_ident = 'ShellEx Server/%s' % desktop_version.strip()
    SERVER_IDENT = zhttp_server.SERVER_IDENT + ' ' + server_ident
    patch(zhttp_server, 'SERVER_IDENT', SERVER_IDENT)

    # Zope 2.8 doesn't have 'zcml:condition', so we have to
    # conditionally register the adapters for GenericSetup only if
    # GenericSetup is available, by loading the zcml ourselves.
    try:
        from Products.GenericSetup.interfaces import IFilesystemExporter
    except ImportError:
        pass
    else:
        import Products.ShellExServer
        from Products.Five.zcml import load_config, load_site
        load_site()
        load_config('adapter.zcml', Products.ShellExServer)

        try:
            import plone.app.linkintegrity
        except ImportError:
            pass
        else:
            load_config('integrity.zcml', Products.ShellExServer)
