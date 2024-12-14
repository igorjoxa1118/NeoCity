import bpy, mathutils, math, gpu, bmesh
from math import cos, sin
from mathutils import Vector, Matrix
from gpu_extras.batch import batch_for_shader
from ... utility import addon
from ... utility.base_modal_controls import Base_Modal_Controls
from ... ui_framework.master import Master
from ... ui_framework.utils.checks import is_mouse_in_quad
from ... utils.toggle_view3d_panels import collapse_3D_view_panels
from ... utility import method_handler
from ... utils.space_3d import get_3D_point_from_mouse, scene_ray_cast, get_3D_point_from_mouse
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
        self.center_verts = []
        self.center_indices = []
        self.center_bounds = []
        self.center_loc = Vector((0,0))
        self.center_setup()
        # Line : 1
        self.l1_batch = None
        self.l1_color = (1,1,1,.25)
        self.l1_verts = []
        self.l1_indices = []
        self.l1_setup()
        # Circle
        self.circle_batch = None
        self.circle_color = (1,1,1,.25)
        self.circle_verts = []
        self.circle_indices = []
        self.circle_setup()
        # Line : 2
        self.l2_batch = None
        self.l2_color = (1,1,1,.25)
        self.l2_verts = []
        self.l2_indices = []
        self.l2_setup()
        # Square
        self.square_batch = None
        self.square_color = (1,1,1,.25)
        self.square_verts = []
        self.square_indices = []
        self.square_setup()
        # State
        self.mouse_is_over = False
        self.center_active = False
        self.circle_active = False
        self.square_active = False


    def center_setup(self):
        width = self.radius * 2
        x = self.loc[0]
        y = self.loc[1] + self.radius * 4
        self.center_verts = [
            Vector((x, y)),
            Vector((x, y + width))]
        self.center_indices = [(0,1)]
        self.center_batch = batch_for_shader(self.shader, 'LINES', {'pos': self.center_verts}, indices=self.center_indices)

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
        self.l1_verts = [
            Vector((x, y)),
            Vector((x + width, y))]
        self.l1_indices = [(0,1)]
        self.l1_batch = batch_for_shader(self.shader, 'LINES', {'pos': self.l1_verts}, indices=self.l1_indices)


    def circle_setup(self):
        segments = 32
        for i in range(segments):
            index = i + 1
            angle = i * 6.28318 / segments
            x = cos(angle) * self.radius
            y = sin(angle) * self.radius
            vert = Vector((x, y + self.radius * 2))
            vert += self.loc
            self.circle_verts.append(vert)
            if(index == segments): self.circle_indices.append((i, 0))
            else: self.circle_indices.append((i, i + 1))
        summed = Vector((0,0))
        for p in self.circle_verts:
            summed += p
        self.circle_center = summed / len(self.circle_verts)
        self.circle_batch = batch_for_shader(self.shader, 'LINES', {'pos': self.circle_verts}, indices=self.circle_indices)


    def l2_setup(self):
        width = self.radius * 2
        x = self.circle_center[0] - self.radius
        y = self.circle_center[1] - self.radius * 1.5
        self.l2_verts = [
            Vector((x, y)),
            Vector((x + width, y))]
        self.l2_indices = [(0,1)]
        self.l2_batch = batch_for_shader(self.shader, 'LINES', {'pos': self.l2_verts}, indices=self.l2_indices)


    def square_setup(self):
        width = self.radius * 2
        x = self.circle_center[0] - self.radius
        y = self.circle_center[1] - self.radius * 2

        self.square_verts = [
            Vector((x, y - width)),         # 0 Bot Left
            Vector((x, y)),                 # 1 Top Left
            Vector((x + width, y)),         # 2 Top Right
            Vector((x + width, y - width))] # 3 Bot Right
        self.square_indices = [
            (0, 1),
            (1, 2),
            (2, 3),
            (3, 0)]
        self.square_batch = batch_for_shader(self.shader, 'LINES', {'pos': self.square_verts}, indices=self.square_indices)


    def update(self, context, event):

        mouse_pos = Vector((event.mouse_region_x, event.mouse_region_y))

        # Center
        if is_mouse_in_quad(self.center_bounds, mouse_pos):
            self.center_active = True
            self.center_color = (1,1,1,1)
        else:
            self.center_active = False
            self.center_color = (1,1,1,.25)

        # Circle
        if (mouse_pos - self.circle_center).magnitude <= self.radius:
            self.circle_active = True
            self.circle_color = (1,1,1,1)
        else:
            self.circle_active = False
            self.circle_color = (1,1,1,.25)

        # Square
        if is_mouse_in_quad((self.square_verts[1], self.square_verts[0], self.square_verts[2], self.square_verts[3]), mouse_pos):
            self.square_active = True
            self.square_color = (1,1,1,1)
        else:
            self.square_active = False
            self.square_color = (1,1,1,.25)

        # Mouse over
        if self.square_active or self.circle_active:
            self.mouse_is_over = True
        else: self.mouse_is_over = False


    def draw(self):
        # GL Settings
        #Enable(GL_LINE_SMOOTH)
        gpu.state.blend_set('ALPHA')
        gpu.state.line_width_set(3)
        # Center
        self.shader.bind()
        self.shader.uniform_float('color', self.center_color)
        self.center_batch.draw(self.shader)
        # Line 1
        self.shader.bind()
        self.shader.uniform_float('color', self.l1_color)
        self.l1_batch.draw(self.shader)
        # Circle
        self.shader.bind()
        self.shader.uniform_float('color', self.circle_color)
        self.circle_batch.draw(self.shader)
        # Line 2
        self.shader.bind()
        self.shader.uniform_float('color', self.l2_color)
        self.l2_batch.draw(self.shader)
        # Square
        self.shader.bind()
        self.shader.uniform_float('color', self.square_color)
        self.square_batch.draw(self.shader)


# Session Data
OBJ_SCALE = 1


class HOPS_OT_Sculpt_Primitives(bpy.types.Operator):
    bl_idname = "hops.sculpt_primitives"
    bl_label = "Sculpt Primitives"
    bl_description = """Sculpt Primitives

    Add primitives in sculpt mode

    Press H for help
    """
    bl_options = {"REGISTER", "UNDO", "BLOCKING"}

    @classmethod
    def poll(cls, context):

        return context.mode in {'OBJECT', 'SCULPT'}


    def invoke(self, context, event):
        # Props
        self.switch_sculpt = True
        self.sculpt_start = False
        self.created_target = False
        self.separate = addon.preference().property.add_primitive_newobject
        self.target_obj = context.active_object
        self.mode = context.mode
        self.shape = 'SPHERE'
        self.avg_center = Vector((0,0,0))
        self.centering = False
        self.can_center_from_widget = True
        global OBJ_SCALE
        self.scale = OBJ_SCALE
        self.location = Vector((0,0,0))
        self.graphics = True
        self.transitional_point = Vector((0,0,0))
        self.dyno_exit = bpy.context.active_object.use_dynamic_topology_sculpting #if self.sculpt_start else False
        self.notify = lambda val: bpy.ops.hops.display_notification(info=val) if addon.preference().ui.Hops_extra_info else lambda val: None

        self.use_mirror_x = False
        self.use_mirror_y = False
        self.use_mirror_z = False

        if context.mode == 'OBJECT' and not context.active_object:
            bpy.ops.object.select_all(action='DESELECT')
            self.target_obj = bpy.data.objects.new('target', None)
            context.collection.objects.link(self.target_obj)
            context.view_layer.objects.active = self.target_obj
            self.target_obj.hide_set(True)
            self.created_target = True
            self.separate = addon.preference().property.add_primitive_newobject
            self.switch_sculpt = True

        else:
            self.sculpt_start = True
            self.use_mirror_x = self.target_obj.data.use_mirror_x
            self.use_mirror_y = self.target_obj.data.use_mirror_y
            self.use_mirror_z = self.target_obj.data.use_mirror_z

        # Mode set
        if self.mode not in {'OBJECT', 'SCULPT'}:
            bpy.ops.object.mode_set(mode='SCULPT')

        # Widget
        self.shape_widget = Widget()

        # Raycast
        self.setup(context)

        # Graphics
        self.graphics_setup()

        # Base Systems
        self.master = Master(context=context)
        self.master.only_use_fast_ui = True
        self.base_controls = Base_Modal_Controls(context, event)
        self.original_tool_shelf, self.original_n_panel = collapse_3D_view_panels(force=True)
        self.draw_handle_2D = bpy.types.SpaceView3D.draw_handler_add(self.safe_draw_2D, (context,), 'WINDOW', 'POST_PIXEL')
        self.draw_handle_3D = bpy.types.SpaceView3D.draw_handler_add(self.safe_draw_3D, (context,), 'WINDOW', 'POST_VIEW')

        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}


    def modal(self, context, event):

        #--- Base Systems ---#
        self.master.receive_event(event=event)
        self.base_controls.update(context, event)

        #--- Widgets ---#
        if self.can_center_from_widget == False:
            mouse_pos = Vector((event.mouse_region_x, event.mouse_region_y))
            if (self.shape_widget.center_loc - mouse_pos).magnitude > 90 * dpi_factor():
                self.can_center_from_widget = True

        self.shape_widget.update(context, event)
        if self.shape_widget.center_active:
            if self.can_center_from_widget:
                self.can_center_from_widget = False
                self.centering = not self.centering
        elif self.shape_widget.circle_active:
            self.shape = 'SPHERE'
        elif self.shape_widget.square_active:
            self.shape = 'CUBE'

        #--- Casting ---#
        if event.shift:
            self.scale_adjust(context, event)
        else:
            self.caster(context, event)
            self.mod_controller()

        #--- Base Controls ---#
        if self.base_controls.pass_through or event.type in {"WHEELUPMOUSE", "WHEELDOWNMOUSE"}:
            return {'PASS_THROUGH'}

        elif self.base_controls.cancel:
            self.caster_cancel()
            self.remove_shaders()
            collapse_3D_view_panels(self.original_tool_shelf, self.original_n_panel, force=True)
            self.master.run_fade()
            return {'CANCELLED'}

        elif self.base_controls.confirm:
            if not self.shape_widget.mouse_is_over:
                global OBJ_SCALE
                OBJ_SCALE = self.scale

                self.caster_confirm(context)
                self.remove_shaders()
                collapse_3D_view_panels(self.original_tool_shelf, self.original_n_panel, force=True)
                self.master.run_fade()
                return {'FINISHED'}

        #--- Modal Controls ---#
        if event.type == 'C' and event.value == 'PRESS':
            self.centering = not self.centering

        if event.type == 'S' and event.value == 'PRESS':
            if self.shape == 'SPHERE':
                self.shape = 'CUBE'
                self.sphereOBJ.hide_set(True)
                self.cubeOBJ.hide_set(False)
            elif self.shape == 'CUBE':
                self.shape = 'SPHERE'
                self.sphereOBJ.hide_set(False)
                self.cubeOBJ.hide_set(True)

        elif event.type == 'G' and event.value == 'PRESS':
            self.graphics = not self.graphics

        elif event.type == 'D' and event.value == 'PRESS':
            self.dyno_exit = not self.dyno_exit
            val = f"Dyntopo Exit: {self.dyno_exit}"
            self.notify(val)

        elif event.type == 'LEFT_BRACKET' and event.value == 'PRESS':
            self.scale -= .125
            self.set_scale()

        elif event.type == 'RIGHT_BRACKET' and event.value == 'PRESS':
            self.scale += .125
            self.set_scale()

        elif event.type == 'P' and event.value == 'PRESS' and self.sculpt_start:
            self.separate = not self.separate

            val = "Object: Separated" if self.separate else "Object: Joined"
            self.notify(val)

        elif event.type == 'K' and event.value == 'PRESS' and (self.separate or not self.sculpt_start):
            self.switch_sculpt = not self.switch_sculpt
            self.notify(f"Sculpt primitive: {self.switch_sculpt}")

        self.interface(context=context)
        context.area.tag_redraw()
        return {"RUNNING_MODAL"}


    def interface(self, context):
        self.master.setup()

        #---  Fast UI ---#
        if self.master.should_build_fast_ui():

            win_list = [
                f"Shape: {self.shape}",
                f"Center: {self.centering}",
                "Scale: {:.3f}".format(self.scale)]
            if self.sculpt_start:
                win_list.append("[P] NEW" if self.separate else "[P] ADD")
            # if self.separate or not self.sculpt_start:
            #     win_list.append(  f"Sculpt primitive: {self.switch_sculpt}")

            # Help
            help_items = {"GLOBAL" : [], "STANDARD" : []}
            help_items["GLOBAL"] = [
                ("M", "Toggle mods list"),
                ("H", "Toggle help"),
                ("~", "Toggle UI Display Type"),
                ("O", "Toggle viewport rendering")]

            help_items["STANDARD"] = [
                ("G"    , "Toggle Extra Graphics"),
                ("D"    , f"Dyno Exit: {self.dyno_exit}"),
                ("S"    , "Toggle Shapes"),
                ("C"    , "Toggle Centering"),
                ("Shift", "Adjust Scale")]

            if self.sculpt_start:
                help_items["STANDARD"].insert(0, ('P', f"New Object: {self.separate}"))
            if self.separate or not self.sculpt_start:
                help_items["STANDARD"].insert(0,('K', f"Switch Sculpt: {self.switch_sculpt}"))

            self.master.receive_fast_ui(win_list=win_list, help_list=help_items, image="Array")

        self.master.finished()

    #--- UTILS ---#

    def setup(self, context):

        if self.sculpt_start:
            depsgraph = context.evaluated_depsgraph_get()
            object_eval = self.target_obj.evaluated_get(depsgraph)
            mesh_eval = object_eval.data
            points = [self.target_obj.matrix_world @ v.co for v in mesh_eval.vertices]
            summed = Vector((0,0,0))
            for p in points:
                summed += p
            self.avg_center = summed / len(points) if len(points) > 1 else 1

            if type(self.avg_center) != Vector:
                self.avg_center = self.target_obj.matrix_world.translation

        # Create : CUBE
        mesh = bpy.data.meshes.new("HopsMesh")
        self.cubeOBJ = bpy.data.objects.new("HopsObj", mesh)
        context.collection.objects.link(self.cubeOBJ)
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bmesh.ops.create_cube(bm, size=2, calc_uvs=False)
        bm.to_mesh(mesh)
        bm.free()

        # Create : SPHERE
        mesh = bpy.data.meshes.new("HopsMesh")
        self.sphereOBJ = bpy.data.objects.new("HopsObj", mesh)
        context.collection.objects.link(self.sphereOBJ)
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bmesh.ops.create_cube(bm, size=1, calc_uvs=False)
        bmesh.ops.subdivide_edges(bm, edges=bm.edges, smooth=1, cuts=4, use_grid_fill=True, use_sphere=True)
        bm.to_mesh(mesh)
        bm.free()

        # Hide
        self.cubeOBJ.hide_set(True)

        # Mod : CUBE
        self.cube_mod = self.cubeOBJ.modifiers.new('Mirror', 'MIRROR')
        self.cube_mod.mirror_object = self.target_obj

        # Mod : SPHERE
        self.sphere_mod = self.sphereOBJ.modifiers.new('Mirror', 'MIRROR')
        self.sphere_mod.mirror_object = self.target_obj

        # symmetry
        self.cube_mod.use_axis[0] = self.sphere_mod.use_axis[0] = self.use_mirror_x
        self.cube_mod.use_axis[1] = self.sphere_mod.use_axis[1] = self.use_mirror_y
        self.cube_mod.use_axis[2] = self.sphere_mod.use_axis[2] = self.use_mirror_z
        self.cube_mod.use_bisect_axis = self.sphere_mod.use_bisect_axis = True, True, True

        self.cubeOBJ.data.use_mirror_x = self.sphereOBJ.data.use_mirror_x = self.use_mirror_x
        self.cubeOBJ.data.use_mirror_y = self.sphereOBJ.data.use_mirror_y = self.use_mirror_y
        self.cubeOBJ.data.use_mirror_z = self.sphereOBJ.data.use_mirror_z = self.use_mirror_z

        self.set_scale()


    def graphics_setup(self):
        self.center_verts = []

        self.center_indices_lines = []
        built_in_shader = 'UNIFORM_COLOR' if bpy.app.version[0] >=4 else '3D_UNIFORM_COLOR'
        self.center_shader_lines = gpu.shader.from_builtin(built_in_shader)
        self.center_batch_lines = None

        self.center_indices_tris = []
        self.center_shader_tris = gpu.shader.from_builtin(built_in_shader)
        self.center_batch_tris = None

        # Verts
        segments = 64
        radius = 8
        for i in range(segments):
            index = i + 1
            angle = i * 6.28318 / segments
            y = cos(angle) * radius
            z = sin(angle) * radius
            vert = Vector((0, y, z))
            vert += self.avg_center
            self.center_verts.append(vert)
            # Line indices
            if(index == segments): self.center_indices_lines.append((i, 0))
            else: self.center_indices_lines.append((i, i + 1))

        # Line batch
        self.center_batch_lines = batch_for_shader(self.center_shader_lines, 'LINES', {'pos': self.center_verts}, indices=self.center_indices_lines)

        # Tri indices
        for i in range(len(self.center_verts) - 1):
            self.center_indices_tris.append((0, i, i + 1))

        # Tri batch
        self.center_batch_tris = batch_for_shader(self.center_shader_tris, 'TRIS', {'pos': self.center_verts}, indices=self.center_indices_tris)


    def caster(self, context, event):

        self.sphereOBJ.hide_set(True)
        self.cubeOBJ.hide_set(True)

        if self.centering:
            self.center_casting(context, event)
            return

        point_location = None

        # Scene cast
        hit, location, normal, index, object, matrix = scene_ray_cast(context, event)
        if hit:
            point_location = location
            self.transitional_point = location

        # Plane cast
        if point_location == None:

            view_quat = context.region_data.view_rotation
            up = Vector((0,0,1))
            view_normal = view_quat @ up

            point = self.avg_center
            if self.transitional_point.length > 0:
                point = self.transitional_point

            mouse_pos = (event.mouse_region_x, event.mouse_region_y)
            location = get_3D_point_from_mouse(mouse_pos, context, point, view_normal)
            if not location: return
            point_location = location

        self.location = location
        self.set_locations()
        self.set_hide_states()


    def center_casting(self, context, event):
        mouse_pos = (event.mouse_region_x, event.mouse_region_y)
        location = get_3D_point_from_mouse(mouse_pos, context, self.avg_center, Vector((1,0,0)))
        if not location: return
        self.location = location

        self.set_locations()
        self.set_hide_states()


    def set_locations(self):
        self.sphereOBJ.location = self.location
        self.cubeOBJ.location = self.location


    def set_hide_states(self):
        if self.shape == 'SPHERE':
            self.sphereOBJ.hide_set(False)
        elif self.shape == 'CUBE':
            self.cubeOBJ.hide_set(False)


    def mod_controller(self):

        obj = self.sphereOBJ if self.shape == 'SPHERE' else self.cubeOBJ
        mod = self.sphere_mod if self.shape == 'SPHERE' else self.cube_mod

        mod.show_viewport = not self.centering

        mod.use_bisect_flip_axis[0] = obj.location[0] < self.avg_center[0]
        mod.use_bisect_flip_axis[1] = obj.location[1] < self.avg_center[1]
        mod.use_bisect_flip_axis[2] = obj.location[2] < self.avg_center[2]


    def scale_adjust(self, context, event):
        view_quat = context.region_data.view_rotation
        up = Vector((0,0,1))
        view_normal = view_quat @ up

        mouse_pos = (event.mouse_region_x, event.mouse_region_y)

        location = get_3D_point_from_mouse(mouse_pos, context, self.sphereOBJ.location, view_normal)
        if not location: return
        self.scale = (location - self.location).magnitude
        self.set_scale()


    def set_scale(self):
        self.cubeOBJ.scale = Vector((self.scale, self.scale, self.scale))
        self.sphereOBJ.scale = Vector((self.scale, self.scale, self.scale))


    def caster_confirm(self, context):

        if self.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')

        new_object = None

        if self.shape == 'SPHERE':
            bpy.data.objects.remove(self.cubeOBJ)
            self.sphereOBJ.select_set(True)
            context.view_layer.objects.active = self.sphereOBJ
            new_object = self.sphereOBJ
            if self.sphere_mod.show_viewport: bpy.ops.object.modifier_apply(modifier=self.sphere_mod.name)

        elif self.shape == 'CUBE':
            bpy.data.objects.remove(self.sphereOBJ)
            self.cubeOBJ.select_set(True)
            context.view_layer.objects.active = self.cubeOBJ
            new_object = self.cubeOBJ
            if self.cube_mod.show_viewport: bpy.ops.object.modifier_apply(modifier=self.cube_mod.name)

        if self.sculpt_start:
            if self.separate:
                if self.switch_sculpt:
                    new_object.select_set(True)
                    context.view_layer.objects.active = new_object
                    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
                    bpy.ops.object.mode_set(mode='SCULPT')
                    if self.dyno_exit:
                        bpy.ops.sculpt.dynamic_topology_toggle()

                else:
                    new_object.select_set(False)
                    context.view_layer.objects.active = self.target_obj
                    self.target_obj.select_set(True)
                    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
                    bpy.ops.object.mode_set(mode='SCULPT')

            else:
                self.target_obj.select_set(True)
                context.view_layer.objects.active = self.target_obj
                bpy.ops.object.join()
                bpy.ops.object.mode_set(mode='SCULPT')

                if self.dyno_exit:
                    bpy.ops.sculpt.dynamic_topology_toggle()
        else:
            bpy.ops.object.select_all(action='DESELECT')
            new_object.select_set(True)
            context.view_layer.objects.active = new_object
            bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
            if self.switch_sculpt:
                bpy.ops.object.mode_set(mode='SCULPT')


        if self.created_target:
            bpy.data.objects.remove(self.target_obj)

    def caster_cancel(self):
        bpy.data.objects.remove(self.cubeOBJ)
        bpy.data.objects.remove(self.sphereOBJ)

        if self.created_target:
            bpy.data.objects.remove(self.target_obj)

    #--- SHADERS ---#

    def remove_shaders(self):
        if self.draw_handle_2D:
            self.draw_handle_2D = bpy.types.SpaceView3D.draw_handler_remove(self.draw_handle_2D, "WINDOW")
        if self.draw_handle_3D:
            self.draw_handle_3D = bpy.types.SpaceView3D.draw_handler_remove(self.draw_handle_3D, "WINDOW")

    # 2D SHADER
    def safe_draw_2D(self, context):
        method_handler(self.draw_shader_2D,
            arguments = (context,),
            identifier = 'Modal Shader 2D',
            exit_method = self.remove_shaders)


    def draw_shader_2D(self, context):
        self.shape_widget.draw()

    # 3D SHADER
    def safe_draw_3D(self, context):
        method_handler(self.draw_shader_3D,
            arguments = (context,),
            identifier = 'Modal Shader 3D',
            exit_method = self.remove_shaders)


    def draw_shader_3D(self, context):
        if not self.graphics: return
        if self.centering:
            #Enable(GL_LINE_SMOOTH)
            gpu.state.blend_set('ALPHA')
            gpu.state.depth_test_set('LESS')
            #glDepthFunc(GL_LESS)
            gpu.state.line_width_set(3)

            self.center_shader_lines.bind()
            self.center_shader_lines.uniform_float('color', (1,1,1,.125))
            self.center_batch_lines.draw(self.center_shader_lines)

            self.center_shader_tris.bind()
            self.center_shader_tris.uniform_float('color', (1,1,1,.03125))
            self.center_batch_tris.draw(self.center_shader_tris)

            gpu.state.depth_test_set('NONE')
            gpu.state.face_culling_set('NONE')
            gpu.state.depth_test_set('NONE')