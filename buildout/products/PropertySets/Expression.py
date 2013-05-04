"""
Persistent TALES Expression. Highly inspired (read copied)
from CMFCore's Expression.

$Id: Expression.py 672 2005-03-22 19:03:16Z sidnei $
"""

from Globals import Persistent, InitializeClass
from Acquisition import aq_inner, aq_parent
from AccessControl import getSecurityManager, ClassSecurityInfo

from Products.PageTemplates.Expressions import getEngine
from Products.PageTemplates.Expressions import SecureModuleImporter

class Expression(Persistent):
    """A Persistent TALES Expression"""

    _text = ''
    _v_compiled = None

    security = ClassSecurityInfo()

    def __init__(self, text):
        self._text = text
        self._v_compiled = getEngine().compile(text)

    def __call__(self, econtext):
        compiled = self._v_compiled
        if compiled is None:
            compiled = self._v_compiled = getEngine().compile(self._text)
        res = compiled(econtext)
        if isinstance(res, Exception):
            raise res
        return res

InitializeClass(Expression)

def createExprContext(obj):
    """ Provides names for TALES expressions.
    """
    if obj is None:
        object_url = ''
    else:
        object_url = obj.absolute_url()

    user = getSecurityManager().getUser()

    data = {
        'object_url':   object_url,
        'object':       obj,
        'nothing':      None,
        'request':      getattr(obj, 'REQUEST', None),
        'modules':      SecureModuleImporter,
        'user':         user,
        }
    return getEngine().getContext(data)