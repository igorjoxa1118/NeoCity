import bpy, mathutils, math, gpu
from mathutils import Vector, Matrix, Quaternion
from gpu_extras.batch import batch_for_shader
from .... utility import math as hops_math
from .... utils.space_3d import get_2d_point_from_3d_point
from .... ui_framework.graphics.draw import render_text
from . import cast_to_plane, State
from . import ANCHORS
from .anchor_edit import Anchor_Edit
from .adjust_overall import Overall
from .adjust_move import Move

class Adjust:
    '''Adjusting controller.'''

    def __init__(self, op):
        self.anchor_edit = Anchor_Edit(op)
        self.overall = Overall(op)
        self.move = Move(op)
        self.__setup()


    def __setup(self):
        built_in_shader = 'UNIFORM_COLOR' if bpy.app.version[0] >= 4 else '3D_UNIFORM_COLOR'
        self.shader = gpu.shader.from_builtin(built_in_shader)
        self.point_batch = None
        self.line_batch = None

        self.face_batch = None

        self.length_pos = Vector()
        self.width_pos = Vector()
        self.height_pos = Vector()

        self.show_face = False
        self.show_move = False
        self.show_anchor_face = False
        self.show_anchor_edit = False


    def update(self, context, event, op):
        self.point_batch = batch_for_shader(self.shader, 'POINTS', {'pos': op.bounds.all_points()})
        self.line_batch = batch_for_shader(self.shader, 'LINES', {'pos': op.bounds.gl_all_lines()})

        self.__setup_2D_drawing(context, op)

        # Run locked state
        if self.move.locked:
            self.move.locked_update(context, event, op)
            return

        self.show_anchor_edit = False
        self.show_move = False
        self.show_anchor_face = False

        # Face Adjust
        if event.shift:
            self.show_anchor_edit = True
            self.anchor_edit.update(context, event, op)

            # No face in zone
            if self.anchor_edit.detection == False:
                self.show_anchor_edit = False
                self.__anchor_face(op)

        # Face Move
        elif not op.form.active():
            self.show_move = True
            self.move.update(context, event, op)

            # No face in zone
            if self.move.detection == False:
                self.show_move = False
                self.__anchor_face(op)

        # Anchor Face
        else:
            self.__anchor_face(op)

        # Overall
        self.overall.update(context, event, op)


    def __anchor_face(self, op):
        self.show_anchor_face = True

        if op.anchor == 'NONE':
            self.face_batch = None
            return

        index = ANCHORS.index(op.anchor)
        faces = op.bounds.faces()
        quad = faces[index]
        indices = [(0,1,2), (2,3,0)]
        self.face_batch = batch_for_shader(self.shader, 'TRIS', {'pos': quad}, indices=indices)


    def __setup_2D_drawing(self, context, op):
        bounds = op.bounds
        self.length_pos = bounds.bot_front_left.lerp(bounds.bot_front_right, .5)
        self.width_pos = bounds.bot_front_left.lerp(bounds.bot_back_left, .5)
        self.height_pos = bounds.bot_front_left.lerp(bounds.top_front_left, .5)


    def draw_2D(self, context, op):
        if self.show_anchor_edit:
            self.anchor_edit.draw_2D(context, op)
            return

        self.__draw_LWH(context)
        self.overall.draw_2D(context, op)


    def __draw_LWH(self, context):
        pos = get_2d_point_from_3d_point(context, self.length_pos)
        if pos: render_text(text="Length", position=pos, size=12, color=(1,1,0,1))
        pos = get_2d_point_from_3d_point(context, self.width_pos)
        if pos: render_text(text="Width", position=pos, size=12, color=(1,1,0,1))
        pos = get_2d_point_from_3d_point(context, self.height_pos)
        if pos: render_text(text="Height", position=pos, size=12, color=(1,1,0,1))


    def draw_3D(self, op):
        if self.show_anchor_edit:
            self.anchor_edit.draw_3D(op)

        elif self.move.locked or self.show_move:
            self.move.draw_3D(op)

        elif self.show_anchor_face:
            self.__draw_anchor_face_3D(op)

        self.overall.draw_3D(op)

        if not self.point_batch: return
        if not self.line_batch: return
        self.__draw_box_3D(op)


    def __draw_anchor_face_3D(self, op):
        if not self.face_batch: return
        self.shader.bind()
        #Enable(GL_LINE_SMOOTH)
        gpu.state.blend_set('ALPHA')

        self.shader.uniform_float('color', (0,0,1,.125))
        self.face_batch.draw(self.shader)


    def __draw_box_3D(self, op):
        #Enable(GL_LINE_SMOOTH)
        gpu.state.blend_set('ALPHA')
        gpu.state.line_width_set(3)
        gpu.state.point_size_set(8)
        self.shader.bind()

        self.shader.uniform_float('color', (0,0,0,1))
        self.line_batch.draw(self.shader)

        self.shader.uniform_float('color', (1,0,0,1))
        self.point_batch.draw(self.shader)
