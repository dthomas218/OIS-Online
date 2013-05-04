"""
$Id: PropertySetPredicate.py 841 2005-11-19 13:29:43Z sidnei $
"""

from OFS.SimpleItem import SimpleItem
from Globals import InitializeClass
from AccessControl import ClassSecurityInfo, getSecurityManager
from AccessControl.Permissions import view, manage_properties
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.PropertySets.Expression import Expression, createExprContext
from Products.PropertySets.PropertySetRegistry import createPredicate, \
     getRegisteredPredicates, registerPredicate
from Products.PropertySets.interfaces.predicate import IPropertySetPredicate

class PropertySetPredicate(SimpleItem):
    """ A Predicate for building property sets.

    Each Predicate is composed of a Expression  which
    is evaluated in the context of the object to
    decide if the Predicate applies, and returns
    a list of PropertySheets to be used for that object.
    """

    meta_type = "Property Set Predicate"
    _property_sets = ()
    security = ClassSecurityInfo()
    __allow_access_to_unprotected_subobjects__ = 0
    __implements__ = (IPropertySetPredicate,)

    manage_options = (
        {'label':'Edit', 'action':'manage_changePredicateForm'},
        ) + SimpleItem.manage_options

    security.declareProtected('View management screens',
      'manage_changePredicateForm', 'manage_main', 'manage')

    manage_changePredicateForm = PageTemplateFile(
        'www/predicateChange', globals(),
        __name__='manage_changePredicateForm')

    manage_changePredicateForm._owner = None
    manage = manage_main = manage_changePredicateForm

    def __init__(self, id, title, expression='', permission=view):
        self.id = id
        self.title = title
        self.setPermission(permission)
        self.setExpression(expression)

    security.declareProtected(view, 'apply')
    def apply(self, obj):
        """ Evaluate expression using the object as
        context and return PropertySheets as applicable.
        """
        if not getSecurityManager().checkPermission(self.getPermission(), obj):
            return ()
        # If there's no expression set, return immediately.
        if not self.getExpression():
            return self.getPropertySets(obj)
        # If there's a expression, then evaluate it.
        context = createExprContext(obj)
        if self.expression(context):
            return self.getPropertySets(obj)
        return ()

    security.declareProtected(view, 'getPropertySets')
    def getPropertySets(self, obj):
        """ Return PropertySheets that apply to the
        given object
        """
        return self._property_sets

    # Ah, if I only had descriptors and the
    # Zope 3 securitymachinery....

    security.declareProtected(manage_properties, 'setExpression')
    def setExpression(self, expression):
        """ Change the expression """
        self._expression_text = expression
        self._expression = Expression(expression)

    security.declareProtected(view, 'expression')
    def expression(self, context):
        """ Evaluate the expression using context """
        return self._expression(context)

    security.declareProtected(view, 'getExpression')
    def getExpression(self):
        """ Get the expression as text """
        return self._expression_text

    security.declareProtected(manage_properties, 'setPermission')
    def setPermission(self, permission):
        """ Change the current permission """
        self._permission = permission

    security.declareProtected(view, 'getPermission')
    def getPermission(self):
        """ Get the permission """
        return self._permission

    security.declareProtected(manage_properties, 'manage_changePredicate')
    def manage_changePredicate(self, expression=None,
                              permission=None, REQUEST=None):
        """ Change the settings of this predicate """

        if expression is not None:
            self.setExpression(expression)
        if permission is not None:
            self.setPermission(permission)

        if REQUEST is not None:
            message = 'Predicate Constraints Changed.'
            return self.manage_changePredicateForm(
                manage_tabs_message=message)
        return self

registerPredicate('null_predicate', 'Null Predicate', PropertySetPredicate)

InitializeClass(PropertySetPredicate)

def manage_addPropertySetPredicate(self, id, expression,
                                   permission, REQUEST=None):
    """ Factory method that creates a Property Set Predicate"""
    obj = createPredicate(id, expression, permission)
    self._setObject(obj.id, obj)

    if REQUEST is not None:
        REQUEST['RESPONSE'].redirect(self.absolute_url()+'/manage_main')

    return self._getOb(obj.id)

def manage_availablePredicates(self):
    return getRegisteredPredicates()

def manage_possiblePermissions(self):
    # possible_permissions is in AccessControl.Role.RoleManager.
    return self.possible_permissions()

manage_addPropertySetPredicateForm = PageTemplateFile(
    'www/predicateAdd', globals(),
    __name__='manage_addPropertySetPredicateForm')

constructors = (
  ('manage_addPropertySetPredicateForm', manage_addPropertySetPredicateForm),
  ('manage_addPropertySetPredicate', manage_addPropertySetPredicate),
  ('manage_availablePredicates', manage_availablePredicates),
  ('manage_possiblePermissions', manage_possiblePermissions),
)
