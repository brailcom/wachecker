### log.py --- Logging

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

import StringIO
import os

import util


class Logger (object):

    def __init__ (self, stream):
        self._stream = stream
        self._eol = True        # new line just started
        self._stream_position = 0 # number of characters written so far
        
    def _terpri (self):
        if not self._eol:
            self._write (os.linesep)

    def _write (self, text):
        if text:
            stream = self._stream
            stream.write (text)
            if hasattr (stream, 'flush'):
                stream.flush ()
            # There's no terpri in Python, so we have to implement it
            # ourselves. :-(
            self._eol = (text[-len(os.linesep):] == os.linesep)
            # Again, 'tell' doesn't work for some kinds of file objects in
            # Python, so we have to implement our own version. :-(
            self._stream_position += len (text)

    def _write_formatted_message (self, format, message, eol=True):
        self._terpri ()
        text = format % (message,)
        self._write (format % (message,))
        if eol:
            self._write (os.linesep)

    def log_info (self, message):
        """Log an informational 'message'.
        """
        self._write_formatted_message ('= %s', message)

    def log_line (self, message):
        """Log 'message' on a separate line.
        """
        self._write_formatted_message ('  %s', message)

    def log_text (self, message):
        """Log a multiline text 'message'.
        """
        self._terpri ()
        s = StringIO.StringIO (message)
        while True:
            line = s.readline ()
            if not line:
                break
            self.log_line (line[:-len(os.linesep)])

    def with_action_log (self, message, function):
        """Log 'message' and call 'function'.
        'function' is called without arguments and must return a pair
        (ERROR, RETVAL,), where ERROR is a single line string or None and
        RETVAL is a return value.  Alternatively, None can be returned which is
        equivalent to returning (None, None,).
        If MESSAGE is false, log success of the action, otherwise log error.
        Return RETVAL.
        """
        self._write_formatted_message ('* %s...', message, eol=False)
        def finalize (error, _spos=self._stream_position):
            if _spos != self._stream_position:
                self._write_formatted_message ('+ %s...', message, eol=False)
            self._write ('%s.' % (util.if_ (error, 'ERROR', 'OK'),))
            self._terpri ()
        try:
            result = function ()
        except Exception:
            finalize ('exception')
            raise
        if result:
            error, retval = result
        else:
            error = retval = None
        finalize (error)
        return retval

    def log_debug (self, message):
        """Log a debug 'message'.
        """
        if __debug__:
            self._write_formatted_message ('DEBUG: %s', message)
