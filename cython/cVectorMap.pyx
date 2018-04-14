#cython: cdivision=True
#cython: boundscheck=False
#cython: wraparound=False
"""
@author deckfln
"""

cimport cython

from THREE.Vector3 import *

import sys
import numpy as np
cimport numpy as np
from cpython cimport array
import array
from libc.math cimport sqrt, floor
from libc.stdlib cimport malloc, free

from THREE.cython.cthree import *

cdef _z1 = THREE.Vector3()
cdef _z2 = THREE.Vector3()
cdef _z3 = THREE.Vector3()
cdef _z4 = THREE.Vector3()

cpdef void cVectorMap_get(np.ndarray[float, ndim=1] map , int size, float x, float y,  np.ndarray[float, ndim=1] vec3 ):
    cdef int p = int(3 * (x + y*size))

    vec3[0] = map[p]
    vec3[1] = map[p + 1]
    vec3[2] = map[p + 2]

cpdef void cVectorMap_bilinear(np.ndarray[float, ndim=1] map , int size, float x, float y,  np.ndarray[float, ndim=1] vec3 ):
    global _z1, _z2, _z3, _z4

    cdef float gridx = floor(x)
    cdef float offsetx = x - gridx
    cdef float gridy = floor(y)
    cdef float offsety = y - gridy

    if x == gridx and y == gridy:
        cVectorMap_get(map, size, x, y, vec3)
        return

    # bilinear interpolation

    cVectorMap_get(map, size, gridx, gridy, _z1.np)
    if gridx < size - 1:
        cVectorMap_get(map, size, gridx + 1, gridy, _z2.np)
        if gridy < size - 1:
            cVectorMap_get(map, size, gridx + 1, gridy + 1, _z3.np)
        else:
            cVector3_copy(_z3.np, _z1.np)
    else:
        cVector3_copy(_z2.np, _z1.np)
        cVector3_copy(_z3.np, _z1.np)
    if gridy < size - 1:
        cVectorMap_get(map, size, gridx, gridy + 1, _z4.np)
    else:
        cVector3_copy(_z4.np, _z1.np)

    # https://forum.unity.com/threads/vector-bilinear-interpolation-of-a-square-grid.205644/
    cVector3_lerp(_z1.np, _z2.np, offsetx)
    cVector3_lerp(_z3.np, _z4.np, offsetx)
    cVector3_lerp(_z1.np, _z3.np, offsety)
    cVector3_copy(vec3, _z1.np)

cpdef void cVectorMap_nearest(np.ndarray[float, ndim=1] map , int size, float x, float y, np.ndarray[float, ndim=1] vec3 ):
    cdef float gridx = floor(x)
    cdef float offsetx = x - gridx
    cdef float gridy = floor(y)
    cdef float offsety = y - gridy

    if x == gridx and y == gridy:
        cVectorMap_get(map, size, x, y, vec3)

    if offsetx > 0.5:
        gridx += 1
    if offsety > 0.5:
        gridy += 1

    cVectorMap_get(map, size, gridx, gridy, vec3)
