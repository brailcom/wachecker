### validator.py --- (X)HTML syntax validation

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

from config import logger
import config


def validate (location):
    """Validate (X)HTML page syntax at 'location'.
    If the page is valid, return an empty string, otherwise return a string
    containing the error report.
    """
    def block ():
        _process_input, stream = os.popen4 ('%s -s %s' % (config.sgmls_program, location.local_copy (),))
        error_report = ''
        while True:
            checker_output = stream.read ()
            if not checker_output:
                break
            error_report = error_report + checker_output
        return error_report, error_report
    return logger.with_action_log ('Checking SGML/XML syntax', block)
