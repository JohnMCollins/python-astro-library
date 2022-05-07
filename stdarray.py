"""Classes for reesult finding as XML"""

import warnings
import numpy as np

# Error types

NOT_INITIALISED = -1
INCOMPAT_SHAPE = -2
DIVBYZERO = -3
INIT_ERROR = -4


class StdArrayErr(Exception):
    """Throw me if there is some kind of error"""

    def __init__(self, typ, *args):
        self.errortype = typ
        super().__init__(*args)


class StdArray:
    """Class for processubg image array with tracking of std errors"""

    def __init__(self, rows=None, cols=None, shape=None, values=None, stddevs=None):

        # Specify dims as tuple or rows and cols

        try:
            rows, cols = shape
        except ValueError:
            raise StdArrayErr(INIT_ERROR, "Incompatible shape expecting 2D")
        except TypeError:
            pass

        if values is not None:
            if stddevs is None:
                raise StdArrayErr(INIT_ERROR, "Values given but not stderr")
            dshape = None
            if np.isscalar(values):
                if np.isscalar(stddevs):
                    if rows is None or cols is None:
                        raise StdArrayErr(INIT_ERROR, "No rows and columns given")
                else:
                    dshape = stddevs.shape
            else:
                dshape = values.shape
                if not np.isscalar(stddevs):
                    if dshape != stddevs.shape:
                        raise StdArrayErr(INIT_ERROR, "Values and stderr shapes do not match")
            if rows is None or cols is None:
                try:
                    rows, cols = dshape
                except TypeError:
                    raise StdArrayErr(INIT_ERROR, "No rows and columns given with scalars")
                except ValueError:
                    raise StdArrayErr(INIT_ERROR, "Expecting 2D shapes")
        else:
            if stddevs is not None:
                raise StdArrayErr(INIT_ERROR, "Stderr given but not values")
            if rows is None or cols is None:
                raise StdArrayErr(INIT_ERROR, "Size of array not given")

        # Now actually do business

        self.shape = (rows, cols)

        if values is None:
            self.values = None
        elif np.isscalar(values):
            self.values = np.full(self.shape, values, dtype=np.float64)
        else:
            self.values = values.copy()

        if stddevs is None:
            self.stdsq = None
        elif np.isscalar(stddevs):
            self.stdsq = np.full(self.shape, stddevs ** 2, dtype=np.float64)
        else:
            self.stdsq = stddevs ** 2

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

    def set_values(self, values=None, stddevs=None):
        """Set values in array"""

        if values is not None:
            if np.isscalar(values):
                self.values = np.full(self.shape, values, dtype=np.float64)
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

        return  self

    def __add__(self, other):
        newinst = StdArray(shape=self.shape)
        if np.isscalar(other):
            try:
                newinst.values = self.values + other
                newinst.stdsq = self.stdsq.copy()
            except TypeError:
                newinst.values = np.full(self.shape, other, dtype=np.float64)
                newinst.stdsq = np.zeros(self.shape, dtype=np.float64)
        else:
            try:
                newinst.values = self.values + other.values
                newinst.stdsq = self.stdsq + other.stdsq
            except TypeError:
                newinst.values = other.values.copy()
                newinst.stdsq = other.stdsq.copy()
            except ValueError:
                raise StdArrayErr(INCOMPAT_SHAPE, "Incompatible arguement types")
        return  newinst

    def __radd__(self, other):
        return self.__add__(other)

    def __iadd__(self, other):
        try:
            if np.isscalar(other):
                self.values += other
            else:
                self.values += other.values
                self.stdsq += other.stdsq
        except TypeError:
            raise StdArrayErr(NOT_INITIALISED, "Array not initialised")
        except ValueError:
            raise StdArrayErr(INCOMPAT_SHAPE, "Incompatible arguement types")
        return self

    def __sub__(self, other):
        newinst = StdArray(shape=self.shape)
        if np.isscalar(other):
            try:
                newinst.values = self.values - other
                newinst.stdsq = self.stdsq.copy()
            except TypeError:
                newinst.values = np.full(self.shape, -other, dtype=np.float64)
                newinst.stdsq = np.zeros(self.shape, dtype=np.float64)
        else:
            try:
                newinst.values = self.values - other.values
                newinst.stdsq = self.stdsq + other.stdsq
            except TypeError:
                newinst.values = -other.values
                newinst.stdsq = other.stdsq.copy()
            except ValueError:
                raise StdArrayErr(INCOMPAT_SHAPE, "Incompatible arguement types")
        return  newinst

    def __rsub__(self, other):
        newinst = StdArray(shape=self.shape)
        if np.isscalar(other):
            try:
                newinst.values = other - self.values
                newinst.stdsq = self.stdsq.copy()
            except TypeError:
                newinst.values = np.full(self.shape, other, dtype=np.float64)
                newinst.stdsq = np.zeros(self.shape, dtype=np.float64)
        else:
            try:
                newinst.values = other.values - self.values
                newinst.stdsq = self.stdsq + other.stdsq
            except TypeError:
                newinst.values = other.values.copy()
                newinst.stdsq = other.stdsq.copy()
            except ValueError:
                raise StdArrayErr(INCOMPAT_SHAPE, "Incompatible arguement types")
        return  newinst

    def __isub__(self, other):
        try:
            if np.isscalar(other):
                self.values -= other
            else:
                self.values -= other.values
                self.stdsq += other.stdsq
        except TypeError:
            raise StdArrayErr(NOT_INITIALISED, "Array not initialised")
        except ValueError:
            raise StdArrayErr(INCOMPAT_SHAPE, "Incompatible arguement types")
        return  self

    def __mul__(self, other):
        newinst = StdArray(shape=self.shape)
        try:
            if np.isscalar(other):
                newinst.values = self.values * other
                newinst.stdsq = self.stdsq * other ** 2
            else:
                newinst.values = self.values * other.values
                newinst.stdsq = self.stdsq * other.values ** 2 + other.stdsq * self.values ** 2
        except TypeError:
            raise StdArrayErr(NOT_INITIALISED, "Array not initialised")
        except ValueError:
            raise StdArrayErr(INCOMPAT_SHAPE, "Incompatible arguement types")
        return  newinst

    def __rmul__(self, other):
        return self.__mul__(other)

    def __imul__(self, other):
        try:
            if np.isscalar(other):
                self.values *= other
                self.stdsq *= other * other
            else:
                self.stdsq = self.stdsq * other.values ** 2 + other.stdsq * self.values ** 2
                self.values *= other.values
        except TypeError:
            raise StdArrayErr(NOT_INITIALISED, "Array not initialised")
        except ValueError:
            raise StdArrayErr(INCOMPAT_SHAPE, "Incompatible arguement types")
        return  self

    def __truediv__(self, other):
        newinst = StdArray(shape=self.shape)
        with warnings.catch_warnings():
            warnings.simplefilter('error', RuntimeWarning)
            try:
                if np.isscalar(other):
                    newinst.values = self.values / other
                    newinst.stdsq = self.stdsq / other ** 2
                else:
                    newinst.values = self.values / other.values
                    newinst.stdsq = (self.stdsq + newinst.values ** 2 * other.stdsq) / other.values ** 2
            except TypeError:
                raise StdArrayErr(NOT_INITIALISED, "Array not initialised")
            except ValueError:
                raise StdArrayErr(INCOMPAT_SHAPE, "Incompatible arguement types")
            except RuntimeWarning:
                raise StdArrayErr(DIVBYZERO, "Division by zero")
        return  newinst

    def __rtruediv__(self, other):
        newinst = StdArray(shape=self.shape)
        with warnings.catch_warnings():
            warnings.simplefilter('error', RuntimeWarning)
            try:
                if np.isscalar(other):
                    newinst.values = other / self.values
                    newinst.stdsq = other ** 2 / self.stdsq ** 4
                else:
                    newinst.values = other.values / self.values
                    newinst.stdsq = (other.stdsq + newinst.values ** 2 * self.stdsq) / self.values ** 2
            except TypeError:
                raise StdArrayErr(NOT_INITIALISED, "Array not initialised")
            except ValueError:
                raise StdArrayErr(INCOMPAT_SHAPE, "Incompatible arguement types")
            except RuntimeWarning:
                raise StdArrayErr(DIVBYZERO, "Division by zero")
        return  newinst

    def __itruediv__(self, other):
        with warnings.catch_warnings():
            warnings.simplefilter('error', RuntimeWarning)
            try:
                if np.isscalar(other):
                    self.values /= other
                    self.stdsq /= other ** 2
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
