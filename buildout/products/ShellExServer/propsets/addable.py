# Enfold Desktop
# Copyright(C), 2004-2006, Enfold Systems, Inc. - ALL RIGHTS RESERVED


# Enfold Systems, Inc.
# 4617 Montrose Blvd., Suite C215
# Houston, Texas 77006 USA
# p. +1 713.942.2377 | f. +1 832.201.8856
# www.enfoldsystems.com
# info@enfoldsystems.com

# $Id: addable.py 8184 2008-03-18 16:45:22Z sidnei $
# $HeadURL: https://svn.enfoldsystems.com/internal/ShellExServer/trunk/propsets/addable.py $

from xml.dom import minidom

from Acquisition import aq_base
from Globals import InitializeClass
from Products.CMFPropertySets.DynamicPropset import DynamicPropset
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.ContentTypeRegistry import ExtensionPredicate
from Products.PropertySets.PropertySetPredicate import PropertySetPredicate
from Products.PropertySets.PropertySetRegistry import registerPredicate
from Products.ShellExServer.utils import getRecords

pm = (
    {'id':'addables', 'type':'records', 'mode':'r'},
    )

class Addables(DynamicPropset):
    """addable types"""

    id = 'addables'
    _md = {'xmlns': 'http://enfoldtechnology.com/propsets/addables'}
    _extensible = 0

    def dav__addables(self):
        vself = self.v_self()
        records = self._getAddables()
        return getRecords(records)

    def _getAddables(self):
        context = self.v_self()
        res = []
        if not getattr(aq_base(context), '__dav_collection__', None):
            return res
        # Get the allowed type ids. The Content Type Registry actually
        # maps predicates to a type id and not type name.
        try:
            at = [ct.getId() for ct in context.getAllowedTypes()]
        except AttributeError:
            return res
        ctr = getToolByName(context, 'content_type_registry', None)
        if ctr is None:
            return res
        # listPredicates() returns (id, (predicate, type name))
        addnew = [(p, t) for (i, (p, t)) in ctr.listPredicates()]
        # Filter out all but ExtensionPredicate
        addnew = filter(lambda x: isinstance(x[0], ExtensionPredicate), addnew)
        # Filter out type ids that are not in allowed types
        addnew = filter(lambda x: x[1] in at, addnew)
        # Split extensions (there may be more than one per predicate)
        addnew = [(p.getExtensions().split(), t) for p, t in addnew]
        # Create a mapping from type id to extension
        seen = {}
        for ext, t in addnew:
            # Use only the first type id.
            # Note that if we have multiple predicates for one
            # type id, only the first one will be used so
            # we don't get duplicates.
            if seen.has_key(t):
                continue
            seen[t] = None
            res.append({'title':t, 'extension':ext[0]})
        return res

    def _propertyMap(self):
        return pm

InitializeClass(Addables)

class AddablesPredicate(PropertySetPredicate):
    """ Expose addable types for an object """

    _property_sets = (Addables(), )

registerPredicate('addables',
    'Addable Types',
    AddablesPredicate)
