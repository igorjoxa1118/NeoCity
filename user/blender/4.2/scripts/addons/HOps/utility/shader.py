import bpy
import gpu
from mathutils import Vector, Matrix
from bpy_extras.view3d_utils import location_3d_to_region_2d

from gpu_extras.batch import batch_for_shader


class dot():
    _highlight = False
    _index = 0
    _size = 20
    _size_high = 40
    _outline_width = 1
    _outline_width_high = 2
    _mat_index = -1

    _location = None
    _color = None
    _color_high = None
    _outline_color = None
    _outline_color_high = None

    @property
    def matrix(self):
        return self.matrices[self.mat_index]

    @property
    def mat_index(self):
        return self._mat_index

    @mat_index.setter
    def mat_index(self, val):
        if not self.matrices: return
        self._mat_index = val % len(self.matrices)

    @property
    def highlight(self):
        return self._highlight

    @highlight.setter
    def highlight(self, val):
        self._highlight = val

        if val:
            self.handler.colors[self._index] = self.color_high
            self.handler.outline_colors[self._index] = self.outline_color_high
            self.handler.sizes[self._index] = self.size_high
            self.handler.outline_widths[self._index] = self.outline_width_high

        else:
            self.handler.colors[self._index] = self.color
            self.handler.outline_colors[self._index] = self.outline_color
            self.handler.sizes[self._index] = self.size
            self.handler.outline_widths[self._index] = self.outline_width

    location = property(fget=lambda self: self._location, fset=lambda self, val: self._set_iter(self._location, val))
    color = property(fget=lambda self: self._color, fset=lambda self, val: self._set_iter(self._color, val))
    color_high = property(fget=lambda self: self._color_high, fset=lambda self, val: self._set_iter(self._color_high, val))
    outline_color = property(fget=lambda self: self._outline_color, fset=lambda self, val: self._set_iter(self._outline_color, val))
    outline_color_high = property(fget=lambda self: self._outline_color_high, fset=lambda self, val: self._set_iter(self._outline_color_high, val))

    size = property(fget=lambda self: self._size, fset=lambda self, val: self._set_val('_size', 'sizes', val, False))
    size_high = property(fget=lambda self: self._size_high, fset=lambda self, val: self._set_val('_size_high', 'sizes', val, True))
    outline_width = property(fget=lambda self: self._outline_width, fset=lambda self, val: self._set_val('_outline_width', 'outline_widths', val, False))
    outline_width_high = property(fget=lambda self: self._outline_width_high, fset=lambda self, val: self._set_val('_outline_width_high', 'outline_widths', val, True))

    def __init__(self, handler):
        self.handler = handler
        self.type = ''
        self.matrices = []

    def _set_iter(self, attr, val):
        for i in range(len(attr)):
            attr[i] = val[i]

    def _set_val(self, attr_name, col_name, val, high):
        setattr(self, attr_name, val)

        if self.highlight == high:
            col = getattr(self.handler, col_name)
            col[self._index] = val

class dot_handler():

    dots = []
    locations = []

    active_dot = None
    draw_handler = None
    draw = True
    dot_preview = False
    dot_preview_size = 0.05

    colors = None
    sizes = None
    outline_colors = None
    outline_widths = None

    snap_radius = 10

    preview_verts = [Vector((-0.5,-0.5, 0)), Vector(( 0.5,-0.5, 0)), Vector((-0.5, 0.5, 0)), Vector(( 0.5, 0.5, 0))]
    preview_indices = [(1, 3, 2), (0, 1, 2)]
    preview_border_indices = [(0, 1), (0, 2), (2, 3), (1, 3)]
    preview_color = [0.5, 0.5, 0.5, 0.3]
    preview_width = 1

    def __init__(self, context, handle_draw=True):
        self.region = context.region
        self.region_3d = context.space_data.region_3d

        self.colors = []
        self.sizes = []
        self.outline_colors = []
        self.outline_widths = []
        self.dot_shader = flat_point_outline.compile()

        if handle_draw:
            self.draw_handler = bpy.types.SpaceView3D.draw_handler_add(self.draw_callback, (context,), 'WINDOW', 'POST_VIEW')

    def update(self, context, event):
        self.mouse = Vector((event.mouse_region_x, event.mouse_region_y))

        areas = [area for area in context.screen.areas if area.type == 'VIEW_3D']

        for area in areas:
            area_mouse_x = event.mouse_x - area.x
            area_mouse_y = event.mouse_y - area.y

            if 0 < area_mouse_x < area.width and 0 < area_mouse_y < area.height:
                space_data = area.spaces.active
                self.region_3d = space_data.region_3d

                for region in area.regions:
                    region_mouse_x = event.mouse_x - region.x
                    region_mouse_y = event.mouse_y - region.y
                    if region.type == 'WINDOW' and 0 < region_mouse_x < region.width and 0 < region_mouse_y < region.height:
                        self.mouse.x = region_mouse_x
                        self.mouse.y = region_mouse_y
                        self.region = region

                        break

                if space_data.region_quadviews:
                    if area_mouse_x < area.width / 2:
                        i = 1 if area_mouse_y > area.height / 2 else 0

                    else:
                        i = 3 if area_mouse_y > area.height / 2 else 2

                    self.region_3d = space_data.region_quadviews[i]
                break

        if self.active_dot:
            self.active_dot.highlight = False

        self.active_dot = None
        distance = 0
        for dot in self.dots:
            vec2d = location_3d_to_region_2d(self.region, self.region_3d, dot.location, default=Vector((0,0)))

            dist = (self.mouse - vec2d).length

            if dist > self.snap_radius:
                continue

            if dist < distance or not self.active_dot:
                self.active_dot = dot
                distance = dist

        if self.active_dot:
            self.active_dot.highlight = True

    def dot_create(self, location, type='VERT', size=5, size_high=10, color=(1, 1, 1, 0.8), color_high=(1, 0, 0, 1), outline_color=(0, 0, 0, 1), outline_color_high=(1, 0, 0, 1), outline_width=1, outline_width_high=2):
        _dot = dot(self)
        index = len(self.dots)
        self.dots.append(_dot)

        _dot._index = index
        _dot.type = type
        _dot._location = Vector(location)
        _dot._size = size
        _dot._size_high = size_high
        _dot._color = list(color)
        _dot._color_high = list(color_high)
        _dot._outline_color = list(outline_color)
        _dot._outline_color_high = list(outline_color_high)
        _dot._outline_width = outline_width
        _dot._outline_width_high = outline_width_high
        _dot._highlight = False

        self.locations.append(_dot.location)
        self.sizes.append(_dot.size)
        self.colors.append(_dot.color)
        self.outline_colors.append(_dot.outline_color)
        self.outline_widths.append(_dot._outline_width)

        return _dot

    def dot_remove(self, dot, update_indices=True):
        index = dot._index
        if self.active_dot is dot:
            self.active_dot = None

        del self.dots[index]
        del self.locations[index]
        del self.sizes[index]
        del self.colors[index]
        del self.outline_colors[index]
        del self.outline_widths[index]

        if update_indices:
            for i in range(index, len(self.dots)):
                self.dots[i]._index = i

    def update_indices(self):
        for dot, i in enumerate(self.dots):
            dot._index = i

    def foreach_set(self, name, val):
        for dot in self.dots:
            setattr(dot, name, val)

    def clear_dots(self):
        self.active_dot = None
        self.dots.clear()
        self.locations.clear()
        self.sizes.clear()
        self.colors.clear()
        self.outline_colors.clear()
        self.outline_widths.clear()

    def purge(self):
        self.clear_dots()

        if self.draw_handler:
            bpy.types.SpaceView3D.draw_handler_remove(self.draw_handler, 'WINDOW')
            self.draw_handler = None

    def draw_callback(self, context):
        if not self.draw: return
        if not self.locations: return
        gpu.state.blend_set('ALPHA')
        #Enable(bgl.GL_LINE_SMOOTH)

        self.alignment_preview(context)

        dot_shader = self.dot_shader

        dot_shader.bind()
        dot_shader.uniform_float('ViewProjectionMatrix', context.region_data.perspective_matrix)

        gpu.state.program_point_size_set(True)

        batch = batch_for_shader(dot_shader, 'POINTS', {'pos': self.locations, 'color_fill': self.colors, 'size': self.sizes, 'outlineWidth': self.outline_widths, 'color_outline': self.outline_colors
        })
        batch.draw(dot_shader)

        gpu.state.program_point_size_set(False)
        gpu.state.blend_set('NONE')
        #Disable(bgl.GL_LINE_SMOOTH)

    def alignment_preview(self, context):
        if not self.active_dot: return

        if self.dot_preview and self.active_dot.matrices:
            size = self.sizes[self.active_dot._index]
            self.sizes[self.active_dot._index] = 0

            dot_matrix = self.active_dot.matrix
            persp_matrix = context.region_data.view_matrix.copy()
            persp_matrix.translation.z = -context.region_data.view_distance

            depth_factor = ((persp_matrix @ dot_matrix.translation) - dot_matrix.translation).length * 0.1
            size = self.dot_preview_size * (1 + depth_factor)
            scale = Matrix.Scale(size, 4)
            matrix = dot_matrix @ scale
            positions = [matrix @ vec for vec in self.preview_verts]

            built_in_shader = 'UNIFORM_COLOR' if bpy.app.version[0] >=4 else '3D_UNIFORM_COLOR'
            preview_shader = gpu.shader.from_builtin(built_in_shader)
            preview_shader.bind()
            preview_shader.uniform_float('color', self.preview_color)

            preview_batch = batch_for_shader(preview_shader, 'TRIS', {'pos': positions}, indices=self.preview_indices)
            preview_batch.draw(preview_shader)

            gpu.state.line_width_set(self.preview_width)

            built_in_shader = 'UNIFORM_COLOR' if bpy.app.version[0] >=4 else '3D_UNIFORM_COLOR'
            border_shader = gpu.shader.from_builtin(built_in_shader)
            border_shader.bind()
            border_shader.uniform_float('color', self.active_dot.outline_color_high)

            border_batch = batch_for_shader(border_shader, 'LINES', {'pos': positions}, indices=self.preview_border_indices)
            border_batch.draw(border_shader)

            gpu.state.line_width_set(1)

            self.sizes[self.active_dot._index] = size

    @classmethod
    def compile(cls):

        if bpy.app.version[:2] < (3, 3):
            vertex = cls.vertex_attr + cls.vertex
            fragment = cls.fragment_attr + cls.fragment

            shader = gpu.types.GPUShader(vertex, fragment)

        else:
            shader_info = gpu.types.GPUShaderCreateInfo()

            shader_info.push_constant('MAT4', 'ViewProjectionMatrix')
            shader_info.push_constant('VEC4', 'color')
            shader_info.vertex_in(0, 'VEC3', 'pos')

            shader_info.fragment_out(0, 'VEC4', 'FragColor')

            shader_info.vertex_source(cls.vertex)
            shader_info.fragment_source(cls.fragment)

            shader = gpu.shader.create_from_info(shader_info)
        return shader

class flat_point_outline():

    vertex_attr = '''
        uniform mat4 ViewProjectionMatrix;

        in float size;
        in float outlineWidth;

        in vec4 color_fill;
        in vec4 color_outline;

        in vec3 pos;

        out vec4 radii;
        out vec4 fillColor;
        out vec4 outlineColor;
    '''

    vertex = '''
        void main()
        {
            vec4 pos_4d = vec4(pos, 1.0);
            gl_Position = ViewProjectionMatrix * pos_4d;
            gl_PointSize = size;

            /* calculate concentric radii in pixels */
            float radius = 0.5 * size;

            /* start at the outside and progress toward the center */
            radii[0] = radius;
            radii[1] = radius - 1.0;
            radii[2] = radius - outlineWidth;
            radii[3] = radius - outlineWidth - 1.0;

            /* convert to PointCoord units */
            radii /= size;

            fillColor = color_fill;
            outlineColor = color_outline;
        }

    '''

    fragment_attr = '''
        in vec4 radii;
        in vec4 fillColor;
        in vec4 outlineColor;

        out vec4 fragColor;
    '''

    fragment = '''
        void main()
        {
        float dist = length(gl_PointCoord - vec2(0.5));

        /* transparent outside of point
        * --- 0 ---
        * smooth transition
        * --- 1 ---
        * pure outline color
        * --- 2 ---
        * smooth transition
        * --- 3 ---
        * pure fill color
        * ...
        * dist = 0 at center of point */

        float midStroke = 0.5 * (radii[1] + radii[2]);

        if (dist > midStroke) {
            fragColor.rgb = outlineColor.rgb;
            fragColor.a = mix(outlineColor.a, 0.0, smoothstep(radii[1], radii[0], dist));
        }
        else {
            fragColor = mix(fillColor, outlineColor, smoothstep(radii[3], radii[2], dist));
        }

        fragColor = fragColor;
        }

    '''

    @classmethod
    def compile(cls):

        if bpy.app.version[:2] < (3, 3):
            vertex = cls.vertex_attr + cls.vertex
            fragment = cls.fragment_attr + cls.fragment

            shader = gpu.types.GPUShader(vertex, fragment)

        else:
            shader_info = gpu.types.GPUShaderCreateInfo()
            vertex_out = gpu.types.GPUStageInterfaceInfo('v_out')
            vertex_out.smooth('VEC4', 'radii')
            vertex_out.smooth('VEC4', 'fillColor')
            vertex_out.smooth('VEC4', 'outlineColor')

            shader_info.push_constant('MAT4', 'ViewProjectionMatrix')
            shader_info.vertex_in(0, 'FLOAT', 'size')
            shader_info.vertex_in(1, 'FLOAT', 'outlineWidth')
            shader_info.vertex_in(2, 'VEC4', 'color_fill')
            shader_info.vertex_in(3, 'VEC4', 'color_outline')
            shader_info.vertex_in(4, 'VEC3', 'pos')
            shader_info.vertex_out(vertex_out)

            shader_info.fragment_out(0, 'VEC4', 'fragColor')

            shader_info.vertex_source(cls.vertex)
            shader_info.fragment_source(cls.fragment)

            shader = gpu.shader.create_from_info(shader_info)
        return shader
