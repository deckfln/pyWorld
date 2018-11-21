"""

"""
from build.road import *
from progress import *


class Roads:
    """

    """
    def __init__(self, terrain):
        progress(0, 100, "Build Roads")

        self.terrain = terrain

        size = terrain.size

        # //pick a random point on the top border
        x = math.floor(size/2+size/4)
        source = THREE.Vector2(x, 0)

        # // pick a random point on the bottom border
        x = math.floor(size/3)
        target = THREE.Vector2(x, size-1)

        # //pick a random point on the leftborder
        x = math.floor(size/2)
        source_left = THREE.Vector2(0, x)

        # // generate first road
        road = Road(terrain, source, target, 12)

        progress(25, 100, "Build Roads")

        # // generate second road
        main_path = len(road.astar.path)
        intersection = round(main_path/2)
        current = road.astar.path[intersection]

        road1 = Road(terrain, source_left, current, 12)

        progress(50, 100, "Build Roads")

        # merge the 2 paths
        self.path = road.astar.path[:]
        self.path.extend(road1.astar.path)

        # // build roads in 3D
        road.convert3d(terrain)
        road1.convert3d(terrain)

        progress(75, 100, "Build Roads")

        elevationmap = Heightmap(size)
        elevationmap_effect = Heightmap(size)

        # follow the roads to build an elevation map
        road.buildNormals()
        road.patchTerrain(terrain, elevationmap, elevationmap_effect)

        road1.buildNormals()
        road1.patchTerrain(terrain, elevationmap, elevationmap_effect)

        progress(100, 100, "Build Roads")

        # // apply the elevation masks on the heightmap
        terrain.heightmap.applyMask(elevationmap, elevationmap_effect)

        # // draw the road on the blendmap
        road.draw_road(terrain, 3)
        road1.draw_road(terrain, 3)

        progress(0, 0)

    def distanceTo(self, p):
        """
         * @description Get nearest distance of a point to the road
        :param p:
        :return:
        """
        path = self.path
        min = 999999
        for i in range(len(path)):
            current = path[i]
            d = current.distanceTo(p)
            if d < min:
                min = d
        return min


