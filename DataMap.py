"""

"""
import numpy as np
import PIL
from PIL import Image
from array import *
import sys
import math
import os

from TextureMap import *
from THREE.textures.DataTexture import *


class DataMap(TextureMap):
    """
    Data storage for textures
    """
    def __init__(self, size: int):
        super(DataMap, self).__init__(size, 0, 4, np.float32)

    def setXY(self, x, y, normal, z):
        super().setXY(x, y, (normal.x, normal.y, normal.z, z))

    def save(self, file):
        if os.path.exists(file):
            os.remove(file)

        np.save(file, self.data)

    def load(self, file):
        self.data = np.load(file)
        self.size = int(math.sqrt(self.data.size / 4))

    def average(self):
        z = 0
        s = self.data.size
        data = self.data
        for p in range(0, s, 4):
            z += data[p + 3]
        z /= (self.size ** 2)

        return z

    def DataTexture(self):
        dt = DataTexture(self.data, self.size, self.size, RGBAFormat, FloatType)
        #dt.magFilter = LinearFilter
        #dt.minFilter = LinearFilter
        return dt
