##############################################################################
#
# DavPack -- A set of patches for all things related to WebDAV
# Copyright (C) 2008 Enfold Systems
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
# Some portions of this module are Benjamin Saller and respective authors.
# The original copyright statement can be found on ArchetypesLicense.txt.
#
##############################################################################
"""
$Id: __init__.py 839 2005-11-19 01:54:18Z sidnei $
"""

import posixpath

from zope import event
from zope.interface import implements

# Recent enough Zopes will have this. Do we care about older ones?
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.PortalFolder import PortalFolderBase as PortalFolder
from Products.Archetypes.utils import shasattr, mapply
from Products.Archetypes.WebDAVSupport import collection_check
from Products.Archetypes.interfaces import IObjectInitializedEvent
from Products.Archetypes.interfaces import IObjectEditedEvent
from Products.Archetypes.event import ObjectInitializedEvent
from Products.Archetypes.event import ObjectEditedEvent

class IWebDAVObjectInitializedEvent(IObjectInitializedEvent):
    """An object is being initialized via WebDAV
    """

class WebDAVObjectInitializedEvent(ObjectInitializedEvent):
    """An object is being initialised via WebDAV
    """
    implements(IWebDAVObjectInitializedEvent)

class IWebDAVObjectEditedEvent(IObjectEditedEvent):
    """An object is being edited via WebDAV
    """

class WebDAVObjectEditedEvent(ObjectEditedEvent):
    """An object is being edited via WebDAV
    """
    implements(IWebDAVObjectEditedEvent)

_marker = []

def PUT(self, REQUEST=None, RESPONSE=None):
    """ HTTP PUT handler with marshalling support
    """
    if not REQUEST:
        REQUEST = self.REQUEST
    if not RESPONSE:
        RESPONSE = REQUEST.RESPONSE
    if not self.Schema().hasLayer('marshall'):
        RESPONSE.setStatus(501) # Not implemented
        return RESPONSE

    self.dav__init(REQUEST, RESPONSE)
    collection_check(self)

    self.dav__simpleifhandler(REQUEST, RESPONSE, refresh=1)
    is_new_object = self.checkCreationFlag()

    file = REQUEST.get('BODYFILE', _marker)
    if file is _marker:
        data = REQUEST.get('BODY', _marker)
        if data is _marker:
            raise AttributeError, 'REQUEST neither has a BODY nor a BODYFILE'
    else:
        data = ''
        file.seek(0)

    mimetype = REQUEST.get_header('content-type', None)
    # mimetype, if coming from request can be like:
    # text/plain; charset='utf-8'
    #
    # XXX we should really parse the extra params and pass them on as
    # keyword arguments.
    if mimetype is not None:
        mimetype = str(mimetype).split(';')[0].strip()

    filename = posixpath.basename(REQUEST.get('PATH_INFO', self.getId()))
    # XXX remove after we are using global services
    # use the request to find an object in the traversal hierachy that is
    # able to acquire a mimetypes_registry instance
    # This is a hack to avoid the acquisition problem on FTP/WebDAV object
    # creation
    parents = (self,) + tuple(REQUEST.get('PARENTS', ()))
    context = None
    for parent in parents:
        if getToolByName(parent, 'mimetypes_registry', None) is not None:
            context = parent
            break

    # Marshall the data
    marshaller = self.Schema().getLayerImpl('marshall')

    args = [self, data]
    kwargs = {'file':file,
              'context':context,
              'mimetype':mimetype,
              'filename':filename,
              'REQUEST':REQUEST,
              'RESPONSE':RESPONSE}
    ddata = mapply(marshaller.demarshall, *args, **kwargs)

    if (shasattr(self, 'demarshall_hook') and self.demarshall_hook):
        self.demarshall_hook(ddata)
    self.manage_afterPUT(data, marshall_data = ddata, **kwargs)
    self.reindexObject()
    self.unmarkCreationFlag()

    if is_new_object:
        event.notify(WebDAVObjectInitializedEvent(self))
    else:
        event.notify(WebDAVObjectEditedEvent(self))
    
    RESPONSE.setStatus(204)
    return RESPONSE

def markCreationFlag(self):
    """Sets flag on the instance to indicate that the object hasn't been
    saved properly (unset in content_edit).
    
    This will only be done if a REQUEST is present to ensure that objects
    created programmatically are considered fully created.
    """
    req = getattr(self, 'REQUEST', None)
    if shasattr(req, 'get'):
        if req.get('SCHEMA_UPDATE', None) is not None:
            return
        meth = req.get('REQUEST_METHOD', None)
        # Ensure that we have an HTTP request, if you're creating an
        # object with something other than a GET or POST, then we assume
        # you are making a complete object.
        if meth in ('GET', 'POST', 'PUT', 'MKCOL'):
            self._at_creation_flag = True

def MKCOL_handler(self, id, REQUEST=None, RESPONSE=None):
    """Hook into the MKCOL (make collection) process to call
    manage_afterMKCOL.
    """
    result = PortalFolder.MKCOL_handler(self, id, REQUEST, RESPONSE)
    new_folder = self._getOb(id)
    if new_folder is not None: # Could it have been renamed?
        new_folder.unmarkCreationFlag()
        event.notify(WebDAVObjectInitializedEvent(new_folder))
    self.manage_afterMKCOL(id, result, REQUEST, RESPONSE)
    return result
