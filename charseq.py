### charseq.py --- Usable string handling

## Copyright (C) 2006 Brailcom, o.p.s.
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


import sys
import types


str_ = sys.modules['__builtin__'].str


class String (object):
    """Class for sane handling of character sequences (AKA strings).
    
    Handling of non-8bit characters in Python is performed in a braindamaged
    way.  There are former strings and new unicode objects.  The two are
    completely separate types and they are mutually incompatible.  Python
    libraries without explicit support for the unicode type generally don't
    work with unicode objects.  Type checking in libraries is often performed
    against StringType, which fails on unicode objects.  The unicode type was
    introduced even without proper support in the standard Python library.  You
    can't mix the two types in a single output stream easily, which is a
    serious problem, because: 1. Many libraries use output streams unable to
    handle unicode objects; 2. You get both string and unicode objects in
    various places of your innocently looking Python program.

    This class is an attempt to keep the WAchecker author in a sane mental
    state when working with character sequences in Python.  It is a wrapper
    around both string and unicode objects.  It accepts both the types in its
    methods and performs reasonable actions on them.  It returns only strings
    (encoded in UTF-8) to the outer world which makes them work everywhere.  Of
    course, this limits you to the UTF-8 encoding when working with streams,
    but WAchecker works solely with UTF-8 streams, so this is not a real
    problem.

    How to use this class in your programs:

    * Import the class: 'import wachecker.charseq.String as S'

    * Wrap all string and unicode objects by it:
    
      - 'S ("foo")'

      - 'S (u"foo")'

      - 'S (str (something))'

      - 'S ("%d seconds to what" % (60,))'

      - 'S (foo.return_character_sequence ())'

    * Make sure to convert 'String's to standard Python strings when using them
      in a code you don't maintain:
      'foo.gets_string_as_arg (str (String_object))'.

    * Ensure you only work with the UTF-8 external character coding.

    * Now you can hopefully work with character sequences without much trouble.

    """

    _CODING = 'utf-8'

    def __init__ (self, object):
        """Initialize a character sequence instance.

        'object' can be a string, unicode or 'String' object.  If it is of
        other type, an exception is raised.  See the 'make' method for safe
        handling of all types.
        """
        if isinstance (object, types.StringType):
            try:
                unicode = object.decode (self._CODING)
            except UnicodeDecodeError:
                # invalid input
                unicode = object.encode ('string_escape')
        elif isinstance (object, types.UnicodeType):
            unicode = object
        elif isinstance (object, self.__class__):
            unicode = unicode (object)
        else:
            raise Exception ("Invalid object type", object)
        self._unicode = unicode

    # Standard Python methods
    
    def __str__ (self):
        return self._unicode.encode (self._CODING)
    
    def __unicode__ (self):
        return self._unicode

    def __repr__ (self):
        return '%s(%s)' % (self.__class__.__name__, repr (str_ (self)),)

    def decode (self, *args):
        string = str_ (self)
        return string.decode (*args)

    def encode (self, *args):
        return self._unicode.encode (*args)

    def __cmp__ (self, other):
        try:
            return cmp (str_ (self), str_ (self.__class__ (other)))
        except:
            return cmp (id (self), id (other))
        
    def __nonzero__ (self):
        if self._unicode:
            return True
        else:
            return False

    def __len__ (self):
        """Return number of unicode characters in the sequence."""
        return len (self._unicode)

    def __getitem__ (self, key):
        """Return key-th element of the underlying unicode object."""
        return self._unicode.__getitem__ (key)

    def __add__ (self, other):
        """Return concatenated string object."""
        return str_ (self) + str_ (self.__class__ (other))

    def __mul__ (self, other):
        """Return multiplied string object."""
        return str_ (self) * other

    # Unicode object dispatching

    def __getattr__ (self, attr):
        return getattr (self._unicode, attr)
    
    # Special methods

    def make (class_, object):
        """Return new 'String' instance if possible.

        If 'object' is a string, unicode or 'String' object, return a new
        'String' object based on the 'object' data.  Otherwise return 'None'.

        This method can be used for typechecking on character sequences.
        
        """
        try:
            return class_ (object)
        except:
            return None
    make = classmethod (make)

    def make_str (class_, object):
        """The same as 'make', but converts 'object' to string if necessary.

        Thus it can work on any object on that 'str' can be applied.

        """
        sobject = class_.make (object)
        if sobject is None:
            sobject = class_.make (str_ (object))
        return sobject
    make_str = classmethod (make_str)

    def str (class_, object):
        """Return string representation of 'object'."""
        return str_ (class_.make_str (object))
    str = classmethod (str)


def str (object):
    """Return object as a UTF-8 string.

    Unlike the standard function 'str', this function works with unicode
    objects.  It can be used as 'str' replacement.
    
    """
    return String.str (object)

