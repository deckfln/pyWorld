import math
import pickle
import numpy as np
from collections import deque

import THREE

from roads import *
from prng import *
from PerlinSimplexNoise import *
from progress import *
from quadtree import *
from TextureMap import *
from VectorMap import *
from IndexMap import *

myrandom = Random(5454334)


TILE_blend_png = 0
TILE_water_png = 1
TILE_riverbed_png = 2
TILE_grass_png = 3
TILE_grass1_png = 4
TILE_grass2_png = 5
TILE_forest_png = 6
TILE_forest1_png = 7
TILE_forest2_png = 8
TILE_paving_png = 9
TILE_rock_png = 10
TILE_dirt_png = 11
TILE_dirt1_png = 12
TILE_stone_path_png = 13

_vector3 = THREE.Vector3()
_vector2 = THREE.Vector2()


class Terrain:
    def __init__(self, size, height, onscreen):
        """

        :param size:
        :param height:
        :param onscreen:
        """
        self.size = size
        self.height = height
        self.onscreen = onscreen
        self.heightmap = Heightmap(size, height)
        self.nb_levels = 6
        self.lod = 2**(self.nb_levels-1)   # // 2^5
        self.heightmaps = [None]*self.nb_levels
        self.quad_lod = [None]*self.nb_levels
        self.tiles = [None]*self.nb_levels
        self.normalMap = None
        self.indexmap = IndexMap(32, 128)
        self.blendmap = TextureMap(256, 1)
        self.scenery = []
        self.roads = None
        self.radiuses = [0] * self.nb_levels

        self.ratio = (self.size-1)/self.onscreen
        self.half = self.onscreen/2

        self.tiles_onscreen = []

        # THREE objects
        self.scene = None
        self.material = None
        self.textures = []
        self.light = None

        # index backup for tiles
        self.quadtree_mesh_indexes = None

        # total number of tiles
        nb_tiles = 1
        width = 1
        for i in range(self.nb_levels):
            nb_tiles += width
            width *= 4
        self.nb_tiles = nb_tiles

        """
        compute the radius at each level
        this is the sum of the radius at one level + the radiuses at at sub-levels
        """
        for i in range(self.nb_levels):
            size = self.onscreen / math.pow(2, i)
            self.radiuses[i] = math.sqrt(size*size/2)
            for j in range(i+1, self.nb_levels):
                size = self.onscreen / math.pow(2, j)
                self.radiuses[i] += math.sqrt(size*size/2)

        """
        initialize the quadtree
        """
        self.quadtree = Quadtree(-1, -1, -1, None)
        self.quadtree_index = {}

    def init(self):
        self.normalMap = VectorMap(self.size)

    def shaders(self, light):
        """
        Initialize the shader material
        :param light:
        :return:
        """
        if Config['terrain']['debug']['uv']:
            loader = THREE.TextureLoader()
            self.material = THREE.MeshPhongMaterial({
                'map': loader.load('img/UV_Grid_Sm.jpg'),
                'wireframe': False
            })
        elif Config['terrain']['debug']['lod']:
            self.material = None
        else:
            """
            Initialize the various maps
            :return:
            """
            loader = THREE.TextureLoader()

            indexmap = loader.load("img/indexmap.png")

            indexmap.magFilter = THREE.NearestFilter
            indexmap.minFilter = THREE.NearestFilter
            self.indexmap.texture = indexmap

            textures = [
                "img/blendmap.png",
                "img/water.png",
                "img/riverbed.png",
                "img/grass.png",
                "img/grass1.png",
                "img/grass2.png",
                "img/forest.png",
                "img/forest1.png",
                "img/forest2.png",
                "img/paving.png",
                "img/rock.png",
                "img/dirt.png",
                "img/dirt1.png",
                "img/stone_path.png"
            ]

            self.textures = []
            for name in textures:
                t = loader.load(name)
                t.generateMipmaps = True
                t.minFilter = THREE.LinearMipMapLinearFilter
                t.magFilter = THREE.LinearFilter
                t.wrapS = THREE.RepeatWrapping
                t.wrapT = THREE.RepeatWrapping
                self.textures.append(t)

            loader = THREE.FileLoader()
            uniforms = {
                'textures': {'type': "tv", 'value': self.textures},
                'light': {'type': "v3", 'value': light.position},
                'water_shift': {'type': "f", 'value': 0},
                'indexmap': {'type': "t", 'value': self.indexmap.texture},
                'indexmap_size': {'type': "f", 'value': self.indexmap.size},
                'indexmap_repeat': {'type': "f", 'value': self.indexmap.repeat},
                'blendmap_repeat': {'type': "f", 'value': 64}
            }

            if Config["shadow"]["enabled"]:
                uniforms['directionalShadowMap'] = {'type': 'v', 'value': light.shadow.map.texture}
                uniforms['directionalShadowMatrix'] = {'type': 'm4', 'value': light.shadow.matrix}
                uniforms['directionalShadowSize'] = {'type': 'v2', 'value': light.shadow.mapSize}

            self.material = THREE.ShaderMaterial( {
                'uniforms': uniforms,
                'vertexShader': loader.load('shaders/vertex.glsl'),
                'fragmentShader': loader.load('shaders/fragment.glsl'),
                'wireframe': Config['terrain']['debug']['wireframe']
            })

    def build(self):
        self.indexmap.build()

    def load(self, sun):
        """
        Load the quad tile pickles and initialize the shaders
        :param sun:
        :return:
        """
        self.light = sun

        self.shaders(sun)
        with open("bin/heightmap.pkl", "rb") as f:
            self.heightmap = pickle.load(f)

        with open("bin/normalmap.pkl", "rb") as f:
            self.normalMap = pickle.load(f)

        with open("bin/worldmap.pkl", "rb") as f:
            quads = pickle.load(f)
            self.quadtree = quads[0]
            quads[0].build_index(self.quadtree_index)
            Quadtree.material = self.material

        self.indexmap.load("img/indexmap.png")
        self.blendmap.load("img/blendmap.png")

    def get(self, x, y):
        """
        return the billinera Z value at position (x,y)
        :param x:
        :param y:
        :return:
        """
        return self.heightmap.bilinear(x, y)

    def getV(self, v):
        """

        :param v:
        :return:
        """
        return self.get(v.x, v.y)

    def set(self, x, y, height):
        """

        :param x:
        :param y:
        :param height:
        :return:
        """
        self.heightmap.set(x, y, height)

    def setV(self, v, z):
        self.set(v.x, v.y, z)

    def get_normalV(self, v):
        return self.normalMap.bilinear(v.x, v.y, _vector3)

    def getBlendMap(self, v):
        """
         * @description get the blend map value at heightmap position
        :param v:
        :return:
        """
        # // convert from the heightmap coordinates to the blendmap coordinates
        # // and round to the nearest point
        self.heightmap2blendmap(v, self.vector2)
        return self._getBlendMap(self.vector2)

    def _getBlendMap(self, bp):
        """

        :param bp:
        :return:
        """
        return self.blendmap.get(bp)

    def _setBlendMap(self, bp, value):
        """

        :param bp:
        :param value:
        :return:
        """
        self.blendmap.set(bp, value)

    def getIndexMap(self, v):
        """
         * @description get the index map value at heightmap position *
        :param v:
        :return:
        """
        # // convert from the heightmap coordinates to the blendmap coordinates
        # // and round to the nearest point
        self.heightmap2indexmap(v, self.vector2)
        return self._getIndexMap(self.vector2)

    def _getIndexMap(self, v):
        """
         * @description get the index map value at indexmap position *
        :param v:
        :return:
        """
        return self.indexmap.get(v)

    def _setIndexMap(self, v, value):
        """
         * @description get the index map value at indexmap position *
        :param v:
        :param value:
        :return:
        """
        self.indexmap.set(v, value)

    def setIndexMap(self, v, value):
        """
         * @description get the index map value at heightmap position *
        :param v:
        :param value:
        :return:
        """
        # // convert from the heightmap coordinates to the blendmap coordinates
        # // and round to the nearest point
        ip = self.heightmap2indexmap(v)
        return self._setIndexMap(ip, value)

    def _getIndexMapXY(self, x, y):
        """
         * @description get the index map value at indexmap position *
        :param x:
        :param y:
        :return:
        """
        return self.indexmap.getXY(x,y)

    def perl_generate(self):
        """
        Generate a terrain heightmap
        :return:
        """
        global myrandom
        perlin = SimplexNoise(myrandom)
        total = self.size*self.size
        count = 0

        for i in range(self.size):
            for j in range(self.size):
                noise = 0
                s = 512
                h1 = self.height*2

                for iteration in range(4):
                    noise += perlin.noise(i/s, j/s) * h1
                    s /= 2
                    h1 /= 2

                self.set(i, j, noise)
                count += 1
            progress(count, total, "Perlin Generate")
        progress(0, 0)

    def _buildLOD(self, level, points_per_block, heightmaps):
        """
        Recursively build multiple LOD of the heightmap
        :param level:
        :param points_per_block:
        :param heightmaps:
        :return:
        """
        # // build LOD0
        size = self.size
        divided_size = size / points_per_block

        heightmaps[level] = Heightmap(divided_size, self.onscreen)
        hm = heightmaps[level].map

        current = 0
        total = divided_size*divided_size

        for y in range(0, size, points_per_block):
            for x in range(0, size, points_per_block):
                # // keep the original values on the border to avoid seams between tiles
                if x == 0 or y == 0:
                    p = x + y * size
                    hm[current] = self.heightmap.map[p]
                    current += 1
                    continue

                if x >= size - points_per_block and y >= size - points_per_block:
                    p = size - 1 + (size - 1) * size
                    hm[current] = self.heightmap.map[p]
                    current += 1
                    continue

                if x >= size - points_per_block:
                    p = size - 1 + y * size
                    hm[current] = self.heightmap.map[p]
                    current += 1
                    continue

                if y >= size - points_per_block:
                    p = x + (size - 1) * size
                    hm[current] = self.heightmap.map[p]
                    current += 1
                    continue

                # // get the max of the points_per_block surround the current point
                sum = 0
                nb = 0
                max = -99999

                half = int(points_per_block/2)
                for i in range(y - half, y + half):
                    for j in range(x - half, x + half):
                        # // crop the cell
                        if i < 0 or j < 0 or i >= size or j >= size:
                            continue

                        p = j + i * size
                        h = self.heightmap.map[p]

                        # // do the math
                        if h > max:
                            max = h
                        sum += h
                        nb += 1

                # // and register the LOD height
                hm[current] = sum / nb
                current += 1
            progress(current, total, "Build LOD %d" % level)

        progress(0, 0)
        # // recurse until points_per_block == 1
        if points_per_block > 2:
            self._buildLOD(level + 1, int(points_per_block / 2), heightmaps)
        else:
            # // when point_per_block == 1, just copy the heightmap
            heightmaps[level + 1] = self.heightmap

    def buildHeightmapsLOD(self):
        """
        Build smaller versions of the top heightmap
        :return:
        """
        self._buildLOD(0, self.lod, self.heightmaps)

    def map2screen(self, position, target=None):
        """
        convert heightmap (max level) coord to screen coordinate
        :param position:
        :return:
        """
        if target is None:
            target = THREE.Vector2()

        target.x = position.x * self.onscreen / self.size - self.onscreen / 2
        target.y = position.y * self.onscreen / self.size - self.onscreen / 2

        return target

    def map2screenXY(self, x, y, target=None):
        """
        convert heightmap (max level) coord to screen coordinate
        :param x:
        :param y:
        :return:
        """
        if target is None:
            target = THREE.Vector2()

        target.x = x * self.onscreen / self.size - self.onscreen / 2
        target.y = y * self.onscreen / self.size - self.onscreen / 2

        return target

    def screen2map(self, position, target=None):
        """
         * @description convert screen coordinate to heightmap (max level) coord
        """
        # // The center if the onscreen grid is 0,0
        # // so we have to move by the half of the grid size
        if not target:
            target = THREE.Vector2()

        ratio = self.ratio
        half = self.half
        target.x = (position.x + half) * ratio
        target.y = (position.y + half) * ratio
        return target

    def screen2mapXY(self, x, y, target=None):
        """
         * @description convert screen coordinate to heightmap (max level) coord
        """
        # // The center if the onscreen grid is 0,0
        # // so we have to move by the half of the grid size
        if not target:
            target = THREE.Vector2()

        ratio = self.ratio
        half = self.half
        target.x = (x + half) * ratio
        target.y = (y + half) * ratio

        return target

    def heightmap2blendmap(self, position, target=None):
        """
         * @desccription convert from heightmap coordinates to blendmap coordinates
        :param position:
        :return:
        """
        if not target:
            target = THREE.Vector2()

        target.set(
            position.x * self.blendmap.size / self.size,
            self.blendmap.size - position.y * self.blendmap.size / self.size
        )
        return target

    def indexmap2blendmap(self, position):
        """
         * @desccription convert from heightmap coordinates to blendmap coordinates
        :param position:
        :return:
        """
        p = THREE.Vector2(
            math.floor(position.x * self.blendmap.size / self.indexmap.size),
            math.floor((self.blendmap.size - 1) - position.y * self.blendmap.size / self.indexmap.size)
        )
        return p

    def indexmap2heighmap(self, v):
        """
         * @desccription convert from ixmap coordinates to heightmap coordinates
        :param v:
        :return:
        """
        return self.indexmap2heightmapXY(v.x, v.y)

    def indexmap2heightmapXY(self, x, y):
        """
         * @desccription convert from ixmap coordinates to heightmap coordinates
        :param x:
        :param y:
        :return:
        """
        p = THREE.Vector2(
            x * self.size / self.indexmap.size,
            (self.indexmap.size - y) * self.size / self.indexmap.size - 1)
        return p

    def heightmap2indexmap(self, v, target=None):
        """
         * @desccription convert from heightlao coordinates to index coordinates
        :param v:
        :return:
        """
        if target is None:
            target = THREE.Vector2()

        target.x = v.x * self.indexmap.size / self.size
        target.y = self.indexmap.size - v.y * self.indexmap.size / self.size

        return target

    def build_normalmap(self):
        """
        compute the normal map of the top heightmap
        :param heightmap: 
        :param normalMap: 
        :return: 
        """
        heightmap = self.heightmap
        normalMap = self.normalMap

        pA = THREE.Vector3()
        pB = THREE.Vector3()
        pC = THREE.Vector3()
        cb = THREE.Vector3()
        ab = THREE.Vector3()

        normalMap.empty()

        current = 0
        total = heightmap.size * heightmap.size

        # // for each vertex, compute the face normal, and add to the vertex normal
        def _initVector():
            return THREE.Vector3()

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

                    self.map2screenXY(x, y-1, mA)
                    self.map2screenXY(x+1, y, mB)
                    self.map2screenXY(x, y, mC)

                    pA.set(mA.x, mA.y, zA)
                    pB.set(mB.x, mB.y, zB)
                    pC.set(mC.x, mC.y, zC)

                    cb.subVectors( pC, pB )
                    ab.subVectors( pA, pB )
                    cb.cross( ab )

                    normalMap.add(x, y-1, cb)
                    normalMap.add(x+1, y, cb)
                    normalMap.add(x, y, cb)

                zA = heightmap.get(x, y)
                zB = heightmap.get(x+1, y)
                zC = heightmap.get(x+1, y+1)

                self.map2screenXY(x, y, mA)
                self.map2screenXY(x+1, y, mB)
                self.map2screenXY(x+1, y+1, mC)

                pA.set(mA.x, mA.y, zA)
                pB.set(mB.x, mB.y, zB)
                pC.set(mC.x, mC.y, zC)

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

    def _build_lod_mesh(self, quad, level, x, y, size, material, count):
        """

        :param center:
        :param size:
        :return:
        """
        progress(count, self.nb_tiles, "Build terrain mesh")
        geometry = THREE.PlaneBufferGeometry(size, size, 16, 16)

        positions = geometry.attributes.position.array
        uvs = geometry.attributes.uv.array
        normals = geometry.attributes.normal.array

        screen = THREE.Vector2()
        normal = THREE.Vector3()
        hm = THREE.Vector2()

        uv_index = 0
        normal_index = 0

        heightmap = self.heightmap
        normalMap = self.normalMap
        map_size = self.size

        for p in range(0, len(positions), 3):
            screen.x = positions[p] + x
            screen.y = positions[p + 1] + y

            self.screen2map(screen, hm)
            z = heightmap.bilinear(hm.x, hm.y)
            positions[p + 2] = z

            uvs[uv_index] = hm.x / (map_size - 1)
            uvs[uv_index + 1] = hm.y / (map_size - 1)
            uv_index += 2

            normalMap.bilinear(hm.x, hm.y, normal)

            normals[p] = normal.x
            normals[p+1] = normal.y
            normals[p+2] = normal.z
            normal_index += 1

        plane = THREE.Mesh(geometry, material)
        plane.castShadow = True
        plane.receiveShadow = True
        plane.position.x = x
        plane.position.y = y

        quad.mesh = plane
        quad.center = THREE.Vector2(x, y)
        quad.lod_radius = self.radiuses[level]
        quad.visibility_radius = math.sqrt(2)*size/2
        quad.size = size
        quad.level = level
        quad.name = "%d-%d-%d" % (level, x, y)

        # sub-divide
        halfSize = size / 2
        quadSize = size / 4

        if level < self.nb_levels - 1:
            quad.sub[0] = Quadtree( -1, -1, -1, quad)     # nw
            quad.sub[1] = Quadtree( -1, -1, -1, quad)     # ne
            quad.sub[2] = Quadtree( -1, -1, -1, quad)     # sw
            quad.sub[3] = Quadtree( -1, -1, -1, quad)     # se

            count = self._build_lod_mesh(quad.sub[0], level + 1, x - quadSize, y - quadSize, halfSize, material, count + 1)
            count = self._build_lod_mesh(quad.sub[1], level + 1, x + quadSize, y - quadSize, halfSize, material, count + 1)
            count = self._build_lod_mesh(quad.sub[2], level + 1, x - quadSize, y + quadSize, halfSize, material, count + 1)
            count = self._build_lod_mesh(quad.sub[3], level + 1, x + quadSize, y + quadSize, halfSize, material, count + 1)

        return count

    def _build_mesh(self, start_x, start_y, tile_onscreen_size, material):
        """
        Build a mesh with a tile of the map
        :param heightmap:
        :param start_x:
        :param start_y:
        :param tile_size:
        :param tile_onscreen_size:
        :param material:
        :return:
        """
        j = 0
        uv_index = 0

        points_per_tile = 16

        normalMap = self.normalMap
        geometry = THREE.PlaneBufferGeometry(tile_onscreen_size, tile_onscreen_size, points_per_tile, points_per_tile)

        positions = geometry.attributes['position'].array
        uvs = geometry.attributes['uv'].array
        normals = geometry.attributes['normal'].array

        # // due to the way the positions will be pushed, it is needed to invert the indexes
        indexes = geometry.index.array
        for i in range(0, len(indexes), 3):
            swap = indexes[i]
            indexes[i] = indexes[i+1]
            indexes[i+1] = swap

        # // compute the onscreen center of the tile
        center = THREE.Vector3(
                tile_onscreen_size / 2,
                tile_onscreen_size / 2,
                0
                )

        mid_map = self.onscreen/2
        step = (tile_onscreen_size) / points_per_tile
        screen = THREE.Vector2()
        y = start_y
        while y <= start_y + tile_onscreen_size:
            x = start_x
            while x <= start_x + tile_onscreen_size:
                screen.x = x - mid_map
                screen.y = y - mid_map
                hm = self.screen2map(screen)

                print(screen.x, screen.y, hm.x, hm.y)
                z = self.heightmap.bilinear(hm.x, hm.y)

                # // move the point relative position
                positions[j] = x - mid_map
                positions[j + 1] = y - mid_map
                positions[j + 2] = z

                uvs[uv_index] = positions[j] / self.onscreen
                uvs[uv_index + 1] = positions[j + 1] / self.onscreen

#                normal = normalMap.get(hm.x, hm.y)
#                normals[j] = normal.x
#                normals[j+1] = normal.y
#                normals[j+2] = normal.z

                j += 3
                uv_index += 2

                x += step
            y += step

        plane = THREE.Mesh(geometry, material)
        plane.castShadow = True
        plane.receiveShadow = True

        return plane

    def _build_tiles_lod(self, level, material):
        """
        Create a mesh per tile on that level
        :param heightmap:
        :param material:
        :return:
        """
        nb_tiles = 2 ** level
        tile_onscreen_size = self.onscreen / nb_tiles

        # the 3D plane is one pixel wider than the heightmap

        tiles = []
        for y_tile in range(0, nb_tiles):
            for x_tile in range(0,  nb_tiles):
                x = x_tile * tile_onscreen_size
                y = y_tile * tile_onscreen_size

                mesh = self._build_mesh(x, y, tile_onscreen_size, material)
                tiles.append(mesh)

        return tiles

    def _initLOD(self):
        """
        Connect all tiles into a quad Tree
        :return:
        """
        nb_levels = len(self.heightmaps)

        size = 1
        for i in range(nb_levels):
            self.quad_lod[i] = [None] * size
            for j in range(size):
                self.quad_lod[i][j] = Quadtree(-1, -1, -1)
            size *= 4

        # // compute the radius at each level
        # // this is the sum of the radius at one level + the radiuses at at sub-levels
        radiuses = [0] * nb_levels
        for i in range(nb_levels):
            size = self.onscreen / math.pow(2, i)
            radiuses[i] = math.sqrt(size*size/2)
            for j in range(i+1, nb_levels):
                size = self.onscreen / math.pow(2, j)
                radiuses[i] += math.sqrt(size*size/2)

        # // link the quad into a tree
        size = 1
        for i in range(nb_levels):
            level = self.quad_lod[i]
            for y in range(size):
                for x in range(size):
                    current_level_index = x+y*size
                    quad = level[current_level_index]

                    # // register center and width
                    mesh = self.tiles[i][current_level_index]
                    quad.mesh = mesh
                    quad.center = THREE.Vector2(mesh.position.x, mesh.position.y)
                    quad.lod_radius = radiuses[i]
                    quad.size = self.onscreen / math.pow(2, i)
                    quad.level = i
                    quad.name = "%d-%d-%d" % (i, x , y)

                    mesh.geometry.computeBoundingSphere()

                    if i < nb_levels-1:
                        next_level = self.quad_lod[i + 1]
                        x1 = x*2   # // next level coordinate
                        y1 = y*2

                        # /*
                        # * +----+----+
                        # * + nw ! ne +
                        # * +----+----+
                        # * + sw ! se +
                        # * +----+----+
                        # */
                        next_level_rowsize = 2*size
                        nw = x1 + y1*next_level_rowsize
                        ne = x1 + 1 + y1*next_level_rowsize
                        sw = x1 + (y1+1)*next_level_rowsize
                        se = x1 + 1 + (y1+1)*next_level_rowsize

                        quad.sub[0] = next_level[nw]
                        quad.sub[1] = next_level[ne]
                        quad.sub[2] = next_level[sw]
                        quad.sub[3] = next_level[se]
            size *= 2

    def buildTerrainMesh(self):
        """
        Build the LOD meshes and the Quad Tree
        :return:
        """
        self._build_lod_mesh(self.quadtree, 0, 0, 0, self.size, None, 1)
        progress(0, 0)

    def flat_areas(self):
        """
        Sum up normals into a smaller grid to indicate flat areas
        :return: 
        """
        size = self.size

        # // Sum up the terrain normals in a grid / 32
        # // find the highest sum of normal.
        # // the highest, the flatter surface
        flatten_size = self.size / 32
        indexm = Heightmap(flatten_size)
        ratio = size / flatten_size
        normalmap = self.normalMap
        normal = THREE.Vector3()

        p = 0
        for y in range(size):
            for x in range(size):
                normalmap.get(x, y, normal)
                z = normal.z

                p2 = int(math.floor(x / ratio) + math.floor(y / ratio)*flatten_size)

                z1 = indexm.map[p2] + z
                indexm.map[p2] = z1

                p += 1

        return indexm

    def isRiverOrRoad(self, v):
        """
         * @description check if there is a river or a road cell from the heightmap coordinates
         :param v
        """
        # // convert from the heightmap coordinates to the blendmap coordinates
        # // and round to the nearest point
        self.heightmap2blendmap(v, _vector2)
        c = self.blendmap.get(_vector2)

        return c.x > 128 or c.z > 128

    def isRiverOrRoad_indexmap(self, v):
        """
         * @description check if there is a river or a road cell from the indexmap coordinates
        :param v:
        :return:
        """
        # // convert from the indexmap coordinates to the blendmap coordinates
        bm = self.indexmap2blendmap(v)
        c = self.blendmap.get(bm)

        return c.x > 128 or c.z > 128

    def isForest_heightmap(self, v):
        """
         * @description check if there is a forest on the indexmap
        :param v:
        :return:
        """
        # // convert from the heightmap coordinates to the index coordinates
        # // and round to the nearest point
        im = self.heightmap2indexmap(v)
        c = self._getIndexMap(im)

        return (c.x == TILE_forest_png) or (c.x==TILE_forest1_png) or (c.x==TILE_forest2_png)

    def isForest_indexmap(self, v):
        """
         * @description check if there is a forest on the indexmap
        :param v:
        :return:
        """
        # // use index coordinates
        # // and round to the nearest point
        c = self._getIndexMap(v)

        return (c.x == TILE_forest_png) or (c.x==TILE_forest1_png) or (c.x==TILE_forest2_png)

    def isCity_indexmap(self, v):
        """
         * @description check if there is a forest on the indexmap
        :param v:
        :return:
        """
        # // use index coordinates
        # // and round to the nearest point
        c = self._getIndexMap(v)

        return c.x == TILE_stone_path_png

    def isOnMap(self, v):
        """

        :param v:
        :return:
        """
        return v.x >= 0 and v.x <= self.size and v.y >= 0 and v.y <= self.size

    def isOnIndexMap(self, v):
        """

        :param v:
        :return:
        """
        return v.x >= 0 and v.x <= self.indexmap.size and v.y >= 0 and v.y <= self.indexmap.size

    def build_roads(self):
        """
        Build 2 roads on the terrain
        :return:
        """
        self.roads = Roads(self)

    def dump(self):
        """
        Save all data of the terrain
        :return:
        """
        with open("bin/heightmap.pkl", "wb") as f:
            pickle.dump(self.heightmap, f)

        with open("bin/normalmap.pkl", "wb") as f:
            pickle.dump(self.normalMap, f)

        # dump the meshes
        self.quadtree.dump_mesh()

        # pack the quad into an array
        # this will DELETE the meshes so they are NOT in the pickle
        worldmap = []
        self.quadtree.dump(worldmap)
        with open("bin/worldmap.pkl", "wb") as f:
            pickle.dump(worldmap, f)

        self.indexmap.generate("img/indexmap.png")
        self.blendmap.generate("img/blendmap.png")

    def _check_quad_lod(self, position: Vector2, quad: Quadtree, tiles_2_display: list):
        """
        @description Recursively check the tiles quadtree to find what is on scree,
        @param {type} position
        @param {type} quad
        @param {type} tiles_2_display
        @returns {undefined}
        """
        quad.traversed = True

        # detect end of tree
        if not quad.sub[0]:
            tiles_2_display.append(quad)
            return

        distance = position.distanceTo(quad.center)
        if distance <= (math.sqrt(quad.size*quad.size + quad.size*quad.size)):    # lod_radius:
            # check the sub tiles
            for i in range(4):
                self._check_quad_lod(position, quad.sub[i], tiles_2_display)
        else:
            # The tile is far away, so display it
            # add the tile on the display list if needed
            tiles_2_display.append(quad)

    def _add_full_quadrant(self, position: Vector2, tiles_2_display: list, max_depth, tile):
        """

        :param position:
        :param tiles_2_display:
        :return:
        """
        if tile is None:
            tile = self.quadtree.around(position, max_depth)
        else:
            index = "%d-%d-%d" % (max_depth, position.np[0], position.np[1])
            # tile = self.quadtree.around(position, max_depth)
            tile = self.quadtree_index[index]

        parent = tile.parent

        quadrant = -1       # north/east, north/west ...

        # add all direct neighbors
        for i in range(4):
            quad = parent.sub[i]
            if quad == tile:
                quadrant = i
            if not quad.traversed:
                quad.traversed = True
                tiles_2_display.append(quad)

        parent.traversed = True

        return tile, quadrant

    def _find_add_quadrant(self, e, x, y, tiles_2_display, queue):
        position = e[0]
        max_depth = e[1]
        tile1 = e[2]

        if x == 0 and y == 0 and tile1 is not None:
            _vector2.np[0] = tile1.center.np[0]
            _vector2.np[1] = tile1.center.np[1]
            tile, quadrant = self._add_full_quadrant(_vector2, tiles_2_display, max_depth, tile1)
            parent = tile.parent
            queue.append([parent.center, parent.level, parent])
            return tile, quadrant

        x += position.np[0]
        y += position.np[1]

        _vector2.np[0] = x
        _vector2.np[1] = y
        size = self.size / 2
        if -size <= x < size and -size <= y < size:
            tile, quadrant = self._add_full_quadrant(_vector2, tiles_2_display, max_depth, tile1)
            parent = tile.parent
            queue.append([parent.center, parent.level, parent])
            return tile, quadrant

        return None,None

    def _build_view(self, position: Vector2, tiles_2_display: list,max_depth: int):
        """

        :return:
        """
        neighbors = [
            [
                # north & west
                [-1, 0],
                [-1, -1],
                [0, -1]
            ],
            [
                # north & east
                [1, 0],
                [1, -1],
                [0, -1]
            ],
            [
                # south & west
                [-1, 0],
                [-1, 1],
                [0, 1]
            ],
            [
                # south & east
                [1, 0],
                [1, 1],
                [0, 1]
            ]
        ]
        queue = deque()
        queue.append([position, max_depth, None])

        while len(queue) > 0:
            e = queue.popleft()
            max_depth = e[1]

            # reached root of tree ?
            if max_depth == 0:
                return -1

            tile, quadrant = self._find_add_quadrant(e, 0, 0, tiles_2_display, queue)
            if tile is None:
                continue

            size = tile.size

            # add the neighbors quadrants
            # based on tile the player is on
            neighbor = neighbors[quadrant]
            for n in neighbor:
                tilex, q = self._find_add_quadrant(e, n[0]*size, n[1]*size, tiles_2_display, queue)


    def build_quadtre_indexes(self):
        """
        Build an array of openGL indexes to tbe used be tiles stitching
        :return:
        """
        self.quadtree_mesh_indexes = [None for i in range(16)]
        mesh = self.quadtree.mesh
        geometry = mesh.geometry
        index = geometry.index
        row = int(geometry.parameters['widthSegments'] * 2 * 3)

        for i in range(16):
            self.quadtree_mesh_indexes[i] = index.clone()

            array = self.quadtree_mesh_indexes[i].array

            if i & 1:
                for k in range(len(array) - row, len(array), 12):
                    array[k + 4] = array[k + 10]
                    array[k + 7] = array[k + 10]
                    array[k + 9] = array[k + 10]

            if i & 2:
                for k in range(0, row, 12):
                    array[k + 2] = array[k]
                    array[k + 5] = array[k]
                    array[k + 6] = array[k]

            if i & 4:
                for k in range(0, len(array), row * 2):
                    array[k + 1] = array[k]
                    array[k + 3] = array[k]
                    array[k + row] = array[k]

            if i & 8:
                for k in range(row - 6, len(array), row * 2):
                    array[k + 4] = array[k + row + 4]
                    array[k + row + 2] = array[k + row + 4]
                    array[k + row + 5] = array[k + row + 4]

    def _stich_neighbours(self):
        """
        build tiles neighbors
        and stich them
        """
        # build the tiles by size from smallest to biggest
        self.tiles_onscreen.sort(key=lambda x: x.size)

        # reset north, south, east, west neighbors
        for tile in self.tiles_onscreen:
            tile.east = tile.west = tile.north = tile.south = None

        # parse all tiles to find the neighbors
        north = THREE.Vector2()
        south = THREE.Vector2()
        east = THREE.Vector2()
        west = THREE.Vector2()
        l = len(self.tiles_onscreen)

        for i in range(l):
            tile = self.tiles_onscreen[i]
            if not tile.mesh.visible:
                continue

            if not hasattr(tile, 'debug'):
                tile.debug = None

            size = tile.size * 0.75
            level = tile.level - 1

            x = tile.center.x
            y = tile.center.y

            north.set(x, y - size)
            south.set(x, y + size)
            east.set(x + size, y)
            west.set(x - size, y)

            code = 0

            for j in range(i + 1, l):
                tile_j = self.tiles_onscreen[j]
                if not tile_j.mesh.visible:
                    continue

                if tile_j.level < level:
                    # there is no more than 1 level of difference between 2 tiles
                    continue

                if tile_j.is_point_inside(north):
                    if tile_j.level < tile.level:
                        code |= 1
                    tile.north = tile_j
                    tile_j.south = tile

                if tile_j.is_point_inside(south):
                    """
                    if hasattr(tile.mesh, 'debug'):
                        self.scene.remove(tile.mesh.debug)
                    t = tile_j.mesh.position.clone()
                    t.sub(tile.mesh.position)
                    l1 = t.length()
                    t.normalize()
                    tile.mesh.debug = THREE.ArrowHelper(t, tile.mesh.position,
                                                        l1, tile_j.mesh.material.color)
                    self.scene.add(tile.mesh.debug)
                    """
                    if tile_j.level < tile.level:
                        code |= 2
                    tile.south = tile_j
                    tile_j.north = tile

                if tile_j.is_point_inside(west):
                    if tile_j.level < tile.level:
                        code |= 4
                    tile.west = tile_j
                    tile_j.east = tile

                if tile_j.is_point_inside(east):
                    if tile_j.level < tile.level:
                        code |= 8
                    tile.east = tile_j
                    tile_j.west = tile

            tile.mesh.geometry.index = self.quadtree_mesh_indexes[code]

            tile.debug = code

    def _frustrum_culling(self, player, position, direction):
        """
        check the frustrum culling
        """
        def isInFront(a, b, c):
            return ((b.np[0] - a.np[0]) * (c.np[1] - a.np[1]) - (b.np[1] - a.np[1]) * (c.np[0] - a.np[0])) < 0

        def distance2(a, b, c, distance):
            a1 = abs((b.np[1] - a.np[1]) * c.np[0] - (b.np[0] - a.np[0]) * c.np[1] + b.np[0] * a.np[1] - b.np[1] * a.np[0])
            b1 = math.sqrt(math.pow(b.np[1] - a.np[1], 2) + math.pow(b.np[0] - a.np[0], 2))
            d = a1 / b1

            return d < distance

        # convert player position and line of view to heightmap coordinates
        hm = THREE.Vector2()
        self.screen2map(position, hm)

        # build the horizon line (90deg of direction)
        horizon = THREE.Vector2(-direction.y, direction.x)
        hm_behind = THREE.Vector2(hm.x + horizon.x, hm.y + horizon.y)

        # build a simple frustrum (45deg left and right)
        left = THREE.Vector2(direction.x + horizon.x + hm.x, direction.y + horizon.y + hm.y)
        right= THREE.Vector2(direction.x - horizon.x + hm.x, direction.y - horizon.y + hm.y)

        if Config["player"]["debug"]["frustrum"]:
            if hasattr(player, "frustrum"):
                player.scene.remove(player.frustrum)
                player.scene.remove(player.frustrum1)

            player.frustrum = THREE.ArrowHelper(THREE.Vector3(right.x - hm.x, right.y - hm.y, 0).normalize(), player.get_position(), 500, 0xff0000)
            self.scene.add(player.frustrum)
            player.frustrum1 = THREE.ArrowHelper(THREE.Vector3(left.x - hm.x, left.y - hm.y, 0).normalize(), player.get_position(), 500, 0x0000ff)
            self.scene.add(player.frustrum1)

        # check if the object is behind the player
        _vector2 = THREE.Vector2()
        hm_quad_radius = 0
        p = THREE.Vector2(position.x, position.y)
        for quad in self.tiles_onscreen:
            # if p.distanceTo(quad.center) < quad.visibility_radius:
            #    print("debug")
            self.screen2map(quad.center, _vector2)
            hm_quad_radius = quad.visibility_radius * self.size/self.onscreen
            # if isLeft(hm, hm_behind, hm_quad) and isLeft(hm, left, hm_quad) and not isLeft(hm, right, hm_quad):
            #    quad.mesh.visible = True
            if isInFront(hm, hm_behind, _vector2) :
                quad.mesh.visible = True
            elif distance2(hm, hm_behind, _vector2, hm_quad_radius):
                quad.mesh.visible = True
            else:
                quad.mesh.visible = False

            if quad.mesh.visible:
                if isInFront(hm, left, _vector2):
                    quad.mesh.visible = True
                elif distance2(hm, left, _vector2, hm_quad_radius):
                    quad.mesh.visible = True
                else:
                   quad.mesh.visible = False

            if quad.mesh.visible:
                if not isInFront(hm, right, _vector2):
                    quad.mesh.visible = True
                elif distance2(hm, right, _vector2, hm_quad_radius):
                    quad.mesh.visible = True
                else:
                    quad.mesh.visible = False

    def _build_tiles_onscreen(self, position):
        """

        :param position:
        :return:
        """
        self.quadtree.notTraversed()
        tiles_2_display = []

        position2D = THREE.Vector2(position.x, position.y)
        # self._check_quad_lod(position2D, self.quadtree, tiles_2_display)
        self._build_view(position2D, tiles_2_display, -1)

        # compare the list of tiles to display with the current list of tiles

        # remove tiles no more on screen
        for i in range(len(self.tiles_onscreen)-1, -1, -1):
            quad = self.tiles_onscreen[i]
            if quad not in tiles_2_display:
                if quad.traversed:
                    # hide tile => the sub-tiles need to be loaded first
                    loaded = 0
                    for sub in quad.sub:
                        if sub.mesh is not None:
                            loaded += 1
                    if loaded == 4:
                        del self.tiles_onscreen[i]
                        quad.hide()
                        # else keep the tile on screen until ALL sub tiles are loaded
                else:
                    del self.tiles_onscreen[i]
                    quad.hide()

        # add missing tiles
        to_load = []
        for quad in tiles_2_display:
            if quad not in self.tiles_onscreen:
                if quad.mesh and quad.parent.visible is False:
                    if quad.added is False:
                        quad.added = True
                        self.scene.add(quad.mesh)

                    self.tiles_onscreen.append(quad)
                    quad.display()
                else:
                    to_load.append(quad)

        # sort the loading priority by distance
        def _sort(quad):
            return quad.center.distanceToSquared(position2D)

        to_load.sort(key = _sort)

        # load the tile in background for next frame
        for quad in to_load:
            quad.load()

    def draw(self, player):
        """
        @description Update the terrain mesh based on the pgiven position
        @param {type} position
        @returns {undefined}
        """
        position = player.vcamera.position
        direction = player.direction

        self._build_tiles_onscreen(position)
        self._frustrum_culling(player, position, direction)
        self._stich_neighbours()

    def update_light(self, time):
        """
        @description: update the terrain
        @param {time} time current time
        """

        """
        # shift the water texture
        self.water_shift += 0.01
        if self.water_shift >= 1:
            self.water_shift = 0
        self.material1.uniforms.water_shift.value = this.water_shift
        """

        # update light position
        if self.material is not None:
            self.material.uniforms.light.value.copy(self.light.position)

    def colisionObjects(self, footprint, debug=None):
        """
        Check if there are objects on the terrain colliding with the given footprint
        :param footprint:
        :return:
        """
        p1 = THREE.Vector2(footprint.center.x, footprint.center.y)
        colision = []
        quad = self.quadtree.around(p1)
        objects = quad.objects

        for object in objects:
            for mfootprint in object.footprints:
                if mfootprint.isNear(footprint, debug):
                    colision.append(object)
                    break

        return colision

    def build_mesh_scenery(self):
        """
        Create a mesh for each object on the terrain
        Insert the mesh in the proper Quad based on it's footprint
        :return:
        """
        root = self.quadtree

        nb = len(self.scenery)
        i = 0
        for object in self.scenery:
            progress(i, nb, "Prepare scenery")
            root.insert_object(object, 0)
            i += 1

        progress(0, 0)

        # root.scenery_instance()

        progress(0, 0)
