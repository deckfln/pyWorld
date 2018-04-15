    // ------->  http://blog.edankwan.com/post/three-js-advanced-tips-shadow
varying vec2 vUv;
varying float z;
varying vec3 vertexNormal;

// shadownmap

// chunk(shadowmap_pars_vertex);
uniform mat4 directionalShadowMatrix;
varying vec4 vDirectionalShadowCoord;
// chunk(shadowmap_pars_vertex);

void main() {
    vUv = uv;

    gl_Position = projectionMatrix *
                modelViewMatrix *
                vec4(position, 1.0);

    //chunk(worldPosition_vertex)
    vec4 worldPosition = modelMatrix * vec4( position, 1.0 );
    //chunk(worldPosition_vertex)

    // chunk(shadowmap_vertex);
    vDirectionalShadowCoord = directionalShadowMatrix * worldPosition;
    // chunk(shadowmap_vertex);

    vertexNormal = normal;
}
