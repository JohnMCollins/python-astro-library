# Interpret a list of level max/min selection arguments
# Currently using for Xray levels in UVES plots

import re

levmatcher = re.compile('^(?:([gl]):)?([-e\d.]*)(,?)([-e\d.]*)$', re.IGNORECASE)

def levelselect(args):
    """ Interpret arg levels thus:

    n (+ve value) upper limit of n
    n (-ve value) lower limit of -n (unless we are talking about gradients when upper limit of n)
    m,n lower limit m upper limit n
    m, lower limit of m
    n upper limit of n

    Prefix by g: to talk about gradients (or l: to specify level).

    Return list of tuples, (low, hi, isgradient)"""

    resultlevels = []

    for larg in args:
        try:

            # Initialise to nice big numbers

            lo = -1e40
            hi = 1e40

            # Special case of no limit given by 0 or :

            if larg == '0' or larg == '-':
                resultlevels.append((lo, hi, False))
                continue

            mtch = levmatcher.match(larg)
            if mtch is None:
                raise ValueError("match")

            # re processing sets first group to l, g or None,
            # second group to first numeric or empty
            # third group to comma or empty
            # fourth group to second numeric or empty

            lgind, lowarg, comma, hiarg = mtch.groups()
            isg = lgind == 'g'  # Covers case where none at all

            if len(hiarg) == 0:     # No second numeric

                # If we had a comma, then this is a lower limit

                if len(comma) != 0:
                    lo = float(lowarg)
                else:
                    # Possibly a high limit but low limit if doing gradient
                    hip = float(lowarg)
                    if not isg and hip < 0.0:
                        lo = -hip
                    else:
                        hi = hip
            else:
                # Did have high limit, if we've got lower limit take it
                hi = float(hiarg)
                if len(lowarg) != 0:
                    lo = float(lowarg)
            resultlevels.append((lo, hi, isg))
        except ValueError:
            return None

    return  resultlevels
