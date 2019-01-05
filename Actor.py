"""
 * @returns {Character}
"""
import THREE
from THREE.loaders.ColladaLoader2 import *
from quadtree import _BoundingSphereMaterial
from Config import *
import math
from THREE.pyOpenGL.pyCache import *


_material = THREE.MeshLambertMaterial({
    'color': 0x00ffff,
    'wireframe': False
    })


class _actor:
    def __init__(self, animations, scene):
        self.animations = animations
        self.scene = scene


class Actor:
    def __init__(self, cwd, file):
        self.animate = True
        self.animate_direction = 0.05
        self.current_animation = None
        self.clip = None

        self.run = False
        self.actor_mesh = None

        cache = pyCache(cwd, file)
        actor = cache.load()
        if actor is None:
            loader = ColladaLoader()
            # loader.options.convertUpAxis = True
            collada  = loader.load(file)
            actor = _actor(collada.animations, collada.scene)
            cache.save(actor)
        else:
            actor.scene.rebuild_id()

        self.animations = actor.animations
        self.mesh = actor.scene
        self.mesh.rotation.x = -math.pi/64
        self.mesh.rotation.z = math.pi/2
        self.basic = None
        self.clips = {}

        # generate the actions
        self.mixer = THREE.AnimationMixer(self.mesh)
        for i in range(len(self.animations)):
            animation = self.animations[i]
            self.clips[animation.name] = self.mixer.clipAction(self.animations[i])

        # self.clips["walking"] = self.mixer.clipAction(self.animations[self.clips["walking"]])
        # self.clips["idle"] = self.mixer.clipAction(self.animations[self.clips["lookaround"]])

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

        if Config["player"]["debug"]["boundingsphere"]:
            bs = THREE.SphereBufferGeometry(self.radius, 16, 16)
            ms = THREE.Mesh(bs, _BoundingSphereMaterial)
            ms.position = self.center
            self.mesh.add(ms)

        self.clip = self.clips["idle"]
        self.clip.play()
        self.current_animation = 'idle'
        self.position = self.mesh.position                      # position position of the player

    def set(self, position):
        """
         * @param {type} position
         * @returns {undefined}
        """
        self.position.copy(position)

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
        return self.position

    def define(self, animation):
        """

        :param animation:
        :return:
        """
        if self.current_animation == animation:
            return

        self.clip.stop()
        self.clip = self.clips[animation]
        self.clip.play()
        # self.clip.crossFadeTo(self.clips["walking"], 0)

        self.current_animation = animation

    def start(self):
        if self.current_animation == 'walking':
            return

        self.clip.stop()
        self.clip = self.clips['walking']
        self.clip.play()
        # self.clip.crossFadeTo(self.clips["walking"], 0)

        self.current_animation = 'walking'

    def stop(self):
        if self.current_animation == 'idle':
            return

        self.clip.stop()
        self.clip = self.clips['idle']
        self.clip.play()

        #self.clip.crossFadeTo(self.clips["idle"], 0)

        self.current_animation = 'idle'

    def freeze(self):
        self.animate = False

    def unfreeze(self):
        self.animate = True

    def update(self, delta):
        """
         * @param {float} delta
         * @returns {undefined}
        """
        if self.animate:
            self.mixer.update(delta)
