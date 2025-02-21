import bpy, mathutils, math, gpu, time
from mathutils import Vector, Matrix, Quaternion
from gpu_extras.batch import batch_for_shader
from .... utility import math as hops_math
from .... utils.space_3d import get_3D_point_from_mouse, scene_ray_cast
from .... ui_framework.graphics.draw import render_text
from . import cast_to_plane, unit_scale


class Overall:
    '''Adjusting controller.'''

    def __init__(self, op):
        self.__setup(op)

    @property
    def length(self):
        return self.op.bounds.length(self.op.unit_length)

    @length.setter
    def length(self, val):
        self.op.bounds.set_anchor_point(self.op.anchor)
        if self.op.equalize:
            self.op.bounds.adjust_length_equalized(val, self.op.unit_length, self.length, self.width, self.height)
        else:
            self.op.bounds.adjust_length(val, self.op.unit_length)
        self.op.bounds.move_to_anchor_point(self.op.anchor)

    @property
    def width(self):
        return self.op.bounds.width(self.op.unit_length)

    @width.setter
    def width(self, val):
        self.op.bounds.set_anchor_point(self.op.anchor)
        if self.op.equalize:
            self.op.bounds.adjust_width_equalized(val, self.op.unit_length, self.length, self.width, self.height)
        else:
            self.op.bounds.adjust_width(val, self.op.unit_length)
        self.op.bounds.move_to_anchor_point(self.op.anchor)

    @property
    def height(self):
        return self.op.bounds.height(self.op.unit_length)

    @height.setter
    def height(self, val):
        self.op.bounds.set_anchor_point(self.op.anchor)
        if self.op.equalize:
            self.op.bounds.adjust_height_equalized(val, self.op.unit_length, self.length, self.width, self.height)
        else:
            self.op.bounds.adjust_height(val, self.op.unit_length)
        self.op.bounds.move_to_anchor_point(self.op.anchor)


    def __setup(self, op):
        self.length_pos = Vector()
        self.width_pos = Vector()
        self.height_pos = Vector()
        self.op = op


    def update(self, context, event, op):
        self.op = op
        self.bounds = op.bounds
        self.unit_length = op.unit_length


    def draw_2D(self, context, op):
        pass


    def draw_3D(self, op):
        pass

