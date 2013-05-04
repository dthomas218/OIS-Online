# Enfold Desktop
# Copyright(C), 2004-2006, Enfold Systems, Inc. - ALL RIGHTS RESERVED

# Enfold Systems, Inc.
# 4617 Montrose Blvd., Suite C215
# Houston, Texas 77006 USA
# p. +1 713.942.2377 | f. +1 832.201.8856
# www.enfoldsystems.com
# info@enfoldsystems.com

# $Id: actions.py 7625 2007-11-07 19:38:42Z sidnei $

import logging

from Acquisition import aq_base
from Globals import InitializeClass
from ZODB.POSException import ConflictError
from Products.CMFPropertySets.interfaces.provider import IVocabularyProvider
from Products.CMFPropertySets.VocabularyProvider import VocabularyProvider
from Products.CMFCore.utils import getToolByName
from Products.ShellExServer.vocabs.helpers import Constructor

# go and get the way more efficient one
from Products.ShellExServer.utils import listFilteredActionsForCategory

logger = logging.getLogger('ShellExServer')

class Actions(VocabularyProvider):
    """ Available actions for a content object """

    id = 'actions'
    ns = 'http://enfoldtechnology.com/vocabs/actions'
    propid = 'actions'

    def getValueFor(self, context):
        res = []
        a = []
        at = getToolByName(context, 'portal_actions', None)
        if at is None:
            return ''
        actions = listFilteredActionsForCategory(
            at,
            context,
            required_category='desktop_action')
        for action in actions.get('desktop_action', []):
            try:
                data = {
                    'label': action.get('title', action.get('name', '')),
                    'value': action['url'],
                    }
            except ConflictError:
                raise
            except:
                logger.exception('Failure computing action: %r', action)
            else:
                res.append(self.template % data)
        return '\n'.join(res)

InitializeClass(Actions)

manage_addActions = Constructor(Actions)
