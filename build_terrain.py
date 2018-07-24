"""
"""
import sys, os.path
mango_dir = (os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
+ '/THREEpy/')
sys.path.append(mango_dir)

from datetime import datetime

from THREE import *
from THREE.pyOpenGL.pyOpenGL import *
from THREE.loaders.BinaryLoader import *

from Scenery import *
from city import *

from Terrain import *
from Forest import *

import build.terrain as build_terrain


def build():
    terrain = Terrain.Terrain(512, 25, 512)
    terrain.init()

    if not Config['terrain']['flat']:
        build_terrain.perlin_generate(terrain)
        build_terrain.build_normalmap(terrain)

    terrain.build()

    if Config['terrain']['roads']:
        build_terrain.build_roads(terrain)

    if Config['terrain']['city']:
        city_create(terrain)

    if Config['terrain']['forest']:
        trees = []
        forest_create(trees, terrain)
        terrain.scenery.extend(trees)

    if not Config['terrain']['flat']:
        build_terrain.build_normalmap(terrain)

    build_terrain.build_mesh(terrain)
    build_terrain.build_mesh_scenery(terrain)

    terrain.dump()


if __name__ == "__main__":
    build()
