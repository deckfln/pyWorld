"""

"""
from threading import Thread
from THREE.controls.TrackballControls import *
from THREE.loaders.FileLoader import *
from THREE.loaders.CubeTextureLoader import *
from THREE.renderers.pyOpenGL.UniformValue import *

from Player import *
from Terrain import *
from Player import *
from Config import *
from PlayerCamera import *
from quadtree import *
from Sun import *


class InitThread(Thread):
    """
    https://skryabiin.wordpress.com/2015/04/25/hello-world/
    SDL 2.0, OpenGL, and Multithreading (Windows)
    """

    def __init__(self, p):
        Thread.__init__(self)
        self.p = p

    def run(self):
        """Code à exécuter pendant l'exécution du thread."""
        p = self.p
        p.controls = TrackballControls(p.camera, p.container)
        p.camera.controls = p.controls

        p.clock = THREE.Clock()

        # initialize the sun
        p.sun = Sun()
        p.sun.add2scene(p.scene)

        # cubemap
        if Config["skybox"]:
            print("Init Skybox...")
            loader = FileLoader()

            background = CubeTextureLoader().load(Config['engine']['skycube'])
            background.format = THREE.RGBFormat

            shader = Config['engine']['shaders']['skybox']
            p.renderer.background.boxMesh_vertex = loader.load(shader['vertex'])
            p.renderer.background.boxMesh_fragment = loader.load(shader['fragment'])
            p.renderer.background.boxMesh_uniforms = {
                        'tCube': UniformValue(None),
                        'tFlip': UniformValue(- 1),
                        'opacity': UniformValue(1.0),
                        'light': {'type': "v3", 'value': p.sun.light.position},
                        'sunColor': {'type': "v3", 'value': p.sun.color}
            }

            p.load_percentage[0] += 5
            p.scene.background = background


        # sun imposter
        """
        g_sun = THREE.SphereBufferGeometry(2, 8, 8)
        m_sun = THREE.Mesh(g_sun, _material)
        self.sun.add(m_sun)
        """

        # init the shadowmap
        if Config['shadow']['enabled']:
            p.renderer.shadowMaself.enabled = True
            p.sun.castShadow = True
            p.sun.shadow.mapSize.width = Config['shadow']['size']
            p.sun.shadow.mapSize.height = Config['shadow']['size']
            p.sun.shadow.camera.top = 32
            p.sun.shadow.camera.bottom = -32
            p.sun.shadow.camera.right = 32
            p.sun.shadow.camera.left = -32
            p.sun.shadow.camera.near = 128
            p.sun.shadow.camera.far = 256 + 32
            pars = {'minFilter': THREE.NearestFilter, 'magFilter': THREE.NearestFilter, 'format': THREE.RGBAFormat}

            p.sun.shadow.map = THREE.pyOpenGLRenderTarget(Config['shadow']['size'], Config['shadow']['size'], pars)
            p.sun.shadow.map.texture.name = p.sun.name + ".shadowMap"

            if Config['shadow']['debug']:
                p.helper = THREE.CameraHelper(p.sun.shadow.camera)
                p.scene.add(p.helper)
                p.debug = THREE.Mesh(THREE.SphereBufferGeometry(2, 8, 8), _material)
                p.scene.add(p.debug)

            instance_material.uniforms.directionalShadowMaself.value = p.sun.shadow.maself.texture
            instance_material.uniforms.directionalShadowMatrix.value = p.sun.shadow.matrix
            instance_material.uniforms.directionalShadowSize.value = p.sun.shadow.mapSize

        # init the asset instanced models
        print("Init Assets...")

        for name in Config['engine']['assets']:
            models = Config['engine']['assets'][name]
            for lod in range(5):
                p.assets.load(name, lod+1, models[lod], THREE.Vector2(1, 1))
                p.load_percentage[0] += 1

        # dynamic assets (sceneries)
        for name in Config['engine']['dynamic_asset']:
            model = Config['engine']['dynamic_asset'][name]
            p.assets.load(name, None, model, THREE.Vector2(1, 1), True)
            p.load_percentage[0] += 5

        # add them to the scene, as each asset as a instancecount=0, none will be displayed
        p.assets.add_2_scene(p.scene)

        # init the terrain
        print("Init Terrain...")
        p.terrain = Terrain(512, 25, 512)
        p.terrain.load(p.sun)
        p.assets.set_sun(p.sun)
        p.terrain.scene = p.scene
        p.load_percentage[0] += 5

        print("Init meshes...")
        # p.terrain.quadtree.loadChildren(p)
        p.terrain.build_quadtre_indexes()
        p.load_percentage[0] += 5

        print("Init Player...")
        cwd = Config["folder"]
        p.player = Player(cwd, Config['engine']['player'], THREE.Vector3(Config['player']['position'][0], Config['player']['position'][1], 0), p.scene, p.terrain)
        p.player.add2scene(p.scene)
        p.actors.append(p.player)
        p.load_percentage[0] += 5

        print("End init")
