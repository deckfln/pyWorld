#cython: cdivision=True
#cython: boundscheck=False
#cython: wraparound=False
"""
@author deckfln
"""

cimport cython

from THREE.math.Vector3 import *

import sys
import numpy as np
cimport numpy as np
from cpython cimport array
import array
from libc.math cimport sqrt, floor
from libc.stdlib cimport malloc, free

from THREE.cython.cthree import *
from THREE.cython.cVector3 import cVector3_lerp

cdef _z1 = Vector3()
cdef _z2 = Vector3()
cdef _z3 = Vector3()
cdef _z4 = Vector3()

cdef void cVectorMap__get(np.ndarray[np.float32_t, ndim=1] map, int size, float x, float y, np.ndarray[np.float32_t, ndim=1] vec3 ):
    cdef int p = 3 * (int(x) + int(y)*size)

    vec3[0] = map[p]
    vec3[1] = map[p + 1]
    vec3[2] = map[p + 2]

cdef cVector3__copy(np.ndarray[np.float32_t, ndim=1] self, np.ndarray[np.float32_t, ndim=1] v):
    self[0] = v[0]
    self[1] = v[1]
    self[2] = v[2]

cpdef void cVectorMap_get(self, float x, float y, v3):
    cdef np.ndarray[np.float32_t, ndim=1] map = self.map
    cdef int size = self.size
    cdef np.ndarray[np.float32_t, ndim=1] vec3 = v3.np
    cdef int p = 3 * (int(x) + int(y)*size)

    vec3[0] = map[p]
    vec3[1] = map[p + 1]
    vec3[2] = map[p + 2]

cpdef void cVectorMap_add(self, float x, float y, v3):
    cdef np.ndarray[np.float32_t, ndim=1] map = self.map
    cdef int size = self.size
    cdef np.ndarray[np.float32_t, ndim=1] vec3 = v3.np
    cdef int p = int(3 * (x + y*size))

    map[p] += vec3[0]
    map[p + 1] += vec3[1]
    map[p + 2] += vec3[2]

cpdef void cVectorMap_bilinear(self, float x, float y, v3):
    cdef np.ndarray[np.float32_t, ndim=1] map = self.map
    cdef int size = self.size
    cdef np.ndarray[np.float32_t, ndim=1] vec3 = v3.np
    global _z1, _z2, _z3, _z4

    cdef float gridx = floor(x)
    cdef float offsetx = x - gridx
    cdef float gridy = floor(y)
    cdef float offsety = y - gridy

    cdef np.ndarray[np.float32_t, ndim=1] _z1np = _z1.np
    cdef np.ndarray[np.float32_t, ndim=1] _z2np = _z2.np
    cdef np.ndarray[np.float32_t, ndim=1] _z3np = _z3.np
    cdef np.ndarray[np.float32_t, ndim=1] _z4np = _z4.np

    if x == gridx and y == gridy:
        cVectorMap__get(map, size, x, y, vec3)
        return

    # bilinear interpolation

    cVectorMap__get(map, size, gridx, gridy, _z1np)
    if gridx < size - 1:
        cVectorMap__get(map, size, gridx + 1, gridy, _z2np)
        if gridy < size - 1:
            cVectorMap__get(map, size, gridx + 1, gridy + 1, _z3np)
        else:
            cVector3__copy(_z3np, _z1np)
    else:
        cVector3__copy(_z2np, _z1np)
        cVector3__copy(_z3np, _z1np)
    if gridy < size - 1:
        cVectorMap__get(map, size, gridx, gridy + 1, _z4np)
    else:
        cVector3__copy(_z4.np, _z1np)

    # https://forum.unity.com/threads/vector-bilinear-interpolation-of-a-square-grid.205644/
    cVector3_lerp(_z1np, _z2np, offsetx)
    cVector3_lerp(_z3np, _z4np, offsetx)
    cVector3_lerp(_z1np, _z3np, offsety)
    cVector3__copy(vec3, _z1np)

cpdef void cVectorMap_nearest(self, float x, float y, v3):
    cdef np.ndarray[np.float32_t, ndim=1] map = self.map
    cdef int size = self.size
    cdef np.ndarray[np.float32_t, ndim=1] vec3 = v3.np
    cdef float gridx = floor(x)
    cdef float offsetx = x - gridx
    cdef float gridy = floor(y)
    cdef float offsety = y - gridy

    if x == gridx and y == gridy:
        cVectorMap__get(map, size, x, y, vec3)

    if offsetx > 0.5:
        gridx += 1
    if offsety > 0.5:
        gridy += 1

    cVectorMap__get(map, size, gridx, gridy, vec3)

cpdef void cVectorMap_empty(np.ndarray[float, ndim=1] map , int size):
    cdef int s = size * size * 3
    cdef int i
    for i in range(0, s, 3):
        map[i ] = 0
        map[i + 1] = 0
        map[i + 2] = 1

cpdef void cVectorMap_normalize(self):
    cdef np.ndarray[np.float32_t, ndim=1] map = self.map
    cdef int size = self.size
    cdef np.ndarray[np.float32_t, ndim=1] np
    cdef int total = size * size * 3
    _z1 = Vector3()
    np = _z1.np

    for i in range(0, total, 3):
        np[0] = map[i]
        np[1] = map[i + 1]
        np[2] = map[i + 2]
        _z1.normalize()
        map[i] = np[0]
        map[i + 1] = np[1]
        map[i + 2] = np[2]
