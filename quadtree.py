import json
import pickle
import multiprocessing
import random

import THREE
import Utils as THREE_utils
from Config import *
from progress import *

AsyncIO = None

_BoundingSphereMaterial = THREE.MeshLambertMaterial({
            'color': 0x0000ff,
            'opacity': 0.2,
            'transparent': True,
            'wireframe': False})

_material = THREE.MeshBasicMaterial({'map': THREE.TextureLoader().load('img/evergreen.png')})


def _loadMeshIO(name):
    """
    # load the terrain mesh and display
    # load the merged mesh
    :return:
    """
    with open("bin/" + name + ".terrain.pkl", "rb") as f:
        mesh = pickle.load(f)

    with open("bin/" + name + ".scenary.pkl", "rb") as f:
        merged_mesh = pickle.load(f)

    return (mesh, merged_mesh)


class Quadtree:
    material = None
    asyncIO = None

    def __init__(self, level, center, size, parent):
        self.name = ""
        self.level = level
        self.center = center
        self.lod_radius = 0       # LOD radius load the tile
        self.visibility_radius = 0  # frustrum visibility radius
        self.size = size
        self.objects = []         # // scenary objects
        self.scenary_meshes = []  # // scenary meshes
        self.mesh = None          # // terrain mesh
        self.merged_mesh = None   # // merged mesh of terrain and scenaries
        self.traversed = False    # was the node traversed during a recursive pass
        self.visible = False
        self.parent = parent
        self.added = False

        self.sub = [None]*4

        if Config['terrain']['debug']['normals']:
            self.normals = None

        if Config['terrain']['debug']['boundingsphere']:
            self.boundingsphere = None

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
        self.mesh = self.scenary_meshes = self.merged_mesh = None
        t.append(self)

        if not self.sub[0] is None:
            for q in self.sub:
                q.dump(t)

    def dump_mesh(self):
        # remove the  parameters from the PlaneBufferGeometry to force THREE to dump all the vertices
        # otherwise it will only dump the meta data
        # self.mesh.geometry.type = 'BufferGeometry'
        # self.mesh.geometry.parameters = None
        # m = self.mesh.toJSON(None)
        # j = json.dumps(m)
        # with open("../public_html/json/" + self.name + ".json", "w") as f:
        #    f.write(j)

        with open("bin/" + self.name + ".terrain.pkl", "wb") as f:
            pickle.dump(self.mesh, f)

        with open("bin/" + self.name + ".scenary.pkl", "wb") as f:
            pickle.dump(self.merged_mesh, f)

        if not self.sub[0] is None:
            for q in self.sub:
                q.dump_mesh()

    def load(self):
        """
        @param {type} scene
        @returns {undefined}
        """
        global AsyncIO

        # Add to scene if not yet there
        if not self.mesh:
            AsyncIO.read(self)

    def display(self):
        """

        :return:
        """
        self.visible = self.mesh.visible = True

        if Config['terrain']['debug']['boundingsphere']:
            self.boundingsphere.visible = True

    def hide(self):
        """
        @param {type} scene
        @returns {undefined}
        """
        if self.mesh is None:
            return

        self.visible = self.mesh.visible = False

        if Config['terrain']['debug']['boundingsphere']:
            self.boundingsphere.visible = False

    def _record_mesh(self, scene, terrain_mesh, scenary_mesh):
        """
        @param {type} name
        @param {type} scene
        @returns {undefined}
        """

        self.mesh = terrain_mesh
        if self.material is None:
            self.mesh.material = THREE.MeshLambertMaterial({'color': random.random()*0xffffff})
        else:
            self.mesh.material = self.material
        self.mesh.castShadow = True
        self.mesh.receiveShadow = True

        # load the scenary mesh and display
        if Config['terrain']['display_scenary'] and scenary_mesh is not None:
            scenary_mesh.castShadow = True
            scenary_mesh.receiveShadow = True
            # scenary_mesh.material = THREE.MeshLambertMaterial({'color': random.random()*0xffffff})
            self.mesh.add(scenary_mesh)

        if Config['terrain']['debug']['boundingsphere']:
            radius = self.merged_mesh.geometry.boundingSphere.radius
            bs = THREE.SphereBufferGeometry(radius, 32, 32)
            self.boundingsphere = THREE.Mesh(bs, _BoundingSphereMaterial)
            self.boundingsphere.position.copy(center)
            self.boundingsphere.visible = True
            self.merged_mesh.add(self.boundingsphere)

        if Config['player']['debug']['collision']:
            center = self.mesh.position.clone()
            for obj in self.objects:
                self.mesh.add(obj.AxisAlignedBoundingBoxes(center))

        if self.level > 4 and Config['terrain']['debug']['normals']:
            self.normals = THREE.VertexNormalsHelper(mesh, 1, 0xff0000, 1)
            self.merged_mesh.add(self.normals)

        return self

    def around(self, p):
        """
        Find the deepest quad containing the provided point
        """
        if not self.sub[0]:
            # reached the deepest level
            return self

        if p.x < self.center.x:
            if p.y < self.center.y:
                return self.sub[0].around(p)
            else:
                return self.sub[2].around(p)
        else:
            if p.y < self.center.y:
                return self.sub[1].around(p)
            else:
                return self.sub[3].around(p)

    def insert_object(self, object, level):
        """
        Use the footprint of the object to insert it mesh on all quads it covers
        """

        # create and register the mesh
        # translate the mesh coordinate(world) to the quadrant coordinate
        mesh = object.build_mesh(level)
        if mesh:
            mesh.position.set(object.position.x - self.center.x, object.position.y - self.center.y, object.position.z)
            self.scenary_meshes.append(mesh)

        # register the 2D footprint
        self.objects.append(object)

        if self.sub[0] is None:
            # reached the deepest level
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

    def optimize_meshes(self, level, count, nb):
        """
        merge all the meshes into a super mesh
        :param level:
        :return:
        """
        progress(count, nb, "Build scenery mesh")
        if len(self.scenary_meshes) > 0:
            self.merged_mesh = THREE_utils.mergeMeshes(self.scenary_meshes)
            self.merged_mesh.geometry.computeBoundingSphere()

        # clean up the scenary data
        self.scenary_meshes = None
        self.scenery = None

        # pre compute the bounding sphere (cpu intensive at run time)
        self.mesh.geometry.computeBoundingSphere()

        for sub in self.sub:
            if sub is not None:
                count = sub.optimize_meshes(level+1, count + 1, nb)

        return count


class quadtreeMessage:
    def __init__(self, name):
        self.name = name
        self.terrain_mesh = None
        self.scenary_mesh = None


class QuadtreeReader(multiprocessing.Process):
    """
    """
    def __init__(self, task_queue, result_queue):
        multiprocessing.Process.__init__(self)
        self.task_queue = task_queue
        self.result_queue = result_queue

    def run(self):
        proc_name = self.name
        while True:
            quadtree_msg = self.task_queue.get()
            if quadtree_msg is None:
                # Poison pill means shutdown
                break
            (terrain_mesh, scenary_mesh) = _loadMeshIO(quadtree_msg.name)
            quadtree_msg.terrain_mesh = terrain_mesh
            quadtree_msg.scenary_mesh = scenary_mesh
            self.result_queue.put(quadtree_msg)
        return


class QuadtreeProcess:
    """

    :return:
    """
    def __init__(self):
        # Establish communication queues
        self.tasks = multiprocessing.Queue()
        self.results = multiprocessing.Queue()
        # self.process = QuadtreeReader(self.tasks, self.results)
        # self.process.start()
        self.callbacks = {}
        self.scene = None

    def read(self, quadtree):
        if quadtree.name in self.callbacks:
            return

        self.callbacks[quadtree.name] = quadtree
        # self.tasks.put(quadtreeMessage(quadtree.name))
        (terrain_mesh, scenary_mesh) = _loadMeshIO(quadtree.name)
        quadtree._record_mesh(self.scene, terrain_mesh, scenary_mesh)

    def check(self):
        return
        while not self.results.empty():
            quadtree_msg = self.results.get()
            quadtree = self.callbacks[quadtree_msg.name]
            quadtree._record_mesh(self.scene, quadtree_msg.terrain_mesh, quadtree_msg.scenary_mesh)

    def terminate(self):
        # self.process.terminate()
        return

def initQuadtreeProcess():
    global AsyncIO
    AsyncIO = QuadtreeProcess()


def checkQuadtreeProcess():
    global AsyncIO
    AsyncIO.check()


def loadQuadtreeProcess(quad, scene):
    global AsyncIO
    AsyncIO.read(quad, scene, False)


def killQuadtreeProcess():
    global AsyncIO
    AsyncIO.terminate()
