# Enfold Desktop
# Copyright(C), 2004-2006, Enfold Systems, Inc. - ALL RIGHTS RESERVED

# Enfold Systems, Inc.
# 4617 Montrose Blvd., Suite C215
# Houston, Texas 77006 USA
# p. +1 713.942.2377 | f. +1 832.201.8856
# www.enfoldsystems.com
# info@enfoldsystems.com

# $Id: config.py 8870 2008-09-24 17:43:51Z sidnei $
# $HeadURL: https://svn.enfoldsystems.com/internal/ShellExServer/trunk/config.py $

import os
import sys
import logging
from Globals import package_home
from Products.Archetypes.Marshall import PrimaryFieldMarshaller

PROJECTNAME = 'ShellExServer'
DEPS = ('Calendaring', 'CMFPropertySets', 'PloneLockManager')
GLOBALS = globals()
DTML_DIR = os.path.join(package_home(GLOBALS), 'www')
HEADER_NAME = 'X-Enfold-Desktop-Portal-Type'
MAX_USERS_AND_GROUPS = 100
logger = logging.getLogger(PROJECTNAME)

CONFIG_SCHEMA = (
    ('root_plone_desktop', '', 'string'),
    ('root_browser', '', 'string'),
    ('filename_normalization', '1', 'boolean'),
    ('relaxed_normalization', '', 'boolean'),
    ('use_member_folder_session', '1', 'boolean'),
    ('external_editor_optimize', '1', 'boolean'),
    ('show_portal_tools', '', 'boolean'),
    ('configured_sessions', '', 'lines'),
    ('blacklist_types', 'Topic', 'lines'),
    )

def log(msg, **kw):
    logger.log(level=kw.get('level', logging.DEBUG), msg=msg, **kw)

def log_exc(msg=None, *args, **kw):
    if msg is None:
        msg = 'An exception occurred.'
    logger.exception(msg, *args, **kw)

# Only register if available.
DEFAULT_MASHALLER = PrimaryFieldMarshaller()
MARSHALLERS = {}

try:
    from Products.Calendaring.marshaller import EventMarshaller
    MARSHALLERS['ATEvent'] = EventMarshaller()
except ImportError:
    log_exc('EventMarshaller not available. '
            'You will not be able to import '
            'and export iCalendar files '
            'properly without this.')

try:
    from Products.Lime.marshaller import URLMarshaller
    MARSHALLERS['ATLink'] = URLMarshaller()
    MARSHALLERS['ATFavorite'] = URLMarshaller()
except ImportError:
    log_exc('URLMarshaller not available.'
            'You will not be able to import '
            'and export links properly '
            'without this.')
