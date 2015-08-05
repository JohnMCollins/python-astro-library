import re

def getfakeobs(filename, suffix = None):
    """Get contents of fake observation file as a dictionary.
    Return None if invalid or cannot open
    Add optional suffix to file names"""

    if suffix is None:
        suffix = ""
    try:
        if suffix[0] != '.':
            suffix = '.' + suffix
    except IndexError:
        pass

    try:
        inf = open(filename, 'r')
    except IOError:
        return  None

    lm = re.compile('\s*(\S+)\s+([\d.]+)')

    red = dict()

    try:
        for line in inf:
            mtch = lm.match(line)
            if not mtch: raise ValueError
            fname = mtch.group(1)
            ot = float(mtch.group(2))
            red[fname + suffix] = ot
        return  red
    except ValueError:
        return  None
    finally:
        inf.close()
