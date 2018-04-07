//https://stackoverflow.com/questions/34205069/three-instancedbuffergeometry-and-shadows/34230060
//http://blog.edankwan.com/post/three-js-advanced-tips-shadow
//https://jsfiddle.net/mikatalk/4fn1oqz9/

#define DEPTH_PACKING 3201
#if DEPTH_PACKING == 3200
    uniform float opacity;
#endif
#include <common>
#include <packing>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
    #include <clipping_planes_fragment>
    vec4 diffuseColor = vec4( 1.0 );
    #if DEPTH_PACKING == 3200
      diffuseColor.a = opacity;
    #endif
    #include <map_fragment>
    #include <alphamap_fragment>
    #include <alphatest_fragment>
    #include <logdepthbuf_fragment>
    #if DEPTH_PACKING == 3200
      vec4 diffuse = vec4( vec3( gl_FragCoord.z ), opacity );
    #elif DEPTH_PACKING == 3201
      vec4 diffuse = packDepthToRGBA( gl_FragCoord.z );
    #endif
    // handle transparency
    if(diffuse.a < 0.5)
        discard;
    gl_FragColor = diffuse;
}