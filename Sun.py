"""

"""

import math

from THREE.math.Color import *
from THREE.lights.DirectionalLight import *
from THREE.materials.MeshBasicMaterial import *
from Config import *


class Sun:
    def __init__(self):
        self.time = 0
        self.ambientCoeff = 0.3
        self.light = THREE.DirectionalLight(0xffffff, 1)
        self.ambient = THREE.AmbientLight(0xffffff, self.ambientCoeff)
        self.color = self.light.color
        self.ambient.color = self.light.color

        self.light.position.set(100, 100, 100)

        self.material = THREE.MeshBasicMaterial({
            'color': 0xffffff
        })

        self.temperatures = [THREE.Color(0, 0, 85/255),        # blue night
                             THREE.Color(255/255, 255/255, 200/255),     # yellow sunrise
                             THREE.Color(255/255, 255/255, 255/255),     # white daylight
                             THREE.Color(250/255, 214/255, 165/255),     # orange sunset
                             THREE.Color(0, 0, 85/255)         # blue night
                             ]

    def add2scene(self, scene):
        scene.add(self.ambient)
        scene.add(self.light)

    def move(self, p):
        # "sun" directional vector
        sun_vector = THREE.Vector3(0, 256 * math.cos(p.hour), 256 * math.sin(p.hour))

        # define the shadowmap camera target, 10 units ahead of the player position along the view sight
        line_of_sight = p.player.direction.clone().multiplyScalar(24).add(p.player.position)
        # hm = p.terrain.screen2map(line_of_sight)
        line_of_sight.z = p.player.position.z  # p.terrain.get(hm.x, hm.y)
        # p.sun.target.position.copy(line_of_sight)
        # p.sun.target.updateMatrixWorld()

        if Config['shadow']['debug']:
            p.debug.position.copy(line_of_sight)

        # move back the sun direction to set the shadow camera position
        line_of_sight.add(sun_vector)
        # p.sun.shadow.camera.position.copy(line_of_sight)
        p.sun.light.position.copy(line_of_sight)

        # need to update the projectmatric, don't know why
        # if the camera herlper is turned on, it does the update
        # p.sun.shadow.camera.updateProjectionMatrix()
        # p.sun.shadow.camera.updateMatrixWorld()

        # change sun color temperature
        # 0           pi/6        2pi/6--4pi/6      5pi/6       pi
        # (0,0,85)   (255,255,200)      (white)         (250,214,165)    (0, 0, 85)
        d = p.hour * 4 / math.pi    # bring the hour from 0..pi to 0..4
        start_color = self.temperatures[int(d)]
        target_color = self.temperatures[int(d) + 1]

        d = d - int(d)      # bring the position between 3 and 4
        delta = THREE.Color().subColors(target_color, start_color)
        delta.multiplyScalar(d)
        delta.add(start_color)
        self.color.copy(delta)
        """
        if p.hour < math.pi/3:
            r = p.hour*(1.0 - 250/255)/(math.pi/3)
            g = p.hour*(1.0 - 214/255)/(math.pi/3)
            b = p.hour*(1.0 - 165/255)/(math.pi/3)
            self.color.setRGB(250/255 + r, 214/255 + g, 165/255 + b)   # sunrise color
        elif p.hour > math.pi*2/3:
            delta = math.pi/3 - (p.hour - math.pi*2/3)
            r = delta*(1.0 - 250/255)/(math.pi/3)
            g = delta*(1.0 - 214/255)/(math.pi/3)
            b = delta*(1.0 - 165/255)/(math.pi/3)
            self.color.setRGB(250/255 + r, 214/255 + g, 165/255 + b)   # sunset color
        else:
            self.color.setRGB(1.0, 1.0, 1.0)   # midday color
        """