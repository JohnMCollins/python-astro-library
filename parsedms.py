"""Parse degree minute second argument"""

import re

parsedmsre = re.compile(r'(\d+|\d*\.\d+)([dDmMsS]?)$')
dmsdiv = dict(d=1.0, D=1.0, m=60.0, M=60.0, s=3600.0, S=3600.0)


def parsedms(arg):
    """Parse string argument as number giving degrees optionally followed by d,
    or minutes, seconds followed by m or s"""

    m = parsedmsre.match(arg)
    if m is None:
        raise ValueError("Unknown dms format")
    mparts = m.groups()
    deg = float(mparts[0])
    if len(mparts[1]) != 0:
        return deg / dmsdiv[mparts[1]]
    return  deg
