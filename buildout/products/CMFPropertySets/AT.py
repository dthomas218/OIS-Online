"""
$Id: AT.py 2384 2008-10-21 17:24:39Z sidnei $
"""

from Globals import InitializeClass
from Acquisition import aq_inner, aq_parent, aq_base
from ComputedAttribute import ComputedAttribute
from AccessControl import ClassSecurityInfo
from AccessControl.Permissions import view, manage_properties
from zExceptions import BadRequest
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.PropertySets.PropertySetPredicate import PropertySetPredicate
from Products.PropertySets.PropertySetRegistry import registerPredicate
from Products.CMFCore.utils import getToolByName
from Products.CMFPropertySets.DynamicPropset import DynamicPropset
from Products.CMFCore.interfaces.Contentish import Contentish
from Products.CMFCore.interfaces.Folderish import Folderish

from Products.Archetypes import Field

SAFE_FIELDS = (Field.IntegerField, Field.StringField,
               Field.DateTimeField, Field.LinesField,
               Field.FloatField, Field.FixedPointField,
               Field.BooleanField)

_marker = ()

class ArchetypesProperties(DynamicPropset):
    """Dynamic Archetypes Properties
    """

    security = ClassSecurityInfo()

    def __init__(self, id, md, fields):
        DynamicPropset.__init__(self, id, md)
        self._fields = fields

    _extensible = 0

    security.declarePrivate('getFields')
    def getFields(self):
        return self._fields or ()

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

    def _propertyMap(self):
        v_self = self.v_self()
        schema = v_self.Schema()
        pm = []
        fields = self.getFields()
        for field in schema.fields():
            if not isinstance(field, SAFE_FIELDS):
                # Ignore non-safe fields.
                continue
            if field.getName() not in fields:
                # Ignore non-requested fields
                continue
            m = {'id': field.getName(),
                 'type': field.type,
                 }
            if field.edit_accessor and hasattr(v_self, field.edit_accessor):
                m['accessor'] = field.edit_accessor
            elif field.accessor and hasattr(v_self, field.accessor):
                m['accessor'] = field.accessor
            if field.mutator and hasattr(v_self, field.mutator):
                m['mutator'] = field.mutator
            modes = ''
            for key, mode in (('accessor', 'r'),
                        ('mutator', 'w')):
                if m.has_key(key):
                    modes += mode
            m['mode'] = modes
            pm.append(m)
        return tuple(pm)

InitializeClass(ArchetypesProperties)

class ArchetypesPredicate(PropertySetPredicate):
    """ Expose Archetypes Properties.
    """

    security = ClassSecurityInfo()
    _ns = None
    _enabled_portal_types = None
    _fields = None

    manage_options = (
        {'label':'Parameters', 'action':'manage_changeParametersForm'},
        ) + PropertySetPredicate.manage_options

    security.declareProtected('View management screens',
                              'manage_changeParametersForm')
    manage_changeParametersForm = PageTemplateFile(
        'www/archetypesPredicateChange', globals(),
        __name__='manage_changeParametersForm')

    security.declareProtected(manage_properties, 'manage_changeParameters')
    def manage_changeParameters(self, id=None, ns=None, portal_types=None,
                                fields=None, REQUEST=None):
        """ Change the settings of this predicate """

        if id is not None:
            if id != self.getId():
                # Needed for rename in the same transaction as creation.
                get_transaction().commit(1)
                parent = aq_parent(aq_inner(self))
                parent.manage_renameObjects(ids=[self.getId()],
                                            new_ids=[id])
                self = parent._getOb(id)
        if ns is not None:
            self.setNamespace(ns)
        if portal_types is not None:
            self.setEnabledPortalTypes(portal_types)
        if fields is not None:
            self.setFields(fields)

        if REQUEST is not None:
            message = 'Property+Set+Parameters+Changed.'
            REQUEST.RESPONSE.redirect(
                self.absolute_url() + (
                '/manage_changeParametersForm?'
                'manage_tabs_message=%s' % message))
        return self

    security.declareProtected(manage_properties, 'setNamespace')
    def setNamespace(self, ns):
        self._ns = ns

    security.declareProtected(manage_properties, 'setEnabledPortalTypes')
    def setEnabledPortalTypes(self, portal_types):
        self._enabled_portal_types = portal_types

    security.declareProtected(manage_properties, 'setFields')
    def setFields(self, fields):
        self._fields = fields

    security.declareProtected(view, 'getNamespace')
    def getNamespace(self):
        ns = self._ns
        if ns is None:
            name = self.getId().lower()
            ns = 'http://archetypes.org/propsets/%s' % name
        return ns

    security.declareProtected(view, 'getEnabledPortalTypes')
    def getEnabledPortalTypes(self):
        return self._enabled_portal_types or ()

    security.declareProtected(view, 'getFields')
    def getFields(self):
        return self._fields or ()

    def _get_property_sets(self):
        name = self.getId().lower()
        ns = self.getNamespace()
        md = {'xmlns': ns}
        fields = self.getFields()
        return (ArchetypesProperties(name, md, fields),)

    _property_sets = ComputedAttribute(_get_property_sets, 1)

    security.declareProtected(view, 'apply')
    def apply(self, obj):
        if not (Contentish.isImplementedBy(obj) or Folderish.isImplementedBy(obj)):
            return ()
        explicit = aq_base(obj)
        if not getattr(explicit, 'Schema', None):
            return ()
        if not getattr(explicit, 'getPortalTypeName', None):
            return ()
        portal_type = obj.getPortalTypeName()
        if not portal_type in self.getEnabledPortalTypes():
            return ()
        return PropertySetPredicate.apply(self, obj)

registerPredicate('archetypes',
                  'Archetypes Properties',
                  ArchetypesPredicate)
