"""Find overlaps in list of x,y points and given radius"""

import numpy as np

def find_overlaps(xypoints, apsize):
    """Find indices of overlaps in a list of xy points within given radius"""

    carr = np.array([complex(x,y) for x,y in xypoints])
    side = carr.shape[0]
    diffs = np.abs(np.subtract.outer(carr, carr)) > 2*apsize + 1
    nooverlaps = np.full(side, True, dtype=bool)
    for rownum, row in enumerate(diffs, 1):
        nooverlaps[rownum:] &= row[rownum:]
    if np.count_nonzero(nooverlaps) == side:
        return  np.array(xypoints)
    return  np.array(xypoints)[nooverlaps]
