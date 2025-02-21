import bpy, mathutils, math, gpu, bmesh, time, traceback
from math import cos, sin
from enum import Enum
from mathutils import Vector, Matrix
from gpu_extras.batch import batch_for_shader
from ... utility import addon
from ... utility.base_modal_controls import Base_Modal_Controls
from ... ui_framework.master import Master
from ... ui_framework.flow_ui.flow import Flow_Menu, Flow_Form
from ... ui_framework.utils.mods_list import get_mods_list
from ... utils.toggle_view3d_panels import collapse_3D_view_panels
from ... utility import method_handler
from ... utility import math as hops_math
from ... utils.modal_frame_drawing import draw_modal_frame
from ... utils.cursor_warp import mouse_warp


class Shapes(Enum):
    BOX = 0
    SPHERE = 1
    CYLINDER = 2
    PLANE = 3
    EMPTY = 4
    CONVEX = 5
    DECAP = 6


class Axis(Enum):
    X = 0
    Y = 1
    Z = 2


class EmptyOpts(Enum):
    SINGLE = 0
    GROUP = 1


class DecapCaps:

    def __init__(self, context, relative_name=''):

        # Side A
        self.mesh_a = bpy.data.meshes.new(f'{relative_name} DecapMeshA')
        self.obj_a = bpy.data.objects.new(f'{relative_name} DecapObjA', self.mesh_a)
        context.collection.objects.link(self.obj_a)
        self.mesh_a.use_auto_smooth = addon.preference().behavior.auto_smooth

        # Side B
        self.mesh_b = bpy.data.meshes.new(f'{relative_name} DecapMeshB')
        self.obj_b = bpy.data.objects.new(f'{relative_name} DecapObjB', self.mesh_b)
        context.collection.objects.link(self.obj_b)
        self.mesh_b.use_auto_smooth = addon.preference().behavior.auto_smooth


    def clear_and_destroy(self):

        bpy.data.objects.remove(self.obj_a)
        bpy.data.meshes.remove(self.mesh_a)
        bpy.data.objects.remove(self.obj_b)
        bpy.data.meshes.remove(self.mesh_b)


    def insert_mesh_into_cap(self, bm, cap=''):

        mesh = None
        if cap == 'a':
            mesh = self.mesh_a
        elif cap == 'b':
            mesh = self.mesh_b
        bm.to_mesh(mesh)


    def clear_cap_verts(self):

        bm = bmesh.new()
        bm.from_mesh(self.mesh_a)
        bmesh.ops.delete(bm, geom=bm.verts, context='VERTS')
        bm.to_mesh(self.mesh_a)
        bm.free()
        bm = bmesh.new()
        bm.from_mesh(self.mesh_b)
        bmesh.ops.delete(bm, geom=bm.verts, context='VERTS')
        bm.to_mesh(self.mesh_b)
        bm.free()


class HOPS_OT_To_Shape_V2(bpy.types.Operator):
    bl_idname = "hops.to_shape_v2"
    bl_label = "To Shape V2"
    bl_description = '''To Shape V2 \n
    Interactive To_Shape
    Converts selection into a shape for quick blocking

    Shift : Ignore last mirror modifier
    '''
    bl_options = {"REGISTER", "UNDO", "BLOCKING"}

    @classmethod
    def poll(cls, context):
        return any(o.type in {'MESH', 'CURVE'} for o in context.selected_objects)


    def invoke(self, context, event):

        # --- Batches --- #
        built_in_shader = 'UNIFORM_COLOR' if bpy.app.version[0] >=4 else '3D_UNIFORM_COLOR'
        self.edges_shader = gpu.shader.from_builtin(built_in_shader)
        self.edges_batch = None

        self.decap_faces_shader = gpu.shader.from_builtin(built_in_shader)
        self.decap_faces_batch = None

        self.decap_keep_caps_shader = gpu.shader.from_builtin(built_in_shader)
        self.decap_keep_caps_batch = None

        self.shape_edges_shader = gpu.shader.from_builtin(built_in_shader)
        self.shape_edges_batch = None

        self.shape_faces_shader = gpu.shader.from_builtin(built_in_shader)
        self.shape_faces_batch = None

        # ---- Data ----
        self.objs = [obj for obj in context.selected_objects if obj.type in {'MESH', 'CURVE'}]

        self.original_locations = []
        for obj in self.objs:
            self.original_locations.append((obj, obj.location.copy(), obj.matrix_world.translation.copy(), obj.matrix_world.copy()))

        self.bounds, self.center = self.capture_bounds_and_center(context, hide_mirror=event.shift)
        if self.bounds == None or self.center == None or len(self.objs) < 1:
            return {'CANCELLED'}

        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        names = ["GroupEmpty", "DecapMesh", "DecapObj", "ToShapeMesh", "ToShapeObj"]
        relative_name = context.active_object.name if context.active_object in self.objs else self.objs[0].name
        for name in names:
            if name in relative_name:
                relative_name = relative_name.replace(name, "")

        self.extents = hops_math.dimensions(self.bounds)
        self.draw_edges = []
        self.update_draw_edges()

        self.original_obj_parents = [(obj, obj.parent) for obj in self.objs]

        # ---- Empty objects ----
        self.reverse_parent_empty = False
        self.empty_objs = []
        for obj in self.objs:
            empty = bpy.data.objects.new(f'SingleEmpty {relative_name}', None)
            context.collection.objects.link(empty)
            empty.matrix_world.translation = obj.matrix_world.translation
            self.empty_objs.append((empty, obj, obj.matrix_world.copy()))
            empty.hide_set(True)

        empty = bpy.data.objects.new(f'GroupEmpty {relative_name}', None)
        context.collection.objects.link(empty)
        empty.matrix_world.translation = self.center
        self.empty_objs.append((empty, None))
        empty.hide_set(True)
        self.original_empty_locations = [(obj[0], obj[0].matrix_world.translation.copy()) for obj in self.empty_objs]

        # ---- Cyclinder ----
        self.show_fade = True

        # ---- Cyclinder ----
        self.mouse_cyclinder = 0

        # ---- Plane ----
        self.mouse_plane = 0

        # ---- Shape Drawing ----
        self.shape_verts = []
        self.shape_indices = []
        self.shape_edges = []

        # ---- Segments ----
        self.adjusting_segments = False
        self.segments = 32

        # ---- Decap ----
        self.exit_with_an_array = True
        self.center_offset = 0
        self.decap_draw_edges = []
        self.decap_mouse_positive = .0125
        self.decap_mouse_negative = .0125
        self.decap_center = Vector((0,0,0))
        self.fill_holes = False
        self.keep_caps = False
        self.decap_caps = DecapCaps(context, relative_name)
        self.decap_mesh = bpy.data.meshes.new(f'{relative_name} DecapMesh')
        self.decap_obj = bpy.data.objects.new(f'{relative_name} DecapObj', self.decap_mesh)
        context.collection.objects.link(self.decap_obj)
        self.decap_bmesh = bmesh.new()
        depsgraph = context.evaluated_depsgraph_get()
        for obj in self.objs:
            eval_obj = obj.evaluated_get(depsgraph)
            temp = eval_obj.to_mesh()
            temp.transform(obj.matrix_world)
            self.decap_bmesh.from_mesh(temp)
        self.decap_bmesh.to_mesh(self.decap_mesh)
        self.decap_mesh_backup = self.decap_mesh.copy()
        self.decap_obj.hide_set(True)

        # ---- The new mesh object for (Shapes) ----
        self.mesh = bpy.data.meshes.new(f'{relative_name} ToShapeMesh')
        self.obj = bpy.data.objects.new(f'{relative_name} ToShapeObj', self.mesh)
        context.collection.objects.link(self.obj)
        self.bm = bmesh.new()
        self.bm.from_mesh(self.mesh)
        self.obj.location = self.center

        # ---- Set auto smooths ----
        if addon.preference().behavior.auto_smooth:
            self.decap_mesh.use_auto_smooth = True
            self.decap_mesh_backup.use_auto_smooth = True
            self.mesh.use_auto_smooth = True

        # ---- State data ----
        self.shape = Shapes.BOX
        self.axis = Axis.X
        self.empty_opts = EmptyOpts.SINGLE
        self.equalize_radius = False
        self.show_graphics = True
        self.offsets = ['CENTER', 'XP', 'XN', 'YP', 'YN', 'ZP', 'ZN']
        self.offset_axis = 'CENTER'

        # ---- Flow menu ----
        self.flow = Flow_Menu()
        self.setup_flow_menu()

        # ---- Base Systems ----
        self.master = Master(context=context)
        self.master.only_use_fast_ui = True
        self.base_controls = Base_Modal_Controls(context, event)
        self.original_tool_shelf, self.original_n_panel = collapse_3D_view_panels()
        self.draw_handle_2D = bpy.types.SpaceView3D.draw_handler_add(self.safe_draw_2D, (context,), 'WINDOW', 'POST_PIXEL')
        self.draw_handle_3D = bpy.types.SpaceView3D.draw_handler_add(self.safe_draw_3D, (context,), 'WINDOW', 'POST_VIEW')

        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}


    def setup_flow_menu(self):
        '''Setup flow menu system.'''

        flow_data = [
            Flow_Form(text="SHAPES"  , font_size=18, tip_box="Pick a shape."),
            Flow_Form(text="BOX"     , font_size=14, func=self.flow_func, pos_args=(Shapes.BOX, )     , tip_box="To box Shape."),
            Flow_Form(text="SPHERE"  , font_size=14, func=self.flow_func, pos_args=(Shapes.SPHERE, )  , tip_box="To sphere Shape."),
            Flow_Form(text="CYLINDER", font_size=14, func=self.flow_func, pos_args=(Shapes.CYLINDER, ), tip_box="To cylinder Shape."),
            Flow_Form(text="PLANE"   , font_size=14, func=self.flow_func, pos_args=(Shapes.PLANE, )   , tip_box="To plane Shape."),
            Flow_Form(text="DECAP"   , font_size=14, func=self.flow_func, pos_args=(Shapes.DECAP, )   , tip_box="Decap the current objects."),
            Flow_Form(text="EMPTY"   , font_size=14, func=self.flow_func, pos_args=(Shapes.EMPTY, )   , tip_box="Add empties to objects."),
            Flow_Form(text="CONVEX"  , font_size=14, func=self.flow_func, pos_args=(Shapes.CONVEX, )  , tip_box="Create a convex shape.")]
        self.flow.setup_flow_data(flow_data)


    def flow_func(self, shape):

        self.shape = shape
        self.cycle_shape(from_flow_menu=True)


    def modal(self, context, event):

        # Base Systems
        self.base_controls.update(context, event)
        self.master.receive_event(event=event)
        self.flow.run_updates(context, event, close_on_click=True, enable_tab_open=True)

        # Mouse adjustments
        if self.flow.is_open == False:

            # Mouse offsets
            if self.shape == Shapes.DECAP:
                mouse_warp(context, event)

                multiplier = 2.5
                if self.axis == Axis.X:
                    multiplier = self.extents[0] * .875
                elif self.axis == Axis.Y:
                    multiplier = self.extents[1] * .875
                elif self.axis == Axis.Z:
                    multiplier = self.extents[2] * .875

                if event.ctrl == True:
                    self.center_offset += self.base_controls.mouse * multiplier
                else:
                    self.decap_mouse_positive += self.base_controls.mouse * multiplier
                    self.decap_mouse_negative += self.base_controls.mouse * multiplier

            elif self.shape == Shapes.CYLINDER:
                mouse_warp(context, event)
                self.mouse_cyclinder += self.base_controls.mouse * 2.5
                self.cylinder_mouse_axis_adjust()

            elif self.shape == Shapes.PLANE:
                mouse_warp(context, event)
                self.mouse_plane += self.base_controls.mouse * 2.5
                self.plane_mouse_axis_adjust()

        # Navigation
        if self.base_controls.pass_through:
            return {'PASS_THROUGH'}

        # Cancel
        elif self.base_controls.cancel:

            self.bm.free()
            bpy.data.objects.remove(self.obj)
            bpy.data.meshes.remove(self.mesh)

            self.decap_bmesh.free()
            bpy.data.objects.remove(self.decap_obj)
            bpy.data.meshes.remove(self.decap_mesh)
            bpy.data.meshes.remove(self.decap_mesh_backup)
            self.decap_caps.clear_and_destroy()

            self.reset_objects_and_empties()

            for obj in self.objs:
                obj.hide_set(False)

            for item in self.empty_objs:
                obj = item[0]
                bpy.data.objects.remove(obj)

            self.flow.shut_down()
            self.remove_shaders()
            collapse_3D_view_panels(self.original_tool_shelf, self.original_n_panel)
            self.master.run_fade()
            return {'CANCELLED'}

        # Allow Wire
        elif event.type == 'Z':
            return {'PASS_THROUGH'}

        # Confirm
        elif event.type in {'SPACE', 'RET', 'NUMPAD_ENTER', 'LEFTMOUSE'} and event.value == 'PRESS':
            if self.flow.is_open == False:
                self.confirmed_exit(context)
                self.flow.shut_down()
                self.remove_shaders()
                collapse_3D_view_panels(self.original_tool_shelf, self.original_n_panel)
                self.master.run_fade()
                return {'FINISHED'}

        # Equalize
        elif event.type == 'E' and event.value == 'PRESS':
            self.equalize_radius = not self.equalize_radius

        # Show Graphics
        elif event.type == 'G' and event.value == 'PRESS':
            self.show_graphics = not self.show_graphics

        # Toggle empty settings / Set adjust segments
        elif event.type == 'S' and event.value == 'PRESS':
            if self.shape == Shapes.EMPTY:
                if self.empty_opts == EmptyOpts.GROUP:
                    self.empty_opts = EmptyOpts.SINGLE
                elif self.empty_opts == EmptyOpts.SINGLE:
                    self.empty_opts = EmptyOpts.GROUP

            elif self.shape in {Shapes.CYLINDER, Shapes.SPHERE}:
                self.adjusting_segments = not self.adjusting_segments
                bpy.ops.hops.display_notification(info=f'Adjust segments : {self.adjusting_segments}',)

        # Reverse parent empty
        elif event.type == 'R' and event.value == 'PRESS':
            self.reverse_parent_empty = not self.reverse_parent_empty

        # Fill Holes
        elif event.type == 'F' and event.value == 'PRESS':
            if self.shape == Shapes.DECAP:
                self.fill_holes = not self.fill_holes

        # Keep Caps
        elif event.type == 'C' and event.value == 'PRESS':
            if self.shape == Shapes.DECAP:
                self.keep_caps = not self.keep_caps

        # Cycle Shapes
        elif event.type == 'X' and event.value == 'PRESS':
            if event.shift == False:
                self.cycle_axis(forward=True)
            else:
                self.cycle_shape(forward=True)

        # Exit with an array for Decap
        elif event.type == 'A' and event.value == 'PRESS':
            if self.shape == Shapes.DECAP:
                if self.keep_caps:
                    self.exit_with_an_array = not self.exit_with_an_array

        # Scroll options
        if self.base_controls.scroll != 0:

            # Change offset location
            if event.ctrl == True:
                self.cycle_offset_axis()

            # Change the direction
            elif event.shift == True:
                if self.base_controls.scroll > 0:
                    self.cycle_axis(forward=True)
                elif self.base_controls.scroll < 0:
                    self.cycle_axis(forward=False)

            # Basic scroll
            else:
                # Adjust segments
                if self.adjusting_segments == True:
                    if self.base_controls.scroll > 0:
                        self.segments += 1
                    elif self.base_controls.scroll < 0:
                        self.segments -= 1
                    if self.segments < 4:
                        self.segments = 4

                # Change shape
                elif self.base_controls.scroll > 0:
                    self.cycle_shape(forward=True)
                elif self.base_controls.scroll < 0:
                    self.cycle_shape(forward=False)

        # Build mesh
        if event.type != 'TIMER':
            if self.flow.is_open == False:
                try:
                    self.build_shape()
                    self.bm.to_mesh(self.mesh)
                    self.decap_bmesh.to_mesh(self.decap_mesh)

                    if self.shape in {Shapes.BOX, Shapes.SPHERE, Shapes.PLANE, Shapes.CYLINDER}:
                        self.build_shape_batche()

                except Exception:
                    traceback.print_exc()
                    self.remove_shaders()
                    return {'CANCELLED'}

        # Fade wire mesh
        if self.show_fade == True:
            self.show_fade = False
            if self.shape in {Shapes.BOX, Shapes.SPHERE, Shapes.CYLINDER, Shapes.PLANE, Shapes.CONVEX}:
                bpy.ops.hops.draw_wire_mesh_launcher('INVOKE_DEFAULT', object_name=self.obj.name)
            elif self.shape == Shapes.DECAP:
                bpy.ops.hops.draw_wire_mesh_launcher('INVOKE_DEFAULT', object_name=self.decap_obj.name)

        self.draw_master(context=context)
        context.area.tag_redraw()
        return {"RUNNING_MODAL"}


    def draw_master(self, context):
        self.master.setup()
        if self.master.should_build_fast_ui():

            win_list = []
            mods_list = []

            if addon.preference().ui.Hops_modal_fast_ui_loc_options != 1:
                win_list.append(self.shape.name)

                if self.shape != Shapes.EMPTY and self.empty_opts != EmptyOpts.SINGLE:
                    win_list.append(self.offset_axis)

                win_list.append(self.offset_axis)
                win_list.append(self.axis.name)
            else:
                # Main
                win_list.append(self.shape.name)
                if self.shape == Shapes.EMPTY:
                    if self.empty_opts == EmptyOpts.GROUP:
                        win_list.append(self.offset_axis)
                    win_list.append(f'(S) Empty Target: {self.empty_opts.name}')
                    win_list.append(f'(R) Parent Reverse: {self.reverse_parent_empty}')
                elif self.shape == Shapes.DECAP:
                    win_list.append(f'(F) Fill Holes: {self.fill_holes}')
                    win_list.append(f'(C) Keep Caps: {self.keep_caps}')
                    if self.keep_caps:
                        win_list.append(f'(A) Exit Array: {self.exit_with_an_array}')
                    win_list.append(f'Shift Scroll: {self.axis.name}')
                else:
                    win_list.append(self.offset_axis)
                    win_list.append(self.axis.name)
                    win_list.append(f'Equalize: {self.equalize_radius}')

                if self.shape in {Shapes.CYLINDER, Shapes.SPHERE}:
                    win_list.append(f'Segments: {self.segments}')

            # Help
            help_items = {"GLOBAL" : [], "STANDARD" : []}

            help_items["GLOBAL"] = [
                ("M", "Toggle mods list"),
                ("H", "Toggle help"),
                ("~", "Toggle UI Display Type"),
                ("O", "Toggle viewport rendering")
            ]

            if self.shape == Shapes.EMPTY:
                help_items["STANDARD"] = [
                    ("S", "Single / Group"),
                    ("R", "Reverse parent empty")]

            elif self.shape == Shapes.DECAP:
                help_items["STANDARD"] = [
                    ("F", f'Fill Holes {self.fill_holes}'),
                    ("C", f'Keep Caps {self.keep_caps}'),
                    ("Ctrl", 'Center offset adjust')]

                if self.keep_caps:
                    help_items["STANDARD"].append(["A", f'Exit with array {self.exit_with_an_array}'])
            else:
                help_items["STANDARD"] = [
                    ("E", "Equalize radius to Axis")]


            if self.shape in {Shapes.CYLINDER, Shapes.SPHERE}:
                help_items["STANDARD"].append(["S", f'Adjust segments {self.adjusting_segments}'])

            help_items["STANDARD"].append(["G",              f"Show Graphics {self.show_graphics}"])
            help_items["STANDARD"].append(["Shift + X",      "Change shape (scroll)"])
            help_items["STANDARD"].append(["Scroll + Ctrl",  "Change offset"])
            help_items["STANDARD"].append(["Scroll + Shift", "Change axis (X)"])
            help_items["STANDARD"].append(["TAB ",           "Open Flow System"])

            self.master.receive_fast_ui(win_list=win_list, help_list=help_items, image="Display_boolshapes")
        self.master.finished()

    ####################################################
    #   UTILS
    ####################################################

    def capture_bounds_and_center(self, context, hide_mirror=False):
        '''Get the bounding dimensions and the center point.'''

        coords = []
        bounds = []
        center = Vector((0,0,0))

        mirrors = []
        if hide_mirror:
            for obj in self.objs:
                for mod in reversed(obj.modifiers):
                    if mod.type == 'MIRROR':
                        mirrors.append((mod, mod.show_viewport))
                        mod.show_viewport = False
                        break

        # Capture from edit mode
        if context.mode == 'EDIT_MESH':
            # Get all selected verts
            for obj in self.objs:
                obj.update_from_editmode()
                mesh = obj.data
                mesh.calc_loop_triangles()
                bm = bmesh.new()
                bm.from_mesh(mesh)
                selected = [v for v in bm.verts if v.select == True]

                for vert in selected:
                    coords.append(obj.matrix_world @ vert.co)
                bm.free()

        # Capture from object mode
        else:
            depsgraph = context.evaluated_depsgraph_get()

            for obj in self.objs:
                obj_eval = obj.evaluated_get(depsgraph)
                data_eval = obj_eval.to_mesh()
                coords.extend([obj.matrix_world @ v.co for v in data_eval.vertices])
                obj_eval.to_mesh_clear()

        if len(mirrors) > 0:
            for item in mirrors:
                mod = item[0]
                mod.show_viewport = item[1]

        if len(coords) < 3:
            return None, None

        bounds = hops_math.coords_to_bounds(coords)
        center = hops_math.coords_to_center(bounds)
        return bounds, center


    def confirmed_exit(self, context):

        if context.mode == 'EDIT_MESH':
            bpy.ops.object.editmode_toggle()
        bpy.ops.object.select_all(action='DESELECT')
        self.set_obj_origin_on_exit()

        self.bm.to_mesh(self.mesh)
        self.bm.free()

        self.decap_bmesh.free()
        bpy.data.meshes.remove(self.decap_mesh_backup)

        def remove_decap():
            bpy.data.objects.remove(self.decap_obj)
            bpy.data.meshes.remove(self.decap_mesh)
            self.decap_caps.clear_and_destroy()

        def remove_empties():
            for item in self.empty_objs:
                obj = item[0]
                bpy.data.objects.remove(obj)

        def remove_base_obj():
            bpy.data.objects.remove(self.obj)
            bpy.data.meshes.remove(self.mesh)

        # Remove decap objects
        if self.shape in {Shapes.BOX, Shapes.CYLINDER, Shapes.SPHERE, Shapes.PLANE, Shapes.CONVEX}:
            remove_decap()
            remove_empties()

            context.view_layer.objects.active = self.obj
            self.obj.select_set(True)

            # Clean convex
            if self.shape == Shapes.CONVEX:
                bpy.ops.view3d.clean_mesh('INVOKE_DEFAULT')

            bpy.ops.hops.draw_wire_mesh_launcher('INVOKE_DEFAULT', object_name=self.obj.name)

        # Using decap so remove other shapes
        elif self.shape == Shapes.DECAP:
            remove_base_obj()
            remove_empties()

            self.decap_obj.hide_set(False)
            context.view_layer.objects.active = self.decap_obj
            self.decap_obj.select_set(True)

            if self.keep_caps == True:
                self.set_decap_origins_on_ext()
                if self.exit_with_an_array:
                    self.set_decap_array_on_exit()
            else:
                self.decap_caps.clear_and_destroy()
                bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')

            for obj in self.objs:
                obj.hide_set(False)

            self.decap_obj.data.use_auto_smooth = addon.preference().behavior.auto_smooth
            bpy.ops.hops.draw_wire_mesh_launcher('INVOKE_DEFAULT', object_name=self.decap_obj.name)

        # Using empties
        elif self.shape == Shapes.EMPTY:
            remove_decap()
            remove_base_obj()

            for item in self.empty_objs:
                obj = item[0]
                if self.empty_opts == EmptyOpts.SINGLE:
                    if obj.name[:10] == 'GroupEmpty':
                        bpy.data.objects.remove(obj)
                    else:
                        obj.hide_set(False)

                elif self.empty_opts == EmptyOpts.GROUP:
                    if obj.name[:11] == 'SingleEmpty':
                        bpy.data.objects.remove(obj)
                    else:
                        obj.hide_set(False)


    def update_draw_edges(self):
        '''Take the bounds and store the drawing data for wire.'''

        self.draw_edges = [
            self.bounds[0], self.bounds[1],
            self.bounds[1], self.bounds[2],
            self.bounds[2], self.bounds[3],
            self.bounds[3], self.bounds[0],
            self.bounds[4], self.bounds[0],
            self.bounds[4], self.bounds[5],
            self.bounds[5], self.bounds[6],
            self.bounds[6], self.bounds[7],
            self.bounds[4], self.bounds[7],
            self.bounds[1], self.bounds[5],
            self.bounds[3], self.bounds[7],
            self.bounds[2], self.bounds[6]]

        self.edges_batch = batch_for_shader(self.edges_shader, 'LINES', {"pos": self.draw_edges})


    def cycle_shape(self, forward=True, from_flow_menu=False):

        # Fade the mesh : called from modal
        self.show_fade = True

        # Change the shape type
        if from_flow_menu == False:
            if forward:
                if self.shape == Shapes.BOX:
                    self.shape = Shapes.SPHERE
                elif self.shape == Shapes.SPHERE:
                    self.shape = Shapes.CYLINDER
                elif self.shape == Shapes.CYLINDER:
                    self.shape = Shapes.PLANE
                elif self.shape == Shapes.PLANE:
                    self.shape = Shapes.EMPTY
                elif self.shape == Shapes.EMPTY:
                    self.shape = Shapes.CONVEX
                elif self.shape == Shapes.CONVEX:
                    self.shape = Shapes.DECAP
                elif self.shape == Shapes.DECAP:
                    self.shape = Shapes.BOX

            else:
                if self.shape == Shapes.BOX:
                    self.shape = Shapes.DECAP
                elif self.shape == Shapes.SPHERE:
                    self.shape = Shapes.BOX
                elif self.shape == Shapes.CYLINDER:
                    self.shape = Shapes.SPHERE
                elif self.shape == Shapes.PLANE:
                    self.shape = Shapes.CYLINDER
                elif self.shape == Shapes.EMPTY:
                    self.shape = Shapes.PLANE
                elif self.shape == Shapes.CONVEX:
                    self.shape = Shapes.EMPTY
                elif self.shape == Shapes.DECAP:
                    self.shape = Shapes.CONVEX

        # Hide decap objects
        if self.shape != Shapes.DECAP:
            self.decap_obj.hide_set(True)
            for obj in self.objs:
                obj.hide_set(False)

        # Show decap objects and setup mouse
        if self.shape == Shapes.DECAP:
            self.decap_obj.hide_set(False)
            self.decap_mouse_positive = 0
            for obj in self.objs:
                obj.hide_set(True)

        # Hide empty objects
        if self.shape != Shapes.EMPTY:
            for item in self.empty_objs:
                obj = item[0]
                obj.hide_set(True)
            self.reset_objects_and_empties()

        if self.shape in {Shapes.CYLINDER, Shapes.SPHERE}:
            self.equalize_radius = True
        else:
            self.equalize_radius = False

        # Setup defualt axis
        if self.shape == Shapes.PLANE or self.shape == Shapes.CONVEX:
            self.axis = Axis.Z
            self.offset_axis = 'CENTER'
        else:
            self.axis = Axis.X

        # Reset mouse for cylinder
        self.mouse_cyclinder = 0
        self.mouse_plane = 0
        self.center_offset = 0
        self.decap_mouse_positive = .0125
        self.decap_mouse_negative = .0125
        # Reset segment adjust
        self.adjusting_segments = False
        self.segments = 32


    def cycle_offset_axis(self):

        if self.shape == Shapes.EMPTY:
            if self.empty_opts == EmptyOpts.SINGLE:
                return

        self.offsets = ['CENTER', 'XP', 'XN', 'YP', 'YN', 'ZP', 'ZN']
        index = self.offsets.index(self.offset_axis)

        if self.base_controls.scroll > 0:
            self.offset_axis = self.offsets[(index + 1) % len(self.offsets)]
        elif self.base_controls.scroll < 0:
            self.offset_axis = self.offsets[(index - 1) % len(self.offsets)]


    def build_shape(self):
        '''Add primative and build the shapes transformations.'''

        # Clear
        bmesh.ops.delete(self.bm, geom=self.bm.verts, context='VERTS')
        self.decap_caps.clear_cap_verts()
        # Primatives
        if self.shape == Shapes.BOX:
            bmesh.ops.create_cube(self.bm)
        elif self.shape == Shapes.SPHERE:
            if bpy.app.version[0] >= 3:
                bmesh.ops.create_uvsphere(self.bm, u_segments=self.segments, v_segments=int(self.segments * .5), radius=.5)
            else:
                bmesh.ops.create_uvsphere(self.bm, u_segments=self.segments, v_segments=int(self.segments * .5), diameter=.5)
        elif self.shape == Shapes.CYLINDER:
            if bpy.app.version[0] >= 3:
                bmesh.ops.create_cone(self.bm, cap_ends=True, cap_tris=False, segments=self.segments, radius1=.5, radius2=.5, depth=1)
            else:
                bmesh.ops.create_cone(self.bm, cap_ends=True, cap_tris=False, segments=self.segments, diameter1=.5, diameter2=.5, depth=1)
        elif self.shape == Shapes.PLANE:
            bmesh.ops.create_grid(self.bm, x_segments=0, y_segments=0, size=.5)
        elif self.shape == Shapes.DECAP:
            self.decap()
            return
        elif self.shape == Shapes.EMPTY:
            self.empty()
            return
        elif self.shape == Shapes.CONVEX:
            self.convex()
            self.translate_shape()
            self.rotate_shape()
            return

        self.rotate_shape()
        self.scale_shape()
        self.translate_shape()

        # Drawing for select shapes
        if self.shape in {Shapes.BOX, Shapes.SPHERE, Shapes.PLANE, Shapes.CYLINDER}:
            tris = self.bm.calc_loop_triangles()
            self.shape_verts = [self.obj.matrix_world @ v.co for v in self.bm.verts]
            self.shape_indices = []
            for tri in tris:
                indexes = []
                for loop in tri:
                    indexes.append(loop.vert.index)
                self.shape_indices.append(tuple(indexes))
            self.shape_edges = []
            for e in self.bm.edges:
                self.shape_edges.append(self.obj.matrix_world @ e.verts[0].co)
                self.shape_edges.append(self.obj.matrix_world @ e.verts[1].co)


    def rotate_shape(self):

        if self.axis == Axis.X:
            mat_rot = Matrix.Rotation(math.radians(90), 4, 'X')
            bmesh.ops.transform(self.bm, matrix=mat_rot, verts=self.bm.verts)
        elif self.axis == Axis.Y:
            mat_rot = Matrix.Rotation(math.radians(90), 4, 'Y')
            bmesh.ops.transform(self.bm, matrix=mat_rot, verts=self.bm.verts)


    def scale_shape(self):

        if self.equalize_radius:
            if self.axis == Axis.X:
                if self.shape == Shapes.CYLINDER:
                    equalized = self.extents[0] if self.extents[0] < self.extents[2] else self.extents[2]
                    scale_mat = hops_math.get_sca_matrix(Vector((equalized, self.extents[1], equalized)))
                    bmesh.ops.transform(self.bm, matrix=scale_mat, verts=self.bm.verts)
                else:
                    equalized = self.extents[0] if self.extents[0] < self.extents[2] else self.extents[2]
                    scale_mat = hops_math.get_sca_matrix(Vector((equalized, equalized, equalized)))
                    bmesh.ops.transform(self.bm, matrix=scale_mat, verts=self.bm.verts)

            elif self.axis == Axis.Y:
                if self.shape == Shapes.CYLINDER:
                    equalized = self.extents[1] if self.extents[1] < self.extents[2] else self.extents[2]
                    scale_mat = hops_math.get_sca_matrix(Vector((self.extents[0], equalized, equalized)))
                    bmesh.ops.transform(self.bm, matrix=scale_mat, verts=self.bm.verts)
                else:
                    equalized = self.extents[1] if self.extents[1] < self.extents[2] else self.extents[2]
                    scale_mat = hops_math.get_sca_matrix(Vector((equalized, equalized, equalized)))
                    bmesh.ops.transform(self.bm, matrix=scale_mat, verts=self.bm.verts)

            elif self.axis == Axis.Z:
                if self.shape == Shapes.CYLINDER:
                    equalized = self.extents[0] if self.extents[0] < self.extents[1] else self.extents[1]
                    scale_mat = hops_math.get_sca_matrix(Vector((equalized, equalized, self.extents[2])))
                    bmesh.ops.transform(self.bm, matrix=scale_mat, verts=self.bm.verts)
                else:
                    equalized = self.extents[0] if self.extents[0] < self.extents[1] else self.extents[1]
                    scale_mat = hops_math.get_sca_matrix(Vector((equalized, equalized, equalized)))
                    bmesh.ops.transform(self.bm, matrix=scale_mat, verts=self.bm.verts)
        else:
            scale_mat = hops_math.get_sca_matrix(self.extents)
            bmesh.ops.transform(self.bm, matrix=scale_mat, verts=self.bm.verts)


    def translate_shape(self):

        if self.shape in {Shapes.SPHERE, Shapes.CYLINDER}:
            if self.equalize_radius == True:
                self.translate_shape_equalized()
                return

        if self.offset_axis == 'XP':
            mat = Matrix.Translation((self.extents[0], 0, 0))

            if self.shape == Shapes.PLANE:
                if self.axis == Axis.Y:
                    mat = Matrix.Translation((self.extents[0] * .5, 0, 0))

            bmesh.ops.transform(self.bm, matrix=mat, verts=self.bm.verts)

        elif self.offset_axis == 'XN':
            mat = Matrix.Translation((-self.extents[0], 0, 0))

            if self.shape == Shapes.PLANE:
                if self.axis == Axis.Y:
                    mat = Matrix.Translation((-self.extents[0] * .5, 0, 0))

            bmesh.ops.transform(self.bm, matrix=mat, verts=self.bm.verts)

        elif self.offset_axis == 'YP':
            mat = Matrix.Translation((0, self.extents[1], 0))

            if self.shape == Shapes.PLANE:
                if self.axis == Axis.X:
                    mat = Matrix.Translation((0, self.extents[1] * .5, 0))

            bmesh.ops.transform(self.bm, matrix=mat, verts=self.bm.verts)

        elif self.offset_axis == 'YN':
            mat = Matrix.Translation((0, -self.extents[1], 0))

            if self.shape == Shapes.PLANE:
                if self.axis == Axis.X:
                    mat = Matrix.Translation((0, -self.extents[1] * .5, 0))

            bmesh.ops.transform(self.bm, matrix=mat, verts=self.bm.verts)

        elif self.offset_axis == 'ZP':
            mat = Matrix.Translation((0, 0, self.extents[2]))

            if self.shape == Shapes.PLANE:
                if self.axis == Axis.Z:
                    mat = Matrix.Translation((0, 0, self.extents[2] * .5))

            bmesh.ops.transform(self.bm, matrix=mat, verts=self.bm.verts)

        elif self.offset_axis == 'ZN':
            mat = Matrix.Translation((0, 0, -self.extents[2]))

            if self.shape == Shapes.PLANE:
                if self.axis == Axis.Z:
                    mat = Matrix.Translation((0, 0, -self.extents[2] * .5))

            bmesh.ops.transform(self.bm, matrix=mat, verts=self.bm.verts)


    def translate_shape_equalized(self):

        coords = [self.obj.matrix_world @ v.co for v in self.bm.verts]
        bounds = hops_math.coords_to_bounds(coords)
        mesh_extents = hops_math.dimensions(bounds)

        if self.offset_axis == 'XP':
            diff = self.extents[0] - mesh_extents[0]
            mat = Matrix.Translation((self.extents[0] - diff * .5, 0, 0))
            bmesh.ops.transform(self.bm, matrix=mat, verts=self.bm.verts)

        elif self.offset_axis == 'XN':
            diff = self.extents[0] - mesh_extents[0]
            mat = Matrix.Translation((-self.extents[0] + diff * .5, 0, 0))
            bmesh.ops.transform(self.bm, matrix=mat, verts=self.bm.verts)

        elif self.offset_axis == 'YP':
            diff = self.extents[1] - mesh_extents[1]
            mat = Matrix.Translation((0, self.extents[1] - diff * .5, 0))
            bmesh.ops.transform(self.bm, matrix=mat, verts=self.bm.verts)

        elif self.offset_axis == 'YN':
            diff = self.extents[1] - mesh_extents[1]
            mat = Matrix.Translation((0, -self.extents[1] + diff * .5, 0))
            bmesh.ops.transform(self.bm, matrix=mat, verts=self.bm.verts)

        elif self.offset_axis == 'ZP':
            diff = self.extents[2] - mesh_extents[2]
            mat = Matrix.Translation((0, 0, self.extents[2] - diff * .5))
            bmesh.ops.transform(self.bm, matrix=mat, verts=self.bm.verts)

        elif self.offset_axis == 'ZN':
            diff = self.extents[2] - mesh_extents[2]
            mat = Matrix.Translation((0, 0, -self.extents[2] + diff * .5))
            bmesh.ops.transform(self.bm, matrix=mat, verts=self.bm.verts)


    def build_shape_batche(self):

        self.shape_edges_batch = batch_for_shader(self.shape_edges_shader, 'LINES', {"pos": self.shape_edges})
        self.shape_faces_batch = batch_for_shader(self.shape_faces_shader, 'TRIS', {'pos': self.shape_verts}, indices=self.shape_indices)


    def decap(self):

        # Clear
        self.decap_draw_edges = []
        bmesh.ops.delete(self.decap_bmesh, geom=self.decap_bmesh.verts, context='VERTS')
        self.decap_bmesh.from_mesh(self.decap_mesh_backup)

        def bisect(plane_co, plane_no, positive=True):
            geom = self.decap_bmesh.verts[:] + self.decap_bmesh.edges[:] + self.decap_bmesh.faces[:]

            if self.keep_caps:
                # ---- Cut for Main ----
                cut_verts = bmesh.ops.bisect_plane(
                    self.decap_bmesh,
                    geom=geom,
                    dist=0,
                    plane_co=plane_co,
                    plane_no=plane_no,
                    use_snap_center=False,
                    clear_outer=True,
                    clear_inner=False)

                edges = [e for e in cut_verts['geom_cut'] if isinstance(e, bmesh.types.BMEdge)]

                for edge in edges:
                    self.decap_draw_edges.append(edge.verts[0].co.copy())
                    self.decap_draw_edges.append(edge.verts[1].co.copy())

                ret = bmesh.ops.split_edges(self.decap_bmesh, edges=edges, use_verts=False)

                if self.fill_holes == True:
                    edges = [e for e in ret['edges'] if isinstance(e, bmesh.types.BMEdge)]
                    bmesh.ops.holes_fill(self.decap_bmesh, edges=edges)

                # ---- Cut for Cap ----
                cap_bm = bmesh.new()
                cap_bm.from_mesh(self.decap_mesh_backup)

                geom = cap_bm.verts[:] + cap_bm.edges[:] + cap_bm.faces[:]
                cut_verts = bmesh.ops.bisect_plane(
                    cap_bm,
                    geom=geom,
                    dist=0,
                    plane_co=plane_co,
                    plane_no=plane_no,
                    use_snap_center=False,
                    clear_outer=False,
                    clear_inner=True)

                edges = [e for e in cut_verts['geom_cut'] if isinstance(e, bmesh.types.BMEdge)]

                for edge in edges:
                    self.decap_draw_edges.append(edge.verts[0].co.copy())
                    self.decap_draw_edges.append(edge.verts[1].co.copy())

                ret = bmesh.ops.split_edges(cap_bm, edges=edges, use_verts=False)

                if self.fill_holes == True:
                    edges = [e for e in ret['edges'] if isinstance(e, bmesh.types.BMEdge)]
                    bmesh.ops.holes_fill(cap_bm, edges=edges)

                if positive == True:
                    self.decap_caps.insert_mesh_into_cap(cap_bm, cap='a')
                else:
                    self.decap_caps.insert_mesh_into_cap(cap_bm, cap='b')

                cap_bm.free()

            else:
                cut_verts = bmesh.ops.bisect_plane(
                    self.decap_bmesh,
                    geom=geom,
                    dist=0,
                    plane_co=plane_co,
                    plane_no=plane_no,
                    use_snap_center=False,
                    clear_outer=True,
                    clear_inner=False)

                if self.fill_holes == True:
                    edges = [e for e in cut_verts['geom_cut'] if isinstance(e, bmesh.types.BMEdge)]
                    bmesh.ops.holes_fill(self.decap_bmesh, edges=edges)

        def clamped_offset(index, positive=True):

            extents = self.extents[index] * .5

            # Clamp center offset
            if self.center_offset > extents:
                self.center_offset = extents
            elif self.center_offset < -extents:
                self.center_offset = -extents

            center = self.center[index] + self.center_offset

            if positive == True:
                val = center + extents - self.decap_mouse_positive

                # Clamp to max side
                if val > self.center[index] + extents:
                    val = self.center[index] + extents

                # Clamp to center point
                if val < center:
                    val = center

                # Clamp mouse center
                if self.decap_mouse_positive > extents:
                    self.decap_mouse_positive = extents

                # Clamp mouse bounds
                if self.decap_mouse_positive - self.center_offset < 0:
                    self.decap_mouse_positive = self.center_offset

                return val

            else:
                val = center - extents + self.decap_mouse_negative

                # Clamp to max side
                if val > self.center[index] + extents:
                    val = self.center[index] + extents

                # Clamp to center point
                if val > center:
                    val = center

                # Clamp to min side
                if val < -extents + self.center[index]:
                    val = -extents + self.center[index]

                # Clamp mouse center
                if self.decap_mouse_negative > extents:
                    self.decap_mouse_negative = extents

                # Clamp mouse bounds
                if self.decap_mouse_negative + self.center_offset < 0:
                    self.decap_mouse_negative = -self.center_offset

                return val

        if self.axis == Axis.X:
            # ----- POSITIVE -----
            x = clamped_offset(0)
            plane_co = Vector((x, 0, 0))
            bisect(plane_co, Vector((1,0,0)))
            # ----- NEGATIVE -----
            x = clamped_offset(0, positive=False)
            plane_co = Vector((x, 0, 0))
            bisect(plane_co, Vector((-1,0,0)), positive=False)

            self.decap_center = Vector((self.center[0] + self.center_offset, self.center[1], self.center[2]))

        elif self.axis == Axis.Y:
            # ----- POSITIVE -----
            y = clamped_offset(1)
            plane_co = Vector((0, y, 0))
            bisect(plane_co, Vector((0,1,0)))
            # ----- NEGATIVE -----
            y = clamped_offset(1, positive=False)
            plane_co = Vector((0, y, 0))
            bisect(plane_co, Vector((0,-1,0)), positive=False)

            self.decap_center = Vector((self.center[0], self.center[1] + self.center_offset, self.center[2]))

        elif self.axis == Axis.Z:
            # ----- POSITIVE -----
            z = clamped_offset(2)
            plane_co = Vector((0, 0, z))
            bisect(plane_co, Vector((0,0,1)))
            # ----- NEGATIVE -----
            z = clamped_offset(2, positive=False)
            plane_co = Vector((0, 0, z))
            bisect(plane_co, Vector((0,0,-1)), positive=False)

            self.decap_center = Vector((self.center[0], self.center[1], self.center[2] + self.center_offset))

        # Shader work
        self.decap_batch_create()


    def decap_batch_create(self):

        indices = [(0,1,2), (0,2,3), (4,5,6), (4,6,7)]

        if self.axis == Axis.X:
            verts = [
                Vector((self.bounds[0][0] + self.decap_mouse_negative + self.center_offset, self.bounds[0][1], self.bounds[0][2])),
                Vector((self.bounds[1][0] + self.decap_mouse_negative + self.center_offset, self.bounds[1][1], self.bounds[1][2])),
                Vector((self.bounds[2][0] + self.decap_mouse_negative + self.center_offset, self.bounds[2][1], self.bounds[2][2])),
                Vector((self.bounds[3][0] + self.decap_mouse_negative + self.center_offset, self.bounds[3][1], self.bounds[3][2])),

                Vector((self.bounds[4][0] - self.decap_mouse_positive + self.center_offset, self.bounds[4][1], self.bounds[4][2])),
                Vector((self.bounds[5][0] - self.decap_mouse_positive + self.center_offset, self.bounds[5][1], self.bounds[5][2])),
                Vector((self.bounds[6][0] - self.decap_mouse_positive + self.center_offset, self.bounds[6][1], self.bounds[6][2])),
                Vector((self.bounds[7][0] - self.decap_mouse_positive + self.center_offset, self.bounds[7][1], self.bounds[7][2]))]
            self.decap_faces_batch = batch_for_shader(self.decap_faces_shader, 'TRIS', {'pos': verts}, indices=indices)

        elif self.axis == Axis.Y:
            verts = [
                Vector((self.bounds[0][0], self.bounds[0][1] + self.decap_mouse_negative + self.center_offset, self.bounds[0][2])),
                Vector((self.bounds[4][0], self.bounds[4][1] + self.decap_mouse_negative + self.center_offset, self.bounds[4][2])),
                Vector((self.bounds[5][0], self.bounds[5][1] + self.decap_mouse_negative + self.center_offset, self.bounds[5][2])),
                Vector((self.bounds[1][0], self.bounds[1][1] + self.decap_mouse_negative + self.center_offset, self.bounds[1][2])),

                Vector((self.bounds[2][0], self.bounds[2][1] - self.decap_mouse_positive + self.center_offset, self.bounds[2][2])),
                Vector((self.bounds[6][0], self.bounds[6][1] - self.decap_mouse_positive + self.center_offset, self.bounds[6][2])),
                Vector((self.bounds[7][0], self.bounds[7][1] - self.decap_mouse_positive + self.center_offset, self.bounds[7][2])),
                Vector((self.bounds[3][0], self.bounds[3][1] - self.decap_mouse_positive + self.center_offset, self.bounds[3][2]))]
            self.decap_faces_batch = batch_for_shader(self.decap_faces_shader, 'TRIS', {'pos': verts}, indices=indices)

        elif self.axis == Axis.Z:
            verts = [
                Vector((self.bounds[1][0], self.bounds[1][1], self.bounds[1][2] - self.decap_mouse_positive + self.center_offset)),
                Vector((self.bounds[2][0], self.bounds[2][1], self.bounds[2][2] - self.decap_mouse_positive + self.center_offset)),
                Vector((self.bounds[6][0], self.bounds[6][1], self.bounds[6][2] - self.decap_mouse_positive + self.center_offset)),
                Vector((self.bounds[5][0], self.bounds[5][1], self.bounds[5][2] - self.decap_mouse_positive + self.center_offset)),

                Vector((self.bounds[3][0], self.bounds[3][1], self.bounds[3][2] + self.decap_mouse_negative + self.center_offset)),
                Vector((self.bounds[0][0], self.bounds[0][1], self.bounds[0][2] + self.decap_mouse_negative + self.center_offset)),
                Vector((self.bounds[4][0], self.bounds[4][1], self.bounds[4][2] + self.decap_mouse_negative + self.center_offset)),
                Vector((self.bounds[7][0], self.bounds[7][1], self.bounds[7][2] + self.decap_mouse_negative + self.center_offset))]
            self.decap_faces_batch = batch_for_shader(self.decap_faces_shader, 'TRIS', {'pos': verts}, indices=indices)

        if self.keep_caps:
            if self.decap_draw_edges != []:
                self.decap_keep_caps_batch = batch_for_shader(self.decap_keep_caps_shader, 'LINES', {"pos": self.decap_draw_edges})


    def empty(self):

        self.reset_objects_and_empties()

        if self.empty_opts == EmptyOpts.GROUP:
            offset = Vector((0,0,0))

            for item in self.empty_objs:
                empty = item[0]
                obj = item[1]

                if self.offset_axis == 'XP':
                    offset = Vector((self.extents[0] * .5, 0, 0))
                    empty.location += offset
                elif self.offset_axis == 'XN':
                    offset = Vector((-self.extents[0] * .5, 0, 0))
                    empty.location += offset
                elif self.offset_axis == 'YP':
                    offset = Vector((0, self.extents[1] * .5, 0))
                    empty.location += offset
                elif self.offset_axis == 'YN':
                    offset = Vector((0, -self.extents[1] * .5, 0))
                    empty.location += offset
                elif self.offset_axis == 'ZP':
                    offset = Vector((0, 0, self.extents[2] * .5))
                    empty.location += offset
                elif self.offset_axis == 'ZN':
                    offset = Vector((0, 0, -self.extents[2] * .5))
                    empty.location += offset

                if empty.name[:11] == 'SingleEmpty':
                    empty.hide_set(True)
                else:
                    empty.hide_set(False)
                    if item[1] != None:
                        item[1].parent = empty
                    else:
                        for other in self.objs:
                            other.parent = empty

            for item in self.original_locations:
                item[0].matrix_world.translation = item[2]
                item[0].matrix_world.translation -= offset

        elif self.empty_opts == EmptyOpts.SINGLE:
            for item in self.empty_objs:
                empty = item[0] # Empty for the mesh
                obj = item[1]   # Associated mesh

                if empty.name[:10] == 'GroupEmpty':
                    empty.hide_set(True)

                else:
                    empty.hide_set(False)
                    if obj != None:

                        if self.reverse_parent_empty == False:
                            empty.location[2] += obj.dimensions[2] * .5
                            obj.parent = empty
                            obj.matrix_world = item[2]
                            obj.location = Vector((0,0,-obj.dimensions[2] * .5))

                        else:
                            location = obj.matrix_world.translation.copy()
                            empty.parent = obj
                            empty.location = Vector((0,0,obj.dimensions[2] * .5))
                            obj.matrix_world.translation = location


    def convex(self):

        self.bm.from_mesh(self.decap_mesh_backup)
        ret = bmesh.ops.convex_hull(self.bm, input=self.bm.verts, use_existing_faces=True)

        verts = [ele for ele in ret['geom_interior'] if isinstance(ele, bmesh.types.BMVert)]
        bmesh.ops.delete(self.bm, geom=verts, context='VERTS')

        coords = [self.obj.matrix_world @ v.co for v in self.bm.verts]
        bounds = hops_math.coords_to_bounds(coords)

        mat = Matrix.Translation((self.bounds[0] - bounds[0]))
        bmesh.ops.transform(self.bm, matrix=mat, verts=self.bm.verts)


    def cycle_axis(self, forward=True):

        if forward:
            if self.axis == Axis.X:
                self.axis = Axis.Y
            elif self.axis == Axis.Y:
                self.axis = Axis.Z
            elif self.axis == Axis.Z:
                self.axis = Axis.X
        else:
            if self.axis == Axis.X:
                self.axis = Axis.Z
            elif self.axis == Axis.Y:
                self.axis = Axis.X
            elif self.axis == Axis.Z:
                self.axis = Axis.Y

        # Default decap on change
        if self.shape == Shapes.DECAP:
            self.center_offset = 0
            self.decap_mouse_positive = .0125
            self.decap_mouse_negative = .0125


    def set_obj_origin_on_exit(self):

        if self.shape == Shapes.CONVEX:
            return

        if self.offset_axis == 'XP':
            self.obj.location[0] += self.extents[0] * .5
            mat = Matrix.Translation((-self.extents[0] * .5, 0, 0))
            bmesh.ops.transform(self.bm, matrix=mat, verts=self.bm.verts)

        elif self.offset_axis == 'XN':
            self.obj.location[0] -= self.extents[0] * .5
            mat = Matrix.Translation((self.extents[0] * .5, 0, 0))
            bmesh.ops.transform(self.bm, matrix=mat, verts=self.bm.verts)

        elif self.offset_axis == 'YP':
            self.obj.location[1] += self.extents[1] * .5
            mat = Matrix.Translation((0, -self.extents[1] * .5, 0))
            bmesh.ops.transform(self.bm, matrix=mat, verts=self.bm.verts)

        elif self.offset_axis == 'YN':
            self.obj.location[1] -= self.extents[1] * .5
            mat = Matrix.Translation((0, self.extents[1] * .5, 0))
            bmesh.ops.transform(self.bm, matrix=mat, verts=self.bm.verts)

        elif self.offset_axis == 'ZP':
            self.obj.location[2] += self.extents[2] * .5
            mat = Matrix.Translation((0, 0, -self.extents[2] * .5))
            bmesh.ops.transform(self.bm, matrix=mat, verts=self.bm.verts)

        elif self.offset_axis == 'ZN':
            self.obj.location[2] -= self.extents[2] * .5
            mat = Matrix.Translation((0, 0, self.extents[2] * .5))
            bmesh.ops.transform(self.bm, matrix=mat, verts=self.bm.verts)


    def cylinder_mouse_axis_adjust(self):

        set_to_zero = False
        if abs(self.mouse_cyclinder) > .5:
            set_to_zero = True

            if self.axis == Axis.X:
                if self.mouse_cyclinder < 0:
                    self.axis = Axis.Y
                else:
                    self.axis = Axis.Z

            elif self.axis == Axis.Y:
                if self.mouse_cyclinder < 0:
                    self.axis = Axis.Z
                else:
                    self.axis = Axis.X

            elif self.axis == Axis.Z:
                if self.mouse_cyclinder < 0:
                    self.axis = Axis.X
                else:
                    self.axis = Axis.Y

        if set_to_zero == True:
            self.mouse_cyclinder = 0


    def plane_mouse_axis_adjust(self):

        set_to_zero = False
        if abs(self.mouse_plane) > .5:
            set_to_zero = True

            if self.axis == Axis.X:
                if self.mouse_plane < 0:
                    self.axis = Axis.Y
                else:
                    self.axis = Axis.Z

            elif self.axis == Axis.Y:
                if self.mouse_plane < 0:
                    self.axis = Axis.Z
                else:
                    self.axis = Axis.X

            elif self.axis == Axis.Z:
                if self.mouse_plane < 0:
                    self.axis = Axis.X
                else:
                    self.axis = Axis.Y

        if set_to_zero == True:
            self.mouse_plane = 0


    def reset_objects_and_empties(self):

        for obj in self.objs:
            obj.parent = None

        for item in self.empty_objs:
            item[0].parent = None

        for item in self.original_obj_parents:
            item[0].parent = item[1]

        for item in self.original_locations: # (item 1 = object, item 2 = the copied vector)
            item[0].matrix_world = item[3]

        for item in self.original_empty_locations: # (item 1 = object, item 2 = the copied vector)
            item[0].matrix_world.translation = item[1]


    def set_decap_origins_on_ext(self):

        # ---- Center Obj ----
        obj = self.decap_obj
        mesh = obj.data
        obj_loc = obj.matrix_world.translation
        CENTER_ORIGIN = obj.matrix_world @ (0.125 * sum((Vector(b) for b in obj.bound_box), Vector()))
        DIMS = obj.dimensions.copy()

        vec = obj_loc - CENTER_ORIGIN
        mat = Matrix.Translation(vec)
        mesh.transform(mat)
        obj.matrix_world.translation = CENTER_ORIGIN

        # ---- Cap A ----
        obj = self.decap_caps.obj_a
        mesh = obj.data
        obj_loc = obj.matrix_world.translation
        bbox_center = obj.matrix_world @ (0.125 * sum((Vector(b) for b in obj.bound_box), Vector()))

        if self.axis == Axis.X:
            vec = obj_loc - CENTER_ORIGIN
            vec[0] -= DIMS[0]
        elif self.axis == Axis.Y:
            vec = obj_loc - CENTER_ORIGIN
            vec[1] -= DIMS[1]
        elif self.axis == Axis.Z:
            vec = obj_loc - CENTER_ORIGIN
            vec[2] -= DIMS[2]

        mat = Matrix.Translation(vec)
        mesh.transform(mat)
        obj.matrix_world.translation = -vec

        # ---- Cap B ----
        obj = self.decap_caps.obj_b
        mesh = obj.data
        obj_loc = obj.matrix_world.translation
        bbox_center = obj.matrix_world @ (0.125 * sum((Vector(b) for b in obj.bound_box), Vector()))

        if self.axis == Axis.X:
            vec = obj_loc - CENTER_ORIGIN
            vec[0] += DIMS[0]
        elif self.axis == Axis.Y:
            vec = obj_loc - CENTER_ORIGIN
            vec[1] += DIMS[1]
        elif self.axis == Axis.Z:
            vec = obj_loc - CENTER_ORIGIN
            vec[2] += DIMS[2]

        mat = Matrix.Translation(vec)
        mesh.transform(mat)
        obj.matrix_world.translation = -vec


    def set_decap_array_on_exit(self):

        obj = self.decap_obj
        obj_a = self.decap_caps.obj_a
        obj_b = self.decap_caps.obj_b

        obj_a.hide_set(True)
        obj_b.hide_set(True)

        mod = obj.modifiers.new('DecapArray', 'ARRAY')
        mod.count = 1
        mod.relative_offset_displace = (0,0,0)
        mod.use_merge_vertices = True
        mod.merge_threshold = 0.02
        mod.use_merge_vertices_cap = True
        mod.start_cap = obj_b
        mod.end_cap = obj_a

        if self.axis == Axis.X:
            mod.relative_offset_displace[0] = 1
        elif self.axis == Axis.Y:
            mod.relative_offset_displace[1] = 1
        elif self.axis == Axis.Z:
            mod.relative_offset_displace[2] = 1

    ####################################################
    #   SHADERS
    ####################################################

    def remove_shaders(self):
        '''Remove shader handle.'''

        if self.draw_handle_2D:
            self.draw_handle_2D = bpy.types.SpaceView3D.draw_handler_remove(self.draw_handle_2D, "WINDOW")
        if self.draw_handle_3D:
            self.draw_handle_3D = bpy.types.SpaceView3D.draw_handler_remove(self.draw_handle_3D, "WINDOW")

    # ------- 2D SHADER -------
    def safe_draw_2D(self, context):
        method_handler(self.draw_shader_2D,
            arguments = (context,),
            identifier = 'Modal Shader 2D',
            exit_method = self.remove_shaders)


    def draw_shader_2D(self, context):

        self.flow.draw_2D()

        if self.shape == Shapes.DECAP:
            draw_modal_frame(context)
        elif self.shape == Shapes.CYLINDER:
            draw_modal_frame(context)

    # ------- 3D SHADER -------
    def safe_draw_3D(self, context):
        method_handler(self.draw_shader_3D,
            arguments = (context,),
            identifier = 'Modal Shader 3D',
            exit_method = self.remove_shaders)


    def draw_shader_3D(self, context):

        if not self.show_graphics:
            return

        #Enable(GL_LINE_SMOOTH)
        gpu.state.blend_set('ALPHA')

        # Edges
        if self.edges_batch:
            gpu.state.line_width_set(2)
            self.edges_shader.bind()
            self.edges_shader.uniform_float("color", (1,.75,0,.25))
            self.edges_batch.draw(self.edges_shader)

        gpu.state.depth_test_set('LESS')
        #glDepthFunc(GL_LESS)

        if self.shape == Shapes.DECAP and self.decap_faces_batch:
            color = (0,0,0,0)
            if self.axis == Axis.X:
                color = (1,0,0, .125)
            elif self.axis == Axis.Y:
                color = (0,1,0, .125)
            elif self.axis == Axis.Z:
                color = (0,0,1, .125)
            self.decap_faces_shader.bind()
            self.decap_faces_shader.uniform_float("color", color)
            self.decap_faces_batch.draw(self.edges_shader)

            if self.keep_caps and self.decap_keep_caps_batch:
                gpu.state.depth_test_set('NONE')
                gpu.state.face_culling_set('NONE')
                gpu.state.line_width_set(3)
                self.decap_keep_caps_shader.bind()
                self.decap_keep_caps_shader.uniform_float("color", (1, 1, 1, 1))
                self.decap_keep_caps_batch.draw(self.decap_keep_caps_shader)

            # Draw center point
            color = (1,0,0,1)
            if self.axis == Axis.Y:
                color = (0,1,0,1)
            elif self.axis == Axis.Z:
                color = (0,0,1,1)
            built_in_shader = 'UNIFORM_COLOR' if bpy.app.version[0] >=4 else '3D_UNIFORM_COLOR'
            shader = gpu.shader.from_builtin(built_in_shader)
            batch = batch_for_shader(shader, 'POINTS', {'pos': [self.decap_center]})
            shader.bind()
            shader.uniform_float('color', color)
            gpu.state.blend_set('ALPHA')
            gpu.state.depth_test_set('NONE')
            gpu.state.face_culling_set('NONE')
            gpu.state.point_size_set(12)
            batch.draw(shader)
            del shader
            del batch

        elif self.shape in {Shapes.BOX, Shapes.SPHERE, Shapes.PLANE, Shapes.CYLINDER}:

            if not self.shape_edges_batch or not self.shape_faces_batch:
                return

            gpu.state.depth_test_set('NONE')
            gpu.state.face_culling_set('NONE')
            gpu.state.blend_set('ALPHA')
            self.shape_faces_shader.bind()
            self.shape_faces_shader.uniform_float('color', (1,1,1,.125))
            self.shape_faces_batch.draw(self.shape_faces_shader)

            gpu.state.line_width_set(1)
            self.shape_edges_shader.bind()
            self.shape_edges_shader.uniform_float("color", addon.preference().color.Hops_wire_mesh)
            self.shape_edges_batch.draw(self.shape_edges_shader)

        gpu.state.depth_test_set('NONE')
        gpu.state.face_culling_set('NONE')
        gpu.state.blend_set('NONE')
