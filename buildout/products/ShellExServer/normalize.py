# Enfold Desktop
# Copyright(C), 2004-2006, Enfold Systems, Inc. - ALL RIGHTS RESERVED

# Enfold Systems, Inc.
# 4617 Montrose Blvd., Suite C215
# Houston, Texas 77006 USA
# p. +1 713.942.2377 | f. +1 832.201.8856
# www.enfoldsystems.com
# info@enfoldsystems.com

# $Id: normalize.py 7720 2007-11-28 03:09:54Z sidnei $
# $HeadURL: https://svn.enfoldsystems.com/internal/ShellExServer/trunk/normalize.py $

import re
import os.path

from webdav import NullResource
from Acquisition import aq_base
from ExtensionClass import Base
from ZPublisher.BeforeTraverse import registerBeforeTraverse
from ZPublisher.BeforeTraverse import unregisterBeforeTraverse
from Products.CMFCore.utils import getToolByName
from Products.ShellExServer.utils import EnvironmentSuppressAccessRule

try:
    from Products.CMFPlone.utils import normalizeString
except ImportError: # Plone 2.1.x
    from Products.CMFPlone.PloneTool import PloneTool
    class FakeTool:
        def __init__(self, enc):
            self.enc = enc
        def getSiteEncoding(self):
            return self.enc or 'utf-8'
        normalizeString = PloneTool.normalizeString.im_func
        
    def normalizeString(name, encoding=None, relaxed=False):
        tool = FakeTool(encoding)
        try:
            return tool.normalizeString(name, relaxed=relaxed)
        except TypeError: # Pre-relaxed
            return tool.normalizeString(name)

HOOK_NAME = 'webdav_normalizer_hook'
PRIORITY = 0
FLAG = '_%s_installed' % HOOK_NAME
_marker = object()

SEQ = re.compile('(?P<fname>.*?)(?P<sep>[ -]{1})(?P<seq>\d+)$')

def install_hook(self, out, adding=False):
    if getattr(aq_base(self), FLAG, _marker) is not _marker:
        print >> out, 'Unregistering %s.' % HOOK_NAME
        unregisterBeforeTraverse(self, HOOK_NAME)
        delattr(self, FLAG)
        delattr(self, HOOK_NAME)

    if adding:
        print >> out, 'Registering %s.' % HOOK_NAME
        setattr(self, HOOK_NAME, Normalizer())
        hook = EnvironmentSuppressAccessRule(HOOK_NAME)
        registerBeforeTraverse(self, hook, HOOK_NAME, PRIORITY)
        setattr(self, FLAG, True)

class FilenameNormalizer:

    def __init__(self, enc, relaxed):
        self.enc = enc
        self.relaxed = relaxed

    def __call__(self, name):
        name = normalizeString(name, encoding=self.enc, relaxed=self.relaxed)
        if isinstance(name, unicode):
            name = name.encode(self.enc)
        if not self.relaxed:
            # In Plone 2.5, non-relaxed mode would lowercase. So we do
            # lowercase here for bw compatibility.
            name = name.lower()
        return name

def normalizerFor(context):
    # See if we can find the setting that controls normalization
    # and if it's enabled.
    pp = getToolByName(context, 'portal_properties', None)
    if pp is None:
        return

    ed = getToolByName(pp, 'plone_desktop_uri', None)
    if ed is None:
        return

    enabled = ed.getProperty('filename_normalization', True)
    if not enabled:
        return

    relaxed = ed.getProperty('relaxed_normalization', True)

    enc = getattr(context, 'management_page_charset', 'utf-8')
    normalizer = FilenameNormalizer(enc, relaxed)

    return normalizer

def exists(parent, name):
    got = parent.unrestrictedTraverse(name, None)
    if got is None:
        return False
    if hasattr(aq_base(got), 'isTemporary') and got.isTemporary():
        return False
    if isinstance(got, NullResource.NullResource):
        return False
    return True

def seq(name, original_name, parent, normalize):
    # An object already exists with the normalized
    # name, so we generate a new name to avoid clashes.
    fname, ext = os.path.splitext(name)
    name_fname = fname

    # If the filename contains a sequence number initialize the
    # seq variable with it and remove it from the filename for
    # looking for 'similar' items.
    match = SEQ.match(fname)
    sep = ' '
    seq = name_seq = ''
    if match is not None:
        md = match.groupdict()
        fname = md['fname']
        sep = md['sep']
        seq = int(md['seq']) + 1
        name_seq = md['seq']

    # Do the same as above for the original filename, we just
    # extract the sequence here. The new 'original_name' (used as
    # title somewhere else) is put back together after the loop
    # below.
    orig_fname, orig_ext = os.path.splitext(original_name)
    orig_sep = ' '
    orig_seq = ''
    match = SEQ.match(orig_fname)
    if match is not None:
        md = match.groupdict()
        orig_fname = md['fname']
        orig_sep = md['sep']
        orig_seq = md['seq']

    # Now, sort by sequential number, in numeric order instead of alpha.
    similar = []
    for n in parent.objectIds():
        if n.startswith(name_fname) and n.endswith(ext):
            match = SEQ.match(os.path.splitext(n)[0])
            if match:
                md = match.groupdict()
                similar.append(((int(md['seq']), md['fname']), n))
            else:
                similar.append((0, n))

    similar.sort()
    similar = [n for o, n in similar]

    # Shortcut. If the original fname with the sequence number does not
    # exist then look no further and just return it as-is.
    if not name in similar:
        return name, original_name

    while True:
        # Keep trying while there are similar
        # filenames, and when there is no more then
        # use '1'.
        if not similar:
            seq = 1
            break

        # If the last one ends with some number then that's
        # the sequence. Otherwise start from one.
        last = similar.pop()
        match = SEQ.match(os.path.splitext(last)[0])
        if match is not None:
            md = match.groupdict()
            fname = md['fname']
            if fname == name_fname or name_seq != md['seq']:
                sep = md['sep']
                seq = int(md['seq']) + 1
            else:
                name_sep = sep or ('-' in fname and '-' or
                                   ' ' in fname and ' ') or ' '
                if name_seq:
                    sep = '%s%s%s' % (sep, name_seq, name_sep)
                seq = 1
            if name_seq and (orig_seq or last != name):
                orig_sep = '%s%s%s' % (orig_sep, 
                                       name_seq, 
                                       orig_sep or ' ')
            break

    # Compute the new name now, filename + sep + seq +
    # extension.
    name = '%s%s%s%s' % (fname, sep, seq, ext)
    original_name = '%s%s%s%s' % (orig_fname, orig_sep, seq, orig_ext)

    # And then do the normalization again.
    name = normalize(name)
    return name, original_name

class Normalizer(Base):

    def __init__(self): pass

    def __call__(self, container, request):
        # Only act on PUT, MKCOL, MOVE, COPY
        method = request.get('REQUEST_METHOD', 'GET').upper()
        if method not in ('PUT', 'MKCOL', 'MOVE', 'COPY'):
            return

        stack = request['TraversalRequestNameStack']
        if '/' in stack:
            # Virtual Hosting setup, we will be traversed
            # again so return immediately.
            return

        if not stack:
            # Should this ever happen?
            return

        normalize = normalizerFor(container)
        if normalize is None:
            return

        # Alright, it's a method we want to handle.
        if method in ('PUT', 'MKCOL'):
            # If it's a PUT or MKCOL we want to normalize the URL, so
            # tweak TraversalRequestNameStack.
            original_name = stack[0]
            parent_path = stack[::-1][:-1]
            parent = container.unrestrictedTraverse(parent_path, None)

            if parent is None:
                # Nothing we can do here
                return

            force = request.get_header('X-Force-New-Name', '')

            if not force:
                if exists(parent, original_name):
                    # The object already exists with the non-normalized
                    # name, so that might mean it was created before
                    # normalization being enabled. We keep the original
                    # name as-is so it doesn't break existing files.
                    return

            # Do the normalization.
            name = stack[0] = normalize(original_name)

            if force:
                # Check the generated filename again, for name
                # clashes. If there's a clash we generate a sequential
                # filename.
                name, original_name = seq(name, original_name,
                                          parent, normalize)
                stack[0] = name

            request.RESPONSE.setHeader('X-Renamed-From', original_name)
            request.RESPONSE.setHeader('X-Renamed-To', name)

        elif method in ('COPY', 'MOVE'):
            # If it's a COPY or MOVE then we need to tweak the
            # 'Destination' header.
            dest = request.get_header('Destination', '')
            while dest and dest[-1] == '/':
                dest = dest[:-1]
            if not dest:
                # Should this ever happen?
                return

            try:
                path = request.physicalPathFromURL(dest)
                # The default access rule installed does set the
                # 'SiteRootPATH' to '/' and appends 'Plone' to the
                # TraversalRequestNameStack, which seems to be wrong
                # from my perspective. So if we detect that, we hack
                # around it by inserting the parent id into the
                # destination path. That will make the traversal to find
                # the parent object work in this pathological case.
                if request.other.get('SiteRootPATH') in ('/',):
                    if path and path[0] in ('',):
                        path.insert(1, container.getId())
            except ValueError:
                # Malformed Destination header, ignore.
                return

            original_name = path[-1]
            parent_path = path[:-1]
            parent = container.unrestrictedTraverse(parent_path, None)

            if parent is None:
                # Nothing we can do here
                return

            force = request.get_header('X-Force-New-Name', '')

            if not force:
                if exists(parent, original_name):
                    # The object already exists with the non-normalized
                    # name, so that might mean it was created before
                    # normalization being enabled. We keep the original
                    # name as-is so it doesn't break existing files.
                    return

            # We just want to normalize the name.
            name = normalize(original_name)

            if force:
                # Check the generated filename again, for name
                # clashes. If there's a clash we generate a sequential
                # filename.
                name, original_name = seq(name, original_name,
                                          parent, normalize)

            dest = '/'.join(parent_path + [name])

            # Hack the environment!
            request.environ['DESTINATION'] = dest
            request.RESPONSE.setHeader('X-Renamed-From', original_name)
            request.RESPONSE.setHeader('X-Renamed-To', name)
