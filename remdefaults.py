# Save options in home control file for later recovery

import os
import sys

def default_database():
    """Get default database depending on what host we are on"""
    
    hostn = os.uname().nodename
    if hostn == "nancy" or hostn == "foxy" :
        return "remfits"
    if hostn == "uhhpc":
        return "cluster"
    try:
        hostn.index("herts.ac.uk")
        return "cluster"
    except ValueError:
        pass
    return "cluster"            # Temporary whilst foxy and nacncy are offline

def get_tmpdir():
    """Select an appropriate temporty directory"""
    try:
        return  os.environ["REMTMP"]
    except KeyError:
        return  os.getcwd()
