import bpy
import enum
from ... utility import addon, method_handler

from os import walk, path
import traceback
import random

from ... ui_framework.master import Master
from ... ui_framework.utils.mods_list import get_mods_list
from ... utility.base_modal_controls import Base_Modal_Controls

# Cursor Warp imports
from ... utils.toggle_view3d_panels import collapse_3D_view_panels
from ... utils.modal_frame_drawing import draw_modal_frame
from ... utils.cursor_warp import mouse_warp

DESC = """Scroll through fonts in a Font folder"""

supported_fonts = {'.ttf', '.otf', '.woff', '.woff2'}

class HOPS_OT_FontScroll(bpy.types.Operator):
    bl_idname = "hops.font_scroll"
    bl_label = "Font Scroll"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = DESC

    @classmethod
    def poll(cls, context):
        return context.active_object.type == 'FONT'

    def invoke (self, context, event):
        self.font_folder_path: str = addon.preference().property.font_folder

        if not path.exists(self.font_folder_path):
            self.report({'INFO'}, 'Font directory does not exist or its path is invalid')
            return {'CANCELLED'}

        self.active_font_index = 0
        self.font_index_max = 0
        self.active_loaded_font_name: str = ''
        self.fonts_dir: list[tuple[str, str]] = [] # fontname dirpath
        self.selected_objects = [o for o in context.selected_objects if o.type == 'FONT']
        self.initial_fonts = {f.filepath : f.name for f in bpy.data.fonts}


        self.back = [o.data.font.name for o in self.selected_objects]

        for root, dirs, filenames in walk(self.font_folder_path):
            names = [s for s in filenames if path.splitext(s)[1] in supported_fonts]
            if names:
                self.font_index_max += len(names) - 1

                for name in names:
                    self.fonts_dir.append((name, root))

        if not self.fonts_dir:
            self.report({'INFO'}, 'Font directory is empty or has no supported fonts')
            return {'CANCELLED'}

        # Base Systems
        self.master = Master(context)
        self.master.only_use_fast_ui = True
        self.base_controls = Base_Modal_Controls(context, event, popover_keys=['TAB', 'SPACE'])
        self.original_tool_shelf, self.original_n_panel = collapse_3D_view_panels()
        self.draw_handle = bpy.types.SpaceView3D.draw_handler_add(self.safe_draw_shader, (context,), 'WINDOW', 'POST_PIXEL')

        self.__class__.operator = self
        context.window_manager.modal_handler_add(self)

        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        try:
            return self._modal(context, event)
        except Exception as e:
            traceback.print_exc()
            self.cancel_exit()
            self.report({'ERROR'}, f'{e}')

            return {'CANCELLED'}

    def _modal(self, context, event):

        # Base Systems
        self.master.receive_event(event=event)
        self.base_controls.update(context, event)
        mouse_warp(context, event)

        if self.base_controls.pass_through:
            return {'PASS_THROUGH'}

        elif self.base_controls.scroll:
            if not self.active_loaded_font_name:
                self.active_font_index = 0
            else:
                self.scroll(self.base_controls.scroll)

            font = self.load_active_font()
            if not font:
                fontpath = self.active_fontpath()
                self.report({'ERROR'}, rf'{fontpath} is not a supportted font. Remove the file and try again.')
                self.cancel_exit()

                return {'CANCELLED'}


            # unloading active can invalidate font
            name = font.name
            if self.active_loaded_font_name != name:
                for o in self.selected_objects:
                    o.data.font = font

                self.unload_active_font()
                self.active_loaded_font_name = name

        elif event.type == 'R' and event.value == 'PRESS':
            new_id = random.randint(0, self.font_index_max)

            self.set_font_index(new_id)

            font = self.load_active_font()
            if not font:
                fontpath = self.active_fontpath()
                self.report({'ERROR'}, rf'{fontpath} is not a supportted font. Remove the file and try again.')
                self.cancel_exit()

                return {'CANCELLED'}


            # unloading active can invalidate font
            name = font.name
            if self.active_loaded_font_name != name:
                for o in self.selected_objects:
                    o.data.font = font

                self.unload_active_font()
                self.active_loaded_font_name = name

        elif event.type == 'S' and event.value == 'RELEASE':
            f_dit = self.fonts_dir[self.active_font_index]

            random.shuffle(self.fonts_dir)

            self.active_font_index = self.fonts_dir.index(f_dit)

        elif self.base_controls.confirm:
            self.kill_ui()
            return {'FINISHED'}

        elif self.base_controls.cancel:
            self.cancel_exit()

            return {'CANCELLED'}

        self.draw_ui(context)
        context.area.tag_redraw()

        return {'RUNNING_MODAL'}

    def scroll(self, direction:int) -> str:
        '''Upadte tracked directory and folder indices'''
        self.active_font_index = (self.active_font_index + direction) % len(self.fonts_dir)


    def load_active_font(self):
        fpath = self.active_fontpath()
        name =  self.initial_fonts.get(fpath)

        if name: return bpy.data.fonts[name]

        try:
            font = bpy.data.fonts.load(self.active_fontpath(), check_existing=True)
            return font
        except Exception as e:
            print(e)
            return None

    def unload_active_font(self):
        if not self.active_loaded_font_name: return

        font = self.active_font_get()
        if font.filepath not in self.initial_fonts:
            font.user_clear()
            bpy.data.fonts.remove(font)
            self.active_loaded_font_name = ''

    def active_font_get(self):
        return bpy.data.fonts[self.active_loaded_font_name]

    def active_fontpath(self) -> str:
        font_name, dirpath = self.fonts_dir[self.active_font_index]
        return path.join(dirpath, font_name)

    def set_font_index(self, index:int):
        self.active_font_index = index % (self.font_index_max + 1)

    def draw_ui(self, context):

        self.master.setup()

        # -- Fast UI -- #
        if not self.master.should_build_fast_ui(): return

        # Main
        win_list = []
        if addon.preference().ui.Hops_modal_fast_ui_loc_options != 1:
            if self.active_loaded_font_name:
                win_list.append(self.active_loaded_font_name)

        else:
            if self.active_loaded_font_name:
                font_dir = self.fonts_dir[self.active_font_index]
                dir_path = path.relpath(font_dir[1], self.font_folder_path)

                win_list.append(dir_path)
                win_list.append(self.active_loaded_font_name)
                win_list.append(f'{self.active_font_index} / {self.font_index_max}')

        # Help
        help_items = {"GLOBAL" : [], "STANDARD" : []}

        help_items["GLOBAL"] = [
            ("M", "Toggle mods list"),
            ("H", "Toggle help"),
            ("~", "Toggle UI Display Type"),
            ("O", "Toggle viewport rendering")]

        help_append = help_items["STANDARD"].append


        help_append(["LMB", "Apply"])
        help_append(["RMB", "Cancel"])
        help_append(["Scroll", "Cycle Fonts"])
        help_append(["R", "Random Font"])
        help_append(["S", "Shuffle Font Order"])

        #copy list because ui mutates it in redacted manner
        active = self.fonts_dir[self.active_font_index][0]
        self.master.receive_fast_ui(win_list=win_list, help_list=help_items, image="Tthick", mods_list=[[fd[0], ''] for fd in self.fonts_dir], active_mod_name=active)
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

    def kill_ui(self):
        collapse_3D_view_panels(self.original_tool_shelf, self.original_n_panel)
        self.remove_shader()
        self.master.run_fade()

    def cancel_exit(self):
        self.kill_ui()

        for name, object in zip(self.back, self.selected_objects):
            object.data.font = bpy.data.fonts[name]

        self.unload_active_font()
