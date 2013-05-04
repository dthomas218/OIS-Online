## Controller Python Script "lm_clear_locks"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind state=state
##bind subpath=traverse_subpath
##parameters=paths=None
##title=Clear Locks
##

from Products.CMFCore.utils import getToolByName
lm = getToolByName(context, 'portal_lock_manager')
failed = lm.clearLocks(paths)

return state.set(
    context=context,
    failed=failed,
    portal_status_message=('Locks Cleared'))

