import bpy, webbrowser
from mathutils import Vector
from . utils import add_list_items, toggle_help, toggle_mods
from .. graphics.load import load_image_file
from ... utility import addon
from ..window.panel.widget.layout.grid.elements.call_back import Call_Back_Event

class Preset_Every_Scroll():

    def __init__(self, create):

        self.create = create
        self.db = self.create.db
        self.images = []
        self.main_window = None
        self.widget = None
        self.widget_layout = None
        self.win_text = None
        self.win_play_button = None
        self.win_play_cell = None
        self.scroll_layout = None
        self.header_layout = None

        # Help Window
        self.help_window = None

        self.__setup()


    def __setup(self):
        
        # Load Images
        self.images.append(load_image_file(filename="play"))
        self.images.append(load_image_file(filename="pause"))

        self.db.prefs.ui.Hops_modal_help_visible = True

        self.main_window = self.create.window(window_key="Every_Scroll")
        self.__main_window_layout()

        self.help_window = self.create.window(window_key="Help")
        self.help_window_layout()


    def __main_window_layout(self):
        '''Create the main window skeleton.'''

        # Panel 1
        self.create.panel(window=self.main_window, x_split_percent=100, y_split_percent=100)

        # Header
        self.create.window_header_layout(window=self.main_window, header_height_percent=20, min_max_height=(20, 30))

        self.header_layout = self.main_window.header_layout
        self.create.row(layout=self.header_layout, height_percent=100)

        # Label
        self.create.column(layout=self.header_layout, width_percent=80)
        self.header_cell = self.create.cell(layout=self.header_layout, hover_highlight=True)
        self.win_text = self.create.element_text(layout=self.header_layout, text="Every Scroll", target_size=12)
        self.create.element_border(layout=self.header_layout, line_width=1)

        # Play button
        self.create.column(layout=self.header_layout, width_percent=20)
        self.win_play_cell = self.create.cell(layout=self.header_layout, hover_highlight=True)
        self.win_play_button = self.create.element_image(layout=self.header_layout, image=self.images[0])
        self.create.element_border(layout=self.header_layout, line_width=1)

        # Widget
        self.create.widget_scroll(panel=self.main_window.panels[-1], win_key="Every_Scroll", collapsable=False)
        self.widget = self.main_window.panels[-1].widget
        self.scroll_layout = self.create.widget_body_layout(widget=self.widget)
        self.widget_layout = self.widget.layout


    def help_window_layout(self):
        '''Create the help window skeleton.'''

        # Body
        # Panel 1
        self.create.panel(window=self.help_window, x_split_percent=100, y_split_percent=100)

        # Widget
        self.create.widget_scroll(panel=self.help_window.panels[-1], win_key="Help")
        widget = self.help_window.panels[-1].widget

        # Widget Header
        self.create.widget_header_layout(widget=widget, header_height_percent=20)
        header_layout = widget.header_layout

        self.create.row(layout=header_layout, height_percent=100)
        self.create.column(layout=header_layout, width_percent=100)
        self.create.cell(layout=header_layout, hover_highlight=False)
        self.create.element_text(layout=header_layout, text="Help")
        self.create.element_border(layout=header_layout, line_width=2)

        self.create.widget_body_layout(widget=widget)
        body_layout = widget.layout


    def build_main(self, win_dict, window_name, win_form=None):
        self.win_text.text = window_name

        # Header Callback
        cb = Call_Back_Event()
        cb.db = self.db
        cb.func = win_form[0]
        cb.positive_args = win_form[1]
        cb.negative_args = win_form[1]
        cb.scrollable = True
        self.header_cell.click_events = [cb]

        # Header Play
        if win_form[2]: self.win_play_button.image = self.images[1]
        else: self.win_play_button.image = self.images[0]
        cb = Call_Back_Event()
        cb.db = self.db
        cb.func = win_form[3]
        cb.positive_args = win_form[4]
        cb.negative_args = win_form[4]
        cb.scrollable = True
        self.win_play_cell.click_events = [cb]

        if win_dict == None:
            return

        if win_dict['TYPE'] == 'MOD':
            self.__build_mod_interface(win_dict)
        elif win_dict['TYPE'] == 'CHILD':
            self.__build_child_interface(win_dict)
        elif win_dict['TYPE'] == 'BOOL':
            self.__build_bool_interface(win_dict)
        elif win_dict['TYPE'] == 'COLL':
            self.__build_coll_interface(win_dict)

    # --- MODS --- #

    def __build_mod_interface(self, win_dict):

        layout = self.scroll_layout
        rows = len(win_dict['ITEMS'])
        row_percent = 100 / rows if rows > 0 else 100

        mods = win_dict['ITEMS']
        mods.reverse()

        index = len(mods)
        for mod in mods:
            
            # Row
            self.create.row(layout=layout, height_percent=row_percent)

            # Col : Number the mods
            self.create.column(layout=layout, width_percent=10)
            self.create.cell(layout=layout, hover_highlight=False)
            self.create.element_border(layout=layout, line_width=1)
            self.create.element_text(layout=layout, text=str(index))
            index -= 1

            # Col : Mod names
            self.create.column(layout=layout, width_percent=60)
            self.create.cell(layout=layout, hover_highlight=True)
            self.create.element_background(layout=layout, primary=False, bevel=True)
            self.create.element_border(layout=layout, line_width=1)

            if mod.name == win_dict['ACTIVE']:
                self.create.element_text(layout=layout, text=mod.name, color_select=2)
            else:
                self.create.element_text(layout=layout, text=mod.name, color_select=0)

            self.create.event_call_back(layout=layout, func=win_dict['SETFUNC'], positive_args=(index,))
            self.create.event_call_back(layout=layout, shift_func=win_dict['SHIFTFUNC'])

            # Col : Mod VP Show
            self.create.column(layout=layout, width_percent=10)
            self.create.cell(layout=layout, hover_highlight=True)
            self.create.element_background(layout=layout, primary=False, bevel=True)
            self.create.element_border(layout=layout, line_width=1)

            if mod.show_viewport:
                self.create.element_text(layout=layout, text="O", color_select=2)
            else:
                self.create.element_text(layout=layout, text="X", color_select=0)

            self.create.event_call_back(layout=layout, func=self.mod_toggle_view, positive_args=(mod,))

            # Col : Mod Show Render
            self.create.column(layout=layout, width_percent=10)
            self.create.cell(layout=layout, hover_highlight=True)
            self.create.element_background(layout=layout, primary=False, bevel=True)
            self.create.element_border(layout=layout, line_width=1)

            if mod.show_render:
                self.create.element_text(layout=layout, text="R", color_select=2)
            else:
                self.create.element_text(layout=layout, text="R", color_select=0)

            self.create.event_call_back(layout=layout, func=self.mod_toggle_render, positive_args=(mod,))

            # Col : Mod Apply
            self.create.column(layout=layout, width_percent=10)
            self.create.cell(layout=layout, hover_highlight=True)
            self.create.element_background(layout=layout, primary=False, bevel=True)
            self.create.element_border(layout=layout, line_width=1)
            self.create.element_text(layout=layout, text="✓", color_select=0)
            self.create.event_call_back(
                layout=layout,
                func=win_dict['APPLYFUNC'], positive_args=(mod,),
                shift_func=win_dict['APPLYFUNC'], shift_arges=(mod, True))


    def mod_toggle_view(self, mod):
        mod.show_viewport = not mod.show_viewport


    def mod_toggle_render(self, mod):
        mod.show_render = not mod.show_render

    # --- CHILD --- #

    def __build_child_interface(self, win_dict):

        layout = self.scroll_layout
        rows = len(win_dict['ITEMS'])
        row_percent = 100 / rows if rows > 0 else 100

        objs = win_dict['ITEMS']
        objs.reverse()

        index = len(objs)
        for obj in objs:
            
            # Row
            self.create.row(layout=layout, height_percent=row_percent)

            # Col : Number the mods
            self.create.column(layout=layout, width_percent=10)
            self.create.cell(layout=layout, hover_highlight=False)
            self.create.element_border(layout=layout, line_width=1)
            self.create.element_text(layout=layout, text=str(index))

            # Col : Mod names
            self.create.column(layout=layout, width_percent=70)
            self.create.cell(layout=layout, hover_highlight=False)
            self.create.element_background(layout=layout, primary=False, bevel=True)
            self.create.element_border(layout=layout, line_width=1)

            if obj.name == win_dict['ACTIVE']:
                self.create.element_text(layout=layout, text=obj.name, color_select=2)
            else:
                self.create.element_text(layout=layout, text=obj.name, color_select=0)

            self.create.event_call_back(layout=layout, func=win_dict['SETFUNC'], positive_args=(index-1,))

            # Col : Mod Show
            self.create.column(layout=layout, width_percent=10)
            self.create.cell(layout=layout, hover_highlight=False)
            self.create.element_background(layout=layout, primary=False, bevel=True)
            self.create.element_border(layout=layout, line_width=1)

            if obj.hide_get():
                self.create.element_text(layout=layout, text="X", color_select=2)
            else:
                self.create.element_text(layout=layout, text="O", color_select=0)

            self.create.event_call_back(layout=layout, func=self.child_toggle, positive_args=(obj,))

            # Col : Tracked
            self.create.column(layout=layout, width_percent=10)
            self.create.cell(layout=layout, hover_highlight=True)
            self.create.element_background(layout=layout, primary=False, bevel=True)
            self.create.element_border(layout=layout, line_width=1)

            if obj in win_dict['TRACKED']:
                self.create.element_text(layout=layout, text="R", color_select=2)
            else:
                self.create.element_text(layout=layout, text="A", color_select=0)
            
            self.create.event_call_back(layout=layout, func=win_dict['TRACKFUNC'], positive_args=(obj,))

            index -= 1


    def child_toggle(self, obj):
        hide = not obj.hide_get()
        obj.hide_set(hide)

    # --- BOOLS --- #

    def __build_bool_interface(self, win_dict):

        layout = self.scroll_layout
        rows = len(win_dict['ITEMS'])
        row_percent = 100 / rows if rows > 0 else 100

        mods = win_dict['ITEMS']
        mods.reverse()

        code_index = len([m for m in mods if m.type == 'BOOLEAN']) - 1
        index = len(mods)

        for mod in mods:
            
            # Row
            self.create.row(layout=layout, height_percent=row_percent)

            if mod.type == 'BOOLEAN':
                # Col : Number the mods
                self.create.column(layout=layout, width_percent=10)
                self.create.cell(layout=layout, hover_highlight=False)
                self.create.element_border(layout=layout, line_width=1)
                self.create.element_text(layout=layout, text=str(index))

                # Col : Mod names
                self.create.column(layout=layout, width_percent=60)
                self.create.cell(layout=layout, hover_highlight=False)
                self.create.element_background(layout=layout, primary=False, bevel=True)
                self.create.element_border(layout=layout, line_width=1)

                if mod.name == win_dict['ACTIVE'] or index == win_dict['ACTIVE']:
                    self.create.element_text(layout=layout, text=mod.name, color_select=2)
                else:
                    self.create.element_text(layout=layout, text=mod.name, color_select=0)

                self.create.event_call_back(layout=layout, func=win_dict['SETFUNC'], positive_args=(code_index,))
                self.create.event_call_back(layout=layout, shift_func=win_dict['ADDCLICK'])
                code_index -= 1

                # Col : Mod Show
                self.create.column(layout=layout, width_percent=10)
                self.create.cell(layout=layout, hover_highlight=False)
                self.create.element_background(layout=layout, primary=False, bevel=True)
                self.create.element_border(layout=layout, line_width=1)

                if mod.show_viewport:
                    self.create.element_text(layout=layout, text="O", color_select=2)
                else:
                    self.create.element_text(layout=layout, text="X", color_select=0)

                self.create.event_call_back(layout=layout, func=self.bool_toggle, positive_args=(mod,))

                # Col : Mod Apply
                self.create.column(layout=layout, width_percent=10)
                self.create.cell(layout=layout, hover_highlight=True)
                self.create.element_background(layout=layout, primary=False, bevel=True)
                self.create.element_border(layout=layout, line_width=1)
                self.create.element_text(layout=layout, text="✓", color_select=0)
                self.create.event_call_back(
                    layout=layout,
                    func=win_dict['APPLYFUNC'], positive_args=(mod,),
                    shift_func=win_dict['APPLYFUNC'], shift_arges=(mod, True))


                # Col : Mod Apply
                self.create.column(layout=layout, width_percent=10)
                self.create.cell(layout=layout, hover_highlight=True)
                self.create.element_background(layout=layout, primary=False, bevel=True)
                self.create.element_border(layout=layout, line_width=1)

                if mod.object and mod.object in win_dict['TRACKED']:
                    self.create.element_text(layout=layout, text="R", color_select=2)
                else:
                    self.create.element_text(layout=layout, text="A", color_select=0)
                
                self.create.event_call_back(layout=layout, func=win_dict['TRACKMOD'], positive_args=(mod,))
                    
            else:
                # Col : Number the mods
                self.create.column(layout=layout, width_percent=10)
                self.create.cell(layout=layout, hover_highlight=False)
                self.create.element_border(layout=layout, line_width=1)
                self.create.element_text(layout=layout, text=str(index))

                # Col : Mod names
                self.create.column(layout=layout, width_percent=90)
                self.create.cell(layout=layout, hover_highlight=False)
                self.create.element_background(layout=layout, primary=True, bevel=True)
                self.create.element_border(layout=layout, line_width=1)
                self.create.element_text(layout=layout, text=mod.name, color_select=0)

            index -= 1


    def bool_toggle(self, mod):
        mod.show_viewport = not mod.show_viewport

    # --- COLL --- #

    def __build_coll_interface(self, win_dict):
        layout = self.scroll_layout
        rows = len(win_dict['ITEMS'])
        row_percent = 100 / rows if rows > 0 else 100

        colls = win_dict['ITEMS']
        index = len(colls)
        for coll in reversed(colls):
            
            # Row
            self.create.row(layout=layout, height_percent=row_percent)

            # Col : Number the collections
            self.create.column(layout=layout, width_percent=10)
            self.create.cell(layout=layout, hover_highlight=True)
            self.create.element_border(layout=layout, line_width=1)
            self.create.element_text(layout=layout, text=str(index))

            # Col : Collection names
            self.create.column(layout=layout, width_percent=80)
            self.create.cell(layout=layout, hover_highlight=False)
            self.create.element_background(layout=layout, primary=False, bevel=True)
            self.create.element_border(layout=layout, line_width=1)

            active_name = win_dict['ACTIVE'].name if win_dict['ACTIVE'] else ""
            if coll.name == active_name:
                self.create.element_text(layout=layout, text=coll.name, color_select=2)
            else:
                self.create.element_text(layout=layout, text=coll.name, color_select=0)

            self.create.event_call_back(layout=layout, func=win_dict['SETFUNC'], positive_args=(coll,))

            # Col : Collection tracking
            self.create.column(layout=layout, width_percent=10)
            self.create.cell(layout=layout, hover_highlight=True)
            self.create.element_background(layout=layout, primary=False, bevel=True)
            self.create.element_border(layout=layout, line_width=1)
            self.create.element_text(layout=layout, text="✓", color_select=2)
            self.create.event_call_back(layout=layout, func=win_dict['OBJTOGGLE'], positive_args=(coll,))

            index -= 1


    def build_help(self, hot_keys_dict, quick_ops_dict):
        widget = self.help_window.panels[0].widget
        layout = widget.layout
        rows = len(hot_keys_dict)
        row_percent = 100 / rows if rows > 0 else 100

        primary = True
        target_size = 12
        drag = False

        for key, val in hot_keys_dict.items():
            
            # Add key
            self.create.row(layout=layout, height_percent=row_percent)
            self.create.column(layout=layout, width_percent=30)
            hover_highlight = True if len(val) > 1 else False
            self.create.cell(layout=layout, hover_highlight=hover_highlight, dims_override=(0,-6,0,0))
            self.create.element_background(layout=layout, primary=False, bevel=True)
            self.create.element_border(layout=layout, line_width=1)
            self.create.element_text(layout=layout, text=key, color_select=1)

            if type(val) == str:

                # Add description
                self.create.column(layout=layout, width_percent=70)
                self.create.cell(layout=layout, hover_highlight=False)
                self.create.element_border(layout=layout, line_width=1)
                self.create.element_text(layout=layout, text=val, color_select=0, target_size=target_size)

            if len(val) > 0:

                if len(val) == 1:

                    # Add description
                    self.create.column(layout=layout, width_percent=70)
                    self.create.cell(layout=layout, hover_highlight=False)
                    self.create.element_text(layout=layout, text=val[0], color_select=0, target_size=target_size)
                    self.create.element_border(layout=layout, line_width=1)

                if len(val) == 2:
                    if drag:
                        self.create.event_call_drag(layout=layout, func=val[1])
                    else:
                        self.create.event_call_back(layout=layout, func=val[1])
                    
                    # Add description
                    self.create.column(layout=layout, width_percent=70)
                    self.create.cell(layout=layout, hover_highlight=False)
                    self.create.element_border(layout=layout, line_width=1)
                    self.create.element_text(layout=layout, text=val[0], color_select=0, target_size=target_size)

                elif len(val) == 3:
                    if drag:
                        self.create.event_call_drag(layout=layout, func=val[1], positive_args=val[2])
                    
                    else:
                        self.create.event_call_back(layout=layout, func=val[1], positive_args=val[2])

                    # Add description
                    self.create.column(layout=layout, width_percent=70)
                    self.create.cell(layout=layout, hover_highlight=False)
                    self.create.element_border(layout=layout, line_width=1)
                    self.create.element_text(layout=layout, text=val[0], color_select=0, target_size=target_size)

                elif len(val) == 4:
                    if drag:
                        self.create.event_call_drag(layout=layout, func=val[1], positive_args=val[2], negative_args=val[3])
                    
                    else:
                        self.create.event_call_back(layout=layout, func=val[1], positive_args=val[2], negative_args=val[3])

                    # Add description
                    self.create.column(layout=layout, width_percent=70)
                    self.create.cell(layout=layout, hover_highlight=False)
                    self.create.element_border(layout=layout, line_width=1)
                    self.create.element_text(layout=layout, text=val[0], color_select=0, target_size=target_size)


    def destroy(self):
        # Unload images
        if self.images != []:
            for image in self.images:
                if image != None:
                    try:
                        bpy.data.images.remove(image)
                    except:
                        pass