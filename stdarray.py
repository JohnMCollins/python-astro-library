"""Classes for reesult finding as XML"""

import warnings
import math
import gzip
import io
import numpy as np
import apoffsets

# Error types

NOT_INITIALISED = -1
INCOMPAT_SHAPE = -2
DIVBYZERO = -3
INIT_ERROR = -4
UNKNOWN_OPERAND = -5
INVALID_FILE = -6
INVALID_ROW = -7
INVALID_COL = -8
IOERROR = -9


class StdArrayErr(Exception):
    """Throw me if there is some kind of error"""

    def __init__(self, typ, *args):
        self.errortype = typ
        super().__init__(*args)


class StdScalar:
    """Class for saving value/std values"""

    def __init__(self, value=0.0, std=0.0, stdsq=None):
        self.value = value
        if stdsq is None:
            self.stdsq = std ** 2
        else:
            self.stdsq = stdsq

    def get_value(self):
        """Get the value on its own"""
        return  self.value

    def get_std(self):
        """Get std deviation"""
        return  math.sqrt(self.stdsq)

    def __add__(self, other):
        if np.isscalar(other):
            return  StdScalar(self.value + other, stdsq=self.stdsq)
        if isinstance(other, StdScalar):
            return  StdScalar(self.value + other.value, self.stdsq + other.stdsq)
        if isinstance(other, StdArray):
            return  StdArray(values=self.value + other.values, stdsq=self.stdsq + other.stdsq)
        raise  StdArrayErr(UNKNOWN_OPERAND, "Unknown second operand in add")

    def __radd__(self, other):
        return self.__add__(other)

    def __iadd__(self, other):
        if np.isscalar(other):
            self.value += other
        elif isinstance(other, StdArray):
            raise StdArrayErr(INCOMPAT_SHAPE, "Cannot increment/add with RHS array")
        else:
            self.value += other.value
            self.stdsq += other.stdsq
        return self

    def __sub__(self, other):
        if np.isscalar(other):
            return  StdScalar(self.value - other, stdsq=self.stdsq)
        if isinstance(other, StdScalar):
            return  StdScalar(self.value - other.value, self.stdsq + other.stdsq)
        if isinstance(other, StdArray):
            return  StdArray(values=self.value - other.values, stdsq=self.stdsq + other.stdsq)
        raise  StdArrayErr(UNKNOWN_OPERAND, "Unknown second operand in subtract")

    def __rsub__(self, other):
        if np.isscalar(other):
            return  StdScalar(other - self.value, stdsq=self.stdsq)
        raise  StdArrayErr(UNKNOWN_OPERAND, "Unknown first operand in subtract")

    def __isub__(self, other):
        if np.isscalar(other):
            self.value -= other
        elif isinstance(other, StdArray):
            raise StdArrayErr(INCOMPAT_SHAPE, "Cannot decrement/subtractwith RHS array")
        else:
            self.value -= other.value
            self.stdsq += other.stdsq
        return  self

    def __mul__(self, other):
        if np.isscalar(other):
            return  StdScalar(self.value * other, stdsq=self.stdsq * other ** 2)
        if isinstance(other, StdScalar):
            return  StdScalar(self.value * other.value, stdsq=self.stdsq * other.value ** 2 + other.stdsq * self.value ** 2)
        if isinstance(other, StdArray):
            return  StdArray(values=self.value * other.values, stdsq=self.stdsq * other.values ** 2 + other.stdsq * self.value ** 2)
        raise  StdArrayErr(UNKNOWN_OPERAND, "Unknown second operand in multiply")

    def __rmul__(self, other):
        return self.__mul__(other)

    def __imul__(self, other):
        if np.isscalar(other):
            self.value *= other
            self.stdsq *= other * other
        elif isinstance(other, StdArray):
            raise StdArrayErr(INCOMPAT_SHAPE, "Cannot multiply with RHS array")
        else:
            self.stdsq = self.stdsq * other.value ** 2 + other.stdsq * self.value ** 2
            self.value *= other.value
        return  self

    def __truediv__(self, other):
        with warnings.catch_warnings():
            warnings.simplefilter('error', RuntimeWarning)
            if np.isscalar(other):
                return  StdScalar(self.value / other, stdsq=self.stdsq / other ** 2)
            if isinstance(other, StdScalar):
                val = self.value / other.value
                return  StdScalar(val, stdsq=(self.stdsq + val ** 2 * other.stdsq) / other.value ** 2)
            if isinstance(other, StdArray):
                val = self.value / other.values
                return  StdArray(values=val, stdsq=(self.stdsq + val ** 2 * other.stdsq) / other.values ** 2)
        raise  StdArrayErr(UNKNOWN_OPERAND, "Unknown second operand in divide")

    def __rtruediv__(self, other):
        with warnings.catch_warnings():
            warnings.simplefilter('error', RuntimeWarning)
            if np.isscalar(other):
                return  StdScalar(other / self.value, stdsq=other ** 2 / self.stdsq ** 4)
        raise  StdArrayErr(UNKNOWN_OPERAND, "Unknown first operand in divide")

    def __itruediv__(self, other):
        with warnings.catch_warnings():
            warnings.simplefilter('error', RuntimeWarning)
            if np.isscalar(other):
                self.value /= other
                self.stdsq /= other ** 2
            elif isinstance(other, StdArray):
                raise StdArrayErr(INCOMPAT_SHAPE, "Cannot multiply with RHS array")
            else:
                self.value = val = self.value / other.value
                self.stdsq = (self.stdsq + val ** 2 * other.stdsq) / other.value ** 2
        return  self


def get_a_shape(*args):
    """Get shape from one of possible ndarray args"""
    for arg in args:
        try:
            return  arg.shape
        except AttributeError:
            pass
    return  None


class StdArray:
    """Class for processubg image array with tracking of std errors"""

    def __init__(self, rows=None, cols=None, shape=None, values=None, stddevs=None, stdsq=None):

        # First get shape - complaining if something clashes

        if shape is None:
            if rows is None or cols is None:
                self.shape = get_a_shape(values, stddevs, stdsq)
                if  self.shape is None:
                    raise StdArrayErr(INIT_ERROR, "Cannot find shape")
            else:
                self.shape = (rows, cols)
        else:
            self.shape = shape
            if rows is not None or cols is not None:
                if  (rows, cols) != shape:
                    raise StdArrayErr(INIT_ERROR, "Specified shape does not match specified row/cols")

        if isinstance(values, np.ndarray) and values.shape != self.shape:
            raise StdArrayErr(INIT_ERROR, "Values shape does not match specified shape")
        if isinstance(stddevs, np.ndarray) and stddevs.shape != self.shape:
            raise StdArrayErr(INIT_ERROR, "Stddevs shape does not match specified shape")
        if isinstance(stdsq, np.ndarray) and stdsq.shape != self.shape:
            raise StdArrayErr(INIT_ERROR, "Stdsq shape does not match specified shape")

        self.values = self.stdsq = None
        if values is None:
            return

        # Get values now, worry about stdsq in a minute

        if np.isscalar(values):
            self.values = np.full(self.shape, values, dtype=np.float64)
        elif isinstance(values, StdScalar):
            self.values = np.full(self.shape, values.value, dtype=np.float64)
            self.stdsq = np.full(self.shape, values.stdsq, dtype=np.float64)
        else:
            self.values = values.copy()

        if self.stdsq is not None:
            if stddevs is not None or stdsq is not None:
                raise StdArrayErr(INIT_ERROR, "Stdscalr value and stddevs supplied")
        elif stddevs is not None:
            if stdsq is not None:
                raise StdArrayErr(INIT_ERROR, "Cannot give both stddevs and stdsq")
            if np.isscalar(stddevs):
                self.stdsq = np.full(self.shape, stddevs ** 2, dtype=np.float64)
            else:
                self.stdsq = stddevs ** 2
        else:
            if stdsq is None:
                self.stdsq = np.zeros_like(self.values)
            elif np.isscalar(stdsq):
                self.stdsq = np.full(self.shape, stdsq, dtype=np.float64)
            else:
                self.stdsq = stdsq.copy()

    def get_values(self):
        """Get the values array"""
        if self.values is None:
            raise StdArrayErr(NOT_INITIALISED, "Arrays not set up yet")
        return  self.values

    def get_stddev(self):
        """Get stddev array"""
        if self.stdsq is None:
            raise StdArrayErr(NOT_INITIALISED, "Arrays not set up yet")
        return  np.sqrt(self.stdsq)

    def set_values(self, values=None, stddevs=None, stdsq=None):
        """Set values in array"""

        if values is not None:
            if np.isscalar(values):
                self.values = np.full(self.shape, values, dtype=np.float64)
            elif isinstance(values, StdScalar):
                self.values = np.full(self.shape, values.value, dtype=np.float64)
                self.stdsq = np.full(self.shape, values.stdsq, dtype=np.float64)
            else:
                if values.shape != self.shape:
                    raise StdArrayErr(INCOMPAT_SHAPE, "Assigned value does not match current shape")
                self.values = values.copy()

        if stddevs is not None:
            if np.isscalar(stddevs):
                self.stdsq = np.full(self.shape, stddevs ** 2, dtype=np.float64)
            else:
                if stddevs.shape != self.shape:
                    raise StdArrayErr(INCOMPAT_SHAPE, "Assigned stddevs does not match current shape")
                self.stdsq = stddevs ** 2

        if stdsq is not None:
            if np.isscalar(stdsq):
                self.stdsq = np.full(self.shape, stdsq, dtype=np.float64)
            else:
                if stdsq.shape != self.shape:
                    raise StdArrayErr(INCOMPAT_SHAPE, "Assigned stdsq does not match current shape")
                self.stdsq = stdsq

        return  self

    def get_sum(self, col, row, apsize):
        """Get sum of values and error around row and column with given aperture size
        row, col and apsize may all be fractional"""
        xycoords = apoffsets.ap_offsets(col, row, apsize) + (int(col), int(row))
        vs = self.get_values()
        errs = self.stdsq
        try:
            return  (np.sum([vs[(y,x)] for x,y in xycoords]), math.sqrt(np.sum([errs[(y,x)] for x, y in xycoords])))
        except IndexError:
            # print("col={:.4f} row={:.4f} apsize={:.4f}".format(col,row,apsize), xycoords)
            raise StdArrayErr(INCOMPAT_SHAPE, "Coords out of range")

    def __add__(self, other):
        try:
            if  np.isscalar(other):
                return  StdArray(values=self.values + other, stdsq=self.stdsq)
            if  isinstance(other, StdScalar):
                return  StdArray(values=self.values + other.value, stdsq=self.stdsq + other.stdsq)
            if isinstance(other, StdArray):
                return  StdArray(values=self.values + other.values, stdsq=self.stdsq + other.stdsq)
            raise  StdArrayErr(UNKNOWN_OPERAND, "Unknown second operand in add")
        except TypeError:
            raise StdArrayErr(NOT_INITIALISED, "Stdarray not fully set up")
        except ValueError:
            raise StdArrayErr(INCOMPAT_SHAPE, "Incompatible arguement types")

    def __radd__(self, other):
        return self.__add__(other)

    def __iadd__(self, other):
        try:
            if np.isscalar(other):
                self.values += other
            elif isinstance(other, StdScalar):
                self.values += other.value
                self.stdsq += other.stdsq
            else:
                self.values += other.values
                self.stdsq += other.stdsq
        except TypeError:
            raise StdArrayErr(NOT_INITIALISED, "Array not initialised")
        except ValueError:
            raise StdArrayErr(INCOMPAT_SHAPE, "Incompatible arguement types")
        return self

    def __sub__(self, other):
        try:
            if  np.isscalar(other):
                return  StdArray(values=self.values - other, stdsq=self.stdsq)
            if  isinstance(other, StdScalar):
                return  StdArray(values=self.values - other.value, stdsq=self.stdsq + other.stdsq)
            if isinstance(other, StdArray):
                return  StdArray(values=self.values - other.values, stdsq=self.stdsq + other.stdsq)
            raise  StdArrayErr(UNKNOWN_OPERAND, "Unknown second operand in subtract")
        except TypeError:
            raise StdArrayErr(NOT_INITIALISED, "Stdarray not fully set up")
        except ValueError:
            raise StdArrayErr(INCOMPAT_SHAPE, "Incompatible arguement types")

    def __rsub__(self, other):
        try:
            if np.isscalar(other):
                return StdArray(values=other - self.values, stdsq=self.stdsq)
            if isinstance(other, StdArray):
                return  StdArray(values=other.values - self.values, stdsq=self.stdsq + other.stdsq)
            raise  StdArrayErr(UNKNOWN_OPERAND, "Unknown second operand in subtract")
        except TypeError:
            raise StdArrayErr(NOT_INITIALISED, "Stdarray not fully set up")
        except ValueError:
            raise StdArrayErr(INCOMPAT_SHAPE, "Incompatible arguement types")

    def __isub__(self, other):
        try:
            if np.isscalar(other):
                self.values -= other
            elif isinstance(other, StdScalar):
                self.values -= other.value
                self.stdsq += other.stdsq
            else:
                self.values -= other.values
                self.stdsq += other.stdsq
        except TypeError:
            raise StdArrayErr(NOT_INITIALISED, "Array not initialised")
        except ValueError:
            raise StdArrayErr(INCOMPAT_SHAPE, "Incompatible arguement types")
        return  self

    def __mul__(self, other):
        try:
            if  np.isscalar(other):
                return  StdArray(values=self.values * other, stdsq=self.stdsq * other ** 2)
            if  isinstance(other, StdScalar):
                return  StdArray(values=self.values * other.value, stdsq=self.stdsq * other.value ** 2 + other.stdsq * self.values ** 2)
            if isinstance(other, StdArray):
                return  StdArray(values=self.values * other.values, stdsq=self.stdsq * other.values ** 2 + other.stdsq * self.values ** 2)
            raise  StdArrayErr(UNKNOWN_OPERAND, "Unknown second operand in multiply")
        except TypeError:
            raise StdArrayErr(NOT_INITIALISED, "Stdarray not fully set up")
        except ValueError:
            raise StdArrayErr(INCOMPAT_SHAPE, "Incompatible arguement types")

    def __rmul__(self, other):
        return self.__mul__(other)

    def __imul__(self, other):
        try:
            if np.isscalar(other):
                self.values *= other
                self.stdsq *= other * other
            elif isinstance(other, StdScalar):
                self.stdsq = self.stdsq * other.value ** 2 + other.stdsq * self.values ** 2
                self.values *= other.value
            else:
                self.stdsq = self.stdsq * other.values ** 2 + other.stdsq * self.values ** 2
                self.values *= other.values
        except TypeError:
            raise StdArrayErr(NOT_INITIALISED, "Array not initialised")
        except ValueError:
            raise StdArrayErr(INCOMPAT_SHAPE, "Incompatible arguement types")
        return  self

    def __truediv__(self, other):
        with warnings.catch_warnings():
            warnings.simplefilter('error', RuntimeWarning)
            try:
                if np.isscalar(other):
                    return  StdArray(values=self.values / other, stdsq=self.stdsq / other ** 2)
                if isinstance(other, StdScalar):
                    val = self.values / other.value
                    return  StdArray(values=val, stdsq=(self.stdsq + val ** 2 * other.stdsq) / other.value ** 2)
                if isinstance(other, StdArray):
                    val = self.values / other.values
                    return  StdArray(values=val, stdsq=(self.stdsq + val ** 2 * other.stdsq) / other.values ** 2)
            except TypeError:
                raise StdArrayErr(NOT_INITIALISED, "Array not initialised")
            except ValueError:
                raise StdArrayErr(INCOMPAT_SHAPE, "Incompatible arguement types")
        raise  StdArrayErr(UNKNOWN_OPERAND, "Unknown second operand in divide")

    def __rtruediv__(self, other):
        with warnings.catch_warnings():
            warnings.simplefilter('error', RuntimeWarning)
            try:
                if np.isscalar(other):
                    return  StdArray(values=other / self.values, stdsq=other ** 2 / self.stdsq ** 4)
                if isinstance(other, StdScalar):
                    val = other.value / self.values
                    return  StdArray(values=val, stdsq=(other.stdsq + val ** 2 * self.stdsq) / self.values ** 2)
                if isinstance(other, StdArray):
                    val = other.values / self.values
                    return  StdArray(values=val, stdsq=(other.stdsq + val ** 2 * self.stdsq) / self.values ** 2)
                raise  StdArrayErr(UNKNOWN_OPERAND, "Unknown first operand in divide")
            except TypeError:
                raise StdArrayErr(NOT_INITIALISED, "Array not initialised")
            except ValueError:
                raise StdArrayErr(INCOMPAT_SHAPE, "Incompatible arguement types")
            except RuntimeWarning:
                raise StdArrayErr(DIVBYZERO, "Division by zero")

    def __itruediv__(self, other):
        with warnings.catch_warnings():
            warnings.simplefilter('error', RuntimeWarning)
            try:
                if np.isscalar(other):
                    self.values /= other
                    self.stdsq /= other ** 2
                elif isinstance(other, StdScalar):
                    self.values /= other.value
                    self.stdsq = (self.stdsq + self.values ** 2 * other.stdsq) / other.value ** 2
                else:
                    self.values /= other.values
                    self.stdsq = (self.stdsq + self.values ** 2 * other.stdsq) / other.values ** 2
            except TypeError:
                raise StdArrayErr(NOT_INITIALISED, "Array not initialised")
            except ValueError:
                raise StdArrayErr(INCOMPAT_SHAPE, "Incompatible arguement types")
            except RuntimeWarning:
                raise StdArrayErr(DIVBYZERO, "Division by zero")
        return  self

    def load(self, bytestring):
        """Do in-memory load of bytestring to object"""
        try:
            parts = np.load(io.BytesIO(gzip.decompress(bytestring)))
        except (ValueError, gzip.BadGzipFile):
            raise StdArrayErr(INVALID_FILE, "Invalid save file rormat")

        try:
            self.values, self.stdsq = parts
        except ValueError:
            raise StdArrayErr(INVALID_FILE, "Invalid save file parts")

        self.shape = self.values.shape
        return  self

    def save(self):
        """Do in memory save of bytestring to object"""

        try:
            parts = np.array([self.values, self.stdsq])
        except ValueError:
            raise StdArrayErr(NOT_INITIALISED, "Array is not initialised")

        f = io.BytesIO()
        np.save(f, parts)
        return  gzip.compress(f.getvalue())

def load_array(filename):
    """Load an array from a staarry file"""
    try:
        with open(filename, 'rb') as inf:
            result = StdArray(rows=0,cols=0)
            return  result.load(inf.read())
    except  OSError  as  e:
        raise  StdArrayErr(IOERROR, "Could not open {:s} error was {:s}".format(filename, e.args[1]))

def save_array(filename, arr):
    """Save array to stdarray file"""
    try:
        with open(filename, 'wb') as outf:
            outf.write(arr.save())
    except  OSError  as  e:
        raise  StdArrayErr(IOERROR, "Could not save {:s} error was {:s}".format(filename, e.args[1]))
