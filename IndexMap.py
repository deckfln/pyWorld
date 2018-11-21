"""

"""

from TextureMap import *
from build.PerlinSimplexNoise import *
import Terrain


class IndexMap(TextureMap):
    def __init__(self, size, repeat):
        super().__init__(size, repeat, 1)
        self.grounds = np.zeros(11, np.float32)

    def build(self):
        """
        generate an index map texture of width size
        :return:
        """
        perlin = SimplexNoise(Terrain.myrandom)

        size = self.size
        data = self.data

        i = 0
        for y in range(size):
            for x in range(size):
                rand = perlin.noise(x/8, y/8)
                diversity = int((perlin.noise(x/16, y/16) + 1)*1.5)
                if rand > 0:
                    first = Terrain.TILE_grass_png + diversity
                else:
                    first = Terrain.TILE_forest_png + diversity

                data[i] = first     # // first layer texture index

                i += 1

    def bilinear_density(self, x, y):
        if not (0 <= x < self.size and 0 <= y < self.size):
            return None

        # bilinear interpolation
        gridx = math.floor(x)
        offsetx = x - gridx
        gridy = math.floor(y)
        offsety = y - gridy

        # pick the correct quadrant
        #
        #    +--------+--------+
        #    !        !        !
        #    !    4...!...2    !
        #    !    .   !   .    !
        #    +--------+--------+--------+
        #    !    .   ! X .    !        !
        #    !    3...!...1****!***3    !
        #    !        !   *  X !   *    !
        #    +--------+--------+--------+
        #             !   *    !   *    !
        #             !   2****!***4    !
        #             !        !        !
        #             +--------+--------+
        #
        if offsetx < 0.5:
            left = -1
            offsetx = 0.5 - offsetx
        else:
            left = 1
            offsetx = offsetx - 0.5

        if offsety < 0.5:
            top = -1
            offsety = 0.5 - offsety
        else:
            top = 1
            offsety = offsety - 0.5

        size = self.size

        z1 = self.get_layer1(gridx, gridy)
        if 0 <= gridy + top < size:
            z2 = self.get_layer1(gridx, gridy + top)
            if 0 <= gridx + left < size:
                z3 = self.get_layer1(gridx + left, gridy)
                z4 = self.get_layer1(gridx + left, gridy + top)
            else:
                z3 = 0
                z4 = 0
        else:
            z2 = 0
            if 0 <= gridx + left < size:
                z3 = self.get_layer1(gridx + left, gridy)
                z4 = 0
            else:
                z3 = 0
                z4 = 0

        def bilinear_ground(ground):
            if z1 != ground and z2 != ground and z3 != ground and z4 != ground:
                return 0

            if z1 == ground and z2 == ground and z3 == ground and z4 == ground:
                return 1

            p1 = 1 if z1 == ground else 0
            p2 = 1 if z2 == ground else 0
            p3 = 1 if z3 == ground else 0
            p4 = 1 if z4 == ground else 0

            pleft = (1-offsety) * p1 + offsety * p2
            pright = (1-offsety) * p3 + offsety * p4

            return (1-offsetx) * pleft + offsetx * pright

        # test each ground
        grounds = self.grounds
        grounds.fill(0)
        grounds[z1] = 1
        grounds[z2] = 1
        grounds[z3] = 1
        grounds[z4] = 1

        for g in range(6):
            if grounds[g]:
                # only run a bilinear computation on grounds that are actually present in the quadrant
                grounds[g] = bilinear_ground(g)

        return grounds
