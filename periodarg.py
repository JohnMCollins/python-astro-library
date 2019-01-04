# @Author: John M Collins <jmc>
# @Date:   2019-01-03T22:48:34+00:00
# @Email:  jmc@toad.me.uk
# @Filename: periodarg.py
# @Last modified by:   jmc
# @Last modified time: 2019-01-04T12:32:14+00:00

# Get period from argument

import string
import re
import numpy as np
import os
import sys

parser = re.compile('(.+?)([smhd])?$', re.I)
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

def periodrange(arg, asday = True):
    """Get range of periods in the form start:step:end or start:stop/number converting to days if asday specified"""

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
    if asday:
        return  ret / SECSPERDAY
    return  ret

def optperiodrange(arg):
    """Get period argument from the environment if not specified or apply default"""
    if arg is None:
        try:
            arg = os.environ['PERIODS']
        except KeyError:
            arg = "1d:.01d:100d"
    try:
        return periodrange(arg)
    except ValueError as e:
        print("Invalid period arg", e.args[0], file=sys.stderr)
        raise
