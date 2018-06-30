// coming from vertexshader
varying vec3 vColor;
varying vec2 vUv;
varying vec3 vViewPosition;
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

#ifdef USE_NORMALMAP
	uniform sampler2D normalMap;
	vec3 perturbNormal2Arb( vec3 eye_pos, vec3 surf_norm ) {
		vec3 q0 = vec3( dFdx( eye_pos.x ), dFdx( eye_pos.y ), dFdx( eye_pos.z ) );
		vec3 q1 = vec3( dFdy( eye_pos.x ), dFdy( eye_pos.y ), dFdy( eye_pos.z ) );
		vec2 st0 = dFdx( vUv.st );
		vec2 st1 = dFdy( vUv.st );
		vec3 S = normalize( q0 * st1.t - q1 * st0.t );
		vec3 T = normalize( -q0 * st1.s + q1 * st0.s );
		vec3 N = normalize( surf_norm );
		vec3 mapN = texture2D( normalMap, vUv ).xyz * 2.0 - 1.0;
		mat3 tsn = mat3( S, T, N );
		return normalize( tsn * mapN );
	}
#endif

#ifdef USE_SPECULARMAP
    uniform sampler2D specularMap;
#endif

uniform vec3 light;
uniform vec3 ambientLightColor;
uniform sampler2D map;

void main()
{
    // colorr
    vec4 color = texture2D(map, vUv);

    // handle transparency
    float opacity = color.a;
    if(opacity < 0.5)
        discard;

    vec3 normal = vNormal;
    #ifdef USE_NORMALMAP
	    normal = perturbNormal2Arb( -vViewPosition, normal );
    #endif

    // Add directional light
    vec3 nlight = normalize(light);
    float nDotl = dot(normal, nlight);
    float brightness = max(nDotl, 0.0);

    //diffuse.rgb = clamp(diffuse.rgb * brightness, 0.0, 1.0);

    // specular
    float specularStrength;
    #ifdef USE_SPECULARMAP
        vec4 texelSpecular = texture2D( specularMap, vUv );
        specularStrength = texelSpecular.r;
    #else
        specularStrength = 1.0;
    #endif


#ifdef USE_SHADOWMAP
    // extract the shadow
    float shadow = clamp(getShadowMap(), 0.5, 1.0);
    gl_FragColor = shadow * (0.3 + brightness) * color;
#else
    gl_FragColor = (0.3 + brightness) * color;
    gl_FragColor.a = opacity;
#endif
}
