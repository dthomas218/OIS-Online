# Enfold Desktop
# Copyright(C), 2004-2006, Enfold Systems, Inc. - ALL RIGHTS RESERVED

# Enfold Systems, Inc.
# 4617 Montrose Blvd., Suite C215
# Houston, Texas 77006 USA
# p. +1 713.942.2377 | f. +1 832.201.8856
# www.enfoldsystems.com
# info@enfoldsystems.com

# $Id: transitions.py 7625 2007-11-07 19:38:42Z sidnei $

from Globals import InitializeClass
from Acquisition import aq_base
from Products.CMFPropertySets.interfaces.provider import IVocabularyProvider
from Products.CMFPropertySets.VocabularyProvider import VocabularyProvider
from Products.CMFCore.utils import getToolByName
from Products.ShellExServer.vocabs.helpers import Constructor
from Products.ShellExServer.utils import listFilteredActionsForCategory

class Transitions(VocabularyProvider):
    """ Available subjects for a content object """

    id = 'transitions'
    ns = 'http://cmf.zope.org/propsets/dcworkflow'
    propid = 'review_state'

    def getValueFor(self, context):
        wf_tool = getToolByName(context, 'portal_workflow', None)
        if wf_tool is None:
            return ''
        
        res = []
        actions = listFilteredActionsForCategory(wf_tool, context, 
                                                 'workflow', 
                                                 ('portal_workflow',))

        for action in actions['workflow']:
            data = {'label':action['name'],
                    'value':action['id']
                    }
            res.append(self.template % data)
        return '\n'.join(res)

InitializeClass(Transitions)

manage_addTransitions = Constructor(Transitions)
