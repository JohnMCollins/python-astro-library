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
            item = QListWidgetItem(string.join(nbits, '.'))
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
 
    def on_xrangemin_valueChanged(self, value):
        if isinstance(value, QString): return
        self.updateplot()

    def on_xrangemax_valueChanged(self, value):
        if isinstance(value, QString): return
        self.updateplot()

    def on_selectx_stateChanged(self, b = None):
        if b is None: return
        self.updateplot()

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

    def incdec_range(self, b, lfld, ufld, lamt, uamt):
        if b is None: return
        clval = lfld.value()
        cuval = ufld.value()
        nlval = clval + lamt
        nuval = cuval + uamt
        if nlval >= nuval:  return
        if nlval < lfld.minimum(): nlval = lfld.minimum()
        if nuval > ufld.maximum(): nuval = ufld.maximum()
        if nlval != clval: lfld.setValue(nlval)
        if nuval != cuval: ufld.setValue(nuval)

    def on_datafiles_itemSelectionChanged(self):
        self.updateplot()
 
    def on_rlp1_clicked(self, b = None): self.incdec_range(b, self.xrangemin, self.xrangemax, 1.0, 0.0)
    def on_rlp5_clicked(self, b = None): self.incdec_range(b, self.xrangemin, self.xrangemax, 5.0, 0.0)
    def on_rlpp1_clicked(self, b = None): self.incdec_range(b, self.xrangemin, self.xrangemax, 0.1, 0.0)
    def on_rlpp5_clicked(self, b = None): self.incdec_range(b, self.xrangemin, self.xrangemax, 0.5, 0.0)
    def on_rlmp1_clicked(self, b = None): self.incdec_range(b, self.xrangemin, self.xrangemax, -0.1, 0.0)
    def on_rlmp5_clicked(self, b = None): self.incdec_range(b, self.xrangemin, self.xrangemax, -0.5, 0.0)
    def on_rlm1_clicked(self, b = None): self.incdec_range(b, self.xrangemin, self.xrangemax, -1.0, 0.0)
    def on_rlm5_clicked(self, b = None): self.incdec_range(b, self.xrangemin, self.xrangemax, -5.0, 0.0)

    def on_rup1_clicked(self, b = None): self.incdec_range(b, self.xrangemin, self.xrangemax, 0.0, 1.0)
    def on_rup5_clicked(self, b = None): self.incdec_range(b, self.xrangemin, self.xrangemax, 0.0, 5.0)
    def on_rupp1_clicked(self, b = None): self.incdec_range(b, self.xrangemin, self.xrangemax, 0.0, 0.1)
    def on_rupp5_clicked(self, b = None): self.incdec_range(b, self.xrangemin, self.xrangemax, 0.0, 0.5)
    def on_rump1_clicked(self, b = None): self.incdec_range(b, self.xrangemin, self.xrangemax, 0.0, -0.1)
    def on_rump5_clicked(self, b = None): self.incdec_range(b, self.xrangemin, self.xrangemax, 0.0, -0.5)
    def on_rum1_clicked(self, b = None): self.incdec_range(b, self.xrangemin, self.xrangemax, 0.0, -1.0)
    def on_rum5_clicked(self, b = None): self.incdec_range(b, self.xrangemin, self.xrangemax, 0.0, -5.0)

    def on_rbp1_clicked(self, b = None): self.incdec_range(b, self.xrangemin, self.xrangemax, 1.0, -1.0)
    def on_rbp5_clicked(self, b = None): self.incdec_range(b, self.xrangemin, self.xrangemax, 5.0, -5.0)
    def on_rbpp1_clicked(self, b = None): self.incdec_range(b, self.xrangemin, self.xrangemax, 0.1, -0.1)
    def on_rbpp5_clicked(self, b = None): self.incdec_range(b, self.xrangemin, self.xrangemax, 0.5, -0.5)
    def on_rbmp1_clicked(self, b = None): self.incdec_range(b, self.xrangemin, self.xrangemax, -0.1, 1.0)
    def on_rbmp5_clicked(self, b = None): self.incdec_range(b, self.xrangemin, self.xrangemax, -0.5, 0.5)
    def on_rbm1_clicked(self, b = None): self.incdec_range(b, self.xrangemin, self.xrangemax, -1.0, 1.0)
    def on_rbm5_clicked(self, b = None): self.incdec_range(b, self.xrangemin, self.xrangemax, -5.0, 5.0)

    def on_srlp1_clicked(self, b = None): self.incdec_range(b, self.srmin, self.srmax, 1.0, 0.0)
    def on_srlp5_clicked(self, b = None): self.incdec_range(b, self.srmin, self.srmax, 5.0, 0.0)
    def on_srlpp1_clicked(self, b = None): self.incdec_range(b, self.srmin, self.srmax, 0.1, 0.0)
    def on_srlpp5_clicked(self, b = None): self.incdec_range(b, self.srmin, self.srmax, 0.5, 0.0)
    def on_srlmp1_clicked(self, b = None): self.incdec_range(b, self.srmin, self.srmax, -0.1, 0.0)
    def on_srlmp5_clicked(self, b = None): self.incdec_range(b, self.srmin, self.srmax, -0.5, 0.0)
    def on_srlm1_clicked(self, b = None): self.incdec_range(b, self.srmin, self.srmax, -1.0, 0.0)
    def on_srlm5_clicked(self, b = None): self.incdec_range(b, self.srmin, self.srmax, -5.0, 0.0)

    def on_srup1_clicked(self, b = None): self.incdec_range(b, self.srmin, self.srmax, 0.0, 1.0)
    def on_srup5_clicked(self, b = None): self.incdec_range(b, self.srmin, self.srmax, 0.0, 5.0)
    def on_srupp1_clicked(self, b = None): self.incdec_range(b, self.srmin, self.srmax, 0.0, 0.1)
    def on_srupp5_clicked(self, b = None): self.incdec_range(b, self.srmin, self.srmax, 0.0, 0.5)
    def on_srump1_clicked(self, b = None): self.incdec_range(b, self.srmin, self.srmax, 0.0, -0.1)
    def on_srump5_clicked(self, b = None): self.incdec_range(b, self.srmin, self.srmax, 0.0, -0.5)
    def on_srum1_clicked(self, b = None): self.incdec_range(b, self.srmin, self.srmax, 0.0, -1.0)
    def on_srum5_clicked(self, b = None): self.incdec_range(b, self.srmin, self.srmax, 0.0, -5.0)

    def on_srbp1_clicked(self, b = None): self.incdec_range(b, self.srmin, self.srmax, 1.0, -1.0)
    def on_srbp5_clicked(self, b = None): self.incdec_range(b, self.srmin, self.srmax, 5.0, -5.0)
    def on_srbpp1_clicked(self, b = None): self.incdec_range(b, self.srmin, self.srmax, 0.1, -0.1)
    def on_srbpp5_clicked(self, b = None): self.incdec_range(b, self.srmin, self.srmax, 0.5, -0.5)
    def on_srbmp1_clicked(self, b = None): self.incdec_range(b, self.srmin, self.srmax, -0.1, 0.1)
    def on_srbmp5_clicked(self, b = None): self.incdec_range(b, self.srmin, self.srmax, -0.5, 0.5)
    def on_srbm1_clicked(self, b = None): self.incdec_range(b, self.srmin, self.srmax, -1.0, 1.0)
    def on_srbm5_clicked(self, b = None): self.incdec_range(b, self.srmin, self.srmax, -5.0, 5.0)

