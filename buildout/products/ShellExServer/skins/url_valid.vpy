##parameters=browser_server=''
##bind state=state

#!/usr/bin/python
#$Id: url_valid.vpy,v 1.1 2004/07/09 01:19:34 andy Exp $
#Copyright: Enfold Systems Ltd
#License: http://www.enfoldsystems.com

if browser_server and not (browser_server.lower().startswith('http://') or
    browser_server.lower().startswith('https://') ):
    state.setError('browser_server', 'Your URI should start with the protocol', new_status='failure')

if state.getErrors():
    state.set(portal_status_message = 'Please correct your errors')

return state
