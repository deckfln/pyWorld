"""
3D Asset
"""
import os

from THREE.loaders.OBJLoader2 import *
from THREE.loaders.MTLLoader import *
from pyOpenGL.pyCache import *


class Asset:
    def __init__(self, name, file):
        self.name = name

        cache = pyCache("%s.obj" % file)
        asset = cache.load()
        if asset is None:
            f = os.path.basename(file)
            dir = os.path.dirname(file)

            mtlLoader = MTLLoader()
            mtlLoader.setPath(dir)
            materials = mtlLoader.load( "%s.mtl" % f)
            materials.preload()

            loader = OBJLoader2()
            loader.setPath(dir)
            loader.setMaterials(materials.materials)
            asset = loader.load("%s.obj" % f)
            cache.save(asset)
        else:
            asset.rebuild_id()

        self.mesh = asset

    def reset_instances(self):
        self.mesh.geometry.maxInstancedCount = 0
