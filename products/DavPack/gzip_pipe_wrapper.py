##############################################################################
#
# DavPack -- A set of patches for all things related to WebDAV
# Copyright (C) 2004-2007 Enfold Systems
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
# Some portions of this module are Copyright Zope Corporatioin and
# Contributors.
# The original copyright statement is reproduced below.
#
##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""
$Id: gzip_pipe_wrapper.py 1182 2007-01-11 21:05:57Z sidnei $
"""

import zlib
import gzip

from threading import Lock
from cStringIO import StringIO
from ZServer.Producers import file_close_producer
from ZServer.Producers import file_part_producer, iterator_producer

COMPRESS_LEVEL = 6
FLUSH_SIZE = 1024 * 4 # 4Kb
CHUNK_TRAILER = '0\r\n\r\n'

class GzipFile(gzip.GzipFile):

    def flush(self):
        self.fileobj.write(self.compress.flush(zlib.Z_SYNC_FLUSH))
        gzip.GzipFile.flush(self)

class GZipPipeWrapper:

    def __init__(self, pipe, chunked):
        self.pipe = pipe
        self._channel = pipe._channel
        self.chunked = chunked
        self.buf = StringIO()
        self.lock = Lock()
        self.zobj = GzipFile(mode='wb',
                             fileobj=self.buf,
                             compresslevel=COMPRESS_LEVEL)
        self.read_start = 0
        self.write_pos = self.read_end = self.buf.tell()
        self.size = 0
        self.flush_size = 0

    def write(self, text, l=None):
        if self.chunked and text in (CHUNK_TRAILER,):
            # Finished writing data.
            return
        if not hasattr(text, 'more'):
            # A normal string
            self.write_chunk(text)
        else:
            # It's a producer, we only understand some of them.
            if not isinstance(text, (file_part_producer,
                                     file_close_producer,
                                     iterator_producer)):
                self.pipe.write(text, l)
                return
            while True:
                chunk = text.more()
                if chunk == '':
                    break
                self.write_chunk(chunk)

    def write_chunk(self, text):
        l = len(text)
        self.size += l
        self.flush_size += l

        # Compress the input data
        self.lock.acquire()
        try:
            self.buf.seek(self.write_pos)
            self.zobj.write(text)
            if self.flush_size > FLUSH_SIZE:
                # Flush some data.
                self.zobj.flush()
                self.flush_size = 0
            self.write_pos = self.read_end = self.buf.tell()
        finally:
            self.lock.release()

        # Attempt to write some of the compressed buffer data out to
        # the pipe.
        self.sync()

    def _write_chunk(self, text, l=None):
        if l is None:
            l = len(text)
        if not l:
            return
        if self.chunked:
            self.pipe.write('%x\r\n' % l)
        self.pipe.write(text, l)
        if self.chunked:
            self.pipe.write('\r\n')

    def sync(self):
        self.lock.acquire()
        try:
            # Start at end of last read, set next read start to current
            # buffer position.
            start = self.read_start
            end = self.read_end
            self.read_start = end
        finally:
            self.lock.release()

        if end == start:
            # Nothing to write.
            return

        # Our safeguard that 'write_pos' and 'read_end' do never go
        # backwards.
        assert end > start, (start, end) 

        # Dump the buffered data since last sync into the pipe.
        chunk = file_part_producer(self.buf, self.lock, start, end)
        self._write_chunk(chunk, end - start)

    def flush(self):
        self.pipe.flush()

    def finish(self, response):
        # We're done here. Make sure all the data has gone out into
        # the buffer.
        self.lock.acquire()
        try:
            self.buf.seek(self.write_pos)
            self.zobj.close()
            self.read_end = self.buf.tell()
        finally:
            self.lock.release()

        # Make sure the buffer has been fully dumped.
        self.sync()

        # Do not forget the chunk trailer.
        if self.chunked:
            self.pipe.write(CHUNK_TRAILER)

        # And also close the buffer.
        self.pipe.write(file_close_producer(self.buf), 0)

        self.pipe.finish(response)

    def close(self):
        self.pipe.close()
        self.pipe = None
        self.crc = None
        self.zobj = None
        self.size = None
        self._channel = None
