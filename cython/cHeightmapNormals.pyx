"""
@author deckfln
"""

cimport cython

import numpy as np
cimport numpy as np
from libc.math cimport sqrt, floor

from cVectorMap import *
from progress import *

from THREE.math.Vector3 import *
from THREE.math.Vector2 import *


cpdef float cHeightmap_get(np.ndarray[float, ndim=1] map, int size, int x, int y):
    cdef int p
    p = x + y * size
    return map[p]


cpdef void cTerrain_map2screenXY(float ratio, float half, float x, float y, np.ndarray[float, ndim=1] target):
    """
    convert heightmap (max level) coord to screen coordinate
    :param position:
    :return:
    """
    target[0] = x * ratio - half
    target[1] = y * ratio - half


cpdef void cVector3_set(np.ndarray[float, ndim=1] target, float x, float y, float z):
    target[0] = x
    target[1] = y
    target[2] = z


cpdef void cVector3_subVectors(np.ndarray[float, ndim=1] self, np.ndarray[float, ndim=1] a, np.ndarray[float, ndim=1] b ):
    self[0] = a[0] - b[0]
    self[1] = a[1] - b[1]
    self[2] = a[2] - b[2]


cpdef void cVector3_cross(np.ndarray[float, ndim=1] self, np.ndarray[float, ndim=1] v):
    cdef float x = self[0]
    cdef float y = self[1]
    cdef float z = self[2]

    self[0] = y * v[2] - z * v[1]
    self[1] = z * v[0] - x * v[2]
    self[2] = x * v[1] - y * v[0]


def cbuild_normalmap(terrain, np.ndarray[float, ndim=1] heightmap, int heightmap_size, np.ndarray[float, ndim=1] normalMap, int normalMap_size):
    """
    compute the normal map of the top heightmap
    :param heightmap:
    :param normalMap:
    :return:
    """
    cdef int current
    cdef int total
    cdef int x
    cdef int y
    cdef float zA
    cdef float zB
    cdef float zC
    cdef float ratio
    cdef float terrain_half
    cdef int pointer

    ratio = terrain.ratio_screen_2_map
    half = terrain.half

    pA = Vector3()
    pB = Vector3()
    pC = Vector3()
    cb = Vector3()
    ab = Vector3()

    cdef np.ndarray[float, ndim=1] pAnp = pA.np
    cdef np.ndarray[float, ndim=1] pBnp = pB.np
    cdef np.ndarray[float, ndim=1] pCnp = pC.np
    cdef np.ndarray[float, ndim=1] cbnp = cb.np
    cdef np.ndarray[float, ndim=1] abnp = ab.np

    cVectorMap_empty(normalMap, normalMap_size)

    current = 0
    total = heightmap_size * heightmap_size

    # // for each vertex, compute the face normal, and add to the vertex normal
    mA = Vector2()
    mB = Vector2()
    mC = Vector2()

    cdef np.ndarray[float, ndim=1] mAnp = mA.np
    cdef np.ndarray[float, ndim=1] mBnp = mB.np
    cdef np.ndarray[float, ndim=1] mCnp = mC.np

    y = 0
    while y < heightmap_size-1:
        x = 0
        pointer = y * heightmap_size

        while x < heightmap_size-1:
            if y > 0:
                # // normalize Z againt the heightmap size
                zA = heightmap[pointer - heightmap_size] # , x, y-1)
                zB = heightmap[pointer + 1]              # x+1, y)
                zC = heightmap[pointer]                  # x, y

                cTerrain_map2screenXY(ratio, half, x, y-1, mAnp)
                cTerrain_map2screenXY(ratio, half, x+1, y, mBnp)
                cTerrain_map2screenXY(ratio, half, x, y, mCnp)

                cVector3_set(pAnp, mAnp[0], mAnp[1], zA)
                cVector3_set(pBnp, mBnp[0], mBnp[1], zB)
                cVector3_set(pCnp, mCnp[0], mCnp[1], zC)

                cVector3_subVectors(cbnp, pCnp, pBnp )
                cVector3_subVectors(abnp, pAnp, pBnp )
                cVector3_cross(cbnp, abnp )

                cVectorMap_add(normalMap, normalMap_size, x, y-1, cbnp)
                cVectorMap_add(normalMap, normalMap_size, x+1, y, cbnp)
                cVectorMap_add(normalMap, normalMap_size, x, y, cbnp)

            zA = heightmap[pointer]                     # , x, y)
            zB = heightmap[pointer + 1]                 # , x+1, y)
            zC = heightmap[pointer + 1 + heightmap_size]     #, x+1, y+1)

            cTerrain_map2screenXY(ratio, half, x, y, mAnp)
            cTerrain_map2screenXY(ratio, half, x+1, y, mBnp)
            cTerrain_map2screenXY(ratio, half, x+1, y+1, mCnp)

            cVector3_set(pAnp, mAnp[0], mAnp[1], zA)
            cVector3_set(pBnp, mBnp[0], mBnp[1], zB)
            cVector3_set(pCnp, mCnp[0], mCnp[1], zC)

            cVector3_subVectors(cbnp, pCnp, pBnp )
            cVector3_subVectors(abnp, pAnp, pBnp )
            cVector3_cross(cbnp, abnp )

            cVectorMap_add(normalMap, normalMap_size, x, y, cbnp)
            cVectorMap_add(normalMap, normalMap_size, x+1, y, cbnp)
            cVectorMap_add(normalMap, normalMap_size, x+1, y+1, cbnp)

            current += 1
            x += 1
            pointer += 1

        y += 1
        progress(current, total, "Build normalMap")

    # // normalize the normals
    cVectorMap_normalize(normalMap, normalMap_size)

    progress(0, 0)