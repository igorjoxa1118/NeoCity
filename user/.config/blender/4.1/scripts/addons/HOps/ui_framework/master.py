import bpy, time, sys, traceback
from . graphics.shader import Shader
from . graphics.load import load_image_file
from . database import DB
from . api.create import Create
from . events.event import Event_System
from . presets.preset_a import Preset_A
from . presets.preset_b import Preset_B
from . presets.preset_kit_ops import Preset_Kit_Ops
from . presets.preset_infinity_mods import Preset_Infinity_Mods
from . presets.pizza_ops import Preset_Pizza_Ops
from . presets.preset_brush_ops import Preset_Brush_Ops
from . presets.video_page import Preset_Videos
from . presets.every_scroll_win import Preset_Every_Scroll


class Modal_Communications():

    # Key   = Unique Time Signature
    # Value = All the com data per instance of modal
    coms = {}
    unique_id = None
    unique_offset = 0


class Com_Instance():

    def __init__(self):

        # Coms from operations modal
        self.start_fade = False

        # Destroy
        self.destroy_now = False

        # Coms for ui modal to operations modal
        self.shader_ref = None
        self.db_ref = None
        self.preset_ref = None
        self.event_system_ref = None
        self.create_api_ref = None
        self.scale_ref = None

        # Coms for UI creation
        self.custom_preset = ""       # Create a non standard window
        self.only_use_fast_ui = False # Prevents expanded mode
        self.show_fast_ui = False     # Only show the expanded

        # Functions from ui modal
        self.get_preset = None

        # Overrides
        self.start_mod_hidden = False

        # Fail safes
        self.time_since_fade_start = None

        # If the windows should use warp mode
        self.use_warp_mode = False


class Master():

    def __init__(self, context, custom_preset="", show_fast_ui=True, use_warp_mode=False, start_mod_hidden=False):

        self.context = context

        # Override
        self.only_use_fast_ui = False

        # Create unique id
        Modal_Communications.unique_id = time.time() + Modal_Communications.unique_offset
        Modal_Communications.unique_offset += 1
        if Modal_Communications.unique_offset > 10:
            Modal_Communications.unique_offset = 0

        self.unique_id = Modal_Communications.unique_id

        Modal_Communications.coms[self.unique_id] = Com_Instance()

        # Overrides
        Modal_Communications.coms[self.unique_id].only_use_fast_ui = self.only_use_fast_ui
        Modal_Communications.coms[self.unique_id].show_fast_ui = show_fast_ui
        Modal_Communications.coms[self.unique_id].custom_preset = custom_preset
        Modal_Communications.coms[self.unique_id].start_mod_hidden = start_mod_hidden

        # Warp mode
        Modal_Communications.coms[self.unique_id].use_warp_mode = use_warp_mode

        # Start the UI modal
        self.__launch_modal()


    def __launch_modal(self):
        '''The modal will create: Shader, Database, Preset, Event System, Create Api'''

        bpy.ops.hops.modal_ui_draw('INVOKE_DEFAULT')


    def setup(self):
        '''Clears the layouts on all the windows.'''

        if not self.__key_checker():
            return

        Modal_Communications.coms[self.unique_id].only_use_fast_ui = self.only_use_fast_ui

        if Modal_Communications.coms[self.unique_id].scale_ref != Modal_Communications.coms[self.unique_id].db_ref.prefs.ui.Hops_modal_size:
            Modal_Communications.coms[self.unique_id].scale_ref = Modal_Communications.coms[self.unique_id].db_ref.prefs.ui.Hops_modal_size
            Modal_Communications.coms[self.unique_id].get_preset()

        if Modal_Communications.coms[self.unique_id].only_use_fast_ui == False:
            if Modal_Communications.coms[self.unique_id].db_ref.event.tab_pressed:
                if not Modal_Communications.coms[self.unique_id].db_ref.event.shift_pressed:
                    Modal_Communications.coms[self.unique_id].db_ref.fast_ui.show = False

        Modal_Communications.coms[self.unique_id].db_ref.clear_db()
        Modal_Communications.coms[self.unique_id].create_api_ref.cell_index = 0


    def receive_event(self, event, skip_m_h=False):
        '''Update the event data in the database.'''

        if not self.__key_checker():
            return

        Modal_Communications.coms[self.unique_id].event_system_ref.update_event_data(event=event, context=self.context, skip_m_h=skip_m_h)

    # Fast UI
    def receive_fast_ui(self, win_list=[], help_list=[], image="", mods_list=[], active_mod_name="", mods_label_text="Press M", number_mods=True):
        '''Receive the main window dictionary.\n
           Image is any image file name from the icons folder, without the extension.'''

        if not self.__key_checker():
            return

        if Modal_Communications.coms[self.unique_id].db_ref.fast_ui.show == True:
            Modal_Communications.coms[self.unique_id].db_ref.fast_ui.build_main(
                win_list=win_list,
                help_list=help_list,
                image=image,
                mods_list=mods_list,
                active_mod_name=active_mod_name,
                mods_label_text=mods_label_text,
                number_mods=number_mods)


    def collapse_fast_help(self):
        '''Collapse fast help menu'''

        if not self.__key_checker():
            return

        Modal_Communications.coms[self.unique_id].db_ref.fast_ui.show_help = False


    def should_build_fast_ui(self):
        '''Use this to determine if you should build the fast ui or the main ui.'''

        if not self.__key_checker():
            return

        if Modal_Communications.coms[self.unique_id].only_use_fast_ui == True:
            return True

        if Modal_Communications.coms[self.unique_id].db_ref.fast_ui.show:
            return True

        return False


    def receive_main(self, win_dict={}, window_name="MAIN", win_form=None):
        '''Receive the main window dictionary.'''

        if not self.__key_checker():
            return

        if Modal_Communications.coms[self.unique_id].preset_ref != None:
            Modal_Communications.coms[self.unique_id].preset_ref.build_main(win_dict=win_dict, window_name=window_name, win_form=win_form)


    def receive_help(self, hot_keys_dict={}, quick_ops_dict={}):
        '''Receive the help window dictionary.'''

        if not self.__key_checker():
            return

        if Modal_Communications.coms[self.unique_id].preset_ref != None:
            Modal_Communications.coms[self.unique_id].preset_ref.build_help(hot_keys_dict=hot_keys_dict, quick_ops_dict=quick_ops_dict)


    def receive_mod(self, win_dict={}, active_mod_name="", rename_window="", body_scroll=True):
        '''Receive the mod window dictionary.'''

        if not self.__key_checker():
            return

        if Modal_Communications.coms[self.unique_id].preset_ref != None:
            Modal_Communications.coms[self.unique_id].preset_ref.build_mods(win_dict=win_dict, active_mod_name=active_mod_name, rename_window=rename_window, body_scroll=body_scroll)


    def finished(self):
        '''Run the event layer.'''

        if not self.__key_checker():
            return

        if Modal_Communications.coms[self.unique_id].db_ref.fast_ui.show == False:
            Modal_Communications.coms[self.unique_id].event_system_ref.run()

        Modal_Communications.coms[self.unique_id].time_since_fade_start = time.time()


    def is_mouse_over_ui(self):
        '''For modal exit.'''

        if not self.__key_checker():
            return

        if Modal_Communications.coms[self.unique_id].db_ref.fast_ui.show:
            return False

        elif Modal_Communications.coms[self.unique_id].db_ref.ui_event.active_window_key == "":
            return False

        else:
            return True


    def destroy(self):
        '''Remove the shader and graphics data.'''

        if not self.__key_checker():
            return

        Modal_Communications.coms[self.unique_id].destroy_now = True

    def destroy_immediate (self):
        '''Remove the shader and graphics data immediately.'''

        if not self.__key_checker():
            return

        Modal_Communications.coms[self.unique_id].destroy_now = True
        Modal_Communications.coms[self.unique_id].shader_ref.destroy()
        Modal_Communications.coms[self.unique_id].preset_ref.destroy()


    def run_fade(self):
        '''Called from the operations modal when finished.'''

        if not self.__key_checker():
            return

        Modal_Communications.coms[self.unique_id].start_fade = True
        Modal_Communications.coms[self.unique_id].time_since_fade_start = time.time()


    def __key_checker(self):
        '''Make sure keys are valid.'''

        if self.unique_id in Modal_Communications.coms:
            return True

        if len(Modal_Communications.coms) > 0:
            for com in Modal_Communications.coms.items():
                com[1].destroy_now = True

        return False


class HOPS_MODAL_UI_Draw(bpy.types.Operator):

    bl_idname = "hops.modal_ui_draw"
    bl_label = "Drawing for modals"
    bl_options = {"INTERNAL"}

    def __init__(self):

        self.db = DB()
        self.preset = None
        self.scale = None
        self.unique_id = Modal_Communications.unique_id

        # Warp mode
        self.db.prefs.ui.Hops_warp_mode = Modal_Communications.coms[self.unique_id].use_warp_mode

        # Event
        self.event_sys = Event_System(db=self.db)

        # Graphics
        self.shader = None

        # API
        self.create = Create(db=self.db)

        # Get window preset
        self.get_preset()


    def get_preset(self):

        custom_preset = Modal_Communications.coms[self.unique_id].custom_preset
        self.db.fast_ui.show = Modal_Communications.coms[self.unique_id].show_fast_ui

        # Custom Presets
        if custom_preset != "":
            if custom_preset == "preset_kit_ops":
                self.preset = Preset_Kit_Ops(create=self.create)
                return

            elif custom_preset == "preset_infinity_mods":
                self.preset = Preset_Infinity_Mods(create=self.create)
                return

            elif custom_preset == "pizza_ops":
                self.preset = Preset_Pizza_Ops(create=self.create)
                return

            elif custom_preset == "brush_ops":
                self.preset = Preset_Brush_Ops(create=self.create)
                return

            elif custom_preset == "Video_Page":
                self.preset = Preset_Videos(create=self.create)
                return

            elif custom_preset == "Every_Scroll":
                self.preset = Preset_Every_Scroll(create=self.create)
                return

        # Prefs Presets
        preset = self.db.prefs.ui.Hops_modal_presets

        if preset == "preset_A":
            self.preset = Preset_A(create=self.create)

        elif preset == "preset_B":
            self.preset = Preset_B(create=self.create)


    def invoke(self, context, event):

        self.shader = Shader(context=context, db=self.db)
        self.scale = self.db.prefs.ui.Hops_modal_size
        # self.timer = context.window_manager.event_timer_add(0.025, window=context.window)
        self.timer = None

        self.setup_modal_com()

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


    def setup_modal_com(self):

        Modal_Communications.coms[self.unique_id].shader_ref = self.shader
        Modal_Communications.coms[self.unique_id].db_ref = self.db
        Modal_Communications.coms[self.unique_id].preset_ref = self.preset
        Modal_Communications.coms[self.unique_id].event_system_ref = self.event_sys
        Modal_Communications.coms[self.unique_id].create_api_ref = self.create
        Modal_Communications.coms[self.unique_id].scale_ref = self.scale

        # Functions
        Modal_Communications.coms[self.unique_id].get_preset = self.get_preset

        self.db.fast_ui.start_mod_hidden = Modal_Communications.coms[self.unique_id].start_mod_hidden


    def modal(self, context, event):

        # Redraw
        try:
            if self.timer != None:
                context.area.tag_redraw()
        except:
            self.shader.destroy()
            self.db.fast_ui.destroy()
            self.preset.destroy()
            Modal_Communications.coms.pop(self.unique_id)
            self.remove_timer()
            context.area.tag_redraw()
            return {'FINISHED'}

        # Destroy now
        if Modal_Communications.coms[self.unique_id].destroy_now == True:
            self.shader.destroy()
            self.preset.destroy()
            Modal_Communications.coms.pop(self.unique_id)
            self.remove_timer()
            return {'FINISHED'}

        # Remove if key is not there
        if self.unique_id not in Modal_Communications.coms:
            try:
                self.shader.destroy()
                self.db.fast_ui.destroy()
                self.preset.destroy()
                self.remove_timer()
            except:
                pass
            self.remove_timer()
            context.area.tag_redraw()
            return {'FINISHED'}

        # Start fade
        if Modal_Communications.coms[self.unique_id].start_fade == True:
            if self.timer == None and self.db.prefs.ui.Hops_modal_fade > 0.01:
                self.timer = context.window_manager.event_timer_add(0.025, window=context.window)

            if self.db.prefs.ui.Hops_modal_fade < 0.01:
                self.shader.destroy()
                self.db.fast_ui.destroy()
                self.preset.destroy()
                Modal_Communications.coms.pop(self.unique_id)
                self.remove_timer()
                context.area.tag_redraw()
                return {'FINISHED'}

            self.shader.remove_handle()
            self.preset.destroy()

        # Fade is done
        if self.shader.handle == None:
            Modal_Communications.coms.pop(self.unique_id)
            self.db.fast_ui.destroy()
            self.preset.destroy()
            self.remove_timer()
            context.area.tag_redraw()
            return {'FINISHED'}

        return {'PASS_THROUGH'}


    def remove_timer(self):

        if self.timer != None:
            bpy.context.window_manager.event_timer_remove(self.timer)


class HOPS_MODAL_UI_Purge(bpy.types.Operator):
    """
    Remove straggling UI by refreshing 3d view.

    """
    bl_idname = "hops.modal_ui_purge"
    bl_label = "Purge dead Hops UI"

    def execute(self, context):

        for com in Modal_Communications.coms.values():
            com.start_fade = True


        return {'FINISHED'}
