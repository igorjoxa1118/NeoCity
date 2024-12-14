import bpy, bmesh, math, enum
from ... utility import addon
from ... utility import modifier, object
from ... utility.base_modal_controls import Base_Modal_Controls
from ... ui_framework.master import Master
from ... ui_framework.utils.mods_list import get_mods_list
from ... utils.objects import apply_scale

# Cursor Warp imports
from ... utils.toggle_view3d_panels import collapse_3D_view_panels
from ... utils.modal_frame_drawing import draw_modal_frame
from ... utils.cursor_warp import mouse_warp
from ... utility import method_handler
from mathutils import Vector, Matrix

class origin_modes(enum.Enum):
    original = 0
    center = 1
    cursor = 2

mode_string = {
    origin_modes.original: "Object Origin",
    origin_modes.center: "Object Center",
    origin_modes.cursor: "3D Cursor",
}

DESC = '''LMB - Array around object origin / Reuse Radial Driven Empty
Ctrl + LMB - Array around 3D cursor
Shift + LMB - Array selected object around active object
'''


class HOPS_OT_RadialArray(bpy.types.Operator):
    bl_idname = "hops.radial_array"
    bl_label = "Radial Array"
    bl_options = {'REGISTER', 'UNDO', 'GRAB_CURSOR'}
    bl_description = DESC

    direction: bpy.props.EnumProperty(
        name="Direction",
        description="What axis to displace on",
        items=[
            ('X', "X", "Displace on the X axis"),
            ('Y', "Y", "Displace on the Y axis"),
            ('Z', "Z", "Displace on the Z axis")],
        default='Y')

    axis: bpy.props.EnumProperty(
        name="Axis",
        description="What axis to array around",
        items=[
            ('X', "X", "Array around the X axis"),
            ('Y', "Y", "Array around the Y axis"),
            ('Z', "Z", "Array around the Z axis")],
        default='Z')

    segments: bpy.props.IntProperty(
        name="Segments",
        description="How many copies to make",
        default=8,
        min=1)

    rotation: bpy.props.IntProperty(
        name="Rotation",
        description="Amount of rotation",
        default=360,
        min=15)

    displace: bpy.props.FloatProperty(
        name="Displace",
        description="How far in or out to displace",
        default=0)

    # cursor: bpy.props.BoolProperty(
    #     name="3D Cursor",
    #     description="Use the 3D cursor as origin",
    #     default=False)

    from_empty: bpy.props.BoolProperty(
        name='From Empty',
        description='Use active Empty object instead of new one',
        default=False)

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type in {'MESH', 'EMPTY'} and obj.mode == 'OBJECT'


    def draw(self, context):
        self.layout.label(text=f"Direction: {self.direction}")
        self.layout.label(text=f"Axis: {self.axis}")
        self.layout.label(text=f"Segments: {self.segments}")
        self.layout.label(text=f"Displace: {self.displace:.3f}")
        self.layout.label(text=f"Origin: {mode_string[self.origin_mode]}")


    def execute(self, context):
        return {'FINISHED'}


    def invoke(self, context, event):

        # Set internal variables
        self.modal_scale = addon.preference().ui.Hops_modal_scale
        self.obj = context.active_object

        self.index = 0
        self.obj_matrix = self.obj.matrix_world.copy()
        self.active_matrix = None
        self.to_selection = False
        self.origin_mode = origin_modes.original

        self.selected_states = [(obj, obj.select_get()) for obj in context.selected_objects if obj is not context.active_object and obj.type == 'MESH']

        if not self.from_empty:
            for pair in self.selected_states:
                pair[0].select_set(False)

        if event.shift and not event.ctrl and len(self.selected_states) == 1:
            self.to_selection = True
            self.obj = self.selected_states[0][0]
            self.active_matrix = context.active_object.matrix_world.copy()
            self.obj_matrix = self.obj.matrix_world.copy()

        if self.from_empty:
            if len(self.selected_states) == 1:
                self.to_selection = False
                self.obj = self.selected_states[0][0]
                self.obj_matrix = self.obj.matrix_world.copy()
                empty = context.active_object
                loc = empty.location.copy()
                rot = empty.rotation_euler.copy()
                sca = empty.scale.copy()
                context.active_object.select_set(False)

                try:
                    for drvr in empty.animation_data.drivers:
                        if drvr.data_path == 'location':
                            loc[drvr.array_index] = 0
                        elif drvr.data_path == 'rotation_euler':
                            rot[drvr.array_index] = 0
                        elif drvr.data_path == 'scale':
                            sca[drvr.array_index] = 1
                except:
                    bpy.ops.hops.display_notification(info=F'Failed: Invalid Empty', subtext='Select a HOPS Radial Empty')
                    return {'CANCELLED'}

                empty_mat = Matrix.Translation(loc) @ rot.to_quaternion().to_matrix().to_4x4() @ Matrix.Diagonal((*sca, 1))
                parent_mat = empty.parent.matrix_world @ empty.matrix_parent_inverse if empty.parent else Matrix()
                matrix = parent_mat @ empty_mat
                object.set_origin(self.obj, matrix)

            elif not self.to_selection:
                self.report({'INFO'}, 'Cannot Array an Empty')
                bpy.ops.hops.display_notification(info=F'CANCELLED: Cannot Array an Empty')
                return {'CANCELLED'}


        is_displace = len([mod for mod in self.obj.modifiers if mod.type == 'DISPLACE'])
        if not is_displace:
            scale_vectors = []
            apply_scale([self.obj], scale_vectors=scale_vectors)

        # Set internal variables
        self.empty = None
        self.displace_mod = None
        self.array_mod = None

        # Find empty and modifiers
        for a, b in zip(self.obj.modifiers[:-1], self.obj.modifiers[1:]):
            if a.type == 'DISPLACE' and b.type == 'ARRAY' and b.use_object_offset == True:
                self.empty = b.offset_object
                self.displace_mod = a
                self.array_mod = b
                break

        # Set internal variables
        self.empty_new = not self.empty
        self.displace_new = not self.displace_mod
        self.array_new = not self.array_mod

        if self.from_empty:
            self.empty = context.active_object
            self.empty_new = False

        # Create empty and modifiers
        if self.empty_new:
            self.empty = bpy.data.objects.new("Radial Empty", None)
            self.empty.empty_display_type = 'SPHERE'
            self.empty.parent = self.obj
            for col in self.obj.users_collection:
                if col not in self.empty.users_collection:
                    col.objects.link(self.empty)

        if self.displace_new:
            self.displace_mod = self.obj.modifiers.new("Radial Displace", 'DISPLACE')
            self.displace_mod.show_expanded = False

            self.displace_mod.show_render = addon.preference().property.Hops_twist_radial_sort
            self.displace_mod.show_in_editmode = not addon.preference().property.Hops_twist_radial_sort

            self.displace_mod.mid_level = 0.0
            self.displace_mod.direction = self.direction
            self.displace_mod.strength = self.displace

        if self.array_new:
            self.array_mod = self.obj.modifiers.new("Radial Array", 'ARRAY')
            self.array_mod.show_expanded = False

            self.array_mod.show_render = addon.preference().property.Hops_twist_radial_sort
            self.array_mod.show_in_editmode = not addon.preference().property.Hops_twist_radial_sort

            self.array_mod.use_constant_offset = False
            self.array_mod.use_relative_offset = False
            self.array_mod.use_object_offset = True
            self.array_mod.offset_object = self.empty
            self.array_mod.count = self.segments

        # Set internal variables
        self.direction = self.displace_mod.direction
        self.axis = "YZX"["XYZ".find(self.direction)]
        self.segments = self.segments_buffer = self.array_mod.count
        self.displace = self.displace_buffer = self.displace_mod.strength

        self.reuse_driver = False
        # Try to find the axis from the empty's drivers
        if self.empty.animation_data:
            for fcurve in self.empty.animation_data.drivers:
                if fcurve.data_path == "rotation_euler":
                    self.axis = "XYZ"[fcurve.array_index]
                    self.reuse_driver = self.from_empty

        # Store modifier settings
        self.displace_settings = {}
        self.displace_settings["show_viewport"] = self.displace_mod.show_viewport
        self.displace_settings["mid_level"] = self.displace_mod.mid_level
        self.displace_settings["direction"] = self.displace_mod.direction
        self.displace_settings["strength"] = self.displace_mod.strength

        self.array_settings = {}
        self.array_settings["use_constant_offset"] = self.array_mod.use_constant_offset
        self.array_settings["use_relative_offset"] = self.array_mod.use_relative_offset
        self.array_settings["use_object_offset"] = self.array_mod.use_object_offset
        self.array_settings["offset_object"] = self.array_mod.offset_object
        self.array_settings["count"] = self.array_mod.count

        # Configure existing modifiers
        if not self.displace_new:
            self.displace_mod.mid_level = 0.0
            self.displace_mod.direction = self.direction
            self.displace_mod.strength = self.displace

        if not self.array_new:
            self.array_mod.use_constant_offset = False
            self.array_mod.use_relative_offset = False
            self.array_mod.use_object_offset = True
            self.array_mod.offset_object = self.empty
            self.array_mod.count = self.segments

        # Move object origin
        # self.cursor_prev = bool(self.cursor)
        if event.ctrl and not event.shift and event.type == 'LEFTMOUSE':
            self.origin_mode = origin_modes.cursor

        if self.empty_new:
            self.set_origin(context)
        elif self.origin_outside_bounds(context): #why is this a thing?
            self.origin_mode = origin_modes.cursor

        if self.from_empty:
            self.origin_mode = origin_modes.original
            self.displace_mod.show_viewport = False
            self.array_mod.count = self.shared_avg_segments()

        # Create driver
        self.direction_prev = str(self.direction)
        self.axis_prev = str(self.axis)
        self.create_driver(context, self.rotation)

        # Set internal variables
        self.adjusting = 'NONE' if self.origin_mode == origin_modes.cursor else  'DISPLACE'
        self.displace_center = float(self.displace)
        self.displace_cursor = float(self.displace)
        self.displace_original = float(self.displace)
        self.set_displace(context)

        # Base Systems
        self.master = Master(context=context)
        self.master.only_use_fast_ui = True
        self.base_controls = Base_Modal_Controls(context, event)
        self.original_tool_shelf, self.original_n_panel = collapse_3D_view_panels()
        self.draw_handle = bpy.types.SpaceView3D.draw_handler_add(self.safe_draw_shader, (context,), 'WINDOW', 'POST_PIXEL')

        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}


    def modal(self, context, event):

        # Base Systems
        self.master.receive_event(event=event)
        self.base_controls.update(context, event)
        mouse_warp(context, event)

        if self.base_controls.pass_through:
            return {'PASS_THROUGH'}

        elif event.type == 'Z' and (event.shift or event.alt):
            return {'PASS_THROUGH'}

        elif self.base_controls.confirm:
            self.confirm(context)
            self.report({'INFO'}, "Finished")
            self.remove_shader()
            collapse_3D_view_panels(self.original_tool_shelf, self.original_n_panel)
            self.master.run_fade()
            return {'FINISHED'}

        elif self.base_controls.cancel:
            self.cancel(context)
            self.report({'INFO'}, "Cancelled")
            self.remove_shader()
            collapse_3D_view_panels(self.original_tool_shelf, self.original_n_panel)
            self.master.run_fade()
            return {'CANCELLED'}

        elif event.type == 'A' and event.value == 'PRESS':
            self.displace_mod.show_viewport = not self.displace_mod.show_viewport
            self.report({'INFO'}, f"{'Enabled' if self.displace_mod.show_viewport else 'Disabled'} Displacement")

        elif event.type == 'S' and event.value == 'PRESS':
            self.adjusting = 'NONE' if self.adjusting == 'SEGMENTS' else 'SEGMENTS'
            self.report({'INFO'}, f"{'Started' if self.adjusting == 'SEGMENTS' else 'Stopped'} Adjusting Segments")

        elif event.type == 'D' and event.value == 'PRESS':
            self.adjusting = 'NONE' if self.adjusting == 'DISPLACE' else 'DISPLACE'
            self.report({'INFO'}, f"{'Started' if self.adjusting == 'DISPLACE' else 'Stopped'} Adjusting Displace")

        elif event.type == 'Z' and event.value == 'PRESS':
            self.direction = "YZX"["XYZ".find(self.direction)]
            self.displace_mod.direction = self.direction
            self.report({'INFO'}, f"Displace Axis: {self.direction}")

        elif event.type == 'X' and event.value == 'PRESS':
            self.direction = "YZX"["XYZ".find(self.direction)]
            self.displace_mod.direction = self.direction
            self.axis = "YZX"["XYZ".find(self.axis)]
            self.create_driver(context, self.rotation)
            self.report({'INFO'}, f"Rotate Axis: {self.axis}")

        elif event.type == 'R' and event.value == 'PRESS':
            rotations = ['360', '180', '90', '60', '45', '30', '15']
            self.index += 1
            if self.index + 1 == len(rotations):
                self.index = 0
            self.rotation = int(rotations[self.index])
            self.report({'INFO'}, F'Rotation : {self.rotation}')

        elif event.type in {'ZERO', 'NUMPAD_0'} and event.value == "PRESS":
            self.displace_mod.strength = 0
            self.displace_buffer = 0
            bpy.ops.hops.display_notification(info=F'Displace: {self.displace_mod.strength}')

        elif event.type == 'C' and event.value == 'PRESS' and not self.from_empty:
            self.adjusting = 'NONE'
            self.origin_mode = origin_modes((self.origin_mode.value + 1) % len(origin_modes.__members__))
            self.set_displace(context)
            self.set_origin(context)
            self.create_driver(context, self.rotation)
            self.report({'INFO'}, f"Origin: {mode_string[self.origin_mode]}")
            bpy.ops.hops.display_notification(info=F'Origin: {mode_string[self.origin_mode]}')

        elif self.base_controls.scroll and event.shift:
            self.rotation += self.base_controls.scroll
            self.report({'INFO'}, F'Rotation : {self.rotation}')

        elif self.base_controls.scroll:
            self.segments_buffer += self.base_controls.scroll
            self.segments_buffer = max(self.segments_buffer, 1)
            self.segments = round(self.segments_buffer)
            self.array_mod.count = self.segments
            self.report({'INFO'}, f"Segments: {self.segments}")

        elif event.type == 'MOUSEMOVE' and self.adjusting == 'SEGMENTS':
            offset = self.base_controls.mouse
            self.segments_buffer += offset
            self.segments_buffer = max(self.segments_buffer, 1)
            self.segments = round(self.segments_buffer)
            self.array_mod.count = self.segments

        elif event.type == 'MOUSEMOVE' and self.adjusting == 'DISPLACE':
            offset = self.base_controls.mouse * 2.5
            self.displace_buffer -= offset
            digits = 2 if event.ctrl and event.shift else 1 if event.ctrl else 3
            self.displace = round(self.displace_buffer, digits)
            self.displace_mod.strength = self.displace

        self.create_driver(context, self.rotation)
        self.draw_master(context=context)
        context.area.tag_redraw()
        return {"RUNNING_MODAL"}


    def set_displace(self, context):
        if self.origin_mode == origin_modes.cursor:
            self.displace_center = self.displace_original = float(self.displace)
            self.displace_buffer = self.displace_cursor
            self.displace = self.displace_cursor
            self.displace_mod.strength = self.displace_cursor

        elif self.origin_mode == origin_modes.center:
            self.displace_original = self.displace_cursor = float(self.displace)
            self.displace_buffer = self.displace_center
            self.displace = self.displace_center
            self.displace_mod.strength = self.displace_center

        else:
            self.displace_center = self.displace_cursor = float(self.displace)
            self.displace_buffer = self.displace_original
            self.displace = self.displace_original
            self.displace_mod.strength = self.displace_original


    def set_origin(self, context):
        if self.to_selection:
            object.set_origin(self.obj, self.active_matrix)
        elif self.origin_mode == origin_modes.cursor:
            bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='BOUNDS')
        elif self.origin_mode == origin_modes.center:
            bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
        elif self.origin_mode == origin_modes.original:
            object.set_origin(self.obj, self.obj_matrix)

        if not self.from_empty:
            self.empty.parent = None
            self.empty.parent = self.obj
            self.empty.location = (0,0,0)
            self.empty.rotation_euler = (0,0,0)
            self.empty.scale = (1,1,1)


    def origin_outside_bounds(self, context):
        temp = bpy.data.objects.new("Bounding Box", self.obj.data)
        bb = temp.bound_box[:]
        bpy.data.objects.remove(temp)
        x = bb[6][0] < 0 or bb[0][0] > 0
        y = bb[6][1] < 0 or bb[0][1] > 0
        z = bb[6][2] < 0 or bb[0][2] > 0
        return x or y or z


    def create_driver(self, context, rotation):
        if self.reuse_driver:
            return

        [self.empty.driver_remove("rotation_euler", i) for i in range(3)]
        self.empty.rotation_euler = (0,0,0)
        index = "XYZ".find(self.axis)
        self.driver = self.empty.driver_add("rotation_euler", index).driver
        count = self.driver.variables.new()
        count.name = "count"
        count.targets[0].id = self.obj
        count.targets[0].data_path = f"modifiers[\"{self.array_mod.name}\"].count"
        self.driver.expression = f"{math.radians(self.rotation)} / count"


    def shared_avg_segments(self):
        if not self.empty: return
        divisor = math.degrees(self.empty.rotation_euler.z)
        if divisor <= 0: divisor = 1
        ret_val = 360 / divisor
        return int(ret_val) + 1


    def confirm(self, context):
        modifier.sort(self.obj, types=['WEIGHTED_NORMAL'], last=True)

        if addon.preference().property.workflow == 'DESTRUCTIVE':
            modifier.apply(self.obj, self.displace_mod)
            modifier.apply(self.obj, self.array_mod)
            bpy.data.objects.remove(self.empty)

        self.from_empty = False


    def cancel(self, context):
        self.direction = self.direction_prev
        self.axis = self.axis_prev

        object.set_origin(self.obj, self.obj_matrix)
        if not self.from_empty:
            self.empty.parent = None
            self.empty.parent = self.obj
            self.empty.location = (0,0,0)
            self.empty.rotation_euler = (0,0,0)
            self.empty.scale = (1,1,1)

        if self.displace_new:
            self.obj.modifiers.remove(self.displace_mod)
        else:
            self.displace_mod.show_viewport = self.displace_settings["show_viewport"]
            self.displace_mod.mid_level = self.displace_settings["mid_level"]
            self.displace_mod.direction = self.displace_settings["direction"]
            self.displace_mod.strength = self.displace_settings["strength"]

        if self.array_new:
            self.obj.modifiers.remove(self.array_mod)
        else:
            self.array_mod.use_constant_offset = self.array_settings["use_constant_offset"]
            self.array_mod.use_relative_offset = self.array_settings["use_relative_offset"]
            self.array_mod.use_object_offset = self.array_settings["use_object_offset"]
            self.array_mod.offset_object = self.array_settings["offset_object"]
            self.array_mod.count = self.array_settings["count"]

        if self.empty_new:
            bpy.data.objects.remove(self.empty)

        elif self.from_empty and not self.reuse_driver:
            for i in range(3) : self.empty.driver_remove("rotation_euler", i)

        else:
            self.create_driver(context, self.rotation)

        for obj, sel_state in self.selected_states:
            obj.select_set(sel_state)

        self.from_empty = False


    def draw_master(self, context):

        # Start
        self.master.setup()

        ########################
        #   Fast UI
        ########################

        if self.master.should_build_fast_ui():

            # Main
            win_list = []
            if addon.preference().ui.Hops_modal_fast_ui_loc_options != 1: #Fast Floating
                win_list.append(f"{self.axis}")
                win_list.append(f"{self.segments}")
                win_list.append(f"{self.displace:.2f}")
            else:
                win_list.append("Radial Array")
                win_list.append(f"{self.axis}")
                win_list.append(f"{self.segments}")
                win_list.append(f"{self.displace:.3f}")

            # Help
            help_items = {"GLOBAL" : [], "STANDARD" : []}

            help_items["GLOBAL"] = [
                ("M", "Toggle mods list"),
                ("H", "Toggle help"),
                ("~", "Toggle UI Display Type"),
                ("O", "Toggle viewport rendering")]

            help_items["STANDARD"] = [
                ("Scroll", "Increment Segments"),
                ("Shift + Scroll", f"Adjust Rotation  {self.rotation}°"),
                ("A",      "Toggle Displace"),
                ("0",      "Set Displace To 0"),
                ("S",      "Adjust Segments"),
                ("D",      "Adjust Displace"),
                ("Z",      "Increment Displace Axis"),
                ("R",      "Change radial to 180/90/45/30"),
                ("X",      "Increment Rotate Axis"),
                ("C",      "Array Around Object Origin / 3D Cursor / Object Center")]

            # Mods
            active_mod = ""
            if self.displace_mod != None:
                active_mod = self.displace_mod.name
            mods_list = get_mods_list(mods=bpy.context.active_object.modifiers)

            self.master.receive_fast_ui(win_list=win_list, help_list=help_items, image="ArrayCircle", mods_list=mods_list, active_mod_name=active_mod)

        # Finished
        self.master.finished()

    # --- SHADER --- #

    def safe_draw_shader(self, context):
        method_handler(self.draw_shader,
            arguments = (context,),
            identifier = 'UI Framework',
            exit_method = self.remove_shader)


    def remove_shader(self):
        '''Remove shader handle.'''

        if self.draw_handle:
            self.draw_handle = bpy.types.SpaceView3D.draw_handler_remove(self.draw_handle, "WINDOW")


    def draw_shader(self, context):
        '''Draw shader handle.'''

        draw_modal_frame(context)
