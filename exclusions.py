# Remember data we aren't displaying.

import string
import re

class ExcludeError(Exception):
    """Class to use for errors in exclusions"""
    pass

class Exclusions(object):
    """Class for remembering exclusions with"""

    def __init__(self):
        self.exclist = dict()

    def add(self, dat, expl):
        """Add an excluded obs date to file with explanation"""
        self.exclist[dat] = expl

    def load(self, fname):
        """Load exclusion list from given file name"""
        try:
            ef = open(fname)
        except IOError as e:
            raise ExcludeError("Cannot open exclude file", e.args[1])
        te = re.compile('([-+\d.e]+)\s+(.*)')
        try:
            for line in ef:
                line = string.strip(line)
                bits = te.match(line)
                if bits is None:
                    raise ExcludeError("Failed to match line in exclude file", line)
                dat = float(bits.group(1))
                expl = bits.group(2)
                self.exclist[dat] = expl
        except ExcludeError:
            raise
        except ValueError:
            raise ExcludeError("Invalid float in exclude file", line)
        finally:
            ef.close()

    def save(self, fname):
        """Save exclusion list to given file name"""
        dats = list(self.exclist.keys())
        dats.sort()
        try:
            ef = open(fname, 'w')
        except IOError as e:
            raise ExcludeError("Cannot write exclude file", e.args[1])
        for d in dats:
            ef.write("%.18e %s\n" % (d, self.exclist[d]))
        ef.close()

    def reasons(self):
        """Get list of explanations for assigning colours"""
        ret = list(set(self.exclist.values()))
        ret.sort()
        return  ret

    def places(self):
        """Get places where exclusions occur in order"""
        ret = list(self.exclist.keys())
        ret.sort()
        return  ret

    def inrange(self, minr, maxr):
        """Get a new list in range"""
        ret = Exclusions()
        for k,v in list(self.exclist.items()):
            if minr <= k <= maxr:   ret.add(k, v)
        return  ret

    def getreason(self, val):
        """Get the reason for a specific exclusion"""
        try:
            return self.exclist[val]
        except KeyError:
            return ""
