uniform samplerCube tCube;
uniform float tFlip;
uniform float opacity;
varying vec3 vWorldPosition;

uniform vec3 light;

void main() {

    vec3 nlight = normalize(light);
    float nDotl = dot(normalize(vWorldPosition.xyz), nlight);
    float brightness = max(nDotl, 0.0);

    // https://www.reddit.com/r/opengl/comments/1qbd2u/simple_skybox_with_procedural_gradient/
    vec4 gradient = vec4(pow(nDotl , 32), pow(nDotl , 48) / 2.0 + 0.5, nDotl / 4.0 + 0.75, 1.0);

    vec4 cubeColor = textureCube( tCube, vec3( tFlip * vWorldPosition.x, vWorldPosition.yz ) );

    float average_color = (cubeColor.r + cubeColor.g + cubeColor.b)/3;
    float color_distance = abs(0.44705882352941176470588235294118 - average_color)*2.0;

    gl_FragColor = mix(gradient, cubeColor, color_distance);
 }
