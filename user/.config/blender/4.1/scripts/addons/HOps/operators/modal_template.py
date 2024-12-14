import bpy, mathutils, math
from mathutils import Vector, Matrix, Quaternion
from .. utility import addon
from .. utility.base_modal_controls import Base_Modal_Controls
from .. ui_framework.master import Master
from .. ui_framework import form_ui as form
from .. ui_framework.utils.mods_list import get_mods_list
from .. utils.toggle_view3d_panels import collapse_3D_view_panels
from .. utils.modal_frame_drawing import draw_modal_frame
from .. utils.cursor_warp import mouse_warp
from .. utility import method_handler


DESC = """NAME

INFO

Press H for help"""


class HOPS_OT_Template(bpy.types.Operator):
    bl_idname = "hops.template"
    bl_label = "Hops Template"
    bl_description = DESC
    bl_options = {"REGISTER", "UNDO", "BLOCKING"}

    @classmethod
    def poll(cls, context):
        return True


    def invoke(self, context, event):

        # Form
        self.form_exit = False
        self.form = None
        self.setup_form(context, event)

        # Base Systems
        self.master = Master(context)
        self.master.only_use_fast_ui = True
        self.base_controls = Base_Modal_Controls(context, event)
        self.original_tool_shelf, self.original_n_panel = collapse_3D_view_panels()
        self.draw_handle_2D = bpy.types.SpaceView3D.draw_handler_add(self.safe_draw_2D, (context,), 'WINDOW', 'POST_PIXEL')
        self.draw_handle_3D = bpy.types.SpaceView3D.draw_handler_add(self.safe_draw_3D, (context,), 'WINDOW', 'POST_VIEW')

        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}


    def modal(self, context, event):

        # --- Base Systems --- #
        self.master.receive_event(event=event)
        self.base_controls.update(context, event)
        self.form.update(context, event)

        mouse_warp(context, event)

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

        elif event.type == 'TAB' and event.value == 'PRESS':
            if self.form.is_dot_open(): 
                self.form.close_dot()
            else:
                self.form.open_dot()

        # --- Actions --- #
        if not self.form.active():
            self.actions(context, event)

        self.interface(context)
        context.area.tag_redraw()
        return {"RUNNING_MODAL"}


    def actions(self, context, event):

        # Event
        if event.type == 'V' and event.value == "PRESS":
            pass


    def interface(self, context):

        self.master.setup()
        if not self.master.should_build_fast_ui(): return
    
        # --- Main --- #
        # Micro UI
        win_list = []
        if addon.preference().ui.Hops_modal_fast_ui_loc_options != 1: 
            win_list.append("Template")
        # Full
        else:
            win_list.append("Template")

        # --- Help --- #
        help_items = {"GLOBAL" : [], "STANDARD" : []}

        help_items["GLOBAL"] = [
            ("M", "Toggle mods list"),
            ("H", "Toggle help"),
            ("~", "Toggle UI Display Type"),
            ("O", "Toggle viewport rendering")]

        help_items["STANDARD"] = [
            ("TAB", f"Dot {'Close' if self.form.is_dot_open() else 'Open'}"),
            ("X", "XXX"),
        ]

        # --- Mods --- #
        obj = context.active_object
        active_mod = ""
        mods_list = get_mods_list(mods=obj.modifiers)

        self.master.receive_fast_ui(win_list=win_list, help_list=help_items, image="Array", mods_list=mods_list, active_mod_name=active_mod)
        self.master.finished()

    # --- FORM --- #

    def setup_form(self, context, event):
        self.form = form.Form(context, event, dot_open=False)

        row = self.form.row()
        row.add_element(form.Label(text="Template", width=60))
        row.add_element(form.Button(text="X", width=20, tips=["Finalize and Exit"], callback=self.exit_button))
        self.form.row_insert(row)

        self.form.build()


    # --- UTILS --- #


    # --- EXITS --- #

    def confirm_exit(self, context):
        self.common_exit(context)
        return {'FINISHED'}


    def cancel_exit(self, context):
        self.common_exit(context)
        return {'CANCELLED'}


    def common_exit(self, context):
        self.form.shut_down(context)
        self.remove_shaders()
        collapse_3D_view_panels(self.original_tool_shelf, self.original_n_panel)
        self.master.run_fade()


    def exit_button(self):
        self.form_exit = True

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
        draw_modal_frame(context)
        self.form.draw()


    def safe_draw_3D(self, context):
        method_handler(self.draw_shader_3D,
            arguments = (context,),
            identifier = 'Modal Shader 3D',
            exit_method = self.remove_shaders)


    def draw_shader_3D(self, context):
        pass