# Decode variants of range arguments

import string

def getrangearg(argparsevar, rangename="range", lowerarg="lower", upperarg="upper"):
    """Get a range out of an "argparse" array.

    rangename (default "range") is the name of a string which might be of form "nnn,nnn"
    lowerarg/upperarg (default "lower" and "upper") is a fallback for separate arguments"""

    try:
        rangearg = argparsevar[rangename]
        if rangearg is not None:
            partrange = string.split(rangearg, ',')
            if len(partrange) == 1:
                llim = partrange
                ulim = 0.0
            elif len(partrange) > 2:
                raise ValueError("Do not understand range argument " + rangearg)
            else:
                try:
                    llim, ulim = partrange
                    if len(llim) == 0:
                        llim = 0.0
                    else:
                        llim = float(llim)
                    if len(ulim) == 0:
                        ulim = 0.0
                    else:
                        ulim = float(ulim)
                except ValueError:
                    raise ValueError("Invalid number in range argument " + rangearg)
        else:
            llim = argparsevar[lowerarg]
            ulim = argparsevar[upperarg]
    except KeyError:
        return  (0.0, 0.0)

    if llim > ulim:
        return  (ulim, llim)
    return  (llim, ulim)

def parserange(arg):
    """Parse a range argument, either a single floating point number, in which case assume other end is zero,
    or a pair. If only a single number add zero. Return a sorted result"""

    if arg is None: return None

    arg = string.replace(arg, ':', ',')
    bits = string.split(arg, ',')
    try:
        if len(bits) == 1:
            ret = [0, float(arg)]
        elif len(bits) == 2:
            ret = map(lambda x: float(x), bits)
        else:
            raise ValueError
    except:
        print "Did not understand range value of", arg
        return None

    ret.sort()
    return ret
