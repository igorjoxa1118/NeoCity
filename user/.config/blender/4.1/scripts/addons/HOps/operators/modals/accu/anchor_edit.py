import bpy, mathutils, math, gpu, time
from mathutils import Vector, Matrix, Quaternion
from gpu_extras.batch import batch_for_shader
from .... utility import math as hops_math
from .... utils.space_3d import get_3D_point_from_mouse, scene_ray_cast, get_2d_point_from_3d_point
from .... ui_framework.graphics.draw import render_text
from . import cast_to_plane, unit_scale, get_face_index, build_face_batch, draw_face_3D
from . import ANCHORS

class Anchor_Edit:
    '''Adjusting controller.'''

    def __init__(self, op):
        self.__setup(op)


    def __setup(self, op):
        built_in_shader = 'UNIFORM_COLOR' if bpy.app.version[0] >=4 else '3D_UNIFORM_COLOR'
        self.shader = gpu.shader.from_builtin(built_in_shader)
        self.face_batch = None
        self.face_center = Vector((0,0,0))
        self.anchor_text = 'BOTTOM'
        self.detection = False
        self.op = op


    def update(self, context, event, op):
        self.op = op

        index = get_face_index(op, context, event)
        if index == None: 
            self.detection = False
            self.face_batch = None
            return
        
        self.detection = True
        face = op.bounds.faces()[index]
        self.build_batches(index, face)
        self.face_center = op.bounds.face_center(face)
        self.anchor_text = ANCHORS[index]
        
        # Lock for face
        if not op.form.active():
            if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
                op.set_anchor(opt=self.anchor_text)
                

    def build_batches(self, index, face):
        indices = [(0,1,2), (2,3,0)]
        self.face_batch = batch_for_shader(self.shader, 'TRIS', {'pos': face}, indices=indices)


    def draw_2D(self, context, op):
        pos = get_2d_point_from_3d_point(context, self.face_center)
        if pos: render_text(text=self.anchor_text, position=pos, size=18, color=(1,1,1,1))


    def draw_3D(self, op):
        if not self.face_batch: return
        self.shader.bind()
        #Enable(GL_LINE_SMOOTH)
        gpu.state.blend_set('ALPHA')

        self.shader.uniform_float('color', (0,0,1,.125))
        self.face_batch.draw(self.shader)