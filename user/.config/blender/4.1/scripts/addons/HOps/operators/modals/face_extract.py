import re
import bpy, math, gpu, bmesh
from enum import Enum
from mathutils import Vector, Matrix
from gpu_extras.batch import batch_for_shader
from bpy_extras import view3d_utils
from ... utility import addon
from ... utility.base_modal_controls import Base_Modal_Controls
from ... ui_framework.master import Master
from ... utils.toggle_view3d_panels import collapse_3D_view_panels
from ... utility import method_handler
from ... utils.space_3d import ray_cast_objects
from ... ui_framework import form_ui as form


class State(Enum):
    EXTRACT = 0
    BOOLEAN = 1
    SOLIDIFY = 2

    @classmethod
    def states(cls):
        return [cls.EXTRACT, cls.BOOLEAN, cls.SOLIDIFY]


DESC = """Face Extract

Select faces to create interactive boolean
Shift Click - Only creates face duplicate
Ctrl Click - Use decimate on initialize

Press H for help"""


class HOPS_OT_FaceExtract(bpy.types.Operator):
    bl_idname = "view3d.face_extract"
    bl_label = "Face Extract"
    bl_description = DESC
    bl_options = {"REGISTER", "UNDO", "BLOCKING"}

    # Popover
    operator = None
    selected_operation = ""

    @classmethod
    def poll(cls, context):
        if context.active_object:
            if context.active_object.type == 'MESH':
                return True
        return False


    def invoke(self, context, event):

        # State
        self.state = State.EXTRACT if event.shift else State.BOOLEAN
        self.mouse_down = False
        self.indexes_during_this_mouse_down = []
        self.use_last_bevel = True
        self.use_decimate = True if event.ctrl else False
        self.use_local_view = True
        self.started_in_local = context.space_data.local_view

        # Object
        self.og_object = context.active_object
        self.og_mod_visibility = {m.name : m.show_viewport for m in self.og_object.modifiers}
        self.mesh = None
        self.obj = None
        self.setup_object(context)
        self.face_indexes = []

        # Shader
        built_in_shader = 'UNIFORM_COLOR' if bpy.app.version[0] >=4 else '3D_UNIFORM_COLOR'
        self.shader = gpu.shader.from_builtin(built_in_shader)
        self.line_batch = None
        self.face_batch = None

        # Dot UI
        self.show_form = len(self.og_object.modifiers) > 0
        self.form = None
        self.setup_form(context, event)

        # --- Base Systems --- #
        self.master = Master(context)
        self.master.only_use_fast_ui = True
        self.base_controls = Base_Modal_Controls(context, event, popover_keys=['TAB'])
        self.base_controls.confirm_events = ['SPACE', 'RET', 'NUMPAD_ENTER']
        self.base_controls.pass_through_events = ['MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE']
        self.original_tool_shelf, self.original_n_panel = collapse_3D_view_panels()
        self.draw_handle_2D = bpy.types.SpaceView3D.draw_handler_add(self.safe_draw_2D, (context,), 'WINDOW', 'POST_PIXEL')
        self.draw_handle_3D = bpy.types.SpaceView3D.draw_handler_add(self.safe_draw_3D, (context,), 'WINDOW', 'POST_VIEW')

        context.window_manager.modal_handler_add(self)

        # Popover
        self.__class__.operator = self
        self.__class__.selected_operation = ""

        return {"RUNNING_MODAL"}


    def modal(self, context, event):

        # --- Base Systems --- #
        self.master.receive_event(event)
        self.base_controls.update(context, event)

        if self.show_form:
            self.form.update(context, event)

        alt_scroll = True if event.type in {'WHEELDOWNMOUSE', 'WHEELUPMOUSE'} and event.alt else False

        # --- Base Controls --- #
        if self.base_controls.pass_through:
            if not self.form.active():
                if not alt_scroll:
                    return {'PASS_THROUGH'}

        elif self.base_controls.cancel:
            return self.cancel_exit(context)

        elif self.base_controls.confirm:
            if not self.form.active():
                return self.confirm_exit(context)

        # Popover
        ret = self.popover(context)
        if ret == True: return {'FINISHED'}

        # --- Actions --- #

        scroll_step = self.base_controls.scroll
        if alt_scroll and scroll_step:
            types = State.states()
            index = types.index(self.state) + scroll_step
            self.state = types[index % len(types)]

        if not self.form.active():
            self.actions(context, event)

        self.interface(context)
        context.area.tag_redraw()
        return {"RUNNING_MODAL"}


    def actions(self, context, event):

        # Mouse Controls
        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            if event.ctrl:
                self.select_shortest_path(context, event)
                return
            else:
                self.mouse_down = True

        elif event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            self.mouse_down = False
            self.indexes_during_this_mouse_down = []

        self.select_face(context, event)

        # Exit to solidify
        if event.type == 'S' and event.value == "PRESS":
            if self.state == State.SOLIDIFY:
                self.state = State.EXTRACT
            else:
                self.state = State.SOLIDIFY
            bpy.ops.hops.display_notification(info=f"Exit : {self.state.name}")

        # Exit to boolean / Clear Selection
        elif event.type == 'A' and event.value == "PRESS":
            if event.alt:
                self.clear_data()
            else:
                if self.state == State.BOOLEAN:
                    self.state = State.EXTRACT
                else:
                    self.state = State.BOOLEAN
                bpy.ops.hops.display_notification(info=f"Exit : {self.state.name}")

        # Remove last bevel
        elif event.type == 'W' and event.value == "PRESS":
            self.clear_data()
            self.use_last_bevel = not self.use_last_bevel
            bpy.ops.hops.display_notification(info=f"Bevel : {'ON' if self.use_last_bevel else 'OFF'}")
            self.restart_object(context)

        # Decimate
        elif event.type == 'D' and event.value == "PRESS":
            self.clear_data()
            self.use_decimate = not self.use_decimate
            bpy.ops.hops.display_notification(info=f"Decimate : {'ON' if self.use_decimate else 'OFF'}")
            self.restart_object(context)

        # Local View
        elif event.type in {'NUMPAD_SLASH', 'SLASH', 'BACK_SLASH'} and event.value == "PRESS":
            self.use_local_view = not self.use_local_view
            bpy.ops.view3d.localview(frame_selected=False)

        return None


    def select_face(self, context, event, ignore_mouse_satus=False, ignore_draw_data_rebuild=False):

        if not self.mouse_down and not ignore_mouse_satus: return

        mouse = Vector((event.mouse_region_x, event.mouse_region_y))
        origin = view3d_utils.region_2d_to_origin_3d(context.region, context.space_data.region_3d, mouse)
        direction = view3d_utils.region_2d_to_vector_3d(context.region, context.space_data.region_3d, mouse)
        result, location, normal, index, object, matrix = ray_cast_objects(context, origin, direction, [self.obj], evaluated=False)

        if not result: return
        if object != self.obj: return
        if index > len(self.obj.data.polygons) - 1: return
        if index < 0: return

        # This allows click drag
        if index in self.indexes_during_this_mouse_down: return
        self.indexes_during_this_mouse_down.append(index)

        if index not in self.face_indexes:
            self.face_indexes.append(index)
        else:
            self.face_indexes.remove(index)

        if not ignore_draw_data_rebuild:
            self.update_draw_data()


    def select_shortest_path(self, context, event):
        if not self.obj: return
        if not self.mesh: return
        if not self.face_indexes: return

        last_face_selected = self.face_indexes[-1]

        self.select_face(context, event, ignore_mouse_satus=True, ignore_draw_data_rebuild=True)
        new_face_selected = self.face_indexes[-1]

        if last_face_selected == new_face_selected: return

        bpy.ops.object.mode_set(mode='EDIT', toggle=False)

        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_mode(use_extend=False, type="FACE")

        bm = bmesh.from_edit_mesh(self.mesh)
        bm.faces.ensure_lookup_table()

        bm.faces[last_face_selected].select_set(True)
        bm.faces[new_face_selected].select_set(True)
        bm.faces.active = bm.faces[last_face_selected]

        bpy.ops.mesh.shortest_path_select(edge_mode='SELECT')
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

        for polygon in self.mesh.polygons:
            if polygon.select:
                if polygon.index not in self.face_indexes:
                    self.face_indexes.append(polygon.index)

        if new_face_selected in self.face_indexes:
            self.face_indexes.remove(new_face_selected)
            self.face_indexes.append(new_face_selected)

        self.update_draw_data()


    def interface(self, context):

        self.master.setup()
        if not self.master.should_build_fast_ui(): return

        # Main
        win_list = []

        msg = "Mode : Extract"
        if self.state == State.BOOLEAN: msg = "Mode : Boolean"
        elif self.state == State.SOLIDIFY: msg = "Mode : Solidify"
        win_list.append(msg)
        win_list.append(f"Decimate : {'ON' if self.use_decimate else 'OFF'}")

        # Help
        help_items = {"GLOBAL" : [], "STANDARD" : []}

        help_items["GLOBAL"] = [
            ("M", "Toggle mods list"),
            ("H", "Toggle help"),
            ("~", "Toggle UI Display Type"),
            ("O", "Toggle viewport rendering")
        ]

        help_items["STANDARD"] = [
            ("/",           f"Local Mode : {'OFF' if context.space_data.local_view else 'ON'}"),
            ("Alt Scroll",  "Cycle Modes"),
            ("D",           "Remove Decimate" if self.use_decimate else "Add Decimate"),
            ("W",           "Remove last Bevel"),
            ("A",          f"Exit to Boolean : {'True' if self.state == State.BOOLEAN else 'False'}"),
            ("S",          f"Exit to Solidify : {'True' if self.state == State.SOLIDIFY else 'False'}"),
            ("Alt A",       "Clear Selection"),
            ("Spacebar",    "Accept"),
            ("Ctrl Click",  "Select Linked"),
            ("Click",       "Select face")]

        if self.show_form:
            help_items["STANDARD"].append(("Tab", f"Dot UI : {'CLOSE' if self.form.is_dot_open() else 'OPEN'}"))

        self.master.receive_fast_ui(win_list=win_list, help_list=help_items, image="FacePanel")
        self.master.finished()

    # --- UTILS --- #

    def setup_object(self, context):

        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        if self.use_local_view:
            if context.space_data.local_view:
                bpy.ops.view3d.localview(frame_selected=False)

        active_obj = context.active_object

        self.obj = active_obj.copy()
        self.obj.data = active_obj.data.copy()

        context.collection.objects.link(self.obj)
        context.view_layer.objects.active = self.obj

        self.obj.show_wire = True

        if self.use_decimate:
            mod = self.obj.modifiers.new("Decimate", 'DECIMATE')
            mod.decimate_type = 'DISSOLVE'
            mod.angle_limit = math.radians(.05)

        if self.use_last_bevel == False:
            for mod in reversed(self.obj.modifiers):
                if mod.type == 'BEVEL':
                    if mod.show_viewport:
                        mod.show_viewport = False
                        break

        bpy.ops.object.select_all(action='DESELECT')
        self.obj.select_set(True)
        bpy.ops.object.convert(target='MESH')
        self.mesh = self.obj.data

        if self.use_local_view:
            bpy.ops.view3d.localview(frame_selected=False)

        self.og_object.hide_set(True)


    def update_draw_data(self):

        matrix = self.obj.matrix_world

        # --- LINES --- #
        verts = []
        indices = []
        offset = 0
        for face_index in self.face_indexes:
            polygon = self.mesh.polygons[face_index]
            vert_indices = polygon.vertices

            normal = polygon.normal

            for vert_indice in vert_indices:
                vert = self.mesh.vertices[vert_indice]
                pos = matrix @ (normal * .005 + vert.co)
                verts.append(pos)

            for i in range(len(vert_indices)):
                j = offset + i
                if i == len(vert_indices) - 1:
                    indices.append((j, offset))
                else:
                    indices.append((j, j + 1))

            offset += len(vert_indices)

        self.line_batch = batch_for_shader(self.shader, 'LINES', {'pos': verts}, indices=indices)

        # --- FACE --- #
        verts = []
        indices = []
        self.mesh.calc_loop_triangles()

        offset = 0
        for loop in self.mesh.loop_triangles:
            if loop.polygon_index not in self.face_indexes: continue

            normal = loop.normal

            for vert_indice in loop.vertices:
                vert = self.mesh.vertices[vert_indice]
                pos = matrix @ (normal * .005 + vert.co)
                verts.append(pos)

            indices.append((offset, offset+1, offset+2))
            offset += 3

        self.face_batch = batch_for_shader(self.shader, 'TRIS', {'pos': verts}, indices=indices)


    def extract(self, context):
        bm = bmesh.new()
        bm.from_mesh(self.mesh)

        # Remove all the other faces
        bm.faces.ensure_lookup_table()
        faces = [ f for f in bm.faces if f.index not in self.face_indexes ]
        bmesh.ops.delete(bm, geom=faces, context='FACES')

        # Remove any loose verts
        bm.faces.ensure_lookup_table()
        bm.verts.ensure_lookup_table()
        face_verts = []
        for face in bm.faces:
            for vert in face.verts:
                face_verts.append(vert)
        verts = []
        for vert in bm.verts:
            if vert not in face_verts:
                verts.append(vert)
        if verts:
            bmesh.ops.delete(bm, geom=verts, context='VERTS')

        sca = Matrix.Diagonal(self.obj.matrix_world.decompose()[2]).to_4x4()
        bmesh.ops.transform(bm, matrix=sca, space=Matrix(), verts=bm.verts)

        bm.to_mesh(self.mesh)
        bm.free()

        self.obj.parent = None

        loc, rot, _ = self.obj.matrix_world.decompose()
        sca = Vector((1,1,1))

        mat_loc = Matrix.Translation(loc).to_4x4()
        mat_rot = rot.to_matrix().to_4x4()
        mat_sca = Matrix.Identity(4)

        mat = mat_loc @ mat_rot @ mat_sca
        self.obj.matrix_world = mat


    def restart_object(self, context, cancel_use_last_bevel=False):

        if cancel_use_last_bevel: self.use_last_bevel = True

        self.clear_data()

        if context.space_data.local_view:
            bpy.ops.view3d.localview(frame_selected=False)

        bpy.ops.object.select_all(action='DESELECT')

        context.view_layer.objects.active = self.og_object
        self.og_object.select_set(True)
        self.og_object.hide_set(False)

        bpy.data.objects.remove(self.obj)
        self.obj = None
        bpy.data.meshes.remove(self.mesh)
        self.mesh = None

        self.setup_object(context)


    def popover(self, context):
        if self.__class__.selected_operation != "":
            if self.__class__.selected_operation == "EXTRACT":
                self.state = State.EXTRACT
            elif self.__class__.selected_operation == "BOOLEAN":
                self.state = State.BOOLEAN
            elif self.__class__.selected_operation == "SOLIDIFY":
                self.state = State.SOLIDIFY
            elif self.__class__.selected_operation == "CONFIRM":
                self.confirm_exit(context)
                return True

            bpy.ops.hops.display_notification(info=f'State Set To : {self.__class__.selected_operation}')
            self.__class__.selected_operation = ""

        # Spawns
        if self.base_controls.popover:
            context.window_manager.popover(popup_draw)

        return False


    def clear_data(self):
        self.face_indexes = []
        self.indexes_during_this_mouse_down = []
        self.line_batch = None
        self.face_batch = None

    # --- FORM FUNCS --- #

    def setup_form(self, context, event):
        # MAX WIDTH = 165
        self.form = form.Form(context, event, dot_open=False)

        # Mod Scroll Box
        group = form.Scroll_Group()
        for index, mod in enumerate(self.og_object.modifiers):
            row = group.row()
            # Count
            row.add_element(form.Label(text=str(index + 1), width=25, height=20))
            # Mod name
            text = form.shortened_text(mod.name, width=95, font_size=12)
            row.add_element(form.Label(text=text, width=100, height=20))
            # Visible
            row.add_element(form.Button(
                scroll_enabled=False, text="X", highlight_text="O", tips=["Toggle visibility"],
                width=20, height=20, use_padding=False,
                callback=self.rebuild_from_form, pos_args=(mod, context),
                highlight_hook_obj=mod, highlight_hook_attr='show_viewport'))
            group.row_insert(row)
        row = self.form.row()

        box_height = 160

        if len(self.og_object.modifiers) < 8:
            box_height = 20 * len(self.og_object.modifiers)

        mod_box = form.Scroll_Box(width=165, height=box_height, scroll_group=group, view_scroll_enabled=True)
        row.add_element(mod_box)
        self.form.row_insert(row, active=True)

        self.form.build()


    def rebuild_from_form(self, mod, context):
        mod.show_viewport = not mod.show_viewport
        self.restart_object(context, cancel_use_last_bevel=True)

    # --- EXIT --- #

    def common_exit(self, context):
        self.__class__.operator = None
        self.__class__.selected_operation = ""

        for mod in self.og_object.modifiers:
            if mod.name not in self.og_mod_visibility: continue
            mod.show_viewport = self.og_mod_visibility[mod.name]

        self.og_object.hide_set(False)
        if context.space_data.local_view:
            bpy.ops.view3d.localview(frame_selected=False)
        self.remove_shaders()
        collapse_3D_view_panels(self.original_tool_shelf, self.original_n_panel)
        self.master.destroy_immediate()


    def confirm_exit(self, context):

        # Nothing selected
        if not self.face_indexes:
            return self.cancel_exit(context)

        self.common_exit(context)
        self.extract(context)

        context.view_layer.objects.active = self.obj
        bpy.ops.mesh.customdata_custom_splitnormals_clear()

        if self.state == State.SOLIDIFY:
            bpy.ops.hops.adjust_tthick('INVOKE_DEFAULT')
            self.obj.show_wire = False

        elif self.state == State.BOOLEAN:
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.hops.sel_to_bool_v3('INVOKE_DEFAULT', override_obj_name=self.og_object.name)

        elif self.state == State.EXTRACT:
            bpy.ops.hops.draw_wire_mesh_launcher('INVOKE_DEFAULT', object_name=self.obj.name)
            self.obj.show_wire = False

        return {'FINISHED'}


    def cancel_exit(self, context):
        self.common_exit(context)

        bpy.data.objects.remove(self.obj)
        bpy.data.meshes.remove(self.mesh)
        self.og_object.select_set(True)
        context.view_layer.objects.active = self.og_object

        return {'CANCELLED'}

    # --- SHADERS --- #

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
        if self.show_form:
            self.form.draw()


    def safe_draw_3D(self, context):
        method_handler(self.draw_shader_3D,
            arguments = (context,),
            identifier = 'Modal Shader 3D',
            exit_method = self.remove_shaders)


    def draw_shader_3D(self, context):

        if self.line_batch == None:
            if self.face_batch == None:
                return

        #Enable(GL_LINE_SMOOTH)
        gpu.state.blend_set('ALPHA')
        gpu.state.depth_test_set('LESS')
        #glDepthFunc(GL_LESS)

        self.shader.bind()
        color = [1,0,0,1]
        if self.state == State.EXTRACT:
            color = [0,0,1,1]
        if self.state == State.SOLIDIFY:
            color = [1,0,1,1]
        self.shader.uniform_float('color', color)

        if self.line_batch:
            gpu.state.line_width_set(2)
            self.line_batch.draw(self.shader)

        if self.face_batch:
            color[3] = .1
            self.shader.uniform_float('color', color)
            self.face_batch.draw(self.shader)

        #Disable(GL_LINE_SMOOTH)
        gpu.state.depth_test_set('NONE')
        gpu.state.face_culling_set('NONE')
        gpu.state.depth_test_set('NONE')

# --- POPOVER --- #

def popup_draw(self, context):
    layout = self.layout

    op = HOPS_OT_FaceExtract.operator
    if not op: return {'CANCELLED'}

    layout.label(text='Selector')
    broadcaster = "hops.popover_data"

    row = layout.row()
    row.scale_y = 2
    props = row.operator(broadcaster, text='Extract')
    props.calling_ops = 'FACE_EXTRACT'
    props.str_1 = 'EXTRACT'

    row = layout.row()
    row.scale_y = 2
    props = row.operator(broadcaster, text='Boolean')
    props.calling_ops = 'FACE_EXTRACT'
    props.str_1 = 'BOOLEAN'

    row = layout.row()
    row.scale_y = 2
    props = row.operator(broadcaster, text='Solidify')
    props.calling_ops = 'FACE_EXTRACT'
    props.str_1 = 'SOLIDIFY'

    if op.face_indexes:
        row = layout.row()
        row.scale_y = 2
        props = row.operator(broadcaster, text='Confirm')
        props.calling_ops = 'FACE_EXTRACT'
        props.str_1 = 'CONFIRM'
    else:
        row = layout.row()
        row.scale_y = 2
        row.label(text="Select faces before continuing.")

