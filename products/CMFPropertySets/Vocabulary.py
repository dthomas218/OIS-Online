"""
$Id: Vocabulary.py 2005 2008-03-18 16:45:03Z sidnei $
"""


import cgi

from xml.dom import minidom
from zope.interface import implements

from StringIO import StringIO
from ComputedAttribute import ComputedAttribute
from Globals import InitializeClass
from Acquisition import aq_base, Implicit
from AccessControl import ClassSecurityInfo
from AccessControl import Permissions as p
from OFS.Folder import Folder
from Products.PropertySets.PropertySetPredicate import PropertySetPredicate
from Products.PropertySets.PropertySetRegistry import registerPredicate
from Products.CMFCore.utils import getToolByName
from Products.CMFPropertySets.DynamicPropset import DynamicPropset
from Products.CMFPropertySets.interfaces import IGlobalVocabRegistry
from Products.CMFPropertySets.interfaces import ILocalVocabRegistry
from Products.CMFPropertySets.interfaces.provider import IVocabularyProvider
from Products.CMFPropertySets.config import *

pm = (
    {'id':'vocabulary', 'type':'string', 'mode':'r'},
    )

class Vocabulary(DynamicPropset):
    """Vocabularies"""

    id='vocabulary'
    _md={'xmlns': 'http://cmf.zope.org/propsets/vocabulary'}
    _extensible = 0

    def __init__(self, context, container):
        self._v_context = context
        self._v_container = container

    context = ComputedAttribute(lambda self: self._v_context)
    container = ComputedAttribute(lambda self: self._v_container)

    def dav__vocabulary(self, result=None):
        if result is None:
            result = StringIO()

        result.write('<vocabs>\n')
        entry = ("<vocab ns='%(ns)s' propid='%(propid)s'>\n"
                 "%(content)s\n"
                 "</vocab>\n")
        for vocab_id, vocab in self.container.objectItems():
            if not hasattr(vocab, 'getValueFor'):
                log('Broken object or not a vocabulary provider '
                    'at %s/%s.' % (self.container.absolute_url(), vocab_id),
                    level=ERROR)
                continue
            content = vocab.getValueFor(self.context)
            if content.strip():
                data = {'ns':cgi.escape(vocab.ns),
                        'propid':cgi.escape(vocab.propid),
                        'content':content
                        }
                result.write(entry % data)

        result.write('</vocabs>\n')

        # It's a StringIO
        if hasattr(result, 'getvalue'):
            return result.getvalue()

        # Might be a Request object.
        return result

    def _propertyMap(self):
        return pm

InitializeClass(Vocabulary)

class BaseVocabularyPredicate(Folder, PropertySetPredicate):
    """ Expose pluggable vocabularies as a big blob.
    """

    security = ClassSecurityInfo()
    meta_type = PropertySetPredicate.meta_type

    def __init__(self, *args, **kw):
        PropertySetPredicate.__init__(self, *args, **kw)

    manage_options = (
        Folder.manage_options[0],
        PropertySetPredicate.manage_options[0],
        ) + Folder.manage_options[1:]

    security.declareProtected(p.view, 'all_meta_types')
    def all_meta_types(self):
        return Folder.all_meta_types(self, interfaces=(IVocabularyProvider,))

    security.declareProtected(p.view, 'getPropertySets')
    def getPropertySets(self, obj):
        """ Return PropertySheets that apply to the given object
        """
        return (Vocabulary(obj, self),)

    security.declareProtected(p.view, 'manage_FTPget')
    def manage_FTPget(self, REQUEST=None, RESPONSE=None):
        """ Expose global vocabs via DAV/FTP """
        if REQUEST is None:
            REQUEST = self.REQUEST

        if RESPONSE is None:
            RESPONSE = REQUEST.RESPONSE

        # Enable gzip compression if requested by the client.
        RESPONSE.enableHTTPCompression(REQUEST)

        purl = getToolByName(self, 'portal_url')
        portal = purl.getPortalObject()
        RESPONSE.setHeader('Content-Type', 'text/xml; charset="utf-8"')
        RESPONSE.write('<?xml version="1.0" encoding="utf-8"?>\n')
        pset = self.getPropertySets(portal)[0]
        return pset.dav__vocabulary(result=RESPONSE)

    security.declareProtected(p.view, '__call__')
    security.declareProtected(p.view, 'index_html')
    security.declareProtected(p.view, 'manage_DAVget')
    __call__ = index_html = manage_DAVget = manage_FTPget

class VocabularyPredicate(BaseVocabularyPredicate):
    implements(ILocalVocabRegistry)

InitializeClass(VocabularyPredicate)

class GlobalVocabRegistry(VocabularyPredicate):
    implements(IGlobalVocabRegistry)

    def __init__(self, id):
        PropertySetPredicate.__init__(self, id, 'Global Vocabulary Registry')

InitializeClass(GlobalVocabRegistry)

registerPredicate('vocabulary',
                  'Pluggable Vocabularies',
                  VocabularyPredicate)
