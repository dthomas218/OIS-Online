"""
$Id: profile.py 1341 2007-09-19 18:44:01Z sidnei $
"""

from StringIO import StringIO

from zope.interface import implements, Interface

from OFS.CopySupport import CopyError
from AccessControl import Permissions as perms
from AccessControl import Unauthorized
from Acquisition import aq_base
from DateTime.DateTime import DateTime
from Products.CMFCore.utils import getToolByName
from Products.ShellExServer.config import *
from Products.ShellExServer.normalize import install_hook

try:
    from Products.CMFCore.interfaces import ISiteRoot
except ImportError: # Plone 2.1
    ISiteRoot = None

try:
    from Products.CMFCore.permissions import View, ModifyPortalContent
    from Products.CMFCore.permissions import AccessContentsInformation
except:
    from Products.CMFCore.CMFCorePermissions import View, ModifyPortalContent
    from Products.CMFCore.CMFCorePermissions import AccessContentsInformation

from Products.PageTemplates.PageTemplateFile import PageTemplateFile

try:
    from Products.GenericSetup.interfaces import IFilesystemExporter
    from Products.GenericSetup.interfaces import IFilesystemImporter
    from Products.GenericSetup.content import FauxDAVRequest
    from Products.GenericSetup.content import FauxDAVResponse
    from Products.GenericSetup.utils import ExportConfiguratorBase
    from Products.GenericSetup.utils import ImportConfiguratorBase
    from Products.GenericSetup.utils import _getDottedName
    from Products.GenericSetup.utils import _resolveDottedName
    from Products.GenericSetup.utils import CONVERTER
    from Products.GenericSetup.utils import DEFAULT
    from Products.GenericSetup.utils import KEY
except ImportError: # Plone 2.1
    IFilesystemImporter = IFilesystemExporter = Interface
    ExportConfiguratorBase = ImportConfiguratorBase = object

TOOL_ID = 'property_set_registry'
VOCAB_ID = 'vocabulary'

_GLOBAL_VOCAB_FNAME = 'global-vocabulary-registry.xml'
_LOCAL_VOCAB_FNAME = 'local-vocabulary-registry.xml'

def createVocab(registry, name):
    add = registry.manage_addProduct['ShellExServer']
    constructor = getattr(add, 'manage_add%s' % name)
    constructor(registry)

def _getGlobalVocab(site):
    registry = site._getOb(VOCAB_ID, None)

    if registry is None:
        raise ValueError, 'Global Vocabulary Not Found'

    return registry

def _getLocalVocab(site):
    pr = site._getOb(TOOL_ID, None)

    if pr is None:
        raise ValueError, 'Property Set Registry Not Found'

    registry = pr._getOb(VOCAB_ID, None)

    if registry is None:
        raise ValueError, 'Local Vocabulary Not Found'

    return registry

def exportVocabRegistry(context, name, _getRegistry, _FILENAME):
    """ Export Vocabulary Registry as an XML file.

    o Designed for use as a GenericSetup export step.
    """
    registry = _getRegistry(context.getSite())
    exporter = RegistryExporter(registry).__of__(registry)
    xml = exporter.generateXML()
    context.writeDataFile(_FILENAME, xml, 'text/xml')
    return '%s Vocabulary Registry exported.' % name

def exportGlobalVocabRegistry(context):
    return exportVocabRegistry(context, 'Global', 
                               _getGlobalVocab, _GLOBAL_VOCAB_FNAME)

def exportLocalVocabRegistry(context):
    return exportVocabRegistry(context, 'Local', 
                               _getLocalVocab, _LOCAL_VOCAB_FNAME)

def _updateVocabRegistry(registry, xml, should_purge, encoding=None):

    if should_purge:
        registry.manage_delObjects(ids=list(registry.objectIds()))

    importer = RegistryImporter(registry, encoding)
    reg_info = importer.parseXML(xml)

    for info in reg_info['providers']:
        if registry.hasObject(info['id']):
            registry.manage_delObjects(ids=[info['id']])
        createVocab(registry, info['name'])

def importVocabRegistry(context, name, _getRegistry, _FILENAME):
    """ Import Vocabulary Registry from an XML file.

    o Designed for use as a GenericSetup import step.
    """
    registry = _getRegistry(context.getSite())
    encoding = context.getEncoding()

    xml = context.readDataFile(_FILENAME)
    if xml is None:
        return '%s Vocabulary Registry: Nothing to import.' % name

    _updateVocabRegistry(registry, xml, context.shouldPurge(), encoding)
    return '%s Vocabulary Registry imported.' % name

def importGlobalVocabRegistry(context):
    return importVocabRegistry(context, 'Global', 
                               _getGlobalVocab, _GLOBAL_VOCAB_FNAME)

def importLocalVocabRegistry(context):
    return importVocabRegistry(context, 'Local', 
                               _getLocalVocab, _LOCAL_VOCAB_FNAME)

class RegistryExporter(ExportConfiguratorBase):

    def __init__(self, context, encoding=None):
        ExportConfiguratorBase.__init__(self, None, encoding)
        self.context = context

    def _getExportTemplate(self):
        return PageTemplateFile('xml/vocabExport.xml', globals())

    def listProviders(self):
        for predicate in self.context.objectValues():
            info = {}
            info['id'] = predicate.getId()
            info['name'] = predicate.__class__.__name__
            yield info

class RegistryImporter(ImportConfiguratorBase):

    def __init__(self, context, encoding=None):
        ImportConfiguratorBase.__init__(self, None, encoding)
        self.context = context

    def _getImportMapping(self):

        return {
          'vocabulary-registry':
              {'provider':        {KEY: 'providers', DEFAULT: ()},
               },
          'provider':
              {'id':               {KEY: 'id'},
               'name':             {KEY: 'name'},
               },
         }

class RegistryFileExportImportAdapter(object):
    """ Designed for use when exporting / importing within a container.
    """
    implements(IFilesystemExporter, IFilesystemImporter)

    def __init__(self, context):
        self.context = context

    def export(self, export_context, subdir, root=False):
        """ See IFilesystemExporter.
        """
        context = self.context
        exporter = RegistryExporter(context).__of__(context)
        xml = exporter.generateXML()
        export_context.writeDataFile(self._FILENAME,
                                     xml,
                                     'text/xml',
                                     subdir,
                                    )

    def listExportableItems(self):
        """ See IFilesystemExporter.
        """
        return ()

    def import_(self, import_context, subdir, root=False):
        """ See IFilesystemImporter.
        """
        data = import_context.readDataFile(self._FILENAME, subdir)
        if data is None:
            import_context.note('SGAIFA',
                                'no %s in %s' % (self._FILENAME, subdir))
        else:
            request = FauxDAVRequest(BODY=data, BODYFILE=StringIO(data))
            response = FauxDAVResponse()
            _updateVocabRegistry(self.context,
                                 data,
                                 import_context.shouldPurge(),
                                 import_context.getEncoding(),
                                 )

class GlobalVocabRegistryFEIA(RegistryFileExportImportAdapter):
    _FILENAME = _GLOBAL_VOCAB_FNAME

class LocalVocabRegistryFEIA(RegistryFileExportImportAdapter):
    _FILENAME = _LOCAL_VOCAB_FNAME


def importVarious(context):
    out = StringIO()
    
    # Check if it's the portal or a ImportContext
    if ISiteRoot and not ISiteRoot.providedBy(context):
        # Only run step if a flag file is present
        if context.readDataFile('enfold-desktop-extra.txt') is None:
            return

        context = context.getSite()

    # Purge the contents of the Content Type Registry, until they fix
    # it to allow purging some other way.
    ctr = getToolByName(context, 'content_type_registry')
    ctr.__init__()

    install_root_error(context, out)
    fix_workflows(context, out)
    install_hook(context, out, adding=True)
    fix_members_folder(context, out)

    return out.getvalue()

def removeVarious(context):
    out = StringIO()

    # Check if it's the portal or a ImportContext
    if ISiteRoot and not ISiteRoot.providedBy(context):
        context = context.getSite()

    # The name is misleading, it's actually removing. :)
    install_hook(context, out, adding=False)
    restore_root_error(context, out)
    remove_cp(context, out)

    return out.getvalue()

DAV_PERMS_1 = (perms.webdav_lock_items,
               perms.webdav_unlock_items)
DAV_PERMS_1_FROM = ModifyPortalContent

DAV_PERMS_2 = (perms.webdav_access,)
DAV_PERMS_2_FROM = AccessContentsInformation

def fix_workflows(self, out):
    wt = getToolByName(self, 'portal_workflow')
    for wf_id, wf in wt.objectItems():
        out.write(('Verifying workflow %r for missing  '
                   'WebDAV-related permissions.\n' % wf_id))
        perms = getattr(wf, 'permissions', None)
        if perms is None:
            continue
        for perm in DAV_PERMS_1 + DAV_PERMS_2:
            if not perm in perms:
                wf.addManagedPermission(perm)
                out.write(('Added managed permission %r '
                           'to %s.\n' % (perm, wf_id)))

        states = getattr(wf, 'states', None)
        if states is None:
            continue

        fix_perms(states, DAV_PERMS_1_FROM, DAV_PERMS_1, out)
        fix_perms(states, DAV_PERMS_2_FROM, DAV_PERMS_2, out)

    out.write(('Finished fixing WebDAV-related '
               'permissions on all workflows.\n'))

def fix_perms(states, from_perm, dav_perms, out):
    for state in states.objectValues():
        for perm in dav_perms:
            # this is a temporary workaround for #13 which
            # doesnt make sense, the State object in DCWorkflow
            # has a permissions role setting, so why would an AttributeError
            # be raised?
            #
            # Following client feedback with more info we should fix this
            if not hasattr(state, "permission_roles"):
                continue
            if not state.permission_roles:
                continue
            roles = state.permission_roles.get(from_perm, None)
            if roles is None:
                continue

            if 'Anonymous' in roles:
                roles = list(roles)
                roles.remove('Anonymous')
                roles.append('Authenticated')
                roles = tuple(roles)

            settings = {'acquired': 0,
                        'permission': perm,
                        'roles': roles}

            state.setPermission(**settings)
            out.write(('Updated permission mappings '
                       'of permission %r to match permission %r '
                       'on state %r.\n' % (perm, from_perm, state.getId())))

def fix_members_folder(self, log):
    mt = getToolByName(self, 'portal_membership')
    m = mt.getMembersFolder()
    if m is None:
        # No members folder
        log.write('No members folder')
        return
    kind = getattr(aq_base(m), '_at_type_subfolder', None)
    allowed = getattr(m, 'getImmediatelyAddableTypes', None)
    if kind is None:
        kind = m.getPortalTypeName()
        if allowed is not None:
            allowed = allowed()
        else:
            # Folder is always allowed... right?
            allowed = ('Folder',)
        if kind not in allowed:
            kind = 'Folder'
        if kind in allowed:
            m._at_type_subfolder = kind
            log.write('Set subfolder type of %r to %r' % (
                '/'.join(m.getPhysicalPath()), kind))

def install_root_error(self, log):
    import os
    from Products import ShellExServer
    dr = os.path.join(os.path.dirname(ShellExServer.__file__))
    py_data = open(os.path.join(dr, 'skins', 'standard_error_message.py')).read()
    pt_data = open(os.path.join(dr, 'skins', 'webdav_error_message.pt')).read()

    zope = self.unrestrictedTraverse('/')
    root_ids = zope.objectIds()

    try:
        # rename the standard_error_message
        if ('standard_error_message' in root_ids and
            zope.standard_error_message.meta_type == 'DTML Method'):
            zope.manage_renameObjects(['standard_error_message',],
                                      ['default_error_message'])
    except CopyError:
        raise Unauthorized(
            "To install ShellExServer you must be using a user "
            "account that has the Manager role at the root of "
            "your Zope site. The current user does not have "
            "this role. It is possible to be a Manager of a Plone "
            "site, without being having the Manager of the Zope site.")

    check = ('standard_error_message', 'webdav_error_message')
    todo = []

    # if standard_error_message
    # has already been moved if in existed and was a DTML Method
    # so re get the object ids
    root_ids = zope.objectIds()
    for id in check:
        if id in root_ids:
            todo.append(id)
    if todo:
        zope.manage_delObjects(ids=todo)

    pyadd = zope.manage_addProduct['PythonScripts']
    pyadd.manage_addPythonScript(id='standard_error_message')
    err = zope.standard_error_message
    err.write(py_data)
    ptadd = zope.manage_addProduct['PageTemplates']
    ptadd.manage_addPageTemplate(id='webdav_error_message')
    webdav = zope.webdav_error_message
    webdav.pt_edit(pt_data, 'text/html')
    log.write("Root error handlers configured.\n")

def remove_cp(self, out=None):
    cp = getToolByName(self, 'portal_controlpanel', None)

    if cp is None:
        return

    # Plone Desktop has been renamed Enfold Desktop
    cp.unregisterConfiglet('Plone Desktop')
    cp.unregisterConfiglet('Enfold Desktop')
    print >> out, 'Removing Enfold Desktop Control Panel'

    ai = getToolByName(self, 'portal_actionicons', None)
    if ai is None:
        return

    if ai._lookup.get(("controlpanel", "Enfold Desktop")):
        print >> out, 'Removing icon for Enfold Desktop Control Panel'
        ai.removeActionIcon("controlpanel", "Enfold Desktop")

def restore_root_error(self, log):
    zope = self.unrestrictedTraverse('/')
    root_ids = zope.objectIds()

    if not ('default_error_message' in root_ids and
        zope.default_error_message.meta_type == 'DTML Method'):
        print >> log, 'default_error_message not found, nothing to restore'
        return

    check = ('standard_error_message', 'webdav_error_message')
    todo = []

    for id in check:
        if id in root_ids:
            todo.append(id)
    if todo:
        print >> log, 'Removing custom error scripts: %s' % ', '.join(todo)
        zope.manage_delObjects(ids=todo) 
    
    try:
        # rename the 'default_error_message' back to 'standard_error_message'
        zope.manage_renameObjects(['default_error_message',],
                                  ['standard_error_message'])
        print >> log, 'Restored original standard_error_message'
    except CopyError:
        msg = ("To uninstall ShellExServer you must be using a user "
               "account that has the Manager role at the root of "
               "your Zope site. The current user does not have "
               "this role. It is possible to be a Manager of a Plone "
               "site, without being having the Manager of the Zope site.")
        print >> log, msg
        raise Unauthorized(msg)
