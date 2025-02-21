import bpy
from mathutils import Matrix, Vector
from ...utility import math as hops_math
from ... utility import addon
from ... ui_framework.master import Master
from ... ui_framework import form_ui as form
from ... ui_framework.utils.mods_list import get_mods_list
from ... ui_framework.graphics.draw import render_text, render_quad, draw_border_lines, render_image, draw_2D_lines
from ... ui_framework.graphics.load import load_image_file
from ... ui_framework.utils.geo import get_blf_text_dims
from ... ui_framework.utils.checks import is_mouse_in_quad
from ...utility.screen import dpi_factor
from ... utility.base_modal_controls import Base_Modal_Controls
from ... utils.toggle_view3d_panels import collapse_3D_view_panels
from ... utils.modal_frame_drawing import draw_modal_frame
from ... utils.cursor_warp import mouse_warp
from ... utility import method_handler


class HOPS_OT_AdjustClothOperator(bpy.types.Operator):
    bl_idname = "hops.adjust_cloth"
    bl_label = "Adjust Cloth"
    bl_options = {'REGISTER', 'UNDO', 'BLOCKING'}
    bl_description = """Placeholder"""

    numpad_map = {
        'NUMPAD_0' : 'ZERO' ,
        'NUMPAD_1' : 'ONE'  ,
        'NUMPAD_2' : 'TWO'  ,
        'NUMPAD_3' : 'THREE',
        'NUMPAD_4' : 'FOUR' ,
        'NUMPAD_5' : 'FIVE'}

    shrink_presets = {
        'ZERO' : 0 ,
        'ONE'  : -0.1,
        'TWO'  : -0.3,
        'THREE': -1.5,
        'FOUR' : -2.0,
        'FIVE' : -5.0}

    pressure_presets = {
        'ZERO' : 0,
        'ONE'  : 1,
        'TWO'  : 2,
        'THREE': 5,
        'FOUR' : 10,
        'FIVE' : 15}

    operator = None
    popover_active = False
    apply_mods_on_exit: bpy.props.BoolProperty(name='Apply Mods', description="Apply Modifiers on exit")
    auto_restart: bpy.props.BoolProperty(name='Auto Refresh', description="Refresh timeline on paremeter change")

    @classmethod
    def poll(cls, context):
        return context.selected_objects


    def invoke(self, context, event):
        self.__class__.operator = self
        self.auto_restart = False
        self.b_popup = addon.preference().property.in_tool_popup_style == 'BLENDER'

        self.param_names = {
            'uniform_pressure_force' : 'Pressure',
            'shrink_min' :  'Shrinking Factor',
            'time_scale' : 'Speed Multiplier'}

        self.params = list(self.param_names.keys())
        self.active_param = self.params[0]
        self.numbers = set()

        self.numbers.update(self.numpad_map.keys())
        self.numbers.update(self.numpad_map.values())

        self.cloth_mods = []
        self.cloth_back = []
        self.active_mod = None

        for obj in context.selected_objects:
            mod = self.get_cloth(obj)
            if mod:
                self.cloth_mods.append((mod, obj))

        if not self.cloth_mods:
            self.report({'INFO'}, "No Cloth modifiiers to adjust")
            return {'CANCELLED'}

        if not self.active_mod:
            self.active_mod = self.cloth_mods[0][0]

        for item in self.cloth_mods:
            mod = item[0]
            self.cloth_back.append([ getattr(mod.settings, name) for name in self.params])


        def check_type(obj):
            if type(obj) == bpy.types.Object:
                if type(obj.data) == bpy.types.Mesh:
                    return True
            return False

        self.active_obj = context.active_object if check_type(context.active_object) else None
        if self.active_obj == None:
            for obj in context.selected_objects:
                if check_type(obj):
                    self.active_obj = obj
                    break

        # Widget : Form
        self.__pressure = self.active_mod.settings.uniform_pressure_force
        self.__shrink   = self.active_mod.settings.shrink_min
        self.__timespan = self.active_mod.settings.time_scale
        self.__gravity  = self.active_mod.settings.effector_weights.gravity
        self.auto_restart = False
        self.apply_mods_on_exit = False
        self.form_exit = False
        self.form = None
        self.setup_form(context, event)
        # UI Props
        self.confirmed_exit = False
        # States
        self.frozen = True
        # Base Systems
        self.master = Master(context=context)
        self.master.only_use_fast_ui = True
        self.base_controls = Base_Modal_Controls(context, event)
        self.original_tool_shelf, self.original_n_panel = collapse_3D_view_panels()

        context.window_manager.modal_handler_add(self)

        if not self.b_popup:
            self.draw_handle = bpy.types.SpaceView3D.draw_handler_add(self.safe_draw_shader, (context,), 'WINDOW', 'POST_PIXEL')
        else:
            self.draw_handle = None
            bpy.ops.hops.adjust_cloth_popup("INVOKE_DEFAULT")

        return {'RUNNING_MODAL'}

    @property
    def pressure(self):
        return round(self.__pressure, 4)

    @pressure.setter
    def pressure(self, val):
        self.set_params('uniform_pressure_force', val)
        self.__pressure = val

    @property
    def shrink(self):
        return round(self.__shrink, 4)

    @shrink.setter
    def shrink(self, val):
        self.set_params('shrink_min', val)
        self.__shrink = val

    @property
    def timespan(self):
        return round(self.__timespan, 4)

    @timespan.setter
    def timespan(self, val):
        self.set_params('time_scale', val)
        self.__timespan = val

    @property
    def gravity(self):
        return round(self.__gravity, 4)

    @gravity.setter
    def gravity(self, val):
        self.set_params('gravity', val)
        self.__gravity = val


    def modal(self, context, event):

        # Base Systems
        self.master.receive_event(event=event)
        self.base_controls.update(context, event)
        if not self.frozen:
            mouse_warp(context, event)

        if self.popover_active:
            self.draw_ui(context)
            context.area.tag_redraw()
            return {'RUNNING_MODAL'}

        if not self.b_popup:
            self.form.update(context, event)

        # Pass
        if self.base_controls.pass_through:
            return {'PASS_THROUGH'}


        # Confirm Exit
        if self.form_exit:
            return self.confirm_exit()

        # Confirm Exit
        if not self.form.active():
            apply_exit = True if event.ctrl and event.type == 'SPACE' and event.value == 'PRESS' else False
            if self.base_controls.confirm or apply_exit:
                if not event.shift:
                    if apply_exit: self.apply_mods()
                    return self.confirm_exit()

        # Cancel Exit
        if self.base_controls.cancel:
            self.__class__.operator = None
            self.remove_shader()
            collapse_3D_view_panels(self.original_tool_shelf, self.original_n_panel)
            self.master.run_fade()

            # Stop the animation
            if bpy.context.screen.is_animation_playing:
                bpy.ops.screen.animation_play()

            # Revert mods
            for item, back in zip(self.cloth_mods, self.cloth_back):
                for name, val in zip(self.param_names.keys(), back):
                    mod = item[0]
                    setattr(mod.settings, name, val)
            return {'CANCELLED'}

        # Actions
        if not self.form.active():
            self.actions(context, event)

        self.draw_ui(context)
        context.area.tag_redraw()
        return {'RUNNING_MODAL'}


    def actions(self, context, event):

        # Non frozen state
        if not self.frozen:

            # Assign value
            if self.base_controls.mouse:
                for item in self.cloth_mods:
                    mod = item[0]
                    attr = getattr(mod.settings, self.active_param)
                    setattr(mod.settings, self.active_param, attr + self.base_controls.mouse)

            # Switch attribute
            elif self.base_controls.scroll:
                self.active_param = self.params[ (self.params.index(self.active_param) + self.base_controls.scroll ) % len(self.params)]
                self.report({'INFO'}, F"Adjusting:{self.param_names[self.active_param]}")

        # Toggle animation play
        elif event.type == 'S' and event.value == 'PRESS':
            bpy.ops.screen.animation_play()

        # Toggle animation play
        elif event.type == 'SPACE' and event.value == 'PRESS' and event.shift:
            bpy.ops.screen.animation_play()

        # Jump to frame 1
        elif event.type == 'R' and event.value == 'PRESS':
            self.restart()

        elif event.type == 'TAB' and event.value == 'PRESS' and self.b_popup:
            bpy.ops.hops.adjust_cloth_popup("INVOKE_DEFAULT")

        # Freeze
        # elif event.type == 'F' and event.value == 'PRESS':
        #     self.frozen = not self.frozen

        # Presets
        # elif event.type in self.numbers and event.value == 'PRESS':
        #     key = self.numpad_map[event.type] if event.type in self.numpad_map else event.type
        #     value_map = None

        #     if self.active_param == 'uniform_pressure_force':
        #         value_map = self.pressure_presets

        #     elif self.active_param == 'shrink_min':
        #         value_map = self.shrink_presets

        #     if value_map:
        #         value  =  value_map[key]
        #         if event.shift:
        #             value *=-1
        #         self.set_params(self.active_param, value)

        # # Invert value
        # elif event.type == 'X' and event.value == 'PRESS':
        #     self.change_params(self.active_param , -1, lambda attr, val: attr*val)


    def draw_ui(self, context):

        self.master.setup()
        if self.master.should_build_fast_ui():

            # Main
            win_list = []
            if addon.preference().ui.Hops_modal_fast_ui_loc_options != 1:
                if not self.frozen:
                    win_list.append("{:.3f}".format(getattr(self.active_mod.settings, self.active_param)))
                else:
                    win_list.append("Cloth Adjust")

            else:
                if not self.frozen:
                    win_list.append(self.param_names[self.active_param])
                    win_list.append("{:.3f}".format(getattr(self.active_mod.settings, self.active_param)))
                else:
                    win_list.append("Cloth Adjust")

            # Help
            help_items = {"GLOBAL" : [], "STANDARD" : []}

            help_items["GLOBAL"] = [
                ("M", "Toggle mods list"),
                ("H", "Toggle help"),
                ("~", "Toggle UI Display Type"),
                ("O", "Toggle viewport rendering")]

            h_append = help_items["STANDARD"].append

            #h_append(["Shift Space", "Toggle play timeline"])
            # if not self.frozen:
            #     h_append(["0", "set value to 0"])

            # var = "ON" if self.frozen else "OFF"
            # h_append(["F", f"Mouse Controls {var}"])

            #h_append(["X", "Set value to negative"])
            #h_append(["1 - 5", "Value presets; Shift for negative values"])
            if self.b_popup:
                h_append(["TAB", "Settings Popup"])
            h_append(["Ctrl + Space", "Apply mods and Exit"])
            h_append(["R", "Reset timeline"])
            h_append(["S / Shift + Space", "Start/Play Timeline"])
            h_append(["LMB", "Apply / Close"])
            h_append(["RMB", "Cancel"])

            # if not self.frozen:
            #     h_append(["Scroll  ", "Cycle Parameter"])
            #     h_append(["Mouse   ", "Adjust Value"])

            # Mods
            mods_list = get_mods_list(mods=bpy.context.active_object.modifiers if context.active_object else [])
            self.master.receive_fast_ui(win_list=win_list, help_list=help_items, image="Tthick", mods_list=mods_list)

        self.master.finished()

    #--- FORM FUNCS ---#

    def setup_form(self, context, event):
        self.form = form.Form(context, event, dot_open=True)

        row = self.form.row()
        row.add_element(form.Label(text="PRESSURE", width=75))
        row.add_element(form.Input(obj=self, attr="pressure", width=75, increment=.1))
        self.form.row_insert(row)

        row = self.form.row()
        row.add_element(form.Label(text="SHRINK", width=75))
        row.add_element(form.Input(obj=self, attr="shrink", width=75, increment=.1))
        self.form.row_insert(row)

        row = self.form.row()
        row.add_element(form.Label(text="TIMESPAN", width=75))
        row.add_element(form.Input(obj=self, attr="timespan", width=75, increment=.1))
        self.form.row_insert(row)

        row = self.form.row()
        row.add_element(form.Label(text="GRAVITY", width=75))
        row.add_element(form.Input(obj=self, attr="gravity", width=75, increment=.1))
        self.form.row_insert(row)

        # Pinning
        self.build_pinning_menu()

        row = self.form.row()
        row.add_element(form.Spacer(width=150, height=15, draw_bar=True))
        self.form.row_insert(row)

        row = self.form.row()
        row.add_element(form.Button(img="rewind", width=24, tips=["Restart Timeline"], callback=self.rewind))
        row.add_element(form.Button(img="play", width=24, tips=["Play Timeline"], callback=self.play))
        row.add_element(form.Button(img="restart", width=24, tips=["Restart Timeline on value change"], callback=self.set_auto_restart, highlight_hook=self.get_auto_restart))

        row.add_element(form.Spacer(width=13))
        row.add_element(form.Button(text="APPLY", width=45, height=12, tips=["Apply modifiers on exit"], callback=self.set_apply_mods, highlight_hook=self.get_apply_mods))
        row.add_element(form.Button(text="✓", width=20, height=12, tips=["Close Operation"], callback=self.set_form_exit))
        self.form.row_insert(row)

        self.form.build()


    def build_pinning_menu(self):

        v_groups = groups = [v.name for v in self.active_obj.vertex_groups]

        v_groups.append('NONE')

        row = self.form.row()
        row.add_element(form.Spacer(height=10))
        self.form.row_insert(row)

        row = self.form.row()
        row.add_element(form.Dropdown(width=90, options=v_groups, tips=["V-Groups for pinning"], callback=self.set_vgroup, update_hook=self.vgroup_hook))
        self.form.row_insert(row)

        row = self.form.row()
        row.add_element(form.Spacer(height=5))
        self.form.row_insert(row)


    def set_vgroup(self, opt=''):
        if opt == 'NONE':
            self.active_mod.settings.vertex_group_mass = ''

        else:
            if opt in self.active_obj.vertex_groups:
                self.active_mod.settings.vertex_group_mass = opt

        if self.auto_restart:
            self.rewind()
            if not bpy.context.screen.is_animation_playing:
                self.play()


    def vgroup_hook(self):
        group = self.active_mod.settings.vertex_group_mass
        if group == '': return 'NONE'
        return group


    def rewind(self):
        bpy.ops.screen.frame_jump(end=False)


    def play(self):
        bpy.ops.screen.animation_play()


    def set_auto_restart(self):
        self.auto_restart = not self.auto_restart


    def get_auto_restart(self):
        return bool(self.auto_restart)


    def set_apply_mods(self):
        self.apply_mods_on_exit = not self.apply_mods_on_exit


    def get_apply_mods(self):
        return bool(self.apply_mods_on_exit)


    def set_form_exit(self):
        self.form_exit = not self.form_exit

    # --- UTILS --- #

    def apply_mods(self):
        for item in self.cloth_mods:
            mod, obj = item[0], item[1]
            bpy.context.view_layer.objects.active = obj

            for modifier in obj.modifiers:
                should_break = True if mod == modifier else False
                bpy.ops.object.modifier_apply(modifier=modifier.name)
                if should_break:
                    break

        bpy.ops.hops.display_notification(info=F'Cloth Modifier Applied ')


    def confirm_exit(self):
        self.__class__.operator = None

        # Stop the animation
        if bpy.context.screen.is_animation_playing:
            bpy.ops.screen.animation_play()

        if self.apply_mods_on_exit:
            self.apply_mods()

        self.remove_shader()
        collapse_3D_view_panels(self.original_tool_shelf, self.original_n_panel)
        self.master.run_fade()
        self.report({'INFO'}, "FINISHED")
        return {'FINISHED'}


    def get_cloth(self, obj):
        for mod in reversed(obj.modifiers):
            if mod.type == 'CLOTH':
                if obj is bpy.context.active_object:
                    self.active_mod = mod
                return mod


    def restart(self):
        for item in self.cloth_mods:
            mod = item[0]
            mod.show_viewport = False
        bpy.ops.screen.frame_jump(end=False)

        for item in self.cloth_mods:
            mod = item[0]
            mod.show_viewport = True


    def set_params(self, name, val):
        for item in self.cloth_mods:
            mod = item[0]
            if name == 'gravity': setattr(mod.settings.effector_weights, name, val)
            else: setattr(mod.settings, name, val)

        if self.auto_restart:
            self.restart()


    def change_params(self, name, val, func):
        for item in self.cloth_mods:
            mod = item[0]
            attr = getattr(mod.settings, name)
            setattr(mod.settings, name, func(attr, val))

    # --- SHADERS --- #

    def safe_draw_shader(self, context):
        method_handler(self.draw_shader,
            arguments = (context,),
            identifier = 'Cloth Shader',
            exit_method = self.remove_shader)


    def remove_shader(self):
        '''Remove shader handle.'''

        if self.draw_handle:
            self.draw_handle = bpy.types.SpaceView3D.draw_handler_remove(self.draw_handle, "WINDOW")


    def draw_shader(self, context):
        '''Draw shader handle.'''

        self.form.draw()

        if not self.frozen:
            draw_modal_frame(context)

def pressure_upd(self, context):
        op = HOPS_OT_AdjustClothOperator.operator
        op.active_mod.settings.uniform_pressure_force = self.uniform_pressure_force

        if op.auto_restart:
            reset_timeline(context)

def shrink_min_upd(self, context):
        op = HOPS_OT_AdjustClothOperator.operator
        op.active_mod.settings.shrink_min = self.shrink_min

        if op.auto_restart:
            reset_timeline(context)

def time_scale_upd(self, context):
        op = HOPS_OT_AdjustClothOperator.operator
        op.active_mod.settings.time_scale = self.time_scale

        if op.auto_restart:
            reset_timeline(context)

def gravity_upd(self, context):
        op = HOPS_OT_AdjustClothOperator.operator
        op.active_mod.settings.effector_weights.gravity = self.gravity

        if op.auto_restart:
            reset_timeline(context)

def vertex_group_mass_upd(self, context):
        op = HOPS_OT_AdjustClothOperator.operator
        op.active_mod.settings.vertex_group_mass = self.vertex_group_mass

        if op.auto_restart:
            reset_timeline(context)

def reset_timeline(context):
    bpy.ops.screen.frame_jump(end=False)
    if not context.screen.is_animation_playing:
        bpy.ops.screen.animation_play()

class HOPS_OT_AdjustClothPopup(bpy.types.Operator):
    bl_idname = "hops.adjust_cloth_popup"
    bl_label = "Cloth"

    uniform_pressure_force: bpy.props.FloatProperty(
        name="Pressure",
        description="The uniform pressure that is constantly applied to the mesh",
        update=pressure_upd
    )
    shrink_min: bpy.props.FloatProperty(
        name="Shrink",
        description="Factor by which to shrink mesh",
        update=shrink_min_upd,
        max=1.0
    )
    time_scale: bpy.props.FloatProperty(
        name='Speed',
        description='Speed of the simulation',
        update=time_scale_upd,
        min=0.0
    )
    gravity: bpy.props.FloatProperty(
        name="Gravity",
        description="Global gravity weight",
        update=gravity_upd)

    vertex_group_mass: bpy.props.StringProperty(
        name="Pin Group",
        description="Vertex group for pinning of vertices",
        update=vertex_group_mass_upd
    )


    def __del__(self):
        op = HOPS_OT_AdjustClothOperator.operator
        if not op: return
        op.popover_active = False

    def invoke(self, context, event):
        op = HOPS_OT_AdjustClothOperator.operator
        if not op: return {'CANCELLED'}
        op.popover_active = True

        self.uniform_pressure_force = op.active_mod.settings.uniform_pressure_force
        self.shrink_min = op.active_mod.settings.shrink_min
        self.time_scale = op.active_mod.settings.time_scale
        self.gravity = op.active_mod.settings.effector_weights.gravity
        self.vertex_group_mass = op.active_mod.settings.vertex_group_mass

        return bpy.context.window_manager.invoke_props_dialog(self, width=int(150 * dpi_factor()))

    def execute(self, context):
        HOPS_OT_AdjustClothOperator.operator.form_exit = True
        return {'FINISHED'}

    def draw(self, context):
        op = HOPS_OT_AdjustClothOperator.operator
        if not op: return

        mod = op.active_mod
        layout = self.layout
        layout.row().prop(self, "uniform_pressure_force")
        layout.row().prop(self, "shrink_min")
        layout.row().prop(self, "time_scale")
        layout.row().prop(self, "gravity")

        row = layout.row()

        row.prop(context.scene, 'frame_current', text='')
        row.operator("screen.animation_play", text="", icon='PAUSE' if context.screen.is_animation_playing else 'PLAY')
        row.operator("screen.frame_jump", text="", icon='EVENT_R').end = False
        row.prop(op, "auto_restart", text="", icon='FILE_REFRESH')
        row.prop(op, "apply_mods_on_exit", text="", icon='CHECKMARK')

        layout.row().prop_search(self, "vertex_group_mass", mod.id_data, "vertex_groups", text="")