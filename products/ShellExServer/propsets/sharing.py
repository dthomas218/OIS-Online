# Enfold Desktop
# Copyright(C), 2004-5, Enfold Systems, Inc. - ALL RIGHTS RESERVED


# Enfold Systems, Inc.
# 4617 Montrose Blvd., Suite C215
# Houston, Texas 77006 USA
# p. +1 713.942.2377 | f. +1 832.201.8856
# www.enfoldsystems.com
# info@enfoldsystems.com

# $Id: sharing.py 8184 2008-03-18 16:45:22Z sidnei $
# $HeadURL: https://svn.enfoldsystems.com/internal/ShellExServer/trunk/propsets/sharing.py $

import logging

from sets import Set
from xml.dom import minidom

from Globals import InitializeClass
from Acquisition import aq_base, Implicit
from Products.PropertySets.PropertySetPredicate import PropertySetPredicate
from Products.PropertySets.PropertySetRegistry import registerPredicate
from Products.PropertySets.utils import site_encoding, nodeAttrValue
from Products.CMFCore.utils import getToolByName
from Products.CMFPropertySets.DynamicPropset import DynamicPropset

logger = logging.getLogger('ShellExServer')

def encodeInfo(ids, elm, node):
    doc = minidom.Document()
    sharing = doc.createElement('sharing')
    doc.appendChild(sharing)
    elm = doc.createElement(elm)
    for uid in ids:
        e = doc.createElement(node)
        name = doc.createAttribute('name')
        name.nodeValue = uid
        e.setAttributeNode(name)
        elm.appendChild(e)
    sharing.appendChild(elm)
    return sharing.toxml()

pm = (
    {'id':'users', 'type':'string', 'mode':'rw'},
    {'id':'groups', 'type':'string', 'mode':'rw'},
    )

class Sharing(DynamicPropset):
    """Sharing"""

    id='sharing'
    _md={'xmlns': 'http://enfoldtechnology.com/propsets/sharing'}
    _extensible = 0

    def _getInfo(self):
        vself = self.v_self()
        share_info = vself.users_with_local_role('Owner')
        # GRUF Implementation detail:
        #   Groups are prefixed with 'group_'.
        group_ids = [uid for uid in share_info
                     if uid.startswith('group_')]
        user_ids = [uid for uid in share_info
                    if uid not in group_ids]
        # Strip 'group_' part
        group_ids = [uid[6:] for uid in group_ids]
        # PAS Implementation detail:
        #  Groups are not prefixed. We have to try looking up a group
        #  by that name.
        uf = getToolByName(vself, 'acl_users')
        if uf.meta_type in ('Pluggable Auth Service',):
            for uid in user_ids:
                try:
                    if uf.getGroup(uid):
                        user_ids.remove(uid)
                        group_ids.append(uid)
                except (RuntimeError,):
                    # Can happen with AD plugin if domain is
                    # unreachable.
                    logger.exception('Error fetching group: %r', uid)
                    break
        return (user_ids, group_ids)

    def dav__users(self):
        uids, gids = self._getInfo()
        return encodeInfo(uids, 'users', 'user')

    def dav__groups(self):
        uids, gids = self._getInfo()
        return encodeInfo(gids, 'groups', 'group')

    def _set_sharing(self, uids=None, gids=None):
        vself = self.v_self()
        _uids, _gids = self._getInfo()
        if uids is None:
            uids = _uids
        if gids is None:
            gids = _gids
        new_ids = Set(uids + ['group_%s' % g for g in gids])
        old_ids = Set(vself.users_with_local_role('Owner'))
        add = new_ids - old_ids
        remove = old_ids - new_ids
        for r in remove:
            roles = vself.get_local_roles_for_userid(r)
            new_roles = list(Set(roles) - Set(['Owner']))
            if new_roles:
                vself.manage_setLocalRoles(r, new_roles)
            else:
                vself.manage_delLocalRoles([r])
        for a in add:
            roles = vself.get_local_roles_for_userid(a)
            roles = Set(roles)
            roles.add('Owner')
            new_roles = list(roles)
            vself.manage_setLocalRoles(a, new_roles)

    def _parse(self, node, value, encoding):
        return nodeAttrValue(node, 'name', value, encoding)

    def dav__set_users(self, value):
        vself = self.v_self()
        enc = site_encoding(vself)
        ids = self._parse('user', value, enc)
        self._set_sharing(uids=ids)

    def dav__set_groups(self, value):
        vself = self.v_self()
        enc = site_encoding(vself)
        ids = self._parse('group', value, enc)
        self._set_sharing(gids=ids)

    def _propertyMap(self):
        return pm

InitializeClass(Sharing)

class SharingPredicate(PropertySetPredicate):
    """ Expose sharing information
    """

    _property_sets = (Sharing(),)

    def apply(self, obj):
        """ Check for 'users_with_local_role' (RoleManager).
        """
        if not hasattr(aq_base(obj), 'users_with_local_role'):
            return ()
        return PropertySetPredicate.apply(self, obj)

registerPredicate('sharing',
                  'Sharing Information',
                  SharingPredicate)
