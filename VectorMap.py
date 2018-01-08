"""

"""
from THREE.Vector3 import *
from Array2D import *


def _bilinear(v1, v2, v3, v4, offsetx, offsety):
    # https://forum.unity.com/threads/vector-bilinear-interpolation-of-a-square-grid.205644/
    abu = v1.clone().lerp(v2, offsetx)
    dcu = v3.clone().lerp(v4, offsetx)
    return abu.lerp(dcu, offsety)


def _newvector():
    return THREE.Vector3(0, 0, 0)


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
