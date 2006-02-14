### util.py --- Miscellaneous utilities

## Copyright (C) 2005, 2006 Brailcom, o.p.s.
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

import copy
import os
import re

import charseq


# Very basic utilities which should be present in any standard language library


def sort (sequence, compfunc=None):
    """Return a sorted copy of 'sequence'.
    Use 'compfunc' if given as in 'list.sort'.
    """
    sequence_copy = copy.copy (sequence)
    sequence_copy.sort (compfunc)
    return sequence_copy


def remove (sequence, object):
    """Return a copy of 'sequence' with 'object' element removed.
    """
    sequence_copy = list (copy.copy (sequence))
    sequence_copy.remove (object)
    if isinstance (sequence, tuple):
        sequence_copy = tuple (sequence_copy)
    return sequence_copy


def if_ (condition, then_expression, else_expression):
    """Very limited emulation of the IF operator.
    """
    if condition:
        result = then_expression
    else:
        result = else_expression
    return result


def class_name (object):
    """Return class name of 'object's class as a string.
    The string includes full module qualification.
    If 'object' is not a class instance, return None.
    If 'object' is a class itself, return its name.
    """
    if not hasattr (object, '__class__'):
        return None
    if hasattr (object, '__mro__'):
        cls = object
    else:
        cls = object.__class__
    module_name = cls.__module__
    class_name = cls.__name__
    if module_name != '__builtin__':
        class_name = module_name + '.' + class_name
    return class_name


def is_sequence (object):
    """Return true iff 'object' is a tuple or a list.
    """
    return isinstance (object, tuple) or isinstance (object, list)


def concatenate (*sequences):
    """Return concatenation of 'sequences'.
    """
    result = []
    for s in sequences:
        result = result + list (s)
    return result


def str_ (object):
    """Same as 'charseq.str' except it applies 'str_' to sequence elements too.
    """
    if isinstance (object, list):
        result = '['
        for x in object[:1]:
            result = result + str_ (x)
        for x in object[1:]:
            result = result + ', ' + str_ (x)
        result = result + ']'
    elif isinstance (object, tuple):
        result = '('
        for x in object[:1]:
            result = result + str_ (x) + ','
        for x in object[1:]:
            result = result + ' ' + str_ (x) + ','
        result = result + ')'
    else:
        result = charseq.str (object)
    return result


class Variable (object):
    """Simple value holder.
    Useful for civilized access to non-local values in local functions.
    """
    
    def __init__ (self, value):
        self._value = value

    def get (self):
        """Return value.
        """
        return self._value

    def set (self, value):
        """Set value to 'value'.
        """
        self._value = value

    def __nonzero__ (self):
        """Return nonzero value of the stored value.
        """
        if self.get ():
            return True
        else:
            return False


undefined_argument = object ()
"""Used for default optional argument values.
It indicates no value was given to the argument.
"""


# File utilities


def directory (directory, pattern=None):
    """Return base names of all files in 'directory'.
    If 'pattern' is not None, it is a string containing regular expression and
    only the files matching the regular expression are returned.
    """
    regexp = pattern and re.compile (pattern)
    return [f for f in os.listdir (directory) if not regexp or regexp.match (f)]


def copy_file (source_file_name, target_file_name):
    """Copy file 'source_file_name' to 'target_file_name'.
    """
    in_ = open (source_file_name, 'r')
    out = open (target_file_name, 'w')
    while True:
        data = in_.read (65536)
        if not data:
            break
        out.write (data)
    out.close ()
    in_.close ()

    
def rename_file (original_file_name, new_file_name):
    """Rename file 'original_file_name' to 'new_file_name'.
    Unlike os.remove, this function works accross file systems.
    """
    try:
        os.rename (original_file_name, new_file_name)
    except OSError:
        copy_file (original_file_name, new_file_name)
        os.remove (original_file_name)


def read_stream (stream):
    """Read the whole stream and return the read data as a string.
    """
    data = ''
    while True:
        next_data = stream.read ()
        if not next_data:
            break
        data = data + next_data
    return data


# Very primitive generic function emulation


class No_Applicable_Method_Exception (Exception):
    """Raised when no applicable method is found in a generic function call.
    """
    

class defgeneric (object):
    """Generic function emulation.
    By creating an instance of this class, you define new generic function.
    
    Generic function methods can be created using the 'defmethod' method.
    
    You can invoke the generic function by calling the class instance.
    """

    def __init__ (self):
        self._methods = {}
        self._cache = {}

    def defmethod (self, function, classes):
        """Define 'function' as the method for args specified by 'classes'.
        'classes' must be a non-empty sequence of classes corresponding to the
        'function' arguments.
        """
        classes = tuple (classes)
        methods = self._methods
        for c in classes[:-1]:
            try:
                methods = methods[c]
            except KeyError:
                methods = methods[c] = {}
        methods[classes[-1]] = function
        self._cache = {}

    def __call__ (self, *args):
        """Call the generic function with 'args'.
        The first argument is considered to be most important for determining
        the corresponding method, the second argument the second most
        important, etc.
        If no applicable method is found 'No_Applicable_Method_Exception' is
        raised.
        """
        method = self._method (args)
        return method (*args)

    def _method (self, args):
        classes = tuple ([a.__class__ for a in args])
        method = self._cache.get (classes)
        if method is None:
            method = self._find_method (classes)
            self._cache[classes] = method
        return method

    def _find_method (self, classes):
        def matching_methods (cls, methods):
            for c in cls.__mro__:
                if methods.has_key (c):
                    return methods[c]
            return None
        methods = self._methods
        for c in classes:
            methods = matching_methods (c, methods)
            if methods is None:
                raise No_Applicable_Method_Exception (classes)
            elif type (methods) != type ({}):
                return methods
        raise No_Applicable_Method_Exception (classes)


# Simple data structures


class Structure (object):
    """Simple data structures.
    Attribute names of the instance are listed in the sequence '_attributes'.
    Each element of '_attributes' is a tuple of the form
    (attribute_name, documentation, default_value).  default_value may be
    omitted, in such a case the attribute value must be provided to the
    constructor call.
    """

    _attributes = ()

    def __init__ (self, **args):
        for a in self._attributes:
            name = a[0]
            if len (a) > 2:
                if args.has_key (name):
                    value = args[name]
                else:
                    value = a[2]
            else:
                value = args[name]
            setattr (self, name, value)

    def __str__ (self):
        result = '<%s:' % (self.__class__.__name__,)
        for a in self._attributes:
            name = a[0]
            result = result + (' %s=%s;' % (name, str_ (getattr (self, name)),))
        result = result + '>'
        return result


class Enumeration (object):
    """Object containing only constant attributes.
    The attribute names are specified in the constructor call.
    """

    def __init__ (self, _documentation, *constants):
        """Create new enumeration instance.
        'documentation' is the enumeration documentation.
        'constants' is a list of pairs
        (constant_name, constant_documentation,).
        """
        self._constants = constants
        for c in constants:
            name = c[0]
            setattr (self, name, name)

    def all_values (self):
        """Return sequence of all enumeration constants.
        """
        return [c[0] for c in self._constants]
