# Trim Nan values from edges of array

import numpy as np

def trimnan(arr):
    """Trim NaN values from last rows and columns of 2D array.
    
    Arg is orignal array,
    Rturn trimmed array"""
    
    rows, cols = arr.shape
    while np.count_nonzero(np.isnan(arr[-1])) == cols:
        arr = arr[0:-1]
        rows -= 1
    while np.count_nonzero(np.isnan(arr[:,-1])) != 0:
        arr = arr[:,0:-1]
    while np.count_nonzero(np.isnan(arr[-1])) != 0:
        arr = arr[0:-1]
    return  arr

def trimto(arr, *arrs):
  
    """Trim arrs to size of first array"""
   
    rows, cols = arr.shape
    
    result = []
    
    for a in arrs:
        result.append(a[0:rows, 0:cols])
    
    return tuple(result)

def trimzeros(arr):
    
    """Fraim trailing parts of ARRAY WHICH ARE ZEROS"""
    
    while np.count_nonzero(arr[-1]) == 0:
        arr = arr[0:-1]

    while np.count_nonzero(arr[:,-1]) == 0:
        arr = arr[:,0:-1]
    
    return arr