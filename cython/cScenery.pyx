#cython: cdivision=True
#cython: boundscheck=False
#cython: wraparound=False
"""
@author deckfln
"""

cimport cython

from THREE.Vector2 import *
from THREE.Vector3 import *

import sys
import numpy as np
cimport numpy as np
from cpython cimport array
import array
from libc.math cimport sqrt, floor
from libc.stdlib cimport malloc, free

from cHeightmap import cHeightmap_bilinear
from cVectorMap import *

cdef object _tm = Vector2()
cdef object _im = Vector2()
cdef object _vector3 = Vector3()

cdef float *_buffer = <float *>malloc(65536 * 3 * sizeof(float))
cdef int _first1 = -1
cdef int _first9 = -1
cdef int _first25 = -1
cdef int _buffer_size = 0


"""
"
"""
cpdef int _displace(float x, float y):
    cdef float x1 = x + 256
    cdef float y1 = y + 256

    cdef int x2 = int(x1)
    cdef int y2 = int(y1)

    cdef int fx = int((x1 - x2) * 32)
    cdef int fy = int((y1 - y2) * 32)

    return (x2 / 16 + fx) * 2 + (y2 / 16 + fy)*128

"""
"
"""
cdef class _scenery:
    cdef int instances
    cdef int normals
    cdef int size

    def __init__(_scenery self, float density, int x, int y, terrain, heightmap, normalMap, np.ndarray[float, ndim=1] displacement_map not None):
        global _buffer_size, _first1, _first9, _first25, _buffer
        cdef int first
        cdef int size

        if density < 0.25:
            self.size = 0
            return
        elif density < 0.5:
            first = _first1
            size = 1
        elif density < 0.75:
            first = _first9
            size = 9
        else:
            first = _first25
            size = 25

        if first < 0:
            first = _buffer_size
            _buffer_size += size*2*3
            if _buffer_size > 65536*3:
                print("cScenery: _buffer_size exceed limit")
                sys.exit(-1)
        else:
            if size == 1:
                _first1 = int(_buffer[first])
            elif size == 9:
                _first9 = int(_buffer[first])
            else:
                _first25 = int(_buffer[first])

        self.instances = first
        self.normals = first + size*3
        self.size = size

        cdef int instances = self.instances
        cdef int normals = self.normals
        cdef int step
        cdef float dstep

        if size == 1:
            step = 4
            dstep = 4
        elif size == 9:
            step = 2
            dstep = 2
        else:
            step = 1
            dstep = 1

        cdef int tx
        cdef int ty
        cdef float _p1x
        cdef float _p1y
        cdef int displacement
        cdef float z
        cdef np.ndarray[float, ndim=1] vec3 = _vector3.np
        cdef np.ndarray[float, ndim=1] heightmap_map = heightmap.map
        cdef int heightmap_size = heightmap.size
        cdef np.ndarray[float, ndim=1] normal_map = normalMap.map
        cdef int normal_size = normalMap.size
        cdef tmx, tmy

        tx = -2
        while tx < 3:
            _p1x = x + tx / 2
            ty = -2
            while ty < 3:
                _p1y = y + ty / 2

                displacement = _displace(_p1x, _p1y)

                _p1x += displacement_map[displacement] * dstep
                _p1y += displacement_map[displacement + 1] * dstep

                terrain.screen2mapXY(_p1x, _p1y, _tm)
                tmx = _tm.x
                tmy = _tm.y
                z = cHeightmap_bilinear(heightmap_map, heightmap_size, tmx, tmy)
                cVectorMap_nearest(normal_map, normal_size, tmx, tmy, vec3)

                _buffer[instances] = _p1x
                _buffer[instances + 1] = _p1y
                _buffer[instances + 2] = z

                _buffer[normals] = vec3[0]
                _buffer[normals + 1] = vec3[1]
                _buffer[normals + 2] = vec3[2]

                normals += 3
                instances += 3

                ty += 2
            tx += 2

    def free(_scenery self):
        global _buffer_size, _first1, _first9, _first25, _buffer
        if not self.size:
            return

        cdef int first

        if self.size == 1:
            first = _first1
        elif self.size == 9:
            first = _first9
        else:
            first = _first25

        _buffer[self.instances] = float(first)

        if self.size == 1:
            _first1 = self.instances
        elif self.size == 9:
            _first9 = self.instances
        else:
            _first25 = self.instances

    def concatenate(_scenery self, geometry):
        global _buffer
        if not self.size:
            return

        cdef int instances = self.instances
        cdef int normals = self.normals

        cdef int le = self.size*3

        cdef attributes = geometry.attributes
        cdef np.ndarray[float, ndim=1, mode="c"] offset = attributes.offset.array
        cdef np.ndarray[float, ndim=1, mode="c"] normal = attributes.normals.array
        cdef float *offset_p = <float *>&offset[0]
        cdef float *normal_p = <float *>&normal[0]

        cdef int nb = geometry.maxInstancedCount

        cdef int length = le - 1
        cdef int end = nb * 3 + length
        instances += length
        normals += length
        while length >= 0:
            offset_p[end] = _buffer[instances]
            normal_p[end] = _buffer[normals]
            end -= 1
            instances -= 1
            normals -= 1
            length -= 1

        nb += le / 3
        geometry.maxInstancedCount = nb


"""
"
"""
cdef class _spot:
    cdef _scenery grass
    cdef _scenery high_grass
    cdef _scenery prairie
    cdef _scenery fern
    cdef _scenery shrub
    cdef _buffer

    def __init__(_spot self, _scenery grass, _scenery high_grass, _scenery prairie, _scenery fern, _scenery shrub):
        self.grass = grass
        self.high_grass = high_grass
        self.prairie = prairie
        self.fern = fern
        self.shrub = shrub

    def free(_spot self):
        self.grass.free()
        self.high_grass.free()
        self.prairie.free()
        self.fern.free()
        self.shrub.free()

    def concatenate(_spot self, list geometries):
        self.grass.concatenate(geometries[0])
        self.high_grass.concatenate(geometries[1])
        self.prairie.concatenate(geometries[2])
        self.fern.concatenate(geometries[3])
        self.shrub.concatenate(geometries[4])

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
    cdef list c
    cdef object fifo = self.fifo
    cdef object indexmap = terrain.indexmap
    cdef object normalMap = terrain.normalMap
    cdef np.ndarray[float, ndim=1] s
    cdef np.ndarray[float, ndim=1] displacement_map = self.displacement
    cdef heightmap = terrain.heightmap
    cdef int heightmap_size = terrain.heightmap.size
    cdef _spot spot

    global _tm
    global _im

    x = _px
    while x < _p2x:
        dx = px - x
        dx2 = dx * dx
        y = _py
        while y < _p2y:
            dy = py - y
            d = dx2 + dy * dy

            if d <= 256:
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
                        continue

                    # now pick the density of grass
                    cache[k] = _spot(
                        _scenery(s[0], x, y, terrain, heightmap, normalMap, displacement_map),
                        _scenery(s[1], x, y, terrain, heightmap, normalMap, displacement_map),
                        _scenery(s[2], x, y, terrain, heightmap, normalMap, displacement_map),
                        _scenery(s[3], x, y, terrain, heightmap, normalMap, displacement_map),
                        _scenery(s[4], x, y, terrain, heightmap, normalMap, displacement_map)
                        )

                    self.fifo.append(k)

                    if len(cache) > 1024:
                        k1 = self.fifo.pop(0)
                        cache[k1].free()
                        del cache[k1]

                cache[k].concatenate(geometries)
            y += 2
        x += 2

    cdef attributes
    for geometry in geometries:
        if geometry.maxInstancedCount > 0:
            attributes = geometry.attributes
            attributes.offset.needsUpdate = True
            attributes.normals.needsUpdate = True
