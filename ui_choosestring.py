# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'choosestring.ui'
#
# Created: Wed May 28 15:31:06 2014
#      by: PyQt4 UI code generator 4.6.2
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_choosestring(object):
    def setupUi(self, choosestring):
        choosestring.setObjectName("choosestring")
        choosestring.resize(400, 205)
        self.buttonBox = QtGui.QDialogButtonBox(choosestring)
        self.buttonBox.setGeometry(QtCore.QRect(30, 140, 341, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.chooseval = QtGui.QLineEdit(choosestring)
        self.chooseval.setGeometry(QtCore.QRect(20, 70, 341, 27))
        self.chooseval.setObjectName("chooseval")
        self.description = QtGui.QLabel(choosestring)
        self.description.setGeometry(QtCore.QRect(20, 30, 341, 17))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.description.setFont(font)
        self.description.setObjectName("description")

        self.retranslateUi(choosestring)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), choosestring.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), choosestring.reject)
        QtCore.QMetaObject.connectSlotsByName(choosestring)
        choosestring.setTabOrder(self.chooseval, self.buttonBox)

    def retranslateUi(self, choosestring):
        choosestring.setWindowTitle(QtGui.QApplication.translate("choosestring", "Specify string", None, QtGui.QApplication.UnicodeUTF8))
        self.chooseval.setToolTip(QtGui.QApplication.translate("choosestring", "Enter a string here.", None, QtGui.QApplication.UnicodeUTF8))
        self.description.setText(QtGui.QApplication.translate("choosestring", "aaa", None, QtGui.QApplication.UnicodeUTF8))

