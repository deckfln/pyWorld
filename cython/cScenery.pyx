#cython: cdivision=True
#cython: boundscheck=False
#cython: wraparound=False
"""
@author deckfln
"""

cimport cython

from THREE.Vector2 import *
from THREE.Vector3 import *
from prng import *

import sys
import numpy as np
cimport numpy as np
from cpython cimport array
import array
from libc.math cimport sqrt, floor
from libc.stdlib cimport malloc, free
from libc.string cimport memcpy

from cHeightmap import cHeightmap_bilinear
from cVectorMap import *

cdef object _tm = Vector2()
cdef object _im = Vector2()
cdef object _vector3 = Vector3()

rand = Random(0)

"""
"
"""
cdef class _scenery:
    cdef public next
    cdef int size
    cdef positions
    cdef normals
    cdef public int index

    def __init__(self):
        self.next = None
        self.size = 0
        self.positions = None
        self.normals = None
        self.index = 0

    def set(_scenery self, int i, _scenery next):
        self.index = i
        self.next = next

    def init(_scenery self, densities, instance, int x, int y, terrain, heightmap, normalMap):
        rand.seed = abs(x*y) * (instance + 1) + 7
        cdef float density = densities[instance]

        cdef int instances = 0

        cdef int nb = int(density*10)
        if nb == 0:
            self.size = 0
            return

        if self.positions is None:
            self.positions = np.zeros(nb*3, dtype=np.float32)
            self.normals = np.zeros(nb * 3, dtype=np.float32)
        elif nb > self.size:
            self.positions = np.zeros(nb*3, dtype=np.float32)
            self.normals = np.zeros(nb * 3, dtype=np.float32)

        self.size = nb
        cdef np.ndarray[float, ndim=1] positions = self.positions
        cdef np.ndarray[float, ndim=1] normals = self.normals

        cdef int i
        cdef float dx
        cdef float dy
        cdef float z
        cdef np.ndarray[float, ndim=1] vec3

        for i in range(nb):
            dx = rand.random()*2 - 1 + x
            dy = rand.random()*2 - 1 + y

            terrain.screen2mapXY(dx, dy, _tm)
            z = heightmap.bilinear(_tm.x, _tm.y)

            normalMap.nearest(_tm.x, _tm.y, _vector3)
            vec3 = _vector3.np

            positions[instances] = dx
            positions[instances + 1] = dy
            positions[instances + 2] = z

            normals[instances] = vec3[0]
            normals[instances + 1] = vec3[1]
            normals[instances + 2] = vec3[2]

            instances += 3

    def concatenate(_scenery self, geometry):
        if not self.size:
            return True

        # if self.loaded:
        #    return True

        cdef np.ndarray[float, ndim=1] positions = self.positions
        cdef np.ndarray[float, ndim=1] normal = self.normals
        cdef int le = self.size*3
        cdef np.ndarray[float, ndim=1] offset = geometry.attributes.offset.array
        cdef np.ndarray[float, ndim=1] normals = geometry.attributes.normals.array
        cdef int nb = geometry.maxInstancedCount

        cdef int i = nb * 3

        cdef float *dest = &offset[i]
        cdef float *source = &positions[0]
        memcpy (dest, source, le*sizeof(float))

        dest = &normals[i]
        source = &normal[0]
        memcpy (dest, source, le*sizeof(float))

        #offset[i:i + le] = positions[0:le]
        #normals[i:i + le] = normal[0:le]

        nb += le / 3
        geometry.maxInstancedCount = nb

        return True


"""
"""
# keep a global list of sceneris
_sceneries = [_scenery() for i in range(8192*6)]
_first = _sceneries[8191*6]

for i in range(8191*6, -1, -1):
    _sceneries[i].set(i, _sceneries[i - 1])


cpdef _allocate(densities, instance, x, y, terrain, heightmap, normalMap):
    global _first, _sceneries
    cdef _scenery allocated = _first
    allocated.init(densities, instance, x, y, terrain, heightmap, normalMap)
    if allocated.size > 0:
        _first = allocated.next
    else:
        allocated = None
    return allocated


cpdef _free(_scenery scenery):
    global _first, _sceneries
    scenery.next = _first
    _first = scenery

"""
"
"""
cdef class _spot:
    cdef _scenery grass
    cdef _scenery high_grass
    cdef _scenery prairie
    cdef _scenery fern
    cdef _scenery shrub
    cdef _scenery forest2
    cdef _buffer

    def __init__(_spot self, _scenery grass, _scenery high_grass, _scenery prairie, _scenery fern, _scenery shrub, _scenery forest2):
        self.grass = grass
        self.high_grass = high_grass
        self.prairie = prairie
        self.fern = fern
        self.shrub = shrub
        self.forest2 = forest2

    def free(self):
        if self.grass is not None:
            _free(self.grass)
        if self.high_grass is not None:
            _free(self.high_grass)
        if self.prairie is not None:
            _free(self.prairie)
        if self.fern is not None:
            _free(self.fern)
        if self.shrub is not None:
            _free(self.shrub)
        if self.forest2 is not None:
            _free(self.forest2)

    def concatenate(self, geometries):
        if self.grass is not None:
            self.grass.concatenate(geometries[0])

        if self.high_grass is not None:
            self.high_grass.concatenate(geometries[1])

        if self.prairie is not None:
            self.prairie.concatenate(geometries[2])

        if self.fern is not None:
            self.fern.concatenate(geometries[3])

        if self.shrub is not None:
            self.shrub.concatenate(geometries[4])

        if self.forest2 is not None:
            self.forest2.concatenate(geometries[5])

"""

"""
def c_instantiate(object self, int px, int py, object terrain, object assets):
        # parse the quad
        cdef int size = 24  # int(quad.size / 2)
        cdef int terrain_size = terrain.size / 2

        cdef int _px = px - size
        cdef int _py = py - size
        if _px <= -terrain_size:
            _px = -terrain_size + 1
        if _py <= -terrain_size:
            _py = -terrain_size + 1

        cdef int _p2x = px + size
        cdef int _p2y = py + size
        if _p2x >= terrain.size:
            _p2x = terrain.size - 1
        if _p2y >= terrain.size:
            _p2y = terrain.size - 1

        cdef object geometries = [assets.get(asset_name).geometry for asset_name in ("grass", "high grass", "grass", "forest", "forest1", 'forest2')]

        cdef cache = self.cache
        indexmap = terrain.indexmap
        normalMap = terrain.normalMap
        heightmap = terrain.heightmap

        cdef int x = _px
        cdef int y
        cdef int dx
        cdef int dx2
        cdef int d
        cdef str k
        cdef s

        while x < _p2x:
            dx = px - x
            dx2 = dx * dx
            y = _py
            while y < _p2y:
                # only sample points inside the player 16 radius
                dy = py - y
                d = dx2 + dy * dy

                if d <= 196 or (d <= 256 and x % 2 == 0 and y % 2 == 0) or (d <= 312 and x % 4 == 0 and y % 4 == 0):
                    k = "%d:%d" % (x, y)
                    if k not in cache:
                        terrain.screen2mapXY(x, y, _tm)

                        # do not put scenery on roads or rivers
                        if terrain.isRiverOrRoad(_tm):
                            continue

                        # get the density of each ground type
                        terrain.heightmap2indexmap(_tm, _im)
                        s = indexmap.bilinear_density(_im.x, _im.y)
                        if s is None:
                            raise RuntimeError("ProceduralScenery : p_instantiate indexmap.bilinear_density is None ", x, y, _im.x, _im.y)

                        # now pick the density of grass
                        grass = _allocate(s, 0, x, y, terrain, heightmap, normalMap)
                        high_grass = _allocate(s, 1, x, y, terrain, heightmap, normalMap)
                        prairie = _allocate(s, 2, x, y, terrain, heightmap, normalMap)
                        fern = _allocate(s, 3, x, y, terrain, heightmap, normalMap)
                        shrub = _allocate(s, 4, x, y, terrain, heightmap, normalMap)
                        forest2 = _allocate(s, 5, x, y, terrain, heightmap, normalMap)

                        cache[k] = _spot(grass, high_grass, prairie, fern, shrub, forest2)

                        self.fifo.append(k)

                        if len(cache) > 8192:
                            k1 = self.fifo.pop(0)
                            cache[k1].free()
                            del cache[k1]

                    cache[k].concatenate(geometries)
                y += 1
            x += 1

        for geometry in geometries:
            if geometry.maxInstancedCount > 0:
                geometry.attributes.offset.needsUpdate = True
                geometry.attributes.normals.needsUpdate = True
