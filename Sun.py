"""

"""

from THREE.Color import *
from THREE.DirectionalLight import *
from THREE.MeshBasicMaterial import *
from Config import *


class Sun:
    def __init__(self):
        self.time = 0
        self.color = THREE.Color(250/255, 214/255, 165/255)   # sunset color
        self.ambientCoeff = 0.3
        self.light = THREE.DirectionalLight(0xffffff, 1)
        self.light.position.set(100, 100, 100)

        self.material = THREE.MeshBasicMaterial({
            'color': 0xffffff
        })

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

        # change sun temperature
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
