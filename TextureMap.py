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
        self.data = np.zeros(size * size * 4, 'b')  # unsigned char RGBA
        self.texture = None
        self.vector4 = THREE.Vector4()

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

        self.vector4.x = self.data[d]        # layer1
        self.vector4.y = self.data[d + 1]    #
        self.vector4.z = self.data[d + 2]    # layer2
        self.vector4.w = self.data[d + 3]    # blending value

        return self.vector4

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