"""Misc utilities, mostly about suffixes"""

def hidden_split(path):
    """Split path into dirname and basename but take leading '.'s off basename
    and append to dirname"""

    try:
        slp = path.rindex('/') + 1
        dirname = path[:slp]
        basename = path[slp:]
    except ValueError:
        dirname = ""
        basename = path

    # Now deal with leading s's in basename so we handle
    # .foo.bar correctly

    try:
        while basename[0] == '.':
            dirname += '.'
            basename = basename[1:]
    except IndexError:
        pass
    return  (dirname, basename)

def split_parts(path):
    """Split (basename) into components, but merge where we've got common cases of compessed files"""
    parts = [p for p in path.split('.') if len(p) != 0]
    if len(parts) > 2  and  parts[-1] in ('gz', 'xz'):
        lpart = parts.pop()
        parts[-1] += '.' + lpart
    return  parts

def hassuffix(st, suff=None):
    """Return whether string (usually file name) has given suffix (or suffix out of list) or any suffix at all"""

    dummy, basename = hidden_split(st)
    parts = split_parts(basename)
    if len(parts) <= 1:
        return  False
    if suff is None:
        return  True
    if isinstance(suff, str):
        return  parts[-1] == suff
    return  parts[-1] in suff

def removesuffix(st, suff=None, allsuff=False):
    """Remove the specified suffix or any suffix if none specified
       If allsuff is true, remove all or all matching suffixes
       suff may be tuple or list to give list of suffixes"""

    dirname, basename = hidden_split(st)
    parts = split_parts(basename)
    if suff is None:
        while len(parts) > 1:
            parts.pop()
            if not allsuff:
                break
    elif isinstance(suff, str):
        while len(parts) > 1 and parts[-1] == suff:
            parts.pop()
            if not allsuff:
                break
    else:
        while len(parts) > 1 and parts[-1] in suff:
            parts.pop()
            if not allsuff:
                break
    return dirname + '.'.join(parts)

def addsuffix(st, suff):
    """Add a suffix if it hasn't got one"""
    if hassuffix(st, suff):
        return  st
    if suff[0] != '.':
        suff = '.' + suff
    return  st + suff

def replacesuffix(st, new, old=None, allsuff=False):
    """Replace any suffix with the new one given"""
    # Cater for string having the desired suffix already, notably with .fits.gz
    if hassuffix(st, new):
        return  st
    try:
        if new[0] != '.':
            new = '.' + new
    except IndexError:
        return  st
    return removesuffix(st, old, allsuff) + new
