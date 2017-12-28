#/*
# * To change this license header, choose License Headers in Project Properties.
# * To change this template file, choose Tools | Templates
# * and open the template in the editor.
# *
# * https://gist.github.com/blixt/f17b47c62508be59987b
# */

#/**
# * Creates a pseudo-random value generator. The seed must be an integer.
# *
# * Uses an optimized version of the Park-Miller PRNG.
# * http://www.firstpr.com.au/dsp/rand31/
# */


class Random:
    def __init__(self, seed):
        self.seed = seed % 2147483647
        if self.seed <= 0:
            self.seed += 2147483646

    def next(self):
        #"""/**
        # * Returns a pseudo-random value between 1 and 2^32 - 2.
        # */"""
        self.seed = self.seed * 16807 % 2147483647
        return self.seed

    def nextFloat(self):
         #"""/**
         #* Returns a pseudo-random floating point number in range [0, 1).
         #   #// We know that result of next() will be 1 to 2147483646 (inclusive).
         #*/"""
        return (self.next() - 1) / 2147483646

    def random(self):
        return self.nextFloat()
