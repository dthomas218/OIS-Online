##############################################################################
#
# PloneLockManager -- Expose WebDAV Lock Management through a Plonish UI
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
##############################################################################
"""
$Id: tool.py 2372 2008-10-20 17:04:47Z sidnei $
"""

from DateTime import DateTime
from DateTime.interfaces import TimeError
from Globals import InitializeClass
from AccessControl import ClassSecurityInfo
from AccessControl import getSecurityManager

from webdav.Lockable import wl_isLocked
from webdav.LockItem import LockItem
from webdav.common import Locked
from webdav.WriteLockInterface import WriteLockInterface

from OFS.SimpleItem import SimpleItem
from OFS.PropertyManager import PropertyManager
from Products.CMFCore.utils import UniqueObject, getToolByName
from Products.CMFCore.interfaces.Dynamic import DynamicType as IDynamicType
from Products.PloneLockManager.config import TOOL_ID, TOOL_TYPE

try:
    from Products.CMFCore.permissions import ManagePortal
except:
    from Products.CMFCore.CMFCorePermissions import ManagePortal

def extractBasic(obj, path, context):
    if not wl_isLocked(obj):
        return

    if not IDynamicType.isImplementedBy(obj):
        return

    purl = getToolByName(context, 'portal_url')
    r = {}
    r['title_or_id'] = obj.Title().strip() or obj.getId()
    r['description'] = obj.Description()
    r['url'] = obj.absolute_url()
    r['path'] = purl.getRelativeContentURL(obj)
    r['icon'] = obj.getIcon()
    locks = obj.wl_lockValues()
    info = []
    for lock in locks:
        creator = lock.getCreator()
        if creator:
            db, creator = creator

        modified = lock.getModifiedTime()
        timeout = lock.getTimeout()

        try:
            timeout_t = DateTime(modified + timeout)
            modified_t = DateTime(modified)
        except TimeError:
            timeout_t = None
            modified_t = None

        i = {'creator':creator,
             'timeout':timeout_t,
             'modified':modified_t}

        info.append(i)
    r['info'] = info
    return r

class Collector:

    def __init__(self, context, extract=extractBasic):
        self.results = []
        self.context = context
        self.extract = extract

    def collect(self, obj, path):
        r = self.extract(obj, path, context=self.context)
        if r is not None:
            self.results.append(r)

    def __iter__(self):
        return iter(self.results)

def lock_owners(obj):
    if not WriteLockInterface.isImplementedBy(obj):
        return

    values = obj.wl_lockValues()
    if not values:
        return

    creators = []
    for lock in values:
        if lock.isValid():
            creator = lock.getCreator()
            if creator:
                # The user id without the path
                creators.append(creator[1])

    if not creators:
        return

    return creators

class LockingError(Exception): pass

class LockManager(UniqueObject, SimpleItem, PropertyManager):
    """Manage WebDAV locks, pretty much like the Lock Manager in
    Zope's Control Panel.
    """

    id = TOOL_ID
    meta_type = TOOL_TYPE
    toolicon = 'skins/plone_images/lock_icon.gif'
    default_lock_timeout = 0 # 0 means 'Use Zope Defaults'
    maximum_lock_timeout = 0 # 0 means 'Use Zope Defaults'

    _properties = (
        PropertyManager._properties + (
        {'id':'default_lock_timeout', 'type': 'int', 'mode': 'w'},
        {'id':'maximum_lock_timeout', 'type': 'int', 'mode': 'w'},
        ))

    manage_options = (
        PropertyManager.manage_options +
        SimpleItem.manage_options
        )

    security = ClassSecurityInfo()

    def Title(self):
        """ """
        return "Lock Manager"

    security.declareProtected(ManagePortal, 'findLockedObjects')
    def findLockedObjects(self, path=None):
        """Given a path, CMF-based locked objects below that path
        """
        purl = getToolByName(self, 'portal_url')
        catalog = getToolByName(self, 'portal_catalog')
        target = purl.getPortalObject()
        if path and path.startswith('/'):
            path = path[1:]
        if path:
            target = self.restrictedTraverse(path)
        collector = Collector(context=self)
        collector.collect(target, '/'.join(target.getPhysicalPath()))
        catalog.ZopeFindAndApply(obj=target, search_sub=True,
                                 apply_func=collector.collect)
        return collector.results

    security.declareProtected(ManagePortal, 'lockObject')
    def lockObject(self, obj, recurse=True, steal=True):
        purl = getToolByName(self, 'portal_url')
        path = purl.getRelativeContentURL(obj)

        if not WriteLockInterface.isImplementedBy(obj):
            raise LockingError, ('Not lockable: %s' % path)

        user = getSecurityManager().getUser()
        if wl_isLocked(obj):
            lockers = lock_owners(obj)
            if user.getId() not in lockers and not steal:
                raise LockingError, ('Cannot unlock %s: lock is held by %s' %
                                     (path, ', '.join(lockers)))
        timeout = 3600 # Default timeout for this method only, for
                       # historical reasons.
        default_timeout = self.getProperty('default_lock_timeout', 0)
        if default_timeout:
            timeout = default_timeout
        lock = LockItem(user, timeout=timeout)
        token = lock.getLockToken()
        obj.wl_setLock(token, lock)
        if recurse:
            def apply_lock(obj, path):
                self.lockObject(obj, recurse=recurse, steal=steal)
            catalog = getToolByName(self, 'portal_catalog')
            catalog.ZopeFindAndApply(obj=obj, search_sub=True,
                                     apply_func=apply_lock)

    security.declareProtected(ManagePortal, 'clearLocks')
    def clearLocks(self, paths):
        """Given a list of paths, clear all locks for those objects.
        """
        purl = getToolByName(self, 'portal_url')
        root = purl.getPortalObject()
        failed = []
        for path in paths:
            if path.startswith('/'):
                path = path[1:]
            if not path:
                failed.append(path)
            obj = root.restrictedTraverse(path, default=None)
            if obj is not None:
                obj.wl_clearLocks()
            else:
                failed.append(path)
        return failed

InitializeClass(LockManager)
