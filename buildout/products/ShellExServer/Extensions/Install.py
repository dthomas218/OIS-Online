# Enfold Desktop
# Copyright(C), 2004-2006, Enfold Systems, Inc. - ALL RIGHTS RESERVED

# Enfold Systems, Inc.
# 4617 Montrose Blvd., Suite C215
# Houston, Texas 77006 USA
# p. +1 713.942.2377 | f. +1 832.201.8856
# www.enfoldsystems.com
# info@enfoldsystems.com

# $Id: Install.py 8844 2008-09-10 16:59:12Z sidnei $

from cStringIO import StringIO
from OFS.CopySupport import CopyError
from Products.CMFCore.DirectoryView import createDirectoryView
from AccessControl import Permissions as perms
from AccessControl import Unauthorized
from DateTime.DateTime import DateTime
from Products.CMFCore.utils import getToolByName
from Products.CMFCore import ContentTypeRegistry
from Products.ShellExServer.config import *
from Products.ShellExServer.normalize import install_hook
from Products.ShellExServer.profile import fix_workflows, fix_members_folder
from Products.ShellExServer.profile import install_root_error
from Products.ShellExServer.profile import removeVarious

from Products.PropertySets import PropertySetRegistry
from Products.PropertySets import manage_addPropertySetRegistry, \
     manage_addPropertySetPredicate

try:
    from Products.CMFCore.permissions import View
except:
    from Products.CMFCore.CMFCorePermissions import View

add_registry = manage_addPropertySetRegistry
add_predicate = manage_addPropertySetPredicate
tool_id = PropertySetRegistry.PropertySetRegistry.id

class foo: pass

def install_tool(self, out):
    tool = getToolByName(self, tool_id, None)
    if tool is not None:
        out.write('Property Set Registry was already installed.\n')
        return
    add_registry(self)
    out.write('Property Set Registry installed sucessfully.\n')

def install_predicates(self, out, ids=('fsattrs', 'sharing', 'permissions',
                                       'vocabulary', 'addables')):
    tool = getToolByName(self, tool_id)
    for id in ids:
        if id in tool.objectIds():
            out.write('Property Set %s was already installed.\n' % id)
        else:
            add_predicate(tool, id=id,
                          expression='',
                          permission=View,
                          REQUEST=None)
        out.write('Property Set %s installed sucessfully.\n' % id)

DAV_PERMS_1 = (perms.webdav_lock_items,
               perms.webdav_unlock_items)
STATE_ROLES_1 = {
    'private':{'acquired':0,
               'roles':['Manager', 'Owner', 'Reviewer']},
    'visible':{'acquired':0,
               'roles':['Manager', 'Owner', 'Reviewer']},
    'pending':{'acquired':0,
               'roles':['Manager', 'Owner', 'Reviewer']},
    'published':{'acquired':0,
                 'roles':['Manager', 'Owner', 'Reviewer']},
    }

DAV_PERMS_2 = (perms.webdav_access,)
STATE_ROLES_2 = {
    'private':{'acquired':0,
               'roles':['Manager', 'Owner', 'Reviewer']},
    'visible':{'acquired':0,
               'roles':['Authenticated', 'Manager', 'Owner', 'Reviewer']},
    'pending':{'acquired':0,
               'roles':['Authenticated', 'Manager', 'Owner', 'Reviewer']},
    'published':{'acquired':0,
                 'roles':['Authenticated', 'Manager', 'Owner', 'Reviewer']},
    }

def install_ctr_predicates(self, out):
    predicates = {
        'ExtensionPredicate':[
        ('Document', 'txt'),
        ('Document', 'rst'),
        ('Document', 'stx'),
        ('Document', 'htm'),
        ('Document', 'html'),
        ('File', 'bin'),
        ('Image', 'gif'),
        ('Image', 'ico'),
        ('Image', 'bmp'),
        ('Image', 'png'),
        ('Image', 'jpg'),
        ('Event', 'evt'), # Backwards compatibility
        ('Event', 'ics'),
        ('Link', 'url'),
        # Not really useful, its just so that
        # the action shows up at the client
        # side if we can add folders.
        ('Folder', 'fld'),
        ]}

    seen_types = {}
    ctr = getToolByName(self, 'content_type_registry')
    for p, info in predicates.items():
        p = getattr(ContentTypeRegistry, p)
        for t, ext in info:
            n_type = t.lower().replace(' ', '_')
            p_type = p.PREDICATE_TYPE
            p_id = "%s_%s_%s" % (n_type, p_type, ext)

            if ctr.getPredicate(p_id) is not None:
                out.write(' * Predicate with id %s already '
                          'existed, replacing.\n' % p_id)
                ctr.removePredicate(p_id)

            ctr.addPredicate(p_id, p_type)
            p_dict = foo()
            setattr(p_dict, 'portal_type_name', t)
            setattr(p_dict, 'extensions', ext)
            ctr.updatePredicate(p_id, p_dict, t)
            out.write(' * Added predicate %s with '
                      'id %s to type %s.\n' % (p_type, p_id, t))
            ctr.reorderPredicate(p_id, 0)

            if t in seen_types:
                # Already added header predicate for this one, skip.
                continue

            # Now, add also a 'header predicate' to match on the
            # header sent by Enfold Desktop in addition to extension.
            seen_types[t] = None
            p_type = 'request_header'
            p_id = "%s_%s" % (n_type, p_type)

            if ctr.getPredicate(p_id) is not None:
                out.write(' * Predicate with id %s already '
                          'existed, replacing.\n' % p_id)
                ctr.removePredicate(p_id)

            ctr.addPredicate(p_id, p_type)
            p_dict = foo()
            setattr(p_dict, 'portal_type_name', t)
            setattr(p_dict, 'header_name', HEADER_NAME)
            ctr.updatePredicate(p_id, p_dict, t)
            out.write(' * Added predicate %s with '
                      'id %s to type %s.\n' % (p_type, p_id, t))
            ctr.reorderPredicate(p_id, 0)

    # Fix for a typo made early on in this installer.
    p_id = 'catch_all',
    if p_id in ctr.predicate_ids:
        ctr.removePredicate(p_id)

    # Add a 'catch all' default predicate that maps to 'File' so that
    # we don't get a stupid 'DTML Document' for unknown
    # extensions/content types.
    p_id = 'catch_all'
    p_type = 'name_regex'
    t = 'File'
    if not p_id in ctr.predicate_ids:
        ctr.addPredicate(p_id, p_type)
        p_dict = foo()
        p_dict.pattern = '.*'
        ctr.updatePredicate(p_id, p_dict, t)
        out.write(' * Added predicate %s with '
                  'id %s to type %s.\n' % (p_type, p_id, t))

def install_vocabularies(self, vocab, names, out):
    add = self.manage_addProduct['ShellExServer']
    __traceback_info__ = (vocab, names, dir(add))
    for name in names:
        if name.lower() in vocab.objectIds():
            out.write('Vocabulary %r was already installed.\n' % name)
            continue
        constructor = getattr(add, 'manage_add%s' % name)
        constructor(vocab)
        out.write('Vocabulary %r installed sucessfully.\n' % name)

def install_global_vocabs(self, names, out):
    vocab = getToolByName(self, 'vocabulary', None)
    if vocab is None:
        add_predicate(self, id='vocabulary',
                      expression='',
                      permission=View,
                      REQUEST=None)
        vocab = getToolByName(self, 'vocabulary')
    install_vocabularies(self, vocab, names, out)

def install_local_vocabs(self, names, out):
    tool = getToolByName(self, 'property_set_registry')
    vocab = getattr(tool, 'vocabulary')
    install_vocabularies(self, vocab, names, out)

def install_actions(self, out=None):
    # Add in View in Browser everywhere
    # Add View in Enfold Desktop to everywhere
    pa = getToolByName(self, 'portal_actions')
    pt = getToolByName(self, 'portal_types')

    action_ids = ('desktop_view', 'view_in_plone')
    found = {}
    for idx, action in enumerate(pa.listActions()):
        if action.id in action_ids:
            found[action.id] = idx

    # If any old action existed, remove them, we're going to re-add.
    if found.values():
        pa.deleteActions(found.values())

    pa.addAction(
        'desktop_view',
        'Edit using Enfold Desktop',
        "string:${object_url}/plone_desktop_config.plonecmd",
        '', #condition
        'WebDAV access',
        'document_actions',
        1)

    # Use a helper function registered as constructor in the
    # ShellExServer product.
    pa.addAction(
        'view_in_plone',
        'View in Browser',
        "string:${object/manage_addProduct/ShellExServer/view_path}",
        '', # condition
        'View',
        'desktop_action',
        1)

    ai = getToolByName(self, 'portal_actionicons')

    if not ai._lookup.get(("plone", "desktop_view")):
        ai.addActionIcon("plone", "desktop_view",
            "windows_explorer.gif",
            title="Edit using Enfold Desktop")

    # The view_in_plone action used to be added to each
    # portal_type. However, that poses a problem because newly-added
    # types wouldn't get the action in their context menu and the user
    # would have to add the manually.  Now, we remove them if found
    # and add a 'global' action in the 'portal_actions' tool.
    aid = "view_in_plone"
    condition = ''
    for typ in pt.listContentTypes():
        t = getattr(pt, typ)

        remove = []
        for idx, action in enumerate(t.listActions()):
            if action.id == aid:
                remove.append(idx)
        t.deleteActions(remove)

    out.write("Added actions.\n")

def install_skin(self, log):
    out = []
    typesTool = getToolByName(self, 'portal_types')
    skinsTool = getToolByName(self, 'portal_skins')

    layer_name = "shellex_server"
    layer_location = "ShellExServer/skins"

    # add in the directory view pointing to our skin
    if layer_name not in skinsTool.objectIds():
        createDirectoryView(skinsTool, layer_location, layer_name)
        out.append('Added "%s" directory view to portal_skins' % layer_name)

    # add in the layer to all our skins
    skins = skinsTool.getSkinSelections()
    for skin in skins:
        path = skinsTool.getSkinPath(skin)
        path = [ p.strip() for p in path.split(',') ]
        if layer_name not in path:
            # Don't bomb if 'custom' is not in skin path.
            if 'custom' in path:
                idx = path.index('custom') + 1
            else:
                idx = 0
            path.insert(idx, layer_name)
            path = ", ".join(path)
            skinsTool.addSkinSelection(skin, path)
            out.append('Added "%s" to "%s" skin.' % (layer_name, skin))
        else:
            out.append('Skipping "%s" skin, already setup.' % skin)

    log.write("\n".join(out))

def install_property_sheet(self, log):
    fldr = getToolByName(self, 'portal_properties')
    id = 'plone_desktop_uri'
    if id not in fldr.objectIds():
        fldr.addPropertySheet(id)
        log.write("Added 'plone_desktop_uri' property sheet.\n")
    else:
        log.write("Property sheet 'plone_desktop_uri' already existed.\n")

    p = getattr(fldr, id)

    add = p.manage_addProperty
    exists = p.hasProperty
    delete = p.manage_delProperties

    # Upgrade check: In version 3.0.0, we had a set of defaults that
    # doesn't make sense anymore. If we detect that the settings have
    # never been changed since the install then we override them.
    reg = getToolByName(self, tool_id, None)
    if reg is not None:
        d1 = p.bobobase_modification_time()
        d2 = reg.bobobase_modification_time()

        if 0 <= d1 - d2 < 0.1:
            # Delete existing properties, the code below will add them
            # back in.
            log.write('Detected upgrade, forcing new defaults.\n')
            for pid in ('filename_normalization',
                        'relaxed_normalization',
                        'show_portal_tools'):
                if exists(pid):
                    log.write('Forcing default value for %s.\n' % pid)
                    delete(ids=[pid])

    for name, default, kind in CONFIG_SCHEMA:
        if not exists(name):
            add(name, default, kind)
            log.write("Added '%s' configuration property.\n" % name)

def install_cp(self, out):
    cp = getToolByName(self, 'portal_controlpanel', None)
    if cp is None:
        return

    # Plone Desktop has been renamed Enfold Desktop
    cp.unregisterConfiglet('Plone Desktop')
    cp.unregisterConfiglet('Enfold Desktop')

    if "Enfold Desktop" not in [c.id for c in cp._actions]:
        cp.registerConfiglet(
           "Enfold Desktop",
            "Enfold Desktop",
            "string:${portal_url}/prefs_plone_desktop",
            category="Products",
            permission="Manage portal",
            appId="Enfold Desktop",)
        print >> out, 'Added Enfold Desktop Control Panel'
    else:
        print >> out, 'Enfold Desktop Control Panel already existed.'

    ai = getToolByName(self, 'portal_actionicons', None)
    if ai is None:
        return
    
    if not ai._lookup.get(("controlpanel", "Enfold Desktop")):
        print >> out, 'Adding icon for Enfold Desktop Control Panel'
        ai.addActionIcon("controlpanel", "Enfold Desktop",
                         "windows_explorer.gif", title="Enfold Desktop")

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

def install_deps(self, out):
    qi = getToolByName(self, 'portal_quickinstaller')
    for dep in DEPS:
        print >> out, 'Installing dependency: %s' % dep
        if not qi.isProductInstallable(dep):
            print >> out, 'WARNING: %s is not installable' % dep
            continue
        qi.installProduct(dep)

def remove_portal_workflow_provider(self, log):
    at = getToolByName(self, 'portal_actions')
    if 'portal_workflow' in at.listActionProviders():
        # Not used anymore in Plone since the advent of the 'review
        # portlet'. Also can be quite expensive because it does a
        # catalog query for each workflow or something equally insane.
        at.deleteActionProvider('portal_workflow')
        log.write('Removed portal_workflow from the list of '
                  'action providers as Plone does not need it '
                  'anymore since the review portlet is born.\n')

def install(self, out=None):
    if out is None:
        out = StringIO()

    install_deps(self, out)
    install_tool(self, out)
    install_predicates(self, out)
    install_ctr_predicates(self, out)
    local_vocabs = ('Transitions', 'Discussion', 'Actions')
    global_vocabs = ('Language', 'Format', 'Users', 'Groups', 'URI')
    install_local_vocabs(self, local_vocabs, out)
    install_global_vocabs(self, global_vocabs, out)
    install_skin(self, out)
    install_root_error(self, out)
    install_property_sheet(self, out)
    install_cp(self, out)
    fix_workflows(self, out)
    install_actions(self, out)
    install_hook(self, out, adding=True)
    fix_members_folder(self, out)

    return out.getvalue()

def uninstall(self, out=None, reinstall=False):
    if out is None:
        out = StringIO()

    return removeVarious(self)
