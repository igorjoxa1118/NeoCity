import bpy, webbrowser
from mathutils import Vector
from . utils import add_list_items, toggle_help, toggle_mods
from .. graphics.load import load_image_file
from ... utility import addon

class Preset_Videos():

    def __init__(self, create):

        self.create = create
        self.db = self.create.db
        self.images = []
        self.main_window = None
        self.widget = None
        self.widget_layout = None

        self.setup()


    def setup(self):

        # Create windows
        self.main_window = self.create.window(window_key="Video_Page")
        self.main_window_layout()

    ########################
    #   Create Skeletons
    ########################

    def main_window_layout(self):
        '''Create the main window skeleton.'''

        # Panel 1
        self.create.panel(window=self.main_window, x_split_percent=100, y_split_percent=100)

        # # Header
        # self.create.window_header_layout(window=self.main_window, header_height_percent=20, min_max_height=(20, 30))

        # header_layout = self.main_window.header_layout
        # self.create.row(layout=header_layout, height_percent=100)

        # self.create.column(layout=header_layout, width_percent=100)
        # self.create.cell(layout=header_layout, hover_highlight=True)
        # self.create.element_text(layout=header_layout, text="Videos", target_size=12)
        # self.create.element_border(layout=header_layout, line_width=1)

        # Widget
        split_count = addon.preference().ui.Hops_modal_pizza_ops_display_count
        self.create.widget_scroll(panel=self.main_window.panels[-1], win_key="Video_Page", collapsable=False, split_count_override=True, split_count=split_count, show_bar=False)
        self.widget = self.main_window.panels[-1].widget
        self.widget.split_count = split_count

        self.create.widget_body_layout(widget=self.widget)
        self.widget_layout = self.widget.layout

    ########################
    #   Populate Skeletons
    ########################

    def build_main(self, win_dict, window_name, win_form=None):

        self.widget.split_count = 1
        row_percent = 100 / len(win_dict) if len(win_dict) > 0 else 100

        for key, val in win_dict.items():

            self.create.row(layout=self.widget_layout, height_percent=row_percent)
            self.create.column(layout=self.widget_layout, width_percent=100)
            self.create.cell(layout=self.widget_layout, hover_highlight=True)
            self.create.element_background(layout=self.widget_layout, primary=False, bevel=True)
            self.create.element_border(layout=self.widget_layout, line_width=1)
            self.create.element_image(layout=self.widget_layout, image=key, scale=1, max_ratio_size=True)
            self.create.element_text(layout=self.widget_layout, target_size=16, text=val[2], color_select=2, bottom_align=True, y_offset=-.2)
            self.create.event_call_back(layout=self.widget_layout, func=val[0], positive_args=(val[1], ))


    def destroy(self):
        if self.images != []:
            for image in self.images:
                if image != None:
                    try:
                        bpy.data.images.remove(image)
                    except:
                        pass