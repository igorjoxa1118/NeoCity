import bpy, webbrowser
from bpy_extras.image_utils import load_image
from ... utility import addon
from ...ui_framework.master import Master, Modal_Communications
from .video_thumbs import image_folder


def load_image_file(filename=""):
    '''Return the loaded image.'''

    directory = image_folder()
    return load_image(filename + ".png", dirname=directory)


class Video_Controller:
    def __init__(self, context):
        self.videos = []
        self.exit_modal = False

        file_link = {
            #"bbro2"      :("https://www.blenderbros.com/scifi-terminal-design-mini-course", ""),
            "bBros1"     :("https://gumroad.com/a/739308659", ""),
            "stellar1"   :("https://stellarworks.gumroad.com/l/smg45c", " "),
            "202_1"      :("https://20two.gumroad.com/l/202_SYMBOLS_VOL_001", ""),
            "carol1"     :("https://carolsung.gumroad.com/l/WRmkQ", ""),
            "kitops_3"   : ("https://www.youtube.com/watch?v=nS1TQBiRvwg", "KitOps Release Log"),
            "rach3l"     :("https://gumroad.com/a/236483699", ""),
            "roughness_maps" :("https://gumroad.com/l/mAPCZ/hardops", ""),
            "hopscut"    : ("https://hopscutter.com/", " "),
            #"ko_synth1"  : ("https://blendermarket.com/products/kit-ops-synth", " "),
            "987Log"     : ("https://masterxeon1001.com/2021/01/10/hard-ops-987-francium-release/", "987 Francium Release Log"),
            "cblr"       : ("https://gumroad.com/l/cblrtr/operative", "Cablerator"),
            "pokeball"   : ("https://www.youtube.com/watch?v=VJ64_8pEBF0&feature=emb_title", "R8CH3L"),
            "hops_one"   : ("https://youtu.be/9q54utRuka8", "HandHeld Demo"),
            "hops_two"   : ("https://gumroad.com/l/boxbot", "Rachel's Boxbot"),
            "hops_three" : ("https://gumroad.com/l/GnHrV", "BlenderBros HOPS"),
            "stellar"    : ("https://www.youtube.com/channel/UCK4RSljZQXfpwBrAUxwwxjw", " "),
            "hops_five"  : ("https://www.youtube.com/playlist?list=PLjqpj14voWsUwjkOaj6EsU9OZxs7qieR1", "Boxcutter 717.X Playlist"),
            "hops_six"   : ("https://www.youtube.com/playlist?list=PLjqpj14voWsXlLHjT8jMnn5uKLfXKFki8", "HOPS Extended Playlist"),
            "hops_seven" : ("https://www.youtube.com/playlist?list=PL0RqAjByAphEUuI2JDxIjjCQtfTRQlRh0", "H9 Content"),
            "kitops_bevel" : ("https://gumroad.com/l/kitopsbevel", "KitOps Bevel"),
            "kitops_2"   : ("https://www.youtube.com/playlist?list=PL0RqAjByAphGGBltaIL_yFbar9fR4YV0y", "KitOps 2 Playlist"),
            "HSE"        : ("https://www.youtube.com/watch?fbclid=IwAR2dhoucqRVfcUM2KVw3HlL3FEaW8ExslgVJSZR6W93pqwK0Fs2P1FYhBIA&v=w7GbBaFFgPY&feature=youtu.be", "Hard Surface Essentials"),
            "987YT"     : ("https://www.youtube.com/playlist?list=PLjqpj14voWsXjD3J-J-s6iMcE0EhmdNmk", "987 Francium Video Playlist"),
            "link_keyboard": ("https://gumroad.com/l/KeyboardRenderKit/", "Keyboard Render Kit"),
            "batch_ops"  : ("https://gumroad.com/l/batchops", " ")
        }

        for item in file_link.items():
            file_name, link, desc = item[0], item[1][0], item[1][1]
            image = load_image_file(file_name)
            if image != None:
                self.videos.append((image, link, desc))

        self.master = Master(context=context, custom_preset="Video_Page", show_fast_ui=False)


    def update(self, context, event):
        self.master.receive_event(event=event)
        self.draw_window(context, event)


    def draw_window(self, context, event):
        self.master.setup()
        prefs = addon.preference()
        window_name = "Videos"
        main_window = {}

        for image, link, desc in self.videos:
            main_window[image] = (self.video_linker, link, desc)

        self.master.receive_main(win_dict=main_window, window_name=window_name)
        self.master.finished()

    # --- Utils --- #

    def shut_down(self):
        self.master.run_fade()
        self.remove_images()


    def video_linker(self, link=""):
        self.exit_modal = True
        webbrowser.open(link)


    def remove_images(self):
        for image, link, desc in self.videos:
            try:
                bpy.data.images.remove(image)
            except:
                pass


class HOPS_OT_Videos_Window(bpy.types.Operator):

    """Link Ops"""
    bl_idname = "hops.video_window"
    bl_label = "Link Ops"
    bl_description = """Videos Window \n CTRL - Load Pizza Ops"""


    def invoke(self, context, event):

        # Go to pizza ops
        if event.ctrl:
            bpy.ops.hops.pizza_ops_window('INVOKE_DEFAULT')
            return {'FINISHED'}
        
        # Asset loaded
        self.video = Video_Controller(context)

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


    def modal(self, context, event):

        self.video.update(context, event)

        # Navigation
        if (event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'} and event.ctrl != True):
            if not self.video.master.is_mouse_over_ui():
                return {'PASS_THROUGH'}

        # Confirm
        if event.type == 'LEFTMOUSE':
            if not self.video.master.is_mouse_over_ui():
                self.video.shut_down()
                context.area.tag_redraw()
                return {'FINISHED'}

        # Cancel
        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            if not self.video.master.is_mouse_over_ui():
                self.video.shut_down()
                context.area.tag_redraw()
                return {'CANCELLED'}

        # Exit after load
        if self.video.exit_modal:
            self.video.shut_down()
            context.area.tag_redraw()
            return {'FINISHED'}

        direction = 1 if event.type in ['UP_ARROW', 'LEFT_ARROW'] and event.value == 'PRESS' else None
        direction = -1 if event.type in ['DOWN_ARROW', 'RIGHT_ARROW'] and event.value == 'PRESS' else direction
        self.arrows_next(direction)

        context.area.tag_redraw()
        return {'RUNNING_MODAL'}


    def arrows_next(self, direction=0):
        if not direction: return
        if self.video.master.unique_id not in Modal_Communications.coms: return

        db = Modal_Communications.coms[self.video.master.unique_id].db_ref
        window = db.windows['Video_Page']
        panel = window.panels[-1]
        widget = panel.widget

        widget.scroll_bar.bottom_offset += (panel.panel_height / len(self.video.videos)) * direction
        widget.scroll_bar.clamp_offset()
