"""
"""
import sys
sys.path.append('../THREEpy')

from datetime import datetime

from THREE import *
from THREE.pyOpenGL.pyOpenGL import *
from THREE.loaders.BinaryLoader import *
from terrain import *

def build():
    terrain = Terrain(512, 25, 512)
    terrain.build_normalmap()
    terrain.perl_generate()
    terrain.buildIndexMap()
    terrain.build_roads()
    terrain.build_city()
    terrain.build_mesh_scenery()
    #    terrain.buildHeightmapsLOD()
    terrain.build_normalmap()
    terrain.buildTerrainMesh()

    terrain.dump()


if __name__ == "__main__":
    build()
