"""

"""
from Config import *

from THREE.textures.DataTextureArray import *
from THREE.scenes.Scene import *
from DataMaps import *
from quadtree import *


class Tiles:
    MAXIMULM_TILES = 1024

    def __init__(self):
        # access to the file stroing all datamaps
        self.datamaps = DataMaps()

        # GPU buffer for the datamps
        self.DataMapArray = DataTextureArray([None for i in range(self.MAXIMULM_TILES)], 9, 9, 1024)

        # mapping gpu texturearray to tiles
        self.on_gpu_by_index = [None for i in range(self.MAXIMULM_TILES)]
        self.on_gpu_by_tile = {}
        self.last = 0
        self.first_available = -1

        # visible tiles
        self.visible = {}

        self.needsUpdate = True

        self.plane = None
        self.stiched_planes = None

    def init_mesh(self, terrain):
        """
        init the material
        """
        material = THREE.RawShaderMaterial({
            'uniforms': {
                'datamaps': {'type': "t", 'value': self.DataMapArray},
                'light': {'type': "v3", 'value': terrain.material.uniforms.light.value},
                'blendmap_texture': {'type': "t", 'value': terrain.material.uniforms.blendmap_texture.value},
                'terrain_textures': {'type': "t", 'value': terrain.material.uniforms.terrain_textures.value},
                'indexmap': {'type': "t", 'value': terrain.material.uniforms.indexmap.value},
                'indexmap_size': {'type': "f", 'value': terrain.material.uniforms.indexmap_size.value},
                'indexmap_repeat': {'type': "f", 'value': terrain.material.uniforms.indexmap_repeat.value},
                'blendmap_repeat': {'type': "f", 'value': 64},
                'ambientCoeff': {'type': "float", 'value': terrain.material.uniforms.ambientCoeff.value},
                'sunColor': {'type': "v3", 'value': terrain.material.uniforms.sunColor.value},
            },
            'vertexShader': terrain.material.vertexShader,
            'fragmentShader': terrain.material.fragmentShader,
            'wireframe': Config['terrain']['debug']['wireframe']
        })

        #TODO: use a the same geometry for each block because the boundinSphere is uniq to each tile
        #TODO: but find how to have different boundingSpheres for the same geometry
        quad_width = self.datamaps.width - 1

        geometry = THREE.PlaneBufferGeometry(1, 1, quad_width, quad_width)
        instancedBufferGeometry = THREE.InstancedBufferGeometry().copy(geometry)

        center = THREE.InstancedBufferAttribute(Float32Array(self.MAXIMULM_TILES * 2), 2, 1).setDynamic(True)
        instancedBufferGeometry.addAttribute('center', center)    # per instance center

        scale = THREE.InstancedBufferAttribute(Float32Array(self.MAXIMULM_TILES), 1, 1).setDynamic(True)
        instancedBufferGeometry.addAttribute('scale', scale)    # per instance center

        datamap_index = THREE.InstancedBufferAttribute(Uint16Array(self.MAXIMULM_TILES), 1, 1).setDynamic(True)
        instancedBufferGeometry.addAttribute('datamapIndex', datamap_index)   # per instance datamap from the texturearray

        centerVuv = THREE.InstancedBufferAttribute(Float32Array(self.MAXIMULM_TILES * 2), 2, 1).setDynamic(True)
        instancedBufferGeometry.addAttribute('centerVuv', centerVuv)    # per instance center

        level = THREE.InstancedBufferAttribute(Uint16Array(self.MAXIMULM_TILES), 1, 1).setDynamic(True)
        instancedBufferGeometry.addAttribute('level', level)    # per instance level

        plane = THREE.Mesh(instancedBufferGeometry, material)
        plane.visible = False
        plane.castShadow = True
        plane.receiveShadow = True
        plane.frustumCulled = False
        self.plane = plane

        # build stiched indexes
        self._build_stiched_planes(plane)

    def add2scene(self, scene: Scene):
        """
        Add all the shallow clones of the plane to the scene
        All clones share the same attributes, the difference being the DrawRange for the indices
        :param scene:
        :return:
        """
        for p in self.stiched_planes:
            scene.add(p)

    def load(self, tile: Quadtree):
        # ensure the tile is not already on the GPU
        if tile.name in self.on_gpu_by_tile:
            return

        self.datamaps.load(tile)

        # find a slot
        if self.last < len(self.on_gpu_by_index):
            p = self.last
            self.last += 1
        else:
            p = self.first_available
            if p < 0:
                # free memory
                p = self._free_slots()

            # get the next available slot
            self.first_available = self.on_gpu_by_index[p]

        self.on_gpu_by_index[p] = tile
        self.on_gpu_by_tile[tile.name] = p

        self.DataMapArray.updateData(p, tile.datamap)

    def _free_slots(self):
        oldest = 9999999999
        index = -1
        for i in range(len(self.on_gpu_by_index)):
            last_on_screen = self.on_gpu_by_index[i].last_on_screen
            if last_on_screen < oldest:
                index = i
                oldest = last_on_screen

        oldest = self.on_gpu_by_index[index]
        if self.first_available >= 0:
            self.on_gpu_by_index[self.first_available] = index
            del self.on_gpu_by_tile[oldest]
        else:
            self.first_available = index
            self.on_gpu_by_index[self.first_available] = -1
            del self.on_gpu_by_tile[oldest.name]

        oldest.unload_datamap()

        return index

    def display(self, tile: Quadtree):
        tile.display()
        if tile in self.visible.keys():
            return

        self.visible[tile] = self.on_gpu_by_tile[tile.name]
        self.needsUpdate = True

    def hide(self, tile: Quadtree):
        tile.hide()
        if tile in self.visible.keys():
            del self.visible[tile]
            self.needsUpdate = True

    def update_instances(self):
        if not self.needsUpdate:
            return

        v2 = Vector2()

        instances = [[] for i in range(16)]
        for i in range(16):
            self.stiched_planes[i].visible = False

        for tile in self.visible.keys():
            instances[tile.stitch_code].append(tile)

        for i in range(16):
            if len(instances[i]) == 0:
                continue

            p = self.stiched_planes[i]
            p.visible = True

            nb_instances = 0
            attributes = p.geometry.attributes
            center = attributes.center.array
            scale = attributes.scale.array
            centerVuv = attributes.centerVuv.array
            level = attributes.level.array
            datamap_index = attributes.datamapIndex.array

            for tile in instances[i]:
                v2.copy(tile.center)
                total_size = tile.size * 2 ** tile.level
                v2.x += total_size / 2
                v2.y += total_size / 2
                v2.divideScalar(total_size)

                tile.center.toArray(center, nb_instances*2)
                scale[nb_instances] = tile.onscreen

                v2.toArray(centerVuv, nb_instances*2)
                level[nb_instances] = 2**tile.level
                datamap_index[nb_instances] = self.visible[tile]

                nb_instances += 1

            p.geometry.maxInstancedCount = nb_instances
            attributes.center.needsUpdate = True
            attributes.scale.needsUpdate = True
            attributes.centerVuv.needsUpdate = True
            attributes.level.needsUpdate = True
            attributes.datamapIndex.needsUpdate = True

        self.needsUpdate = False

    def _build_stiched_planes(self, mesh):
        """
        Build an array of openGL indexes to be used by tiles stitching
        :return:
        """
        self.stiched_planes = []

        geometry = mesh.geometry
        index = geometry.index
        row = int(geometry.parameters['widthSegments'] * 2 * 3)
        indices = []

        for i in range(16):
            array = np.copy(index.array)

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

            for i in array:
                indices.append(i)

        self.plane.geometry.index = Uint16BufferAttribute(indices, 1)

        for i in range(16):
            p = self.plane.clone()
            p.geometry = self.plane.geometry.clone()   # shallow cloning, keep attributes
            self.stiched_planes.append(p)

            p.geometry.drawRange.start = index.count * i
            p.geometry.drawRange.count = index.count
