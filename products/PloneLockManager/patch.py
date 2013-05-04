##############################################################################
#
# PloneLockManager -- Expose WebDAV Lock Management through a Plonish UI
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
##############################################################################
"""
$Id: patch.py 826 2005-11-09 01:03:27Z sidnei $
"""

from webdav.davcmds import Lock
from webdav.Resource import Resource
from Products.CMFCore.utils import getToolByName
from Products.PloneLockManager.config import logger, TOOL_ID

def log(msg):
    logger.info(msg)

PATTERN = '__PloneLockManager_%s__'
def call(self, __name__, *args, **kw):
    return getattr(self, PATTERN % __name__)(*args, **kw)

WRAPPER = '__plonelockmanager_is_wrapper_method__'
ORIG_NAME = '__plonelockmanager_original_method_name__'
def isWrapperMethod(meth):
    return getattr(meth, WRAPPER, False)

def wrap_method(klass, name, method, pattern=PATTERN):
    old_method = getattr(klass, name)
    if isWrapperMethod(old_method):
        # Double-wrapping considered harmful.
        log('Already wrapped method %s.%s, skipping.' %
            (klass.__name__, name))
        return
    log('Wrapping method %s.%s' % (klass.__name__, name))
    new_name = pattern % name
    setattr(klass, new_name, old_method)
    setattr(method, ORIG_NAME, new_name)
    setattr(method, WRAPPER, True)
    setattr(klass, name, method)

def unwrap_method(klass, name):
    old_method = getattr(klass, name)
    if not isWrapperMethod(old_method):
        raise ValueError, ('Trying to unwrap non-wrapped '
                           'method %s.%s' % (klass.__name__, name))
    orig_name = getattr(old_method, ORIG_NAME)
    new_method = getattr(klass, orig_name)
    delattr(klass, orig_name)
    setattr(klass, name, new_method)

def calculateTimeout(context, timeout):
    tool = getToolByName(context, TOOL_ID, None)
    if tool is None:
        return timeout
    default_lock_timeout = tool.getProperty('default_lock_timeout', 0)
    maximum_lock_timeout = tool.getProperty('maximum_lock_timeout', 0)
    secs = timeout.split('-')[-1]
    if secs.lower() in ('infinite',):
        # Header not set or set to infinite, change it to
        # 'default_lock_timeout' if it's not zero, otherwise return
        # the current value, unchanged.
        if default_lock_timeout:
            return default_lock_timeout
        return timeout
    # Looks like we got some value for seconds, try to convert it to a
    # long. If an error happens, return original value and let Zope
    # deal with it.
    try:
        secs = long(secs)
    except ValueError:
        raise
    # If value is larger than 'maximum_lock_timeout', then change it
    # to maximum_lock_timeout.
    if maximum_lock_timeout and secs > maximum_lock_timeout:
        return maximum_lock_timeout
    return timeout

def set_header(request, name, value):
    environ = request.environ
    name = '_'.join(name.split('-')).upper()
    if environ.get(name) is not None:
        environ[name] = value
        return
    if name[:5] != 'HTTP_':
        name = 'HTTP_%s' % name
    if environ.get(name) is not None:
        environ[name] = value

def LOCK(self, REQUEST, RESPONSE):
    """Lock a resource
    """
    timeout = REQUEST.get_header('Timeout', 'Infinite')
    # Sanitize header, the same way it's done in davcmds.Lock()
    timeout = timeout.split(',')[-1].strip()
    new_timeout = calculateTimeout(self, timeout)
    if new_timeout != timeout:
        assert isinstance(new_timeout, (int, long)), repr(new_timeout)
        timeout = 'Second-%s' % new_timeout
        set_header(REQUEST, 'Timeout', timeout)
    return call(self, 'LOCK', REQUEST, RESPONSE)

def apply(self, *args, **kw):
    """ Apply, built for recursion (so that we may lock subitems
    of a collection if requested
    """
    context = args[0]
    timeout = self.timeout
    new_timeout = calculateTimeout(context, timeout)
    if new_timeout != timeout:
        assert isinstance(new_timeout, (int, long)), repr(new_timeout)
        self.timeout = 'Second-%s' % new_timeout
    return call(self, 'apply', *args, **kw)

wrap_method(Resource, 'LOCK',
            LOCK, pattern=PATTERN)

wrap_method(Lock, 'apply',
            apply, pattern=PATTERN)
