"""Get object in vicinity of given coords"""

# Set target objects here, this is for Red Dots where we use the GJ names for convenience

Target_objects = ('GJ551', 'GJ699', 'GJ729')


def get_vicinity(dbcurs, radeg, decdeg, margin=0.5):
    """Get the object in the target group nearest to the given coords within the given
    margin (in degrees)"""

    dbcurs.execute("SELECT objname,radeg,decdeg FROM objdata WHERE " + " OR ".join(["objname=" + dbcurs.connection.escape(m) for m in Target_objects]))
    objpos = complex(radeg, decdeg)
    mind = 1e50
    vicinity = None
    for nam, ra, dec in dbcurs.fetchall():
        d = abs(complex(ra, dec) - objpos)
        if d < mind:
            mind = d
            vicinity = nam
    if mind > margin:
        return None
    return vicinity
