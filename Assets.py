"""
3D Asset
"""
from THREE.loaders.OBJLoader2 import *
from THREE.loaders.MTLLoader import *
from THREE.pyOpenGL.pyCache import *
from Config import *
from THREE.loaders.ColladaLoader2 import *
import Utils

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
    'vertexShader': loader.load('shaders/dynamic_instances/vertex.glsl'),
    'fragmentShader': loader.load('shaders/instances/fragment.glsl'),
    'wireframe': False,
    'vertexColors': THREE.Constants.VertexColors,
    'transparent': True
})

instance_grass_material = THREE.ShaderMaterial({
    'uniforms': uniforms,
    'vertexShader': loader.load('shaders/dynamic_instances/vertex_grass.glsl'),
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
        self.cache = {}

    def _load(self, file):
        f = os.path.basename(file)
        dir = os.path.dirname(file)

        if ".dae" in file:
            loader = ColladaLoader()
            collada = loader.load(file)
            asset = collada.scene
        else:
            mtlLoader = MTLLoader()
            mtlLoader.setPath(dir)
            materials = mtlLoader.load( "%s.mtl" % f)
            materials.preload()

            loader = OBJLoader2()
            loader.setPath(dir)
            loader.setMaterials(materials.materials)
            asset = loader.load("%s.obj" % f)

        return asset

    def set_light_uniform(self, position):
        for asset in self.assets.values():
            asset.material.uniforms.light.value.copy(position)

    def _instantiate_mesh(self, mesh, dynamic):
        normalMap = None
        map = None

        if mesh.material is not None:
            if hasattr(mesh.material, 'map'):
                map = mesh.material.map
            if hasattr(mesh.material, 'normalMap'):
                normalMap = mesh.material.normalMap

        instancedBufferGeometry = THREE.InstancedBufferGeometry().copy(mesh.geometry)

        # we can display up to 16000 instances
        offsets = THREE.InstancedBufferAttribute(Float32Array(64000), 3, 1).setDynamic(True)
        instancedBufferGeometry.addAttribute('offset', offsets)  # per mesh translation

        if dynamic:
            mesh.material = instance_grass_material.clone()
            normals = THREE.InstancedBufferAttribute(Float32Array(64000), 3, 1).setDynamic(True)
            instancedBufferGeometry.addAttribute('normals', normals)
            instancedBufferGeometry.removeAttribute('normal')
        else:
            mesh.material = instance_material.clone()
            scales = THREE.InstancedBufferAttribute(Float32Array(64000), 2, 1).setDynamic(True)
            instancedBufferGeometry.addAttribute('scale', scales)  # per mesh scale

        instancedBufferGeometry.maxInstancedCount = 0

        mesh.geometry = instancedBufferGeometry

        mesh.castShadow = True
        mesh.receiveShadow = True
        mesh.customDepthMaterial = instance_depth_material
        mesh.material.map = map
        mesh.material.normalMap = normalMap
        mesh.material.uniforms.map.value = map
        mesh.material.uniforms.normalMap.value = normalMap

        mesh.frustumCulled = False

    def load(self, name, level, model, vscale, dynamic=False):
        if model in self.cache:
            mesh = self.cache[model].clone()
        else:
            cache = pyCache("%s.obj" % model)
            mesh = cache.load()
            if mesh is None:
                asset = self._load(model)

                mesh = asset.children[0]
                mesh.geometry = Utils.Geometry2indexedBufferGeometry(mesh.geometry)
                mesh.userData["dynamic"] = True
                mesh.geometry.computeBoundingBox()
                if not isinstance(mesh.material, list):
                    mesh.material.normalMap = mesh.material.bumpMap
                    mesh.material.bumpMap = None
                dx = abs(mesh.geometry.boundingBox.min.x) + abs(mesh.geometry.boundingBox.max.x)
                dy = abs(mesh.geometry.boundingBox.min.y) + abs(mesh.geometry.boundingBox.max.y)
                dz = abs(mesh.geometry.boundingBox.min.z) + abs(mesh.geometry.boundingBox.max.z)

                mesh.geometry.scale(1 / dx, 1 / dx, 1 / dx)
                mesh.geometry.rotateX(math.pi / 2)
                self.cache[model] = mesh
                mesh.name = model
                cache.save(mesh)
            else:
                mesh.rebuild_id()

        self._instantiate_mesh(mesh, dynamic)

        if not dynamic:
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
           scene.add_instance(mesh)

    def reset_instances(self):
        for asset in self.assets.values():
            if "dynamic" not in asset.userData:
                asset.geometry.maxInstancedCount = 0

    def reset_dynamic_instances(self):
        for asset in self.assets.values():
            if "dynamic" in asset.userData:
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
