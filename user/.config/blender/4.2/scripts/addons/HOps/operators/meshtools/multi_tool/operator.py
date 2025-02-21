from .utils import *
from .select import Select
from .spin import Spin
from .merge import Merge
from .dissolve import Dissolve
from .join import Join
from .knife import Knife

from bpy.props import EnumProperty

tool_type_items = [
        ("SELECT", "SELECT", ""),
        ("SPIN", "SPIN", ""),
        ("MERGE", "MERGE", ""),
        ("DISSOLVE", "DISSOLVE", ""),
        ("JOIN", "JOIN", ""),
        ("KNIFE", "KNIFE", "")]

#set mode on prop update
def tool_update(self, context):
    instance = HOPS_OT_FastMeshEditor.instance
    if not instance: return

    entry = instance.tool_type

    if entry == 'SELECT':
        instance.tool = Tool.SELECT
    elif entry == 'SPIN':
        instance.tool = Tool.SPIN
    elif entry == 'MERGE':
        instance.tool = Tool.MERGE
    elif entry == 'DISSOLVE':
        instance.tool = Tool.DISSOLVE
    elif entry == 'JOIN':
        instance.tool = Tool.JOIN
    elif entry == 'KNIFE':
        instance.tool = Tool.KNIFE

    instance.ensure_selection_change()


class HOPS_OT_FastMeshEditor(bpy.types.Operator):
    bl_idname = "hops.fast_mesh_editor"
    bl_label = "Fast mesh editor"
    bl_description = """Fast Mesh Editor
    Quickly do basic edits on the mesh
    Press H for help
    """
    bl_options = {"REGISTER", "UNDO", "BLOCKING"}
    relaunch_tool: StringProperty(default="")

    # operator instance to communicate with popover
    instance = None

    # prop for popover to draw
    tool_type: EnumProperty(
    name="Tool Type",
    description="",
    items=tool_type_items,
    default='SELECT',
    update=tool_update)

    @classmethod
    def poll(cls, context):
        if context.active_object != None:
            if context.active_object.type == 'MESH':
                return True
        return False


    def invoke(self, context, event):

        # Correct mode state
        if context.mode == 'OBJECT':
            bpy.ops.object.mode_set(mode='EDIT')

        # Tool state
        self.tool = Tool.SELECT
        entry = addon.preference().property.multi_tool_entry
        entry = self.relaunch_tool if self.relaunch_tool != "" else entry

        self.tool_type = entry
        self.__class__.instance = self

        if entry == 'SELECT':
            self.tool = Tool.SELECT
        elif entry == 'SPIN':
            self.tool = Tool.SPIN
        elif entry == 'MERGE':
            self.tool = Tool.MERGE
        elif entry == 'DISSOLVE':
            self.tool = Tool.DISSOLVE
        elif entry == 'JOIN':
            self.tool = Tool.JOIN
        elif entry == 'KNIFE':
            self.tool = Tool.KNIFE

        # Data container
        self.data = Data(context, event)

        # Tools
        self.select = Select()
        self.spin = Spin()
        self.merge = Merge(context)
        self.dissolve = Dissolve()
        self.join = Join()
        self.knife = Knife()
        self.setup_tool_data()

        # Flow menu
        self.flow = Flow_Menu() if addon.preference().property.menu_style_selector == 'DEFAULT' else FlowDummy()
        self.setup_flow_menu()

        # Base Systems
        self.master = Master(context=context)
        self.master.only_use_fast_ui = True
        self.base_controls = Base_Modal_Controls(context, event)
        self.original_tool_shelf, self.original_n_panel = collapse_3D_view_panels()
        self.draw_handle_2D = bpy.types.SpaceView3D.draw_handler_add(self.safe_draw_2D, (context,), 'WINDOW', 'POST_PIXEL')
        self.draw_handle_3D = bpy.types.SpaceView3D.draw_handler_add(self.safe_draw_3D, (context,), 'WINDOW', 'POST_VIEW')
        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}


    def setup_flow_menu(self):
        '''Setup flow menu system.'''

        flow_data = [
            Flow_Form(text="TOOLS",    font_size=18, tip_box="Pick a tool;TIP: Cant switch during bevel."),
            Flow_Form(text="SELECT",   font_size=14, func=self.flow_func, pos_args=(Tool.SELECT,  ), tip_box="Select tool."),
            Flow_Form(text="SPIN",     font_size=14, func=self.flow_func, pos_args=(Tool.SPIN,    ), tip_box="Spin tool."),
            Flow_Form(text="MERGE",    font_size=14, func=self.flow_func, pos_args=(Tool.MERGE,   ), tip_box="Merge tool."),
            Flow_Form(text="DISSOLVE", font_size=14, func=self.flow_func, pos_args=(Tool.DISSOLVE,), tip_box="Dissolve tool."),
            Flow_Form(text="JOIN",     font_size=14, func=self.flow_func, pos_args=(Tool.JOIN,    ), tip_box="Join tool."),
            Flow_Form(text="KNIFE",    font_size=14, func=self.flow_func, pos_args=(Tool.KNIFE,   ), tip_box="Knife tool.")
        ]
        self.flow.setup_flow_data(flow_data)


    def flow_func(self, tool=Tool.SELECT):
        '''Func to switch tools from flow menu.'''

        if self.data.locked == False:
            self.tool = tool
            self.ensure_selection_change()
        else:
            bpy.ops.hops.display_notification(info="Cancel locked state first")


    def modal(self, context, event):

        if event.type == 'TIMER':
            return {"RUNNING_MODAL"}

        # --- Base Systems --- #
        self.data.update(context, event)
        self.master.receive_event(event=event)
        self.base_controls.update(context, event)
        self.flow.run_updates(context, event, enable_tab_open=True)

        # --- Base Controls --- #
        # Navigation
        if self.base_controls.pass_through:
            return {'PASS_THROUGH'}

        elif self.base_controls.scroll and event.alt:
            new = (self.tool.value + self.base_controls.scroll) % 5 # current tool count
            self.tool = Tool(new)
            self.ensure_selection_change()

        elif self.tool != Tool.SELECT:
            if event.type in {'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
                return {'PASS_THROUGH'}

        # Cancel
        if self.base_controls.cancel:
            self.data.cancelled_exit()
            self.shut_down(context)
            return {'CANCELLED'}

        # Confirm exit
        if self.flow.is_open == False or not event.shift:
            if event.type in {'RET', 'SPACE', 'NUMPAD_ENTER'}:
                self.data.confirmed_exit()
                self.shut_down(context)
                return {'FINISHED'}

        # Toggle perspective
        if event.type in {'P', 'NUMPAD_5'} and not event.shift:
            if event.value == 'PRESS':
                bpy.ops.view3d.view_persportho()

        # Toggle poly debug
        if event.type == 'D' and event.shift and event.value == 'PRESS':
            bpy.ops.hops.poly_debug_display('INVOKE_DEFAULT')

        # Undo
        if event.type == 'Z' and event.ctrl and event.value == 'PRESS':
            self.data.undo()
            self.ensure_selection_change()

        # Apply current
        if event.type == 'W' and event.shift and event.value == 'PRESS':
            if self.data.locked == False:
                self.data.confirmed_exit()
                self.shut_down(context)
                bpy.ops.hops.display_notification(info="Blender Undo Registered")
                bpy.ops.hops.fast_mesh_editor('INVOKE_DEFAULT', relaunch_tool=self.tool.name)
                return {'FINISHED'}
            else:
                bpy.ops.hops.display_notification(info="Finish locked state first")

        # Check for tool switch
        if self.data.locked == False:
            self.tool_switcher(context, event)

        # --- Tools --- #
        if self.flow.is_open == False:
            method_handler(self.update_tools,
                arguments = (context, event),
                identifier = 'Tools Update',
                exit_method = self.remove_shaders)

        # Bmesh update
        self.data.update_bmesh()
        self.interface(context=context)
        context.area.tag_redraw()
        return {"RUNNING_MODAL"}


    def tool_switcher(self, context, event):
        '''Check for tool switches.'''

        if event.value != 'PRESS': return
        current = self.tool

        # Cycle Tools
        if event.type == 'X' and event.ctrl == False:
            if self.data.left_click_down: return # Make sure not in locked state
            if self.tool == Tool.SELECT:
                self.tool = Tool.SPIN
            elif self.tool == Tool.SPIN:
                self.tool = Tool.MERGE
            elif self.tool == Tool.MERGE:
                self.tool = Tool.DISSOLVE
            elif self.tool == Tool.DISSOLVE:
                self.tool = Tool.JOIN
            elif self.tool == Tool.JOIN:
                self.tool = Tool.KNIFE
            elif self.tool == Tool.KNIFE:
                self.tool = Tool.SELECT
        # SELECT
        elif event.type == 'S' and event.shift == False:
            self.tool = Tool.SELECT
        # SPIN
        elif event.type == 'S' and event.shift == True:
            self.tool = Tool.SPIN
        # MERGE
        elif event.type == 'M' and event.shift == False:
            self.tool = Tool.MERGE
        # DISSOLVE
        elif event.type == 'D' and event.shift == False:
            self.tool = Tool.DISSOLVE
        # JOIN
        elif event.type == 'J' and event.shift == False:
            self.tool = Tool.JOIN
        # KNIFE
        elif event.type == 'K' and event.shift == False:
            self.tool = Tool.KNIFE

        if self.tool != current: self.ensure_selection_change()


    def interface(self, context):

        self.master.setup()
        if self.master.should_build_fast_ui():
            win_list = []

            # Help
            help_items = {"GLOBAL" : [], "STANDARD" : []}

            help_items["GLOBAL"] = [
                ("H", "Toggle help"),
                ("~", "Toggle UI Display Type"),
                ("O", "Toggle viewport rendering"),
                ("", "________MODAL________"),
                ("K",         "KNIFE"),
                ("J",         "JOIN"),
                ("D",         "DISSOLVE"),
                ("M",         "MERGE"),
                ("S + Shift", "SPIN"),
                ("S",         "SELECT"),
                ("X",         "Toggle through tools"),
                ("", "________SWITCH________")]

            # Main / Help
            if self.tool == Tool.SELECT:
                win_list.append("TOOL: SELECT")
                win_list.append(f'Verts: {self.select.vert_count_draw}')
                help_items["STANDARD"] = self.select.help()

            elif self.tool == Tool.SPIN:
                win_list.append("TOOL: SPIN")
                help_items["STANDARD"] = self.spin.help()

            elif self.tool == Tool.MERGE:
                win_list.append("TOOL: MERGE")
                help_items["STANDARD"] = self.merge.help()

            elif self.tool == Tool.DISSOLVE:
                win_list.append("TOOL: DISSOLVE")
                help_items["STANDARD"] = self.dissolve.help()

            elif self.tool == Tool.JOIN:
                win_list.append("TOOL: JOIN")
                help_items["STANDARD"] = self.join.help()

            elif self.tool == Tool.KNIFE:
                win_list.append("TOOL: KNIFE")
                help_items["STANDARD"] = self.knife.help()

            # Base Help
            h_append = help_items["STANDARD"].append
            h_append(["Shift D",  "Toggle Poly Debug"])
            h_append(["Shift W",  "Save Blender Undo State"])
            h_append(["Ctrl + Z", "Undo"])
            h_append(["P / 5",    "Toggle Perspective"])
            h_append(["TAB",      "Spawn tool switcher"])
            h_append(["", "________UTILS________"])

            self.master.receive_fast_ui(win_list=win_list, help_list=help_items, image="logo_blue")
        self.master.finished()

    # --- EXIT --- #

    def shut_down(self, context):
        '''Shut down modal.'''

        # Close out shaders and ui
        self.remove_shaders()
        self.master.run_fade()
        # Flow system
        self.flow.shut_down()
        # Set the cursor back
        bpy.context.window.cursor_set("CROSSHAIR")
        # Update bmesh and leave
        self.data.shut_down()
        # Set the tool panels back
        collapse_3D_view_panels(self.original_tool_shelf, self.original_n_panel)
        # Tools
        self.tool_shut_downs(context)

        self.__class__.instance = None


    def tool_shut_downs(self, context):
        self.merge.shut_down(context)

    # --- TOOLS --- #

    def update_tools(self, context, event):
        '''Do tool actions.'''

        # Select
        if self.tool == Tool.SELECT:
            self.select.update(context, event, self.data, self)
        # Spin
        elif self.tool == Tool.SPIN:
            self.spin.update(context, event, self.data, self)
        # Merge
        elif self.tool == Tool.MERGE:
            self.merge.update(context, event, self.data, self)
        # Dissolve
        elif self.tool == Tool.DISSOLVE:
            self.dissolve.update(context, event, self.data, self)
        # Join
        elif self.tool == Tool.JOIN:
            self.join.update(context, event, self.data, self)
        # Kinfe
        elif self.tool == Tool.KNIFE:
            self.knife.update(context, event, self.data, self)

    # --- UTILS --- #

    def ensure_selection_change(self):
        '''Make sure the correct selection mode is active.'''

        self.setup_tool_data()

        if self.tool == Tool.SELECT:
            bpy.context.window.cursor_set("CROSSHAIR")

        elif self.tool == Tool.SPIN:
            bpy.context.window.cursor_set("SCROLL_XY")
            if 'EDGE' not in self.data.bm.select_mode:
                bpy.ops.mesh.select_mode(use_extend=False, type="EDGE")

        elif self.tool == Tool.MERGE:
            bpy.context.window.cursor_set("SCROLL_XY")
            if 'EDGE' in self.data.bm.select_mode:
                bpy.ops.mesh.select_mode(use_extend=False, type="VERT")

        elif self.tool == Tool.DISSOLVE:
            bpy.context.window.cursor_set("ERASER")
            bpy.ops.mesh.select_mode(use_extend=False, type="EDGE")

        elif self.tool == Tool.JOIN:
            bpy.context.window.cursor_set("SCROLL_XY")
            if self.data.bm.select_mode != 'VERT':
                bpy.ops.mesh.select_mode(use_extend=False, type="VERT")

        elif self.tool == Tool.KNIFE:
            bpy.context.window.cursor_set("KNIFE")


    def setup_tool_data(self):
        tools = [self.select, self.spin, self.merge, self.dissolve, self.join, self.knife]
        for tool in tools: tool.setup()

    # --- SHADERS --- #

    def remove_shaders(self):
        '''Remove shader handle.'''

        if self.draw_handle_2D:
            self.draw_handle_2D = bpy.types.SpaceView3D.draw_handler_remove(self.draw_handle_2D, "WINDOW")

        if self.draw_handle_3D:
            self.draw_handle_3D = bpy.types.SpaceView3D.draw_handler_remove(self.draw_handle_3D, "WINDOW")

    # 2D SHADER
    def safe_draw_2D(self, context):
        method_handler(self.draw_shader_2D,
            arguments = (context,),
            identifier = 'Modal Shader 2D',
            exit_method = self.remove_shaders)


    def draw_shader_2D(self, context):
        '''Draw shader handle.'''

        self.flow.draw_2D()

        if self.tool == Tool.SELECT:
            self.select.draw_2d(context, self.data, self)
        if self.tool == Tool.MERGE:
            self.merge.draw_2d(context, self.data, self)
        if self.tool == Tool.KNIFE:
            self.knife.draw_2d(context, self.data, self)

    # 3D SHADER
    def safe_draw_3D(self, context):
        method_handler(self.draw_shader_3D,
            arguments = (context,),
            identifier = 'Modal Shader 3D',
            exit_method = self.remove_shaders)


    def draw_shader_3D(self, context):
        '''Draw shader handle.'''

        if self.tool == Tool.SPIN:
            self.spin.draw_3d(context, self.data, self)
        elif self.tool == Tool.MERGE:
            self.merge.draw_3d(context, self.data, self)
        elif self.tool == Tool.DISSOLVE:
            self.dissolve.draw_3d(context, self.data, self)
        elif self.tool == Tool.JOIN:
            self.join.draw_3d(context, self.data, self)
        elif self.tool == Tool.KNIFE:
            self.knife.draw_3d(context, self.data, self)

# mimic Flow object. it's abit less of a headache than if it out
class FlowDummy:
    is_open = False
    def setup_flow_data(self, _): pass
    def shut_down(self): pass
    def draw_2D(self): pass
    def run_updates(self, context, event, enable_tab_open=True):
        instance = HOPS_OT_FastMeshEditor.instance
        if not instance: return
        if not event.value == 'PRESS': return
        if event.type == 'TAB' and enable_tab_open:
            bpy.context.window_manager.popover(popup_draw)

        elif event.type == 'SPACE' and (event.shift or event.alt):
            bpy.context.window_manager.popover(popup_draw)


# draw popover
def popup_draw(self, context):
    layout = self.layout

    data = HOPS_OT_FastMeshEditor.instance
    if not data: return {'CANCELLED'}

    layout.label(text= 'Selector')
    vals = (item[0] for item in tool_type_items)

    for val in vals:
        row = layout.row()
        row.scale_y = 2
        row.prop_enum(data, 'tool_type', val)
