# -*- coding: utf-8 -*-
### standard.py --- Tests of public standards

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
import re
import string
import time
import urllib2

from config import logger
import document


class Test__WCAG_1__1_1 (Link_Watching_Test):
    # Provide a text equivalent for every non-text element
    
    _name = 'WCAG 1.0 checkpoint  1.1, Section 508 (a)'
    _description = "Provide a text equivalent for every non-text element (e.g., via `alt', `longdesc', or in element content)."
    _url = 'http://www.w3.org/TR/WCAG10/#tech-text-equivalent'
    _state = Implementation_State.COMPLETE
    _version = 1

    _sensitive_tags = (Link_Watching_Test._sensitive_tags +
                       ('object', 'applet', 'script', 'a', 'link',
                        'area', 'img', 'input',
                        'base',))

    _ok_mime_types = ('application', 'text',)
    _ko_mime_types = ('audio', 'image', 'video',)

    def _check_link (self, node, location):
        issues = []
        url = location.url ()
        mime_type = location.mime_type ()
        if mime_type:
            major = mime_type[0]
            if major in self._ok_mime_types or mime_type in self._ok_mime_types:
                pass
            elif major in self._ko_mime_types or mime_type in self._ko_mime_types:
                issues.append (Possible_Issue (node, 'Text alternative to a non-text link missing', url))
            else:
                issues.append (Possible_Issue (node, 'Unknown link type -- text alternative may be needed', url))
        else:
            issues.append (Possible_Issue (node, 'Link may need a text alternative', url))
        return issues

    def _check_alt (self, node):
        issues = []
        alt = node.attr ('alt')
        longdesc = node.attr ('longdesc')
        if longdesc:
            issues.append (Possible_Issue (node, 'Check text alternatives to an image', (alt, longdesc,)))
        elif alt:
            issues.append (Possible_Issue (node, 'Check text alternative of a non-text element', alt))
        else:
            issues.append (Error (node, 'ALT text missing in a non-text element'))
        return issues

    def _check_object (self, node):
        issues = []
        if node.data or node.children:
            issues.append (Possible_Issue (node, 'Check text alternatives to an OBJECT',
                                           (node.data, node.children)))
        else:
            issues.append (Error (node, 'No text alternative to an OBJECT'))
        return issues

    def _check_script (self, node):
        issues = []
        sibling = node.next_sibling ()
        if sibling and sibling.name == 'noscript':
            issues.append (Possible_Issue (node, 'Check NONSCRIPT contents', sibling))
        else:
            issues.append (Error (node, 'No NONSCRIPT for a SCRIPT'))
        return issues

    def _check_node (self, node):
        issues = super (Test__WCAG_1__1_1, self)._check_node (node)
        tag = node.name ()
        if tag == 'object':
            issues = self._check_object (node)
        elif tag in ('a', 'link',):
            if not node.attr ('href') and not node.attr ('name'):
                issues.append (Possible_Error (node, 'Link without source'))
        elif tag in ('img', 'applet', 'area',):
            issues = self._check_alt (node)
        elif tag == 'input':
            if node.attr ('type') == 'image':
                issues = self._check_alt (node)                
        elif tag == 'script':
            issues = self._check_script (node)
        return issues

class Test__WCAG_1__1_2 (Walking_Test):
    # Provide redundant text links for each active region of a server-side image map
    
    _name = 'WCAG 1.0 checkpoint  1.2, Section 508 (e)'
    _description = "Provide redundant text links for each active region of a server-side image map."
    _url = 'http://www.w3.org/TR/WCAG10/#tech-redundant-server-links'
    _state = Implementation_State.COMPLETE
    _version = 0

    _sensitive_tags = ('img', 'input',)

    def _check_node (self, node):
        issues = []
        tag = node.name ()
        if ((tag == 'img' and node.attr ('ismap')) or
            (tag == 'input' and node.attr ('type') == 'image')):
            issues.append (Possible_Issue (node, 'Check presence of alternative links to all image map regions'))
        return issues

class Test__WCAG_1__1_3 (Link_Watching_Test):
    
    _name = 'WCAG 1.0 checkpoint  1.3'
    _description = "Until user agents can automatically read aloud the text equivalent of a visual track, provide an auditory description of the important information of the visual track of a multimedia presentation."
    _url = 'http://www.w3.org/TR/WCAG10/#tech-auditory-descriptions'
    _state = Implementation_State.COMPLETE
    _version = 0

    _sensitive_tags = (Link_Watching_Test._sensitive_tags +
                       ('object', 'applet', 'script',))
    
    _ok_mime_types = ('application', 'text', 'audio', 'image',)
    _ko_mime_types = ('video',)

    def _check_link (self, node, location):
        issues = []
        url = location.url ()
        mime_type = location.mime_type ()
        if mime_type:
            major = mime_type[0]
            if major in self._ok_mime_types or mime_type in self._ok_mime_types:
                pass
            elif major in self._ko_mime_types or mime_type in self._ko_mime_types:
                issues.append (Possible_Issue (node, 'Multimedia presentation -- check for audio description of the important information in it', url))
            else:
                issues.append (Possible_Issue (node, 'Unknown link type -- if it is a multimedia presentation, check for important information in it', url))
        else:
            issues.append (Possible_Issue (node, 'Unknown link type -- if it is a multimedia presentation, check for important information in it', url))
        return issues

    def _check_node (self, node):
        issues = super (Test__WCAG_1__1_3, self)._check_node (node)
        tag = node.name ()
        if tag in ('object', 'applet', 'script',):
            issues.append (Possible_Issue (node, 'If the object is a multimedia presentation, check for audio description of the important information in it'))
        return issues        

class Test__WCAG_1__1_4 (Walking_Test):

    _name = 'WCAG 1.0 checkpoint  1.4, Section 508 (b)'
    _description = "For any time-based multimedia presentation (e.g., a movie or animation), synchronize equivalent alternatives (e.g., captions or auditory descriptions of the visual track) with the presentation."
    _url = 'http://www.w3.org/TR/WCAG10/#tech-synchronize-equivalents'
    _state = Implementation_State.COMPLETE
    _version = 0

    _sensitive_tags = ('object', 'applet', 'script',)
    
    _ok_mime_types = ('application', 'text', 'audio', 'image',)
    _ko_mime_types = ('video',)

    def _check_node (self, node):
        issues = super (Test__WCAG_1__1_4, self)._check_node (node)
        issues.append (Possible_Issue (node, 'If the object is a time-based multimedia presentation, check the provided equivalent alternatives (text, sound, ...) are synchronized'))
        return issues

class Test__WCAG_1__1_5 (Walking_Test):

    _name = 'WCAG 1.0 checkpoint  1.5'
    _description = "Until user agents render text equivalents for client-side image map links, provide redundant text links for each active region of a client-side image map."
    _url = 'http://www.w3.org/TR/WCAG10/#tech-redundant-client-links'
    _state = Implementation_State.COMPLETE
    _version = 0

    _sensitive_tags = ('area',)

    def _check_node (self, node):
        issues = super (Test__WCAG_1__1_5, self)._check_node (node)
        issues.append (Possible_Issue (node, 'Check presence of a redundant text link to a client-side image map link',
                                       (node.attr ('href'), node.attr ('alt'),)))
        return issues

class Test__WCAG_1__2_1 (Color_Test):

    _name = 'WCAG 1.0 checkpoint  2.1, Section 508 (c)'
    _description = "Ensure that all information conveyed with color is also available without color, for example from context or markup."
    _url = 'http://www.w3.org/TR/WCAG10/#tech-color-convey'
    _state = Implementation_State.COMPLETE
    _version = 0

    _dependencies = (Test__Common_Colors,)

    def _check_node_color (self, node, foreground, background, link_colors,
                           style_foreground, style_background, style_background_image):
        issues = super (Test__WCAG_1__2_1, self)._check_node_color (
            node, foreground, background, link_colors,
            style_foreground, style_background, style_background_image)
        if node.name () != 'body':
            colors = [c for c in foreground, background, style_foreground, style_background, style_background_image
                      if c]
            issues.append (Possible_Issue (
                    node, "Colors used in document, check they are not the only source of given information",
                    colors))
        return issues    

class Test__WCAG_1__2_2_Images (Image_Test):

    _name = 'WCAG 1.0 checkpoint  2.2 for images'
    _description = "Ensure that foreground and background color combinations provide sufficient contrast when viewed by someone having color deficits or when viewed on a black and white screen."
    _url = 'http://www.w3.org/TR/WCAG10/#tech-color-contrast'
    _state = Implementation_State.COMPLETE
    _version = 2

    def _check_image (self, node, is_object):
        issues = []
        if is_object:
            issues.append (Possible_Issue (node, 'If the object contains image, check it for sufficient contrast'))
            issues.append (Possible_Issue (node, 'If the object contains image, check its greyscale version'))
        else:
            issues.append (Possible_Issue (node, 'Check sufficient contrast of the image'))
            issues.append (Possible_Issue (node, 'Check greyscale version of the image'))
        return issues

class Test__WCAG_1__2_2_Text (Color_Test):

    _name = 'WCAG 1.0 checkpoint  2.2 for text'
    _description = "Ensure that foreground and background color combinations provide sufficient contrast when viewed by someone having color deficits or when viewed on a black and white screen."
    _url = 'http://www.w3.org/TR/WCAG10/#tech-color-contrast'
    _state = Implementation_State.COMPLETE
    _version = 1
    
    _dependencies = (Test__Common_Colors,)

    def _check_node_color (self, node, foreground, background, link_colors,
                           style_foreground, style_background, style_background_image):
        issues = super (Test__WCAG_1__2_2_Text, self)._check_node_color (
            node, foreground, background, link_colors,
            style_foreground, style_background, style_background_image)
        any_foreground = foreground or style_foreground
        any_background = background or style_background or style_background_image
        if any_foreground and not any_background:
            issues.append (Possible_Error (node, "Only foreground color given", any_foreground))
        if any_background and not any_foreground:
            issues.append (Possible_Error (node, "Only background color given", any_background))
        if any_foreground or any_background:
            colors = [c for c in foreground, background, style_foreground, style_background, style_background_image
                      if c]
            issues.append (Possible_Issue (node, "Colors specified -- check contrast, incl. greyscale version",
                                           colors))
        if link_colors:
            issues.append (Possible_Issue (node,
                                           "Link colors specified -- check contrast, incl. greyscale version",
                                           link_colors))
        return issues

class Test__WCAG_1__3_1 (Image_Test):
    
    _name = 'WCAG 1.0 checkpoint  3.1'
    _description = "When an appropriate markup language exists, use markup rather than images to convey information."
    _url = 'http://www.w3.org/TR/WCAG10/#tech-use-markup'
    _state = Implementation_State.COMPLETE
    _version = 0

    def _check_image (self, node, is_object):
        return [Possible_Issue (node, "Check the object doesn't represent text")]

class Test__WCAG_1__3_2 (Test):
    
    _name = 'WCAG 1.0 checkpoint  3.2'
    _description = "Create documents that validate to published formal grammars."
    _url = 'http://www.w3.org/TR/WCAG10/#tech-identify-grammar'
    _state = Implementation_State.COMPLETE
    _version = 1

    def _run (self, document):
        issues = []
        doctype = document.doctype ()
        if doctype is None:
            issues.append (Error (None, "No DOCTYPE given"))
        else:
            match = re.match ('^DOCTYPE[ \n]+(html|HTML)[ \n]+PUBLIC[ \n]+[\'"]([^\'"\n]+)[\'"].*', doctype)
            if (not match or
                match.group (2) not in ('-//W3C//DTD HTML 3.2 Final//EN',
                                        '-//W3C//DTD HTML 4.01//EN',
                                        '-//W3C//DTD HTML 4.01 Transitional//EN',
                                        '-//W3C//DTD HTML 4.01 Frameset//EN',
                                        '-//W3C//DTD XHTML 1.0 Strict//EN',
                                        '-//W3C//DTD XHTML 1.0 Transitional//EN',
                                        '-//W3C//DTD XHTML 1.0 Frameset//EN',
                                        )):
                issues.append (Possible_Error (None, "Unknown DOCTYPE", doctype))
        return issues

class Test__WCAG_1__3_3 (Walking_Test, Color_Test):
    
    _name = 'WCAG 1.0 checkpoint  3.3'
    _description = "Use style sheets to control layout and presentation."
    _url = 'http://www.w3.org/TR/WCAG10/#tech-style-sheets'
    _state = Implementation_State.COMPLETE
    _version = 3

    _sensitive_tags = ('tt', 'i', 'b', 'u', 'strike', 'big', 'small', 'basefont', 'font', 'pre',)

    def _check_node (self, node):
        tag = node.name ()
        if tag == 'pre':
            issue = Possible_Issue (node, "Check PRE element is used properly")
        else:
            issue = Error (
                node, "HTML elements used instead of stylesheets and structural markup for changing fonts",
                node.name ())
        return [issue]

    def _check_node_color (self, node, foreground, background, link_colors,
                           style_foreground, style_background, style_background_image):
        if foreground or background or link_colors:
            issues = [Error (node, "HTML elements used instead of stylesheets for changing colors")]
        else:
            issues = []
        return issues

class Test__WCAG_1__3_4 (Stylesheet_Test):
    
    _name = 'WCAG 1.0 checkpoint  3.4'
    _description = "Use relative rather than absolute units in markup language attribute values and style sheet property values."
    _url = 'http://www.w3.org/TR/WCAG10/#tech-relative-units'
    _state = Implementation_State.COMPLETE
    _version = 0

    def _run (self, document):
        issues = super (Test__WCAG_1__3_4, self)._run (document)
        regex_number = re.compile ('^[0-9]')
        regex_ok = re.compile ('^[0-9]+[0-9.]*(em|%)$|0')
        def check (node):
            def check_value (value):
                if isinstance (value, list):
                    for v in value[1:]:
                        if check_value (v):
                            return True
                    else:
                        return False
                elif regex_number.match (value) and not regex_ok.match (value):
                    issues.append (Possible_Error (node, "Absolute units used", (property, complete_value,)))
                    return True
            for k, v in node.style ().items ():
                property = k
                complete_value = v
                check_value (v)
        document.for_all_nodes (check)
        return issues

class Test__WCAG_1__3_5 (Test):
    
    _name = 'WCAG 1.0 checkpoint  3.5'
    _description = "Use header elements to convey document structure and use them according to specification."
    _url = 'http://www.w3.org/TR/WCAG10/#tech-logical-headings'
    _state = Implementation_State.COMPLETE
    _version = 0

    def _run (self, document):
        issues = []
        headings = []
        last_level = util.Variable (0)
        def check_for_heading (node):
            tag = node.name ()
            if tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6',):
                level = int (tag[1])
                if level > last_level.get () + 1:
                    issues.append (Error (node, "Heading level skipped",
                                          'h%d--%s' % (last_level.get (), tag,)))
                last_level.set (level)
                headings.append ('%s: %s' % (tag, node.text (),))
        document.for_all_nodes (check_for_heading)
        if headings:
            issues.append (Possible_Issue (
                    None, "Check headings represent document structure, not font or other information", headings))
        return issues

class Test__WCAG_1__3_6 (Walking_Test):
    
    _name = 'WCAG 1.0 checkpoint  3.6'
    _description = "Mark up lists and list items properly."
    _url = 'http://www.w3.org/TR/WCAG10/#tech-list-structure'
    _state = Implementation_State.COMPLETE
    _version = 0

    _sensitive_tags = ('ul', 'ol', 'dl',)
    
    def _check_node (self, node):
        issues = []
        tag = node.name ()
        issues.append (Possible_Issue (node, "Check boundaries of a list are marked clearly"))
        if tag == 'ul':
            issues.append (Possible_Issue (node, "Check items of an unordered list are marked clearly"))
        elif tag == 'ol':
            def block ():
                while True:
                    parent = node.parent ()
                    if parent is None:
                        return False
                    elif parent.name () == 'ol':
                        return True
            if block ():
                issues.append (Possible_Issue (node, "Check a nested ordered list uses "))
        return issues

class Test__WCAG_1__3_7 (Walking_Test):
    
    _name = 'WCAG 1.0 checkpoint  3.7'
    _description = "Mark up quotations. Do not use quotation markup for formatting effects such as indentation."
    _url = 'http://www.w3.org/TR/WCAG10/#tech-quotes'
    _state = Implementation_State.COMPLETE
    _version = 0

    _sensitive_tags = ('q', 'blockquote',)

    def _check_node (self, node):
        issues = [Possible_Issue (
                node, "Quotation present, check it really contains quoation and is not used for formatting instead",
                node.text ())]
        return issues

class Test__WCAG_1__4_1 (Test):
    
    _name = 'WCAG 1.0 checkpoint  4.1'
    _description = "Clearly identify changes in the natural language of a document\'s text and any text equivalents (e.g., captions)."
    _url = 'http://www.w3.org/TR/WCAG10/#tech-identify-changes'
    _state = Implementation_State.COMPLETE
    _version = 0

    def _run (self, _document):
        return [Possible_Issue (None, "Check all language changes, including text equivalents, are marked with the LANG attribute")]

class Test__WCAG_1__4_2 (Test):
    
    _name = 'WCAG 1.0 checkpoint  4.2'
    _description = "Specify the expansion of each abbreviation or acronym in a document where it first occurs."
    _url = 'http://www.w3.org/TR/WCAG10/#tech-expand-abbr'
    _state = Implementation_State.COMPLETE
    _version = 0

    def _run (self, document):
        issues = super (Test__WCAG_1__4_2, self)._run (document)
        abbrevs = []
        text_seen = util.Variable (False)
        def check (node):
            tag = node.name ()
            if tag in ('abbr', 'acronym',):
                text = node.text ()
                if text not in abbrevs:
                    abbrevs.append (text)
            elif tag == 'pre':
                pass
            elif node.text ():
                text_seen.set (True)
        document.for_all_nodes (check)
        if text_seen:
            issues.append (Possible_Issue (None, "Check expansions are defined for all abbreviations and acronyms within the text", 'Defined abbreviations/acronyms: %s' % (abbrevs,)))
            regex_acronym = re.compile ('\w\w+', re.UNICODE)
            regex_abbrev = re.compile ('(\w+)\. (\w)', re.UNICODE)
            regex_other = re.compile ('.*[0-9_]')
            def check_text (node):
                text = node.text ()
                if text:
                    for match in regex_acronym.finditer(text):
                        word = match.group (0)
                        if not regex_other.match (word) and word == word.upper () and word not in abbrevs:
                            issues.append (Possible_Error (node, "Acronym without expansion?", word))
                    for match in regex_abbrev.finditer(text):
                        word = match.group (1)
                        next_char = match.group (2)
                        if not regex_other.match (word) and next_char == next_char.lower () and word not in abbrevs:
                            issues.append (Possible_Error (node, "Abbreviation without expansion?", word))
            document.for_all_nodes (check_text)
        return issues

class Test__WCAG_1__4_3 (Test):
    
    _name = 'WCAG 1.0 checkpoint  4.3'
    _description = "Identify the primary natural language of a document."
    _url = 'http://www.w3.org/TR/WCAG10/#tech-identify-lang'
    _state = Implementation_State.COMPLETE
    _version = 0

    def _run (self, document):
        issues = []
        lang_defined = False
        for node in document.iter_tags (('html',)):
            if node.attr ('lang') or node.attr ('xml:lang'):
                lang_defined = True
                break
        if not lang_defined:
            for node in document.iter_tags (('meta',)):
                if (node.attr ('http-equiv') and
                    node.attr ('http-equiv').lower () == 'content-language' and
                    node.attr ('content')):
                    lang_defined = True
                    break
        if not lang_defined:
            if self._location.header ('Content-Language'):
                lang_defined = True
        if not lang_defined:
            issues.append (Error (None, "No primary natural language of the document defined"))
        return issues

class Test__WCAG_1__5_1 (Walking_Test):
    
    _name = 'WCAG 1.0 checkpoint  5.1, Section 508 (g)'
    _description = "For data tables, identify row and column headers."
    _url = 'http://www.w3.org/TR/WCAG10/#tech-table-headers'
    _state = Implementation_State.COMPLETE
    _version = 0

    _sensitive_tags = ('table',)
    
    def _check_node (self, node):
        issues = []
        ths = []
        def find_ths (n):
            for c in n.children ():
                tag = c.name ()
                if tag == 'th':
                    text = n.text ()
                    if text:
                        ths.append (text)
                elif tag in ('thead', 'tfoot', 'tbody', 'tr',):
                    find_ths (c)
        find_ths (node)
        if ths:
            issues.append (Possible_Issue (node, "Check all table columns and rows are sufficiently identified in headers", ths))
        else:
            issues.append (Error (node, "Table columns and rows not identified"))
        return issues

class Test__WCAG_1__5_2 (Walking_Test):
    
    _name = 'WCAG 1.0 checkpoint  5.2, Section 508 (h)'
    _description = "For data tables that have two or more logical levels of row or column headers, use markup to associate data cells and header cells."
    _url = 'http://www.w3.org/TR/WCAG10/#tech-table-structure'
    _state = Implementation_State.COMPLETE
    _version = 0
    
    _sensitive_tags = ('table',)

    def _check_node (self, node):
        issues = []
        def find_structure_information (n):
            for c in n.children ():
                tag = c.name ()
                if tag == 'th':
                    if c.attr ('scope'):
                        return True
                elif tag == 'td':
                    if c.attr ('headers'):
                        return True
                elif tag in ('thead', 'tfoot', 'tbody', 'tr',):
                    if find_structure_information (c):
                        return True
            return False
        if find_structure_information (node):
            issues.append (Possible_Issue (node, "Check the table provides information about its structure and cell relationships"))
        else:
            issues.append (Possible_Error (node, "No structure information found in the table"))
        return issues

class Test__WCAG_1__5_3 (Walking_Test):
    
    _name = 'WCAG 1.0 checkpoint  5.3'
    _description = "Do not use tables for layout unless the table makes sense when linearized. Otherwise, if the table does not make sense, provide an alternative equivalent (which may be a linearized version)."
    _url = 'http://www.w3.org/TR/WCAG10/#tech-table-for-layout'
    _state = Implementation_State.COMPLETE
    _version = 0

    _sensitive_tags = ('table',)

    def _check_node (self, node):
        return [Possible_Issue (node, "Table -- check it is not used to control layout inappropriately")]

class Test__WCAG_1__5_4 (Walking_Test):
    
    _name = 'WCAG 1.0 checkpoint  5.4'
    _description = "If a table is used for layout, do not use any structural markup for the purpose of visual formatting."
    _url = 'http://www.w3.org/TR/WCAG10/#tech-table-layout'
    _state = Implementation_State.COMPLETE
    _version = 0

    _sensitive_tags = ('table',)

    def _check_node (self, node):
        issues = []
        def find_th (n):
            children = n.children ()
            for c in children:
                tag = c.name ()
                if tag == 'th':
                    return True
                elif tag in ('thead', 'tfoot', 'tbody', 'tr',):
                    if find_th (c):
                        return True
            return False
        if find_th (node):
            issues.append (Possible_Issue (node, "If the table is used to control layout, check table elements are not used for visual formatting"))
        return issues

class Test__WCAG_1__5_5 (Walking_Test):
    
    _name = 'WCAG 1.0 checkpoint  5.5'
    _description = "Provide summaries for tables."
    _url = 'http://www.w3.org/TR/WCAG10/#tech-table-summaries'
    _state = Implementation_State.COMPLETE
    _version = 0

    _sensitive_tags = ('table',)
    
    def _check_node (self, node):
        issues = []
        children = node.children ()
        if not children or children[0].name () != 'caption':
            if node.attr ('title'):
                issues.append (Possible_Error (node, "No CAPTION in a table"))
            else:
                issues.append (Error (node, "No CAPTION nor TITLE in a table"))
        if not node.attr ('summary'):
            issues.append (Error (node, "No SUMMARY attribute in a table"))
        return issues

class Test__WCAG_1__5_6 (Walking_Test):
    
    _name = 'WCAG 1.0 checkpoint  5.6'
    _description = "Provide abbreviations for header labels."
    _url = 'http://www.w3.org/TR/WCAG10/#tech-abbreviate-labels'
    _state = Implementation_State.COMPLETE
    _version = 0

    _sensitive_tags = ('th',)
    
    def _check_node (self, node):
        issues = []
        if not node.attr ('abbr'):
            issues.append (Possible_Error (node, "No ABBR attribute in a table header", node.text ()))
        return issues

class Test__WCAG_1__6_1 (Stylesheet_Test):
    
    _name = 'WCAG 1.0 checkpoint  6.1, Section 508 (d)'
    _description = "Organize documents so they may be read without style sheets."
    _url = 'http://www.w3.org/TR/WCAG10/#tech-order-style-sheets'
    _state = Implementation_State.COMPLETE
    _version = 0

    def _run (self, document):
        issues = super (Test__WCAG_1__6_1, self)._run (document)
        for node in document.iter_all_nodes ():
            if node.style ():
                issues.append (Possible_Issue (None, "Check the document is readable without stylesheets"))
                break
        return issues

class Test__WCAG_1__6_2 (Walking_Test):
    
    _name = 'WCAG 1.0 checkpoint  6.2'
    _description = "Ensure that equivalents for dynamic content are updated when the dynamic content changes."
    _url = 'http://www.w3.org/TR/WCAG10/#tech-dynamic-source'
    _state = Implementation_State.COMPLETE
    _version = 0

    _sensitive_tags = ('object', 'applet', 'script', 'frame', 'img',)

    def _check_node (self, node):
        issues = []
        tag = node.name ()
        if tag == 'frame':
            src = node.attr ('src')
            if src:
                frame_location = self._location.make_location (src)
                mime_type = frame_location.mime_type ()
                if (mime_type[0] != 'text' or
                    mime_type[1] not in ('html', 'plain',)):
                    issues.append (Possible_Error (node, "Frame source apparently not an HTML file", src))
        else:
            issues.append (Possible_Issue (node, "If the object is dynamic, check its equivalents are updated appropriately on changes", (tag, node.attr ('classid') or node.attr ('data') or node.attr ('src'))))
        return issues
    
class Test__WCAG_1__6_3 (Script_Test):
    
    _name = 'WCAG 1.0 checkpoint  6.3'
    _description = "Ensure that pages are usable when scripts, applets, or other programmatic objects are turned off or not supported. If this is not possible, provide equivalent information on an alternative accessible page."
    _url = 'http://www.w3.org/TR/WCAG10/#tech-scripts'
    _state = Implementation_State.COMPLETE
    _version = 0

    def _check_script (self, node):
        self._scripts.append (node)
        return []

    def _run (self, document):
        self._scripts = []
        issues = super (Test__WCAG_1__6_3, self)._run (document)
        if self._scripts:
            data = [node.attr ('classid') or node.attr ('src') or node.attr ('code') or node.attr ('object') or '?'
                    for node in self._scripts]
            issues.append (Possible_Issue (None, "Check page is usable when scripts, applets, etc. are turned off",
                                           data))
        return issues

class Test__WCAG_1__6_4 (Test):
    
    _name = 'WCAG 1.0 checkpoint  6.4'
    _description = "For scripts and applets, ensure that event handlers are input device-independent."
    _url = 'http://www.w3.org/TR/WCAG10/#tech-keyboard-operable-scripts'
    _state = Implementation_State.COMPLETE
    _version = 0

    def _run (self, document):
        issues = []
        for node in document.iter_all_nodes ():
            tag = node.name ()
            if (tag in ('applet', 'script') or
                tag == 'object' and node.attr ('classid')):
                issues.append (Possible_Issue (node, "Check the script event handlers are device independent",
                                               (tag, node.attr ('classid') or node.attr ('src') or
                                                node.attr ('code') or node.attr ('object') or '?')))
            else:
                regex = re.compile ('^on(mouse|key)')
                for a in node.attribute_names ():
                    if regex.match (a):
                        issues.append (Possible_Error (node, "Device dependent script", (tag, a, node.attr (a))))
        return issues

class Test__WCAG_1__6_5 (Walking_Test):
    
    _name = 'WCAG 1.0 checkpoint  6.5'
    _description = "Ensure that dynamic content is accessible or provide an alternative presentation or page."
    _url = 'http://www.w3.org/TR/WCAG10/#tech-fallback-page'
    _state = Implementation_State.COMPLETE
    _version = 0
    
    _sensitive_tags = ('object', 'applet', 'script', 'frameset',)

    def _check_node (self, node):
        issues = []
        tag = node.name ()
        if tag == 'frameset':
            if 'noframes' in [c.name () for c in node.children ()]:
                issues.append (Possible_Issue (node, "Check nonframe version of the frame"))
            else:
                issues.append (Error (node, "Frameset without NOFRAMES"))
        elif (tag in ('applet', 'script') or
              tag == 'object' and node.attr ('classid')):
            if 'noscript' in [c.name () for c in node.children ()]:
                issues.append (Possible_Issue (node, "Check noscript version of the script"))
            else:
                issues.append (Error (node, "Script without NOSCRIPT"))
        return issues

class Test__WCAG_1__7_1 (Walking_Test):
    
    _name = 'WCAG 1.0 checkpoint  7.1, Section 508 (j)'
    _description = "Until user agents allow users to control flickering, avoid causing the screen to flicker."
    _url = 'http://www.w3.org/TR/WCAG10/#tech-avoid-flicker'
    _state = Implementation_State.COMPLETE
    _version = 0
    
    _sensitive_tags = ('object', 'applet', 'script', 'img',)

    def _check_node (self, node):
        return [Possible_Issue (node, "Check the object doesn't flicker")]

class Test__WCAG_1__7_2 (Walking_Test):
    
    _name = 'WCAG 1.0 checkpoint  7.2'
    _description = "Until user agents allow users to control blinking, avoid causing content to blink (i.e., change presentation at a regular rate, such as turning on and off)."
    _url = 'http://www.w3.org/TR/WCAG10/#tech-avoid-blinking'
    _state = Implementation_State.COMPLETE
    _version = 0
    
    _sensitive_tags = ('object', 'applet', 'script', 'img',)

    def _check_node (self, node):
        return [Possible_Issue (node, "Check the object doesn't blink")]

class Test__WCAG_1__7_3 (Walking_Test):
    
    _name = 'WCAG 1.0 checkpoint  7.3'
    _description = "Until user agents allow users to freeze moving content, avoid movement in pages."
    _url = 'http://www.w3.org/TR/WCAG10/#tech-avoid-movement'
    _state = Implementation_State.COMPLETE
    _version = 0
    
    _sensitive_tags = ('object', 'applet', 'script', 'img',)

    def _check_node (self, node):
        return [Possible_Issue (node, "Check the object contents doesn't move")]

class Test__WCAG_1__7_4 (Walking_Test):
    
    _name = 'WCAG 1.0 checkpoint  7.4'
    _description = "Until user agents provide the ability to stop the refresh, do not create periodically auto-refreshing pages."
    _url = 'http://www.w3.org/TR/WCAG10/#tech-no-periodic-refresh'
    _state = Implementation_State.COMPLETE
    _version = 0
    
    _sensitive_tags = ('meta',)

    def _check_node (self, node):
        issues = []
        if (node.attr ('http-equiv') and
            node.attr ('http-equiv').lower () == 'refresh' and
            node.attr ('content') and
            node.attr ('content').lower ().find ('url=') == -1):
            issues.append (Error (node, "Refresh in the page"))
        return issues

class Test__WCAG_1__7_5 (Walking_Test):
    
    _name = 'WCAG 1.0 checkpoint  7.5'
    _description = "Until user agents provide the ability to stop auto-redirect, do not use markup to redirect pages automatically. Instead, configure the server to perform redirects."
    _url = 'http://www.w3.org/TR/WCAG10/#tech-no-auto-forward'
    _state = Implementation_State.COMPLETE
    _version = 0
    
    _sensitive_tags = ('meta',)

    def _check_node (self, node):
        issues = []
        if (node.attr ('http-equiv') and
            node.attr ('http-equiv').lower () == 'refresh' and
            node.attr ('content') and
            node.attr ('content').lower ().find ('url=') != -1):
            issues.append (Error (node, "Redirect in the page"))
        return issues

class Test__WCAG_1__8_1_Important (Script_Test):
    
    _name = 'WCAG 1.0 checkpoint  8.1 for important functionality'
    _description = "Make programmatic elements such as scripts and applets directly accessible or compatible with assistive technologies."
    _url = 'http://www.w3.org/TR/WCAG10/#tech-directly-accessible'
    _state = Implementation_State.COMPLETE
    _version = 0
    
    _ISSUE_MESSAGE = "If the object's functionality is important and not presented elsewhere, check the script/applet is accessible"
    
    def _check_script (self, node):
        return [Possible_Issue (node, self._ISSUE_MESSAGE)]

class Test__WCAG_1__8_1 (Test__WCAG_1__8_1_Important):
    
    _name = 'WCAG 1.0 checkpoint  8.1 for all functionality'
    _description = "Make programmatic elements such as scripts and applets directly accessible or compatible with assistive technologies."
    _url = 'http://www.w3.org/TR/WCAG10/#tech-directly-accessible'
    _state = Implementation_State.COMPLETE
    _version = 0

    _ISSUE_MESSAGE = "Check the script/applet is accessible"

# Backward compatibility alias
Test__WCAG_1__8_1_Other = Test__WCAG_1__8_1

class Test__WCAG_1__9_1 (Walking_Test):
    
    _name = 'WCAG 1.0 checkpoint  9.1, Section 508 (f)'
    _description = "Provide client-side image maps instead of server-side image maps except where the regions cannot be defined with an available geometric shape."
    _url = 'http://www.w3.org/TR/WCAG10/#tech-client-side-maps'
    _state = Implementation_State.COMPLETE
    _version = 0

    _sensitive_tags = ('img',)
    
    def _check_node (self, node):
        issues = []
        if node.attr ('ismap'):
            issues.append (Possible_Error (node, "Client side image map should be used, unless it's impossible with the available geometric shapes"))
        return issues

class Test__WCAG_1__9_2 (Script_Test):
    
    _name = 'WCAG 1.0 checkpoint  9.2'
    _description = "Ensure that any element that has its own interface can be operated in a device-independent manner."
    _url = 'http://www.w3.org/TR/WCAG10/#tech-keyboard-operable'
    _state = Implementation_State.COMPLETE
    _version = 0

    def _check_script (self, node):
        return [Possible_Issue (node, "Check the script/applet is operable in an input device independent way")]

class Test__WCAG_1__9_3 (Script_Test):
    
    _name = 'WCAG 1.0 checkpoint  9.3'
    _description = "For scripts, specify logical event handlers rather than device-dependent event handlers."
    _url = 'http://www.w3.org/TR/WCAG10/#tech-device-independent-events'
    _state = Implementation_State.COMPLETE
    _version = 0

    def _check_script (self, node):
        return [Possible_Issue (node, "Check the script/applet uses logical rather than device dependent event handlers")]

class Test__WCAG_1__9_4 (Walking_Test):
    
    _name = 'WCAG 1.0 checkpoint  9.4'
    _description = "Create a logical tab order through links, form controls, and objects."
    _url = 'http://www.w3.org/TR/WCAG10/#tech-tab-order'
    _state = Implementation_State.COMPLETE
    _version = 0

    _sensitive_tags = ('a', 'area', 'button', 'input', 'object', 'select', 'textarea',)

    def _check_node (self, node):
        issues = []
        if node.name () == 'object' and not node.attr ('classid'):
            pass
        elif not node.attr ('tabindex'):
            issues.append (Possible_Error (node, "No TABINDEX in the element"))
        return issues
    
class Test__WCAG_1__9_5 (Walking_Test):
    
    _name = 'WCAG 1.0 checkpoint  9.5'
    _description = "Provide keyboard shortcuts to important links (including those in client-side image maps), form controls, and groups of form controls."
    _url = 'http://www.w3.org/TR/WCAG10/#tech-keyboard-shortcuts'
    _state = Implementation_State.COMPLETE
    _version = 0

    _sensitive_tags = ('a', 'area', 'button', 'input', 'label', 'legend', 'textarea',)
    
    def _check_node (self, node):
        util.if_ (node.attr ('accesskey'), self._access_keys, self._no_access_keys).append (node)
        return []

    def _run (self, document):
        self._access_keys = []
        self._no_access_keys = []
        issues = super (Test__WCAG_1__9_5, self)._run (document)
        if self._no_access_keys:
            if not self._access_keys:
                issues.append (Possible_Error (None, "No access keys defined"))
            elif len (self._access_keys) < 10:
                for n in self._no_access_keys:
                    issues.append (Possible_Issue (n, "Access key not defined", n.name ()))
        return issues
    
class Test__WCAG_1__10_1 (Script_Test, Walking_Test):
    
    _name = 'WCAG 1.0 checkpoint 10.1'
    _description = "Until user agents allow users to turn off spawned windows, do not cause pop-ups or other windows to appear and do not change the current window without informing the user."
    _url = 'http://www.w3.org/TR/WCAG10/#tech-avoid-pop-ups'
    _state = Implementation_State.COMPLETE
    _version = 0

    _sensitive_tags = ('a', 'area', 'base', 'form', 'link',)
    
    def __init__ (self):
        super (Script_Test, self).__init__ ()
        self._sensitive_tags = self._sensitive_tags + Test__WCAG_1__10_1._sensitive_tags

    def _check_script (self, node):
        return [Possible_Issue (node, "Check the script doesn't popup new window")]
    
    def _check_node (self, node):
        issues = super (Test__WCAG_1__10_1, self)._check_node (node)
        if (node.name () in Test__WCAG_1__10_1._sensitive_tags and
            node.attr ('target') == '_blank'):
            issues.append (Error (node, "Link causing window popup"))
        return issues
    
class Test__WCAG_1__10_2 (Test):
    
    _name = 'WCAG 1.0 checkpoint 10.2'
    _description = "Until user agents support explicit associations between labels and form controls, for all form controls with implicitly associated labels, ensure that the label is properly positioned."
    _url = 'http://www.w3.org/TR/WCAG10/#tech-unassociated-labels'
    _state = Implementation_State.COMPLETE
    _version = 0

    def _run (self, document):
        issues = []
        labels = []
        ok_nodes = []
        def find_inputs (node):
            inputs = []
            for n in node.children ():
                tag = n.name ()
                if tag == 'label':
                    pass
                elif tag == 'input':
                    inputs.append (n)
                else:
                    inputs = inputs + find_inputs (n)
            return inputs
        for node in document.iter_tags (('label',)):
            if node.attr ('for'):
                labels.append (node.attr ('for'))
            else:
                inputs = find_inputs (node)
                if len (inputs) == 1:
                    ok_nodes.append (inputs[0])
        for node in document.iter_tags (('input',)):
            if node in ok_nodes or node.attr ('id') in labels:
                pass
            else:
                issues.append (Possible_Issue (node, "Check there is clearly associated label to the input field"))
        return issues

class Test__WCAG_1__10_3 (Walking_Test):
    
    _name = 'WCAG 1.0 checkpoint 10.3'
    _description = "Until user agents (including assistive technologies) render side-by-side text correctly, provide a linear text alternative (on the current page or some other) for all tables that lay out text in parallel, word-wrapped columns."
    _url = 'http://www.w3.org/TR/WCAG10/#tech-linear-tables'
    _state = Implementation_State.COMPLETE
    _version = 0

    _sensitive_tags = ('table',)

    def _check_node (self, node):
        issues = []
        def check_cols (node):
            children = []
            for c in node.children ():
                if c.name () == 'td':
                    children.append (c)
                else:
                    children = children + check_cols (c)
            return children
        def check_rows (node):
            for c in node.children ():
                if node.name () in ('th', 'tr',):
                    cols = check_cols (c)
                    if len (cols) > 1:
                        return True
                else:
                    if check_rows (c):
                        return True
            return False
        if check_rows (node):
            issues.append (Possible_Issue (node, "If the table contains word-wrapped columns, check a linearized version is provided"))
        return issues

class Test__WCAG_1__10_4 (Walking_Test):
    
    _name = 'WCAG 1.0 checkpoint 10.4'
    _description = "Until user agents handle empty controls correctly, include default, place-holding characters in edit boxes and text areas."
    _url = 'http://www.w3.org/TR/WCAG10/#tech-place-holders'
    _state = Implementation_State.COMPLETE
    _version = 0

    _sensitive_tags = ('input', 'textarea',)

    def _check_node (self, node):
        issues = []
        tag = node.name ()
        if tag == 'textarea':
            if not node.text ():
                issues.append (Error (node, "No default characters in a text input element"))
        elif tag == 'input' and node.attr ('type') in ('text', 'password', 'file',):
            if not node.attr ('value'):
                issues.append (Error (node, "No default characters in a text input element"))
        return issues

class Test__WCAG_1__10_5 (Walking_Test):
    
    _name = 'WCAG 1.0 checkpoint 10.5'
    _description = "Until user agents (including assistive technologies) render adjacent links distinctly, include non-link, printable characters (surrounded by spaces) between adjacent links."
    _url = 'http://www.w3.org/TR/WCAG10/#tech-divide-links'
    _state = Implementation_State.COMPLETE
    _version = 0

    _sensitive_tags = ('a',)

    def _check_node (self, node):
        issues = []
        if node.attr ('href'):
            def adjacent_link (node):
                if node.name () == 'a':
                    if node.attr ('href'):
                        return node
                    else:
                        return None
                text = node.text ()
                if text:
                    return text
                return None
            text = ''
            next = node.next_node ()
            while next:                
                link_or_text = adjacent_link (next)
                if isinstance (link_or_text, document.Node):
                    if not text:
                        message = "Links not separated"
                    elif re.match ('^[\0-\40\200-\240]+$', text):
                        message = "No separator between links"
                    elif not re.match ('.*\\s.*', text):
                        message = "No space between links"
                    else:
                        message = "Adjacent links"
                    issues.append (Possible_Error (node, message, (node.text (), link_or_text.text (), text,)))
                    break
                elif link_or_text:
                    text = text + link_or_text.replace ('&nbsp;', ' ').replace ('\n', ' ')
                    if re.match ('.*([^\0-\40\200-\240].*\\s.*[^\0-\40\200-\240]|\\s.*[^\0-\40\200-\240].*\\s).*', text):
                        break
                children = next.children ()
                if children:
                    next = children[0]
                else:
                    next = next.next_node ()
        return issues

class Test__WCAG_1__11_1 (Test):

    _name = 'WCAG 1.0 checkpoint 11.1'
    _description = "Use W3C technologies when they are available and appropriate for a task and use the latest versions when supported."
    _url = 'http://www.w3.org/TR/WCAG10/#tech-latest-w3c-specs'
    _state = Implementation_State.COMPLETE
    _version = 0

    def _run (self, document):
        issues = []
        doctype = document.doctype ()
        if not doctype:
            issues.append (Possible_Error (None, "No doctype found"))
        elif not re.match ('.*DTD (XHTML 1\.0|HTML 4\.01)', doctype):
            issues.append (Possible_Error (None, "Old (X)HTML version used", doctype))
        return issues

class Test__WCAG_1__11_2 (Test):

    _name = 'WCAG 1.0 checkpoint 11.2'
    _description = "Avoid deprecated features of W3C technologies."
    _url = 'http://www.w3.org/TR/WCAG10/#tech-avoid-deprecated'
    _state = Implementation_State.COMPLETE
    _version = 0

    _deprecated_elements = ('applet', 'basefont', 'center', 'dir', 'font', 'isindex', 'menu', 's', 'strike', 'u',)
    _deprecated_attributes = {'align': ('col', 'colgroup', 'tbody', 'td', 'tfoot', 'th', 'thead', 'tr',),
                              'alink': (),
                              'background': (),
                              'bgcolor': (),
                              'border': ('img', 'object',),
                              'clear': (),
                              'color': (),
                              'compact': (),
                              'face': (),
                              'height': ('td', 'th',),
                              'hspace': (),
                              'language': (),
                              'link': (),
                              'noshade': (),
                              'nowrap': (),
                              'size': ('hr',),
                              'start': (),
                              'text': (),
                              'type': ('li', 'ol', 'ul',),
                              'value': ('li',),
                              'version': (),
                              'vlink': (),
                              'vspace': (),
                              'width': ('hr', 'td', 'th', 'pre',),
                              }

    def _run (self, document):
        issues = []
        for node in document.iter_all_nodes ():
            tag = node.name ()
            if tag in self._deprecated_elements:
                issues.append (Error (node, "Deprecated element", tag))
            else:
                for aname in node.attribute_names ():
                    spec = self._deprecated_attributes.get (aname)
                    if (spec is not None and
                        (not spec or tag in spec)):
                        issues.append (Error (node, "Deprecated attribute", (tag, aname,)))
        return issues

class Test__WCAG_1__11_3 (Test):

    _name = 'WCAG 1.0 checkpoint 11.3'
    _description = "Provide information so that users may receive documents according to their preferences (e.g., language, content type, etc.)."
    _url = 'http://www.w3.org/TR/WCAG10/#tech-content-preferences'
    _state = Implementation_State.COMPLETE
    _version = 0

    def _run (self, _document):
        return [Possible_Issue (None, "Check users can receive the document according to their preferences")]

class Test__WCAG_1__11_4 (Test):

    _name = 'WCAG 1.0 checkpoint 11.4, Section 508 (k)'
    _description = "If, after best efforts, you cannot create an accessible page, provide a link to an alternative page that uses W3C technologies, is accessible, has equivalent information (or functionality), and is updated as often as the inaccessible (original) page."
    _url = 'http://www.w3.org/TR/WCAG10/#tech-alt-pages'
    _state = Implementation_State.COMPLETE
    _version = 0

    def _run (self, _document):
        return [Possible_Issue (None, "If the page can't be made accessible, check an accessible page is provided")]

class Test__WCAG_1__12_1 (Walking_Test):

    _name = 'WCAG 1.0 checkpoint 12.1, Section 508 (i)'
    _description = "Title each frame to facilitate frame identification and navigation."
    _url = 'http://www.w3.org/TR/WCAG10/#tech-frame-titles'
    _state = Implementation_State.COMPLETE
    _version = 0

    _sensitive_tags = ('frame',)
    
    def _check_node (self, node):
        issues = []
        if not node.attr ('title'):
            issues.append (Error (node, "No TITLE in a FRAME element"))
        return issues

class Test__WCAG_1__12_2 (Walking_Test):

    _name = 'WCAG 1.0 checkpoint 12.2'
    _description = "Describe the purpose of frames and how frames relate to each other if it is not obvious by frame titles alone."
    _url = 'http://www.w3.org/TR/WCAG10/#tech-frame-longdesc'
    _state = Implementation_State.COMPLETE
    _version = 0

    _sensitive_tags = ('frame',)
    
    def _check_node (self, node):
        issues = []
        if not node.attr ('longdesc'):
            issues.append (Possible_Issue (node, "Check no further description of the frame and its relation to other frames is needed", node.attr ('title')))
        return issues

class Test__WCAG_1__12_3 (Test):

    _name = 'WCAG 1.0 checkpoint 12.3'
    _description = "Divide large blocks of information into more manageable groups where natural and appropriate."
    _url = 'http://www.w3.org/TR/WCAG10/#tech-group-information'
    _state = Implementation_State.COMPLETE
    _version = 0

    def _run (self, document, _max_fields=8, _max_options=10, _max_text_len=500):
        issues = [Possible_Issue (None, "Check there is no large undivided block of information")]
        def subtag_present (node, subtag):
            for n in node.iter_subtree ():
                if n.name () == subtag:
                    return True
            return False
        for node in document.iter_tags (('form',)):
            if not subtag_present (node, 'fieldset'):
                n = 0
                for i in node.iter_subtree_tags (('input',)):
                    if i.attr ('type') != 'hidden':
                        n = n + 1
                if n > _max_fields:
                    issues.append (Possible_Issue (node, "Many ungrouped INPUTs in a single FORM"))
        for node in document.iter_tags (('select',)):
            if not subtag_present (node, 'optgroup'):
                options = [n.name () for n in node.iter_subtree_tags (('option',))]
                if len (options) > _max_options:
                    issues.append (Possible_Issue (node, "Many ungrouped OPTIONs in a single SELECT",
                                                   options[:3] + ['...']))
        for node in document.iter_all_nodes ():
            if len (node.text () or '') > _max_text_len:
                issues.append (Possible_Issue (node, "Long undivided text", node.text ()[:20] + '...'))
        return issues

class Test__WCAG_1__12_4 (Test):

    _name = 'WCAG 1.0 checkpoint 12.4'
    _description = "Associate labels explicitly with their controls."
    _url = 'http://www.w3.org/TR/WCAG10/#tech-associate-labels'
    _state = Implementation_State.COMPLETE
    _version = 0

    def _run (self, document):
        issues = []
        ids = {}
        for node in document.iter_tags (('label',)):
            id = node.attr ('for')
            if id:
                ids[id] = True
        for node in document.iter_tags (('input',)):
            if node.attr ('type') not in ('submit', 'reset', 'button', 'hidden',):
                if not ids.get (node.attr ('id')):
                    issues.append (Error (node, "No explicit label for an INPUT element"))
        return issues

class Test__WCAG_1__13_1 (Walking_Test):

    _name = 'WCAG 1.0 checkpoint 13.1'
    _description = "Clearly identify the target of each link."
    _url = 'http://www.w3.org/TR/WCAG10/#tech-meaningful-links'
    _state = Implementation_State.COMPLETE
    _version = 0

    _sensitive_tags = ('a',)

    def _check_node (self, node):
        issues = []
        if node.attr ('href'):
            text = node.text ()
            for n in node.iter_subtree ():
                text = text + (n.text () or '')
            if re.match ('(click +)?here', text):
                issues.append (Error (node, "Non-meaningful link text", text))
            else:
                issues.append (Possible_Issue (node, "Check the link text is meaningful and terse", text))
        return issues

class Test__WCAG_1__13_2 (Test):

    _name = 'WCAG 1.0 checkpoint 13.2'
    _description = "Provide metadata to add semantic information to pages and sites."
    _url = 'http://www.w3.org/TR/WCAG10/#tech-use-metadata'
    _state = Implementation_State.COMPLETE
    _version = 0

    def _run (self, document):
        return [Possible_Issue (None, "Check metadata containing semantic information about the document and site is provided")]

class Test__WCAG_1__13_3 (Test):

    _name = 'WCAG 1.0 checkpoint 13.3'
    _description = "Provide information about the general layout of a site (e.g., a site map or table of contents)."
    _url = 'http://www.w3.org/TR/WCAG10/#tech-site-description'
    _state = Implementation_State.COMPLETE
    _version = 0

    def _run (self, document):
        return [Possible_Issue (None, "Check information about site layout is available and contains clear information about provided accessibility features")]

class Test__WCAG_1__13_4 (Test):

    _name = 'WCAG 1.0 checkpoint 13.4'
    _description = "Use navigation mechanisms in a consistent manner."
    _url = 'http://www.w3.org/TR/WCAG10/#tech-clear-nav-mechanism'
    _state = Implementation_State.COMPLETE
    _version = 0

    def _run (self, document):
        return [Possible_Issue (None, "Check navigation mechanism is used consistently")]

class Test__WCAG_1__13_5 (Test):

    _name = 'WCAG 1.0 checkpoint 13.5'
    _description = "Provide navigation bars to highlight and give access to the navigation mechanism."
    _url = 'http://www.w3.org/TR/WCAG10/#tech-nav-bar'
    _state = Implementation_State.COMPLETE
    _version = 0

    def _run (self, document):
        return [Possible_Issue (None, "Check a navigation bar is available")]

class Test__WCAG_1__13_6 (Test):

    _name = 'WCAG 1.0 checkpoint 13.6'
    _description = "Group related links, identify the group (for user agents), and, until user agents do so, provide a way to bypass the group."
    _url = 'http://www.w3.org/TR/WCAG10/#tech-group-links'
    _state = Implementation_State.COMPLETE
    _version = 0

    def _run (self, document, _max_nearby_links=3):
        issues = []
        links = []
        def link_groups (node):
            tag = node.name ()
            if tag == 'map' and links:
                yield links
                links[:] = []
            elif tag == 'a' and node.attr ('href'):
                links.append (node)
            else:
                for c in node.children ():
                    for g in link_groups (c):
                        yield g
        for top_node in document.iter_all_nodes ():
            for group in list (link_groups (top_node)) + [links]:
                if len (group) > _max_nearby_links:
                    issues.append (Possible_Issue (group[0], "If the links are related, check they are grouped and there is a way to bypass the group", group[0].text () + ', ...'))
            break
        return issues

class Test__WCAG_1__13_7 (Test):

    _name = 'WCAG 1.0 checkpoint 13.7'
    _description = "If search functions are provided, enable different types of searches for different skill levels and preferences."
    _url = 'http://www.w3.org/TR/WCAG10/#tech-searches'
    _state = Implementation_State.COMPLETE
    _version = 0

    def _run (self, document):
        return [Possible_Issue (None, "If search functions are provided, check different types of searches are provided")]

class Test__WCAG_1__13_8 (Test):

    _name = 'WCAG 1.0 checkpoint 13.8'
    _description = "Place distinguishing information at the beginning of headings, paragraphs, lists, etc."
    _url = 'http://www.w3.org/TR/WCAG10/#tech-front-loading'
    _state = Implementation_State.COMPLETE
    _version = 0

    def _run (self, document):
        return [Possible_Issue (None, "Check distinguishing information is placed at the beginnings of headings, paragraphs, lists, etc.")]

class Test__WCAG_1__13_9 (Test):

    _name = 'WCAG 1.0 checkpoint 13.9'
    _description = "Provide information about document collections (i.e., documents comprising multiple pages.)."
    _url = 'http://www.w3.org/TR/WCAG10/#tech-bundled-version'
    _state = Implementation_State.COMPLETE
    _version = 0

    def _run (self, document):
        return [Possible_Issue (None, "If document collection is presented, check LINK elements are used properly and possibly presence of an archive of multiple pages")]

class Test__WCAG_1__13_10 (Walking_Test):

    _name = 'WCAG 1.0 checkpoint 13.10'
    _description = "Provide a means to skip over multi-line ASCII art."
    _url = 'http://www.w3.org/TR/WCAG10/#tech-skip-over-ascii'
    _state = Implementation_State.COMPLETE
    _version = 0

    _sensitive_tags = ('pre',)

    def _check_node (self, node):
        issues = []
        text = node.text ()
        if text and text.find ('\n') >= 0:
            issues.append (Possible_Issue (node, "If the text is an ASCII art, check necessity of its use and check there are means to skip it",
                                           text[:20] + util.if_ (len (text) > 20, '...', '')))
        return issues

class Test__WCAG_1__14_1 (Test):

    _name = 'WCAG 1.0 checkpoint 14.1'
    _description = "Use the clearest and simplest language appropriate for a site's content."
    _url = 'http://www.w3.org/TR/WCAG10/#tech-simple-and-straightforward'
    _state = Implementation_State.COMPLETE
    _version = 0

    def _run (self, document):
        return [Possible_Issue (None, "Check the document language is the clearest and simplest possible")]
    
class Test__WCAG_1__14_2 (Test):

    _name = 'WCAG 1.0 checkpoint 14.2'
    _description = "Supplement text with graphic or auditory presentations where they will facilitate comprehension of the page."
    _url = 'http://www.w3.org/TR/WCAG10/#tech-icons'
    _state = Implementation_State.COMPLETE
    _version = 0

    def _run (self, document):
        return [Possible_Issue (None, "Check graphic and auditory presentations are present where they are useful for better comprehension")]

class Test__WCAG_1__14_3 (Test):

    _name = 'WCAG 1.0 checkpoint 14.3'
    _description = "Create a style of presentation that is consistent across pages."
    _url = 'http://www.w3.org/TR/WCAG10/#tech-consistent-style'
    _state = Implementation_State.COMPLETE
    _version = 0

    def _run (self, document):
        return [Possible_Issue (None, "If the site contains multiple pages, check their presentation style is consistent")]

Test__508_a = Test__WCAG_1__1_1

Test__508_b = Test__WCAG_1__1_4

Test__508_c = Test__WCAG_1__2_1

Test__508_d = Test__WCAG_1__6_1

Test__508_e = Test__WCAG_1__1_2

Test__508_f = Test__WCAG_1__9_1

Test__508_g = Test__WCAG_1__5_1

Test__508_h = Test__WCAG_1__5_2

Test__508_i = Test__WCAG_1__12_1

Test__508_j = Test__WCAG_1__7_1

Test__508_k = Test__WCAG_1__11_4

class Test__508_l (Script_Test):

    _name = 'Section 508 (l)'
    _description = "When pages utilize scripting languages to display content, or to create interface elements, the information provided by the script shall be identified with functional text that can be read by assistive technology."
    _url = 'http://www.section508.gov/index.cfm?FuseAction=Content&ID=12#Web'
    _state = Implementation_State.COMPLETE
    _version = 0

    def _check_script (self, node):
        return [Possible_Issue (node, "Check the information provided by the script is identified with functional text that can be read using assistive technology")]

class Test__508_m (Script_Test):

    _name = 'Section 508 (m)'
    _description = "When a web page requires that an applet, plug-in or other application be present on the client system to interpret page content, the page must provide a link to a plug-in or applet that complies with §1194.21(a) through (l)."
    _url = 'http://www.section508.gov/index.cfm?FuseAction=Content&ID=12#Web'
    _state = Implementation_State.COMPLETE
    _version = 0

    def _check_script (self, node):
        return [Possible_Issue (node, "If the object requires a piece of software on the client system to interpret page content, check there is a link to an interpreter which complies with Section 508 1194.21 (a) through (l)")]

class Test__508_n (Walking_Test):

    _name = 'Section 508 (n)'
    _description = "When electronic forms are designed to be completed on-line, the form shall allow people using assistive technology to access the information, field elements, and functionality required for completion and submission of the form, including all directions and cues."
    _url = 'http://www.section508.gov/index.cfm?FuseAction=Content&ID=12#Web'
    _state = Implementation_State.COMPLETE
    _version = 0

    _sensitive_tags = ('form',)

    def _check_node (self, node):
        return [Possible_Issue (node, "If the object is an electronic form, check it allows people using assistive technologies to access the information, field elements, functionality, directions and cues required for completion and submission of the form")]
    
class Test__508_o (Test):

    _name = 'Section 508 (o)'
    _description = "A method shall be provided that permits users to skip repetitive navigation links."
    _url = 'http://www.section508.gov/index.cfm?FuseAction=Content&ID=12#Web'
    _state = Implementation_State.COMPLETE
    _version = 0

    def _run (self, document):
        issues = []
        if len (list (document.iter_tags (('a',)))) > 1:
            issues.append (Possible_Issue (None, "If there are repetitive navigation links in the document, check there is a method to skip them"))
        return issues

class Test__508_p (Script_Test):

    _name = 'Section 508 (p)'
    _description = "When a timed response is required, the user shall be alerted and given sufficient time to indicate more time is required."
    _url = 'http://www.section508.gov/index.cfm?FuseAction=Content&ID=12#Web'
    _state = Implementation_State.COMPLETE
    _version = 0

    def _check_script (self, node):
        self._timed_response_possible = True
        return []

    def _run (self, document):
        self._timed_response_possible = False
        issues = super (Test__508_p, self)._run (document)
        if not self._timed_response_possible:
            for node in document.iter_tags (('meta',)):
                if (node.attr ('http-equiv') and
                    node.attr ('http-equiv').lower () == 'refresh' and
                    node.attr ('content') and
                    node.attr ('content').lower ().find ('url=') != -1):
                    self._timed_response_possible = True
                    break
        if self._timed_response_possible:
            issues.append (Possible_Issue (None, "If a timed response is required somewhere in the document, check the user is alerted and given sufficient time to indicate more time is required"))
        return issues
