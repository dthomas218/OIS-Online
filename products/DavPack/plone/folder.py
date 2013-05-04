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
$Id: folder.py 733 2005-05-30 18:52:15Z sidnei $
"""

from ComputedAttribute import ComputedAttribute
from Acquisition import aq_inner, aq_parent, aq_base
from webdav.NullResource import NullResource
from Products.CMFCore.Skinnable import SkinnableObjectManager
from Products.CMFPlone.PloneFolder import BasePloneFolder, ReplaceableWrapper
from Products.CMFPlone.Portal import PloneSite
from Products.DavPack import log

def folder_index_html(self):
    """ Acquire if not present. """
    request = getattr(self, 'REQUEST', None)
    if request and request.has_key('REQUEST_METHOD'):
        if request.maybe_webdav_client:
            method = request['REQUEST_METHOD']
            if method in ('PUT',):
                # Very likely a WebDAV client trying to create something
                return ReplaceableWrapper(NullResource(self, 'index_html'))
            elif method in ('GET', 'HEAD', 'POST'):
                # Do nothing, let it go and acquire.
                pass
            else:
                raise AttributeError, 'index_html'
    # Acquire from parent
    _target = aq_parent(aq_inner(self)).aq_acquire('index_html')
    return ReplaceableWrapper(aq_base(_target).__of__(self))

BasePloneFolder.index_html = ComputedAttribute(folder_index_html, 1)
log('Patch applied to BasePloneFolder.index_html')

def site_index_html(self):
    """ Acquire if not present. """
    request = getattr(self, 'REQUEST', None)
    if request and request.has_key('REQUEST_METHOD'):
        if request.maybe_webdav_client:
            method = request['REQUEST_METHOD']
            if method in ('PUT',):
                # Very likely a WebDAV client trying to create something
                return ReplaceableWrapper(NullResource(self, 'index_html'))
            elif method in ('GET', 'HEAD', 'POST'):
                # Do nothing, let it go and acquire.
                pass
            else:
                raise AttributeError, 'index_html'
    # Acquire from skin.
    _target = self.__getattr__('index_html')
    return ReplaceableWrapper(aq_base(_target).__of__(self))

PloneSite.index_html = ComputedAttribute(site_index_html, 1)
log('Patch applied to PloneSite.index_html')
