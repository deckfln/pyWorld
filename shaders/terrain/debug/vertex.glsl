precision mediump float;
precision mediump int;

layout (std140) uniform modelMatricesBlock
{
    uniform mat4 modelMatrices[1024];
};

uniform mat4 modelViewMatrix; // optional
uniform mat4 projectionMatrix; // optional
uniform sampler2D datamap;
uniform vec2 centerVuv;
uniform float level;

attribute vec3 position;
attribute vec4 color;
attribute vec2 uv;

varying vec4 vColor;
varying vec2 vUv;
varying vec3 vNormal;

void main()    {
    vUv= (uv - 0.5) / level + centerVuv;

    vec3 vPosition = position;
    vColor = color;

    vec4 data = texture2D(datamap, uv);
    vPosition.z = data.w;
    vNormal.x = data.x;
    vNormal.y = data.y;
    vNormal.z = data.z;

    gl_Position = projectionMatrix * modelViewMatrix * vec4( vPosition, 1.0 );
}
