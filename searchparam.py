"""Save search param settings"""

import xml.etree.ElementTree as ET
import xmlutil
import configfile

# These are the default values for the seqrch parameters

DEFAULT_SIGN = 1.5
DEFAULT_TOTSIGN = .75
DEFAULT_MAXSHIFT = 10.0
DEFAULT_SHIFT2 = 5.0
DEFAULT_LOOKAROUND = 3.0
DEFAULT_DEFAPSIZE = 6.0
DEFAULT_NSIGMAAP = 2.5
DEFAULT_MINAP = 3.0
DEFAULT_MAXAP = 20.0
DEFAULT_APSTEP = 1.0
DEFAULT_SINGLEPIX = 7.5

class SearchParamErr(Exception):
    """Throw in case of errors"""


Field_names = dict(signif=(DEFAULT_SIGN,
                             "Multiple of std devs above sky level to consider point significant"),
                    totsig=(DEFAULT_TOTSIGN,
                              "Total nomber of std devs to consider a peak significant"),
                    maxshift=(DEFAULT_MAXSHIFT,
                               "Max displacement from expected position to consider on initial search "),
                    maxshift2=(DEFAULT_SHIFT2,
                               "Max displacement from expected position to consider on subsequent search "),
                    lookaround=(DEFAULT_LOOKAROUND,
                                "Displacement to look around after finding approximate peak"),
                    singlepixn=(DEFAULT_SINGLEPIX,
                                "Multiple of signle pixels to treat single pixel as important"),
                    defapsize=(DEFAULT_DEFAPSIZE,
                                "Default aperture size if none given"),
                    nsigmaap=(DEFAULT_NSIGMAAP,
                              "Number of sigmas of fit to take as aperture"),
                    minap=(DEFAULT_MINAP,
                            "Minimum aperture size when optimising aperture"),
                    maxap=(DEFAULT_MAXAP,
                            "Maximum aperture size when optimising aperture"),
                    apstep=(DEFAULT_APSTEP,
                            "Step in aperture size when optimising aperture"))


class SearchParam:
    """Remember search params"""

    def __init__(self):
        self.signif = DEFAULT_SIGN
        self.totsig = DEFAULT_TOTSIGN
        self.maxshift = DEFAULT_MAXSHIFT
        self.lookaround = DEFAULT_LOOKAROUND
        self.defapsize = DEFAULT_DEFAPSIZE
        self.singlepixn = DEFAULT_SINGLEPIX
        self.nsigmaap = DEFAULT_NSIGMAAP
        self.minap = DEFAULT_MINAP
        self.maxap = DEFAULT_MAXAP
        self.apstep = DEFAULT_APSTEP
        self.saveparams = False

    def load(self, node):
        """Load parameters from XML file"""
        self.saveparams = False
        for f, v in Field_names.items():
            defv, dummy = v
            setattr(self, f, defv)
        for child in node:
            tagn = child.tag
            try:
                setattr(self, tagn, xmlutil.getfloat(child))
            except KeyError:
                pass

    def save(self, doc, pnode, name):
        """Save to XML DOM node"""
        node = ET.SubElement(pnode, name)
        for tagn in Field_names:
            xmlutil.savedata(doc, node, tagn, getattr(self, tagn))
        return  node

    def argparse(self, argp):
        """Initialise arg parser with search options"""
        for f, v in Field_names.items():
            dummy, helpm = v
            argp.add_argument('--' + f, type=float, default=getattr(self, f, 0), help=helpm)
        argp.add_argument('--searchsave', action='store_true', help='Save new search parametrs file')

    def getargs(self, resargs):
        """Get search options"""

        for f in Field_names:
            setattr(self, f, resargs[f])
        self.saveparams = resargs['searchsave']

    def display(self, outfile):
        """Output search parameters"""
        print("Search parameters:\n", file=outfile)
        maxn = maxh = 0
        for f, v in Field_names.items():
            defv, hlp = v
            maxn = max(maxn, len(f))
            maxh = max(maxh, len(hlp))
        for f, v in Field_names.items():
            val = getattr(self, f, 0)
            defv, hlp = v
            print("{nam:{naml}s} {hlp:{hlpl}s} {val:#10.4g} (def: {defv:#10.4g}".format(nam=f, naml=maxn, hlp=hlp, hlpl=maxh, val=val, defv=defv), file=outfile)

def load(fname=None, mustexist=False):
    """Load search params from file"""
    if fname is None:
        fname = "searchparams"
    ret = SearchParam()
    try:
        dr = configfile.load(fname, "SEARCHPAR")
    except configfile.ConfigError as e:
        raise SearchParamErr(e.args[0])
    if dr is None:
        if mustexist:
            raise SearchParamErr("Cannot open " + fname)
        return ret
    for child in dr[1]:
        if child.tag == "searchp":
            ret.load(child)
    return ret


def save(rg, fname=None):
    """Save search params to file"""
    if fname is None:
        fname = "searchparams"
    doc, root = configfile.init_save("SEARCHPAR")
    rg.save(doc, root, "searchp")
    try:
        configfile.complete_save(doc, fname)
    except configfile.ConfigError as e:
        raise SearchParamErr(e.args[0])
