# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'chooseopt.ui'
#
# Created: Wed May 28 15:31:06 2014
#      by: PyQt4 UI code generator 4.6.2
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_chooseopt(object):
    def setupUi(self, chooseopt):
        chooseopt.setObjectName("chooseopt")
        chooseopt.resize(683, 280)
        self.buttonBox = QtGui.QDialogButtonBox(chooseopt)
        self.buttonBox.setGeometry(QtCore.QRect(280, 200, 341, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.description = QtGui.QLabel(chooseopt)
        self.description.setGeometry(QtCore.QRect(40, 40, 571, 17))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.description.setFont(font)
        self.description.setObjectName("description")
        self.optlist = QtGui.QComboBox(chooseopt)
        self.optlist.setGeometry(QtCore.QRect(60, 110, 531, 27))
        self.optlist.setObjectName("optlist")

        self.retranslateUi(chooseopt)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), chooseopt.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), chooseopt.reject)
        QtCore.QMetaObject.connectSlotsByName(chooseopt)

    def retranslateUi(self, chooseopt):
        chooseopt.setWindowTitle(QtGui.QApplication.translate("chooseopt", "Choose option", None, QtGui.QApplication.UnicodeUTF8))
        self.description.setText(QtGui.QApplication.translate("chooseopt", "aaa", None, QtGui.QApplication.UnicodeUTF8))
        self.optlist.setToolTip(QtGui.QApplication.translate("chooseopt", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Sans\'; font-size:10pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">This is the option to be selected.</p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Scroll to the one required and click <span style=\" font-weight:600;\">OK</span>.</p></body></html>", None, QtGui.QApplication.UnicodeUTF8))

