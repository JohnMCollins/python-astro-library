# Create selection list for targets


def remtargets(dbcursor, selectlist):
    """Fill selectlist array with field selections to get REM targets,
    Probably joined by OR but allow for adding other things"""

    conn = dbcursor.connection
    selectlist.append("object REGEXP " + conn.escape("Proxima"))
    selectlist.append("object=" + conn.escape("BarnardStar"))
    selectlist.append("object=" + conn.escape("Ross154"))


def notargets(objlist):
    """Report if we have already got one of the targets in the objlist"""

    for o in objlist:
        lco = o.lower()
        if lco == "barnardstar" or lco == "ross154":
            return  False
        if len(lco) > 4 and lco[0:4] == "prox":
            return  False

    return  True
