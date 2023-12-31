"""

"""
import Terrain as terr
import THREE as THREE

from Heightmap import *
from House import *
from Utils import *


def city_create(terrain):
    """
    Find a flat area on the map and build a city
    :return:
    """
    objects = terrain.scenery
    indexmap_size = terrain.indexmap.size
    road = terrain.roads

    # // find a relatively flat section of the heightmap to implement the city
    center = city_find_flat_surface(terrain)

    # // from the center of the flat section, paint the city following less height delta
    city_paint_indexmap(terrain, center)

    v = THREE.Vector2()
    normal = THREE.Vector3()

    screen2hm = terrain.size / terrain.onscreen

    # // implement boxes
    for i in range(indexmap_size):
        for j in range(indexmap_size):
            v.x = j
            v.y = i

            # // ensure we are on the city area
            if not terrain.isCity_indexmap(v):
                continue

            # // check there is no road nor river at that place
            if terrain.isRiverOrRoad_indexmap(v):
                continue

            # // convert from indexmap coordinate to heightmap coordinate
            v.x += 0.5
            hm = terrain.indexmap2heighmap(v)

            # // check the terrain is not too vertical at that point
            terrain.normalMap.bilinear(hm.x, hm.y, normal)
            if normal.z < 0.95:
                continue

            # // ensure we're not too close to the road
            if road.distanceTo(hm) < 16:
                continue

            r = normal.x * math.pi
            z = terrain.get(hm.x, hm.y)

            # rt from heightmap coordinate to world coordinate
            world = terrain.map2screen(hm)

            position = THREE.Vector3(world.x, world.y, z)

            box = House(8, 8, 8, r, position)

            # flatten the terrain around the object
            City_flatten_terrain(terrain, box, hm, screen2hm)

            # add to the terrain
            objects.append(box)


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
