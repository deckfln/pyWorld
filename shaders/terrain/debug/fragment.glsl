precision mediump float;
precision mediump int;

uniform vec3 light;
uniform sampler2D map;

varying vec4 vColor;
varying vec2 vUv;
varying vec3 vNormal;

void main()    {

    vec4 color = texture2D(map, vUv);

    // Add directional light
    vec3 nlight = normalize(light);
    float nDotl = dot(vNormal, nlight);
    float brightness = max(nDotl, 0.0);

    gl_FragColor = color * brightness;
    //gl_FragColor = vec4(vNormal, 1.0);
}
