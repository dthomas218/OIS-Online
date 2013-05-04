# Enfold Desktop
# Copyright(C), 2004-2006, Enfold Systems, Inc. - ALL RIGHTS RESERVED

# Enfold Systems, Inc.
# 4617 Montrose Blvd., Suite C215
# Houston, Texas 77006 USA
# p. +1 713.942.2377 | f. +1 832.201.8856
# www.enfoldsystems.com
# info@enfoldsystems.com

# $Id: format.py 6740 2006-12-20 13:07:14Z sidnei $

from Globals import InitializeClass
from Acquisition import aq_base
from Products.CMFPropertySets.interfaces.provider import IVocabularyProvider
from Products.CMFPropertySets.VocabularyProvider import VocabularyProvider
from Products.CMFCore.utils import getToolByName
from Products.ShellExServer.vocabs.helpers import Constructor

class Format(VocabularyProvider):
    """ Available formats for a content object """

    id = 'format'
    ns = 'http://cmf.zope.org/propsets/dublincore'
    propid = 'format'

    def getValueFor(self, context):
        res = []
        ut = getToolByName(context, 'plone_utils', None)
        if ut is None:
            return ''
        for mime in ut.availableMIMETypes():
            data = {'label':mime,
                    'value':mime
                    }
            res.append(self.template % data)
        return '\n'.join(res)

InitializeClass(Format)

manage_addFormat = Constructor(Format)
