#!/usr/bin/python
#$Id: plone_desktop_config.plonecmd.py 5853 2006-07-26 15:34:52Z sidnei $
#Copyright: Enfold Systems, Inc.
#License: http://www.enfoldsystems.com

product = context.manage_addProduct['ShellExServer']
config = product.getDesktopCommandSettings()

data = """# Enfold Desktop client setup data
# this file is meant to be run with Enfold Desktop
# installed which will process this data.
#
# If you have seen this, then it's likely you
# do not have Enfold Desktop installed.
#
# See http://www.enfoldsystems.com/Products/Desktop for more
"""

data += """
[addsession]
url = %(session)s
username = %(username)s
title = %(title)s
""" % config

if config['folderish']:
    # if its a folder make a session
    data += """
[shellexecute]
verb = Explore
class = Folder
name = %(folder)s
""" % config
else:
    # if its not a folder, PD will make a session (if needed) and invoke
    data += """
[invoke]
name = %(object)s
""" % config

context.REQUEST.RESPONSE.setHeader('Content-type', 'text/x-plone-command')
return data
