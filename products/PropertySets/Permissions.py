"""
$Id: Permissions.py 672 2005-03-22 19:03:16Z sidnei $
"""

def fixRolesForMethod(klass, method, roles):
    from AccessControl.PermissionRole import PermissionRole
    old_roles = getattr(klass, '%s__roles__' % method)
    setattr(klass, '%s__roles__' % method,
            PermissionRole(old_roles.__name__, roles))

    perms = getattr(klass, '__ac_permissions__', ())
    new_perms = []
    for perm in perms:
        if method in perm[1]:
            new_methods = list(perm[1])
            del new_methods[new_methods.index(method)]
            if new_methods:
                new_perm = (perm[0], tuple(new_methods))
                if len(perm) > 2:
                    new_perm += (perm[2],)
                new_perms.append(new_perm)
            new_perms.append((perm[0], (method,), roles))
            continue
        new_perms.append(perm)
    klass.__ac_permissions__ = tuple(new_perms)

def fixDefaultRoles(permission, roles):
    from AccessControl.Permission import pname
    from Globals import InitializeClass, ApplicationDefaultPermissions
    import Products

    perms = getattr(Products, '__ac_permissions__', ())
    new_perms = filter(lambda p: p[0] != permission, perms)
    Products.__ac_permissions__=(
        new_perms + ((permission, (), roles),))

    mangled=pname(permission) # get mangled permission name
    setattr(ApplicationDefaultPermissions, mangled, roles)
