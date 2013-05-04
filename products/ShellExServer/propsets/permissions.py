# Enfold Desktop
# Copyright(C), 2004-2006, Enfold Systems, Inc. - ALL RIGHTS RESERVED


# Enfold Systems, Inc.
# 4617 Montrose Blvd., Suite C215
# Houston, Texas 77006 USA
# p. +1 713.942.2377 | f. +1 832.201.8856
# www.enfoldsystems.com
# info@enfoldsystems.com

# $Id: permissions.py 8184 2008-03-18 16:45:22Z sidnei $
# $HeadURL: https://svn.enfoldsystems.com/internal/ShellExServer/trunk/propsets/permissions.py $

from xml.dom import minidom

from zExceptions import Unauthorized
from webdav.WriteLockInterface import WriteLockInterface
from Globals import InitializeClass
from Acquisition import aq_base, Implicit
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.utils import _checkPermission
from Products.CMFPropertySets.DynamicPropset import DynamicPropset
from Products.PageTemplates.Expressions import getEngine
from Products.PropertySets.PropertySetPredicate import PropertySetPredicate
from Products.PropertySets.PropertySetRegistry import registerPredicate
from Products.ShellExServer.permissions import ShareObject
from Products.ShellExServer.utils import getRecords

class Expression:

    text = ''
    expression = None
    debug = False

    def __init__(self, text):
        self.text = text
        self.expression = getEngine().compile(text)

    def __call__(self, target):
        context = getEngine().getContext({'object':target})
        try:
            res = self.expression(context)
        except Unauthorized:
            return False
        if isinstance(res, Exception):
            if self.debug:
                raise res
            return False
        return res

pm = (
    {'id':'read',  'type':'boolean', 'mode':'r'},
    {'id':'write', 'type':'boolean', 'mode':'r'},
    {'id':'share', 'type':'boolean', 'mode':'r'},
    {'id':'locked_by', 'type':'string', 'mode':'r'},
    )

class Permissions(DynamicPropset):
    """Permissions"""

    id='permissions'
    _md={'xmlns': 'http://enfoldtechnology.com/propsets/permissions'}
    _extensible = 0
    _can_read = Expression("python: getattr(object.aq_explicit, "
                           "'manage_DAVget', None) is not None")
    _can_write = Expression("python: getattr(object.aq_explicit, "
                            "'PUT', None) is not None")

    def dav__read(self):
        vself = self.v_self()
        return self._can_read(vself)

    def dav__write(self):
        vself = self.v_self()
        return self._can_write(vself)

    def dav__share(self):
        vself = self.v_self()
        return bool(_checkPermission(ShareObject, vself))

    def dav__locked_by(self):
        vself = self.v_self()
        owners = []
        if WriteLockInterface.isImplementedBy(vself):
            mt = getToolByName(vself, 'portal_membership', None)
            locks = vself.wl_lockValues(killinvalids=1)
            for lock in locks:
                db, name = lock.getCreator()
                # XXX Might need to handle clashing user ids in nested
                # user folders at some point.
                if mt is None:
                    # Get acl_users and then get the user.
                    acl = vself.unrestrictedTraverse('/'.join(db))
                    user = acl.getUserById(name)
                    name = fullname = user.getUserName()
                else:
                    # Use the membership tool api
                    member = mt.getMemberById(name)
                    name = member.getUserName()
                    fullname = member.getProperty('fullname', '') or name
                owners.append({'id': name, 'name': fullname})

        owners.sort()
        return getRecords(owners)

    def _propertyMap(self):
        return pm

InitializeClass(Permissions)

class PermissionsPredicate(PropertySetPredicate):
    """ Expose permissions for an object in terms
    of read/write. This is done by mapping groups of
    permissions under the hood and checking all of them.
    """

    _property_sets = (Permissions(),)

registerPredicate('permissions',
                  'Permissions',
                  PermissionsPredicate)
