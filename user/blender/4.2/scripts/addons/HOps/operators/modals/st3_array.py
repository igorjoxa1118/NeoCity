import bpy, math, gpu
from math import cos, sin
from enum import Enum
from mathutils import Vector, Matrix
from gpu_extras.batch import batch_for_shader
from ... utility import addon
from ... utility.base_modal_controls import Base_Modal_Controls
from ... ui_framework.master import Master
from ... ui_framework import form_ui as form
from ... ui_framework.utils.mods_list import get_mods_list
from ... utils.toggle_view3d_panels import collapse_3D_view_panels
from ... utils.modal_frame_drawing import draw_modal_frame
from ... utils.cursor_warp import mouse_warp
from ... utils.space_3d import get_3D_point_from_mouse
from ... utils.gizmo_axial import Axial
from ... utils.mod_controller import Mod_Controller
from ... utility import method_handler
from ...utility.screen import dpi_factor


DESC = """Array V2

CTRL - New Array

Adds an array on the mesh.
Supports multiple modifiers.
V during modal for 2d / 3d mode.

Press H for help"""


class Widget:
    def __init__(self, event):
        # Dims
        self.x_offset = event.mouse_region_x
        self.y_offset = event.mouse_region_y
        self.loc = Vector((0,0))
        self.radius = 26 * dpi_factor()
        # Shader
        built_in_shader = 'UNIFORM_COLOR' if bpy.app.version[0] >=4 else '2D_UNIFORM_COLOR'
        self.shader = gpu.shader.from_builtin(built_in_shader)
        # Circle
        self.circle_setup(event)
        # State
        self.mouse_is_over = False


    def circle_setup(self, event):
        self.x_offset = event.mouse_region_x
        self.y_offset = event.mouse_region_y
        self.loc = Vector((self.x_offset, self.y_offset))
        self.circle_batch = None
        self.circle_color = (1,1,1,.06)
        self.circle_verts = []
        self.circle_indices = []
        segments = 32
        for i in range(segments):
            index = i + 1
            angle = i * 6.28318 / segments
            x = cos(angle) * self.radius
            y = sin(angle) * self.radius
            vert = Vector((x, y))
            vert += self.loc
            self.circle_verts.append(vert)
            if(index == segments): self.circle_indices.append((i, 0))
            else: self.circle_indices.append((i, i + 1))
        summed = Vector((0,0))
        for p in self.circle_verts:
            summed += p
        self.circle_center = summed / len(self.circle_verts)
        self.circle_batch = batch_for_shader(self.shader, 'LINES', {'pos': self.circle_verts}, indices=self.circle_indices)


    def update(self, context, event):
        # Circle
        mouse_pos = Vector((event.mouse_region_x, event.mouse_region_y))
        if (mouse_pos - self.circle_center).magnitude <= self.radius:
            self.mouse_is_over = True
            self.circle_color = (1,1,1,.08)
        else:
            self.mouse_is_over = False
            self.circle_color = (1,1,1,.06)


    def draw(self):
        # GL Settings
        #Enable(GL_LINE_SMOOTH)
        gpu.state.blend_set('ALPHA')
        gpu.state.line_width_set(3)
        # Circle
        self.shader.bind()
        self.shader.uniform_float('color', self.circle_color)
        self.circle_batch.draw(self.shader)
        # GL Settings
        #Disable(GL_LINE_SMOOTH)
        gpu.state.blend_set('NONE')


class Axis(Enum):
    X = 0
    Y = 1
    Z = 2


class Edit_Space(Enum):
    View_2D = 1
    View_3D = 2

# set controller index and notification
def mod_name_update(self, context):
    op = HOPS_OT_ST3_Array.operator
    if not op: return

    valid = op.mod_controller.set_active_obj_mod_index(op.mod_selected)
    if valid:
        bpy.ops.hops.display_notification(info=f'Target Array : {op.mod_selected}')
        op.set_initial_axis()

class HOPS_OT_ST3_Array(bpy.types.Operator):
    bl_idname = "hops.st3_array"
    bl_label = "Adjust Array V2"
    bl_description = DESC
    bl_options = {"REGISTER", "UNDO", "BLOCKING"}

    exit_with_empty_driver: bpy.props.BoolProperty("Exit with empty", name='Driver', description='Crate empty with a driver')

    # Popover
    operator = None
    mod_selected: bpy.props.StringProperty(update=mod_name_update)
    array_index: bpy.props.IntProperty(name='ArrayIndex')
    popover_active = False

    @classmethod
    def poll(cls, context):
        objs = context.selected_objects
        return any(type(o.data) in {bpy.types.Mesh, bpy.types.GreasePencil} for o in objs if hasattr(o, 'data'))


    def invoke(self, context, event):

        # UI Data
        self.drawing_radius = 0            # The radius for the circle gizmo
        self.show_guides = False           # Show graphical guides
        self.defualt_object_dims = (0,0,0) # The defualt objects dimensions before array modifiers
        self.circle_loc_3d = (0,0,0)       # The intersection poing of the mouse

        # Controler Vars
        self.intersection_point = Vector((0,0,0)) # Where the mouse is in 3D space : Used to draw the circle gizmo
        self.mouse_x_offset_2D = 0                # Tracked for 2D offseting
        self.mouse_accumulation = 0               # This is used as a sudo timer for 2D offset snaps
        self.axis = Axis.X                        # The current axis to offset with
        self.edit_space = Edit_Space.View_2D      # The offset space
        self.freeze_controls = False              # Used to freeze the mouse
        self.use_snaps = False                    # Used to offset by object dimensions
        self.exit_with_empty_driver = False       # If an empty should be calculated for the arrays (Drivers)
        self.exit_with_empty_obj = False

        # Setup
        types = {bpy.types.Mesh, bpy.types.GreasePencil}
        objs = context.selected_objects
        objs = [o for o in objs if hasattr(o, 'data') and type(o.data) in types]
        type_map = {bpy.types.Mesh : 'ARRAY', bpy.types.GreasePencil : 'GP_ARRAY'}
        self.mod_controller = Mod_Controller(context, objs, type_map, create_new=event.ctrl, active_obj=context.active_object)
        self.setup_objects(context)
        self.set_initial_axis(created_new=event.ctrl)

        # Offset Data
        self.sync_to_active = True
        self.sync_object = None
        self.offset_data = {} # KEY : obj, VAL : difference vector
        self.setup_offset_sync_data(context, objs)

        # OP Prefs settings
        if addon.preference().property.array_v2_use_2d == '3D':
            self.edit_space = Edit_Space.View_3D

        self.popup_style = addon.preference().property.in_tool_popup_style

        # Widgets : Deadzone
        self.widget = Widget(event)
        self.deadzone_previous = False
        self.deadzone_active = True

        # Widgets : Axial
        self.axial = Axial()

        # Widget : Form
        self.__x_offset = 0
        self.__y_offset = 0
        self.__z_offset = 0
        self.__count = 0
        self.index_button = None
        self.form_exit = False
        self.form = None
        self.setup_form(context, event)

        # Base Systems
        self.master = Master(context=context)
        self.master.only_use_fast_ui = True
        self.base_controls = Base_Modal_Controls(context, event, popover_keys=['SPACE'])
        self.original_tool_shelf, self.original_n_panel = collapse_3D_view_panels()
        self.draw_handle_2D = bpy.types.SpaceView3D.draw_handler_add(self.safe_draw_2D, (context,), 'WINDOW', 'POST_PIXEL')
        self.draw_handle_3D = bpy.types.SpaceView3D.draw_handler_add(self.safe_draw_3D, (context,), 'WINDOW', 'POST_VIEW')

        # Popover
        self.__class__.operator = self
        self.__class__.mod_selected = ""

        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    @property
    def x_offset(self):
        return round(self.__x_offset, 3)

    @x_offset.setter
    def x_offset(self, val):
        self.set_offset(index=0, val=val)
        self.__x_offset = val

    @property
    def y_offset(self):
        return round(self.__y_offset, 3)

    @y_offset.setter
    def y_offset(self, val):
        self.set_offset(index=1, val=val)
        self.__y_offset = val

    @property
    def z_offset(self):
        return round(self.__z_offset, 3)

    @z_offset.setter
    def z_offset(self, val):
        self.set_offset(index=2, val=val)
        self.__z_offset = val

    @property
    def count(self):
        return self.__count

    @count.setter
    def count(self, val):
        self.set_array_count(val)
        self.__count = val


    def modal(self, context, event):

        # --- Base Systems --- #
        self.master.receive_event(event=event)
        self.base_controls.update(context, event)
        self.widget_update(context, event)

        if self.edit_space == Edit_Space.View_2D and not self.__class__.popover_active:
            mouse_warp(context, event)

        self.props_update()

        self.mouse_x_offset_2D = self.base_controls.mouse
        if self.popup_style == 'DEFAULT':
            self.form.update(context, event)

        if not self.form.active():
            self.axial.update(context, event, self.axial_callback)

        # Popover
        self.popover(context)

        if self.__class__.popover_active:
            self.interface(context)
            context.area.tag_redraw()
            return {'RUNNING_MODAL'}

        # --- Base Controls --- #
        if self.base_controls.pass_through:
            if not self.form.active():
                return {'PASS_THROUGH'}

        elif self.base_controls.cancel:
            return self.cancel_exit(context)

        elif self.base_controls.confirm:
            if not self.form.active():
                return self.confirm_exit(context)

        elif self.form_exit:
            return self.confirm_exit(context)

        # Close help when menu opens / Freeze modal if menu opens
        if self.form.db.menu_just_opened or self.form.db.dot_dragging:
            self.master.collapse_fast_help()
            self.freeze_controls = True

        # Switch to 2D adjust if menu is open
        if self.form.db.menu_just_opened:
            self.edit_space = Edit_Space.View_2D

        if not self.form.active():
            return self.actions(context, event)

        self.interface(context=context)
        context.area.tag_redraw()
        return {"RUNNING_MODAL"}


    def actions(self, context, event):

        # Toggle 2D / 3D manipulation
        if event.type == 'V' and event.value == "PRESS":
            self.widget.mouse_is_over = False
            self.deadzone_previous = False
            self.deadzone_active = True
            self.widget.circle_setup(event)

            if self.edit_space == Edit_Space.View_2D:
                self.edit_space = Edit_Space.View_3D
            elif self.edit_space == Edit_Space.View_3D:
                self.edit_space = Edit_Space.View_2D

        # Cycle the current array : W
        elif event.type == 'W' and event.value == "PRESS":
            self.goto_next_array()

        # Drop arrays with empty
        elif event.type == 'E' and event.value == "PRESS":
            if event.shift:
                self.exit_with_empty_driver = False
                self.exit_with_empty_target_toggle()
            else:
                self.exit_with_empty_obj = False
                self.exit_with_empty_driver_toggle()

        # Toggle perspective
        elif event.type == 'P' or event.type == 'NUMPAD_5':
            if event.value == 'PRESS':
                bpy.ops.view3d.view_persportho()

        # Toggle freeze controls
        elif event.type in {'F', 'TAB'} and event.value == "PRESS":
            self.freeze_controls = not self.freeze_controls

            if self.freeze_controls:
                self.form.open_dot()

                if self.popup_style == 'BLENDER':
                    bpy.ops.hops.st3_array_popup('INVOKE_DEFAULT')
                    self.__class__.popover_active = True
            else:
                self.form.close_dot()

        # Toggle graphics guides
        elif event.type == 'G' and event.value == "PRESS":
            self.show_guides = not self.show_guides

        # Toggle Axis : If CTRL -> Clear the axis
        elif event.type == 'X' and event.value == "PRESS":
            if event.ctrl == True:
                self.toggle_axis(clear_axis_on_change=False)
                if addon.preference().ui.Hops_extra_info:
                    bpy.ops.hops.display_notification(info=f"Axis Switched To: {self.axis.name}")
            else:
                self.toggle_axis(clear_axis_on_change=True)
                if addon.preference().ui.Hops_extra_info:
                    bpy.ops.hops.display_notification(info=f"Axis Reset To: {self.axis.name}")

        # Toggle snap mode
        elif event.type == 'S' and event.value == "PRESS" and not event.shift:
            self.mouse_accumulation = 0
            self.use_snaps = not self.use_snaps

        # Toggle snap mode
        elif event.type == 'S' and event.value == "PRESS" and event.shift:
            if self.sync_object:
                self.sync_to_active = not self.sync_to_active
                bpy.ops.hops.display_notification(info=F"Sync to Active : {'ON' if self.sync_to_active else 'OFF'}")

        # Add Array
        elif event.type == 'A' and event.value == "PRESS" and event.alt == False:
            self.add_an_array()

        # Remove Array
        elif event.type == 'A' and event.value == "PRESS" and event.alt == True:
            self.remove_an_array()

        # Toggle Relative / Constant
        elif event.type == 'R' and event.value == "PRESS":
            self.toggle_relative_constant()

        # Set every thing to one
        elif event.type in {'ONE', 'NUMPAD_1'} and event.value == "PRESS":
            self.widget.mouse_is_over = False
            self.deadzone_previous = False
            self.deadzone_active = True
            self.widget.circle_setup(event)

            if event.shift == True:
                self.set_arrays_to_one(negative=True)
            else:
                self.set_arrays_to_one(negative=False)

            if addon.preference().ui.Hops_extra_info:
                if self.edit_space == Edit_Space.View_3D and not self.deadzone_active:
                    bpy.ops.hops.display_notification(info=f"Not Possible In 3D")
                else:
                    bpy.ops.hops.display_notification(info=f"Set to 1")

        # Set to 0
        elif event.type in {'ZERO', 'NUMPAD_0'} and event.value == "PRESS":
            self.widget.mouse_is_over = False
            self.deadzone_previous = False
            self.deadzone_active = True
            self.widget.circle_setup(event)
            self.set_arrays_to_zero()

        if self.base_controls.scroll:
            # Increment / Decrement / Axis change scrolling
            if not any((event.shift, event.ctrl, event.alt)):
                if self.freeze_controls == False:
                    self.increment_decrement_count(count=self.base_controls.scroll)

            # Ctrl Scrolling for axis change
            if event.alt:
                self.toggle_axis(clear_axis_on_change=True)
                self.set_arrays_to_one(negative=False)
                if addon.preference().ui.Hops_extra_info:
                    bpy.ops.hops.display_notification(info=f"Axis Reset To: {self.axis.name}")

            # Move mod up or down
            if event.shift == True:
                if self.base_controls.scroll > 0:
                    self.move_mod(context, up=True)
                if self.base_controls.scroll < 0:
                    self.move_mod(context, up=False)

            # Cycle the current array : Ctrl Scroll
            if event.ctrl == True:
                self.goto_next_array()

        # This is to smooth the mouse snapping motion
        if self.use_snaps:
            if self.edit_space == Edit_Space.View_2D:
                self.mouse_accumulation += self.base_controls.mouse

        # Navigation for frozen state
        if self.freeze_controls == True:
            if not event.ctrl and not event.shift:
                    if event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
                        return {'PASS_THROUGH'}

        # Adjust Displace
        if self.deadzone_active == False and self.freeze_controls == False:
            # 2D
            if self.edit_space == Edit_Space.View_2D:
                if event.type == "MOUSEMOVE":
                    if event.ctrl == True:
                        self.adjust_2D(accelerated=True)
                    else:
                        self.adjust_2D(accelerated=False)
            # 3D
            elif self.edit_space == Edit_Space.View_3D:
                self.adjust_3D(context=context, event=event)

        self.interface(context=context)
        context.area.tag_redraw()
        return {"RUNNING_MODAL"}


    def props_update(self):
        self.index_button.text = str(self.mod_controller.active_obj_mod_index() + 1)
        mod = self.mod_controller.active_object_mod()

        constant_offset = mod_constant_offset_object(mod)
        relative_offset = mod_relative_offset_object(mod)

        offset = (0,0,0)
        if mod.use_constant_offset: offset = constant_offset
        else: offset = relative_offset

        self.__x_offset = offset[0]
        self.__y_offset = offset[1]
        self.__z_offset = offset[2]
        self.__count = mod.count


    def interface(self, context):

        obj_data = self.mod_controller.active_object_mod(as_obj_data=True)
        obj = obj_data.obj
        mod = obj_data.active_mod()
        offset_type = "Relative"
        if mod.use_constant_offset:
            offset_type = "Constant"
        array_count = mod.count

        constant_offset = mod_constant_offset_object(mod)
        relative_offset = mod_relative_offset_object(mod)

        offset = (0,0,0)
        if mod.use_constant_offset: offset = constant_offset
        else: offset = relative_offset

        self.master.setup()
        if not self.master.should_build_fast_ui(): return

        win_list = []
        mods_list = []

        # Main
        if addon.preference().ui.Hops_modal_fast_ui_loc_options != 1: # Micro UI
            win_list.append(str(int(array_count)))
            if self.axis.name == 'X':
                win_list.append("X : {:.3f}".format(offset[0]))
            elif self.axis.name == 'Y':
                win_list.append("Y : {:.3f}".format(offset[1]))
            elif self.axis.name == 'Z':
                win_list.append("Z : {:.3f}".format(offset[2]))
            win_list.append(self.edit_space.name[-2:])
            if offset_type == "Relative":
                win_list.append("R")
            elif offset_type == "Constant":
                win_list.append("C")
            if self.freeze_controls:
                win_list.append("[F] Unpause")

        else:
            win_list.append(str(int(array_count)))
            win_list.append(self.axis.name)
            win_list.append("  X: {:.3f}  Y: {:.3f}  Z: {:.3f} ".format(offset[0], offset[1], offset[2]))
            win_list.append(self.edit_space.name[-2:])
            win_list.append(offset_type)
            if self.freeze_controls:
                win_list.append("[F] Unpause")
            else:
                win_list.append("[F] Pause / DotUI")

        # Help
        help_items = {"GLOBAL" : [], "STANDARD" : []}

        help_items["GLOBAL"] = [
            ("M", "Toggle mods list"),
            ("H", "Toggle help"),
            ("~", "Toggle UI Display Type"),
            ("O", "Toggle viewport rendering")
        ]

        help_items["STANDARD"] = [
            ("Scroll",         "Adjust segments."),
            ("Shift + S",      "Sync To Active"),
            ("S",              "Toggle Snap Mode"),
            ("P / 5",          "Toggle Perspective"),
            ("W",              "Goto Next Array"),
            ("Ctrl + Scroll",  "Goto Next Array"),
            ("Shift + Scroll", "Move Modifier Up / Down"),
            ("Alt + Scroll",   "Axial scroll"),
            ("R",              "Toggle Relative / Constant"),
            ("1 / Shift",      "Set to 1 or -1 on current Axis"),
            ("0",              "Set to 0 on current Axis"),
            ("G",              "Toggle Graphics"),
            ("Alt + A",        "Remove Active Array"),
            ("A",              f"Add New Array"),
            ("Ctrl + X",       "Toggle Axis"),
            ("X",              "Toggle Axis & Clear Current"),
            ("V",              f"Toggle {(str(self.edit_space)[-2:])} Mode"),
            ("E",              "Exiting with empty as driver" if self.exit_with_empty_driver else "Set exit with empty as driver"),
            ("Shift E",        "Exiting with empty as target" if self.exit_with_empty_obj else "Set exit with empty as target"),
            ("C" if context.preferences.inputs.use_mouse_emulate_3_button else "Alt", "Open Axial Change"),
            ("F / TAB",        "Unpause / Freeze Rotation" if self.freeze_controls else "Pause (DotUI) / Free Rotation")
        ]

        if 'SPACE' in self.base_controls.popover_keys:
            help_items["STANDARD"].append(('Space', 'Open Select Menu'))

        # Mods
        mods_list = get_mods_list(mods=obj.modifiers)

        self.master.receive_fast_ui(win_list=win_list, help_list=help_items, image="Array", mods_list=mods_list, active_mod_name=mod.name)
        self.master.finished()

    # --- FORM FUNCS --- #

    def setup_form(self, context, event):
        self.form = form.Form(context, event, dot_open=False)

        self.form.dot_calls(
            LR_callback=self.dot_adjust_count,
            LR_args=(True,),
            UD_callback=self.dot_adjust_count,
            UD_args=(False,),
            tips=["Click : Open / Close Controls", "Drag Left / Right: Add to Count", "Drag Up / Down : Subtract from Count"])

        row = self.form.row()
        row.add_element(form.Label(text="Array V2", width=60))

        tip = ["Scroll / Click", "Active Array to effect."]
        self.index_button = form.Button(text="0", width=20, callback=self.mod_index_move, pos_args=(True,), neg_args=(False,), tips=tip)
        row.add_element(self.index_button)
        row.add_element(form.Spacer(width=5))

        row.add_element(form.Button(text="P", width=20, tips=["Toggle Pause Mode"], callback=self.toggle_pause))
        row.add_element(form.Button(text="X", width=20, tips=["Finalize and Exit"], callback=self.exit_button))
        self.form.row_insert(row)

        row = self.form.row()
        row.add_element(form.Spacer(height=10))
        self.form.row_insert(row)

        tips = ["Click - Set array to 1", "Shift Click - Add 1 to array", "Alt Click - Set array to one and others to 0"]

        row = self.form.row()
        row.add_element(form.Label(text="X", width=30))
        row.add_element(form.Input(obj=self, attr="x_offset", width=75, increment=.1))
        row.add_element(form.Button(text="1", width=20, tips=tips, callback=self.set_to_one, pos_args=(False, 'X'), neg_args=(True, 'X'), alt_callback=self.set_others_to_one, alt_args=('X',)))
        self.form.row_insert(row)

        row = self.form.row()
        row.add_element(form.Label(text="Y", width=30))
        row.add_element(form.Input(obj=self, attr="y_offset", width=75, increment=.1))
        row.add_element(form.Button(text="1", width=20, tips=tips, callback=self.set_to_one, pos_args=(False, 'Y'), neg_args=(True, 'Y'), alt_callback=self.set_others_to_one, alt_args=('Y',)))
        self.form.row_insert(row)

        row = self.form.row()
        row.add_element(form.Label(text="Z", width=30))
        row.add_element(form.Input(obj=self, attr="z_offset", width=75, increment=.1))
        row.add_element(form.Button(text="1", width=20, tips=tips, callback=self.set_to_one, pos_args=(False, 'Z'), neg_args=(True, 'Z'), alt_callback=self.set_others_to_one, alt_args=('Z',)))
        self.form.row_insert(row)

        row = self.form.row()
        row.add_element(form.Spacer(width=125, height=15, draw_bar=True))
        self.form.row_insert(row)

        row = self.form.row()
        row.add_element(form.Dropdown(width=35, options=['X', 'Y', 'Z'], tips=["Active Axis"], callback=self.set_axis, update_hook=self.get_axis_hook))
        row.add_element(form.Input(obj=self, attr="count", tips=["Array Count"], width=35, increment=1))
        row.add_element(form.Button(text="F", width=20, tips=["Flip the current Array"], callback=self.flip_array))
        row.add_element(form.Button(text="+", shift_text="-", width=20, font_size=14, tips=["Click - Add array", "Shift Click - Remove array"], callback=self.add_remove_array, pos_args=(False,), neg_args=(True,)))
        self.form.row_insert(row)

        row = self.form.row()
        row.add_element(form.Button(text="E", width=20, tips=["Exit with Empty"], callback=self.exit_with_empty_driver_toggle))
        row.add_element(form.Button(text="M", width=20, scroll_enabled=True, tips=["Click - Move mod up", "Shift Click - Move mod down"], callback=self.move_mod, pos_args=(context, True), neg_args=(context, False)))
        row.add_element(form.Dropdown(width=70, options=['Relative', 'Constant'], tips=["Offset type"], callback=self.set_relative_constant, update_hook=self.get_offset_hook))
        self.form.row_insert(row)

        self.form.build()


    def mod_index_move(self, forward=True):
        self.mod_controller.clamped_next_mod_index(forward)


    def toggle_pause(self):
        self.freeze_controls = not self.freeze_controls


    def set_relative_constant(self, option=''):
        for mod in self.mod_controller.active_modifiers():
            if option == 'Relative':
                mod.use_constant_offset = False
                mod.use_relative_offset = True
            elif option == 'Constant':
                mod.use_constant_offset = True
                mod.use_relative_offset = False


    def get_offset_hook(self):
        obj_data = self.mod_controller.active_object_mod(as_obj_data=True)
        if not obj_data: return 'Constant'
        mod = obj_data.active_mod()

        if mod.use_relative_offset: return 'Relative'
        elif mod.use_constant_offset: return 'Constant'
        else: return 'Constant'


    def set_offset(self, index=0, val=0):
        for mod in self.mod_controller.active_modifiers():
            constant_offset = mod_constant_offset_object(mod)
            relative_offset = mod_relative_offset_object(mod)

            if mod.use_constant_offset == True:
                constant_offset[index] = val
            else:
                relative_offset[index] = val


    def set_array_count(self, val=0):
        obj_datas = self.mod_controller.validated_obj_datas()
        for obj_data in obj_datas:
            mod = obj_data.active_mod()

            constant_offset = mod_constant_offset_object(mod)
            relative_offset = mod_relative_offset_object(mod)

            if self.edit_space == Edit_Space.View_3D and self.intersection_point:
                index = self.axis.value
                mod.count = int(val)

                if mod.use_constant_offset == True:
                    distance = self.intersection_point[index]
                    count = mod.count - 1
                    if count < 1: count = 1
                    vec = distance / count
                    constant_offset[index] = vec

                else:
                    dims = obj_data.dims
                    obj = obj_data.obj
                    offset = self.intersection_point[index] / (dims[index] * obj.scale[index]) if dims[index] > 0 else 1
                    offset /= mod.count - 1 if mod.count - 1 > 0 else 1
                    relative_offset[index] = offset

            else:
                mod.count = int(val)


    def set_axis(self, option=''):
        if option == 'X': self.axis = Axis.X
        elif option == 'Y': self.axis = Axis.Y
        elif option == 'Z': self.axis = Axis.Z


    def get_axis_hook(self):
        if self.axis == Axis.X: return 'X'
        if self.axis == Axis.Y: return 'Y'
        if self.axis == Axis.Z: return 'Z'


    def set_adjust_mode(self, option=''):
        if option == '2D': self.edit_space = Edit_Space.View_2D
        elif option == '3D': self.edit_space = Edit_Space.View_3D
        bpy.ops.hops.display_notification(info=f"Edit mode : {self.edit_space.name}")


    def get_adjust_hook(self):
        if self.edit_space == Edit_Space.View_2D: return '2D'
        if self.edit_space == Edit_Space.View_3D: return '3D'


    def exit_with_empty_driver_toggle(self):
        self.exit_with_empty_driver = not self.exit_with_empty_driver
        msg = "Exiting with empty (Driver)" if self.exit_with_empty_driver else "No empty will be added (Driver)"
        bpy.ops.hops.display_notification(info=msg)


    def exit_with_empty_target_toggle(self):
        self.exit_with_empty_obj = not self.exit_with_empty_obj
        msg = "Exiting with empty (Target)" if self.exit_with_empty_obj else "No empty will be added (Target)"
        bpy.ops.hops.display_notification(info=msg)


    def dot_adjust_count(self, positive=True):
        count = 1 if positive else -1
        for mod in self.mod_controller.active_modifiers():
            mod.count += count


    def set_others_to_one(self, preserve_axis='X'):
        index = ['X', 'Y', 'Z'].index(preserve_axis)
        for mod in self.mod_controller.active_modifiers():
            constant_offset = mod_constant_offset_object(mod)
            relative_offset = mod_relative_offset_object(mod)

            for i in range(3):
                if i == index: continue
                if mod.use_constant_offset == True:
                    constant_offset[i] = 0
                else:
                    relative_offset[i] = 0

        self.set_to_one(axis=preserve_axis)


    def set_to_one(self, shift=False, axis='X'):
        i = ['X', 'Y', 'Z'].index(axis)
        for obj_data in self.mod_controller.validated_obj_datas():
            mod = obj_data.active_mod()

            constant_offset = mod_constant_offset_object(mod)
            relative_offset = mod_relative_offset_object(mod)

            if mod.use_relative_offset:
                if shift:
                    relative_offset[i] += 1
                else:
                    relative_offset[i] = 1
            else:
                snap_factor = abs(obj_data.dims[i])
                if shift:
                    constant_offset[i] += snap_factor
                else:
                    constant_offset[i] = snap_factor


    def flip_array(self):
        for mod in self.mod_controller.active_modifiers():
            constant_offset = mod_constant_offset_object(mod)
            relative_offset = mod_relative_offset_object(mod)

            index = self.axis.value
            if mod.use_relative_offset:
                val = relative_offset[index]
                relative_offset[index] = val * -1
            else:
                val = constant_offset[index]
                constant_offset[index] = val * -1


    def add_remove_array(self, remove=False):
        if remove:
            self.remove_an_array()
        else:
            self.add_an_array()


    def exit_button(self):
        self.form_exit = True

    # --- ADJUST 2D --- #

    def adjust_2D(self, accelerated=True):

        speed_bonus = 10 if accelerated else 5

        for obj_data in self.mod_controller.validated_obj_datas():
            mod = obj_data.active_mod()

            self.end_object_offset(mod)

            if mod.use_constant_offset == True:
                self.adjust_constant_arrays_2D(obj_data, mod, speed_bonus)
            else:
                self.adjust_relative_arrays_2D(obj_data, mod, speed_bonus)

        # Reset the mouse accumulation for snaps
        if abs(self.mouse_accumulation) > .25:
            self.mouse_accumulation = 0


    def adjust_constant_arrays_2D(self, obj_data, mod, speed_bonus=0):
        '''Adjust arrays based on 2D screen coordinates.'''

        constant_offset = mod_constant_offset_object(mod)

        offset = self.mouse_x_offset_2D * speed_bonus
        index = self.axis.value
        if self.use_snaps:
            # Limit this operation
            if abs(self.mouse_accumulation) > .25:
                # 1/2 of the mesh dims
                snap_factor = abs(obj_data.dims[index] * .5)
                # Reverse the offset direction
                if self.mouse_x_offset_2D > 0:
                    snap_factor = -snap_factor
                # Clamp the offset to a snapped value
                vec = constant_offset[index]
                remainder = abs(vec) % abs(snap_factor) if abs(snap_factor) > 0 else 0
                if (vec + remainder) % abs(snap_factor) == 0:
                    constant_offset[index] += remainder
                else:
                    constant_offset[index] -= remainder
                # Assign the snap factor
                constant_offset[index] += snap_factor
        else:
            constant_offset[index] -= offset


    def adjust_relative_arrays_2D(self, obj_data, mod, speed_bonus=0):
        '''Adjust arrays based on 2D screen coordinates.'''

        relative_offset = mod_relative_offset_object(mod)

        offset = self.mouse_x_offset_2D * speed_bonus
        offset *= .25
        index = self.axis.value
        if self.use_snaps:
            # Limit this operation
            if abs(self.mouse_accumulation) > .25:
                if abs(relative_offset[index]) % .25 != 0:
                        relative_offset[index] = round_quarter(relative_offset[index])
                snap_factor = .25 if self.mouse_x_offset_2D > 0 else -.25
                relative_offset[index] -= snap_factor
        else:
            relative_offset[index] -= offset

    # --- ADJUST 3D --- #

    def adjust_3D(self, context, event):
        '''Adjust the arrays 3D.'''

        for obj_data in self.mod_controller.validated_obj_datas():

            # Data
            obj = obj_data.obj
            mod = obj_data.active_mod()
            dims = obj_data.dims
            index = self.axis.value

            self.end_object_offset(mod)

            # Intersection
            normal = Vector((0,1,0)) if index == 2 else Vector((0,0,1))
            normal = normal @ obj.matrix_world.inverted()
            if context.region_data.is_orthographic_side_view:
                view_quat = context.region_data.view_rotation
                up = Vector((0,0,1))
                normal = view_quat @ up

            mouse_pos = Vector((event.mouse_region_x, event.mouse_region_y))

            point = obj.matrix_world.to_translation()

            # Sync
            if self.sync_to_active and self.sync_object:
                point = self.sync_object.matrix_world.to_translation()

            self.intersection_point = get_3D_point_from_mouse(mouse_pos, context, point, normal)
            self.circle_loc_3d = self.intersection_point
            self.intersection_point = obj.matrix_world.inverted() @ self.intersection_point

            intersection = self.intersection_point.copy()

            # Sync
            if self.sync_to_active and self.sync_object:
                if obj in self.offset_data:
                    # offset = Matrix.Diagonal(obj.scale).inverted() @ self.offset_data[obj]
                    intersection += self.offset_data[obj]

            # Adjust Arrays
            if mod.use_constant_offset == True:
                # intersection = Vector([intersection[i] * obj.matrix_world.to_scale()[i] for i in range(3)])
                self.adjust_constant_arrays_3D(intersection, index, mod, obj, dims)
            else:
                intersection = Vector([intersection[i] * obj.matrix_world.to_scale()[i] for i in range(3)])
                self.adjust_relative_arrays_3D(intersection, index, mod, obj, dims)

            # Put the intersection point back for drawing
            self.intersection_point = obj.matrix_local @ self.intersection_point


    def adjust_constant_arrays_3D(self, intersection, index, mod, obj, dims):
        '''Adjust constant arrays based on 3D mouse coordinates.'''

        distance = intersection[index]
        count = mod.count - 1
        if count < 1: count = 1
        vec = distance / count

        if self.use_snaps:
            x_dim = dims[index]
            vec -= vec % (x_dim * .25) if (x_dim * .25) > 0 else 1

        constant_offset = mod_constant_offset_object(mod)
        constant_offset[index] = vec


    def adjust_relative_arrays_3D(self, intersection, index, mod, obj, dims):
        '''Adjust relative arrays based on 3D mouse coordinates.'''

        relative_offset = mod_relative_offset_object(mod)

        offset = intersection[index] / (dims[index] * obj.scale[index]) if dims[index] > 0 else 1
        offset /= mod.count - 1 if mod.count - 1 > 0 else 1
        offset = round_quarter(offset) if self.use_snaps else offset
        relative_offset[index] = offset

    # --- WIDGETS --- #

    def widget_update(self, context, event):

        # Not active so discontinue
        if self.deadzone_active == False: return

        self.deadzone_previous = self.widget.mouse_is_over
        self.widget.update(context, event)
        if self.widget.mouse_is_over == False:
            if self.deadzone_previous == True:
                self.deadzone_active = False


    def axial_callback(self, val):

        self.clear_axis(axis=Axis.X)
        self.clear_axis(axis=Axis.Y)
        self.clear_axis(axis=Axis.Z)

        if val == 'X':
            self.axis = Axis.X
            self.set_arrays_to_one(negative=False)
        elif val == 'Y':
            self.axis = Axis.Y
            self.set_arrays_to_one(negative=False)
        elif val == 'Z':
            self.axis = Axis.Z
            self.set_arrays_to_one(negative=False)

        elif val == '-X':
            self.axis = Axis.X
            self.set_arrays_to_one(negative=True)
        elif val == '-Y':
            self.axis = Axis.Y
            self.set_arrays_to_one(negative=True)
        elif val == '-Z':
            self.axis = Axis.Z
            self.set_arrays_to_one(negative=True)

    # --- UTILS --- #

    def confirm_exit(self, context):
        self.__class__.operator = None
        if self.exit_with_empty_driver:
            self.array_to_empty_driver(context)
        elif self.exit_with_empty_obj:
            self.array_to_empty_target(context)
        self.store_axis_on_object()
        self.form.shut_down(context)
        self.remove_shaders()
        collapse_3D_view_panels(self.original_tool_shelf, self.original_n_panel)
        self.master.run_fade()
        self.mod_controller.confirm_exit()
        return {'FINISHED'}


    def cancel_exit(self, context):
        self.__class__.operator = None
        self.form.shut_down(context)
        self.remove_shaders()
        collapse_3D_view_panels(self.original_tool_shelf, self.original_n_panel)
        self.master.run_fade()
        self.mod_controller.cancel_exit()
        return {'CANCELLED'}


    def setup_objects(self, context):

        for obj_data in self.mod_controller.validated_obj_datas():

            # Drawing Radius / Default Dims
            if obj_data.obj == self.mod_controller.active_obj:
                dims = self.mod_controller.active_object_mod(as_obj_data=True).dims
                self.defualt_object_dims = dims
                self.drawing_radius = self.defualt_object_dims[0] * .5

            obj = obj_data.obj

            used_driver = False

            for mod_data in obj_data.mod_datas:
                mod = mod_data.mod

                constant_offset = mod_constant_offset_object(mod)
                relative_offset = mod_relative_offset_object(mod)

                if mod.show_viewport == False: continue

                # Set default offset for new
                if mod_data.was_created:
                    mod.use_relative_offset = False
                    mod.use_constant_offset = True
                    constant_offset[0] = obj_data.dims[0]

                else:
                    # BC Array Check
                    if mod.use_relative_offset and mod.use_constant_offset:
                        for i in range(3):
                            if abs(relative_offset[i]) == 1:
                                mod.use_relative_offset = False
                                neg = -1 if relative_offset[i] < 0 else 1
                                constant_offset[i] += neg * obj_data.dims[i]
                                obj.hops.last_array_axis = ['X', 'Y', 'Z'][i]
                                break

                    if mod.use_relative_offset:
                        mod.use_constant_offset = False

                    if mod.use_constant_offset:
                        mod.use_relative_offset = False

                    if not mod.use_constant_offset and not mod.use_relative_offset:
                        mod.use_constant_offset = True

                    # Fix for Radial Array
                    if mod.use_object_offset:
                        if mod.offset_object:
                            mod.use_constant_offset = False
                            mod.use_relative_offset = False
                        else:
                            mod.use_object_offset = False
                            mod.use_constant_offset = True
                            mod.use_relative_offset = False

                    # Remove old drivers
                    driver_1 = mod.driver_remove('count')
                    driver_2 = mod.driver_remove('constant_offset_displace')

                    if driver_1 or driver_2:
                        used_driver = True

            # Make sure new array uses proper settings based on last array
            if obj_data.active_mod_data().was_created and len(obj_data.mod_datas) > 1:
                prev_mod = obj_data.mod_datas[-2].mod
                cur_mod = obj_data.active_mod()

                # Make sure new array isnt using same axis as array before it
                axises = ['X', 'Y', 'Z']
                index, compare = 0, 0

                prev_relative_offset = mod_relative_offset_object(prev_mod)
                prev_constant_offset = mod_constant_offset_object(prev_mod)

                cur_relative_offset = mod_relative_offset_object(cur_mod)
                cur_constant_offset = mod_constant_offset_object(cur_mod)


                if prev_mod.use_relative_offset:
                    for i in range(3):
                        if abs(prev_relative_offset[i]) > compare:
                            index = i
                            compare = abs(prev_relative_offset[i])
                    axis = axises[(index + 1) % len(axises)]
                    cur_relative_offset[0] = 0
                    obj.hops.last_array_axis = axis

                elif prev_mod.use_constant_offset:
                    for i in range(3):
                        if abs(prev_constant_offset[i]) > compare:
                            index = i
                            compare = abs(prev_constant_offset[i])
                    axis = axises[(index + 1) % len(axises)]
                    cur_constant_offset[0] = 0
                    obj.hops.last_array_axis = axis

            # Remove old driver empty
            for child in obj.children:
                if child.name[:15] == "HOPSArrayTarget":
                    if used_driver:
                        self.exit_with_empty_driver = True
                        bpy.data.objects.remove(child)


    def setup_offset_sync_data(self, context, objs):
        '''Generate offsets needed to keep objects grouped during array.'''

        if context.active_object in objs:
            self.sync_object = context.active_object
        else: return

        if self.sync_object in objs:
            objs.remove(self.sync_object)

        for obj in objs:

            A_mat = self.sync_object.matrix_world.copy()
            A_loc = self.sync_object.matrix_world.translation
            A_sca = Matrix.Diagonal(A_mat.decompose()[2])
            A_mat.translation = Vector()

            B_mat = obj.matrix_world
            B_loc = B_mat.translation
            B_sca = Matrix.Diagonal(B_mat.decompose()[2]).inverted()

            sub = B_loc - A_loc
            offset = A_mat.inverted() @ sub

            self.offset_data[obj] = A_sca @ B_sca @ offset


    def set_initial_axis(self, created_new=False):
        obj_data = self.mod_controller.active_object_mod(as_obj_data=True)
        if obj_data == None: return

        # Check if the array should actually use another axis
        mod = obj_data.active_mod()

        if created_new:
            if len(obj_data.mod_datas) > 1:
                mod = obj_data.mod_datas[-2].mod

        index = 0
        offset = (0,0,0)

        constant_offset = mod_constant_offset_object(mod)
        relative_offset = mod_relative_offset_object(mod)

        if mod.use_constant_offset:
            offset = list(constant_offset)
        else:
            offset = list(relative_offset)

        offset = [abs(o) for o in offset]
        index = offset.index(max(offset))

        if created_new:
            created_mod = obj_data.mod_datas[-1].mod
            if index == 0:
                self.axis = Axis.Y
                created_mod.relative_offset_displace = [0.0, created_mod.relative_offset_displace[0], 0.0]
                created_mod.constant_offset_displace = [0.0, created_mod.constant_offset_displace[0], 0.0]
            elif index == 1:
                self.axis = Axis.Z
                created_mod.relative_offset_displace = [0.0, 0.0, created_mod.relative_offset_displace[1]]
                created_mod.constant_offset_displace = [0.0, 0.0, created_mod.constant_offset_displace[1]]
            elif index == 2:
                self.axis = Axis.X
                created_mod.relative_offset_displace = [created_mod.relative_offset_displace[2], 0.0, 0.0]
                created_mod.constant_offset_displace = [created_mod.constant_offset_displace[2], 0.0, 0.0]
            return

        if index == 0:
            self.axis = Axis.X
        elif index == 1:
            self.axis = Axis.Y
        elif index == 2:
            self.axis = Axis.Z


    def end_object_offset(self, mod):
        if mod.use_object_offset:
            if mod.use_relative_offset:
                mod.use_constant_offset = False
            elif mod.use_constant_offset:
                mod.use_relative_offset = False
            elif not mod.use_constant_offset and not mod.use_relative_offset:
                mod.use_constant_offset = True


    def store_axis_on_object(self):
        for obj_data in self.mod_controller.validated_obj_datas():
            obj = obj_data.obj
            if self.axis == Axis.X:
                obj.hops.last_array_axis = 'X'
            elif self.axis == Axis.Y:
                obj.hops.last_array_axis = 'Y'
            elif self.axis == Axis.Z:
                obj.hops.last_array_axis = 'Z'


    def toggle_relative_constant(self):
        # Determine what to set the other arrays to based on defualt obj
        use_relative = False
        mod = self.mod_controller.active_object_mod()
        if mod != None: use_relative = mod.use_relative_offset

        # Set to the inverse of what defualt was using
        for mod in self.mod_controller.active_modifiers():
            if use_relative:
                mod.use_constant_offset = True
                mod.use_relative_offset = False
            else:
                mod.use_constant_offset = False
                mod.use_relative_offset = True


    def clear_axis(self, axis=Axis.Y):
        for mod in self.mod_controller.active_modifiers():
            index = axis.value

            constant_offset = mod_constant_offset_object(mod)
            relative_offset = mod_relative_offset_object(mod)

            constant_offset[index] = 0
            relative_offset[index] = 0


    def increment_decrement_count(self, count=0):
        for mod in self.mod_controller.active_modifiers():
            if mod.count + count >= 1:
                mod.count += count


    def add_an_array(self):
        self.mod_controller.create_new_mod()
        for mod in self.mod_controller.active_modifiers():

            constant_offset = mod_constant_offset_object(mod)
            relative_offset = mod_relative_offset_object(mod)

            mod.use_relative_offset = False
            mod.use_constant_offset = True
            relative_offset[0] = 0
            constant_offset[0] = 0

        self.toggle_axis()

        # Set initial offset
        for obj_data in self.mod_controller.validated_obj_datas():
            mod = obj_data.active_mod()
            constant_offset = mod_constant_offset_object(mod)
            index = self.axis.value
            constant_offset[index] = obj_data.dims[index]

        if addon.preference().ui.Hops_extra_info:
            bpy.ops.hops.display_notification(info=f"Array Added")


    def remove_an_array(self):
        self.mod_controller.remove_active_mod(leave_one=True, use_logical_delete=True, remove_if_created=True)
        if addon.preference().ui.Hops_extra_info:
            bpy.ops.hops.display_notification(info=f"Array Removed")


    def toggle_axis(self, clear_axis_on_change=False):
        '''Toggle the current axis, also setting some other values.'''

        self.mouse_accumulation = 0

        if self.axis == Axis.X:
            self.axis = Axis.Y
            if clear_axis_on_change:
                self.clear_axis(axis=Axis.X)
        elif self.axis == Axis.Y:
            self.axis = Axis.Z
            if clear_axis_on_change:
                self.clear_axis(axis=Axis.Y)
        elif self.axis == Axis.Z:
            self.axis = Axis.X
            if clear_axis_on_change:
                self.clear_axis(axis=Axis.Z)


    def goto_next_array(self):
        self.mod_controller.cyclic_next_mod_index()
        self.set_initial_axis()


    def set_arrays_to_one(self, negative=False):
        for obj_data in self.mod_controller.validated_obj_datas():
            mod = obj_data.active_mod()
            dims = obj_data.dims
            i = self.axis.value

            constant_offset = mod_constant_offset_object(mod)
            relative_offset = mod_relative_offset_object(mod)

            if mod.use_relative_offset:
                relative_offset[i] = 1 if negative == False else -1
            else:
                snap_factor = abs(dims[i])
                constant_offset[i] = snap_factor if negative == False else -snap_factor


    def set_arrays_to_zero(self):
        for mod in self.mod_controller.active_modifiers():

            constant_offset = mod_constant_offset_object(mod)
            relative_offset = mod_relative_offset_object(mod)

            i = self.axis.value
            if mod.use_relative_offset: relative_offset[i] = 0
            else: constant_offset[i] = 0


    def move_mod(self, context, up=True):
        self.mod_controller.move_mod(context, up)


    def array_to_empty_driver(self, context):

        # Key = Obj : Val = Empties
        obj_empty_data = {}

        for obj_data in self.mod_controller.validated_obj_datas():
            obj = obj_data.obj
            dims = obj_data.dims

            if obj not in obj_empty_data:
                obj_empty_data[obj] = []

            for mod in obj_data.all_active_mods():

                constant_offset = mod_constant_offset_object(mod)
                relative_offset = mod_relative_offset_object(mod)

                constant_offset_string = 'constant_offset_displace' if mod.type == 'ARRAY' else 'constant_offset'

                # Create empty
                empty = bpy.data.objects.new("HOPSArrayTarget", None)
                context.collection.objects.link(empty)
                empty.empty_display_size = .5
                empty.empty_display_type = 'SPHERE'
                empty.parent = obj
                empty.rotation_euler.z = math.radians((mod.count * 10) - 15)

                obj_empty_data[obj].append(empty)

                # Empty constraint
                con = empty.constraints.new(type='LIMIT_ROTATION')
                con.use_limit_x = True
                con.use_limit_y = True
                con.use_limit_z = True
                con.max_z = math.radians(360)
                con.owner_space = 'LOCAL'

                # Constant
                if mod.use_constant_offset == True:
                    loc_x = constant_offset[0] * (mod.count - 1)
                    loc_y = constant_offset[1] * (mod.count - 1)
                    loc_z = constant_offset[2] * (mod.count - 1)

                    empty.location = (loc_x, loc_y, loc_z)

                # Relative
                else:
                    loc_x = dims[0] * obj.scale[0] * relative_offset[0] * (mod.count - 1)
                    loc_y = dims[1] * obj.scale[1] * relative_offset[1] * (mod.count - 1)
                    loc_z = dims[2] * obj.scale[2] * relative_offset[2] * (mod.count - 1)

                    empty.location = (loc_x, loc_y, loc_z)

                # Set constant
                mod.use_constant_offset = True
                mod.use_relative_offset = False

                # Count driver
                driver = mod.driver_add('count').driver

                empty_rot = driver.variables.new()
                empty_rot.name = 'empty_rot'
                empty_rot.type = 'TRANSFORMS'
                empty_rot.targets[0].id = empty
                empty_rot.targets[0].transform_type = 'ROT_Z'
                empty_rot.targets[0].transform_space = 'LOCAL_SPACE'

                driver.expression = "abs( (degrees(empty_rot) / 10) + 2 )"

                # Count Data Path
                count_data_path = f'modifiers["{mod.name}"].count' if mod.type == 'ARRAY' else f'grease_pencil_modifiers["{mod.name}"].count'

                # Driver X
                driver = mod.driver_add(constant_offset_string, 0).driver

                empty_x = driver.variables.new()
                empty_x.name = 'empty_x'
                empty_x.type = 'TRANSFORMS'
                empty_x.targets[0].id = empty
                empty_x.targets[0].transform_type = 'LOC_X'
                empty_x.targets[0].transform_space = 'LOCAL_SPACE'

                count = driver.variables.new()
                count.name = 'count'
                count.type = 'SINGLE_PROP'
                count.targets[0].id = obj
                count.targets[0].data_path = count_data_path

                driver.expression = "empty_x / (count - 1) if (count - 1) > 0 else 1"

                # Driver Y
                driver = mod.driver_add(constant_offset_string, 1).driver

                empty_y = driver.variables.new()
                empty_y.name = 'empty_y'
                empty_y.type = 'TRANSFORMS'
                empty_y.targets[0].id = empty
                empty_y.targets[0].transform_type = 'LOC_Y'
                empty_y.targets[0].transform_space = 'LOCAL_SPACE'

                count = driver.variables.new()
                count.name = 'count'
                count.type = 'SINGLE_PROP'
                count.targets[0].id = obj
                count.targets[0].data_path = count_data_path

                driver.expression = "empty_y / (count - 1) if (count - 1) > 0 else 1"

                # Driver Z
                driver = mod.driver_add(constant_offset_string, 2).driver

                empty_z = driver.variables.new()
                empty_z.name = 'empty_z'
                empty_z.type = 'TRANSFORMS'
                empty_z.targets[0].id = empty
                empty_z.targets[0].transform_type = 'LOC_Z'
                empty_z.targets[0].transform_space = 'LOCAL_SPACE'

                count = driver.variables.new()
                count.name = 'count'
                count.type = 'SINGLE_PROP'
                count.targets[0].id = obj
                count.targets[0].data_path = count_data_path

                driver.expression = "empty_z / (count - 1) if (count - 1) > 0 else 1"

    # TODO : Maybe get this working...  probably needs a different method
    def assign_main_empty(self, context, main_obj, obj_empty_data):

        # Location
        loc = Vector()
        summed = Vector()
        div = 0
        for key, val in obj_empty_data.items():
            for empty in val:
                summed += empty.location
                div += 1
        loc = summed / div if div > 0 else Vector()

        # Create empty
        controller_empty = bpy.data.objects.new("HOPSArrayController", None)
        context.collection.objects.link(controller_empty)
        controller_empty.empty_display_size = .5
        controller_empty.empty_display_type = 'SPHERE'
        controller_empty.parent = main_obj
        controller_empty.location = loc

        # Empty constraint
        con = controller_empty.constraints.new(type='LIMIT_ROTATION')
        con.use_limit_x = True
        con.use_limit_y = True
        con.use_limit_z = False
        con.owner_space = 'LOCAL'

        context.view_layer.update()

        # Add empty constraints
        for obj, empties in obj_empty_data.items():
            for empty in empties:

                con = empty.constraints.new(type='COPY_LOCATION')
                con.target = controller_empty
                con.use_x = True
                con.use_y = True
                con.use_z = True
                con.use_offset = True
                con.target_space = 'CUSTOM'
                con.space_object = obj
                con.owner_space = 'LOCAL'

                con = empty.constraints.new(type='COPY_ROTATION')
                con.target = controller_empty
                con.use_x = True
                con.use_y = True
                con.use_z = True
                con.mix_mode = 'AFTER'
                con.target_space = 'CUSTOM'
                con.space_object = obj
                con.owner_space = 'LOCAL'

                con = empty.constraints.new(type='TRANSFORM')
                con.target = controller_empty
                con.target_space = 'LOCAL'
                con.owner_space = 'WORLD'
                con.map_from = 'LOCATION'
                con.map_to = 'LOCATION'


                '''
                Controller empty location
                minus
                the offset from empty to controller empty
                '''

                space = main_obj.matrix_world.copy()
                ispace = space.inverted()

                controller_loc = ispace @ controller_empty.matrix_world.translation
                empty_loc = ispace @ empty.matrix_world.translation

                offset = (empty_loc - controller_loc) - controller_loc

                con.to_min_x = offset.x
                con.to_min_y = offset.y
                con.to_min_z = offset.z


    def array_to_empty_target(self, context):
        for obj_data in self.mod_controller.validated_obj_datas():
            obj = obj_data.obj
            dims = obj_data.dims

            for mod in obj_data.all_active_mods():

                constant_offset = mod_constant_offset_object(mod)
                relative_offset = mod_relative_offset_object(mod)

                # Create empty
                empty = bpy.data.objects.new("HOPSArrayTarget", None)
                context.collection.objects.link(empty)
                empty.empty_display_size = .5
                empty.empty_display_type = 'SPHERE'
                empty.parent = obj

                # Constant
                if mod.use_constant_offset == True:
                    loc_x = constant_offset[0]
                    loc_y = constant_offset[1]
                    loc_z = constant_offset[2]

                    empty.location = (loc_x, loc_y, loc_z)

                # Relative
                else:
                    loc_x = dims[0] * obj.scale[0] * relative_offset[0]
                    loc_y = dims[1] * obj.scale[1] * relative_offset[1]
                    loc_z = dims[2] * obj.scale[2] * relative_offset[2]

                    empty.location = (loc_x, loc_y, loc_z)

                # Zero out offset for GP array
                if mod.type == 'GP_ARRAY':
                    for i in range(3): constant_offset[i] = 0

                mod.use_constant_offset = False
                mod.use_relative_offset = False
                mod.use_object_offset = True
                mod.offset_object = empty


    def popover(self, context):

        # # Popup captured new mod
        # if self.__class__.mod_selected != "":
        #     valid = self.mod_controller.set_active_obj_mod_index(self.__class__.mod_selected)
        #     if valid:
        #         bpy.ops.hops.display_notification(info=f'Target Array : {self.__class__.mod_selected}')
        #         self.set_initial_axis()
        #     self.__class__.mod_selected = ""

        # Spawns
        if self.base_controls.popover:
            context.window_manager.popover(popup_draw)

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
        '''Draw shader handle.'''

        if self.popup_style == 'DEFAULT':
            self.form.draw()
        self.axial.draw()

        if self.edit_space == Edit_Space.View_2D:
            draw_modal_frame(context)

        if self.deadzone_active:
            self.widget.draw()


    def safe_draw_3D(self, context):
        method_handler(self.draw_shader_3D,
            arguments = (context,),
            identifier = 'Modal Shader 3D',
            exit_method = self.remove_shaders)


    def draw_shader_3D(self, context):
        if self.freeze_controls == True: return
        elif self.show_guides == False: return

        if self.edit_space == Edit_Space.View_3D:
            self.draw_circle_3D()
            self.draw_plane_3D()
        elif self.edit_space == Edit_Space.View_2D:
            self.draw_plane_3D()


    def draw_circle_3D(self):
        '''Draw the circle where the mouse is in 3D.'''

        radius = self.drawing_radius
        if addon.preference().property.array_type == "DOT":
            radius = .0125
            width = 12
        else:
            width = 3

        vertices = []
        indices = []
        segments = 64
        color = (0,0,0,1)
        obj = self.mod_controller.active_obj

        #Build ring
        for i in range(segments):
            index = i + 1
            angle = i * 3.14159 * 2 / segments

            x = cos(angle) * radius
            y = sin(angle) * radius
            z = 0
            vert = Vector((x, y, z))

            if self.axis == Axis.Z:
                plane_normal = Vector((0,1,0)) @ obj.matrix_world.inverted()
                up = Vector((0,0,1))
                angle = plane_normal.rotation_difference(up)
                rot_mat = angle.to_matrix()
                vert = vert @ rot_mat

            else:
                rot_mat = obj.matrix_world.to_quaternion()
                rot_mat = rot_mat.to_matrix()
                rot_mat = rot_mat.inverted()
                vert = vert @ rot_mat

            vert[0] = vert[0] + self.circle_loc_3d[0]
            vert[1] = vert[1] + self.circle_loc_3d[1]
            vert[2] = vert[2] + self.circle_loc_3d[2]

            vertices.append(vert)

            if index == segments: indices.append((i, 0))
            else: indices.append((i, i + 1))

        if self.axis == Axis.X:
            color = (1,0,0,1)
        elif self.axis == Axis.Y:
            color = (0,1,0,1)
        elif self.axis == Axis.Z:
            color = (0,1,1,1)

        built_in_shader = 'UNIFORM_COLOR' if bpy.app.version[0] >=4 else '3D_UNIFORM_COLOR'
        shader = gpu.shader.from_builtin(built_in_shader)
        batch = batch_for_shader(shader, 'LINES', {'pos': vertices}, indices=indices)
        shader.bind()
        shader.uniform_float('color', color)
        # Lines
        #Enable(GL_LINE_SMOOTH)
        gpu.state.blend_set('ALPHA')
        gpu.state.line_width_set(width)
        batch.draw(shader)
        del shader
        del batch


    def draw_plane_3D(self):
        '''Draw a 3D plane to represent the editing axis.'''

        vertices = []
        indices = []
        obj = self.mod_controller.active_obj
        mat = obj.matrix_world
        x_offset = 1
        y_offset = 1

        scale = obj.matrix_world.inverted()
        scale = scale.to_scale()

        if self.axis == Axis.X:
            x_offset = (obj.dimensions[0] + .25) * scale[0]
            y_offset = self.defualt_object_dims[0] * scale[0]
        elif self.axis == Axis.Y:
            x_offset = self.defualt_object_dims[0] * scale[0]
            y_offset = (obj.dimensions[1]  + .25) * scale[0]
        elif self.axis == Axis.Z:
            x_offset = self.defualt_object_dims[0] * scale[0]
            y_offset = (obj.dimensions[2] + .25) * scale[0]


        if self.axis == Axis.Z:
            mat_rot = Matrix.Rotation(math.radians(90.0), 4, 'X')
            mat = mat @ mat_rot

        # Bottom Left
        vert = Vector(( -x_offset, -y_offset, 0 ))
        vert = mat @ vert
        vertices.append(vert)

        # Top Left
        vert = Vector(( -x_offset, y_offset, 0 ))
        vert = mat @ vert
        vertices.append(vert)

        # Top Right
        vert = Vector(( x_offset, y_offset, 0 ))
        vert = mat @ vert
        vertices.append(vert)

        # Bottom Right
        vert = Vector(( x_offset, -y_offset, 0 ))
        vert = mat @ vert
        vertices.append(vert)

        indices.append((0, 1, 2 ))
        indices.append((0, 2, 3 ))

        color = (0,0,0,1)
        if self.axis == Axis.X:
            color = (1, 0, 0, .03125)
        elif self.axis == Axis.Y:
            color = (0, 1, 0, .03125)
        elif self.axis == Axis.Z:
            color = (0, 1, 1, .03125)

        built_in_shader = 'UNIFORM_COLOR' if bpy.app.version[0] >=4 else '3D_UNIFORM_COLOR'
        shader = gpu.shader.from_builtin(built_in_shader)
        batch = batch_for_shader(shader, 'TRIS', {'pos': vertices}, indices=indices)
        shader.bind()

        shader.uniform_float('color', color)

        #Enable(GL_LINE_SMOOTH)
        gpu.state.blend_set('ALPHA')
        gpu.state.depth_test_set('LESS')
        #glDepthFunc(GL_LESS)

        batch.draw(shader)
        gpu.state.depth_test_set('NONE')
        gpu.state.face_culling_set('NONE')
        gpu.state.depth_test_set('NONE')
        del shader
        del batch


def mod_constant_offset_object(mod):
    if mod.type == 'ARRAY':
        return mod.constant_offset_displace
    if mod.type == 'GP_ARRAY':
        return mod.constant_offset


def mod_relative_offset_object(mod):
    if mod.type == 'ARRAY':
        return mod.relative_offset_displace
    if mod.type == 'GP_ARRAY':
        return mod.relative_offset


def round_quarter(x):
    '''Rounds the decimal point to the nearest quarter (.0, .25, .5, .75)'''
    return round(x * 4) / 4.0

# --- POPOVER --- #

def popup_draw(self, context):
    layout = self.layout

    op = HOPS_OT_ST3_Array.operator
    if not op: return

    layout.label(text='Selector')

    mods = [m.name for m in op.mod_controller.active_obj_mods()]

    broadcaster = "hops.popover_data"

    for i, mod in enumerate(mods):
        row = layout.row()
        row.scale_y = 2
        props = row.operator(broadcaster, text=mod)
        props.calling_ops = 'ARRAY_V2'
        props.str_1 = mod


class HOPS_OT_ST3_Array_Popup(bpy.types.Operator):
    bl_idname = "hops.st3_array_popup"
    bl_label = "Adjust Array V2"

    def __del__(self):
        HOPS_OT_ST3_Array.popover_active = False

    def execute(self, context):
        preference = addon.preference().ui
        return bpy.context.window_manager.invoke_popup(self, width=int(150 * dpi_factor()))

    def draw(self, context):
        layout = self.layout

        op = HOPS_OT_ST3_Array.operator
        if not op: return

        mod = op.mod_controller.active_object_mod()

        if not mod: return

        layout.label(text='ARRAY V2')

        if mod.type == 'ARRAY':
            if mod.use_constant_offset:
                offset = 'constant_offset_displace'
            else:
                offset = 'relative_offset_displace'
        else:
            if mod.use_constant_offset:
                offset = 'constant_offset'
            else:
                offset = 'relativet_offset'

        row = layout.row()
        row.label(text='X')
        row.prop(mod, offset, index=0, text='')
        sone = row.row().operator('hops.st3_add_setone', text='', icon='THREE_DOTS')
        sone.axis ='X'

        row = layout.row()
        row.label(text='Y')
        row.prop(mod, offset, index=1, text='')
        sone = row.row().operator('hops.st3_add_setone', text='', icon='THREE_DOTS')
        sone.axis ='Y'

        row = layout.row()
        row.label(text='Z')
        row.prop(mod, offset, index=2, text='')
        sone = row.row().operator('hops.st3_add_setone', text='', icon='THREE_DOTS')
        sone.axis ='Z'

        func_row = layout.row(align=True)
        func_row.row().prop(mod, 'count', text='')

        offset = op.get_offset_hook()
        func_row.operator("hops.st3_array_offset", text='', icon='EVENT_R' if offset == 'Relative' else 'EVENT_C',)

        move_ops = func_row
        move = move_ops.operator("hops.st3_array_modmove", text='', icon='TRIA_UP')
        move.up = True
        move = move_ops.operator("hops.st3_array_modmove", text='', icon='TRIA_DOWN')
        move.up = False

        func_row.prop(op, 'exit_with_empty_driver', text='', icon='DRIVER')

        add_rem = func_row.row()
        add_rem.operator_context = 'INVOKE_DEFAULT'
        add_rem.operator("hops.st3_add_remove", text='', icon='ADD')

        layout.popover(HOPS_PT_ST3_array_switch.bl_idname, text=mod.name)

class HOPS_PT_ST3_array_switch(bpy.types.Panel):
    bl_idname = 'HOPS_PT_ST3_array_switch'
    bl_label = "Selector"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    def draw(self, context):
        popup_draw(self, context)

class HOPS_OT_ST3_Array_Offset(bpy.types.Operator):
    bl_idname = "hops.st3_array_offset"
    bl_label = "Offset"
    bl_description = 'Set offset type'

    def execute(self, context):
        op = HOPS_OT_ST3_Array.operator
        if not op: return {'FINISHED'}
        offset = op.get_offset_hook()

        offset = 'Relative' if offset == 'Constant' else 'Constant'
        op.set_relative_constant(offset)

        return {'FINISHED'}

class HOPS_OT_ST3_Array_ModMove(bpy.types.Operator):
    bl_idname = "hops.st3_array_modmove"
    bl_label = "Move"
    bl_description = 'Move modifier'

    up: bpy.props.BoolProperty()
    def execute(self, context):
        op = HOPS_OT_ST3_Array.operator
        if not op: return {'FINISHED'}

        op.move_mod(context, self.up)

        return {'FINISHED'}

class HOPS_OT_ST3_Array_AddRemove(bpy.types.Operator):
    bl_idname = "hops.st3_add_remove"
    bl_label = "Add"
    bl_description = '''Click to Add a new array
    Shift + Click to remove current array'''

    def invoke(self, context, event):
        op = HOPS_OT_ST3_Array.operator
        if not op: return {'FINISHED'}

        op.add_remove_array(remove=event.shift)

        return {'FINISHED'}

class HOPS_OT_ST3_Array_SetOne(bpy.types.Operator):
    bl_idname = "hops.st3_add_setone"
    bl_label = "Add"
    bl_description = '''Click - Set Array to 1
    Shift + Click - Add 1
    Alt + Click - Set array to 1 and others to 0'''

    axis: bpy.props.StringProperty()

    def invoke(self, context, event):
        op = HOPS_OT_ST3_Array.operator
        if not op: return {'FINISHED'}

        if event.alt:
            op.set_others_to_one(preserve_axis=self.axis)
        else:
            op.set_to_one(shift=event.shift, axis=self.axis)

        return {'FINISHED'}
