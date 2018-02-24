"""
 @class Scenary: Upper class for all scenary objects
 @returns {Scenery}
"""
from Config import*

from THREE.Loader import *
from THREE.Group import *
from THREE.javascriparray import *
from Asset import *


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


class Scenery:
    Forest = 3
    Grass = 0
    
    def __init__(self, position, scale, name):
        self.position = position
        self.scale = scale
        self.footprints = []
        self.type = None
        self.name = name
        self.mesh = None

    def rotateZ(self, r):
        self.mesh.geometry.rotateZ(r)    

    def translate(self, v):
        self.mesh.position.copy(v)
        
        # translate the footprints
        for footprint in self.footprints:
            footprint.translate(v)

    def AxisAlignedBoundingBoxes(self, center):
        aabbs = THREE.Group()
        center.z = self.position.z
        for footprint in self.footprints:
            aabbs.add(footprint.AxisAlignedBoundingBox(center))

        return aabbs

    def build_mesh(self, level, model):
        asset = Asset(self.name, model)
        mesh = asset.mesh.children[0]
        mesh.geometry.computeBoundingBox()
        mesh.material.normalMap = mesh.material.bumpMap
        mesh.material.bumpMap = None
        dx = abs(mesh.geometry.boundingBox.min.x) + abs(mesh.geometry.boundingBox.max.x)
        dy = abs(mesh.geometry.boundingBox.min.y) + abs(mesh.geometry.boundingBox.max.y)
        dz = abs(mesh.geometry.boundingBox.min.z) + abs(mesh.geometry.boundingBox.max.z)

        mesh.geometry.scale(1 / dx, 1 / dy, 1 / dz)
        mesh.geometry.rotateX(math.pi / 2)

        self.instantiate_mesh(mesh)

        scale = mesh.geometry.attributes.scale
        for i in range(0, len(scale.array), 2):
            scale.array[i] = self.scale.x
            scale.array[i + 1] = self.scale.y

        return mesh

    def instantiate_mesh(self, mesh):
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
