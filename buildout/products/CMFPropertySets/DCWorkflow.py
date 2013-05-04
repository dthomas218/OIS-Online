"""
$Id: DCWorkflow.py 2384 2008-10-21 17:24:39Z sidnei $
"""

from Globals import InitializeClass
from zExceptions import BadRequest
from Products.PropertySets.PropertySetPredicate import PropertySetPredicate
from Products.PropertySets.PropertySetRegistry import registerPredicate
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.WorkflowCore import WorkflowException
from Products.CMFPropertySets.DynamicPropset import DynamicPropset
from Products.CMFCore.interfaces.Contentish import Contentish
from Products.CMFCore.interfaces.Folderish import Folderish

_marker = []

class DCWorkflowProperties(DynamicPropset):
    """DCWorkflow Properties"""

    id='dcworkflow'
    _md={'xmlns': 'http://cmf.zope.org/propsets/dcworkflow'}
    _extensible=0

    def getProperty(self, id, default=None):
        value = DynamicPropset.getProperty(self, id, _marker)
        if value is not _marker:
            return value
        vself=self.v_self()
        wf_tool = getToolByName(vself, 'portal_workflow', None)
        if wf_tool is None:
            return default
        try:
            return wf_tool.getInfoFor(vself, id, default=default)
        except WorkflowException:
            return default

    def _propertyMap(self):
        vself=self.v_self()
        wf_tool = getToolByName(vself, 'portal_workflow', None)
        if wf_tool is None:
            return {}
        vars = wf_tool.getCatalogVariablesFor(vself)
        if vars is None:
            return {}
        pm = []
        for k in vars.keys():
            pm.append({'id':k, 'mode':'rw'})
        return tuple(pm)

    def dav__set_review_state(self, value, default=_marker):
        vself = self.v_self()
        wf_tool = getToolByName(vself, 'portal_workflow', None)
        if wf_tool is None:
            return
        return wf_tool.doActionFor(vself, value)

InitializeClass(DCWorkflowProperties)

class DCWorkflowPredicate(PropertySetPredicate):
    """ Expose DCWorkflow Catalogable Variables

    Usually, this includes workflow state.
    """

    _property_sets = (DCWorkflowProperties(),)

    def apply(self, obj):
        """ Check for interface implements.

        This should probably be a default feature,
        e.g.: having a _apply_to class attribute
        containing interfaces to check against.
        """
        if not (Contentish.isImplementedBy(obj) or Folderish.isImplementedBy(obj)):
            return ()
        return PropertySetPredicate.apply(self, obj)

registerPredicate('dcworkflow',
                  'DCWorkflow Catalogable Variables',
                  DCWorkflowPredicate)
