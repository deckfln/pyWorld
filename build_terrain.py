"""
"""
import sys
sys.path.append('../THREEpy')

from datetime import datetime

from THREE import *
from THREE.pyOpenGL.pyOpenGL import *
from THREE.loaders.BinaryLoader import *
from Terrain import *
from Forest import *
from city import *


def build():
    terrain = Terrain.Terrain(512, 25, 512)
    terrain.perl_generate()
    terrain.build_normalmap()
    terrain.buildIndexMap()
    terrain.build_roads()

    city_create(terrain)

    # trees = []
    # forest_create(trees, terrain)
    # terrain.scenery.extend(trees)

    terrain.build_normalmap()
    terrain.buildTerrainMesh()
    terrain.build_mesh_scenery()

    terrain.dump()


if __name__ == "__main__":
    build()
