import json
import pickle

import THREE
import Utils as THREE_utils
from Config import *
from progress import *


_BoundingSphereMaterial = THREE.MeshLambertMaterial({
            'color': 0x0000ff,
            'opacity': 0.2,
            'transparent': True,
            'wireframe': False})

_material = THREE.MeshBasicMaterial({'map': THREE.TextureLoader().load('img/evergreen.png')})


class Quadtree:
    material = None

    def __init__(self, level, center, size):
        self.name = ""
        self.level = level
        self.center = center
        self.radius = 0
        self.size = size
        self.objects = []         # // scenary objects
        self.scenary_meshes = []  # // scenary meshes
        self.mesh = None          # // terrain mesh
        self.merged_mesh = None   # // merged mesh of terrain and scenaries
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
                "radius": self.radius,
                "size": self.size,
            }
        else:
            return {
                "name": self.name,
                "level": self.level,
                "center": self.center.toArray(),
                "radius": self.radius,
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

    def add2scene(self, scene):
        """
        @param {type} scene
        @returns {undefined}
        """
        # Add to scene if not yet there
        if not self.mesh:
            self._loadMesh(scene)
            return

        self.mesh.visible = True

        if Config['terrain']['debug']['boundingsphere']:
            self.boundingsphere.visible = True

    def remove4scene(self, scene):
        """
        @param {type} scene
        @returns {undefined}
        """
        self.mesh.visible = False

        if Config['terrain']['debug']['boundingsphere']:
            self.boundingsphere.visible = False

    def _loadMesh(self, scene):
        """
        @param {type} name
        @param {type} scene
        @returns {undefined}
        """

        # load the terrain mesh and display
        with open("bin/" + self.name + ".terrain.pkl", "rb") as f:
            mesh = pickle.load(f)

        # load the merged mesh
        with open("bin/" + self.name + ".scenary.pkl", "rb") as f:
            merged_mesh = pickle.load(f)

        param = mesh.geometry.parameters
        geometry = THREE.PlaneBufferGeometry(param['height'], param['width'], param['heightSegments'], param['widthSegments'])

        geometry.attributes = mesh.geometry.attributes

        self.mesh = THREE.Mesh(geometry, self.material)
        self.mesh.position = mesh.position

        # print("TODO: quadtree._loadMesh > why build a new mesh and not use the loaded one ?")
        # mesh.material = self.material
        # self.merged_mesh = mesh

        # self.merged_mesh.material = Materials['terrain']

        # load the scenary mesh and display
        if merged_mesh is not None:
            mesh1 = THREE.Mesh(merged_mesh.geometry, merged_mesh.material)
            # mesh1.position.copy(mesh.position)
            self.mesh.add(mesh1)

        scene.add(self.mesh)

        if Config['terrain']['debug']['boundingsphere']:
            radius = self.merged_mesh.geometry.boundingSphere.radius
            bs = THREE.SphereBufferGeometry(radius, 32, 32)
            # center = THREE.Vector3().addVectors(self.merged_mesh.geometry.boundingSphere.center, self.merged_mesh.position)
            self.boundingsphere = THREE.Mesh(bs, _BoundingSphereMaterial)
            # self.boundingsphere.position.copy(center)
            self.boundingsphere.visible = True
            self.merged_mesh.add(self.boundingsphere)

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

        # delete the scenary meshes
        # self.scenary_meshes = None

        for sub in self.sub:
            if sub is not None:
                count = sub.optimize_meshes(level+1, count + 1, nb)

        return count
