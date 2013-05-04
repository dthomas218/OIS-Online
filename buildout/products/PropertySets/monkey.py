"""
$Id: monkey.py 2003 2008-03-17 22:05:06Z sidnei $
"""

def patch():
    from OFS.PropertySheets import DefaultPropertySheets
    old_defaults = DefaultPropertySheets._get_defaults

    def _get_defaults(self):
        """Find PropertySheets using our PropertySetRegistry
        and then append the defaults from Zope.
        """
        prop_sheets = ()
        registry = getattr(self, 'property_set_registry', None)
        if registry is not None:
            # The 'propertysheets' attribute usually
            # is an object which has the real object
            # as it's aq_parent. If it doesn't, then
            # the world has moved from under our feet.
            obj = self.aq_parent
            prop_sheets = registry.getPropSetsFor(obj)
        return old_defaults(self) + prop_sheets

    DefaultPropertySheets._get_defaults = _get_defaults

    # Patch NullResource.MKCOL to be available to Owner,
    # otherwise you need to be Manager to be able to
    # create folders via WebDAV.
    from Products.PropertySets.Permissions import fixDefaultRoles, \
         fixRolesForMethod

    from webdav.NullResource import NullResource
    from AccessControl.Permissions import add_folders

    roles = ('Manager', 'Owner', 'Editor', 'Contributor')
    fixRolesForMethod(NullResource, 'MKCOL', roles)
    fixDefaultRoles(add_folders, roles)
