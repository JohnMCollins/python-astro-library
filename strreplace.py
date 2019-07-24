import numpy as np

def strreplace(image, rs):
    """Replace things i> rs sttd evs from median with median"""
    med = np.median(image)
    s = rs * np.std(image)
    xc, yc = np.where(image - med > s)
    for x, y in zip(xc, yc):
        image[x,y] = med
    return image