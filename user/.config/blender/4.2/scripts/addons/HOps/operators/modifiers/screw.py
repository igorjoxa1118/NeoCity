import bpy, math
from enum import Enum
from ... utility import addon
from ... utility import modifier
from ... utility.base_modal_controls import Base_Modal_Controls
from ... ui_framework.master import Master
from ... ui_framework.utils.mods_list import get_mods_list
from ... utils.mod_controller import Mod_Controller
from ... ui_framework import form_ui as form
from ... utils.toggle_view3d_panels import collapse_3D_view_panels
from ... utils.modal_frame_drawing import draw_modal_frame
from ... utils.cursor_warp import mouse_warp
from ... utility import method_handler


class Mode(Enum):
    SEGMENT   = 0
    ANGLE     = 1
    SCREW     = 2
    ITERATION = 3


DESC = """LMB - Adjust Screw Modifier
LMB + CTRL - Add New Screw Modifier

Press H for help
"""


class HOPS_OT_MOD_Screw(bpy.types.Operator):
    bl_idname = "hops.mod_screw"
    bl_label = "Adjust Screw Modifier"
    bl_options = {"REGISTER", "UNDO", "BLOCKING"}
    bl_description = DESC

    screw_objects = {}

    axis: bpy.props.EnumProperty(
        name="Axis",
        description="What axis screw / spin",
        items=[
            ('X', "X", "Screw X axis"),
            ('Y', "Y", "Screw Y axis"),
            ('Z', "Z", "Screw Z axis")],
        default='X')

    @classmethod
    def poll(cls, context):
        return any(o.type == 'MESH' for o in context.selected_objects)

    @property
    def segment(self):
        for mod in self.mod_controller.active_modifiers():
            return int(mod.steps)

    @segment.setter
    def segment(self, val):
        for mod in self.mod_controller.active_modifiers():
            mod.steps = int(val)

    @property
    def angle(self):
        for mod in self.mod_controller.active_modifiers():
            return round(math.degrees(mod.angle), 2)

    @angle.setter
    def angle(self, val):
        for mod in self.mod_controller.active_modifiers():
            mod.angle = math.radians(val)

    @property
    def screw(self):
        for mod in self.mod_controller.active_modifiers():
            return round(mod.screw_offset, 2)

    @screw.setter
    def screw(self, val):
        for mod in self.mod_controller.active_modifiers():
            mod.screw_offset = val

    @property
    def iteration(self):
        for mod in self.mod_controller.active_modifiers():
            return int(mod.iterations)

    @iteration.setter
    def iteration(self, val):
        for mod in self.mod_controller.active_modifiers():
            mod.iterations = int(val)


    def invoke(self, context, event):

        # Setup
        self.setup(context, event)

        # Form
        self.form_exit = False
        self.index_button = None
        self.form = None
        self.setup_form(context, event)

        # Base Systems
        self.master = Master(context=context)
        self.master.only_use_fast_ui = True
        self.base_controls = Base_Modal_Controls(context, event)
        self.original_tool_shelf, self.original_n_panel = collapse_3D_view_panels()
        self.draw_handle = bpy.types.SpaceView3D.draw_handler_add(self.safe_draw_shader, (context,), 'WINDOW', 'POST_PIXEL')

        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}


    def modal(self, context, event):

        # --- Base Systems --- #
        self.master.receive_event(event=event)
        self.base_controls.update(context, event)
        self.form.update(context, event)
        if not self.form.is_dot_open():
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

        # --- Form --- #
        if self.form_exit:
            return self.confirm_exit(context)

        self.index_button.text = str(self.mod_controller.active_obj_mod_index() + 1)

        if event.type == 'TAB' and event.value == 'PRESS':
            if self.form.is_dot_open(): 
                self.form.close_dot()
            else:
                self.form.open_dot()

        # --- Actions --- #
        if not self.form.active():
            self.actions(context, event)

        # --- Interface --- #
        self.view3d_header(context)
        self.setup_FAS(context)
        
        context.area.tag_redraw()
        return {"RUNNING_MODAL"}

    # --- ACTIONS --- #

    def actions(self, context, event):

        # --- Keys --- #
        if event.type == "ONE" and event.value == "PRESS":
            self.preset_screw_12_steps()

        elif event.type == "TWO" and event.value == "PRESS":
            self.preset_screw_36_steps()

        elif event.type == "THREE" and event.value == "PRESS":
            self.preset_extrude_mode()

        elif event.type == "A" and event.value == "PRESS":
            self.mode = Mode.ANGLE

        elif event.type == "E" and event.value == "PRESS":
            self.mode = Mode.ITERATION

        elif event.type == "S" and event.value == "PRESS":
            if event.shift: self.mode = Mode.SEGMENT
            else: self.mode = Mode.SCREW

        elif event.type == 'V' and event.value == 'PRESS':
            if event.shift: self.add_remove_screw(add=False)
            else: self.add_remove_screw(add=True)

        elif event.type == "F" and event.value == "PRESS":
            self.flip_normals()

        elif event.type == 'X' and event.value == 'PRESS':
            self.cycle_axis()

        elif event.type == "Y" and event.value == "PRESS":
            self.set_axis_y()

        elif event.type == "Z" and event.value == "PRESS" and not event.shift:
            self.set_axis_z()

        elif event.type == "M" and event.value == "PRESS" and event.shift:
            self.toggle_merge_verts()

        elif event.type == "C" and event.value == "PRESS":
            self.toggle_use_normals_calc()

        elif event.type == "N" and event.value == "PRESS":
            self.toggle_use_smooth_shade()

        elif event.type == "Q" and event.value == "PRESS":
            self.mod_controller.move_mod(context, up=True)

        elif event.type == "W" and event.value == "PRESS":
            self.mod_controller.move_mod(context, up=False)

        elif event.type == "Z" and event.value == "PRESS" and event.shift:
            self.toggle_show_face_orientation()

        # Mouse Paused
        if self.form.is_dot_open(): return

        # --- Modes --- #
        if self.mode == Mode.SEGMENT:
            self.segment_adjust(context, event)
        elif self.mode == Mode.ANGLE:
            self.angle_adjust(context, event)
        elif self.mode == Mode.SCREW:
            self.screw_adjust(context, event)
        elif self.mode == Mode.ITERATION:
            self.iteration_adjust(context, event)

        # --- Scroll --- #
        self.scroll_adjust(context, event)


    def segment_adjust(self, context, event):
        for mod in self.mod_controller.active_modifiers():
            self.snap_buffer += self.base_controls.mouse
            if abs(self.snap_buffer) > self.snap_break:
                increment = 1
                mod.steps += int(math.copysign(increment, self.snap_buffer))
                mod.steps = snap(mod.steps, increment)
                self.snap_buffer = 0


    def angle_adjust(self, context, event):
        for mod in self.mod_controller.active_modifiers():
            if event.shift:
                mod.angle += self.base_controls.mouse
            else:
                self.snap_buffer += self.base_controls.mouse
                increment = math.radians(5) if event.ctrl else math.radians(45)
                if abs(self.snap_buffer) > self.snap_break:
                    mod.angle += math.copysign(increment , self.snap_buffer)
                    mod.angle = snap(mod.angle, increment)
                    self.snap_buffer = 0


    def screw_adjust(self, context, event):
        for mod in self.mod_controller.active_modifiers():
            self.snap_buffer += self.base_controls.mouse
            if abs(self.snap_buffer) > self.snap_break:
                if event.shift: increment = 0.01
                elif event.ctrl: increment = 1
                else: increment = 0.1
                mod.screw_offset += math.copysign(increment, self.snap_buffer)
                mod.screw_offset = snap(mod.screw_offset, increment)
                self.snap_buffer = 0


    def iteration_adjust(self, context, event):
        for mod in self.mod_controller.active_modifiers():
            self.snap_buffer += self.base_controls.mouse
            if abs(self.snap_buffer) > self.snap_break:
                mod.iterations += int(math.copysign(1, self.snap_buffer))
                self.snap_buffer = 0


    def preset_screw_12_steps(self):
        for mod in self.mod_controller.active_modifiers():
            mod.angle = math.radians(360)
            mod.steps = 12
            mod.render_steps = 12
            mod.screw_offset = 0
            mod.use_merge_vertices = True
            mod.use_smooth_shade = True
            mod.use_normal_calculate = True
            if addon.preference().ui.Hops_extra_info:
                bpy.ops.hops.display_notification(info=f'Screw - 12 Steps' )


    def preset_screw_36_steps(self):
        for mod in self.mod_controller.active_modifiers():
            mod.angle = math.radians(360)
            mod.steps = 36
            mod.render_steps = 36
            mod.screw_offset = 0
            mod.use_merge_vertices = True
            mod.use_smooth_shade = True
            mod.use_normal_calculate = False
            if addon.preference().ui.Hops_extra_info:
                bpy.ops.hops.display_notification(info=f'Screw - 36 Steps' )


    def preset_extrude_mode(self):
        for mod in self.mod_controller.active_modifiers():
            mod.angle = math.radians(0)
            mod.steps = 2
            mod.render_steps = 2
            mod.screw_offset = 2.3
            mod.use_merge_vertices = True
            mod.use_smooth_shade = True
            mod.use_normal_calculate = False
            mod.axis = 'Z'
            if addon.preference().ui.Hops_extra_info:
                bpy.ops.hops.display_notification(info=f'Extrude Mode' )


    def scroll_adjust(self, context, event):
        scroll = self.base_controls.scroll 
        if not scroll: return

        if event.shift:
            if scroll > 0:
                self.mod_controller.move_mod(context, up=True)
            elif scroll < 0:
                self.mod_controller.move_mod(context, up=False)
        else:
            for mod in self.mod_controller.active_modifiers():
                mod.iterations += scroll


    def flip_normals(self):
        for mod in self.mod_controller.active_modifiers():
            mod.use_normal_flip = not mod.use_normal_flip


    def cycle_axis(self):
        self.axis = "YZX"["XYZ".find(self.axis)]
        self.report({'INFO'}, f"Screw Axis: {self.axis}")
        for mod in self.mod_controller.active_modifiers():
            mod.axis = self.axis


    def set_axis_y(self):
        for mod in self.mod_controller.active_modifiers():
            mod.axis = "Y"


    def set_axis_z(self):
        for mod in self.mod_controller.active_modifiers():
            mod.axis = "Z"


    def toggle_merge_verts(self):
        use_verts = None
        for mod in self.mod_controller.active_modifiers():
            mod.use_merge_vertices = not mod.use_merge_vertices
            use_verts = mod.use_merge_vertices if not use_verts else None

        if addon.preference().ui.Hops_extra_info:
            bpy.ops.hops.display_notification(info=f'Merge Verts {use_verts}')


    def toggle_use_normals_calc(self):
        for mod in self.mod_controller.active_modifiers():
            mod.use_normal_calculate = not mod.use_normal_calculate


    def toggle_use_smooth_shade(self):

        smooth_enabled = False

        for mod in self.mod_controller.active_modifiers():
            mod.use_smooth_shade = not mod.use_smooth_shade

            if mod.use_smooth_shade:
                smooth_enabled = True

        if smooth_enabled:
            addon.preference().modifier.screw_normals = True
            if addon.preference().ui.Hops_extra_info:
                bpy.ops.hops.display_notification(info="Smoothing : On")
        else:
            addon.preference().modifier.screw_normals = False
            if addon.preference().ui.Hops_extra_info:
                bpy.ops.hops.display_notification(info="Smoothing : Off")


    def toggle_show_face_orientation(self):
        overlay = bpy.context.space_data.overlay
        overlay.show_face_orientation = not overlay.show_face_orientation


    def add_remove_screw(self, add=True):
        if add: self.mod_controller.create_new_mod(count_limit=4)
        else: self.mod_controller.remove_active_mod(use_logical_delete=True, remove_if_created=True)


    def set_axis(self, opt=''):
        if opt not in {'X', 'Y', 'Z'}: return
        self.axis = opt
        for mod in self.mod_controller.active_modifiers():
            mod.axis = self.axis


    def axis_hook(self):
        return str(self.axis)

    # --- SETUP --- #

    def setup(self, context, event):
        
        # State
        self.mode = Mode.SCREW

        # Mods
        objs = [o for o in context.selected_objects if o.type == 'MESH']
        type_map = {bpy.types.Mesh : 'SCREW'}
        self.mod_controller = Mod_Controller(context, objs, type_map, create_new=event.ctrl, active_obj=context.active_object)

        self.mod_controller.sort_mods(sort_types=['WEIGHTED_NORMAL'])

        for mod in self.mod_controller.all_created_mods():
            mod.angle = math.radians(360)
            mod.axis = 'Y'
            mod.steps = 36
            mod.render_steps = 36
            mod.screw_offset = 0
            mod.iterations = 1
            mod.use_smooth_shade = True
            mod.use_merge_vertices = True

        # Snaps
        self.snap_buffer = 0
        self.snap_break = 0.05
        
        bpy.context.space_data.overlay.show_face_orientation = True
        bpy.types.ThemeView3D.face_front = [.6,1,1,0]

        mod = self.mod_controller.active_object_mod()
        if mod: self.axis = mod.axis

    # --- EXIT --- #

    def cancel_exit(self, context):
        self.shut_down(context)
        self.mod_controller.cancel_exit()
        return {'CANCELLED'} 


    def confirm_exit(self, context):
        self.shut_down(context)
        self.mod_controller.confirm_exit()
        return {'FINISHED'}


    def shut_down(self, context):
        context.area.header_text_set(text=None)
        bpy.context.space_data.overlay.show_face_orientation = False
        self.remove_shader()
        collapse_3D_view_panels(self.original_tool_shelf, self.original_n_panel)
        self.master.run_fade()

    # --- INTERFACE --- #

    def view3d_header(self, context):
        mod = self.mod_controller.active_object_mod()
        if not mod: return
        context.area.header_text_set("Hardops Screw:     N : Smooth - {}     M : Merge - {}     X/Y/Z : AxiS - {}     F : Flip - {}      C : Calculate - {}".format(
            mod.use_smooth_shade, mod.use_merge_vertices, mod.axis, mod.use_normal_flip, mod.use_normal_calculate))


    def setup_FAS(self, context):
        self.master.setup()
        obj_data = self.mod_controller.active_object_mod(as_obj_data=True)
        mod = obj_data.active_mod()
        obj = obj_data.obj

        if self.master.should_build_fast_ui():
            # Main
            win_list = []
            if addon.preference().ui.Hops_modal_fast_ui_loc_options != 1: # Fast Floating
                win_list.append(mod.steps)
                win_list.append("{:.0f}".format(math.degrees(mod.angle))+ "°")
                win_list.append("{}".format(round(mod.screw_offset, 4)))
                win_list.append("{}".format(mod.iterations))
            else:
                win_list.append("Screw")
                win_list.append("Steps: {}".format(mod.steps))
                win_list.append("Angle: {:.1f}".format(math.degrees(mod.angle))+ "°")
                win_list.append("Screw: {}".format(round(mod.screw_offset, 4)))
                win_list.append("It: {}".format(mod.iterations))
                win_list.append("[F] Flip")

            # Help
            help_items = {"GLOBAL" : [], "STANDARD" : []}

            help_items["GLOBAL"] = [
                ("M", "Toggle mods list"),
                ("H", "Toggle help"),
                ("~", "Toggle UI Display Type"),
                ("O", "Toggle viewport rendering")]

            help_items["STANDARD"] = [
                ("Move",      "Steps"),
                ("A",         "Angle"),
                ("E",         "Iterations"),
                ("S",         "Steps"),
                ("S + Shift", "Segments"),
                ("C",         "Use normal calculate"),
                ("WHEEL",     "Change axis"),
                ("M + Shift", "Merge vertices"),
                ("N",         "Smooth shading"),
                ("V + Shift", "Remove current Screw"),
                ("V",         "Add new Screw"),
                ("Q",         "Move mod DOWN"),
                ("W",         "Move mod UP"),
                ("Shift + Scroll", "Move mod up/down"),
                ("N",         "Smooth shading"),
                ("F",         "Use normal flip"),
                ("Shift + Z", "Toggle Visual Orientation"),
                ("X",         "Change Axis"),
                ("Y",         "Set Axis to Y"),
                ("Z",         "Set Axis to Z"),
                ("3",         "Preset 3: Extrude"),
                ("2",         "Preset 2: 36 Steps"),
                ("1",         "Preset 1: 12 Steps"),
                ("TAB",       "Open Dot UI"),
                (" ",         "Red means normals are flipped.")]

            # Mods
            active_mod = mod.name
            mods_list = get_mods_list(mods=obj.modifiers)

            self.master.receive_fast_ui(win_list=win_list, help_list=help_items, image="Twist", mods_list=mods_list, active_mod_name=active_mod)
        self.master.finished()


    def setup_form(self, context, event):
        self.form = form.Form(context, event, dot_open=False)

        def spacer(height=10):
            row = self.form.row()
            row.add_element(form.Spacer(height=height))
            self.form.row_insert(row)

        # TOTAL WIDTH : 135

        row = self.form.row()
        row.add_element(form.Label(text="Screw", width=60))
        row.add_element(form.Spacer(width=15))

        tip = ["Scroll / Click : Active Screw to effect", "Ctrl Click : Add new Screw", "Shift Ctrl Click : Remove current Screw"]
        self.index_button = form.Button(
            text="0", width=20, tips=tip,
            callback=self.mod_controller.clamped_next_mod_index, pos_args=(True,), neg_args=(False,),
            ctrl_callback=self.add_remove_screw, ctrl_args=(True,),
            shift_ctrl_callback=self.add_remove_screw, shift_ctrl_args=(False,))
        row.add_element(self.index_button)

        row.add_element(form.Spacer(width=15))
        row.add_element(form.Button(text="✓", width=25, tips=["Finalize and Exit"], callback=self.form_exit_trigger))
        self.form.row_insert(row)

        spacer()

        row = self.form.row()
        row.add_element(form.Label(text='SEGMENT', width=75))
        row.add_element(form.Input(obj=self, attr="segment", width=60, increment=1))
        self.form.row_insert(row)

        row = self.form.row()
        row.add_element(form.Label(text='ANGLE', width=75))
        row.add_element(form.Input(obj=self, attr="angle", width=60, increment=1))
        self.form.row_insert(row)

        row = self.form.row()
        row.add_element(form.Label(text='SCREW', width=75))
        row.add_element(form.Input(obj=self, attr="screw", width=60, increment=.1))
        self.form.row_insert(row)

        row = self.form.row()
        row.add_element(form.Label(text='ITERATION', width=75))
        row.add_element(form.Input(obj=self, attr="iteration", width=60, increment=1))
        self.form.row_insert(row)

        spacer()

        row = self.form.row()
        row.add_element(form.Spacer(width=3))
        row.add_element(form.Button(text="F", width=20, tips=["Click : Show face oreintation", "Shift Click : Shade Smooth"], callback=self.form_face_settings, pos_args=(False,), neg_args=(True,)))
        row.add_element(form.Spacer(width=5))
        row.add_element(form.Button(text="N", width=20, tips=["Click : Flip Normals", "Shift Click : Use Normals Calc"], callback=self.form_normals, pos_args=(True,), neg_args=(False,), scroll_enabled=False))
        row.add_element(form.Spacer(width=5))
        row.add_element(form.Button(text="M", width=20, tips=["Merge Verts"], callback=self.toggle_merge_verts))
        row.add_element(form.Spacer(width=5))
        row.add_element(form.Button(text="U", width=20, tips=["Click / Scroll", "Move modifier up", "Shift : Move modifier down"],
            callback=self.mod_controller.move_mod, shift_text="D", pos_args=(context, True), neg_args=(context, False)))
        row.add_element(form.Spacer(width=5))
        row.add_element(form.Dropdown(width=30, options=['X', 'Y', 'Z'], tips=["Active Axis"], callback=self.set_axis, update_hook=self.axis_hook))
        self.form.row_insert(row)

        self.form.build()

    # --- FORM FUNCS --- #

    def form_exit_trigger(self):
        self.form_exit = True


    def form_normals(self, use_flip=True):
        if use_flip: self.flip_normals()
        else: self.toggle_use_normals_calc()


    def form_face_settings(self, shade_smooth=True):
        if shade_smooth: self.toggle_use_smooth_shade()
        else: self.toggle_show_face_orientation()


    # --- SHADERS --- #

    def safe_draw_shader(self, context):
        method_handler(self.draw_shader,
            arguments = (context,),
            identifier = 'UI Framework',
            exit_method = self.remove_shader)


    def remove_shader(self):
        if self.draw_handle:
            self.draw_handle = bpy.types.SpaceView3D.draw_handler_remove(self.draw_handle, "WINDOW")


    def draw_shader(self, context):
        draw_modal_frame(context)
        self.form.draw()


def snap(value, increment):
    result = round (value/increment) * increment
    return result
