######################################################################
#
# Extension Rename - Hook into Archetypes to enforce extension usage.
# Copyright(C), 2005, Enfold Systems, Inc. - ALL RIGHTS RESERVED
#
# This software is licensed under the Terms and Conditions contained
# within the LICENSE.txt file that accompanied this software.  Any
# inquiries concerning the scope or enforceability of the license should
# be addressed to:
#
# Enfold Systems, Inc.
# 4617 Montrose Blvd., Suite C215
# Houston, Texas 77006 USA
# p. +1 713.942.2377 | f. +1 832.201.8856
# www.enfoldsystems.com
# info@enfoldsystems.com
#
######################################################################
"""
$Id: test_functional.py 8833 2008-09-08 21:21:57Z sidnei $
"""

import os, sys

if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

# Load fixture
from Testing import ZopeTestCase
from Products.CMFPlone.tests import PloneTestCase

# Install our product
ZopeTestCase.installProduct('Marshall')
ZopeTestCase.installProduct('Calendaring')
ZopeTestCase.installProduct('PloneLockManager')
ZopeTestCase.installProduct('ShellExServer')
ZopeTestCase.installProduct('ExtensionRename')

from Products.CMFCore.utils import getToolByName

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
    """Functional Tests
    """

    def afterSetUp(self):
        PTC.afterSetUp(self)
        self.loginAsPortalOwner()
        self.addProduct('ShellExServer')

def test_suite():
    import unittest
    suite = unittest.TestSuite()
    from Testing.ZopeTestCase import doctest
    FileSuite = doctest.FunctionalDocFileSuite
    files = ['extensions.txt']
    for f in files:
        suite.addTest(FileSuite(f, test_class=FunctionalTest,
                                package='Products.ExtensionRename.tests'))
    return suite

if __name__ == '__main__':
    framework(descriptions=1, verbosity=1)
