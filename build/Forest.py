"""
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
"""

from THREE import *

from Config import *
from progress import *
import Utils as THREE_Utils
import Terrain
from Utils import *
from Evergreen import *
from Tree import *


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
    normal = THREE.Vector3()

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
        if terrain.isRiverOrRoad(hm):
            continue

        # // check the terrain is not too steep at that point
        terrain.normalMap.bilinear(hm.x, hm.y, normal)
        if normal.z < 0.75:
            continue

        # if the ground is a bit steep, dig the tree more in the ground
        if normal.z < 0.98:
            z -= 0.5

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
