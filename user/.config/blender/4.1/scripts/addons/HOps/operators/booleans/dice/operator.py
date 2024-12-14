import bpy, bmesh
from .... ui_framework.master import Master
from .... utility.base_modal_controls import Base_Modal_Controls
from .... utils.toggle_view3d_panels import collapse_3D_view_panels
from .... utils.modal_frame_drawing import draw_modal_frame
from .... utility import method_handler

from . import Mode
from . dice_3d import Edit_3D
from . dice_2d import Edit_2D
from . dice_line import Edit_Line
from . shader import SD
from . interface import draw_FAS, setup_form, alter_form_layout
from . struct import get_boxelize_ref

DESC = """Dice Cut

LMB - Dice on last used axes
Shift + LMB - Dice active from selection
Ctrl + LMB - Dice on all axes
Alt + LMB - Smart Apply Dice (applies select modifiers)

Press H for help"""


class HOPS_OT_BoolDice_V2(bpy.types.Operator):
    bl_idname = "hops.bool_dice_v2"
    bl_label = "Dice V2"
    bl_options = {'REGISTER', 'UNDO', 'BLOCKING'}
    bl_description = DESC

    dice_axis: bpy.props.EnumProperty(
        name="Dice Axis Memory",
        description="Axis for dice to start on",
        items=[
            ("X", "X", ""),
            ("Y", "Y", ""),
            ("Z", "Z", "")],
        default='X')

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'MESH' and obj.mode in {'OBJECT', 'EDIT'}


    def invoke(self, context, event):

        # Bad Selection
        obj = context.active_object
        if context.active_object.mode == 'EDIT':
            bm = bmesh.from_edit_mesh(obj.data)
            if len([v for v in bm.verts if v.select]) < 2:
                bpy.ops.hops.display_notification(info="Select More Geo")
                return {'CANCELLED'}

        if context.active_object.mode == 'EDIT':
            obj.update_from_editmode()

        # States
        self.edit_mode = Mode.DICE_3D
        self.show_wire = obj.show_wire
        
        # Editors
        self.dice_3d = Edit_3D(self, context, event)
        self.dice_2d = Edit_2D(self, context, event)
        self.dice_line = Edit_Line(self, context, event)

        # Setup
        if self.edit_mode == Mode.DICE_3D:
            if not self.dice_3d.setup(context, event):
                bpy.ops.hops.display_notification(info="Invalid Selection")
                return {'CANCELLED'}

        # Ctrl entry
        if event.ctrl:
            get_boxelize_ref().active = True

        # Form
        self.form_exit = False
        self.form = None
        setup_form(self, context, event)

        # Base Systems
        self.master = Master(context)
        self.master.only_use_fast_ui = True
        self.base_controls = Base_Modal_Controls(context, event)
        self.original_tool_shelf, self.original_n_panel = collapse_3D_view_panels()
        self.draw_handle_2d = bpy.types.SpaceView3D.draw_handler_add(self.safe_draw_2d, (context,), 'WINDOW', 'POST_PIXEL')

        # Graphics Modal
        if self.edit_mode == Mode.DICE_3D:
            SD.pause_drawing = False
        elif self.edit_mode == Mode.DICE_2D:
            SD.pause_drawing = True

        if SD.draw_modal_running == False: 
            bpy.ops.hops.draw_dice_v2('INVOKE_DEFAULT')
        else:
            SD.reset_modal = True
        SD.dice_modal_running = True
        SD.reset_data()
        SD.see_though = False

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


    def modal(self, context, event):

        # Base System
        self.master.receive_event(event)
        self.base_controls.update(context, event)
        self.form.update(context, event)

        # Form Exit
        if self.form_exit:
            return self.confirm_exit(context, event)

        # Navigation
        if self.base_controls.pass_through:
            if not self.form.active():
                return {'PASS_THROUGH'}

        # Allow wire / wire shaded
        elif event.type == 'Z' and (event.shift or event.alt):
            if not self.form.active():
                return {'PASS_THROUGH'}

        # Confirm
        elif self.base_controls.confirm:
            if not self.form.active():
                # Line dice uses Left Mouse
                if self.edit_mode == Mode.DICE_LINE:
                    if event.type != 'LEFTMOUSE':
                        return self.confirm_exit(context, event)
                # Regular Cases
                else:
                    return self.confirm_exit(context, event)

        # Cancel
        elif self.base_controls.cancel:
            return self.cancel_exit(context)

        # Form Toggle
        elif event.type == 'TAB' and event.value == 'PRESS':
            if self.form.is_dot_open():
                self.form.close_dot()
            else:
                self.form.open_dot()

        # Mode Switch
        if not self.form.active():
            if event.type == 'V' and event.value == 'PRESS':
                if self.edit_mode == Mode.DICE_3D:
                    self.edit_mode = Mode.DICE_2D
                elif self.edit_mode == Mode.DICE_2D:
                    self.edit_mode = Mode.DICE_LINE
                elif self.edit_mode == Mode.DICE_LINE:
                    self.edit_mode = Mode.DICE_3D
                self.mode_manager()

        # Zoom
        if self.edit_mode in {Mode.DICE_3D, Mode.DICE_LINE}:
            if self.form.is_dot_open():
                if not self.form.active():
                    if event.type in {"WHEELUPMOUSE", "WHEELDOWNMOUSE"} and event.value == 'PRESS':
                        return {'PASS_THROUGH'}

        # Views
        if self.edit_mode in {Mode.DICE_2D, Mode.DICE_LINE}:
            if not self.form.active():
                if event.type in {'NUMPAD_2', 'NUMPAD_4', 'NUMPAD_6', 'NUMPAD_8', 'NUMPAD_1', 'NUMPAD_3', 'NUMPAD_5', 'NUMPAD_7', 'NUMPAD_9'} and event.value == 'PRESS':
                    return {'PASS_THROUGH'}

        if event.type == 'W' and event.value == 'PRESS':
            self.set_wire_frame(context, toggle=True)

        # Updates
        if self.edit_mode == Mode.DICE_3D:
            self.dice_3d.update(self, context, event)

        elif self.edit_mode == Mode.DICE_2D:
            if event.type != 'TIMER':
                self.dice_2d.update(self, context, event)

        elif self.edit_mode == Mode.DICE_LINE:
            if event.type != 'TIMER':
                self.dice_line.update(self, context, event)


        draw_FAS(self, context)
        context.area.tag_redraw()
        return {'RUNNING_MODAL'}

    # --- EXITS --- #

    def common_exit(self, context):
        self.set_wire_frame(context, value=self.show_wire)
        SD.dice_modal_running = False
        self.remove_shader()
        self.form.shut_down(context)
        self.master.run_fade()
        collapse_3D_view_panels(self.original_tool_shelf, self.original_n_panel)


    def confirm_exit(self, context, event):
        self.common_exit(context)
        
        if self.edit_mode == Mode.DICE_3D:
            self.dice_3d.confirm_exit(context, event)
        
        elif self.edit_mode == Mode.DICE_2D:
            self.dice_2d.confirm_exit(context, event)
        
        self.dice_line.confirm_exit(context)

        self.report({'INFO'}, "Finished")
        return {'FINISHED'}


    def cancel_exit(self, context):
        self.common_exit(context)

        if self.edit_mode == Mode.DICE_3D:
            self.dice_3d.cancel_exit(context)

        elif self.edit_mode == Mode.DICE_2D:
            self.dice_2d.cancel_exit(context)

        self.dice_line.cancel_exit(context)

        self.report({'INFO'}, "Cancelled")
        return {'CANCELLED'}

    # --- UTILS --- #

    def mode_manager(self):

        if self.edit_mode == Mode.DICE_2D:
            SD.pause_drawing = True
            alter_form_layout(self, preset_label='2D_DICE')

        elif self.edit_mode == Mode.DICE_3D:
            SD.pause_drawing = False
            alter_form_layout(self, preset_label='3D_DICE')
        
        elif self.edit_mode == Mode.DICE_LINE:
            SD.pause_drawing = True
            alter_form_layout(self, preset_label='LINE_DICE')


    def set_wire_frame(self, context, value=True, toggle=False):
        if context.active_object:
            obj = context.active_object
            if toggle:
                obj.show_wire = not obj.show_wire
            else:
                obj.show_wire = value

    # --- FORM --- #

    def exit_button(self, use_twist=False):
        self.form_exit = True
        self.dice_3d.exit_to_twist = use_twist


    def switch_edit_modes(self, opt=''):
        if opt == '2D':
            self.edit_mode = Mode.DICE_2D
        elif opt == '3D':
            self.edit_mode = Mode.DICE_3D
        elif opt == 'LINE':
            self.edit_mode = Mode.DICE_LINE
        self.mode_manager()


    def edit_modes_hook(self):
        if self.edit_mode == Mode.DICE_2D:
            return '2D'
        elif self.edit_mode == Mode.DICE_3D:
            return '3D'
        elif self.edit_mode == Mode.DICE_LINE:
            return 'LINE'
        return '3D'

    # --- SHADER --- #

    def remove_shader(self):
        if self.draw_handle_2d:
            self.draw_handle_2d = bpy.types.SpaceView3D.draw_handler_remove(self.draw_handle_2d, "WINDOW")


    def safe_draw_2d(self, context):
        method_handler(self.draw_shader_2d,
            arguments = (context,),
            identifier = 'Dice 2D Shader',
            exit_method = self.remove_shader)


    def draw_shader_2d(self, context):
        self.form.draw()

        if self.edit_mode == Mode.DICE_3D:
            if not self.form.is_dot_open():
                draw_modal_frame(context)

        elif self.edit_mode == Mode.DICE_2D:
            self.dice_2d.draw_2d(context)
        
        elif self.edit_mode == Mode.DICE_LINE:
            self.dice_line.draw_2d(context)
