"""
3D Asset
"""
import os

from THREE.loaders.OBJLoader2 import *
from THREE.loaders.MTLLoader import *
from pyOpenGL.pyCache import *
from Config import *

loader = THREE.FileLoader()

uniforms = {
    'light': {'type': "v3", 'value': None},
    'ambientLightColor': {'type': "v3", 'value': None},
    'map': {'type': "t", 'value': None},
    'normalMap': {'type': "t", 'value': None},
}

if Config["shadow"]["enabled"]:
    uniforms['directionalShadowMap'] = {'type': 'v', 'value': None}
    uniforms['directionalShadowMatrix'] = {'type': 'm4', 'value': None}
    uniforms['directionalShadowSize'] = {'type': 'v2', 'value': None}

instance_material = THREE.ShaderMaterial({
    'uniforms': uniforms,
    'vertexShader': loader.load('shaders/instances/vertex.glsl'),
    'fragmentShader': loader.load('shaders/instances/fragment.glsl'),
    'wireframe': False,
    'vertexColors': THREE.Constants.VertexColors,
    'transparent': True
})

instance_depth_material = THREE.ShaderMaterial({
    'uniforms': {},
    'vertexShader': loader.load('shaders/instances/depth_vertex.glsl'),
    'fragmentShader': loader.load('shaders/instances/depth_fragment.glsl')
})


class Assets:
    def __init__(self):
        self.assets = {}

    def _load(self, file):
        cache = pyCache("%s.obj" % file)
        asset = cache.load()
        if asset is None:
            f = os.path.basename(file)
            dir = os.path.dirname(file)

            mtlLoader = MTLLoader()
            mtlLoader.setPath(dir)
            materials = mtlLoader.load( "%s.mtl" % f)
            materials.preload()

            loader = OBJLoader2()
            loader.setPath(dir)
            loader.setMaterials(materials.materials)
            asset = loader.load("%s.obj" % f)
            cache.save(asset)
        else:
            asset.rebuild_id()

        return asset

    def set_light_uniform(self, position):
        for asset in self.assets.values():
            asset.material.uniforms.light.value.copy(position)

    def _instantiate_mesh(self, mesh):
        normalMap = None
        map = None

        if mesh.material is not None:
            if hasattr(mesh.material, 'map'):
                map = mesh.material.map
            if hasattr(mesh.material, 'normalMap'):
                normalMap = mesh.material.normalMap

        instancedBufferGeometry = THREE.InstancedBufferGeometry().copy(mesh.geometry)

        # we can display up to 1000 instances
        offsets = THREE.InstancedBufferAttribute(Float32Array(48000), 3, 1).setDynamic( True )
        scales = THREE.InstancedBufferAttribute(Float32Array(48000), 2, 1).setDynamic( True )
        instancedBufferGeometry.addAttribute('offset', offsets)  # per mesh translation
        instancedBufferGeometry.addAttribute('scale', scales)  # per mesh scale

        instancedBufferGeometry.maxInstancedCount = 0

        mesh.geometry = instancedBufferGeometry

        mesh.castShadow = True
        mesh.receiveShadow = True
        mesh.customDepthMaterial = instance_depth_material
        mesh.material = instance_material.clone()
        mesh.material.map = map
        mesh.material.normalMap = normalMap
        mesh.material.uniforms.map.value = map
        mesh.material.uniforms.normalMap.value = normalMap

        mesh.frustumCulled = False

    def load(self, name, level, model, vscale):
        asset = self._load(model)
        mesh = asset.children[0]
        mesh.geometry.computeBoundingBox()
        mesh.material.normalMap = mesh.material.bumpMap
        mesh.material.bumpMap = None
        dx = abs(mesh.geometry.boundingBox.min.x) + abs(mesh.geometry.boundingBox.max.x)
        dy = abs(mesh.geometry.boundingBox.min.y) + abs(mesh.geometry.boundingBox.max.y)
        dz = abs(mesh.geometry.boundingBox.min.z) + abs(mesh.geometry.boundingBox.max.z)

        mesh.geometry.scale(1 / dx, 1 / dy, 1 / dz)
        mesh.geometry.rotateX(math.pi / 2)

        self._instantiate_mesh(mesh)

        scale = mesh.geometry.attributes.scale
        for i in range(0, len(scale.array), 2):
            scale.array[i] = vscale.x
            scale.array[i + 1] = vscale.y

        if level is not None:
            k = "%s:%d" % (name, level)
        else:
            k = name

        self.assets[k] = mesh

    def add_2_scene(self, scene):
        # add them to the scene, as each asset as a instancecount=0, none will be displayed
        for mesh in self.assets.values():
           scene.add(mesh)

    def reset_instances(self):
        for asset in self.assets.values():
            asset.geometry.maxInstancedCount = 0

    def instantiate(self, asset):
        key = "%s:%d" % (asset.name, asset.level)
        geometry = self.assets[key].geometry
        l = geometry.maxInstancedCount
        m = len(asset.offset)
        geometry.attributes.offset.array[l * 3:l * 3 + m] = asset.offset[0:m]
        m = len(asset.scale)
        geometry.attributes.scale.array[l * 2:l * 2 + m] = asset.scale[0:m]

        geometry.maxInstancedCount += int(m / 2)

        geometry.attributes.offset.needsUpdate = True
        geometry.attributes.scale.needsUpdate = True

    def get(self, name):
        return self.assets[name]
