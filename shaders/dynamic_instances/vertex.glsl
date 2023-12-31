// per instance
in vec3 offset;
in vec2 scale;

// shadownmap

// chunk(shadowmap_pars_vertex);
uniform mat4 directionalShadowMatrix;
varying vec4 vDirectionalShadowCoord;
// chunk(shadowmap_pars_vertex);

// for the fragment
out vec3 vColor;
out vec2 vUv;
out vec3 vViewPosition;
out vec3 vNormal;

void main() {
    vUv = uv;
    vColor.xyz = color.xyz;
    vNormal = normal;

    vec3 iPosition = position * vec3(scale.x, scale.x,  scale.y) + offset;
    vec4 mvPosition = modelViewMatrix * vec4( iPosition, 1.0 );

    gl_Position = projectionMatrix * mvPosition;

    //chunk(worldPosition_vertex)
    vec4 worldPosition = modelMatrix * vec4( iPosition, 1.0 );
    //chunk(worldPosition_vertex)

    // chunk(shadowmap_vertex);
    vDirectionalShadowCoord = directionalShadowMatrix * worldPosition;
    // chunk(shadowmap_vertex);

    vViewPosition = mvPosition.xyz;
}
