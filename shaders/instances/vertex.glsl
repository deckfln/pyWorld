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
varying vec2 vUv;
varying vec3 vViewPosition;

void main() {
    vUv = uv;
#ifdef USE_COLOR
    vColor.xyz = color.xyz;
#endif

    // the normal vector might not be normalized. So extra check
    vNormal = normalize(normal);

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
