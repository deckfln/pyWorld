"""

"""
import json
import pickle
# import multiprocessing
import random
from threading import Thread
import queue
import time

import THREE
import Utils as THREE_utils
import THREE.renderers.shaders.ShaderLib as THREE_ShaderLib
from THREE.textures.DataTexture import *

from Config import *
from progress import *
from THREE.javascriparray import *
import math
from DataMap import *

_BoundingSphereMaterial = THREE.MeshLambertMaterial({
    'color': 0x0000ff,
    'opacity': 0.2,
    'transparent': False,
    'wireframe': True
})
_spheregeometry = THREE.SphereBufferGeometry(0.7, 32, 32)

# _material = THREE.MeshBasicMaterial({'map': THREE.TextureLoader().load(Config['folder']+'/img/UV_Grid_Sm.jpg')})


def _loadMeshIO(name):
    """
    # load the terrain mesh and display
    # load the merged mesh
    :return:
    """
    with open("bin/" + name + ".terrain.pkl", "rb") as f:
        mesh = pickle.load(f)
        mesh.rebuild_id()

    return mesh


class _instance:
    def __init__(self, name, level):
        self.name = name
        self.level = level
        self.offset = []
        self.scale = []


class Quadtree:
    material = None
    material_far = None
    material_very_far = None
    asyncIO = None
    NOT_LOADED = 0
    LOADING = 1
    LOADED = 2

    def __init__(self, level, center, size, parent):
        self.name = ""
        self.level = level
        self.center = center
        self.lod_radius = 0       # LOD radius load the tile
        self.visibility_radius = 0  # frustrum visibility radius
        self.size = size
        self.objects = []         # // scenary objects
        self.assets = {}       # // scenary meshes
        self.mesh = None          # // terrain mesh
        self.last_on_screen = 0   # last time the mesh was on screen
        self.traversed = False    # was the node traversed during a recursive pass
        self.visible = False      # display or not the tile
        self.parent = parent      #
        self.added = False        # is the tile added to the Scene ?
        self.north = None         # neighbors on screen
        self.south = None
        self.west = None
        self.east = None
        self.datamap = None
        self.status = Quadtree.NOT_LOADED

        self.sub = [None]*4

        if Config['terrain']['debug']['normals']:
            self.normals = None

        if Config['terrain']['debug']['boundingsphere']:
            self.boundingsphere = None

    def init_mesh(self, quad_width):
        v2 = self.center.clone()
        total_size = self.size * 2**self.level
        v2.x += total_size/2
        v2.y += total_size/2
        v2.divideScalar(total_size)

        if Config['terrain']['debug']['uv']:
            material = THREE.RawShaderMaterial({
                'uniforms': {
                    'datamap': {'type': "t", 'value': self.datamap},
                    'map': {'type': 't', 'value': self.material.map},
                    'centerVuv': {'type': 'v2', 'value': v2},
                    'level': {'type': 'f', 'value': 2**self.level},
                    'light': {'type': 'v3', 'value': self.material.uniforms.light.value}
                },
                'vertexShader': self.material.vertexShader,
                'fragmentShader': self.material.fragmentShader,
                'color': 0x000ff,
                'wireframe': Config['terrain']['debug']['wireframe']
            })
        else:
            material = THREE.RawShaderMaterial( {
                'uniforms': {
                    'datamap': {'type': "t", 'value': self.datamap},
                    'centerVuv': {'type': 'v2', 'value': v2},
                    'level': {'type': 'f', 'value': 2**self.level},
                    'blendmap_texture': {'type': "t", 'value': self.material.uniforms.blendmap_texture.value},
                    'terrain_textures': {'type': "t", 'value': self.material.uniforms.terrain_textures.value},
                    'light': {'type': "v3", 'value': self.material.uniforms.light.value},
                    'indexmap': {'type': "t", 'value': self.material.uniforms.indexmap.value},
                    'indexmap_size': {'type': "f", 'value': self.material.uniforms.indexmap_size.value},
                    'indexmap_repeat': {'type': "f", 'value': self.material.uniforms.indexmap_repeat.value},
                    'blendmap_repeat': {'type': "f", 'value': 64},
                    'ambientCoeff': {'type': "float", 'value': self.material.uniforms.ambientCoeff.value},
                    'sunColor': {'type': "v3", 'value': self.material.uniforms.sunColor.value},
                    },
                'vertexShader': self.material.vertexShader,
                'fragmentShader': self.material.fragmentShader,
                'wireframe': Config['terrain']['debug']['wireframe']
            })

        #TODO: use a the same geometry for each block because the boundinSphere is uniq to each tile
        #TODO: but find how to have different boundingSpheres for the same geometry
        s = self.size - 1
        geometry = THREE.PlaneBufferGeometry(1, 1, quad_width, quad_width)
        plane = THREE.Mesh(geometry, material)
        plane.castShadow = True
        plane.receiveShadow = True

        return plane

    def toJSON(self):
        if self.sub[0] is None:
            return {
                "name": self.name,
                "level": self.level,
                "center": self.center.toArray(),
                "radius": self.lod_radius,
                "size": self.size,
            }
        else:
            return {
                "name": self.name,
                "level": self.level,
                "center": self.center.toArray(),
                "radius": self.lod_radius,
                "size": self.size,
                "sub_name": [a.name for a in self.sub]
            }

    def dump(self, t):
        # j = self.toJSON()
        # t.append(j)
        self.datamap = self.mesh = self.scenary_meshes = None
        t.append(self)

        if not self.sub[0] is None:
            for q in self.sub:
                q.dump(t)

    def dump_mesh(self):
        self.mesh.geometry.computeBoundingSphere()
        with open(Config['folder']+"/bin/" + self.name + ".terrain.pkl", "wb") as f:
            pickle.dump(self.mesh, f)

        if not self.sub[0] is None:
            for q in self.sub:
                q.dump_mesh()

    def dump_datamap(self):
        file = Config['folder']+"/bin/" + self.name
        if self.datamap is None:
            raise Exception("not good")
        self.datamap.save(file)

        if not self.sub[0] is None:
            for q in self.sub:
                q.dump_datamap()

    def load(self):
        """
        """
        with open(Config['folder']+"/bin/" + self.name + ".terrain.pkl", "rb") as f:
            mesh = pickle.load(f)
            mesh.rebuild_id()
            self._record_mesh(mesh)

    def load_datamap(self):
        """
        """
        file = Config['folder']+"/bin/" + self.name +".npy"
        datamap = DataMap(0)
        datamap.load(file)

        # find the average Z for the boundingsphere
        z = datamap.average()

        self.datamap = datamap.DataTexture()
        self.datamap.needsUpdate = True

        scale = 2 ** (9 - self.level)
        mesh = self.init_mesh(datamap.size-1)
        mesh.scale.set(scale, scale, 1.0)
        mesh.position.x = self.center.x
        mesh.position.y = self.center.y
        mesh.geometry.computeBoundingSphere()
        mesh.geometry.boundingSphere.center.z = z

        if Config['terrain']['debug']['boundingsphere']:
            # TODO : how do you draw the bounding spheres of an instance ?
            radius = mesh.geometry.boundingSphere.radius
            boundingsphere = THREE.Mesh(_spheregeometry, _BoundingSphereMaterial)
            boundingsphere.scale.set(1.0, 1.0, scale)
            boundingsphere.position.z = z
            mesh.add(boundingsphere)
            self.bs = boundingsphere

        self.mesh = mesh

    def loadChildren(self, p):
        """
        @param {type} scene
        @returns {undefined}
        """
        p.load_percentage += 0.1
        self.load_datamap()
        if self.sub[0] is not None:
            for child in self.sub:
                child.loadChildren(p)

    #def add2scene(self, list):
    #    list.append(self)
    #    if self.sub[0] is not None:
    #        for child in self.sub:
    #            child.add2scene(list)
    def add2scene(self, scene):
        if not self.added:
            self.mesh.visible = self.visible
            scene.add(self.mesh)
            self.added = True

    def notTraversed(self):
        self.traversed = False
        if self.sub[0] is not None:
            for child in self.sub:
                if child.traversed:
                    child.notTraversed()

    def build_index(self, index):
        idx = "%d-%d-%d" % (self.level, self.center.x, self.center.y)
        index[idx] = self
        if self.sub[0] is not None:
            for child in self.sub:
                child.build_index(index)

    def display(self):
        self.visible = True
        if self.mesh:
            self.mesh.visible = True
        self.last_on_screen = time.clock()

        if Config['terrain']['debug']['boundingsphere']:
            self.bs.visible = True

    def hide(self):
        """
        @param {type} scene
        @returns {undefined}
        """
        self.visible = False
        if self.mesh:
            self.mesh.visible = False
            return

        if Config['terrain']['debug']['boundingsphere']:
            self.bs.visible = False

    def _record_mesh(self, terrain_mesh):
        """
        @param {type} name
        @param {type} scene
        @returns {undefined}
        """

        if self.material is None:
            terrain_mesh.material = THREE.MeshLambertMaterial({
                'color': random.random()*0xffffff,
                'wireframe': Config['terrain']['debug']['wireframe']
            })
        else:
            if self.level < 3:
                terrain_mesh.material = self.material_very_far
            elif self.level < 5:
                terrain_mesh.material = self.material_far
            else:
                terrain_mesh.material = self.material

        # if Config['terrain']['debug']['boundingsphere']:
        # TODO : how do you draw the bounding spheres of an instance ?
        #    radius = self.merged_mesh.geometry.boundingSphere.radius
        #    bs = THREE.SphereBufferGeometry(radius, 32, 32)
        #    self.boundingsphere = THREE.Mesh(bs, _BoundingSphereMaterial)
        #    self.boundingsphere.position.copy(center)
        #    self.boundingsphere.visible = True
        #    self.merged_mesh.add(self.boundingsphere)

        if Config['player']['debug']['collision']:
            center = self.mesh.position.clone()
            for obj in self.objects:
                terrain_mesh.add(obj.AxisAlignedBoundingBoxes(center))

        if self.level > 3 and Config['terrain']['debug']['normals']:
            self.normals = THREE.VertexNormalsHelper(terrain_mesh, 4, 0xff0000, 4)
            terrain_mesh.add(self.normals)

        self.mesh = terrain_mesh
        # print("quadtree:_record_mesh:%s" % self.name)

        return self

    def around(self, p, max_depth: int = -1):
        """
        Find the deepest quad containing the provided point
        """
        if self.level == max_depth or not self.sub[0]:
            # reached the deepest level
            return self

        x = self.center.np[0]
        y = self.center.np[1]
        py = p.np[1]

        if p.np[0] < x:
            if py < y:
                return self.sub[0].around(p, max_depth)
            else:
                return self.sub[2].around(p, max_depth)
        else:
            if py < y:
                return self.sub[1].around(p, max_depth)
            else:
                return self.sub[3].around(p, max_depth)

    def insert_object(self, object, level):
        """
        Use the footprint of the object to insert it mesh on all quads it covers
        """

        # create and register the mesh for the instance
        if object.name not in self.assets:
            self.assets[object.name] = _instance(object.name, level)

        # translate the object position
        # register the instance
        self.assets[object.name].offset.extend([
            object.position.x,
            object.position.y,
            object.position.z
        ])
        self.assets[object.name].scale.extend([
            object.scale,
            object.scale
        ])
        # register the 2D footprint
        self.objects.append(object)

        # reached the deepest level
        if self.sub[0] is None:
            return

        # use the footprints of the object
        quadrand=[False, False, False, False]
        target = -1

        # insert the object in the subquads based on its footprint corners
        for footprint in object.footprints:
            # foreach corners of the footprint
            for p in footprint.p:       # corner of the footprint
                # find the sub-quad target for the corner
                if p.x < self.center.x:
                    if p.y < self.center.y:
                        target = 0
                    else:
                        target = 2
                else:
                    if p.y < self.center.y:
                        target = 1
                    else:
                        target = 3

                # insert the objet inb the sub-quad, if it was not yet added
                if not quadrand[target]:
                    self.sub[target].insert_object(object, level+1)
                    quadrand[target] = True

    def scenery_instance(self):
        """
        :return:
        """
        box = THREE.Box3()
        vector = THREE.Vector3()

        def computeBoundingSphere(geometry):
            if geometry.boundingSphere is None:
                geometry.boundingSphere = THREE.Sphere()

            offset = geometry.attributes.offset
            if offset:
                center = geometry.boundingSphere.center
                box.setFromBufferAttribute(offset)
                box.getCenter(center)
                # // hoping to find a boundingSphere with a radius smaller than the
                # // boundingSphere of the boundingBox: sqrt(3) smaller in the best case

                maxRadiusSq = 0
                for i in range(0, len(offset.array), offset.itemSize):
                    vector.np[0] = offset.array[i]
                    vector.np[1] = offset.array[i + 1]
                    vector.np[2] = offset.array[i + 2]
                    maxRadiusSq = max(maxRadiusSq, center.distanceToSquared(vector))

                    geometry.boundingSphere.radius = math.sqrt(maxRadiusSq)
                if math.isnan(geometry.boundingSphere.radius):
                    print(
                        'THREE.BufferGeometry.computeBoundingSphere(): Computed radius is NaN. The "position" attribute is likely to have NaN values.', self)

        # clean up the scenary data

        # create instances of each type of scenery
        for obj in self.scenary_meshes.values():
            if obj is not None:
                offsets = THREE.InstancedBufferAttribute(Float32Array(obj.instances), 3, 1)
                scales = THREE.InstancedBufferAttribute(Float32Array(obj.scales), 2, 1)
                obj.geometry.addAttribute( 'offset', offsets )  # per mesh translation
                obj.geometry.addAttribute( 'scale', scales)     # per mesh scale
                computeBoundingSphere(obj.geometry)

        # pre compute the bounding sphere (cpu intensive at run time)
        self.mesh.geometry.computeBoundingSphere()

        for sub in self.sub:
            if sub is not None:
                count = sub.scenery_instance()

    def is_point_inside(self, p):
        """
        """
        size = self.size / 2
        x = self.center.np[0]
        y = self.center.np[1]

        sx = x - size
        ex = x + size
        sy = y - size
        ey = y + size
        return sx <= p.np[0] <= ex and sy <= p.np[1] <= ey


class quadtreeMessage:
    def __init__(self, name):
        self.name = name
        self.terrain_mesh = None
        self.scenary_mesh = None


class QuadtreeReader(Thread):
    """
    https://skryabiin.wordpress.com/2015/04/25/hello-world/
    SDL 2.0, OpenGL, and Multithreading (Windows)
    """

    def __init__(self, parent):
        super().__init__()
        self.queue = parent.queue
        self.inmemory  = parent.inmemory

    def run(self):
        queue = self.queue

        while True:
            quadtree = queue.get()
            if quadtree is None:
                break

            quadtree.status = Quadtree.LOADING
            quadtree.load_datamap()
            quadtree.status = Quadtree.LOADED

            queue.task_done()

            # register the mesh in memory and the time of load
            self.inmemory.append(quadtree)


class QuadtreeManager:
    """

    :return:
    """
    def __init__(self):
        # Establish communication queues
        self.queue = queue.Queue()
        self.loaded = 0
        self.inmemory = []

        self.thread = QuadtreeReader(self)
        self.thread.start()

    def read(self, quadtree):
        self.queue.put(quadtree)
        self.loaded += 1

    def cleanup(self, scene):
        """
        clean old unused mesh quads
        :return:
        """
        # sort the quad by last time on screen
        def _sort(quad):
            return quad.last_on_screen

        if self.loaded >= 1024:
            self.inmemory.sort(key=_sort)

            count = 100
            for quad in self.inmemory:
                if count < 0:
                    break

                if not quad.visible:
                    if quad.mesh:
                        scene.remove(quad.mesh)
                        quad.mesh.dispose()
                        quad.mesh = None
                        self.loaded -= 1

                count -= 1

    def terminate(self):
        self.queue.put(None)
        self.thread.join()
        return
