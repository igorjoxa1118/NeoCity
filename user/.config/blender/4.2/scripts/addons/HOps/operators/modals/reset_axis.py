import bpy, bmesh
from collections import OrderedDict
from ... utility import addon
from ...ui_framework.master import Master
from ...ui_framework.utils.mods_list import get_mods_list
from . import infobar
from ... utility.base_modal_controls import Base_Modal_Controls
from ... utils.objects import set_active


class HOPS_OT_Align_Objs(bpy.types.Operator):
    bl_idname = "hops.align_objs"
    bl_label = "Hops Align Objects"
    bl_description = """Align Objects
    
    Align Objects

    """
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object and len(context.selected_objects) > 1


    def execute(self, context):
        active = context.active_object
        selection = [obj for obj in context.selected_objects if obj != active]

        loc, rot, sca = active.matrix_world.decompose()
        for obj in selection:
            obj.location = loc
            obj.rotation_euler = rot.to_euler()

        return {'FINISHED'}


class HOPS_OT_ResetAxisModal(bpy.types.Operator):
    bl_idname = "hops.reset_axis_modal"
    bl_label = "Hops Reset Axis"
    bl_description = """ Reset / Flatten
    
    Reset object on selected axis.

    Object - Resets object axis globally
        *two object axis supported*
    Edit - flatten selection to axis or snap to cursor
    
    """
    bl_options = {"REGISTER", "UNDO"}


    def invoke(self, context, event):

        self.setup(context)

        self.base_controls = Base_Modal_Controls(context, event)
        self.master = Master(context)
        self.master.only_use_fast_ui = True

        context.window_manager.modal_handler_add(self)
        infobar.initiate(self)
        return {"RUNNING_MODAL"}


    def setup(self, context):
        if context.active_object.mode == "EDIT":
            self.bm = bmesh.from_edit_mesh(context.active_object.data)
            self.original_verts = [[i for i in vert.co] for vert in self.bm.verts]
        self.active_obj_original_location = [i for i in context.active_object.matrix_world.translation]
        self.original_locations = [[i for i in obj.matrix_world.translation] for obj in context.selected_objects]
        self.axises = []
        self.set_axis = ""
        self.xyz = ["X", "Y", "Z"]
        self.xyz_index = -1


    def modal(self, context, event):

        self.master.receive_event(event)
        self.base_controls.update(context, event)

        if self.base_controls.cancel:
            self.reset_object()
            self.master.run_fade()
            infobar.remove(self)
            return {'CANCELLED'}

        elif self.base_controls.confirm:
            self.selection_exit(context)
            self.master.run_fade()
            infobar.remove(self)
            return {'FINISHED'}

        elif self.base_controls.pass_through:
            return {'PASS_THROUGH'}

        elif self.base_controls.scroll:
            self.reset_object()
            self.xyz_index -= self.base_controls.scroll
            self.xyz_index = min(max(-1, self.xyz_index), 2)
            if self.xyz_index == -1:
                self.set_axis = "RESET"
            else:
                self.set_axis = self.xyz[self.xyz_index]

        elif event.type == 'C' and event.value == 'PRESS':
            if event.shift:
                if self.set_axis == "CO":
                    self.set_axis = "RESET"
                else:
                    self.set_axis = "CO"
                    bpy.ops.view3d.snap_selected_to_cursor(use_offset=True)
                    context.view_layer.objects.active.select_set(True)
                    self.report({'INFO'}, F'Snapped to: Cursor (offset)')
            else:
                if self.set_axis == "C":
                    self.set_axis = "RESET"
                else:
                    self.set_axis = "C"
                    bpy.ops.view3d.snap_selected_to_cursor(use_offset=False)
                    context.view_layer.objects.active.select_set(True)
                    self.report({'INFO'}, F'Snapped to: Cursor')

        elif event.type == 'X' and event.value == 'PRESS':
            if self.set_axis == "X":
                self.set_axis = "RESET"
            else:
                self.set_axis = "X"
                self.report({'INFO'}, F'Snapped to: X Axis')
            self.axises.append("X")

        elif event.type == 'Y' and event.value == 'PRESS':
            if self.set_axis == "Y":
                self.set_axis = "RESET"
            else:
                self.set_axis = "Y"
                self.report({'INFO'}, F'Snapped to: Y Axis')
            self.axises.append("Y")

        elif event.type == 'Z' and event.value == 'PRESS':
            if self.set_axis == "Z":
                self.set_axis = "RESET"
            else:
                self.set_axis = "Z"
                self.report({'INFO'}, F'Snapped to: Z Axis')
            self.axises.append("Z")

        elif event.type == 'A' and event.value == 'PRESS':
            if HOPS_OT_Align_Objs.poll(context):
                bpy.ops.hops.align_objs('INVOKE_DEFAULT')
                self.setup(context)

        elif self.base_controls.tilde and event.shift == True:
            bpy.context.space_data.overlay.show_overlays = not bpy.context.space_data.overlay.show_overlays

        if context.active_object.mode == "OBJECT":
            for obj in context.selected_objects:
                reset_to = [0, 0, 0]
                if len(context.selected_objects) > 1:
                    reset_to = self.active_obj_original_location
                if self.set_axis == "X":
                    obj.matrix_world.translation[0] = reset_to[0]
                elif self.set_axis == "Y":
                    obj.matrix_world.translation[1] = reset_to[1]
                elif self.set_axis == "Z":
                    obj.matrix_world.translation[2] = reset_to[2]

        elif context.active_object.mode == "EDIT":
            if self.set_axis == "X":
                bpy.ops.transform.resize(value=(0, 1, 1), orient_type='GLOBAL', orient_matrix_type='GLOBAL', constraint_axis=(True, False, False))
            elif self.set_axis == "Y":
                bpy.ops.transform.resize(value=(1, 0, 1), orient_type='GLOBAL', orient_matrix_type='GLOBAL', constraint_axis=(False, True, False))
            elif self.set_axis == "Z":
                bpy.ops.transform.resize(value=(1, 1, 0), orient_type='GLOBAL', orient_matrix_type='GLOBAL', constraint_axis=(False, False, True))

        if self.set_axis == "RESET":
            self.reset_object()

        self.draw_master(context=context)
        context.area.tag_redraw()
        return {"RUNNING_MODAL"}


    def reset_object(self):
        if bpy.context.active_object.mode == "EDIT":
            for count, vert in enumerate(self.bm.verts):
                vert.co = self.original_verts[count]
            bpy.ops.mesh.normals_make_consistent(inside=False)
        else:
            for count, obj in enumerate(bpy.context.selected_objects):
                obj.matrix_world.translation = self.original_locations[count]


    def selection_exit(self, context):
        if context.active_object.mode != "OBJECT": return
        if context.active_object == None: return
        if len(context.selected_objects) != 2: return
        other = [o for o in context.selected_objects if o != context.active_object][0]
        if not other: return
        set_active(other, select=True, only_select=True)


    def draw_master(self, context):
        self.master.setup()
        if not self.master.should_build_fast_ui(): return

        # Main
        win_list = []
        axis = self.set_axis
        if axis == "RESET":
            axis = ""
            self.axises = []
        if len(axis) > 1:
            axis = axis[0]

        if axis == "":
            axis = "None"

        if addon.preference().ui.Hops_modal_fast_ui_loc_options != 1: #Fast Floating
            win_list.append(axis)
            win_list.append(format(", ".join(list(OrderedDict.fromkeys(self.axises)))))
        else:
            win_list.append("Reset Axis")
            win_list.append(axis)
            win_list.append("Axis - {}".format(", ".join(list(OrderedDict.fromkeys(self.axises)))))

        # Help
        help_items = {"GLOBAL" : [], "STANDARD" : []}

        help_items["GLOBAL"] = [
            ("M", "Toggle mods list"),
            ("H", "Toggle help"),
            ("~", "Toggle UI Display Type"),
            ("O", "Toggle viewport rendering")]

        help_items["STANDARD"] = [
            ("A",         "Align Objects"),
            ("X",         "Reset x axis"),
            ("Y",         "Reset y axis"),
            ("Z",         "Reset z axis"),
            ("C",         "Snap to cursor"),
            ("C + Shift", "Snap to cursor offset"),
            ("Scroll",    "Change axis")]

        # Mods
        mods_list = get_mods_list(mods=bpy.context.active_object.modifiers)

        self.master.receive_fast_ui(win_list=win_list, help_list=help_items, image="Xslap", mods_list=mods_list)
        self.master.finished()
