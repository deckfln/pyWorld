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


def build():
    terrain = Terrain.Terrain(512, 25, 512)
    terrain.init()

    if not Config['terrain']['flat']:
        terrain.perl_generate()
        terrain.build_normalmap()

    terrain.build()

    if Config['terrain']['roads']:
        terrain.build_roads()

    if Config['terrain']['city']:
        city_create(terrain)

    if Config['terrain']['forest']:
        trees = []
        forest_create(trees, terrain)
        terrain.scenery.extend(trees)

    if not Config['terrain']['flat']:
        terrain.build_normalmap()

    terrain.buildTerrainMesh()
    terrain.build_mesh_scenery()

    terrain.dump()


if __name__ == "__main__":
    build()
