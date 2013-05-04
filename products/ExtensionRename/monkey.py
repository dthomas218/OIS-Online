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
$Id: monkey.py 8873 2008-09-29 18:07:04Z sidnei $
"""

import transaction
from Acquisition import aq_inner, aq_parent
from Products.Archetypes.utils import shasattr
from Products.CMFCore.utils import getToolByName
from Products.ExtensionRename.config import log, log_exc
from Products.ShellExServer.normalize import seq, exists, normalizerFor

def renameMethod(file_ext):
    """Method factory to create renameAfterCreation methods that use
    different file extensions, yet do basically the same thing.

    Takes non-dotted file extension.

    Returns method suitable for monkey patching as '_renameAfterCreation'
    """
    fext = ".%s" % file_ext


    def _renameAfterCreation(self, check_auto_id=False):
        """Rename objects like their titles, including file extension.
        File extension for this method is .%s
        """ % fext

        container = aq_parent(aq_inner(self))
        normalize = normalizerFor(container)
        title = new_title = self.Title()

        old_id = self.getId()
        if check_auto_id and not self._isIDAutoGenerated(old_id):
            # No auto generated id
            return False

        if normalize is not None and title is not None:
            # Must have a title and a normalizer to be able to
            # generate a normalized id from the title.
            new_id = normalize(title)
        else:
            if not shasattr(self, 'generateNewId'):
                # Ok, we can't even generate a new id. Bail out.
                return False
            new_id = self.generateNewId()

        if not new_id.endswith(fext):
            # add extension if not already there
            new_id = new_id + fext

        if exists(container, new_id):
            new_id, new_title = seq(new_id, title,
                                    container, normalize)

        # Can't rename without a savepoint when using
        # portal_factory!
        transaction.savepoint(optimistic=True)
        self.setId(new_id)
        if not title == new_title:
            self.setTitle(new_title)
        return new_id

    return _renameAfterCreation

renameHTML = renameMethod('html')
renameICS = renameMethod('ics')
renameURL = renameMethod('url')

try:
    from Products.ATContentTypes.atct import ATDocument, ATEvent, ATLink
    ATDocument._renameAfterCreation = renameHTML
    ATEvent._renameAfterCreation = renameICS
    ATLink._renameAfterCreation = renameURL
    log('Hooked ATContentTypes to forcibly add extensions '
        'to newly-created Document, Event and Link.')
except ImportError:
    log_exc('ATContentTypes not available, not hooking extensions.')
