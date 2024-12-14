import bpy, mathutils, math, gpu
from math import cos, sin
from mathutils import Vector
from gpu_extras.batch import batch_for_shader
from ..utility.screen import dpi_factor
from . space_3d import get_3D_point_from_mouse, get_2d_point_from_3d_point


class Axial:
    def __init__(self):
        # States
        self.open = False
        self.just_closed = False
        self.exit_val = None
        # 3D
        self.loc_spawn = Vector()
        # 2D
        self.loc_center = None
        built_in_shader = 'UNIFORM_COLOR' if bpy.app.version[0] >=4 else '2D_UNIFORM_COLOR'
        self.shader = gpu.shader.from_builtin(built_in_shader)
        # Outer ring
        self.radius = 60 * dpi_factor()
        self.outer_color = (1,1,1,.125)
        self.outer_verts = []
        self.outer_batch = None
        # Outer X
        self.x_loc = Vector((0,0))
        self.x_color = (1,0,0,.75)
        self.x_verts = []
        self.x_batch = None
        # Outer Y
        self.y_loc = Vector((0,0))
        self.y_color = (0,1,0,.75)
        self.y_verts = []
        self.y_batch = None
        # Outer Z
        self.z_loc = Vector((0,0))
        self.z_color = (0,0,1,.75)
        self.z_verts = []
        self.z_batch = None
        # Outer NEG X
        self.neg_x_loc = Vector((0,0))
        self.neg_x_color = (.5,0,0,.75)
        self.neg_x_verts = []
        self.neg_x_batch = None
        # Outer NEG Y
        self.neg_y_loc = Vector((0,0))
        self.neg_y_color = (0,.5,0,.75)
        self.neg_y_verts = []
        self.neg_y_batch = None
        # Outer NEG Z
        self.neg_z_loc = Vector((0,0))
        self.neg_z_color = (0,0,.5,.75)
        self.neg_z_verts = []
        self.neg_z_batch = None


    def update(self, context, event, callback):
        
        # Update open widget
        if self.open:
            self.__axial_change(context, event)
            return
        else:
            if self.just_closed:
                self.just_closed = False
                callback(self.exit_val)
                self.exit_val = None

        # Reset
        self.loc_center = None

        # Key control to open
        action = False
        if context.preferences.inputs.use_mouse_emulate_3_button:
            if event.type == 'C' and event.value == 'PRESS':
                action = True
        else:
            action = event.alt and event.value == 'PRESS'

        # Not supported
        if action:
            if context.region_data.is_orthographic_side_view:
                bpy.ops.hops.display_notification(info="Ortho side view not available")
                return

        if not action: return

        # Cast to view plane
        mouse_pos = Vector((event.mouse_region_x, event.mouse_region_y))
        view_quat = context.region_data.view_rotation
        view_normal = view_quat @ Vector((0,0,1))
        self.loc_spawn = get_3D_point_from_mouse(mouse_pos, context, Vector(), view_normal)

        # 2D screen space
        loc = get_2d_point_from_3d_point(context, self.loc_spawn)
        if not loc: return

        self.loc_center = loc
        self.open = True

        self.__setup_batches(context)
        return


    def __axial_change(self, context, event):
        mouse_pos = Vector((event.mouse_region_x, event.mouse_region_y))
        mag = (mouse_pos - self.loc_center).magnitude
        if mag > self.radius:
            self.open = False
            self.just_closed = True
            return

        mouse_pos = self.loc_center - mouse_pos
        vec_x = self.loc_center - self.x_loc
        vec_y = self.loc_center - self.y_loc
        vec_z = self.loc_center - self.z_loc
        vec_neg_x = self.loc_center - self.neg_x_loc
        vec_neg_y = self.loc_center - self.neg_y_loc
        vec_neg_z = self.loc_center - self.neg_z_loc

        # TODO: keep vecs with mag <= 0 out of list for ortho side views
        angles = [
            mouse_pos.angle(vec_x),
            mouse_pos.angle(vec_y),
            mouse_pos.angle(vec_z),
            mouse_pos.angle(vec_neg_x),
            mouse_pos.angle(vec_neg_y),
            mouse_pos.angle(vec_neg_z)]

        minpos = angles.index(min(angles)) 
        
        if minpos == 0:
            self.outer_color = self.x_color
            self.exit_val = 'X'
        elif minpos == 1:
            self.outer_color = self.y_color
            self.exit_val = 'Y'
        elif minpos == 2:
            self.outer_color = self.z_color
            self.exit_val = 'Z'
        if minpos == 3:
            self.outer_color = self.neg_x_color
            self.exit_val = '-X'
        elif minpos == 4:
            self.outer_color = self.neg_y_color
            self.exit_val = '-Y'
        elif minpos == 5:
            self.outer_color = self.neg_z_color
            self.exit_val = '-Z'


    def __setup_batches(self, context):
        self.__outer_batch()
        self.__x_batch(context)
        self.__y_batch(context)
        self.__z_batch(context)
        self.__neg_x_batch(context)
        self.__neg_y_batch(context)
        self.__neg_z_batch(context)


    def __outer_batch(self):
        self.outer_color = (1,1,1,.125)
        self.outer_verts = []
        segments = 32
        for i in range(segments):
            index = i + 1
            angle = i * 3.14159 * 2 / segments
            x = (cos(angle) * self.radius) + self.loc_center[0]
            y = (sin(angle) * self.radius) + self.loc_center[1]
            self.outer_verts.append((x, y))
        self.outer_verts.append(self.outer_verts[0])
        self.outer_batch = batch_for_shader(self.shader, 'LINE_STRIP', {"pos": self.outer_verts})


    def __x_batch(self, context):
        loc = get_2d_point_from_3d_point(context, self.loc_spawn + Vector((1,0,0)))
        if not loc: return

        loc -= self.loc_center
        loc.normalize()
        loc *= self.radius * .75
        loc += self.loc_center

        self.x_loc = loc
        self.x_verts = [self.loc_center, loc]
        self.x_batch = batch_for_shader(self.shader, 'LINE_STRIP', {"pos": self.x_verts})


    def __y_batch(self, context):
        loc = get_2d_point_from_3d_point(context, self.loc_spawn + Vector((0,1,0)))
        if not loc: return

        loc -= self.loc_center
        loc.normalize()
        loc *= self.radius * .75
        loc += self.loc_center

        self.y_loc = loc
        self.y_verts = [self.loc_center, loc]
        self.y_batch = batch_for_shader(self.shader, 'LINE_STRIP', {"pos": self.y_verts})


    def __z_batch(self, context):
        loc = get_2d_point_from_3d_point(context, self.loc_spawn + Vector((0,0,1)))
        if not loc: return

        loc -= self.loc_center
        loc.normalize()
        loc *= self.radius * .75
        loc += self.loc_center

        self.z_loc = loc
        self.z_verts = [self.loc_center, loc]
        self.z_batch = batch_for_shader(self.shader, 'LINE_STRIP', {"pos": self.z_verts})


    def __neg_x_batch(self, context):
        loc = get_2d_point_from_3d_point(context, self.loc_spawn + Vector((-1,0,0)))
        if not loc: return

        loc -= self.loc_center
        loc.normalize()
        loc *= self.radius * .75
        loc += self.loc_center

        self.neg_x_loc = loc
        self.neg_x_verts = [self.loc_center, loc]
        self.neg_x_batch = batch_for_shader(self.shader, 'LINE_STRIP', {"pos": self.neg_x_verts})


    def __neg_y_batch(self, context):
        loc = get_2d_point_from_3d_point(context, self.loc_spawn + Vector((0,-1,0)))
        if not loc: return

        loc -= self.loc_center
        loc.normalize()
        loc *= self.radius * .75
        loc += self.loc_center

        self.neg_y_loc = loc
        self.neg_y_verts = [self.loc_center, loc]
        self.neg_y_batch = batch_for_shader(self.shader, 'LINE_STRIP', {"pos": self.neg_y_verts})


    def __neg_z_batch(self, context):
        loc = get_2d_point_from_3d_point(context, self.loc_spawn + Vector((0,0,-1)))
        if not loc: return

        loc -= self.loc_center
        loc.normalize()
        loc *= self.radius * .75
        loc += self.loc_center

        self.neg_z_loc = loc
        self.neg_z_verts = [self.loc_center, loc]
        self.neg_z_batch = batch_for_shader(self.shader, 'LINE_STRIP', {"pos": self.neg_z_verts})


    def draw(self):
        if not self.open: return
        #Enable(GL_LINE_SMOOTH)
        gpu.state.blend_set('ALPHA')
        self.shader.bind()

        if self.outer_batch:
            gpu.state.line_width_set(2)
            self.shader.uniform_float("color", self.outer_color)
            self.outer_batch.draw(self.shader)
        if self.x_batch:
            gpu.state.line_width_set(4)
            self.shader.uniform_float("color", self.x_color)
            self.x_batch.draw(self.shader)
        if self.y_batch:
            gpu.state.line_width_set(4)
            self.shader.uniform_float("color", self.y_color)
            self.y_batch.draw(self.shader)
        if self.z_batch:
            gpu.state.line_width_set(4)
            self.shader.uniform_float("color", self.z_color)
            self.z_batch.draw(self.shader)
        if self.neg_x_batch:
            gpu.state.line_width_set(3)
            self.shader.uniform_float("color", self.neg_x_color)
            self.neg_x_batch.draw(self.shader)
        if self.neg_y_batch:
            gpu.state.line_width_set(3)
            self.shader.uniform_float("color", self.neg_y_color)
            self.neg_y_batch.draw(self.shader)
        if self.neg_z_batch:
            gpu.state.line_width_set(3)
            self.shader.uniform_float("color", self.neg_z_color)
            self.neg_z_batch.draw(self.shader)

        #Disable(GL_LINE_SMOOTH)
        gpu.state.blend_set('NONE')
