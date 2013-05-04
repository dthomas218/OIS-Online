"""
$Id: profile.py 1341 2007-09-19 18:44:01Z sidnei $
"""

from StringIO import StringIO

from zope.interface import implements

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
from Products.PageTemplates.PageTemplateFile import PageTemplateFile

TOOL_ID = 'property_set_registry'
from Products.PropertySets.PropertySetRegistry import createPredicate

_FILENAME = 'property-set-registry.xml'

def _getRegistry(site):
    registry = site._getOb(TOOL_ID, None)

    if registry is None:
        raise ValueError, 'PropertySet Registry Not Found'

    return registry

def exportPropertySetRegistry(context):
    """ Export PropertySets registry as an XML file.

    o Designed for use as a GenericSetup export step.
    """
    registry = _getRegistry(context.getSite())
    exporter = PropertySetRegistryExporter(registry).__of__(registry)
    xml = exporter.generateXML()
    context.writeDataFile(_FILENAME, xml, 'text/xml')
    return 'PropertySets Registry exported.'

def _updatePropertySetRegistry(registry, xml, should_purge, encoding=None):

    if should_purge:
        registry.manage_delObjects(ids=list(registry.objectIds()))

    importer = PropertySetRegistryImporter(registry, encoding)
    reg_info = importer.parseXML(xml)

    for info in reg_info['predicates']:
        if registry.hasObject(info['id']):
            registry.manage_delObjects(ids=[info['id']])
        obj = createPredicate(info['id'], info['expression'], 
                              info['permission'])
        if info.get('title', '') and obj.title != info['title']:
            obj.title = info['title']
        registry._setObject(obj.getId(), obj)

def importPropertySetRegistry(context):
    """ Import PropertySets registry from an XML file.

    o Designed for use as a GenericSetup import step.
    """
    registry = _getRegistry(context.getSite())
    encoding = context.getEncoding()

    xml = context.readDataFile(_FILENAME)
    if xml is None:
        return 'Site properties: Nothing to import.'

    _updatePropertySetRegistry(registry, xml, context.shouldPurge(), encoding)
    return 'PropertySets Registry imported.'

class PropertySetRegistryExporter(ExportConfiguratorBase):

    def __init__(self, context, encoding=None):
        ExportConfiguratorBase.__init__(self, None, encoding)
        self.context = context

    def _getExportTemplate(self):
        return PageTemplateFile('xml/psrExport.xml', globals())

    def listPredicates(self):
        for predicate in self.context.objectValues():
            info = {}
            info['id'] = predicate.getId()
            info['title'] = predicate.title_or_id()
            info['expression'] = predicate.getExpression()
            info['permission'] = predicate.getPermission()
            yield info

class PropertySetRegistryImporter(ImportConfiguratorBase):

    def __init__(self, context, encoding=None):
        ImportConfiguratorBase.__init__(self, None, encoding)
        self.context = context

    def _getImportMapping(self):

        return {
          'property-set-registry':
              {'predicate':        {KEY: 'predicates', DEFAULT: ()},
               },
          'predicate':
              {'id':               {KEY: 'id'},
               'title':            {KEY: 'title'},
               'expression':       {KEY: 'expression'},
               'permission':       {KEY: 'permission'},
               },
         }

class PropertySetRegistryFileExportImportAdapter(object):
    """ Designed for use when exporting / importing within a container.
    """
    implements(IFilesystemExporter, IFilesystemImporter)

    def __init__(self, context):
        self.context = context

    def export(self, export_context, subdir, root=False):
        """ See IFilesystemExporter.
        """
        context = self.context
        exporter = PropertySetRegistryExporter(context).__of__(context)
        xml = exporter.generateXML()
        export_context.writeDataFile(_FILENAME,
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
        data = import_context.readDataFile(_FILENAME, subdir)
        if data is None:
            import_context.note('SGAIFA',
                                'no %s in %s' % (_FILENAME, subdir))
        else:
            request = FauxDAVRequest(BODY=data, BODYFILE=StringIO(data))
            response = FauxDAVResponse()
            _updatePluginRegistry(self.context,
                                  data,
                                  import_context.shouldPurge(),
                                  import_context.getEncoding(),
                                 )
