### common.py --- Tests common to most test sets

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

import re

import document
import validator


class Test__Common_Syntax (Test):

    _name = 'Common (X)HTML syntax test'
    _state = Implementation_State.COMPLETE
    _version = 0

    def _run (self, document_):
        issues = []
        regex = re.compile ('^[^:]+:[^:]+:([0-9]+):([0-9]+):(.*)$')
        ignore_regex = re.compile ('.* non SGML character number [12][0-9][0-9]')
        error_output = validator.validate (document_.location ())
        for error in error_output.split ('\n'):
            if error:
                if ignore_regex.match (error):
                    continue
                match = regex.match (error)
                if match:
                    line = int (match.group (1))
                    column = int (match.group (2))
                    message = match.group (3)
                    node = document.Node (None, '', (), (line, column,))
                    issues.append (Error (node, "Syntax error", message))
                else:
                    issues.append (Error (None, "Syntax error", error))
        return issues


class Test__Common_Stylesheets (Stylesheet_Test):

    _name = 'Common stylesheet test implied by another test'
    _state = Implementation_State.COMPLETE
    _version = 0

    def _run (self, document_):
        issues = super (Test__Common_Stylesheets, self)._run (document_)
        for e in self._style_errors:
            issues.append (util.if_ (isinstance (e, document.No_Stylesheet_Type_Error), Error, Possible_Issue)
                           (e.node, e.description, e.data))
        return issues

    
class Test__Common_Colors (Color_Test):

    _name = 'Common color test implied by another test'
    _state = Implementation_State.COMPLETE
    _version = 0

    def _check_node_color (self, node, foreground, background, link_colors,
                           style_foreground, style_background, style_background_image):
        issues = super (Test__Common_Colors, self)._check_node_color (
            node, foreground, background, link_colors,
            style_foreground, style_background, style_background_image)
        # Check common color properties
        colors = [c for c in [foreground, background, style_foreground, style_background] + link_colors
                  if c and c[0] != '#']
        if colors:
            issues.append (Error (node, "Colors specified by names instead of RGB values", colors))
        return issues
