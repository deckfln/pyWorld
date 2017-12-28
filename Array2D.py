"""

"""


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

    def forEach(self, func):
        for i in range(self.size*self.size):
            func(self.map[i])
