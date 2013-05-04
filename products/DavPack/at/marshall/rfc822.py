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
$Id: rfc822.py 921 2006-01-17 15:35:07Z sidnei $
"""

from OFS.content_types import guess_content_type
from OFS.Image import File
from Products.Archetypes.debug import log
from Products.Archetypes.Marshall import RFC822Marshaller as OrigMarshaller
from Products.Archetypes.Field import FileField
from Products.Archetypes.interfaces.base import IBaseUnit

class RFC822Marshaller(OrigMarshaller):

    def demarshall(self, instance, data, **kwargs):
        from Products.CMFDefault.utils import parseHeadersBody
        headers, body = parseHeadersBody(data)
        for k, v in headers.items():
            if v.strip() == 'None':
                v = None
            field = instance.getField(k)
            if field is not None:
                mutator = field.getMutator(instance)
                if mutator is not None:
                    mutator(v)
        content_type = headers.get('Content-Type')
        if not kwargs.get('mimetype', None):
            kwargs.update({'mimetype': content_type})
        p = instance.getPrimaryField()
        # We don't want to pass file forward.
        if kwargs.has_key('file'):
            del kwargs['file']
        if p is not None:
            mutator = p.getMutator(instance)
            if mutator is not None:
                mutator(body, **kwargs)
