import bpy, bmesh, mathutils, math, copy, gpu, time
from gpu_extras.batch import batch_for_shader
from mathutils import Vector, Matrix
from . import operator
from .. meshtools.applymod import apply_mod
from ... utils.blender_ui import get_dpi, get_dpi_factor
from ... utility import addon
from ... ui_framework.utils.mods_list import get_mods_list
from ... ui_framework.master import Master
from ... utility.renderer import cycles
from ... utility import collections,  object
from ... utility import math as hops_math
from ... utility.base_modal_controls import Base_Modal_Controls
from ... utils.objects import set_active
from ... utils.toggle_view3d_panels import collapse_3D_view_panels
from ... utils.modal_frame_drawing import draw_modal_frame
from ... utils.cursor_warp import mouse_warp
from ... utility import method_handler

##############################################################################
# Draw Data
##############################################################################

HANDLE_3D = None

class Data:
    # States
    draw_modal_running = False
    dice_modal_running = False
    reset_modal = False
    exit_with_no_fade = False

    # Draw Data
    draw_x = False
    draw_y = False
    draw_z = False
    xp_line_data = []
    xp_point_data = []
    yp_line_data = []
    yp_point_data = []
    zp_line_data = []
    zp_point_data = []
    xp_ticks = []
    yp_ticks = []
    zp_ticks = []

    # Settings
    see_though = False

    @staticmethod
    def reset_data():
        Data.draw_x = False
        Data.draw_y = False
        Data.draw_z = False
        Data.xp_line_data = []
        Data.xp_point_data = []
        Data.yp_line_data = []
        Data.yp_point_data = []
        Data.zp_line_data = []
        Data.zp_point_data = []
        Data.xp_ticks = []
        Data.yp_ticks = []
        Data.zp_ticks = []

    @staticmethod
    def reset_states():
        Data.draw_modal_running = False
        Data.dice_modal_running = False
        Data.reset_modal = False
        Data.exit_with_no_fade = False

description = """Dice Loopcut

LMB - Dice on last used axes
Shift + LMB - Dice active from selection
Ctrl + LMB - Dice on all axes
Alt + LMB - Smart Apply Dice (applies select modifiers)
"""

class HOPS_OT_BoolDice(bpy.types.Operator):
    bl_idname = "hops.bool_dice"
    bl_label = "Hops Boolean Dice"
    bl_options = {'REGISTER', 'UNDO', 'BLOCKING', 'INTERNAL'}
    bl_description = description

    axis: bpy.props.EnumProperty(
        name="Axis",
        description="What axis to dice on",
        items=[
            ('X', "X", "Dice on the X axis"),
            ('Y', "Y", "Dice on the Y axis"),
            ('Z', "Z", "Dice on the Z axis")],
        default='X')

    axes: bpy.props.BoolVectorProperty(
        name="Axes",
        description="Which axis to dice on",
        default=(True, False, False),
        size=3)

    count: bpy.props.IntProperty(
        name="Count",
        description="How many cutting planes to make on each axis",
        min=1,
        soft_max=100,
        default=5)

    use_knife_project: bpy.props.BoolProperty(
        name="Use Knife Project",
        description="Otherwise use mesh intersect",
        default=True)

    smart_apply: bpy.props.BoolProperty(
        name="Smart Apply",
        description="Uses smart apply prior to dice to ensure dicing is received",
        default=False)

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'MESH' and obj.mode in {'OBJECT', 'EDIT'}


    def draw(self, context):

        axes = ", ".join(a for i,a in enumerate("XYZ") if self.axes[i])
        self.layout.label(text=f"Axes: {axes}")
        self.layout.label(text=f"Segments: {self.count}")
        self.layout.label(text=f"Method: {'Knife Project' if self.use_knife_project else 'Mesh Intersect'}")


    def execute(self, context):
        # Without execute, draw doesn't work
        return {'FINISHED'}


    def invoke(self, context, event):

        # ---------- Check for correct context ----------
        if context.area.type != 'VIEW_3D':
            self.report({'WARNING'}, 'Launch from 3D view')
            return {'CANCELLED'}

        # ---------- Controls ----------
        self.modal_scale = addon.preference().ui.Hops_modal_scale
        self.base_controls = Base_Modal_Controls(context, event)
        self.smart_apply = event.alt or addon.preference().property.smart_apply_dice != 'NONE'
        self.adjusting = 'NONE' if event.ctrl and event.type == 'LEFTMOUSE' else addon.preference().property.dice_adjust
        self.to_twist = False
        self.mouse_prev_x = event.mouse_region_x
        self.mouse_start_x = event.mouse_region_x
        self.mouse_start_y = event.mouse_region_y

        # ---------- Props ----------
        self.prefs = addon.preference().property
        self.obj = context.active_object
        self.mode = self.obj.mode
        self.selected = [o for o in context.selected_objects if o.type == 'MESH']
        self.sources = self.selected[:]
        self.big_box = False
        self.bound_box = []
        self.size = tuple
        self.axis_buffer = float("XYZ".find(self.axis))
        self.count_buffer = self.count
        self.use_knife_project = addon.preference().property.dice_method == 'KNIFE_PROJECT'
        self.update_draw_data = True
        self.curves = [o for o in context.selected_objects if o.type == 'CURVE']
        self.joined = False
        self.display_join_notification = True if len(self.selected) + len(self.curves) > 1 else False

        # ---------- Setup ----------
        self.setup(context, event)

        # ---------- Drawing / Menus ----------
        self.master = Master(context=context)
        self.master.only_use_fast_ui = True
        self.original_tool_shelf, self.original_n_panel = collapse_3D_view_panels()
        self.draw_handle_2d = bpy.types.SpaceView3D.draw_handler_add(self.safe_draw_2d, (context,), 'WINDOW', 'POST_PIXEL')

        # Draw modal
        if Data.draw_modal_running == False:
            bpy.ops.hops.draw_dice('INVOKE_DEFAULT')
        else:
            Data.reset_modal = True
        Data.dice_modal_running = True
        Data.reset_data()
        Data.see_though = False

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


    def setup(self, context, event):

        self.obj.select_set(True)

        # Smart apply mods
        if event.alt or addon.preference().property.smart_apply_dice == 'SMART_APPLY':
            mode = context.mode
            bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
            for obj in self.selected:
                apply_mod(self, obj, clear_last=False)
            bpy.ops.hops.display_notification(info=f'Smart Apply' )
            self.report({'INFO'}, F'Smart Applied')
            if mode == 'EDIT_MESH':
                bpy.ops.object.mode_set(mode='EDIT', toggle=False)

        # Convert to mesh
        elif addon.preference().property.smart_apply_dice == 'APPLY':
            for obj in self.selected:
                bpy.ops.object.convert(target='MESH')
                bpy.ops.mesh.customdata_custom_splitnormals_clear()
            bpy.ops.hops.display_notification(info=f'Converted To Mesh' )
            self.report({'INFO'}, F'Converted To Mesh')

        # Filter out active object from sources
        if event.shift and len(self.sources) > 1:
            self.sources.remove(self.obj)

        # Encompass all objects
        if len(self.sources) > 1:
            self.big_box = True
            bound_boxes = []
            if context.mode == "EDIT_MESH":
                for o in self.sources:
                    o.update_from_editmode()
                    bound_boxes.extend([o.matrix_world @ v.co for v in o.data.vertices if v.select])
            if context.mode == "OBJECT" or len(bound_boxes)<2 :
                for o in self.sources:
                    bound_boxes.extend( self.get_bound_box(o, o.matrix_world))
            self.bound_box = hops_math.coords_to_bounds(bound_boxes)

        # Only use active obj bounds
        else:
            self.big_box = False
            if context.mode == "EDIT_MESH":
                self.sources[0].update_from_editmode()
                bounds = [v.co for v in self.sources[0].data.vertices if v.select]
                if len(bounds) > 1:
                    self.bound_box = hops_math.coords_to_bounds(bounds)
            if context.mode == "OBJECT" or len(bounds) < 2:
                self.bound_box = self.get_bound_box(self.sources[0])
                set_active(self.sources[0], select=True, only_select=True)

        # Get size of bounds
        self.size = self.get_size(context, self.bound_box)

        # Cut planes
        self.plane_x = self.create_plane(context, 'X')
        self.plane_y = self.create_plane(context, 'Y')
        self.plane_z = self.create_plane(context, 'Z')

        # Preset axis
        if event.type == 'LEFTMOUSE' and event.ctrl:
            self.axes[0] = True
            self.axes[1] = True
            self.axes[2] = True

        # Hide all planes
        self.plane_x.hide_set(True)
        self.plane_y.hide_set(True)
        self.plane_z.hide_set(True)


    def modal(self, context, event):

        # Base Systems
        self.master.receive_event(event=event)
        self.base_controls.update(context, event)
        mouse_warp(context, event)
        original_remove_setting = addon.preference().property.Hops_sharp_remove_cutters

        # Free navigation
        if event.type == 'MIDDLEMOUSE':
            return {'PASS_THROUGH'}

        # Allow wire / wire shaded
        elif event.type == 'Z' and (event.shift or event.alt):
            return {'PASS_THROUGH'}

        # Confirm
        elif event.type in {'LEFTMOUSE', 'SPACE'}:

            if self.to_twist:
                self.join_objs(context, event)

            # Unhide cutter planes
            self.plane_x.hide_set(not self.axes[0])
            self.plane_y.hide_set(not self.axes[1])
            self.plane_z.hide_set(not self.axes[2])

            # Apply cutters
            if event.shift == False:
                if self.obj in self.sources:
                    targets = self.sources
                else:
                    targets = [self.obj]

                for obj in targets:
                    set_active(obj, select=True, only_select=True)
                    self.dice_target = obj
                    if self.axes[0]:
                        self.knife(context, 'X')
                    if self.axes[1]:
                        self.knife(context, 'Y')
                    if self.axes[2]:
                        self.knife(context, 'Z')

                self.remove_plane(context, self.plane_x)
                self.remove_plane(context, self.plane_y)
                self.remove_plane(context, self.plane_z)

            # Create cutters and dont perform cut
            elif event.shift == True:
                if not self.axes[0]:
                    self.remove_plane(context, self.plane_x)
                else:
                    collections.unlink_obj(context, self.plane_x)
                    collections.link_obj(context, self.plane_x, "Cutters")

                if not self.axes[1]:
                    self.remove_plane(context, self.plane_y)
                else:
                    collections.unlink_obj(context, self.plane_y)
                    collections.link_obj(context, self.plane_y, "Cutters")

                if not self.axes[2]:
                    self.remove_plane(context, self.plane_z)
                else:
                    collections.unlink_obj(context, self.plane_z)
                    collections.link_obj(context, self.plane_z, "Cutters")

            set_active(self.obj)

            for obj in self.selected:
                obj.select_set(True)

            if self.mode == 'EDIT':
                bpy.ops.object.mode_set(mode='OBJECT')
                bpy.ops.object.mode_set(mode='EDIT')

            self.obj.show_wire = False

            self.remove_shader()
            collapse_3D_view_panels(self.original_tool_shelf, self.original_n_panel)
            self.master.run_fade()

            if self.to_twist == True:
                Data.exit_with_no_fade = True
                bpy.ops.hops.array_twist('INVOKE_DEFAULT')

            Data.dice_modal_running = False

            # Draw wire mesh
            if Data.exit_with_no_fade == False:
                bpy.ops.hops.draw_wire_mesh_launcher('INVOKE_DEFAULT', target='SELECTED')

            self.report({'INFO'}, "Finished")
            return {'FINISHED'}

        # Cancel
        elif event.type in {'RIGHTMOUSE', 'ESC'}:

            self.remove_plane(context, self.plane_x)
            self.remove_plane(context, self.plane_y)
            self.remove_plane(context, self.plane_z)

            set_active(self.obj)
            for obj in self.selected:
                obj.select_set(True)

            self.remove_shader()
            collapse_3D_view_panels(self.original_tool_shelf, self.original_n_panel)
            self.master.run_fade()

            Data.exit_with_no_fade = True
            Data.dice_modal_running = False

            self.report({'INFO'}, "Cancelled")
            return {'CANCELLED'}

        # Toggle mouse axis switching
        elif event.type == 'A' and event.value == 'PRESS':
            self.adjusting = 'NONE' if self.adjusting == 'AXIS' else 'AXIS'
            self.report({'INFO'}, f"{'Started' if self.adjusting != 'NONE' else 'Stopped'} Adjusting Axis")

        # Mouse adjust segments
        elif event.type == 'S' and event.shift and event.value == 'PRESS':
            self.adjusting = 'NONE' if self.adjusting == 'SEGMENTS' else 'SEGMENTS'
            self.report({'INFO'}, f"{'Started' if self.adjusting != 'NONE' else 'Stopped'} Adjusting Segments")

        # Smart apply
        elif event.type == 'S' and event.value == 'PRESS':
            if original_remove_setting:
                addon.preference().property.Hops_sharp_remove_cutters = False
            bpy.ops.hops.apply_modifiers('INVOKE_DEFAULT')
            addon.preference().property.Hops_sharp_remove_cutters = original_remove_setting

            # Rest modal
            self.remove_plane(context, self.plane_x)
            self.remove_plane(context, self.plane_y)
            self.remove_plane(context, self.plane_z)
            set_active(self.obj)
            for obj in self.selected:
                obj.select_set(True)
            self.setup(context, event)

            self.report({'INFO'}, f"Smart Apply")

        # Exit to twist
        elif event.type == 'T' and event.value == 'PRESS':
            obj = bpy.context.object
            if self.to_twist == False:
                self.to_twist = True
                for mod in obj.modifiers:
                    if mod.type == 'BOOLEAN':
                        if original_remove_setting:
                            addon.preference().property.Hops_sharp_remove_cutters = False
                        for obj in bpy.context.selected_objects:
                            apply_mod(self, obj, clear_last=False)
                        addon.preference().property.Hops_sharp_remove_cutters = original_remove_setting
            else:
                self.to_twist = not self.to_twist
            self.report({'INFO'}, f"To_Twist {self.to_twist}")

        # Cycle axis with mouse
        elif event.type == 'MOUSEMOVE' and self.adjusting == 'AXIS':
            self.update_draw_data = True
            divisor = self.modal_scale * (2500 if event.shift else 250)
            offset = event.mouse_region_x - self.mouse_prev_x

            self.axis_buffer -= offset / divisor / get_dpi_factor()
            self.axis = "XYZ"[round(self.axis_buffer) % 3]

            self.axes[0] = self.axis == 'X'
            self.axes[1] = self.axis == 'Y'
            self.axes[2] = self.axis == 'Z'

        # Adjust segments with mouse
        elif event.type == 'MOUSEMOVE' and self.adjusting == 'SEGMENTS':
            self.update_draw_data = True
            divisor = self.modal_scale * (1000 if event.shift else 100)
            offset = event.mouse_region_x - self.mouse_prev_x

            self.count_buffer -= offset / divisor / get_dpi_factor()
            self.count_buffer = max(self.count_buffer, 1)
            self.count = round(self.count_buffer)

            for index, plane in enumerate([self.plane_x, self.plane_y, self.plane_z]):
                distance = self.size[index] / (self.count + 1)
                plane.modifiers["Array"].count = self.count
                plane.modifiers["Array"].constant_offset_displace[index] = distance
                plane.modifiers["Displace"].strength = distance

        # Increase segments
        elif self.base_controls.scroll != 0:
            self.update_draw_data = True
            self.count_buffer += self.base_controls.scroll
            self.count_buffer = max(self.count_buffer, 1)
            self.count = round(self.count_buffer)

            for index, plane in enumerate([self.plane_x, self.plane_y, self.plane_z]):
                distance = self.size[index] / (self.count + 1)
                plane.modifiers["Array"].count = self.count
                plane.modifiers["Array"].constant_offset_displace[index] = distance
                plane.modifiers["Displace"].strength = distance

        # Toggle wireframe
        elif event.type == 'W' and event.value == 'PRESS':
            self.obj.show_wire = not self.obj.show_wire
            wire ={True:"ON", False:"OFF"}
            self.report({'INFO'}, F'Wireframe:{wire[self.obj.show_wire]}')

        # Toggle X axis
        elif event.type == 'X' and event.value == 'PRESS' and (self.axes[1] or self.axes[2]):
            self.update_draw_data = True
            self.adjusting = 'NONE'
            self.axes[0] = not self.axes[0]

            if self.axes[0]:
                self.axis = 'X'
                self.axis_buffer = 0

            self.report({'INFO'}, f"{'Enabled' if self.axes[0] else 'Disabled'} Axis X")

        # Toggle Y axis
        elif event.type == 'Y' and event.value == 'PRESS' and (self.axes[0] or self.axes[2]):
            self.update_draw_data = True
            self.adjusting = 'NONE'
            self.axes[1] = not self.axes[1]

            if self.axes[1]:
                self.axis = 'Y'
                self.axis_buffer = 1

            self.report({'INFO'}, f"{'Enabled' if self.axes[1] else 'Disabled'} Axis Y")

        # Toggle Z axis
        elif event.type == 'Z' and event.value == 'PRESS' and (self.axes[0] or self.axes[1]):
            self.update_draw_data = True
            self.adjusting = 'NONE'
            self.axes[2] = not self.axes[2]

            if self.axes[2]:
                self.axis = 'Z'
                self.axis_buffer = 2

            self.report({'INFO'}, f"{'Enabled' if self.axes[2] else 'Disabled'} Axis Z")

        # Swap bisect methods
        elif event.type == 'Q' and event.value == 'PRESS':
            self.use_knife_project = not self.use_knife_project
            self.report({'INFO'}, f"Method: {'Knife Project' if self.use_knife_project else 'Mesh Intersect'}")

        # Presets for dice count
        elif event.type in {'ONE', 'TWO', 'THREE', 'FOUR'} and event.value == 'PRESS':
            self.update_draw_data = True
            if event.type == 'ONE':
                self.count = self.count_buffer = 7
            elif event.type == 'TWO':
                self.count = self.count_buffer = 15
            elif event.type == 'THREE':
                self.count = self.count_buffer = 23
            elif event.type == 'FOUR':
                self.count = self.count_buffer = 31

            for index, plane in enumerate([self.plane_x, self.plane_y, self.plane_z]):
                distance = self.size[index] / (self.count + 1)
                plane.modifiers["Array"].count = self.count
                plane.modifiers["Array"].constant_offset_displace[index] = distance
                plane.modifiers["Displace"].strength = distance

        # Drawing : See through toggle
        elif event.type == 'N' and event.value == "PRESS":
            Data.see_though = not Data.see_though

        # Drawing : Angle Ticks toggle
        elif event.type == 'B' and event.value == "PRESS":
            if self.prefs.dice_wire_type == 'DOTS':
                self.prefs.dice_wire_type = 'LINES'
            elif self.prefs.dice_wire_type == 'LINES':
                self.prefs.dice_wire_type = 'TICKS'
            elif self.prefs.dice_wire_type == 'TICKS':
                self.prefs.dice_wire_type = 'DOTS'

        # Join
        elif event.type == 'J' and event.value == "PRESS" and not event.shift and not event.ctrl:
            self.join_objs(context, event)

        # Update draw data
        if self.update_draw_data == True:
            self.update_draw_data = False
            self.setup_draw_data(context)

        self.mouse_prev_x = event.mouse_region_x
        self.draw_master(context=context)
        context.area.tag_redraw()
        return {'RUNNING_MODAL'}


    def draw_master(self, context):

        # Start
        self.master.setup()

        if self.master.should_build_fast_ui():
            win_list = []
            help_list = []
            mods_list = []
            active_mod = ""

            # Main
            if addon.preference().ui.Hops_modal_fast_ui_loc_options != 1:
                axes = ", ".join(a for i,a in enumerate("XYZ") if self.axes[i])
                win_list.append(axes)
                win_list.append(str(self.count))
                if self.to_twist == True:
                    win_list.append('To_Twist')
                if len(context.active_object.modifiers[:]) >= 1:
                    win_list.append(f'[S]mart Apply')
                win_list.append(f"{'Knife Project' if self.use_knife_project else 'Mesh Intersect'}")
            else:
                # Main
                axes = ", ".join(a for i,a in enumerate("XYZ") if self.axes[i])
                win_list.append(axes)
                win_list.append(str(self.count))
                win_list.append(f"Method: {'Knife Project' if self.use_knife_project else 'Mesh Intersect'}")
                if self.to_twist == True:
                    win_list.append(f'To_Twist {self.to_twist}')
                if len(context.active_object.modifiers[:]) >= 1:
                    win_list.append(f'S -  Smart Apply')

            # Help
            help_items = {"GLOBAL" : [], "STANDARD" : []}

            help_items["GLOBAL"] = [
                ("M", "Toggle mods list"),
                ("H", "Toggle help"),
                ("~", "Toggle UI Display Type"),
                ("O", "Toggle viewport rendering")
            ]

            help_items["STANDARD"] = [
                ("J",                   "Join objects"),
                ("B",                   f"Shader draw type : {self.prefs.dice_wire_type}"),
                ("N",                   f"See through : {Data.see_though}"),
                ("Shift + LMB / Space", "Create cutters but don't perform cut"),
                ("X / Y / Z",           "Toggle dicing per axis"),
                ("1 / 2 / 3 / 4",       "Set segments to 7 / 15 / 23 / 31"),
                ("Shift + S",           "Adjust Segments"),
                ("T",                   "Twist / Smart Apply"),
                ("S",                   "Smart Apply"),
                ("W",                   "Show Wire"),
                ("Q",                   "Toggle Knife Project / Mesh Intersect")
            ]

            # Mods
            mods_list = get_mods_list(mods=bpy.context.active_object.modifiers)

            self.master.receive_fast_ui(win_list=win_list, help_list=help_items, image="Dice", mods_list=mods_list, active_mod_name=active_mod)

        # Finished
        self.master.finished()

    ####################################################
    #   Utils
    ####################################################

    def get_bound_box(self, obj, matrix=Matrix()):
        temp = bpy.data.objects.new("Bounding Box", obj.data)
        bound_box = object.bound_coordinates(temp, matrix)
        bpy.data.objects.remove(temp)
        return bound_box


    def get_size(self, context, bb):
        size_x = bb[6][0] - bb[0][0]
        size_y = bb[6][1] - bb[0][1]
        size_z = bb[6][2] - bb[0][2]
        return (size_x, size_y, size_z)


    def create_plane(self, context, axis):
        bb = [list(v) for v in self.bound_box]

        if axis != 'X':
            bb[0][0] -= 0.01
            bb[1][0] -= 0.01
            bb[2][0] -= 0.01
            bb[3][0] -= 0.01
            bb[4][0] += 0.01
            bb[5][0] += 0.01
            bb[6][0] += 0.01
            bb[7][0] += 0.01

        if axis != 'Y':
            bb[0][1] -= 0.01
            bb[1][1] -= 0.01
            bb[2][1] += 0.01
            bb[3][1] += 0.01
            bb[4][1] -= 0.01
            bb[5][1] -= 0.01
            bb[6][1] += 0.01
            bb[7][1] += 0.01

        if axis != 'Z':
            bb[0][2] -= 0.01
            bb[1][2] += 0.01
            bb[2][2] += 0.01
            bb[3][2] -= 0.01
            bb[4][2] -= 0.01
            bb[5][2] += 0.01
            bb[6][2] += 0.01
            bb[7][2] -= 0.01

        if axis == 'X':
            bb = [bb[0], bb[1], bb[2], bb[3]]
        if axis == 'Y':
            bb = [bb[0], bb[4], bb[5], bb[1]]
        if axis == 'Z':
            bb = [bb[0], bb[3], bb[7], bb[4]]

        plane_bm = bmesh.new()
        for vert in bb:
            plane_bm.verts.new(vert)
        plane_bm.faces.new(plane_bm.verts)

        plane_mesh = bpy.data.meshes.new(f"Cutter {axis}")
        plane_bm.to_mesh(plane_mesh)
        plane_bm.free()

        if self.obj in self.sources:
            plane_obj = self.obj.copy()
        else:
            plane_obj = self.sources[0].copy()
        for col in self.obj.users_collection:
            if col not in plane_obj.users_collection:
                col.objects.link(plane_obj)

        plane_obj.name = f"Cutter {axis}"
        plane_obj.data = plane_mesh
        plane_obj.modifiers.clear()
        plane_obj.select_set(False)

        cycles.hide_preview(context, plane_obj)
        plane_obj.hops.status = 'BOOLSHAPE'
        plane_obj.display_type = 'WIRE'
        plane_obj.hide_render = True

        array = plane_obj.modifiers.new("Array", 'ARRAY')
        array.use_relative_offset = False
        array.use_constant_offset = True
        array.fit_type = 'FIXED_COUNT'
        array.count = self.count

        displace = plane_obj.modifiers.new("Displace", 'DISPLACE')
        displace.direction = axis
        displace.mid_level = 0.0

        axis = "XYZ".find(axis)
        distance = self.size[axis] / (self.count + 1)
        array.constant_offset_displace = (0, 0, 0)
        array.constant_offset_displace[axis] = distance
        displace.strength = distance

        if self.big_box:
            object.clear_transforms(plane_obj)

        return plane_obj


    def remove_plane(self, context, obj):
        mesh = obj.data
        bpy.data.objects.remove(obj)
        bpy.data.meshes.remove(mesh)


    def knife(self, context, axis):
        bpy.ops.object.mode_set(mode='OBJECT')

        self.plane_x.select_set(axis == 'X')
        self.plane_y.select_set(axis == 'Y')
        self.plane_z.select_set(axis == 'Z')

        if self.use_knife_project:
            self.knife_project(context, axis)
        else:
            self.knife_intersect(context, axis)

        bpy.ops.object.mode_set(mode=self.mode)


    def knife_project(self, context, axis):
        perspective = copy.copy(context.region_data.view_perspective)
        camera_zoom = copy.copy(context.region_data.view_camera_zoom)
        distance = copy.copy(context.region_data.view_distance)
        location = copy.copy(context.region_data.view_location)
        rotation = copy.copy(context.region_data.view_rotation)

        view = {'X': 'FRONT', 'Y': 'TOP', 'Z': 'RIGHT'}[axis]
        if axis == 'X':
            plane = self.plane_x
        elif axis == 'Y':
            plane = self.plane_y
        elif axis == 'Z':
            plane = self.plane_z
        set_active(plane)
        bpy.ops.view3d.view_axis(type=view, align_active=True)
        set_active(self.dice_target)
        context.region_data.view_perspective = 'ORTHO'
        context.region_data.update()

        plane.select_set(False)
        bpy.ops.object.mode_set(mode='EDIT')
        plane.select_set(True)
        bpy.ops.mesh.knife_project(cut_through=True)
        bpy.ops.object.mode_set(mode='OBJECT')

        context.region_data.view_perspective = perspective
        context.region_data.view_camera_zoom = camera_zoom
        context.region_data.view_distance = distance
        context.region_data.view_location = location
        context.region_data.view_rotation = rotation
        context.region_data.update()

        if perspective == 'ORTHO':
            axis = [int(math.degrees(a)) for a in mathutils.Quaternion(rotation).to_euler()]

            if axis == [90, 0, 90]:
                bpy.ops.view3d.view_axis(type='RIGHT')
            elif axis == [90, 0, 0]:
                bpy.ops.view3d.view_axis(type='FRONT')
            elif axis == [0, 0, 0]:
                bpy.ops.view3d.view_axis(type='TOP')
            elif axis == [90, 0, -90]:
                bpy.ops.view3d.view_axis(type='LEFT')
            elif axis == [90, 0, 180]:
                bpy.ops.view3d.view_axis(type='BACK')
            elif axis == [180, 0, 0]:
                bpy.ops.view3d.view_axis(type='BOTTOM')


    def knife_intersect(self, context, axis):
        bpy.ops.object.mode_set(mode='OBJECT')
        operator.knife(context, knife_project=False)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')


    def setup_draw_data(self, context):
        '''Generate all the draw data.'''

        Data.reset_data()

        depsgraph = context.evaluated_depsgraph_get()

        Data.xp_ticks = []
        Data.yp_ticks = []
        Data.zp_ticks = []

        # X Data
        if self.axes[0]:
            Data.draw_x = True
            object_eval = self.plane_x.evaluated_get(depsgraph)
            mesh = object_eval.data
            mesh.calc_loop_triangles()
            bm = bmesh.new()
            bm.from_mesh(mesh)
            for face in bm.faces:
                points = [self.plane_x.matrix_world @ v.co.copy() for v in face.verts]
                Data.xp_point_data.extend(points)
                lines = [ points[0], points[1], points[1], points[2], points[2], points[3], points[3], points[0] ]
                Data.xp_line_data.append(lines)

                # Angle ticks
                for i, point in enumerate(points):
                    if i == 0:
                        a = point.lerp(points[-1], .125)
                        b = point.lerp(points[1], .125)
                    elif i == 1:
                        a = point.lerp(points[0], .125)
                        b = point.lerp(points[2], .125)
                    elif i == 2:
                        a = point.lerp(points[1], .125)
                        b = point.lerp(points[3], .125)
                    elif i == 3:
                        a = point.lerp(points[2], .125)
                        b = point.lerp(points[0], .125)

                    if i < 4:
                        Data.xp_ticks.extend([
                            a, point,
                            point, b])
            bm.free()

        # Y Data
        if self.axes[1]:
            Data.draw_y = True
            object_eval = self.plane_y.evaluated_get(depsgraph)
            mesh = object_eval.data
            mesh.calc_loop_triangles()
            bm = bmesh.new()
            bm.from_mesh(mesh)
            for face in bm.faces:
                points = [self.plane_y.matrix_world @ v.co.copy() for v in face.verts]
                Data.yp_point_data.extend(points)
                lines = [ points[0], points[1], points[1], points[2], points[2], points[3], points[3], points[0] ]
                Data.yp_line_data.append(lines)

                # Angle ticks
                for i, point in enumerate(points):
                    if i == 0:
                        a = point.lerp(points[-1], .125)
                        b = point.lerp(points[1], .125)
                    elif i == 1:
                        a = point.lerp(points[0], .125)
                        b = point.lerp(points[2], .125)
                    elif i == 2:
                        a = point.lerp(points[1], .125)
                        b = point.lerp(points[3], .125)
                    elif i == 3:
                        a = point.lerp(points[2], .125)
                        b = point.lerp(points[0], .125)

                    if i < 4:
                        Data.yp_ticks.extend([
                            a, point,
                            point, b])

        # Z Data
        if self.axes[2]:
            Data.draw_z = True
            object_eval = self.plane_z.evaluated_get(depsgraph)
            mesh = object_eval.data
            mesh.calc_loop_triangles()
            bm = bmesh.new()
            bm.from_mesh(mesh)
            for face in bm.faces:
                points = [self.plane_z.matrix_world @ v.co.copy() for v in face.verts]
                Data.zp_point_data.extend(points)
                lines = [ points[0], points[1], points[1], points[2], points[2], points[3], points[3], points[0] ]
                Data.zp_line_data.append(lines)

                # Angle ticks
                for i, point in enumerate(points):
                    if i == 0:
                        a = point.lerp(points[-1], .125)
                        b = point.lerp(points[1], .125)
                    elif i == 1:
                        a = point.lerp(points[0], .125)
                        b = point.lerp(points[2], .125)
                    elif i == 2:
                        a = point.lerp(points[1], .125)
                        b = point.lerp(points[3], .125)
                    elif i == 3:
                        a = point.lerp(points[2], .125)
                        b = point.lerp(points[0], .125)

                    if i < 4:
                        Data.zp_ticks.extend([
                            a, point,
                            point, b])
            bm.free()


    def join_objs(self, context, event):

        if self.joined: return
        self.joined = True

        mode = context.mode
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

        for obj in self.selected:
            apply_mod(self, obj, clear_last=False)

        for obj in self.curves:
            context.view_layer.objects.active = obj
            obj.select_set(True)
            bpy.ops.object.convert('INVOKE_DEFAULT', target='MESH')
        self.curves = []

        context.view_layer.objects.active = self.obj
        bpy.ops.object.join()

        self.remove_plane(context, self.plane_x)
        self.remove_plane(context, self.plane_y)
        self.remove_plane(context, self.plane_z)

        self.obj = context.active_object
        self.mode = self.obj.mode
        self.selected = [o for o in context.selected_objects if o.type == 'MESH']
        self.sources = self.selected[:]

        self.setup(context, event)

        self.setup_draw_data(context)

        if self.display_join_notification:
            bpy.ops.hops.display_notification(info="Objects Joined")

        if mode == 'EDIT_MESH':
            bpy.ops.object.mode_set(mode='EDIT', toggle=False)


    ####################################################
    #   Shaders : Modal Frame
    ####################################################

    def remove_shader(self):
        '''Remove shader handle.'''

        if self.draw_handle_2d:
            self.draw_handle_2d = bpy.types.SpaceView3D.draw_handler_remove(self.draw_handle_2d, "WINDOW")


    def safe_draw_2d(self, context):
        method_handler(self.draw_shader_2d,
            arguments = (context,),
            identifier = 'Dice 2D Shader',
            exit_method = self.remove_shader)


    def draw_shader_2d(self, context):
        '''Draw shader handle.'''

        draw_modal_frame(context)

##############################################################################
# Drawing Modal
##############################################################################

class HOPS_OT_Draw_Dice(bpy.types.Operator):
    '''Dice Modal'''

    bl_idname = "hops.draw_dice"
    bl_label = "Drawing for dice"
    bl_options = {"INTERNAL"}

    def invoke(self, context, event):

        # Global
        Data.reset_data()

        # Registers
        self.shader = Shader(context)
        self.timer = context.window_manager.event_timer_add(0.075, window=context.window)

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


    def modal(self, context, event):

        Data.draw_modal_running = True

        # Resest every thing if new drawing is initialized
        if Data.reset_modal:
            Data.reset_modal = False
            Data.reset_data()
            self.shader.reset()

        # Check for exit after fade
        if Data.dice_modal_running == False:

            # Fast exit
            if Data.exit_with_no_fade == True:
                self.__finished(context)
                return {'FINISHED'}

            # Fade exit
            self.shader.should_be_fading = True
            if self.shader.fade_complete == True:
                self.__finished(context)
                return {'FINISHED'}

        # Redraw the viewport
        if context.area != None:
            context.area.tag_redraw()

        return {'PASS_THROUGH'}


    def __finished(self, context):
        '''Remove the timer, shader, and reset Data'''

        # Global
        Data.reset_data()
        Data.exit_with_no_fade = False
        Data.draw_modal_running = False

        # Unregister
        if self.timer != None:
            context.window_manager.event_timer_remove(self.timer)
        if self.shader != None:
            self.shader.destroy()
        if context.area != None:
            context.area.tag_redraw()


class Shader():

    def __init__(self, context):

        self.should_be_fading = False
        self.fade_complete = False
        self.alpha_dice = .75
        self.fade_duration = .25 #addon.preference().ui.Hops_extra_draw_time
        self.fade_start_time = 0
        self.fade_start_time_set = False
        self.__setup_handle(context)
        self.prefs = addon.preference().property


    def __setup_handle(self, context):
        '''Setup the draw handle for the UI'''

        global HANDLE_3D
        if HANDLE_3D == None:
            HANDLE_3D = bpy.types.SpaceView3D.draw_handler_add(self.safe_draw_3d, (context, ), "WINDOW", "POST_VIEW")


    def reset(self):
        '''Reboot the shader props.'''

        self.should_be_fading = False
        self.fade_complete = False
        self.alpha_dice = .75
        self.fade_start_time = 0
        self.fade_start_time_set = False


    def safe_draw_3d(self, context):
        method_handler(self.__draw_3d,
            arguments = (context,),
            identifier = 'Dice Fade Draw Shader 3D',
            exit_method = self.destroy)


    def __draw_3d(self, context):
        '''Draw the UVs.'''

        # Fade started but there was a modal cancel or to twist so bounce out
        if Data.exit_with_no_fade and self.should_be_fading:
            return

        # Lower alpha during fade
        self.__handle_fade()

        #Enable(GL_LINE_SMOOTH)
        gpu.state.blend_set('ALPHA')
        gpu.state.line_width_set(1)
        if Data.see_though == False:
            gpu.state.depth_test_set('LESS')
            #glDepthFunc(GL_LESS)


        # X Axis
        if Data.draw_x and Data.xp_line_data and Data.xp_point_data:

            # Angle Ticks
            if self.prefs.dice_wire_type == 'TICKS' and Data.xp_ticks:
                gpu.state.line_width_set(3)
                built_in_shader = 'UNIFORM_COLOR' if bpy.app.version[0] >=4 else '3D_UNIFORM_COLOR'
                shader = gpu.shader.from_builtin(built_in_shader)
                batch = batch_for_shader(shader, 'LINES', {"pos": Data.xp_ticks})
                shader.bind()
                shader.uniform_float("color", (1, 0, 0, self.alpha_dice))
                batch.draw(shader)
                del shader
                del batch

            # Full edges
            elif self.prefs.dice_wire_type != 'DOTS':
                for verts in Data.xp_line_data:
                    built_in_shader = 'UNIFORM_COLOR' if bpy.app.version[0] >=4 else '3D_UNIFORM_COLOR'
                    shader = gpu.shader.from_builtin(built_in_shader)
                    batch = batch_for_shader(shader, 'LINES', {"pos": verts})
                    shader.bind()
                    shader.uniform_float("color", (1, 0, 0, self.alpha_dice))
                    batch.draw(shader)
                    del shader
                    del batch

            # Points
            built_in_shader = 'UNIFORM_COLOR' if bpy.app.version[0] >=4 else '3D_UNIFORM_COLOR'
            shader = gpu.shader.from_builtin(built_in_shader)
            batch = batch_for_shader(shader, 'POINTS', {"pos": Data.xp_point_data})
            shader.bind()
            shader.uniform_float("color", (1, 0, 0, self.alpha_dice))
            batch.draw(shader)
            del shader
            del batch

        # Y Axis
        if Data.draw_y and Data.yp_line_data and Data.yp_point_data:

            # Angle Ticks
            if self.prefs.dice_wire_type == 'TICKS' and Data.yp_ticks:
                gpu.state.line_width_set(3)
                built_in_shader = 'UNIFORM_COLOR' if bpy.app.version[0] >=4 else '3D_UNIFORM_COLOR'
                shader = gpu.shader.from_builtin(built_in_shader)
                batch = batch_for_shader(shader, 'LINES', {"pos": Data.yp_ticks})
                shader.bind()
                shader.uniform_float("color", (0, 1, 0, self.alpha_dice))
                batch.draw(shader)
                del shader
                del batch

            # Full Edges
            elif self.prefs.dice_wire_type != 'DOTS':
                for verts in Data.yp_line_data:
                    built_in_shader = 'UNIFORM_COLOR' if bpy.app.version[0] >=4 else '3D_UNIFORM_COLOR'
                    shader = gpu.shader.from_builtin(built_in_shader)
                    batch = batch_for_shader(shader, 'LINES', {"pos": verts})
                    shader.bind()
                    shader.uniform_float("color", (0, 1, 0, self.alpha_dice))
                    batch.draw(shader)
                    del shader
                    del batch

            # Points
            built_in_shader = 'UNIFORM_COLOR' if bpy.app.version[0] >=4 else '3D_UNIFORM_COLOR'
            shader = gpu.shader.from_builtin(built_in_shader)
            batch = batch_for_shader(shader, 'POINTS', {"pos": Data.yp_point_data})
            shader.bind()
            shader.uniform_float("color", (0, 1, 0, self.alpha_dice))
            batch.draw(shader)
            del shader
            del batch

        # Z Axis
        if Data.draw_z and Data.zp_line_data and Data.zp_point_data:

            # Angle Ticks
            if self.prefs.dice_wire_type == 'TICKS' and Data.zp_ticks:
                gpu.state.line_width_set(3)
                built_in_shader = 'UNIFORM_COLOR' if bpy.app.version[0] >=4 else '3D_UNIFORM_COLOR'
                shader = gpu.shader.from_builtin(built_in_shader)
                batch = batch_for_shader(shader, 'LINES', {"pos": Data.zp_ticks})
                shader.bind()
                shader.uniform_float("color", (0, 0, 1, self.alpha_dice))
                batch.draw(shader)
                del shader
                del batch

            # Edges
            elif self.prefs.dice_wire_type != 'DOTS':
                for verts in Data.zp_line_data:
                    built_in_shader = 'UNIFORM_COLOR' if bpy.app.version[0] >=4 else '3D_UNIFORM_COLOR'
                    shader = gpu.shader.from_builtin(built_in_shader)
                    batch = batch_for_shader(shader, 'LINES', {"pos": verts})
                    shader.bind()
                    shader.uniform_float("color", (0, 0, 1, self.alpha_dice))
                    batch.draw(shader)
                    del shader
                    del batch

            # Points
            built_in_shader = 'UNIFORM_COLOR' if bpy.app.version[0] >=4 else '3D_UNIFORM_COLOR'
            shader = gpu.shader.from_builtin(built_in_shader)
            batch = batch_for_shader(shader, 'POINTS', {"pos": Data.zp_point_data})
            shader.bind()
            shader.uniform_float("color", (0, 0, 1, self.alpha_dice))
            batch.draw(shader)
            del shader
            del batch

        gpu.state.blend_set('NONE')
        gpu.state.depth_test_set('NONE')
        gpu.state.face_culling_set('NONE')
        gpu.state.depth_test_set('NONE')

        if self.alpha_dice <= 0:
            self.fade_complete = True


    def __handle_fade(self):
        '''Fade alpha if fading is active.'''

        if self.should_be_fading == True:
            # Set the initial fade start time
            if self.fade_start_time_set == False:
                self.fade_start_time_set = True
                self.fade_start_time = time.time()

            # Fade alpha
            diff = time.time() - self.fade_start_time
            ratio = diff / self.fade_duration #if not self.prefs.dice_show_mesh_wire else diff / (self.fade_duration * .5)
            self.alpha_dice = .75 - (.75 * ratio)


    def destroy(self):
        '''Remove the shader.'''

        global HANDLE_3D
        if HANDLE_3D != None:
            bpy.types.SpaceView3D.draw_handler_remove(HANDLE_3D, "WINDOW")
            HANDLE_3D = None

        Data.reset_data()

##############################################################################
# Remove On App Reload
##############################################################################

from bpy.app.handlers import persistent
@persistent
def remove_dice_draw_shader(dummy):
    global HANDLE_3D
    if HANDLE_3D != None:
        bpy.types.SpaceView3D.draw_handler_remove(HANDLE_3D, "WINDOW")
        HANDLE_3D = None

    Data.reset_data()
    Data.reset_states()