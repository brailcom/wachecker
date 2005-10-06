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

MAKEINFO := makeinfo

program := wachecker

all: info

info: $(program).info
%.info: %.texi
	$(MAKEINFO) $<

pdf: $(program).pdf
%.pdf: %.texi
	texi2pdf $<

html: html/index.html
html/index.html: $(program).texi
	$(MAKEINFO) --html -o html $<

clean:
	-rm -f *.aux *.cp *.cps *.fn *.ky *.log *.pg *.toc *.tp *.vr

distclean: clean

maintainer-clean: distclean
	-rm -f *.info *.pdf
	-rm -rf html
