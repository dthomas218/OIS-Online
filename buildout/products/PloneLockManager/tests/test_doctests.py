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
$Id: test_doctests.py 1662 2007-11-28 03:56:03Z sidnei $
"""
import os, sys

if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

# Load fixture
from Testing import ZopeTestCase
from Products.CMFPlone.tests import PloneTestCase
from Products.CMFCore.utils import getToolByName

# Install our product
ZopeTestCase.installProduct('DavPack')
ZopeTestCase.installProduct('PloneLockManager')

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

class FunctionalTest(ZopeTestCase.Functional, PTC):
    """Functional Tests for PloneLockManager
    """

    def afterSetUp(self):
        PTC.afterSetUp(self)
        self.loginAsPortalOwner()
        self.addProduct('PloneLockManager')

def test_suite():
    import unittest
    suite = unittest.TestSuite()
    from Testing.ZopeTestCase import doctest
    FileSuite = doctest.FunctionalDocFileSuite
    files = ['lock_behaviour.txt']
    for f in files:
        suite.addTest(FileSuite(f, test_class=FunctionalTest,
                                package='Products.PloneLockManager.tests'))
    return suite

if __name__ == '__main__':
    framework(descriptions=1, verbosity=1)
