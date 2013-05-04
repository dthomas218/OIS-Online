## Script (Python) "validate_clear_locks"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind state=state
##bind subpath=traverse_subpath
##parameters=paths=None
##title=Validates content publishing
##
if not paths:
    state.setError('paths', 'Must select at least one item to clear locks')

if state.getErrors():
    return state.set(status='failure',
                     portal_status_message='Please correct the indicated errors.')
else:
    return state

