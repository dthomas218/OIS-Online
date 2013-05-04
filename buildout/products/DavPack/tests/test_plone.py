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
$Id: test_plone.py 1661 2007-11-28 03:50:27Z sidnei $
"""

import os, sys

if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

# Load fixture
import unittest
from Testing import ZopeTestCase
from Testing.ZopeTestCase import doctest
from Products.CMFPlone.tests import PloneTestCase

from cStringIO import StringIO
from Products.CMFPlone.tests import dummy

ZopeTestCase.installProduct('PageTemplates')
ZopeTestCase.installProduct('DavPack')

from zExceptions.ExceptionFormatter import format_exception
from ZPublisher.HTTPResponse import HTTPResponse

# Silence Plone's handling of exceptions
orig_exception = HTTPResponse.exception
def exception(self, **kw):
    def tag_search(*args):
        return False
    kw['tag_search'] = tag_search
    return orig_exception(self, **kw)

orig_setBody = HTTPResponse.setBody
def setBody(self, *args, **kw):
    kw['is_error'] = 0
    if len(args[0]) == 2:
        title, body = args[0]
        args = (body,) + args[1:]
    return orig_setBody(self, *args, **kw)

def _traceback(self, t, v, tb, as_html=1):
    return ''.join(format_exception(t, v, tb, as_html=as_html))

HTTPResponse._error_format = 'text/plain'
HTTPResponse._traceback = _traceback
HTTPResponse.exception = exception
HTTPResponse.setBody = setBody

default_user = ZopeTestCase.user_name
default_password = ZopeTestCase.user_password

html = """\
<html>
<head><title>Foo</title></head>
<body>Bar</body>
</html>
"""

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

class TestPUTObjects(FTC):
    # PUT objects into Plone including special cases like index_html.
    # Confirms fix for http://plone.org/collector/1375

    def afterSetUp(self):
        FTC.afterSetUp(self)
        self.basic_auth = '%s:%s' % (default_user, default_password)
        self.portal_path = self.portal.absolute_url(1)
        self.folder_path = self.folder.absolute_url(1)

    def testPUTDocument(self):
        # Create a new document via FTP/DAV
        response = self.publish(self.folder_path+'/new_html',
                                env={'CONTENT_TYPE': 'text/html'},
                                request_method='PUT',
                                stdin=StringIO(html),
                                basic=self.basic_auth)

        self.assertEqual(response.getStatus(), 201)
        self.failUnless('new_html' in self.folder.objectIds())
        # XXX Give up on testing HTML upload, Plone is broken.
        # self.assertEqual(self.folder.new_html.EditableBody(), 'Bar')
        self.failUnless('Document' in self.folder.new_html.meta_type)

    def testPUTIndexHtmlDocument(self):
        # Create an index_html document via FTP/DAV
        response = self.publish(self.folder_path+'/index_html',
                                env={'CONTENT_TYPE': 'text/html'},
                                request_method='PUT',
                                stdin=StringIO(html),
                                basic=self.basic_auth)

        self.assertEqual(response.getStatus(), 201, response.getBody())
        self.failUnless('index_html' in self.folder.objectIds())
        # XXX Give up on testing HTML upload, Plone is broken.
        # self.assertEqual(self.folder.index_html.EditableBody(), 'Bar')
        self.failUnless('Document' in self.folder.index_html.meta_type)

    def testPUTImage(self):
        # Create a new image via FTP/DAV
        response = self.publish(self.folder_path+'/new_image',
                                env={'CONTENT_TYPE': 'image/gif'},
                                request_method='PUT',
                                stdin=StringIO(dummy.GIF),
                                basic=self.basic_auth)

        self.assertEqual(response.getStatus(), 201)
        self.failUnless('new_image' in self.folder.objectIds())
        self.assertEqual(str(self.folder.new_image.data), dummy.GIF)
        self.assertEqual(self.folder.new_image.portal_type, 'Image')

    def testPUTIndexHtmlImage(self):
        # Create a new image named index_html via FTP/DAV
        response = self.publish(self.folder_path+'/index_html',
                                env={'CONTENT_TYPE': 'image/gif'},
                                request_method='PUT',
                                stdin=StringIO(dummy.GIF),
                                basic=self.basic_auth)

        self.assertEqual(response.getStatus(), 201)
        self.failUnless('index_html' in self.folder.objectIds())
        self.assertEqual(str(self.folder.index_html.data), dummy.GIF)
        self.assertEqual(self.folder.index_html.portal_type, 'Image')

    def testPUTDocumentIntoPortal(self):
        # Create a new document in the portal via FTP/DAV
        self.setRoles(['Manager'])

        response = self.publish(self.portal_path+'/new_html',
                                env={'CONTENT_TYPE': 'text/html'},
                                request_method='PUT',
                                stdin=StringIO(html),
                                basic=self.basic_auth)

        self.assertEqual(response.getStatus(), 201)
        self.failUnless('new_html' in self.portal.objectIds())
        # XXX Give up on testing HTML upload, Plone is broken.
        # self.assertEqual(self.portal.new_html.EditableBody(), 'Bar')
        self.failUnless('Document' in self.portal.new_html.meta_type)

    def testPUTIndexHtmlDocumentIntoPortal(self):
        # Create an index_html document in the portal via FTP/DAV
        self.setRoles(['Manager'])

        response = self.publish(self.portal_path+'/index_html',
                                env={'CONTENT_TYPE': 'text/html'},
                                request_method='PUT',
                                stdin=StringIO(html),
                                basic=self.basic_auth)

        self.assertEqual(response.getStatus(), 201)
        self.failUnless('index_html' in self.portal.objectIds())
        # XXX Give up on testing HTML upload, Plone is broken.
        # self.assertEqual(self.portal.index_html.EditableBody(), 'Bar')
        self.failUnless('Document' in self.portal.index_html.meta_type)


class TestDAVOperations(FTC):
    # MOVE/COPY objects inside Plone including special cases like index_html.

    def afterSetUp(self):
        FTC.afterSetUp(self)
        self.setRoles(['Manager'])
        self.basic_auth = '%s:%s' % (default_user,
                                     default_password)
        self.portal_path = self.portal.absolute_url(1)
        self.folder_path = self.folder.absolute_url(1)

    def test_document_move(self):
        self.folder.invokeFactory('Document', 'new_html')
        self.folder.invokeFactory('Folder', 'sub')

        # Move document into a different name in the subfolder
        dest = self.folder_path + '/sub/doc-in-subfolder'
        response = self.publish(self.folder_path + '/new_html',
                                env={'DESTINATION': dest},
                                request_method='MOVE',
                                stdin=StringIO(''),
                                basic=self.basic_auth)

        self.assertEqual(response.getStatus(), 201, response.getBody())

        # Make sure it got moved
        self.failIf('new_html' in self.folder.objectIds())
        self.failUnless('doc-in-subfolder' in self.folder.sub.objectIds())

    def test_document_move_index_html_non_exist_folder(self):
        self.folder.invokeFactory('Document', 'new_html')
        self.folder.invokeFactory('Folder', 'sub')

        self.failIf('index_html' in self.folder.sub.objectIds())

        # Move document into a different name in the subfolder
        dest = self.folder_path + '/sub/index_html'
        response = self.publish(self.folder_path + '/new_html',
                                env={'DESTINATION': dest},
                                request_method='MOVE',
                                stdin=StringIO(''),
                                basic=self.basic_auth)

        self.assertEqual(response.getStatus(), 201, response.getBody())

        # Make sure it got moved
        self.failIf('new_html' in self.folder.objectIds())
        self.failUnless('index_html' in self.folder.sub.objectIds())

    def test_document_move_index_html_exist_folder(self):
        self.folder.invokeFactory('Document', 'new_html')
        self.folder.invokeFactory('Folder', 'sub')
        self.folder.sub.invokeFactory('Document', 'index_html')

        self.failUnless('index_html' in self.folder.sub.objectIds())

        # Move document into a different name in the subfolder
        dest = self.folder_path + '/sub/index_html'
        response = self.publish(self.folder_path + '/new_html',
                                env={'DESTINATION': dest,
                                     'OVERWRITE': 'T'},
                                request_method='MOVE',
                                stdin=StringIO(''),
                                basic=self.basic_auth)

        self.assertEqual(response.getStatus(), 204, response.getBody())

        # Make sure it got moved
        self.failIf('new_html' in self.folder.objectIds())
        self.failUnless('index_html' in self.folder.sub.objectIds())

    def test_document_move_index_html_non_exist_portal(self):
        self.folder.invokeFactory('Document', 'new_html')

        if 'index_html' in self.portal.objectIds():
            self.portal.manage_delObjects('index_html')

        self.failIf('index_html' in self.portal.objectIds())

        # Move document into a different name in the subfolder
        dest = self.portal_path + '/index_html'
        response = self.publish(self.folder_path + '/new_html',
                                env={'DESTINATION': dest},
                                request_method='MOVE',
                                stdin=StringIO(''),
                                basic=self.basic_auth)

        self.assertEqual(response.getStatus(), 201, response.getBody())

        # Make sure it got moved
        self.failIf('new_html' in self.folder.objectIds())
        self.failUnless('index_html' in self.portal.objectIds())

    def test_document_move_index_html_exist_portal(self):
        self.folder.invokeFactory('Document', 'new_html')

        if 'index_html' not in self.portal.objectIds():
            self.portal.invokeFactory('Document', 'index_html')

        self.failUnless('index_html' in self.portal.objectIds())

        # Move document into a different name in the subfolder
        dest = self.portal_path + '/index_html'
        response = self.publish(self.folder_path + '/new_html',
                                env={'DESTINATION': dest,
                                     'OVERWRITE': 'T'},
                                request_method='MOVE',
                                stdin=StringIO(''),
                                basic=self.basic_auth)

        self.assertEqual(response.getStatus(), 204, response.getBody())

        # Make sure it got moved
        self.failIf('new_html' in self.folder.objectIds())
        self.failUnless('index_html' in self.portal.objectIds())

    def test_document_copy(self):
        self.folder.invokeFactory('Document', 'new_html')
        self.folder.invokeFactory('Folder', 'sub')

        # COPY document into a different name in the subfolder
        dest = self.folder_path + '/sub/doc-in-subfolder'
        response = self.publish(self.folder_path + '/new_html',
                                env={'DESTINATION': dest},
                                request_method='COPY',
                                stdin=StringIO(''),
                                basic=self.basic_auth)

        self.assertEqual(response.getStatus(), 201, response.getBody())

        # Make sure it got copied
        self.failUnless('new_html' in self.folder.objectIds())
        self.failUnless('doc-in-subfolder' in self.folder.sub.objectIds())


    def test_document_copy_index_html_non_exist_folder(self):
        self.folder.invokeFactory('Document', 'new_html')
        self.folder.invokeFactory('Folder', 'sub')

        self.failIf('index_html' in self.folder.sub.objectIds())

        # Copy document into a different name in the subfolder
        dest = self.folder_path + '/sub/index_html'
        response = self.publish(self.folder_path + '/new_html',
                                env={'DESTINATION': dest},
                                request_method='COPY',
                                stdin=StringIO(''),
                                basic=self.basic_auth)

        self.assertEqual(response.getStatus(), 201, response.getBody())

        # Make sure it got copied
        self.failUnless('new_html' in self.folder.objectIds())
        self.failUnless('index_html' in self.folder.sub.objectIds())

    def test_document_copy_index_html_exist_folder(self):
        self.folder.invokeFactory('Document', 'new_html')
        self.folder.invokeFactory('Folder', 'sub')
        self.folder.sub.invokeFactory('Document', 'index_html')

        self.failUnless('index_html' in self.folder.sub.objectIds())

        # Copy document into a different name in the subfolder
        dest = self.folder_path + '/sub/index_html'
        response = self.publish(self.folder_path + '/new_html',
                                env={'DESTINATION': dest,
                                     'OVERWRITE': 'T'},
                                request_method='COPY',
                                stdin=StringIO(''),
                                basic=self.basic_auth)

        self.assertEqual(response.getStatus(), 204, response.getBody())

        # Make sure it got copied
        self.failUnless('new_html' in self.folder.objectIds())
        self.failUnless('index_html' in self.folder.sub.objectIds())

    def test_document_copy_index_html_non_exist_portal(self):
        self.folder.invokeFactory('Document', 'new_html')

        if 'index_html' in self.portal.objectIds():
            self.portal.manage_delObjects('index_html')

        self.failIf('index_html' in self.portal.objectIds())

        # Copy document into a different name in the subfolder
        dest = self.portal_path + '/index_html'
        response = self.publish(self.folder_path + '/new_html',
                                env={'DESTINATION': dest},
                                request_method='COPY',
                                stdin=StringIO(''),
                                basic=self.basic_auth)

        self.assertEqual(response.getStatus(), 201, response.getBody())

        # Make sure it got copied
        self.failUnless('new_html' in self.folder.objectIds())
        self.failUnless('index_html' in self.portal.objectIds())

    def test_document_copy_index_html_exist_portal(self):
        self.folder.invokeFactory('Document', 'new_html')

        if 'index_html' not in self.portal.objectIds():
            self.portal.invokeFactory('Document', 'index_html')

        self.failUnless('index_html' in self.portal.objectIds())

        # Copy document into a different name in the subfolder
        dest = self.portal_path + '/index_html'
        response = self.publish(self.folder_path + '/new_html',
                                env={'DESTINATION': dest,
                                     'OVERWRITE': 'T'},
                                request_method='COPY',
                                stdin=StringIO(''),
                                basic=self.basic_auth)

        self.assertEqual(response.getStatus(), 204, response.getBody())

        # Make sure it got copied
        self.failUnless('new_html' in self.folder.objectIds())
        self.failUnless('index_html' in self.portal.objectIds())

    def test_document_propfind_index_html_non_exist_folder(self):
        self.folder.invokeFactory('Folder', 'sub')
        self.failIf('index_html' in self.folder.sub.objectIds())

        # Do a PROPFIND on folder/index_html, this needs to result in a NotFound.
        response = self.publish(self.folder_path + '/sub/index_html',
                                env={},
                                request_method='PROPFIND',
                                stdin=StringIO(''),
                                basic=self.basic_auth)

        self.assertEqual(response.getStatus(), 404, response.getBody())

    def test_document_propfind_index_html_exist_folder(self):
        self.folder.invokeFactory('Folder', 'sub')
        self.folder.sub.invokeFactory('Document', 'index_html')
        self.failUnless('index_html' in self.folder.sub.objectIds())

        # Do a PROPFIND on folder/index_html, this needs to result in a 207
        response = self.publish(self.folder_path + '/sub/index_html',
                                env={},
                                request_method='PROPFIND',
                                stdin=StringIO(''),
                                basic=self.basic_auth)

        self.assertEqual(response.getStatus(), 207, response.getBody())

    def test_document_propfind_index_html_non_exist_portal(self):
        if 'index_html' in self.portal.objectIds():
            self.portal.manage_delObjects('index_html')

        self.failIf('index_html' in self.portal.objectIds())

        # Do a PROPFIND on portal/index_html, this needs to result in a NotFound.
        response = self.publish(self.portal_path + '/index_html',
                                env={},
                                request_method='PROPFIND',
                                stdin=StringIO(''),
                                basic=self.basic_auth)

        self.assertEqual(response.getStatus(), 404, response.getBody())

    def test_document_propfind_index_html_exist_portal(self):
        if 'index_html' not in self.portal.objectIds():
            self.portal.invokeFactory('Document', 'index_html')

        self.failUnless('index_html' in self.portal.objectIds())

        # Do a PROPFIND on folder/index_html, this needs to result in a 207
        response = self.publish(self.portal_path + '/index_html',
                                env={},
                                request_method='PROPFIND',
                                stdin=StringIO(''),
                                basic=self.basic_auth)

        self.assertEqual(response.getStatus(), 207, response.getBody())

def test_suite():
    suite = unittest.TestSuite()
    tests = [
        doctest.FunctionalDocFileSuite(
        'PlonePUT.txt',
        'PlonePROPPATCH.txt',
        package='Products.DavPack.tests',
        test_class=FTC),
        ]
    for t in tests:
        suite.addTest(t)
    suite.addTest(unittest.makeSuite(TestPUTObjects))
    suite.addTest(unittest.makeSuite(TestDAVOperations))
    return suite

if __name__ == '__main__':
    framework(descriptions=0, verbosity=1)
