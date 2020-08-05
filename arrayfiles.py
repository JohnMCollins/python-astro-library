# Routines for handling array files

import miscutils
import remdefaults
import numpy as np


class ArrayFileError(Exception):
    """Throuw this if we have some sort of error"""
    pass


def get_argfile(farg):
    """Get argument file and possible :n planes with optional weighting xn. Abort with error if we don't understand it
    otherwise return 2D (file, array)"""

    bits = farg.split(':')
    if len(bits) > 1:
        file = bits.pop(0)
        plane = []
        try:
            for b in bits:
                bparts = b.split('x')
                if len(bparts) > 2:
                    raise ValueError("Too many parts to plane spec")
                else:
                    pl = int(bparts[0])
                    weight = 1
                    if len(bparts) > 1:
                        weight = float(bparts[1])
                    plane.append((pl, weight))
        except ValueError:
            raise ArrayFileError("Do not understand " + farg + " expecting filename or filename:plane[:plane]")
    else:
        plane = None
        file = bits[0]

    mfile = remdefaults.meanstd_file(file)
    try:
        arr = np.load(mfile)
    except OSError as e:
        raise ArrayFileError("Cannot load " + mfile + " error was " + e.args[1])

    if plane is None:
        if len(arr.shape) == 2:
            return  (file, arr)
        raise ArrayFileError("file " + mfile + " has dimension " + str(len(arr.shape)) + " but no plane given")
    elif len(arr.shape) == 3:
        try:
            result = np.zeros_like(arr[0])
            for pl, weight in plane:
                result += arr[pl] * weight
            return (file, result)
        except IndexError:
            raise ArrayFileError("Plane out of range for file " + mfile + " which has dims " + "x".join([str(i) for i in arr.shape]))
    else:
        raise ArrayFileError("Plane " + str(plane) + " given but " + mfile + " has dimension " + str(len(arr.shape)))
