"""Misc utilities, mostly about suffixes"""


def hassuffix(st, suff=None):
    """Return whether string (usually file name) has given suffix or any suffix at all"""
    try:
        if suff is None:
            return st.rindex('.') < len(st)
        if suff[0] != '.':
            suff = '.' + suff
        if st[st.rindex(suff):] == suff:
            return True
    except (ValueError, IndexError):
        pass
    return False


def removesuffix(st, suff=None, allsuff=False):
    """Remove the specified suffix or any suffix if none specified
       If allsuff is true, remove all or all matching suffixes"""

    # Get rid of leading dots in suffice

    if suff is not None:
        while len(suff) > 0 and suff[0] == '.':
            suff = suff[1:]
        if len(suff) == 0:
            suff = None
    bits = st.split('.')
    if allsuff:
        while len(bits) > 1:
            if suff is not None:
                if suff != bits[-1]:
                    break
            bits.pop()
    elif len(bits) > 1:
        if suff is None or suff == bits[-1]:
            bits.pop()
    return '.'.join(bits)


def addsuffix(st, suff):
    """Add a suffix if it hasn't got one"""
    if hassuffix(st, suff):
        return  st
    if suff[0] != '.':
        suff = '.' + suff
    return  st + suff


def replacesuffix(st, new, old=None):
    """Replace any suffix with the new one given"""
    # Cater for string having the desired suffix already, notably with .fits.gz
    if hassuffix(st, new):
        return  st
    try:
        if new[0] != '.':
            new = '.' + new
    except IndexError:
        return  st
    return removesuffix(st, old) + new
