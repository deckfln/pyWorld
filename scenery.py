"""
 @class Scenary: Upper class for all scenary objects
 @returns {Scenery}
"""


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


    def rotateZ(self, r):
        self.mesh.geometry.rotateZ(r)    

    def translate(self, v):
        self.mesh.position.copy(v)
        
        # translate the footprints
        for footprint in self.footprints:
            footprint.translate(v)
