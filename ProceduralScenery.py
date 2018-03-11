"""

"""

from Assets import *
from Terrain import*
from Scenery import *
from Array2D import *
from prng import *
import numpy as np


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

    def instantiate(self, player_position, terrain, quad, assets):
        tm = THREE.Vector2()
        im = THREE.Vector2()
        p = THREE.Vector2()
        p1 = THREE.Vector2()
        p2 = THREE.Vector2()

        # parse the quad
        size = int(quad.size / 2 )
        p.x = int(quad.center.x-size)
        p.y = int(quad.center.y-size)

        p2.x = int(quad.center.x+size)
        p2.y = int(quad.center.y+size)

        def instantiate_for_spot(s, ground_type):
            """
            instantiate one ground type at the current spot
            :param s:
            :param ground_type:
            :param asset_name:
            :return:
            """
            instances = []
            density = s[ground_type]  # 0 => TILE_grass_png

            if density < 0.25:
                pass
            elif density < 0.50:
                displacement = self.displace(x, y)
                p1.x = x + displacement.x * 2
                p1.y = y + displacement.x * 2

                terrain.screen2mapXY(p1.x, p1.y, tm)
                z = terrain.heightmap.bilinear(tm.x, tm.y)

                instances.extend([p1.x, p1.y, z])

            else:
                # the higher the desity, the smaller the step to generate instances
                if density < 0.75:
                    step = 2
                    dstep = 0.5
                else:
                    step = 1
                    dstep = 0.25

                # map the step on the upper loop -6 -> 6  <=> -1 -> 1
                for tx in range(-2, 3, step):
                    for ty in range(-2, 3, step):
                        displacement = self.displace(p1.x, p1.y)

                        p1.x = x + tx / 2 + displacement.x * dstep
                        p1.y = y + ty / 2 + displacement.y * dstep

                        terrain.screen2map(p1, tm)
                        z = terrain.heightmap.bilinear(tm.x, tm.y)

                        instances.extend([p1.x, p1.y, z])

            return instances

        def concatenate_spots(spot, asset_name):
            le = len(spot)

            if le > 0:
                geometry = assets.get(asset_name).geometry
                offset = geometry.attributes.offset
                nb = geometry.maxInstancedCount

                i = nb * 3
                offset.array[i:len(spot) + i] = spot[:]

                nb += int(len(spot)/3)
                geometry.maxInstancedCount = nb
                geometry.attributes.offset.needsUpdate = True

        spots = []
        for x in range(p.x, p2.x, 2):
            for y in range(p.y, p2.y, 2):

                # only sample points inside the player 16 radius
                dx = player_position.x - x
                dy = player_position.y - y
                d = dx * dx + dy * dy

                if d > 256:
                    continue

                k = "%f:%d" % (x, y)
                if k not in self.cache:
                    terrain.screen2mapXY(x, y, tm)

                    # do not put scenery on roads or rivers
                    if terrain.isRiverOrRoad(tm):
                        continue

                    # get the density of each ground type
                    terrain.heightmap2indexmap(tm, im)
                    s = terrain.indexmap.bilinear_density(im.x, im.y)
                    if s is None:
                        continue

                    # now pick the density of grass
                    self.cache[k] = [
                        instantiate_for_spot(s, 0),
                        instantiate_for_spot(s, 1),
                        instantiate_for_spot(s, 2),
                        instantiate_for_spot(s, 3),
                        instantiate_for_spot(s, 4)
                        ]

                    self.fifo.append(k)

                    if len(self.cache) > 1024:
                        k1 = self.fifo.pop(0)
                        del self.cache[k1]

                spots.append(k)

        """
        a = 0
        for asset in ('grass', 'high grass', 'prairie', 'fern', 'shrub'):
            geometry = assets.get(asset).geometry
            offset = geometry.attributes.offset
            i = 0

            for spot in spots:
                cached = self.cache[spot][a]
                le = len(cached)
                if le > 0:
                    offset.array[i:i + le] = cached[:]
                    i += int(le/3)

            geometry.maxInstancedCount = int(i/3)
            geometry.attributes.offset.needsUpdate = True
            a += 1
        """
        for spot in spots:
            cached = self.cache[spot]

            concatenate_spots(cached[0], 'grass')
            concatenate_spots(cached[1], 'high grass')
            concatenate_spots(cached[2], 'prairie')
            concatenate_spots(cached[3], 'fern')
            concatenate_spots(cached[4], 'shrub')