uniform mat4 modelMatrix;
uniform mat4 modelViewMatrix;
uniform mat4 projectionMatrix;

uniform sampler2DArray datamaps;

attribute vec2 center;
attribute float scale;
attribute vec2 centerVuv;
attribute unsigned int level;
attribute unsigned int datamapIndex;

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
    vUv= (uv - 0.5) / float(level) + centerVuv;

    vec3 vPosition = position;
    vColor = color;

    vec3 textureP = vec3(uv.x, uv.y, float(datamapIndex));
    vec4 data = texture(datamaps, textureP);
    vPosition.z = data.w;
    vPosition.xy *= scale;
    vPosition.xy += center;

    vNormal = data.xyz;

    gl_Position = projectionMatrix * modelViewMatrix * vec4( vPosition, 1.0 );

    //chunk(worldPosition_vertex)
    vec4 worldPosition = modelMatrix * vec4( vPosition, 1.0 );
    //chunk(worldPosition_vertex)

    // chunk(shadowmap_vertex);
    vDirectionalShadowCoord = directionalShadowMatrix * worldPosition;
    // chunk(shadowmap_vertex);

    vViewPosition = worldPosition.xyz;
}
