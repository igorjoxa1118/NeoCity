import bpy
import blf
import bmesh
import gpu
from gpu_extras.batch import batch_for_shader
from bpy_extras import view3d_utils
from math import pi
from ...Tools.helper import *


def drawing_tris(vertices, indices, color):
    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    shader.uniform_float("color", color)
    gpu.state.blend_set('ALPHA')
    batch = batch_for_shader(shader, 'TRIS', {"pos": vertices}, indices=indices)
    batch.draw(shader)
    gpu.state.blend_set('NONE')


def draw_rectangle(x, y, width, height, color, align = 'CENTER'):
    if align == 'LEFT':
        l = x + width
        h = y - height
        vertices = ((x, y), (l, y), (l, h), (x, h))
    elif align == 'CENTER':
        vertices = ((x-width/2, y+height/2), (x+width/2, y+height/2), (x+width/2, y-height/2), (x-width/2, y-height/2))
    indices = ((0, 1, 2),(0, 2, 3))
    drawing_tris(vertices, indices, color)


def draw_rounded_rectangle(x, y, width, height, color, align='CENTER', radius=8, resolution=6):
    half_width = width / 2
    half_height = height / 2
    bevel_positions = {
        'top_left': (x + radius - half_width, y - radius + half_height),
        'top_right': (x + width - radius - half_width, y - radius + half_height),
        'bottom_right': (x + width - radius - half_width, y - height + radius + half_height),
        'bottom_left': (x + radius - half_width, y - height + radius + half_height),
    }
    vertices = []
    # quart supérieur droit
    starter = 0
    for i in range(resolution):
        vertices.append((
            bevel_positions['top_right'][0]+math.cos(starter + i * pi/2 / (resolution - 1))*radius,
            bevel_positions['top_right'][1]+math.sin(starter + i * pi/2 / (resolution - 1))*radius
        ))
    # quart supérieur gauche
    starter = pi/2
    for i in range(resolution):
        vertices.append((
            bevel_positions['top_left'][0] + math.cos(starter + i * pi/2 / (resolution - 1))*radius,
            bevel_positions['top_left'][1] + math.sin(starter + i * pi/2 / (resolution - 1))*radius
        ))
    # quart inférieur gauche
    starter = pi
    for i in range(resolution):
        vertices.append((
            bevel_positions['bottom_left'][0] + math.cos(starter + i * pi/2 / (resolution - 1))*radius,
            bevel_positions['bottom_left'][1] + math.sin(starter + i * pi/2 / (resolution - 1))*radius
        ))
    # quart inférieur droit
    starter = 3*pi/2
    for i in range(resolution):
        vertices.append((
            bevel_positions['bottom_right'][0] + math.cos(starter + i * pi/2 / (resolution - 1))*radius,
            bevel_positions['bottom_right'][1] + math.sin(starter + i * pi/2 / (resolution - 1))*radius
        ))
    indices = []
    for i in range(len(vertices)-2):
        indices.append(
            (0, i+1, i+2)
        )
    drawing_tris(vertices, indices, color)


def draw_circle(cx, cy, r, color, segments, thickness = 1):
    theta = 2*math.pi/segments
    coords = [(cx+r, cy)]
    for i in range(segments):
        coords.append((math.cos(i*theta)*r+cx , math.sin(i*theta)*r+cy))
        coords.append((math.cos(i*theta)*r+cx , math.sin(i*theta)*r+cy))
    coords.append((cx+r, cy))
    draw_line(coords, 1, color)


def draw_circle_full(cx, cy, r, color, segments = 16):
    theta = 2*math.pi/segments
    coords = [(cx,cy)]
    for i in range(segments):
        coords.append((math.cos(i*theta)*r+cx , math.sin(i*theta)*r+cy))
    indices = []
    for i in range(segments-1):
        indices.append((0, i+1, i+2))
    indices.append((0, segments, 1))
    if bpy.app.version >= (4, 0, 0):
        shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    else:
        shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
    shader.uniform_float("color", color)
    gpu.state.blend_set('ALPHA')
    batch = batch_for_shader(shader, 'TRIS', {"pos": coords}, indices=indices)
    batch.draw(shader)
    gpu.state.blend_set('NONE')


def draw_line(coords=None, thickness=1, color=(1, 1, 1, 1), indices=None, transform_2d=False):
    region = bpy.context.region
    rv3d = bpy.context.region_data
    if transform_2d:
        transformed_coords = []
        for c in coords:
            transformed_coords.append(view3d_utils.location_3d_to_region_2d(region, rv3d, c))
    else:
        transformed_coords = coords

    if bpy.app.version >= (4, 0, 0):
        shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    else:
        shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')

    batch = batch_for_shader(shader, 'LINES', {"pos": transformed_coords}, indices=indices)
    shader.bind()
    shader.uniform_float("color", color)
    gpu.state.blend_set('ALPHA')
    gpu.state.line_width_set(thickness)
    batch.draw(shader)

    gpu.state.blend_set('NONE')
    gpu.state.line_width_set(1)


def draw_text(text = '', text_pos = (0,0), text_size = 16, text_color = (1, 1, 1, 1), align = 'CENTER'):
    if bpy.app.version >= (4, 0, 0):
        blf.size(0, text_size)
    else:
        blf.size(0, text_size, 72)
    text_dimensions = blf.dimensions(0, text)

    if align == 'CENTER':
        text_pos_x = text_pos[0] - text_dimensions[0] / 2
        text_pos_y = text_pos[1] - text_dimensions[1] / 2
    elif align == 'LEFT':
        text_pos_x = text_pos[0]
        text_pos_y = text_pos[1] + text_dimensions[1] / 2
    elif align == 'RIGHT':
        text_pos_x = text_pos[0] - text_dimensions[0]
        text_pos_y = text_pos[1] + text_dimensions[1] / 2
    elif align == 'CENTER LEFT':
        text_pos_x = text_pos[0]
        text_pos_y = text_pos[1] - text_dimensions[1] / 2
    blf.position(0, text_pos_x, text_pos_y, 0)

    r, g, b, a = text_color
    blf.color(0, r, g, b, a)

    blf.draw(0, text)


def draw_image(texture, position = [0, 32], size = [32, 32]):
    vertices = (
    (position[0], position[1] + size[1]),
    (position[0], position[1]),
    (position[0] + size[0], position[1]),
    (position[0] + size[0], position[1] + size[1])
    )
    if bpy.app.version >= (4, 0, 0):
        shader = gpu.shader.from_builtin('IMAGE')
    else:
        shader = gpu.shader.from_builtin('2D_IMAGE')
    gpu.state.blend_set('ALPHA')
    batch_img = batch_for_shader(shader, 'TRI_FAN', {"pos": vertices, "texCoord": ((0, 1), (0, 0), (1, 0), (1, 1))})
    shader.bind()
    shader.uniform_sampler("image", texture)
    batch_img.draw(shader)
    gpu.state.blend_set('NONE')


def prepare_draw_shape(obj):
    region = bpy.context.region
    rv3d = bpy.context.region_data
    data = obj.data
    if len(data.vertices)<3:
        depsgraph = bpy.context.evaluated_depsgraph_get()
        obj_eval = obj.evaluated_get(depsgraph)
        data = obj_eval.data
    bm = bmesh.new()
    bm.from_mesh(data)
    coords = [(view3d_utils.location_3d_to_region_2d(region, rv3d, obj.matrix_world @ v.co)) for v in bm.verts]
    indices = [[loop.vert.index for loop in looptris] for looptris in bm.calc_loop_triangles()]
    bm.free()
    return [coords, indices]


def draw_faces(obj, color):
    data = obj.data
    bm = bmesh.new()
    bm.from_mesh(data)

    coords = [obj.matrix_world @ v.co for v in data.vertices]
    indices = [[loop.vert.index for loop in looptris] for looptris in bm.calc_loop_triangles()]

    drawing_tris(coords, indices, color)


def draw_edges(obj=None, thickness=1, color=(1, 1, 1, 1), transform_2d=False):
    data = obj.data
    if len(data.vertices)<3:
        depsgraph = bpy.context.evaluated_depsgraph_get()
        obj_eval = obj.evaluated_get(depsgraph)
        data = obj_eval.data

    coords = [obj.matrix_world @ v.co for v in data.vertices]
    indices = [(e.vertices[0], e.vertices[1]) for e in data.edges]

    draw_line(coords, thickness, color, indices=indices, transform_2d=transform_2d)


def draw_all_circle_full(center_coord_list, r, color, segments):
    gpu.state.blend_set('ALPHA')
    theta = 2*math.pi/segments
    vertices = []
    indices = []
    center = 0
    for c in center_coord_list:
        cx = c[0]
        cy = c[1]
        vertices.append((cx,cy))
        for i in range(segments):
            vertices.append((math.cos(i*theta)*r+cx , math.sin(i*theta)*r+cy))
        for i in range(segments-1):
            indices.append((center, center+i+1, center+i+2))
        indices.append((center, center+segments, center+1))
        center += segments + 1

    if bpy.app.version >= (4, 0, 0):
        shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    else:
        shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
    batch = batch_for_shader(shader, 'TRIS', {"pos": vertices}, indices=indices)
    # shader.bind()
    shader.uniform_float("color", color)
    batch.draw(shader)
    gpu.state.blend_set('NONE')


class FLUENT_Draw_Object():

    def __init__(self, obj, color = (0.0, 0.643, 1, 0.05)):
        self.obj = obj
        self.depsgraph = bpy.context.evaluated_depsgraph_get()
        self.obj_evaluated = self.obj.evaluated_get(self.depsgraph)
        self.face_color = (color[0], color[1], color[2], color[3])

    def set_object(self, obj):
        self.obj = obj
        self.refresh_data()

    def get_object(self):
        return self.obj

    def refresh_data(self):
        self.obj_evaluated = self.obj.evaluated_get(self.depsgraph)

    def draw(self):
        if not self.obj.hide_viewport:
            draw_faces(self.obj_evaluated, self.face_color)
            draw_edges(self.obj_evaluated, color=(1, 1, 1, .75))


class FLUENT_Cursor_Infos():
    def __init__(self):
        self.text = [] #chaque élément du tableau est une ligne.
        self.text_size = get_addon_preferences().font_size * get_addon_preferences().interface_factor
        self.text_dimensions = [0, 0]

    def set_text(self, text):
        self.text = text # text doit être un tableau
        if bpy.app.version >= (4, 0, 0):
            blf.size(0, self.text_size)
        else:
            blf.size(0, self.text_size, 72)
        try:
            self.text_dimensions = blf.dimensions(0, text[0])
        except:
            pass

    def reset_text(self):
        self.text = []

    def draw(self, events):
        for index, t in enumerate(self.text):
            draw_text(text = t, text_pos = (events['mouse_x'] + 32, events['mouse_y'] - self.text_dimensions[1] - (index * self.text_dimensions[1] * 2)), text_size = self.text_size, text_color = (1, 1, 1, 1), align = 'LEFT')


class FLUENT_Draw_Dots():
    def __init__(self):
        self.dots = [] # pour chaque point un tableau [pos_x, pos_y, rayon, color]
        self.dots_3d = [] # pour chaque point [coords_3d, radius, colors]
        self.dots_2d = [] # pour chaque point un tableau [pos_x, pos_y, rayon, color]

    def set_dots(self, a):
        self.dots = a

    def clear_dots(self, what='ALL'):
        if what == 'ALL':
            self.dots = []
            self.dots_2d = []
            self.dots_3d = []
        if what == '2D':
            self.dots_2d = []
        if what == '3D':
            self.dots_3d = []

    def add_2d_dot(self, tab):
        self.dots_2d.append(tab)

    def add_3d_dot(self, coords_3d, radius, color):
        self.dots_3d.append([coords_3d, radius, color])

    def refresh_dots(self):
        self.dots = []
        self.dots = self.dots_2d.copy()
        region = bpy.context.region
        rv3d = bpy.context.region_data
        for d in self.dots_3d:
            co_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, d[0])
            self.dots.append([co_2d.x, co_2d.y, d[1], d[2]])

    def get_dots(self):
        return self.dots

    def is_hover(self, events):
        pass

    def get_state(self):
        pass

    def draw(self, events):
        self.refresh_dots()
        for d in self.dots:
            draw_circle_full(d[0], d[1], d[2], d[3], segments = 8)


class FLUENT_Draw_Lines():
    def __init__(self):
        self.lines = [] #pour chaque point un tableau [coords, thickness, color, is_2d]

    def set_lines(self, a):
        self.lines = a

    def get_lines(self):
        return self.lines

    def append_a_line(self, tab):
        self.lines.append(tab)

    def is_hover(self, events):
        pass

    def get_state(self):
        pass

    def draw(self, events):
        for d in self.lines:
            draw_line(coords = d[0], thickness = d[1], color = d[2], transform_2d=True)


class FLUENT_Panel_Infos():
        def __init__(self):
            self.text = [[],[]]
            self.text_size = get_addon_preferences().font_size * get_addon_preferences().interface_factor
            self.text_dimensions = [0, 0]
            self.cell_dimensions = [0,0]
            t_panel_width = 0
            for region in bpy.context.area.regions:
                if region.type == 'TOOLS':
                    t_panel_width = region.width
            self.origine = [8+t_panel_width, 128]
            self.highlight_color = get_addon_preferences().highlight_text

        def reset(self):
            self.text = [[],[]]

        def add_line(self, t1, t2 = '', reset = False):
            if reset:
                self.text = [[],[]]
            self.text[0].append(t1)
            self.text[1].append(t2)
            if bpy.app.version >= (4, 0, 0):
                blf.size(0, self.text_size)
            else:
                blf.size(0, self.text_size, 72)
            for i in self.text[0]:
                dim = blf.dimensions(0, i)
                if dim[0] > self.cell_dimensions[0]:
                    self.cell_dimensions[0] = dim[0]
                if dim[1] > self.cell_dimensions[1]:
                    self.cell_dimensions[1] = dim[1]

        def draw(self, events):
            for i, t in enumerate(self.text[0]):
                # première colonne
                pos_x = self.origine[0]
                pos_y = i * (self.cell_dimensions[1]*1.5) + self.origine[1]
                draw_text(text = self.text[0][-i-1], text_pos = (pos_x, pos_y), text_size = self.text_size, text_color = (1, 1, 1, 1), align = 'LEFT')
                # deuxième colonne
                pos_x = self.origine[0] + self.cell_dimensions[0] * 1.1
                draw_text(text = self.text[1][-i-1], text_pos = (pos_x, pos_y), text_size = self.text_size, text_color = self.highlight_color, align = 'LEFT')