"""
@author deckfln
"""

cimport cython

import numpy as np
cimport numpy as np
from libc.math cimport sqrt, floor

def c_bilinear(np.ndarray[float, ndim=1] map, int size, double x, double y):

    cdef int gridx = int(x)
    cdef int gridy = int(y)

    if x == gridx and y == gridy:
        return map[gridx + size * gridy]

    # bilinear interpolation
    cdef double offsetx = x - gridx
    cdef double offsety = y - gridy

    cdef double z1 = map[gridx + gridy * size]
    cdef double z2
    cdef double z3
    cdef double z4

    if gridx < size - 1:
        z2 = map[gridx + 1 + gridy * size]
        if gridy < size - 1:
            z3 = map[gridx + 1 + (gridy + 1) * size]
        else:
            z3 = z1
    else:
        z2 = z1
        z3 = z1
    if gridy < size - 1:
        z4 = map[gridx + (gridy + 1) * size]
    else:
        z4 = z1

    if offsetx > offsety:
        z = z1 - offsetx * (z1 - z2) - offsety * (z2 - z3)
    else:
        z = z1 - offsetx * (z4 - z3) - offsety * (z1 - z4)

    return z
