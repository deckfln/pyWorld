"""

"""

from build.PerlinSimplexNoise import *
from build.roads import *
from build.Forest import *
from build.city import *
from Terrain import *
import time
from DataMap import *

mango_dir = os.path.dirname(__file__) + '/../cython/'
sys.path.append(mango_dir)

from cHeightmapNormals import *
cython = True


class TerrainBuilder(Terrain):
    def __init__(self, size, height, onscreen):
        super().__init__(size, height, onscreen)
        self.roads = None
        self.datamaps = None

    def perlin_generate(self):
        """
        Generate a terrain heightmap using perlin
        :return:
        """
        global myrandom
        perlin = SimplexNoise(myrandom)
        total = self.size * self.size
        count = 0

        for i in range(self.size):
            for j in range(self.size):
                noise = 0
                s = 512
                h1 = self.height * 2

                for iteration in range(4):
                    noise += perlin.noise(i / s, j / s) * h1
                    s /= 2
                    h1 /= 2

                self.set(i, j, noise)
                count += 1
            progress(count, total, "Perlin Generate")
        progress(0, 0)

    def _pbuild_normalmap(self):
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

                self.map2screenXY(x, y, mA)
                self.map2screenXY(x+1, y, mB)
                self.map2screenXY(x+1, y+1, mC)

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

    def build_normalmap(self):
        if cython:
            cbuild_normalmap(self, self.heightmap.map, self.heightmap.size, self.normalMap.map, self.normalMap.size)
        else:
            self._pbuild_normalmap()

        """
        np = self.normalMap.map.copy()
        t  = self.normalMap.map.size
        normals = self.normalMap.map
        for i in range(t):
            if nm[i] != normals[i]:
                raise RuntimeError("cyhton & python disagreee")
        """

    def _build_lod_mesh(self, quad, level, lx, ly, size, material, count):
        """

        :param center:
        :param size:
        :return:
        """
        quad_width = 16
        progress(count, self.nb_tiles, "Build terrain mesh")
        geometry = THREE.PlaneBufferGeometry(size, size, quad_width, quad_width)

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
        ratio_screenmap_2_hm = self.onscreen / self.size

        map_size = self.size - 1
        half_quad_size = int((self.onscreen / (quad_width * 2**level)) / 2)

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
                        self.screen2map(screen, hm)
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
                self.screen2map(screen, hm)
            else:
                screen.x = screen_x
                screen.y = screen_y
                self.screen2map(screen, hm)
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
        quad.lod_radius = self.radiuses[level]
        quad.visibility_radius = math.sqrt(2)*size/2
        quad.size = size
        quad.level = level
        quad.name = "%d-%d-%d" % (level, lx, ly)

        # sub-divide
        halfSize = size / 2
        quadSize = size / 4

        if level < self.nb_levels - 1:
            quad.sub[0] = Quadtree( -1, -1, -1, quad)     # nw
            quad.sub[1] = Quadtree( -1, -1, -1, quad)     # ne
            quad.sub[2] = Quadtree( -1, -1, -1, quad)     # sw
            quad.sub[3] = Quadtree( -1, -1, -1, quad)     # se

            count = self._build_lod_mesh(quad.sub[0], level + 1, lx - quadSize, ly - quadSize, halfSize, material, count + 1)
            count = self._build_lod_mesh(quad.sub[1], level + 1, lx + quadSize, ly - quadSize, halfSize, material, count + 1)
            count = self._build_lod_mesh(quad.sub[2], level + 1, lx - quadSize, ly + quadSize, halfSize, material, count + 1)
            count = self._build_lod_mesh(quad.sub[3], level + 1, lx + quadSize, ly + quadSize, halfSize, material, count + 1)

        return count

    def build_mesh(self):
        """
        Build the LOD meshes and the Quad Tree
        :return:
        """
        self._build_lod_mesh(self.quadtree, 0, 0, 0, self.size, None, 1)
        progress(0, 0)

    def _build_heightmap_lod(self, source_datamap):
        """
        Build a half datamap from the source datamap
        :param source_datamap:
        :return:
        """
        size = source_datamap.size
        datamap = DataMap(int(size / 2))

        vecs = [None, None, None, None]
        vec4 = THREE.Vector4()

        for y in range(0, size, 2):
            for x in range(0, size, 2):
                vecs[0] = source_datamap.getXY(x, y)
                vecs[1] = source_datamap.getXY(x + 1, y)
                vecs[2] = source_datamap.getXY(x, y + 1)
                vecs[3] = source_datamap.getXY(x + 1, y + 1)

                w = -9999
                j = -1
                for i in range(4):
                    if vecs[i].w > w:
                        w = vecs[i].w
                        j = i

                px = x / 2
                py = y / 2
                vec4.copy(vecs[j])
                datamap.setXY(px, py, (vec4.x, vec4.y, vec4.z, vec4.w))

        return datamap

    def build_heightmap_lod(self):
        """
        Build multiple levels of DataMaps from the heightmap and the normalmap
        :return:
        """
        size = self.heightmap.size
        datamaps = [None for i in range(self.nb_levels)]

        # build the root datamap : full scale
        progress(0, self.nb_levels, "Build DataMap lods")
        datamaps[self.nb_levels - 1] = DataMap(size)
        normal = THREE.Vector3()

        for y in range(size):
            for x in range(size):
                w = self.heightmap.get(x, y)
                self.normalMap.get(x, y, normal)

                datamaps[self.nb_levels - 1].setXY(x, y, (normal.x, normal.y, normal.z, w))

        # and now build smaller scales datamaps
        for i in range(self.nb_levels - 2, -1, -1):
            progress(i, self.nb_levels, "Build DataMap lods")
            datamaps[i] = self._build_heightmap_lod(datamaps[i + 1])

        progress(6, 6, "Build DataMap lods")
        progress(0, 0)

        self.datamaps = datamaps

    def _build_tiled_datamap(self, quad, level, lx, ly, hmx, hmy, size, count):
        """
        extract a tile from the provided DataMap
        :param center:
        :param size:
        :return:
        """
        quad_width = 16
        progress(count, self.nb_tiles, "Build tiled datamap")

        source_datamap = self.datamaps[level]
        datamap = DataMap(quad_width)
        screen = THREE.Vector2()
        hm = THREE.Vector2()

        ratio_screenmap_2_hm = self.onscreen / self.size

        datamap_size = source_datamap.size
        half_quad_size = int((self.onscreen / (quad_width * 2**level)) / 2)

        pmin = size/2
        v4 = THREE.Vector4()
        v3 = THREE.Vector3()
        scale = 2**(self.nb_levels - level - 1)

        x = hmx * quad_width
        y = hmy * quad_width
        for y1 in range(0, quad_width):
            for x1 in range(0, quad_width):

                # on the borders of the quad do not pick Z = max (from the lod heightmaps)
                # but the value from the source heightmap
                # this limits cracks between the tiles
                x2 = y2 = -1
                if x1 == 0:
                    x2 = (x + x1) * scale
                    if y1 == quad_width - 1:
                        y2 = (y + y1 + 1) * scale - 1
                    else:
                        y2 = (y + y1) * scale
                elif x1 == quad_width-1:
                    x2 = (x + x1 + 1) * scale - 1
                    if y1 == quad_width - 1:
                        y2 = (y + y1 + 1) * scale - 1
                    else:
                        y2 = (y + y1) * scale

                if y1 == 0:
                    y2 = (y + y1) * scale
                    if x1 == quad_width - 1:
                        x2 = (x + x1 + 1) * scale - 1
                    else:
                        x2 = (x + x1) * scale
                elif y1 == quad_width - 1:
                    y2 = (y + y1 + 1) * scale - 1
                    if x1 == quad_width - 1:
                        x2 = (x + x1 + 1) * scale - 1
                    else:
                        x2 = (x + x1) * scale

                if x2 < 0 and y2 < 0:
                    vec4 = source_datamap.getXY(x + x1, y + y1)
                    datamap.setXY(x1, y1, (vec4.x, vec4.y, vec4.z, vec4.w))
                else:
                    z = self.heightmap.get(x2, y2)
                    self.normalMap.get(x2, y2, v3)
                    datamap.setXY(x1, y1, (v3.np[0], v3.np[1], v3.np[2], z))

        quad.datamap = datamap
        quad.center = THREE.Vector2(lx, ly)
        quad.lod_radius = self.radiuses[level]
        quad.visibility_radius = math.sqrt(2)*size/2
        quad.size = size
        quad.level = level
        quad.name = "%d-%d-%d" % (level, lx, ly)

        # sub-divide
        halfSize = int(size / 2)
        quadSize = size / 4

        if level < self.nb_levels - 1:
            quad.sub[0] = Quadtree(-1, -1, -1, quad)     # nw
            quad.sub[1] = Quadtree(-1, -1, -1, quad)     # ne
            quad.sub[2] = Quadtree(-1, -1, -1, quad)     # sw
            quad.sub[3] = Quadtree(-1, -1, -1, quad)     # se

            count = self._build_tiled_datamap(quad.sub[0],
                                              level + 1,
                                              lx - quadSize, ly - quadSize,
                                              hmx * 2, hmy * 2,
                                              halfSize, count + 1)
            count = self._build_tiled_datamap(quad.sub[1],
                                              level + 1,
                                              lx + quadSize, ly - quadSize,
                                              hmx * 2 + 1, hmy * 2,
                                              halfSize, count + 1)
            count = self._build_tiled_datamap(quad.sub[2],
                                              level + 1,
                                              lx - quadSize, ly + quadSize,
                                              hmx * 2, hmy * 2 + 1,
                                              halfSize, count + 1)
            count = self._build_tiled_datamap(quad.sub[3],
                                              level + 1,
                                              lx + quadSize, ly + quadSize,
                                              hmx * 2 + 1, hmy * 2 + 1,
                                              halfSize, count + 1)

        return count

    def build_tiled_datamaps(self):
        """
        Build the LOD meshes and the Quad Tree
        :return:
        """
        self._build_tiled_datamap(self.quadtree, 0, 0, 0, 0, 0, self.size, 1)
        progress(0, 0)

    def _build_tile_map(self, quad, level, lx, ly, size, material, count):
        """

        :param center:
        :param size:
        :return:
        """
        quad_width = 16
        progress(count, self.nb_tiles, "Build tile map")
        geometry = THREE.PlaneBufferGeometry(size, size, quad_width-1, quad_width-1)
        positions = geometry.attributes.position.array

        datamap = DataMap(quad_width)

        screen = THREE.Vector2()
        normal = THREE.Vector3()
        hm = THREE.Vector2()

        heightmap = self.heightmap
        normalMap = self.normalMap
        ratio_screenmap_2_hm = self.onscreen / self.size

        map_size = self.size - 1
        half_quad_size = int((self.onscreen / (quad_width * 2**level)) / 2)
        halfSize = size / 2
        steps = size / (quad_width - 1)
        pmin = size/2

        p = 0
        #sy = - size / 2
        for y in range(quad_width):
            #sx = - size / 2
            for x in range(quad_width):
                sx = positions[p]
                sy = positions[p + 1]

                screen_x = sx + lx
                screen_y = sy + ly

                # leave the borders alone ! they are needed for continuity between 2 tiles
                if half_quad_size >= 1 and -pmin < sx < pmin and -pmin < sy < pmin:
                    # find the most visible point in the sub-quad
                    max_x = -1
                    max_y = -1
                    max_z = -99999999

                    screen.x = screen_x
                    screen.y = screen_y
                    self.screen2map(screen, hm)
                    max_z = heightmap.bilinear(hm.x, hm.y)
                    max_x = hm.x
                    max_y = hm.y
                    """
                    py = screen_y - half_quad_size
                    while py < screen_y + half_quad_size:
                        px = screen_x - half_quad_size
                        while px < screen_x + half_quad_size:
                            screen.x = px
                            screen.y = py
                            self.screen2map(screen, hm)
                            z = heightmap.bilinear(hm.x, hm.y)
                            if z > max_z:
                                max_z = z
                                max_x = hm.x
                                max_y = hm.y
                            px += ratio_screenmap_2_hm
                        py += ratio_screenmap_2_hm
                    """
                else:
                    screen.x = screen_x
                    screen.y = screen_y
                    self.screen2map(screen, hm)
                    max_z = heightmap.bilinear(hm.x, hm.y)
                    max_x = hm.x
                    max_y = hm.y

                if max_x > 511 or max_y > 511:
                    raise Exception("bad value")
                normalMap.bilinear(max_x, max_y, normal)

                datamap.setXY(x, quad_width - 1 - y, normal, max_z)

                p += 3
                #sx += steps
            #sy += steps

        quad.datamap = datamap
        quad.center = THREE.Vector2(lx, ly)
        quad.lod_radius = self.radiuses[level]
        quad.visibility_radius = math.sqrt(2)*size/2
        quad.size = size
        quad.level = level
        quad.name = "%d-%d-%d" % (level, lx, ly)

        # sub-divide
        quadSize = size / 4

        if level < self.nb_levels - 1:
            quad.sub[0] = Quadtree( -1, -1, -1, quad)     # nw
            quad.sub[1] = Quadtree( -1, -1, -1, quad)     # ne
            quad.sub[2] = Quadtree( -1, -1, -1, quad)     # sw
            quad.sub[3] = Quadtree( -1, -1, -1, quad)     # se

            count = self._build_tile_map(quad.sub[0], level + 1, lx - quadSize, ly - quadSize, halfSize, material, count + 1)
            count = self._build_tile_map(quad.sub[1], level + 1, lx + quadSize, ly - quadSize, halfSize, material, count + 1)
            count = self._build_tile_map(quad.sub[2], level + 1, lx - quadSize, ly + quadSize, halfSize, material, count + 1)
            count = self._build_tile_map(quad.sub[3], level + 1, lx + quadSize, ly + quadSize, halfSize, material, count + 1)

        return count

    def build_tiles_datamaps(self):
        """
        Build the LOD meshes and the Quad Tree
        :return:
        """
        self._build_tile_map(self.quadtree, 0, 0, 0, self.size, None, 1)
        progress(0, 0)

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

    def build_roads(self):
        """
        Build 2 roads on the terrain
        :return:
        """
        self.roads = Roads(self)

    def city(self):
        city_create(self)

    def forest(self):
        trees = []
        forest_create(trees, self)
        self.scenery.extend(trees)

    def buildIndexmap(self):
        self.indexmap.build()

    def dump(self):
        """
        Save all data of the terrain
        :return:
        """
        with open(Config['folder']+"/bin/heightmap.pkl", "wb") as f:
            pickle.dump(self.heightmap, f)

        with open(Config['folder']+"/bin/normalmap.pkl", "wb") as f:
            pickle.dump(self.normalMap, f)

        # dump the meshes
        self.quadtree.dump_datamap()

        # pack the quad into an array
        # this will DELETE the meshes so they are NOT in the pickle
        worldmap = []
        self.quadtree.dump(worldmap)
        with open(Config['folder']+"/bin/worldmap.pkl", "wb") as f:
            pickle.dump(worldmap, f)

        self.indexmap.generate(Config['folder']+"/img/indexmap.png")
        self.blendmap.generate(Config['folder']+"/img/blendmap.png")
