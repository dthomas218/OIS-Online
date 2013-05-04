######################################################################
#
# Extension Rename - Hook into Archetypes to enforce extension usage.
# Copyright(C), 2005, Enfold Systems, Inc. - ALL RIGHTS RESERVED
#
# This software is licensed under the Terms and Conditions contained
# within the LICENSE.txt file that accompanied this software.  Any
# inquiries concerning the scope or enforceability of the license should
# be addressed to:
#
# Enfold Systems, Inc.
# 4617 Montrose Blvd., Suite C215
# Houston, Texas 77006 USA
# p. +1 713.942.2377 | f. +1 832.201.8856
# www.enfoldsystems.com
# info@enfoldsystems.com
#
######################################################################
"""
$Id: config.py 6832 2007-01-29 21:11:03Z sidnei $
"""

import logging

PROJECTNAME = 'ExtensionRename'
logger = logging.getLogger(PROJECTNAME)

def log_exc(msg=None, *args, **kw):
    if msg is None:
        msg = 'An exception occurred.'
    logger.exception(msg, *args, **kw)

def log(msg, **kw):
    level = kw.get('level', logging.DEBUG)
    if 'level' in kw:
        del kw['level']
    logger.log(level=level, msg=msg, **kw)
