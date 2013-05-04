"""
$Id: __init__.py 2004 2008-03-18 16:44:41Z sidnei $
"""

from Products.PropertySets.PropertySetRegistry import registerPredicate, \
     manage_addPropertySetRegistry
from Products.PropertySets.PropertySetPredicate import \
     manage_addPropertySetPredicate

# Import and run monkeypatch, until we get
# a patch into Zope, or Zope 3 comes to save us all.
from Products.PropertySets.monkey import patch
patch()

def initialize(context):
    from Products.PropertySets import PropertySetRegistry
    from Products.PropertySets import PropertySetPredicate

    context.registerClass(
        PropertySetRegistry.PropertySetRegistry,
        permission='Add Property Set Registry',
        constructors=(PropertySetRegistry.manage_addPropertySetRegistry,),
        icon='www/PropertySetRegistry.gif',
        )

    context.registerClass(
        instance_class=PropertySetPredicate.PropertySetPredicate,
        permission='Add Property Set Predicate',
        constructors=PropertySetPredicate.constructors,
        icon='www/PropertySetRegistry.gif')

    # Zope 2.8 doesn't have 'zcml:condition', so we have to
    # conditionally register the adapters for GenericSetup only if
    # GenericSetup is available, by loading the zcml ourselves.
    try:
        from Products.GenericSetup.interfaces import IFilesystemExporter
    except ImportError:
        pass
    else:
        import Products.PropertySets
        from Products.Five.zcml import load_config, load_site
        load_site()
        load_config('adapter.zcml', Products.PropertySets)
        
