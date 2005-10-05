### exception.py --- WAchecker exceptions

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

class Wachecker_Exception (Exception):
    """WAchecker exception raised when an error occurs.
    """

    def __init__ (self, message, *args):
        Exception.__init__ (self, message, *args)

    def message (self):
        """Return WAchecker error message.
        """
        return self.args[0]


class System_Error (Wachecker_Exception):
    """WAchecker exception raised when a system error occurs.
    """

    def __init__ (self, message, exception, *args):
        Wachecker_Exception.__init__ (self, message, exception, *args)
    
    def exception (self):
        """Return the original exception.
        """
        return self.args[1]
