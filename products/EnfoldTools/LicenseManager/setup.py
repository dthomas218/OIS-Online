# License Manager
# Copyright(C), 2004-2006, Enfold Systems, Inc. - ALL RIGHTS RESERVED

# Enfold Systems, Inc.
# 4617 Montrose Blvd., Suite C215
# Houston, Texas 77006 USA
# p. +1 713.942.2377 | f. +1 832.201.8856
# www.enfoldsystems.com
# info@enfoldsystems.com

# $Id: setup.py 5780 2006-07-18 13:54:20Z sidnei $
# $HeadURL: https://svn.enfoldsystems.com/internal/Products/EnfoldTools/trunk/LicenseManager/setup.py $

# this is run by the installer
# which only sends out .pyc file
# instead of .py files

import py_compile
import os

for fname in [
        'seat.py',
        'products.py',
        'license.py',
        'config.py',
        '__init__.py',
        'enfold/__init__.py',
        'enfold/runtime/__init__.py',
        'enfold/runtime/license.py',
        'enfold/runtime/logutils.py',
        'enfold/runtime/tarfile_2_4.py',
        'enfold/runtime/logging_2_4/__init__.py',
        'enfold/runtime/logging_2_4/config.py',
        'enfold/runtime/logging_2_4/handlers.py',
        ]:
    fullname = os.path.abspath(fname)
    if os.path.exists(fullname):
        py_compile.compile(fullname)
        py_compile.compile(fullname, fullname+'o')
        os.remove(fullname)
    else:
        print 'File not found: %s' % fullname
