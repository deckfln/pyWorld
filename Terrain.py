import math
import pickle
import numpy as np
from collections import deque

import THREE

from roads import *
from prng import *
from progress import *
from quadtree import *
from TextureMap import *
from VectorMap import *
from IndexMap import *

myrandom = Random(5454334)


TILE_grass_png = 0
TILE_grass1_png = 1
TILE_grass2_png = 2
TILE_forest_png = 3
TILE_forest1_png = 4
TILE_forest2_png = 5
TILE_stone_path_png = 6
TILE_paving_png = 7
TILE_blend_png = 0
TILE_water_png = 1
TILE_riverbed_png = 2
TILE_rock_png = 3
TILE_dirt_png = 4
TILE_dirt1_png = 5

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
        self.ratio_screen_2_map = self.onscreen / self.size
        self.half = self.onscreen/2

        self.tiles_onscreen = []

        # THREE objects
        self.scene = None
        self.material = None
        self.material_far = None
        self.material_very_far = None
        self.textures = []
        self.light = None
        self.terrain_textures = None
        self.blendmap_texture = None

        self.quadtree_mesh_indexes = None       # index backup for tiles
        self.quadtree_current_tile = None       # cache the current tile the player is sitting on

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

    def shaders(self, sun):
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

            self.terrain_textures = loader.load("img/terrain_d.png")
            normalMap = loader.load("img/terrain_n.png")

            self.blendmap.texture = loader.load("img/blendmap.png")

            floader = THREE.FileLoader()
            uniforms = {
                'blendmap_texture': {'type': "t", 'value': self.blendmap.texture},
                'terrain_textures': {'type': "t", 'value': self.terrain_textures},
                'light': {'type': "v3", 'value': sun.light.position},
                'water_shift': {'type': "f", 'value': 0},
                'indexmap': {'type': "t", 'value': self.indexmap.texture},
                'indexmap_size': {'type': "f", 'value': self.indexmap.size},
                'indexmap_repeat': {'type': "f", 'value': self.indexmap.repeat},
                'blendmap_repeat': {'type': "f", 'value': 64},
                'ambientCoeff': {'type': "float", 'value': sun.ambientCoeff},
                'sunColor': {'type': "v3", 'value': sun.color},
                'normalMap': {'type': "t", 'value': normalMap},
            }

            if Config["shadow"]["enabled"]:
                uniforms['directionalShadowMap'] = {'type': 'v', 'value': sun.light.shadow.map.texture}
                uniforms['directionalShadowMatrix'] = {'type': 'm4', 'value': sun.light.shadow.matrix}
                uniforms['directionalShadowSize'] = {'type': 'v2', 'value': sun.light.shadow.mapSize}

            self.material = THREE.ShaderMaterial( {
                'uniforms': uniforms,
                'vertexShader': floader.load('shaders/vertex.glsl'),
                'fragmentShader': floader.load('shaders/fragment.glsl'),
                'wireframe': Config['terrain']['debug']['wireframe']
            })

            terrain_far = loader.load("img/terrain_far_d.png")

            uniforms_far = {
                'blendmap_texture': {'type': "t", 'value': self.blendmap.texture},
                'terrain_textures': {'type': "t", 'value': terrain_far},
                'light': {'type': "v3", 'value': sun.light.position},
                'water_shift': {'type': "f", 'value': 0},
                'indexmap': {'type': "t", 'value': self.indexmap.texture},
                'indexmap_size': {'type': "f", 'value': self.indexmap.size},
                'indexmap_repeat': {'type': "f", 'value': self.indexmap.repeat},
                'blendmap_repeat': {'type': "f", 'value': 64},
                'ambientCoeff': {'type': "float", 'value': sun.ambientCoeff},
                'sunColor': {'type': "v3", 'value': sun.color},
                'normalMap': {'type': "t", 'value': normalMap}
            }
            self.material_far = THREE.ShaderMaterial( {
                'uniforms': uniforms_far,
                'vertexShader': floader.load('shaders/vertex.glsl'),
                'fragmentShader': floader.load('shaders/fragment.glsl'),
                'wireframe': Config['terrain']['debug']['wireframe']
            })

            terrain_very_far = loader.load("img/terrain_very_far.png")

            uniforms_very_far = {
                'blendmap_texture': {'type': "t", 'value': self.blendmap.texture},
                'terrain_textures': {'type': "t", 'value': terrain_very_far},
                'light': {'type': "v3", 'value': sun.light.position},
                'water_shift': {'type': "f", 'value': 0},
                'indexmap': {'type': "t", 'value': self.indexmap.texture},
                'indexmap_size': {'type': "f", 'value': self.indexmap.size},
                'indexmap_repeat': {'type': "f", 'value': self.indexmap.repeat},
                'blendmap_repeat': {'type': "f", 'value': 64},
                'ambientCoeff': {'type': "float", 'value': sun.ambientCoeff},
                'sunColor': {'type': "v3", 'value': sun.color},
                'normalMap': {'type': "t", 'value': normalMap}
            }
            self.material_very_far = THREE.ShaderMaterial( {
                'uniforms': uniforms_very_far,
                'vertexShader': floader.load('shaders/vertex.glsl'),
                'fragmentShader': floader.load('shaders/fragment.glsl'),
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
        self.light = sun.light

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
            Quadtree.material_far = self.material_far
            Quadtree.material_very_far = self.material_very_far

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

        ratio = self.ratio_screen_2_map
        half = self.half

        target.np[0] = position.np[0] * ratio - half
        target.np[1] = position.np[1] * ratio - half

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

        ratio = self.ratio_screen_2_map
        half = self.half

        target.np[0] = x * ratio - half
        target.np[1] = y * ratio - half

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
        target.np[0] = (position.np[0] + half) * ratio
        target.np[1] = (position.np[1] + half) * ratio
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
        sub = parent.sub
        for i in range(4):
            quad = sub[i]
            if quad == tile:
                quadrant = i
            if not quad.traversed:
                tiles_2_display.append(quad)

        # register stitching on borders
        if not sub[0].traversed:
            sub[0].east = sub[0].south = False
            sub[0].west = sub[0].north = True

        if not sub[1].traversed:
            sub[1].west = sub[1].south = False
            sub[1].east = sub[1].north = True

        if not sub[2].traversed:
            sub[2].east = sub[2].north = False
            sub[2].west = sub[2].south = True

        if not sub[3].traversed:
            sub[3].west = sub[3].north = False
            sub[3].east = sub[3].south = True

        for quad in sub:
            if not quad.traversed:
                quad.traversed = True

        parent.traversed = True

        return parent, quadrant

    def _find_add_quadrant(self, e, x, y, tiles_2_display, queue):
        position = e[0]
        max_depth = e[1]
        tile1 = e[2]

        if x == 0 and y == 0 and tile1 is not None:
            _vector2.np[0] = tile1.center.np[0]
            _vector2.np[1] = tile1.center.np[1]
            parent, quadrant = self._add_full_quadrant(_vector2, tiles_2_display, max_depth, tile1)
            queue.append([parent.center, parent.level, parent])
            return parent, quadrant

        x += position.np[0]
        y += position.np[1]

        _vector2.np[0] = x
        _vector2.np[1] = y
        size = self.size / 2
        if -size <= x < size and -size <= y < size:
            parent, quadrant = self._add_full_quadrant(_vector2, tiles_2_display, max_depth, tile1)
            queue.append([parent.center, parent.level, parent])
            return parent, quadrant

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

        # if the player is on the same tile as last frame
        tile = self.quadtree.around(position, max_depth)
        if self.quadtree_current_tile == tile:
            return False

        self.quadtree_current_tile = tile

        queue = deque()
        queue.append([position, max_depth, None])

        while len(queue) > 0:
            e = queue.popleft()
            max_depth = e[1]

            # reached root of tree ?
            if max_depth == 0:
                return -1

            """
            quadrant
            +-----+-----+
            !  0  !  1  !
            +-----+-----+
            !  2  !  3  !
            +-----+-----+           
            """
            parent, quadrant = self._find_add_quadrant(e, 0, 0, tiles_2_display, queue)
            if parent is None:
                continue

            size = parent.sub[0].size

            # add the neighbors quadrants
            # based on tile the player is on
            if quadrant == 0:
                """
                +-----+-----+
                ! n_w !north!
                +-----+-----+
                ! west!tile !
                +-----+-----+
                """
                west, q = self._find_add_quadrant(e, -size, 0, tiles_2_display, queue)
                north_west, q = self._find_add_quadrant(e, -size, -size, tiles_2_display, queue)
                north, q = self._find_add_quadrant(e, 0, -size, tiles_2_display, queue)
                # stitching ?
                if west is not None:
                    west.sub[1].east = west.sub[3].east = False
                    parent.sub[0].west = parent.sub[2].west = False
                if north is not None:
                    north.sub[2].south = north.sub[3].south = False
                    parent.sub[0].north = parent.sub[1].north = False
                if north_west is not None:
                    north.sub[0].west = north.sub[2].west = False
                    north_west.sub[1].east = north_west.sub[3].east = False
                    west.sub[0].north = west.sub[1].north = False
                    north_west.sub[2].south = north_west.sub[3].south = False

            elif quadrant == 1:
                """
                +-----+-----+
                !north! n_e !
                +-----+-----+
                !tile !east !
                +-----+-----+
                """
                east, q = self._find_add_quadrant(e, size, 0, tiles_2_display, queue)
                north_east, q = self._find_add_quadrant(e, size, -size, tiles_2_display, queue)
                north, q = self._find_add_quadrant(e, 0, -size, tiles_2_display, queue)
                # stitching ?
                if east is not None:
                    east.sub[0].west = east.sub[2].west = False
                    parent.sub[1].east = parent.sub[3].east = False
                if north is not None:
                    north.sub[2].south = north.sub[3].south = False
                    parent.sub[0].north = parent.sub[1].north = False
                if north_east is not None:
                    east.sub[0].north = east.sub[1].north = False
                    north_east.sub[2].south = north_east.sub[3].south = False
                    north.sub[1].east = north.sub[3].east = False
                    north_east.sub[0].west = north_east.sub[2].west = False

            elif quadrant == 2:
                """
                +-----+-----+
                !west !tile !
                +-----+-----+
                ! s_w !south!
                +-----+-----+
                """
                west, q = self._find_add_quadrant(e, -size, 0, tiles_2_display, queue)
                south_west, q = self._find_add_quadrant(e, -size, size, tiles_2_display, queue)
                south, q = self._find_add_quadrant(e, 0, size, tiles_2_display, queue)
                # stitching ?
                if west is not None:
                    west.sub[1].east = west.sub[3].east = False
                    parent.sub[0].west = parent.sub[2].west = False
                if south is not None:
                    south.sub[0].north = south.sub[1].north = False
                    parent.sub[2].south = parent.sub[3].south = False
                if south_west is not None:
                    west.sub[2].south = west.sub[3].south = False
                    south_west.sub[0].north = south_west.sub[1].north = False
                    south.sub[0].west = south.sub[3].west = False
                    south_west.sub[1].east = south_west.sub[3].east = False
            else:
                """
                +-----+-----+
                !tile !east !
                +-----+-----+
                !south! s_e !
                +-----+-----+
                """
                east, q = self._find_add_quadrant(e, size, 0, tiles_2_display, queue)
                south_east, q = self._find_add_quadrant(e, size, size, tiles_2_display, queue)
                south, q = self._find_add_quadrant(e, 0, size, tiles_2_display, queue)
                # stitching ?
                if east is not None:
                    east.sub[0].west = east.sub[2].west = False
                    parent.sub[1].east = parent.sub[3].east = False
                if south is not None:
                    south.sub[0].north = south.sub[1].north = False
                    parent.sub[2].south = parent.sub[3].south = False
                if south_east is not None:
                    east.sub[2].south = east.sub[3].south = False
                    south_east.sub[0].north = south_east.sub[1].north = False
                    south.sub[1].east = south.sub[3].east = False
                    south_east.sub[0].west = south_east.sub[2].west = False

        return True

    def _stich_neighbours(self):
        """
        check for each tile if a border needs stitching
        """
        # build the tiles by size from smallest to biggest
        self.tiles_onscreen.sort(key=lambda x: x.size)

        for tile in self.tiles_onscreen:
            if not tile.mesh.visible:
                continue

            if not hasattr(tile, 'debug'):
                tile.debug = None

            code = 0

            if tile.north:
                code |= 1

            if tile.south:
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
                code |= 2

            if tile.west:
                code |= 4

            if tile.east:
                code |= 8

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
        if not self._build_view(position2D, tiles_2_display, -1):
            # there is no change
            return

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

