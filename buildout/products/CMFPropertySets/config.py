"""
$Id: config.py 919 2006-01-17 15:32:33Z sidnei $
"""

import sys
from zLOG import LOG, INFO, ERROR

PROJECTNAME = 'CMFPropertySets'

def log(msg, **kw):
    LOG(PROJECTNAME, kw.get('level', INFO), msg)

def log_exc(msg=None, *args, **kwargs):
    # Logging package doesn't like (None, None, None)!
    error = sys.exc_info()
    if error[0] is None: error = None
    LOG(PROJECTNAME, kwargs.get('level', ERROR),
        msg, error=error,
        reraise=kwargs.get('reraise', None))
