# Enfold Desktop
# Copyright(C), 2004-2006, Enfold Systems, Inc. - ALL RIGHTS RESERVED

# Enfold Systems, Inc.
# 4617 Montrose Blvd., Suite C215
# Houston, Texas 77006 USA
# p. +1 713.942.2377 | f. +1 832.201.8856
# www.enfoldsystems.com
# info@enfoldsystems.com

# $Id: users.py 5635 2006-07-03 15:44:24Z sidnei $

from Globals import InitializeClass
from Acquisition import aq_base
from ZODB.POSException import ConflictError
from Products.CMFPropertySets.interfaces.provider import IVocabularyProvider
from Products.CMFPropertySets.VocabularyProvider import VocabularyProvider
from Products.CMFCore.utils import getToolByName
from Products.ShellExServer.vocabs.helpers import Constructor
from Products.ShellExServer.config import MAX_USERS_AND_GROUPS

class Users(VocabularyProvider):
    """ Available users for a content object """

    id = 'users'
    ns = 'http://enfoldtechnology.com/propsets/sharing'
    propid = 'users'
    max_results = MAX_USERS_AND_GROUPS

    def _getMemberIds(self, context):
        res = []
        mt = getToolByName(context, 'portal_membership', None)
        if mt is None:
            return ''
        valid_users = mt.listMemberIds()[:self.max_results]
        if len(valid_users) == self.max_results:
            # Limit exceeded.
            valid_users = ()
        for user in valid_users:
            data = {'label':user,
                    'value':user
                    }
            res.append(self.template % data)
        return '\n'.join(res)

    def _searchUserIds(self, context):
        res = []
        acl = getToolByName(context, 'acl_users')

        # According to Wichert Akkerman a search that returns 'too
        # many' results in AD might blow up here. We don't have the
        # actual exception handy so it probably deserves a better fix.
        try:
            valid_users = acl.searchUsers(max_results=self.max_results)
        except ConflictError:
            raise
        except:
            return '\n'.join(res)

        if len(valid_users) == self.max_results:
            # Limit exceeded.
            valid_users = ()
        for user in valid_users:
            data = {'label':user['title'],
                    'value':user['id']
                    }
            res.append(self.template % data)
        return '\n'.join(res)

    def getValueFor(self, context):
        acl = getToolByName(context, 'acl_users')
        if acl.meta_type == 'Pluggable Auth Service':
            return self._searchUserIds(context)
        return self._getMemberIds(context)

InitializeClass(Users)

manage_addUsers = Constructor(Users)
