import bpy
from ..utils.geo import get_blf_text_dims
from ..graphics.load import load_image_file
from ..graphics.draw import render_text
from ..window.panel.widget.layout.grid.elements.text import Text_Element
from ..window.panel.widget.layout.grid.elements.background import Background_Element
from ..window.panel.widget.layout.grid.elements.image import Image_Element
from ..window.panel.widget.layout.grid.elements.border import Border_Element


class Fast_UI():

    def __init__(self, db):

        self.db = db
        self.show = True

        # Start up data
        self.start_mouse_pos = None

        # Dims
        self.y_offset_mouse = 60 * self.db.scale_factor
        self.panel_padding = self.db.prefs.ui.Hops_modal_fast_ui_padding * self.db.scale_factor
        self.font_size = 12
        self.cell_padding = 12 #* self.db.scale_factor
        self.text_padding = 8 # * self.db.scale_factor

        # Switches
        self.first_in = True
        
        # Help
        self.show_help = self.db.prefs.ui.Hops_modal_auto_show_help
        self.show_global_help = False
        if self.show_help == False:
            self.show_help = self.db.prefs.ui.Hops_modal_help_left_open

        # Mods
        self.start_mod_hidden = False
        self.show_mods = self.db.prefs.ui.Hops_modal_auto_show_mods
        if self.show_mods == False:
            self.show_mods = self.db.prefs.ui.Hops_modal_mods_left_open

        self.location_option = 1    # NOTE: 1 = Center, 2 = Follow Mouse, 3 = Stays at mouse Pos

        # Drawing
        self.help = Help(db=self.db)
        self.boxes = []
        self.image = None
        self.mods = Mods(db=self.db)


    def clear(self):

        self.boxes = []


    def build_main(self, win_list=[], help_list=[], image="", mods_list=[], active_mod_name="", mods_label_text="Press M", number_mods=True):

        # Overrides
        self.mods.label_text = mods_label_text
        self.mods.number_mods = number_mods
        
        if self.start_mouse_pos == None:
            self.start_mouse_pos = self.db.event.mouse_pos

        # Override example in : Adjust Viewport
        if self.start_mod_hidden:
            if self.db.event.m_key_pressed:
                self.show_mods = True
                self.start_mod_hidden = False
            self.show_mods = False

        # Hot key checks
        self.hot_key_toggles()

        # Mods Panels
        self.mods.mod_items = mods_list
        if self.show_mods or self.db.prefs.ui.Hops_modal_mods_left_open:
            if mods_list != []:
                self.mods.active_mod_name = active_mod_name
                self.mods.already_sliced = False

        # Help Panel
        if self.show_help or self.db.prefs.ui.Hops_modal_help_left_open:
            self.help.help_items = help_list

        # Main Panel
        if win_list != []:

            bottom_left = (0, 0)

            prefs_y_offset = self.db.prefs.ui.Hops_modal_fast_ui_main_y_offset

            # Main banner is centered
            if self.location_option == 1:
                width = get_text_width(win_list=win_list, font_size=self.font_size) + 32 * self.db.scale_factor
                bottom_left = ((self.db.event.screen_width * .5) - (width * .5), self.panel_padding + prefs_y_offset)
            
            # Main banner will follow the mouse
            elif self.location_option == 2:
                bottom_left = (self.db.event.mouse_pos[0], self.db.event.mouse_pos[1] - self.y_offset_mouse)

            # Main banner will follow the mouse
            elif self.location_option == 3:
                bottom_left = (self.start_mouse_pos[0], self.start_mouse_pos[1] - self.y_offset_mouse)

            # Add image box
            bottom_left = self.setup_image_box(image=image, bottom_left=bottom_left)

            # Add text boxes
            self.setup_text_boxes(win_list=win_list, bottom_left=bottom_left)


    def setup_text_boxes(self, win_list=[], bottom_left=(0,0)):

        text_height = get_blf_text_dims(text="SAMPLE", size=self.font_size)[1]

        for item in win_list:

            font_dims = get_blf_text_dims(text=str(item), size=self.font_size)

            # Text box setup
            box = Box(db=self.db)

            # Dims
            box.bottom_left = bottom_left

            box.bottom_right = (
                bottom_left[0] + font_dims[0] + (self.text_padding * 2), 
                bottom_left[1])

            box.top_left = (
                bottom_left[0], 
                bottom_left[1]  + text_height + (self.text_padding * 2))

            box.top_right = (
                bottom_left[0] + font_dims[0] + (self.text_padding * 2),
                bottom_left[1]  + text_height + (self.text_padding * 2))

            # Text
            box.text = str(item)

            # Build elements
            box.setup(text_height=text_height)

            # Add to the drawing list
            self.boxes.append(box)

            # Add to bottom left
            bottom_left = (bottom_left[0] + self.cell_padding + font_dims[0] + (self.text_padding * 2), 
                        bottom_left[1])


    def setup_image_box(self, image="", bottom_left=(0,0)):

        # Add image box
        if image != "":

            if self.image == None:
                self.image = load_image_file(filename=image)

            # Font size sample
            font_dims = get_blf_text_dims(text="SAMPLE", size=self.font_size)

            # Box setup
            box = Box(db=self.db)

            box.using_text = False
            box.image = self.image
            box.force_fit = True

            # Dims
            box.bottom_left = bottom_left

            box.bottom_right = (
                bottom_left[0] + font_dims[1] + (self.text_padding * 2), 
                bottom_left[1])

            box.top_left = (
                bottom_left[0], 
                bottom_left[1] + font_dims[1] + (self.text_padding * 2))

            box.top_right = (
                bottom_left[0] + font_dims[1] + (self.text_padding * 2),
                bottom_left[1] + font_dims[1] + (self.text_padding * 2))

            # Build elements
            box.setup()

            # Add to the drawing list
            self.boxes.append(box)

            # Add to bottom left
            bottom_left = (bottom_left[0] + self.cell_padding + font_dims[1] + (self.text_padding * 2), 
                            bottom_left[1])  

        return bottom_left


    def hot_key_toggles(self):

        # Toggle Help
        if self.db.event.h_key_pressed:
            if not self.db.event.shift_pressed:
                self.show_help = not self.show_help
                self.db.prefs.ui.Hops_modal_help_left_open = self.show_help
                self.show_global_help = False
            if self.show_help and self.db.event.shift_pressed:
                self.show_global_help = not self.show_global_help

        # Toggle Mods
        if self.db.event.m_key_pressed == True and not self.db.event.shift_pressed:
            self.show_mods = not self.show_mods
            self.db.prefs.ui.Hops_modal_mods_left_open = self.show_mods

        # Toggle UI Follow
        if self.db.event.accent_grave_pressed == True and not self.db.event.shift_pressed:

            if self.db.prefs.ui.Hops_modal_fast_ui_loc_options == 1:
                self.db.prefs.ui.Hops_modal_fast_ui_loc_options = 2

            elif self.db.prefs.ui.Hops_modal_fast_ui_loc_options == 2:
                self.db.prefs.ui.Hops_modal_fast_ui_loc_options = 3

            elif self.db.prefs.ui.Hops_modal_fast_ui_loc_options == 3:
                self.db.prefs.ui.Hops_modal_fast_ui_loc_options = 1

        self.location_option = self.db.prefs.ui.Hops_modal_fast_ui_loc_options


    def draw(self, context):

        # Main banner
        for box in self.boxes:
            box.draw()

        # Help
        if self.show_help:
            if self.show_global_help:
                self.help.draw(as_global=True)
            else:
                self.help.draw()
        elif self.db.prefs.ui.Hops_modal_help_show_label:
            self.help.draw_label()

        # Mods
        if self.show_mods:
            self.mods.draw(context)
            self.mods.already_sliced = True
        elif self.db.prefs.ui.Hops_modal_mods_show_label:
            self.mods.draw_label(context)


    def destroy(self):

        # Unload images
        if self.image != None:
            try:
                bpy.data.images.remove(self.image)
            except:
                pass


def get_text_width(win_list=[], font_size=12):

    if win_list != []:

        total_characters = 0
        for item in win_list:
            item = str(item)
            total_characters += len(item)

        return get_blf_text_dims(text=("X" * total_characters), size=font_size)[0]

    return 0


class Box():

    def __init__(self, db):

        self.db = db

        # Dims
        self.top_left = (0, 0)
        self.top_right = (0, 0)
        self.bottom_left = (0, 0)
        self.bottom_right = (0, 0)

        # Drawing
        self.using_text = True
        self.text = ""
        self.image = None
        self.text_element = Text_Element()
        self.background_element = Background_Element()
        self.image_element = Image_Element()
        self.border_element = Border_Element()
        self.setup_elements()


    def setup_elements(self):

        self.text_element.db = self.db
        self.background_element.db = self.db
        self.image_element.db = self.db
        self.border_element.db = self.db
        self.border_element.line_width = 1


    def setup(self, text_height=0):

        # Border
        if self.db.prefs.ui.Hops_modal_cell_border:
            self.border_element.top_left = self.top_left
            self.border_element.top_right = self.top_right
            self.border_element.bottom_left = self.bottom_left
            self.border_element.bottom_right = self.bottom_right 


        # Background Element
        self.background_element.primary = False
        self.background_element.top_left = self.top_left
        self.background_element.top_right = self.top_right
        self.background_element.bottom_left = self.bottom_left
        self.background_element.bottom_right = self.bottom_right 


        # Setup for text
        if self.using_text:

            # Text Element
            self.text_element.text = self.text
            self.text_element.force_fit_text = False
            self.text_element.color_select = 1
            self.text_element.set_y_external = True
            center = self.bottom_left[1] + ((self.top_left[1] - self.bottom_left[1]) * .5)
            center -= text_height * .5
            self.text_element.external_y = center
            self.text_element.top_left = self.top_left
            self.text_element.top_right = self.top_right
            self.text_element.bottom_left = self.bottom_left
            self.text_element.bottom_right = self.bottom_right

        # Setup for image
        else:

            # Image Element
            self.image_element.image = self.image
            self.image_element.force_fit = False
            self.image_element.top_left = self.top_left
            self.image_element.top_right = self.top_right
            self.image_element.bottom_left = self.bottom_left
            self.image_element.bottom_right = self.bottom_right


    def draw(self):

        self.background_element.draw()

        # Border
        if self.db.prefs.ui.Hops_modal_cell_border:
            self.border_element.draw()

        if self.using_text:
            self.text_element.draw()

        else:
            self.image_element.draw()


class Mods():

    def __init__(self, db):

        self.db = db

        # Text Dims
        self.padding_LR = 8 # * self.db.scale_factor
        self.padding_TB = 8 # * self.db.scale_factor
        self.panel_padding = self.db.prefs.ui.Hops_modal_fast_ui_padding * self.db.scale_factor

        # Font
        self.font_size = int(12 * self.db.prefs.ui.Hops_modal_fast_ui_mods_size)

        # Mods list
        self.already_sliced = False
        self.active_mod_name = ""
        self.mod_items = []

        # Label
        self.label_text = "Press M"

        # Options
        self.number_mods = True

        # Drawing
        self.background_element = Background_Element()
        self.border_element = Border_Element()
        self.setup_elements()


    def setup_elements(self):

        self.background_element.db = self.db
        self.background_element.primary = False

        self.border_element.db = self.db
        self.border_element.line_width = 1


    def draw_label(self, context):

        if self.mod_items != []:
            prefs_x_offset = self.db.prefs.ui.Hops_modal_fast_ui_mods_offset[0]
            prefs_y_offset = self.db.prefs.ui.Hops_modal_fast_ui_mods_offset[1]

            text_dims = get_blf_text_dims(text=self.label_text, size=12)
            total_width = text_dims[0] + self.padding_LR
            total_height = text_dims[1] + self.padding_TB
            self.draw_elements(total_width=total_width, total_height=total_height)
            color = self.db.colors.Hops_UI_secondary_text_color

            render_text(text=self.label_text, position=(self.panel_padding + prefs_x_offset, self.panel_padding + self.padding_TB + prefs_y_offset), size=12, color=color)


    def draw(self, context):

        if self.mod_items != []:

            self.slice_mods()

            # Dims
            offset_y = 0
            key_max_width = 0
            desc_max_width = 0
            total_height = 0
            total_width = 0

            # Get text offsets
            largest_item = ""
            index = 0

            for item in self.mod_items:
                key, desc = item[0], item[1]

                # Text dims
                key_dims = get_blf_text_dims(text=key, size=self.font_size)
                desc_dims = get_blf_text_dims(text=desc, size=self.font_size)

                if key_dims[0] > key_max_width:
                    key_max_width = key_dims[0]
                    largest_item = key

                if desc_dims[0] > desc_max_width:
                    desc_max_width = desc_dims[0]

                offset_y = key_dims[1]
                index += 1

            offset_y += self.padding_TB
            total_height = (len(self.mod_items) * offset_y) + self.padding_TB
            key_max_width += self.padding_LR
            desc_max_width += self.padding_LR

            total_width = key_max_width + desc_max_width

            self.draw_elements(total_width, total_height)
            self.draw_text(key_max_width, offset_y, key_dims)


    def slice_mods(self):

        if not self.already_sliced:
            
            # Number mods
            if self.number_mods:
                
                numbering = 0
                for item in reversed(self.mod_items):
                    
                    if item[0] == self.active_mod_name:
                        item[0] = str(numbering + 1) + " : " + item[0]
                        self.active_mod_name = item[0]
                    
                    else:
                        item[0] = str(numbering + 1) + " : " + item[0]

                    numbering += 1

            # Get mod index
            mod_index = 0
            for item in self.mod_items:
                if item[0] == self.active_mod_name:
                    break
                else:
                    mod_index += 1

            # Slice
            slice_limit = int(self.db.prefs.ui.Hops_modal_mod_count_fast_ui *.5)

            start_slice = 0
            if mod_index >= slice_limit:
                start_slice = mod_index - slice_limit

            end_slice = len(self.mod_items)
            if len(self.mod_items) - mod_index >= slice_limit:
                end_slice = mod_index + slice_limit

            self.mod_items = self.mod_items[start_slice : end_slice]


    def draw_elements(self, total_width, total_height):

        prefs_x_offset = self.db.prefs.ui.Hops_modal_fast_ui_mods_offset[0]
        prefs_y_offset = self.db.prefs.ui.Hops_modal_fast_ui_mods_offset[1]

        # Background
        self.background_element.bottom_left =  (prefs_x_offset + self.panel_padding - self.padding_LR, self.panel_padding + prefs_y_offset)
        self.background_element.top_left =     (prefs_x_offset + self.panel_padding - self.padding_LR, total_height + self.panel_padding + self.padding_TB + prefs_y_offset)
        self.background_element.bottom_right = (prefs_x_offset + self.panel_padding + total_width, self.panel_padding + prefs_y_offset)
        self.background_element.top_right =    (prefs_x_offset + self.panel_padding + total_width, total_height + self.panel_padding + self.padding_TB + prefs_y_offset)
        self.background_element.draw()

        # Border
        if self.db.prefs.ui.Hops_modal_cell_border:
            self.border_element.bottom_left =  (prefs_x_offset + self.panel_padding - self.padding_LR, self.panel_padding + prefs_y_offset)
            self.border_element.top_left =     (prefs_x_offset + self.panel_padding - self.padding_LR, total_height + self.panel_padding + self.padding_TB + prefs_y_offset)
            self.border_element.bottom_right = (prefs_x_offset + self.panel_padding + total_width, self.panel_padding + prefs_y_offset)
            self.border_element.top_right =    (prefs_x_offset + self.panel_padding + total_width, total_height + self.panel_padding + self.padding_TB + prefs_y_offset)
            self.border_element.draw()


    def draw_text(self, key_max_width, offset_y, key_dims):

        prefs_x_offset = self.db.prefs.ui.Hops_modal_fast_ui_mods_offset[0]
        prefs_y_offset = self.db.prefs.ui.Hops_modal_fast_ui_mods_offset[1]

        # Draw text
        for index, item in enumerate(self.mod_items):
            key, desc = item[0], item[1]

            color = (0,0,0,0)
            if key == self.active_mod_name or str(index) == self.active_mod_name:
                color = self.db.colors.Hops_UI_mods_highlight_color
            else:
                color = self.db.colors.Hops_UI_secondary_text_color

            render_text(text=key, position=(prefs_x_offset + self.panel_padding, offset_y + self.panel_padding + prefs_y_offset - self.padding_TB), size=self.font_size, color=color)
            render_text(text=desc, position=(prefs_x_offset + self.panel_padding + key_max_width, offset_y + self.panel_padding + prefs_y_offset - self.padding_TB), size=self.font_size, color=color)

            offset_y += key_dims[1] + self.padding_TB


class Help():

    def __init__(self, db):

        self.db = db

        # Font
        self.font_size = int(12 * db.prefs.ui.Hops_modal_fast_ui_help_size)

        # Items
        self.help_items = []

        # Window BG
        self.window_background = Background_Element()
        self.window_background.db = db
        self.window_background.primary = False

        self.window_border = Border_Element()
        self.window_border.db = db
        self.window_border.line_width = 1

        # Label BG
        self.label_background = Background_Element()
        self.label_background.db = db
        self.label_background.primary = False

        self.label_border = Border_Element()
        self.label_border.db = db
        self.label_border.line_width = 1

        # Dimensions
        self.font_padding = 8 * db.scale_factor
        self.prefs_offset = db.prefs.ui.Hops_modal_fast_ui_help_offset
        self.panel_padding = db.prefs.ui.Hops_modal_fast_ui_padding * db.scale_factor


    def draw_label(self):

        text_dims = get_blf_text_dims(text="Press H", size=12)

        total_width = text_dims[0] + self.font_padding
        total_height = text_dims[1] + self.font_padding

        offset_x = self.db.event.screen_width - total_width - self.panel_padding
        offset_x += self.prefs_offset[0]
        bot_y = self.panel_padding + self.prefs_offset[1]
        top_y = self.panel_padding + self.prefs_offset[1] + total_height + self.font_padding

        if self.db.prefs.ui.Hops_modal_background:
            self.label_background.bottom_left  = (offset_x - self.font_padding, bot_y)
            self.label_background.bottom_right = (offset_x + total_width      , bot_y)
            self.label_background.top_left     = (offset_x - self.font_padding, top_y)
            self.label_background.top_right    = (offset_x + total_width      , top_y)
            self.label_background.draw()

        if self.db.prefs.ui.Hops_modal_cell_border:
            self.label_border.bottom_left  = (offset_x - self.font_padding, bot_y)
            self.label_border.bottom_right = (offset_x + total_width      , bot_y)
            self.label_border.top_left     = (offset_x - self.font_padding, top_y)
            self.label_border.top_right    = (offset_x + total_width      , top_y)
            self.label_border.draw()

        color = self.db.colors.Hops_UI_secondary_text_color
        render_text(text="Press H", position=(offset_x, self.panel_padding + self.font_padding + self.prefs_offset[1]), size=12, color=color)


    def draw(self, as_global=False):

        if not self.help_items: return

        help_items = []
        if as_global:
            if "GLOBAL" not in self.help_items: return
            help_items = self.help_items["GLOBAL"]
        else:
            if "STANDARD" not in self.help_items: return
            help_items = self.help_items["STANDARD"]
        if not help_items:
            help_items = [("Nothing available", "")]

        offset_y = 0
        offset_x = 0
        key_max_width = 0
        desc_max_width = 0
        total_height = 0
        prefs_x_offset = self.db.prefs.ui.Hops_modal_fast_ui_help_offset[0]
        prefs_y_offset = self.db.prefs.ui.Hops_modal_fast_ui_help_offset[1]

        longest_key_string = ""
        longest_val_string = ""

        for item in help_items:
            key, desc = item[0], item[1]

            if len(key) > len(longest_key_string):
                longest_key_string = key

            if len(desc) > len(longest_val_string):
                longest_val_string = desc

        key_dims = get_blf_text_dims(text=longest_key_string, size=self.font_size)
        desc_dims = get_blf_text_dims(text=longest_val_string, size=self.font_size)
        key_max_width = key_dims[0] + self.font_padding
        desc_max_width = desc_dims[0] + self.font_padding
        offset_y = key_dims[1] + self.font_padding

        total_height = (len(help_items) * offset_y) + self.font_padding * 2
        total_width = key_max_width + desc_max_width + self.font_padding

        offset_x = self.db.event.screen_width - total_width - self.panel_padding
        offset_x += prefs_x_offset

        if self.db.prefs.ui.Hops_modal_background:
            self.window_background.bottom_left =  (offset_x - self.font_padding, self.panel_padding + prefs_y_offset)
            self.window_background.bottom_right = (offset_x + total_width, self.panel_padding + prefs_y_offset)
            self.window_background.top_left =     (offset_x - self.font_padding, total_height + self.panel_padding + prefs_y_offset)
            self.window_background.top_right =    (offset_x + total_width, total_height + self.panel_padding + prefs_y_offset)
            self.window_background.draw()

        if self.db.prefs.ui.Hops_modal_cell_border:
            self.window_border.bottom_left =  (offset_x - self.font_padding, self.panel_padding + prefs_y_offset)
            self.window_border.bottom_right = (offset_x + total_width, self.panel_padding + prefs_y_offset)
            self.window_border.top_left =     (offset_x - self.font_padding, total_height + self.panel_padding + prefs_y_offset)
            self.window_border.top_right =    (offset_x + total_width, total_height + self.panel_padding + prefs_y_offset)
            self.window_border.draw()

        for item in help_items:
            
            key, desc = item[0], item[1]
            color = self.db.colors.Hops_UI_secondary_text_color
            render_text(text=key, position=(offset_x, offset_y + self.panel_padding + prefs_y_offset - self.font_padding), size=self.font_size, color=color)
            render_text(text=desc, position=(offset_x + key_max_width, offset_y + self.panel_padding + prefs_y_offset - self.font_padding), size=self.font_size, color=color)

            offset_y += key_dims[1] + self.font_padding

        msg = "Standard (Shift H)" if as_global else "Global (Shift H)"
        self.__draw_window_label(msg=msg, pos=(offset_x - self.font_padding, offset_y))


    def __draw_window_label(self, msg="", pos=(0,0)):

        text_dims = get_blf_text_dims(text=msg, size=12)

        total_width = text_dims[0] + self.font_padding * 2
        total_height = text_dims[1] + self.font_padding * 2

        x, y = pos
        y += self.font_padding * 4

        if self.db.prefs.ui.Hops_modal_background:
            self.label_background.bottom_left  = (x , y)
            self.label_background.bottom_right = (x + total_width, y)
            self.label_background.top_left     = (x, y + total_height)
            self.label_background.top_right    = (x + total_width, y + total_height)
            self.label_background.draw()

        if self.db.prefs.ui.Hops_modal_cell_border:
            self.label_border.bottom_left  = (x , y)
            self.label_border.bottom_right = (x + total_width, y)
            self.label_border.top_left     = (x, y + total_height)
            self.label_border.top_right    = (x + total_width, y + total_height)
            self.label_border.draw()

        y += self.font_padding
        x += self.font_padding
        color = self.db.colors.Hops_UI_secondary_text_color
        render_text(text=msg, position=(x, y), size=12, color=color)

