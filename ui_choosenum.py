# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'choosenum.ui'
#
# Created: Wed May 28 15:31:06 2014
#      by: PyQt4 UI code generator 4.6.2
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_choosenum(object):
    def setupUi(self, choosenum):
        choosenum.setObjectName("choosenum")
        choosenum.resize(400, 231)
        font = QtGui.QFont()
        font.setPointSize(10)
        choosenum.setFont(font)
        self.buttonBox = QtGui.QDialogButtonBox(choosenum)
        self.buttonBox.setGeometry(QtCore.QRect(30, 180, 341, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.description = QtGui.QLabel(choosenum)
        self.description.setGeometry(QtCore.QRect(40, 40, 341, 17))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.description.setFont(font)
        self.description.setObjectName("description")
        self.chooseval = QtGui.QDoubleSpinBox(choosenum)
        self.chooseval.setGeometry(QtCore.QRect(40, 80, 271, 27))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.chooseval.setFont(font)
        self.chooseval.setObjectName("chooseval")
        self.minus10pc = QtGui.QPushButton(choosenum)
        self.minus10pc.setGeometry(QtCore.QRect(40, 120, 61, 27))
        self.minus10pc.setObjectName("minus10pc")
        self.minus1pc = QtGui.QPushButton(choosenum)
        self.minus1pc.setGeometry(QtCore.QRect(110, 120, 61, 27))
        self.minus1pc.setObjectName("minus1pc")
        self.plus10pc = QtGui.QPushButton(choosenum)
        self.plus10pc.setGeometry(QtCore.QRect(250, 120, 61, 27))
        self.plus10pc.setObjectName("plus10pc")
        self.plus1pc = QtGui.QPushButton(choosenum)
        self.plus1pc.setGeometry(QtCore.QRect(180, 120, 61, 27))
        self.plus1pc.setObjectName("plus1pc")

        self.retranslateUi(choosenum)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), choosenum.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), choosenum.reject)
        QtCore.QMetaObject.connectSlotsByName(choosenum)
        choosenum.setTabOrder(self.chooseval, self.minus10pc)
        choosenum.setTabOrder(self.minus10pc, self.minus1pc)
        choosenum.setTabOrder(self.minus1pc, self.plus1pc)
        choosenum.setTabOrder(self.plus1pc, self.plus10pc)
        choosenum.setTabOrder(self.plus10pc, self.buttonBox)

    def retranslateUi(self, choosenum):
        choosenum.setWindowTitle(QtGui.QApplication.translate("choosenum", "Choose value", None, QtGui.QApplication.UnicodeUTF8))
        self.description.setText(QtGui.QApplication.translate("choosenum", "aaa", None, QtGui.QApplication.UnicodeUTF8))
        self.chooseval.setToolTip(QtGui.QApplication.translate("choosenum", "This is the value being requested", None, QtGui.QApplication.UnicodeUTF8))
        self.minus10pc.setToolTip(QtGui.QApplication.translate("choosenum", "Subtracts 10% from value", None, QtGui.QApplication.UnicodeUTF8))
        self.minus10pc.setText(QtGui.QApplication.translate("choosenum", "-10%", None, QtGui.QApplication.UnicodeUTF8))
        self.minus1pc.setToolTip(QtGui.QApplication.translate("choosenum", "Subtracts 1% from value", None, QtGui.QApplication.UnicodeUTF8))
        self.minus1pc.setText(QtGui.QApplication.translate("choosenum", "-1%", None, QtGui.QApplication.UnicodeUTF8))
        self.plus10pc.setToolTip(QtGui.QApplication.translate("choosenum", "Adds 10% to value", None, QtGui.QApplication.UnicodeUTF8))
        self.plus10pc.setText(QtGui.QApplication.translate("choosenum", "+10%", None, QtGui.QApplication.UnicodeUTF8))
        self.plus1pc.setToolTip(QtGui.QApplication.translate("choosenum", "Adds 1% to value", None, QtGui.QApplication.UnicodeUTF8))
        self.plus1pc.setText(QtGui.QApplication.translate("choosenum", "+1%", None, QtGui.QApplication.UnicodeUTF8))

