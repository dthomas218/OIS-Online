"""
$Id: DublinCore.py 2005 2008-03-18 16:45:03Z sidnei $
"""

from Globals import InitializeClass
from App.Common import iso8601_date
from DateTime import DateTime
from Products.PropertySets.PropertySetPredicate import PropertySetPredicate
from Products.PropertySets.PropertySetRegistry import registerPredicate
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.interfaces.DublinCore import MutableDublinCore, \
     DublinCore
from Products.CMFPropertySets.DynamicPropset import DynamicPropset

_marker = []

pm = (
    {'id':'title', 'type':'string', 'mode':'rw',
     'mutator':'setTitle', 'accessor':'Title'},
    {'id':'creator', 'type':'string', 'mode':'r',
     'accessor':'Creator'},
    {'id':'subject', 'type':'lines', 'mode':'rw',
     'mutator':'setSubject', 'accessor':'Subject'},
    {'id':'description', 'type':'string', 'mode':'rw',
     'mutator':'setDescription', 'accessor':'Description'},
    {'id':'publisher', 'type':'string', 'mode':'r',
     'accessor':'Publisher'},
    {'id':'contributors', 'type':'lines', 'mode':'rw',
     'mutator':'setContributors', 'accessor':'Contributors'},
    {'id':'date', 'type':'date', 'mode':'r',
     'accessor':'Date'},
    {'id':'creationdate', 'type':'date', 'mode':'r',
     'accessor':'CreationDate'},
    {'id':'effectivedate', 'type':'date', 'mode':'rw',
     'mutator':'setEffectiveDate', 'accessor':'EffectiveDate'},
    {'id':'expirationdate', 'type':'date', 'mode':'rw',
     'mutator':'setExpirationDate', 'accessor':'ExpirationDate'},
    {'id':'modificationdate', 'type':'date', 'mode':'r',
     'accessor':'ModificationDate'},
    {'id':'type', 'type':'string', 'mode':'r',
     'accessor':'Type'},
    {'id':'format', 'type':'string', 'mode':'rw',
     'mutator':'setFormat', 'accessor':'Format'},
    {'id':'identifier', 'type':'string', 'mode':'r',
     'accessor':'Identifier'},
    {'id':'language', 'type':'string', 'mode':'rw',
     'mutator':'setLanguage', 'accessor':'Language'},
    {'id':'rights', 'type':'string', 'mode':'rw',
     'mutator':'setRights', 'accessor':'Rights'},
    )

class DublinCoreProperties(DynamicPropset):
    """Dublin Core Properties"""

    id='dublincore'
    _md={'xmlns': 'http://cmf.zope.org/propsets/dublincore'}
    _extensible=0

    def _getAccessor(self, id):
        acc = DynamicPropset._getAccessor(self, id)
        if acc is not None:
            return acc
        propinfo = self.propertyInfo(id)
        ac_name = propinfo['accessor']
        vself = self.v_self()
        return getattr(vself, ac_name, None)

    def _getMutator(self, id):
        mut = DynamicPropset._getMutator(self, id)
        if mut is not None:
            return mut
        propinfo = self.propertyInfo(id)
        m_name = propinfo.get('mutator')
        if m_name is None:
            return None
        vself = self.v_self()
        return getattr(vself, m_name, None)

    def dav__modificationdate(self):
        vself = self.v_self()
        modified = DateTime(vself.ModificationDate()).timeTime()
        return iso8601_date(modified)

    def dav__creationdate(self):
        vself = self.v_self()
        created = DateTime(vself.CreationDate()).timeTime()
        return iso8601_date(created)

    def _propertyMap(self):
        return pm

InitializeClass(DublinCoreProperties)

class DublinCorePredicate(PropertySetPredicate):
    """ Expose Dublin Core Metadata for an object
    """

    _property_sets = (DublinCoreProperties(),)

    def apply(self, obj):
        """ Check for interface implements.

        This should probably be a default feature,
        e.g.: having a _apply_to class attribute
        containing interfaces to check against.
        """
        if not DublinCore.isImplementedBy(obj):
            return ()
        if not MutableDublinCore.isImplementedBy(obj):
            return ()
        return PropertySetPredicate.apply(self, obj)

registerPredicate('dublincore',
                  'Dublin Core Metadata',
                  DublinCorePredicate)
