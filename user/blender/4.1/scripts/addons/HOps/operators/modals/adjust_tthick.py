import bpy
from gpu_extras.batch import batch_for_shader
from mathutils import Vector
from ...utility.screen import dpi_factor
from ... utility import modifier
from ... utility.base_modal_controls import Base_Modal_Controls
from ... utils.toggle_view3d_panels import collapse_3D_view_panels
from ... utils.mod_controller import Mod_Controller
from ... utility import addon
from ... ui_framework.master import Master
from ... ui_framework import form_ui as form
from ... ui_framework.utils.mods_list import get_mods_list
from . import infobar
# Cursor Warp imports
from ... utils.cursor_warp import mouse_warp
from ... utils.modal_frame_drawing import draw_modal_frame
from ... utility import method_handler


# set controller index and notification
def mod_name_update(self, context):
    op = HOPS_OT_AdjustTthickOperator.operator
    if not op: return

    valid = op.mod_controller.set_active_obj_mod_index(op.active_mod_name)
    if valid and addon.preference().ui.Hops_extra_info:
        bpy.ops.hops.display_notification(info=f'Target Solidify: {op.active_mod_name}')

DESC = """LMB - Adjust SOLIDIFY modifier
LMB + Ctrl - Add New SOLIDIFY modifier

Press H for help"""


class HOPS_OT_AdjustTthickOperator(bpy.types.Operator):
    bl_idname = "hops.adjust_tthick"
    bl_label = "Adjust Tthick"
    bl_description = DESC
    bl_options = {"REGISTER", "UNDO", "BLOCKING"}

    operator = None
    popup = False
    active_mod_name: bpy.props.StringProperty(update=mod_name_update)

    @classmethod
    def poll(cls, context):
        return any(o.type == 'MESH' for o in context.selected_objects)

    @property
    def thickness(self):
        for mod in self.mod_controller.active_modifiers():
            return round(mod.thickness, 2)

    @thickness.setter
    def thickness(self, val):
        for mod in self.mod_controller.active_modifiers():
            mod.thickness = val

    @property
    def offset(self):
        for mod in self.mod_controller.active_modifiers():
            return round(mod.offset, 2)

    @offset.setter
    def offset(self, val):
        for mod in self.mod_controller.active_modifiers():
            mod.offset = val


    def invoke(self, context, event):

        self.__class__.operator = self

        objs = [o for o in context.selected_objects if o.type == 'MESH']
        for obj in objs: modifier.sort(obj, types=['WEIGHTED_NORMAL'], last=True)

        type_map = {bpy.types.Mesh : 'SOLIDIFY'}
        self.mod_controller = Mod_Controller(context, objs, type_map, create_new=event.ctrl, active_obj=context.active_object)

        self.mod_controller.sort_mods(sort_types=['WEIGHTED_NORMAL'])

        self.mod_controller.set_attr(attr='use_even_offset', value=True)
        self.mod_controller.set_attr(attr='use_quality_normals', value=True)
        self.mod_controller.set_attr(attr='use_rim_only', value=False)
        self.mod_controller.set_attr(attr='show_on_cage', value=True)

        self.form_exit = False
        self.remove_exit = False
        self.offset_hook_val = '0'
        self.index_button = None
        self.setup_form(context, event)

        self.popup_style = addon.preference().property.in_tool_popup_style

        self.master = Master(context)
        self.master.only_use_fast_ui = True
        self.base_controls = Base_Modal_Controls(context, event)
        self.original_tool_shelf, self.original_n_panel = collapse_3D_view_panels()

        self.draw_handle = None
        if self.popup_style == 'DEFAULT':
            self.draw_handle = bpy.types.SpaceView3D.draw_handler_add(self.safe_draw_shader, (context,), 'WINDOW', 'POST_PIXEL')

        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}


    def modal(self, context, event):

        self.master.receive_event(event)
        self.base_controls.update(context, event)

        if self.popup_style == 'DEFAULT':
            self.form.update(context, event)

        # Label
        self.index_button.text = str(self.mod_controller.active_obj_mod_index() + 1)

        if self.popup:
            self.FAS_interface(context, event)
            context.area.tag_redraw()
            return {'RUNNING_MODAL'}

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

            if self.popup_style == 'BLENDER':
                bpy.ops.hops.adjust_tthick_popup()
                self.popup = True

            else:
                if self.form.is_dot_open():
                    self.form.close_dot()
                else:
                    self.form.open_dot()

        # Modal Mouse
        if not self.form.is_dot_open():
            mouse_warp(context, event)
            self.mouse_adjust(context, event)

        # Hot Keys
        if not self.form.active():
            self.actions(context, event)

        self.FAS_interface(context, event)
        context.area.tag_redraw()
        return {"RUNNING_MODAL"}


    def mouse_adjust(self, context, event):
        offset = self.base_controls.mouse
        for mod in self.mod_controller.active_modifiers():
            mod.thickness += offset
            if event.ctrl:
                mod.thickness = round(mod.thickness, 1)

        if event.shift:
            if self.base_controls.scroll > 0: self.mod_controller.move_mod(context, up=True)
            elif self.base_controls.scroll < 0: self.mod_controller.move_mod(context, up=False)


    def actions(self, context, event):

        if event.type == 'ONE' and event.value == 'PRESS':
            self.offset_negative_one()

        elif event.type == 'TWO' and event.value == 'PRESS':
            self.offset_to_zero()

        elif event.type == 'THREE' and event.value == 'PRESS':
            self.offset_to_one()

        elif event.type == "Q" and event.value == "PRESS":
            self.mod_controller.move_mod(context, up=True)

        elif event.type == "E" and event.value == "PRESS":
            self.mod_controller.move_mod(context, up=False)

        elif event.type == 'R' and event.value == 'PRESS':
            self.toggle_use_rim()

        elif event.type == 'FOUR' and event.value == 'PRESS':
            self.toggle_solidify_mode()

        elif event.type == 'A' and event.value == 'PRESS':
            if event.shift:
                self.mod_controller.remove_active_mod()
            else:
                self.mod_controller.create_new_mod(count_limit=4)

        elif event.type in {'NUMPAD_PLUS'} and event.value == 'PRESS':
            self.mod_index_move(forward=True)

        elif event.type in {'NUMPAD_MINUS'} and event.value == 'PRESS':
            self.mod_index_move(forward=False)


    def offset_negative_one(self):
        for mod in self.mod_controller.active_modifiers():
            mod.offset = -1


    def offset_to_zero(self):
        for mod in self.mod_controller.active_modifiers():
            mod.offset = 0


    def offset_to_one(self):
        for mod in self.mod_controller.active_modifiers():
            mod.offset = 1


    def toggle_use_rim(self):
        for mod in self.mod_controller.active_modifiers():
            mod.use_rim_only = not mod.use_rim_only


    def toggle_solidify_mode(self):
        if (2, 82, 4) < bpy.app.version:
            for mod in self.mod_controller.active_modifiers():
                if mod.solidify_mode == 'EXTRUDE': mod.solidify_mode = 'NON_MANIFOLD'
                else: mod.solidify_mode = 'EXTRUDE'


    def set_solidify_mode(self, opt=''):
        if (2, 82, 4) < bpy.app.version:
            for mod in self.mod_controller.active_modifiers():
                if opt == 'EXTRUDE': mod.solidify_mode = 'EXTRUDE'
                else: mod.solidify_mode = 'NON_MANIFOLD'


    def solidify_mode_hook(self, opt=''):
        if (2, 82, 4) < bpy.app.version:
            for mod in self.mod_controller.active_modifiers():
                if mod.solidify_mode == 'EXTRUDE': return 'EXTRUDE'
                return 'NON_MANIFOLD'


    def offset_switch(self, opt=''):
        self.offset_hook_val = opt

        if opt == '-1':
            self.offset_negative_one()
        elif opt == '0':
            self.offset_to_zero()
        elif opt == '1':
            self.offset_to_one()


    def offset_switch_hook(self):
        return self.offset_hook_val


    def mod_index_move(self, forward=True):
        self.mod_controller.clamped_next_mod_index(forward)

    # --- INTERFACE --- #

    def FAS_interface(self, context, event):
        self.master.setup()
        if self.master.should_build_fast_ui():

            mod = self.mod_controller.active_object_mod()

            # Main
            win_list = []
            if addon.preference().ui.Hops_modal_fast_ui_loc_options != 1: #Fast Floating
                if mod != None:
                    win_list.append("{:.2f}".format(mod.thickness))
                    win_list.append("{}".format(mod.use_rim_only))
                    win_list.append("{:.2f}".format(mod.offset))
                else:
                    win_list.append("0")
                    win_list.append("Rim: Removed")
                    win_list.append("Offset: Removed")
            else:
                win_list.append("Solidify")
                if mod != None:
                    win_list.append("{:.3f}".format(mod.thickness))
                    win_list.append("Rim: {}".format(mod.use_rim_only))
                    win_list.append("Offset: {:.2f}".format(mod.offset))
                else:
                    win_list.append("0")
                    win_list.append("Rim: Removed")
                    win_list.append("Offset: Removed")

            # Help
            help_items = {"GLOBAL" : [], "STANDARD" : []}

            help_items["GLOBAL"] = [
                ("M", "Toggle mods list"),
                ("H", "Toggle help"),
                ("~", "Toggle UI Display Type"),
                ("O", "Toggle viewport rendering")]

            help_items["STANDARD"] = [
                ("Shift A",        "Remove current Solidify"),
                ("A",              "Add a new Solidify"),
                ("R",              "Turn rim on/off"),
                ("Ctrl",           "Set thickness (snap)"),
                ("Shift + Scroll", "Move mod up/down"),
                ("+ / -",          "Active solidify to effect"),
                ("1",              "Set offset to -1"),
                ("2",              "Set offset to 0"),
                ("3",              "Set offset to 1")]

            h_append = help_items["STANDARD"].append

            if mod != None:
                h_append(["4", F"Solidify Mode: {mod.solidify_mode.capitalize()}"])
            h_append(["E / Q",  "Move mod up/down"])
            h_append(["X",      "Pause mouse"])
            h_append(["TAB", "Open Dot UI"])

            # Mods
            active_mod = ""
            if mod != None:
                active_mod = mod.name
            mods_list = get_mods_list(mods=bpy.context.active_object.modifiers)

            self.master.receive_fast_ui(win_list=win_list, help_list=help_items, image="Tthick", mods_list=mods_list, active_mod_name=active_mod)
        self.master.finished()


    def setup_form(self, context, event):
        self.form = form.Form(context, event, dot_open=False)

        def spacer(height=10):
            row = self.form.row()
            row.add_element(form.Spacer(height=height))
            self.form.row_insert(row)

        row = self.form.row()
        row.add_element(form.Label(text="Solidify", width=55))
        tip = ["Scroll / Click", "Active Solidify to effect."]
        self.index_button = form.Button(text="0", width=20, callback=self.mod_index_move, pos_args=(True,), neg_args=(False,), tips=tip)
        row.add_element(self.index_button)
        row.add_element(form.Spacer(width=12))
        row.add_element(
            form.Button(
                text="✓", width=23, tips=["Click : Finalize and Exit", "Ctrl Click : Remove Solidify and Exit"],
                callback=self.exit_button, ctrl_callback=self.remove_and_exit, ctrl_text='X'))
        self.form.row_insert(row)

        spacer()

        row = self.form.row()
        row.add_element(form.Dropdown(width=30, options=['-1', '0', '1'], tips=["Offset Values"], callback=self.offset_switch, update_hook=self.offset_switch_hook))
        row.add_element(form.Button(text="R", width=20, tips=["Toggle use Rim"], callback=self.toggle_use_rim))
        self.form.row_insert(row)

        spacer()

        row = self.form.row()
        row.add_element(form.Label(text='Thickness', width=65))
        row.add_element(form.Input(obj=self, attr="thickness", width=45, increment=.1))
        self.form.row_insert(row)

        row = self.form.row()
        row.add_element(form.Label(text='Offset', width=65))
        row.add_element(form.Input(obj=self, attr="offset", width=45, increment=.1))
        self.form.row_insert(row)

        if (2, 82, 4) < bpy.app.version:

            spacer()

            row = self.form.row()
            row.add_element(form.Dropdown(width=110, options=['EXTRUDE', 'NON_MANIFOLD'], tips=["Solidify Mode"], callback=self.set_solidify_mode, update_hook=self.solidify_mode_hook))
            self.form.row_insert(row)

        self.form.build()

    # --- EXIT --- #

    def remove_and_exit(self):
        self.remove_exit = True
        self.form_exit = True


    def exit_button(self):
        self.form_exit = True


    def confirm_exit(self, context, event):
        self.__class__.operator = None
        self.form.shut_down(context)
        self.remove_shader()
        self.mod_controller.confirm_exit()
        collapse_3D_view_panels(self.original_tool_shelf, self.original_n_panel)
        self.master.run_fade()



    def cancel_exit(self, context, event):
        self.__class__.operator = None
        self.form.shut_down(context)
        self.remove_shader()
        collapse_3D_view_panels(self.original_tool_shelf, self.original_n_panel)
        self.mod_controller.cancel_exit()
        self.master.run_fade()
        infobar.remove(self)

    # --- SHADERS --- #

    def remove_shader(self):
        if self.draw_handle:
            self.draw_handle = bpy.types.SpaceView3D.draw_handler_remove(self.draw_handle, "WINDOW")


    def safe_draw_shader(self, context):
        method_handler(self.draw_shader,
            arguments = (context,),
            identifier = 'UI Framework',
            exit_method = self.remove_shader)


    def draw_shader(self, context):
        self.form.draw()

        if not self.form.is_dot_open():
            draw_modal_frame(context)

class HOPS_OT_AdjustTthicPopup(bpy.types.Operator):
    bl_idname = "hops.adjust_tthick_popup"
    bl_label = "Adjust Tthick"
    bl_description = ""

    def __del__(self):
        op = HOPS_OT_AdjustTthickOperator.operator
        if not op: return

        op.popup = False

    def execute(self, context):
        return bpy.context.window_manager.invoke_popup(self, width=int(150 * dpi_factor()))

    def draw(self, context):

        op = HOPS_OT_AdjustTthickOperator.operator
        if not op: return
        if op.form_exit:
            self.layout.label(text='Pres ESC or move cursor')
            return

        layout = self.layout
        layout.label(text="Solidify")

        mod = op.mod_controller.active_object_mod()

        row = layout.row(align=True)
        row.label(text=mod.name)
        row.operator("hops.adjust_tthick_confirm", text='', icon='CHECKMARK')

        row = layout.row(align=True)
        row.prop(mod, 'thickness')


        row = layout.row(align=True)
        # row.alignment = 'LEFT'
        row.prop(mod, 'offset')


        row = layout.row(align=True)

        offset = row.operator("hops.adjust_tthick_offset", text='-1')
        offset.value = -1.0
        offset = row.operator("hops.adjust_tthick_offset", text='0')
        offset.value = 0
        offset = row.operator("hops.adjust_tthick_offset", text='1')
        offset.value = 1.0

        row.prop(mod, 'use_rim_only', icon='EVENT_R', text='')

        row = layout.row(align=True)
        row.prop(mod, 'solidify_mode')

        layout.popover(HOPS_PT_AdjustTthicSelector.bl_idname, text=mod.name)

class HOPS_OT_AdjustTthicConfirm(bpy.types.Operator):
    bl_idname = "hops.adjust_tthick_confirm"
    bl_label = """Confirm and exit\nCtrl-Click Remove modifier and exit"""
    bl_description = ""

    def invoke(self, context, event):
        op = HOPS_OT_AdjustTthickOperator.operator
        if not op: return

        if event.ctrl:
            op.remove_and_exit()
        else:
            op.exit_button()

        return {'FINISHED'}

class HOPS_PT_AdjustTthicSelector(bpy.types.Panel):
    bl_idname = "HOPS_PT_AdjustTthicSelector"
    bl_label = ""
    bl_description = 'Selector'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'

    def draw(self, context):
        layout = self.layout

        op = HOPS_OT_AdjustTthickOperator.operator
        if not op: return

        layout.label(text='Selector')

        mods = [m.name for m in op.mod_controller.active_obj_mods()]

        for mod in mods:
            row = layout.row()
            row.scale_y = 2
            props = row.operator("hops.adjust_tthick_modset", text=mod)
            props.modname = mod

class HOPS_OT_AdjustTthicModSet(bpy.types.Operator):
    bl_idname = "hops.adjust_tthick_modset"
    bl_label = ""
    bl_description = 'Selector'

    modname: bpy.props.StringProperty()

    def execute(self, context):
        HOPS_OT_AdjustTthickOperator.operator.active_mod_name = self.modname

        return {'FINISHED'}

class HOPS_OT_AdjustTthicOffset(bpy.types.Operator):
    bl_idname = "hops.adjust_tthick_offset"
    bl_label = "Offset"
    bl_description = 'Offset preset'

    value: bpy.props.FloatProperty()

    def execute(self, context):
        op = HOPS_OT_AdjustTthickOperator.operator
        if not op: return
        mod = op.mod_controller.active_object_mod()
        mod.offset = self.value

        return {'FINISHED'}
