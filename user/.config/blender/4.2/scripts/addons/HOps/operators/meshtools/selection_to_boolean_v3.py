import bpy, bmesh
from mathutils import Matrix, Vector
from enum import Enum
from ... utility import addon
from ... utility.base_modal_controls import Base_Modal_Controls
from ... utility.collections import view_layer_unhide, hide_all_objects_in_collection, hops_col_get
from ... ui_framework.master import Master
from ... ui_framework.utils.mods_list import get_mods_list
from ... utils.toggle_view3d_panels import collapse_3D_view_panels
from ... utils.modal_frame_drawing import draw_modal_frame
from ... utils.cursor_warp import mouse_warp
from ... utility import method_handler
from ... utility.modifier import user_sort


class State(Enum):
    INSET = 0
    EXTRUDE = 1

    @classmethod
    def states(cls):
        return [cls.INSET, cls.EXTRUDE]


class HOPS_OT_Sel_To_Bool_V3(bpy.types.Operator):
    bl_idname = "hops.sel_to_bool_v3"
    bl_label = "Selection To Boolean V3"
    bl_description = """Selection to Boolean
    Convert active face(s) to boolean
    Press H for help
    """
    bl_options = {"REGISTER", "UNDO", "BLOCKING"}

    override_obj_name: bpy.props.StringProperty(name="Target Override", default="")

    # Popover
    operator = None
    selected_operation = ""

    @classmethod
    def poll(cls, context):
        if context.mode == 'EDIT_MESH':
            if context.active_object and context.active_object.type == 'MESH':
                return True
        return False


    def invoke(self, context, event):

        # Override : Called from extract face
        use_override = False
        if self.override_obj_name:
            if self.override_obj_name in bpy.data.objects:
                target_obj = bpy.data.objects[self.override_obj_name]
                if target_obj.name in context.view_layer.objects:
                    use_override = True
                    self.override_setup(context, target_obj)

        if use_override == False:
            # Target
            self.obj = context.active_object
            self.boolean_mod = None

            # Boolean
            self.bool_obj = None
            self.solidify_mod = None
            self.bm = None
            self.bool_mesh_backup = None

            # Setup
            if not self.selection_valid(): return {'CANCELLED'}
            self.standard_setup(context)

        # State
        self.state = State.INSET
        self.apply_mods = False
        self.use_as_boolean = True
        self.og_xray = context.space_data.shading.show_xray
        self.og_shading = context.space_data.shading.type

        # Controls
        self.accumulation = 0
        self.inset_value = 0
        self.extrude_value = 0

        # Base Systems
        self.master = Master(context)
        self.master.only_use_fast_ui = True
        self.base_controls = Base_Modal_Controls(context, event, popover_keys=['TAB', 'SPACE'])
        self.original_tool_shelf, self.original_n_panel = collapse_3D_view_panels()
        self.draw_handle_2D = bpy.types.SpaceView3D.draw_handler_add(self.safe_draw_2D, (context,), 'WINDOW', 'POST_PIXEL')
        context.window_manager.modal_handler_add(self)

        # Popover
        self.__class__.operator = self
        self.__class__.selected_operation = ""

        return {"RUNNING_MODAL"}

    # --- Setup --- #

    def selection_valid(self):
        bm = bmesh.from_edit_mesh(self.obj.data)
        faces = [f for f in bm.faces if f.select]
        if len(faces) > 0: return True
        else: return False


    def override_setup(self, context, target_obj):

        self.obj = target_obj
        self.bool_obj = context.active_object
        self.bool_obj.hops.status = "BOOLSHAPE"

        # Collection
        col = hops_col_get(bpy.context)

        if col and self.bool_obj.users_collection:
            for collection in self.bool_obj.users_collection:
                if collection != col:
                    collection.objects.unlink(self.bool_obj)
                
        if self.bool_obj.name not in col.objects:
            view_layer_unhide(col, enable=True)
            hide_all_objects_in_collection(coll=col)
            col.objects.link(self.bool_obj)

        self.add_mods(context)
        self.parent_move_display()

        context.view_layer.objects.active = self.bool_obj

        # Edit
        if context.mode != 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT')

        # Clean
        self.bm = bmesh.from_edit_mesh(self.bool_obj.data)
        self.bool_obj.update_from_editmode()

        # Backup
        self.bool_mesh_backup = self.bool_obj.data.copy()


    def standard_setup(self, context):

        # New mesh
        bpy.ops.object.mode_set(mode='OBJECT')
        mesh = self.obj.data.copy()
        self.bool_obj = bpy.data.objects.new(mesh.name, mesh)
        self.bool_obj.hops.status = "BOOLSHAPE"

        # Collection
        col = hops_col_get(bpy.context)

        view_layer_unhide(col, enable=True)
        hide_all_objects_in_collection(coll=col)

        col.objects.link(self.bool_obj)

        self.add_mods(context)
        self.parent_move_display()

        # Edit
        bpy.ops.object.select_all(action='DESELECT')
        self.bool_obj.select_set(True)
        context.view_layer.objects.active = self.bool_obj
        bpy.ops.object.mode_set(mode='EDIT')

        # Clean
        self.bm = bmesh.from_edit_mesh(self.bool_obj.data)
        verts = [v for v in self.bm.verts if not v.select]
        bmesh.ops.delete(self.bm, geom=verts, context='VERTS')
        faces = [f for f in self.bm.faces if not f.select]
        bmesh.ops.delete(self.bm, geom=faces, context='FACES')
        
        sca = self.obj.matrix_world.decompose()[2]
        bmesh.ops.transform(self.bm, matrix=Matrix.Diagonal(sca), space=Matrix(), verts=self.bm.verts)
        
        bmesh.update_edit_mesh(self.bool_obj.data)
        self.bool_obj.update_from_editmode()

        # Backup
        self.bool_mesh_backup = self.bool_obj.data.copy()


    def add_mods(self, context):

        # Solidify
        self.solidify_mod = self.bool_obj.modifiers.new('Solidify', type='SOLIDIFY')
        self.solidify_mod.use_even_offset = True
        self.solidify_mod.offset = -.95
        self.solidify_mod.use_quality_normals = True
        self.solidify_mod.show_viewport = False

        # Boolean
        self.boolean_mod = self.obj.modifiers.new("HOPS Boolean", 'BOOLEAN')
        if hasattr(self.boolean_mod, 'solver'):
            self.boolean_mod.solver = 'FAST'
        self.boolean_mod.show_render = True
        self.boolean_mod.object = self.bool_obj
        self.boolean_mod.show_viewport = False

        user_sort(self.obj)


    def parent_move_display(self):
        
        loc, rot, sca = self.obj.matrix_world.decompose()
        mat_loc = Matrix.Translation(loc).to_4x4()
        mat_sca = Matrix.Diagonal(Vector((1,1,1))).to_4x4()
        mat_rot = rot.to_matrix().to_4x4()
        mat_out = mat_loc @ mat_rot @ mat_sca
                
        self.bool_obj.matrix_world = mat_out
        self.bool_obj.parent = self.obj
        self.bool_obj.matrix_parent_inverse = self.obj.matrix_world.inverted()
        self.bool_obj.display_type = 'WIRE'

    # --- Controler -- #

    def modal(self, context, event):

        # --- Systems --- #
        self.master.receive_event(event)
        self.base_controls.update(context, event)
        mouse_warp(context, event)
        self.accumulation += self.base_controls.mouse

        # --- Controls ---#
        if self.base_controls.pass_through:
            return {'PASS_THROUGH'}

        elif self.base_controls.cancel:
            self.cancelled(context)
            return {'CANCELLED'}

        elif self.base_controls.confirm:
            if self.state == State.EXTRUDE:
                self.confirmed(context)
                return {'FINISHED'}
            else:
                self.state = State.EXTRUDE

        elif self.base_controls.scroll and not event.shift:
            self.cycle_state(forward=bool(self.base_controls.scroll))

        # Popover
        ret = self.popover(context)
        if ret == True: return {'FINISHED'}

        # Cycle
        if event.type == 'X' and event.value == 'PRESS':
            self.cycle_state(forward=event.shift)

        # Toggle Bool
        elif event.type == 'S' and event.value == 'PRESS':
            self.use_as_boolean = not self.use_as_boolean

            if self.use_as_boolean:
                self.boolean_mod.show_viewport = True
                self.boolean_mod.object = self.bool_obj
                self.bool_obj.display_type = 'WIRE'
            else:
                self.boolean_mod.show_viewport = False
                self.boolean_mod.object = None
                self.bool_obj.display_type = 'SOLID'

        # Apply mods on exit / Boolean Sovler
        elif event.type == 'A' and event.value == 'PRESS':
            if event.shift:
                self.apply_mods = not self.apply_mods
            else:
                if self.boolean_mod.operation == 'DIFFERENCE':
                    self.boolean_mod.operation = 'UNION'
                elif self.boolean_mod.operation == 'UNION':
                    self.boolean_mod.operation = 'DIFFERENCE'
                bpy.ops.hops.display_notification(info=f"Boolean Operation : {self.boolean_mod.operation}")

        # Flip
        elif event.type == 'F' and event.value == 'PRESS':
            if self.state == State.EXTRUDE:
                self.solidify_mod.offset = self.solidify_mod.offset * -1
                
        # Toggle X-Ray
        elif event.type == 'Z' and event.value == 'PRESS':
            bpy.context.space_data.shading.show_xray = not bpy.context.space_data.shading.show_xray
                
        # Solver
        elif event.type == 'E' and event.value == 'PRESS':
            if hasattr(self.boolean_mod, 'solver'):
                if self.boolean_mod.solver == 'EXACT':
                    self.boolean_mod.solver = 'FAST'
                elif self.boolean_mod.solver == 'FAST':
                    self.boolean_mod.solver = 'EXACT'
                bpy.ops.hops.display_notification(info=f"Boolean Solver : {self.boolean_mod.solver}")

        # Move mod
        elif self.base_controls.scroll and event.shift:
            if self.obj and self.boolean_mod:
                    active = context.active_object
                    context.view_layer.objects.active = self.obj
                    if self.base_controls.scroll > 0:
                        bpy.ops.object.modifier_move_up(modifier=self.boolean_mod.name)
                    else:
                        bpy.ops.object.modifier_move_down(modifier=self.boolean_mod.name)
                    context.view_layer.objects.active = active

        # Solidify Offsets
        if self.state == State.EXTRUDE:
            if event.type == 'ONE' and event.value == 'PRESS':
                self.solidify_mod.offset = -.95

            elif event.type == 'TWO' and event.value == 'PRESS':
                self.solidify_mod.offset = 0

            elif event.type == 'THREE' and event.value == 'PRESS':
                self.solidify_mod.offset = .95

            elif event.type == 'FOUR' and event.value == 'PRESS':
                if (2, 82, 4) < bpy.app.version:
                    if self.solidify_mod.solidify_mode == 'EXTRUDE':
                        self.solidify_mod.solidify_mode = 'NON_MANIFOLD'
                    elif self.solidify_mod.solidify_mode == 'NON_MANIFOLD':
                        self.solidify_mod.solidify_mode = 'EXTRUDE'

        # --- Update --- #
        if event.type != 'TIMER':
            self.update_mesh(event)
            self.interface(context)

        context.area.tag_redraw()
        return {"RUNNING_MODAL"}


    def update_mesh(self, event):

        if self.state == State.INSET:
            bmesh.ops.delete(self.bm, geom=self.bm.verts, context='VERTS')
            self.bm.from_mesh(self.bool_mesh_backup)
            self.set_mod_visibility(on=False)
            self.inset_value = self.accumulation
            self.inset()

        elif self.state == State.EXTRUDE:
            self.set_mod_visibility(on=True)
            self.extrude_value = self.accumulation
            self.extrude(event)

        bmesh.update_edit_mesh(self.bool_obj.data)


    def inset(self):
        result = bmesh.ops.inset_region(
            self.bm,
            faces=self.bm.faces,
            use_boundary=True,
            use_even_offset=True,
            use_interpolate=True,
            use_relative_offset=False,
            use_edge_rail=True,
            thickness=self.inset_value,
            depth=0,
            use_outset=False)
        bmesh.ops.delete(self.bm, geom=result['faces'], context='FACES')


    def extrude(self, event):
        if event.alt:
            self.solidify_mod.offset += self.base_controls.mouse
            if self.solidify_mod.offset > 1: self.solidify_mod.offset = 1
            elif self.solidify_mod.offset < -1: self.solidify_mod.offset = -1
        else:
            self.solidify_mod.thickness = self.extrude_value


    def interface(self, context):
        self.master.setup()
        if not self.master.should_build_fast_ui(): return
    
        win_list = []
        if self.state == State.INSET:
            win_list.append("Mode: Inset")
            win_list.append(f"{self.inset_value:.3f}")
            
        elif self.state == State.EXTRUDE:
            win_list.append("Mode: Extrude")
            win_list.append(f"{self.extrude_value:.3f}")

        win_list.append(f"Apply: {self.apply_mods}")
        win_list.append(f"Boolean: {self.use_as_boolean}")

        help_items = {"GLOBAL" : [], "STANDARD" : []}
        help_items["GLOBAL"] = [
            ("M", "Toggle mods list"),
            ("H", "Toggle help"),
            ("~", "Toggle UI Display Type"),
            ("O", "Toggle viewport rendering"),
            ("Z", "Toggle Wireframe / Solid")]

        help_items["STANDARD"] = [
            ("ALT"         , "Solidify Offset"),
            ("F"           , "Flip Offset"),
            ("Z"           , "X-Ray View"),
            ("1"           , "Offset to : -1"),
            ("2"           , "Offset to : 0"),
            ("3"           , "Offset to : 1"),
            ("4"           , f"Solidify Mode : {self.solidify_mod.solidify_mode}"),
            ("Shift A"     , "Apply modifiers"),
            ("A"           , 'Use : DIFFERENCE' if self.boolean_mod.operation == 'UNION' else 'Use : UNION'),
            ("S"           , "Toggle use as bool"),
            ("X"           , "Cycle Operation"),
            ("Scroll"      , "Cycle Operation"),
            ("Shift Scroll", "Move Modifier"),
            ("TAB"         , "Select Menu")]

        if hasattr(self.boolean_mod, 'solver'):
            help_items["STANDARD"].append(("E", f"Solver {self.boolean_mod.solver}"))
            
        active_mod = self.boolean_mod.name if self.boolean_mod else ""
        self.master.receive_fast_ui(win_list=win_list, help_list=help_items, image="Booleans", mods_list=get_mods_list(mods=self.obj.modifiers), active_mod_name=active_mod)
        self.master.finished()


    def popover(self, context):
        if self.__class__.selected_operation != "":
            if self.__class__.selected_operation == "INSET":
                self.state = State.INSET
                bpy.ops.hops.display_notification(info=f'State Set To : {self.__class__.selected_operation}')
            elif self.__class__.selected_operation == "EXTRUDE":
                self.state = State.EXTRUDE
                bpy.ops.hops.display_notification(info=f'State Set To : {self.__class__.selected_operation}')
            elif self.__class__.selected_operation == "APPLY":
                self.apply_mods = True
                bpy.ops.hops.display_notification(info="Modifiers will be applied on exit.")
            elif self.__class__.selected_operation == "CONFIRM":
                self.confirmed(context)
                return True
                
            self.__class__.selected_operation = ""

        # Spawns
        if self.base_controls.popover:
            context.window_manager.popover(popup_draw)

        return False

    # --- Utils --- #

    def set_mod_visibility(self, on=True):
        self.solidify_mod.show_viewport = on
        self.boolean_mod.show_viewport = on


    def cycle_state(self, forward=True):
        step = 1 if forward else -1
        types = State.states()
        index = types.index(self.state) + step
        self.state = types[index % len(types)]

    # --- Exit --- #

    def shut_down(self, context):
        self.__class__.operator = None
        self.__class__.selected_operation = ""
        self.override_obj_name = ""
        collapse_3D_view_panels(self.original_tool_shelf, self.original_n_panel)
        self.master.run_fade()
        self.remove_shaders()
        context.space_data.shading.show_xray = self.og_xray
        context.space_data.shading.type = self.og_shading
        bpy.data.meshes.remove(self.bool_mesh_backup)


    def cancelled(self, context):
        self.shut_down(context)
        bpy.ops.object.mode_set(mode='OBJECT')
        mesh = self.bool_obj.data
        bpy.data.objects.remove(self.bool_obj)
        bpy.data.meshes.remove(mesh)

        bpy.ops.object.select_all(action='DESELECT')
        self.obj.select_set(True)
        context.view_layer.objects.active = self.obj
        bpy.ops.object.mode_set(mode='EDIT')

        self.obj.modifiers.remove(self.boolean_mod)


    def confirmed(self, context):
        self.shut_down(context)
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        self.obj.hide_set(False)
        context.view_layer.objects.active = self.obj
        self.obj.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')

        # Fallback on errors
        if self.boolean_mod.object == None:
            self.obj.modifiers.remove(self.boolean_mod)
            # Unlink
            for coll in self.bool_obj.users_collection:
                coll.objects.unlink(self.bool_obj)
            # Link
            coll = None
            if self.obj.users_collection: coll = self.obj.users_collection[0]
            else: coll = context.collection
            coll.objects.link(self.bool_obj)
            # Apply
            if self.apply_mods:
                bpy.ops.object.mode_set(mode='OBJECT')
                context.view_layer.objects.active = self.bool_obj
                bpy.ops.object.modifier_apply(modifier=self.solidify_mod.name)
                context.view_layer.objects.active = self.obj
                bpy.ops.object.mode_set(mode='EDIT')

        # Show bool in edit mode
        else:
            if hasattr(self.boolean_mod, 'show_in_editmode'):
                self.boolean_mod.show_in_editmode = True
            # Apply
            if self.apply_mods:
                bpy.ops.object.mode_set(mode='OBJECT')
                context.view_layer.objects.active = self.bool_obj
                bpy.ops.object.modifier_apply(modifier=self.solidify_mod.name)
                context.view_layer.objects.active = self.obj
                bpy.ops.object.modifier_apply(modifier=self.boolean_mod.name)

                # Remove bool object
                mesh = self.bool_obj.data
                bpy.data.objects.remove(self.bool_obj)
                bpy.data.meshes.remove(mesh)
                self.bool_obj = None

                bpy.ops.object.mode_set(mode='EDIT')

        # Select bool object
        if not self.apply_mods:
            if self.bool_obj:
                bpy.ops.object.mode_set(mode='OBJECT')
                bpy.ops.object.select_all(action='DESELECT')
                context.view_layer.objects.active = self.bool_obj
                self.bool_obj.select_set(True)

        # Remove custom normals.
        if self.bool_obj:
            context.view_layer.objects.active = self.bool_obj
            bpy.ops.mesh.customdata_custom_splitnormals_clear()

    # --- Shaders --- #

    def remove_shaders(self):
        if self.draw_handle_2D:
            self.draw_handle_2D = bpy.types.SpaceView3D.draw_handler_remove(self.draw_handle_2D, "WINDOW")


    def safe_draw_2D(self, context):
        method_handler(draw_modal_frame, arguments=(context,), identifier='Modal Shader 2D', exit_method=self.remove_shaders)

# --- POPOVER --- #

def popup_draw(self, context):
    layout = self.layout

    op = HOPS_OT_Sel_To_Bool_V3.operator
    if not op: return {'CANCELLED'}

    layout.label(text='Selector')
    broadcaster = "hops.popover_data"

    row = layout.row()
    row.scale_y = 2
    props = row.operator(broadcaster, text='Inset')
    props.calling_ops = 'SELECT_TO_BOOLEAN'
    props.str_1 = 'INSET'
    
    row = layout.row()
    row.scale_y = 2
    props = row.operator(broadcaster, text='Extrude')
    props.calling_ops = 'SELECT_TO_BOOLEAN'
    props.str_1 = 'EXTRUDE'
    
    row = layout.row()
    row.scale_y = 2
    props = row.operator(broadcaster, text='Apply')
    props.calling_ops = 'SELECT_TO_BOOLEAN'
    props.str_1 = 'APPLY'
    
    if op.state == State.EXTRUDE:
        row = layout.row()
        row.scale_y = 2
        props = row.operator(broadcaster, text='Confirm')
        props.calling_ops = 'SELECT_TO_BOOLEAN'
        props.str_1 = 'CONFIRM'
    else:
        row = layout.row()
        row.scale_y = 2
        row.label(text="Extrude before continuing.")
