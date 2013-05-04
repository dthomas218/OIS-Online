# Enfold Desktop
# Copyright(C), 2004-2006, Enfold Systems, Inc. - ALL RIGHTS RESERVED

# Enfold Systems, Inc.
# 4617 Montrose Blvd., Suite C215
# Houston, Texas 77006 USA
# p. +1 713.942.2377 | f. +1 832.201.8856
# www.enfoldsystems.com
# info@enfoldsystems.com

# $Id: _base.py 7332 2007-07-21 02:38:55Z sidnei $
# $HeadURL: https://svn.enfoldsystems.com/internal/ShellExServer/trunk/ctr/_base.py $

from OFS.SimpleItem import SimpleItem
from AccessControl import ClassSecurityInfo
from Globals import InitializeClass

try:
    from Products.CMFCore.permissions import ManagePortal
except:
    from Products.CMFCore.CMFCorePermissions import ManagePortal

class BasePredicate(SimpleItem):

    security = ClassSecurityInfo()

    _portal_type_name = None
    PREDICATE_TYPE = None

    def __init__(self, id):
        self.id = id

    security.declareProtected(ManagePortal, 'getPortalTypeName')
    def getPortalTypeName(self):
        """
        """
        if self._portal_type_name is None:
            return 'None'
        return self._portal_type_name

    security.declareProtected(ManagePortal, 'edit')
    def edit(self, portal_type_name):

        if type(portal_type_name) is type(''):
            self._portal_type_name = portal_type_name
        else:
            raise TypeError, 'String Value Required.'

    #
    #   ContentTypeRegistryPredicate interface
    #
    security.declareObjectPublic()
    def __call__(self, name, typ, body):
        raise NotImplementedError

    security.declareProtected(ManagePortal, 'getTypeLabel')
    def getTypeLabel(self):
        """ Return a human-readable label for the predicate type.
        """
        return self.PREDICATE_TYPE

InitializeClass(BasePredicate)
