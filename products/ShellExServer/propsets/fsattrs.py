# Enfold Desktop
# Copyright(C), 2004-2006, Enfold Systems, Inc. - ALL RIGHTS RESERVED


# Enfold Systems, Inc.
# 4617 Montrose Blvd., Suite C215
# Houston, Texas 77006 USA
# p. +1 713.942.2377 | f. +1 832.201.8856
# www.enfoldsystems.com
# info@enfoldsystems.com

# $Id: fsattrs.py 8184 2008-03-18 16:45:22Z sidnei $
# $HeadURL: https://svn.enfoldsystems.com/internal/ShellExServer/trunk/propsets/fsattrs.py $

from Globals import InitializeClass
from Acquisition import aq_base, Implicit
from Products.PropertySets.PropertySetPredicate import PropertySetPredicate
from Products.PropertySets.PropertySetRegistry import registerPredicate
from Products.CMFCore.utils import getToolByName
from Products.CMFPropertySets.DynamicPropset import DynamicPropset

pm = (
    {'id':'hidden', 'type':'boolean', 'mode':'rw'},
    {'id':'executable', 'type':'boolean', 'mode':'rw'},
    )

class PMethod(Implicit):
    """ A simple, parameterized method """

    def __init__(self, method, *args, **kw):
        self.method = method
        self.args = args
        self.kw = kw

    def __call__(self, *args, **kw):
        v_self = self.aq_parent
        args = (v_self,) + self.args + args
        kw.update(self.kw)
        return self.method(*args, **kw)

class FSAttrProperties(DynamicPropset):
    """Filesystem Attributes Properties"""

    id='fsattrs'
    _md={'xmlns': 'http://enfoldtechnology.com/propsets/fsattrs'}
    _extensible = 0
    _prefix = '_fsattr_'

    def _get_attr(self, name, default=None):
        vself = self.v_self()
        attr_name = self._prefix + name
        if not hasattr(aq_base(vself), attr_name):
            if name == 'hidden' and aq_base(vself).getId().startswith('.'):
                return True
            return default
        return getattr(vself, attr_name)

    def _set_attr(self, value, name):
        vself = self.v_self()
        attr_name = self._prefix + name
        setattr(vself, attr_name, value)

    dav__hidden = PMethod(_get_attr, name='hidden', default=False)
    dav__set_hidden = PMethod(_set_attr, name='hidden')
    dav__executable = PMethod(_get_attr, name='executable', default=False)
    dav__set_executable = PMethod(_set_attr, name='executable')

    def _propertyMap(self):
        return pm

InitializeClass(FSAttrProperties)

class FSAttrPredicate(PropertySetPredicate):
    """ Expose Filesystem Attributes for an object
    """

    _property_sets = (FSAttrProperties(),)

registerPredicate('fsattrs',
                  'Filesystem Attributes',
                  FSAttrPredicate)
