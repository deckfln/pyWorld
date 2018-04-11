"""
"""
import THREE
from THREE.Camera import *

from Config import *

_p = THREE.Vector3()
_p1 = THREE.Vector3()
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
        if self.updated:
            camera.position.copy(self.position)
            camera.controls.target.copy(self.lookAt)
            camera.up.set(0, 0, 1)
            self.updated = False
