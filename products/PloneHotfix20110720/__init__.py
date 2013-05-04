from AccessControl.PermissionRole import PermissionRole
import Products.CMFPlone

import logging
logger = logging.getLogger('PloneHotfix20110720')


class PatchTarget(object):
    
    klass = None
    methods = ()
    
    set_roles = ('Manager',)
    kill_docstrings = False
    
    def __init__(self, klass, **kw):
        self.klass = klass
        self.__dict__.update(kw)


targets = [
    PatchTarget('Products.Archetypes.ReferenceEngine.ReferenceCatalog',
                kill_docstrings = True),
    PatchTarget('Products.Archetypes.Referenceable.Referenceable',
                kill_docstrings = True),
    PatchTarget('Products.ZCatalog.ZCatalog.ZCatalog',
                kill_docstrings = True, methods=['getMetadataForRID',
                'getMetadataForUID', 'getIndexDataForRID', 'getIndexDataForUID',
                'getrid', 'resolve_path']),
    PatchTarget('Products.PluggableAuthService.PluggableAuthService.PluggableAuthService',
                methods='monkeys'),
    PatchTarget('Products.PortalTransforms.TransformEngine.TransformTool',
                methods=('convertTo', 'registerTransform', 'unregisterTransform'),
                set_roles=()),
    PatchTarget('Products.PortalTransforms.Transform.Transform',
                methods=('convert',),
                set_roles=()),
    PatchTarget('Products.PlonePAS.plugins.user.UserManager',
                set_roles=PermissionRole('Manage users', ('Manager',))),
    PatchTarget('Products.PlonePAS.plugins.property.ZODBMutablePropertyProvider',
                methods=('deleteUser', 'enumerateUsers')),
    PatchTarget('Products.CMFPlone.PropertiesTool.PropertiesTool',
                methods=('addPropertySheet',)),
    PatchTarget('Products.CMFQuickInstallerTool.QuickInstallerTool.QuickInstallerTool',
                methods=('isProductInstalled',)),
    PatchTarget('plone.app.customerize.tool.ViewTemplateContainer'),
    ]


def get_klass(dottedname):
    parts = dottedname.split('.')
    klassname = parts.pop()
    modulename = '.'.join(parts)
    try:
        return getattr(__import__(modulename, [], [], [klassname]), klassname)
    except:
        raise ImportError


def initialize(context):
    from Products.PloneHotfix20110720.publisher import install_patch
    install_patch()
    
    for target in targets:
        try:
            klass = get_klass(target.klass)
        except ImportError:
            continue
        
        for k,v in klass.__dict__.items():
            if target.methods == 'monkeys':
                modname = getattr(v, '__module__', '') or ''
                if klass.__module__ == modname:
                    continue
            elif target.methods and k not in target.methods:
                continue

            if not callable(v):
                continue
            if k.startswith('_'):
                continue

            roles = getattr(klass, '%s__roles__' % k, None)
            if roles is None:
                if target.kill_docstrings:
                    if getattr(v, '__doc__', None):
                        try:
                            del v.__doc__
                        except:
                            pass
                        try:
                            del v.im_func.__doc__
                        except:
                            pass
                else:
                    setattr(klass, '%s__roles__' % k, target.set_roles)

    logger.info('Hotfix installed.')
