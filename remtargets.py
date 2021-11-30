# Create selection list for targets


def remtargets(dbcursor, selectlist):
    """Fill selectlist array with field selections to get REM targets,
    Probably joined by OR but allow for adding other things"""
    
    conn = dbcursor.connection
    selectlist.append("object REGEXP " + conn.escape("Proxima"))
    selectlist.append("object=" + conn.escape("BarnardStar"))
    selectlist.append("object=" + conn.escape("Ross154"))
