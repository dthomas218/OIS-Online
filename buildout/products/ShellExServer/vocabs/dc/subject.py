# Enfold Desktop
# Copyright(C), 2004-2006, Enfold Systems, Inc. - ALL RIGHTS RESERVED

# Enfold Systems, Inc.
# 4617 Montrose Blvd., Suite C215
# Houston, Texas 77006 USA
# p. +1 713.942.2377 | f. +1 832.201.8856
# www.enfoldsystems.com
# info@enfoldsystems.com

# $Id: subject.py 6740 2006-12-20 13:07:14Z sidnei $

from sets import Set
from Globals import InitializeClass
from Acquisition import aq_base
from Products.CMFPropertySets.interfaces.provider import IVocabularyProvider
from Products.CMFPropertySets.VocabularyProvider import VocabularyProvider
from Products.CMFCore.utils import getToolByName
from Products.ShellExServer.vocabs.helpers import Constructor

class Subject(VocabularyProvider):
    """ Available subjects for a content object """

    id = 'subject'
    ns = 'http://cmf.zope.org/propsets/dublincore'
    propid = 'subject'

    def getValueFor(self, context):
        subjects = Set()
        mt = getToolByName(context, 'portal_metadata', None)
        if mt is None:
            return ''
        ct = getToolByName(context, 'portal_catalog', None)
        if ct is None:
            return ''
        subjects.update(mt.listAllowedSubjects(context))
        subjects.update(ct.uniqueValuesFor('Subject'))
        res = []
        for sub in subjects:
            data = {'label':sub,
                    'value':sub
                    }
            res.append(self.template % data)
        return '\n'.join(res)

InitializeClass(Subject)

manage_addSubject = Constructor(Subject)
