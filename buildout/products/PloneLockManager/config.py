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
$Id: config.py 1276 2007-07-21 02:36:14Z sidnei $
"""

import logging
try:
    from Products.CMFCore.permissions import ManagePortal
except:
    from Products.CMFCore.CMFCorePermissions import ManagePortal

GLOBALS = globals()
TOOL_ID = 'portal_lock_manager'
TOOL_TYPE = 'Plone Lock Manager'
LAYER_NAME = 'lock_manager'
PROJECTNAME = 'PloneLockManager'

LOCK_ACTION = "python:portal_url + '/%s/pane_manage_locks'" % TOOL_ID
MAIN_PAGE = {'id': 'lock_manager',
             'appId': PROJECTNAME,
             'name': 'Lock Manager',
             'action': LOCK_ACTION,
             'category': 'Products',
             'permission': ManagePortal,
             'imageUrl': 'lock_icon.gif'}

LOCK_ACTION_ICON = "%s + '?search_path=' + folder.relative_path()" % LOCK_ACTION
ACTION_ICONS = {'plone':
                {'lock_manager':('lock_icon.gif',
                                 'Lock Manager'),
                 }
                }

ACTIONS = ({'id': 'lock_manager',
            'name': 'Lock Manager',
            'action': LOCK_ACTION_ICON,
            'permission': (ManagePortal,),
            'condition':'',
            'category': 'document_actions',
            },
           )

CONFIGLETS = [
    MAIN_PAGE
    ]

GROUP_ID = MAIN_PAGE['id']
GROUP = '|'.join((GROUP_ID, PROJECTNAME, TOOL_TYPE))

logger = logging.getLogger(PROJECTNAME)
