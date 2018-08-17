"""

"""
from Scenery import *
from Footprint import *


class Tree(Scenery):
    """
    """
    def __init__(self, radius, height, position):
        if radius is None:
            return

        super().__init__(position, radius*2, "tree")

        self.radius = radius
        self.height = height
        self.type = 1

        footprint = FootPrint(
            THREE.Vector2(-0.5, -0.5),  # footprint of the TRUNK
            THREE.Vector2(1, 1),
            0.5,
            position,
            10,
            self
        )
        self.footprints.append(footprint)

    def _build(self, radius, height, trunk, foliage, level):
        """
        """
        g_trunk = THREE_Utils.cylinder(0.1, height/3, trunk)
        colors = g_trunk.attributes.position.clone()
        for i in range(0, len(colors.array), 3):
            colors.array[i] = 0.54
            colors.array[i + 1] = 0.27
            colors.array[i + 2] = 0.07
        g_trunk.addAttribute('color', colors)

        g_foliage = THREE.SphereBufferGeometry(radius, foliage, foliage)
        g_foliage.translate(0, 0, height/2 + height/4)
        colors = g_foliage.attributes.position.clone()
        for i in range(0, len(colors.array), 3):
            colors.array[i] = 0.0
            colors.array[i + 1] = 1.0
            colors.array[i + 2] = 0.0
        g_foliage.addAttribute('color', colors)

        geometry = THREE.BufferGeometry()
        mergeGeometries([g_trunk, g_foliage], geometry)

        return THREE.Mesh(geometry, None)

