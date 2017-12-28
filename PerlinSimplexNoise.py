#/*
# * To change this license header, choose License Headers in Project Properties.
# * To change this template file, choose Tools | Templates
# * and open the template in the editor.
# */
#//https://gist.github.com/banksean/304522#file-perlin-noise-simplex-js
#// Ported from Stefan Gustavson's java implementation
#// http://staffwww.itn.liu.se/~stegu/simplexnoise/simplexnoise.pdf
#// Read Stefan's excellent paper for details on how this code works.
#//
#// Sean McCullough banksean@gmail.com

#/**
# * You can pass in a random number generator object if you like.
# * It is assumed to have a random() method.
# */
import math
import random


class SimplexNoise:
    def __init__(self, r):
        if not r :
            r = random
        self.grad3 = [[1,1,0],[-1,1,0],[1,-1,0],[-1,-1,0],
                                 [1,0,1],[-1,0,1],[1,0,-1],[-1,0,-1],
                                 [0,1,1],[0,-1,1],[0,1,-1],[0,-1,-1]]
        self.p = [0]*256
        for i in range(256):
            self.p[i] = math.floor(r.random()*256)

        #// To remove the need for index wrapping, double the permutation table length
        self.perm = [0]*512
        for i in range(512):
            self.perm[i]=self.p[i & 255]

        #// A lookup table to traverse the simplex around a given point in 4D.
        #// Details can be found where this table is used, in the 4D noise method.
        self.simplex = [
            [0,1,2,3],[0,1,3,2],[0,0,0,0],[0,2,3,1],[0,0,0,0],[0,0,0,0],[0,0,0,0],[1,2,3,0],
            [0,2,1,3],[0,0,0,0],[0,3,1,2],[0,3,2,1],[0,0,0,0],[0,0,0,0],[0,0,0,0],[1,3,2,0],
            [0,0,0,0],[0,0,0,0],[0,0,0,0],[0,0,0,0],[0,0,0,0],[0,0,0,0],[0,0,0,0],[0,0,0,0],
            [1,2,0,3],[0,0,0,0],[1,3,0,2],[0,0,0,0],[0,0,0,0],[0,0,0,0],[2,3,0,1],[2,3,1,0],
            [1,0,2,3],[1,0,3,2],[0,0,0,0],[0,0,0,0],[0,0,0,0],[2,0,3,1],[0,0,0,0],[2,1,3,0],
            [0,0,0,0],[0,0,0,0],[0,0,0,0],[0,0,0,0],[0,0,0,0],[0,0,0,0],[0,0,0,0],[0,0,0,0],
            [2,0,1,3],[0,0,0,0],[0,0,0,0],[0,0,0,0],[3,0,1,2],[3,0,2,1],[0,0,0,0],[3,1,2,0],
            [2,1,0,3],[0,0,0,0],[0,0,0,0],[0,0,0,0],[3,1,0,2],[0,0,0,0],[3,2,0,1],[3,2,1,0]]

    def dot(self, g, x, y):
        return g[0]*x + g[1]*y

    def noise(self, xin, yin):
        #// Noise contributions from the three corners
        # Skew the input space to determine which simplex cell we're in
        F2 = 0.5*(math.sqrt(3.0)-1.0)
        s = (xin+yin)*F2           #// Hairy factor for 2D
        i = math.floor(xin+s)
        j = math.floor(yin+s)
        G2 = (3.0-math.sqrt(3.0))/6.0
        t = (i+j)*G2
        X0 = i-t                    # Unskew the cell origin back to (x,y) space
        Y0 = j-t
        x0 = xin-X0                 # // The x,y distances from the cell origin
        y0 = yin-Y0
        #// For the 2D case, the simplex shape is an equilateral triangle.
        #// Determine which simplex we are in.
        #// Offsets for second (middle) corner of simplex in (i,j) coords
        if x0>y0:
            i1=1
            j1=0                    #// lower triangle, XY order: (0,0)->(1,0)->(1,1)
        else:
            i1=0
            j1=1                    #// upper triangle, YX order: (0,0)->(0,1)->(1,1)
        #// A step of (1,0) in (i,j) means a step of (1-c,-c) in (x,y), and
        #// a step of (0,1) in (i,j) means a step of (-c,1-c) in (x,y), where
        #// c = (3-sqrt(3))/6
        x1 = x0 - i1 + G2           #// Offsets for middle corner in (x,y) unskewed coords
        y1 = y0 - j1 + G2
        x2 = x0 - 1.0 + 2.0 * G2    #// Offsets for last corner in (x,y) unskewed coords
        y2 = y0 - 1.0 + 2.0 * G2
        #// Work out the hashed gradient indices of the three simplex corners
        ii = i & 255
        jj = j & 255
        gi0 = self.perm[ii+self.perm[jj]] % 12
        gi1 = self.perm[ii+i1+self.perm[jj+j1]] % 12
        gi2 = self.perm[ii+1+self.perm[jj+1]] % 12
        #// Calculate the contribution from the three corners
        t0 = 0.5 - x0*x0-y0*y0
        if t0<0:
            n0 = 0.0
        else:
            t0 *= t0
            n0 = t0 * t0 * self.dot(self.grad3[gi0], x0, y0)  #// (x,y) of grad3 used for 2D gradient

        t1 = 0.5 - x1*x1-y1*y1
        if t1<0:
            n1 = 0.0
        else:
            t1 *= t1
            n1 = t1 * t1 * self.dot(self.grad3[gi1], x1, y1)
        t2 = 0.5 - x2*x2-y2*y2
        if t2<0:
            n2 = 0.0
        else:
            t2 *= t2
            n2 = t2 * t2 * self.dot(self.grad3[gi2], x2, y2)

        #// Add contributions from each corner to get the final noise value.
        #// The result is scaled to return values in the interval [-1,1].
        return 70.0 * (n0 + n1 + n2)