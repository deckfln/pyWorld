precision highp float;

uniform mat4 modelViewMatrix;
uniform mat4 projectionMatrix;

// per object
attribute vec3 position;
attribute vec3 normal;
attribute vec3 color;

// per instance
attribute vec3 offset;
attribute vec2 scale;

varying vec3 vColor;
varying vec3 vNormal;

void main() {
    vColor.xyz = color.xyz;
    vNormal = normal;

    vec3 vPosition = position * vec3(scale.x, scale.x,  scale.y);
    gl_Position = projectionMatrix * modelViewMatrix * vec4( offset + vPosition, 1.0 );
}
