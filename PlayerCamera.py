"""
"""
import THREE
from THREE.Camera import *

from Config import *


class PlayerCamera:
    def __init__(self):
        self.position = THREE.Vector3()
        self.controls = None
        self.lookAt = THREE.Vector3()
        self.updated = False

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
        shoulder = player.position.clone()
        behind = shoulder.clone()
        distance = player.direction.clone()
        distance.multiplyScalar(20)
        l1 = distance.length()
        behind.sub(distance)
        behind.z += 2    # over the shoulder
        
        # check if there is an obstacle on our line of sight
        # move the camera near the player 
        d = behind.clone().sub(shoulder)
        p = THREE.Vector3()
        p1 = THREE.Vector3()
        
        i = 0.05
        while i < 1.05:
            p1.copy(d)
            p1.multiplyScalar(i)
            p.copy(shoulder)
            p.add(p1)

            hm = terrain.screen2map(p)
            ground = terrain.getV(hm)
            if p.z - ground < i:    # the nearest to the camera the more over the ground
                p.z = ground + i    # to avoid clipping of the terrain
                
                # compute a line of sight
                p.sub(shoulder)
                l = p.length()
                l = l1 / l
                p.multiplyScalar(l)
                
                behind.copy(shoulder).add(p)
                d.copy(p)
                
            i += 0.05

        self.updated = True

        if Config['camera']['debug']:
            self.line.geometry.vertices[0].copy(shoulder)
            self.line.geometry.vertices[1].copy(behind)
            self.line.geometry.verticesNeedUpdate = True
        
        if Config['player']['tps']:
            self.position.copy(behind)
            self.lookAt.copy(shoulder)

    def display(self, camera):
        if self.updated:
            camera.position.copy(self.position)
            camera.controls.target.copy(self.lookAt)
            camera.up.set(0, 0, 1)
            self.updated = False
