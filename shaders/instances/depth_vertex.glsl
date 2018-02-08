//https://stackoverflow.com/questions/34205069/three-instancedbuffergeometry-and-shadows/34230060
//http://blog.edankwan.com/post/three-js-advanced-tips-shadow
//https://jsfiddle.net/mikatalk/4fn1oqz9/

#define DEPTH_PACKING 3201

// per instance
attribute vec3 offset;
attribute vec2 scale;

#include <common>

void main() {
    #include <begin_vertex>
    transformed = transformed * vec3(scale.x, scale.x,  scale.y) + offset;
    #include <project_vertex>
}
