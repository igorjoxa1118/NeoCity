uniform vec3 intersect;

uniform float count;
uniform float size;
uniform float thickness;

uniform vec4 color;

in vec4 position;

out vec4 FragColor;


void main() {
    float increment = size / count;
    vec2 anchor = position.xy * count / size;
    vec2 grid_fract = abs(fract(anchor - 0.5) - 0.5) / fwidth(anchor) / thickness;
    vec3 grid = vec3(1.0 - min(min(grid_fract.x, grid_fract.y), 1.0)) * 0.5;

    float dist = distance(position.xy, intersect.xy) / (size / 1.72);
    vec3 region_fade = vec3(1.0 - smoothstep(((0.33 * size) / size), 0.85, dist)) * 0.5;
    float highlight_ratio = increment / size;
    vec3 highlight = vec3(1.0 - smoothstep(0.01 * highlight_ratio, 1.5 * highlight_ratio, dist));

    vec3 col = color.rgb;
    float alpha = color.a;

    FragColor = vec4(col, vec3(grid * (region_fade + highlight)).z * alpha);
}
