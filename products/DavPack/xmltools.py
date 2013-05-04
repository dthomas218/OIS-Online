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
# Some portions of this module are Copyright Zope Corporatioin and
# Contributors.
# The original copyright statement is reproduced below.
#
##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""
WebDAV XML request parsing tool using xml.minidom as xml parser.
Code contributed by Simon Eisenmann, struktur AG, Stuttgart, Germany
"""
__version__='$Revision: 1.15.2.3 $'[11:-2]

"""
TODO:

 - Check the methods Node.addNode
   and find out if some code uses/requires this method.

   => If yes implement them, else forget them.

   NOTE: So far i didn't have any problems.
         If you have problems please report them.

 - We are using a hardcoded default of latin-1 for encoding unicode
   strings. While this is suboptimal, it does match the expected
   encoding from OFS.PropertySheet. We need to find a the encoding
   somehow, maybe use the same encoding as the ZMI is using?

"""

from StringIO import StringIO
from xml.dom import minidom
from xml.sax.saxutils import escape as _escape, unescape as _unescape

escape_entities = {'"': '&quot;',
                   "'": '&apos;',
                   }

unescape_entities = {'&quot;': '"',
                     '&apos;': "'",
                     }

def escape(value, entities=None):
    _ent = escape_entities
    if entities is not None:
        _ent = _ent.copy()
        _ent.update(entities)
    return _escape(value, entities)

def unescape(value, entities=None):
    _ent = unescape_entities
    if entities is not None:
        _ent = _ent.copy()
        _ent.update(entities)
    return _unescape(value, entities)

# XXX latin-1 is hardcoded on OFS.PropertySheets as the expected
# encoding properties will be stored in. Optimally, we should use the
# same encoding as the 'default_encoding' property that is used for
# the ZMI.
zope_encoding = 'latin-1'

class Node:
    """ Our nodes no matter what type
    """

    node = None

    def __init__(self, node):
        self.node = node

    def elements(self, name=None, ns=None):
        nodes = []
        for n in self.node.childNodes:
            if (n.nodeType == n.ELEMENT_NODE and
                ((name is None) or ((n.localName.lower())==name)) and
                ((ns is None) or (n.namespaceURI==ns))):
                nodes.append(Element(n))
        return nodes

    def qname(self):
        return '%s%s' % (self.namespace(), self.name())

    def addNode(self, node):
        # XXX: no support for adding nodes here
        raise NotImplementedError, 'addNode not implemented'

    def toxml(self):
        return self.node.toxml()

    def strval(self):
        return self.toxml() #.encode(zope_encoding)

    def name(self):  return self.node.localName
    def value(self): return self.node.nodeValue
    def nodes(self): return self.node.childNodes
    def nskey(self): return self.node.namespaceURI

    def namespace(self): return self.nskey()

    def attrs(self):
        return [Node(n) for n in self.node.attributes.values()]

    def del_attr(self, name):
        if self.node.hasAttributes():
            for key, attr in self.node.attributes.items():
                if key == name:
                    # Only remove attributes if they exist
                    return self.node.removeAttribute(name)

    def remap(self, dict, n=0, top=1):
        # NOTE: zope calls this to change namespaces in PropPatch and Lock
        #       we dont need any fancy remapping here and simply remove
        #       the attributes in del_attr

        for value, name in dict.items():
            for attr in self.node.attributes.values():
                if attr.value == value:
                    new_attr = attr.cloneNode(attr)
                    new_attr.name = u'xmlns:%s' % name
                    new_attr.localName = unicode(name)
                    self.node.removeAttributeNodeNS(attr)
                    self.node.setAttributeNodeNS(new_attr)
        return {}, 0

    def __repr__(self):
        if self.namespace():
            return "<Node %s (from %s)>" % (self.name(), self.namespace())
        else: return "<Node %s>" % self.name()

class Element(Node):

    def toxml(self):
        # When dealing with Elements, we only want the Element's content.
        writer = StringIO(u'')
        for n in self.node.childNodes:
            if n.nodeType == n.CDATA_SECTION_NODE:
                # CDATA sections should not be unescaped.
                writer.write(n.data)
            elif n.nodeType == n.ELEMENT_NODE:
                writer.write(n.toxml())
            else:
                # TEXT_NODE and what else?
                value = n.toxml()
                # Unescape possibly escaped values.  We do this
                # because the value is *always* escaped in it's XML
                # representation, and if we store it escaped it will come
                # out *double escaped* when doing a PROPFIND.
                value = unescape(value, entities=unescape_entities)
                writer.write(value)
        return writer.getvalue()

class XmlParser:
    """ Simple wrapper around minidom to support the required
    interfaces for zope.webdav
    """

    dom = None

    def __init__(self):
        pass

    def parse(self, data):
        self.dom = minidom.parseString(data)
        return Node(self.dom)