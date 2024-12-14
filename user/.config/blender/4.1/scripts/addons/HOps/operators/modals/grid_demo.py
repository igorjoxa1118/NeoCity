import bpy, mathutils, math, gpu
from mathutils import Vector, Matrix, Quaternion
from ... utility import addon
from ... utility.base_modal_controls import Base_Modal_Controls
from ... ui_framework.master import Master
from ... ui_framework import form_ui as form
from ... ui_framework.utils.mods_list import get_mods_list
from ... utils.toggle_view3d_panels import collapse_3D_view_panels
from ... utility import method_handler
from gpu_extras.batch import batch_for_shader

from ...utils.grid import Grid_Controller


DESC = """Grid Demo

Press H for help"""


class HOPS_OT_Grid_Demo(bpy.types.Operator):
    bl_idname = "hops.grid_template"
    bl_label = "Grid Demo"
    bl_description = DESC
    bl_options = {"REGISTER", "UNDO", "BLOCKING"}

    @classmethod
    def poll(cls, context):
        return True


    def invoke(self, context, event):

        # Grid Data
        self.grid_controller = Grid_Controller()
        self.grid_controller.create_grid(key=0, active=True, mode_type='2D')
        # grid = self.grid_controller.create_grid(key=0, active=True, mode_type='2D')
        # grid.alter_grid(loc=(context.area.width * .5, context.area.height * .5, 0), size_x=300, size_y=300)

        self.point = Vector((0,0))
        self.border_points = []
        self.u_lines = []
        self.v_lines = []

        # States
        self.grid_casting = False

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

        if event.type in {'NUMPAD_2', 'NUMPAD_4', 'NUMPAD_6', 'NUMPAD_8', 'NUMPAD_1', 'NUMPAD_3', 'NUMPAD_5', 'NUMPAD_7', 'NUMPAD_9'} and event.value == 'PRESS':
            return {'PASS_THROUGH'}

        # --- Base Systems --- #
        self.master.receive_event(event=event)
        self.base_controls.update(context, event)
        self.form.update(context, event)

        # --- Grid System --- #
        self.grid_updates(context, event)

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


        self.master.receive_fast_ui(win_list=win_list, help_list=help_items)
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


    # --- GRID --- #

    def grid_updates(self, context, event):

        grid = self.grid_controller.get_grid(key=0, mode_type='2D')
        if not grid: return

        grid.locate_grid(context, event, method='object_bounds', object_name=context.active_object.name)

        scroll = self.base_controls.scroll
        if scroll:
            grid.alter_grid(u=grid.u + scroll, v=grid.v + scroll)

        # point = grid.grid_point(context, event)
        # if point:
        #     self.point = point

        # Events
        if event.type == 'R' and event.value == 'PRESS':
            data = grid.to_object_bounds(context, context.active_object.name)
            self.border_points  = data['border']
            self.u_lines = data['u_lines']
            self.v_lines = data['v_lines']

        self.grid_controller.update(context, event)


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
        self.grid_controller.draw_2d(context)
        self.form.draw()

        if self.point:
            built_in_shader = 'UNIFORM_COLOR' if bpy.app.version[0] >= 4 else '2D_UNIFORM_COLOR'
            shader = gpu.shader.from_builtin(built_in_shader)
            batch = batch_for_shader(shader, 'POINTS', {'pos': [self.point]})
            shader.bind()
            shader.uniform_float('color', (1,0,0,1))
            gpu.state.blend_set('ALPHA')
            gpu.state.point_size_set(6)
            batch.draw(shader)


    def safe_draw_3D(self, context):
        method_handler(self.draw_shader_3D,
            arguments = (context,),
            identifier = 'Modal Shader 3D',
            exit_method = self.remove_shaders)


    def draw_shader_3D(self, context):
        self.grid_controller.draw_3d(context)

        built_in_shader = 'UNIFORM_COLOR' if bpy.app.version[0] >=4 else '3D_UNIFORM_COLOR'
        shader = gpu.shader.from_builtin(built_in_shader)

        if self.border_points:
            batch = batch_for_shader(shader, 'POINTS', {'pos': self.border_points})
            shader.bind()
            shader.uniform_float('color', (1,0,0,1))
            gpu.state.blend_set('ALPHA')
            gpu.state.point_size_set(6)
            batch.draw(shader)


        for line in self.u_lines:
            batch = batch_for_shader(shader, 'LINES', {'pos': line})
            shader.bind()
            shader.uniform_float('color', (0,1,0,1))
            # Lines
            #Enable(GL_LINE_SMOOTH)
            gpu.state.blend_set('ALPHA')
            gpu.state.line_width_set(1)
            batch.draw(shader)

        for line in self.v_lines:
            batch = batch_for_shader(shader, 'LINES', {'pos': line})
            shader.bind()
            shader.uniform_float('color', (0,0,1,1))
            # Lines
            #Enable(GL_LINE_SMOOTH)
            gpu.state.blend_set('ALPHA')
            gpu.state.line_width_set(1)
            batch.draw(shader)