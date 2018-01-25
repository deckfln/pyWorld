"""

"""
import Terrain as terr
import THREE as THREE

from Heightmap import *
from Scenery import *
from Footprint import *
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
            normal = terrain.normalMap.bilinear(hm.x, hm.y)
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


vertexShader = """
precision highp float;

uniform mat4 modelViewMatrix;
uniform mat4 projectionMatrix;

attribute vec3 position;
attribute vec3 offset;
atrribute vec3 normal;
attribute vec3 color;

varying vec3 vColor;
varying vec3 vNormal;

void main() {
    vColor.xyz = color.xyz;
    vec3 vPosition = position;
    gl_Position = projectionMatrix * modelViewMatrix * vec4( offset + vPosition, 1.0 );

    vNormal = normal;
}
"""

fragmentShader = """
precision highp float;

uniform vec3 light;
uniform vec3 ambientLight;

varying vec3 vColor;
varying vec3 vNormal;

void main() {

    // Add directional light
    vec3 nlight = normalize(light);
    float nDotl = dot(vertexNormal, nlight);
    float brightness = max(nDotl, 0.0);
    vec3 diffuse = vec4(1.0) * brightness;

    gl_FragColor = diffuse * vec4(vColor, 255);

}
"""

"""
house_texture = (THREE.MeshLambertMaterial({
    'color': 0xeeeeee,
    'wireframe': False,
    'name': "house_texture"
}))
"""

house_texture = THREE.RawShaderMaterial({
        'uniforms': {
            'light': {'type': "v3", 'value': THREE.Vector3()},
        },
        'vertexShader': vertexShader,
        'fragmentShader': fragmentShader,
    })


class House(Scenery):
    def __init__(self, width, len, height, alpha, position):
        radius = math.sqrt(width*width + len*len)/2
        super().__init__(position, radius)

        self.type = 0
        self.width = width
        self.height = height
        self.len = len
        self.rotation = alpha

        footprint = FootPrint(
                THREE.Vector2(-width/2, -len/2),
                THREE.Vector2(width, len),
                radius,
                position,
                10,
                self
                )

        footprint.rotate(alpha)
        self.footprints.append(footprint)

    def build_mesh(self, level):
        w = 10
        geometry = THREE.BoxBufferGeometry(w, w, w)
        geometry.setDrawRange(0, 32)         # do not draw the bottom of the box
        geometry.translate(0, 0, w/2)
        # geometry.rotateZ(self.rotation)

        instancedBufferGeometry = THREE.InstancedBufferGeometry().copy(geometry)

        colors = instancedBufferGeometry.attributes.position.clone()
        for i in range(0, len(colors.array), 3):
            colors.array[i] = 0.84
            colors.array[i + 1] = 0.27
            colors.array[i + 2] = 0.37
            instancedBufferGeometry.addAttribute('color', colors)  # per mesh translation

        mesh = THREE.Mesh(instancedBufferGeometry, None)

        return mesh
