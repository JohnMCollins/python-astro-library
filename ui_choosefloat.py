# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'choosefloat.ui'
#
# Created: Wed May 28 15:31:06 2014
#      by: PyQt4 UI code generator 4.6.2
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_choosefloat(object):
    def setupUi(self, choosefloat):
        choosefloat.setObjectName("choosefloat")
        choosefloat.resize(400, 245)
        self.buttonBox = QtGui.QDialogButtonBox(choosefloat)
        self.buttonBox.setGeometry(QtCore.QRect(170, 180, 201, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.description = QtGui.QLabel(choosefloat)
        self.description.setGeometry(QtCore.QRect(20, 40, 341, 17))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.description.setFont(font)
        self.description.setObjectName("description")
        self.chooseval = QtGui.QLineEdit(choosefloat)
        self.chooseval.setGeometry(QtCore.QRect(20, 80, 341, 27))
        self.chooseval.setObjectName("chooseval")
        self.minus1pc = QtGui.QPushButton(choosefloat)
        self.minus1pc.setGeometry(QtCore.QRect(130, 130, 61, 27))
        self.minus1pc.setObjectName("minus1pc")
        self.plus1pc = QtGui.QPushButton(choosefloat)
        self.plus1pc.setGeometry(QtCore.QRect(200, 130, 61, 27))
        self.plus1pc.setObjectName("plus1pc")
        self.minus10pc = QtGui.QPushButton(choosefloat)
        self.minus10pc.setGeometry(QtCore.QRect(60, 130, 61, 27))
        self.minus10pc.setObjectName("minus10pc")
        self.plus10pc = QtGui.QPushButton(choosefloat)
        self.plus10pc.setGeometry(QtCore.QRect(270, 130, 61, 27))
        self.plus10pc.setObjectName("plus10pc")

        self.retranslateUi(choosefloat)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), choosefloat.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), choosefloat.reject)
        QtCore.QMetaObject.connectSlotsByName(choosefloat)
        choosefloat.setTabOrder(self.chooseval, self.minus10pc)
        choosefloat.setTabOrder(self.minus10pc, self.minus1pc)
        choosefloat.setTabOrder(self.minus1pc, self.plus1pc)
        choosefloat.setTabOrder(self.plus1pc, self.plus10pc)
        choosefloat.setTabOrder(self.plus10pc, self.buttonBox)

    def retranslateUi(self, choosefloat):
        choosefloat.setWindowTitle(QtGui.QApplication.translate("choosefloat", "Choose number (floating-point)", None, QtGui.QApplication.UnicodeUTF8))
        self.description.setText(QtGui.QApplication.translate("choosefloat", "aaa", None, QtGui.QApplication.UnicodeUTF8))
        self.chooseval.setToolTip(QtGui.QApplication.translate("choosefloat", "Enter a floating-point number here", None, QtGui.QApplication.UnicodeUTF8))
        self.minus1pc.setToolTip(QtGui.QApplication.translate("choosefloat", "Subtracts 1% from value", None, QtGui.QApplication.UnicodeUTF8))
        self.minus1pc.setText(QtGui.QApplication.translate("choosefloat", "-1%", None, QtGui.QApplication.UnicodeUTF8))
        self.plus1pc.setToolTip(QtGui.QApplication.translate("choosefloat", "Adds 1% to value", None, QtGui.QApplication.UnicodeUTF8))
        self.plus1pc.setText(QtGui.QApplication.translate("choosefloat", "+1%", None, QtGui.QApplication.UnicodeUTF8))
        self.minus10pc.setToolTip(QtGui.QApplication.translate("choosefloat", "Subtracts 10% from value", None, QtGui.QApplication.UnicodeUTF8))
        self.minus10pc.setText(QtGui.QApplication.translate("choosefloat", "-10%", None, QtGui.QApplication.UnicodeUTF8))
        self.plus10pc.setToolTip(QtGui.QApplication.translate("choosefloat", "Adds 10% to value", None, QtGui.QApplication.UnicodeUTF8))
        self.plus10pc.setText(QtGui.QApplication.translate("choosefloat", "+10%", None, QtGui.QApplication.UnicodeUTF8))

