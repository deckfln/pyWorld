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


"""
* @class Tree: inerite from Scenary
* @param {float} radius
* @param {float} height
* @returns {Tree}
"""

tree_material_trunk= THREE.MeshLambertMaterial( {
            'color': 0x8B4513,
            'wireframe': False,
            'name':"tree_material_trunk"})

tree_material_foliage= THREE.MeshLambertMaterial( {
            'color': 0x00ff00,
            'wireframe': False,
            'name':"tree_material_foliage"} )
tree_texture = THREE.MeshBasicMaterial({
    'side': THREE.DoubleSide,
    'transparent': True,
    'depthWrite': True,
    'depthTest': True,
    'wireframe': False,
    'alphaTest': 0.1,
    'map': THREE.ImageUtils.loadTexture('img/tree.png'),
    'name':"tree_texture"
})


class Tree(Scenery):
    def __init__(self, radius, height, position):
        self.radius = radius
        self.height = height
        super().__init__(position, radius)
        
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
         * 
         * @param {type} radius
         * @param {type} height
         * @param {type} trunk
         * @param {type} foliage
         * @param {type} level
         * @returns {THREE.Group|Tree.prototype._build.m_tree|.Object@call;create._build.m_tree}
        """
        material1 = tree_material_trunk
        material2 = tree_material_foliage
        # if Config['terrain']['debug']['lod']:
        #    material1 = lod_materials[level]
        #    material2 = material1

        g_trunk = THREE_Utils.cylinder(0.5, height/1.5, trunk)
        m_trunk = THREE.Mesh( g_trunk, material1 )

        g_foliage = THREE.SphereBufferGeometry(radius, foliage, foliage)
        g_foliage.translate(0, 0, height/3 + radius)
        m_foliage = THREE.Mesh(g_foliage, material2)

        m_tree = THREE.Group()
        m_tree.add(m_trunk)
        m_tree.add(m_foliage)

        if Config['player']['debug']['collision']:
            aabb = THREE.BoxHelper(m_trunk)
            m_tree.add(aabb)
        
        return m_tree
    
    def build_mesh(self, level):
        """
         * 
         * @param {type} level
         * @returns {Tree.prototype.build_mesh.mesh|THREE.Group|Tree.prototype.build_mesh.m_tree|.Object@call;create.build_mesh.m_tree|THREE.Mesh|.Object@call;create.build_mesh.mesh}
        """
        height = self.height
        radius = self.radius
        mesh = None

        if level == 0:
            return None
        elif level == 1:
            mergedGeometry = THREE.Geometry()
            pane1 = THREE.PlaneGeometry(radius*3, radius*2 + height/3, 1 , 1)
            pane1.rotateX(math.pi/2)
            pane1.translate(0, 0, (radius*2 + height/3)/2)
            mergedGeometry.merge(pane1)
            pane1.rotateZ(math.pi/2)
            mergedGeometry.merge(pane1)

            material = tree_texture
            # if Config['terrain']['debug']['lod']:
            #    material = lod_materials[level]

            mesh = THREE.Mesh(mergedGeometry, material)
        elif level == 2:
            mesh = self._build(radius, height, 3, 8, level)
        elif level == 3:
            mesh = self._build(radius, height, 4, 16, level)
        elif level == 3:
            mesh = self._build(radius, height, 8, 32, level)
        else:    # maximum details
            mesh = self._build(radius, height, 16, 64, level)
            self.mesh = mesh
        
        if mesh:
            mesh.position.copy(self.position)
        
        return mesh

"""
* @class Evergreen: inerite from Scenary
* @param {float} radius
* @param {float} height
* @returns {Tree}
"""
evergreen_material_foliage= THREE.MeshLambertMaterial( {
            'color': 0x008800,
            'wireframe': False,
            'name':"evergreen_material_foliage"} )

evergreen_texture = THREE.MeshBasicMaterial({
    'side': THREE.DoubleSide,
    'transparent': True,
    'depthWrite': True,
    'depthTest': True,
    'wireframe': False,
    'alphaTest': 0.1,
    'map': THREE.ImageUtils.loadTexture('img/evergreen.png'),
    'name':"evergreen_texture"} )

class Evergreen(Scenery):
    def __init__(self, radius, height, position):
        self.radius = radius
        self.height = height
        super().__init__(position, radius)
        
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
        material1 = tree_material_trunk
        material2 = evergreen_material_foliage
        #if Config['terrain']['debug']['lod']:
        #    material1 = lod_materials[level]
        #    material2 = material1

        g_trunk = THREE_Utils.cylinder(0.5, height/3, trunk)
        m_trunk = THREE.Mesh( g_trunk, material1 )

        foliage_height = height
        if foliage_height < 2:
            foliage_height = 2
            
        """
        g_foliage = THREE.CylinderBufferGeometry(radius, 0,foliage_height, foliage, 1, true)
        g_foliage.rotateX(-Math.PI/2)
        """
        g_foliage = THREE_Utils.cone(radius, foliage_height, foliage)
        g_foliage.translate(0,0,height/3)
        m_foliage = THREE.Mesh( g_foliage, material2 )

        m_tree = THREE.Group()
        m_tree.add(m_trunk)
        m_tree.add(m_foliage)
        
        if Config['player']['debug']['collision']:
            aabb = THREE.BoxHelper(m_trunk)
            m_tree.add(aabb)
            
        return m_tree
        
    def build_mesh(self, level):
        """
         * 
         * @param {type} level
         * @returns {Evergreen.prototype.build_mesh.mesh|THREE.Group|THREE.Mesh|.Object@call;create.build_mesh.mesh}
        """
        height = self.height
        radius = self.radius
        mesh = None

        if level == 0:
            mesh = None
        elif level == 1:
            mergedGeometry = THREE.Geometry()
            pane1 = THREE.PlaneGeometry(radius*3, height + height/3, 1 , 1)
            pane1.rotateX(math.pi/2)
            pane1.translate(0, 0, (height + height/3)/2)
            mergedGeometry.merge(pane1)
            pane1.rotateZ(math.pi/2)
            mergedGeometry.merge(pane1)

            material = evergreen_texture
            # if Config['terrain']['debug']['lod']:
            #    material = lod_materials[level]

            mesh = THREE.Mesh(mergedGeometry, material)
        elif level == 2:
            mesh = self._build(radius, height, 3, 3, level)
        elif level == 3:
            mesh = self._build(radius, height, 4, 4, level)
        elif level == 4:
            mesh = self._build(radius, height, 8, 8, level)
        else: # maximum details
            mesh = self._build(radius, height, 16, 16, level)
            self.mesh = mesh
            
        if mesh:
            mesh.position.copy(self.position)
            
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
