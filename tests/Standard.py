# -*- coding: utf-8 -*-
### Standard.py --- Test sets corresponding to public standards

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

import util


class Test_Set__WCAG_1_A (Test_Set):
    
    _name = 'WCAG 1.0 A'
    _description = 'Testing for conformance with Web Accessibility Guidelines 1.0, level Single-A.'
    _tests = (Test__WCAG_1__1_1,
              Test__WCAG_1__1_2,
              Test__WCAG_1__1_3,
              Test__WCAG_1__1_4,
              Test__WCAG_1__2_1,
              Test__WCAG_1__4_1,
              Test__WCAG_1__5_1,
              Test__WCAG_1__5_2,
              Test__WCAG_1__6_1,
              Test__WCAG_1__6_2,
              Test__WCAG_1__6_3,
              Test__WCAG_1__7_1,
              Test__WCAG_1__8_1_Important,
              Test__WCAG_1__9_1,
              Test__WCAG_1__11_4,
              Test__WCAG_1__12_1,
              Test__WCAG_1__14_1,
              )


class Test_Set__WCAG_1_AA (Test_Set):
    
    _name = 'WCAG 1.0 AA'
    _description = 'Testing for conformance with Web Accessibility Guidelines 1.0, level Double-A.'
    _tests = (util.remove (Test_Set__WCAG_1_A._tests, Test__WCAG_1__8_1_Important) +
              (Test__WCAG_1__2_2_Images,
               Test__WCAG_1__3_1,
               Test__WCAG_1__3_2,
               Test__WCAG_1__3_3,
               Test__WCAG_1__3_4,
               Test__WCAG_1__3_5,
               Test__WCAG_1__3_6,
               Test__WCAG_1__3_7,
               Test__WCAG_1__5_3,
               Test__WCAG_1__5_4,
               Test__WCAG_1__6_4,
               Test__WCAG_1__6_5,
               Test__WCAG_1__7_2,
               Test__WCAG_1__7_3,
               Test__WCAG_1__7_4,
               Test__WCAG_1__7_5,
               Test__WCAG_1__8_1,
               Test__WCAG_1__9_2,
               Test__WCAG_1__9_3,
               Test__WCAG_1__10_1,
               Test__WCAG_1__10_2,
               Test__WCAG_1__11_1,
               Test__WCAG_1__11_2,
               Test__WCAG_1__12_2,
               Test__WCAG_1__12_3,
               Test__WCAG_1__12_4,
               Test__WCAG_1__13_1,
               Test__WCAG_1__13_2,
               Test__WCAG_1__13_3,
               Test__WCAG_1__13_4,
               ))


class Test_Set__WCAG_1_AAA (Test_Set):
    
    _name = 'WCAG 1.0 AAA'
    _description = 'Testing for conformance with Web Accessibility Guidelines 1.0, level Tripple-A.'
    _tests = (Test_Set__WCAG_1_AA._tests +
              (Test__WCAG_1__1_5,
               Test__WCAG_1__2_2_Text,
               Test__WCAG_1__4_2,
               Test__WCAG_1__4_3,
               Test__WCAG_1__5_5,
               Test__WCAG_1__5_6,
               Test__WCAG_1__9_4,
               Test__WCAG_1__9_5,
               Test__WCAG_1__10_3,
               Test__WCAG_1__10_4,
               Test__WCAG_1__10_5,
               Test__WCAG_1__11_3,
               Test__WCAG_1__13_5,
               Test__WCAG_1__13_6,
               Test__WCAG_1__13_7,
               Test__WCAG_1__13_8,
               Test__WCAG_1__13_9,
               Test__WCAG_1__13_10,
               Test__WCAG_1__14_2,
               Test__WCAG_1__14_3,
               ))



class Test_Set__Section508 (Test_Set):

    _name = 'Section 508'
    _description = 'Testing for conformance with U.S. Section 508, § 1194.22.'
    _tests = (Test__508_a,
              Test__508_b,
              Test__508_c,
              Test__508_d,
              Test__508_e,
              Test__508_f,
              Test__508_g,
              Test__508_h,
              Test__508_i,
              Test__508_j,
              Test__508_k,
              Test__508_l,
              Test__508_m,
              Test__508_n,
              Test__508_o,
              Test__508_p,
              )

