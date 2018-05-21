"""
"""
import THREE
from THREE.Camera import *

from Config import *

_p = THREE.Vector3()
_p1 = THREE.Vector3()
_p2 = THREE.Vector3()
_hm = THREE.Vector2()


class PlayerCamera:
    def __init__(self):
        self.position = THREE.Vector3()
        self.controls = None
        self.lookAt = THREE.Vector3()
        self.updated = False
        self.shoulder = THREE.Vector3()
        self.behind = THREE.Vector3()
        self.distance = THREE.Vector3()
        self.angularSpeed = 0
        self.accelerate = False

        if Config['camera']['debug']:
            material = THREE.LineBasicMaterial({
                    'color': 0x0000ff
            })

            geometry = THREE.Geometry()
            geometry.vertices.append(
                    THREE.Vector3( -10, 0, 0 ),
                    THREE.Vector3( 0, 10, 0 )
            )

            self.line = THREE.Line(geometry, material)
            self.line.frustumCulled = False

    def debug(self, scene):
        if Config['camera']['debug']:
            scene.add(self.line)

    def set_controls(self, controls):
        self.controls = controls

    def move(self, player, terrain):
        shoulder = self.shoulder
        behind = self.behind
        distance = self.distance

        shoulder.copy(player.position)
        behind.copy(shoulder)
        distance.copy(player.direction)
        distance.multiplyScalar(10)
        l1 = distance.length()
        behind.sub(distance)
        behind.z += 2    # over the shoulder
        
        # check if there is an obstacle on our line of sight
        # move the camera near the player
        d = behind.clone().sub(shoulder)

        i = 0.05
        while i < 1.05:
            _p1.copy(d)
            _p1.multiplyScalar(i)
            _p.copy(shoulder)
            _p.add(_p1)

            terrain.screen2map(_p, _hm)

            # reached heightmap limit
            if _hm.x < 0 or _hm.y < 0 or _hm.x >= terrain.size or _hm.y >= terrain.size:
                break

            ground = terrain.getV(_hm)

            if _p.z - ground < i:    # the nearest to the camera the more over the ground
                _p.z = ground + i    # to avoid clipping of the terrain
                
                # compute a line of sight
                _p.sub(shoulder)
                l = _p.length()
                l = l1 / l
                _p.multiplyScalar(l)
                
                behind.copy(shoulder).add(_p)
                d.copy(_p)
                
            i += 0.05
        self.updated = True

        if Config['camera']['debug']:
            self.line.geometry.vertices[0].copy(self.shoulder)
            self.line.geometry.vertices[1].copy(self.behind)
            self.line.geometry.verticesNeedUpdate = True
        
        if Config['player']['tps']:
            self.position.copy(self.behind)
            self.lookAt.copy(self.shoulder)

    def display(self, camera):
        """
        move the real camera to the virtual camera
        the real camera has a momentum and speedup to join the position of the virtual camera
        :param camera:
        :return:
        """
        _p.subVectors(self.position, self.lookAt)
        d = _p.length()
        _p1.subVectors(camera.position, self.lookAt).normalize().multiplyScalar(d)
        a = _p.angleTo(_p1)

        # print("angle", a)
        if a < 0.005:
            # if the 2 vectors point to the same direction
            # move straight ahead
            camera.position.copy(self.position)
            camera.controls.target.copy(self.lookAt)
            camera.up.set(0, 0, 1)
            self.angularSpeed = 0
            self.accelerate = False
        else:
            # rotate angular
            # if camera was steady, give it a kick
            if self.angularSpeed == 0:
                self.angularSpeed = 0.05
                self.accelerate = True
                # print("kick")

            _p2.subVectors(_p, _p1)
            delta = _p2.length()
            d1 = delta * self.angularSpeed
            if d1 > delta:
                self.angularSpeed = 1
                self.accelerate = False
                # print('stop')

            _p2.multiplyScalar(self.angularSpeed)
            _p.copy(_p1).add(_p2).normalize().multiplyScalar(d)

            camera.position.copy(self.lookAt).add(_p)
            _p.subVectors(camera.position, self.position)
            camera.controls.target.copy(self.lookAt)
            camera.up.set(0, 0, 1)

            # print("  ", delta, d1, self.angularSpeed, _p.length())

            if self.accelerate:
                self.angularSpeed *= 2
                # print('speed')
