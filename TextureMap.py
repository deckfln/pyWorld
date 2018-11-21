"""

"""
import numpy as np
import PIL
from PIL import Image
from array import *
import sys
import math
import os

import THREE


class TextureMap:
    """
    Image storage for textures
    """
    def __init__(self, size, repeat, depth=4):
        """

        :param size:
        :param repeat:
        """
        self.size = size
        self.repeat = repeat
        self.depth = depth
        self.data = np.zeros(size * size * depth, np.uint8)  # unsigned char RGBA
        self.texture = None
        self.vector4 = THREE.Vector4()

    def set(self, v, rgba):
        self.setXY(v.x, v.y, rgba)

    def setXY(self, x, y, rgba):
        depth = self.depth
        p = int(x) * depth + int(y) * self.size * depth

        self.data[p] = rgba[0]
        if depth > 1:
            self.data[p + 1] = rgba[1]
            if depth > 2:
                self.data[p + 2] = rgba[2]
                if depth > 3:
                    self.data[p + 3] = rgba[3]

    def get(self, v):
        return self.getXY(v.x, v.y)

    def getXY(self, x, y):
        depth = self.depth
        d = int(x) * depth + int(y) * self.size * depth

        self.vector4.x = self.data[d]        # layer1
        if depth > 1:
            self.vector4.y = self.data[d + 1]    #
            if depth > 2:
                self.vector4.z = self.data[d + 2]    # layer2
                if depth > 3:
                    self.vector4.w = self.data[d + 3]    # blending value

        return self.vector4

    def get_layer1(self, x, y):
        depth = self.depth
        d = int(x) * depth + int(y) * self.size * depth

        r = self.data[d]        # layer1

        return r

    def generate(self, file):
        bytes = self.data.tobytes()
        depth = self.depth
        if depth == 1:
            mode = "L"
        elif depth == 3:
            mode = "RGB"
        else:
            mode = "RGBA"

        im = PIL.Image.frombytes(mode, (self.size, self.size), bytes)
        if os.path.exists(file):
            os.remove(file)
        im.save(file)

    def load(self, file):
        im = Image.open(file)
        self.data = im.getdata()
        self.data = im.tobytes()
        self.size = im.size[0]