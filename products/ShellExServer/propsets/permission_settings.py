# Enfold Desktop
# Copyright(C), 2004-2006, Enfold Systems, Inc. - ALL RIGHTS RESERVED


# Enfold Systems, Inc.
# 4617 Montrose Blvd., Suite C215
# Houston, Texas 77006 USA
# p. +1 713.942.2377 | f. +1 832.201.8856
# www.enfoldsystems.com
# info@enfoldsystems.com

# $Id: permission_settings.py 8184 2008-03-18 16:45:22Z sidnei $
# $HeadURL: https://svn.enfoldsystems.com/internal/ShellExServer/trunk/propsets/permission_settings.py $

from xml.dom import minidom

from Globals import InitializeClass
from Acquisition import aq_base, Implicit
from Products.PropertySets.PropertySetPredicate import PropertySetPredicate
from Products.PropertySets.PropertySetRegistry import registerPredicate
from Products.CMFCore.utils import getToolByName
from Products.CMFPropertySets.DynamicPropset import DynamicPropset

pm = (
    {'id':'permissions', 'type':'string', 'mode':'rw'},
    )

class PermissionSettings(DynamicPropset):
    """Permission Settings"""

    id='perm_settings'
    _md={'xmlns': 'http://enfoldtechnology.com/propsets/permission_settings'}
    _extensible = 0

    def dav__permissions(self):
        vself = self.v_self()
        settings = vself.permission_settings()
        valid_roles = vself.valid_roles()
        doc = minidom.Document()
        perms = doc.createElement('permissions')
        doc.appendChild(perms)
        for setting in settings:
            e = doc.createElement('permission')
            name = doc.createAttribute('name')
            name.nodeValue = setting['name']
            acquire = doc.createAttribute('acquire')
            acquire.nodeValue = setting['acquire'] == 'CHECKED' and '1' or '0'
            e.setAttributeNode(name)
            e.setAttributeNode(acquire)
            roles = doc.createElement('roles')
            e.appendChild(roles)
            perms.appendChild(e)
            for role_name, info in zip(valid_roles, setting['roles']):
                e = doc.createElement('role')
                name = doc.createAttribute('name')
                name.nodeValue = role_name
                checked = doc.createAttribute('checked')
                checked.nodeValue = info['checked'] == 'CHECKED' and '1' or '0'
                e.setAttributeNode(name)
                e.setAttributeNode(checked)
                roles.appendChild(e)
        return perms.toxml()

    def dav__set_permissions(self, xml):
        return None

    def _propertyMap(self):
        return pm

InitializeClass(PermissionSettings)

class PermissionSettingsPredicate(PropertySetPredicate):
    """ Expose permission settings for an object
    """

    _property_sets = (PermissionSettings(),)

registerPredicate('perm_settings',
                  'Permission Settings',
                  PermissionSettingsPredicate)
