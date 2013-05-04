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
# Some portions of this module are Benjamin Saller and respective authors.
# The original copyright statement can be found on ArchetypesLicense.txt.
#
##############################################################################
"""
$Id: __init__.py 839 2005-11-19 01:54:18Z sidnei $
"""

from field import text
from marshall import primary
from marshall import rfc822
from utils import patch_base

patch_base(text.TextField)
patch_base(primary.PrimaryFieldMarshaller)
patch_base(rfc822.RFC822Marshaller)
