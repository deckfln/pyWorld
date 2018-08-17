"""

"""
import numpy as np
import os, sys

from THREE.Vector3 import *
from THREE.DataTexture import *
from Array2D import *

mango_dir = os.path.dirname(__file__) + '/cython/'
sys.path.append(mango_dir)

from cVectorMap import *

cython = True

# reusable vectors
_v1_static = THREE.Vector3()
_v2_static = THREE.Vector3()

_z1 = THREE.Vector3()
_z2 = THREE.Vector3()
_z3 = THREE.Vector3()
_z4 = THREE.Vector3()


def _normamlize(vec3):
    vec3.normalize()


class VectorMap:
    def __init__(self, size):
        self.size = size
        self.map = np.zeros(size * size * 3, np.float32)

    def set(self, x, y, v):
        if x < 0 or y < 0 or x > self.size or y > self.size:
            return
        p = int(3 * (x + y*self.size))

        self.map[p] = v.np[0]
        self.map[p + 1] = v.np[1]
        self.map[p + 2] = v.np[2]

    def setV(self, v, vec3):
        self.set(v.x, v.y, vec3)

    def _add(self, x, y, vec3):
        if x < 0 or y < 0 or x > self.size or y > self.size:
            return
        p = int(3 * (x + y*self.size))

        map = self.map
        np = vec3.np

        map[p] += np[0]
        map[p + 1] += np[1]
        map[p + 2] += np[2]

        return vec3

    def add(self, x, y, vec3):
        if cython:
            cVectorMap_add(self.map, self.size, x, y, vec3.np)
        else:
            self._padd(x, y, vec3)

    def _pget(self, x, y, v):
        if x < 0 or y < 0 or x > self.size or y > self.size:
            return None

        p = int(3 * (x + y*self.size))
        map = self.map
        np = v.np
        np[0] = map[p]
        np[1] = map[p + 1]
        np[2] = map[p + 2]

        return v

    def get(self, x, y , v):
        if cython:
            cVectorMap_get(self.map, self.size, x, y, v.np)
        else:
            return self._pget(x, y, v)
        return v

    def getV(self, v, vec3):
        return self.get(v.x, v.y, vec3)

    def empty(self):
        map = self.map
        for i in range(0, self.size*self.size*3, 3):
            map[i ] = 0
            map[i + 1] = 0
            map[i + 2] = 1

    def _pbilinear(self, x, y, vec3):
        global _z1, _z2, _z3, _z4

        size = self.size

        if not (0 <= x < size and 0 <= y < size):
            return None

        if isinstance(x, int) and isinstance(y, int):
            return self.get(x, y, vec3)

        # bilinear interpolation
        gridx = math.floor(x)
        offsetx = x - gridx
        gridy = math.floor(y)
        offsety = y - gridy

        if offsetx == 0 and offsety == 0:
            return self.get(x, y, vec3)

        self.get(gridx, gridy, _z1)
        if gridx < size - 1:
            self.get(gridx + 1, gridy, _z2)
            if gridy < size - 1:
                self.get(gridx + 1, gridy + 1, _z3)
            else:
                _z3.copy(_z1)
        else:
            _z2.copy(_z1)
            _z3.copy(_z1)
        if gridy < size - 1:
            self.get(gridx, gridy + 1, _z4)
        else:
            _z4.copy(_z1)

        # https://forum.unity.com/threads/vector-bilinear-interpolation-of-a-square-grid.205644/
        _z1.lerp(_z2, offsetx)
        _z3.lerp(_z4, offsetx)
        _z1.lerp(_z3, offsety)
        vec3.copy(_z1)
        return vec3

    def bilinear(self, x, y, vec3):
        if cython:
            cVectorMap_bilinear(self.map, self. size, x, y, vec3.np)
        else:
            self._pbilinear(x, y, vec3)
        return vec3

    def _pnearest(self, x, y, vec3):
        size = self.size

        if not (0 <= x < size and 0 <= y < size):
            raise RuntimeError("VectorMap : p_nearest out of bound x,y ")

        if isinstance(x, int) and isinstance(y, int):
            return self.get(x, y, vec3)

        if x - int(x) == 0 and y - int(y) == 0:
            return self.get(x, y, vec3)

        gridx = math.floor(x)
        offsetx = x - gridx
        gridy = math.floor(y)
        offsety = y - gridy

        if offsetx > 0.5:
            if gridx < size-1:
                gridx += 1
        if offsety > 0.5:
            if gridy < size-1:
                gridy += 1

        return self.get(gridx, gridy, vec3)

    def nearest(self, x, y, vec3):
        if cython:
            cVectorMap_nearest(self.map, self.size, x, y, vec3.np)
        else:
            self._pnearest(x, y, vec3)
        return vec3

    def normalize(self):
        map = self.map
        np = _z1.np
        for i in range(0, self.size*self.size*3, 3):
            np[0] = map[i]
            np[1] = map[i + 1]
            np[2] = map[i + 2]
            _z1.normalize()
            map[i] = np[0]
            map[i + 1] = np[1]
            map[i + 2] = np[2]

    def export2texture(self):
        data = np.zeros(self.size * self.size * 3, np.float32)

        i = 0
        for x in range(self.size):
            for y in range(self.size):
                self.get(x,y, _v1_static)
                data[i] = _v1_static.np[0]
                data[i + 1] = _v1_static.np[1]
                data[i + 2] = _v1_static.np[2]

                i += 3

        return THREE.DataTexture(data, self.size, self.size, RGBAFormat, FloatType)

"""

"""


def _bilinear(v1, v2, v3, v4, offsetx, offsety):
    # https://forum.unity.com/threads/vector-bilinear-interpolation-of-a-square-grid.205644/
    _v1_static.copy(v1).lerp(v2, offsetx)
    _v2_static.copy(v3).lerp(v4, offsetx)
    return _v1_static.lerp(_v2_static, offsety)


def _newvector():
    return THREE.Vector3(0, 0, 1.0)


# reset the normal map
def _zeros(v3):
    v3.x = v3.y = v3.z = 0


def _normamlize(vec3):
    vec3.normalize()


class a2dVectorMap(Array2D):
    def __init__(self, size):
        super().__init__(size, _newvector)

    def get(self, x, y, vec3):
        return vec3.copy(super().get(x, y))

    def bilinear(self, x, y, vec3):
        return vec3.copy(super().bilinear(x, y, _bilinear))

    def empty(self):
        super().forEach(_zeros)

    def normalize(self):
        super().forEach(_normamlize)
