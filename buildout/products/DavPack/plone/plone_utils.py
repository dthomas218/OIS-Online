##############################################################################
#
# DavPack -- A set of patches for all things related to WebDAV
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
# Some portions of this module copyright 2001-2004 George A. Runyan
# Jr., Alexande Limi and Vidar Andersen.
#
##############################################################################
"""
$Id: plone_utils.py 921 2006-01-17 15:35:07Z sidnei $
"""

from Products.DavPack import log
from Products.CMFPlone.PloneTool import PloneTool

if not getattr(PloneTool, '__doc__', ''):
    PloneTool.__doc__ = "Various utility methods."
    log("Added missing docstring to 'plone_utils' tool.")
