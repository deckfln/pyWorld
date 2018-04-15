"""

"""
import numpy as np
from array import *
import math
import json
import THREE
import PIL
from PIL import Image

import sys, os.path
mango_dir = os.path.dirname(__file__) + '/cython/'
sys.path.append(mango_dir)

from cHeightmap import *

cython = False

class Heightmap:
    """
    Heightmap of Float32 values
    """
    def __init__(self, size, onscreen=0):
        self.size = size = int(size)
        self.map = np.zeros(size * size, dtype=np.float32)  # float
        self.onscreen = onscreen
        self.normalMap = None

    def set(self, x, y, h):
        if x < 0 or y < 0 or x >= self.size or y >= self.size:
            return

        self.map[int(x) + int(y) * self.size] = h

    def setV(self, v, h):
        self.map[int(v.x) + int(v.y) * self.size] = h

    def add(self, x, y, h):
        if x < 0 or y < 0 or x >= self.size or y >= self.size:
            return

        self.map[x + y * self.size] += h

    def get(self, x, y):
        if x < 0 or y < 0 or x >= self.size or y >= self.size:
            return None

        p = int(int(x) + int(y) * self.size)
        return self.map[p]

    def getNormalize(self, x, y):
        return self.get(x, y) / self.size

    def getV(self, v):
        p = int(v.x) + int(v.y) * self.size
        return self.map[p]

    def bilinear(self, x, y):
        if cython:
            return cHeightmap_bilinear(self.map, self.size, x, y)
        else:
            return self._bilinear(x, y)

    def _bilinear(self, x, y):
        if isinstance(x, int) and isinstance(y, int):
            return self.map[x + self.size * y]

        # bilinear interpolation
        gridx = math.floor(x)
        offsetx = x - gridx
        gridy = math.floor(y)
        offsety = y - gridy

        if offsetx == 0 and offsety == 0:
            p = int(x + self.size * y)
            return self.map[p]

        z1 = self.map[gridx + gridy * self.size]
        if gridx < self.size - 1:
            z2 = self.map[gridx + 1 + gridy * self.size]
            if gridy < self.size - 1:
                z3 = self.map[gridx + 1 + (gridy + 1) * self.size]
            else:
                z3 = z1
        else:
            z2 = z1
            z3 = z1
        if gridy < self.size - 1:
            z4 = self.map[gridx + (gridy + 1) * self.size]
        else:
            z4 = z1

        if offsetx > offsety:
            z = z1 - offsetx * (z1 - z2) - offsety * (z2 - z3)
        else:
            z = z1 - offsetx * (z4 - z3) - offsety * (z1 - z4)

        return z

    def applyMask(self, map, effect):
        """
        Apply the map effect on the current map
        :param map:
        :param effect:
        :return:
        """
        p = 0
        terrain_data = self.map
        roadmap_data = map.map
        roadmap_effect_data = effect.map
        size = self.size
        for p in range(size*size):
            alpha = roadmap_effect_data[p]
            if alpha == 0:
                continue

            z = terrain_data[p]
            z1 = roadmap_data[p]
            diff = (z - z1) * alpha
            z = z - diff
            terrain_data[p] = z

    def divide(self, countmap):
        """

        :param count:
        :return:
        """
        p = 0
        data = self.map
        count = countmap.map
        size = self.size
        for i in range(size*size):
            d = data[i]
            c = count[i]
            if c > 0:
                data[i] = d / c

    def save(self, file):
        map = array('B', [0] * (self.size * self.size * 4))  # float

        mini = 99999
        maxi = -99999
        for i in range(self.size*self.size):
            h = self.map[i]
            if h > maxi:
                maxi = h
            if h < mini:
                mini = h

        rang = maxi - mini

        p = 0
        for i in range(self.size*self.size):
            map[p] = int((self.map[i] - mini)*255/rang)
            map[p+1] = 0
            map[p+2] = 0
            map[p+3] = 255
            p += 4

        bytes = map.tobytes()
        im = PIL.Image.frombytes("RGBA", (self.size, self.size), bytes)
        im.save(file)

    def toJSON(self):
        return json.dumps([ a for a in self.map ])
