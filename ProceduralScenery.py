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

_cython = False

_tm = THREE.Vector2()
_im = THREE.Vector2()
_p = THREE.Vector2()
_p1 = THREE.Vector2()
_p2 = THREE.Vector2()


class _spot:
    def __init__(self, size):
        self.instances = np.zeros(size*3, dtype=np.float32)
        self.normals = np.zeros(size*3, dtype=np.float32)


def _concatenate_spots(spot, geometry):
    instances = spot.instances
    normals = spot.normals

    le = len(instances)

    offset = geometry.attributes.offset
    normal = geometry.attributes.normals

    nb = geometry.maxInstancedCount

    i = nb * 3
    offset.array[i:le + i] = instances[0:le]
    normal.array[i:le + i] = normals[0:le]

    nb += int(le / 3)
    geometry.maxInstancedCount = nb


def _instantiate_for_spot(x, y, density, terrain, self):
    """
    instantiate one ground type at the current spot
    :param s:
    :param ground_type:
    :param asset_name:
    :return:
    """
    if density < 0.25:
        return None

    if density < 0.50:
        displacement = self.displace(x, y)
        _p1x = x + displacement.x * 2
        _p1y = y + displacement.x * 2

        terrain.screen2mapXY(_p1x, _p1y, _tm)
        z = terrain.heightmap.bilinear(_tm.x, _tm.y)
        n = terrain.normalMap.nearest(_tm.x, _tm.y)

        spot = _spot(1)
        instances = spot.instances
        normals = spot.normals

        instances[0] = _p1x
        instances[1] = _p1y
        instances[2] = z

        normals[0] = n.np[0]
        normals[1] = n.np[1]
        normals[2] = n.np[2]

        return spot

    # the higher the desity, the smaller the step to generate instances
    if density < 0.75:
        step = 2
        dstep = 0.5
        mx = 9*3
    else:
        step = 1
        dstep = 0.25
        mx = 25*3

    # map the step on the upper loop -6 -> 6  <=> -1 -> 1
    spot = _spot(mx)
    instances = spot.instances
    normals = spot.normals

    i = 0
    for tx in range(-2, 3, step):
        _p1x = x + tx / 2
        for ty in range(-2, 3, step):
            _p1y = y + ty / 2

            displacement = self.displace(_p1x, _p1y)

            _p1x += displacement.x * dstep
            _p1y += displacement.y * dstep

            terrain.screen2mapXY(_p1x, _p1y, _tm)
            z = terrain.heightmap.bilinear(_tm.x, _tm.y)
            n = terrain.normalMap.nearest(_tm.x, _tm.y)

            instances[i] = _p1x
            instances[i + 1] = _p1y
            instances[i + 2] = z

            normals[i] = n.np[0]
            normals[i + 1] = n.np[1]
            normals[i + 2] = n.np[2]

            i += 3

    return spot


class ProceduralScenery:
    def __init__(self):
        self.name = "procedural_scenery"
        self.np = np.zeros(2)
        rand = Random(5489671)

        def init_prn():
            return THREE.Vector2((rand.random() - 0.5) * 2, (rand.random() - 0.5) * 2)

        self.displacement_map = Array2D(64, init_prn)
        self.cache = {}
        self.fifo = []

    def displace(self, x, y):
        # absolute position
        """
        self.np[0] = x
        self.np[1] = y

        self.np += 256
        b = np.floor(self.np)
        self.np -= b
        self.np *= 32
        b /= 16

        self.np += b
        """
        x1 = x + 256
        y1 = y + 256

        x2 = int(x1)
        y2 = int(y1)

        fx = (x1 - x2) * 32
        fy = (y1 - y2) * 32

        return self.displacement_map.get(x2 / 16 + fx, y2 / 16 + fy)
        # return self.displacement_map.get(self.np[0], self.np[1])

    def instantiate(self, player, terrain, quad, assets):
        _p.copy(player.position)
        _p1.copy(player.direction).multiplyScalar(8)
        _p.add(_p1)

        if _cython:
            c_instantiate(self, _p.x, _p.y, terrain, quad, assets)
        else:
            self.p_instantiate(_p.x, _p.y, terrain, quad, assets)

    def p_instantiate(self, px, py, terrain, quad, assets):

        # parse the quad
        size = int(quad.size / 2)
        _p.x = int(quad.center.x - size)
        _p.y = int(quad.center.y - size)

        _p2.x = int(quad.center.x + size)
        _p2.y = int(quad.center.y + size)

        px = int(px)
        py = int(py)

        geometries = [assets.get(asset_name).geometry for asset_name in ("grass", "high grass", "prairie", "fern", "shrub")]

        cache = self.cache

        for x in range(_p.x, _p2.x, 2):
            dx = px - x
            dx2 = dx * dx
            for y in range(_p.y, _p2.y, 2):

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

                    if len(cache) > 1024:
                        k1 = self.fifo.pop(0)
                        del cache[k1]

                cached = cache[k]

                for i in range(5):
                    if cached[i] is not None:
                        _concatenate_spots(cached[i], geometries[i])

        for i in range(5):
            if geometries[i].maxInstancedCount > 0:
                geometries[i].attributes.offset.needsUpdate = True
                geometries[i].attributes.normals.needsUpdate = True
