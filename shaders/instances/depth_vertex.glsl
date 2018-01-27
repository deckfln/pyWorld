#define DEPTH_PACKING 3201

// per instance
attribute vec3 offset;
attribute vec2 scale;

#include <common>

void main() {
    #include <begin_vertex>
    transformed * vec3(scale.x, scale.x,  scale.y);
    transformed += offset;
    #include <project_vertex>
}
