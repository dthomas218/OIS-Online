## Controller Python Script "lm_timeout_settings"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind state=state
##bind subpath=traverse_subpath
##parameters=default_lock_timeout=0, maximum_lock_timeout=0
##title=Change Timeout Settings
##

from Products.CMFCore.utils import getToolByName
lm = getToolByName(context, 'portal_lock_manager')
lm.manage_changeProperties(default_lock_timeout=default_lock_timeout,
                           maximum_lock_timeout=maximum_lock_timeout)

return state.set(
    context=context,
    portal_status_message=('Timeout Settings Changed.'))

