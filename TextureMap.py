"""

"""
import numpy as np
import PIL
from PIL import Image
from array import *
import sys
import math

import THREE


class TextureMap:
    """
    Image storage for textures
    """
    def __init__(self, size, repeat):
        """

        :param size:
        :param repeat:
        """
        self.size = size
        self.repeat = repeat
        self.data = array('B', [0] * (size * size * 4))  # unsigned char RGBA
        self.texture = None

    def set(self, v, rgba):
        self.setXY(v.x, v.y, rgba)

    def setXY(self, x, y, rgba):
        p = int(x)*4 + int(y)*self.size*4

        self.data[p] = rgba[0]
        self.data[p + 1] = rgba[1]
        self.data[p + 2] = rgba[2]
        self.data[p + 3] = rgba[3]

    def get(self, v):
        return self.getXY(v.x, v.y)

    def getXY(self, x, y):
        d = int(x)*4 + int(y)*self.size*4

        r = self.data[d]        # layer1
        g = self.data[d + 1]    #
        b = self.data[d + 2]    # layer2
        a = self.data[d + 3]    # blending value

        return THREE.Vector4(r, g, b, a)

    def get_layer1(self, x, y):
        d = int(x)*4 + int(y)*self.size*4

        r = self.data[d]        # layer1

        return r

    def generate(self, file):
        bytes = self.data.tobytes()
        im = PIL.Image.frombytes("RGBA", (self.size, self.size), bytes)
        im.save(file)

    def load(self, file):
        im = Image.open(file)
        self.data = im.getdata()
        self.data = im.tobytes()
        self.size = im.size[0]

    def bilinear_density(self, x, y):
        if not (0 <= x < self.size and 0 <= y < self.size):
            return None

        #if isinstance(x, int) and isinstance(y, int):
        #    p = int(x*4 + self.size * y * 4)
        #    return self.data[x*4 + self.size * y * 4]

        #if x.is_integer() and y.is_integer():
        #    p = int(x + self.size * y * 4)
        #    return self.data[p]

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

        z1 = self.get_layer1(gridx, gridy)
        z2 = self.get_layer1(gridx, gridy + top)
        z3 = self.get_layer1(gridx + left, gridy)
        z4 = self.get_layer1(gridx + left, gridy + top)

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
        grounds = [0, 0, 0, 0, 0, 0]
        grounds[z1-4] = 1
        grounds[z2-4] = 1
        grounds[z3-4] = 1
        grounds[z4-4] = 1

        for g in range(6):
            if grounds[g]:
                # only run a bilinear computation on grounds that are actually present in the quadrant
                grounds[g] = bilinear_ground(g+4)

        return grounds
