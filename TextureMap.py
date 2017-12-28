"""

"""
import PIL
from PIL import Image
from array import *
import sys

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

    def generate(self, file):
        bytes = self.data.tobytes()
        im = PIL.Image.frombytes("RGBA", (self.size, self.size), bytes)
        im.save(file)
