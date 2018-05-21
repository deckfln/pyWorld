"""
"""
import sys, os.path
mango_dir = (os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
+ '/THREEpy/')
sys.path.append(mango_dir)

import pickle

from datetime import datetime

from THREE import *
from THREE.pyOpenGL.pyOpenGL import *
from THREE.controls.TrackballControls import *

from Terrain import *
from Player import *
from Config import *
from PlayerCamera import *
from quadtree import *

from ProceduralScenery import *
from Scenery import *


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


def init(p):
    """
    Initialize all objects
    :param p:
    :return:
    """
    # /// Global : renderer
    print("Init pyOPenGL...")
    p.container = pyOpenGL(p)
    p.container.addEventListener('resize', onWindowResize, False)

    p.renderer = THREE.pyOpenGLRenderer({'antialias': True})
    p.renderer.setSize( window.innerWidth, window.innerHeight )

    p.camera = THREE.PerspectiveCamera(65, window.innerWidth / window.innerHeight, 0.1, 2000)
    p.camera.position.set(0, 0, 100)
    p.camera.up.set(0, 0, 1)

    p.controls = TrackballControls(p.camera, p.container)
    p.camera.controls = p.controls

    # cubemap
    path = "img/skybox/"
    format = '.png'

    urls = [
        path + 'front' + format,
        path + 'left' + format,
        path + 'right' + format,
        path + 'back' + format,
        path + 'top' + format,
        path + 'bottom' + format
    ]

    print("Init CubeMap...")
    background = THREE.CubeTextureLoader().load(urls)
    background.format = THREE.RGBFormat

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

    # sun imposter
    g_sun = THREE.SphereBufferGeometry(2, 8, 8)
    m_sun = THREE.Mesh(g_sun, _material)
    p.sun.add(m_sun)

    # init the scene
    p.scene = THREE.Scene()
    p.scene.add(p.camera)
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
        p.sun.shadow.camera.far = 256+32
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

    p.assets.load('evergreen', 5,  "models/anime_tree/D0406452B11", THREE.Vector2(1, 1))
    p.assets.load('evergreen', 4,  "models/anime_tree/4/model", THREE.Vector2(1, 1))
    p.assets.load('evergreen', 3,  "models/anime_tree/3/model", THREE.Vector2(1, 1))
    p.assets.load('evergreen', 2,  "models/anime_tree/2/model", THREE.Vector2(1, 1))
    p.assets.load('evergreen', 1,  "models/anime_tree/1/model", THREE.Vector2(1, 1))

    p.assets.load('tree', 5,  "models/old-tree/model", THREE.Vector2(1, 1))
    p.assets.load('tree', 4,  "models/old-tree/4/model", THREE.Vector2(1, 1))
    p.assets.load('tree', 3,  "models/old-tree/3/model", THREE.Vector2(1, 1))
    p.assets.load('tree', 2,  "models/old-tree/2/model", THREE.Vector2(1, 1))
    p.assets.load('tree', 1,  "models/old-tree/1/model", THREE.Vector2(1, 1))

    p.assets.load('house', 1,  "models/wooden_house/wooden_house", THREE.Vector2(1, 1))
    p.assets.load('house', 2,  "models/wooden_house/wooden_house", THREE.Vector2(1, 1))
    p.assets.load('house', 3,  "models/wooden_house/wooden_house", THREE.Vector2(1, 1))
    p.assets.load('house', 4,  "models/wooden_house/wooden_house", THREE.Vector2(1, 1))
    p.assets.load('house', 5,  "models/wooden_house/wooden_house", THREE.Vector2(1, 1))

    # dynamic assets
    p.assets.load('grass', None, "models/grass/grass", THREE.Vector2(1, 1), True)
    p.assets.load('high grass', None, "models/grass/grass", THREE.Vector2(1, 3), True)
    p.assets.load('prairie', None, "models/flower/obj__flow2", THREE.Vector2(1, 1), True)
    p.assets.load('fern', None, "models/ferm/obj__fern3", THREE.Vector2(1, 1), True)
    p.assets.load('shrub', None, "models/shrub/obj__shr3", THREE.Vector2(1, 1), True)
    
    # add them to the scene, as each asset as a instancecount=0, none will be displayed
    p.assets.add_2_scene(p.scene)

    # init the terrain
    print("Init Terrain...")
    p.terrain = Terrain(512, 25, 512)
    p.terrain.load(p.sun)
    p.terrain.scene = p.scene

    print("Init Player...")
    p.player = Player(THREE.Vector3(27.8510658816, -11.0726747753, 0), p.scene, p.terrain)
    p.actors.append(p.player)

    initQuadtreeProcess()

    print("Init meshes...")
    p.terrain.quadtree.loadChildren()
    p.terrain.build_quadtre_indexes()

    p.player.draw()

    # do a first render to initialize as much as possible
    render(p)
    print("End Init")


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

    checkQuadtreeProcess()

    # target 30 FPS, if time since last animate is exactly 0.033ms, delta=1
    delta = (p.clock.getDelta() * 30)
    delta = 1

    p.controls.update()

    # Check player direction
    # and move the terrain if needed
    p.player.move(delta, p.terrain)

    # update the animation loops
    for actor in p.actors:
        actor.update(delta/30)

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
    p.hour += delta * (math.pi / 9000)
    if p.hour > math.pi:
        p.hour = 0

    p.terrain.update_light(p.hour)
    p.assets.set_light_uniform(p.sun.position)

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

                # build procedural scenery on the higher tiles
                if quad.level >= 4:
                   p.procedural_scenery.instantiate(p.player, p.terrain, quad, p.assets)

    p.fps += 1

    # t = time.time()
    render(p)
    # c = time.time() - t
        # print(c, p.player.vcamera.position.x, p.player.vcamera.position.y, p.player.vcamera.position.z)
        # if c > 0.033:
        #    print(c)


def render(p):
    p.renderer.render(p.scene, p.camera)


def keyboard(event, p):
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
    p = Params()

    init(p)

    p.container.addEventListener('animationRequest', animate)
    p.container.addEventListener('keydown', keyboard)
    p.container.addEventListener('keyup', keyboard)
    p.container.loop()


if __name__ == "__main__":
    r = main()
    killQuadtreeProcess()

    sys.exit(r)
