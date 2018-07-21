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
rand = Random(0)


class _scenery:
    def __init__(self):
        self.next = None
        self.size = 0
        self.positions = None
        self.normals = None
        self.index = 0

    def init(self, densities, instance, x, y, terrain, heightmap, normalMap):
        global _buffer, _buffer_size, _first1, _first9, _first25

        rand.seed = abs(x*y) * (instance + 1) + 7
        density = densities[instance]

        instances = 0

        nb = int(density*10)
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
        positions = self.positions
        normals = self.normals

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

    def concatenate(self, geometry):
        global _buffer
        if not self.size:
            return True

        # if self.loaded:
        #    return True

        positions = self.positions
        le = self.size*3
        offset = geometry.attributes.offset.array
        nb = geometry.maxInstancedCount

        i = nb * 3
        offset[i:i + le] = positions[0:le]

        nb += int(le / 3)
        geometry.maxInstancedCount = nb

        return True


# keep a global list of sceneris
_sceneries = [_scenery() for i in range(8192*6)]
_first = _sceneries[8191*6]

for i in range(8191*6, -1, -1):
    _sceneries[i].next = _sceneries[i - 1]
    _sceneries[i].index = i


def _allocate(densities, instance, x, y, terrain, heightmap, normalMap):
    global _first
    allocated = _first
    allocated.init(densities, instance, x, y, terrain, heightmap, normalMap)
    if allocated.size > 0:
        _first = allocated.next
    else:
        allocated = None
    return allocated


def _free(scenery):
    global _first
    scenery.next = _first
    _first = scenery


class _spot:
    """
    all the scenery computed at a spot
    a spot if an integer position
    """
    def __init__(self, grass, high_grass, prairie, fern, shrub, forest2):
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


class ProceduralScenery:
    def __init__(self):
        self.name = "procedural_scenery"
        self.np = np.zeros(2)
        rand = Random(5489671)

        self.cache = {}
        self.fifo = []

    def instantiate(self, player, terrain, assets):
        _p.copy(player.position)
        _p1.copy(player.direction).multiplyScalar(8)
        _p.add(_p1)

        if _cython:
            c_instantiate(self, _p.x, _p.y, terrain, assets)
        else:
            self.p_instantiate(_p.x, _p.y, terrain, assets)

    def p_instantiate(self, px, py, terrain, assets):
        global _buffer_size

        # parse the quad
        size = 32  # int(quad.size / 2)
        terrain_size = terrain.size / 2

        _px = int(px - size)
        _py = int(py - size)
        if _px <= -terrain_size:
            _px = -terrain_size + 1
        if _py <= -terrain_size:
            _py = -terrain_size + 1

        _p2x = int(px + size)
        _p2y = int(py + size)
        if _p2x > terrain.size:
            _p2x = terrain.size - 1
        if _p2y > terrain.size:
            _p2y = terrain.size - 1

        px = int(px)
        py = int(py)

        geometries = [assets.get(asset_name).geometry for asset_name in ("grass", "high grass", "grass", "forest", "forest1", 'forest2')]

        cache = self.cache
        indexmap = terrain.indexmap
        normalMap = terrain.normalMap
        heightmap = terrain.heightmap

        x = _px
        while x < _p2x:
            dx = px - x
            dx2 = dx * dx
            y = _py
            while y < _p2y:
                # only sample points inside the player 16 radius
                dy = py - y
                d = dx2 + dy * dy

                if d <= 512:
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
                            print("p_instantiate:", x, y, _im.x, _im.y)
                            continue

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
