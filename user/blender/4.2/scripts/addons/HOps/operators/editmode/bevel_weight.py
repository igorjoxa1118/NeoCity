import bpy, bmesh
from mathutils import Vector
from ... utility import addon
from ... ui_framework.master import Master
from ... ui_framework.utils.mods_list import get_mods_list
from ... utility.base_modal_controls import Base_Modal_Controls

# Cursor Warp imports
from ... utils.toggle_view3d_panels import collapse_3D_view_panels
from ... utils.modal_frame_drawing import draw_modal_frame
from ... utils.cursor_warp import mouse_warp
from ... utility import method_handler


class HOPS_OT_AdjustBevelWeightOperator(bpy.types.Operator):
    bl_idname = "hops.bevel_weight"
    bl_label = "Adjust Bevel Weight"
    bl_options = {"REGISTER", "UNDO", "BLOCKING"}
    bl_description = """Adjust the bevel weight of selected edges
Press H for help"""

    bevel_data: bpy.props.EnumProperty(
        name="Mode",
        description="option to affect bevel weight selection",
        items=[("Edges", "Edges", "Edges"),
               ("Verts", "Verts", "Verts")],
        default="Edges")

    @classmethod
    def poll(cls, context):
        if context.active_object != None:
            object = context.active_object
            return(object.type == 'MESH' and context.mode == 'EDIT_MESH')
        return False

    def invoke(self, context, event):

        self.bevel_data = 'Verts' if tuple(bpy.context.tool_settings.mesh_select_mode) == (True, False, False) else 'Edges'
        self.value = 0
        self.start_value_edge = self.detect(context, 'edges')
        self.start_value_vert = self.detect(context, 'verts')
        self.offset = 0

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


        self.offset += self.base_controls.mouse
        self.offset = 1 if self.offset> 1 else self.offset
        self.offset = -1 if self.offset< -1 else self.offset

        obj = bpy.context.object
        me = obj.data
        bm = bmesh.from_edit_mesh(me)
        if bpy.app.version[0] >= 4:
            bw_e = bm.edges.layers.float.get('bevel_weight_edge')
            if bw_e is None:
                bw_e = bm.edges.layers.float.new('bevel_weight_edge')
        else:
            bw_e = bm.edges.layers.bevel_weight.verify()

        if bpy.app.version[0] >= 4:
            bw_v = bm.verts.layers.float.get('bevel_weight_vert')
            if bw_v is None:
                bw_v = bm.verts.layers.float.new('bevel_weight_vert')
        else:
            bw_v = bm.verts.layers.bevel_weight.verify()

        if self.bevel_data == 'Edges':

            self.value_base_edge = float("{:.2f}".format(self.start_value_edge + self.offset))
            self.value = max(self.value_base_edge, 0) and min(self.value_base_edge, 1)


        elif self.bevel_data == 'Verts':

            self.value_base_vert = float("{:.2f}".format(self.start_value_vert + self.offset))
            self.value = max(self.value_base_vert, 0) and min(self.value_base_vert, 1)


        if not event.ctrl and not event.shift:
            self.value = round(self.value, 1)

        selected = [e for e in bm.edges if e.select] if self.bevel_data == 'Edges' else [v for v in bm.verts if v.select]
        bw = bw_e if self.bevel_data == 'Edges' else bw_v
        for s in selected:
            s[bw] = self.value

        bmesh.update_edit_mesh(me)

        if self.base_controls.cancel:
            for s in selected:
                s[bw] = self.start_value_edge if self.bevel_data == 'Edges' else self.start_value_vert
            bmesh.update_edit_mesh(me)
            self.remove_shader()
            collapse_3D_view_panels(self.original_tool_shelf, self.original_n_panel)
            self.master.run_fade()
            return {'CANCELLED'}

        if self.base_controls.confirm:
            self.remove_shader()
            collapse_3D_view_panels(self.original_tool_shelf, self.original_n_panel)
            self.master.run_fade()
            return {'FINISHED'}

        if event.type == 'A' and event.value == 'PRESS' and event.ctrl:
            selectedbw = [e for e in bm.edges if e[bw] > 0] if self.bevel_data == 'Edges' else [v for v in bm.verts if v[bw] > 0]
            for s in selectedbw:
                s.select_set(True)

        elif event.type == 'A' and event.value == 'PRESS' and not event.ctrl:
            bpy.ops.mesh.select_linked(delimit=set())
            selectedbw = [e for e in bm.edges if e[bw] == 0] if self.bevel_data == 'Edges' else [v for v in bm.verts if v[bw] > 0]

            for s in selectedbw:
                s.select_set(False)
                for elem in reversed(bm.select_history):
                    if self.bevel_data == 'Edges':
                        if isinstance(elem, bmesh.types.BMEdge):
                            elem.select_set(True)
                    else:
                        if isinstance(elem, bmesh.types.BMVert):
                            elem.select_set(True)

        if event.type == 'V' and event.value == 'PRESS':
            if self.bevel_data == 'Edges':
                self.bevel_data = 'Verts'
            else:
                self.bevel_data = 'Edges'

        self.draw_master(context=context)
        context.area.tag_redraw()
        return {"RUNNING_MODAL"}


    def detect(self, context, data):

        obj = bpy.context.object
        me = obj.data
        bm = bmesh.from_edit_mesh(me)

        if bpy.app.version[0] >= 4:
            bw = bm.edges.layers.float.get('bevel_weight_edge') if data == 'edges' else bm.verts.layers.float.get('bevel_weight_vert')
            if bw is None:
                bw = bm.edges.layers.float.new('bevel_weight_edge') if data == 'edges' else bm.verts.layers.float.new('bevel_weight_vert')
        else:
            bw = bm.edges.layers.bevel_weight.verify() if data == 'edges' else bm.verts.layers.bevel_weight.verify()

        selected = [e for e in bm.edges if e.select] if data == 'edges' else [v for v in bm.verts if v.select]
        bmesh.update_edit_mesh(me)

        if len(selected) > 0:
            return selected[-1][bw]
        else:
            return 0


    def draw_master(self, context):

        # Start
        self.master.setup()

        ########################
        #   Fast UI
        ########################

        if self.master.should_build_fast_ui():

            # Main
            win_list = []
            if addon.preference().ui.Hops_modal_fast_ui_loc_options != 1:
                win_list.append(self.value)
                win_list.append(self.bevel_data)
            else:
                win_list.append("Bevel Weight")
                win_list.append(self.value)
                win_list.append(self.bevel_data)

            # Help
            help_items = {"GLOBAL" : [], "STANDARD" : []}

            help_items["GLOBAL"] = [
                ("M", "Toggle mods list"),
                ("H", "Toggle help"),
                ("~", "Toggle UI Display Type"),
                ("O", "Toggle viewport rendering"),
            ]

            help_items["STANDARD"] = [
                ("A",        "Select all weights in mesh"),
                ("Ctrl + A", "Select all weights"),
                ("V", "Toggle bevel data"),
            ]

            # Mods
            active_mod = ""
            mods_list = []
            mods_list = get_mods_list(mods=bpy.context.active_object.modifiers)

            self.master.receive_fast_ui(win_list=win_list, help_list=help_items, image="AdjustBevel", mods_list=mods_list, active_mod_name=active_mod)

        # Finished
        self.master.finished()

    ####################################################
    #   CURSOR WARP
    ####################################################

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