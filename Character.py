"""
 * @returns {Character}
"""
import THREE

_material = THREE.MeshLambertMaterial({
    'color': 0x00ffff,
    'wireframe': False
    })


class Character:
    def __init__(self):
        bound_g = THREE.SphereBufferGeometry(1, 32, 32)
        bound = THREE.Mesh(bound_g, _material)
        
        head_g = THREE.BoxBufferGeometry(0.4, 0.4, 0.4)
        self.head = THREE.Mesh(head_g, _material)
        self.head.position.z += 0.8
        torso_g = THREE.BoxBufferGeometry(0.5, 0.5, 0.7)
        self.torso = THREE.Mesh(torso_g, _material)
        self.torso.position.z += 0.2
        
        left_arm_g = THREE.BoxBufferGeometry(0.25, 0.25, 0.7)
        left_arm_g.translate(0, 0, -0.30)
        self.left_arm = THREE.Mesh(left_arm_g, _material)
        self.left_arm.position.z += .45
        self.left_arm.position.y += .4
        
        right_arm_g = THREE.BoxBufferGeometry(0.25, 0.25, 0.7)
        right_arm_g.translate(0, 0, -0.30)
        self.right_arm = THREE.Mesh(right_arm_g, _material)
        self.right_arm.position.z += .45
        self.right_arm.position.y -= .4
        
        left_leg_g = THREE.BoxBufferGeometry(0.25, 0.25, 0.8)
        left_leg_g.translate(0, 0, -0.20)
        self.left_leg = THREE.Mesh(left_leg_g, _material)
        self.left_leg.position.z += -0.35
        self.left_leg.position.y += .15
        
        right_leg_g = THREE.BoxBufferGeometry(0.25, 0.25, 0.8)
        right_leg_g.translate(0, 0, -0.20)
        self.right_leg = THREE.Mesh(right_leg_g, _material)
        self.right_leg.position.z += -0.35
        self.right_leg.position.y -= .15
        
        self.mesh = THREE.Group()
        # //    player.add(bound)
        self.mesh.add(self.head)
        self.mesh.add(self.torso)
        self.mesh.add(self.left_arm)
        self.mesh.add(self.right_arm)
        self.mesh.add(self.left_leg)
        self.mesh.add(self.right_leg)
          
        for child in self.mesh.children:
            child.castShadow = True
            child.receiveShadow = True

        self.animate = 0
        self.animate_direction = 0.05

        self.move = THREE.Vector2()
        self.run = False

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

    def add(self, direction):
        """
         * @param {type} direction
         * @returns {undefined}
        """
        self.mesh.position.add(direction)
        self.walk()

    def sub(self, direction):
        """
         * @param {type} direction
         * @returns {undefined}
        """
        self.mesh.position.sub(direction)
        self.walk()

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
        self.animate = 0
        self.animate_direction = 0.05

    def stop(self):
        """ 
         * @returns {undefined}
        """ 
        self.left_arm.rotation.y = 0
        self.right_arm.rotation.y = 0
        self.left_leg.rotation.y = 0
        self.right_leg.rotation.y = 0

    def update(self, delta):
        """
         * @param {float} delta
         * @returns {undefined}
        """
        if self.animate < -0.6:
            self.animate_direction = 0.05
        elif self.animate > 0.6:
            self.animate_direction = -0.05
        
        self.animate += self.animate_direction
        
        self.left_arm.rotation.y = self.animate
        self.right_arm.rotation.y = -self.animate
        self.left_leg.rotation.y = -self.animate
        self.right_leg.rotation.y = self.animate
