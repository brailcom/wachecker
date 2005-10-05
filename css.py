### css.py --- Simple CSS parser

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
import sys
import types

import yappy.parser

import config
import location
import util


# Selectors

class Selector (object):
    
    def __init__ (self):
        self._weight = [0, 0, 0]

    def weight (self):
        return self._weight

    def matches (self, node, document):
        return False

class Node_Selector (Selector):
    pass

class Simple_Node_Selector (Node_Selector):
    
    def __init__ (self, node_name):
        super (Simple_Node_Selector, self).__init__ ()
        self._weight[2] = self._weight[2] + 1
        self._node_name = node_name

    def matches (self, node, document):
        return node.name () == self._node_name

    def __str__ (self):
        return '<%s: %s; weight: %s>' % (self.__class__.__name__, self._node_name, self._weight,)

class Universal_Selector (Node_Selector):

    def matches (self, node, document):
        return True

class Property_Selector (Selector):
    pass

class Pseudo_Selector (Property_Selector):

    def __init__ (self, pseudo_name, pseudo_args=()):
        super (Pseudo_Selector, self).__init__ ()
        self._name = pseudo_name
        self._args = pseudo_args

    def matches (self, node, document):
        if self._name == 'first-child':
            return not node.prev_sibling ()
        elif self._name in ('link', 'visited',):
            return node.name () in ('a', 'link',)
        elif self._name in ('hover', 'active', 'focus',):
            return True
        elif self._name == 'lang':
            return node.attr ('lang') in self._args
        else:
            return False

    def __str__ (self):
        return '<%s: %s, %s; weight: %s>' % (self.__class__.__name__, self._name, self._args, self._weight,)

class Attribute_Selector (Property_Selector):

    NONE_OP = 'NONE_OP'
    EQUAL_OP = 'EQUAL_OP'
    SPACE_LIST_OP = 'SPACE_LIST_OP'
    COMMA_LIST_OP = 'COMMA_LIST_OP'

    def __init__ (self, attribute, operator, value=None):
        super (Attribute_Selector, self).__init__ ()
        self._weight[1] = self._weight[1] + 1
        self._attribute = attribute
        self._operator = operator
        self._value = value

    def matches (self, node, document):
        attval = node.attr (self._attribute)
        if self._operator == self.NONE_OP:
            if attval:
                return True
        elif self._operator == self.EQUAL_OP:
            if attval and attval == self._value:
                return True
        elif self._operator == self.SPACE_LIST_OP:
            if attval:
                for v in attval.split (' '):
                    if v == self._value:
                        return True
        elif self._operator == self.COMMA_LIST_OP:
            if attval:
                for v in attval.split (','):
                    if v.trim () == self._value:
                        return True
        else:
            raise Exception ('Case error', self._operator)
        return False

    def __str__ (self):
        return ('<%s: %s %s %s; weight: %s>' %
                (self.__class__.__name__, self._attribute, self._operator, self._value, self._weight,))

class Combined_Selector (Selector):

    def __init__ (self, selector1, selector2):
        super (Combined_Selector, self).__init__ ()
        self._weight = [x + y for x, y in zip (selector1.weight(), selector2.weight ())]
        self._selector1 = selector1
        self._selector2 = selector2

    def __str__ (self):
        return '<%s: %s %s>' % (self.__class__.__name__, self._selector1, self._selector2,)

class Predecessor_Selector (Combined_Selector):

    def matches (self, node, document):
        if not self._selector1.matches (node, document):
            return False
        while True:
            node = node.parent ()
            if not node:
                break
            if self._selector2.matches (node, document):
                return True
        return False

class Parent_Selector (Combined_Selector):

    def matches (self, node, document):
        parent = node.parent ()
        return (parent and
                self._selector1.matches (parent, document) and
                self._selector2.matches (node, document))

class Neighbor_Selector (Combined_Selector):

    def matches (self, node, document):
        prev_node = node.prev_sibling ()
        return (prev_node and
                self._selector1.matches (prev_node, document) and
                self._selector2.matches (node, document))
    
class Selector_Set (Selector):
    
    def __init__ (self, selectors):
        super (Selector_Set, self).__init__ ()
        def sum (values):
            result = 0
            for v in values:
                result = result + v
            return result
        weights = [s.weight () for s in selectors]
        self._weight = [sum (x) for x in zip (*weights)]
        self._selectors = selectors

    def matches (self, node, document):
        for s in self._selectors:
            if not s.matches (node, document):
                return False
        return True

    def __str__ (self):
        return '<%s: %s>' % (self.__class__.__name__, self._selectors,)

def selector_set (*selectors):
    if len (selectors) == 1:
        result = selectors[0]
    else:
        result = Selector_Set (selectors)
    return result

# Intermediate CSS data structures

class Property (util.Structure):
    _attributes = (('name', "Property name.",),
                   ('value', "Property value.",),
                   ('important', "True iff the rule is important in the CSS sense.", False,),
                   )

class Rule (util.Structure):
    _attributes = (('selector', "'Selector' instance.",),
                   ('properties', "Sequence of properties.",),
                   )

class Media_Rules (util.Structure):
    _attributes = (('media', "Sequence of media types; if empty, apply to all.", [],),
                   ('rules', "Sequence of 'Rule' instances.",),
                   )
    
# Stylesheets

class Stylesheet (object):

    def __init__ (self, media_rules):
        self._media_rules = list (media_rules)

    def restrict_to_media (self, media):
        if media:
            for i in len (self._media_rules):
                r = self._media_rules[i]
                orig_media = r.media
                if orig_media:
                    r.media = [m for m in orig_media if m in media]
                    if not r.media:
                        del self._media_rules[i]
                else:
                    r.media = media
                    i = i + 1

    def merge (self, stylesheet):
        return Stylesheet (self._media_rules + stylesheet._media_rules)
                    
    def node_properties (self, node, document, media='screen'):
        properties = {}
        property_weights = {}
        for mr in self._media_rules:
            if not mr.media or media in mr.media:
                for r in mr.rules:
                    if r.selector.matches (node, document):
                        parent = node
                        while True:
                            parent = parent.parent ()
                            if parent:
                                if r.selector.matches (parent, document):
                                    break
                            else:
                                weight = r.selector.weight ()
                                for p in r.properties:
                                    if (not properties.has_key (p.name) or
                                        property_weights[p.name] < weight):
                                        properties[p.name] = p.value
                                        property_weights[p.name] = weight
                                break
        return properties

    def __str__ (self):
        result = 'Stylesheet:\n'
        for mr in self._media_rules:
            result = result + str (mr) + '\n'
        return result

def merge_stylesheets (stylesheet1, stylesheet2):
    return stylesheet1.merge (stylesheet2)

# Lexer

Tokens = util.Enumeration ("CSS tokens",
                           ('IDENT', "",),
                           ('ATKEYWORD', "",),
                           ('IMPORT_SYM', "",),
                           ('MEDIA_SYM', "",),
                           ('PAGE_SYM', "",),
                           ('FONT_FACE_SYM', "",),
                           ('CHARSET_SYM', "",),
                           ('IMPORTANT_SYM', "",),
                           ('STRING', "",),
                           ('HASH', "",),
                           ('NUMBER', "",),
                           ('PERCENTAGE', "",),
                           ('DIMENSION', "",),
                           ('URI', "",),
                           ('UNICODE_RANGE', "",),
                           ('SEMICOLON', "",),
                           ('COLON', "",),
                           ('COMMA', "",),
                           ('SLASH', "",),
                           ('PLUS', "",),
                           ('STAR', "",),
                           ('MINUS', "",),
                           ('GT', "",),
                           ('EQ', "",),
                           ('DOT', "",),
                           ('LBRACE', "",),
                           ('RBRACE', "",),
                           ('LPAREN', "",),
                           ('RPAREN', "",),
                           ('LBRACKET', "",),
                           ('RBRACKET', "",),
                           ('S', "",),
                           ('COMMENT', "",),
                           ('FUNCTION', "",),
                           ('INCLUDES', "",),
                           ('DASHMATCH', "",),
                           ('DELIM', "",),
                           )

_m_w = '[ \t\r\n\f]*'
_m_nl = '\n|\r\n|\r|\f'
_m_h = '[0-9a-fA-F]'
_m_nonascii = '[^\0-\177]'
_m_unicode = '\\\\(%s){1,6}[ \n\r\t\f]?' % (_m_h,)
_m_escape = '(%s)|\\\\[^\0-\37]' % (_m_unicode,)
_m_nmstart = '[a-zA-Z]|(%s)|(%s)' % (_m_nonascii, _m_escape,)
_m_nmchar = '[a-zA-Z0-9-]|(%s)|(%s)' % (_m_nonascii, _m_escape,)
_m_string1 = '"([\t !#$%%&(-~]|\\\\(%s)|\'|(%s)|(%s))*"' % (_m_nl, _m_nonascii, _m_escape,)
_m_string2 = '\'([\t !#$%%&(-~]|\\\\(%s)|"|(%s)|(%s))*\''  % (_m_nl, _m_nonascii, _m_escape,)
_m_ident = '(%s)(%s)*' % (_m_nmstart, _m_nmchar,)
_m_name = '(%s)+' % (_m_nmchar,)
_m_num = '[0-9]*\\.[0-9]+|[0-9]+'
_m_string = '(%s)|(%s)' % (_m_string1, _m_string2,)
_m_url = '([!#$%%&*-~]|(%s)|(%s))*' % (_m_nonascii, _m_escape,)
_m_range = ('\\?{1,6}|(%s)(\\?{0,5}|(%s)(\\?{0,4}|(%s)(\\?{0,3}|(%s)(\?{0,2}|(%s)(\\??|(%s))))))' %
            (_m_h, _m_h, _m_h, _m_h, _m_h, _m_h,))

def token_func (name):
    def func (x):
        return (name, x,)
    return func

def string_token_func (x):
    return (Tokens.STRING, x[1:-1],)

def url_token_func (x):
    url = x[x.find('"')+1:x.rfind('"')]
    return (Tokens.URI, url,)

tokens = [
    # Order here is important to resolve conflicts!
    ('/\\*[^*]*\\*+([^/][^*]*\\*+)*/', '',), # comment
    ('@import', token_func (Tokens.IMPORT_SYM),),
    ('@page', token_func (Tokens.PAGE_SYM),),
    ('@media', token_func (Tokens.MEDIA_SYM),),
    ('@font-face', token_func (Tokens.FONT_FACE_SYM),),
    ('@charset', token_func (Tokens.CHARSET_SYM),),
    ('@(%s)' % (_m_ident,), token_func (Tokens.ATKEYWORD),),
    ('!(%s)important' % (_m_w,), token_func (Tokens.IMPORTANT_SYM),),
    ('#(%s)' % (_m_name,), token_func (Tokens.HASH),),
    ('url\\((%s)(%s)(%s)\\)|url\\((%s)(%s)(%s)\\)' % (_m_w, _m_string, _m_w, _m_w, _m_url, _m_w,), url_token_func,),
    (_m_string, string_token_func,),
    ('(%s)\\(' % (_m_ident,), token_func (Tokens.FUNCTION),),
    ('(%s)%%' % (_m_num,), token_func (Tokens.PERCENTAGE),),
    ('(%s)(%s)' % (_m_num, _m_ident,), token_func (Tokens.DIMENSION),),
    (_m_ident, token_func (Tokens.IDENT),),
    (_m_num, token_func (Tokens.NUMBER),),
    ('U\\+((%s)|(%s){1,6}-(%s){1,6})' % (_m_range, _m_h, _m_h,), token_func (Tokens.UNICODE_RANGE),),
    ('<!--', '',),
    ('-->', '',),
    (';', token_func (Tokens.SEMICOLON),),
    (':', token_func (Tokens.COLON),),
    (',', token_func (Tokens.COMMA),),
    ('\\{', token_func (Tokens.LBRACE),),
    ('\\}', token_func (Tokens.RBRACE),),
    ('\\(', token_func (Tokens.LPAREN),),
    ('\\)', token_func (Tokens.RPAREN),),
    ('\\[', token_func (Tokens.LBRACKET),),
    ('\\]', token_func (Tokens.RBRACKET),),
    ('[ \t\r\n\f]+', '',),      # whitespace
    ('~=', token_func (Tokens.INCLUDES),),
    ('\\|=', token_func (Tokens.DASHMATCH),),
    ('/', token_func (Tokens.SLASH),),
    ('\\+', token_func (Tokens.PLUS),),
    ('\\*', token_func (Tokens.STAR),),
    ('-', token_func (Tokens.MINUS),),
    ('>', token_func (Tokens.GT),),
    ('=', token_func (Tokens.EQ),),
    ('\\.', token_func (Tokens.DOT),),
    ('.', '',),                 # delimiter
    ]

# "Bug fix" class
class Lexer (yappy.parser.Lexer):
    
    def scanOneRule(self,rule,st):
        re = rule[0]
        fun = rule[1]
        if isinstance(st, types.StringType) or isinstance (st, types.UnicodeType):
            if st == "": return st
            m = re.search(st)
            if not m: return st
            else:
                if m.start() == 0: left = ""
                else: left = st[0:m.start()]
                if m.end() == len(st): right = ""
                else: right = st[m.end():]
                if fun == "":
                      return ("",left, self.scanOneRule(rule,right))
                return (apply(fun,[st[m.start():m.end()]]),left,
                        self.scanOneRule(rule,right))
        else:
            (match, left, right) = st
            return (match, self.scanOneRule(rule,left),
                    self.scanOneRule(rule,right))

# Parser

first_error = True
def ignore_errors (function):
    def f (list, context):
        global first_error
        try:
            return function (list, context)
        except Exception, e:
            if first_error:
                import traceback
                traceback.print_exc ()
                first_error = False
            return []
    return f

def default_semantic_rule (list, context):
    return list

def fixed_value_srule (value):
    def srule (list, context):
        return value
    return srule

def nth_value_srule (n):
    def srule (list, context):
        return list[n]
    return srule

def cons_srule (car=0, cdr=1, ignore_none=False):
    def srule (list, context):
        car_, cdr_ = list[car], list[cdr]
        if ignore_none and car_ is None:
            result = cdr_
        else:
            result = [car_] + cdr_
        return result
    return ignore_errors (srule)

def apply_srule (function, *args):
    def srule (list, context):
        def nth (n):
            if type (n) == type (0):
                result = list[n]
            else:
                result = n
            return result
        return function (*map (nth, args))
    return ignore_errors (srule)

def import_semantic_rule (list, context):
    url = list[1]
    media = list[2]
    loc = context['location']
    if loc:
        import_location = loc.make_location (url)
    else:
        import_location = location.Location (url)
    stylesheet = parse (import_location)
    stylesheet.restrict_to_media (media)
    return stylesheet
import_semantic_rule = ignore_errors (import_semantic_rule)

def simple_statement_semantic_rule (list, context):
    rule = list[0]
    return Media_Rules (rules=[rule])
simple_statement_semantic_rule = ignore_errors (simple_statement_semantic_rule)

def media_semantic_rule (list, context):
    media = list[1]
    rules = list[3]
    return Media_Rules (media=media, rule=rules)
media_semantic_rule = ignore_errors (media_semantic_rule)

def ruleset_semantic_rule (list, context):
    selectors = list[0]
    declarations = list[2]
    return Rule (selector=selector_set (*selectors), properties=declarations)
ruleset_semantic_rule = ignore_errors (ruleset_semantic_rule)

def declaration_semantic_rule (list, context):
    name = list[0]
    value = list[2]
    important = list[3]
    return [Property (name=name, value=value, important=important)]
declaration_semantic_rule = ignore_errors (declaration_semantic_rule)

def selector_semantic_rule (list, context):
    selector1, combinator, selector2 = list
    return combinator (selector1, selector2)
selector_semantic_rule = ignore_errors (selector_semantic_rule)

def pseudo_semantic_rule (list, context):
    return Pseudo_Selector (list[0], (list[1],))
pseudo_selector = ignore_errors (pseudo_semantic_rule)

def attrib_semantic_rule (list, context):
    ident = list[1]
    op, value = list[2]
    return Attribute_Selector (ident, op, value)
attrib_semantic_rule = ignore_errors (attrib_semantic_rule)

def expr_semantic_rule (list, context):
    term, operator, expr = list
    return [operator, term, expr]
expr_semantic_rule = ignore_errors (expr_semantic_rule)

grammar = [
    ('stylesheet', ['charset', 'import+statement'], nth_value_srule (1),),
    ('stylesheet', ['import+statement'], nth_value_srule (0),),
    ('charset', [Tokens.CHARSET_SYM, Tokens.STRING, Tokens.SEMICOLON], default_semantic_rule,),
    ('import+statement', ['import', 'import+statement'], apply_srule (merge_stylesheets, 0, 1),),
    ('import+statement', ['statement*'], apply_srule (Stylesheet, 0),),
    ('import', [Tokens.IMPORT_SYM, 'string/uri', 'medium-list?', Tokens.SEMICOLON], import_semantic_rule,),
    ('string/uri', [Tokens.STRING], nth_value_srule (0),),
    ('string/uri', [Tokens.URI], nth_value_srule (0),),
    ('medium-list?', ['medium-list'], nth_value_srule (0),),
    ('medium-list?', [], fixed_value_srule ([]),),
    ('medium-list', ['medium', Tokens.COMMA, 'medium-list'], cons_srule (0, 2),),
    ('medium-list', ['medium'], nth_value_srule (0),),
    ('medium', [Tokens.IDENT], nth_value_srule (0),),
    ('statement*', ['statement', 'statement*'], cons_srule (ignore_none=True),),
    ('statement*', [], fixed_value_srule ([]),),
    ('statement', ['ruleset'], simple_statement_semantic_rule,),
    ('statement', ['media'], nth_value_srule (0),),
    ('statement', ['page'], fixed_value_srule (None),),
    ('statement', ['font-face'], fixed_value_srule (None),),
    ('media', [Tokens.MEDIA_SYM, 'medium-list', Tokens.LBRACE, 'ruleset*', Tokens.RBRACE], media_semantic_rule,),
    ('ruleset*', ['ruleset', 'ruleset*'], cons_srule (),),
    ('ruleset*', [], fixed_value_srule ([]),),
    ('page', [Tokens.PAGE_SYM, 'ident?', 'pseudo-page?', Tokens.LBRACE, 'declaration-list', Tokens.RBRACE],
     default_semantic_rule,),
    ('ident?', [Tokens.IDENT], default_semantic_rule,),
    ('ident?', [], default_semantic_rule,),
    ('pseudo-page?', [Tokens.COLON, Tokens.IDENT], default_semantic_rule,),
    ('pseudo-page?', [], default_semantic_rule,),
    ('font-face', [Tokens.FONT_FACE_SYM, Tokens.LBRACE, 'declaration-list', Tokens.RBRACE], default_semantic_rule,),
    ('ruleset', ['selector-list', Tokens.LBRACE, 'declaration-list', Tokens.RBRACE], ruleset_semantic_rule,),
    ('selector-list', ['selector', Tokens.COMMA, 'selector-list'], cons_srule (0, 2),),
    ('selector-list', ['selector'], default_semantic_rule,),
    ('selector', ['simple-selector', 'combinator', 'selector'], selector_semantic_rule,),
    ('selector', ['simple-selector'], nth_value_srule (0),),
    ('combinator', [Tokens.PLUS], fixed_value_srule (Neighbor_Selector),),
    ('combinator', [Tokens.GT], fixed_value_srule (Parent_Selector),),
    ('combinator', [], fixed_value_srule (Predecessor_Selector),),
    ('simple-selector', ['element-name', 'selector-spec+'], apply_srule (selector_set, 0, 1),),
    ('simple-selector', ['element-name'], nth_value_srule (0),),
    ('simple-selector', ['selector-spec+'], nth_value_srule (0),),
    ('selector-spec+', ['selector-spec', 'selector-spec+'], apply_srule (selector_set, 0, 1),),
    ('selector-spec+', ['selector-spec'], nth_value_srule (0),),
    ('selector-spec', [Tokens.HASH], apply_srule (Attribute_Selector, 'id', Attribute_Selector.EQUAL_OP, 0),),
    ('selector-spec', ['class'], nth_value_srule (0),),
    ('selector-spec', ['attrib'], nth_value_srule (0),),
    ('selector-spec', ['pseudo'], nth_value_srule (0),),
    ('element-name', [Tokens.IDENT], apply_srule (Simple_Node_Selector, 0),),
    ('element-name', [Tokens.STAR], apply_srule (Universal_Selector),),
    ('class', [Tokens.DOT, Tokens.IDENT],
     apply_srule (Attribute_Selector, 'class', Attribute_Selector.EQUAL_OP, 1),),
    ('pseudo', [Tokens.COLON, 'pseudo-spec'], nth_value_srule (1),),
    ('pseudo-spec', [Tokens.IDENT], apply_srule (Pseudo_Selector, 0)),
    ('pseudo-spec', [Tokens.FUNCTION, Tokens.IDENT, Tokens.LPAREN], pseudo_semantic_rule,),
    ('attrib', [Tokens.LBRACKET, Tokens.IDENT, 'attrib-spec', Tokens.RBRACKET], attrib_semantic_rule,),
    ('attrib-spec', ['relop', 'ident/string'], default_semantic_rule,),
    ('attrib-spec', [], fixed_value_srule ([Attribute_Selector.NONE_OP, None]),),
    ('relop', [Tokens.EQ], fixed_value_srule (Attribute_Selector.EQUAL_OP),),
    ('relop', [Tokens.INCLUDES], fixed_value_srule (Attribute_Selector.SPACE_LIST_OP),),
    ('relop', [Tokens.DASHMATCH], fixed_value_srule (Attribute_Selector.COMMA_LIST_OP),),
    ('ident/string', [Tokens.IDENT], nth_value_srule (0),),
    ('ident/string', [Tokens.STRING], nth_value_srule (0),),
    ('declaration-list', ['declaration', Tokens.SEMICOLON, 'declaration-list'],
     apply_srule (util.concatenate, 0, 2),),
    ('declaration-list', ['declaration'], nth_value_srule (0),),
    ('declaration', ['property', Tokens.COLON, 'expr', 'prio?'], declaration_semantic_rule,),
    ('declaration', [], fixed_value_srule ([]),),
    ('property', [Tokens.IDENT], nth_value_srule (0),),
    ('prio?', [Tokens.IMPORTANT_SYM], fixed_value_srule (True),),
    ('prio?', [], fixed_value_srule (False),),
    ('expr', ['term', 'operator', 'expr'], expr_semantic_rule,),
    ('expr', ['term'], nth_value_srule (0),),
    ('term', ['unary-operator', 'number-like'], default_semantic_rule,),
    ('term', ['number-like'], nth_value_srule (0),),
    ('term', [Tokens.STRING], nth_value_srule (0),),
    ('term', [Tokens.IDENT], nth_value_srule (0),),
    ('term', [Tokens.URI], nth_value_srule (0),),
    ('term', [Tokens.UNICODE_RANGE], nth_value_srule (0),),
    ('term', ['hexcolor'], nth_value_srule (0),),
    ('number-like', [Tokens.NUMBER], nth_value_srule (0),),
    ('number-like', [Tokens.PERCENTAGE], nth_value_srule (0),),
    ('number-like', [Tokens.DIMENSION], nth_value_srule (0),),
    ('number-like', ['function'], nth_value_srule (0),),
    ('function', [Tokens.FUNCTION, 'expr', Tokens.RPAREN], default_semantic_rule,),
    ('hexcolor', [Tokens.HASH], nth_value_srule (0),),
    ('operator', [Tokens.SLASH], nth_value_srule (0),),
    ('operator', [Tokens.COMMA], nth_value_srule (0),),
    ('operator', [], fixed_value_srule (' '),),
    ('unary-operator', [Tokens.PLUS], nth_value_srule (0),),
    ('unary-operator', [Tokens.MINUS], nth_value_srule (0),),
    ]

class Grammar (object):

    def __init__ (self, name, grammar, root):
        self._name = name
        top_rule = ('Root', [root], nth_value_srule (0),)
        stripped_grammar = grammar
        while stripped_grammar and stripped_grammar[0][0] != root:
            stripped_grammar = stripped_grammar[1:]
        self._grammar = [top_rule] + stripped_grammar

    def grammar (self):
        return self._grammar

    def cache_file_name (self):
        return os.path.join (config.cache_directory, 'grammar.%s' % (self._name,))

standard_grammar = Grammar ('standard', grammar, 'stylesheet')

properties_grammar = Grammar ('properties', grammar, 'declaration-list')

def parse_stream (stream, location=None, use_parser_cache=True, grammar=standard_grammar):
    try:
        #yappy.parser._DEBUG = 1
        lexer = Lexer (tokens)
        parser = yappy.parser.LRparser (grammar.grammar (), grammar.cache_file_name (),
                                        util.if_ (use_parser_cache, 1, 0), yappy.parser.LALRtable)
        text = util.read_stream (stream)
        token_list = lexer.scan (text)
        first_error = True
        result = parser.parsing (token_list, context={'location': location})
    except yappy.parser.LRParserError, e:
        result = str (e)
    return result

def parse (location, use_parser_cache=True):
    return parse_stream (location.open (), location=location, use_parser_cache=use_parser_cache)

