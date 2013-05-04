# Enfold Desktop
# Copyright(C), 2004-2006, Enfold Systems, Inc. - ALL RIGHTS RESERVED

# Enfold Systems, Inc.
# 4617 Montrose Blvd., Suite C215
# Houston, Texas 77006 USA
# p. +1 713.942.2377 | f. +1 832.201.8856
# www.enfoldsystems.com
# info@enfoldsystems.com

# $Id: test_propsets.py 8589 2008-06-24 17:02:32Z sidnei $
# $HeadURL: https://svn.enfoldsystems.com/internal/ShellExServer/trunk/tests/test_propsets.py $

import os, sys

# Load fixture
from Testing import ZopeTestCase
from Products.CMFPlone.tests import PloneTestCase

from AccessControl import getSecurityManager
from AccessControl.SecurityManagement import setSecurityManager

class PTC(PloneTestCase.PloneTestCase):
    pass

try:
    PTC.addProduct
except AttributeError: # Plone 2.1
    def addProduct(self, name):
        '''Quickinstalls a product into the site.'''
        sm = getSecurityManager()
        self.loginPortalOwner()
        try:
            qi = self.portal.portal_quickinstaller
            if not qi.isProductInstalled(name):
                qi.installProduct(name)
                self._refreshSkinData()
        finally:
            setSecurityManager(sm)
    PTC.addProduct = addProduct
    PTC.loginAsPortalOwner = PTC.loginPortalOwner.im_func

# Install our product
ZopeTestCase.installProduct('Marshall')
ZopeTestCase.installProduct('PropertySets')
ZopeTestCase.installProduct('CMFPropertySets')
ZopeTestCase.installProduct('ShellExServer')

try:
    from Products.CMFCore.permissions import View
except:
    from Products.CMFCore.CMFCorePermissions import View

from cStringIO import StringIO
from Products.ShellExServer.propsets.sharing import encodeInfo
from Products.CMFCore.utils import getToolByName
from Products.PropertySets.utils import site_encoding
from Products.PropertySets.utils import nodeAttrValue, nodeChildrenInfo
from Products.PropertySets import PropertySetRegistry
from Products.PropertySets import manage_addPropertySetRegistry, \
     manage_addPropertySetPredicate
tool_id = PropertySetRegistry.PropertySetRegistry.id
add_registry = manage_addPropertySetRegistry
add_predicate = manage_addPropertySetPredicate

class FakeResponse:

    def __init__(self):
        self.out = StringIO()
        self.write = self.out.write
        self.getvalue = self.out.getvalue

    def enableHTTPCompression(self, *args): pass
    def setHeader(self, *args, **kw): pass

class TestFSAttrs(PTC):

    def afterSetUp(self):
        self.loginAsPortalOwner()
        self.addProduct('Marshall')
        self.addProduct('ShellExServer')
        self.mt = self.portal.portal_membership
        self.acl_users = self.portal.acl_users

    def test_document(self):
        self.portal.invokeFactory('Document', id='test')
        doc = self.portal.test
        psets = dict(doc.propertysheets.items())
        self.failUnless('fsattrs' in psets)
        dc = psets['fsattrs']
        items = dict(dc.propertyItems())
        self.failUnless('hidden' in items)
        self.failUnless('executable' in items)
        self.assertEquals(items['hidden'], False)
        dc._updateProperty('hidden', True)
        items = dict(dc.propertyItems())
        self.assertEquals(items['hidden'], True)
        self.assertEquals(items['executable'], False)
        dc._updateProperty('executable', True)
        items = dict(dc.propertyItems())
        self.assertEquals(items['executable'], True)

    def test_hiddenDocument(self):
        self.portal.invokeFactory('Document', id='.test')
        doc = self.portal['.test']
        psets = dict(doc.propertysheets.items())
        self.failUnless('fsattrs' in psets)
        dc = psets['fsattrs']
        items = dict(dc.propertyItems())
        self.failUnless('hidden' in items)
        self.assertEquals(items['hidden'], True)
        dc._updateProperty('hidden', False)
        items = dict(dc.propertyItems())
        self.assertEquals(items['hidden'], False)
        dc._updateProperty('hidden', True)
        items = dict(dc.propertyItems())
        self.assertEquals(items['hidden'], True)

    def test_folder(self):
        self.portal.invokeFactory('Folder', id='test')
        doc = self.portal.test
        psets = dict(doc.propertysheets.items())
        self.failUnless('fsattrs' in psets)
        dc = psets['fsattrs']
        items = dict(dc.propertyItems())
        self.failUnless('hidden' in items)
        self.failUnless('executable' in items)
        self.assertEquals(items['hidden'], False)
        dc._updateProperty('hidden', True)
        items = dict(dc.propertyItems())
        self.assertEquals(items['hidden'], True)
        self.assertEquals(items['executable'], False)
        dc._updateProperty('executable', True)
        items = dict(dc.propertyItems())
        self.assertEquals(items['executable'], True)

    def test_hiddenFolder(self):
        self.portal.invokeFactory('Folder', id='.test')
        doc = self.portal['.test']
        psets = dict(doc.propertysheets.items())
        self.failUnless('fsattrs' in psets)
        dc = psets['fsattrs']
        items = dict(dc.propertyItems())
        self.failUnless('hidden' in items)
        self.assertEquals(items['hidden'], True)
        dc._updateProperty('hidden', False)
        items = dict(dc.propertyItems())
        self.assertEquals(items['hidden'], False)
        dc._updateProperty('hidden', True)
        items = dict(dc.propertyItems())
        self.assertEquals(items['hidden'], True)

class TestPermissionSettings(PTC):

    def afterSetUp(self):
        self.loginAsPortalOwner()
        self.addProduct('Marshall')
        self.addProduct('ShellExServer')
        self.mt = self.portal.portal_membership
        self.acl_users = self.portal.acl_users
        tool = getToolByName(self.portal, tool_id)
        add_predicate(tool, id='perm_settings',
                      expression='',
                      permission=View,
                      REQUEST=None)

    def test_document(self):
        self.portal.invokeFactory('Document', id='test')
        doc = self.portal.test
        psets = dict(doc.propertysheets.items())
        self.failUnless('perm_settings' in psets)
        dc = psets['perm_settings']
        items = dict(dc.propertyItems())
        self.failUnless('permissions' in items)
        self.failUnless(items['permissions'])

    def test_folder(self):
        self.portal.invokeFactory('Folder', id='test')
        doc = self.portal.test
        psets = dict(doc.propertysheets.items())
        self.failUnless('perm_settings' in psets)
        dc = psets['perm_settings']
        items = dict(dc.propertyItems())
        self.failUnless('permissions' in items)
        self.failUnless(items['permissions'])

class TestPermissions(PTC):

    def afterSetUp(self):
        self.loginAsPortalOwner()
        self.addProduct('Marshall')
        self.addProduct('ShellExServer')
        self.mt = self.portal.portal_membership
        self.acl_users = self.portal.acl_users
        self.acl_users.userFolderAddUser('user1', 'secret',
                                         ['Member'], [])

    def test_document(self):
        self.portal.invokeFactory('Document', id='test')
        doc = self.portal.test
        psets = dict(doc.propertysheets.items())
        self.failUnless('permissions' in psets)
        dc = psets['permissions']
        items = dict(dc.propertyItems())
        self.failUnless('read' in items)
        self.assertEquals(items['read'], True)
        self.failUnless('write' in items)
        self.assertEquals(items['write'], True)
        self.failUnless('share' in items)
        self.assertEquals(items['share'], True)

        # Now logout and make sure user can't read, write or share
        # content.
        self.logout()
        items = dict(dc.propertyItems())
        self.failUnless('read' in items)
        self.assertEquals(items['read'], False)
        self.failUnless('write' in items)
        self.assertEquals(items['write'], False)
        self.failUnless('share' in items)
        self.assertEquals(items['share'], False)

        # And then login as a Member and check that it can read but
        # not write or share.
        self.login('user1')
        items = dict(dc.propertyItems())
        self.failUnless('read' in items)
        self.assertEquals(items['read'], True)
        self.failUnless('write' in items)
        self.assertEquals(items['write'], False)
        self.failUnless('share' in items)
        self.assertEquals(items['share'], False)

    def test_folder(self):
        self.portal.invokeFactory('Folder', id='test')
        doc = self.portal.test
        psets = dict(doc.propertysheets.items())
        self.failUnless('permissions' in psets)
        dc = psets['permissions']
        items = dict(dc.propertyItems())
        self.failUnless('read' in items)
        self.assertEquals(items['read'], True)
        self.failUnless('write' in items)
        self.assertEquals(items['write'], True)
        self.failUnless('share' in items)
        self.assertEquals(items['share'], True)

        # Now logout and make sure user can't read, write or share
        # content.
        self.logout()
        items = dict(dc.propertyItems())
        self.failUnless('read' in items)
        self.assertEquals(items['read'], False)
        self.failUnless('write' in items)
        self.assertEquals(items['write'], False)
        self.failUnless('share' in items)
        self.assertEquals(items['share'], False)

        # And then login as a Member and check that it can read but
        # not write or share.
        self.login('user1')
        items = dict(dc.propertyItems())
        self.failUnless('read' in items)
        self.assertEquals(items['read'], True)
        self.failUnless('write' in items)
        self.assertEquals(items['write'], False)
        self.failUnless('share' in items)
        self.assertEquals(items['share'], False)

class TestSharing(PTC):

    def afterSetUp(self):
        self.loginAsPortalOwner()
        self.addProduct('Marshall')
        self.addProduct('ShellExServer')
        self.mt = self.portal.portal_membership
        if not self.mt.getMemberareaCreationFlag():
            _ = self.mt.setMemberareaCreationFlag()
        self.acl_users = self.portal.acl_users
        self.gt = self.portal.portal_groups
        if not self.gt.getGroupWorkspacesCreationFlag():
            self.gt.toggleGroupWorkspacesCreation()
        self.gt.addGroup('group1', roles = ['Member',], )
        self.gt.addGroup('group2', roles = ['Member',], )
        self.acl_users.userFolderAddUser('user1', 'secret',
                                         ['Member'], [], groups=['group1'])
        self.acl_users.userFolderAddUser('user2', 'secret',
                                         ['Member'], [], groups=['group2'])
        self.mt.createMemberArea('user1')
        self.mt.createMemberArea('user2')

    def _sharingInfo(self, data):
        info = {}
        enc = site_encoding(self.portal)
        info['groups'] = nodeAttrValue('group', 'name', data, enc)
        info['users'] = nodeAttrValue('user', 'name', data, enc)
        return info

    def test_document(self):
        self.portal.invokeFactory('Document', id='test')
        doc = self.portal.test
        psets = dict(doc.propertysheets.items())
        self.failUnless('sharing' in psets)
        dc = psets['sharing']
        items = dict(dc.propertyItems())
        self.failUnless('users' in items)
        data = items['users']
        info = self._sharingInfo(data)
        self.assertEquals(info.get('users'), ['portal_owner'])
        self.assertEquals(info.get('groups'), [])
        self.failUnless('groups' in items)
        data = items['groups']
        info = self._sharingInfo(data)
        self.assertEquals(info.get('users'), [])
        self.assertEquals(info.get('groups'), [])

        # Now try to set it
        user_ids = ['portal_owner', 'user1']
        group_ids = ['group2']
        xml = encodeInfo(user_ids, 'users', 'user')
        dc._updateProperty('users', xml)
        items = dict(dc.propertyItems())
        data = items['users']
        info = self._sharingInfo(data)
        self.assertEquals(info.get('users'), ['portal_owner', 'user1'])
        self.assertEquals(info.get('groups'), [])
        data = items['groups']
        info = self._sharingInfo(data)
        self.assertEquals(info.get('users'), [])
        self.assertEquals(info.get('groups'), [])

        xml = encodeInfo(group_ids, 'groups', 'group')
        dc._updateProperty('groups', xml)
        items = dict(dc.propertyItems())
        data = items['users']
        info = self._sharingInfo(data)
        self.assertEquals(info.get('users'), ['portal_owner', 'user1'])
        self.assertEquals(info.get('groups'), [])
        data = items['groups']
        info = self._sharingInfo(data)
        self.assertEquals(info.get('users'), [])
        self.assertEquals(info.get('groups'), ['group2'])

    def test_folder(self):
        self.portal.invokeFactory('Folder', id='test')
        doc = self.portal.test
        psets = dict(doc.propertysheets.items())
        self.failUnless('sharing' in psets)
        dc = psets['sharing']
        items = dict(dc.propertyItems())
        self.failUnless('users' in items)
        data = items['users']
        info = self._sharingInfo(data)
        self.assertEquals(info.get('users'), ['portal_owner'])
        self.assertEquals(info.get('groups'), [])
        self.failUnless('groups' in items)
        data = items['groups']
        info = self._sharingInfo(data)
        self.assertEquals(info.get('users'), [])
        self.assertEquals(info.get('groups'), [])

        # Now try to set it
        user_ids = ['portal_owner', 'user1']
        group_ids = ['group2']
        xml = encodeInfo(user_ids, 'users', 'user')
        dc._updateProperty('users', xml)
        items = dict(dc.propertyItems())
        data = items['users']
        info = self._sharingInfo(data)
        self.assertEquals(info.get('users'), ['portal_owner', 'user1'])
        self.assertEquals(info.get('groups'), [])
        data = items['groups']
        info = self._sharingInfo(data)
        self.assertEquals(info.get('users'), [])
        self.assertEquals(info.get('groups'), [])

        xml = encodeInfo(group_ids, 'groups', 'group')
        dc._updateProperty('groups', xml)
        items = dict(dc.propertyItems())
        data = items['users']
        info = self._sharingInfo(data)
        self.assertEquals(info.get('users'), ['portal_owner', 'user1'])
        self.assertEquals(info.get('groups'), [])
        data = items['groups']
        info = self._sharingInfo(data)
        self.assertEquals(info.get('users'), [])
        self.assertEquals(info.get('groups'), ['group2'])

    def test_home_folder1(self):
        doc = self.mt.getHomeFolder(id='user1')
        self.failIf(doc is None)
        psets = dict(doc.propertysheets.items())
        self.failUnless('sharing' in psets)
        dc = psets['sharing']
        items = dict(dc.propertyItems())
        self.failUnless('users' in items)
        data = items['users']
        info = self._sharingInfo(data)
        self.assertEquals(info.get('users'), ['user1'])
        self.assertEquals(info.get('groups'), [])

        # Now try to set it
        user_ids = ['portal_owner', 'user1']
        group_ids = ['group2']
        xml = encodeInfo(user_ids, 'users', 'user')
        dc._updateProperty('users', xml)
        items = dict(dc.propertyItems())
        data = items['users']
        info = self._sharingInfo(data)
        self.assertEquals(info.get('users'), ['portal_owner', 'user1'])
        self.assertEquals(info.get('groups'), [])
        data = items['groups']
        info = self._sharingInfo(data)
        self.assertEquals(info.get('users'), [])
        self.assertEquals(info.get('groups'), [])

        xml = encodeInfo(group_ids, 'groups', 'group')
        dc._updateProperty('groups', xml)
        items = dict(dc.propertyItems())
        data = items['users']
        info = self._sharingInfo(data)
        self.assertEquals(info.get('users'), ['portal_owner', 'user1'])
        self.assertEquals(info.get('groups'), [])
        data = items['groups']
        info = self._sharingInfo(data)
        self.assertEquals(info.get('users'), [])
        self.assertEquals(info.get('groups'), ['group2'])

    def test_home_folder2(self):
        doc = self.mt.getHomeFolder(id='user2')
        self.failIf(doc is None)
        psets = dict(doc.propertysheets.items())
        self.failUnless('sharing' in psets)
        dc = psets['sharing']
        items = dict(dc.propertyItems())
        self.failUnless('users' in items)
        data = items['users']
        info = self._sharingInfo(data)
        self.assertEquals(info.get('users'), ['user2'])
        self.assertEquals(info.get('groups'), [])

        # Now try to set it
        user_ids = ['portal_owner', 'user1']
        group_ids = ['group2']
        xml = encodeInfo(user_ids, 'users', 'user')
        dc._updateProperty('users', xml)
        items = dict(dc.propertyItems())
        data = items['users']
        info = self._sharingInfo(data)
        self.assertEquals(info.get('users'), ['portal_owner', 'user1'])
        self.assertEquals(info.get('groups'), [])
        data = items['groups']
        info = self._sharingInfo(data)
        self.assertEquals(info.get('users'), [])
        self.assertEquals(info.get('groups'), [])

        xml = encodeInfo(group_ids, 'groups', 'group')
        dc._updateProperty('groups', xml)
        items = dict(dc.propertyItems())
        data = items['users']
        info = self._sharingInfo(data)
        self.assertEquals(info.get('users'), ['portal_owner', 'user1'])
        self.assertEquals(info.get('groups'), [])
        data = items['groups']
        info = self._sharingInfo(data)
        self.assertEquals(info.get('users'), [])
        self.assertEquals(info.get('groups'), ['group2'])

    def test_group_folder1(self):
        doc = self.gt.getGroupareaFolder(id='group1')
        psets = dict(doc.propertysheets.items())
        self.failUnless('sharing' in psets)
        dc = psets['sharing']
        items = dict(dc.propertyItems())
        self.failUnless('users' in items)
        data = items['users']
        info = self._sharingInfo(data)
        self.assertEquals(info.get('users'), [])
        self.assertEquals(info.get('groups'), [])
        data = items['groups']
        info = self._sharingInfo(data)
        self.assertEquals(info.get('users'), [])
        self.assertEquals(info.get('groups'), ['group1'])

        # Now try to set it
        user_ids = ['portal_owner', 'user1']
        group_ids = ['group2', 'group1']
        xml = encodeInfo(user_ids, 'users', 'user')
        dc._updateProperty('users', xml)
        items = dict(dc.propertyItems())
        data = items['users']
        info = self._sharingInfo(data)
        self.assertEquals(info.get('users'), ['portal_owner', 'user1'])
        self.assertEquals(info.get('groups'), [])
        data = items['groups']
        info = self._sharingInfo(data)
        self.assertEquals(info.get('users'), [])
        self.assertEquals(info.get('groups'), ['group1'])

        xml = encodeInfo(group_ids, 'groups', 'group')
        dc._updateProperty('groups', xml)
        items = dict(dc.propertyItems())
        data = items['users']
        info = self._sharingInfo(data)
        self.assertEquals(info.get('users'), ['portal_owner', 'user1'])
        self.assertEquals(info.get('groups'), [])
        data = items['groups']
        info = self._sharingInfo(data)
        self.assertEquals(info.get('users'), [])
        self.assertEquals(info.get('groups'), ['group2', 'group1'])

    def test_group_folder2(self):
        doc = self.gt.getGroupareaFolder(id='group2')
        psets = dict(doc.propertysheets.items())
        self.failUnless('sharing' in psets)
        dc = psets['sharing']
        items = dict(dc.propertyItems())
        self.failUnless('users' in items)
        data = items['users']
        info = self._sharingInfo(data)
        self.assertEquals(info.get('users'), [])
        self.assertEquals(info.get('groups'), [])
        data = items['groups']
        info = self._sharingInfo(data)
        self.assertEquals(info.get('users'), [])
        self.assertEquals(info.get('groups'), ['group2'])

        # Now try to set it
        user_ids = ['portal_owner', 'user1']
        group_ids = ['group1', 'group2']
        xml = encodeInfo(user_ids, 'users', 'user')
        dc._updateProperty('users', xml)
        items = dict(dc.propertyItems())
        data = items['users']
        info = self._sharingInfo(data)
        self.assertEquals(info.get('users'), ['portal_owner', 'user1'])
        self.assertEquals(info.get('groups'), [])
        data = items['groups']
        info = self._sharingInfo(data)
        self.assertEquals(info.get('users'), [])
        self.assertEquals(info.get('groups'), ['group2'])

        xml = encodeInfo(group_ids, 'groups', 'group')
        dc._updateProperty('groups', xml)
        items = dict(dc.propertyItems())
        data = items['users']
        info = self._sharingInfo(data)
        self.assertEquals(info.get('users'), ['portal_owner', 'user1'])
        self.assertEquals(info.get('groups'), [])
        data = items['groups']
        info = self._sharingInfo(data)
        self.assertEquals(info.get('users'), [])
        self.assertEquals(info.get('groups'), ['group2', 'group1'])

    def test_portal(self):
        portal = self.portal
        psets = dict(portal.propertysheets.items())
        self.failUnless('sharing' in psets)
        dc = psets['sharing']
        items = dict(dc.propertyItems())
        self.failUnless('users' in items)
        data = items['users']
        info = self._sharingInfo(data)
        self.assertEquals(info.get('users'), ['portal_owner'])
        self.assertEquals(info.get('groups'), [])

        # Now try to set it
        user_ids = ['portal_owner', 'user1']
        group_ids = ['group2']
        xml = encodeInfo(user_ids, 'users', 'user')
        dc._updateProperty('users', xml)
        items = dict(dc.propertyItems())
        data = items['users']
        info = self._sharingInfo(data)
        self.assertEquals(info.get('users'), ['portal_owner', 'user1'])
        self.assertEquals(info.get('groups'), [])
        data = items['groups']
        info = self._sharingInfo(data)
        self.assertEquals(info.get('users'), [])
        self.assertEquals(info.get('groups'), [])

        xml = encodeInfo(group_ids, 'groups', 'group')
        dc._updateProperty('groups', xml)
        items = dict(dc.propertyItems())
        data = items['users']
        info = self._sharingInfo(data)
        self.assertEquals(info.get('users'), ['portal_owner', 'user1'])
        self.assertEquals(info.get('groups'), [])
        data = items['groups']
        info = self._sharingInfo(data)
        self.assertEquals(info.get('users'), [])
        self.assertEquals(info.get('groups'), ['group2'])

class TestVocabulary(PTC):

    def afterSetUp(self):
        self.loginAsPortalOwner()
        self.addProduct('Marshall')
        self.addProduct('CMFPropertySets')
        self.addProduct('ShellExServer')
        self.mt = self.portal.portal_membership
        self.acl_users = self.portal.acl_users
        self.gt = self.portal.portal_groups
        self.gt.addGroup('group1', roles = ['Member',], )
        self.gt.addGroup('group2', roles = ['Member',], )
        self.acl_users.userFolderAddUser('user1', 'secret',
                                         ['Member'], [], groups=['group1'])
        self.acl_users.userFolderAddUser('user2', 'secret',
                                         ['Member'], [], groups=['group2'])

    def _getVocabs(self, data):
        enc = site_encoding(self.portal)
        return nodeChildrenInfo('vocab', ('ns', 'propid'),
                                'term', ('label', 'value'),
                                data, enc)

    def DISABLEDtest_subject_vocab(self):
        portal = self.portal
        portal.invokeFactory('Document', 'test')
        doc = portal.test
        psets = dict(doc.propertysheets.items())
        vocab = portal.vocabulary
        out = FakeResponse()
        vocab.manage_DAVget(RESPONSE=out)
        self.failUnless(out.getvalue())
        vocabs = self._getVocabs(out.getvalue())
        ns = 'http://cmf.zope.org/propsets/dublincore'
        propid = 'subject'
        key = (ns, propid)
        self.failIf(key in vocabs.keys())

        # Now, modify and check that we get the
        # expected values.
        subs = ('CMF', 'Plone', 'Zope')
        dc = psets['dublincore']
        dc._updateProperty('subject', subs)
        out = FakeResponse()
        vocab.manage_DAVget(RESPONSE=out)
        self.failUnless(out.getvalue())
        vocabs = self._getVocabs(out.getvalue())
        self.failUnless(key in vocabs.keys())
        self.failUnless(vocabs.get(key))
        expected = zip(subs, subs)
        expected.sort()
        got = vocabs.get(key)
        got.sort()
        self.assertEquals(got, expected)

    def test_langs_vocab(self):
        portal = self.portal
        portal.invokeFactory('Document', 'test')
        doc = portal.test
        psets = dict(doc.propertysheets.items())
        vocab = portal.vocabulary
        out = FakeResponse()
        vocab.manage_DAVget(RESPONSE=out)
        self.failUnless(out.getvalue())
        vocabs = self._getVocabs(out.getvalue())
        ns = 'http://cmf.zope.org/propsets/dublincore'
        propid = 'language'
        key = (ns, propid)
        self.failUnless(key in vocabs.keys())
        langs = vocabs.get(key)
        self.failUnless(langs)
        self.failUnless(('Language neutral (site default)', '') in langs)
        self.failUnless(('Portuguese', 'pt') in langs)
        self.failUnless(('English', 'en') in langs)
        self.failUnless(('Afrikaans', 'af') in langs)

    def test_formats_vocab(self):
        portal = self.portal
        portal.invokeFactory('Document', 'test')
        doc = portal.test
        psets = dict(doc.propertysheets.items())
        vocab = portal.vocabulary
        out = FakeResponse()
        vocab.manage_DAVget(RESPONSE=out)
        self.failUnless(out.getvalue())
        vocabs = self._getVocabs(out.getvalue())
        ns = 'http://cmf.zope.org/propsets/dublincore'
        propid = 'format'
        key = (ns, propid)
        self.failUnless(key in vocabs.keys())
        formats = vocabs.get(key)
        self.failUnless(formats)
        self.failUnless(('message/rfc822', 'message/rfc822') in formats, formats)
        self.failUnless(('image/png', 'image/png') in formats, formats)
        self.failUnless(('image/jpeg', 'image/jpeg') in formats, formats)
        self.failUnless(('application/octet-stream',
                         'application/octet-stream') in formats, formats)

    def test_users_vocab(self):
        portal = self.portal
        portal.invokeFactory('Document', 'test')
        doc = portal.test
        psets = dict(doc.propertysheets.items())
        vocab = portal.vocabulary
        out = FakeResponse()
        vocab.manage_DAVget(RESPONSE=out)
        self.failUnless(out.getvalue())
        vocabs = self._getVocabs(out.getvalue())
        ns = 'http://enfoldtechnology.com/propsets/sharing'
        propid = 'users'
        key = (ns, propid)
        self.failUnless(key in vocabs.keys())
        users = vocabs.get(key)
        self.failUnless(users)
        self.failUnless(('user1', 'user1') in users, users)
        self.failUnless(('user2', 'user2') in users, users)

    def test_groups_vocab(self):
        portal = self.portal
        portal.invokeFactory('Document', 'test')
        doc = portal.test
        psets = dict(doc.propertysheets.items())
        vocab = portal.vocabulary
        out = FakeResponse()
        vocab.manage_DAVget(RESPONSE=out)
        self.failUnless(out.getvalue())
        vocabs = self._getVocabs(out.getvalue())
        ns = 'http://enfoldtechnology.com/propsets/sharing'
        propid = 'groups'
        key = (ns, propid)
        self.failUnless(key in vocabs.keys())
        users = vocabs.get(key)
        self.failUnless(users)
        self.failUnless(('group1', 'group1') in users, users)
        self.failUnless(('group2', 'group2') in users, users)

    def test_actions_vocab(self):
        portal = self.portal
        portal.invokeFactory('Document', 'test')
        doc = portal.test
        psets = dict(doc.propertysheets.items())
        self.failUnless('vocabulary' in psets)
        voc = psets['vocabulary']
        items = dict(voc.propertyItems())
        self.failUnless('vocabulary' in items)
        data = items['vocabulary']
        self.failUnless(data)
        vocabs = self._getVocabs(data)
        ns = 'http://enfoldtechnology.com/vocabs/actions'
        propid = 'actions'
        key = (ns, propid)
        self.failUnless(key in vocabs.keys())
        actions = vocabs.get(key)
        self.failUnless(actions)
        self.failUnless(('View in Browser', 'test/') in actions, actions)

    def test_transitions_vocab(self):
        portal = self.portal
        portal.invokeFactory('Document', 'test')
        doc = portal.test
        psets = dict(doc.propertysheets.items())
        self.failUnless('vocabulary' in psets)
        voc = psets['vocabulary']
        items = dict(voc.propertyItems())
        self.failUnless('vocabulary' in items)
        data = items['vocabulary']
        self.failUnless(data)
        vocabs = self._getVocabs(data)
        ns = 'http://cmf.zope.org/propsets/dcworkflow'
        propid = 'review_state'
        key = (ns, propid)
        self.failUnless(key in vocabs.keys())
        trans = vocabs.get(key)
        self.failUnless(trans)
        self.failUnless(('Make private', 'hide') in trans, trans)
        self.failUnless('submit' in [id for title, id in trans], trans)
        self.failUnless(('Publish', 'publish') in trans, trans)

        # Now change workflow state and recheck
        dc = psets['dcworkflow']
        items = dict(dc.propertyItems())
        self.failUnless('review_state' in items)
        self.assertEquals(items['review_state'], 'visible')
        dc._updateProperty('review_state', 'publish')
        items = dict(voc.propertyItems())
        self.failUnless('vocabulary' in items)
        data = items['vocabulary']
        self.failUnless(data)
        vocabs = self._getVocabs(data)
        ns = 'http://cmf.zope.org/propsets/dcworkflow'
        propid = 'review_state'
        key = (ns, propid)
        self.failUnless(key in vocabs.keys())
        trans = vocabs.get(key)
        self.failUnless(trans)
        self.failUnless(('Retract', 'retract') in trans, trans)
        self.failUnless('reject' in [id for title, id in trans], trans)


def test_suite():
    import unittest
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestVocabulary))
    suite.addTest(unittest.makeSuite(TestPermissionSettings))
    suite.addTest(unittest.makeSuite(TestPermissions))
    suite.addTest(unittest.makeSuite(TestSharing))
    suite.addTest(unittest.makeSuite(TestFSAttrs))
    return suite
