### document.py --- Representation of HTML document structure

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

import htmlentitydefs
import HTMLParser
import string
import StringIO

from charseq import str
from charseq import String as S
import css
import util


class Node (object):
    """'Document' nodes.
    """

    def __init__ (self, parent, name, attrs, input_position):
        """Construct node named 'name' with 'parent' node.
        'attrs' is a sequence of pairs (name, value,) representing node
        attributes.
        'input_position' identifies the starting position of the node in the
        input stream, it is a pair (LINE, COLUMN) where LINE and COLUMN are
        integers, or None.
        """
        self._parent = parent
        self._name = str (name)
        self._attrs = [(str (x[0]), x[1],) for x in attrs]
        self._children = []
        self._text = ''
        self._style = {}
        self._input_position = input_position

    def name (self):
        """Return node's name.
        """
        return self._name

    def text (self):
        """Return node's text, as a string.
        """
        if self.name ():
            text = ''
            for c in self.children ():
                if not c.name ():
                    text = text + c.text ()
            return text
        else:
            return self._text

    def add_text (self, text):
        """Append 'text' to the node.
        """
        if self.name ():
            text_node = Node (self, '', (), self.input_position ())
            text_node.add_text (text)
            self.append_child (text_node)
        else:
            self._text = self._text + str (text)
        
    def attr (self, name):
        """Return the value of the attribute named 'name'.
        """
        for a in self._attrs:
            if a[0] == name:
                return a[1]
        return None

    def attribute_names (self):
        """Return sequence of names of all attributes.
        """
        return [a[0] for a in self._attrs]

    def style (self):
        """Return style information associated with the node.
        Style properties of parent nodes are not included.
        Return value is a dictionary with property names as keys and their
        values as values.
        """
        return self._style

    def set_style (self, style):
        """Set style information associated with the node.
        See 'style' method for more details about the 'style' argument.
        """
        assert isinstance (style, dict), "Invalid argument type"
        self._style = style
        
    def parent (self):
        """Return node's parent.
        """
        return self._parent
    
    def children (self):
        """Return sequence of all node's children.
        """
        return self._children

    def append_child (self, child):
        """Add new 'child' node and return it.
        """
        self._children.append (child)
        return child

    def next_child (self, child):
        """Return the next node's child after 'child'.
        """
        children = self.children ()
        i = 0
        clen = len (children)
        while i < clen:
            if children[i] is child:
                break
            i = i + 1
        i = i + 1
        next_child = None
        if i < clen:
            next_child = children[i]
        return next_child

    def prev_child (self, child):
        """Return the previous node's child before 'child'.
        """
        children = self.children ()
        i = 0
        clen = len (children)
        while i < clen:
            if children[i] is child:
                break
            i = i + 1
        i = i - 1
        prev_child = None
        if i >= 0:
            prev_child = children[i]
        return prev_child

    def next_sibling (self):
        """Return the next node's sibling.
        """
        sibling = None
        if self._parent:
            sibling = self._parent.next_child (self)
        return sibling

    def prev_sibling (self):
        """Return the previous node's sibling.
        """
        sibling = None
        if self._parent:
            sibling = self._parent.prev_child (self)
        return sibling

    def next_node (self):
        """Return the next node after this node, on any level.
        If there is no such node, return None."""
        node = self.next_sibling ()
        if node:
            return node
        parent = self.parent ()
        if parent:
            return parent.next_node ()
        return None

    def input_position (self):
        """Return starting position of the node in the input stream.
        The position is either a pair (LINE, COLUMN) where LINE and COLUMN are
        integers, or None.
        """
        return self._input_position
    
    def iter_subtree (self):
        """Iterator over all node subnodes.
        """
        for child in self.children ():
            yield child
            for node in child.iter_subtree ():
                yield node

    def iter_subtree_tags (self, tags):
        """Iterator over all node subnodes specified by 'tags'.
        'tags' is a sequence of node names on which the iterator should yield.
        """
        for node in self.iter_subtree ():
            if node.name () in tags:
                yield node


class Document_Error (util.Structure):
    """Error in document structure.
    """
    _attributes = (('node', "Node in which the error occurs", None,),
                   ('description', "Description of the error",),
                   ('data', "Data related to the error", None,),
                   )


class Unknown_Stylesheet_Type_Error (Document_Error):
    """Error signalling that a stylesheet of an unknown type was encountered.
    The unknown stylesheet type is stored in 'data'.
    """


class No_Stylesheet_Type_Error (Document_Error):
    """Error signalling that a style was used without default stylesheet.
    """


class Stylesheet_Parse_Error (Document_Error):
    """Error signalling parse error in a stylesheet.
    The invalid stylesheet location is stored in 'data'.
    """


class Document (object):
    """Representation of an HTML document.
    """

    def __init__ (self, location=None):
        """'location', if given, is the originating location of the document.
        """
        self._document = Node (None, None, (), None)
        self._doctype = None
        self._location = location
        self._current_node = self._document
        self._stylesheets_assigned = False

    def location (self):
        """Return document location as 'location.Location' or None.
        """
        return self._location
    
    # Construction
        
    def add_tag (self, tag, attrs, input_position):
        """Add new node named 'tag' and start its processing.
        'attrs' and 'input_position' are the same as in 'Node.__init__'.
        """
        tag = string.lower (tag)
        attrs = [(string.lower (name), value,) for name, value in attrs]
        node = Node (self._current_node, tag, attrs, input_position)
        self._current_node.append_child (node)
        self._current_node = node

    def close_tag (self):
        """Finish processing of the current node.
        """
        self._current_node = self._current_node.parent ()
        if self._current_node is None:
            self._current_node = self._document

    def add_text (self, text):
        """Add text to the current node.
        """
        self._current_node.add_text (S (text))

    def doctype (self):
        """Return document type as a string if set, or None.
        """
        return self._doctype

    def set_doctype (self, doctype):
        """Set document type to 'doctype'.
        See 'doctype' method for more details.
        """
        self._doctype = doctype

    # Walking

    def iter_tags (self, tags):
        """Iterator over all nodes specified by 'tags'.
        'tags' is a sequence of node names on which the iterator should yield.
        """
        return self._document.iter_subtree_tags (tags)

    def for_tags (self, tags, function):
        """Call 'function' for each of the nodes specified by 'tags'.
        'tags' is a sequence of node names on which 'function' should be
        called.
        'function' is called with a 'Node' instance as its only argument.        
        """
        for node in self.iter_tags (tags):
            function (node)

    def iter_all_nodes (self):
        """Iterator over all document nodes.
        """
        return self._document.iter_subtree ()
        
    def for_all_nodes (self, function):
        """Call 'function' for all document nodes.
        'function' is called with a 'Node' instance as its only argument.
        """
        for node in self.iter_all_nodes ():
            function (node)

    # Stylesheets

    def assign_stylesheets (self):
        if self._stylesheets_assigned:
            errors = None
        else:
            errors = []
            stylesheet = util.Variable (css.Stylesheet (()))
            default_stylesheet_type = util.Variable (None)
            current_location = util.Variable (self._location)
            def add_stylesheet (s, location):
                if isinstance (s, css.Stylesheet):
                    stylesheet.set (stylesheet.get ().merge (s))
                else:
                    errors.append (Stylesheet_Parse_Error (description="Parse error in stylesheet",
                                                           data=location))
            # Find default stylesheet type
            def let (type=current_location.get ().header ('Content-Style-Type')):
                if type:
                    default_stylesheet_type.set (type)
            let ()
            if not default_stylesheet_type:
                def check_stylesheet_type (node):
                    if node.attr ('http-equiv') and node.attr ('http-equiv').lower () == 'content-style-type':
                        default_stylesheet_type.set (node.attr ('content'))
                self.for_tags (('meta',), check_stylesheet_type)
            if default_stylesheet_type:
                if default_stylesheet_type.get () != 'text/css':
                    errors.append (Unknown_Stylesheet_Type_Error (
                            description="The specified page stylesheet is of unknown type",
                            data=default_stylesheet_type.get ()))
            # Find base location of the document
            def set_base_location (node):
                import location
                if node.attr ('href'):
                    current_location.set (location.Location (node.attr ('href')))
            self.for_tags (('base',), set_base_location)
            # Load stylesheets
            def load_external_stylesheet (node):
                if node.attr ('rel') == 'stylesheet':
                    type = node.attr ('type')
                    href = node.attr ('href')
                    if type and type != 'text/css':
                        errors.append (Unknown_Stylesheet_Type_Error (node=node,
                                                                      description="Unknown stylesheet type",
                                                                      data=type))
                    elif href:
                        loc = current_location.get ().make_location (href)
                        add_stylesheet (css.parse (loc), loc)
            self.for_tags (('link',), load_external_stylesheet)
            def load_inline_stylesheet (node):
                type = node.attr ('type')
                if type and type != 'text/css':
                    errors.append (Unknown_Stylesheet_Type_Error (node=node,
                                                                  description="Unknown stylesheet type",
                                                                  data=type))
                else:
                    stream = StringIO.StringIO (node.text ())
                    def let (loc=current_location.get()):
                        add_stylesheet (css.parse_stream (stream, loc), loc)
                    let ()
            self.for_tags (('style',), load_inline_stylesheet)
            # Assign styles to nodes
            def assign_properties (node):
                properties = stylesheet.get ().node_properties (node, self)
                style = node.attr ('style')
                if style:
                    if default_stylesheet_type.get () == 'text/css':
                        stream = StringIO.StringIO (style)
                        declarations = css.parse_stream (stream, grammar=css.properties_grammar)
                        if util.is_sequence (declarations):
                            for d in declarations:
                                properties[d.name] = d.value
                        else:
                            errors.append (Stylesheet_Parse_Error (description="Parse error in stylesheet",
                                                                   data='inline'))
                    elif not default_stylesheet_type:
                        errors.append (No_Stylesheet_Type_Error
                                       (node=node, description="Style without stylesheet type defined",
                                        data=style))
                    else:
                        errors.append (Unknown_Stylesheet_Type_Error (node=node,
                                                                      description="Unknown stylesheet type",
                                                                      data=style))
                node.set_style (properties)
            self.for_all_nodes (assign_properties)
            self._stylesheets_assigned = True
        return errors
    

class Parser (HTMLParser.HTMLParser):
    """(X)HTML parser.
    """
    # This is actually not an HTML parser, because HTMLParser.HTMLParser is
    # not.  Only tags are handled in a trivial (and sometimes incorrect) way.

    # HTMLParser has bugs, the following paragraph work around them:
    CDATA_CONTENT_ELEMENTS = ()
    def unknown_decl (self, data):
        pass

    def document (self):
        """Return the parsed document as a 'Document' instance.
        """
        return self._document

    def __init__ (self, **kwargs):
        """'kwargs' is given to 'Document.__init__'.
        """
        HTMLParser.HTMLParser.__init__ (self)
        self._document = Document (**kwargs)

    def _get_real_pos (self):
        row, col = self.getpos ()
        return (row, col+1,)
    
    # Inherited methods

    def reset (self):
        HTMLParser.HTMLParser.reset (self)
        self._open_tags = []

    def handle_starttag (self, tag, attrs):
        self._document.add_tag (tag, attrs, self._get_real_pos ())
        self._open_tags.append (tag)

    def handle_endtag (self, tag):
        while True:
            self._document.close_tag ()
            if not self._open_tags:
                break
            closed_tag = self._open_tags.pop ()
            if closed_tag == tag or not self._open_tags:
                break

    def handle_data (self, data):
        self._document.add_text (data)

    def handle_charref (self, name):
        self._document.add_text (name)

    def handle_entityref (self, name):
        code = htmlentitydefs.name2codepoint.get (name)
        if not code:
            # This can be caused by another bug in HTMLParser, so let's ignore
            # it.
            return
        self._document.add_text (unichr (code))

    def handle_decl (self, declaration):
        doctype_prefix = 'doctype '
        if (declaration[:len(doctype_prefix)].lower () == doctype_prefix and
            self._document.doctype () is None):
            self._document.set_doctype (declaration)

