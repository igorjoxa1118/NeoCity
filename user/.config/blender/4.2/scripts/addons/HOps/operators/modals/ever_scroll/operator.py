import bpy, time
from .... utility import addon
from .... ui_framework.master import Master
from .... ui_framework import form_ui as form
from .... ui_framework.utils.mods_list import get_mods_list
from .... utility.base_modal_controls import Base_Modal_Controls, confirm_events, increment_maps, decrement_maps
from .... utils.toggle_view3d_panels import collapse_3D_view_panels
from .... utility import method_handler
from ... meshtools.applymod import apply_mod
from .... utils.blender_ui import get_dpi_factor
from .... ui.hops_helper.mods_data import DATA_PT_modifiers

from . import States, Auto_Scroll, update_local_view, mods_exit_options, turn_on_coll, get_mod_object
from . mod_tracker import Mod_Tracker
from . bool_tracker import Bool_Tracker
from . child_tracker import Child_Tracker
from . coll_tracker import Coll_Tracker
from . popups import popup_generator

def max_rows():
    return addon.preference().ui.Hops_modal_mod_count_fast_ui


DESC = """Ever Scroll V2\n
LMB - Booleans
LMB + SHIFT - Modifiers
LMB + CTRL - Child Objects
LMB + ALT - Smart Apply
"""

def state_update(self, context):
    op = HOPS_OT_Ever_Scroll_V2.operator
    if not op: return
    if op.popup_active:
        op.set_state(self.b_state, context)

class HOPS_OT_Ever_Scroll_V2(bpy.types.Operator):
    bl_idname = "hops.ever_scroll_v2"
    bl_label = "Ever Scroll V2"
    bl_description = DESC
    bl_options = {"REGISTER", "UNDO", "BLOCKING"}

    entry_state: bpy.props.EnumProperty(
        name="State",
        items=(
            ("NONE",  "NONE",  "NONE"),
            ("BOOL",  "BOOL",  "BOOL"),
            ("MOD",   "MOD",   "MOD"),
            ("CHILD", "CHILD", "CHILD"),
            ("COLL",  "COLL",  "COLL")),
        default="NONE")

    b_state: bpy.props.EnumProperty(
    name="State",
    items=(
        # ("NONE",  "NONE",  "NONE"),
        ("Modifiers",   "MODIFIERS",   "MOD"),
        ("Booleans",  "BOOLEANS",  "BOOL"),
        ("Children", "CHILDREN", "CHILD"),
        # ("COLL",  "COLL",  "COLL")
        ),
        update=state_update,
    default="Modifiers")

    dot_open: bpy.props.BoolProperty(default=False)

    operator = None
    popup_active = False

    def invoke(self, context, event):

        def check_type(obj):
            if type(obj) == bpy.types.Object:
                if type(obj.data) == bpy.types.Mesh:
                    return True
            return False

        self.obj = context.active_object if check_type(context.active_object) else None
        if self.obj == None:
            for obj in context.selected_objects:
                if check_type(obj):
                    self.obj = obj
                    break

        if self.obj == None:
            bpy.ops.hops.display_notification(info="Select an Object")
            return {'CANCELLED'}

        # Smart apply option
        if event.alt:
            if check_type(self.obj):
                apply_mod(self, self.obj, clear_last=False)
                bpy.ops.hops.display_notification(info='Smart Apply')
                bpy.ops.hops.draw_wire_mesh_launcher('INVOKE_DEFAULT', target='SELECTED')
            self.report({'INFO'}, F'Smart Applied')
            return {'FINISHED'}

        self.__class__.operator = self

        # States
        self.state = States.BOOL

        # Entry
        if self.entry_state == 'NONE':
            # Modifiers
            if event.shift:
                self.state = States.MOD
            # Children
            elif event.ctrl:
                self.state = States.CHILD

        elif self.entry_state == 'BOOL':
            self.state = States.BOOL
        elif self.entry_state == 'MOD':
            self.state = States.MOD
        elif self.entry_state == 'CHILD':
            self.state = States.CHILD
        elif self.entry_state == 'COLL':
            self.state = States.COLL

        self.display_state_notification()

        # Trackers
        self.mod_tracker = Mod_Tracker()
        self.bool_tracker = Bool_Tracker()
        self.child_tracker = Child_Tracker()
        self.coll_tracker = Coll_Tracker()
        self.update_tracker_data(context)

        # Auto Scroll
        self.auto_scroll = Auto_Scroll(context)

        # Prefs
        if addon.preference().property.ever_scroll_dot_open == 'DOT':
            self.dot_open = True

        self.popup_style = addon.preference().property.in_tool_popup_style

        # Hops Dots
        self.hops_dots_running = False
        self.hops_dots_op_used = False

        # Form
        self.late_update = False
        self.form_exit = False
        self.form_exit_option = ''
        self.auto_scroll_form_label = None
        self.form = None
        self.setup_form(context, event)

        # Systems
        self.master = Master(context)
        self.master.only_use_fast_ui = True
        self.draw_handle_2D = bpy.types.SpaceView3D.draw_handler_add(self.safe_draw_2D, (context,), 'WINDOW', 'POST_PIXEL') if self.popup_style == 'DEFAULT' else None
        self.original_tool_shelf, self.original_n_panel = collapse_3D_view_panels()
        self.base_controls = Base_Modal_Controls(context, event)

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


    def modal(self, context, event):

        # Form late update
        if self.late_update:
            self.late_update = False
            self.alter_form_layout(context)

        # --- Base Systems --- #
        self.master.receive_event(event=event)
        self.base_controls.update(context, event)
        self.auto_scroll_update(context, event)

        form_active = False
        if self.popup_style == 'DEFAULT':
            self.form.update(context, event, return_on_timer=not self.auto_scroll.active)
            form_active = self.form.active()

        # --- Hops Dots --- #
        ret = self.hardflow(context, event)
        if ret: return ret

        # --- Base Controls --- #

        if self.popup_active:
            self.draw_FAS(context)
            context.area.tag_redraw()

            return {'RUNNING_MODAL'}

        if self.base_controls.pass_through:
            if not form_active:
                return {'PASS_THROUGH'}

        if self.base_controls.cancel:
            if not form_active:
                return self.cancel_exit(context)

        elif self.base_controls.confirm:
            if not form_active:
                if not (event.type == 'SPACE' and event.value == 'PRESS' and event.shift):
                    return self.confirm_exit(context, event)

        if self.form_exit:
            return self.exit_action(context, event)

        if event.type == 'TAB' and event.value == 'PRESS':

            if self.popup_style == 'BLENDER':
                if event.shift:
                    self.toggle_state(context)
                else:
                    bpy.ops.hops.ever_scroll_v2_popup()

            else:
                if event.shift:
                    self.toggle_state(context)
                elif self.form.is_dot_open():
                    self.form.close_dot()
                else:
                    self.form.open_dot()

        # --- Actions --- #
        if not form_active and not self.auto_scroll.active:
            self.actions(context, event)

        self.draw_FAS(context)
        context.area.tag_redraw()
        return {'RUNNING_MODAL'}

    # --- ACTIONS --- #

    def actions(self, context, event):

        scroll = self.base_controls.scroll

        # Scrolling
        if scroll and not event.shift and not event.ctrl:
            self.scroll_trackers(context, scroll)

        # Tracker Keys
        if self.state == States.MOD:
            self.mod_tracker.event_update(self, context, event, self.obj)
        elif self.state == States.CHILD:
            self.child_tracker.event_update(self, context, event, self.obj)
        elif self.state == States.BOOL:
            self.bool_tracker.event_update(self, context, event, self.obj)
        elif self.state == States.COLL:
            self.coll_tracker.event_update(self, context, event)


    def hardflow(self, context, event):
        if self.hops_dots_running:
            if context.window_manager.hardflow.running:
                self.draw_FAS(context)
                context.area.tag_redraw()
                return {'RUNNING_MODAL'}
            else:
                self.hops_dots_running = False
                self.obj.select_set(True)
                context.view_layer.objects.active = self.obj
                self.draw_FAS(context)
                context.area.tag_redraw()
                return {'RUNNING_MODAL'}

        if not self.form.active() and self.state == States.BOOL:
            if event.ctrl and not event.shift:
                self.hops_dots_running = True
                self.hops_dots_op_used = True
                bpy.ops.hardflow_om.display('INVOKE_DEFAULT', use_operations=False)
                self.draw_FAS(context)
                context.area.tag_redraw()
                return {'RUNNING_MODAL'}

        return False

    # --- INTERFACE --- #

    def draw_FAS(self, context):
        self.master.setup()
        if not self.master.should_build_fast_ui(): return

        # Main
        win_list = []

        tracker_data = []
        if self.state == States.MOD:
            tracker_data = self.mod_tracker.FAS_data()
        elif self.state == States.BOOL:
            tracker_data = self.bool_tracker.FAS_data()
        elif self.state == States.CHILD:
            tracker_data = self.child_tracker.FAS_data()
        elif self.state == States.COLL:
            tracker_data = []

        if tracker_data:
            for entry in tracker_data:
                win_list.append(entry)

        # Help
        help_items = {"GLOBAL" : [], "STANDARD" : []}

        help_items["GLOBAL"] = [
            ("M", "Toggle mods list"),
            ("H", "Toggle help"),
            ("~", "Toggle UI Display Type"),
            ("O", "Toggle viewport rendering")]

        help_items["STANDARD"] = [
            ("TAB",       "Dot UI"),
            ("Shift TAB", "Change Mode"),
            ("Ctrl S",    "Toggle Auto Scroll")]

        h_append = help_items["STANDARD"].append

        if self.auto_scroll.active:
            h_append(("Scroll", "Control Auto Scroll Speed"))

        if self.state == States.MOD:
            help_items["STANDARD"].extend(self.mod_tracker.help)
        elif self.state == States.BOOL:
            help_items["STANDARD"].extend(self.bool_tracker.help)
        elif self.state == States.CHILD:
            help_items["STANDARD"].extend(self.child_tracker.help)
        elif self.state == States.COLL:
            tracker_data = []

        help_items["STANDARD"].reverse()

        # Mods
        active_mod = ""
        mods_list = []

        if not self.form.is_dot_open():
            if self.state == States.MOD:
                active_mod = self.mod_tracker.current_mod.name if self.mod_tracker.current_mod else ""
                mods_list = get_mods_list(mods=self.obj.modifiers)
            elif self.state == States.BOOL:
                # Recursive Mode
                if self.bool_tracker.recursive_active:
                    # Since the mod names can be the same in recursive mode the active mod highlight doesnt know which one to use
                    # This area will alter the mod names by adding (1) mod name, (2) mod name... to the front of the mod name

                    mods = []
                    group = self.bool_tracker.recursive.active_group()
                    if group:
                        active_mod = group.active_bool_data().real_mod()
                        index = None

                        for i, bool_data in enumerate(group.bool_datas):
                            mod = bool_data.real_mod()
                            if mod:
                                mods.append(mod)
                                if mod == active_mod:
                                    index = i

                        mods_list = get_mods_list(mods=mods)

                        names = []
                        for mod_item in mods_list:
                            if mod_item[0] in names:
                                names.append(mod_item[0])
                                name = f'({names.count(mod_item[0]) - 1}) {mod_item[0]}'
                                mod_item[0] = name
                            else:
                                names.append(mod_item[0])

                        if index:
                            active_mod = mods_list[index][0]
                        else:
                            active_mod = group.active_mod()
                        mods_list.reverse()
                else:
                    active_mod = self.bool_tracker.current_mod.name if self.bool_tracker.current_mod else ""
                    mods_list = get_mods_list(mods=self.obj.modifiers)
            elif self.state == States.CHILD:
                active_mod = self.child_tracker.current_obj.name if self.child_tracker.current_obj else ""
                mods_list = [[c.name, c.type] for c in self.child_tracker.children if c]
            elif self.state == States.COLL:
                active_mod = ""
                mods_list = []

        self.master.receive_fast_ui(win_list=win_list, help_list=help_items, image="Booleans", mods_list=mods_list, active_mod_name=active_mod)
        self.master.finished()


    def setup_form(self, context, event):
        # MAX WIDTH : 220px

        self.form = form.Form(context, event, dot_open=self.dot_open)

        # Load Image Group
        form.setup_image_group(img_names=['play', 'pause', 'eyecon_open', 'eyecon_closed'])

        def spacer(height=10):
            row = self.form.row()
            row.add_element(form.Spacer(height=height))
            self.form.row_insert(row)

        row = self.form.row()
        modes = ["Modifiers", "Booleans", "Children"] # "Collections"
        row.add_element(form.Dropdown(width=80, options=modes, callback=self.set_state, update_hook=self.state_hook, additional_args=(context,)))
        row.add_element(form.Spacer(width=30))
        self.auto_scroll_form_label = form.Label(text="", width=60)
        row.add_element(self.auto_scroll_form_label)

        self.play_button = form.Button(glob_img_key='play', width=20, tips=["Auto Scroll"], callback=self.toggle_auto_scroll, pos_args=(context,))

        row.add_element(self.play_button)
        row.add_element(form.Spacer(width=10))

        self.exit_button = form.Button(text="✓", shift_text="D", ctrl_text="A", alt_text="X", width=20, tips=self.exit_button_tips_updater(),
            callback=self.exit_button_func, pos_args=('',), neg_args=('DUPLICATE',),
            ctrl_callback=self.exit_button_func, ctrl_args=('APPLY',),
            alt_callback=self.exit_button_func, alt_args=('CANCEL',))

        self.set_exit_button_modifier_key_text()

        tips = self.exit_button.tips
        tips.update_func = self.exit_button_tips_updater

        row.add_element(self.exit_button)
        self.form.row_insert(row)

        spacer()

        # --- Mods --- #
        row = self.form.row()
        group = self.mod_group(context)

        self.mod_box = form.Scroll_Box(width=220, height=self.mods_box_height(), scroll_group=group, view_scroll_enabled=True)
        row.add_element(self.mod_box)
        self.form.row_insert(row, label="MODS", active=True if self.state == States.MOD else False)

        # --- Bools --- #
        row = self.form.row()
        row.add_element(form.Button(text="End", tips=["End Recursive Scroll"], callback=self.bool_tracker.stop_recursive, pos_args=(context, self)))
        self.form.row_insert(row, label="BOOL_REC", active=True if self.state == States.BOOL and self.bool_tracker.recursive_active else False)

        row = self.form.row()
        group = self.bool_group(context)

        self.bool_box = form.Scroll_Box(width=220, height=self.bool_box_height(), scroll_group=group, view_scroll_enabled=True)
        row.add_element(self.bool_box)
        self.form.row_insert(row, label="BOOL", active=True if self.state == States.BOOL else False)

        # --- Child --- #
        row = self.form.row()
        group = self.child_group()

        self.child_box = form.Scroll_Box(width=220, height=self.child_box_height(), scroll_group=group, view_scroll_enabled=True)
        row.add_element(self.child_box)
        self.form.row_insert(row, label="CHILD", active=True if self.state == States.CHILD else False)

        self.form.build()

    # --- FORM FUNCS --- #

    def mod_group(self, context):
        group = form.Scroll_Group()
        for index, mod in enumerate(self.mod_tracker.mods):
            row = group.row()

            row.add_element(form.Label(text=str(index + 1), width=25, height=20))

            tip = []
            text = form.shortened_text(mod.name, width=100, font_size=12)
            tip = tip if text == mod.name else [mod.name]
            obj = get_mod_object(mod)
            if obj: tip.append(f"Shift Click : Toggle Reveal {obj.name}")

            msg, pop_up = popup_generator(self, mod, index + 1)
            if pop_up: tip.append(msg)

            if mod.type == 'NODES':
                tip = ["Shift Click : Toggle Objects"]

            row.add_element(form.Button(
                scroll_enabled=False, text=text, tips=tip,
                width=110, height=20, use_padding=False,
                callback=self.mod_tracker.make_selected_active, pos_args=(context, index, False), neg_args=(context, index, True),
                highlight_hook=self.mod_tracker.highlight, highlight_hook_args=(index,),
                popup=pop_up, popup_modifier_key='CTRL'))

            row.add_element(form.Button(
                scroll_enabled=False, text="O", highlight_text="X", tips=["Toggle modifier visibility"],
                width=20, height=20, use_padding=False,
                callback=self.mod_tracker.mod_toggle_view, pos_args=(self.obj, mod.name),
                highlight_hook=self.mod_tracker.mod_show_view_highlight, highlight_hook_args=(self.obj, mod.name)))

            row.add_element(form.Button(
                scroll_enabled=False, text="R", tips=["Toggle modifier render"],
                width=20, height=20, use_padding=False,
                callback=self.mod_tracker.mod_toggle_render, pos_args=(self.obj, mod.name),
                highlight_hook=self.mod_tracker.mod_show_render_highlight, highlight_hook_args=(self.obj, mod.name)))

            row.add_element(form.Button(
                scroll_enabled=False, text="✓", tips=["Click : Apply modifier", "Shift Click : Apply modifiers up to"],
                width=25, height=20, use_padding=False,
                callback=self.mod_tracker.apply_mods_form, pos_args=(context, self, mod.name, False), neg_args=(context, self, mod.name, True)))

            group.row_insert(row)
        return group


    def bool_group(self, context):
        group = form.Scroll_Group()

        # Keep the bools index inline while looping over all mods
        bool_index = 0

        # Recursive Mode
        if self.bool_tracker.recursive_active:
            mods = self.bool_tracker.recursive.active_mods()
            for index, mod_name in enumerate(mods):

                text = form.shortened_text(mod_name, width=115, font_size=12)
                row = group.row()
                row.add_element(form.Label(text=str(index + 1), width=25, height=20))

                row.add_element(form.Button(
                    scroll_enabled=False, text=text, tips=["Toggle object visibility"],
                    width=135, height=20, use_padding=False,
                    callback=self.bool_tracker.recursive.activate_selected, pos_args=(index,),
                    highlight_hook=self.bool_tracker.recursive.active_highlight, highlight_hook_args=(index,)))

                row.add_element(form.Button(
                    scroll_enabled=False, text="O", highlight_text="X", tips=["Toggle modifier visibility"],
                    width=20, height=20, use_padding=False,
                    callback=self.bool_tracker.recursive.bool_toggle, pos_args=(index,),
                    highlight_hook=self.bool_tracker.recursive.bool_show_view_highlight, highlight_hook_args=(index,)))

                row.add_element(form.Button(
                    scroll_enabled=False, tips=["Lock modifier object visibility"],
                    width=20, height=20, use_padding=False,
                    callback=self.bool_tracker.recursive.selection_to_tracked, pos_args=(index,),
                    highlight_hook=self.bool_tracker.recursive.tracked_highlight, highlight_hook_args=(index,),
                    glob_img_key='eyecon_closed', glob_img_key_update_func=self.bool_tracker.recursive.tracked_img_key_update, glob_img_key_update_args=(index,)))

                group.row_insert(row)

            return group

        # Standard Mode
        for index, mod in enumerate(self.bool_tracker.all_mods):
            if mod not in self.bool_tracker.bools:
                text = form.shortened_text(mod.name, width=150, font_size=12)
                row = group.row()
                row.add_element(form.Label(text=str(index + 1), width=25, height=20))
                row.add_element(form.Label(text=str(text), width=175, height=20))
                group.row_insert(row)
                continue

            row = group.row()

            if self.bool_tracker.has_recursive_mods(mod):
                row.add_element(form.Button(
                    scroll_enabled=False, text=str(index + 1), tips=["Start Recursive Scroll"],
                    width=25, height=20, use_padding=False,
                    callback=self.bool_tracker.select_start_recursive, pos_args=(context, self, bool_index)))
            else:
                row.add_element(form.Label(text=str(index + 1), width=25, height=20))

            text = form.shortened_text(mod.name, width=100, font_size=12)

            _, pop_up = popup_generator(self, mod, index + 1, bool_tracker_mode=True)

            button = form.Button(
                scroll_enabled=False, text=text, tips=self.bool_tips_updater(mod.name),
                width=110, height=20, use_padding=False,
                callback=self.bool_tracker.make_selected_active, pos_args=(bool_index, False), neg_args=(bool_index, True),
                highlight_hook=self.bool_tracker.highlight, highlight_hook_args=(bool_index,),
                popup=pop_up, popup_modifier_key='CTRL')

            tips = button.tips
            if tips:
                tips.update_func = self.bool_tips_updater
                tips.update_args = (mod.name,)

            row.add_element(button)

            bool_index += 1

            row.add_element(form.Button(
                scroll_enabled=False, text="O", highlight_text="X", tips=["Toggle modifier visibility"],
                width=20, height=20, use_padding=False,
                callback=self.bool_tracker.bool_toggle, pos_args=(self.obj, mod.name),
                highlight_hook=self.bool_tracker.bool_show_view_highlight, highlight_hook_args=(self.obj, mod.name)))

            row.add_element(form.Button(
                scroll_enabled=False, tips=["Lock modifier object visibility"],
                width=20, height=20, use_padding=False,
                callback=self.bool_tracker.add_selected_to_tracked, pos_args=(self.obj, mod.name),
                highlight_hook=self.bool_tracker.bool_tracked_highlight, highlight_hook_args=(self.obj, mod.name),
                glob_img_key='eyecon_closed', glob_img_key_update_func=self.bool_tracker.bool_tracked_img_key_update, glob_img_key_update_args=(self.obj, mod.name)))

            row.add_element(form.Button(
                scroll_enabled=False, text="✓", tips=["Click : Apply modifier", "Shift Click : Apply modifiers up to"],
                width=25, height=20, use_padding=False,
                callback=self.bool_tracker.apply_mods_form, pos_args=(context, self, mod.name, False), neg_args=(context, self, mod.name, True)))

            group.row_insert(row)
        return group


    def child_group(self):
        group = form.Scroll_Group()
        for index, child in enumerate(self.child_tracker.children):
            row = group.row()

            text = form.shortened_text(child.name, width=100, font_size=12)
            tip = [] if text == child.name else [child.name]

            row.add_element(form.Label(text=str(index + 1), width=25, height=20))

            row.add_element(form.Button(
                scroll_enabled=False, text=text, tips=tip,
                width=130, height=20, use_padding=False,
                callback=self.child_tracker.make_selected_active, pos_args=(index,), neg_args=(index,),
                highlight_hook=self.child_tracker.highlight, highlight_hook_args=(index,)))

            row.add_element(form.Button(
                scroll_enabled=False, text="X", highlight_text="O", tips=["Toggle visibility"],
                width=20, height=20, use_padding=False,
                callback=self.child_tracker.hide_toggle, pos_args=(child,),
                highlight_hook=self.child_tracker.hide_highlight, highlight_hook_args=(child,)))

            row.add_element(form.Button(
                scroll_enabled=False, text="A", highlight_text="R", tips=["Click : Append / Remove from visibility"],
                width=25, height=20, use_padding=False,
                callback=self.child_tracker.add_to_tracked, pos_args=(child,),
                highlight_hook=self.child_tracker.tracked_highlight, highlight_hook_args=(child,)))

            group.row_insert(row)
        return group


    def set_exit_button_modifier_key_text(self):
        if self.state == States.MOD:
            self.exit_button.shift_text = "D"
            self.exit_button.ctrl_text = "A"
        elif self.state == States.BOOL or self.state == States.CHILD:
            self.exit_button.shift_text = ""
            self.exit_button.ctrl_text = ""


    def exit_button_func(self, option=''):
        self.form_exit = True

        # Additional exit options for Mod Mode
        if self.state == States.MOD:
            self.form_exit_option = option
        else:
            if option == 'CANCEL':
                self.form_exit_option = option


    def exit_action(self, context, event):
        self.common_exit(context)
        if self.form_exit_option == 'CANCEL':
            return self.cancel_exit(context)

        if self.state == States.MOD:
            if self.form_exit_option == 'DUPLICATE':
                self.mod_tracker.exit_tracker(context, event, self.obj, force_ctrl=False, force_shift=True)
            elif self.form_exit_option == 'APPLY':
                self.mod_tracker.exit_tracker(context, event, self.obj, force_ctrl=True, force_shift=False)
        elif self.state == States.BOOL:
            self.bool_tracker.exit_tracker(context)
        elif self.state == States.CHILD:
            self.child_tracker.exit_tracker(context)
        elif self.state == States.COLL:
            self.coll_tracker.exit_tracker(context, event)
        return {'FINISHED'}


    def set_state(self, opt, context):

        preset = ''

        if opt == "Modifiers":
            self.state = States.MOD
            preset = 'MODS'
        elif opt == "Booleans":
            self.state = States.BOOL
            preset = 'BOOL'
        elif opt == "Children":
            self.state = States.CHILD
            preset = 'CHILD'
        elif opt == "Collections":
            self.state = States.COLL
            preset = 'COLL'

        self.set_exit_button_modifier_key_text()
        self.update_tracker_data(context)
        self.alter_form_layout(context)


    def state_hook(self):
        if self.state == States.MOD:
            return "Modifiers"
        elif self.state == States.BOOL:
            return "Booleans"
        elif self.state == States.CHILD:
            return "Children"
        elif self.state == States.COLL:
            return "Collections"


    def alter_form_layout(self, context):
        if self.state == States.MOD:
            self.mod_box.scroll_group = self.mod_group(context)
            self.mod_box.height = self.mods_box_height()
            self.form.row_activation(label='MODS', active=True)
            self.form.row_activation(label='BOOL_REC', active=False)
            self.form.row_activation(label='BOOL', active=False)
            self.form.row_activation(label='CHILD', active=False)
        elif self.state == States.BOOL:
            self.bool_box.scroll_group = self.bool_group(context)
            self.bool_box.height = self.bool_box_height()
            self.form.row_activation(label='MODS', active=False)
            self.form.row_activation(label='BOOL_REC', active=self.bool_tracker.recursive_active)
            self.form.row_activation(label='BOOL', active=True)
            self.form.row_activation(label='CHILD', active=False)
        elif self.state == States.CHILD:
            self.child_box.scroll_group = self.child_group()
            self.child_box.height = self.child_box_height()
            self.form.row_activation(label='MODS', active=False)
            self.form.row_activation(label='BOOL_REC', active=False)
            self.form.row_activation(label='BOOL', active=False)
            self.form.row_activation(label='CHILD', active=True)
        self.form.build(preserve_top_left=True)


    def mods_box_height(self):
        height = 20 * max_rows()
        if self.state == States.MOD:
            mod_len = len(self.obj.modifiers)
            if mod_len < max_rows():
                height = 20 * mod_len
        return height


    def bool_box_height(self):
        height = 20 * max_rows()
        if self.state == States.BOOL:

            if self.bool_tracker.recursive_active:
                mod_len = len(self.bool_tracker.recursive.active_mods())
                if mod_len < max_rows():
                    height = 20 * mod_len
                return height

            mod_len = len(self.obj.modifiers)
            if mod_len < max_rows():
                height = 20 * mod_len
        return height


    def child_box_height(self):
        height = 20 * max_rows()
        if self.state == States.CHILD:
            child_len = Child_Tracker.child_count(self.obj)
            if child_len < max_rows():
                height = 20 * child_len
        return height


    def exit_button_tips_updater(self):
        if self.state == States.MOD:
            return [
                "Click : Finalize / Exit",
                "Shift Click : Smart Apply Clone",
                "Ctrl Click : Apply Visible Modifiers",
                "Alt Click : Cancel / Exit"]
        elif self.state == States.BOOL or self.state == States.CHILD:
            return [
                "Click : Finalize / Exit",
                "Alt Click : Cancel / Exit"]


    def bool_tips_updater(self, mod_name=''):
        tip = []

        mod = None
        if mod_name in self.obj.modifiers:
            mod = self.obj.modifiers[mod_name]
        if not mod: return ["No Modifier"]

        try:
            if not hasattr(mod, 'name'): return ["No Modifier"]

            text = form.shortened_text(mod.name, width=100, font_size=12)
            tip = tip if text == mod.name else [mod.name]
            obj = get_mod_object(mod)
            if obj:
                tip.append(f"Click : Reveal : {obj.name}")
                if obj in self.bool_tracker.tracked_bools:
                    tip.append("Shift Click : Remove from additive")
                else:
                    tip.append("Shift Click : Add to additive")
            else:
                tip.append("No Object in Modifier")

        except: pass

        tip.append("Ctrl Click : Popup Menu")

        return tip

    # --- TRACKERS --- #

    def update_tracker_data(self, context):
        # Global
        self.coll_tracker.set_collectons_back()

        # Trackers
        if self.state == States.MOD:
            self.mod_tracker.update_data(context, self.obj)
        elif self.state == States.BOOL:
            self.bool_tracker.update_data(context, self.obj)
        elif self.state == States.CHILD:
            self.child_tracker.update_data(context, self.obj)
        elif self.state == States.COLL:
            self.coll_tracker.update_data(context, self.obj)


    def scroll_trackers(self, context, step=0):
        if self.state == States.MOD:
            self.mod_tracker.cycle_mods(context, step)
        elif self.state == States.CHILD:
            self.child_tracker.cycle_children(context, step)
        elif self.state == States.BOOL:
            self.bool_tracker.cycle_bools(context, step)
        elif self.state == States.COLL:
            self.coll_tracker.cycle_coll(context, step)

    # --- UTILS --- #

    def toggle_state(self, context):
        if self.state == States.BOOL:
            self.state = States.MOD
        elif self.state == States.MOD:
            self.state = States.CHILD
        elif self.state == States.CHILD:
            self.state = States.BOOL

        self.set_exit_button_modifier_key_text()
        self.update_tracker_data(context)
        self.alter_form_layout(context)
        self.display_state_notification()


    def display_state_notification(self):
        if self.state == States.CHILD:
            bpy.ops.hops.display_notification(info="Children")
        elif self.state == States.BOOL:
            bpy.ops.hops.display_notification(info="Booleans")
        elif self.state == States.MOD:
            bpy.ops.hops.display_notification(info="Modifiers")
        elif self.state == States.COLL:
            bpy.ops.hops.display_notification(info="Collections")

    # --- EXIT --- #

    def common_exit(self, context):
        self.form.shut_down(context)
        if self.auto_scroll.timer: context.window_manager.event_timer_remove(self.auto_scroll.timer)
        self.remove_shaders()
        collapse_3D_view_panels(self.original_tool_shelf, self.original_n_panel)
        self.master.run_fade()
        self.entry_state = 'NONE'


    def confirm_exit(self, context, event):
        self.common_exit(context)

        if self.state == States.MOD:
            self.mod_tracker.exit_tracker(context, event, self.obj)
        elif self.state == States.BOOL:
            self.bool_tracker.exit_tracker(context, select_all=self.hops_dots_op_used)
        elif self.state == States.CHILD:
            self.child_tracker.exit_tracker(context)
        elif self.state == States.COLL:
            self.coll_tracker.exit_tracker(context, event)

        self.__class__.operator = None
        return {'FINISHED'}


    def cancel_exit(self, context):
        self.common_exit(context)
        bpy.ops.ed.undo_push()
        bpy.ops.ed.undo()
        self.__class__.operator = None
        return {'CANCELLED'}

    # --- AUTO SCROLL --- #

    def toggle_auto_scroll(self, context):
        self.auto_scroll.active = not self.auto_scroll.active
        self.mod_tracker.looping = True
        self.child_tracker.looping = True

        if self.auto_scroll.active:
            self.auto_scroll.timer = context.window_manager.event_timer_add(0.1, window=context.window)
            self.auto_scroll.activated_time = time.time()
            self.play_button.change_image_group_key('pause')

        else:
            self.play_button.change_image_group_key('play')
            if self.auto_scroll.timer:
                context.window_manager.event_timer_remove(self.auto_scroll.timer)
                self.auto_scroll.timer = None

            if self.form.is_dot_open():
                if self.auto_scroll_form_label:
                    self.auto_scroll_form_label.text = ""


    def auto_scroll_update(self, context, event):

        s_key = event.type == 'S' and event.value == 'PRESS' and event.ctrl and not event.shift
        space_key = event.type == 'SPACE' and event.value == 'PRESS' and event.shift

        if s_key or space_key:
            self.toggle_auto_scroll(context)

        if not self.auto_scroll.active: return

        if self.form.is_dot_open():
            if self.auto_scroll_form_label:
                self.auto_scroll_form_label.text = self.auto_scroll.display_msg()

        self.time = self.auto_scroll.display_msg()

        if self.auto_scroll.sequance_hold:
            if time.time() - self.auto_scroll.sequance_hold_time > 1:
                self.auto_scroll.activated_time = time.time()
                self.auto_scroll.sequance_hold = False
            else: return

        if time.time() - self.auto_scroll.activated_time > addon.preference().property.auto_scroll_time_interval:
            self.auto_scroll.activated_time = time.time()

            # Make both left and right scroll same direction
            step = 1
            if addon.preference().property.modal_handedness == 'RIGHT': step *= -1
            self.scroll_trackers(context, step)

        # Pause looping on sequence restart
        if self.auto_scroll.sequance_hold == False:

            if self.state == States.MOD:
                self.auto_scroll.sequance_hold = self.mod_tracker.auto_scroll_sequance_begin
                self.auto_scroll.sequance_hold_time = time.time()
                self.mod_tracker.auto_scroll_sequance_begin = False

            elif self.state == States.CHILD:
                self.auto_scroll.sequance_hold = self.child_tracker.auto_scroll_sequance_begin
                self.auto_scroll.sequance_hold_time = time.time()
                self.child_tracker.auto_scroll_sequance_begin = False

            elif self.state == States.BOOL:
                self.auto_scroll.sequance_hold = self.bool_tracker.auto_scroll_sequance_begin
                self.auto_scroll.sequance_hold_time = time.time()
                self.bool_tracker.auto_scroll_sequance_begin = False

        # Adjust speed
        if self.form.active(): return

        if event.type in {'WHEELDOWNMOUSE', 'LEFT_BRACKET'} and event.value == 'PRESS':
            self.auto_scroll.activated_time = time.time()
            addon.preference().property.auto_scroll_time_interval -= .125
            if addon.preference().property.auto_scroll_time_interval < .1:
                addon.preference().property.auto_scroll_time_interval = .25

            bpy.ops.hops.display_notification(info=f"Interval time set: {addon.preference().property.auto_scroll_time_interval:.3f}")

        elif event.type in {'WHEELUPMOUSE', 'RIGHT_BRACKET'} and event.value == 'PRESS':
            self.auto_scroll.activated_time = time.time()
            addon.preference().property.auto_scroll_time_interval += .125
            if addon.preference().property.auto_scroll_time_interval > 60:
                addon.preference().property.auto_scroll_time_interval = 60

            bpy.ops.hops.display_notification(info=f"Interval time set: {addon.preference().property.auto_scroll_time_interval:.3f}")

    # --- SHADER --- #

    def remove_shaders(self):
        if self.draw_handle_2D:
            self.draw_handle_2D = bpy.types.SpaceView3D.draw_handler_remove(self.draw_handle_2D, "WINDOW")


    def safe_draw_2D(self, context):
        method_handler(self.draw_shader_2D,
            arguments = (context,),
            identifier = 'EverScroll V2 Shader',
            exit_method = self.remove_shaders)


    def draw_shader_2D(self, context):
        self.form.draw()
        if self.form.is_dot_open(): return
        self.auto_scroll.draw()


class HOPS_OT_Ever_Scroll_V2_Popup(bpy.types.Operator):
    bl_idname = "hops.ever_scroll_v2_popup"
    bl_label = ""
    bl_description = ""

    def __del__(self):
        op = HOPS_OT_Ever_Scroll_V2.operator
        if not op: return
        op.popup_active = False

    def execute(self, context):
        op = HOPS_OT_Ever_Scroll_V2.operator
        if not op: return {'CANCELLED'}

        if op.state == States.MOD:
            op.b_state = "Modifiers"
        elif op.state == States.BOOL:
            op.b_state = "Booleans"
        elif op.state == States.CHILD:
            op.b_state = "Children"

        op.popup_active = True

        return bpy.context.window_manager.invoke_popup(self, width=int(180 * get_dpi_factor(force=False)))

    def draw(self, context):
        layout = self.layout

        op = HOPS_OT_Ever_Scroll_V2.operator
        if not op: return

        if op.form_exit:
            layout.label(text='Finished')
            return

        row = layout.row()
        row.prop(op, "b_state", text='')
        row.operator("hops.ever_scroll_v2_scroll", text='', icon='PAUSE' if op.auto_scroll.active else 'PLAY')

        if op.state == States.CHILD:
            row.operator("hops.ever_scroll_v2_finishobj", text='', icon='CHECKMARK')
        else:
            row.operator("hops.ever_scroll_v2_finish", text='', icon='CHECKMARK')

        def row_layout(row):
            # row = row.split(factor=0.10, align=True)
            # row.alignment = 'LEFT'
            # row.label(text=str(i + 1))
            row = row.row(align=True)
            row.alignment = 'EXPAND'

            return row

        def mod_func(row, mod_name):
            row.separator()
            row.operator_context = 'INVOKE_DEFAULT'
            row.prop(mod, 'show_viewport', text='')
            row.prop(mod, 'show_render', text='')

            props = row.operator('hops.ever_scroll_v2_modedit', text="", icon='PROPERTIES')
            props.name = mod_name

            apply = row.operator("hops.ever_scroll_v2_apply", text="", icon='CHECKMARK')
            apply.mod_name = mod_name



        if op.state == States.MOD:
            for i, mod in enumerate(context.active_object.modifiers):
                row = layout.row(align=True)
                row = row_layout(row)
                row.alert = op.mod_tracker.current_mod == mod
                row.operator_context = 'INVOKE_DEFAULT'
                op_btn = row.operator("hops.ever_scroll_v2_modbtn", text=mod.name)
                op_btn.index = i

                row = row.row(align=True)
                row.alert = False
                mod_func(row, mod.name)

        elif op.state == States.BOOL:
            for i, mod in enumerate(context.active_object.modifiers):
                active = op.bool_tracker.current_mod == mod
                row = layout.row(align=True)
                row = row_layout(row)

                if mod.type == 'BOOLEAN':
                    row.alert = active
                    op_btn = row.operator("hops.ever_scroll_v2_boolbtn", text=mod.name)
                    op_btn.index = i
                    row = row.row(align=True)
                    row.alert = False

                    row.separator()
                    row.operator_context = 'INVOKE_DEFAULT'
                    row.prop(mod, 'show_viewport', text='')
                    obj_vis = row.operator('hops.ever_scroll_v2_boolvisbtn', icon='LOCKED' if op.bool_tracker.bool_tracked_highlight(mod.id_data, mod.name) else 'UNLOCKED')
                    obj_vis.obj_name = mod.id_data.name
                    obj_vis.mod_name = mod.name

                    props = row.operator('hops.ever_scroll_v2_modedit', text="", icon='PROPERTIES')
                    props.name = mod.name

                    apply = row.operator("hops.ever_scroll_v2_apply", text="", icon='CHECKMARK')
                    apply.mod_name = mod.name

                else:
                    row.label(text=mod.name)
                    row.alert = active

        elif op.state == States.CHILD:
            for i, obj in enumerate(op.child_tracker.children):
                row = row_layout(layout)
                row.alert = op.child_tracker.current_obj == obj
                active = row.operator("hops.ever_scroll_v2_objbtn", text=obj.name)
                active.index = i
                row.separator()

                row = row.row(align=True)
                row.alert = False
                vis = row.operator("hops.ever_scroll_v2_objvis", text='', icon="HIDE_ON" if obj.hide_get() else "HIDE_OFF")
                vis.obj_name = obj.name
                visadd = row.operator("hops.ever_scroll_v2_objvisadd", text='', icon='EVENT_R' if op.child_tracker.tracked_highlight(obj) else 'EVENT_A')
                visadd.obj_name = obj.name

class HOPS_OT_Ever_Scroll_V2_Scroll(bpy.types.Operator):
    bl_idname = "hops.ever_scroll_v2_scroll"
    bl_label = "Auto Scroll"
    bl_description = ""

    def execute(self, context):
        op = HOPS_OT_Ever_Scroll_V2.operator
        if not op: return {'CANCELLED'}

        op.toggle_auto_scroll(context)

        return {'FINISHED'}

class HOPS_OT_Ever_Scroll_V2_Apply(bpy.types.Operator):
    bl_idname = "hops.ever_scroll_v2_apply"
    bl_label = "Apply"
    bl_description = "Click : Apply modifier\nShift Click : Apply modifiers up to"

    mod_name: bpy.props.StringProperty()

    def invoke(self, context, event):
        op = HOPS_OT_Ever_Scroll_V2.operator
        if not op: return {'CANCELLED'}

        if event.shift:
            op.mod_tracker.apply_mods_form(context, op, self.mod_name, True)

        else:
            op.mod_tracker.apply_mods_form(context, op, self.mod_name, False)

        return {'FINISHED'}



class HOPS_OT_Ever_Scroll_V2_Finish(bpy.types.Operator):
    bl_idname = "hops.ever_scroll_v2_finish"
    bl_label = "Finish"
    bl_description = """Click : Finalize / Exit
    Shift Click : Smart Apply Clone
    Ctrl Click : Apply Visible Modifiers
    Alt Click : Cancel / Exit"""

    def invoke(self, context, event):
        op = HOPS_OT_Ever_Scroll_V2.operator
        if not op: return {'CANCELLED'}

        val = ''
        if event.shift:
            val ='DUPLICATE'

        elif event.ctrl:
            val = 'CLONE'

        elif event.alt:
            val = 'CANCEL'

        op.exit_button_func(val)

        op.popup_active = False

        return {'FINISHED'}

class HOPS_OT_Ever_Scroll_V2_FinishObj(bpy.types.Operator):
    bl_idname = "hops.ever_scroll_v2_finishobj"
    bl_label = "Finish"
    bl_description = """Click : Finalize / Exit"
    Alt Click : Cancel / Exit"""

    def invoke(self, context, event):
        op = HOPS_OT_Ever_Scroll_V2.operator
        if not op: return {'CANCELLED'}
        val = ''
        if event.alt:
            val = 'CANCEL'

        op.exit_button_func(val)
        op.popup_active = False

        return {'FINISHED'}

class HOPS_OT_Ever_Scroll_V2_ModBtn(bpy.types.Operator):
    bl_idname = "hops.ever_scroll_v2_modbtn"
    bl_label = ""
    bl_description = "Shift+Click: Reveal Mod object if applicable"

    index: bpy.props.IntProperty()

    def invoke (self, context, event):
        op = HOPS_OT_Ever_Scroll_V2.operator
        if not op: return {'CANCELLED'}

        op.mod_tracker.make_selected_active(context, self.index, reveal_object=event.shift)

        return {'FINISHED'}

class HOPS_OT_Ever_Scroll_V2_BoolBtn(bpy.types.Operator):
    bl_idname = "hops.ever_scroll_v2_boolbtn"
    bl_label = ""
    bl_description = "Click: Reveal\nShift + Click: Additive reveal"

    index: bpy.props.IntProperty()

    def invoke (self, context, event):
        op = HOPS_OT_Ever_Scroll_V2.operator
        if not op: return {'CANCELLED'}

        op.bool_tracker.make_selected_active(self.index, event.shift)


        return {'FINISHED'}
class HOPS_OT_Ever_Scroll_V2_BoolVisBtn(bpy.types.Operator):
    bl_idname = "hops.ever_scroll_v2_boolvisbtn"
    bl_label = ""
    bl_description = "Lock modifier object visibility"

    obj_name: bpy.props.StringProperty()
    mod_name: bpy.props.StringProperty()

    def invoke (self, context, event):
        op = HOPS_OT_Ever_Scroll_V2.operator
        if not op: return {'CANCELLED'}

        obj = bpy.data.objects[self.obj_name]
        op.bool_tracker.add_selected_to_tracked(obj, self.mod_name)

        return {'FINISHED'}

class HOPS_OT_Ever_Scroll_V2_ModEdit(bpy.types.Operator):
    bl_idname = "hops.ever_scroll_v2_modedit"
    bl_label = "Modifier Properties"
    bl_description = "Edit Modifier Properties"

    name: bpy.props.StringProperty()

    def draw(self, context):
        obj = context.active_object
        mod = obj.modifiers[self.name]
        getattr(DATA_PT_modifiers, mod.type)(DATA_PT_modifiers, self.layout, obj, mod)


    def execute (self, context):
        op = HOPS_OT_Ever_Scroll_V2.operator
        if not op: return {'CANCELLED'}

        return bpy.context.window_manager.invoke_popup(self, width=int(240 * get_dpi_factor(force=False)))


class HOPS_OT_Ever_Scroll_V2_ObjBtn(bpy.types.Operator):
    bl_idname = "hops.ever_scroll_v2_objbtn"
    bl_label = ""
    bl_description = "Reveal"

    index: bpy.props.IntProperty()

    def execute(self, context):
        op = HOPS_OT_Ever_Scroll_V2.operator
        if not op: return {'CANCELLED'}

        op.child_tracker.make_selected_active(self.index)

        return {'FINISHED'}

class HOPS_OT_Ever_Scroll_V2_ObjVis(bpy.types.Operator):
    bl_idname = "hops.ever_scroll_v2_objvis"
    bl_label = ""
    bl_description = "Toggle Visibility"

    obj_name: bpy.props.StringProperty()

    def invoke(self, context, event):
        op = HOPS_OT_Ever_Scroll_V2.operator
        if not op: return {'CANCELLED'}

        obj = bpy.data.objects[self.obj_name]
        op.child_tracker.hide_toggle(obj)

        return {'FINISHED'}

class HOPS_OT_Ever_Scroll_V2_ObjVisAdd(bpy.types.Operator):
    bl_idname = "hops.ever_scroll_v2_objvisadd"
    bl_label = ""
    bl_description = "Click : Append / Remove from visibility"

    obj_name: bpy.props.StringProperty()

    def invoke(self, context, event):
        op = HOPS_OT_Ever_Scroll_V2.operator
        if not op: return {'CANCELLED'}

        obj = bpy.data.objects[self.obj_name]

        op.child_tracker.add_to_tracked(obj)

        return {'FINISHED'}