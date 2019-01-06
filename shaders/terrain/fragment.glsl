varying vec2 vUv;
varying vec3 vNormal;
varying vec3 vViewPosition;

// chunk(packing)
const float PackUpscale = 256. / 255.;
const float UnpackDownscale = 255. / 256.;
const vec3 PackFactors = vec3( 256. * 256. * 256., 256. * 256.,  256. );
const vec4 UnpackFactors = UnpackDownscale / vec4( PackFactors, 1. );
const float ShiftRight8 = 1. / 256.;
float unpackRGBAToDepth( const in vec4 v ) {
    return dot( v, UnpackFactors );
}
// chunk(packing)

// chunk(shadowmap_pars_fragment);
#ifdef USE_SHADOWMAP
    uniform sampler2D directionalShadowMap;
    uniform vec2 directionalShadowSize;
    varying vec4 vDirectionalShadowCoord;
    float texture2DCompare( sampler2D depths, vec2 uv, float compare ) {
        float depth = unpackRGBAToDepth( texture2D( depths, uv ) );
        float distance = compare - depth;
        if (distance < 0)
            return 1.0;

        float shadow = distance*20.0;
        return shadow;
    }

    float getShadow( sampler2D shadowMap, vec2 shadowMapSize, float shadowBias, float shadowRadius, vec4 shadowCoord ) {
        float shadow = 1.0;
        shadowCoord.xyz /= shadowCoord.w;
        shadowCoord.z += shadowBias;
        bvec4 inFrustumVec = bvec4 ( shadowCoord.x >= 0.0, shadowCoord.x <= 1.0, shadowCoord.y >= 0.0, shadowCoord.y <= 1.0 );
        bool inFrustum = all( inFrustumVec );
        bvec2 frustumTestVec = bvec2( inFrustum, shadowCoord.z <= 1.0 );
        bool frustumTest = all( frustumTestVec );
        if ( frustumTest ) {
    //        shadow = texture2DCompare( shadowMap, shadowCoord.xy, shadowCoord.z );
            vec2 texelSize = vec2( 1.0 ) / shadowMapSize;
            float dx0 = - texelSize.x * shadowRadius;
            float dy0 = - texelSize.y * shadowRadius;
            float dx1 = + texelSize.x * shadowRadius;
            float dy1 = + texelSize.y * shadowRadius;
            shadow = (
                    texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx0, dy0 ), shadowCoord.z ) +
                    texture2DCompare( shadowMap, shadowCoord.xy + vec2( 0.0, dy0 ), shadowCoord.z ) +
                    texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx1, dy0 ), shadowCoord.z ) +
                    texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx0, 0.0 ), shadowCoord.z ) +
                    texture2DCompare( shadowMap, shadowCoord.xy, shadowCoord.z ) +
                    texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx1, 0.0 ), shadowCoord.z ) +
                    texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx0, dy1 ), shadowCoord.z ) +
                    texture2DCompare( shadowMap, shadowCoord.xy + vec2( 0.0, dy1 ), shadowCoord.z ) +
                    texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx1, dy1 ), shadowCoord.z )
                    ) * ( 1.0 / 9.0 );
        }
        return shadow;
    }
    // chunk(shadowmap_pars_fragment);

    /**
     * Get the shadow
     */
    float getShadowMap()
    {
        return  getShadow( directionalShadowMap, directionalShadowSize, 0.0, 0.5, vDirectionalShadowCoord );
    }
#endif

/*
 *
 */
vec3 perturbNormal2Arb( vec3 eye_pos, vec3 surf_norm, vec3 normal ) {
    vec3 q0 = vec3( dFdx( eye_pos.x ), dFdx( eye_pos.y ), dFdx( eye_pos.z ) );
    vec3 q1 = vec3( dFdy( eye_pos.x ), dFdy( eye_pos.y ), dFdy( eye_pos.z ) );
    vec2 st0 = dFdx( vUv.st );
    vec2 st1 = dFdy( vUv.st );
    vec3 S = normalize( q0 * st1.t - q1 * st0.t );
    vec3 T = normalize( -q0 * st1.s + q1 * st0.s );
    vec3 N = normalize( surf_norm );
    // vec3 mapN = texture2D( normalMap, vUv ).xyz * 2.0 - 1.0;
    vec3 mapN = normal * 2.0 - 1.0;
    mat3 tsn = mat3( S, T, N );
    return normalize( tsn * mapN );
}

uniform sampler2D blendmap_texture;
uniform sampler2DArray terrain_textures;
uniform sampler2DArray normalMap;
uniform sampler2D indexmap;
uniform sampler2D shadowmap;
uniform float indexmap_repeat;
uniform float indexmap_size;
uniform float water_shift;
uniform vec3 light;
uniform float blendmap_repeat;
uniform vec3 sunColor;
uniform float ambientCoeff;

/**
 * mix a seamless tile to avoid the repetition effect byt mixing borders
 * get the composited texel value at the tile position
 *
 * http://www.iquilezles.org/www/articles/texturerepetition/texturerepetition.htm
 */
vec4 hash4( vec2 p ) { return fract(sin(vec4( 1.0+dot(p,vec2(37.0,17.0)),
                                              2.0+dot(p,vec2(11.0,47.0)),
                                              3.0+dot(p,vec2(41.0,29.0)),
                                              4.0+dot(p,vec2(23.0,31.0))))*103.0); }

/**
 *
 * use a texture array
 */
vec4 colorAtArray(sampler2DArray map, vec2 in_map)
{
  vec2 p = in_map/indexmap_size;

  vec4 tile = texture2D(indexmap, p);
  float tileID = tile.r * 255.0;

  vec2 rvv =  vUv*indexmap_repeat;
  vec2 vv = fract(rvv);

  return texture(map, vec3(vv.x, vv.y, tileID));
}

/**
 *
 * use a traditionnal texture
 */
vec4 colorAt(sampler2D map, vec2 in_map)
{
  vec2 p = in_map/indexmap_size;

  vec4 tile = texture2D(indexmap, p);
  int tileID = int(tile.r*255.0);

  vec2 rvv =  vUv*indexmap_repeat;
  vec2 vv = fract(rvv);

    // textureMap is 4 textures x 4 textures
  float row = (tileID >> 2) / 4.0;
  float column = (tileID & 0x3) / 4.0;

  return texture2D(map, vec2(column + vv.x / 4.0, row + vv.y / 4.0));
  /*
  return getIndex(tileID, vv);

  vec2 iuv = floor(rvv);
  vec4 ofa = hash4(iuv + vec2(0,0));
  vec4 ofb = hash4(iuv + vec2(1,0));
  vec4 ofc = hash4(iuv + vec2(0,1));
  vec4 ofd = hash4(iuv + vec2(1,1));

  ofa.zw = sign(ofa.zw-0.5);
  ofb.zw = sign(ofb.zw-0.5);
  ofc.zw = sign(ofc.zw-0.5);
  ofd.zw = sign(ofd.zw-0.5);

  vec2 b = smoothstep(0.25,0.75,vv);

  vec2 uva = rvv*ofa.zw + ofa.xy;
  vec2 uvb = rvv*ofb.zw + ofb.xy;
  vec2 uvc = rvv*ofc.zw + ofc.xy;
  vec2 uvd = rvv*ofd.zw + ofd.xy;


  return mix( mix( getIndex(tileID, uva), getIndex(tileID, uvb), b.x ),
              mix( getIndex(tileID, uvc), getIndex(tileID, uvb), b.x),
              b.y );
*/
}

/*******
 *
 *******/
void main()
{
    // position in the atlasmap
    vec2 mapvUv = vUv*indexmap_size;
    vec2 center_of_tile = floor(mapvUv) + 0.5;
    vec2 delta = fract(mapvUv)-0.5;

    // get a box in the atlas map
    // find the bottomleft point of the quad
    vec2 bottomleft;
    vec2 quadrant = sign(delta);
    bottomleft = clamp(quadrant, vec2(-1, -1), vec2(0, 0)) + center_of_tile;

    // bilinear blending of the 4 textures
    vec4 bottomleft_b = vec4(0.0, 0.0, 0.0, 1.0);
    vec4 bottomright_b = vec4(0.0, 0.0, 1.0, 0.0);
    vec4 topleft_b = vec4(0.0, 1.0, 0.0, 0.0);
    vec4 topright_b = vec4(1.0, 0.0, 0.0, 0.0);

    // locate the texel inside the quadrand
    vec2 blend4tex = mapvUv - bottomleft;
    /*
    vec4 t1 = mix(bottomleft_b, bottomright_b, blend4tex.x);
    vec4 t2 = mix(topleft_b, topright_b, blend4tex.x);
    vec4 t3 = mix(t1, t2, blend4tex.y);
    */

    // texture from atlas maps at each corner of the box
    vec4 bottomleft_c = colorAtArray(terrain_textures, bottomleft);
    vec4 bottomright_c= colorAtArray(terrain_textures, bottomleft + vec2(1,0));
    vec4 topleft_c= colorAtArray(terrain_textures, bottomleft + vec2(0,1));
    vec4 topright_c= colorAtArray(terrain_textures, bottomleft + vec2(1,1));

    vec4 t1 = mix(bottomleft_c, bottomright_c, blend4tex.x);
    vec4 t2 = mix(topleft_c, topright_c, blend4tex.x);
    vec4 ground = mix(t1, t2, blend4tex.y);

    // blend the 4 quadrand textures
    //vec4 ground = t3.w*bottomleft_c + t3.z*bottomright_c + t3.y*topleft_c + t3.x*topright_c;
    //ground = vec4(0.5,0.5,0.5,1.0);

    // do the same with the normalmap
    // normal from atlas maps at each corner of the box
    vec3 bottomleft_n = normalize(colorAtArray(normalMap, bottomleft).xyz);
    vec3 bottomright_n= normalize(colorAtArray(normalMap, bottomleft + vec2(1,0)).xyz);
    vec3 topleft_n= normalize(colorAtArray(normalMap, bottomleft + vec2(0,1)).xyz);
    vec3 topright_n= normalize(colorAtArray(normalMap, bottomleft + vec2(1,1)).xyz);

    vec3 t1_n = mix(bottomleft_n, bottomright_n, blend4tex.x);
    vec3 t2_n = mix(topleft_n, topright_n, blend4tex.x);
    vec3 normal = mix(t1_n, t2_n, blend4tex.y);

    // path & river extracted from the blendmap
    float tileID = 7;     // if of the road

    vec2 blend_uv = fract(vUv * blendmap_repeat);
    vec3 blend_uvz = vec3(blend_uv.x, blend_uv.y, tileID);
    vec4 paving = texture(terrain_textures, blend_uvz);
    vec3 blend_normal = normalize(texture(normalMap, blend_uvz).xyz);
    // vec4 riverbed = texture2D(textures[riverbed_png], blend_uv);

    vec4 blendIndex = texture2D(blendmap_texture, vUv);
    // vec4 red=vec4(1.0, 0.0, 0.0, 1.0);

    vec4 fromBlend = paving*blendIndex.x; // + red*blendIndex.y + riverbed*blendIndex.z;
    float blend_idx = clamp(blendIndex.x + blendIndex.z, 0.0, 1.0);

    // blend blendmap + ground
    vec4 color = mix(ground, fromBlend, blend_idx);
    normal = mix(normal, blend_normal, blend_idx);

    // perturb the normal vector
    vec3 finalNormal = perturbNormal2Arb( -vViewPosition, vNormal, normal );

    // Add directional light
    vec3 nlight = normalize(light);
    float nDotl = dot(finalNormal, nlight);
    float brightness = max(nDotl, 0.0);

#ifdef USE_SHADOWMAP
    // extract the shadow
    float shadow = clamp(getShadowMap(), 0.0, 1.0);

//    gl_FragColor = vec4(shadow, 0.0, 0.0, 1.0);

    gl_FragColor = shadow * diffuse*( mix(ground, fromBlend, blend_idx));
#else
    color = clamp(brightness + ambientCoeff, 0.0, 1.0) * color;

    // tend to blue haze over distance
    float z = clamp(gl_FragCoord.z / gl_FragCoord.w, 0.0, 8192.0);
    float fogAmount = 1.0 - exp( -z * 0.005 );
    vec4  fogColor  = vec4(0.5, 0.6, 0.7, 1.0);

    // color = mix( color, fogColor, fogAmount );

    // tint the whole color
    color = vec4(sunColor, 1.0) * color;

    gl_FragColor = color;
    gl_FragColor.a = 1.0;
#endif

#ifdef DEBUG_INDEXMAP
    gl_FragColor.r = (texture2D(indexmap, vUv).r*50.0);
#endif
#ifdef DEBUG_SHADOWMAP
    gl_FragColor = texture2D(shadowmap, vUv);
#endif
#ifdef DEBUG_BLENDMAP
    gl_FragColor = red*blendIndex.x;
#endif
#ifdef DEBUG_NORMALMAP
    gl_FragColor = vec4(finalNormal, 1.0);
#endif
#ifdef DEBUG_FLATNESS
    gl_FragColor.r = texture2D(indexmap, vUv).r*50.0;
    gl_FragColor.g = 0.0;
    gl_FragColor.b = 0.0;
    gl_FragColor.a = 1.0;
#endif
}