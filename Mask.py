import math
from array import *
import PIL
from PIL import Image


class Mask:
    def __init__(self, radius):
        """
        
        :param radius: 
        """
        self.radius = radius
        size = radius * 2
        self.mask = array('B', [0] * (size * size))  # float
        p = 0
        for y in range(size):
            for x in range(size):
                l = math.sqrt((radius - x)*(radius - x) + (radius - y)*(radius - y))
                if l > radius:
                    l = 255
                else:
                    l = round(l*255/radius)
                    if l < 128:
                        l = 0
                    else:
                        l = (l - 128)*2
                self.mask[p] = int(255-l)
                p += 1

    def apply(self, position, to, blend):
        """

        :param position:
        :param to:
        :param blend:
        :return:
        """
        x = position[0].x
        y = position[0].y
        z = position[1]

        radius = self.radius
        size = self.radius * 2
        data = blend.data
        data_s = blend.width * 4

        # // move the heightmap around the center
        for i in range(size):
            for j in range(size):
                px = x - radius + j
                py = y - radius + i

                if 0 <= px < to.size and 0 <= py < to.size:
                    p = px*4 + (blend.width-py)*data_s
                    m = self.mask[j + i*size]
                    z1 = z - m*4/255
                    if data[p] <= 128 and data[p+2] < m:
                        data[p+2] = m
                        to.set(px, py, z1)

    def applyBlend(self, position, terrain, channel):
        """

        :param position:
        :param terrain:
        :param blend:
        :param channel:
        :return:
        """
        # // convert heightmap coordinates to blendmap coordinates
        bm = terrain.heightmap2blendmap(position)
        x = int(bm.x)
        y = int(bm.y)

        blend = terrain.blendmap
        radius = self.radius
        size = self.radius * 2
        data = blend.data
        data_s = blend.size * 4
        blendSize = blend.size

        alpha = 3 - channel

        # // print mask on the blendmap
        for i in range(size):
            for j in range(size):
                px = x - radius + j
                py = y - radius + i

                if 0 <= px < blendSize and 0 <= py < blendSize:
                    p = px*4 + py*data_s + channel
                    m = self.mask[j + i*size]
                    if data[p] < m:
                        data[p] = m
                        data[p + alpha] = 255


class ElevationMask:
    """

    """
    def __init__(self, inner_radius, rim_radius):
        """

        :param inner_radius:
        :param rim_radius:
        """
        # // prepare an elevation mask
        self.size = rim_radius*2
        self.full = inner_radius
        self.mask = array('B', [0] * (self.size * self.size))  # unsigned byte
        self.effect = array('f', [0] * (self.size * self.size))  # float

        mask = self.mask
        effect = self.effect
        i = 0
        outer_len = rim_radius - inner_radius

        for y in range(-rim_radius, rim_radius):
            for x in range(-rim_radius, rim_radius):
                len = math.sqrt(x*x + y*y)

                if len > rim_radius:
                    mask[i] = 0
                    effect[i] = 0
                elif len > inner_radius:
                    len -= inner_radius
                    mask[i] = 1
                    effect[i] = 1 - math.cos(( outer_len - len)/outer_len * math.pi/2)
                else:
                    mask[i] = 1
                    effect[i] = 1
                i += 1

    def save(self, file):
        map = array('B', [0] * (self.size * self.size * 4))  # float

        p = 0
        for i in range(self.size*self.size):
            map[p] = int(self.effect[i]*255)
            map[p+1] = 0
            map[p+2] = 0
            map[p+3] = 255
            p += 4

        bytes = map.tobytes()
        im = PIL.Image.frombytes("RGBA", (self.size, self.size), bytes)
        im.save(file)

    def apply(self, current, sourcemap, map, effectmap, count):
        """

        :param current:
        :param sourcemap:
        :param map:
        :param effectmap:
        :return:
        """
        size = int(self.size/2)
        mask = self.mask
        effect = self.effect

        p = 0

        z = sourcemap.getV(current)
        source_size = sourcemap.size
        ky = current.y - size
        for y in range(-size, size):
            kx = current.x - size
            for x in range(-size, size):
                if kx < 0 or ky < 0 or kx >= source_size or ky >= source_size:
                    p += 1
                    continue

                if mask[p] == 0:
                    p += 1
                    continue

                z1 = map.get(kx, ky)
                if z1 == 0:
                    map.set(kx, ky, z)
                else:
                    map.set(kx, ky, z + z1)

                count.add(kx, ky, 1)

                alpha = effect[p]
                alpha1 = effectmap.get(kx, ky)
                effectmap.set(kx, ky, max(alpha, alpha1))

                p += 1
                kx += 1
            ky += 1
