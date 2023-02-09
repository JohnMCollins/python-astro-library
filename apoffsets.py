"""Get offsets from fractional row/column/aperture"""

import math
import numpy as np

def ap_offsets(col, row, apsize):
    """Get integer offsets in array for circle delineated by apsize at row/col.
    row, col and apsize may all be fractional"""

    apsq = apsize **2
    iapsize = int(math.ceil(apsize))
    rng = range(-iapsize, iapsize+1)
    xpoints, ypoints = np.meshgrid(rng, rng)
    colfrac, dummy = math.modf(col)
    rowfrac, dummy = math.modf(row)
    return np.array([(x,y) for x,y in zip(xpoints.flatten(), ypoints.flatten()) if (x - colfrac) ** 2 + (y - rowfrac) ** 2 <= apsq])
