import bpy, mathutils, math, gpu, bmesh
from math import cos, sin
from mathutils import Vector, Matrix
from gpu_extras.batch import batch_for_shader
from enum import Enum
from ... utility import addon
from ... utility.base_modal_controls import Base_Modal_Controls, numpad_types
from ... ui_framework.master import Master
from ... ui_framework.utils.checks import is_mouse_in_quad
from ... utils.toggle_view3d_panels import collapse_3D_view_panels
from ... utility import method_handler
from ... utils.space_3d import get_3D_point_from_mouse, scene_ray_cast, get_2d_point_from_3d_point
from ...utility.screen import dpi_factor


class Widget:
    def __init__(self):
        # Dims
        self.x_offset = 128 * dpi_factor()
        self.y_offset = 128 * dpi_factor()
        self.loc = Vector((self.x_offset, self.y_offset))
        self.radius = 18 * dpi_factor()
        # Shader
        built_in_shader = 'UNIFORM_COLOR' if bpy.app.version[0] >=4 else '2D_UNIFORM_COLOR'
        self.shader = gpu.shader.from_builtin(built_in_shader)
        # Center
        self.center_batch = None
        self.center_color = (1,1,1,.25)
        self.center_bounds = []
        self.center_loc = Vector((0,0))
        self.center_setup()
        # Line : 1
        self.l1_batch = None
        self.l1_color = (1,1,1,.25)
        self.l1_setup()
        # Mirror
        self.mirror_batch = None
        self.mirror_color = (1,1,1,.25)
        self.mirror_bounds = []
        self.mirror_loc = Vector((0,0))
        self.mirror_setup()
        # State
        self.mouse_is_over = False
        self.center_active = False
        self.circle_active = False


    def center_setup(self):
        width = self.radius * 2
        x = self.loc[0]
        y = self.loc[1] + self.radius * 4
        points = [
            Vector((x, y)),
            Vector((x, y + width))]
        indices = [(0,1)]
        self.center_batch = batch_for_shader(self.shader, 'LINES', {'pos': points}, indices=indices)

        pad = 10 * dpi_factor()
        self.center_bounds = (
            (x - pad, y + width),
            (x - pad, y),
            (x + pad, y + width),
            (x + pad, y))

        self.center_loc = Vector((x, self.loc[1] + self.radius * 2))


    def l1_setup(self):
        width = self.radius * 2
        x = self.loc[0] - self.radius
        y = self.loc[1] + self.radius * 3.5
        points = [
            Vector((x, y)),
            Vector((x + width, y))]
        indices = [(0,1)]
        self.l1_batch = batch_for_shader(self.shader, 'LINES', {'pos': points}, indices=indices)


    def mirror_setup(self):
        width = self.radius * 2
        x = self.loc[0] - self.radius
        y = self.loc[1] + self.radius

        self.mirror_bounds = (
            (x, y + width),
            (x, y),
            (x + width, y + width),
            (x + width, y))

        self.mirror_loc = Vector((self.loc[0], self.loc[1] + self.radius * .5))

        x1 = x + width * .25
        x2 = x + width * .75
        x3 = x + width * .5

        points = (
            (x, y),
            (x1, y + width),
            (x3, y),
            (x2, y + width),
            (x + width, y)
        )
        indices = [(0,1), (1,2), (2,3), (3,4)]
        self.mirror_batch = batch_for_shader(self.shader, 'LINES', {'pos': points}, indices=indices)


    def update(self, context, event):

        mouse_pos = Vector((event.mouse_region_x, event.mouse_region_y))

        # Center
        if is_mouse_in_quad(self.center_bounds, mouse_pos):
            self.center_active = True
            self.center_color = (1,1,1,1)
        else:
            self.center_active = False
            self.center_color = (1,1,1,.25)

        # Mirror
        if is_mouse_in_quad(self.mirror_bounds, mouse_pos):
            self.mirror_active = True
            self.mirror_color = (1,1,1,1)
        else:
            self.mirror_active = False
            self.mirror_color = (1,1,1,.25)


    def draw(self):
        # GL Settings
        #Enable(GL_LINE_SMOOTH)
        gpu.state.blend_set('ALPHA')
        gpu.state.line_width_set(3)
        self.shader.bind()
        # Center
        self.shader.uniform_float('color', self.center_color)
        self.center_batch.draw(self.shader)
        # Line 1
        self.shader.uniform_float('color', self.l1_color)
        self.l1_batch.draw(self.shader)
        # Mirror
        self.shader.uniform_float('color', self.mirror_color)
        self.mirror_batch.draw(self.shader)


class Boarder:

    def __init__(self, context):
        width = context.area.width
        height = context.area.height
        pad = 15 * dpi_factor(min=.5)
        self.width = 4
        self.color = (.5, .5, .5, 1)

        self.points = [
            (pad, pad),
            (pad , height - pad * 2),
            (width - pad * 2, height - pad * 2),
            (width - pad * 2, pad)]

        indices = ((0,1), (1,2), (2,3), (3,0))
        built_in_shader = 'UNIFORM_COLOR' if bpy.app.version[0] >=4 else '2D_UNIFORM_COLOR'
        self.shader = gpu.shader.from_builtin(built_in_shader)
        self.batch = batch_for_shader(self.shader, 'LINES', {"pos": self.points}, indices=indices)


    def draw(self):
        #Enable(GL_LINE_SMOOTH)
        gpu.state.blend_set('ALPHA')
        gpu.state.line_width_set(self.width)

        self.shader.bind()
        self.shader.uniform_float("color", self.color)
        self.batch.draw(self.shader)

        gpu.state.line_width_set(1)
        gpu.state.blend_set('NONE')


class State(Enum):
    FIRST = 0
    SECOND = 1
    ADJUST = 2


DESC = """Sculpt Arms

Add appendages

Press H for help"""


class HOPS_OT_Sculpt_Arms(bpy.types.Operator):
    bl_idname = "hops.sculpt_arms"
    bl_label = "Sculpt Arms"
    bl_description = DESC
    bl_options = {"REGISTER", "UNDO", "BLOCKING"}

    @classmethod
    def poll(cls, context):
        if context.active_object:
            if context.active_object.type == 'MESH':
                if context.mode in {'SCULPT', 'OBJECT'}:
                    return True
        return False


    def invoke(self, context, event):

        # States
        self.og_mode = context.mode
        self.state = State.FIRST
        self.exit_on_click = False
        self.exit_distance = 150 * dpi_factor(min=.5)
        self.dyno_exit = False
        if context.mode == 'SCULPT':
            self.dyno_exit = True if bpy.context.sculpt_object.use_dynamic_topology_sculpting else False
        self.centering = False

        # Locks
        self.move_locked = False
        self.move_lock_index = None
        self.scale_locked = False
        self.scale_locked_index = None
        self.scale_locked_mouse_start = Vector((0,0))

        # Props
        self.target_obj = context.active_object
        self.obj = None
        self.bm = None
        self.cast_location = Vector()
        self.subd_mod = None
        self.mirror_mod = None
        self.separate = False

        # Widgets
        self.boarder = Boarder(context)
        self.widget = Widget()
        self.can_widget_center = True
        self.can_widget_mirror = True

        # Drawing
        built_in_shader = 'UNIFORM_COLOR' if bpy.app.version[0] >=4 else '3D_UNIFORM_COLOR'
        self.shader_3d = gpu.shader.from_builtin(built_in_shader)
        self.graphics_setup()
        self.closest_point = None

        # Setup
        self.create_mesh(context)
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        context.view_layer.objects.active = self.obj
        bpy.ops.object.mode_set(mode='EDIT')

        # Systems
        self.master = Master(context=context)
        self.master.only_use_fast_ui = True
        self.base_controls = Base_Modal_Controls(context, event)
        self.original_tool_shelf, self.original_n_panel = collapse_3D_view_panels(force=True)
        self.draw_handle_2D = bpy.types.SpaceView3D.draw_handler_add(self.safe_draw_2D, (context,), 'WINDOW', 'POST_PIXEL')
        self.draw_handle_3D = bpy.types.SpaceView3D.draw_handler_add(self.safe_draw_3D, (context,), 'WINDOW', 'POST_VIEW')

        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}


    def modal(self, context, event):

        # --- Systems --- #
        self.master.receive_event(event=event)
        self.base_controls.update(context, event)

        #--- Widgets ---#
        self.update_widget(context, event)

        # --- Controls --- #
        if self.base_controls.pass_through:
            return {'PASS_THROUGH'}

        elif event.type in {'WHEELUPMOUSE', 'WHEELDOWNMOUSE'} or event.type in numpad_types:
            return {'PASS_THROUGH'}

        elif self.base_controls.cancel:
            return self.cancel_exit(context)

        elif event.type in {'SPACE', 'RET', 'NUMPAD_ENTER'}:
            return self.confirm_exit(context)

        elif event.type == 'S' and event.value == 'PRESS':
            if self.state == State.ADJUST:
                if self.subd_mod.levels == 0:
                    self.subd_mod.levels = 1
                elif self.subd_mod.levels == 1:
                    self.subd_mod.levels = 2
                elif self.subd_mod.levels == 2:
                    self.subd_mod.levels = 0

        elif event.type in {'X', 'ONE'} and event.value == 'PRESS':
            self.cycle_mirror()

        elif event.type == 'C' and event.value == 'PRESS':
            self.centering = not self.centering

        elif event.type == 'P' and event.value == 'PRESS':
            self.separate = not self.separate

        self.bm = bmesh.from_edit_mesh(self.obj.data)

        # Exit on Click
        self.exit_on_click = self.mouse_out_of_bounds(event, context)
        if self.exit_on_click:
            if self.base_controls.confirm:
                return self.confirm_exit(context)

        # FIRST
        if self.state == State.FIRST:
            self.set_cast_location(context, event)

            if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
                self.state = State.SECOND
                self.bm.verts.new(self.cast_location)

        # SECOND
        elif self.state == State.SECOND:
            self.set_cast_location(context, event)
            self.second_point = self.cast_location

            if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
                self.state = State.ADJUST

                self.bm.verts.ensure_lookup_table()

                v1 = self.bm.verts[0]
                v2 = self.bm.verts.new(self.cast_location)

                self.bm.edges.new((v1, v2))

                self.obj.modifiers.new('Skin', 'SKIN')
                self.subd_mod = self.obj.modifiers.new('Subsurf', 'SUBSURF')
                self.subd_mod.levels = 1

                self.mirror_mod = self.obj.modifiers.new('Mirror', 'MIRROR')
                self.mirror_mod.use_axis[0] = False
                self.mirror_mod.use_bisect_axis[0] = False
                self.mirror_mod.use_bisect_flip_axis[0] = False
                self.mirror_mod.mirror_object = self.target_obj

        # ADJUST
        elif self.state == State.ADJUST:

            index = self.vert_index_under_mouse(context, event)
            if index != None:
                self.closest_point = self.obj.matrix_world @ self.bm.verts[index].co

            self.adjust_controls(context, event)

        bmesh.update_edit_mesh(self.obj.data)

        self.interface(context)
        context.area.tag_redraw()
        return {"RUNNING_MODAL"}


    def interface(self, context):
        self.master.setup()
        if not self.master.should_build_fast_ui(): return

        win_list = []
        w_append = win_list.append

        if self.state == State.FIRST:
            w_append('Adding')

        elif self.state == State.SECOND:
            w_append('Adding')

        elif self.state == State.ADJUST:
            w_append('Adjusting')
            w_append(f'SubD : {self.subd_mod.levels}')
            w_append(f'Mirror : {self.mirror_mod.use_axis[0]}')
            w_append('Separate' if self.separate else 'Join')

        # Help
        help_items = {"GLOBAL" : [], "STANDARD" : []}
        help_items["GLOBAL"] = [
            ("M", "Toggle mods list"),
            ("H", "Toggle help"),
            ("~", "Toggle UI Display Type"),
            ("O", "Toggle viewport rendering")]

        help_items["STANDARD"] = []
        h_append = help_items["STANDARD"].append

        if self.state == State.FIRST:
            h_append(('Click', 'Add First Point'))

        elif self.state == State.SECOND:
            h_append(('Click', 'Add Second Point'))

        elif self.state == State.ADJUST:
            h_append(('Drag', 'Move Points'))
            h_append(('Shift Drag', 'Scale Points'))
            h_append(('Ctrl Drag', 'Extrude Points'))
            h_append(('S', 'Subdivide Levels'))
            h_append(('X', 'Mirror X'))
            h_append(('C', f'Center {self.centering}'))

        h_append(('P', f'Separate' if not self.separate else 'Join'))

        help_items["STANDARD"].reverse()

        self.master.receive_fast_ui(win_list=win_list, help_list=help_items, image="Array")

        self.master.finished()

    #--- UTILS ---#

    def create_mesh(self, context):
        mesh = bpy.data.meshes.new("HopsMesh")
        self.obj = bpy.data.objects.new("HopsObj", mesh)
        context.collection.objects.link(self.obj)


    def mouse_out_of_bounds(self, event, context):
        if self.state != State.ADJUST: return False

        points = []
        for vert in self.bm.verts:
            point = get_2d_point_from_3d_point(context, self.obj.matrix_world @ vert.co)
            if not point: continue
            points.append(point)
        if not points: return

        mouse = Vector((event.mouse_region_x, event.mouse_region_y))
        validations = []
        for point in points:
            mag = (point - mouse).magnitude
            validations.append(mag < self.exit_distance)

        return not any(validations)


    def set_cast_location(self, context, event):

        hit, location, normal, index, object, matrix = scene_ray_cast(context, event)
        if hit:
            self.cast_location = location
            return

        self.cast_location = self.plane_cast(context, event, self.cast_location)


    def plane_cast(self, context, event, plane_co):
        if self.centering:
            normal = self.target_obj.matrix_world.decompose()[1] @ Vector((1,0,0))
            plane_co = self.target_obj.matrix_world.translation
            mouse_pos = (event.mouse_region_x, event.mouse_region_y)
            return get_3D_point_from_mouse(mouse_pos, context, plane_co, normal)

        view_quat = context.region_data.view_rotation
        up = Vector((0,0,1))
        view_normal = view_quat @ up
        mouse_pos = (event.mouse_region_x, event.mouse_region_y)
        return get_3D_point_from_mouse(mouse_pos, context, plane_co, view_normal)


    def adjust_controls(self, context, event):

        # Stop Locks
        if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            self.close_locks()

        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':

            # Scale
            if event.shift:
                index = self.vert_index_under_mouse(context, event)
                if index == None: return
                self.scale_locked_index = index
                self.scale_locked = True
                self.scale_locked_mouse_start = Vector((event.mouse_region_x, event.mouse_region_y))

            # Extrude
            if event.ctrl:
                index = self.vert_index_under_mouse(context, event)
                if index == None: return

                self.bm.verts.ensure_lookup_table()
                v1 = self.bm.verts[index]
                self.cast_location = self.obj.matrix_world @ v1.co
                v2 = self.bm.verts.new(self.cast_location)

                self.bm.edges.new((v1, v2))

                self.move_locked = True
                self.bm.verts.ensure_lookup_table()
                self.move_lock_index = v2.index

            # Move
            else:
                index = self.vert_index_under_mouse(context, event)
                if index == None: return
                self.move_lock_index = index
                self.move_locked = True

        # SCALE
        if self.scale_locked:
            self.scale(context, event)
            return

        # MOVE
        if self.move_locked:
            self.move(context, event)
            return


    def scale(self, context, event):
        if self.scale_locked_index == None:
            self.close_locks()
            return

        vert = self.bm.verts[self.scale_locked_index]
        mouse = Vector((event.mouse_region_x, event.mouse_region_y))
        scale = (self.scale_locked_mouse_start - mouse).magnitude * .01 * dpi_factor(min=.5)

        if scale < .01:
            scale = .01

        layer = self.bm.verts.layers.skin.verify()
        data = vert[layer]
        data.radius = (scale, scale)


    def move(self, context, event):
        if self.move_lock_index == None:
            self.close_locks()
            return

        vert = self.bm.verts[self.move_lock_index]
        location = self.plane_cast(context, event, self.obj.matrix_world @ vert.co)
        vert.co = location


    def vert_index_under_mouse(self, context, event):
        self.bm.verts.ensure_lookup_table()

        vert_map = {}
        for vert in self.bm.verts:
            point = get_2d_point_from_3d_point(context, self.obj.matrix_world @ vert.co)
            if not point: continue
            vert_map[vert.index] = point

        if not vert_map: return None

        mouse = Vector((event.mouse_region_x, event.mouse_region_y))
        compare = None
        ret_index = None
        for index, point in vert_map.items():
            mag = (point - mouse).magnitude
            if compare == None or mag < compare:
                compare = mag
                ret_index = index

        return ret_index


    def close_locks(self):
        self.move_locked = False
        self.move_lock_index = None
        self.scale_locked = False
        self.scale_locked_index = None


    def cycle_mirror(self):

        if not self.mirror_mod: return

        # Right Side
        if not self.mirror_mod.use_axis[0]:
            self.mirror_mod.use_axis[0] = True
            self.mirror_mod.use_bisect_axis[0] = True
            self.mirror_mod.use_bisect_flip_axis[0] = False
            bpy.ops.hops.display_notification(info="Right Side Mirror")

        # Left Side
        elif self.mirror_mod.use_axis[0] and not self.mirror_mod.use_bisect_flip_axis[0]:
            self.mirror_mod.use_axis[0] = True
            self.mirror_mod.use_bisect_axis[0] = True
            self.mirror_mod.use_bisect_flip_axis[0] = True
            bpy.ops.hops.display_notification(info="Left Side Mirror")

        # Off
        elif self.mirror_mod.use_axis[0] and self.mirror_mod.use_bisect_flip_axis[0]:
            self.mirror_mod.use_axis[0] = False
            self.mirror_mod.use_bisect_axis[0] = False
            self.mirror_mod.use_bisect_flip_axis[0] = False
            bpy.ops.hops.display_notification(info="Mirror Off")


    def graphics_setup(self):
        self.center_verts = []

        self.center_indices_lines = []
        self.center_batch_lines = None

        self.center_indices_tris = []
        self.center_batch_tris = None

        rotation = self.target_obj.matrix_world.decompose()[1]
        radius = max(self.target_obj.dimensions[:])

        # Verts
        segments = 64
        for i in range(segments):
            index = i + 1
            angle = i * 6.28318 / segments
            y = cos(angle) * radius
            z = sin(angle) * radius
            vert = Vector((0, y, z))
            vert = rotation @ vert
            vert += self.target_obj.matrix_world.translation
            self.center_verts.append(vert)
            # Line indices
            if(index == segments): self.center_indices_lines.append((i, 0))
            else: self.center_indices_lines.append((i, i + 1))

        # Line batch
        self.center_batch_lines = batch_for_shader(self.shader_3d, 'LINES', {'pos': self.center_verts}, indices=self.center_indices_lines)

        # Tri indices
        for i in range(len(self.center_verts) - 1):
            self.center_indices_tris.append((0, i, i + 1))

        # Tri batch
        self.center_batch_tris = batch_for_shader(self.shader_3d, 'TRIS', {'pos': self.center_verts}, indices=self.center_indices_tris)

    #--- WIDGET ---#

    def update_widget(self, context, event):
        if self.state != State.ADJUST:
            return

        mouse_pos = Vector((event.mouse_region_x, event.mouse_region_y))
        if self.can_widget_center == False:
            if (self.widget.center_loc - mouse_pos).magnitude > 90 * dpi_factor():
                self.can_widget_center = True
        if self.can_widget_mirror == False:
            if (self.widget.mirror_loc - mouse_pos).magnitude > 90 * dpi_factor():
                self.can_widget_mirror = True

        self.widget.update(context, event)

        if self.widget.center_active:
            if self.can_widget_center:
                self.can_widget_center = False
                self.centering = not self.centering
        if self.widget.mirror_active:
            if self.can_widget_mirror:
                self.can_widget_mirror = False
                self.cycle_mirror()

    #--- EXITS ---#

    def common_exit(self, context):
        if self.og_mode == 'SCULPT':
            if context.mode != 'SCULPT':
                bpy.ops.object.mode_set(mode='SCULPT')

            if self.dyno_exit:
                bpy.ops.sculpt.dynamic_topology_toggle()

        self.remove_shaders()
        collapse_3D_view_panels(self.original_tool_shelf, self.original_n_panel, force=True)
        self.master.run_fade()


    def confirm_exit(self, context):

        # Update Mesh
        bmesh.update_edit_mesh(self.obj.data)

        # Object Mode / Flush
        bpy.ops.object.mode_set(mode='OBJECT')

        if self.og_mode != 'OBJECT':
            bpy.ops.object.select_all(action='DESELECT')

            # Apply Mods
            context.view_layer.objects.active = self.obj
            self.obj.select_set(True)
            bpy.ops.object.convert(target='MESH')

            if self.separate:
                self.target_obj.select_set(False)
                self.obj.select_set(True)
                context.view_layer.objects.active = self.obj

            else:
                # Join
                self.target_obj.select_set(True)
                context.view_layer.objects.active = self.target_obj
                self.obj.select_set(True)
                bpy.ops.object.join()

        else:
            self.obj.select_set(True)
            context.view_layer.objects.active = self.obj


        self.common_exit(context)
        return {'FINISHED'}


    def cancel_exit(self, context):
        bmesh.update_edit_mesh(self.obj.data)
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        context.view_layer.objects.active = self.target_obj
        self.target_obj.select_set(True)

        self.common_exit(context)

        if self.obj:
            mesh = self.obj.data
            bpy.data.objects.remove(self.obj)
            bpy.data.meshes.remove(mesh)

        return {'CANCELLED'}

    #--- SHADERS ---#

    def remove_shaders(self):
        if self.draw_handle_2D:
            self.draw_handle_2D = bpy.types.SpaceView3D.draw_handler_remove(self.draw_handle_2D, "WINDOW")
        if self.draw_handle_3D:
            self.draw_handle_3D = bpy.types.SpaceView3D.draw_handler_remove(self.draw_handle_3D, "WINDOW")


    def safe_draw_2D(self, context):
        method_handler(self.draw_shader_2D,
            arguments = (context,),
            identifier = 'Modal Shader 2D',
            exit_method = self.remove_shaders)


    def draw_shader_2D(self, context):
        if self.exit_on_click:
            self.boarder.draw()

        if self.state == State.ADJUST:
            self.widget.draw()


    def safe_draw_3D(self, context):
        method_handler(self.draw_shader_3D,
            arguments = (context,),
            identifier = 'Modal Shader 3D',
            exit_method = self.remove_shaders)


    def draw_shader_3D(self, context):

        self.shader_3d.bind()

        if self.centering:
            #Enable(GL_LINE_SMOOTH)
            gpu.state.blend_set('ALPHA')
            gpu.state.depth_test_set('LESS')
            #glDepthFunc(GL_LESS)
            gpu.state.line_width_set(3)

            self.shader_3d.uniform_float('color', (1,1,1,.125))
            self.center_batch_lines.draw(self.shader_3d)

            self.shader_3d.uniform_float('color', (1,1,1,.03125))
            self.center_batch_tris.draw(self.shader_3d)

            gpu.state.depth_test_set('NONE')
            gpu.state.face_culling_set('NONE')
            gpu.state.depth_test_set('NONE')

        self.bm = bmesh.from_edit_mesh(self.obj.data)
        if not self.bm.verts: return
        points = [self.obj.matrix_world @ v.co for v in self.bm.verts]

        batch = batch_for_shader(self.shader_3d, 'POINTS', {'pos': points})
        self.shader_3d.uniform_float('color', (1,0,0,1))
        gpu.state.blend_set('ALPHA')
        gpu.state.point_size_set(8)
        batch.draw(self.shader_3d)
        del batch

        if self.closest_point:
            batch = batch_for_shader(self.shader_3d, 'POINTS', {'pos': [self.closest_point]})
            self.shader_3d.uniform_float('color', (1,1,0,1))
            gpu.state.blend_set('ALPHA')
            gpu.state.point_size_set(12)
            batch.draw(self.shader_3d)
            del batch
