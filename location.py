### location.py --- URL handling and fetching

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

import codecs
import httplib
import md5
import mimetypes
import os
import string
import StringIO
import urllib
import urllib2
import urlparse

from config import logger
import config
import document
import exception
import util


class Location (object):
    """Represents location identified by URL.
    """

    def __init__ (self, url, mime_type=None, refresh_cache=util.undefined_argument):
        """Create location identified by 'url' given as a string.
        If 'mime_type' is given, it explicitly specifies the MIME type of the
        location.  It must be either of the form returned by the 'mime_type'
        method or a common MIME type string.
        If 'refresh_cache' is true, refresh page cache on the first page
        access.
        """
        self._url = url
        self._local_copy_name_ = None
        if refresh_cache is util.undefined_argument:
            self._refresh_cache = config.refresh_cache
        else:
            self._refresh_cache = refresh_cache
        self._mime_type = mime_type and self._parse_mime_type (mime_type)
        self._headers = None

    def _parse_mime_type (self, mime_type):
        default_mime_type = (None, None,)
        if isinstance (mime_type, basestring):
            # Split and convert from Unicode
            mime_type = [str (s) for s in string.split (mime_type, '/')]
        elif not util.is_sequence (mime_type):
            mime_type = default_mime_type
        if len (mime_type) != 2:
            mime_type = default_mime_type
        return tuple (mime_type)
    
    def _find_headers (self):
        # Cached?
        cache_file = self._headers_file_name ()
        try:
            headers = httplib.HTTPMessage (open (cache_file))
        except:
            headers = None
        # Retrieve
        if not headers:
            url = self.url ()
            host = urlparse.urlparse (url)[1]
            def block ():
                try:
                    connection = urllib2.urlopen (url)
                    headers = connection.info ()
                    connection.close ()
                except urllib2.HTTPError:
                    return 'URL could not be fetched', None
                return None, headers
            headers = logger.with_action_log ('Connecting to %s' % (host,), block)
        # Save
        if headers:
            try:
                open (cache_file, 'w').write (headers)
            except:
                pass
        else:
            headers = httplib.HTTPMessage (StringIO.StringIO (''), seekable=0)
        return headers

    def _find_mime_type (self):
        # Cached?
        cache_file = self._mime_type_file_name ()
        try:
            mime_type_string = open (cache_file).read ()
        except:
            mime_type_string = None
        # Guess
        if not mime_type_string:
            url = self.url ()
            mime_type_string = mimetypes.guess_type (url)[0]
        # Retrieve        
        if not mime_type_string:
            mime_type_string = self._find_headers ().gettype ()
        # Save
        if mime_type_string:
            mime_type = self._parse_mime_type (mime_type_string)
            try:
                open (cache_file, 'w').write ('%s/%s' % mime_type)
            except:
                pass
        else:
            mime_type = ''    # not None -- to avoid future repeated retrievals
        return mime_type

    def _local_copy_name (self):
        if not self._local_copy_name_:
            hash_ = md5.new (self.url ()).hexdigest ()
            self._local_copy_name_ = os.path.join (config.cache_directory, hash_)
        return self._local_copy_name_

    def _charset_file_name (self):
        return self._local_copy_name () + '.charset'

    def _mime_type_file_name (self):
        return self._local_copy_name () + '.mimetype'

    def _headers_file_name (self):
        return self._local_copy_name () + '.headers'
    
    def _local_copy_charset (self):
        self._ensure_local_copy ()
        f = open (self._charset_file_name ())
        return f.read ()

    def _fetch (self):
        if not os.path.exists (config.cache_directory):
            try:
                os.mkdir (config.cache_directory)
            except OSError, e:
                raise exception.System_Error ("Write to local disk failed", e)
        copy_name = self._local_copy_name ()
        def block ():
            try:
                _file_name, headers = urllib.urlretrieve (self.url (), copy_name)
            except IOError, e:
                raise exception.System_Error ("URL could not be retrieved", e)
            charset = headers.getparam ('charset') or ''
            try:
                f = open (self._charset_file_name (), 'w')
                f.write (charset)
                f.close ()
                f = open (self._headers_file_name (), 'w')
                f.write (str (headers))
                f.close ()
            except Exception, e:
                raise exception.System_Error ("Write to local disk failed", e)
        logger.with_action_log ('Fetching page', block)

    def _ensure_local_copy (self):
        if not os.path.exists (self._local_copy_name ()) or self._refresh_cache:
            self._fetch ()
            self._refresh_cache = False
        
    def _open (self):
        file_name = self.local_copy ()
        charset = self._local_copy_charset () or 'utf-8'
        input_codec = codecs.getreader (charset)
        return input_codec (open (file_name))

    def __str__ (self):
        return self.url ()

    def __eq__ (self, other):
        return (self.__class__ == other.__class__ and
                self.url () == other.url ())

    def __ne__ (self, other):
        return not self.__eq__ (other)

    def url (self):
        """Return the url of the location, as a string.
        """
        return self._url

    def protocol (self):
        """Return protocol name of the location, as a string.
        """
        url = self.url ()
        return urlparse.urlparse (url)[0]

    def mime_type (self):
        """Return the MIME type of the location as a pair (MAJOR, MINOR,).
        If the MIME type cannot be determined, return None.
        """
        if self._mime_type is None:
            self._mime_type = self._find_mime_type ()
        return self._mime_type

    def header (self, header):
        """Return the value of 'header', as a string.
        """
        if self._headers is None:
            self._headers = self._find_headers ()
        return self._headers.getparam (header)
    
    def local_copy (self):
        """Return the name of the local copy file.
        """
        self._ensure_local_copy ()
        return self._local_copy_name ()

    def document (self):
        """Return the location document as a 'document.Document' instance.
        """
        p = document.Parser (location=self)
        p.feed (self._open ().read ())
        return p.document ()

    def open (self):
        """Return a stream of the location contents.
        """
        return self._open ()

    def make_location (self, url, mime_type=None):
        """Return new location from 'url'.
        If 'url' is not an absolute URL, use 'self' as the base URL.
        If 'mime_type' is given, it explicitly specifies the MIME type of the
        location.  It must be either of the form returned by the 'mime_type'
        method or a common MIME type string.
        """
        url_parsed = list (urlparse.urlparse (url))
        self_parsed = urlparse.urlparse (self.url ())
        if not url_parsed[0]:   # protocol
            url_parsed[0] = self_parsed[0]
            if not url_parsed[1]: # server
                url_parsed[1] = self_parsed[1]
                path = url_parsed[2]
                if path and path != '/' and self_parsed[2]: # relative path
                    dirname = os.path.dirname (self_parsed[2])
                    url_parsed[2] = os.path.join (dirname, path)
                if not url_parsed[5]: # anchor
                    url_parsed[5] = self_parsed[5]
        full_url = urlparse.urlunparse (tuple (url_parsed))
        return Location (full_url, mime_type=mime_type)
