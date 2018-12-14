"""
"""
import sys, os.path
mango_dir = (os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
+ '/THREEpy/')
sys.path.append(mango_dir)

import pickle
import queue
from InitThread import *

from datetime import datetime

from THREE import *
from THREE.pyOpenGL.pyOpenGL import *
from THREE.controls.TrackballControls import *
from THREE.loaders.TextureLoader import *
from THREE.pyOpenGL.pyGUI import *
from THREE.pyOpenGL.widgets.Stats import *
from THREE.pyOpenGL.widgets.LoadBar import *

from ProceduralScenery import *
from Scenery import *
from Gui import *


class PYWorld:
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
        self.hour = math.pi/2
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
        self.waypoints =[]
        self.waypoint = Config["benchmark"]
        self.procedural_scenery = ProceduralScenery()
        self.fps = 0
        self.frame_by_frame = False
        self.suspended = False
        self.gui = None
        self.init_thread = None
        self.queue = queue.Queue()
        self.load_percentage = [0]

    def init(self):
        """
        Initialize all objects
        :param p:
        :return:
        """
        # load the gui
        loader = TextureLoader()
    
        img = loader.load(Config["folder"] + '/' + "img/gui.png")
        img.magFilter = THREE.NearestFilter
        img.minFilter = THREE.NearestFilter
    
        # /// Global : renderer
        print("Init pyOPenGL...")
        self.container = pyOpenGL(self)
        self.container.addEventListener('resize', self.onWindowResize, False)
        self.container.addEventListener('keydown', self.keyboard)
        self.container.addEventListener('keyup', self.keyboard)

        self.renderer = THREE.pyOpenGLRenderer({'antialias': True})
        self.renderer.setSize( window.innerWidth, window.innerHeight )
        self.gui = pyGUI(self.renderer)
        self.gui.add(Stats())
        self.gui.add(LoadBar(self.load_percentage))

        self.camera = THREE.PerspectiveCamera(65, window.innerWidth / window.innerHeight, 0.1, 2000)
        self.camera.position.set(0, 0, 100)
        self.camera.up.set(0, 0, 1)
    
        self.scene = THREE.Scene()
        self.scene.add(self.camera)
    
        self.init_thread = InitThread(self)
        self.init_thread.start()
    
        """
        self.player.draw()
    
        # do a first render to initialize as much as possible
        render(p)
        """
        self.container.addEventListener('animationRequest', self.render_load)

    @staticmethod
    def render_load(self):
        """
    
        :param p:
        :return:
        """
        if self.init_thread is not None and not self.init_thread.is_alive():
            self.init_thread.join()
            self.init_thread = None
            self.container.addEventListener('animationRequest', self.animate)
            self.gui.reset()
            self.gui.add(Stats())
            if Config["benchmark"]:
                self.container.start_benchmark()
            return
    
        self.renderer.render(self.scene, self.camera)
        self.gui.update()

    @staticmethod
    def onWindowResize(event, self):
        """
        Handle display window resize
        :param event:
        :param p:
        :return:
        """
        windowHalfX = window.innerWidth / 2
        windowHalfY = window.innerHeight / 2
    
        self.camera.aspect = window.innerWidth / window.innerHeight
        self.camera.updateProjectionMatrix()
    
        self.renderer.setSize(window.innerWidth, window.innerHeight)

    @staticmethod
    def animate(self):
        """
    
        :param p:
        :return:
        """
        if self.waypoint:
            # direction toward the next waypoint
            x = self.waypoints[self.waypoint + 1][0]
            y = self.waypoints[self.waypoint + 1][1]
            d = THREE.Vector2(x, y)
            dp = THREE.Vector2(self.player.position.x, self.player.position.y)
            d = d.sub(dp)
            dst = d.length()
    
            # angle with the current direction
            a = math.atan2(d.y, d.x) - math.atan2(self.player.direction.y, self.player.direction.x)
    
            if dst > 1:
                if a < -0.1:
                    self.player.action.y = 1
                    self.player.action.x = 0
                elif a > 0.1:
                    self.player.action.y = -1
                    self.player.action.x = 0
                else:
                    self.player.action.y = 0
                    self.player.action.x = 1
            else:
                self.player.action.x = 0
                self.waypoint += 1
    
        # print(a, dst, self.player.action.x, self.player.action.y)
    
        # target 30 FPS, if time since last animate is exactly 0.033ms, delta=1
        delta = (self.clock.getDelta() * 30)
        delta = 1
    
        self.controls.update()
    
        # update lighting
        self.sun.move(self)
    
        # Check player direction
        # and move the terrain if needed
        self.player.move(delta, self.terrain)
    
        # update the animation loops
        for actor in self.actors:
            actor.update(delta / 30)
    
        # Check player direction
        # self.player.update(delta, self.gamepad.move_direction, self.gamepad.run, self.terrain)
    
        # move the camera
        if not self.free_camera:
            self.player.vcamera.display(self.camera)
    
        # display the terrain tiles
        self.terrain.draw(self.player)
    
        # extract the assets from each visible tiles and build the instances
        if Config['terrain']['display_scenary']:
            self.assets.reset_instances()
    
            for quad in self.terrain.tiles_onscreen:
                if quad.visible:
                    # build instances from teh tiles
                    for asset in quad.assets.values():
                        if len(asset.offset) > 0:
                            self.assets.instantiate(asset)
    
            # build procedural scenery around the player, on even frame
            if Config['terrain']['display_grass']:
                if self.renderer.info.render.frame % 5:
                    self.assets.reset_dynamic_instances()
                    self.procedural_scenery.instantiate(self.player, self.terrain, self.assets)
    
        # Check player direction
        # self.player.update(delta, self.gamepad.move_direction, self.gamepad.run, self.terrain)
    
        # time passes
        # complete half-circle in 5min = 9000 frames
        # 1 frame = pi/9000
        if Config['time']:
            self.hour += delta * (math.pi / 4000)
            if self.hour > math.pi:
                self.hour = 0

        self.render(self)
        # c = time.time() - t
        # print(c, self.player.vcamera.position.x, self.player.vcamera.position.y, self.player.vcamera.position.z)
        # if c > 0.033:
            #    print(c)
    
        # self.queue.put(1)

    @staticmethod
    def render(self):
        """
    
        :param p:
        :param p:
        :return:
        """
        self.renderer.render(self.scene, self.camera)
        self.gui.update()

    @staticmethod
    def keyboard(event, self):
        """
    
        :param event:
        :param p:
        :return:
        """
        keyCode = event.keyCode
        down = (event.type == 'keydown' ) * 1
    
        # change status of SHIFT
        if keyCode == 304:
            self.shift = down
            self.player.set_run(down)
    
        if keyCode == 97:   # Q
            self.container.quit()
        elif keyCode == 99:   # C
            self.free_camera = not self.free_camera
        elif keyCode == 116:  # T
            if down:
                print("[%f, %f]," %(self.player.position.x, self.player.position.y))
        elif keyCode == 115:  # S
            self.frame_by_frame = True
            self.suspended = True
        elif keyCode == 110:  # N
            if not self.keymap[keyCode]:
                self.suspended = False
            self.keymap[keyCode] = down
    
        elif keyCode in self.keymap:
            self.keymap[keyCode] = down
    
            self.player.action.x = self.keymap[273] or -self.keymap[274]  # up / down
            self.player.action.y = self.keymap[275] or -self.keymap[276]  # left / right
        else:
            print("keyCode:", keyCode)

    def run(self):
        """
        :param argv:
        :return:
        """
        self.init()

        self.container.loop()

        self.terrain.loader.terminate()
