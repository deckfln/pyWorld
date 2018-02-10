"""
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
"""

from THREE import *

from Config import *
from Footprint import *
from Scenery import *
from progress import *
import Utils as THREE_Utils
import Terrain
from Utils import *
import city
from Asset import *


tree_material_trunk= Material2InstancedMaterial(THREE.MeshLambertMaterial( {
            'color': 0x8B4513,
            'wireframe': False,
            'name': "tree_material_trunk"}))

tree_material_foliage= Material2InstancedMaterial(THREE.MeshLambertMaterial( {
            'color': 0x00ff00,
            'wireframe': False,
            'name':"tree_material_foliage"} ))
tree_texture = Material2InstancedMaterial(THREE.MeshBasicMaterial({
    'side': THREE.DoubleSide,
    'transparent': True,
    'depthWrite': True,
    'depthTest': True,
    'wireframe': False,
    'alphaTest': 0.1,
    'map': THREE.ImageUtils.loadTexture('img/tree.png'),
    'name':"tree_texture"
}))


class Tree(Scenery):
    """
    """
    def __init__(self, radius, height, position):
        if radius is None:
            return

        super().__init__(position, radius*2, "tree")

        self.radius = radius
        self.height = height
        self.type = 1

        footprint = FootPrint(
            THREE.Vector2(-0.5, -0.5),  # footprint of the TRUNK
            THREE.Vector2(1, 1),
            0.5,
            position,
            10,
            self
        )
        self.footprints.append(footprint)

    def _build(self, radius, height, trunk, foliage, level):
        """
        """
        g_trunk = THREE_Utils.cylinder(0.1, height/3, trunk)
        colors = g_trunk.attributes.position.clone()
        for i in range(0, len(colors.array), 3):
            colors.array[i] = 0.54
            colors.array[i + 1] = 0.27
            colors.array[i + 2] = 0.07
        g_trunk.addAttribute('color', colors)

        g_foliage = THREE.SphereBufferGeometry(radius, foliage, foliage)
        g_foliage.translate(0, 0, height/2 + height/4)
        colors = g_foliage.attributes.position.clone()
        for i in range(0, len(colors.array), 3):
            colors.array[i] = 0.0
            colors.array[i + 1] = 1.0
            colors.array[i + 2] = 0.0
        g_foliage.addAttribute('color', colors)

        geometry = THREE.BufferGeometry()
        mergeGeometries([g_trunk, g_foliage], geometry)

        return THREE.Mesh(geometry, None)

    def build_mesh(self, level):
        """
        """
        height = 1
        radius = 0.5

        if level == 0:
            return None
        elif level == 1:
            mesh = self._build(radius, height, 3, 4, level)
        elif level == 2:
            mesh = self._build(radius, height, 3, 8, level)
        elif level == 3:
            mesh = self._build(radius, height, 4, 16, level)
        elif level == 4:
            mesh = self._build(radius, height, 8, 32, level)
        else:    # maximum details
            asset = Asset("tree", "models/tree228/tree228")
            mesh = asset.mesh.children[0]
            mesh.geometry.computeBoundingBox()
            mesh.material.normalMap = mesh.material.bumpMap
            mesh.material.bumpMap = None
            dx = abs(mesh.geometry.boundingBox.min.x) + abs(mesh.geometry.boundingBox.max.x)
            dy = abs(mesh.geometry.boundingBox.min.y) + abs(mesh.geometry.boundingBox.max.y)
            dz = abs(mesh.geometry.boundingBox.min.z) + abs(mesh.geometry.boundingBox.max.z)

            mesh.geometry.scale(1/dx, 1/dy, 1/dz)
            mesh.geometry.rotateX(math.pi/2)

        self.instantiate_mesh(mesh)

        return mesh


evergreen_material_foliage= Material2InstancedMaterial(THREE.MeshLambertMaterial( {
            'color': 0x008800,
            'wireframe': False,
            'name':"evergreen_material_foliage"} ))

evergreen_texture = Material2InstancedMaterial(THREE.MeshBasicMaterial({
    'side': THREE.DoubleSide,
    'transparent': True,
    'depthWrite': True,
    'depthTest': True,
    'wireframe': False,
    'alphaTest': 0.1,
    'map': THREE.ImageUtils.loadTexture('img/evergreen.png'),
    'name':"evergreen_texture"} ))


class Evergreen(Scenery):
    """
    * @class Evergreen: inerite from Scenary
    * @param {float} radius
    * @param {float} height
    * @returns {Tree}
    """
    def __init__(self, radius, height, position):
        if radius is None:
            return

        # the width of the tree is actually twice the radius
        super().__init__(position, radius*2, "evergreen")

        self.radius = radius
        self.height = height
        self.type = 2

        footprint = FootPrint(
                THREE.Vector2(-0.5, -0.5),
                THREE.Vector2(1, 1),
                0.5,
                position,
                10,
                self
                )
        self.footprints.append(footprint)
        
    def _build(self, radius, height, trunk, foliage, level):
        """
         * 
         * @param {type} radius
         * @param {type} height
         * @param {type} trunk
         * @param {type} foliage
         * @param {type} level
         * @returns {THREE.Group|Evergreen.prototype._build.m_tree|.Object@call;create._build.m_tree}
        """
        if height < 2:
            height = 2

        g_trunk = THREE_Utils.cylinder(0.2, height/3, trunk)
        colors = g_trunk.attributes.position.clone()
        for i in range(0, len(colors.array), 3):
            colors.array[i] = 0.54
            colors.array[i + 1] = 0.27
            colors.array[i + 2] = 0.07
        g_trunk.addAttribute('color', colors)  # per mesh translation

        g_foliage = THREE_Utils.cone(radius, height, foliage)
        g_foliage.translate(0, 0, height/3)
        colors = g_foliage.attributes.position.clone()
        for i in range(0, len(colors.array), 3):
            colors.array[i] = 0.0
            colors.array[i + 1] = 1.0
            colors.array[i + 2] = 0.0
        g_foliage.addAttribute('color', colors)  # per mesh translation

        geometry = THREE.BufferGeometry()
        mergeGeometries([g_trunk, g_foliage], geometry)

        return THREE.Mesh(geometry, None)

    def build_mesh(self, level):
        """
         * 
         * @param {type} level
         * @returns {Evergreen.prototype.build_mesh.mesh|THREE.Group|THREE.Mesh|.Object@call;create.build_mesh.mesh}
        """
        # height = self.height
        # radius = self.radius
        height = 1
        radius = 0.5

        if level == 0:
            return None
        elif level == 1:
            mesh = self._build(radius, height, 3, 3, level)
        elif level == 2:
            mesh = self._build(radius, height, 3, 6, level)
        elif level == 3:
            mesh = self._build(radius, height, 4, 12, level)
        elif level == 4:
            asset = Asset("tree", "models/pine/4/pine")
            mesh = asset.mesh.children[0]
            mesh.geometry.computeBoundingBox()
            mesh.material.normalMap = mesh.material.bumpMap
            mesh.material.bumpMap = None
            dx = abs(mesh.geometry.boundingBox.min.x) + abs(mesh.geometry.boundingBox.max.x)
            dy = abs(mesh.geometry.boundingBox.min.y) + abs(mesh.geometry.boundingBox.max.y)
            dz = abs(mesh.geometry.boundingBox.min.z) + abs(mesh.geometry.boundingBox.max.z)

            mesh.geometry.scale(1/dx, 1/dy, 1/dz)
            mesh.geometry.rotateX(math.pi/2)
        else: # maximum details
            asset = Asset("tree", "models/pine/pine")
            mesh = asset.mesh.children[0]
            mesh.geometry.computeBoundingBox()
            mesh.material.normalMap = mesh.material.bumpMap
            mesh.material.bumpMap = None
            dx = abs(mesh.geometry.boundingBox.min.x) + abs(mesh.geometry.boundingBox.max.x)
            dy = abs(mesh.geometry.boundingBox.min.y) + abs(mesh.geometry.boundingBox.max.y)
            dz = abs(mesh.geometry.boundingBox.min.z) + abs(mesh.geometry.boundingBox.max.z)

            mesh.geometry.scale(1/dx, 1/dy, 1/dz)
            mesh.geometry.rotateX(math.pi/2)

        self.instantiate_mesh(mesh)

        return mesh


"""
 * 
 * @param {array} trees
 * @param {Terrain} terrain
 * @returns {undefined}
"""


def forest_create(trees, terrain):
    # ratio conversion from indexmap coordinates to world oordinates
    ratio = terrain.onscreen / terrain.indexmap.size
    size = terrain.indexmap.size

    # check the indexmap for cell with code
    list = []
    v = THREE.Vector2()

    for y in range(size):
        for x in range(size):
            v.x = x
            v.y = y
            if terrain.isForest_indexmap(v):
                create_forest_cell(list, x, y)

    progress(33, 100, "Build forest")

    # move the trees depending on their size
    # the higher the wider exclusion zone
    moved = 0
    for j in range(len(list)):
        moved += pushMyNeighbours(list, list[j])

    progress(66, 100, "Build forest")

    # convert the relocated trees to tree objects
    for obj in list:
        # ignore object outside of the map
        p = obj['xy']

        if not terrain.isOnIndexMap(p):
            continue

        # ignore the tree if there is no forest tile on the indexmap
        if not terrain.isForest_indexmap(p):
            continue

        t = 0
        if Config['pseudo_random']:
            t = Terrain.myrandom.random()
        else:
            t = random.random()

        # convert from heightmap coordinate to world coordinate
        hm = terrain.indexmap2heighmap(p)
        if hm.x < 0 or hm.y < 0 or hm.x >= terrain.size or hm.y >= terrain.size:
            continue

        z = terrain.get(hm.x, hm.y)

        # ignore the tree if there is a road or a river on the heightmap
        if terrain.isRiverOrRoad_heightmap(hm):
            continue

        # // check the terrain is not too steep at that point
        normal = terrain.normalMap.bilinear(hm.x, hm.y)
        if normal.z < 0.75:
            continue

        world = terrain.map2screen(hm)

        # convert the indexmap radius to a world radius
        obj['height'] *= ratio
        obj['radius'] *= ratio
        position = THREE.Vector3(world.x, world.y, z)

        if t > 0.5:
            tree = Evergreen(obj['radius'], obj['height'], position)
        else:
            tree = Tree(obj['radius'], obj['height'], position)

        trees.append(tree)

    progress(100, 100, "Build forest")
    progress(0, 0, "Build forest")


def create_forest_cell(list_of_trees, x, y):
    """
    *
    * @param {type} list
    * @param {type} start
    * @param {type} width
    * @returns {undefined}
    """

    # get the center of cell on the world
    cell_center = THREE.Vector2(x + 0.5, y + 0.5)

    # initialize the pseudo random
    #    norandom = noRandom(start.x  + start.y*5)
    #    perlin = SimplexNoise()

    # put a tree randomly in the cell
    for i in range(2):
        if Config['pseudo_random']:
            d = Terrain.myrandom.random() - 0.5
            h = Terrain.myrandom.random() / 2 + 0.5
        else:
            d = random.random() - 0.5
            h = random.random() / 2 + 0.5

        p = THREE.Vector2(cell_center.x + d, cell_center.y + d)

        # first tree is the highest
        list_of_trees.append({
            'xy': p,
            'height': h,
            'radius': h / 2,
            'exclusion': h / 2  # tree exclusion zone
        })


def pushMyNeighbours(list, current):
    """
    * @description push the neighbours away from each tree
    * @param {type} list
    * @param {type} current
    * @returns {undefined}
    """

    moved = 0
    todo = []
    done = []

    todo.append(current)
    while len(todo) > 0:
        current = todo.pop()
        done.append(current)

        # build the list of my neighbours
        # find all trees overlapping based on the exclusion zone defined by their height
        neighbours = []
        for neighbour in list:
            if neighbour == current:
                continue

            d = current['xy'].distanceTo(neighbour['xy'])  # distance between the 2 trees
            if d < current['exclusion'] + neighbour['exclusion']:
                # trees overlap
                neighbours.append(neighbour)

        # push each neighbours away
        for neighbour in neighbours:
            # ignore trees that are on the history
            found = False
            for i in done:
                if i == neighbour:
                    found = True
                    break

            if found:
                continue

            toTree = THREE.Vector2()
            toTree.subVectors(neighbour['xy'], current['xy'])
            toTree.normalize()

            d = neighbour['xy'].distanceTo(current['xy'])
            t = neighbour['exclusion'] + current['exclusion']

            correction = t - d

            if abs(correction) > 0.01:
                toTree.multiplyScalar(correction)
                neighbour['xy'].add(toTree)
                #        draw(list)
                #    ctx.fillStyle = 'red'
                #                drawTree(neighbour)
                moved += 1

                todo.append(neighbour)

    return moved
