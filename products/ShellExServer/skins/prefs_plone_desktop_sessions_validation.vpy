portal = context.portal_url.getPortalObject()
get = context.REQUEST.get
configured = get('configured_sessions', '')
configured = configured.replace('\r','\n').splitlines()
configured = filter(None, configured)
failed = []
traverse = portal.restrictedTraverse
for path in configured:
    npath = path.split('/')
    npath = filter(None, npath)
    try:
        traverse(npath)
    except ('NotFound', KeyError, AttributeError):
        failed.append(path)

if len(failed):
    failed = ', '.join(failed)
    msg = 'The following folders could not be found in the Plone site: %s' % failed
    state.setError('configured_sessions', msg)

if state.getErrors():
    msg = 'There was an error in processing that page, your changes were not saved. Please correct the indicated errors.'
    return state.set(status='failure', portal_status_message=msg)
else:
    return state
