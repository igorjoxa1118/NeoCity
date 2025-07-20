import bpy, mathutils, math, gpu
from mathutils import Vector, Matrix, Quaternion
from gpu_extras.batch import batch_for_shader
from .... utility import math as hops_math
from . import cast_to_plane, State, ray_point

class Make_Primitive:
    '''Draws out the box primitive.'''

    def __init__(self):
        self.__setup()


    def __setup(self):
        built_in_shader = 'UNIFORM_COLOR' if bpy.app.version[0] >=4 else '3D_UNIFORM_COLOR'
        self.shader = gpu.shader.from_builtin(built_in_shader)
        self.point_batch = None
        self.line_batch = None
        self.corner_1 = False
        self.corner_2 = False
        self.corner_3 = False


    def update(self, context, event, op):
        if not self.corner_1:
            self.__corner_1(context, event, op)
        elif not self.corner_2:
            self.__corner_2(context, event, op)
        elif not self.corner_3:
            self.__corner_3(context, event, op)


    def __corner_1(self, context, event, op):

        loc = Vector((0,0,0))
        normal = Vector((0,0,1))
        point = ray_point(context, event, loc, normal)
        if not point:
            point = op.bounds.bot_front_left

        op.bounds.bot_front_left = point

        # Drawing
        self.point_batch = batch_for_shader(self.shader, 'POINTS', {'pos': [op.bounds.bot_front_left]})

        # Confirm
        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            self.corner_1 = True


    def __corner_2(self, context, event, op):
        loc = op.bounds.bot_front_left
        normal = Vector((0,0,1))
        point = ray_point(context, event, loc, normal)
        if not point:
            point = op.bounds.bot_back_right

        point[2] = op.bounds.bot_front_left[2]
        op.bounds.bot_back_right = point

        # Set other bottom points
        bfl = op.bounds.bot_front_left
        bbr = op.bounds.bot_back_right
        z = loc[2]

        op.bounds.bot_front_right = Vector((bbr[0], bfl[1], z))
        op.bounds.bot_back_left   = Vector((bfl[0], bbr[1], z))

        # Drawing
        self.point_batch = batch_for_shader(self.shader, 'POINTS', {'pos': op.bounds.bottom_points()})
        self.line_batch = batch_for_shader(self.shader, 'LINES', {'pos': op.bounds.gl_bottom_lines()})

        # Confirm
        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            self.corner_2 = True


    def __corner_3(self, context, event, op):
        center = (op.bounds.bot_front_left + op.bounds.bot_back_right) * .5
        view_quat = context.region_data.view_rotation
        up = Vector((0,0,1))
        view_normal = view_quat @ up
        view_normal[2] = 0
        view_normal.normalize()
        point = ray_point(context, event, center, view_normal)
        if not point:
            point = op.bounds.top_back_right

        # Set top points
        z = point[2]
        op.bounds.top_front_left  = Vector((op.bounds.bot_front_left[0] , op.bounds.bot_front_left[1] , z))
        op.bounds.top_front_right = Vector((op.bounds.bot_front_right[0], op.bounds.bot_front_right[1], z))
        op.bounds.top_back_left   = Vector((op.bounds.bot_back_left[0]  , op.bounds.bot_back_left[1]  , z))
        op.bounds.top_back_right  = Vector((op.bounds.bot_back_right[0] , op.bounds.bot_back_right[1] , z))

        # Drawing
        self.point_batch = batch_for_shader(self.shader, 'POINTS', {'pos': op.bounds.all_points()})
        self.line_batch = batch_for_shader(self.shader, 'LINES', {'pos': op.bounds.gl_all_lines()})

        # Confirm
        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            self.corner_3 = True
            op.state = State.ADJUSTING
            op.bounds_reset_copy.map_other_bounds(op.bounds)
            op.set_anchor(opt='BOTTOM')


    def reset(self):
        self.corner_1 = False
        self.corner_2 = False
        self.corner_3 = False


    def draw_2D(self, op):
        pass


    def draw_3D(self, op):
        if not self.point_batch: return

        if not self.corner_1:
            self.__draw_corner_1_3D(op)
        elif not self.corner_2:
            if not self.line_batch: return
            self.__draw_corner_2_3D(op)
        elif not self.corner_3:
            if not self.line_batch: return
            self.__draw_corner_3_3D(op)


    def __draw_corner_1_3D(self, op):
        gpu.state.blend_set('ALPHA')
        gpu.state.point_size_set(8)
        self.shader.bind()

        self.shader.uniform_float('color', (1,0,0,1))
        self.point_batch.draw(self.shader)


    def __draw_corner_2_3D(self, op):
        gpu.state.blend_set('ALPHA')
        #Enable(GL_LINE_SMOOTH)
        gpu.state.line_width_set(3)
        gpu.state.point_size_set(8)
        self.shader.bind()

        self.shader.uniform_float('color', (0,0,0,1))
        self.line_batch.draw(self.shader)

        self.shader.uniform_float('color', (1,0,0,1))
        self.point_batch.draw(self.shader)


    def __draw_corner_3_3D(self, op):
        #Enable(GL_LINE_SMOOTH)
        gpu.state.blend_set('ALPHA')
        gpu.state.line_width_set(3)
        gpu.state.point_size_set(8)
        self.shader.bind()

        self.shader.uniform_float('color', (0,0,0,1))
        self.line_batch.draw(self.shader)

        self.shader.uniform_float('color', (1,0,0,1))
        self.point_batch.draw(self.shader)
