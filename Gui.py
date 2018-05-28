"""

"""

import time
import numpy as np


class GUI:
    def __init__(self, renderer):
        self.renderer = renderer
        self.texture = renderer.guiRenderer.texture
        self.gui_data = self.texture.img_data
        (x, y) = renderer.guiRenderer.texture.image.size
        self.width = x
        self.height = y
        self.history = np.zeros(30, 'b')
        self.last_frame = 0
        self.last_time = -1

    def update_fps(self):
        t = time.time()
        if self.last_time > 0 and t < self.last_time + 1:
            return

        self.last_time = t
        fps = self.renderer._infoRender.frame - self.last_frame
        if fps > 30:
            fps = 30

        self.last_frame = self.renderer._infoRender.frame

        for i in range(29):
            self.history[i] = self.history[i+1]
        self.history[29] = fps

        for x in range(30):
            fps = self.history[x]
            for y in range(self.height - 30, self.height - 30 + fps):
                p = 4*(x + y*self.width)
                self.gui_data[p] = 255
                self.gui_data[p+3] = 255
            for y in range(self.height - 30 + fps, self.height):
                p = 4*(x + y*self.width)
                self.gui_data[p+3] = 0

        self.texture.needsUpdate = True
