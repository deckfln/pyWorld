"""

"""
import terrain as terr
import THREE as THREE

from Heightmap import *
from scenery import *
from Footprint import *


def city_find_flat_surface(terrain):
    """
    Find the center of a relatively flat surface on the terrain
    :param terrain:
    :return:
    """
    roads = terrain.roads.path
    normals = terrain.flat_areas()

    size = terrain.size
    sizen = normals.size
    ratio = size / sizen
    center = THREE.Vector2()

    # find the highest sum of normal along the roads.
    # the highest, the flatter surface
    p = 0
    maxi = -999999

    normal = THREE.Vector2()

    for segment in roads:
        normal.x = math.floor(segment.x/ratio)
        normal.y = math.floor(segment.y/ratio)

        z = normals.getV(normal)

        if z > maxi:
            maxi = z
            center.copy(normal)

    # // convert the cells coordinates to heightmap coordinates and keep the center of the cell
    center.x = center.x*ratio + ratio/2
    center.y = center.y*ratio + ratio/2

    return center


def City_flatten_terrain(terrain, box, hm, screen2hm):
    """
    Flattend the surface under a box, sommthly propagate the flatness around the box
    :param terrain:
    :param box:
    :param hm:
    :param screen2hm:
    :return:
    """
    center = hm.clone()

    # // move the terrain JUST under the box
    z = terrain.getV(hm)
    r = math.ceil(box.radius*screen2hm)
    box_r = r

    hm.x -= r
    hm.y -= r

    for y in range(int(r*2)):
        for x in range(int(r*2)):
            terrain.set(hm.x + x, hm.y + y, z)

    # // move the terrain AROUND the box
    hm.copy(center)
    r *= 3
    hm.x -= r
    hm.y -= r
    length = r - box_r
    p = THREE.Vector2()
    for y in range(int(r*2)):
        for x in range(int(r*2)):
            p.x = hm.x + x
            p.y = hm.y + y

            # //TODO: improve the smoothing function
            d = p.distanceTo(center) - box_r
            if d >= length:
                continue

            ratio = 1-math.cos((length-d)/length * math.pi/2)

            z1 = terrain.getV(p)
            if z1 is None:
                continue

            delta = (z1 - z) * ratio

            z1 -= delta

            terrain.setV(p, z1)


def city_paint_indexmap(terrain, center):
    """

    :param terrain:
    :param center:
    :return:
    """
    boundary = terrain.size - 1
    frontier = [center]
    loop = 32000
    next = THREE.Vector2()
    delay=0
    directions = [
        THREE.Vector2(0,1),
        THREE.Vector2(0,-1),
        THREE.Vector2(-1, 0),
        THREE.Vector2(1, 0)
    ]

    done = Heightmap(terrain.size)
    done.setV(center, -1)

    while len(frontier) > 0 and loop > 0:
        loop -= 1
        current = frontier.pop(0)
        delay = done.getV(current)

        if delay <= 0:
            z = terrain.getV(current)
            for i in range(4):
                d = directions[i]

                next.addVectors(current, d)
                if next.x < 0 or next.y < 0 or next.x > boundary or next.y > boundary:
                    continue

                if done.getV(next) != 0:
                    continue

                z1 = terrain.getV(next)
                done.setV(next, abs(z1 -z))

                frontier.append(next.clone())
        else:
            delay -= 0.1
            if delay == 0: delay = -0.4
            done.setV(current, delay)
            frontier.append(current)

    for y in range(terrain.size):
        for x in range(terrain.size):
            center.set(x, y)
            ok = done.getV(center)
            if ok < 0:
                terrain.setIndexMap(center, [terr.TILE_stone_path_png, 255, 255, 255])


house_texture = THREE.MeshLambertMaterial({
    'color': 0xeeeeee,
    'wireframe': False,
    'name': "house_texture"
})


class House(Scenery):
    def __init__(self, width, len, height, alpha, position):
        radius = math.sqrt(width*width + len*len)/2
        super().__init__(position, radius)

        self.width = width
        self.height = height
        self.len = len
        self.rotation = alpha

        footprint = FootPrint(
                THREE.Vector2(-width/2, -len/2),
                THREE.Vector2(width, len),
                radius,
                position,
                self
                )

        footprint.rotate(alpha)
        self.footprints.append(footprint)

    def build_mesh(self, level):
        geometry = THREE.BoxBufferGeometry(self.width, self.len, self.height)
        geometry.setDrawRange(0, 32)         # do not draw the bottom of the box
        geometry.translate(0, 0, self.height/2)
        geometry.rotateZ(self.rotation)

        mesh = THREE.Mesh(geometry, house_texture)

        return mesh
