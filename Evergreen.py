"""

"""
from Scenery import *
from Footprint import *


class Evergreen(Scenery):
    """
    * @class Evergreen: inerite from Scenary
    * @param {float} radius
    * @param {float} height
    * @returns {Tree}
    """

    def __init__(self, radius, height, position):
        if radius is None:
            return

        # the width of the tree is actually twice the radius
        super().__init__(position, radius * 2, "evergreen")

        self.radius = radius
        self.height = height
        self.type = 2

        footprint = FootPrint(
            THREE.Vector2(-0.5, -0.5),
            THREE.Vector2(1, 1),
            0.5,
            position,
            10,
            self
        )
        self.footprints.append(footprint)

    def _build(self, radius, height, trunk, foliage, level):
        """
         *
         * @param {type} radius
         * @param {type} height
         * @param {type} trunk
         * @param {type} foliage
         * @param {type} level
         * @returns {THREE.Group|Evergreen.prototype._build.m_tree|.Object@call;create._build.m_tree}
        """
        if height < 2:
            height = 2

        g_trunk = THREE_Utils.cylinder(0.2, height / 3, trunk)
        colors = g_trunk.attributes.position.clone()
        for i in range(0, len(colors.array), 3):
            colors.array[i] = 0.54
            colors.array[i + 1] = 0.27
            colors.array[i + 2] = 0.07
        g_trunk.addAttribute('color', colors)  # per mesh translation

        g_foliage = THREE_Utils.cone(radius, height, foliage)
        g_foliage.translate(0, 0, height / 3)
        colors = g_foliage.attributes.position.clone()
        for i in range(0, len(colors.array), 3):
            colors.array[i] = 0.0
            colors.array[i + 1] = 1.0
            colors.array[i + 2] = 0.0
        g_foliage.addAttribute('color', colors)  # per mesh translation

        geometry = THREE.BufferGeometry()
        mergeGeometries([g_trunk, g_foliage], geometry)

        return THREE.Mesh(geometry, None)
