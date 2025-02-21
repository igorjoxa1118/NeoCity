import bpy
from enum import Enum
from ... utility import method_handler
from ... ui_framework import form_ui as form
from ... utility.base_modal_controls import Base_Modal_Controls
from ... ui_framework.master import Master
from ... ui_framework.utils.dialogue import Dialogue

from .cycle_node import validate_context


'''
Notes

- Ability to save a selection set as a node group
- Abilty to explode a group into the graph (something to detect if it was originally a group?)
- On exit : Remove all the other node groups
- Probably should add node groups in the current blend into the main scrolling group
- Keep an eye on : adding groups when blender auto numbers things
- Saving groups : probably the reverse of reading groups

- Write code notes:
    - It overwrites every thing in the other file
    - Might need to save every thing that was loaded in plus every thing created
    - When saving files : it will save the node group that the main node group is also in
    - Basically make sure to not save the "modifier main group"

'''



DESC = """Scroll / Save : Nodes

Press H for help"""


class HOPS_OT_Cycle_Node_Groups(bpy.types.Operator):
    bl_idname = "hops.cycle_node_groups"
    bl_label = "Cycle Geo Nodes"
    bl_description = DESC
    bl_options = {"REGISTER", "UNDO", "BLOCKING"}

    @classmethod
    def poll(cls, context):
        if context.area:
            if context.area.ui_type in {'GeometryNodeTree', 'ShaderNodeTree'}:
                return True
        return False


    def invoke(self, context, event):
        # Validate
        if not validate_context(context):
            return {'CANCELLED'}


        # NOTE: Write code
        # groups = {*bpy.data.node_groups}
        # bpy.data.libraries.write(filepath=filepath, datablocks=groups, fake_user=True)


        filedir = 'C:/Users/smwga/Desktop/Demos/NODE-Groups.blend'
        self.imported = []

        with bpy.data.libraries.load(filedir) as (data_from, data_to):
            internal_groups = bpy.data.node_groups
            external_groups = getattr(data_from, 'node_groups')
            self.imported = [g for g in external_groups if g not in internal_groups]
            setattr(data_to, 'node_groups', self.imported)

        print(self.imported)

        # Tool Shelf
        self.show_region = bpy.context.space_data.show_region_ui
        bpy.context.space_data.show_region_ui = False

        # Form
        self.form_exit = False
        self.form = None
        self.setup_form(context, event)
        self.draw_handle_2D = bpy.types.SpaceNodeEditor.draw_handler_add(self.safe_draw_2D, (context,), 'WINDOW', 'POST_PIXEL')

        # Input
        self.dialogue = Dialogue(context, self.set_dialogue, help_text="Enter : Group Name")
        self.dialogue_str = ""

        # Base Systems
        self.master = Master(context)
        self.master.only_use_fast_ui = True
        self.base_controls = Base_Modal_Controls(context, event)
        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}


    def modal(self, context, event):

        self.base_controls.update(context, event)
        self.form.update(context, event)
        skip_m_h = self.form.active()
        self.master.receive_event(event, skip_m_h)

        unblocked = True
        if self.dialogue.active or self.form.active():
            unblocked = False

        if self.base_controls.pass_through:
            if unblocked:
                return {'PASS_THROUGH'}

        elif self.base_controls.confirm:
            if unblocked:
                return self.confirm_exit(context)

        elif self.base_controls.cancel:
            if unblocked:
                return self.cancel_exit(context)

        if event.type == 'TAB' and event.value == 'PRESS':
            if not self.dialogue.active:
                if self.form.is_dot_open():
                    self.form.close_dot()
                else:
                    self.form.open_dot()

        # Dialogue Menu : Update
        if self.dialogue.active:
            self.dialogue.update(event)

        # Actions
        if unblocked:
            self.actions(context, event)

        self.interface(context)
        context.area.tag_redraw()
        return {"RUNNING_MODAL"}


    def actions(self, context, event):

        # Tool Shelf
        if event.type == 'N' and event.value == 'PRESS':
            return {'PASS_THROUGH'}
        
        # Cycle Groups
        elif self.base_controls.scroll:
            scroll = self.base_controls.scroll

        # Dialogue Menu : Spawn
        elif event.type == 'S' and event.value == 'PRESS':
            self.dialogue.start()


    def interface(self, context):

        self.master.setup()
        if not self.master.should_build_fast_ui(): return

        # Main
        win_list = []
        w_append = win_list.append
        
        w_append("XXX")
        
        # Help
        help_items = {"GLOBAL" : [], "STANDARD" : []}

        help_items["GLOBAL"] = [
            ("H", "Toggle help"),
            ("N", "Toggle Side Panel"),
            ("~", "Toggle UI Display Type"),]

        h_append = help_items["STANDARD"].append
        h_append(('TAB' , 'Dot UI'))
        h_append(('S' , 'Save Dialogue'))
        help_items["STANDARD"].reverse()

        self.master.receive_fast_ui(win_list=win_list, help_list=help_items, image="green")
        self.master.finished()

    # --- FORM --- #

    def setup_form(self, context, event):
        self.form = form.Form(context, event, dot_open=False)

        def spacer(height=10, label='', active=True):
            row = self.form.row()
            row.add_element(form.Spacer(height=height))
            self.form.row_insert(row, label, active)

        # --- All --- #
        
        self.form.build()


    # --- UTILS --- #

    def set_dialogue(self, string):
        self.dialogue_str = string

    # --- EXITS --- #

    def common_exit(self, context):
        self.remove_shaders()
        self.form.shut_down(context)
        self.master.run_fade()
        bpy.context.space_data.show_region_ui = self.show_region
        context.area.tag_redraw()


    def confirm_exit(self, context):
        self.common_exit(context)
        return {'FINISHED'}


    def cancel_exit(self, context):
        self.common_exit(context)
        return {'CANCELLED'}

    # --- SHADERS --- #

    def remove_shaders(self):
        if self.draw_handle_2D:
            self.draw_handle_2D = bpy.types.SpaceNodeEditor.draw_handler_remove(self.draw_handle_2D, "WINDOW")


    def safe_draw_2D(self, context):
        method_handler(self.draw_shader_2D,
            arguments = (context,),
            identifier = 'Modal Shader 2D',
            exit_method = self.remove_shaders)


    def draw_shader_2D(self, context):
        self.form.draw()
        self.dialogue.draw()