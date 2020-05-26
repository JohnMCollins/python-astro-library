#
# Generated Makefile for PyQt interfaces
#
# Created on Fri Oct 24 15:25:02 2014

all:	ui_choosenum.py\
	ui_choosefloat.py\
	ui_getrangedlg.py\
	ui_choosestring.py\
	ui_chooseopt.py

ui_choosenum.py:	choosenum.ui
	pyuic4 -o $@ $?

ui_choosefloat.py:	choosefloat.ui
	pyuic4 -o $@ $?

ui_getrangedlg.py:	getrangedlg.ui
	pyuic4 -o $@ $?

ui_choosestring.py:	choosestring.ui
	pyuic4 -o $@ $?

ui_chooseopt.py:	chooseopt.ui
	pyuic4 -o $@ $?

clean:
	rm -f ui_*.py *_rc.py *.pyc

distclean: clean
	rm -f config.py
