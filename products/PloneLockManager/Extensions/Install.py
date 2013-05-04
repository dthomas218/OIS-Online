##############################################################################
#
# PloneLockManager -- Expose WebDAV Lock Management through a Plonish UI
# Copyright (C) 2004 Enfold Systems
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
##############################################################################
"""
$Id: Install.py 825 2005-11-09 01:01:41Z sidnei $
"""

from cStringIO import StringIO
from Products.CMFCore.DirectoryView import addDirectoryViews
from Products.CMFCore.utils import getToolByName, manage_addTool
from Products.PloneLockManager.config import *

def install_tool(self, out):
    tool = getToolByName(self, TOOL_ID, None)
    if tool is not None:
        print >> out, '%s already existed. Replacing' % TOOL_TYPE
        self.manage_delObjects([TOOL_ID])

    adding = self.manage_addProduct[PROJECTNAME]
    manage_addTool(adding, TOOL_TYPE)
    tool = getToolByName(self, TOOL_ID, None)
    tool._updateProperty('title', 'Lock Manager')
    print >> out, 'Added %s' % TOOL_TYPE

def install_control_panel(self, out):
    cp = getToolByName(self, 'portal_controlpanel')

    if GROUP_ID not in cp.getGroupIds():
        groups = list(cp.groups)
        groups.append(GROUP)
        cp.groups = groups
        print >> out, 'Control Panel Group %s has been registered' % GROUP_ID

    cp.unregisterConfiglet(GROUP_ID)
    cp.registerConfiglets(CONFIGLETS)

def install_skin(self, out):
    skinsTool = getToolByName(self, 'portal_skins')

    layer_name = LAYER_NAME
    layer_location = '%s/skins' % PROJECTNAME

    # add in the directory view pointing to our skin
    if layer_name not in skinsTool.objectIds():
        addDirectoryViews(skinsTool, 'skins', GLOBALS)
        print >> out, 'Added "%s" directory view to portal_skins' % layer_name

    # add in the layer to all our skins
    skins = skinsTool.getSkinSelections()
    for skin in skins:
        path = skinsTool.getSkinPath(skin)
        path = [p.strip() for p in path.split(',')]
        if layer_name not in path:
            position = 'custom' in path and (path.index('custom') + 1) or 0
            path.insert(position, layer_name)
            path = ', '.join(path)
            skinsTool.addSkinSelection(skin, path)
            print >> out, 'Added "%s" to "%s" skin' % (layer_name, skin)
        else:
            print >> out, 'Skin "%s" already contained %s' % (skin, layer_name)

def install_actions(self, out):
    at = getToolByName(self, 'portal_actions')
    action_ids = [a.getId() for a in at.listActions()]
    for action in ACTIONS:
        if action['id'] not in action_ids:
            at.addAction(**action)
            print >> out, ('Installed action %s' % (action['name'],))
        else:
            print >> out, ('Action %s was already installed' % (action['name'],))

    ai = getToolByName(self, 'portal_actionicons')
    for category, config in ACTION_ICONS.items():
        for icon_id, info in config.items():
            if ai.queryActionIcon(category, icon_id, None) is None:
                ai.addActionIcon(category, icon_id,
                                 info[0], info[1])
                print >> out, ('Installed action icon '
                               'for %s.' % info[1])
            else:
                print >> out, ('Action Icon for %s '
                               'was already Installed.'
                               % info[1])

def install(self, out=None):
    if out is None:
        out = StringIO()
    install_tool(self, out)
    install_control_panel(self, out)
    install_skin(self, out)
    install_actions(self, out)
    return out.getvalue()
