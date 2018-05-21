"""

"""

from Terrain import *
from PerlinSimplexNoise import *
from threading import Thread


def perlin_generate(terrain):
    """
    Generate a terrain heightmap using perlin
    :return:
    """
    global myrandom
    perlin = SimplexNoise(myrandom)
    total = terrain.size * terrain.size
    count = 0

    for i in range(terrain.size):
        for j in range(terrain.size):
            noise = 0
            s = 512
            h1 = terrain.height * 2

            for iteration in range(4):
                noise += perlin.noise(i / s, j / s) * h1
                s /= 2
                h1 /= 2

            terrain.set(i, j, noise)
            count += 1
        progress(count, total, "Perlin Generate")
    progress(0, 0)


def build_normalmap(terrain):
    """
    compute the normal map of the top heightmap
    :param heightmap:
    :param normalMap:
    :return:
    """
    heightmap = terrain.heightmap
    normalMap = terrain.normalMap

    pA = THREE.Vector3()
    pB = THREE.Vector3()
    pC = THREE.Vector3()
    cb = THREE.Vector3()
    ab = THREE.Vector3()

    normalMap.empty()

    current = 0
    total = heightmap.size * heightmap.size

    # // for each vertex, compute the face normal, and add to the vertex normal
    mA = THREE.Vector2()
    mB = THREE.Vector2()
    mC = THREE.Vector2()

    size = heightmap.size
    for y in range(size-1):
        for x in range(size-1):
            if y > 0:
                # // normalize Z againt the heightmap size
                zA = heightmap.get(x, y-1)
                zB = heightmap.get(x+1, y)
                zC = heightmap.get(x, y)

                terrain.map2screenXY(x, y-1, mA)
                terrain.map2screenXY(x+1, y, mB)
                terrain.map2screenXY(x, y, mC)

                pA.set(mA.np[0], mA.np[1], zA)
                pB.set(mB.np[0], mB.np[1], zB)
                pC.set(mC.np[0], mC.np[1], zC)

                cb.subVectors( pC, pB )
                ab.subVectors( pA, pB )
                cb.cross( ab )

                normalMap.add(x, y-1, cb)
                normalMap.add(x+1, y, cb)
                normalMap.add(x, y, cb)

            zA = heightmap.get(x, y)
            zB = heightmap.get(x+1, y)
            zC = heightmap.get(x+1, y+1)

            terrain.map2screenXY(x, y, mA)
            terrain.map2screenXY(x+1, y, mB)
            terrain.map2screenXY(x+1, y+1, mC)

            pA.set(mA.np[0], mA.np[1], zA)
            pB.set(mB.np[0], mB.np[1], zB)
            pC.set(mC.np[0], mC.np[1], zC)

            cb.subVectors( pC, pB )
            ab.subVectors( pA, pB )
            cb.cross( ab )

            normalMap.add(x, y, cb)
            normalMap.add(x+1, y, cb)
            normalMap.add(x+1, y+1, cb)
            current += 1

        progress(current, total, "Build normalMap")

    # // normalize the normals
    normalMap.normalize()

    progress(0, 0)


def _build_lod_mesh(terrain, quad, level, lx, ly, size, material, count):
    """

    :param center:
    :param size:
    :return:
    """
    quad_width = 16
    progress(count, terrain.nb_tiles, "Build terrain mesh")
    geometry = THREE.PlaneBufferGeometry(size, size, quad_width, quad_width)

    positions = geometry.attributes.position.array
    uvs = geometry.attributes.uv.array
    normals = geometry.attributes.normal.array

    screen = THREE.Vector2()
    normal = THREE.Vector3()
    hm = THREE.Vector2()

    uv_index = 0
    normal_index = 0

    heightmap = terrain.heightmap
    normalMap = terrain.normalMap
    ratio_screenmap_2_hm = terrain.onscreen / terrain.size

    map_size = terrain.size - 1
    half_quad_size = int((terrain.onscreen / (quad_width * 2**level)) / 2)

    pmin = size/2

    source_positions = np.copy(positions)

    for p in range(0, len(positions), 3):
        sx = source_positions[p]
        sy = source_positions[p + 1]
        screen_x = sx + lx
        screen_y = sy + ly

        # leave the borders alone ! they are needed for continuity between 2 tiles
        if half_quad_size >= 1 and -pmin < sx < pmin and -pmin < sy < pmin:
            # find the most visible point in the sub-quad
            max_x = -1
            max_y = -1
            max_z = -99999999

            py = screen_y - half_quad_size
            while py < screen_y + half_quad_size:
                px = screen_x - half_quad_size
                while px < screen_x + half_quad_size:
                    screen.x = px
                    screen.y = py
                    terrain.screen2map(screen, hm)
                    z = heightmap.bilinear(hm.x, hm.y)
                    if z > max_z:
                        max_x = px
                        max_y = py
                        max_z = z
                    px += ratio_screenmap_2_hm
                py += ratio_screenmap_2_hm

            positions[p] = max_x - lx
            positions[p + 1] = max_y - ly

            screen.x = max_x
            screen.y = max_y
            terrain.screen2map(screen, hm)
        else:
            screen.x = screen_x
            screen.y = screen_y
            terrain.screen2map(screen, hm)
            max_z = heightmap.bilinear(hm.x, hm.y)

        positions[p + 2] = max_z

        uvs[uv_index] = hm.x / map_size
        uvs[uv_index + 1] = hm.y / map_size
        uv_index += 2

        normalMap.bilinear(hm.x, hm.y, normal)

        normals[p] = normal.x
        normals[p+1] = normal.y
        normals[p+2] = normal.z
        normal_index += 1

    plane = THREE.Mesh(geometry, material)
    plane.castShadow = True
    plane.receiveShadow = True
    plane.position.x = lx
    plane.position.y = ly

    quad.mesh = plane
    quad.center = THREE.Vector2(lx, ly)
    quad.lod_radius = terrain.radiuses[level]
    quad.visibility_radius = math.sqrt(2)*size/2
    quad.size = size
    quad.level = level
    quad.name = "%d-%d-%d" % (level, lx, ly)

    # sub-divide
    halfSize = size / 2
    quadSize = size / 4

    if level < terrain.nb_levels - 1:
        quad.sub[0] = Quadtree( -1, -1, -1, quad)     # nw
        quad.sub[1] = Quadtree( -1, -1, -1, quad)     # ne
        quad.sub[2] = Quadtree( -1, -1, -1, quad)     # sw
        quad.sub[3] = Quadtree( -1, -1, -1, quad)     # se

        count = _build_lod_mesh(terrain, quad.sub[0], level + 1, lx - quadSize, ly - quadSize, halfSize, material, count + 1)
        count = _build_lod_mesh(terrain, quad.sub[1], level + 1, lx + quadSize, ly - quadSize, halfSize, material, count + 1)
        count = _build_lod_mesh(terrain, quad.sub[2], level + 1, lx - quadSize, ly + quadSize, halfSize, material, count + 1)
        count = _build_lod_mesh(terrain, quad.sub[3], level + 1, lx + quadSize, ly + quadSize, halfSize, material, count + 1)

    return count


def build_mesh(terrain):
    """
    Build the LOD meshes and the Quad Tree
    :return:
    """
    _build_lod_mesh(terrain, terrain.quadtree, 0, 0, 0, terrain.size, None, 1)
    progress(0, 0)


def build_mesh_scenery(terrain):
    """
    Create a mesh for each object on the terrain
    Insert the mesh in the proper Quad based on it's footprint
    :return:
    """
    root = terrain.quadtree

    nb = len(terrain.scenery)
    i = 0
    for object in terrain.scenery:
        progress(i, nb, "Prepare scenery")
        root.insert_object(object, 0)
        i += 1

    progress(0, 0)

    # root.scenery_instance()

    progress(0, 0)
