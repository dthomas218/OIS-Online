# Enfold Desktop
# Copyright(C), 2004-2006, Enfold Systems, Inc. - ALL RIGHTS RESERVED

# Enfold Systems, Inc.
# 4617 Montrose Blvd., Suite C215
# Houston, Texas 77006 USA
# p. +1 713.942.2377 | f. +1 832.201.8856
# www.enfoldsystems.com
# info@enfoldsystems.com

# $Id: utils.py 8147 2008-02-29 20:06:54Z sidnei $
# $HeadURL: https://svn.enfoldsystems.com/internal/ShellExServer/trunk/utils.py $

import os
import re
import platform
import socket

from email.MIMEText import MIMEText
from email.MIMEMultipart import MIMEMultipart
from email.Utils import formatdate, make_msgid

from xml.dom import minidom
from warnings import warn
from Acquisition import aq_base, aq_inner, aq_parent, aq_acquire
from AccessControl import Unauthorized
from AccessControl.SecurityManagement import getSecurityManager
from Globals import package_home
from ZODB.POSException import ConflictError
from ZPublisher.BeforeTraverse import NameCaller
from Products.CMFCore.Expression import createExprContext
from Products.CMFPlone import ToolNames, FactoryTool
from Products.CMFPlone.utils import getFSVersionTuple, versionTupleFromString
from Products.CMFCore.ActionInformation import oai
from Products.CMFCore.utils import _checkPermission, getToolByName
from Products.ShellExServer.config import log, log_exc
from Products.EnfoldTools.LicenseManager import products, seat

PACKAGE_HOME = package_home(globals())
SUPPRESS_ACCESSRULE = os.environ.has_key('SUPPRESS_ACCESSRULE')
ENTRY_ID = re.compile('(?P<base_url>.*)/(.*)/showEntry[\?]?id=(?P<entry_id>[\d\.]+)[&]?')

class EnvironmentSuppressAccessRule(NameCaller):
    """A AccessRule that can be disabled only by environment but not
    by URL mangling.
    """
    meta_type = 'Environment Suppress Access Rule'

    def __call__(self, container, request):
        if SUPPRESS_ACCESSRULE: return
        NameCaller.__call__(self, container, request)

def getRecords(records):
    doc = minidom.Document()
    recs = doc.createElement('records')
    doc.appendChild(recs)
    if not records:
        return recs.toxml()
    for entry in records:
        rec = doc.createElement('record')
        for k, v in entry.items():
            value = doc.createElement('value')
            name = doc.createAttribute('name')
            name.nodeValue = k
            value.setAttributeNode(name)
            txt = doc.createTextNode(v) # XXX may want to process v first
            value.appendChild(txt)
            rec.appendChild(value)
        recs.appendChild(rec)
    return recs.toxml()

def getGroupNames(ctx):
    # Return group names in a forward *and* backward compatible way
    warn('getGroupNames is deprecated, please use '
         'the portal_groups tool directly', DeprecationWarning, 2)
    gt = getToolByName(ctx, 'portal_groups', None)
    if gt is None:
        return ()
    if not hasattr(gt, 'listGroupIds'):
        return ()
    return gt.listGroupIds()

def get_root(context):
    request = getattr(context, 'REQUEST', None)
    assert request is not None, 'Cannot find REQUEST from %r' % context
    vroot = request.get('VirtualRootPhysicalPath', None)
    if vroot is not None:
        root = context.unrestrictedTraverse(vroot)
    else:
        purl = getToolByName(context, 'portal_url')
        root = purl.getPortalObject()
    return root

def get_roots(context):
    # Handle FactoryDispatcher.
    dst =  getattr(aq_base(context), 'Destination', None)
    if dst is not None:
        context = context.Destination()

    # We have disabled the configuration for Enfold Desktop and
    # Browser root because our 'guessing' has gotten so much better
    # since and the configuration causes more trouble than it helps
    # now.
    ed_root = browser_root = ''

    # pp = getToolByName(context, 'portal_properties')
    # c = getattr(pp, 'plone_desktop_uri', pp)
    # ed_root = getattr(c, 'root_plone_desktop', '').strip()
    # browser_root = getattr(c, 'root_browser', '').strip()
    if not ed_root or not browser_root:
        # Has not been configured yet. Try a best-guess by looking
        # at a VHM root and failing that, default to portal
        # root. This should be good enough in 99% of the cases,
        # and avoid user frustration of having to go enable
        # something before 'View in Plone' works.
        url = get_root(context).absolute_url()
        if not ed_root:
            ed_root = url
        if not browser_root:
            browser_root = url
    return ed_root.rstrip('/'), browser_root.rstrip('/')

def view_path(context):
    """Given a context object, try to lookup the best available
    default 'view' url. We don't use Plone's browserDefault here
    because that can potentially lead to a 'download' url for files
    and images.
    """
    # Handle FactoryDispatcher.
    dst =  getattr(aq_base(context), 'Destination', None)
    if dst is not None:
        context = context.Destination()

    purl = getToolByName(context, 'portal_url')
    absolute = context.absolute_url()
    relative = context.absolute_url(1)

    # getRelativeContentURL doesn't take 'VHM' into account, so we fix
    # that up.
    portal_relative = purl.getRelativeContentURL(context)
    request = getattr(context, 'REQUEST', None)
    if request is not None:
        vroot = request.get('VirtualRootPhysicalPath', None)
        if vroot is not None:
            physical_path = '/'.join(context.getPhysicalPath())
            portal_relative = physical_path.replace('/'.join(vroot), '')
            if portal_relative.startswith('/'):
                portal_relative = portal_relative[1:]

    # Currently (Plone 2.1.x) the correct default 'view' for a Folder
    # is '/' and not '/view', so we skip this logic if it's folderish.
    if context.isPrincipiaFolderish:
        return portal_relative

    ti = context.getTypeInfo()
    if ti is not None:
        # First of all, if it has a 'folderlisting' action, use that.
        # Then, if that doesn't cut it, try the 'view' action.
        action_chain = ('folder/folderlisting', 'object/view')
        try:
            url = ti.getActionInfo(action_chain, context)['url']
        except (ValueError, Unauthorized):
            pass
        else:
            for r in (absolute, relative, '/'):
                if url.startswith(r):
                    # Replace only at the start.
                    url = url.replace(r, '')
            return '/'.join((portal_relative, url))
    # If we got this far, we haven't been able to find a proper action
    # for the object. Try the relative (to portal) content url.
    return portal_relative

interesting_providers = ('portal_actions', 'portal_types')
def listFilteredActionsForCategory(self, object, required_category,
                                   interesting=interesting_providers):
    """
    This is an override over the default one so its wayyyy faster

    Return a mapping containing of all actions available to the
    user against object, bucketing into categories.
    """
    portal = aq_parent(aq_inner(self))
    if object is None or not hasattr(object, 'aq_base'):
        folder = portal
    else:
        folder = object
        # Search up the containment hierarchy until we find an
        # object that claims it's a folder.
        while folder is not None:
            if getattr(aq_base(folder), 'isPrincipiaFolderish', 0):
                # found it.
                break
            else:
                # !!! This is the only change from
                # CMFCore.ActionsTool.listFilteredActionsFor
                # If the parent of the object in hand is a TempFolder
                # don't strip off its outer acquisition context.
                parent = aq_parent(aq_inner(folder))
                klass = getattr(parent, '__class__', None)
                if klass == FactoryTool.TempFolder:
                    folder = aq_parent(folder)
                else:
                    folder = parent
    ec = createExprContext(folder, portal, object)
    actions = []
    append = actions.append
    info = oai(self, folder, object)

    # Include actions from specific tools.
    #
    # We are really only interested in a few ones though.
    for provider_name in interesting:
        # skip around failed product installs
        try:
            provider = getattr(self, provider_name)
        except AttributeError:
            continue
        # Watch out for broken providers!
        if hasattr(aq_base(provider), 'listActions'):
            actions = actions + list(provider.listActions(info))

    # Include actions from object.
    if object is not None:
        if hasattr(aq_base(object), 'listActions'):
            actions = actions + list(object.listActions(info))

    # Reorganize the actions by category,
    # filtering out disallowed actions.
    filtered_actions={'user':[],
                      'folder':[],
                      'object':[],
                      'global':[],
                      'workflow':[],
                      }

    for raw_action in actions:
        # first filter out categories
        if required_category:
            # Account for Workflow actions, which are still old-style.
            if (isinstance(raw_action, dict)
                and raw_action.has_key('category')):
                if raw_action['category'] != required_category:
                    continue
                else:
                    action = raw_action
            else:
                if hasattr(aq_base(raw_action), 'getCategory'):
                    if raw_action.getCategory() != required_category:
                        continue
                elif hasattr(aq_base(raw_action), 'getInfoData'):
                    from Products.CMFCore.ActionInformation import ActionInfo
                    action = ActionInfo(raw_action, ec)
                    if action['category'] != required_category:
                        continue
                else:
                    # What else?
                    continue

        # Now start filtering.
        # Account for Workflow actions, which are still old-style.
        __traceback_info__ = (raw_action,)
        if not isinstance(raw_action, dict):
            if (hasattr(raw_action, 'testCondition') and 
                raw_action.testCondition(ec)):
                action = raw_action.getAction(ec)

        category = action['category']

        permissions = action.get('permissions', None)
        visible = action.get('visible', 1)
        if not visible:
            continue
        verified = 0
        if not permissions:
            # This action requires no extra permissions.
            verified = 1
        else:
            # startswith() is used so that we can have several
            # different categories that are checked in the object or
            # folder context.
            if (object is not None and
                (category.startswith('object') or
                 category.startswith('workflow'))):
                context = object
            elif (folder is not None and
                  category.startswith('folder')):
                context = folder
            else:
                context = portal
            for permission in permissions:
                # The user must be able to match at least one of
                # the listed permissions.
                if _checkPermission(permission, context):
                    verified = 1
                    break
        if verified:
            catlist = filtered_actions.setdefault(category, [])
            catlist.append(action)
    return filtered_actions

def inside(ob, other):
    p1 = '/'.join(ob.getPhysicalPath())
    p2 = '/'.join(other.getPhysicalPath())
    return p2.startswith(p1)

def getDesktopSessions(context):
    """List of configured root sessions for desktop
    """
    # Handle FactoryDispatcher.
    dst =  getattr(aq_base(context), 'Destination', None)
    if dst is not None:
        context = context.Destination()

    res = []
    pp = getToolByName(context, 'portal_properties', None)
    if pp is None:
        log('portal_properties not found at %s.' % context.absolute_url())
        return res

    props = getToolByName(pp, 'plone_desktop_uri', None)
    if props is None:
        log('plone_desktop_uri not found at %s.' % context.absolute_url())
        return res

    use_site = props.getProperty('use_site_root_session', True)
    use_member = props.getProperty('use_member_folder_session', True)
    configured = props.getProperty('configured_sessions', [])

    purl = getToolByName(context, 'portal_url')
    portal = purl.getPortalObject()
    root = get_root(context)

    site_root, ignored = get_roots(context)
    res.append((site_root, root.title_or_id()))

    if use_member:
        mt = getToolByName(context, 'portal_membership')
        home_folder = mt.getHomeFolder()
        if home_folder is not None:
            if inside(root, home_folder):
                res.append((home_folder.absolute_url(),
                            home_folder.title_or_id()))

    traverse = portal.restrictedTraverse
    for path in configured:
        try:
            path = path.split('/')
            path = filter(None, path)
            ob = traverse(path)
            if inside(root, ob):
                res.append((ob.absolute_url(), ob.title_or_id()))
        except ('NotFound', KeyError, AttributeError):
            log('%s is not a valid path.' % path)
        except Unauthorized:
            pass

    res.sort()
    res.reverse()

    accessed_root = root.absolute_url().rstrip('/')
    if not accessed_root == site_root:
        for idx, (r, t) in enumerate(res):
            res[idx] = (r.replace(accessed_root, site_root), t)

    return res

def getDesktopCommandSettings(context):
    """Get Desktop Command Settings for a specific object
    """
    # Handle FactoryDispatcher.
    dst =  getattr(aq_base(context), 'Destination', None)
    if dst is not None:
        context = context.Destination()

    config = {}

    pp = getToolByName(context, 'portal_properties', None)
    if pp is None:
        log('portal_properties not found at %s.' % context.absolute_url())
        return config

    props = getToolByName(pp, 'plone_desktop_uri', None)
    if props is None:
        log('plone_desktop_uri not found at %s.' % context.absolute_url())
        return config

    purl = getToolByName(context, 'portal_url')

    root = get_root(context)
    site_root, ignored = get_roots(context)

    parent = aq_parent(context)
    obj_url = context.absolute_url()
    parent_url = parent.absolute_url()

    folderish = False
    if (getattr(aq_base(context), "isPrincipiaFolderish", None) and
        context.isPrincipiaFolderish):
        folderish = True

    config['external_editor_optimize'] = props.getProperty('external_editor_optimize', True)
    config['folderish'] = folderish

    if not site_root:
        # Should never happen in 3.0 and beyond.
        raise ValueError(
            "The administrator has not set a WebDAV URI for this instance. "
            "If you are the site administrator please go to "
            "site setup > Enfold Desktop and configure these values.")

    request = context.REQUEST
    sessions = getDesktopSessions(context)
    session = title = None
    for s, t in sessions:
        if obj_url.startswith(s):
            session = s
            title = t
            break

    __traceback_info__ = (sessions, obj_url, site_root, context)

    # This should never *ever* happen!
    assert session is not None, ('Could not find a session containing '
                                 'the object at %s.' % obj_url)

    config['session'] = session
    config['title'] = title
    config['object'] = obj_url
    if folderish:
        config['folder'] = obj_url
    else:
        config['folder'] = parent_url

    config['username'] = getSecurityManager().getUser().getUserName()
    return config

def getExternalEditorMetadata(context, metadata, request, response):
    # Get Desktop Settings. If not found, bail out.
    config = getDesktopCommandSettings(context)
    if not config:
        return

    # If external_editor_optimize is not disabled then set the
    # 'skip_data' request variable so that External Editor doesn't
    # send the body with the metadata when clicking on it's icon.
    if config.get('external_editor_optimize', True):
        request.set('skip_data', '1')

    # Get the accessed root and the configured root. If they are
    # different then we fixup the url in metadata as well.
    root = get_root(context)
    root_url = root.absolute_url()
    site_root, ignored = get_roots(context)

    if not root_url == site_root:
        for idx, entry in enumerate(metadata):
            if entry.startswith('url:'):
                metadata[idx] = entry.replace(root_url, site_root)
                break

    # Finally, append Enfold Desktop-specific metadata.
    metadata.append('x-desktop-session-url: %s' % config['session'])
    metadata.append('x-desktop-session-title: %s' % config['title'])
    metadata.append('x-desktop-session-username: %s' % config['username'])

def setupExternalEditorCallback():
    try:
        from Products.ExternalEditor.ExternalEditor import registerCallback
    except ImportError:
        log_exc('Could not find External Editor or newer version required.')
    else:
        registerCallback(getExternalEditorMetadata)
        log('Registered External Editor Callback.')

def getDesktopLicenseInfo(context):
    """ Get the number of licensed desktop seats
    """
    info = products.getDesktopLicenseData()
    if not info:
        return info
    info['allocated'] = seat.allocated_desktop_licenses(context)
    info['available'] = seat.get_desktop_seats(context)
    return info

def standard_error_message(context, **kwargs):
    """Delegate to the correct error message depending on the kind of
    request coming in.
    """
    error_type = kwargs.get('error_type', None)
    error_message = kwargs.get('error_message', None)
    error_log_url = kwargs.get('error_log_url', None)
    error_tb = kwargs.get('error_tb', None)
    error_traceback = kwargs.get('error_traceback', None)
    error_value = kwargs.get('error_value', None)

    request = context.REQUEST
    request_method = request.get('REQUEST_METHOD', 'GET')

    is_webdav = False
    if (request.environ.get('WEBDAV_SOURCE_PORT') or
        request_method not in ('GET', 'POST', 'HEAD')):
        mth = context.webdav_error_message
        is_webdav = True
    else:
        mth = context.default_error_message

    entry_id = error_base_url = None
    if error_log_url:
        match = ENTRY_ID.match(error_log_url)
        if match:
            d = match.groupdict()
            entry_id = d.get('entry_id', None)
            # We used to use the base url parsed from the full
            # error_log_url. Now we use the currently accessed URL and
            # let acquisition kick in, so that we can guarantee that
            # the error URL is inside the session.
            #
            # error_base_url = d.get('base_url', None)
            error_base_url = context.absolute_url()

    if entry_id and error_base_url:
        # If we have the entry_id from the SiteErrorLog, then we can
        # fetch the traceback formatted as text and also compute a url
        # that is accessible only by the user.
        try:
            log = aq_acquire(context, '__error_log__', containment=1)
        except AttributeError:
            pass
        else:
            if is_webdav:
                # The original error_log_url is unlikely to be useful
                # in this context, so we compute one that only the
                # user that got the error can access.
                error_log_url = '%s/showUserError?id=%s' % (error_base_url,
                                                            entry_id)

            entry = log.getLogEntryById(entry_id)
            info = None
            info_tool = None
            if entry is not None:
                # Fetch error value and traceback text from the
                # SiteErrorLog.
                if is_webdav:
                    error_value = entry['value']
                    error_tb = entry['tb_text']

            # Then stuff some extra info from EnfoldErrorReporting
            # into the error log entry if it's installed.
            info_tool = getToolByName(context, 'enfold_info', None)

            # Should we do the info_tool dance?
            if info_tool is not None:
                entries = log._getLog()
                for _e in entries:
                    if _e['id'] == entry_id:
                        _e['enfold'] = info = {}
                        break

            # XXX Should we move this to EnfoldErrorReporting?
            #
            # If we found the entry and the EnfoldErrorReporting tool,
            # then stuff the extra info into it.
            if info_tool is not None and info is not None:
                try:
                    pas_info = info_tool.getPASPluginInfo()
                    info['plugin_info'] = pas_info.get('plugin_info')
                    info['desktop_info'] = info_tool.getEnfoldDesktopInfo()
                    info['caching_info'] = info_tool.getCachingInfo()
                    info['windows_username'] = info_tool.getWindowsUserName()
                except ConflictError:
                    raise
                except:
                    log_exc()

    if error_log_url:
        request.RESPONSE.setHeader('X-Error-Log-Url', error_log_url)
    error_page = mth(client=context,
                     error_type=error_type,
                     error_message=error_message,
                     error_tb=error_tb,
                     error_value=error_value,
                     error_log_url=error_log_url)

    if isinstance(error_page, unicode):
        # Make sure the rendered error_page is not unicode, but utf-8
        # encoded.
        error_page = error_page.encode('utf-8')
    return error_page

def showUserError(context, id):
    try:
        log = aq_acquire(context, '__error_log__', containment=1)
    except AttributeError:
        return

    entry = log.getLogEntryById(id)
    if entry is None:
        return

    user = getSecurityManager().getUser()
    username = user.getUserName()
    userid = user.getId()

    if not (entry['userid'] == userid and entry['username'] == username):
        raise Unauthorized('You are not allowed to see this error entry')

    return entry

def formatErrorEntry(entry):
    stamp = formatdate()
    msg = MIMEMultipart()

    msg['From'] = '%s@%s' % (entry['username'], socket.gethostname())
    msg['To'] = 'bugs@enfoldsystems.com'
    msg['Date'] = stamp
    msg['Subject'] = '%s at %s' % (entry['type'],
                                   entry['url'])

    # Do the standard stuff
    for key, value in entry.items():
        if key not in ('type', 'username', 'userid', 'url', 'id'):
            continue
        parts = ['X', 'Error'] + [p.capitalize() for p in key.split('_')]
        name = '-'.join(parts)
        msg[name] = value

    def m(text, name, typ, enc):
        t = MIMEText(text, typ, enc)
        t['Name'] = name
        return t

    msg.attach(m(entry['value'], 'value', 'plain', 'utf-8'))
    msg.attach(m(entry['tb_text'], 'tb_text', 'plain', 'utf-8'))
    msg.attach(m(entry['req_html'], 'req_html', 'plain', 'utf-8'))
    msg.attach(m(serverVersion(), 'server_version', 'plain', 'utf-8'))
    msg.attach(m(platform.platform(), 'server_os_version', 'plain', 'utf-8'))

    # Then check if we have extra info from the EnfoldErrorReporting
    for key, value in entry.get('enfold', {}).items():
        msg.attach(m(value, key, 'plain', 'utf-8'))

    return msg.as_string()

def versionTupleToString(vt):
    vt = map(str, vt)
    return '.'.join(vt[:3]) + '-' + ''.join(vt[3:])

def serverVersion():
    vfile = os.path.join(PACKAGE_HOME, 'version.txt')
    if os.path.exists(vfile):
        v_str = open(vfile, 'r').read().lower()
        shellex_version = versionTupleToString(versionTupleFromString(v_str))
    else:
        shellex_version = 'Unknown'

    plone_version = versionTupleToString(getFSVersionTuple())

    # XXX Read version from Control Panel on Windows
    server_version = 'Unknown'
    
    return 'Enfold Server (%s), Plone (%s), ShellExServer (%s)' % (
        server_version, plone_version, shellex_version)
