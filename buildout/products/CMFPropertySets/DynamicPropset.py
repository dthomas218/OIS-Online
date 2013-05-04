"""
$Id: DynamicPropset.py 794 2005-09-29 02:18:58Z sidnei $
"""

from cgi import escape
from types import ListType
from zExceptions import BadRequest
from Globals import InitializeClass
from OFS.PropertySheets import Virtual, View, PropertySheet
from ZPublisher.Converters import type_converters, get_converter

_marker = []

class DynamicPropset(Virtual, PropertySheet, View):
    """ A Dynamic Propset, computed from information
    spread across various tools and objects.
    """

    def __init__(self, id=None, md=None):
        if id is None:
            id = self.id
        if md is None:
            md = self._md
        PropertySheet.__init__(self, id, md)

    # As its dynamic, it's not extensible
    _extensible = 0

    def _getAccessor(self, id):
        """ By default, 'dav__${id}' """
        return getattr(self, 'dav__%s' % id, None)

    def _getMutator(self, id):
        """ By default, 'dav__set_${id}' """
        return getattr(self, 'dav__set_%s' % id, None)

    def getProperty(self, id, default=None):
        """ We first try a method named 'dav__${id}'.

        If that method doesn't exists, we return default.
        """
        if not self.hasProperty(id):
            return default
        accessor = self._getAccessor(id)
        if accessor is not None:
            return accessor()
        return default

    def _setProperty(self, id, value, type='string', meta=None):
        """ By default we disallow creating new properties.

        You can choose to allow this on your subclass if you want
        to, then you need to override this method and set '_extensible' to 1.
        """
        raise ValueError, 'New property %s cannot be created.' % escape(id)

    def _updateProperty(self, id, value, meta=None):
        """ For updating existing properties, we look for a method
        named 'dav__set_${id}'. If it doesn't exist, then we can't
        set the value.
        """
        # Check for acquisition wrappers
        self._wrapperCheck(value)

        # Can't set properties that do not exist
        if not self.hasProperty(id):
            raise BadRequest, 'The property %s does not exist.' % escape(id)

        # Check that the property is writable
        # (as we are dynamically generating this, you can modify
        # _propertyMap() to override settings)
        propinfo=self.propertyInfo(id)
        if not 'w' in propinfo.get('mode', 'w'):
            raise BadRequest, '%s cannot be changed.' % escape(id)

        # If the property is of a different type
        # try to use a converter to turn it into the
        # right type. The type comes from _propertyMap()
        if type(value)==type(''):
            proptype=propinfo.get('type', 'string')
            if type_converters.has_key(proptype):
                value=type_converters[proptype](value)

        # Never store lists. Convert them to safe,
        # immutable tuples.
        if type(value) == ListType:
            value = tuple(value)

        method = self._getMutator(id)
        if method is None:
            # If it doesn't exist, we can't change the property
            raise BadRequest, '%s cannot be changed.' % escape(id)
        res = method(value)
        vself = self.v_self()
        if getattr(vself, 'reindexObject', None) is not None:
            vself.reindexObject()
        return res

    def _delProperty(self, id):
        """ As we are dynamic, it doesn't make sense to
        try to delete properties.
        """
        raise ValueError, '%s cannot be deleted.' % escape(id)

    def _propertyMap(self):
        """ This is the method that exposes the available
        properties, their types and modes (read, write, delete).

        Subclasses should override this method to suit their
        set of properties and return a tuple of dictionaries
        in the form:

            {'id':<propertyname>,
             'mode':<r,w,d>,
             'type':<string,integer...>
             }
        """
        raise NotImplementedError, '_propertyMap'

    def propertyMap(self):
        return map(lambda dict: dict.copy(), self._propertyMap())

InitializeClass(DynamicPropset)
