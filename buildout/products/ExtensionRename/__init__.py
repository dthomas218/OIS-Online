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
$Id: __init__.py 5635 2006-07-03 15:44:24Z sidnei $
"""

def initialize(context):
    # Warm up those monkeys.
    from Products.ExtensionRename import monkey
