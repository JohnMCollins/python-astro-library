# XML Utility functions

import xml.etree.ElementTree as ET

class XMLError(Exception):
    """Throw these errors if we get some value etc error"""
    pass

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

def savedata(doc, pnode, name, value):
    """Encode something to an XML file"""
    subnode = ET.SubElement(pnode, name)
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

def load_file(filename, rootname):
    """Load XML DOM document from file"""
    try:
        doc = ET.parse(filename)
    except IOError as e:
        raise XMLError("IO error on " + filename + " - " + e.args[1])
    except ET.ParseError as e:
        raise XMLError("Parse error on " + filename + " - " + e.args[0])
    root = doc.getroot()
    if root.tag != rootname:
        raise XMLError("Unexpected document type read '" + root.tag + "' expected '" + rootname + "'")
    return (doc, root)

def init_save(docname, rootname):
    """Create XML DOM document ready to save"""
    root = ET.Element(rootname)
    doc = ET.ElementTree(root)
    return (doc, root)

def complete_save(filename, doc):
    """Complete save operation by writing document to filename"""
    fh = None
    try:
        fh = open(filename, 'w')
        doc.write(fh)
        fh.write("\n")
    except IOError as e:
        raise XMLError("IO error on " + filename + " - " + e.args[0])
    finally:
        if fh is not None:
            fh.close()

