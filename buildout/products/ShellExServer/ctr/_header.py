# Enfold Desktop
# Copyright(C), 2004-2006, Enfold Systems, Inc. - ALL RIGHTS RESERVED

# Enfold Systems, Inc.
# 4617 Montrose Blvd., Suite C215
# Houston, Texas 77006 USA
# p. +1 713.942.2377 | f. +1 832.201.8856
# www.enfoldsystems.com
# info@enfoldsystems.com

# $Id: _header.py 7614 2007-11-06 20:39:36Z sidnei $
# $HeadURL: https://svn.enfoldsystems.com/internal/ShellExServer/trunk/ctr/_header.py $

from AccessControl import ClassSecurityInfo
from Globals import DTMLFile, InitializeClass

from Products.ShellExServer.config import DTML_DIR
from Products.ShellExServer.ctr._base import BasePredicate

try:
    from Products.CMFCore.permissions import ManagePortal
except:
    from Products.CMFCore.CMFCorePermissions import ManagePortal

def headerPredicateCracker(p):
    return p.getPortalTypeName(), p.getHeaderName() 

class HeaderPredicate(BasePredicate):

    _header_name = ''
    PREDICATE_TYPE  = 'request_header'

    security = ClassSecurityInfo()

    security.declareProtected(ManagePortal, 'edit')
    def edit(self, portal_type_name, header_name):
        if type(header_name) is type(''):
            self._header_name = header_name
        else:
            raise TypeError, 'String Value Required.'
        BasePredicate.edit(self, portal_type_name)

    def getHeaderName(self):
        return self._header_name

    def __call__(self, name, typ, body):
        # We are abusing the fact that the request is always
        # acquirable here and implicitly fetching it instead of
        # explicitly requiring the ctr to pass us the request.
        header_name = self.getHeaderName()
        if not header_name:
            return 0

        # Extension Headers are normalized to this format in
        # the request by ZPublisher
        header_name = 'HTTP_' + header_name.upper().replace('-', '_')

        request = self.REQUEST
        type_name = request.get(header_name, '').strip()

        if not type_name:
            return 0

        if type_name == self.getPortalTypeName():
            return 1

        return 0

    security.declareProtected(ManagePortal, 'predicateWidget')
    predicateWidget = DTMLFile('headerPredicateWidget', DTML_DIR)

InitializeClass(HeaderPredicate)
