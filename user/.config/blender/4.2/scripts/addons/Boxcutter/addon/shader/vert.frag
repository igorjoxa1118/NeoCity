uniform vec4 color;
uniform vec3 outline;

out vec4 FragColor;


void main() {
    vec2 pos = gl_PointCoord.xy;
    pos = pos * 2.0 - 1.0;

    float angle = atan(pos.x, pos.y) + 3.14159265359;
    float radius = 1.57079632679;
    float dist = cos(floor(0.5 + angle / radius) * radius - angle) * length(pos);

    float offs = 0.95;
    float thick = 0.5;
    float line = smoothstep(offs, thick, dist) * smoothstep(thick, offs, dist);
    float point = (1.0 - smoothstep(0.8, 1.0, dist + 0.25) / fwidth(pos)).x;

    vec3 col = color.rgb;
    float alpha = color.a;

    FragColor = vec4(mix(outline, col, point), max(line * 3.3 * (alpha * 2), point * alpha));
}

