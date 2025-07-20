import bpy, webbrowser
from mathutils import Vector
from . utils import add_list_items, toggle_help, toggle_mods
from .. graphics.load import load_image_file
from ... utility import addon

class Preset_Brush_Ops():

    def __init__(self, create):

        self.create = create
        self.db = self.create.db
        self.images = []
        self.main_window = None

        self.brush_widget = None
        self.brush_widget_layout = None

        self.op_widget = None
        self.op_widget_layout = None

        self.header_button = None

        self.setup()


    def setup(self):

        # Create windows
        self.main_window = self.create.window(window_key="Brush_Ops")
        self.main_window.can_stack_vertical = False
        self.main_window_layout()

        # Override colors
        prefs = addon.preference()

    ########################
    #   Create Skeletons
    ########################

    def main_window_layout(self):
        '''Create the main window skeleton.'''

        # Panel 1
        self.create.panel(window=self.main_window, x_split_percent=100, y_split_percent=50)
        # self.create.panel(window=self.main_window, x_split_percent=60, y_split_percent=50)

        # Header
        self.create.window_header_layout(window=self.main_window, header_height_percent=20, min_max_height=(20, 30))

        header_layout = self.main_window.header_layout
        self.create.row(layout=header_layout, height_percent=100)

        self.create.column(layout=header_layout, width_percent=100)
        self.create.cell(layout=header_layout, hover_highlight=True)
        self.create.element_text(layout=header_layout, text="Brush List", target_size=12)
        self.create.element_border(layout=header_layout, line_width=1)
        self.header_button = self.create.event_call_back(layout=header_layout, func=None, positive_args=None)

        # Widget
        self.create.widget_scroll(panel=self.main_window.panels[-1], win_key="Brush_Ops", collapsable=False, split_count_override=False)
        self.brush_widget = self.main_window.panels[-1].widget

        self.create.widget_body_layout(widget=self.brush_widget)
        self.brush_widget_layout = self.brush_widget.layout


        # # Panel 2
        # self.create.panel(window=self.main_window, x_split_percent=40, y_split_percent=50)

        # # Header
        # self.create.window_header_layout(window=self.main_window, header_height_percent=20, min_max_height=(20, 30))

        # header_layout = self.main_window.header_layout
        # self.create.row(layout=header_layout, height_percent=100)

        # self.create.column(layout=header_layout, width_percent=100)
        # self.create.cell(layout=header_layout, hover_highlight=True)
        # self.create.element_text(layout=header_layout, text="Brush List", target_size=12)
        # self.create.element_border(layout=header_layout, line_width=1)
        # self.header_button = self.create.event_call_back(layout=header_layout, func=None, positive_args=None)

        # # Widget
        # self.create.widget_scroll(panel=self.main_window.panels[-1], win_key="Brush_Ops", collapsable=False, split_count_override=False)
        # self.op_widget = self.main_window.panels[-1].widget

        # self.create.widget_body_layout(widget=self.op_widget)
        # self.op_widget_layout = self.op_widget.layout

    ########################
    #   Populate Skeletons
    ########################

    def build_main(self, win_dict, window_name, win_form=None):

        # Header
        header = win_dict['header']
        self.header_button.func = header[0]
        self.header_button.positive_args = header[1]

        # Brushes
        brushes = win_dict['brushes']
        height = 100 / len(brushes) if len(brushes) > 0 else 100
        for brush_form in reversed(brushes):
            self.create.row(layout=self.brush_widget_layout, height_percent=height)
            self.create.column(layout=self.brush_widget_layout, width_percent=75)
            self.create.cell(layout=self.brush_widget_layout, hover_highlight=True)
            self.create.element_text(layout=self.brush_widget_layout, target_size=16, text=brush_form.name)
            self.create.event_call_back(layout=self.brush_widget_layout, func=brush_form.call_back, positive_args=brush_form.call_args)

            self.create.column(layout=self.brush_widget_layout, width_percent=25)
            self.create.cell(layout=self.brush_widget_layout, hover_highlight=True)
            self.create.element_background(layout=self.brush_widget_layout, primary=False, bevel=True)
            self.create.element_border(layout=self.brush_widget_layout, line_width=1)
            self.create.element_text(layout=self.brush_widget_layout, target_size=16, text=brush_form.hot_key_display)
            self.create.event_call_back(layout=self.brush_widget_layout, func=brush_form.call_back, positive_args=brush_form.call_args)

        # # Operations
        # ops = win_dict['ops']
        # height = 100 / len(ops) if len(ops) > 0 else 100
        # for op in ops:
        #     self.create.row(layout=self.op_widget_layout, height_percent=height)
        #     self.create.column(layout=self.op_widget_layout, width_percent=100)
        #     self.create.cell(layout=self.op_widget_layout, hover_highlight=True)
        #     self.create.element_text(layout=self.op_widget_layout, target_size=16, text=op[0])
        #     self.create.event_call_back(layout=self.op_widget_layout, func=op[1], positive_args=op[2])
        

    def destroy(self):

        # Unload images
        if self.images != []:
            for image in self.images:
                if image != None:
                    try:
                        bpy.data.images.remove(image)
                    except:
                        pass
