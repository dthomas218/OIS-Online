##############################################################################
#
# Copyright (c) 2004 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""
$Id: utils.py 708 2005-05-06 21:47:02Z sidnei $
"""

from types import MethodType, FunctionType, UnboundMethodType
from Products.Archetypes.utils import wrap_method
from Products.Archetypes.utils import isWrapperMethod, WRAPPER
from Products.DavPack import log

def patch_base(klass):
    attrs = klass.__dict__.items()
    attrs = filter(lambda item: not item[0].startswith('__'), attrs)
    base = klass.__bases__[-1]
    kname = base.__name__
    for name, attr in attrs:
        old_attr = getattr(base, name, None)
        if (old_attr is not None and name in base.__dict__ and
            isinstance(old_attr, (MethodType, FunctionType, UnboundMethodType))):
            if not isWrapperMethod(old_attr):
                wrap_method(base, name, attr, pattern='__davpack_%s__')
                log('Patch applied to %s.%s' % (kname, name))
            else:
                # Already wrapped
                log('Found wrapped method at %s.%s. '
                    'Patch not applied'  % (kname, name))
        else:
            setattr(base, name, attr)
            log('Patch applied to %s.%s' % (kname, name))

def _isUnwrappedWrappable(obj):
    return (getattr(obj, '__of__', None) is not None and
            getattr(obj, 'aq_base', None) is None)
