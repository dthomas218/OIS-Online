# Enfold Desktop
# Copyright(C), 2004-2006, Enfold Systems, Inc. - ALL RIGHTS RESERVED

# Enfold Systems, Inc.
# 4617 Montrose Blvd., Suite C215
# Houston, Texas 77006 USA
# p. +1 713.942.2377 | f. +1 832.201.8856
# www.enfoldsystems.com
# info@enfoldsystems.com

# $Id: groups.py 5635 2006-07-03 15:44:24Z sidnei $

from Globals import InitializeClass
from Acquisition import aq_base
from ZODB.POSException import ConflictError
from Products.CMFPropertySets.interfaces.provider import IVocabularyProvider
from Products.CMFPropertySets.VocabularyProvider import VocabularyProvider
from Products.CMFCore.utils import getToolByName
from Products.ShellExServer.utils import getGroupNames
from Products.ShellExServer.vocabs.helpers import Constructor
from Products.ShellExServer.config import MAX_USERS_AND_GROUPS

class Groups(VocabularyProvider):
    """ Available groups for a content object """

    id = 'groups'
    ns = 'http://enfoldtechnology.com/propsets/sharing'
    propid = 'groups'
    max_results = MAX_USERS_AND_GROUPS

    def _getGroupsIds(self, context):
        res = []
        gt = getToolByName(context, 'portal_groups', None)
        if gt is None:
            return ''
        valid_groups = gt.listGroupIds()[:self.max_results]
        if len(valid_groups) == self.max_results:
            # Limit exceeded.
            valid_groups = ()
        for group in valid_groups:
            data = {'label':group,
                    'value':group
                    }
            res.append(self.template % data)
        return '\n'.join(res)

    def _searchGroupIds(self, context):
        res = []
        acl = getToolByName(context, 'acl_users')

        # According to Wichert Akkerman a search that returns 'too
        # many' results in AD might blow up here. We don't have the
        # actual exception handy so it probably deserves a better fix.
        try:
            valid_groups = acl.searchGroups(max_results=self.max_results)
        except ConflictError:
            raise
        except:
            return '\n'.join(res)

        if len(valid_groups) == self.max_results:
            # Limit exceeded.
            valid_groups = ()
        for group in valid_groups:
            data = {'label':group['title'],
                    'value':group['id']
                    }
            res.append(self.template % data)
        return '\n'.join(res)

    def getValueFor(self, context):
        acl = getToolByName(context, 'acl_users')
        if acl.meta_type == 'Pluggable Auth Service':
            return self._searchGroupIds(context)
        return self._getGroupsIds(context)

InitializeClass(Groups)

manage_addGroups = Constructor(Groups)
