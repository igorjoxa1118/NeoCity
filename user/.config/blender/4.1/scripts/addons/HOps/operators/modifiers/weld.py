import bpy, math
from mathutils import Vector
from ... utility import addon
from ... utility import modifier
from ... utility.base_modal_controls import Base_Modal_Controls
from ... ui_framework.master import Master
from ... ui_framework.utils.mods_list import get_mods_list

# Cursor Warp imports
from ... utils.toggle_view3d_panels import collapse_3D_view_panels
from ... utils.modal_frame_drawing import draw_modal_frame
from ... utils.cursor_warp import mouse_warp
from ... utility import method_handler


DESC = """LMB - Adjust Weld Modifier
LMB + CTRL - Add new Weld Modifier

Press H for help
"""

class HOPS_OT_MOD_Weld(bpy.types.Operator):
    bl_idname = "hops.mod_weld"
    bl_label = "Adjust Weld Modifier"
    bl_options = {"REGISTER", "UNDO", "BLOCKING"}
    bl_description = DESC

    weld_objects = {}

    @classmethod
    def poll(cls, context):
        return any(o.type == 'MESH' for o in context.selected_objects)

    @staticmethod
    def weld_modifiers(object):
        return [modifier for modifier in object.modifiers if modifier.type == "WELD"]


    def invoke(self, context, event):

        self.objects = [o for o in context.selected_objects if o.type == 'MESH']
        self.object = context.active_object if context.active_object else self.objects[0]
        self.modal_scale = addon.preference().ui.Hops_modal_scale
        self.weld_objects = {}
        self.snap_buffer = 0
        self.snap_break = 0.1

        for object in self.objects:
            self.get_weld_modifier(context, object, event)
            object.show_wire = True
            object.show_all_edges = True

        self.store_values()

        self.active_weld_modifier = context.object.modifiers[self.weld_objects[context.object.name]["modifier"]]

        for object in self.objects:
            modifier.sort(object, types=['WEIGHTED_NORMAL'], last=True)

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

        offset = self.base_controls.mouse / 10
        if not event.ctrl:
            merge_threshold_offset = offset
        else:
            merge_threshold_offset = 0
        context.area.header_text_set("Hardops weld:     merge threshold: {:.4f}".format(self.active_weld_modifier.merge_threshold))

        for object_name in self.weld_objects:
            object = bpy.data.objects[object_name]
            modifier = object.modifiers[self.weld_objects[object_name]["modifier"]]

            # if event.ctrl:
            #     self.snap_buffer += self.base_controls.mouse
            #     if abs(self.snap_buffer) > self.snap_break:
            #         modifier.max_interactions = snap(modifier.max_interactions, 1) + math.copysign(1, self.snap_buffer)
            #         self.snap_buffer = 0

            # else:
            modifier.merge_threshold = self.weld_objects[object_name]["buffer_threshold"] + merge_threshold_offset
            self.weld_objects[object_name]["buffer_threshold"] = modifier.merge_threshold

            if self.base_controls.scroll:
                if event.shift and event.ctrl:
                    self.cycle_vgroup(object, modifier, forward=self.base_controls.scroll)

                elif event.shift:
                    if self.base_controls.scroll ==1:
                        bpy.ops.object.modifier_move_up(modifier=modifier.name)
                    else:
                        bpy.ops.object.modifier_move_down(modifier=modifier.name)
                else:
                    modifier.merge_threshold += 0.005 * self.base_controls.scroll
                    self.weld_objects[object_name]["buffer_threshold"] = modifier.merge_threshold

            if event.type == "Z" and event.value == "PRESS":
                object.show_wire = False if object.show_wire else True
                object.show_all_edges = True if object.show_wire else False
                # self.report({'INFO'}, F'Show Wire : {object.show_all_edges}')

            if self.base_controls.cancel:
                object.show_wire = False
                object.show_all_edges = False
                self.restore()
                context.area.header_text_set(text=None)
                self.remove_shader()
                collapse_3D_view_panels(self.original_tool_shelf, self.original_n_panel)
                self.master.run_fade()
                return {'CANCELLED'}

            if self.base_controls.confirm:
                object.show_wire = False
                object.show_all_edges = False
                context.area.header_text_set(text=None)
                self.remove_shader()
                collapse_3D_view_panels(self.original_tool_shelf, self.original_n_panel)
                self.master.run_fade()
                return {'FINISHED'}

            if event.type == 'A' and event.value == 'PRESS':
                self.toggle_mod_mode(modifier)


        self.active_weld_modifier = self.object.modifiers[self.weld_objects[self.object.name]["modifier"]]

        self.interface(context=context)
        context.area.tag_redraw()
        return {"RUNNING_MODAL"}


    def toggle_mod_mode(self, mod):
        if not hasattr(mod, 'mode'): return
        if mod.mode == 'CONNECTED':
            mod.mode = 'ALL'
        elif mod.mode == 'ALL':
            mod.mode = 'CONNECTED'


    def cycle_vgroup(self, obj, mod, forward=True):

        if not obj.vertex_groups:
            bpy.ops.hops.display_notification(info="No V-Groups")
            return
        groups = [v.name for v in obj.vertex_groups]
        index = 0
        if mod.vertex_group not in groups:
            mod.vertex_group = groups[0]
            bpy.ops.hops.display_notification(info=f"V-Group Assigned : {groups[0]}")
            return
        index = groups.index(mod.vertex_group)
        value = 1 if forward else -1
        group = groups[(index + value) % len(groups)]
        mod.vertex_group = group

        bpy.ops.hops.display_notification(info=f"V-Group Assigned : {group}")


    def get_weld_modifier(self, context, object, event):
        if event.ctrl:
            mod = self.add_weld_modifier(context, object)
        else:
            try: self.weld_objects.setdefault(object.name, {})["modifier"] = self.weld_modifiers(object)[-1].name
            except: self.add_weld_modifier(context, object)


    def add_weld_modifier(self, context, object):

        weld_modifier = object.modifiers.new(name="Weld", type="WELD")
        weld_modifier.merge_threshold = 0.0001
        #weld_modifier.max_interactions = 0

        if context.mode == 'EDIT_MESH':
            vg = object.vertex_groups.new(name='HardOps')
            bpy.ops.object.vertex_group_assign()
            weld_modifier.vertex_group = vg.name

        self.weld_objects.setdefault(object.name, {})["modifier"] = weld_modifier.name
        self.weld_objects[object.name]["added_modifier"] = True


    def store_values(self):
        for object_name in self.weld_objects:
            object = bpy.data.objects[object_name]
            modifier = object.modifiers[self.weld_objects[object_name]["modifier"]]
            self.weld_objects[object_name]["show_viewport"] = modifier.show_viewport
            self.weld_objects[object_name]["merge_threshold"] = modifier.merge_threshold
            #self.weld_objects[object_name]["max_interactions"] = modifier.max_interactions
            self.weld_objects[object_name]["buffer_threshold"] = modifier.merge_threshold
            #self.weld_objects[object_name]["buffer_interactions"] = modifier.max_interactions
            self.weld_objects[object_name]["vertex_group"] = modifier.vertex_group


    def restore(self):
        for object_name in self.weld_objects:
            object = bpy.data.objects[object_name]
            if "added_modifier" in self.weld_objects[object_name]:
                object.modifiers.remove(object.modifiers[self.weld_objects[object_name]["modifier"]])
            else:
                modifier = object.modifiers[self.weld_objects[object_name]["modifier"]]
                modifier.show_viewport = self.weld_objects[object_name]["show_viewport"]
                modifier.merge_threshold = self.weld_objects[object_name]["merge_threshold"]
                modifier.vertex_group = self.weld_objects[object_name]["vertex_group"]
                #modifier.max_interactions = self.weld_objects[object_name]["max_interactions"]
        self.original_viewport = bpy.context.space_data.overlay.show_overlays
        self.show_wireframes = bpy.context.space_data.overlay.show_wireframes


    def interface(self, context):
        self.master.setup()

        if self.master.should_build_fast_ui():

            v_group = self.active_weld_modifier.vertex_group

            # Main
            win_list = []
            if addon.preference().ui.Hops_modal_fast_ui_loc_options != 1: #Fast Floating
                win_list.append("{:.4f}".format(self.active_weld_modifier.merge_threshold))
                #win_list.append("{}".format(self.active_weld_modifier.max_interactions))
            else:
                win_list.append("Weld")
                win_list.append("Threshold: {:.4f}".format(self.active_weld_modifier.merge_threshold))
                if v_group:
                    win_list.append(f"V-Group: {v_group}")
                if hasattr(self.active_weld_modifier, 'mode'):
                    win_list.append(f"Mode: {self.active_weld_modifier.mode}")
                #win_list.append("Duplicate Limit: {}".format(self.active_weld_modifier.max_interactions))

            # Help
            help_items = {"GLOBAL" : [], "STANDARD" : []}

            help_items["GLOBAL"] = [
                ("M", "Toggle mods list"),
                ("H", "Toggle help"),
                ("~", "Toggle UI Display Type"),
                ("O", "Toggle viewport rendering")]

            help_items["STANDARD"] = [
                ("Move",           "Set merge threshold"),
                ("Shift + Scroll", "Move mod up/down"),
                ("Shift + Ctrl + Scroll",  "Cycles V-Groups : " + str(v_group) if v_group else "Cycle V-Groups"),
                ("Shift + Q",      "Move mod down"),
                ("Shift + W",      "Move mod up"),
                ("Z",              "Toggle wire display")]

            if hasattr(self.active_weld_modifier, 'mode'):
                help_items["STANDARD"].append(("A", "Toggle Mode"))

            # Mods
            active_mod = ""
            if self.active_weld_modifier != None:
                active_mod = self.active_weld_modifier.name
            mods_list = get_mods_list(mods=bpy.context.active_object.modifiers)

            self.master.receive_fast_ui(win_list=win_list, help_list=help_items, image="BevelMultiply", mods_list=mods_list, active_mod_name=active_mod)

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


def snap(value, increment):
        result = round(value / increment) * increment
        return result
