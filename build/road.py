from AStar import *
from Mask import *


class Road:
    def __init__(self, terrain, source, target, wide):
        self.astar = AStar(terrain, terrain.size, source, target)
        self.astar.parse_graph()
        self.path3d = None
        self.normals = None
        self.wide = wide

    def convert3d(self, terrain):
        path = []
        for i in range(0, len(self.astar.path), 8):
            p = self.astar.path[i]
            path.append(THREE.Vector3(p.x, p.y, terrain.getV(p)))
        self.path3d = path

    def draw_road(self, terrain, radius):
        """

        :param terrain:
        :param blendMap:
        :param astar:
        :return:
        """
        path = self.astar.path
        mask = Mask(radius)

        # // print the road on the blendmap
        for i in range(len(path)):
            current = path[i]
            mask.applyBlend(current, terrain, 0)

    # Apply Game.Programming.Gems.8 road 3D building

    def buildNormals(self):
        """
        For each segment, compute and average the 2D normal vector at the point of the road
        :param road:
        :return:
        """
        self.normals = [None for i in range(len(self.path3d))]

        for index in range(len(self.path3d)-1):
            start = self.path3d[index]
            end = self.path3d[index + 1]
            direction = end.clone().sub(start)

            # get 2D normal vector to the segment
            # dot(0) = this.x * v.x + this.y * v.y
            # v.x=1
            # 0 = this.x + this.y * v.y
            # -this.x/this.y = v.y
            normal = THREE.Vector2()
            if direction.y == 0:
                normal.set(0, 1)
            else:
                normal.set(1, -direction.x / direction.y)
                normal.normalize()

            # average the normal with the next patch
            if index == 0:
                self.normals[index] = normal.clone()
                self.normals[index + 1] = normal.clone()
            else:
                self.normals[index].add(normal)
                self.normals[index].normalize()

                self.normals[index + 1] = normal.clone()

        return self.normals

    def patchTerrain(self, terrain, elevationmap, elevationmap_effect):
        """
        Use the normals at each point to build triangles
        under each triangle adapt the heightmap
        :param terrain:
        :return:
        """
        size = terrain.size
        radius = self.wide

        for index in range(len(self.path3d)-1):
            start = self.path3d[index]
            end = self.path3d[index + 1]

            normal_start2d = self.normals[index].clone().multiplyScalar(radius)
            normal_end2d = self.normals[index+1].clone().multiplyScalar(radius)

            normal_start3d = THREE.Vector3(normal_start2d.x, normal_start2d.y, 0)
            normal_end3d = THREE.Vector3(normal_end2d.x, normal_end2d.y, 0)

            points = [
                end.clone().sub(normal_end3d),
                end.clone().add(normal_end3d),
                start.clone().sub(normal_start3d),
                start.clone().add(normal_start3d)
            ]

            # 2D boundingbox
            pmin = THREE.Vector2(99999, 99999)
            pmax = THREE.Vector2(-99999, -99999)
            for i in range(4):
                p = points[i]
                if p.x < pmin.x: pmin.x = math.floor(p.x)
                if p.y < pmin.y: pmin.y = math.floor(p.y)
                if p.x > pmax.x: pmax.x = math.ceil(p.x)
                if p.y > pmax.y: pmax.y = math.ceil(p.y)

            triangles = [
                THREE.Triangle(points[0], points[1], points[2]),
                THREE.Triangle(points[1], points[2], points[3])
            ]

            planes = [
                triangles[0].plane(),
                triangles[1].plane()
            ]

            # // apply a mask on the triangles
            pmin.x = int(pmin.x)
            pmin.y = int(pmin.y)
            pmax.x = int(pmax.x)
            pmax.y = int(pmax.y)

            for y in range(int(pmin.y), int(pmax.y) + 1):
                for x in range(int(pmin.x), int(pmax.x) + 1):
                    if x < 0 or x >= size or y < 0 or y >= size:
                        continue

                    # // get Z on the terrain
                    sz = terrain.get(x, y)

                    m = THREE.Vector3(x, y, sz)

                    # // test each triangles
                    for i in range(2):
                        # // move each point only once
                        if elevationmap.get(x, y):
                            continue

                        a = planes[i].normal.x
                        b = planes[i].normal.y
                        c = planes[i].normal.z
                        d = planes[i].constant

                        # use the plane equation to find Z on the triangle
                        m.z = (-d - a*m.x - b*m.y)/c

                        # // ensure the point is on the triangle
                        if not triangles[i].containsPoint(m):
                            continue

                        elevationmap.set(m.x, m.y, m.z)

                        # // get distance of the point to the line
                        # // to compute hte power of the effect
                        # var l= THREE_utils_point2line(m, start, end);
                        d = end.clone().sub(start).normalize()
                        v = m.clone().sub(start)
                        t = v.dot(d)
                        P = start.clone().add(d.multiplyScalar(t))
                        l = P.distanceTo(m)
                        if l < radius/2:
                            elevationmap_effect.set(m.x, m.y, 1)
                        else:
                            l -= radius/2
                            t = elevationmap_effect.get(m.x, m.y)
                            n = 1 - math.cos(( radius/2 - l)/(radius/2) * math.pi/2)
                            elevationmap_effect.set(m.x, m.y, max(t, n))
