# Convert numpy array velocities to wavelengths

C = 299792.458

def veltowavel(basewl, velarry):
    """Convert 2nd arg array of velocities to wavelengths"""
    cfn = lambda x: basewl * (1.0 + x/C)
    return cfn(velarry)

