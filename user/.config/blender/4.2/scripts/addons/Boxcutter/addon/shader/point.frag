uniform vec4 color;
uniform vec3 outline;

out vec4 FragColor;


void main() {
    float offs = 0.5;
    float dist = distance(gl_PointCoord, vec2(offs));

    float thick = 0.3;
    float line = smoothstep(offs, thick, dist) * smoothstep(thick, offs, dist);
    float point = (1.0 - smoothstep(0.425, 1.0, dist + 0.1) / fwidth(gl_PointCoord)).x;

    vec3 col = color.rgb;
    float alpha = color.a;

    FragColor = vec4(mix(outline, col, point), max(line * 3.3 * (alpha * 2), point * alpha));
}

