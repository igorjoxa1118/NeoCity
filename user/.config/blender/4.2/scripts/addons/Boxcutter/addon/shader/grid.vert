uniform mat4 projection;
uniform vec3 intersect;

in vec3 frame;

out vec4 position;


void main() {
    position = vec4((frame) + intersect, 1.0);
    gl_Position = projection * position;
}
