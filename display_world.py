"""
"""
import sys, os.path
mango_dir = (os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
+ '/THREEpy/')
sys.path.append(mango_dir)

import pickle
from threading import Thread

from datetime import datetime

from THREE import *
from THREE.pyOpenGL.pyOpenGL import *
from THREE.controls.TrackballControls import *
from THREE.TextureLoader import *

from Terrain import *
from Player import *
from Config import *
from PlayerCamera import *
from quadtree import *

from ProceduralScenery import *
from Scenery import *
from Gui import *


class Params:
    def __init__(self):
        self.container = None
        self.camera = None
        self.scene = None
        self.renderer = None
        self.mesh = None
        self.terrain = None
        self.quads = None
        self.player = None
        self.actors = []
        self.sun = None
        self.clock = None
        self.hour = 0
        self.keymap = {
            110: 0,     # N
            273: 0,     # up
            274: 0,     # down
            275: 0,     # left
            276: 0      # right
        }
        self.shift = False
        self.free_camera = False
        self.debug = None
        self.helper = None
        self.assets = Assets()
        self.waypoints = [
            [27.851066, -11.072675],
            [82.691207, -7.590076],
            [101.407703, 13.839407],
            [163.939700, 17.976922],
            [140.623194, 190.161045],
            [80.165049, 219.885517],
            [39.678931, 168.043069],
            [45.278453, 173.812005],
            [5.467293, 195.812008],
            [-83.311626, 199.816100],
            [-126.860680, 109.217034],
            [-138.746920, 101.351219],
            [-142.627914, 88.164670],
            [-149.326163, 45.132085],
            [-140.465237, 13.597540],
            [-85.459352, -22.551980],
            [-151.262829, -118.220122],
            [-83.218297, -93.002215],
            [-38.293321, -33.974625],
            [-1.120154, -51.350403],
            [31.228154, -114.540116],
            [80.523751, -77.058823]
        ]
        self.waypoint = Config["benchmark"]
        self.procedural_scenery = ProceduralScenery()
        self.fps = 0
        self.frame_by_frame = False
        self.suspended = False
        self.GUI = None
        self.init_thread = None
        self.animate_thread = None
        self.queue = queue.Queue()
        self.load_percentage = 0


class _InitThread(Thread):
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

        # cubemap
        print("Init CubeMap...")
        background = THREE.CubeTextureLoader().load(Config['engine']['skycube'])
        background.format = THREE.RGBFormat

        p.load_percentage += 5

        p.clock = THREE.Clock()

        # Lights
        ambLight = THREE.AmbientLight(0x999999)

        # initialize the sun
        _material = THREE.MeshBasicMaterial({
            'color': 0xffffff
        })
        p.sun = THREE.DirectionalLight(0xffffff, 1)
        p.sun.position.set(100, 100, 100)

        instance_material.uniforms.light.value = p.sun.position
        instance_material.uniforms.ambientLightColor.value = ambLight.color

        instance_grass_material.uniforms.light.value = p.sun.position
        instance_grass_material.uniforms.ambientLightColor.value = ambLight.color

        # sun imposter
        g_sun = THREE.SphereBufferGeometry(2, 8, 8)
        m_sun = THREE.Mesh(g_sun, _material)
        p.sun.add(m_sun)

        # init the scene
        p.scene.add(ambLight)
        p.scene.add(p.sun)
        p.scene.background = background

        # init the shadowmap
        if Config['shadow']['enabled']:
            p.renderer.shadowMap.enabled = True
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

            instance_material.uniforms.directionalShadowMap.value = p.sun.shadow.map.texture
            instance_material.uniforms.directionalShadowMatrix.value = p.sun.shadow.matrix
            instance_material.uniforms.directionalShadowSize.value = p.sun.shadow.mapSize

        # init the asset instanced models
        print("Init Assets...")

        for name in Config['engine']['assets']:
            models = Config['engine']['assets'][name]
            for lod in range(5):
                p.assets.load(name, lod+1, models[lod], THREE.Vector2(1, 1))
                p.load_percentage += 1

        # dynamic assets (sceneries)
        for name in Config['engine']['dynamic_asset']:
            model = Config['engine']['dynamic_asset'][name]
            p.assets.load(name, None, model, THREE.Vector2(1, 1), True)
            p.load_percentage += 5

        # add them to the scene, as each asset as a instancecount=0, none will be displayed
        p.assets.add_2_scene(p.scene)

        # init the terrain
        print("Init Terrain...")
        p.terrain = Terrain(512, 25, 512)
        p.terrain.load(p.sun)
        p.assets.set_light_uniform(p.sun.position)
        p.load_percentage += 5
        p.terrain.scene = p.scene
        p.load_percentage += 5

        print("Init Player...")
        p.player = Player(THREE.Vector3(27.8510658816, -11.0726747753, 0), p.scene, p.terrain)
        p.actors.append(p.player)
        p.load_percentage += 5

        initQuadtreeProcess()

        print("Init meshes...")
        p.terrain.quadtree.loadChildren(p)
        p.terrain.build_quadtre_indexes()
        p.load_percentage += 5
        print("End init")


class _animate_thread(Thread):
    """
    https://skryabiin.wordpress.com/2015/04/25/hello-world/
    SDL 2.0, OpenGL, and Multithreading (Windows)
    """

    def __init__(self, p, queue):
        Thread.__init__(self)
        self.p = p
        self.queue = queue

    def run(self):
        q = self.queue
        p = self.p

        while True:
            action = q.get()
            if action is None:
                break

            checkQuadtreeProcess()

            q.task_done()


def init(p):
    """
    Initialize all objects
    :param p:
    :return:
    """
    # load the gui
    loader = THREE.TextureLoader()

    img = loader.load("img/gui.png")
    img.magFilter = THREE.NearestFilter
    img.minFilter = THREE.NearestFilter

    # /// Global : renderer
    print("Init pyOPenGL...")
    p.container = pyOpenGL(p)
    p.container.addEventListener('resize', onWindowResize, False)

    p.renderer = THREE.pyOpenGLRenderer({'antialias': True, 'gui': img})
    p.renderer.setSize( window.innerWidth, window.innerHeight )
    p.GUI = GUI(p.renderer)

    p.camera = THREE.PerspectiveCamera(65, window.innerWidth / window.innerHeight, 0.1, 2000)
    p.camera.position.set(0, 0, 100)
    p.camera.up.set(0, 0, 1)

    p.scene = THREE.Scene()
    p.scene.add(p.camera)

    p.init_thread = _InitThread(p)
    p.init_thread.start()

    p.animate_thread = _animate_thread(p, p.queue)
    p.animate_thread.start()

    """
    p.player.draw()

    # do a first render to initialize as much as possible
    render(p)
    """
    p.container.addEventListener('animationRequest', render_load)


def render_load(p):
    """

    :param p:
    :return:
    """
    if p.init_thread is not None and not p.init_thread.is_alive():
        p.init_thread.join()
        p.init_thread = None
        p.player.draw()
        p.container.addEventListener('animationRequest', animate)
        p.GUI.reset()
        if Config["benchmark"]:
            p.container.start_benchmark()
        return

    p.GUI.load_bar(p.load_percentage)
    p.renderer.render(p.scene, p.camera)


def onWindowResize(event, p):
    """
    Handle display window resize
    :param event:
    :param p:
    :return:
    """
    windowHalfX = window.innerWidth / 2
    windowHalfY = window.innerHeight / 2

    p.camera.aspect = window.innerWidth / window.innerHeight
    p.camera.updateProjectionMatrix()

    p.renderer.setSize(window.innerWidth, window.innerHeight)


def animate(p):
    """

    :param p:
    :return:
    """
    if p.waypoint:
        # direction toward the next waypoint
        x = p.waypoints[p.waypoint + 1][0]
        y = p.waypoints[p.waypoint + 1][1]
        d = THREE.Vector2(x, y)
        dp = THREE.Vector2(p.player.position.x, p.player.position.y)
        d = d.sub(dp)
        dst = d.length()

        # angle with the current direction
        a = math.atan2(d.y, d.x) - math.atan2(p.player.direction.y, p.player.direction.x)

        if dst > 1:
            if a < -0.1:
                p.player.action.y = 1
                p.player.action.x = 0
            elif a > 0.1:
                p.player.action.y = -1
                p.player.action.x = 0
            else:
                p.player.action.y = 0
                p.player.action.x = 1
        else:
            p.player.action.x = 0
            p.waypoint += 1

    # print(a, dst, p.player.action.x, p.player.action.y)

    # target 30 FPS, if time since last animate is exactly 0.033ms, delta=1
    delta = (p.clock.getDelta() * 30)
    delta = 1

    p.controls.update()

    # Check player direction
    # and move the terrain if needed
    p.player.move(delta, p.terrain)

    # update the animation loops
    for actor in p.actors:
        actor.update(delta / 30)

    # Check player direction
    # p.player.update(delta, p.gamepad.move_direction, p.gamepad.run, p.terrain)

    # move the camera
    if not p.free_camera:
        p.player.vcamera.display(p.camera)

    # display the terrain tiles
    p.terrain.draw(p.player)

    # extract the assets from each visible tiles and build the instances
    if Config['terrain']['display_scenary']:
        p.assets.reset_instances()

        for quad in p.terrain.tiles_onscreen:
            if quad.mesh.visible:
                # build instances from teh tiles
                for asset in quad.assets.values():
                    if len(asset.offset) > 0:
                        p.assets.instantiate(asset)

        # build procedural scenery around the player, on even frame
        if p.renderer._infoRender.frame % 5:
            p.assets.reset_dynamic_instances()
            p.procedural_scenery.instantiate(p.player, p.terrain, p.assets)

    # Check player direction
    # p.player.update(delta, p.gamepad.move_direction, p.gamepad.run, p.terrain)

    # "sun" directional vector
    sun_vector = THREE.Vector3(0, 256 * math.cos(p.hour), 256 * math.sin(p.hour))

    # define the shadowmap camera target, 10 units ahead of the player position along the view sight
    line_of_sight = p.player.direction.clone().multiplyScalar(24).add(p.player.position)
    # hm = p.terrain.screen2map(line_of_sight)
    line_of_sight.z = p.player.position.z   # p.terrain.get(hm.x, hm.y)
    p.sun.target.position.copy(line_of_sight)
    p.sun.target.updateMatrixWorld()

    if Config['shadow']['debug']:
        p.debug.position.copy(line_of_sight)

    # move back the sun direction to set the shadow camera position
    line_of_sight.add(sun_vector)
    p.sun.shadow.camera.position.copy(line_of_sight)
    p.sun.position.copy(line_of_sight)

    # need to update the projectmatric, don't know why
    # if the camera herlper is turned on, it does the update
    p.sun.shadow.camera.updateProjectionMatrix()
    p.sun.shadow.camera.updateMatrixWorld()

    # time passes
    # complete half-circle in 5min = 9000 frames
    # 1 frame = pi/9000
    p.hour += delta * (math.pi / 4000)
    if p.hour > math.pi:
        p.hour = 0

    p.terrain.update_light(p.hour)

    p.fps += 1

    # update gui
    p.GUI.update_fps()

    render(p)
    # c = time.time() - t
    # print(c, p.player.vcamera.position.x, p.player.vcamera.position.y, p.player.vcamera.position.z)
    # if c > 0.033:
        #    print(c)

    # p.queue.put(1)


def render(p):
    """

    :param p:
    :return:
    """
    p.renderer.render(p.scene, p.camera)


def keyboard(event, p):
    """

    :param event:
    :param p:
    :return:
    """
    keyCode = event.keyCode
    down = (event.type == 'keydown' ) * 1

    # change status of SHIFT
    if keyCode == 304:
        p.shift = down
        p.player.run = down

    if keyCode == 97:   # Q
        p.container.quit()
    elif keyCode == 99:   # C
        p.free_camera = not p.free_camera
    elif keyCode == 116:  # T
        if down:
            print("[%f, %f]," %(p.player.position.x, p.player.position.y))
    elif keyCode == 115:  # S
        p.frame_by_frame = True
        p.suspended = True
    elif keyCode == 110:  # N
        if not p.keymap[keyCode]:
            p.suspended = False
        p.keymap[keyCode] = down

    elif keyCode in p.keymap:
        p.keymap[keyCode] = down

        p.player.action.x = p.keymap[273] or -p.keymap[274]  # up / down
        p.player.action.y = p.keymap[275] or -p.keymap[276]  # left / right
    else:
        print(keyCode)


def main(argv=None):
    """

    :param argv:
    :return:
    """
    p = Params()

    init(p)

    p.container.addEventListener('keydown', keyboard)
    p.container.addEventListener('keyup', keyboard)
    p.container.loop()
    p.queue.put(None)
    p.animate_thread.join()


if __name__ == "__main__":
    r = main()
    # killQuadtreeProcess()

    sys.exit(r)
