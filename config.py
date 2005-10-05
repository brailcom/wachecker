### config.py --- Configuration settings

## Copyright (C) 2005 Brailcom, o.p.s.
##
## Author: Milan Zamazal <pdm@brailcom.org>
##
## COPYRIGHT NOTICE
##
## This program is free software; you can redistribute it and/or modify it
## under the terms of the GNU General Public License as published by the Free
## Software Foundation; either version 2 of the License, or (at your option)
## any later version.
##
## This program is distributed in the hope that it will be useful, but WITHOUT
## ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
## FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
## more details.
##
## You should have received a copy of the GNU General Public License along with
## this program; if not, write to the Free Software Foundation, Inc., 51
## Franklin St, Fifth Floor, Boston, MA 02110-1301 USA

import os
import sys

import log

# Directory where cached Web pages are stored
cache_directory = '/var/lib/wachecker/cache'
# Directories containing tests
test_directories = ('/usr/lib/python2.3/site-packages/wachecker/tests',)

# Program to use for validating HTML documents
sgmls_program = 'onsgmls'

# If true, read page from the server on every access to it.
# If false, try to use its cached version by default.
refresh_cache = False

# Logging instance
logger = log.Logger (sys.stderr)

# Load local configuration
for file in '/etc/wachecker/config.py', os.path.expanduser ('~/.wachecker/config.py'):
    if os.path.exists (file):
        try:
            # Check the file is readable
            open (file)
        except:
            continue
        execfile (file, globals ())
