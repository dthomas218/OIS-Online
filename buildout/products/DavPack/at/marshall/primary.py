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
$Id: primary.py 621 2004-11-23 02:48:46Z sidnei $
"""

from OFS.content_types import guess_content_type
from OFS.Image import File
from Products.Archetypes.debug import log
from Products.Archetypes.Marshall import PrimaryFieldMarshaller as OrigMarshaller
from Products.Archetypes.Field import FileField
from Products.Archetypes.interfaces.base import IBaseUnit

class PrimaryFieldMarshaller(OrigMarshaller):

    def demarshall(self, instance, data, **kwargs):
        p = instance.getPrimaryField()
        file = kwargs.get('file')
        if isinstance(p, FileField) and file:
            data = file
            del kwargs['file']
        p.set(instance, data, **kwargs)

    def marshall(self, instance, **kwargs):
        p = instance.getPrimaryField()
        if not p:
            raise TypeError, 'Primary Field could not be found.'
        data = p and instance[p.getName()] or ''
        content_type = length = None
        # Gather/Guess content type
        if IBaseUnit.isImplementedBy(data):
            content_type = data.getContentType()
            length = data.get_size()
            data   = data.getRaw()
        elif isinstance(data, File):
            content_type = data.content_type
            length = data.get_size()
            data = data.data
        else:
            log('WARNING: PrimaryFieldMarshaller(%r): '
                'field %r does not return a IBaseUnit '
                'instance.' % (instance, p.getName()))
            if hasattr(p, 'getContentType'):
                content_type = p.getContentType(instance) or 'text/plain'
            else:
                content_type = data and guess_content_type(data) or 'text/plain'
            length = len(data)
            # ObjectField without IBaseUnit?
            if hasattr(data, 'data'):
                data = data.data
            else:
                data = str(data)

        return (content_type, length, data)
