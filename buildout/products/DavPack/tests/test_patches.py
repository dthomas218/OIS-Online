##############################################################################
#
# Copyright (c) 2004 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""
$Id: test_patches.py 2332 2008-09-26 21:15:22Z sidnei $
"""

import os, sys

if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

# Load fixture
import unittest
from Testing import ZopeTestCase
from Testing.ZopeTestCase import doctest
from Products.PloneTestCase import PloneTestCase
from OFS.Folder import Folder

ZopeTestCase.installProduct('PageTemplates')
ZopeTestCase.installProduct('DavPack')

class FunctionalTest(ZopeTestCase.Functional,
                     ZopeTestCase.ZopeTestCase):
    """A funcional test for PUT behavior"""


class BrokenPS(object):

    def dav__allprop(self):
        raise ValueError('Broken!')

    def dav__propnames(self):
        raise ValueError('Broken!')

    def dav__propstat(self, name, rdict):
        raise ValueError('Broken!')

class BrokenDAVCollection(Folder):

    def listDAVObjects(self):
        raise ValueError('Broken!')

def test_suite():
    suite = unittest.TestSuite()
    tests = [
        doctest.DocFileSuite(
            'RESPONSE.txt',
            package='Products.DavPack.tests',
            optionflags=(doctest.ELLIPSIS |
                         doctest.NORMALIZE_WHITESPACE)),
        doctest.FunctionalDocFileSuite(
            'PUT.txt',
            package='Products.DavPack.tests',
            test_class=FunctionalTest),
        doctest.FunctionalDocFileSuite(
            'PROPPATCH.txt',
            package='Products.DavPack.tests',
            test_class=FunctionalTest),
        doctest.FunctionalDocFileSuite(
            'PROPFIND.txt',
            package='Products.DavPack.tests',
            test_class=FunctionalTest),
        ]

    try:
        import Products.CMFEditions.subscriber
    except ImportError:
        tests.append(
            doctest.FunctionalDocFileSuite(
                'cmfeditions-webdav-history.txt',
                package='Products.DavPack.tests',
                test_class=PloneTestCase.FunctionalTestCase)
            )

    for t in tests:
        suite.addTest(t)
    return suite

if __name__ == '__main__':
    framework(descriptions=0, verbosity=1)
