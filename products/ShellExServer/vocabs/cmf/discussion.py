# Enfold Desktop
# Copyright(C), 2004-2006, Enfold Systems, Inc. - ALL RIGHTS RESERVED

# Enfold Systems, Inc.
# 4617 Montrose Blvd., Suite C215
# Houston, Texas 77006 USA
# p. +1 713.942.2377 | f. +1 832.201.8856
# www.enfoldsystems.com
# info@enfoldsystems.com

# $Id: discussion.py 5635 2006-07-03 15:44:24Z sidnei $

from Globals import InitializeClass
from Acquisition import aq_base
from Products.CMFPropertySets.interfaces.provider import IVocabularyProvider
from Products.CMFPropertySets.VocabularyProvider import VocabularyProvider
from Products.CMFCore.utils import getToolByName
from Products.ShellExServer.vocabs.helpers import Constructor

class Discussion(VocabularyProvider):
    """ Available discussions for a content object """

    id = 'discussion'
    ns = 'http://cmf.zope.org/propsets/default'
    propid = 'discussion'

    def getValueFor(self, context):
        values = {
            'Enabled':1,
            'Disabled':0,
            'Default':None
            }
        res = []
        for label, value in values.items():
            data = {'label':label,
                    'value':value
                    }
            res.append(self.template % data)
        return '\n'.join(res)

InitializeClass(Discussion)

manage_addDiscussion = Constructor(Discussion)
