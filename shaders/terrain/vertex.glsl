#version 330

uniform mat4 modelMatrix;
uniform mat4 modelViewMatrix;
uniform mat4 projectionMatrix;

uniform sampler2D datamap;
uniform vec2 centerVuv;
uniform float level;

attribute vec3 position;
attribute vec4 color;
attribute vec2 uv;

    // ------->  http://blog.edankwan.com/post/three-js-advanced-tips-shadow
varying vec3 vViewPosition;
varying vec4 vColor;
varying vec2 vUv;
varying vec3 vNormal;

// shadownmap

// chunk(shadowmap_pars_vertex);
uniform mat4 directionalShadowMatrix;
varying vec4 vDirectionalShadowCoord;
// chunk(shadowmap_pars_vertex);

void main() {
    vUv= (uv - 0.5) / level + centerVuv;

    vec3 vPosition = position;
    vColor = color;

    vec4 data = texture2D(datamap, uv);
    vPosition.z = data.w;
    vNormal.x = data.x;
    vNormal.y = data.y;
    vNormal.z = data.z;

    gl_Position = projectionMatrix * modelViewMatrices[objectID] * vec4( vPosition, 1.0 );

    //chunk(worldPosition_vertex)
    vec4 worldPosition = modelMatrices[objectID] * vec4( vPosition, 1.0 );
    //chunk(worldPosition_vertex)

    // chunk(shadowmap_vertex);
    vDirectionalShadowCoord = directionalShadowMatrix * worldPosition;
    // chunk(shadowmap_vertex);

    vViewPosition = worldPosition.xyz;
}
