## Script (Python) "logged_in"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=
##title=login
##
r = context.REQUEST
d = r.get('go_to')
if d:
    r.RESPONSE.redirect(d)
return "Logged in"
