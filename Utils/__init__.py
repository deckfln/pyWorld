""" 
* To change this license header, choose License Headers in Project Properties.
* To change this template file, choose Tools | Templates
* and open the template in the editor.
"""
from THREE import *
import math


Materials = []


def Geometry2indexedBufferGeometry(geometry): 
    """
    * @description Convert a THREE.Geometry to indexed BufferGeometry
    * @param {THREE.Geometry} geometry
    """
    attributes = geometry.attributes
    position = attributes.position
    p = THREE.Vector3()
    total_vert=0

    # identified buffers
    indices = []
    hposition = {}
    
    # general buffers
    attrib = {}
    for key in attributes:
        attrib[key] = []
    
    # deduplicate positions
    # and build indices
    array1 = position.array
    for j in range(position.count):
        i = j * position.itemSize
        p.x = array1[i]
        p.y = array1[i+1]
        p.z = array1[i+2]

        key= "%d:%d:%d" % (p.x, p.y, p.z)
        if key in hposition:
            vertice_index = hposition[key]
        else:
            hposition[key] = total_vert

            for key in attributes:
                attribute1 = attributes[ key ]
                attributeArray1 = attribute1.array
                itemSize = attribute1.itemSize
                
                for i in range(itemSize):
                    attrib[key].append(attributeArray1[j * itemSize + i])
            
            vertice_index = total_vert
            
            total_vert += 1
        
        indices.append(vertice_index)
    
    bufGeometry = THREE.BufferGeometry()
    bufGeometry.boundingSphere = geometry.boundingSphere
    bufGeometry.setIndex( indices )
    
    itemSize = 0
    for key in attributes:
        if key== 'position' or key== 'normal' or key == 'color':
            itemSize=3
        elif key == 'uv':
            itemSize=2
        bufGeometry.addAttribute( key, THREE.Float32BufferAttribute( attrib[key], itemSize ) )
    
    return bufGeometry


class MaterialIndex:
    def __init__(self, index, material, mesh):
        self.index =index
        self.material = material
        self.meshes = [ mesh]


def mergeMeshes(orig_meshes):
    """*
    * @description For each tile, merge the static meshes
    * @param {array of THREE.Mesh} orig_meshes description
    """
    
    # unroll the meshes
    meshes = []
    for mesh in orig_meshes:
        if mesh.type == 'Group':
            for child in mesh.children:
                child.position.add(mesh.position)
                meshes.append(child)
        else:
            meshes.append(mesh)
    
    # convert all meshes to BufferGeometry
    for mesh in meshes:
        geometry = mesh.geometry
        
        if geometry.my_class(isGeometry):
            # convert geometry to nonindexed BufferGeometry
            bufgeometry = THREE.BufferGeometry()
            bufgeometry.fromGeometry(geometry)
            
            mesh.geometry = bufgeometry

    # convert all meshes to indexed BufferGeometry
    for mesh in meshes:
        geometry = mesh.geometry
        
        if not geometry.index:
            mesh.geometry = Geometry2indexedBufferGeometry(geometry)
    
    # List of all the materials used in the meshes you want to combine
    # build a list of all meshes sharing the same material
    material_indexes = {}

    for mesh in meshes:
        material = mesh.material
        uuid = material.uuid

        materialindex = -1
        for i in range(len(Materials) - 1, -1, -1):
            if Materials[i].uuid == uuid:
                materialindex = i
                break

        if materialindex < 0:
            Materials.append (material)
            materialindex = len(Materials) - 1

        if uuid in material_indexes:
             material_indexes[uuid].meshes.append(mesh)
        else:
             material_indexes[uuid] = MaterialIndex(materialindex,Materials[materialindex],mesh)

    # merge all indexed BufferGeometry
    start=0
    total_vertices = 0

    # buffers

    indices = []
    vertices = []
    normals = []
    uvs = []
    groups = []

    for j in material_indexes:
        mymeshes = material_indexes[j].meshes
        materialindex = material_indexes[j].index

        for mesh in mymeshes:
            geometry = mesh.geometry

            geometry.translate(mesh.position.x, mesh.position.y, mesh.position.z)

            # merge the indexes
            index = geometry.index
            item_start = len(indices)
            for j in range(index.count * index.itemSize):
                indices.append(index.array[j] + total_vertices)

            # merge the attributes
            attributes = geometry.attributes

            for key in attributes:
                attribute1 = attributes[ key ]
                attributeArray1 = attribute1.array

                if key == 'position':
                    target=vertices
                elif key == 'normal':
                    target=normals
                elif key == 'uv':
                    target=uvs

                item_start = len(target)
                for j in range(attribute1.count * attribute1.itemSize):
                    target.append(attributeArray1[ j ])

            total_vertices += attributes.position.count
        end = len(indices)

        groups.append( [start, (end-start), materialindex] )     # materialIndex 0

        start = end
        
    # build geometry

    mergedGeometry = THREE.BufferGeometry()
    #TODO: currently assume the first mesh is the terrain, so pick it bounding sphere
    mergedGeometry.boundingSphere = meshes[0].geometry.boundingSphere
    mergedGeometry.clearGroups()

    for group in groups:
        mergedGeometry.addGroup(group[0], group[1], group[2])
        
    mergedGeometry.setIndex( indices )
    mergedGeometry.addAttribute( 'position', THREE.Float32BufferAttribute( vertices, 3 ) )
    mergedGeometry.addAttribute( 'normal', THREE.Float32BufferAttribute( normals, 3 ) )
    mergedGeometry.addAttribute( 'uv', THREE.Float32BufferAttribute( uvs, 2 ) )

    # Create the combined mesh
    return THREE.Mesh(mergedGeometry, Materials)


def cylinder(radius, length, radialSegments):
    """*
     * 
     * @param {type} radius
     * @param {type} length
     * @param {type} radialSegments
     * @returns {THREE.BufferGeometry|THREE_utils_cylinder.bufGeometry}
    """
    indices = []
    vertices = []
    normals = []
    uvs = []
    
    normal = THREE.Vector3()
    vertex = THREE.Vector3()

    # build vertices
    for y in range(2):
        for x in range(radialSegments):
            u = x / radialSegments
            theta = u * 2 * math.pi

            sinTheta = math.sin( theta )
            cosTheta = math.cos( theta )

            # vertex
            vertex.x = radius * sinTheta
            vertex.y = radius * cosTheta
            vertex.z = y*length
            vertices.extend([ vertex.x, vertex.y, vertex.z ])
            
            # normal
            normal.set( sinTheta, cosTheta, 0 ).normalize()
            normals.extend([ normal.x, normal.y, normal.z ])

            # uv
            uvs.extend([ u, y ])
    
    for x in range(radialSegments):
        a = x
        b = (x+1) % radialSegments
        c = x + radialSegments
        d = ((x+1) % radialSegments) + radialSegments

        # faces
        indices.extend([ a, d, b ])
        indices.extend([ a, c, d ])
    
    bufGeometry = THREE.BufferGeometry()
    bufGeometry.setIndex( indices )
    bufGeometry.addAttribute( 'position', THREE.Float32BufferAttribute( vertices, 3 ) )
    bufGeometry.addAttribute( 'normal', THREE.Float32BufferAttribute( normals, 3 ) )
    bufGeometry.addAttribute( 'uv', THREE.Float32BufferAttribute( uvs, 2 ) )
    
    return bufGeometry


def cone(radius, length, radialSegments):
    """*
     * 
     * @param {type} radius
     * @param {type} length
     * @param {type} radialSegments
     * @returns {THREE.BufferGeometry|THREE_utils_cone.bufGeometry}
    """
    indices = []
    vertices = []
    normals = []
    uvs = []
    
    normal = THREE.Vector3()
    vertex = THREE.Vector3()
    
    # build base vertices
    for x in range(radialSegments):
        u = x / radialSegments
        theta = u * 2 *math.pi

        sinTheta = math.sin( theta )
        cosTheta = math.cos( theta )

        # vertex
        vertex.x = radius * sinTheta
        vertex.y = radius * cosTheta
        vertex.z = 0
        vertices.extend([ vertex.x, vertex.y, vertex.z ])

        # normal
        normal.set( sinTheta, cosTheta, 0 ).normalize()
        normals.extend([ normal.x, normal.y, normal.z ])

        # uv
        uvs.extend([ u, 0 ])
    
    # top
    vertex.set(0, 0, length)
    vertices.extend([ vertex.x, vertex.y, vertex.z ])

    normal.set( 0, 0, 0 )
    normals.extend([ normal.x, normal.y, normal.z ])

    uvs.extend([ 0, 0 ])
    
    # build side of the cone
    c = radialSegments
    for x in range(radialSegments):
        a = x
        b = (x+1) % radialSegments

        # faces
        indices.extend([ a, c, b ])
    
    # build base of the cone
    vertex.set(0, 0, 0)
    vertices.extend([ vertex.x, vertex.y, vertex.z ])

    normal.set( 0, 0, -1 )
    normals.extend([ normal.x, normal.y, normal.z ])

    uvs.extend([ 0, 0 ])
    
    c = radialSegments+1
    for x in range(radialSegments):
        a = x
        b = (x+1) % radialSegments

        # faces
        indices.extend([ a, b, c ])
    
    bufGeometry = THREE.BufferGeometry()
    bufGeometry.setIndex( indices )
    bufGeometry.addAttribute( 'position', THREE.Float32BufferAttribute( vertices, 3 ) )
    bufGeometry.addAttribute( 'normal', THREE.Float32BufferAttribute( normals, 3 ) )
    bufGeometry.addAttribute( 'uv', THREE.Float32BufferAttribute( uvs, 2 ) )
    
    return bufGeometry


def parseMesh(json):
    """*
     * @description Load the JSON data to build a Mesh
     * @param {type} json
     * @returns {undefined}
    """
    loader = THREE.ObjectLoader()
    mesh = loader.parse(json)

    p = mesh.geometry.attributes.position
    j = 0
    for i in range(p.count):
        x = p.array[j]
        y = p.array[j + 1]
        z = p.array[j + 2]
        
        j += 3

    mesh.position.fromArray(json.object.position)
    
    return mesh


def TriangleContains(triangle, point):
    """*
     * @description: THREE.triangle.contains has rounding errors if the point is on an edge
     * @param {type} triangle
     * @param {type} point
     * @returns {Boolean}
    """
    result = THREE.Triangle.barycoordFromPoint( point, triangle.a, triangle.b, triangle.c )
    if abs(result.x) < 0.00001:
        result.x = 0.00001
    if abs(result.y) < 0.00001:
        result.y = 0.00001
    
    return ( result.x >= 0 ) and ( result.y >= 0 ) and ( ( result.x + result.y ) <= 1 )


def THREE_utils_point2line(A, B, C):
    """*
     * 
     * @param {type} A
     * @param {type} B
     * @param {type} C
     * @returns {Number}
    """
    d = C.clone().sub(B).normalize()
    v = A.clone().sub(B)
    t = v.dot(d)
    P = B.clone().add(d.multiplyScalar(t))
    return P.distanceTo(A)


class ShadowMap:
    def __init__(self, size):
        """*
         * 
         * @param {type} size
         * @returns {ShadowMap}
        """
        self.target = THREE.WebGLRenderTarget( size, size, {
            minFilter: THREE.NearestFilter,
            magFilter: THREE.NearestFilter,
            generateMipmaps: False})
        self.target.stencilBuffer = False
        self.depthBuffer = False
    #    this.depthTexture = THREE.DepthTexture()
    #    this.depthTexture.type = THREE.UnsignedShortType

        self.camera = THREE.OrthographicCamera( -256, 256, 256, -256, 0, 512)
        self.depthMaterial = THREE.MeshDepthMaterial()
        if Config.shadow.debug_camera:
            self.helper = THREE.CameraHelper(self.camera)
            scene.add(self.helper)

        self.shadowMatrix = THREE.Matrix4()

    def render(self, scene):
        scene.overrideMaterial = self.depthMaterial
        renderer.render( scene, self.camera, self.target )
        scene.overrideMaterial = None

    def light(self, position):
        self.camera.position.copy(position)
        self.camera.lookAt(THREE.Vector3(0,0,0))
        self.camera.updateMatrixWorld()
        
        self.shadowMatrix.set(
                0.5, 0.0, 0.0, 0.5,
                0.0, 0.5, 0.0, 0.5,
                0.0, 0.0, 0.5, 0.5,
                0.0, 0.0, 0.0, 1.0
        )

        self.shadowMatrix.multiply( self.camera.projectionMatrix )
        self.shadowMatrix.multiply( self.camera.matrixWorldInverse )
                                            
        terrain.material1.directionalShadowMatrix = self.shadowMatrix
