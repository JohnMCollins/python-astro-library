# XML Utility functions

from PyQt4.QtCore import *
from PyQt4.QtXml import *

class XMLError(Exception):
    """Throw these errors if we get some value etc error"""
    pass

def gettext(node):
    """Extract the text child from an XML node"""
    return str(node.firstChild().toText().data())

def getint(node):
    """Extract text field from XML node and make an int out of it"""
    try:
        return int(gettext(node))
    except ValueError:
        raise XMLError("Invalid int value for " + str(node.toElement().tagName()))

def getfloat(node):
    """Extract text field from XML node and make a float out of it"""
    try:   
        return float(gettext(node))
    except ValueError:
        raise XMLError("Invalid float value for " + str(node.toElement().tagName()))

def savedata(doc, pnode, name, value):
    """Encode something to an XML file"""
    item = doc.createElement(name)
    pnode.appendChild(item)
    item.appendChild(doc.createTextNode(str(value)))

def savebool(doc, pnode, name, value):
    """Possibly encode a bool value"""
    if not value: return
    item = doc.createElement(name)
    pnode.appendChild(item)

def find_child(pnode, name):
    """Find the first top-level child node of pnode of given name"""
    child = pnode.firstChild()
    while not child.isNull():
        if child.toElement().tagName() == name: return child
        child = child.nextSibling()
    raise XMLError("Could not find element '" + name + "'")

def load_file(filename, rootname):
    """Load XML DOM document from file"""
    fh = None
    try:
        fh = QFile(filename)
        if not fh.open(QIODevice.ReadOnly):
            raise IOError(unicode(fh.errorString()))
        doc = QDomDocument()
        if not doc.setContent(fh):
            raise XMLError("Could not parse " + filename + " as XML file")
    except IOError as e:
        raise XMLError("IO error on " + filename + " - " + e.args[0])
    finally:
        if fh is not None:
            fh.close()
    root = doc.documentElement()
    if root.tagName() != rootname:
        raise XMLError("Unexpected document type read '" + root.tagName() + "' expected '" + rootname + "'")
    return (doc, root)

def init_save(docname, rootname):
    """Create XML DOM document ready to save"""
    doc = QDomDocument(docname)
    root = doc.createElement(rootname)
    doc.appendChild(root)
    return (doc, root)

def complete_save(filename, doc):
    """Complete save operation by writing document to filename"""
    xmlstr = doc.toString()
    fh = None
    try:
        fh = QFile(filename)
        if not fh.open(QIODevice.WriteOnly):
            raise IOError(unicode(fh.errorString()))
        fh.write(str(xmlstr))
    except IOError as e:
        raise XMLError("IO error writing output file -", e.args[0])
    finally:
        if fh is not None:
            fh.close()

