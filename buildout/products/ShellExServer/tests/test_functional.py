# Enfold Desktop
# Copyright(C), 2004-2006, Enfold Systems, Inc. - ALL RIGHTS RESERVED

# Enfold Systems, Inc.
# 4617 Montrose Blvd., Suite C215
# Houston, Texas 77006 USA
# p. +1 713.942.2377 | f. +1 832.201.8856
# www.enfoldsystems.com
# info@enfoldsystems.com

# $Id: test_functional.py 8851 2008-09-17 20:05:21Z sidnei $
# $HeadURL: https://svn.enfoldsystems.com/internal/ShellExServer/trunk/tests/test_functional.py $

import os, sys

# Load fixture
from urlparse import urlparse, urlunparse
from Testing import ZopeTestCase
from Testing.ZopeTestCase.zopedoctest.functional import http as base_http
from Products.CMFPlone.tests import PloneTestCase

class ErrorResponseWrapper:

    def __init__(self, resp, error_resp):
        self.resp = resp
        self.error_resp = error_resp

    def __str__(self):
        return "%s\n\nError Response:\n\n%s" % (self.resp, self.error_resp)

def httpx(request_string, handle_errors=True):
    resp = base_http(request_string, handle_errors=handle_errors)
    error = resp.getHeader('X-Error-Log-Url')
    if error is not None:
        lines = request_string.splitlines()
        auth = [l for l in lines if l.startswith('Authorization')]
        if auth:
            s, h, p, par, q, f = urlparse(error)
            url = urlunparse(('', '', p, par, q, f))
            request_string = "\n".join(("",
                                       "GET %s HTTP/1.1" % url,
                                       auth[0],
                                       ""))
            error_resp = base_http(request_string, handle_errors=handle_errors)
            return ErrorResponseWrapper(resp, error_resp)
    return resp

# Install our product
ZopeTestCase.installProduct('PropertySets')
ZopeTestCase.installProduct('CMFPropertySets')
ZopeTestCase.installProduct('Calendaring')
ZopeTestCase.installProduct('DavPack')
ZopeTestCase.installProduct('PloneLockManager')
ZopeTestCase.installProduct('ShellExServer')
ZopeTestCase.installProduct('SiteAccess')

from Products.CMFCore.utils import getToolByName
from AccessControl import getSecurityManager
from AccessControl.SecurityManagement import setSecurityManager

class FTC(PloneTestCase.FunctionalTestCase):
    pass

try:
    FTC.addProduct
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
    FTC.addProduct = addProduct
    FTC.afterSetUp = afterSetUp
    FTC.loginAsPortalOwner = FTC.loginPortalOwner.im_func

class FunctionalTest(FTC):
    """Functional Tests for ShellExServer"""

    def afterSetUp(self):
        FTC.afterSetUp(self)
        self.loginAsPortalOwner()
        self.addProduct('CMFPropertySets')
        self.addProduct('ShellExServer')

def test_suite():
    import unittest
    suite = unittest.TestSuite()
    from Testing.ZopeTestCase import doctest
    FileSuite = doctest.FunctionalDocFileSuite
    files = [
        'desktop_command.txt',
        'session_root.txt',
        'dav_access.txt',
        'dav_put.txt',
        'error_message.txt',
        'locked_by.txt',
        'lock_behaviour.txt',
        'addables.txt',
        'ctr_predicates.txt',
        ]
    for f in files:
        suite.addTest(FileSuite(f, test_class=FunctionalTest,
                                package='Products.ShellExServer.tests',
                                optionflags=(doctest.ELLIPSIS |
                                             doctest.NORMALIZE_WHITESPACE |
                                             doctest.REPORT_UDIFF),
                                globs={'httpx':httpx},
                                ))
    try:
        from plone.app.linkintegrity.tests.layer import PloneLinkintegrity

        class LinkIntegrityFunctionalTest(FunctionalTest):
            layer = PloneLinkintegrity

        suite.addTest(FileSuite('link_integrity.txt', 
                                test_class=LinkIntegrityFunctionalTest,
                                package='Products.ShellExServer.tests',
                                optionflags=(doctest.ELLIPSIS |
                                             doctest.NORMALIZE_WHITESPACE |
                                             doctest.REPORT_UDIFF),
                                ))
    except ImportError:
        pass

    return suite
