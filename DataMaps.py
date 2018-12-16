"""

"""
import numpy as np
import sys
import math
import os

from DataMap import *
from Config import *
import pickle


class DataMaps:
    def __init__(self, mode='rb'):
        file = Config['folder']+"/bin/datamap.bin"

        self.file = open(file, mode)
        self.index = {}
        self.size = None
        self.mode = mode

        if mode == 'rb':
            self.load_index()

    def close(self):
        self.file.close()
        if self.mode == 'wb':
            self.save_index()

    def save(self, data, size, name):
        self.index[name] = self.file.tell()
        self.file.write(data.tobytes())
        if self.size is None:
            self.index["size"] = size

    def load(self, name):
        self.file.seek(self.index[name])
        b = self.file.read(self.size)
        return np.frombuffer(b, dtype=np.float32)

    def save_index(self):
        file = Config['folder']+"/bin/datamap.idx"
        with open(file, "wb") as f:
            pickle.dump(self.index, f)

    def load_index(self):
        file = Config['folder']+"/bin/datamap.idx"
        with open(file, "rb") as f:
            self.index = pickle.load(f)

        self.size = self.index['size']
