import time
import numpy

import bpy
import gpu

from bpy.types import SpaceView3D
from mathutils import Vector, Matrix

from ...... utility import method_handler, addon, shader, screen, object, math
from ...... addon import shader as _shader

from .. import tracked_states


def wire_width():
    preference = addon.preference()
    bc = bpy.context.scene.bc

    width = preference.display.wire_width * screen.dpi_factor(rounded=True, integer=True)
    if preference.display.wire_only and preference.display.thick_wire:
        width *= preference.display.wire_size_factor

    return round(width) if (not bc.shape or bc.shape.type == 'CURVE' or len(bc.shape.data.vertices) > 2) else round(width * 1.5)


class setup:
    handler = None

    exit: bool = False

    @staticmethod
    def polys(batch, shader, color, xray=False):
        shader.bind()
        shader.uniform_float('color', color)

        gpu.state.blend_set('ALPHA')

        if not xray:
            gpu.state.depth_test_set('LESS_EQUAL')
            gpu.state.face_culling_set('BACK')

        batch.draw(shader)

        gpu.state.depth_test_set('NONE')
        gpu.state.face_culling_set('NONE')
        gpu.state.blend_set('NONE')

    @staticmethod
    def lines(context, batch, shader, width, xray=False):
        shader.bind()
        shader.uniform_float('viewportSize', (context.area.width, context.area.height))
        shader.uniform_float('lineWidth', width)

        gpu.state.line_width_set(width)
        gpu.state.blend_set('ALPHA')

        if not xray:
            gpu.state.depth_test_set('LESS')

        batch.draw(shader)

        gpu.state.depth_test_set('NONE')
        gpu.state.blend_set('NONE')

    @staticmethod
    def element_snap(batch, shader, color, size):
        shader.bind()
        shader.uniform_float('color', color)

        gpu.state.depth_test_set('ALWAYS')
        gpu.state.blend_set('NONE')
        gpu.state.point_size_set(size)

        batch.draw(shader)

        gpu.state.depth_test_set('NONE')


    def __init__(self, op):
        preference = addon.preference()
        bc = bpy.context.scene.bc

        self.running = True
        self.name = bc.shape.name
        self.verts = []
        self.last = []
        self.verts_shell = []
        self.index_tri = []
        self.index_edge = []
        self.polygons = 0
        self.extract_fade = False

        self.mode = op.mode

        self.time = time.perf_counter()
        self.fade_time = preference.display.shape_fade_time_in * 0.001
        self.fade = bool(preference.display.shape_fade_time_in) or bool(preference.display.shape_fade_time_out)
        self.fade_type = 'IN' if bool(preference.display.shape_fade_time_in) else 'NONE'
        self.fade_exit = False
        self.alpha = 1.0 if self.fade_type == 'NONE' else 0.0

        uniform_color = 'UNIFORM_COLOR' if bpy.app.version[0] >= 4 else '3D_UNIFORM_COLOR'
        polyline_flat_color = 'POLYLINE_FLAT_COLOR' if bpy.app.version[0] >= 4 else '3D_POLYLINE_FLAT_COLOR'
        self.shaders = {
            'uniform': gpu.shader.from_builtin(uniform_color),
            'polylines': gpu.shader.from_builtin(polyline_flat_color)}
        self.batches = dict()

        _shader.handlers.append(self)

        setup = self.shader
        setup(polys=True, batch=True, operator=op)

        draw_arguments = (self.draw_handler, (op, bpy.context), 'WINDOW', 'POST_VIEW')
        self.handler = SpaceView3D.draw_handler_add(*draw_arguments)


    def shader(self, polys=False, batch=False, alpha=False, operator=None):
        preference = addon.preference() if alpha else None
        bc = bpy.context.scene.bc

        if self.running:
            self.running = bc.running

        if self.running and bc.shape:
            self.name = bc.shape.name

        ref_by_name = None
        if self.name in bpy.data.objects:
            ref_by_name = bpy.data.objects[self.name]

        shape = bc.shape if self.running else ref_by_name
        shape_matrix = shape.matrix_world if shape else Matrix()

        self.last = self.verts[:]

        if not bc.running and not self.fade_exit and self.fade_type == 'OUT':
            if preference.display.shape_fade_time_out_extract and bc.extract_name:
                self.shape = shape = bpy.data.objects[bc.extract_name]

                self.name = bc.extract_name
                self.last = []

                self.time = time.perf_counter()
                self.alpha = 1
                self.extract_fade = True

                bc.extract_name = ''

                shape_matrix = bc.extract_matrix
                polys = batch = True

            elif preference.display.shape_fade_time_out:
                polys = batch = True

            self.fade_exit = True

        if polys and shape:
            polygons = len(shape.data.polygons)

            if polygons != self.polygons:
                self.polygons = polygons

            local, loop_index, edge_index, mesh = object.mesh_coordinates(shape, local=True)
            coords = math.transform_coordinates(shape_matrix, local)

            if not len(self.last) or not numpy.array_equal(self.last, coords):
                self.verts, self.index_tri, self.index_edge = coords, loop_index, edge_index

                length = len(self.verts)
                normals = numpy.ones([length, 3], dtype='f', order='C')
                mesh.vertices.foreach_get('normal', numpy.reshape(normals, length * 3))

                self.verts = math.transform_coordinates(shape_matrix, local + (normals * 0.001))
                self.verts_shell = math.transform_coordinates(shape_matrix, local + (normals * 0.001))

        if alpha:
            current = 1.0 if not self.exit else 0.0

            if self.fade and self.fade_time:
                current = (time.perf_counter() - self.time) / self.fade_time

            if self.fade_type == 'IN':
                self.alpha = current if current < 1.0 else 1.0

                if current >= 1.0:
                    self.fade_type = 'NONE'

            elif self.fade_type == 'OUT':
                self.alpha = 1.0 - current

                if self.alpha <= 0.0:
                    self.fade_type = 'NONE'
                    self.fade = False

            elif self.fade_type == 'NONE':
                if self.fade and self.exit:
                    self.fade_time = (preference.display.shape_fade_time_out if not self.extract_fade else preference.display.shape_fade_time_out_extract) * 0.001
                    self.time = time.perf_counter()
                    current = 0.0

                    self.fade_type = 'OUT'

        preference = addon.preference()

        self.color = Vector(getattr(preference.color, operator.mode.lower())) if not self.extract_fade else Vector(preference.color.extract_fade)
        self.color[3] = self.color[3] * self.alpha

        self.negative_color = Vector(preference.color.negative)
        self.negative_color[3] = self.negative_color[3] * self.alpha

        self.wire_color = Vector(preference.color.show_shape_wire[:]) if (preference.behavior.show_shape or (preference.display.show_shape_wire and hasattr(bc.operator, 'shift') and bc.operator.shift)) else Vector(preference.color.wire[:])
        self.wire_color[3] = self.wire_color[3] * self.alpha

        inset_bevel = bc.shape and bc.shape.data.bc.inset_bevel
        wire_only = preference.display.wire_only or (bc.operator.mode == 'INSET' and inset_bevel) or ((bc.operator.mode == 'MAKE' or tracked_states.make_fallback) and not preference.behavior.hide_make_shapes)
        color = self.color if wire_only else self.wire_color
        show_shape_wire = preference.behavior.show_shape or (preference.display.show_shape_wire and hasattr(bc.operator, 'shift') and bc.operator.shift)
        wire_color = Vector(color if not preference.color.wire_use_mode or show_shape_wire else self.color)
        wire_color[3] *= 0.5

        mode_color = (color[0], color[1], color[2], wire_color[3])
        shell_color = color if not preference.color.wire_use_mode or show_shape_wire else mode_color

        self.wire_color_set = [wire_color for _ in range(len(self.verts))]
        self.shell_color_set = [shell_color for _ in range(len(self.verts_shell))]

        force_batch = tracked_states.shader_batch

        if batch and (not len(self.last) or not numpy.array_equal(self.last, self.verts) or force_batch):
            uniform = self.shaders['uniform']
            polylines = self.shaders['polylines']
            verts = {'pos': self.verts}
            atributes = {'pos': self.verts, 'color': self.wire_color_set}
            atributes_shel = {'pos': self.verts_shell, 'color': self.shell_color_set}
            edges = self.index_edge
            self.batches = {
                'polys': shader.batch(uniform, 'TRIS', verts, indices=self.index_tri),
                'lines': shader.batch(polylines, 'LINES', atributes, indices=edges),
                'shell': shader.batch(polylines, 'LINES', atributes_shel, indices=edges)}

        if force_batch:
            tracked_states.shader_batch = False

        if bc.running:
            bc_op = bc.operator
            a, b = bc_op.last['wedge_points']
            # assumes no mods on lattice
            matrix = bc.lattice.matrix_world if bc.lattice else Matrix.Diagonal((0, 0, 0, 0))
            line = [
                matrix @ bc.lattice.data.points[a].co_deform,
                matrix @ bc.lattice.data.points[b].co_deform,
            ]
            color = Vector((1, 1, 1, 1)) - Vector(wire_color)
            color.w = 1
            atributes = {'pos':line, 'color': (color, color)}
            self.batches['wedge'] = shader.batch(self.shaders['polylines'], 'LINES', atributes)

            if bc_op.element_snap_vec is not None:
                atributes = {'pos':[ bc.shape.matrix_world @ bc_op.element_snap_vec]}
                self.batches['element_snap'] = shader.batch(self.shaders['uniform'], 'POINTS', atributes)


    def draw(self, op, context):
        method_handler(
            self.draw_handler,
            arguments = (op, context),
            identifier = 'Shape Shader',
            exit_method = self.remove)


    def draw_handler(self, op, context):
        preference = addon.preference()
        bc = context.scene.bc

        color = Vector(self.color)
        negative_color = Vector(self.negative_color)

        uniform = self.shaders['uniform']
        polylines = self.shaders['polylines']
        polys = self.batches['polys']
        lines = self.batches['lines']
        shell = self.batches['shell']

        inset_bevel = bc.shape and bc.shape.data.bc.inset_bevel
        wire_only = preference.display.wire_only or (bc.operator.mode == 'INSET' and inset_bevel) or ((bc.operator.mode == 'MAKE' or tracked_states.make_fallback) and not preference.behavior.hide_make_shapes)
        if wire_only or len(self.verts) < 3:
            if self.polygons:
                negative_color[3] *= 0.5
                self.polys(polys, uniform, negative_color, xray=True)

        else:
            if self.polygons or op.shape_type == 'CIRCLE':
                self.polys(polys, uniform, negative_color, xray=True)
                self.polys(polys, uniform, color, xray=self.polygons == 1)

        self.lines(context, lines, polylines, wire_width(), xray=True)
        self.lines(context, shell, polylines, wire_width())

        if bc.running and addon.preference().shape.wedge and not bc.operator.draw_line:
            wedge = self.batches['wedge']
            self.lines(context, wedge, polylines, wire_width() * 2, xray=True)

        element_snap = self.batches.get('element_snap', None)

        if element_snap:
            size = preference.display.snap_dot_size * screen.dpi_factor()
            x, y, z = context.preferences.themes[0].view_3d.object_active
            self.element_snap(element_snap, uniform, Vector((x, y, z, 1.0)), size)

    def update(self, op, context):
        method_handler(
            self.update_handler,
            arguments = (op, context),
            identifier = 'Shape Shader Update',
            exit_method = self.remove)


    def update_handler(self, op, context):
        if not self.exit:
            self.mode = op.mode

        setup = self.shader
        setup(polys=not self.exit, batch=not self.exit, alpha=True, operator=op)


    def remove(self, force=True):
        if self.handler:
            SpaceView3D.draw_handler_remove(self.handler, 'WINDOW')
            self.handler = None

            if bpy.context.area:
                bpy.context.area.tag_redraw()

            _shader.handlers = [handler for handler in _shader.handlers if handler != self]
