## Script (Python) "showUserError"
##bind context=context
##parameters=id
##title=Show a user's error entry, if the user matches.
##

from Products.ShellExServer.utils import showUserError, formatErrorEntry
entry = showUserError(context, id) # Might raise Unauthorized if the
                                   # user does not match.
if entry is None:
    # Entry has expired already, nothing we can do :(
    print 'Entry %s has expired' % id
else:
    print formatErrorEntry(entry)
return printed

