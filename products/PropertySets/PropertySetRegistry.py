"""
$Id: PropertySetRegistry.py 1341 2007-09-19 18:44:01Z sidnei $
"""

from zope.interface import implements

from OFS.Folder import Folder
from Globals import PersistentMapping, InitializeClass
from AccessControl import ClassSecurityInfo
from AccessControl.Permissions import view, manage_properties

from Products.PropertySets.interfaces.predicate import IPropertySetPredicate
from Products.PropertySets.interfaces.registry import IPropertySetRegistry

class RegistryItem:

    def __init__(self, name, title, factory):
        self.name = name
        if not title:
            title = name
        self.title = title
        self.factory = factory

    def info(self):
        return {'name':self.name,
                'title':self.title}

    def create(self, expression, permission):
        return self.factory(self.name, self.title, expression, permission)

registry = {}
def registerPredicate(name, title, component):
    registry[name] = RegistryItem(name, title, component)

def getRegisteredPredicates():
    return [item.info() for item in registry.values()]

def createPredicate(name, expression, permission):
    return registry[name].create(expression, permission)

class PropertySetRegistry(Folder):
    """ A registry that allows attaching PropertySheets to
    normal objects in a pluggable and dynamic fashion.

    One of the purposes of attaching PropertySheets to objects
    is that Zope's WebDAV implementation of PROPFIND looks
    for PropertySheets when building the XML response.
    """

    meta_type = 'Property Set Registry'
    id = 'property_set_registry'
    security = ClassSecurityInfo()
    implements(IPropertySetRegistry)

    def __init__(self, id='', title=''):
        Folder.__init__(self, self.id)
        self.title = title or self.meta_type

    security.declareProtected(view, 'all_meta_types')
    def all_meta_types(self):
        return Folder.all_meta_types(self, interfaces=(IPropertySetPredicate,))

    security.declareProtected(view, 'getPropSetsFor')
    def getPropSetsFor(self, obj):
        sets = []
        for predicate in self.objectValues():
            sets.extend(predicate.apply(obj))
        return tuple(sets)

InitializeClass(PropertySetRegistry)

def manage_addPropertySetRegistry(self, REQUEST=None, **ignored):
    """ Factory method that creates a Property Set Registry"""
    obj = PropertySetRegistry()
    self._setObject(obj.id, obj)

    if REQUEST is not None:
        REQUEST['RESPONSE'].redirect(self.absolute_url()+'/manage_main')
    else:
        return self._getOb(obj.id)
