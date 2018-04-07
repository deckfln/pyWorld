"""
@author deckfln
"""

cimport cython

from THREE.Vector2 import *

import numpy as np
cimport numpy as np
from cpython cimport array
import array
from libc.math cimport sqrt, floor

_tm = Vector2()
_im = Vector2()

@cython.boundscheck(False) # turn off bounds-checking for entire function
@cython.wraparound(False)  # turn off negative index wrapping for entire function
cpdef void _concatenate_spots(np.ndarray[float, ndim=1] spot, object geometry):
    cdef int le = len(spot)
    cdef int i
    cdef int t

    cdef np.ndarray[float, ndim=1] offset = geometry.attributes.offset.array
    cdef int nb = geometry.maxInstancedCount

    i = nb * 3
    offset[i:i+le] = spot[:]

    geometry.maxInstancedCount += le/3

@cython.cdivision(True)
@cython.boundscheck(False) # turn off bounds-checking for entire function
@cython.wraparound(False)  # turn off negative index wrapping for entire function
def _instantiate_for_spot(double x, double y, double density, terrain, self):
    """
    instantiate one ground type at the current spot
    :param s:
    :param ground_type:
    :param asset_name:
    :return:
    """
    cdef np.ndarray[float, ndim=1] instances
    cdef double _p1x
    cdef double _p1y
    cdef double z

    _tm = Vector2()

    if density < 0.25:
        return None

    if density < 0.50:
        displacement = self.displace(x, y)
        _p1x = x + displacement.x * 2
        _p1y = y + displacement.x * 2

        terrain.screen2mapXY(_p1x, _p1y, _tm)
        z = terrain.heightmap.bilinear(_tm.x, _tm.y)

        return np.array([_p1x, _p1y, z], dtype=np.float32)

    # the higher the desity, the smaller the step to generate instances
    cdef int mx
    cdef int step
    cdef double dstep
    cdef int tx
    cdef int ty

    if density < 0.75:
        step = 2
        dstep = 0.5
        mx = 9*3
    else:
        step = 1
        dstep = 0.25
        mx = 25*3

    # map the step on the upper loop -6 -> 6  <=> -1 -> 1
    instances = np.zeros(mx, dtype=np.float32)
    i = 0

    # map the step on the upper loop -6 -> 6  <=> -1 -> 1
    for tx in range(-2, 3, step):
        _p1x = x + tx / 2
        for ty in range(-2, 3, step):
            _p1y = y + ty / 2

            displacement = self.displace(_p1x, _p1y)

            _p1x += displacement.x * dstep
            _p1y += displacement.y * dstep

            terrain.screen2mapXY(_p1x, _p1y, _tm)
            z = terrain.heightmap.bilinear(_tm.x, _tm.y)

            instances[i] = _p1x
            instances[i + 1] = _p1y
            instances[i + 2] = z

            i += 3

    return instances

"""

"""
def c_instantiate(object self, int px, int py, object terrain, object quad, object assets):

    # parse the quad
    cdef int size = quad.size / 2
    cdef int _px = quad.center.x - size
    cdef int _py = quad.center.y - size

    cdef int _p2x = quad.center.x + size
    cdef int _p2y = quad.center.y + size

    cdef int nbspots = 0

    cdef list geometries = [assets.get(asset_name).geometry for asset_name in ("grass", "high grass", "prairie", "fern", "shrub")]
    cdef dict cache = self.cache

    cdef int x
    cdef int y

    cdef int dx
    cdef int dx2
    cdef int dy
    cdef int d

    cdef int i
    cdef list cached

    global _tm
    global _im

    for x in range(_px, _p2x, 2):
        dx = px - x
        dx2 = dx * dx
        for y in range(_py, _p2y, 2):

            # only sample points inside the player 16 radius
            dy = py - y
            d = dx2 + dy * dy

            if d > 256:
                continue

            k = "%d:%d" % (x, y)
            if k not in cache:
                terrain.screen2mapXY(x, y, _tm)

                # do not put scenery on roads or rivers
                if terrain.isRiverOrRoad(_tm):
                    continue

                # get the density of each ground type
                terrain.heightmap2indexmap(_tm, _im)
                s = terrain.indexmap.bilinear_density(_im.x, _im.y)
                if s is None:
                    continue

                # now pick the density of grass
                cache[k] = [
                    _instantiate_for_spot(x, y, s[0], terrain, self),
                    _instantiate_for_spot(x, y, s[1], terrain, self),
                    _instantiate_for_spot(x, y, s[2], terrain, self),
                    _instantiate_for_spot(x, y, s[3], terrain, self),
                    _instantiate_for_spot(x, y, s[4], terrain, self)
                    ]

                self.fifo.append(k)

                if len(self.cache) > 1024:
                    k1 = self.fifo.pop(0)
                    del self.cache[k1]

            cached = cache[k]

            for i in range(5):
                if cached[i] is not None:
                    _concatenate_spots(cached[i], geometries[i])

        for i in range(5):
            if geometries[i].maxInstancedCount > 0:
                geometries[i].attributes.offset.needsUpdate = True
