import os, sys
from xml.sax.saxutils import escape, quoteattr

if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

# Load fixture
import unittest
from Testing import ZopeTestCase

# Install our product
ZopeTestCase.installProduct('DavPack')
ZopeTestCase.installProduct('PropertySets')
ZopeTestCase.installProduct('CMFPropertySets')

from Products.CMFPlone.tests import PloneTestCase

from cStringIO import StringIO
from ZPublisher.HTTPRequest import HTTPRequest
from ZPublisher.HTTPResponse import HTTPResponse
from webdav.davcmds import PropPatch, PropFind
from Products.CMFPropertySets.VocabularyProvider import Template
from Products.CMFCore.utils import getToolByName
from Products.PropertySets.utils import site_encoding

def make_request(stdout=None, **kw):
    if stdout is None:
        stdout = StringIO()
    resp = HTTPResponse(stdout=stdout)
    env = dict(kw)
    env['SERVER_NAME']='foo'
    env['SERVER_PORT']='80'
    env['REQUEST_METHOD'] = 'GET'
    body = StringIO()
    if env.get('BODY'):
        body.write(env['BODY'])
        del env['BODY']
    req = HTTPRequest(sys.stdin, env, resp)
    req._file = body
    return req

PROPPATCH_XML="""<?xml version="1.0" encoding="utf-8"?>
<d:propertyupdate xmlns:d="DAV:"
xmlns:z="%(ns)s">
<d:set>
<d:prop>
<z:%(propname)s>%(propvalue)s</z:%(propname)s>
</d:prop>
</d:set>
</d:propertyupdate>
"""

PROPSTAT_XML="""<?xml version="1.0" encoding="utf-8"?>
<DAV:propfind xmlns:DAV="DAV:"
xmlns:%(prefix)s="%(ns)s">
<DAV:prop><%(prefix)s:%(propname)s/></DAV:prop>
</DAV:propfind>"""

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

class TestDCWorkflowSet(PTC):

    def afterSetUp(self):
        self.loginAsPortalOwner()
        self.addProduct('CMFPropertySets')
        self.mt = self.portal.portal_membership
        self.acl_users = self.portal.acl_users

    def test_document(self):
        self.portal.invokeFactory('Document', id='test')
        doc = self.portal.test
        psets = dict(doc.propertysheets.items())
        self.failUnless('dcworkflow' in psets)
        dc = psets['dcworkflow']
        items = dict(dc.propertyItems())
        self.failUnless('review_state' in items)
        self.assertEquals(items['review_state'], 'visible')
        dc._updateProperty('review_state', 'publish')
        items = dict(dc.propertyItems())
        self.assertEquals(items['review_state'], 'published')
        dc._updateProperty('review_state', 'retract')
        items = dict(dc.propertyItems())
        self.assertEquals(items['review_state'], 'visible')

    def test_folder(self):
        self.portal.invokeFactory('Folder', id='test')
        folder = self.portal.test
        psets = dict(folder.propertysheets.items())
        self.failUnless('dcworkflow' in psets)
        dc = psets['dcworkflow']
        items = dict(dc.propertyItems())
        self.failUnless('review_state' in items)
        self.assertEquals(items['review_state'], 'visible')
        dc._updateProperty('review_state', 'publish')
        items = dict(dc.propertyItems())
        self.assertEquals(items['review_state'], 'published')
        dc._updateProperty('review_state', 'retract')
        items = dict(dc.propertyItems())
        self.assertEquals(items['review_state'], 'visible')

class TestDublinCoreSet(PTC):

    def afterSetUp(self):
        self.loginAsPortalOwner()
        self.addProduct('CMFPropertySets')
        self.mt = self.portal.portal_membership
        self.acl_users = self.portal.acl_users

    def test_document(self):
        self.portal.invokeFactory('Document', id='test')
        doc = self.portal.test
        psets = dict(doc.propertysheets.items())
        self.failUnless('dublincore' in psets)
        dc = psets['dublincore']
        dav = dict(psets['webdav'].propertyItems())
        items = dict(dc.propertyItems())
        self.failUnless('title' in items)
        self.failUnless('description' in items)
        self.failUnless('creator' in items)
        self.failUnless('subject' in items)
        self.failUnless('publisher' in items)
        self.failUnless('date' in items)
        self.failUnless('creationdate' in items)
        self.failUnless('effectivedate' in items)
        self.failUnless('expirationdate' in items)
        self.failUnless('modificationdate' in items)
        self.failUnless('type' in items)
        self.failUnless('format' in items)
        self.failUnless('identifier' in items)
        self.failUnless('language' in items)
        self.failUnless('rights' in items)
        self.assertEquals(items['title'], '')
        dc._updateProperty('title', 'Stupid Title')
        items = dict(dc.propertyItems())
        self.assertEquals(items['title'], 'Stupid Title')
        self.assertEquals(items['description'], '')
        dc._updateProperty('description', 'Some Description')
        items = dict(dc.propertyItems())
        self.assertEquals(items['description'], 'Some Description')
        self.assertEquals(items['subject'], ())
        self.assertEquals(items['contributors'], ())
        self.assertEquals(items['creator'], 'portal_owner')
        self.assertEquals(items['type'], 'Page') # This is the type title!
        self.assertEquals(items['format'], 'text/html')
        self.assertEquals(items['language'], '')
        self.assertEquals(items['rights'], '')
        # XXX webdav creationdate is hardcoded because Zope by default
        # doesn't keep a creation date.
        # self.assertEquals(items['creationdate'], dav['creationdate'])
        self.failUnless('Z' in items['creationdate'],
                        items['creationdate'])
        self.failUnless('Z' in items['modificationdate'],
                        items['modificationdate'])
        # XXX This *may* be true sometimes, but cannot be guaranteed.
        # self.assertEquals(items['modificationdate'], dav['getlastmodified'])

    def test_folder(self):
        self.portal.invokeFactory('Folder', id='test')
        doc = self.portal.test
        psets = dict(doc.propertysheets.items())
        self.failUnless('dublincore' in psets)
        dc = psets['dublincore']
        items = dict(dc.propertyItems())
        self.failUnless('title' in items)
        self.failUnless('description' in items)
        self.failUnless('creator' in items)
        self.failUnless('subject' in items)
        self.failUnless('publisher' in items)
        self.failUnless('date' in items)
        self.failUnless('creationdate' in items)
        self.failUnless('effectivedate' in items)
        self.failUnless('expirationdate' in items)
        self.failUnless('modificationdate' in items)
        self.failUnless('type' in items)
        self.failUnless('format' in items)
        self.failUnless('identifier' in items)
        self.failUnless('language' in items)
        self.failUnless('rights' in items)
        self.assertEquals(items['title'], '')
        dc._updateProperty('title', 'Stupid Title')
        items = dict(dc.propertyItems())
        self.assertEquals(items['title'], 'Stupid Title')
        self.assertEquals(items['description'], '')
        dc._updateProperty('description', 'Some Description')
        items = dict(dc.propertyItems())
        self.assertEquals(items['description'], 'Some Description')
        self.assertEquals(items['subject'], ())
        self.assertEquals(items['contributors'], ())
        self.assertEquals(items['creator'], 'portal_owner')
        self.assertEquals(items['type'], 'Folder')
        # XXX Doesn't make sense.
        # self.assertEquals(items['format'], 'text/html')
        self.assertEquals(items['language'], '')
        self.assertEquals(items['rights'], '')

    def test_proppatch_quotable(self):
        self.portal.invokeFactory('Document', id='test')
        doc = self.portal.test
        psets = dict(doc.propertysheets.items())
        dc = psets['dublincore']
        items = dict(dc.propertyItems())
        self.assertEquals(items['subject'], ())
        self.assertEquals(doc.Subject(), ())
        value = 'ACME & ACME, LLC'
        d = {'ns':'http://cmf.zope.org/propsets/dublincore',
             'propname':'subject',
             'propvalue':escape(value)}
        req = make_request(BODY=PROPPATCH_XML % d)
        patch = PropPatch(req)
        patch.apply(doc)
        items = dict(dc.propertyItems())
        self.assertEquals(items['subject'], (value,))
        self.assertEquals(doc.Subject(), (value,))

    def _test_proppatch_encoding(self, value, encoding=None):
        if encoding is not None:
            pp = getToolByName(self.portal, 'portal_properties')
            sp = getToolByName(pp, 'site_properties')
            sp._updateProperty('default_charset', encoding)
        self.portal.invokeFactory('Document', id='test')
        doc = self.portal.test
        psets = dict(doc.propertysheets.items())
        dc = psets['dublincore']
        items = dict(dc.propertyItems())
        self.assertEquals(items['subject'], ())
        self.assertEquals(doc.Subject(), ())
        d = {'ns':'http://cmf.zope.org/propsets/dublincore',
             'propname':'subject',
             'propvalue':value.encode('utf-8')} # xml encoding is utf-8
        req = make_request(BODY=PROPPATCH_XML % d)
        patch = PropPatch(req)
        patch.apply(doc)
        s = dc.getProperty('subject')
        items = dict(dc.propertyItems())
        # Make sure the property got stored in the 'portal encoding'
        enc = site_encoding(doc)
        self.assertEquals(items['subject'][0].decode(enc), value)
        self.assertEquals(doc.Subject()[0].decode(enc), value)
        # Do a PROPFIND to exercise dav__allprop
        req = make_request()
        find = PropFind(req)
        res = find.apply(doc)
        # We are checking the XML stream here, which we know is utf-8.
        self.failUnless(value in res.decode('utf-8'))
        # And now a PROPFIND to exercise dav__propstat
        d.update({'prefix':'cmf'})
        req = make_request(BODY=PROPSTAT_XML % d)
        find = PropFind(req)
        res = find.apply(doc)
        self.failUnless(value in res.decode('utf-8'))

    def test_proppatch_unicode_default(self):
        self._test_proppatch_encoding(value=u'La Pe\xf1a')

    def test_proppatch_unicode_latin_1(self):
        self._test_proppatch_encoding(value=u'La Pe\xf1a', encoding='latin-1')

    def test_proppatch_unicode_iso_8859_1(self):
        self._test_proppatch_encoding(value=u'La Pe\xf1a', encoding='iso-8859-1')

    def test_proppatch_unicode_koi8_r(self):
        value = (u'\u041f\u0440\u0435\u0434\u0438'
                 u'\u0441\u043b\u043e\u0432\u0438\u0435')
        self._test_proppatch_encoding(value=value, encoding='koi8-r')

class TestCMFSet(PTC):

    def afterSetUp(self):
        self.loginAsPortalOwner()
        self.addProduct('CMFPropertySets')
        self.mt = self.portal.portal_membership
        self.acl_users = self.portal.acl_users
        self.pt = self.portal.portal_types

    def test_document_discussion(self):
        self.portal.invokeFactory('Document', id='test')
        doc = self.portal.test
        psets = dict(doc.propertysheets.items())
        self.failUnless('cmf' in psets)
        cmf = psets['cmf']
        items = dict(cmf.propertyItems())
        self.failUnless('discussion' in items)
        # Defaults to disabled
        self.assertEquals(items['discussion'], 0)
        cmf._updateProperty('discussion', 1)
        items = dict(cmf.propertyItems())
        self.assertEquals(items['discussion'], 1)
        cmf._updateProperty('discussion', '1')
        items = dict(cmf.propertyItems())
        self.assertEquals(items['discussion'], 1)
        cmf._updateProperty('discussion', 0)
        items = dict(cmf.propertyItems())
        self.assertEquals(items['discussion'], 0)
        cmf._updateProperty('discussion', '0')
        items = dict(cmf.propertyItems())
        self.assertEquals(items['discussion'], 0)
        # Revert to default
        cmf._updateProperty('discussion', None)
        items = dict(cmf.propertyItems())
        self.assertEquals(items['discussion'], 0)
        cmf._updateProperty('discussion', 'None')
        items = dict(cmf.propertyItems())
        self.assertEquals(items['discussion'], 0)
        cmf._updateProperty('discussion', 'none')
        items = dict(cmf.propertyItems())
        self.assertEquals(items['discussion'], 0)

    def test_folder_discussion(self):
        self.portal.invokeFactory('Folder', id='test')
        doc = self.portal.test
        psets = dict(doc.propertysheets.items())
        psets = dict(doc.propertysheets.items())
        self.failUnless('cmf' in psets)
        cmf = psets['cmf']
        items = dict(cmf.propertyItems())
        self.failUnless('discussion' in items)
        # Defaults to disabled
        self.assertEquals(items['discussion'], 0)
        cmf._updateProperty('discussion', 1)
        items = dict(cmf.propertyItems())
        self.assertEquals(items['discussion'], 1)
        cmf._updateProperty('discussion', '1')
        items = dict(cmf.propertyItems())
        self.assertEquals(items['discussion'], 1)
        cmf._updateProperty('discussion', 0)
        items = dict(cmf.propertyItems())
        self.assertEquals(items['discussion'], 0)
        cmf._updateProperty('discussion', '0')
        items = dict(cmf.propertyItems())
        self.assertEquals(items['discussion'], 0)
        # Revert to default
        cmf._updateProperty('discussion', None)
        items = dict(cmf.propertyItems())
        self.assertEquals(items['discussion'], 0)
        cmf._updateProperty('discussion', 'None')
        items = dict(cmf.propertyItems())
        self.assertEquals(items['discussion'], 0)
        cmf._updateProperty('discussion', 'none')
        items = dict(cmf.propertyItems())
        self.assertEquals(items['discussion'], 0)

class TestVocabulary(PTC):

    def afterSetUp(self):
        self.loginAsPortalOwner()
        self.addProduct('CMFPropertySets')
        self.acl_users = self.portal.acl_users

    def test_vocabs(self):
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

class TestTemplate(unittest.TestCase):

    def test_quote_attrs(self):
        d = {'label':"<ACME's Corp>",
             'value':'ACME & ACME, LLC',
             }
        t = Template()
        got = t % d
        expected = ('<term label="&lt;ACME\'s Corp&gt;" '
                    'value="ACME &amp; ACME, LLC" />')
        self.assertEquals(got, expected)

    def test_unicode_attrs(self):
        d = {'label':u'La Pe\xf1a',
             'value':u'La Pe\xf1a',
             }
        t = Template()
        got = t % d
        expected = (u'<term label="La Pe\xf1a" '
                    u'value="La Pe\xf1a" />'.encode('utf-8'))
        self.assertEquals(got, expected)

def test_suite():
    import unittest
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestTemplate))
    suite.addTest(unittest.makeSuite(TestCMFSet))
    suite.addTest(unittest.makeSuite(TestVocabulary))
    suite.addTest(unittest.makeSuite(TestDCWorkflowSet))
    suite.addTest(unittest.makeSuite(TestDublinCoreSet))
    return suite

if __name__ == '__main__':
    framework(descriptions=1, verbosity=1)
