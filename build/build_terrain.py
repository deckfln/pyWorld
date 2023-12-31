"""
"""
import sys, os.path
mango_dir = (os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')) + '/THREEpy/')
sys.path.append(mango_dir)

from TerrainBuilder import *


def build():
    terrain = TerrainBuilder(Config["terrain"])
    terrain.init()

    if not Config['terrain']['flat']:
        terrain.perlin_generate()
        terrain.build_normalmap()

    terrain.buildIndexmap()

    if Config['terrain']['roads']:
        terrain.build_roads()

    if Config['terrain']['city']:
        terrain.city()

    if Config['terrain']['forest']:
        terrain.forest()

    if not Config['terrain']['flat']:
        terrain.build_normalmap()

    terrain.build_tiles_datamaps()

    #terrain.build_mesh()
    terrain.build_mesh_scenery()

    terrain.dump()


if __name__ == "__main__":
    build()
