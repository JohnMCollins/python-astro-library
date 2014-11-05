# Save options in home control file for later recovery

import os
import os.path
import sys
import re
import string
import xmlutil

class ConfigError(Exception):
  pass

HOMED_CONFIG_DIR = "~/.jmc"

def check_homed_configdir():
    """Check that we've got the tools config save options handy

    In any case return the expanded directory"""

    name = os.path.expanduser(HOMED_CONFIG_DIR)
    if not os.path.isdir(name):
        try:
            os.mkdir(name)
        except OSError:
            raise ConfigError("Cannot create config file directory " + name)
    return  name   

def get_full_config_path(fname):
    """Get full path for config file"""
    # NB if fname is a full path the home conffigdir is ignored
    return  os.path.join(check_homed_configdir(), fname)

def get_progname():
    """Get base part of program name and strip any suffices"""
    progname = sys.argv[0]
    if len(progname) == 0:
        raise ConfigError("No programe name available")
    progname = os.path.basename(progname)
    mtch = re.match('(\w+)', progname)
    if not mtch:
        raise ConfigError("Cannot convert prog name " + progname)
    return mtch.group(0)

def get_rootname(rootname = None):
    """Get root name for document"""
    if rootname is None:
        return string.upper(get_progname())
    return rootname

def get_filename(fname = None):
    if fname is None:
        fname = string.lower(get_progname())
    return get_full_config_path(fname)

def load(fname = None, rootname = None):
    """Load config file, checking that the root document is correct.
    
    If either are null, get the file name and root doc name from program name"""
    
    fname = get_filename(fname)
    
    # No error if not there
    
    if not os.path.isfile(fname): return None
    
    try:
        return  xmlutil.load_file(fname, get_rootname(rootname))
    except xmlutil.XMLError as e:
        raise ConfigError(e.args[0])

def init_save(rootname = None):
    """Start of save operation, get document and root"""
    rootname = get_rootname(rootname)
    return  xmlutil.init_save(rootname, rootname)

def complete_save(doc, fname = None):
    """Complete save operation
    
    NB args other way round from XMLUTIL"""
    try:
        xmlutil.complete_save(get_filename(fname), doc)
    except xmlutil.XMLError as e:
        raise ConfigError(e.args[0])
