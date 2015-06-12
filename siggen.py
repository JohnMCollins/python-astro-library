# For generating possible periodic signals

import numpy as np
import numpy.random as nr

def siggen(pers, amps = 1, ntimes = 100, npers = 10.0, randv = 0.0, unorm = 0.0, randphase = False):
    """Generate a signal from a list of periods or single period
    amps gives amplitude for each or a scalar for all
    ntimes gives the total number of samples to take
    npers gives the total multiple of the maximum period to take
    randv gives the amount by which the sample times are randomly adjusted
    unorm (0 to 1) gives the proportion of uniform to gaussian Adjustment
    randphase gives a random phase to each signal

    Return a tuple of sampling times and amplitudes"""

    if np.isscalar(pers):
        pers = (pers, )

    if np.isscalar(amps):
        amps = np.zeros_like(pers, np.float64) + amps

    timelist, stepsize = np.linspace(0, npers * np.max(pers), ntimes, retstep=True)

    # Possibly adjust the stepsize randomly

    if randv > 0.0:
        maxtime = np.max(timelist)
        dt = stepsize * randv
        adjs = nr.uniform(-dt, dt, size = ntimes) * (1.0 - unorm) * nr.normal(scale = dt, size = ntimes) * unorm
        timelist += adjs
        timelist.sort()
        timelist -= timelist[0]
        timelist *= maxtime / np.max(timelist)

    amps = list(amps)
    if randphase:
        phases = nr.uniform(0, 2.0 * np.pi, size=len(pers))
    else:
        phases = np.zeros(len(pers))

    ampres = [0.0] * ntimes

    freqs = list(2.0 * np.pi / np.array(pers))

    for fr, amp, phas in zip(freqs, amps, phases):
        ampres += amp * np.sin(timelist * fr + phas)

    return (timelist, ampres)


    