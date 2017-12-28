"""
 * @class Player
 * @param {THREE.Vector3} position
 * @param {THREE.scene} scene
 * @param {Heightmap} heightmap
 * @returns {Player}
"""
import math
import THREE
from Character import *
from Config import *
from Footprint import *


class Player(Character):
    def __init__(self, position, scene, heightmap):
        super().__init__()

        # @property { string } status display the object status
        self.status = "drop"

        # * @property {number} radius face the player is moving to
        self.radius = 1

        # * @property {THREE.Vector2} position position of the player
        self.position = position

        # * @property {THREE.Vector3} direction face the player is moving to
        self.direction = THREE.Vector3(0.6, 0, 0)

        # * @property {THREE.Vector3} rotation_speed direction face the player is moving to
        self.rotation_speed = math.pi/128
        self.rotation = 0

        # * @property {number} heightmap
        self.heightmap = heightmap

        # * @property {string} animation
        self.animation = "stop"

        # * @property {THREE.Scene} scene
        self.scene = scene
        
        # pre-compute the bounding sphere
        #    player.geometry.computeBoundingSphere()
        #    player.geometry.boundingSphere.center.set(position.x, position.y, position.z)
        self.set(position)
        self.setZ()
        self.frustumCulled = False
        
        # * @property {type} footprint
        self.footprint = FootPrint(
                THREE.Vector2(-self.radius/2, -self.radius/2),
                THREE.Vector2(self.radius, self.radius),
                self.radius/2,
                THREE.Vector2(0, 0)
        )
        
        if Config['player']['debug']['direction']:
            # * @property {type} helper
            self.helper = THREE.ArrowHelper(THREE.Vector3(1, 0, 0), self.get_position(), 3, 0xf0000f)

        if Config['player']['debug']['collision']:
            # * @property {type} aabb Axis Aligned Bounding Box of the player
            aabb = THREE.BoxHelper(self.mesh)
            positions = aabb.geometry.attributes.position.array
            positions[0] = self.footprint.p[3].x;        positions[1] = self.footprint.p[3].y
            positions[3] = self.footprint.p[2].x;        positions[4] = self.footprint.p[2].y
            positions[6] = self.footprint.p[0].x;        positions[7] = self.footprint.p[0].y
            positions[9] = self.footprint.p[1].x;        positions[10] =self.footprint.p[1].y
            positions[12]= self.footprint.p[3].x;        positions[13] =self.footprint.p[3].y
            positions[15]= self.footprint.p[2].x;        positions[16] =self.footprint.p[2].y
            positions[18]= self.footprint.p[0].x;        positions[19] =self.footprint.p[0].y
            positions[21]= self.footprint.p[1].x;        positions[22] =self.footprint.p[1].y
            
            self.aabb = aabb
            self.aabb_z = position.z
            
            # * @property {type} ortho1 colisiong helpers right
            self.ortho1 = None

            # * @property {type} ortho2 colisiong helpers left
            self.ortho2 = None

            # * @property {type} last_colision
            self.last_colision = None

    def draw(self):
        """
         * @description put the player on screen
         * @returns {undefined}
        """
        self.add2scene(self.scene)
        if Config['player']['debug']['direction']:
            self.scene.add(self.helper)
        
        if Config['player']['debug']['collision']:
            self.scene.add(self.aabb)
        
        self.heightmap.draw(self.position)

    def getZ(self, position=None):
        """
         * @param {type} position
         * @returns {undefined}
        """
        if position is None:
            position = self.position

        # force the player to stick to the surface
        p = self.heightmap.screen2map(position)
        return self.heightmap.get(p.x, p.y) + self.radius
    
    def setZ(self):
        """
         * @returns {undefined}
        """
        # force the player to stick to the surface
        p = self.heightmap.screen2map(self.position)
        self.position.z = self.heightmap.get(p.x, p.y) + self.radius
        super().setZ(self.position.z)
  
    def update(self, delta, terrain, camera):
        """
         * @param {time} delta ms since last frame
         * @param {THREE.Vector2} direction
         * @param {Boolean} run
         * @returns {undefined}
        """
        run = self.run
        direction = self.move
        if direction.x == 0 and direction.y == 0:
            self.stop()
            return
        
        if direction.y == 1:
            self.turn_right(delta, run)
        elif direction.y == -1:
            self.turn_left(delta, run)

        if direction.x == 1:
            self.move_forward(delta, run)
            self.set(self.position)
            self.heightmap.draw(self.position)
            self.setZ()
        elif direction.x == -1:
            self.move_back(delta, run)
            self.set(self.position)
            self.heightmap.draw(self.position)
            self.setZ()
        
        super().update(delta)
        # TODO: get the players camera from smehwere
        camera.move(self, terrain)
 
    def move_forward(self, delta, run):
        """
         * @description move player along the direction vector
         * @param {float} delta
         * @param {Boolean} run
        """
        if self.colision(self.direction):
            return False
        
        self.start()

        # forward speed depend of the steep and the run param
        z = self.getZ()
        p = self.position.clone()
        d = self.direction.clone()
        d.multiplyScalar(delta)    # handle time
        
        # handle speed
        if run:
            d.multiplyScalar(2)
            delta *= 2
        p.add(d)
        z1 = self.getZ(p)

        if z1 -z > 0.8*delta:
            # stop in front of a cliff
            self.stop()
            return
        elif z1 - z > 0.08*delta:
            # slow down walking uphill
            p.copy(self.position)
            d.divideScalar(1.5)
            p.add(d)
        elif z1 - z < -0.08*delta:
            # spee dup walking downhill
            p.copy(self.position)
            d.multiplyScalar(1.5)
            p.add(d)
        
        self.position.copy(p)
        
        if Config['player']['debug']['direction']:
            self.helper.position.copy(p)
        if Config['player']['debug']['collision']:
            p.z -= self.aabb_z
            self.aabb.position.copy(p)
        
        return True

    def move_back(self,delta, run):
        """
         * @description move player along the direction vector
         * @param {float} delta
         * @param {boolean} run
        """
        if self.colision(self.direction.clone().negate()):
            return False
        self.start()
        
        # forward speed depend of the steep
        z = self.getZ()
        p = self.position.clone()
        d = self.direction.clone()
        d.multiplyScalar(delta)    # handle time
        if run:
            d.multiplyScalar(2)
            delta *= 2
        p.sub(d)
        z1 = self.getZ(p)

        if z1 -z > 0.8*delta:
            # stop in front of a cliff
            self.stop()
            return
 
        elif z1 - z > 0.08*delta:
            p.copy(self.position)
            d.divideScalar(1.5)
            p.sub(d)
        elif z1 - z < -0.08*delta:
            p.copy(self.position)
            d.multiplyScalar(1.5)
            p.sub(d)
        
        self.position.copy(p)
        
        if Config['player']['debug']['direction']:
            self.helper.position.copy(p)

        if Config['player']['debug']['collision']:
            p.z -= self.aabb_z
            self.aabb.position.copy(p)

        return True

    def turn_left(self,delta, run):
        """
         * @description move player along the direction vector
         * @param {float} delta
         * @param {boolean} run
        """
        rotation = self.rotation_speed*delta
        if run:
            rotation *= 2
        
        self.direction.applyAxisAngle(THREE.Vector3(0,0,1), rotation)
        self.add_rotation(rotation)

        if Config['player']['debug']['direction']:
            self.helper.rotation.z += rotation
   
    def turn_right(self,delta, run): 
        """
         * @description move player along the direction vector
         * @param {float} delta
         * @param {boolean} run
        """
        rotation = self.rotation_speed*delta
        if run:
            rotation *= 2

        self.direction.applyAxisAngle(THREE.Vector3(0,0,1), -rotation)
        self.add_rotation(-rotation)
        
        if Config['player']['debug']['direction']:
            self.helper.rotation.z -= rotation

    def get_position(self):
        return self.position

    def start(self):
        if self.animation != "walk":
            self.animation = "walk"
            super().start()

    def stop(self):
        """
        * @returns {undefined}
        """
        if self.animation != "stop":
            self.animation="stop"
            super().stop()

    def colision(self,direction):
        """
         * @param {THREE.Vector3} direction
         * @returns {Boolean}
        """
        next_position = self.position.clone().add(direction)
        footprint = self.footprint.clone(next_position)
        
        return self.heightmap.colisionObjects(footprint)