import bpy
import math
from mathutils import Vector
from ... utility import addon
from ... utility import modifier
from ... utility.base_modal_controls import Base_Modal_Controls
from ... ui_framework.master import Master
from ... ui_framework import form_ui as form
from ... ui_framework.utils.mods_list import get_mods_list
from ... utils.toggle_view3d_panels import collapse_3D_view_panels
from ... utils.gizmo_axial import Axial
from ... utils.mod_controller import Mod_Controller
from ... utils.modal_frame_drawing import draw_modal_frame
from ... utils.cursor_warp import mouse_warp
from ... utility import method_handler
from ...utility.screen import dpi_factor

DIRECTION_TYPES = ["NORMAL", "X", "Y", "Z", "CUSTOM_NORMAL", "RGB_TO_XYZ"]

DESC = """LMB - Adjust Displace Modifier
LMB + CTRL - Add new Displace Modifier

Press H for help
"""

#Popup props
def direction_update(self, context):
    op = HOPS_OT_MOD_Displace.operator
    if op.popup:
        op.set_direction(self.prop_direction)
        if addon.preference().ui.Hops_extra_info:
            bpy.ops.hops.display_notification(info=f"Displacement: {self.prop_direction}")

def strength_update(self, context):
    op = HOPS_OT_MOD_Displace.operator
    if op.popup:
        op.strength = self.prop_strength

def midlevel_update(self, context):
    op = HOPS_OT_MOD_Displace.operator
    if op.popup:
        op.mid_level = self.prop_midlevel

def prop_sync():
    op = HOPS_OT_MOD_Displace.operator
    op.popup = False
    op.prop_direction = op.direction_hook()
    op.prop_strength = op.strength
    op.prop_midlevel = op.mid_level
    op.popup = True

class HOPS_OT_MOD_Displace(bpy.types.Operator):
    bl_idname = "hops.mod_displace"
    bl_label = "Adjust Displace Modifier"
    bl_options = {"REGISTER", "UNDO", "BLOCKING"}
    bl_description = DESC

    displace_objects = {}
    operator = None
    popup = False

    axis: bpy.props.EnumProperty(
        name="Axis",
        description="What axis to array around",
        items=[
            ('X', "X", "Displace X axis"),
            ('Y', "Y", "Displace Y axis"),
            ('Z', "Z", "Displace Z axis")
            ],
        default='X')

    prop_direction: bpy.props.EnumProperty(
        name='Direction',
        description='',
        items=[
            ("X", "X", "Displace in X direction"),
            ("Y", "Y", "Displace in Y direction"),
            ("Z", "Z", "Displace in Z direction"),
            ("NORMAL", "Normal", "Displace along vertex normals"),
            ("CUSTOM_NORMAL", "Custom Normal", "Displace along averaged custom normals"),
            ("RGB_TO_XYZ", "RGB to XYZ", "Convert textures RGB values into XYZ displacement"),
        ],
        update=direction_update
    )

    prop_strength: bpy.props.FloatProperty(
        name='Strength',
        description='Amount to displace geometry',
        update=strength_update,
    )

    prop_midlevel: bpy.props.FloatProperty(
        name='Midlevel',
        description='Material value that gives no displacement',
        soft_min=0,
        soft_max=1,
        update=midlevel_update,
    )

    @classmethod
    def poll(cls, context):
        return any(o.type == 'MESH' for o in context.selected_objects)

    @property
    def strength(self):
        for mod in self.mod_controller.active_modifiers():
            return round(mod.strength, 2)

    @strength.setter
    def strength(self, val):
        for mod in self.mod_controller.active_modifiers():
            mod.strength = val

    @property
    def mid_level(self):
        for mod in self.mod_controller.active_modifiers():
            return round(mod.mid_level, 2)

    @mid_level.setter
    def mid_level(self, val):
        for mod in self.mod_controller.active_modifiers():
            mod.mid_level = val


    def invoke(self, context, event):

        self.__class__.operator = self
        self.blender_popup = addon.preference().property.in_tool_popup_style == 'BLENDER'

        # Mods
        objs = [o for o in context.selected_objects if o.type == 'MESH']
        type_map = {bpy.types.Mesh : 'DISPLACE'}
        self.mod_controller = Mod_Controller(context, objs, type_map, create_new=event.ctrl, active_obj=context.active_object)

        self.mod_controller.sort_mods(sort_types=['WEIGHTED_NORMAL'])

        for mod in self.mod_controller.all_created_mods():
            initial_mod_settings(mod)

        # Gizmo
        self.axial = Axial()

        # Form
        self.form_exit = False
        self.remove_exit = False
        self.index_button = None
        self.setup_form(context, event)

        # Base Systems
        self.master = Master(context=context)
        self.master.only_use_fast_ui = True
        self.base_controls = Base_Modal_Controls(context, event)
        self.original_tool_shelf, self.original_n_panel = collapse_3D_view_panels()
        self.draw_handle = bpy.types.SpaceView3D.draw_handler_add(self.safe_draw_shader, (context,), 'WINDOW', 'POST_PIXEL')

        if not addon.preference().keymap.spacebar_accept:
            self.base_controls.confirm_events.remove('SPACE')

        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}


    def modal(self, context, event):

        # Base Systems
        self.master.receive_event(event)
        self.base_controls.update(context, event)

        if self.popup:
            self.draw_master(context=context)
            context.area.tag_redraw()
            return {"PASS_THROUGH"}

        # Form
        if not self.blender_popup:
            self.form.update(context, event)
            self.index_button.text = str(self.mod_controller.active_obj_mod_index() + 1)

        # Gizmo
        if not self.form.active():
            self.axial.update(context, event, self.axial_callback)

        # Base Controls
        if self.base_controls.pass_through:
            if not self.form.active():
                return {'PASS_THROUGH'}

        elif self.base_controls.confirm:
            if not self.form.active():
                self.confirm_exit(context, event)
                return {'FINISHED'}

        elif self.base_controls.cancel:
            self.cancel_exit(context, event)
            return {'CANCELLED'}

        elif self.form_exit:
            if self.remove_exit:
                self.mod_controller.remove_active_mod(leave_one=False)
                self.mod_controller.cancel_exit()
            self.confirm_exit(context, event)
            return {'FINISHED'}

        if event.type == 'TAB' and event.value == 'PRESS':
            if self.blender_popup:
                self.popup = True
                bpy.ops.hops.mod_displace_popup()

            else:
                if self.form.is_dot_open():
                    self.form.close_dot()
                else:
                    self.form.open_dot()

        mod = self.mod_controller.active_object_mod()
        if mod: context.area.header_text_set(f"Hardops Displace:     Space: {mod.space}")

        if not self.form.is_dot_open():
            mouse_warp(context, event)
            self.mouse_adjust(context, event)

        if not self.form.active():
            self.actions(context, event)

        self.draw_master(context=context)
        context.area.tag_redraw()
        return {"RUNNING_MODAL"}

    # --- ACTIONS --- #

    def mouse_adjust(self, context, event):
        for mod in self.mod_controller.active_modifiers():
            # Mouse motion
            if addon.preference().property.modal_handedness == 'LEFT':
                if event.ctrl:
                    mod.mid_level -= self.base_controls.mouse / 10
                else:
                    mod.strength -= self.base_controls.mouse
            else:
                if event.ctrl:
                    mod.mid_level += self.base_controls.mouse / 10
                else:
                    mod.strength += self.base_controls.mouse
            # Regular scroll
            if self.base_controls.scroll:
                if not event.shift:
                    mod.direction = DIRECTION_TYPES[(DIRECTION_TYPES.index(mod.direction) + self.base_controls.scroll) % len(DIRECTION_TYPES)]
                    if addon.preference().ui.Hops_extra_info:
                        bpy.ops.hops.display_notification(info=f"{mod.direction}" )
        # Shift scroll
        if self.base_controls.scroll > 0 and event.shift:
            self.mod_controller.move_mod(context, up=True)

        elif self.base_controls.scroll < 0 and event.shift:
            self.mod_controller.move_mod(context, up=False)


    def actions(self, context, event):

        if event.type == "Q" and event.value == "PRESS" and event.shift:
            self.toggle_space()

        elif event.type == 'X' and event.value == 'PRESS':
            self.toggle_axis()

        elif event.type == "Y" and event.value == "PRESS":
            self.set_direction(direction='Y')

        elif event.type == "Z" and event.value == "PRESS":
            self.set_direction(direction='Z')

        elif event.type == "N" and event.value == "PRESS":
            self.set_direction(direction='NORMAL')

        elif event.type == "Q" and event.value == "PRESS":
            self.mod_controller.move_mod(context, up=True)

        elif event.type == "W" and event.value == "PRESS":
            self.mod_controller.move_mod(context, up=False)

        elif event.type in {'ZERO', 'NUMPAD_0'} and event.value == "PRESS":
            self.set_strength(strength=0)

        elif event.type == 'SPACE' and event.value == 'PRESS':
            self.popup = True
            bpy.ops.hops.mod_displace_modselect()


    def toggle_space(self):
        space_types = ["GLOBAL", "LOCAL"]
        for mod in self.mod_controller.active_modifiers():
            mod.space = space_types[(space_types.index(mod.space) + 1) % len(space_types)]


    def toggle_axis(self):
        self.axis = "YZX"["XYZ".find(self.axis)]
        for mod in self.mod_controller.active_modifiers():
            mod.direction = self.axis
            self.report({'INFO'}, f"Displace Axis: {self.axis}")
            if addon.preference().ui.Hops_extra_info:
                bpy.ops.hops.display_notification(info=f"Displace Axis: {self.axis}")


    def set_direction(self, direction='Y'):
        for mod in self.mod_controller.active_modifiers():
            mod.direction = direction


    def set_strength(self, strength=0):
        for mod in self.mod_controller.active_modifiers():
            mod.strength = strength
        if addon.preference().ui.Hops_extra_info:
            bpy.ops.hops.display_notification(info=F'Strength : {strength}' )

    # --- GIZMO --- #

    def axial_callback(self, val):

        def set_mods(direction='X', pos_dir=True):
            for mod in self.mod_controller.active_modifiers():
                mod.direction = direction
                if pos_dir: mod.strength = abs(mod.strength)
                else: mod.strength = abs(mod.strength) * -1

        if val == 'X':
            set_mods(direction='X', pos_dir=True)
        elif val == 'Y':
            set_mods(direction='Y', pos_dir=True)
        elif val == 'Z':
            set_mods(direction='Z', pos_dir=True)
        if val == '-X':
            set_mods(direction='X', pos_dir=False)
        elif val == '-Y':
            set_mods(direction='Y', pos_dir=False)
        elif val == '-Z':
            set_mods(direction='Z', pos_dir=False)

    # --- INTERFACE --- #

    def draw_master(self, context):
        self.master.setup()
        if not self.master.should_build_fast_ui(): return

        mod = self.mod_controller.active_object_mod()
        obj = self.mod_controller.active_obj

        if not mod or not obj: return

        # Main
        win_list = []
        if addon.preference().ui.Hops_modal_fast_ui_loc_options != 1: #Fast Floating
            win_list.append("{}".format(mod.direction))
            win_list.append("{:.3f}".format(mod.strength))
            win_list.append("{:.3f}".format(mod.mid_level))
        else:
            win_list.append("Displace")
            win_list.append("Str: {:.3f}".format(mod.strength))
            win_list.append("Mid: {:.3f}".format(mod.mid_level))
            win_list.append("Direction: {}".format(mod.direction))

        # Help
        help_items = {"GLOBAL" : [], "STANDARD" : []}

        help_items["GLOBAL"] = [
            ("M", "Toggle mods list"),
            ("H", "Toggle help"),
            ("~", "Toggle UI Display Type"),
            ("O", "Toggle viewport rendering")]

        help_items["STANDARD"] = [
            ("Space",          "Select direction"),
            ("move",           "Set strength"),
            ("ctrl",           "Set Offset"),
            ("WHEEL",          "Direction"),
            ("Shift + Scroll", "Move mod up/down"),
            ("Shift + Q",      "Space"),
            ("0",              "Strength to 0."),
            ("N",              "Set Normal"),
            ("Q",              "Move mod DOWN"),
            ("W",              "Move mod UP"),
            ("C" if context.preferences.inputs.use_mouse_emulate_3_button else "Alt", "Open Axial Change"),]

        # Mods
        active_mod = mod.name
        mods_list = get_mods_list(mods=bpy.context.active_object.modifiers)

        self.master.receive_fast_ui(win_list=win_list, help_list=help_items, image="BevelMultiply", mods_list=mods_list, active_mod_name=active_mod)
        self.master.finished()


    def setup_form(self, context, event):
        self.form = form.Form(context, event, dot_open=False)

        def spacer(height=10):
            row = self.form.row()
            row.add_element(form.Spacer(height=height))
            self.form.row_insert(row)

        row = self.form.row()
        row.add_element(form.Label(text="Displace", width=65))

        tip = ["Scroll / Click : Active Displace to effect", "Ctrl Click : Add new Displace", "Shift Ctrl Click : Remove current Displace"]
        self.index_button = form.Button(
            text="0", width=20, tips=tip,
            callback=self.mod_index_move, pos_args=(True,), neg_args=(False,),
            ctrl_callback=self.add_remove_displace, ctrl_args=(True,),
            shift_ctrl_callback=self.add_remove_displace, shift_ctrl_args=(False,))
        row.add_element(self.index_button)

        row.add_element(form.Button(text="U", width=20, tips=["Click / Scroll", "Move modifier up", "Shift : Move modifier down"],
            callback=self.mod_controller.move_mod, shift_text="D", pos_args=(context, True), neg_args=(context, False)))

        row.add_element(
            form.Button(
                text="✓", width=23, tips=["Click : Finalize and Exit", "Ctrl Click : Remove Solidify and Exit"],
                callback=self.exit_button, ctrl_callback=self.remove_and_exit, ctrl_text='X'))

        self.form.row_insert(row)

        spacer()

        row = self.form.row()
        row.add_element(form.Label(text='Strength', width=65))
        row.add_element(form.Input(obj=self, attr="strength", width=55, increment=.1))
        self.form.row_insert(row)

        row = self.form.row()
        row.add_element(form.Label(text='Mid Level', width=65))
        row.add_element(form.Input(obj=self, attr="mid_level", width=55, increment=.1))
        self.form.row_insert(row)

        spacer()

        row = self.form.row()
        row.add_element(form.Dropdown(width=120, options=DIRECTION_TYPES, tips=["Displace Options"],
            callback=self.direction_opts, update_hook=self.direction_hook, cyclic_scroll=True))
        self.form.row_insert(row)

        self.form.build()

    # --- FORM FUNCS --- #

    def mod_index_move(self, forward=True):
        self.mod_controller.clamped_next_mod_index(forward)


    def direction_opts(self, opt='X'):
        if opt not in DIRECTION_TYPES: return
        for mod in self.mod_controller.active_modifiers():
            mod.direction = opt


    def direction_hook(self):
        mod = self.mod_controller.active_object_mod()
        if not mod: return 'X'
        if not hasattr(mod, 'direction'): return 'X'
        return str(mod.direction)


    def add_remove_displace(self, add=True):
        if add:
            mods = self.mod_controller.create_new_mod(count_limit=4)
            for mod in mods:
                initial_mod_settings(mod)
        else:
            self.mod_controller.remove_active_mod(use_logical_delete=True, remove_if_created=True)

    # --- EXIT --- #

    def remove_and_exit(self):
        self.remove_exit = True
        self.form_exit = True


    def exit_button(self):
        self.form_exit = True


    def confirm_exit(self, context, event):
        self.remove_shader()
        collapse_3D_view_panels(self.original_tool_shelf, self.original_n_panel)
        self.mod_controller.confirm_exit()
        self.master.run_fade()
        context.area.header_text_set(text=None)
        self.__class__.operator = None


    def cancel_exit(self, context, event):
        self.remove_shader()
        collapse_3D_view_panels(self.original_tool_shelf, self.original_n_panel)
        self.mod_controller.cancel_exit()
        self.master.run_fade()
        context.area.header_text_set(text=None)
        self.__class__.operator = None

    # --- SHADER --- #

    def safe_draw_shader(self, context):
        method_handler(self.draw_shader,
            arguments = (context,),
            identifier = 'Displace Shader',
            exit_method = self.remove_shader)


    def remove_shader(self):
        if self.draw_handle:
            self.draw_handle = bpy.types.SpaceView3D.draw_handler_remove(self.draw_handle, "WINDOW")


    def draw_shader(self, context):
        if not self.blender_popup:
            self.form.draw()

            if not self.form.is_dot_open():
                draw_modal_frame(context)

        self.axial.draw()

# --- UTILS --- #

def initial_mod_settings(mod):
    mod.direction = 'X'
    mod.space = 'LOCAL'
    mod.mid_level = 0
    mod.strength = 0



# Popup

class Displace_Popup(bpy.types.Operator):

    @classmethod
    def poll(cls, context):
        return HOPS_OT_MOD_Displace.operator

class HOPS_OT_MOD_Displace_Popup(Displace_Popup):
    bl_idname = "hops.mod_displace_popup"
    bl_label = ""
    bl_description = ""

    def __del__(self):
        op = HOPS_OT_MOD_Displace.operator
        if not op: return

        op.popup = False

    def execute(self, context):
        op = HOPS_OT_MOD_Displace.operator
        if not op: return {'CANCELLED'}

        prop_sync()

        return bpy.context.window_manager.invoke_popup(self, width=int(150 * dpi_factor()))


    def draw (self, context):
        op = HOPS_OT_MOD_Displace.operator
        if not op: return
        if op.form_exit:
            self.layout.label(text='Pres ESC or move cursor')
            return

        layout = self.layout

        row = layout.row(align=True)
        row.label(text='Displace')
        row.operator(HOPS_OT_MOD_Displace_ModAdd.bl_idname, text='', icon='PLUS')
        row.operator(HOPS_OT_MOD_Displace_ModRem.bl_idname, text='', icon='X')
        row.operator(HOPS_OT_MOD_Displace_Confirm.bl_idname, text='', icon='CHECKMARK')

        row = layout.row(align=True)
        row.label(text='Strength')
        row.prop(op, 'prop_strength', text='')

        row = layout.row(align=True)
        row.label(text='Midlevel')
        row.prop(op, 'prop_midlevel', text='')

        row = layout.row(align=True)
        row.label(text='Direction')
        row.prop(op, 'prop_direction', text='')

        mod = op.mod_controller.active_object_mod()
        row = layout.row(align=True)
        row.popover(HOPS_PT_MOD_Displace_Selector.bl_idname, text=mod.name)

class HOPS_OT_MOD_Displace_Confirm(Displace_Popup):
    bl_idname = "hops.mod_displace_confirm"
    bl_label = """Confirm and exit\nCtrl-Click Remove modifier and exit"""
    bl_description = ""

    def invoke(self, context, event):
        op = HOPS_OT_MOD_Displace.operator

        if event.ctrl:
            op.remove_and_exit()
        else:
            op.exit_button()

        return {'FINISHED'}

class HOPS_PT_MOD_Displace_Selector(bpy.types.Panel):
    bl_idname = "HOPS_PT_MOD_Displace_Selector"
    bl_label = ""
    bl_description = 'Selector'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'

    def draw(self, context):
        layout = self.layout

        op = HOPS_OT_MOD_Displace.operator
        if not op: return

        layout.label(text='Selector')

        mods = op.mod_controller.active_obj_mods()

        for i, mod in enumerate(mods):
            row = layout.row()
            row.scale_y = 2
            props = row.operator("hops.mod_displace_modset", text=f'({mod.direction}) {mod.name}')
            props.index = i

class HOPS_OT_MOD_Displace_ModSet(Displace_Popup):
    bl_idname = "hops.mod_displace_modset"
    bl_label = ""
    bl_description = 'Selector'

    index: bpy.props.IntProperty()

    def execute(self, context):
        op = HOPS_OT_MOD_Displace.operator

        current = op.mod_controller.active_obj_mod_index()
        forward = False
        count = 0
        if self.index > current:
            count = self.index - current
            forward = True
        else:
            count = current - self.index
            forward = False

        for _ in range(count):
            op.mod_index_move(forward)

        prop_sync()

        return {'FINISHED'}


class HOPS_OT_MOD_Displace_ModAdd(Displace_Popup):
    bl_idname = "hops.mod_displace_modadd"
    bl_label = ""
    bl_description = 'Add new Dispalce modifier'

    def execute(self, context):
        op = HOPS_OT_MOD_Displace.operator

        op.add_remove_displace(add=True)

        prop_sync()

        return {'FINISHED'}

class HOPS_OT_MOD_Displace_ModRem(Displace_Popup):
    bl_idname = "hops.mod_displace_modrem"
    bl_label = ""
    bl_description = 'Remove current Dispalce modifier'

    def execute(self, context):
        op = HOPS_OT_MOD_Displace.operator

        op.add_remove_displace(add=False)
        prop_sync()

        return {'FINISHED'}

class HOPS_OT_MOD_Displace_ModSelect(Displace_Popup):
    bl_idname = "hops.mod_displace_modselect"
    bl_label = ""
    bl_description = ''

    def __del__(self):
        op = HOPS_OT_MOD_Displace.operator
        if op:
            op.popup = False

    def execute(self, context):
        op = HOPS_OT_MOD_Displace.operator

        prop_sync()

        return bpy.context.window_manager.invoke_popup(self, width=int(180 * dpi_factor()))

    def draw(self, context):
        HOPS_PT_MOD_Displace_Selector.draw(self, context)
