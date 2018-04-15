"""

"""

from THREE.Vector3 import *
from Assets import *
from Terrain import*
from Scenery import *
from Array2D import *
from prng import *
import numpy as np

import sys, os.path
mango_dir = os.path.dirname(__file__) + '/cython/'
sys.path.append(mango_dir)

from cScenery import *

_cython = True

_tm = THREE.Vector2()
_im = THREE.Vector2()
_p = THREE.Vector2()
_p1 = THREE.Vector2()
_p2 = THREE.Vector2()
_vector3 = THREE.Vector3()

_buffer = np.zeros(65536*3, dtype=np.float32)
_first1 = -1
_first9 = -1
_first25 = -1
_buffer_size = 0


class _scenery:
    def __init__(self, density, x, y, terrain, heightmap, normalMap, displacement_map):
        global _buffer, _buffer_size, _first1, _first9, _first25

        # self.instances = np.zeros(size*3, dtype=np.float32)
        # self.normals = np.zeros(size*3, dtype=np.float32)
        if density < 0.25:
            self.instances = -1
            self.normals = -1
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
            # print(_buffer_size)
        else:
            if size == 1:
                _first1 = int(_buffer[first])
            elif size == 9:
                _first9 = int(_buffer[first])
            else:
                _first25 = int(_buffer[first])

        self.instances = int(first)
        self.normals = int(first + size*3)
        self.size = size

        instances = self.instances
        normals = self.normals

        if size == 1:
            step = 5
            dstep = 2
        elif size == 9:
            step = 2
            dstep = 1
        else:
            step = 1
            dstep = 0.5

        for tx in range(-2, 3, step):
            _p1x = x + tx / 2
            for ty in range(-2, 3, step):
                _p1y = y + ty / 2

                displacement = _displace(_p1x, _p1y)

                _p1x += displacement_map[displacement] * dstep
                _p1y += displacement_map[displacement + 1] * dstep

                terrain.screen2mapXY(_p1x, _p1y, _tm)
                try:
                    z = heightmap.bilinear(_tm.x, _tm.y)
                except:
                    print("heightmap.bilinear ", x, y, _tm.x, _tm.y)

                normalMap.nearest(_tm.x, _tm.y, _vector3)
                vec3 = _vector3.np

                _buffer[instances] = _p1x
                _buffer[instances + 1] = _p1y
                _buffer[instances + 2] = z

                _buffer[normals] = vec3[0]
                _buffer[normals + 1] = vec3[1]
                _buffer[normals + 2] = vec3[2]

                normals += 3
                instances += 3

    def free(self):
        global _buffer, _buffer_size, _first1, _first9, _first25
        if self.size == 0:
            return

        if self.size == 1:
            first = _first1
        elif self.size == 9:
            first = _first9
        else:
            first = _first25

        _buffer[self.instances] = first

        if self.size == 1:
            _first1 = self.instances
        elif self.size == 9:
            _first9 = self.instances
        else:
            _first25 = self.instances

    def concatenate(self, geometry):
        global _buffer
        if not self.size:
            return True

        instances = self.instances
        normals = self.normals

        le = self.size*3

        offset = geometry.attributes.offset.array
        normal = geometry.attributes.normals.array

        nb = geometry.maxInstancedCount

        i = nb * 3

        offset[i:i + le] = _buffer[instances:instances + le]
        normal[i:i + le] = _buffer[normals:normals + le]

        nb += int(le / 3)
        geometry.maxInstancedCount = nb

        return True


def _displace(x, y):
    x1 = x + 256
    y1 = y + 256

    x2 = int(x1)
    y2 = int(y1)

    fx = (x1 - x2) * 32
    fy = (y1 - y2) * 32

    return int((x2 / 16 + fx) * 2 + (y2 / 16 + fy)*128)


class _spot:
    def __init__(self, grass, high_grass, prairie, fern, shrub):
        self.grass = grass
        self.high_grass = high_grass
        self.prairie = prairie
        self.fern = fern
        self.shrub = shrub

    def free(self):
        self.grass.free()
        self.high_grass.free()
        self.prairie.free()
        self.fern.free()
        self.shrub.free()

    def concatenate(self, geometries):
        self.grass.concatenate(geometries[0])
        self.high_grass.concatenate(geometries[1])
        self.prairie.concatenate(geometries[2])
        self.fern.concatenate(geometries[3])
        self.shrub.concatenate(geometries[4])


class ProceduralScenery:
    def __init__(self):
        self.name = "procedural_scenery"
        self.np = np.zeros(2)
        rand = Random(5489671)

        self.displacement = np.zeros(64*64*2, np.float32)
        p = 0
        for i in range(64*64):
            self.displacement[p] = (rand.random() - 0.5) * 2
            self.displacement[p + 1] = (rand.random() - 0.5) * 2
            p += 2

        self.cache = {}
        self.fifo = []

    def instantiate(self, player, terrain, quad, assets):
        _p.copy(player.position)
        _p1.copy(player.direction).multiplyScalar(8)
        _p.add(_p1)

        if _cython:
            c_instantiate(self, _p.x, _p.y, terrain, quad, assets)
        else:
            self.p_instantiate(_p.x, _p.y, terrain, quad, assets)

    def p_instantiate(self, px, py, terrain, quad, assets):
        global _buffer_size

        # parse the quad
        size = int(quad.size / 2)
        terrain_size = terrain.size / 2

        _px = int(quad.center.x - size)
        _py = int(quad.center.y - size)
        if _px <= -terrain_size:
            _px = -terrain_size + 1
        if _py <= -terrain_size:
            _py = -terrain_size + 1

        _p2x = int(quad.center.x + size)
        _p2y = int(quad.center.y + size)
        if _p2x > terrain.size:
            _p2x = terrain.size - 1
        if _p2y > terrain.size:
            _p2y = terrain.size - 1

        px = int(px)
        py = int(py)

        geometries = [assets.get(asset_name).geometry for asset_name in ("grass", "high grass", "prairie", "fern", "shrub")]

        cache = self.cache
        indexmap = terrain.indexmap
        normalMap = terrain.normalMap
        heightmap = terrain.heightmap
        displacement_map = self.displacement

        x = _px
        while x < _p2x:
            dx = px - x
            dx2 = dx * dx
            y = _py
            while y < _p2y:
                # only sample points inside the player 16 radius
                dy = py - y
                d = dx2 + dy * dy

                if d <= 256:
                    k = "%d:%d" % (x, y)
                    if k not in cache:
                        terrain.screen2mapXY(x, y, _tm)

                        # do not put scenery on roads or rivers
                        try:
                            if terrain.isRiverOrRoad(_tm):
                                continue
                        except:
                            print("p_instantiate ", x, y, _tm.x, _tm.y)
                            continue

                        # get the density of each ground type
                        terrain.heightmap2indexmap(_tm, _im)
                        s = indexmap.bilinear_density(_im.x, _im.y)
                        if s is None:
                            print(x, y, _im.x, _im.y)
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

                        if len(cache) > 1022:
                            k1 = self.fifo.pop(0)
                            cache[k1].free()
                            del cache[k1]

                    cache[k].concatenate(geometries)
                y += 2
            x += 2

        for geometry in geometries:
            if geometry.maxInstancedCount > 0:
                geometry.attributes.offset.needsUpdate = True
                geometry.attributes.normals.needsUpdate = True
