##############################################################################
#
# DavPack -- A set of patches for all things related to WebDAV
# Copyright (C) 2004 Enfold Systems
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
# Some portions of this module are Gregoire Webber and respective authors.
# The original copyright statement can be found on CMFEditionsLicense.txt.
#
##############################################################################
"""
$Id: __init__.py 839 2005-11-19 01:54:18Z sidnei $
"""

import zope.component
import zope.component.interface

from Products.CMFPlone.utils import base_hasattr
from Products.CMFCore.utils import getToolByName
from Products.CMFEditions.interfaces.IModifier import FileTooLargeToVersionError
from Products.CMFEditions.interfaces.IArchivist import ArchivistUnregisteredError

try:
    from Products.Archetypes.interfaces import IWebDAVObjectInitializedEvent
    from Products.Archetypes.interfaces import IWebDAVObjectEditedEvent
except ImportError:
    from Products.DavPack.at.webdav import IWebDAVObjectInitializedEvent
    from Products.DavPack.at.webdav import IWebDAVObjectEditedEvent

def isObjectChanged(obj):
    pr = getToolByName(obj, 'portal_repository')

    changed = False
    if not base_hasattr(obj, 'version_id'):
        changed = True
    else:
        try:
            changed = not pr.isUpToDate(obj, obj.version_id)
        except ArchivistUnregisteredError:
            # The object is not actually registered, but a version is
            # set, perhaps it was imported, or versioning info was
            # inappropriately destroyed
            changed = True
    return changed

def maybeSaveVersion(obj, policy='at_edit_autoversion', comment='', force=False):
    pr = getToolByName(obj, 'portal_repository')
    isVersionable = pr.isVersionable(obj)

    if isVersionable and (force or pr.supportsPolicy(obj, policy)):
        pr.save(obj=obj, comment=comment)

def webdavObjectEventHandler(event, comment):
    obj = event.object

    changed = isObjectChanged(obj)

    if not changed:
        return

    try:
        maybeSaveVersion(obj, comment=comment, force=False)
    except FileTooLargeToVersionError:
        pass # There's no way to emit a warning here. Or is there?

def webdavObjectInitialized(event):
    return webdavObjectEventHandler(event, comment='Initial revision')

def webdavObjectEdited(event):
    return webdavObjectEventHandler(event, comment='Edited (WebDAV)')

def registerSubscribers():
    zope.component.provideHandler(webdavObjectInitialized, 
                                  (IWebDAVObjectInitializedEvent,))
    zope.component.interface.provideInterface('', IWebDAVObjectInitializedEvent)
    zope.component.provideHandler(webdavObjectEdited, 
                                  (IWebDAVObjectEditedEvent,))
    zope.component.interface.provideInterface('', IWebDAVObjectEditedEvent)
