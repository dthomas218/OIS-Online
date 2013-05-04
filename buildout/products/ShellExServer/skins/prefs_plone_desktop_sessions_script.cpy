##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##bind state=state
##parameters=
##title=Set Enfold Desktop settings
##

props = context.portal_properties.plone_desktop_uri
get = context.REQUEST.get

if not props.hasProperty('use_member_folder_session'):
    props.manage_addProperty('use_member_folder_session', True, 'boolean')

if not props.hasProperty('configured_sessions'):
    props.manage_addProperty('configured_sessions', '', 'lines')

props.manage_changeProperties(**{
    'use_member_folder_session': get('member_folder', False),
    'configured_sessions': get('configured_sessions', '')})

msg = 'Enfold Desktop session information updated'
state.set(status='success', portal_status_message=msg)
return state
