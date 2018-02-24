"""

"""

from Asset import *
from Terrain import*
from Scenery import *


class ProceduralScenery:
    def __init__(self):
        self.name = "procedural_scenery"

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
            scale = geometry.attributes.scale
            nb = geometry.maxInstancedCount

            i = nb * 3

            if density < 0.25:
                pass
            elif density < 0.50:
                z = terrain.getV(tm)

                offset.array[i] = x1
                offset.array[i + 1] = y
                offset.array[i + 2] = z
                i += 3

                nb += 1
            else:
                # the higher the desity, the smaller the step to generate instances
                if density < 0.75:
                    step = 2
                else:
                    step = 1

                # map the step on the upper loop -6 -> 6  <=> -1 -> 1
                for tx in range(-2, 3, step):
                    checkboard1 = 0
                    for ty in range(-2, 3, step):
                        checkboard1 = 0 if checkboard1 else step / 2

                        p1.x = x1 + (tx + checkboard1) / 2
                        p1.y = y + ty / 2

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
            checkboard = 0
            for y in range(p.y, p2.y, 2):

                x1 = x + checkboard

                checkboard = 0 if checkboard else 1

                # only sample points inside the player 16 radius
                dx = player_position.x - x1
                dy = player_position.y - y
                d = dx * dx + dy * dy

                if d > 256:
                    continue

                terrain.screen2mapXY(x1, y, tm)

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
