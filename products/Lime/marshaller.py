##############################################################################
#
# Lime - Link Marshaller
# Copyright(C), 2004-2007, Enfold Systems, Inc. - ALL RIGHTS RESERVED
#
# This software is licensed under the Terms and Conditions contained
# within the LICENSE.txt file that accompanied this software.  Any
# inquiries concerning the scope or enforceability of the license should
# be addressed to:
#
# Enfold Systems, Inc.
# 4617 Montrose Blvd., Suite C215
# Houston, Texas 77006 USA
# p. +1 713.942.2377 | f. +1 832.201.8856
# www.enfoldsystems.com
# info@enfoldsystems.com
#
##############################################################################
"""
$Id: marshaller.py 7352 2007-07-24 01:59:26Z sidnei $
"""

import transaction
from StringIO import StringIO

try:
    from ConfigParser import SafeConfigParser as BaseParser
except ImportError:
    from ConfigParser import ConfigParser as BaseParser

from Products.CMFDefault.Link import Link
from Products.Archetypes.Marshall import Marshaller

ACCEPTABLE_LANGS = ['', 'en', 'en_US']

URL_SECTION = 'InternetShortcut'
URL_MAP = {'remoteUrl': 'URL'}

DESKTOP_SECTION = 'Desktop Entry'
DESKTOP_MAP = {'remoteUrl': 'URL',
               'encoding': 'Encoding',
               'type': 'Type',
               'title': 'Name',
               'description': 'GenericName',
               }

SECTION_MAPPINGS = dict([(DESKTOP_SECTION, DESKTOP_MAP),
                         (URL_SECTION, URL_MAP),
                         ])

# Mapping for ATLink and CMF Link
default_mapping = {'remoteUrl': 'getRemoteUrl',
                   'title': 'Title',
                   'description': 'Description',
                   }
kw_mappings = []

cmf_update = {'remoteUrl': '_edit',
              'title': 'setTitle',
              'description': 'setDescription',
              }

def cmf_link_update(self, **kw):
    for key, name in cmf_update.items():
        value = kw.get(key)
        if value:
            method = getattr(self, name)
            method(value)
    self.reindexObject()
Link.update = cmf_link_update

class CasePreservingParser(BaseParser):

    def optionxform(self, key):
        return key

Parser = CasePreservingParser

def parse_url_or_desktop(fp, filename, section, encoding='ascii'):
    parser = Parser()
    parser.readfp(fp, filename)
    # Discover which mapping to use
    mapping = SECTION_MAPPINGS[section]
    # Now for the real data extraction.
    data = {}
    for key, option in mapping.items():
        for lang in ACCEPTABLE_LANGS:
            lang_option = option
            if lang:
                lang_option = '%s[%s]' % (option, lang)
            if not parser.has_option(section, lang_option):
                continue
            value = parser.get(section, lang_option)
            if not value:
                continue
            if key in ('type',):
                if value not in ('Link',):
                    # Not a valid .desktop file.
                    return
                # It's a .desktop Link
                break
            if key in ('encoding',):
                encoding = value
                break
            data[key] = value
    # If we have an encoding, decode the values using it.
    if encoding:
        for key, value in data.items():
            data[key] = value.decode(encoding)
    return data

def set_props_from_data(ob, data):
    # Setting id might cause a rename, so we commit a subtransaction.
    transaction.savepoint(optimistic=True)
    ob.update(**data)

def marshall_link_to_string(ob, section):
    parser = Parser()
    data = {}
    section_map = SECTION_MAPPINGS[section]

    # Figure out a proper mapping here.
    kw_map = default_mapping
    for klass, mapping in kw_mappings:
        if isinstance(instance, klass):
            kw_map = mapping

    # Extract data.
    for key, mname in kw_map.items():
        value = getattr(ob, mname)
        if callable(value):
            value = value()
        data[key] = value

    # Dump section.
    parser.add_section(section)
    for key, option in section_map.items():
        if key in ('type', 'encoding'):
            continue
        parser.set(section, option, data[key])

    io = StringIO()
    parser.write(io)
    return io.getvalue()

class LinkMarshaller(Marshaller):

    def __init__(self, mimetype=None,
                 section=None,
                 demarshall_hook=None,
                 marshall_hook=None):
        Marshaller.__init__(self, demarshall_hook, marshall_hook)
        self.mimetype = mimetype
        self.section = section

    def marshall(self, instance, **kw):
        link = marshall_link_to_string(instance, self.section)
        return (self.mimetype, len(link), link)

    def demarshall(self, instance, data, **kw):
        fname = kw.get('filename', None)
        fp = kw.get('file', None)
        if fp is None:
            fp = StringIO(data)
        parsed = parse_url_or_desktop(fp, fname, self.section)
        set_props_from_data(instance, parsed)

def URLMarshaller():
    return LinkMarshaller('text/x-uri', URL_SECTION)

def DesktopMarshaller():
    return LinkMarshaller('application/x-desktop', DESKTOP_SECTION)
