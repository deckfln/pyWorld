precision mediump float;
precision mediump int;

uniform vec3 light;
uniform vec2 centerVuv;
uniform float level;

varying vec3 vNormal;

void main()    {

    vec4 color = vec4(level * 20, abs(centerVuv.x), abs(centerVuv.y), 1.0);

    // Add directional light
    vec3 nlight = normalize(light);
    float nDotl = dot(vNormal, nlight);
    float brightness = max(nDotl, 0.0);

    gl_FragColor = color * brightness;
}
