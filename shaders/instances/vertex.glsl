// per instance
attribute vec3 offset;
attribute vec2 scale;

// shadownmap

// chunk(shadowmap_pars_vertex);
uniform mat4 directionalShadowMatrix;
varying vec4 vDirectionalShadowCoord;
// chunk(shadowmap_pars_vertex);

// for the fragment
varying vec3 vColor;
varying vec3 vNormal;

void main() {
    vColor.xyz = color.xyz;
    vNormal = normal;

    vec3 vPosition = position * vec3(scale.x, scale.x,  scale.y) + offset;
    gl_Position = projectionMatrix * modelViewMatrix * vec4( vPosition, 1.0 );

    //chunk(worldPosition_vertex)
    vec4 worldPosition = modelMatrix * vec4( vPosition, 1.0 );
    //chunk(worldPosition_vertex)

    // chunk(shadowmap_vertex);
    vDirectionalShadowCoord = directionalShadowMatrix * worldPosition;
    // chunk(shadowmap_vertex);

}
