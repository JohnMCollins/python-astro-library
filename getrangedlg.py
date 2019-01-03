# @Author: John M Collins <jmc>
# @Date:   2019-01-03T21:01:27+00:00
# @Email:  jmc@toad.me.uk
# @Filename: getrangedlg.py
# @Last modified by:   jmc
# @Last modified time: 2019-01-03T22:28:35+00:00

# Manage parameters dialog

from PyQt4.QtCore import *
from PyQt4.QtGui import *
import string
import os
import os.path
import math
import copy

import numpy as np
import matplotlib.pyplot as plt
import ui_getrangedlg
import calcticks

def rangeadj(lobox, hibox, loadj, hiadj):
    """Adjust range limit spin boxes by given adjustments

    Don't do anything if the result would make the low value >= high value or either below minimum
    or maximum"""

    lomin = lobox.minimum()
    himax = hibox.maximum()
    loval = lobox.value()
    hival = hibox.value()
    nlo = loval + loadj
    nhi = hival + hiadj
    if  nlo < lomin or nhi > himax or nlo >= nhi: return
    if  nlo != loval: lobox.setValue(nlo)
    if  nhi != hival: hibox.setValue(nhi)

class Getrangedlg(QDialog, ui_getrangedlg.Ui_getrangedlg):

    def __init__(self, parent = None, width = 15, height = 10):
        super(Getrangedlg, self).__init__(parent)
        self.already = False
        self.filelist = []
        self.xcol = 0
        self.ycol = 1
        self.setupUi(self)
        self.colour = QColor(0,0,0)
        self.colourdisp.setScene(QGraphicsScene())
        self.colourdisp.scene().setForegroundBrush(self.colour)
        self.colourdisp.show()
        plt.rcParams['figure.figsize'] = (width, height)
        self.width = width
        self.height = height
        self.xtit = None
        self.ytit = None
        self.hangon = False

    def copyin_range(self, x_range = None, s_range = None):
        """Copy in ranges from parameters at start"""
        if x_range is not None and x_range[0] < x_range[1]:
            self.xrangemin.setValue(x_range[0])
            self.xrangemax.setValue(x_range[1])
            self.selectx.setChecked(True)
        if s_range is not None and s_range[0] < s_range[1]:
            self.srmin.setValue(s_range[0])
            self.srmax.setValue(s_range[1])

    def copyout_ranges(self):
        """Copy back the changed ranges"""
        return ((self.xrangemin.value(), self.xrangemax.value()), (self.srmin.value(), self.srmax.value()))

    def set_filelist(self, flist):
        """Set up file list"""
        self.filelist = flist
        for n, fnam in enumerate(flist):
            nbits = string.split(fnam, '.')
            if len(nbits) > 1: nbits.pop()
            item = QListWidgetItem('.'.join(nbits))
            item.setData(Qt.UserRole, QVariant(n))
            self.datafiles.addItem(item)

    def set_columns(self, xcolumn = 0, ycolumn = 1):
        """Set columns in data for x and y values"""
        self.xcol = xcolumn
        self.ycol = ycolumn

    def set_titles(self, xtitle = None, ytitle = None):
        """Set titles for plot"""
        self.xtit = xtitle
        self.ytit = ytitle

    def updateplot(self):
        """Revise plot when anything changes"""

        # Clear any existing plot

        if  self.already:
            plt.clf()

        # Find which files have been selected, go home if none

        selected = [ p.data(Qt.UserRole).toInt()[0] for p in self.datafiles.selectedItems() ]
        if len(selected) == 0: return

        if self.selectx.isChecked():
            minx = self.xrangemin.value()
            maxx = self.xrangemax.value()
            plt.xlim(minx, maxx)
            xt, xtl = calcticks.calcticks(self.width, minx, maxx)
            plt.xticks(xt, xtl)

        ymin = 1e9
        ymax = -1e9

        legends = []
        plots = []

        for sf in [self.filelist[n] for n in selected]:
            try:
                sp = np.loadtxt(sf, unpack=True)
                wavelengths = sp[self.xcol]
                amps = sp[self.ycol]
            except IOError, ValueError:
                continue
            bits = string.split(sf, '.')
            legends.append(bits[0])
            ymin = min(ymin, np.min(amps))
            ymax = max(ymax, np.max(amps))
            plots.append((wavelengths, amps))

        ymin *= .95
        ymax *= 1.05
        plt.ylim(ymin, ymax)

        if len(legends) > 5:
            legends = legends[0:5]
            legends.append("etc...")

        col = "#%.2x%.2x%.2x" % (self.colour.red(), self.colour.green(), self.colour.blue())
        plt.axvline(x=self.srmin.value(), color=col)
        plt.axvline(x=self.srmax.value(), color=col)

        for pl in plots:
            wavelengths, amps = pl
            plt.plot(wavelengths, amps)

        if self.xtit is not None: plt.xlabel(self.xtit)
        if self.ytit is not None: plt.ylabel(self.ytit)
        plt.legend(legends, loc='upper left')

        plt.show()
        self.already = True

    def getxamounts(self):
        """Get adjustments for X range"""
        amt = float(self.adjby.currentText())
        lamt = amt
        ramt = -amt
        if self.zoomout.isChecked():
            lamt = -amt
            ramt = amt
        if self.zleft.isChecked():
            ramt = 0.0
        elif self.zright.isChecked():
            lamt = 0.0
        return (lamt, ramt)

    def on_xrangemin_valueChanged(self, value):
        if isinstance(value, QString): return
        self.updateplot()

    def on_xrangemax_valueChanged(self, value):
        if isinstance(value, QString): return
        self.updateplot()

    def on_selectx_stateChanged(self, b = None):
        if b is None: return
        self.updateplot()

    def on_adjustx_clicked(self, b = None):
        if b is None: return
        amt = float(self.adjby.currentText())
        lamt = amt
        ramt = -amt
        if self.zoomout.isChecked():
            lamt = -amt
            ramt = amt
        if self.zleft.isChecked():
            ramt = 0.0
        elif self.zright.isChecked():
            lamt = 0.0
        rangeadj(self.xrangemin, self.xrangemax, lamt, ramt)

    def on_adjrange_clicked(self, b = None):
        if b is None: return
        amt = float(self.radjby.currentText())
        lamt = amt
        ramt = -amt
        if self.rzoomout.isChecked():
            lamt = -amt
            ramt = amt
        if self.rzleft.isChecked():
            ramt = 0.0
        elif self.rzright.isChecked():
            lamt = 0.0
        rangeadj(self.srmin, self.srmax, lamt, ramt)

    def on_selcolour_clicked(self, b = None):
        if b is None: return
        nc = QColorDialog.getColor(self.colour, self, "Select new colour")
        if not nc.isValid(): return
        self.colour = nc
        self.colourdisp.scene().setForegroundBrush(nc)
        self.updateplot()

    def on_srmin_valueChanged(self, value):
        self.updateplot()

    def on_srmax_valueChanged(self, value):
        self.updateplot()

    def on_datafiles_itemSelectionChanged(self):
        if self.hangon: return
        self.updateplot()

    def on_selectall_clicked(self, b = None):
        if b is None: return
        self.hangon = True
        for row in xrange(0, self.datafiles.count()):
            self.datafiles.item(row).setSelected(True)
        self.hangon = False
        self.updateplot()
