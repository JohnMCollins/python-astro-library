# Fix duplicates in array

import numpy as np
import numpy.random as nr


def fixdups(arr, division=.001, minimum=0.0, maximum=100.0):
    """Fix duplications in array by randomly adding or subtracting divions from duplicate elements,
       We specify the reange and the amount to add or subtrace"""

    rangev = maximum - minimum
    arr = np.array(arr)
    usecount = np.count_nonzero(np.equal.outer(arr, arr), axis=0)

    while np.count_nonzero(usecount > 1) > 0:
        firstplace = np.where(usecount > 1)[0][0]
        if  arr[firstplace] - minimum > nr.uniform() * rangev:
            arr[firstplace] -= division
        else:
            arr[firstplace] += division
        usecount = np.count_nonzero(np.equal.outer(arr, arr), axis=0)

    arr.sort()
    return arr
