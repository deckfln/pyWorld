"""
Asset to store a house
"""

from Scenery import *
from Footprint import *


class House(Scenery):
    """

    """
    def __init__(self, width, len, height, alpha, position):
        if width is None:
            return

        radius = math.sqrt(width*width + len*len)/2
        super().__init__(position, width, "house")

        self.radius = radius
        self.type = 0
        self.width = width
        self.height = height
        self.len = len
        self.rotation = alpha

        footprint = FootPrint(
                THREE.Vector2(-width/2, -len/2),
                THREE.Vector2(width, len),
                radius,
                position,
                10,
                self
                )

        footprint.rotate(alpha)
        self.footprints.append(footprint)
