## Script (Python) "standard_error_message"
##bind context=context
##parameters=**kwargs
##title=Dispatches to relevant error view
##

from Products.ShellExServer.utils import standard_error_message
return standard_error_message(context, **kwargs)
