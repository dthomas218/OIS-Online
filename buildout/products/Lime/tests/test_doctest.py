##############################################################################
#
# Lime - Link Marshaller
# Copyright(C), 2004-2007, Enfold Systems, Inc. - ALL RIGHTS RESERVED
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
##############################################################################
"""
$Id: test_doctest.py 7352 2007-07-24 01:59:26Z sidnei $
"""


# Load fixture
import unittest
from Testing import ZopeTestCase
from Testing.ZopeTestCase import doctest
from Testing.ZopeTestCase import FunctionalDocFileSuite as DocSuite

# Install our product
ZopeTestCase.installProduct('MimetypesRegistry')
ZopeTestCase.installProduct('PortalTransforms')
ZopeTestCase.installProduct('Archetypes')
ZopeTestCase.installProduct('Lime')
ZopeTestCase.installProduct('ATContentTypes')

from Products.CMFPlone.tests import PloneTestCase
from Products.Lime.tests.utils import installType

class TestATLink(PloneTestCase.FunctionalTestCase):

    def afterSetUp(self):
        self.loginAsPortalOwner()
        self.addProduct('PortalTransforms')
        self.addProduct('Archetypes')

        installType(self.portal,
                    'ATLink',
                    'ATContentTypes',
                    'Link',
                    global_allow=True)

class TestCMFLink(PloneTestCase.FunctionalTestCase):

    def afterSetUp(self):
        self.loginAsPortalOwner()
        self.addProduct('PortalTransforms')
        self.addProduct('Archetypes')

        # Install CMF Link as Link.
        pt = self.portal.portal_types
        if 'Link' in pt.objectIds():
            pt.manage_delObjects(ids=['Link'])
        pt.manage_addTypeInformation(
            id='Link',
            add_meta_type='Factory-based Type Information',
            typeinfo_name='CMFDefault: Link (Link)')

class TestATFavorite(PloneTestCase.FunctionalTestCase):

    def afterSetUp(self):
        self.loginAsPortalOwner()
        self.addProduct('PortalTransforms')
        self.addProduct('Archetypes')

        installType(self.portal,
                    'ATFavorite',
                    'ATContentTypes',
                    'Favorite',
                    global_allow=True)

def test_suite():
    suite = unittest.TestSuite()
    functional = [
        (TestATLink, 'export.txt'),
        # (TestCMFLink, 'export.txt'),
        (TestATFavorite, 'favorite.txt'),
        ]
    for test, f in functional:
        suite.addTest(DocSuite(f, test_class=test,
                               package='Products.Lime.tests',
                               globs=globals()))
    return suite
