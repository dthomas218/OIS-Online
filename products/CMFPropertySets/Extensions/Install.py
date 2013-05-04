from StringIO import StringIO
from Products.CMFCore.utils import getToolByName
from Products.PropertySets import PropertySetRegistry
from Products.PropertySets import manage_addPropertySetRegistry, \
     manage_addPropertySetPredicate
add_registry = manage_addPropertySetRegistry
add_predicate = manage_addPropertySetPredicate
tool_id = PropertySetRegistry.PropertySetRegistry.id

try:
    from Products.CMFCore.permissions import View
except ImportError:
    from Products.CMFCore.CMFCorePermissions import View

def install_tool(self, out):
    tool = getToolByName(self, tool_id, None)
    if tool is not None:
        out.write('Property Set Registry was already installed.\n')
        return
    add_registry(self)
    out.write('Property Set Registry installed sucessfully.\n')

def install_predicates(self, out):
    tool = getToolByName(self, tool_id)
    ids = ('dublincore', 'dcworkflow', 'vocabulary', 'cmf')
    for id in ids:
        if id in tool.objectIds():
            out.write('Property Set %s was already installed.\n' % id)
        else:
            add_predicate(tool, id=id,
                          expression='',
                          permission=View,
                          REQUEST=None)
        out.write('Property Set %s installed sucessfully.\n' % id)

def install(self, out=None):
    if out is None:
        out = StringIO()

    install_tool(self, out)
    install_predicates(self, out)

    return out.getvalue()
