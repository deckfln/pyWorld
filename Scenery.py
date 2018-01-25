"""
 @class Scenary: Upper class for all scenary objects
 @returns {Scenery}
"""
from THREE.Group import *


class Scenery:
    Forest = 3
    Grass = 0
    
    def __init__(self, position, radius):
        # @property {TREE.Vector3} position
        self.position = position
        
        # @property {double} radius
        self.radius = radius

        # @property {THREE.Mesh} name description
        self.mesh = None
        
        # @property {Array of FootPrint} name description
        self.footprints = []

        self.type = None

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
