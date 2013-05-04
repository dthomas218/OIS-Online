##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##bind state=state
##parameters=browser_server=''
##title=Set Enfold Desktop settings
##

props = context.portal_properties.plone_desktop_uri

if not props.hasProperty('filename_normalization'):
    props.manage_addProperty('filename_normalization', '1', 'boolean')

if not props.hasProperty('relaxed_normalization'):
    props.manage_addProperty('relaxed_normalization', '', 'boolean')

if not props.hasProperty('external_editor_optimize'):
    props.manage_addProperty('external_editor_optimize', '1', 'boolean')

if not props.hasProperty('show_portal_tools'):
    props.manage_addProperty('show_portal_tools', '', 'boolean')

if not props.hasProperty('blacklist_types'):
    props.manage_addProperty('blacklist_types', '', 'lines')

get = context.REQUEST.get

props.manage_changeProperties(**{
    # Enfold Desktop root is always the same as Browser Root, for a while now.
    "root_plone_desktop":browser_server,
    "root_browser": browser_server,
    # if relaxed_normalization is on, then filename normalization is on too
    "filename_normalization":get('filename_normalization', 'relaxed_normalization') in ['relaxed_normalization', 'filename_normalization'],
    "relaxed_normalization":get('filename_normalization', 'relaxed_normalization') == 'relaxed_normalization',
    "external_editor_optimize":bool(get('external_editor_optimize', False)),
    "show_portal_tools":bool(get('show_portal_tools', False)),
    "blacklist_types":tuple(get('blacklist_types', ('Topic',))),
    })

msg = 'Enfold Desktop updated'
state.set(status="success", portal_status_message=msg)
return state
