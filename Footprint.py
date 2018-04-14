""" 
 * @param {THREE.Vector2} topleft
 * @param {THREE.Vector2} heightwidth
 * @param {float} radius
 * @param {float} position
 * @param {Scenary} scenary
 * @returns {FootPrint}
"""
import THREE
from Config import *


class FootPrint:
    dbghelper = [None, None, None, None]

    def __init__(self, topleft=None, heightwidth=None, radius=None, position=None, height=None, scenery=None):
        if topleft is None:
            # empty creation
            self.p = [
                THREE.Vector2(),
                THREE.Vector2(),
                THREE.Vector2(),
                THREE.Vector2()
            ]

            self.polygon = [
                THREE.Vector2(),
                THREE.Vector2(),
                THREE.Vector2(),
                THREE.Vector2()
            ]
            
            self.radius = 0
            self.center = THREE.Vector2()
            self.height = 0

            return

        # * @property {array of Vector2} p Axis aligned bounding box of the footprint
        self.p = [
            THREE.Vector2(topleft.x,topleft.y).add(position),
            THREE.Vector2(topleft.x+heightwidth.x,topleft.y).add(position),
            THREE.Vector2(topleft.x,topleft.y+heightwidth.y).add(position),
            THREE.Vector2(topleft.x+heightwidth.x,topleft.y+heightwidth.y).add(position)
        ]

        # * @propery {array of Vector2} corners real corners of the box
        self.polygon = [
            self.p[0].clone(),
            self.p[1].clone(),
            self.p[3].clone(),
            self.p[2].clone()
        ]

        # * @property {bool} rotated. The footprint was rotated, so need a deeper check
        self.rotated = False

        # * @property {number} radius description
        self.radius = radius

        # * @property {THREE.Vector2} center description
        self.center = THREE.Vector2(
                topleft.x+heightwidth.x/2,
                topleft.y+heightwidth.y/2
                ).add(position)
                
        # * @property {Scenary} scenary back pointer to the object
        self.scenery = scenery

        self.height = height

    def rotate(self,angle):
        """
         * @param {type} angle
         * @returns {undefined}
        """
        # rotate the footprint
        center = self.center
        topleft = THREE.Vector2(9999,9999)
        bottomright = THREE.Vector2(-9999,-9999)
        polygon = self.polygon
        
        # rotate the corners
        # and check the corners
        for i in range(4):
            polygon[i].rotateAround(center, angle)
            
            x = polygon[i].x
            y = polygon[i].y
            
            if x < topleft.x:
                topleft.x = x
            elif x > bottomright.x:
                bottomright.x = x
                
            if y < topleft.y:
                topleft.y = y
            elif y > bottomright.y:
                bottomright.y = y
        
        self.p[0] = topleft
        self.p[3] = bottomright
        
        self.p[1].x = bottomright.x
        self.p[1].y = topleft.y
        self.p[2].x = topleft.x
        self.p[2].y = bottomright.y
        
        self.rotated = True

        """
        if Config.player.debug_collision:
            for i in range(4):
                # segment
                v0 = polygon[i];       
                v1 = polygon[(i + 1) % 4]

                n = THREE.Vector3(v0.x-v1.x, v0.y-v1.y, 0)
                l = n.length()
                n.normalize()
                a = THREE.ArrowHelper(
                    n, 
                    THREE.Vector3(v1.x, v1.y, 1), 
                    l, 
                    0x00ff00)
                scene.add(a)
        """    

    def isPointInsidePolygon(self, p):
        """
         * @param {THREE.Vector2} p
         * @returns {bool}
        """
         # http:#www.ecse.rpi.edu/Homepages/wrf/Research/Short_Notes/pnpoly.html
        inside = False
        polygon = self.polygon
        
        for i in range(4):
            pi = polygon[i]
            pj = polygon[ (i+1) % 4]
            
            if  (pi.y > p.y) != (pj.y > p.y) and p.x < ((pj.x - pi.x) * (p.y - pi.y) / (pj.y - pi.y) + pi.x):
                inside = not inside

        return inside

    def isPointNearPolygon(self, p, radius, debug=None):
        """
         * @param {THREE.Vector2} p
         * @param {float} radius
         * @returns {bool}
        """
        polygon = self.polygon
        x3=p.x
        y3=p.y
        ortho = THREE.Vector2()
        
        for i in range(4):
            if Config['player']['debug']['collision'] and debug is not None:
                if self.dbghelper[i]:
                    debug.remove(self.dbghelper[i])
            
            # segment
            v0 = polygon[i]
            v1 = polygon[(i + 1) % 4]

            # projection on the line
            x1=v0.x
            y1=v0.y
            x2=v1.x
            y2=v1.y
            x3=p.x
            y3=p.y
            px = x2-x1
            py = y2-y1
            dAB = px*px + py*py
            u = ((x3 - x1) * px + (y3 - y1) * py) / dAB
            x = x1 + u * px
            y = y1 + u * py
            
            #bounding box of the segment
            sx = x1 if (x1 < x2 ) else x2
            ex = x2 if (x2 > x1 ) else x1
            sy = y1 if (y1 < y2 ) else y2
            ey = y2 if (y2 > y1 ) else y1
            isOnSegment = (x >= sx and x <= ex and y >= sy and y <= ey)
            
            if isOnSegment:
                ortho.set(x - x3, y - y3)
                d = ortho.length()
                
                if Config['player']['debug']['collision'] and debug is not None:
                    o = THREE.Vector3(ortho.x, ortho.y, 0)
                    o.normalize()
                    self.dbghelper[i] = THREE.ArrowHelper(
                        o, 
                        THREE.Vector3(p.x, p.y, 20),
                        d, 
                        0xf0000f)
                    debug.add(self.dbghelper[i])

                # Return the distance of the point to the line passing through the segment
                if d < radius:
                    return True

        return False

    def isPointInsideAABB(self, p):
        """
         * @param {type} p
         * @returns {Boolean}
        """
        # Inside the Axis Aligned Bounding box ?
        # add the object to test half radius to the AABB
        sx = self.p[0].x
        ex = self.p[1].x
        sy = self.p[0].y
        ey = self.p[2].y

        return (p.x >= sx and p.x <= ex and p.y >= sy and p.y <= ey)

    def intersectAABB(self, footprint):
        """
         * @param {type} footprint
         * @returns {Boolean}
        """
        for i in range(4):
            if self.isPointInsideAABB(footprint.p[i]):
                return True

        for i in range(4):
            if footprint.isPointInsideAABB(self.p[i]):
                return True
        
        return False

    def isNear(self, footprint, debug=None):
        """
         * @param {type} footprint
         * @returns {undefined}
        """

        # if the 2 footprints AABB intersect
        if self.intersectAABB(footprint):
            # inside the radius ?
            d = self.center.distanceTo(footprint.center)

            if d <= self.radius + footprint.radius:
                if self.rotated:
                    # box footprint
                    if self.isPointInsidePolygon(footprint.center):
                        # so the center of the footprint is inside the polygon
                        return True
                    else:
                        # Now check the distance from the point to each segment of the polygon
                        return self.isPointNearPolygon(footprint.center, footprint.radius, debug)
                else:
                    # round footprint
                    return True
        return False

    def clone(self, translation):
        """
         * @param {type} translation
         * @returns {FootPrint|def clone.n}
        """
        n = FootPrint()
        t = THREE.Vector2(translation.x, translation.y)
        for i in range(4):
            n.p[i].copy(self.p[i]).add(t)
        
        n.center.copy(self.center).add(t)
        n.radius = self.radius
        n.height = self.height

        return n

    def distanceTo(self, p):
        """
         * @description distance from the center of the foorprint to the v2
         * @param {THREE.Vector2} p
         * @returns {number}
        """
        return self.center.distanceTo(p)

    def translate(self,v):
        """
         * @description Translate the footprint
         * @param {THREE.Vector2} v
        """
        for i in range(4):
            self.p[i].add(v)
        
        self.center.add(v)

    def fromMesh(self, mesh):
        """
         * @param {THREE.Mesh} mesh
         * @returns {undefined}
        """
        # build object 2D axis aligned footprint
        geometry = mesh.geometry
        center = mesh.position
        minx=99999
        miny=99999
        maxx=-99999
        maxy=-99999
        minz=99999

        # compute the floorprint
        floorpoints = []
        if mesh.constructor.name == "Group":
            # if group of object, extract all points
            p =  []
            for o in mesh.children:
                c = o.position
                geometry = o.geometry
                if geometry.constructor.name.indexOf("BufferGeometry") > -1:
                    positions = geometry.attributes.position
                    for i in range(positions.count):
                        x=positions.array[i*3] + c.x
                        y=positions.array[i*3+1] + c.y
                        z=positions.array[i*3+2] + c.z

                        p.append(x)
                        p.append(y)
                        p.append(z)
                else:
                    vertices = geometry.vertices
                    for i in range(len(vertices)):
                        x=vertices[i].x + c.x
                        y=vertices[i].y + c.y
                        z=vertices[i].z + c.z

                        p.append(x)
                        p.append(y)
                        p.append(z)
        elif geometry.constructor.name.indexOf("BufferGeometry") > -1:
            p = geometry.attributes.position.array
        else:
            vertices = geometry.vertices
            p =  []
            for i in range(len(vertices)):
                x=vertices[i].x
                y=vertices[i].y
                z=vertices[i].z

                p.append(x)
                p.append(y)
                p.append(z)

        # run a first pass to find the lowest points (floor print)
        for i in range(0, len(p), 3):
            z=p[i+2] + center.z

            if z < minz:
                minz = z
                
        # run a second pass to extract the lowest points (floor print)
        for i in range(0, len(p), 3):
            x=p[i] + center.x
            y=p[i+1] + center.y
            z=p[i+2] + center.z

            if z == minz:
                floorpoints.append(x)
                floorpoints.append(y)

        # run a third pass to extract the axis aligned boundingbox
        for i in range(0, len(floorpoints), 2):
            x = floorpoints[i]
            y = floorpoints[i+1]
            
            if x < minx:
                minx = x
            if x > maxx:
                maxx = x
            if y < miny:
                miny = y
            if y > miny:
                maxy = y
            
        self.p[0].x = minx
        self.p[0].y = miny
        self.p[1].x = minx
        self.p[1].y = maxy
        self.p[2].x = maxx
        self.p[2].y = miny
        self.p[3].x = maxx
        self.p[3].y = maxy    

    def AxisAlignedBoundingBox(self, position):
        box = THREE.Box3()
        for p in self.p:
            if p.x < box.min.x:
                box.min.x = p.x
            if p.y < box.min.y:
                box.min.y = p.y
            if p.x > box.max.x:
                box.max.x = p.x
            if p.y > box.max.y:
                box.max.y = p.y

        x = position.x
        y = position.y
        z = position.z

        box.min.x -= x
        box.max.x -= x
        box.min.y -= y
        box.max.y -= y

        aabb = THREE.BoxHelper()
        aabb.matrixAutoUpdate = False
        positions = aabb.geometry.attributes.position.array
        positions[0] = box.min.x;        positions[1] = box.min.y;    positions[2] = z
        positions[3] = box.min.x;        positions[4] = box.max.y;    positions[5] = z
        positions[6] = box.max.x;        positions[7] = box.max.y;    positions[8] = z
        positions[9] = box.max.x;        positions[10] = box.min.y;   positions[11] = z
        positions[12] = box.min.x;       positions[13] = box.min.y;   positions[14] = z + self.height
        positions[15] = box.min.x;       positions[16] = box.max.y;   positions[17] = z + self.height
        positions[18] = box.max.x;       positions[19] = box.max.y;   positions[20] = z + self.height
        positions[21] = box.max.x;       positions[22] = box.min.y;   positions[23] = z + self.height

        return aabb
