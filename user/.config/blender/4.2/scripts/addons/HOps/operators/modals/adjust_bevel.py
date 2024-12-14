import bpy, math
from pathlib import Path
from math import radians, degrees
from bpy.props import BoolProperty
from . import infobar
from ... utils.objects import apply_scale
from ... utility import modifier, ops
from ... utility.base_modal_controls import Base_Modal_Controls
from ... utils.mod_controller import Mod_Controller
from ... utility import addon
from ... ui_framework.master import Master
from ... ui_framework.utils.mods_list import get_mods_list, custom_profile
from ...utils.profile import load_bevel_profile
from ... utils.toggle_view3d_panels import collapse_3D_view_panels
from ... utils.modal_frame_drawing import draw_modal_frame
from ... utils.cursor_warp import mouse_warp
from ... utility import method_handler
from ... assets.custom_profiles import profile_path as hops_profile_path


DESC = """Add / Adjust Bevel

LMB               - Adjust Bevel Modifier
CTRL              - Add new Bevel (30º)
CTRL + Shift  - Add new Bevel (60º)
Shift               - Bypass Scale

Press H for help"""


class HOPS_OT_AdjustBevelOperator(bpy.types.Operator):
    bl_idname = "hops.adjust_bevel"
    bl_label = "Adjust Bevel"
    bl_options = {"REGISTER", "UNDO", "BLOCKING"}
    bl_description = DESC

    ignore_ctrl: BoolProperty(
        name='Ignore Ctrl',
        default=False,
        description='Ignore Ctrl keypress')

    use_workflow: BoolProperty(
        name='Use Worflow Pref',
        default=True,
        description='Use workflow pref')

    flag: BoolProperty(
        name='Use Bevel Special Behavior',
        default=False,
        description='Ignore Ctrl keypress')

    # Popover
    operator = None
    mod_selected = ""

    @classmethod
    def poll(cls, context):
        return any(o.type in {'MESH', 'CURVE'} for o in context.selected_objects)


    def invoke(self, context, event):

        # Header Bar
        self.text = "nothing"

        # Mod Controller
        objs = [o for o in context.selected_objects if o.type in {'MESH', 'CURVE'}]

        if addon.preference().behavior.auto_smooth and context.mode == 'OBJECT':
            for obj in objs:
                if not obj.data.use_auto_smooth:
                    obj.data.auto_smooth_angle = radians(60)
                obj.data.use_auto_smooth = True

        type_map = {bpy.types.Mesh : 'BEVEL', bpy.types.Curve : 'BEVEL'}
        ctrl_new = True if event.ctrl and not self.ignore_ctrl else False
        self.mod_controller = Mod_Controller(context, objs, type_map, create_new=ctrl_new, active_obj=context.active_object)
        self.initialize_new_mods(context, event)

        # Apply Scale
        self.scaleapply = True if context.mode == 'OBJECT' and not event.shift and not event.ctrl else False
        if self.scaleapply:
            apply_scale(self.mod_controller.all_objs())

        # States
        self.segments_mode = False
        self.profile_mode = False
        self.angle_mode = False
        self.percent_mode = False
        self.adaptivemode = addon.preference().property.adaptivemode
        self.snap_break = 0.05
        self.snap_buffer = 0

        # Directory Profiles
        self.setup_profiles()

        # Sort
        self.mod_controller.sort_mods(sort_types=['WEIGHTED_NORMAL'])

        # Base Systems
        self.master = Master(context)
        self.master.only_use_fast_ui = True
        self.base_controls = Base_Modal_Controls(context, event, popover_keys=['TAB', 'SPACE'])
        self.original_tool_shelf, self.original_n_panel = collapse_3D_view_panels()
        self.draw_handle = bpy.types.SpaceView3D.draw_handler_add(self.safe_draw_shader, (context,), 'WINDOW', 'POST_PIXEL')

        context.window_manager.modal_handler_add(self)
        infobar.initiate(self)

        # Popover
        self.__class__.operator = self
        self.__class__.mod_selected = ""

        return {"RUNNING_MODAL"}


    def modal(self, context, event):

        # Base Systems
        self.master.receive_event(event=event)
        self.base_controls.update(context, event)
        mouse_warp(context, event)

        # Pass
        if self.base_controls.pass_through:
            return {'PASS_THROUGH'}

        # Popover
        self.popover(context)

        # Cancel
        if self.base_controls.cancel:
            self.common_exit(context)
            self.cancel_exit(context)
            return {'CANCELLED'}

        # Confirm
        if self.base_controls.confirm:
            # Apply active mod
            mod = self.mod_controller.active_object_mod()
            if event.type in ("RET", "NUMPAD_ENTER") and event.shift and mod:
                if context.mode == 'EDIT_MESH':
                    bpy.ops.object.editmode_toggle()
                if context.mode == 'OBJECT':
                    mod_name = mod.name[:]
                    bpy.ops.object.modifier_apply(modifier=mod_name)
                    bpy.ops.hops.draw_wire_mesh_launcher('INVOKE_DEFAULT', target='SELECTED')
                    if addon.preference().ui.Hops_extra_info:
                        bpy.ops.hops.display_notification(info=f'{mod_name} : Applied' )
            # Display
            bpy.context.space_data.overlay.show_overlays = True
            for obj in context.selected_objects:
                obj.show_wire = False
            # Exit
            self.confirm_exit(context)
            self.common_exit(context)
            return {'FINISHED'}

        # Inputs
        ret = self.actions(context, event)
        if ret != None:
            context.area.tag_redraw()
            return ret

        # UI
        self.header(context)
        self.draw_ui(context)

        context.area.tag_redraw()
        return {'RUNNING_MODAL'}

    # --- ACTIONS --- #

    def actions(self, context, event):

        # Scroll
        if self.base_controls.scroll:
            self.scroll_adjust(context, event)

        # Mouse
        elif event.type == "MOUSEMOVE":
            self.mouse_adjust(context, event)

        # Preset One
        elif event.type == "ONE" and event.value == "PRESS":
            self.preset_one(context)

        # Preset Two
        elif event.type == "TWO" and event.value == "PRESS":
            self.preset_two(context)

        # Preset Three
        elif event.type == "THREE" and event.value == "PRESS":
            self.preset_three()

        # Adaptive / Angle / Auto Smooth / Angle Mode
        elif event.type == "A" and event.value == "PRESS":

            # Adaptive
            if event.shift:
                self.toggle_adaptive()

            # Limit Angle
            elif event.ctrl:
                self.limit_angle()

            # Auto Smooth
            elif event.alt:
                return self.auto_smooth_modal(context)

            # Angle Mode
            else:
                for mod in self.mod_controller.active_modifiers():
                    if mod.limit_method == 'ANGLE':
                        self.angle_mode = not self.angle_mode
                        if self.angle_mode:
                            self.profile_mode = False
                        break

        # Move Mod / Change Index
        elif event.type == "Q" and event.value == "PRESS":
            # Move Mod
            if event.shift:
                self.mod_controller.move_mod(context, up=True)
            # Move Index
            else:
                self.mod_controller.cyclic_directional_mod_index(forward=True)

            self.display_active_mod_notification()

        # Move Mod / Change Index
        elif event.type == "E" and event.value == "PRESS":
            # Move Mod
            if event.shift:
                self.mod_controller.move_mod(context, up=False)
            # Move Index
            else:
                self.mod_controller.cyclic_directional_mod_index(forward=False)

            self.display_active_mod_notification()

        # Clamp / Loop Slide
        elif event.type == "C" and event.value == "PRESS":
            # Clamp
            if event.shift:
                msg = ""
                for mod in self.mod_controller.active_modifiers():
                    mod.loop_slide = not mod.loop_slide
                    msg = mod.loop_slide
                self.report({'INFO'}, F'Loop Slide : {msg}')
            # Loop Slide
            else:
                msg = ""
                for mod in self.mod_controller.active_modifiers():
                    mod.use_clamp_overlap = not mod.use_clamp_overlap
                    msg = mod.use_clamp_overlap
                self.report({'INFO'}, F'Clamp Overlap : {msg}')

        # Limit Methods
        elif event.type == "L" and event.value == "PRESS":
            msg = ""
            limit_methods = ["NONE", "ANGLE", "WEIGHT", "VGROUP"]
            for mod in self.mod_controller.active_modifiers():
                mod.limit_method = limit_methods[(limit_methods.index(mod.limit_method) + 1) % len(limit_methods)]
                msg = mod.limit_method
            if addon.preference().ui.Hops_extra_info:
                bpy.ops.hops.display_notification(info=F'Limit Method : {msg}')
            self.report({'INFO'}, F'Limit Method : {msg}')

        # Harden Normals / Miter
        elif event.type == "M" and event.value == "PRESS":
            # Harden Normals
            if event.shift:
                msg = ""
                for mod in self.mod_controller.active_modifiers():
                    mod.harden_normals = not mod.harden_normals
                    msg = mod.harden_normals
                self.report({'INFO'}, F'Harden Normals : {msg}')
            # Miter
            elif event.alt:
                msg = ""
                miter_types = ["MITER_SHARP", "MITER_ARC", "MITER_PATCH"]
                for mod in self.mod_controller.active_modifiers():
                    mod.miter_outer = miter_types[(miter_types.index(mod.miter_outer) + 1) % len(miter_types)]
                    msg = mod.miter_outer
                self.report({'INFO'}, F'Miter Outer Type : {msg}')

        # Flip / Harden Normals
        elif event.type == "N" and event.value == "PRESS":
            # Flip
            if context.mode == 'EDIT_MESH':
                bpy.ops.mesh.flip_normals()
            # Harden Normals
            else:
                msg = ""
                for mod in self.mod_controller.active_modifiers():
                    mod.harden_normals = not mod.harden_normals
                    msg = mod.harden_normals
                bpy.ops.hops.display_notification(info=F'Harden Normals : {msg}')
                self.report({'INFO'}, F'Harden Normals : {msg}')

        # Profile Mode / Profile Toggles / Profile Mode Set
        if event.type == 'P' and event.value == 'PRESS':
            # Profile Mode
            if event.shift:
                self.segments_mode = False
                if self.support_profile_scroll:
                    if addon.preference().ui.Hops_extra_info:
                        bpy.ops.hops.display_notification(info=F'Profile Scroll: {self.support_profile_scroll}' )
                    self.profile_mode = False
                    self.segments_mode = False
                    self.scrolling_profiles = not self.scrolling_profiles
                    action = 'Started' if self.scrolling_profiles else 'Stopped'
                    self.report({'INFO'}, f'{action} scrolling profiles')
                else:
                    if addon.preference().ui.Hops_extra_info:
                        bpy.ops.hops.display_notification(info='No Profiles Found' )

            # Profile Toggles
            elif event.ctrl:
                if bpy.app.version < (2, 90, 0):
                    msg = ""
                    for mod in self.mod_controller.active_modifiers():
                        mod.use_custom_profile = not mod.use_custom_profile
                        msg = mod.use_custom_profile
                    self.report({'INFO'}, F'Custom Profile : {msg}')
                else:
                    msg = ""
                    for mod in self.mod_controller.active_modifiers():
                        if mod.profile_type == 'CUSTOM':
                            mod.profile_type = 'SUPERELLIPSE'
                        else:
                            mod.profile_type = 'CUSTOM'
                        msg = mod.profile_type
                    self.report({'INFO'}, F'Custom Profile : {msg}')

            # Profile Mode Set
            else:
                self.segments_mode = False
                self.scrolling_profiles = False
                self.profile_mode = not self.profile_mode

        # Smooth Shade / Segment Mode
        if event.type == "S" and event.value == "PRESS":
            # Smooth Shade
            if addon.preference().behavior.auto_smooth and event.shift:
                if context.mode == 'OBJECT':
                    for obj, mod in self.iter_obj_mod():
                        obj.data.use_auto_smooth = True
                    ops.shade_smooth()

            # Segment Mode
            else:
                self.profile_mode = False
                self.scrolling_profiles = False
                self.segments_mode = not self.segments_mode

        # Offset Types / Render Toggle
        if event.type == "W" and event.value == "PRESS" and event.alt:
            # Offset Types
            if event.alt:
                msg = ""
                offset_types = ["OFFSET", "WIDTH", "DEPTH", "PERCENT"]
                for mod in self.mod_controller.active_modifiers():
                    mod.offset_type = offset_types[(offset_types.index(mod.offset_type) + 1) % len(offset_types)]
                    msg = mod.offset_type
                self.report({'INFO'}, F'Offset Type : {msg}')

            # Render Toggle
            if event.shift:
                msg = ""
                for mod in self.mod_controller.active_modifiers():
                    mod.show_render = not mod.show_render
                    msg = mod.show_render
                self.report({'INFO'}, F'Modifiers Renderability : {msg}')

        # Viewport Toggle
        if event.type == "V" and event.value == "PRESS":
            msg = ""
            for mod in self.mod_controller.active_modifiers():
                mod.show_viewport = False if mod.show_viewport else True
                msg = mod.show_viewport
            self.report({'INFO'}, F'Toggle Bevel : {msg}')

        # Set to 50%
        if event.type == "X" and event.value == "PRESS":
            obj = self.mod_controller.active_obj
            mod = self.mod_controller.active_object_mod()
            if not obj: return None

            bevel_widths = [mod.width for mod in obj.modifiers if mod.type == 'BEVEL']
            if not bevel_widths: return None

            lw = bevel_widths[-1]
            if len(bevel_widths) > 1 and not event.alt:
                lw = bevel_widths[-2]
            lw = lw * 0.5 if not event.shift else lw * 2
            mod.width = lw

            if addon.preference().ui.Hops_extra_info:
                bpy.ops.hops.display_notification(info=F'Bevel Set to: {lw:.3f}' )
            self.report({'INFO'}, F'Width Set to half: {lw:.3f}')

            self.confirm_exit(context)
            self.common_exit(context)
            return {'FINISHED'}

        # Wire Display
        if event.type == "Z" and event.value == "PRESS":
            bpy.context.space_data.overlay.show_overlays = True
            for obj, mod in self.iter_obj_mod():
                obj.show_wire = False if obj.show_wire else True
                obj.show_all_edges = True if obj.show_wire else False

        return None


    def mouse_adjust(self, context, event):
        for obj, mod in self.iter_obj_mod():

            if self.angle_mode:
                angle_offset = self.base_controls.mouse
                if event.ctrl:
                    self.snap_buffer += angle_offset
                    if abs(self.snap_buffer) > self.snap_break:
                        increment = radians(5)
                        mod.angle_limit = snap(mod.angle_limit + math.copysign(increment, self.snap_buffer), increment)
                        self.snap_buffer = 0
                else:
                    mod.angle_limit += angle_offset

            elif self.segments_mode:
                self.snap_buffer += self.base_controls.mouse
                if abs(self.snap_buffer) > self.snap_break:
                    mod.segments += int(math.copysign(1, self.snap_buffer))
                    self.snap_buffer = 0

            elif self.profile_mode:
                self.snap_buffer += self.base_controls.mouse
                if abs(self.snap_buffer) > self.snap_break:
                    mod.profile = round(mod.profile + math.copysign(0.1, self.snap_buffer), 1)
                    self.snap_buffer = 0

            else:
                bevel_offset = self.base_controls.mouse
                multiplier = 10 if mod.offset_type == 'PERCENT' else 1
                if event.ctrl and event.shift:
                    self.snap_buffer += bevel_offset
                    if abs(self.snap_buffer) > self.snap_break:
                        mod.width = round(mod.width + math.copysign(0.1 * multiplier, self.snap_buffer), 1)
                        self.snap_buffer = 0
                else:
                    mod.width += bevel_offset * multiplier

            if self.adaptivemode:
                self.adaptivesegments = int(mod.width * addon.preference().property.adaptiveoffset) + obj.hops.adaptivesegments
                mod.segments = self.adaptivesegments


    def scroll_adjust(self, context, event):

        # Profiles
        if self.support_profile_scroll and self.scrolling_profiles:
            # Index
            self.profile_index += self.base_controls.scroll
            if self.profile_index > len(self.profile_files) - 1:
                self.profile_index = 0
            if self.profile_index < 0:
                self.profile_index = len(self.profile_files) - 1

            # Set Profiles
            mods = self.mod_controller.active_modifiers()
            for mod in mods:
                load_bevel_profile(mod, str(self.profile_files[self.profile_index]), False)

        # Adaptive
        elif self.adaptivemode:
            if event.ctrl:
                addon.preference().property.adaptiveoffset += 0.5 * self.base_controls.scroll
            elif event.shift:
                if self.base_controls.scroll > 0:
                    self.mod_controller.clamped_next_mod_index(forward=True)
                elif self.base_controls.scroll < 0:
                    self.mod_controller.clamped_next_mod_index(forward=False)
            else:
                for obj_data in self.mod_controller.validated_obj_datas():
                    obj = obj_data.obj
                    if not obj: continue
                    obj.hops.adaptivesegments += self.base_controls.scroll

        # Move Mod
        elif event.shift:
            if self.base_controls.scroll > 0:
                self.mod_controller.move_mod(context, up=True)
            elif self.base_controls.scroll < 0:
                self.mod_controller.move_mod(context, up=False)

        # Move Index
        elif event.ctrl:
            if self.base_controls.scroll > 0:
                self.mod_controller.clamped_next_mod_index(forward=True)
            elif self.base_controls.scroll < 0:
                self.mod_controller.clamped_next_mod_index(forward=False)

        # Angle Limit
        elif event.alt:
            for mod in self.mod_controller.active_modifiers():
                mod.angle_limit += radians(self.base_controls.scroll)

        # Angle Limit / Segments
        else:
            if self.angle_mode:
                for mod in self.mod_controller.active_modifiers():
                    mod.angle_limit += radians(self.base_controls.scroll)
            else:
                for mod in self.mod_controller.active_modifiers():
                    mod.segments += self.base_controls.scroll


    def preset_one(self, context):
        for obj, mod in self.iter_obj_mod():
            if round(obj.data.auto_smooth_angle, 4) == round(radians(60), 4):
                if context.mode == 'OBJECT':
                    ops.shade_smooth()
                    if addon.preference().behavior.auto_smooth:
                        obj.data.use_auto_smooth = True
                        obj.data.auto_smooth_angle = radians(30)
                        self.report({'INFO'}, F'Autosmooth')
                mod.harden_normals = False
                if bpy.app.version < (2, 90, 0):
                    mod.use_only_vertices = False
                else:
                    mod.affect = 'EDGES'
                if mod.segments == 2:
                    mod.segments = 4
            else:
                if context.mode == 'OBJECT':
                    ops.shade_smooth()
                    obj.data.auto_smooth_angle = radians(60)
                    if addon.preference().behavior.auto_smooth:
                        obj.data.use_auto_smooth = True
                        self.report({'INFO'}, F'Autosmooth')
                mod.harden_normals = False
                if bpy.app.version < (2, 90, 0):
                    mod.use_only_vertices = False
                else:
                    mod.affect = 'EDGES'
                if mod.segments == 2:
                    mod.segments = 4

            if context.mode == 'EDIT_MESH':
                if mod.profile == 0.5:
                    mod.profile = 0.05
                else:
                    mod.profile = 0.5
                self.report({'INFO'}, F'Profile set to: {round(mod.profile, 4)}')
            else:
                mod.profile = 0.5

        # Notifications
        mod = self.mod_controller.active_object_mod()
        if not mod: return
        angle = round(degrees(obj.data.auto_smooth_angle), 4)
        if addon.preference().ui.Hops_extra_info:
            bpy.ops.hops.display_notification(info=F'Profile set to: {round(mod.profile, 4)}' if context.mode == 'EDIT_MESH' else F'Autosmooth : {(angle)}')
        if bpy.app.version >= (4, 1):
            self.report({'INFO'}, F'Profile set to: {round(mod.profile, 4)}')
        else:
            self.report({'INFO'}, F'Autosmooth : {angle} / Harden Normals : {mod.harden_normals}')


    def preset_two(self, context):
        for mod in self.mod_controller.active_modifiers():
            if bpy.app.version < (2, 90, 0):
                mod.use_only_vertices = True
            else:
                mod.affect = 'VERTICES'

            if context.mode == 'EDIT_MESH':
                if mod.profile == 0.5:
                    mod.profile = 0.05
                else:
                    mod.profile = 0.5
            else:
                mod.profile = 0.5

        # Notifications
        if addon.preference().ui.Hops_extra_info:
            bpy.ops.hops.display_notification(info=F'Vert Bevel' )
        self.report({'INFO'}, F'Vert Bevel')


    def preset_three(self):
        for obj, mod in self.iter_obj_mod():
            if bpy.app.version < (2, 90, 0):
                mod.use_only_vertices = False
            else:
                mod.affect = 'EDGES'
            mod.harden_normals = False
            mod.profile = 1.0
            mod.segments = 2
            obj.show_wire = False if obj.show_wire else True
            obj.show_all_edges = True if obj.show_wire else False

        # Notifications
        if addon.preference().ui.Hops_extra_info:
            bpy.ops.hops.display_notification(info='Conversion Bevel' )
        self.report({'INFO'}, 'Conversion Bevel')


    def toggle_adaptive(self):
        self.adaptivemode = not self.adaptivemode
        addon.preference().property.adaptivemode = not addon.preference().property.adaptivemode
        self.report({'INFO'}, F'Adaptive Mode : {self.adaptivemode}')


    def limit_angle(self):
        display_msg = ""
        for obj, mod in self.iter_obj_mod():
            mod.limit_method = 'ANGLE' if not 'VGROUP' else 'ANGLE'
            angle_types = [60, 30, degrees(obj.data.auto_smooth_angle)]

            if int(degrees(mod.angle_limit)) not in angle_types:
                mod.angle_limit = radians(angle_types[0])
            else:
                index = angle_types.index(int(degrees(mod.angle_limit)))
                mod.angle_limit = radians(angle_types[index + 1 if index + 1 < len(angle_types) else 0])

            display_msg = str(int(degrees(mod.angle_limit)))

        self.report({'INFO'}, F'Bevel Mod Angle : {display_msg}')


    def auto_smooth_modal(self, context):
        if context.mode == 'OBJECT':
            for mod in self.mod_controller.active_modifiers():
                mod.show_viewport = False if mod.show_viewport else True
            bpy.ops.hops.adjust_auto_smooth("INVOKE_DEFAULT", flag=True)
            self.report({'INFO'}, F'Autosmooth Adjustment')
            self.confirm_exit(context)
            self.common_exit(context)
            return {'FINISHED'}
        else:
            self.report({'INFO'}, F'Unavailable')
            return None

    # --- UI --- #

    def draw_ui(self, context):

        self.master.setup()
        if not self.master.should_build_fast_ui(): return

        mod = self.mod_controller.active_object_mod()
        if not mod: return

        # Main
        win_list = []

        if addon.preference().ui.Hops_modal_fast_ui_loc_options != 1:
            win_list.append(mod.segments)
            win_list.append("%.3f" % mod.width)
            if mod.limit_method == 'ANGLE':
                win_list.append("%.0f" % (degrees(mod.angle_limit)) + "°")
            if self.support_profile_scroll and self.scrolling_profiles:
                win_list.append(mod.segments)
                win_list.append(self.profile_files[self.profile_index].name[:-5])

        else:
            win_list.append(mod.name)
            if self.text != "nothing" and addon.preference().property.workflow_mode == 'ANGLE' and mod.limit_method == 'ANGLE':
                win_list.append(self.text)
            win_list.append("Segments : " + str(mod.segments))
            win_list.append("Width : "    + "%.4f" % mod.width)
            if self.support_profile_scroll and self.scrolling_profiles:
                win_list.append("Custom Profile : " + str(self.profile_files[self.profile_index].name[:-5]))
            else:
                if custom_profile(mod):
                    win_list.append("Custom Profile")
                else:
                    win_list.append("Profile : "  + "%.2f" % mod.profile)
            win_list.append("Limit : "   + str(mod.limit_method))
            if mod.limit_method == 'ANGLE':
                win_list.append("Angle : "+ "%.0f" % (degrees(mod.angle_limit)) + "°" + " (alt)")
            if self.support_profile_scroll and self.scrolling_profiles:
                win_list.append(str(self.profile_files[self.profile_index].name[:-5]))

        # Help
        help_items = {"GLOBAL" : [], "STANDARD" : []}

        help_items["GLOBAL"] = [
            ("M", "Toggle mods list"),
            ("H", "Toggle help"),
            ("~", "Toggle UI Display Type"),
            ("O", "Toggle viewport rendering")]

        help_items["STANDARD"] = [
            ("Shift + Enter",  "Apply the current modifier"),
            ("Ctrl + Shift",   "Mouse move snap"),
            ("Shift + Scroll", "Move mod up/down"),
            ("Ctrl + Scroll",  "Select next/previous bevel modifier"),
            ("Alt + W",        "Adjust the offset algorithm [shift] sort toggle"),
            ("Alt + M",        f"Adjust the miter outer algorithm ({mod.miter_outer})"),
            ("Ctrl + A",       "Change angle to bevel at to 30 / 60"),
            ("C",              "Toggle Clamp Overlap"),
            ("3",              "Profile 1.0 / Segment 1 - Sub-d Conversion"),
            ("2",              "Profile .5 / Toggle vertex bevel"),
            ("1",              "Profile .5 / Autosmooth 30 / 60 / Harden Normals Off"),
            ("S",              "Modal Segment Toggle"),
            ("L",              f"Change limit method - {mod.limit_method}"),
            ("X",              f"Set bevel to 50% of current ({mod.width/2:.2f})"),
            ("Z",              "Toggle the wireframe display"),
            ("V",              "Toggle visibility in the viewport")]

        h_append = help_items["STANDARD"].append

        if context.mode == 'OBJECT':
            if self.angle_mode:
                h_append(["A", "Return to segments"])
            else:
                h_append(["A", "Adjust Bevel Angle [shift] Adaptive Mode"])

        if self.profile_mode: # FIXME : This does not take into account that Shift + P should also say "Return to segments" when it's toggled on
            h_append(["P", "Return to segments"])
        else:
            h_append(["P", "Adjust the Profile [shift] scroll [ctrl] toggle"])

        if context.mode == 'EDIT_MESH':
            h_append(["N", "Flip Normal"])
        else:
            h_append(["N", "Harden normal toggle"])

        if self.angle_mode:
            h_append(["Scroll", "Adjust angle of modifier"])
        else:
            h_append(["Scroll", "Add bevel segments to modifier"])

        h_append(["Q / E", "Change mod being adjusted [shift] move [ctrl] change"])

        if self.profile_mode:
            h_append(["Move", "Adjust the profile of bevel modifier"])
        elif self.angle_mode:
            h_append(["Move", "Adjust the angle of bevel modifier"])
        elif self.segments_mode:
            h_append(["Move", "Adjust segments of bevel modifier"])
        else:
            h_append(["Move", "Adjust width of bevel modifier"])

        if 'SPACE' in self.base_controls.popover_keys:
            help_items["STANDARD"].append(('Space', 'Open Select Menu'))
        elif 'TAB' in self.base_controls.popover_keys:
            help_items["STANDARD"].append(('TAB', 'Open Select Menu'))

        if mod.limit_method == 'ANGLE':
            help_items["STANDARD"].append(('Alt + Scroll', 'Adjust angle amount'))
        # Mods
        mods_list = get_mods_list(mods=self.mod_controller.active_obj.modifiers)

        self.master.receive_fast_ui(win_list=win_list, help_list=help_items, image="AdjustBevel", mods_list=mods_list, active_mod_name=mod.name)
        self.master.finished()


    def header(self, context):
        mod = self.mod_controller.active_object_mod()
        if not mod: return
        context.area.header_text_set("Hardops Adjust Bevel,                Current modifier: - {}".format(mod.name))


    def display_active_mod_notification(self):
        active_mod = self.mod_controller.active_object_mod()
        if active_mod:
            bpy.ops.hops.display_notification(info=F'Target Bevel : {active_mod.name}')


    def popover(self, context):

        # Popup captured new mod
        if self.__class__.mod_selected != "":
            valid = self.mod_controller.set_active_obj_mod_index(self.__class__.mod_selected)
            if valid:
                bpy.ops.hops.display_notification(info=f'Target Bevel : {self.__class__.mod_selected}')
            self.__class__.mod_selected = ""

        # Spawns
        if self.base_controls.popover:
            context.window_manager.popover(popup_draw)

    # --- UTILS --- #

    def initialize_new_mods(self, context, event):

        obj_mods = self.mod_controller.all_created_mods(with_objs=True)
        if not obj_mods: return

        for obj, mods in obj_mods.items():
            for mod in mods:

                self.text = "60° Bevel Added" if event.shift else "30° Bevel Added"
                angle = radians(60) if event.shift else radians(30)

                mod.limit_method = addon.preference().property.workflow_mode
                mod.miter_outer = addon.preference().property.bevel_miter_outer
                mod.miter_inner = addon.preference().property.bevel_miter_inner
                mod.profile = addon.preference().property.bevel_profile
                mod.loop_slide = addon.preference().property.bevel_loop_slide
                mod.segments = addon.preference().property.default_segments
                mod.use_clamp_overlap = False
                mod.angle_limit = angle
                mod.width = 0.01

                if bpy.app.version > (2, 89, 0):
                    mod.affect = 'EDGES'

                if obj.dimensions[2] == 0 or obj.dimensions[1] == 0 or obj.dimensions[0] == 0:
                    mod.segments = 6
                    if bpy.app.version < (2, 90, 0):
                        mod.use_only_vertices = True
                    else:
                        mod.affect = 'VERTICES'
                    mod.use_clamp_overlap = True

                elif obj.hops.status == "BOOLSHAPE":
                    mod.harden_normals = False

                elif addon.preference().property.use_harden_normals and not obj.hops.status == 'BOOLSHAPE':
                    mod.harden_normals = True

                obj.show_all_edges = True

                if obj.type == 'MESH':
                    if context.mode == 'EDIT_MESH':
                        vg = obj.vertex_groups.new(name='HardOps')
                        weight = context.scene.tool_settings.vertex_group_weight
                        context.scene.tool_settings.vertex_group_weight = 1.0
                        bpy.ops.object.vertex_group_assign()
                        context.scene.tool_settings.vertex_group_weight = weight
                        if addon.preference().property.adjustbevel_use_1_segment:
                            if context.tool_settings.mesh_select_mode[2] and obj.hops.status == "BOOLSHAPE":
                                mod.segments = 1
                                mod.harden_normals = False
                                bpy.ops.mesh.flip_normals()
                        mod.limit_method = 'VGROUP'
                        mod.vertex_group = vg.name
                        bpy.ops.mesh.faces_shade_smooth()
                    else:
                        ops.shade_smooth()

        # Notifications
        if addon.preference().ui.Hops_extra_info:
            mods = self.mod_controller.all_created_mods()
            if addon.preference().property.workflow_mode == 'ANGLE':
                bpy.ops.hops.display_notification(info=f'Bevel Added {"%.1f"%(degrees(angle))}° - Total : {len(mods)}' )
            else:
                bpy.ops.hops.display_notification(info=f'Bevel Added - Total : {len(mods)}' )


    def setup_profiles(self):

        self.support_profile_scroll = False
        self.profile_files = []

        # --- Edge Cases --- #

        profile_opt = 'CUSTOM'
        if addon.preference().property.profile_folder == '':
            if addon.preference().property.use_default_profiles == False:
                profile_opt = 'NONE'
            else:
                profile_opt = 'DEFAULT'

        if profile_opt == 'CUSTOM' and addon.preference().property.use_default_profiles:
            profile_folder = Path(addon.preference().property.profile_folder).resolve()
            if len([x for x in profile_folder.glob('*.json') if x.is_file()]) == 0:
                profile_opt = 'DEFAULT'

        # --- Capture Files --- #

        if profile_opt == 'DEFAULT':
            profile_folder = Path(hops_profile_path()).resolve()
            if profile_folder.is_dir():
                self.profile_files = [x for x in profile_folder.glob('*.json') if x.is_file()]

        elif profile_opt == 'CUSTOM':
            profile_folder = Path(addon.preference().property.profile_folder).resolve()
            self.profile_files = [x for x in profile_folder.glob('*.json') if x.is_file()]

        if self.profile_files:
            self.profile_index = 0
            self.scrolling_profiles = False
            self.support_profile_scroll = True


    def move_weighted_normals(self):
        for obj_data in self.mod_controller.validated_obj_datas():
            move = False

            for mod_data in obj_data.mod_datas:
                if mod_data.was_created:
                    move = True
                    break

            if not move: continue
            obj = obj_data.obj
            if not obj: continue
            wn_mods =  [wn for wn in obj.modifiers if wn.type == 'WEIGHTED_NORMAL' ]

            for mod in wn_mods:
                stored = modifier.stored(mod)
                obj.modifiers.remove(mod)
                modifier.new(obj, mod=stored)


    def iter_obj_mod(self):
        obj_datas = self.mod_controller.validated_obj_datas()
        for obj_data in obj_datas:
            obj = obj_data.obj
            mod = obj_data.active_mod()
            if not obj or not mod: continue
            yield obj, mod

    # --- EXIT --- #

    def common_exit(self, context):
        infobar.remove(self)
        context.area.header_text_set(text=None)
        collapse_3D_view_panels(self.original_tool_shelf, self.original_n_panel)
        self.remove_shader()
        self.master.run_fade()
        self.__class__.operator = None


    def confirm_exit(self, context):
        self.mod_controller.confirm_exit()


    def cancel_exit(self, context):
        self.mod_controller.cancel_exit()

        if self.scaleapply:
            objs, scales = [], []
            for obj_data in self.mod_controller.validated_obj_datas():
                objs.append(obj_data.obj)
                scales.append(obj_data.scale)
            apply_scale(objs, scales)

    # --- SHADER --- #

    def safe_draw_shader(self, context):
        method_handler(self.draw_shader,
            arguments = (context,),
            identifier = 'Bevel Shader',
            exit_method = self.remove_shader)


    def remove_shader(self):
        if self.draw_handle:
            self.draw_handle = bpy.types.SpaceView3D.draw_handler_remove(self.draw_handle, "WINDOW")


    def draw_shader(self, context):
        draw_modal_frame(context)

# --- UTILS --- #

def snap(value, increment):
        return round(value / increment) * increment

# --- POPOVER --- #

def popup_draw(self, context):
    layout = self.layout

    op = HOPS_OT_AdjustBevelOperator.operator
    if not op: return {'CANCELLED'}

    layout.label(text='Selector')

    mods = [m.name for m in op.mod_controller.active_obj_mods()]

    broadcaster = "hops.popover_data"

    for mod in mods:
        row = layout.row()
        row.scale_y = 2
        props = row.operator(broadcaster, text=mod)
        props.calling_ops = 'BEVEL_ADJUST'
        props.str_1 = mod
