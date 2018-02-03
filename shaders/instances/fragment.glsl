uniform vec3 light;
uniform vec3 ambientLightColor;

varying vec3 vColor;
varying vec3 vNormal;

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

void main()
{
    // Add directional light
    vec3 nlight = normalize(light);
    float nDotl = dot(vNormal, nlight);
    float brightness = max(nDotl, 0.0);
    vec4 diffuse = vec4(1.0) * brightness + vec4(ambientLightColor, 1.0);

#ifdef USE_SHADOWMAP
    // extract the shadow
    float shadow = clamp(getShadowMap(), 0.5, 1.0);

//    gl_FragColor = vec4(shadow, 0.0, 0.0, 1.0);

    gl_FragColor = shadow * diffuse * vec4(vColor, 255);;
#else
    gl_FragColor = diffuse * vec4(vColor, 255);
#endif

}
