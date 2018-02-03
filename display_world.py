"""
"""
import sys
sys.path.append('../THREEpy')

from datetime import datetime

from THREE import *
from THREE.pyOpenGL.pyOpenGL import *
from THREE.controls.TrackballControls import *

from Terrain import *
from Player import *
from Config import *
from PlayerCamera import *
from quadtree import *


class Params:
    def __init__(self):
        self.camera = None
        self.scene = None
        self.renderer = None
        self.container = None
        self.mesh = None
        self.terrain = None
        self.quads = None
        self.player = None
        self.actors = []
        self.sun = None
        self.clock = None
        self.hour = 0
        self.keymap = {
            273: 0,     # up
            274: 0,     # down
            275: 0,     # left
            276: 0      # right
        }
        self.shift = False
        self.free_camera = False
        self.debug = None
        self.helper = None


def init(p):
    """
    Initialize all objects
    :param p:
    :return:
    """
    # /// Global : renderer
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

    # init the terrain
    p.terrain = Terrain(512, 25, 512)
    p.terrain.load(p.sun)
    p.terrain.scene = p.scene

    p.player = Player(THREE.Vector3(3,3,0), p.scene, p.terrain)
    p.actors.append(p.player)

    initQuadtreeProcess()

    p.player.draw()


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
    checkQuadtreeProcess()

    # target 30 FPS, if time since last animate is exactly 0.033ms, delta=1
    delta = (p.clock.getDelta() * 30)

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

    p.terrain.update(p.hour)

    # move the camera
    if not p.free_camera:
        p.player.vcamera.display(p.camera)

    p.terrain.draw(p.player)

    # t = time.time()
    render(p)
    # c = time.time() - t
    # if c > 0.033:
    #     print(c)


def render(p):
    p.renderer.render(p.scene, p.camera)


def keyboard(event, p):
    keyCode = event.keyCode
    down = (event.type == 'keydown' ) * 1

    # change status of SHIFT
    if keyCode == 304:
        p.shift = down
        p.player.run = down

    if keyCode == 99:
        p.free_camera = not p.free_camera

    if keyCode in p.keymap:
        p.keymap[keyCode] = down

        p.player.action.x = p.keymap[273] or -p.keymap[274]  # up / down
        p.player.action.y = p.keymap[275] or -p.keymap[276]  # left / right


def main(argv=None):
    p = Params()

    init(p)
    p.container.addEventListener('animationRequest', animate)
    p.container.addEventListener('keydown', keyboard)
    p.container.addEventListener('keyup', keyboard)
    return p.container.loop()


if __name__ == "__main__":
    r = main()
    killQuadtreeProcess()

    sys.exit(r)
