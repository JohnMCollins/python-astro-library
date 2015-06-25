# Get period from argument

import re

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
