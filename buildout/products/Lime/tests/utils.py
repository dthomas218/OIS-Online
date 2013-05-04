##############################################################################
#
# Lime - Link Marshaller
# Copyright(C), 2004-2007, Enfold Systems, Inc. - ALL RIGHTS RESERVED
#
# This software is licensed under the Terms and Conditions contained
# within the LICENSE.txt file that accompanied this software.  Any
# inquiries concerning the scope or enforceability of the license should
# be addressed to:
#
# Enfold Systems, Inc.
# 4617 Montrose Blvd., Suite C215
# Houston, Texas 77006 USA
# p. +1 713.942.2377 | f. +1 832.201.8856
# www.enfoldsystems.com
# info@enfoldsystems.com
#
##############################################################################
"""
$Id: utils.py 7352 2007-07-24 01:59:26Z sidnei $
"""

from Products.CMFCore.utils import getToolByName
from Products.Archetypes.ArchetypeTool import FactoryTypeInformation
from Products.Archetypes.ArchetypeTool import fixActionsForType, getType
from Products.Archetypes.Extensions.utils import _getFtiAndDataFor

# Mostly copied from ArchetypeTool.manage_installType
def installType(self, typeName, package, 
                portal_type=None, global_allow=False):

    typesTool = getToolByName(self, 'portal_types')

    typeDesc = getType(typeName, package)
    klass = typeDesc['klass']
    typeinfo_name = "%s: %s (%s)" % (package, klass.__name__,
                                     klass.meta_type)

    if not portal_type:
        portal_type = typeDesc['portal_type']

    try:
        typesTool._delObject(portal_type)
    except:
        pass

    typesTool.manage_addTypeInformation(
        FactoryTypeInformation.meta_type,
        id=portal_type,
        typeinfo_name=typeinfo_name)

    t, fti = _getFtiAndDataFor(typesTool, klass.portal_type, 
                               klass.__name__, package)
    if t and fti:
        t.manage_changeProperties(**fti)
