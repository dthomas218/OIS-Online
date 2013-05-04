"""
$Id: utils.py 920 2006-01-17 15:33:14Z sidnei $
"""

from xml.dom import minidom
from Products.CMFCore.utils import getToolByName

def site_encoding(ctx, default='utf-8'):
    pprops = getToolByName(ctx, 'portal_properties', None)
    if pprops is not None:
        sprops = getToolByName(pprops, 'site_properties', None)
        if sprops is not None:
            encoding = sprops.getProperty('default_charset')
            if encoding is not None:
                return encoding
    return default

def DOM(value):
    if isinstance(value, basestring):
        dom = minidom.parseString(value)
    else:
        dom = value
    return dom

def free(dom):
    if hasattr(dom, 'unlink'):
        dom.unlink()

def nodeAttrValue(node, attr, value, encoding):
    dom = DOM(value)
    values = [e.getAttribute(attr) for e in dom.getElementsByTagName(node)]
    values = map(lambda x: x.encode(encoding), values)
    free(dom)
    return values

def attrValues(elm, attrs, encoding):
    key = ()
    for attr in attrs:
        key += (elm.getAttribute(attr).encode(encoding),)
    return key

def nodeChildrenInfo(node, attrs, sub, sub_attrs, value, encoding):
    dom = DOM(value)
    info = {}
    for e in dom.getElementsByTagName(node):
        key = attrValues(e, attrs, encoding)
        plist = info.setdefault(key, [])
        for s in e.getElementsByTagName(sub):
            plist.append(attrValues(s, sub_attrs, encoding))
    free(dom)
    return info
