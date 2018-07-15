uniform samplerCube tCube;
uniform float tFlip;
uniform float opacity;
uniform vec3 light;
uniform vec3 sunColor;

varying vec3 vWorldPosition;


void main() {

    vec3 nlight = normalize(light);
    float nDotl = dot(normalize(vWorldPosition.xyz), nlight);
    float brightness = max(nDotl, 0.0);

    vec4 cubeColor = textureCube( tCube, vec3( tFlip * vWorldPosition.x, vWorldPosition.yz ) );

/*
    if (brightness > 0.95) {
        // https://www.reddit.com/r/opengl/comments/1qbd2u/simple_skybox_with_procedural_gradient/
        vec4 gradient = vec4(pow(nDotl , 32), pow(nDotl , 48) / 2.0 + 0.5, nDotl / 4.0 + 0.75, 1.0);
        float gray =  0.21 * gradient.r + 0.72 * gradient.g + 0.07 * gradient.b;

        float average_color = (cubeColor.r + cubeColor.g + cubeColor.b)/3;
        float color_distance = abs(0.44705882352941176470588235294118 - average_color)*2.0;

        //gl_FragColor = mix(gradient, cubeColor, color_distance);
        gl_FragColor = cubeColor + clamp((gray - 0.5) * 2.0, 0.0, 1.0)*cubeColor;
    }
    else {
        gl_FragColor = cubeColor;
    }
*/
        float average_color = (cubeColor.r + cubeColor.g + cubeColor.b)/3;
        float color_distance = 1.0 - abs(0.44705882352941176470588235294118 - average_color);
        gl_FragColor = (cubeColor + pow(brightness, 96)) * vec4(sunColor, 1.0);
 }
