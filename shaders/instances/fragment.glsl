precision highp float;

uniform vec3 light;
uniform vec3 ambientLight;

varying vec3 vColor;
varying vec3 vNormal;

void main() {

    // Add directional light
    vec3 nlight = normalize(light);
    float nDotl = dot(vNormal, nlight);
    float brightness = max(nDotl, 0.0);
    vec4 diffuse = vec4(1.0) * brightness;

    gl_FragColor = diffuse * vec4(vColor, 255);

}
