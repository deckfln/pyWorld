"""

"""
import numpy as np

from THREE.Vector3 import *
from Array2D import *
from THREE.DataTexture import *

# reusable vectors
_v1_static = THREE.Vector3()
_v2_static = THREE.Vector3()


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


class VectorMap(Array2D):
    def __init__(self, size):
        super().__init__(size, _newvector)

    def bilinear(self, x, y):
        return super().bilinear(x, y, _bilinear)

    def empty(self):
        super().forEach(_zeros)

    def normalize(self):
        super().forEach(_normamlize)

    def export2texture(self):
        data = np.zeros(self.size * self.size * 3, np.float32)

        i = 0
        for x in range(self.size):
            for y in range(self.size):
                v = self.get(x,y)
                data[i] = v.np[0]
                data[i + 1] = v.np[1]
                data[i + 2] = v.np[2]

                i += 3

        return THREE.DataTexture(data, self.size, self.size, RGBAFormat, FloatType)
