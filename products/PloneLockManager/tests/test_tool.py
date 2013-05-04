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
$Id: test_tool.py 1662 2007-11-28 03:56:03Z sidnei $
"""

import os, sys

if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

# Load fixture
import unittest
from Testing import ZopeTestCase
from Testing.ZopeTestCase import doctest
from Products.CMFPlone.tests import PloneTestCase
from Products.CMFCore.utils import getToolByName
from Products.PloneLockManager.config import *
from Products.PloneLockManager.tool import Collector

ZopeTestCase.installProduct(PROJECTNAME)

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
    def afterSetUp(self):
        self.portal.aq_parent.aq_inner.plone = self.portal
        self.portal.id = 'plone'
    PTC.afterSetUp = afterSetUp
    PTC.addProduct = addProduct
    PTC.loginAsPortalOwner = PTC.loginPortalOwner.im_func

class ToolTest(PTC):

    def afterSetUp(self):
        PTC.afterSetUp(self)
        self.addProduct('PloneLockManager')
        self.tool = getToolByName(self.portal, TOOL_ID)
        self.loginAsPortalOwner()

    def test_no_locks(self):
        self.assertEquals(list(self.tool.findLockedObjects()), [])

    def test_lock_simple(self):
        self.portal.invokeFactory('Document', 'test1',
                                  title='Test Document',
                                  description='Document Description')
        self.tool.lockObject(self.portal.test1)
        locked = list(self.tool.findLockedObjects())
        self.assertEquals(len(locked), 1)

        lock = locked[0]
        self.assertEquals(lock['path'], 'test1')
        self.assertEquals(lock['title_or_id'], 'Test Document')
        self.assertEquals(lock['description'], 'Document Description')
        self.assertEquals(len(lock['info']), 1)

        info = lock['info'][0]
        self.assertEquals(info['creator'], 'portal_owner')
        timeout = int(round((info['timeout'] - info['modified']) * 86400))
        self.assertEquals(timeout, 3600)
        self.assertEquals(lock['icon'], 'plone/document_icon.gif')
        self.failUnless(lock['url'].endswith('/plone/test1'))

        self.tool.clearLocks(paths=['test1'])
        locked = list(self.tool.findLockedObjects())
        self.assertEquals(len(locked), 0)

    def test_lock_non_cmf(self):
        self.portal.manage_addFile('test1')
        obj = self.portal.test1
        self.tool.lockObject(obj)
        self.failUnless(obj.wl_isLocked())
        locked = list(self.tool.findLockedObjects())
        self.assertEquals(len(locked), 0)

    def test_locked_folder(self):
        self.portal.invokeFactory('Folder', 'sub')
        sub = self.portal.sub
        sub.invokeFactory('Document', 'test1')
        obj = self.portal.sub.test1
        locked = list(self.tool.findLockedObjects())
        self.assertEquals(len(locked), 0)
        self.tool.lockObject(sub, recurse=True)
        locked = list(self.tool.findLockedObjects())
        self.assertEquals(len(locked), 2)
        locked = list(self.tool.findLockedObjects(path='sub'))
        self.assertEquals(len(locked), 2)

    def test_path(self):
        self.portal.invokeFactory('Folder', 'sub')
        sub = self.portal.sub
        sub.invokeFactory('Document', 'test1')
        obj = self.portal.sub.test1
        locked = list(self.tool.findLockedObjects())
        self.assertEquals(len(locked), 0)
        self.tool.lockObject(obj)
        locked = list(self.tool.findLockedObjects())
        self.assertEquals(len(locked), 1)
        self.portal.invokeFactory('Folder', 'sub2')
        locked = list(self.tool.findLockedObjects(path='sub2'))
        self.assertEquals(len(locked), 0)
        locked = list(self.tool.findLockedObjects(path='sub'))
        self.assertEquals(len(locked), 1)
        locked = list(self.tool.findLockedObjects(path='/sub'))
        self.assertEquals(len(locked), 1)

        failed = self.tool.clearLocks(paths=['/sub/test1'])
        self.assertEquals(failed, [])
        locked = list(self.tool.findLockedObjects())
        self.assertEquals(len(locked), 0)

        failed = self.tool.clearLocks(paths=['/foo/bar'])
        self.assertEquals(failed, ['foo/bar'])
        locked = list(self.tool.findLockedObjects())
        self.assertEquals(len(locked), 0)


data = [
    {'id':'test1',
     'title':'Test 1'},
    {'id':'test2',
     'title':'Test 2'},
    {'id':'test3',
     'title':'Test 3'},
    ]

def test_extract(obj, path, context):
    return (obj['id'], obj['title'])

class CollectorTest(unittest.TestCase):

    def test_collector(self):
        collector = Collector(context=None, extract=test_extract)
        for o in data:
            collector.collect(o, path=o['id'])
        expected = [(o['id'], o['title']) for o in data]
        self.assertEquals(list(iter(collector)), expected)

def test_suite():
    suite = unittest.TestSuite()
    tests = [
        ToolTest,
        CollectorTest
        ]
    for t in tests:
        suite.addTest(unittest.makeSuite(t))
    return suite

if __name__ == '__main__':
    framework(descriptions=0, verbosity=1)
