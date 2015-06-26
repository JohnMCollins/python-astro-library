# Get period from argument

import string
import re
import numpy as np

parser = re.compile('(.+)([smhd])$', re.I)

mult = dict(s=1.0, m=60.0, h=3600.0, d=3600.0*24.0, S=1.0, M=60.0, H=3600.0, D=3600.0*24.0)

def periodarg(arg):
    """Get period from string which should be a float followed by s/m/h/d to donote multiplier
    by secs/mins/hours/days"""

    mtch = parser.match(arg)
    if mtch is None:
        raise ValueError("Invalid period arg: " + arg)
    try:
         per = float(mtch.group(1))
    except ValueError:
        raise ValueError("Invalid period arg: " + arg)

    return per * mult[mtch.group(2)]

def periodrange(arg):
    """Get range of periods in the form start:step:end"""

    rangespecs = string.split(arg, ':')
    if len(rangespecs) != 3:
        raise ValueError("Expecting 3 range parameters not " + arg)

    start, step, stop = [periodarg(p) for p in rangespecs]

    if start >= stop:
        raise ValueError("start of range >= stop in " + arg)

    ret = np.arange(start, stop+step, step)
    if len(ret) < 10:
        raise ValueError(arg + " specifies too few intervals")
    return  ret
