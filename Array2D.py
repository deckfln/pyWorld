"""

"""
import math


class Array2D:
    """

    """
    def __init__(self, size, initObject):
        self.size = size
        self.map = [None] * (size * size)

        for i in range(size*size):
            self.map[i] = initObject()

    def set(self, x, y, obj):
        if x < 0 or y < 0 or x > self.size or y > self.size:
            return
        p = int(x + y*self.size)

        if self.map[p]:
            self.map[p].copy(obj)
        else:
            self.map[p] = obj.clone()

    def setV(self, v, obj):
        self.set(v.x, v.y, obj)

    def add(self, x, y, obj):
        if x < 0 or y < 0 or x > self.size or y > self.size:
            return

        self.map[int(x + y*self.size)].add(obj)

    def get(self, x, y):
        if x < 0 or y < 0 or x > self.size or y > self.size:
            return

        p = int(x + y*self.size)
        return self.map[p]

    def getV(self, v):
        return self.get(v.x, v.y)

    def bilinear(self, x, y, func):
        if not (0 <= x < self.size and 0 <= y < self.size):
            return None

        if isinstance(x, int) and isinstance(y, int):
            return self.map[x + self.size * y]

        if x.is_integer() and y.is_integer():
            p = int(x + self.size * y)
            return self.map[p]

        # bilinear interpolation
        gridx = math.floor(x)
        offsetx = x - gridx
        gridy = math.floor(y)
        offsety = y - gridy

        z1 = self.get(gridx, gridy)
        if gridx < self.size - 1:
            z2 = self.get(gridx + 1, gridy)
            if gridy < self.size - 1:
                z3 = self.get(gridx + 1, gridy + 1)
            else:
                z3 = z1
        else:
            z2 = z1
            z3 = z1
        if gridy < self.size - 1:
            z4 = self.get(gridx, gridy + 1)
        else:
            z4 = z1

        return func(z1, z2, z3, z4, offsetx, offsety)

    def forEach(self, func):
        for i in range(self.size*self.size):
            func(self.map[i])
