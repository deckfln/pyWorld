"""
 @class Scenary: Upper class for all scenary objects
 @returns {Scenery}
"""
from Config import*

from THREE.loaders.Loader import *
from THREE.objects.Group import *
from THREE.javascriparray import *
from Assets import *


class Scenery:
    """
    Forest = 3
    Grass = 0
    """
    def __init__(self, position, scale, name):
        self.position = position
        self.footprints = []
        self.type = None
        self.name = name
        self.scale = scale

    def rotateZ(self, r):
        self.mesh.geometry.rotateZ(r)    

    def translate(self, v):
        self.mesh.position.copy(v)
        
        # translate the footprints
        for footprint in self.footprints:
            footprint.translate(v)

    def AxisAlignedBoundingBoxes(self, center):
        aabbs = THREE.Group()
        center.z = self.position.z
        for footprint in self.footprints:
            aabbs.add(footprint.AxisAlignedBoundingBox(center))

        return aabbs
