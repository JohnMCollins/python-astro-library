# @Author: John M Collins <jmc>
# @Date:   2019-01-03T21:01:27+00:00
# @Email:  jmc@toad.me.uk
# @Filename: miscutils.py
# @Last modified by:   jmc
# @Last modified time: 2019-01-03T22:28:54+00:00

# Misc handy utils

import string

def hassuffix(st, suff = None):
    """Return whether string (usually file name) has given suffix or any suffix at all"""
    try:
        if suff is None:
            return st.rindex('.') < len(st)
        if suff[0] != '.':
            suff = '.' + suff
        if st[st.rindex(suff):] == suff: return True
    except (ValueError, IndexError):
        pass
    return False

def removesuffix(st, suff = None):
    """Remove the specified suffix or any suffix if none specified"""

    bits = string.split(st, '.')
    if len(bits) <= 1:
        return  st
    if suff is not None:
        while suff[0] == '.':
            suff = suff[1:]
        if suff != bits[-1]:
            return  st
    bits.pop()
    return '.'.join(bits)

def addsuffix(st, suff):
    """Add a suffix if it hasn't got one"""
    if hassuffix(st, suff):
        return  st
    if suff[0] != '.':
        suff = '.' + suff
    return  st + suff

def replacesuffix(st, new, old = None):
    """Replace any suffix with the new one given"""
    try:
        if new[0] != '.':
            new = '.' + new
    except IndexError:
        return  st
    return removesuffix(st, old) + new
