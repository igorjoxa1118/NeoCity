import bpy, mathutils, math, gpu, time
from mathutils import Vector, Matrix, Quaternion
from .... utility import math as hops_math
from .... utils.space_3d import get_3D_point_from_mouse, scene_ray_cast, get_2d_point_from_3d_point
from .... ui_framework.graphics.draw import render_text
from . import cast_to_plane, unit_scale, get_face_index, build_face_batch, draw_face_3D, ray_point
from . import ANCHORS

class Move:
    '''Adjusting controller.'''

    def __init__(self, op):
        self.__setup(op)


    def __setup(self, op):
        built_in_shader = 'UNIFORM_COLOR' if bpy.app.version[0] >= 4 else '3D_UNIFORM_COLOR'
        self.shader = gpu.shader.from_builtin(built_in_shader)
        self.face_batch = None
        self.point_batch = None

        self.locked = False
        self.face_index = 0
        self.detection = False

        self.op = op


    def update(self, context, event, op):
        self.op = op

        index = get_face_index(op, context, event)
        if index == None: 
            self.detection = False
            return
        
        self.detection = True
        
        # Build batch
        self.face_index = index
        self.build_batches()

        # Lock for face
        if not op.form.active():
            if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
                self.locked = True
                op.equalize = False
                op.set_anchor(opt=ANCHORS[self.face_index])


    def build_batches(self):
        build_face_batch(self)


    def locked_update(self, context, event, op):
        if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            self.locked = False
            return

        face_points = op.bounds.faces()[self.face_index]
        center = op.bounds.face_center(face_points)
        view_quat = context.region_data.view_rotation
        view_normal = context.region_data.view_rotation @ Vector((0,0,1))
        view_normal.normalize()
        opt = ['TOP', 'BOTTOM', 'LEFT', 'RIGHT', 'FRONT', 'BACK'][self.face_index]
        point = ray_point(context, event, center, view_normal)
        op.bounds.move_face(face=opt, position=point)
        self.build_batches()


    def draw_2D(self, context, op):
        pass


    def draw_3D(self, op):
        draw_face_3D(self)