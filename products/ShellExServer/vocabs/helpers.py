# Enfold Desktop
# Copyright(C), 2004-2006, Enfold Systems, Inc. - ALL RIGHTS RESERVED

# Enfold Systems, Inc.
# 4617 Montrose Blvd., Suite C215
# Houston, Texas 77006 USA
# p. +1 713.942.2377 | f. +1 832.201.8856
# www.enfoldsystems.com
# info@enfoldsystems.com

# $Id: helpers.py 5635 2006-07-03 15:44:24Z sidnei $
# $HeadURL: https://svn.enfoldsystems.com/internal/ShellExServer/trunk/vocabs/helpers.py $

from AccessControl import ClassSecurityInfo
from AccessControl import Unauthorized
from ExtensionClass import Base
from Globals import InitializeClass
from Products.CMFCore.utils import _checkPermission

class Constructor(Base):
    """I am a constructor and this is my docstring """

    security = ClassSecurityInfo()

    def __init__(self, klass):
        self.__name__ = 'manage_add%s' % klass.__name__
        self.factory = klass
        self.permission = None

    security.declarePrivate('setPermission')
    def setPermission(self, perm):
        self.permission = perm

    security.declarePublic('__call__')
    def __call__(inst, self, REQUEST=None):
        # Arguments renamed so it can be called from the ZMI.
        if not _checkPermission(inst.permission, self):
            raise Unauthorized
        obj = inst.factory()
        self._setObject(obj.id, obj)

        if REQUEST is not None:
            REQUEST['RESPONSE'].redirect(self.absolute_url()+'/manage_main')
        else:
            return self._getOb(obj.id)

InitializeClass(Constructor)
