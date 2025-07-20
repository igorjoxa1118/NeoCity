import bpy, mathutils, math
from mathutils import Matrix, Vector
from enum import Enum
from ... meshtools.applymod import apply_mod
from ....utility.screen import dpi_factor
from .... utility import addon
from .... ui_framework.master import Master
from .... utility.base_modal_controls import Base_Modal_Controls
from .... utils.toggle_view3d_panels import collapse_3D_view_panels
from .... utils.modal_frame_drawing import draw_modal_frame
from .... utils.objects import set_active
from .... utils.cursor_warp import mouse_warp
from .... utility import method_handler
from .... utility import math as hops_math

from .struct import Axis, Dice_Box_3D, selection_boundary, get_boxelize_ref
from .shader import SD, setup_draw_data
from .interface import alter_form_layout

from . import knife_project, knife_intersect, prepare, remove

MEM_X_COUNT = 5
MEM_Y_COUNT = 5
MEM_Z_COUNT = 5


class Edit_3D:
    def __init__(self, op, context, event):

        # States
        self.knife_method = "Knife" if addon.preference().property.dice_method == 'KNIFE_PROJECT' else "Intersect"

        # Dice Structs
        self.x_dice = Dice_Box_3D(Axis.X, active=True, segments=MEM_X_COUNT)
        self.y_dice = Dice_Box_3D(Axis.Y, active=False, segments=MEM_Y_COUNT)
        self.z_dice = Dice_Box_3D(Axis.Z, active=False, segments=MEM_Z_COUNT)

        # Entry events
        if not event.ctrl:
            if op.dice_axis == 'X':
                self.x_dice.active = True
            elif op.dice_axis == 'Y':
                self.y_dice.active = True
            elif op.dice_axis == 'Z':
                self.z_dice.active = True

        # Setup
        self.selected = []
        self.curves = []

        # Controls
        self.presets = [3,5,7,11,15,18,20,23,26,29,33,42,45,49,52,63]
        self.preset_index = 0
        self.prefs = addon.preference().property
        self.dpi = dpi_factor(min=.5)
        self.exit_to_twist = False
        self.mouse_buffer = 0
        self.mouse_mode_segments = max(MEM_X_COUNT, MEM_Y_COUNT, MEM_Z_COUNT)
        self.modal_scale = addon.preference().ui.Hops_modal_scale
        self.cut_active_only = event.shift

        # Updates
        self.rebuild_setup_data = False
        self.rebuild_draw_data = True

    # --- ACTIONS --- #

    def update(self, op, context, event):

        # Setup structs
        if self.rebuild_setup_data:
            self.rebuild_setup_data = False
            self.setup(context, event)

        # Check for draw update
        self.check_for_updates()
        if self.rebuild_draw_data:
            self.rebuild_draw_data = False
            setup_draw_data(op)

        # Hot keys
        if not op.form.active():
            mouse_warp(context, event)
            self.actions(op, context, event)


    def actions(self, op, context, event):

        # Toggle X
        if event.type == 'X' and event.value == 'PRESS':
            self.rebuild_draw_data = True
            self.x_dice.active = not self.x_dice.active
            self.x_dice.segments = self.mouse_mode_segments
            self.set_segments_via_mouse_mode()

        # Toggle Y
        elif event.type == 'Y' and event.value == 'PRESS':
            self.rebuild_draw_data = True
            self.y_dice.active = not self.y_dice.active
            self.y_dice.segments = self.mouse_mode_segments
            self.set_segments_via_mouse_mode()

        # Toggle Z
        elif event.type == 'Z' and event.value == 'PRESS':
            self.rebuild_draw_data = True
            self.z_dice.active = not self.z_dice.active
            self.z_dice.segments = self.mouse_mode_segments
            self.set_segments_via_mouse_mode()

        # Smart Apply
        elif event.type == 'S' and event.value == 'PRESS':
            self.smart_apply(context)

        # Exit to Twist
        elif event.type == 'T' and event.value == 'PRESS':
            self.exit_to_twist = not self.exit_to_twist
            bpy.ops.hops.display_notification(info=f"Exit To_Twist: {'ON' if self.exit_to_twist else 'OFF'}")

        # Join
        elif event.type == 'J' and event.value == 'PRESS':
            self.join_objs(context, event)

        # Exit to Twist
        elif event.type == 'Q' and event.value == 'PRESS':
            if self.knife_method == "Knife":
                self.knife_method = "Intersect"
            elif self.knife_method == "Intersect":
                self.knife_method = "Knife"
            bpy.ops.hops.display_notification(info=f"Method : {self.knife_method}")

        # Boxelize
        elif event.type == 'B' and event.value == 'PRESS':
            self.toggle_boxelize(op)

        # Graphics
        elif event.type == 'N' and event.value == 'PRESS':
            types = ['LINES', 'TICKS', 'DOTS']
            index = types.index(self.prefs.dice_wire_type)
            self.prefs.dice_wire_type = types[(index + 1) % len(types)]
            self.rebuild_draw_data = True

        if not op.form.is_dot_open():
            self.mouse_actions(op, context, event)

        # Keep at least the X axis alive
        self.ensure_active_axis()


    def mouse_actions(self, op, context, event):

        boxelize = get_boxelize_ref()

        # Segments
        if op.base_controls.scroll:
            scroll = op.base_controls.scroll

            # Boxelize
            if boxelize.active:
                boxelize.segments += scroll
                if boxelize.segments < 2:
                    boxelize.segments = 2
                self.rebuild_draw_data = True
                return

            # Presets
            if event.shift:
                if scroll > 0: self.preset_index += 1
                else: self.preset_index -= 1
                if self.preset_index < 0:
                    self.preset_index = len(self.presets) - 1
                elif self.preset_index > len(self.presets) - 1:
                    self.preset_index = 0
                self.mouse_mode_segments = self.presets[self.preset_index]

            # Standard
            else:
                self.mouse_mode_segments += scroll

            self.set_segments_via_mouse_mode()

        # Mouse Axis
        if boxelize.active == False:
            self.mouse_axis_change(context, event)


    def set_segments_via_mouse_mode(self):
        if self.x_dice.active:
            self.x_dice.segments = self.mouse_mode_segments
        if self.y_dice.active:
            self.y_dice.segments = self.mouse_mode_segments
        if self.z_dice.active:
            self.z_dice.segments = self.mouse_mode_segments


    def mouse_axis_change(self, context, event):

        delta = event.mouse_x - event.mouse_prev_x
        delta *= self.dpi
        delta = delta * .5 if event.shift else delta
        self.mouse_buffer += delta

        alter = False
        if abs(self.mouse_buffer) > self.modal_scale * 250 * self.dpi:
            self.mouse_buffer = 0
            alter = True
        if not alter: return

        structs = [self.x_dice, self.y_dice, self.z_dice]
        active = None
        for struct in structs:
            if struct.active:
                # Set the axis to use
                if not active:
                    active = struct
                # More than one axis in use
                else: return
        # Catch
        if not active: return

        index = structs.index(active)
        index = index + 1 if self.mouse_buffer > 0 else index - 1

        if index < 0: index = 2
        if index > 2: index = 0

        for struct in structs:
            struct.active = False

        structs[index].active = True

        self.rebuild_draw_data = True
        self.set_segments_via_mouse_mode()

    # --- UTILS --- #

    def setup(self, context, event):

        self.selected = [o for o in context.selected_objects if o.type == 'MESH']
        self.curves = [o for o in context.selected_objects if o.type == 'CURVE']

        # Smart Apply
        if event.alt or addon.preference().property.smart_apply_dice == 'SMART_APPLY':
            self.smart_apply(context)

        # Convert to mesh
        elif addon.preference().property.smart_apply_dice == 'APPLY':
            obj = context.active_object
            if obj.mode != 'EDIT':
                for obj in self.selected:
                    bpy.ops.object.convert(target='MESH')
                    bpy.ops.mesh.customdata_custom_splitnormals_clear()
            bpy.ops.hops.display_notification(info="Converted To Mesh")
            self.selected = [o for o in context.selected_objects if o.type == 'MESH']
            self.curves = []

        structs = [self.x_dice, self.y_dice, self.z_dice]

        # Cut others based on bounds of active
        cut_objects = self.selected[:]

        if self.cut_active_only and len(self.selected) > 1:
            if context.active_object in cut_objects:
                cut_objects.remove(context.active_object)

        # Matrix
        obj = context.active_object
        matrix = obj.matrix_world if obj in self.selected else Matrix()

        # Rotation for empty
        empty_matrix = None
        for obj in context.selected_objects:
            if obj.type == 'EMPTY':
                loc, _, sca = matrix.decompose()
                rot = obj.matrix_world.to_quaternion()

                mat_loc = mathutils.Matrix.Translation(loc).to_4x4()
                mat_rot = rot.to_matrix().to_4x4()
                mat_sca = mathutils.Matrix.Diagonal(sca).to_4x4()
                empty_matrix = mat_loc @ mat_rot @ mat_sca
                break

        # Cut active only
        if self.cut_active_only:
            if len(cut_objects) == 1:
                matrix = cut_objects[0].matrix_world
            else: matrix = Matrix()

        mat = empty_matrix if empty_matrix else matrix
        for struct in structs: struct.matrix = mat

        # Bounds
        bounds = selection_boundary(context, cut_objects, matrix, empty_matrix)
        if not bounds: return False
        for struct in structs: struct.bounds = bounds

        # Center
        center = hops_math.coords_to_center(bounds)
        for struct in structs: struct.center = center

        # Will boxelize if possible
        self.boxelize_setup()

        return True


    def boxelize_setup(self):
        boxelize = get_boxelize_ref()
        if not boxelize.active: return


    def check_for_updates(self):
        structs = [self.x_dice, self.y_dice, self.z_dice]
        for struct in structs:
            if struct.pending_update:
                struct.pending_update = False
                self.rebuild_draw_data = True


    def knife(self, context):

        original_mode = context.mode
        original_active = context.active_object
        bpy.ops.object.mode_set(mode='OBJECT')

        use_normal_offset = True if self.knife_method == "Intersect" else False
        boxelize = get_boxelize_ref()

        cut_objects = self.selected[:]
        if self.cut_active_only:
            if context.active_object in cut_objects:
                cut_objects = [context.active_object]

        if self.x_dice.active or boxelize.active:
            x_obj = self.x_dice.create_mesh(context, use_normal_offset)
            if x_obj:
                for obj in cut_objects:
                    prepare(obj, x_obj)
                    if self.knife_method == "Knife":
                        knife_project(context, obj, x_obj, axis='X')
                    elif self.knife_method == "Intersect":
                        knife_intersect(context)
                remove(x_obj)

        if self.y_dice.active or boxelize.active:
            y_obj = self.y_dice.create_mesh(context, use_normal_offset)
            if y_obj:
                for obj in cut_objects:
                    prepare(obj, y_obj)
                    if self.knife_method == "Knife":
                        knife_project(context, obj, y_obj, axis='Y')
                    elif self.knife_method == "Intersect":
                        knife_intersect(context)
                remove(y_obj)

        if self.z_dice.active or boxelize.active:
            z_obj = self.z_dice.create_mesh(context, use_normal_offset)
            if z_obj:
                for obj in cut_objects:
                    prepare(obj, z_obj)
                    if self.knife_method == "Knife":
                        knife_project(context, obj, z_obj, axis='Z')
                    elif self.knife_method == "Intersect":
                        knife_intersect(context)
                remove(z_obj)

        for obj in self.selected:
            obj.select_set(True)

        set_active(original_active)

        if original_mode == 'EDIT_MESH':
            bpy.ops.object.mode_set(mode='EDIT')


    def ensure_active_axis(self):
        if self.x_dice.active: return
        if self.y_dice.active: return
        if self.z_dice.active: return
        self.x_dice.active = True
        self.rebuild_draw_data = True


    def smart_apply(self, context):
        mode = context.mode
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
        for obj in self.selected: apply_mod(self, obj, clear_last=False)
        if mode == 'EDIT_MESH': bpy.ops.object.mode_set(mode='EDIT', toggle=False)
        bpy.ops.hops.display_notification(info="Smart Apply")
        self.rebuild_setup_data = True
        self.rebuild_draw_data = True


    def join_objs(self, context, event):

        self.smart_apply(context)

        object_count = len(self.selected) + len(self.curves)
        mode = context.mode

        active_obj = context.active_object
        if active_obj not in self.selected:
            active_obj = self.selected[0]

        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

        for obj in self.curves:
            context.view_layer.objects.active = obj
            obj.select_set(True)
            bpy.ops.object.convert('INVOKE_DEFAULT', target='MESH')

        context.view_layer.objects.active = active_obj
        bpy.ops.object.join()

        self.setup(context, event)

        if object_count > 1:
            bpy.ops.hops.display_notification(info="Objects Joined")

        if mode == 'EDIT_MESH':
            bpy.ops.object.mode_set(mode='EDIT', toggle=False)

        self.rebuild_setup_data = True
        self.rebuild_draw_data = True

    # --- EXITS --- #

    def confirm_exit(self, context, event):

        if self.exit_to_twist:
            self.smart_apply(context)
            self.join_objs(context, event)
            SD.exit_with_no_fade = True

        self.knife(context)

        if SD.exit_with_no_fade == False:
            bpy.ops.hops.draw_wire_mesh_launcher('INVOKE_DEFAULT', target='SELECTED')

        if self.exit_to_twist:
            bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
            bpy.ops.hops.array_twist('INVOKE_DEFAULT')

        if self.x_dice.active:
            self.dice_axis = 'X'
        elif self.y_dice.active:
            self.dice_axis = 'Y'
        elif self.z_dice.active:
            self.dice_axis = 'Z'

        boxelize = get_boxelize_ref()
        boxelize.deactivate()

        global MEM_X_COUNT, MEM_Y_COUNT, MEM_Z_COUNT
        MEM_X_COUNT = self.x_dice.segments
        MEM_Y_COUNT = self.y_dice.segments
        MEM_Z_COUNT = self.z_dice.segments


    def cancel_exit(self, context):
        boxelize = get_boxelize_ref()
        boxelize.deactivate()

    # --- FORM --- #

    @property
    def boxelize_segments(self):
        return get_boxelize_ref().segments

    @boxelize_segments.setter
    def boxelize_segments(self, val):
        get_boxelize_ref().segments = int(val) if int(val) > 0 else 1
        self.rebuild_setup_data = True
        self.rebuild_draw_data = True


    def set_knife_method(self, opt=''):
        self.knife_method = opt


    def knife_method_hook(self):
        return self.knife_method


    def set_shader_type(self, opt=''):
        self.prefs.dice_wire_type = opt


    def shader_type_hook(self):
        return self.prefs.dice_wire_type


    def toggle_boxelize(self, op):
        if op.form.operator_stop_building(): return

        boxelize = get_boxelize_ref()
        if boxelize.active:

            # Transfer the cuts to standard mode on exit
            if op.form.is_dot_open():
                self.x_dice.segments = len(self.x_dice.loops())
                self.y_dice.segments = len(self.y_dice.loops())
                self.z_dice.segments = len(self.z_dice.loops())

            boxelize.deactivate()
            self.rebuild_draw_data = True
            self.rebuild_setup_data = True
            alter_form_layout(op, preset_label='AXIAL')
            return

        boxelize.active = True
        self.rebuild_draw_data = True
        self.rebuild_setup_data = True
        alter_form_layout(op, preset_label='BOXELIZE')


    def toggle_see_through(self):
        SD.see_though = not SD.see_though


    def see_through_hook(self):
        return SD.see_though