"""

"""

from Asset import *
from Terrain import*
from Scenery import *
from Array2D import *
from prng import *


class ProceduralScenery:
    def __init__(self):
        self.name = "procedural_scenery"

        rand = Random(5489671)

        def init_prn():
            return THREE.Vector2((rand.random() - 0.5) * 2, (rand.random() - 0.5) * 2)

        self.displacement_map = Array2D(64, init_prn)

    def displace(self, x, y):
        # absolute position
        x1 = x + 256
        y1 = y + 256

        x2 = math.floor(x1)
        y2 = math.floor(y1)

        fx = (x1 - x2) * 32
        fy = (y1 - y2) * 32

        return self.displacement_map.get(int(x2/16 + fx), int(y2/16 + fy))

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

        def instantiate_ground(s, ground_type, asset_name):
            density = s[ground_type]  # 0 => TILE_grass_png

            geometry = assets[asset_name].geometry
            offset = geometry.attributes.offset
            nb = geometry.maxInstancedCount

            i = nb * 3

            if density < 0.25:
                pass
            elif density < 0.50:
                displacement = self.displace(x, y)

                terrain.screen2mapXY(x + displacement.x * 2, y + displacement.y * 2, tm)
                z = terrain.getV(tm)

                offset.array[i] = x + displacement.x
                offset.array[i + 1] = y + displacement.y
                offset.array[i + 2] = z
                i += 3

                nb += 1
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
                        z = terrain.getV(tm)

                        offset.array[i] = p1.x
                        offset.array[i + 1] = p1.y
                        offset.array[i + 2] = z
                        i += 3

                        nb += 1

            geometry.maxInstancedCount = nb
            geometry.attributes.offset.needsUpdate = True

        for x in range(p.x, p2.x, 2):
            for y in range(p.y, p2.y, 2):

                # only sample points inside the player 16 radius
                dx = player_position.x - x
                dy = player_position.y - y
                d = dx * dx + dy * dy

                if d > 256:
                    continue

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
                instantiate_ground(s, 0, 'grass')
                instantiate_ground(s, 1, 'high grass')
                instantiate_ground(s, 2, 'prairie')
                instantiate_ground(s, 3, 'fern')
                instantiate_ground(s, 4, 'shrub')
