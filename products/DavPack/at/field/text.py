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
# Some portions of this module are copyright Benjamin Saller and respective
# authors.
# The original copyright statement can be found on ArchetypesLicense.txt.
#
##############################################################################
"""
$Id: text.py 839 2005-11-19 01:54:18Z sidnei $
"""
from OFS.Image import File
from Products.Archetypes.Field import TextField as OrigField
from Products.Archetypes.BaseUnit import BaseUnit

orig_wrapValue = OrigField._wrapValue
class TextField(OrigField):

    def _wrapValue(self, instance, value, **kwargs):
        """Wraps the value in the content class if it's not wrapped
        """
        if getattr(value, '__class__', None) is File:
            # Old instance, migrate.
            # In case someone changes the 'content_class'
            filename = getattr(value, 'filename', '')
            mimetype = getattr(value, 'content_type', '')
            value = getattr(value, 'data', '')
            bu = BaseUnit(self.getName(), file='', instance=instance)
            self.storage.set(self.getName(), instance, bu)
            bu = self.storage.get(self.getName(), instance)
            bu.update(value, instance, mimetype=mimetype, filename=filename)
            value = bu
        return orig_wrapValue(self, instance, value, **kwargs)
