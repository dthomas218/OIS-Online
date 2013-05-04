# -*- coding: utf-8 -*-
"""
$Id: VocabularyProvider.py 703 2005-04-21 17:39:26Z sidnei $
"""

from xml.sax.saxutils import quoteattr
from AccessControl import ClassSecurityInfo
from Acquisition import aq_base
from OFS.SimpleItem import SimpleItem
from Globals import InitializeClass
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
try:
    from Products.CMFPropertySets.interfaces.provider import IVocabularyProvider
except ImportError:
    class IVocabularyProvider: pass
    # so this can be run from cmd line

class Template:

    template = """<term label=%(label)s value=%(value)s />"""

    def __mod__(self, arg):
        assert isinstance(arg, dict)
        _arg = {}
        for k, v in arg.items():
            # Unicode must be encoded in the encoding declared in
            # the top XML tag.  We don't know what this is, so assume
            # UTF-8
            if type(v)==unicode:
                _v = v.encode("utf-8")
            else:
                # Convert to str here, as the template will anyway
                try:
                    _v = str(v)
                except:
                    # who knows?
                    return ''
            _arg[k] = quoteattr(_v)
        return self.template % _arg

class VocabularyProvider(SimpleItem):
    """ A Simple Vocabulary Provider """

    __implements__ = (getattr(SimpleItem, '__implements__', ()) +
                      (IVocabularyProvider,))

    security = ClassSecurityInfo()
    template = Template()
    __allow_access_to_unprotected_subobjects__ = 0

    security.setDefaultAccess(
        {'id':1, 'ns':1,
         'propid':1, 'meta_type':1}
        )
    id = 'vocab_provider'
    ns = 'http://foo.com/bar'
    propid = 'foo'
    meta_type = 'Vocabulary Provider'

    def __init__(self):
        pass

    manage_options = (
        {'label':'Overview', 'action':'manage_providerOverviewForm'},
        ) + SimpleItem.manage_options

    manage_providerOverviewForm = PageTemplateFile(
        'www/vocabularyProviderOverview', globals(),
        __name__='manage_providerOverviewForm')

    security.declarePrivate('getValueFor')
    def getValueFor(self, obj):
        """ Get the vocabulary for the given object. """
        return ''

InitializeClass(VocabularyProvider)

if __name__=='__main__':
    class X:
        def __str__(self):
            # hehe
            return "<>"
    x = [
            ['&', '"&amp;"'],
            [' ', '" "'],
            ['"', '\'"\''],
            ['\'"', '"\'&quot;"'],
            ['¥', ''],
            [u'¥', ''],
            ['Δ, ',''],
            ["There's only one ®Guinness", ""],
            ["There's only \"one\" ®Guinness", ""],
            [1.1234, '"1.1234"'],
            ["None", '"None"'],
            [None, "\"None\""],
            ["<", '"&lt;"'],
            [X(), '"&lt;&gt;"'],
    ]

    for value, oup in x:
        t = Template()
        out = t % ( {
            'label':'label',
            'value':value
            }
        )
        res = out[26:-3]
        if res != oup:
            print "Failure: output is %s not %s" % (res, oup)
