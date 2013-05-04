"""
$Id: CMF.py 2384 2008-10-21 17:24:39Z sidnei $
"""

from Globals import InitializeClass
from zExceptions import BadRequest
from Products.PropertySets.PropertySetPredicate import PropertySetPredicate
from Products.PropertySets.PropertySetRegistry import registerPredicate
from Products.CMFCore.utils import getToolByName
from Products.CMFPropertySets.DynamicPropset import DynamicPropset
from ZPublisher.Converters import type_converters
from Products.CMFCore.interfaces.Contentish import Contentish
from Products.CMFCore.interfaces.Folderish import Folderish

def int_or_none(v):
    if v in (None, 'none', 'None', ''):
        return None
    if v in (False, 'False'):
        return 0
    if v in (True, 'True'):
        return 1
    return type_converters['int'](v)
type_converters['int_or_none'] = int_or_none

_marker = []

pm = ({'id':'discussion', 'type':'int_or_none', 'mode':'rw'},)

class CMFProperties(DynamicPropset):
    """CMF Properties that don't fit anywere"""

    id='cmf'
    _md={'xmlns': 'http://cmf.zope.org/propsets/default'}
    _extensible=0

    def _propertyMap(self):
        return pm

    def dav__discussion(self):
        vself=self.v_self()
        dtool = getToolByName(vself, 'portal_discussion', None)
        if dtool is None:
            return
        return int_or_none(dtool.isDiscussionAllowedFor(vself))

    def dav__set_discussion(self, value, default=_marker):
        vself=self.v_self()
        dtool = getToolByName(self, 'portal_discussion', None)
        if dtool is None:
            return
        return dtool.overrideDiscussionFor(vself, value)

InitializeClass(CMFProperties)

class CMFPredicate(PropertySetPredicate):
    """ Expose CMF Properties that don't fit anywere.
    """

    _property_sets = (CMFProperties(),)

    def apply(self, obj):
        """ Check for interface implements.

        This should probably be a default feature,
        e.g.: having a _apply_to class attribute
        containing interfaces to check against.
        """
        if not (Contentish.isImplementedBy(obj) or Folderish.isImplementedBy(obj)):
            return ()
        return PropertySetPredicate.apply(self, obj)

registerPredicate('cmf',
                  'CMF Properties (discussion, etc)',
                  CMFPredicate)
