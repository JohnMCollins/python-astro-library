# Polynomial evaluation functions

def polyeval(x, a):
    """Evaluate polynomial of X with coefficients a[0] = const term a[1] = coeff of x etc"""
    return  sum([j*k for j,k in zip(a,[x**p for p in range(0,len(a))])])

def areapol(x, a):
    """Compute the area under the polynomial given by coefficients a[0] = const term etc
    by integration"""
    return sum([j*k for j,k in zip(a,[x**p/float(p) for p in range(1,len(a)+1)])])
