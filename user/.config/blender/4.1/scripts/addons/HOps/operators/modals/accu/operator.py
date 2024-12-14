import bpy, bmesh
from mathutils import Vector
from .... utility import addon
from .... utility.base_modal_controls import Base_Modal_Controls
from .... ui_framework.master import Master
from .... ui_framework import form_ui as form
from .... utils.toggle_view3d_panels import collapse_3D_view_panels
from .... utils.modal_frame_drawing import draw_modal_frame
from .... utility import method_handler
from .... utility import math as hops_math

from . import State, Bounds, confirmed_exit, unit_scale
from .make_primitive import Make_Primitive
from .adjust import Adjust
from . import ANCHORS

description = """Accu Shape V2
Allows for semi-accurate scaling or drawing
Selection - Interactive dimension system for rescaling
No Selection - Box Creation utilizing accushape
Shift - Use the active object as the bounds
Press H for help"""

class HOPS_OT_Accu_Shape_V2(bpy.types.Operator):
    bl_idname = "hops.accu_shape_v2"
    bl_label = "Accu Shape V2"
    bl_description = description
    bl_options = {"REGISTER", "UNDO", "BLOCKING"}

    def invoke(self, context, event):

        # Data
        self.objs = [o for o in context.selected_objects if o.type in {'MESH', 'CURVE', 'FONT', 'SURFACE'}]
        
        self.bounds = Bounds()
        self.bounds_reset_copy = Bounds()
        self.initial_center_point = Vector()
        self.initial_extents = Vector()

        # Unit
        self.unit_system = 'Metric'
        self.unit_length = 'Meters'

        # State
        self.state = State.MAKE_PRIMITIVE
        self.use_edit_mode = False
        self.started_with_obj = False
        self.add_cube = True if len(self.objs) == 0 else False
        self.exit_with_empty = False
        self.exit = False
        self.equalize = True
        self.skip_frame = False
        self.anchor = 'NONE'

        # Behaviors
        self.make_primitive = Make_Primitive()
        self.adjust = Adjust(self)

        # Initialize the starting point
        if len(self.objs) > 0:
            self.initialize(context, event)

        # Systems
        self.setup_form(context, event)
        self.master = Master(context=context)
        self.master.only_use_fast_ui = True
        self.base_controls = Base_Modal_Controls(context, event)
        self.original_tool_shelf, self.original_n_panel = collapse_3D_view_panels()
        self.draw_handle_2D = bpy.types.SpaceView3D.draw_handler_add(self.safe_draw_2D, (context,), 'WINDOW', 'POST_PIXEL')
        self.draw_handle_3D = bpy.types.SpaceView3D.draw_handler_add(self.safe_draw_3D, (context,), 'WINDOW', 'POST_VIEW')
        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}


    def modal(self, context, event):

        # Systems
        self.master.receive_event(event=event)
        self.base_controls.update(context, event)
        self.form.update(context, event)

        # Update
        if not self.form.active():
            self.actions(context, event)
        self.behavior(context, event)
        self.interface(context)

        # Cancel
        if self.base_controls.cancel:
            self.common_exit(context)
            return {'CANCELLED'}

        # Confirm
        elif event.type in {'RET', 'SPACE'} and event.value == 'PRESS':
            if not self.form.active():
                confirmed_exit(self, context)
                self.common_exit(context)
                return {'FINISHED'}

        # Exit Buttom
        elif self.exit:
            confirmed_exit(self, context)
            self.common_exit(context)
            return {'FINISHED'}

        # Pass Through
        elif self.base_controls.pass_through or event.type in {'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            if not self.form.active():
                return {'PASS_THROUGH'}

        # Running
        context.area.tag_redraw()
        return {"RUNNING_MODAL"}


    def interface(self, context):
        self.master.setup()
        if self.master.should_build_fast_ui():
            # --- Main --- #
            win_list = ["AccuV2"]
            if self.state == State.MAKE_PRIMITIVE:
                win_list.append("Draw Mode")

            # --- Help --- #
            help_items = {"GLOBAL" : [], "STANDARD" : []}
            help_items["GLOBAL"] = [
                ("M", "Toggle mods list"),
                ("H", "Toggle help"),
                ("~", "Toggle UI Display Type"),
                ("O", "Toggle viewport rendering")]

            h_append = help_items["STANDARD"].append
            h_append(["Shift E", "Use Empty"])
            h_append(["E", "Equalize"])
            h_append(["X", "Reset"])
            h_append(["R", "Redraw"])

            if self.state == State.MAKE_PRIMITIVE:
                h_append(["Click", "Confirm Point"])
                h_append(["Ctrl", "Surface Cast"])
                h_append(["Shift", "Vert Cast"])

            elif self.state == State.ADJUSTING:
                if self.adjust.move.locked:
                    h_append(["Click", "Confirm Point"])
                    h_append(["Ctrl", "Surface Cast"])
                    h_append(["Shift", "Vert Cast"])
                else:
                    h_append(["Shift Click", "Set Anchor"])
                    h_append(["Click Drag", "Move selected face"])

            self.master.receive_fast_ui(win_list=win_list, help_list=help_items, image="Display_boolshapes")
        self.master.finished()

    # --- ACTIONS --- #

    def actions(self, context, event):
        # Equalize / Empty
        if event.type == 'E' and event.value == 'PRESS':
            if event.shift:
                self.exit_with_empty = not self.exit_with_empty
                msg = "Exit With Empty : ON" if self.exit_with_empty else "Exit With Empty : OFF"
                bpy.ops.hops.display_notification(info=msg)
            else:
                self.equalize_dimensions()
        # Reset
        elif event.type == 'X' and event.value == 'PRESS':
            self.reset_bounds()
        # Redraw
        elif event.type == 'R' and event.value == 'PRESS':
            self.redraw_bounds()


    def equalize_dimensions(self):
        self.equalize = not self.equalize
        msg = "Equalize On" if self.equalize else "Equalize Off"
        bpy.ops.hops.display_notification(info=msg)

        bounds = hops_math.coords_to_bounds(self.bounds.all_points())
        self.bounds.map_bounds(bounds)


    def reset_bounds(self):
        self.bounds.map_other_bounds(self.bounds_reset_copy)
        bpy.ops.hops.display_notification(info="Reset Bounds")


    def redraw_bounds(self):
        self.skip_frame = True
        self.make_primitive.reset()
        self.state = State.MAKE_PRIMITIVE
        bpy.ops.hops.display_notification(info="Started Redraw")

    # --- BEHAVIOR --- #

    def behavior(self, context, event):
        if self.skip_frame:
            self.skip_frame = False
            return

        if self.state == State.MAKE_PRIMITIVE:
            self.make_primitive.update(context, event, self)
        elif self.state == State.ADJUSTING:
            self.adjust.update(context, event, self)

    # --- EXIT --- #

    def common_exit(self, context):
        addon.preference().property.accu_length = self.unit_length
        collapse_3D_view_panels(self.original_tool_shelf, self.original_n_panel)
        self.remove_shaders()
        self.master.run_fade()
        self.form.shut_down(context)

    # --- UTILS --- #

    def initialize(self, context, event):
        self.started_with_obj = True
        if context.mode == 'EDIT_MESH':
            self.edit_mode_capture(context, event)
        else:
            self.obj_mode_capture(context, event)

        self.bounds_reset_copy.map_other_bounds(self.bounds)


    def edit_mode_capture(self, context, event):
        objs = [o for o in context.selected_objects if o.type == 'MESH' and o.mode == 'EDIT']
        coords = []

        # Get all selected verts
        for obj in objs:
            obj.update_from_editmode()
            bm = bmesh.from_edit_mesh(obj.data)
            selected = [v for v in bm.verts if v.select == True]
            for vert in selected:
                coords.append(obj.matrix_world @ vert.co)

        if len(coords) < 3: return
        bounds = hops_math.coords_to_bounds(coords)

        self.initial_center_point = hops_math.coords_to_center(bounds)
        self.initial_extents = hops_math.dimensions(bounds)
        self.bounds.map_bounds(bounds)
        self.state = State.ADJUSTING
        self.use_edit_mode = True


    def obj_mode_capture(self, context, event):
        if context.mode != 'OBJECT': bpy.ops.object.mode_set(mode='OBJECT')
        objs = self.objs[:]

        # Only use active object
        if event.shift:
            if context.active_object in objs:
                objs = [context.active_object]
            else:
                bpy.ops.hops.display_notification(info="Active object was not a valid type.")

        coords = []
        depsgraph = context.evaluated_depsgraph_get()

        for obj in objs:
            obj_eval = obj.evaluated_get(depsgraph)
            data_eval = obj_eval.to_mesh()
            coords.extend([obj.matrix_world @ v.co for v in data_eval.vertices])
            obj_eval.to_mesh_clear()

        if len(coords) < 3: return
        bounds = hops_math.coords_to_bounds(coords)

        self.initial_center_point = hops_math.coords_to_center(bounds)
        self.initial_extents = hops_math.dimensions(bounds)
        self.bounds.map_bounds(bounds)
        self.state = State.ADJUSTING

    # --- FORM --- #
    
    def setup_form(self, context, event):

        # Form Props
        self.form = form.Form(context, event, dot_open=True)
        self.before_equalize = self.equalize

        # Label
        row = self.form.row()
        row.add_element(form.Label(text="AccuShape V2", width=160))
        row.add_element(form.Button(text="✓", width=25, tips=["Finalize and Exit"], callback=self.exit_button))
        self.form.row_insert(row)

        row = self.form.row()
        row.add_element(form.Spacer(height=10))
        self.form.row_insert(row)

        # Utils
        row = self.form.row()
        row.add_element(form.Button(text="E", width=20, tips=["Equalize"], callback=self.equalize_dimensions, highlight_hook=self.get_equalize))
        row.add_element(form.Button(text="X", width=20, tips=["Reset"], callback=self.reset_bounds))
        row.add_element(form.Button(text="R", width=20, tips=["Redraw"], callback=self.redraw_bounds))
        row.add_element(form.Spacer(width=45))
        row.add_element(form.Dropdown(width=75, options=['Lattice', 'Empty'], callback=self.set_exit_obj, update_hook=self.exit_obj_hook, index=0))
        self.form.row_insert(row)

        row = self.form.row()
        row.add_element(form.Spacer(height=10))
        self.form.row_insert(row)

        # L W H
        row = self.form.row()
        row.add_element(form.Label(text="Length", width=60))
        self.default_input_length = form.Input(obj=self.adjust.overall, attr="length", width=120, increment=.1, font_size=16, ctrl_scroll_callback=self.ctrl_scroll_values)
        row.add_element(self.default_input_length)
        self.form.row_insert(row, label='Default', active=True)

        row = self.form.row()
        row.add_element(form.Label(text="Width", width=60))
        self.default_input_width = form.Input(obj=self.adjust.overall, attr="width", width=120, increment=.1, font_size=16, ctrl_scroll_callback=self.ctrl_scroll_values)
        row.add_element(self.default_input_width)
        self.form.row_insert(row, label='Default', active=True)

        row = self.form.row()
        row.add_element(form.Label(text="Height", width=60))
        self.default_input_height = form.Input(obj=self.adjust.overall, attr="height", width=120, increment=.1, font_size=16, ctrl_scroll_callback=self.ctrl_scroll_values)
        row.add_element(self.default_input_height)
        self.form.row_insert(row, label='Default', active=True)

        row = self.form.row()
        row.add_element(form.Spacer(height=10))
        self.form.row_insert(row)

        metric, imperial, metric_index, imperial_index = self.accu_length_indexes()

        # Unit Length : Default
        row = self.form.row()
        row.add_element(form.Dropdown(width=90, options=['Metric', 'Imperial'], tips=["Unit System"], callback=self.set_unit_system, update_hook=self.unit_system_hook))
        row.add_element(form.Dropdown(width=90, options=['Kilometers', 'Meters', 'Centimeters', 'Millimeters', 'Micrometers'], tips=["Unit Length"], callback=self.set_unit_length, update_hook=self.unit_length_hook, index=metric_index))
        self.form.row_insert(row, label='Metric', active=metric)

        # Unit Length : Preset
        row = self.form.row()
        row.add_element(form.Dropdown(width=90, options=['Metric', 'Imperial'], tips=["Unit System"], callback=self.set_unit_system, update_hook=self.unit_system_hook))
        row.add_element(form.Dropdown(width=90, options=['Miles', 'Feet', 'Inches', 'Thousandth'], tips=["Unit Length"], callback=self.set_unit_length, update_hook=self.unit_length_hook, index=imperial_index))
        self.form.row_insert(row, label='Imperial', active=imperial)

        # Anchor
        row = self.form.row()
        row.add_element(form.Label(text="Anchor", width=90))
        row.add_element(form.Dropdown(width=90, options=ANCHORS, callback=self.set_anchor, update_hook=self.anchor_hook, index=1))
        self.form.row_insert(row)

        self.form.build()


    def accu_length_indexes(self):
        length = addon.preference().property.accu_length

        metric_lengths = ['Kilometers', 'Meters', 'Centimeters', 'Millimeters', 'Micrometers']
        imperial_lengths = ['Miles', 'Feet', 'Inches', 'Thousandth']
        
        metric = True if length in metric_lengths else False
        imperial = True if length in imperial_lengths else False

        metric_index = 0
        imperial_index = 0

        if metric:
            metric_index = metric_lengths.index(length)
            self.unit_system = 'Metric'
            self.unit_length = length

        elif imperial:
            imperial_index = imperial_lengths.index(length)
            self.unit_system = 'Imperial'
            self.unit_length = length
        
        return metric, imperial, metric_index, imperial_index


    def alter_form_layout(self, preset_label=''):
        if preset_label == 'Metric':
            self.form.row_activation(label='Metric', active=True)
            self.form.row_activation(label='Imperial', active=False)
            self.form.build()
        elif preset_label == 'Imperial':
            self.form.row_activation(label='Metric', active=False)
            self.form.row_activation(label='Imperial', active=True)
            self.form.build()


    def set_exit_obj(self, opt=''):
        if opt == 'Lattice':
            self.exit_with_empty = False
        elif opt == 'Empty':
            self.exit_with_empty = True


    def exit_obj_hook(self):
        if self.exit_with_empty: return 'Empty'
        else: return 'Lattice'


    def ctrl_scroll_values(self, opt=''):
        if opt == 'before':
            self.before_equalize = self.equalize
            self.equalize = False
        elif opt == 'after':
            self.equalize = self.before_equalize


    def get_equalize(self):
        return bool(self.equalize)


    def set_unit_system(self, opt=''):
        self.unit_system = opt
        self.alter_form_layout(preset_label=opt)
        if opt == 'Metric':
            self.unit_length = 'Meters'
        elif opt == 'Imperial':
            self.unit_length = 'Feet'
        self.set_increment()


    def unit_system_hook(self):
        return self.unit_system


    def set_unit_length(self, opt=''):
        self.unit_length = opt
        self.alter_form_layout(preset_label=opt)
        self.set_increment()


    def unit_length_hook(self):
        return self.unit_length


    def set_increment(self):
        increment = .1 * unit_scale(self.unit_length)
        self.default_input_length.increment = increment
        self.default_input_width.increment  = increment
        self.default_input_height.increment = increment


    def set_anchor(self, opt=''):
        if opt in ANCHORS: self.anchor = opt
        else: self.anchor = 'BOTTOM'


    def anchor_hook(self):
        return self.anchor


    def exit_button(self):
        self.exit = True

    # --- SHADER --- #

    def remove_shaders(self):
        if self.draw_handle_2D:
            self.draw_handle_2D = bpy.types.SpaceView3D.draw_handler_remove(self.draw_handle_2D, "WINDOW")
        if self.draw_handle_3D:
            self.draw_handle_3D = bpy.types.SpaceView3D.draw_handler_remove(self.draw_handle_3D, "WINDOW")


    def safe_draw_2D(self, context):
        method_handler(self.draw_2D,
            arguments = (context,),
            identifier = 'Modal Shader 2D',
            exit_method = self.remove_shaders)


    def draw_2D(self, context):
        self.form.draw()

        if self.state == State.MAKE_PRIMITIVE:
            self.make_primitive.draw_2D(self)
        elif self.state == State.ADJUSTING:
            self.adjust.draw_2D(context, self)


    def safe_draw_3D(self, context):
        method_handler(self.draw_3D,
            arguments = (context,),
            identifier = 'Modal Shader 3D',
            exit_method = self.remove_shaders)


    def draw_3D(self, context):
        if self.state == State.MAKE_PRIMITIVE:
            self.make_primitive.draw_3D(self)
        elif self.state == State.ADJUSTING:
            self.adjust.draw_3D(self)


