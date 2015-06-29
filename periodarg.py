# Get period from argument

import string
import re
import numpy as np

parser = re.compile('(.+)([smhd])?$', re.I)
rparser = re.compile('(.+):(.+)/(.+)$')

SECSPERDAY = 3600.0 * 24.0

mult = dict(s=1.0, m=60.0, h=3600.0, d=SECSPERDAY, S=1.0, M=60.0, H=3600.0, D=SECSPERDAY)

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

    if mtch.group(2) is None:
        return per

    return per * mult[mtch.group(2)]

def periodrange(arg):
    """Get range of periods in the form start:step:end"""

    rangespecs = string.split(arg, ':')

    numb = -1
    if len(rangespecs) == 3:
        start, step, stop = [periodarg(p) for p in rangespecs]
    else:
        mtch = rparser.match(arg)
        if not mtch:
            raise ValueError("Cannot understand range spec " + arg)
        start = periodarg(mtch.group(1))
        stop = periodarg(mtch.group(2))
        numb = int(mtch.group(3))
        if numb <= 0:
            raise ValueError("Cannot understand range spec " + arg)

    if start >= stop:
        raise ValueError("start of range >= stop in " + arg)

    if numb <= 0:
        ret = np.arange(start, stop, step)
    else:
        ret = np.linspace(start, stop, numb)
    if len(ret) < 10:
        raise ValueError(arg + " specifies too few intervals")
    return  ret
