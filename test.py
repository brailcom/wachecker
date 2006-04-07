### test.py --- Framework for defining tests and test sets

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

import os

from charseq import str
from config import logger
import config
import copy
import document
import location
import util


# Issues


class Issue (object):
    """Represents problem in a web page.
    """

    _classification = 'ISSUE'
    
    def __init__ (self, node, description, data=None):
        """Make issue related to 'node' described by 'description'.
        'node' must be a 'document.Node' instance.
        'description' is a natural language string describing the problem.
        'data' can be arbitrary data complementing the description.
        """
        self._description = str (description)
        self._input_position = node and node.input_position ()
        self._data = util.str_ (data)

    def __str__ (self):
        pp = self.input_position ()
        position = '%d:%d' % (self.input_position () or (0, 0,))
        data = self.data ()
        if data:
            data_ = ': %s' % (data,)
        else:
            data_ = ''
        return '%s: %s -- %s%s' % (position, self._classification, self.description (), data_,)

    def description (self):
        """Return problem description as a string.
        """
        return self._description

    def data (self):
        """Return data associated with the problem or None.
        """
        return self._data

    def input_position (self):
        """Return starting position of the problem node in the source page.
        The returned value is either a pair (LINE, COLUMN) or None.  Both LINE
        and COLUMN are integers.
        """
        # Allow transition of project .xml files
        try:
            getattr (self, '_input_position')
        except AttributeError:
            self._input_position = self._node and self._node.input_position ()
        return self._input_position

    def classification (self):
        """Return issue classification, as a string.
        """
        return self._classification

class Error (Issue):
    """Issue classified as a clear error.
    """
    _classification = 'ERROR'

class Possible_Error (Issue):
    """Issue classified as a possible error.
    Human confirmation is needed.
    """
    _classification = 'ERR??'

class Possible_Issue (Issue):
    """Possible issue which may or may not actually be an error.
    Human decision is needed.
    """
    _classification = 'CHECK'


# Tests


Implementation_State = util.Enumeration ("Implementation state of a test.",
                                         ('UNIMPLEMENTED', "The test has not be implemented yet.",),
                                         ('PROTOTYPE', "The test is partially implemented.",),
                                         ('COMPLETE', "The test is completely implemented..",),
                                         )


class Test (object):
    """Base class of all tests.
    """

    _name = ''
    _description = ''
    _url = ''
    _state = Implementation_State.UNIMPLEMENTED
    _version = None
    _dependencies = ()

    def __init__ (self):
        self._version = self.__class__._version # to be XML exported
        if self._state != Implementation_State.UNIMPLEMENTED and self._version is None:
            raise Exception ('Test version not defined')

    def _run (self, _document):
        return []

    def name (cls):
        """Return test name as a string.
        """
        return cls._name or cls.__name__
    name = classmethod (name)

    def description (cls):
        """Return test description as a string.
        """
        return cls._description
    description = classmethod (description)

    def dependencies (cls):
        """Return sequence of the classes of the 'Test's this test depends on.
        """
        return cls._dependencies
    dependencies = classmethod (dependencies)

    def version (cls):
        """Return test version.
        The test version may be any object.
        Test version changes any time the test starts producing different
        results.
        """
        return cls._version
    version = classmethod (version)

    def location (cls):
        """Return 'location.Location' of a web page related to the test.
        """
        if cls._url:
            loc = location.Location (cls._url)
        else:
            loc = None
        return loc
    location = classmethod (location)
    
    def run (self, location):
        """Run the test on 'location'.
        'location' is a 'location.Location' instance.
        Return sequence of 'Issue' instances.
        """
        self._location = location
        self._base_location = location
        document = location.document ()
        for node in document.iter_tags (('base',)):
            url = node.attr ('href')
            if url:
                self._base_location = location.make_location (url)
                break
        results = []
        def block ():
            for r in self._run (document):
                results.append (r)
            if self._state == Implementation_State.UNIMPLEMENTED:
                results.append (Error (None, 'This test is not yet implemented, perform manual check'))
            elif self._state == Implementation_State.PROTOTYPE:
                results.append (Possible_Issue (None, 'This test is incomplete, perform additional manual checks'))
        logger.with_action_log ('Test: %s' % (self.name (),), block)
        for r in results:
            logger.log_line (r)
        return results


class Stylesheet_Test (Test):
    """Test using information from stylesheets.
    """

    def _run (self, document_):
        issues = super (Stylesheet_Test, self)._run (document_)
        self._style_errors = document_.assign_stylesheets () or []
        return issues

    def style_errors (self):
        """Return style errors reported by the document.
        Available only after the 'run' method is run.
        """
        return self._style_errors

    def dependencies (cls):
        return tuple (cls._dependencies) + (Test__Common_Stylesheets,)
    dependencies = classmethod (dependencies)


class Color_Test (Stylesheet_Test):
    """Test checking color information in the document.
    The test invokes the '_check_node_color' method for all document nodes,
    which have color information assigned, either in the document or in its
    stylesheet.
    """

    def _check_node_color (self, _node, _foreground, _background, _link_colors,
                           _style_foreground, _style_background, _style_background_image):
        return []

    def _run (self, document):
        issues = super (Color_Test, self)._run (document)
        def check_node (node):
            # Find colors
            style = node.style ()
            fg_color = node.attr ('color') or (node.name () == 'body' and node.attr ('text'))
            bg_color = node.attr ('bgcolor')
            link_colors = ((node.name () == 'body' and
                            [node.attr (c) for c in ('link', 'vlink', 'alink',) if node.attr (c)])
                           or [])
            style_fg_color = style.get ('color')
            style_bg_color = style.get ('bgcolor')
            style_bg_image = style.get ('background-image')
            # Call the test specific method
            if fg_color or bg_color or link_colors or style_fg_color or style_bg_color or style_bg_image:
                for i in self._check_node_color (node, fg_color, bg_color, link_colors,
                                                 style_fg_color, style_bg_color, style_bg_image):
                    issues.append (i)
        document.for_all_nodes (check_node)
        return issues


class Walking_Test (Test):
    """Test walking over all document nodes.
    For nodes names of which are present in '_sensitive_tags' the method
    '_check_node' with the given node as an argument is called.
    """

    _sensitive_tags = ()
    _known_tags = {
        'html': ('xmlns',),
        'head': ('base',),
        'title': (),
        'base': ('href', 'target',),
        'meta': ('http-equiv', 'name', 'content', 'scheme',),
        'link': ('charset', 'href', 'hreflang', 'type', 'rel', 'rev', 'media',
                 'target',),
        'style': ('type', 'media', 'xml:space',),
        'script': ('charset', 'type', 'language', 'src', 'defer', 'xml:space',),
        'noscript': (),
        'frameset': ('rows', 'cols', 'onload', 'onunload',),
        'frame': ('longdesc', 'name', 'src', 'frameborder', 'marginwidth',
                  'marginheight', 'noresize', 'scrolling',),
        'iframe': ('longdesc', 'name', 'src', 'frameborder', 'marginwidth',
                   'marginheight', 'noresize', 'scrolling', 'align', 'height',
                   'width',),
        'noframes': (),
        'body': ('onload', 'onunload', 'background', 'bgcolor', 'text',
                 'vlink', 'alink',),
        'div': ('align',),
        'p': ('align',),
        'h1': ('align',),
        'h2': ('align',),
        'h3': ('align',),
        'h4': ('align',),
        'h5': ('align',),
        'h6': ('align',),
        'ul': ('type', 'compact',),
        'ol': ('type', 'compact', 'start',),
        'menu': ('compact',),
        'dir': ('compact',),
        'li': ('type', 'value',),
        'dl': ('compact',),
        'dt': (),
        'dd': (),
        'address': (),
        'hr': ('align', 'noshade', 'size', 'width',),
        'pre': ('width', 'xml:space',),
        'blockquote': ('cite',),
        'center': (),
        'ins': ('cite', 'datetime',),
        'del': ('cite', 'datetime',),
        'a': ('charset', 'type', 'name', 'href', 'hreflang', 'rel', 'rev',
              'shaper', 'coords', 'target',
              'accesskey', 'tabindex', 'onfocus', 'onblur',),
        'span': (),
        'bdo': (),
        'br': ('clear',),
        'em': (),
        'strong': (),
        'dfn': (),
        'code': (),
        'samp': (),
        'kbd': (),
        'var': (),
        'cite': (),
        'abbr': (),
        'acronym': (),
        'q': ('cite',),
        'sub': (),
        'sup': (),
        'tt': (),
        'i': (),
        'b': (),
        'big': (),
        'small': (),
        'u': (),
        's': (),
        'strike': (),
        'basefont': ('size', 'color', 'face',),
        'font': ('size', 'color', 'face',),
        'object': ('declare', 'classid', 'codebase', 'data', 'type',
                   'codetype', 'archive', 'standby', 'height', 'width',
                   'usemap', 'name', 'tabindex', 'align', 'border', 'hspace',
                   'vspace',),
        'param': ('name', 'value', 'valuetype', 'type',),
        'applet': ('codebase', 'archive', 'code', 'object', 'alt', 'name',
                   'width', 'height', 'align', 'hspace', 'vspace',),
        'img': ('src', 'alt', 'name', 'longdesc', 'height', 'width', 'usemap',
                'ismap', 'align', 'border', 'hspace', 'vspace',),
        'map': ('class', 'style', 'name',),
        'area': ('shape', 'coords', 'href', 'nohref', 'alt', 'target',
                 'accesskey', 'tabindex', 'onfocus', 'onblur',),
        'form': ('action', 'method', 'name', 'enctype', 'onsubmit', 'onreset',
                 'accept', 'accept-charset', 'target',),
        'label': ('for', 'accesskey', 'onfocus', 'onblur',),
        'input': ('type', 'name', 'value', 'checked', 'disabled', 'readonly',
                  'size', 'maxlength', 'src', 'alt', 'usemap', 'onselect',
                  'onchange', 'accept', 'align',
                  'accesskey', 'tabindex', 'onfocus', 'onblur',),
        'select': ('name', 'size', 'multiple', 'disabled', 'tabindex',
                   'onfocus', 'onblur', 'onchange',),
        'optgroup': ('disabled', 'label',),
        'option': ('selected', 'disabled', 'label', 'value',),
        'textarea': ('name', 'rows', 'cols', 'disabled', 'readonly',
                     'onselect', 'onchange',),
        'fieldset': (),
        'legend': ('accesskey', 'align',),
        'button': ('name', 'value', 'type', 'disabled',),
        'isindex': ('prompt',),
        'table': ('summary', 'width', 'border', 'frame', 'rules',
                  'cellspacing', 'cellpadding', 'align', 'bgcolor',),
        'caption': ('align',),
        'thead': ('align', 'char', 'charoff', 'valign',),
        'tfoot': ('align', 'char', 'charoff', 'valign',),
        'tbody': ('align', 'char', 'charoff', 'valign',),
        'colgroup': ('span', 'width', 'align', 'char', 'charoff', 'valign',),
        'col': ('span', 'width', 'align', 'char', 'charoff', 'valign',),
        'tr': ('align', 'char', 'charoff', 'valign', 'bgcolor',),
        'th': ('abbr', 'axis', 'headers', 'scope', 'rowspan', 'colspan',
               'align', 'char', 'charoff', 'valign',
               'nowrap', 'bgcolor', 'width', 'height',),
        'td': ('abbr', 'axis', 'headers', 'scope', 'rowspan', 'colspan',
               'align', 'char', 'charoff', 'valign',
               'nowrap', 'bgcolor', 'width', 'height',),
        }
    
    _known_common_attributes = (
        'id', 'class', 'style', 'title',
        'lang', 'xml:lang', 'dir', 'onclick',
        'ondblclick', 'onmousedown', 'onmouseup', 'onmouseover', 'onmousemove',
        'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup',)

    def _check_node (self, _node):
        return []
    
    def _run (self, document):
        issues = super (Walking_Test, self)._run (document)
        sensitive_tags = self._sensitive_tags
        known_tags = self._known_tags
        common_attrs = self._known_common_attributes
        check_node = self._check_node
        def walker (node):
            tag = node.name ()
            if tag in sensitive_tags:
                for i in check_node (node):
                    issues.append (i)
            elif known_tags.has_key (tag):
                attrs = known_tags[tag]
                if attrs is not None:
                    for a in node.attribute_names ():
                        if a not in attrs and not a in common_attrs:
                            issues.append (Error (node, 'Internal: Unknown attribute', a))
            elif tag:
                issues.append (Error (node, 'Internal: Unknown element', node.name))
        document.for_all_nodes (walker)
        return issues


class Image_Test (Walking_Test):
    """Test checking images in the document.
    For each image in the document, '_check_image' method is called.
    """
    
    _sensitive_tags = ('img', 'object', 'applet', 'script', 'input',)

    def __init__ (self):
        super (Image_Test, self).__init__ ()
        self._sensitive_tags = super (Image_Test, self)._sensitive_tags + self._sensitive_tags
        
    def _check_image (self, _node, _is_object):
        return []

    def _check_node (self, node):
        issues = super (Image_Test, self)._check_node (node)
        tag = node.name ()
        if (tag == 'img' or
            (tag == 'input' and node.attr ('type') == 'image')):
            issues = issues + self._check_image (node, False)
        elif tag in ('object', 'applet', 'script',):
            issues = issues + self._check_image (node, True)
        return issues


class Script_Test (Walking_Test):
    """Test checking scripts in the document.
    For each script in the document, '_check_script' method is called.
    """

    _sensitive_tags = ('object', 'applet', 'script',)
    
    def __init__ (self):
        super (Script_Test, self).__init__ ()
        self._sensitive_tags = super (Script_Test, self)._sensitive_tags + self._sensitive_tags

    def _script_data_string (self, node):
        return node.attr ('classid') or node.attr ('data') or node.attr ('src')
        
    def _check_script (self, _node):
        return []

    def _check_node (self, node):
        issues = super (Script_Test, self)._check_node (node)
        tag = node.name ()
        if (tag == 'object' and node.attr ('classid') or
            tag in ('applet', 'script',)):
            issues = issues + self._check_script (node)
        return issues


class Link_Watching_Test (Walking_Test):
    """Test watching links in the document.
    Only HTTP links pointing to another document are checked.
    For each of the links, the '_check_link' method is called with the location
    of the link.
    """

    _sensitive_tags = ('a', 'link', 'area',)
    
    def __init__ (self):
        super (Link_Watching_Test, self).__init__ ()
        self._sensitive_tags = super (Link_Watching_Test, self)._sensitive_tags + self._sensitive_tags

    def _check_link (self, _node, _location):
        """Return issues related to '_node' at '_location'.
        """
        return []
        
    def _check_node (self, node):
        issues = super (Link_Watching_Test, self)._check_node (node)
        if node.name () in ('a', 'link', 'area',):
            href = node.attr ('href')
            if href:
                url = self._base_location.make_location (href, mime_type=node.attr ('type'))
                if url.protocol () == 'http' and href[0] != '#':
                    issues = issues + self._check_link (node, url)
        return issues

    def run (self, location):
        self._last_url_retrieval_time = 0
        return super (Link_Watching_Test, self).run (location)        


# Test sets


class Test_Set (object):
    """Collection of tests.
    """
    
    _name = ''
    _description = ''
    _tests = ()

    def name (cls):
        """Return test set name.
        """
        return cls._name
    name = classmethod (name)

    def description (cls):
        """Return test set description.
        """
        return cls._description
    description = classmethod (description)

    def tests (cls):
        """Return sequence of the test set test classes.
        """
        tests = [Test__Common_Syntax] + list (cls._tests)
        i = 0
        while i < len (tests):
            for t in tests[i].dependencies ():
                if t not in tests:
                    tests.append (t)
            i = i + 1
        return tests
    tests = classmethod (tests)
   

def load_tests (directories=config.test_directories):
    """Load all tests from 'directories'.
    """
    for d in directories:
        test_files = util.directory (d, '[a-z].*\.py$')
        set_files = util.directory (d, '[A-Z].*\.py$')
        for f in util.sort (test_files) + util.sort (set_files):
            execfile (os.path.join (d, f), globals ())

def _all_classes (prefix):
    g = copy.copy (globals ())
    class_names = [name for name in g if name.find (prefix) == 0]
    return [(name, g[name],) for name in util.sort (class_names)]
    
def all_tests ():
    """Return sequence of all currently loaded test names and classes.
    Each element of the resulting sequence is of the form (NAME, CLASS,).
    """
    return _all_classes ('Test__')

def all_test_sets ():
    """Return sequence of all currently loaded test set names and classes.
    Each element of the resulting sequence is of the form (NAME, CLASS,).
    """
    return _all_classes ('Test_Set__')

def all_test_set_names ():
    """Return sequence of class names of all currently loaded test sets.
    """
    return ['test.' + name_class[0] for name_class in all_test_sets ()]
