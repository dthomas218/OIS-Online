# Enfold Desktop
# Copyright(C), 2004-2006, Enfold Systems, Inc. - ALL RIGHTS RESERVED

# Enfold Systems, Inc.
# 4617 Montrose Blvd., Suite C215
# Houston, Texas 77006 USA
# p. +1 713.942.2377 | f. +1 832.201.8856
# www.enfoldsystems.com
# info@enfoldsystems.com

# $Id: test_doctests.py 7720 2007-11-28 03:09:54Z sidnei $
# $HeadURL: https://svn.enfoldsystems.com/internal/ShellExServer/trunk/tests/test_doctests.py $

import os, sys

# Load fixture
from Testing import ZopeTestCase

def test_suite():
    import unittest
    from Testing.ZopeTestCase import doctest

    suite = unittest.TestSuite()

    try:
        from Products.PloneTestCase.layer import ZCML
        suite.layer = ZCML
    except ImportError:
        pass
    
    FileSuite = doctest.DocFileSuite
    files = [
        'normalization.txt',
        ]
    for f in files:
        suite.addTest(FileSuite(f, package='Products.ShellExServer.tests',
                                optionflags=(doctest.ELLIPSIS |
                                             doctest.NORMALIZE_WHITESPACE |
                                             doctest.REPORT_UDIFF),
                                ))
    return suite
