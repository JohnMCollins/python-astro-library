# @Author: John M Collins <jmc>
# @Date:   2019-01-03T21:01:27+00:00
# @Email:  jmc@toad.me.uk
# @Filename: xmlutil.py
# @Last modified by:   jmc
# @Last modified time: 2019-01-03T22:29:14+00:00

# XML Utility functions

import xml.etree.ElementTree as ET
import string


class XMLError(Exception):
    """Throw these errors if we get some value etc error"""

    def __init__(self, message, warningonly=False):
        super(XMLError, self).__init__(message)
        self.warningonly = warningonly


def gettext(node):
    """Extract the text child from an XML node"""
    return node.text


def getint(node):
    """Extract text field from XML node and make an int out of it"""
    try:
        return int(node.text)
    except ValueError:
        raise XMLError("Invalid int value for " + node.tag)


def getfloat(node):
    """Extract text field from XML node and make a float out of it"""
    try:
        return float(node.text)
    except ValueError:
        raise XMLError("Invalid float value for " + node.tag)


def getfloatlist(node):
    """Extract text field from XML node and make a list of floats out of it"""
    try:
        return [float(x) for x in string.split(node.text, ",")]
    except ValueError:
        raise XMLError("Invalid float list for " + node.tag)


def savedata(doc, pnode, name, value):
    """Encode something to an XML file"""
    subnode = ET.SubElement(pnode, name)
    subnode.text = str(value)
    return subnode


def savefloatlist(doc, pnode, name, value):
    """Encode a list of floats to an XML file"""
    subnode = ET.SubElement(pnode, name)
    if type(value) != 'float' and type(value) != 'int':
        subnode.text = ','.join([str(x) for x in value])
    else:
        subnode.text = str(value)
    return subnode


def setboolattr(pnode, name, value):
    """Save a boolean attribute"""
    if not value: return
    pnode.set(name, 'y')


def getboolattr(pnode, name):
    """Retreive a boolean attribute"""
    v = pnode.get(name, default=False)
    return v and v == 'y'


def savebool(doc, pnode, name, value):
    """Possibly encode a bool value"""
    if not value: return
    ET.SubElement(pnode, name)


def find_child(pnode, name):
    """Find the first top-level child node of pnode of given name"""
    child = pnode.find(name)
    if child is not None: return child
    raise XMLError("Could not find element '" + name + "'")


def load_file(filename, rootname=None):
    """Load XML DOM document from file.
    If first char of filename is a < treat as string to parse"""

    if filename[0] == '<':
        try:
            root = ET.fromstring(filename)
            return  (ET.ElementTree(root), root)
        except ET.ParseError as e:
            raise XMLError("Parse error: " + e.args[0])
    try:
        doc = ET.parse(filename)
    except IOError as e:
        if e.args[0] == 2:
            raise XMLError(message='File not found: ' + filename, warningonly=True)
        raise XMLError("IO error on " + filename + " - " + e.args[1])
    except ET.ParseError as e:
        raise XMLError("Parse error on " + filename + " - " + e.args[0])
    root = doc.getroot()
    if rootname is not None and root.tag != rootname:
        raise XMLError("Unexpected document type read '" + root.tag + "' expected '" + rootname + "'")
    return (doc, root)


def init_save(docname, rootname):
    """Create XML DOM document ready to save"""
    root = ET.Element(rootname)
    doc = ET.ElementTree(root)
    return (doc, root)


def complete_save(filename, doc):
    """Complete save operation by writing document to filename
    If filename is None, return a string"""

    if filename is None:
        return ET.tostring(doc.getroot(), encoding='utf8', method='xml')
    fh = None
    try:
        fh = open(filename, "wb")
        doc.write(fh, encoding='utf8', method='xml')
        fh.write("\n".encode())
    except IOError as e:
        raise XMLError("IO error on " + filename + " - " + e.strerror)
    finally:
        if fh is not None:
            fh.close()
    return None
