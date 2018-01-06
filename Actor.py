"""
 * @returns {Character}
"""
import THREE
from THREE.loaders.ColladaLoader2 import *
from quadtree import _BoundingSphereMaterial
from Config import *
import math


_material = THREE.MeshLambertMaterial({
    'color': 0x00ffff,
    'wireframe': False
    })


class Actor:
    def __init__(self, file=None):
        self.animate = 0
        self.animate_direction = 0.05
        self.current_animation = None
        self.clip = None

        self.run = False
        self.actor_mesh = None

        if file:
            loader = ColladaLoader()
            # loader.options.convertUpAxis = True
            collada  = loader.load(file)
            self.animations = collada.animations
            self.mesh = collada.scene
            self.mesh.rotation.x = -math.pi/64
            self.mesh.rotation.z = math.pi/2
            self.basic = None
            self.clips = {}

            # find the walking and idle animations
            self.mixer = THREE.AnimationMixer(self.mesh)
            for i in range(len(self.animations)):
                animation = self.animations[i]
                self.clips[animation.name] = i

            # generate the actions
            self.clips["walking"] = self.mixer.clipAction(self.animations[self.clips["walking"]])
            self.clips["idle"] = self.mixer.clipAction(self.animations[self.clips["lookaround"]])

            # find the mesh and get the boundingsphere
            for child in self.mesh.children:
                if child.my_class(isSkinnedMesh):
                    self.actor_mesh = child
                    child.geometry.computeBoundingSphere()
                    child.castShadow = True
                    child.receiveShadow = True
                    # * @property {number} radius face the player is moving to
                    self.radius = child.geometry.boundingSphere.radius
                    self.center = child.geometry.boundingSphere.center.clone()

                    # don't forget we rotate the model
                    z = self.center.z
                    self.center.z = self.center.y
                    self.center.y = z

        else:
            self.animations = None
            self.action = None
            bound_g = THREE.SphereBufferGeometry(1, 32, 32)
            bound = THREE.Mesh(bound_g, _material)

            head_g = THREE.BoxBufferGeometry(0.4, 0.4, 0.4)
            self.basic.head = THREE.Mesh(head_g, _material)
            self.basic.head.position.z += 0.8
            torso_g = THREE.BoxBufferGeometry(0.5, 0.5, 0.7)
            self.basic.torso = THREE.Mesh(torso_g, _material)
            self.basic.torso.position.z += 0.2

            left_arm_g = THREE.BoxBufferGeometry(0.25, 0.25, 0.7)
            left_arm_g.translate(0, 0, -0.30)
            self.basic.left_arm = THREE.Mesh(left_arm_g, _material)
            self.basic.left_arm.position.z += .45
            self.basic.left_arm.position.y += .4

            right_arm_g = THREE.BoxBufferGeometry(0.25, 0.25, 0.7)
            right_arm_g.translate(0, 0, -0.30)
            self.basic.right_arm = THREE.Mesh(right_arm_g, _material)
            self.basic.right_arm.position.z += .45
            self.basic.right_arm.position.y -= .4

            left_leg_g = THREE.BoxBufferGeometry(0.25, 0.25, 0.8)
            left_leg_g.translate(0, 0, -0.20)
            self.basic.left_leg = THREE.Mesh(left_leg_g, _material)
            self.basic.left_leg.position.z += -0.35
            self.basic.left_leg.position.y += .15

            right_leg_g = THREE.BoxBufferGeometry(0.25, 0.25, 0.8)
            right_leg_g.translate(0, 0, -0.20)
            self.basic.right_leg = THREE.Mesh(right_leg_g, _material)
            self.basic.right_leg.position.z += -0.35
            self.basic.right_leg.position.y -= .15

            self.mesh = THREE.Group()

            # //    player.add(bound)
            self.mesh.add(self.basic.head)
            self.mesh.add(self.basic.torso)
            self.mesh.add(self.basic.left_arm)
            self.mesh.add(self.basic.right_arm)
            self.mesh.add(self.basic.left_leg)
            self.mesh.add(self.basic.right_leg)

            for child in self.mesh.children:
                child.castShadow = True
                child.receiveShadow = True

        if Config["player"]["debug"]["boundingsphere"]:
            bs = THREE.SphereBufferGeometry(self.radius, 16, 16)
            ms = THREE.Mesh(bs, _BoundingSphereMaterial)
            ms.position = self.center
            self.mesh.add(ms)

        self.clip = self.clips["idle"]
        self.clip.play()
        self.current_animation = 'idle'

    def set(self, position):
        """
         * @param {type} position
         * @returns {undefined}
        """
        self.mesh.position.copy(position)

    def add2scene(self, scene):
        """ 
         * @param {type} scene
         * @returns {undefined}
        """
        scene.add(self.mesh)

    def setZ(self, z):
        """    
         * @param {type} z
         * @returns {undefined}
        """
        self.mesh.position.z = z

    def add_rotation(self, r):
        """
         * @param {type} r
         * @returns {undefined}
        """
        self.mesh.rotation.z += r

    def get_position(self):
        """ 
         * @returns {Character.mesh.position}
        """
        return self.mesh.position

    def start(self):
        """
         * @returns {undefined}
        """
        if self.current_animation == 'walking':
            return

        if self.basic:
            self.animate = 0
            self.animate_direction = 0.05
        else:
            self.clip.stop()
            self.clip = self.clips['walking']
            self.clip.play()
            # self.clip.crossFadeTo(self.clips["walking"], 0)

        self.current_animation = 'walking'

    def stop(self):
        """ 
         * @returns {undefined}
        """
        if self.current_animation == 'idle':
            return

        if self.basic:
            self.basic.left_arm.rotation.y = 0
            self.basic.right_arm.rotation.y = 0
            self.basic.left_leg.rotation.y = 0
            self.basic.right_leg.rotation.y = 0
        else:
            self.clip.stop()
            self.clip = self.clips['idle']
            self.clip.play()

            #self.clip.crossFadeTo(self.clips["idle"], 0)

        self.current_animation = 'idle'

    def update(self, delta):
        """
         * @param {float} delta
         * @returns {undefined}
        """
        if self.basic:
            if self.animate < -0.6:
                self.animate_direction = 0.05
            elif self.animate > 0.6:
                self.animate_direction = -0.05

            self.animate += self.animate_direction

            self.basic.left_arm.rotation.y = self.animate
            self.basic.right_arm.rotation.y = -self.animate
            self.basic.left_leg.rotation.y = -self.animate
            self.basic.right_leg.rotation.y = self.animate
        else:
            self.mixer.update(delta)
