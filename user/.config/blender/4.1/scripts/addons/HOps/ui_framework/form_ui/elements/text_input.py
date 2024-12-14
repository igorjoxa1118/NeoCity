import bpy, time, math, numpy
from math import sin
from mathutils import Vector
from ....utility.screen import dpi_factor
from ... graphics.load import load_image_file
from ... graphics.draw import render_text, draw_border_lines, render_quad, draw_2D_lines
from ... utils.geo import get_blf_text_dims
from ... utils.checks import is_mouse_in_quad
from . import Dims, Tips


class Text_Input:
    def __init__(self,
        obj=None, attr="", font_size=12, width=50, height=0,
        tips=None, tip_size=12,
        on_active_callback=None):
        
        self.dims = Dims()
        self.font_color = (0,0,0,1)
        self.bg_color = (0,0,0,1)
        self.border_color = (0,0,0,1)
        self.obj = obj
        self.attr = attr
        self.font_size = font_size
        self.width = width * dpi_factor(min=0.5)
        self.height = height * dpi_factor(min=0.5)
        self.text = ""
        self.tips = Tips(tips, tip_size) if tips else None
        self.mouse_over = False
        self.on_active_callback = on_active_callback
        # Input
        self.entry_string = ""
        # Notify
        self.timer = None
        self.locked = False
        self.alpha = 1


    def build(self, db, x_offset, h_offset):
        self.font_color = db.color.text
        self.bg_color = db.color.cell_background
        self.border_color = db.color.border

        if self.obj == None or self.attr == "": return

        self.text = self.__get_value()
        dims = get_blf_text_dims(self.text, self.font_size)
        pad = self.dims.padding

        self.dims.max_width = self.width
        if self.height: self.dims.max_height = self.height
        else: self.dims.max_height = dims[1] + pad * 2

        self.dims.bot_left  = (x_offset, h_offset)
        self.dims.top_left  = (x_offset, h_offset + self.dims.max_height)
        self.dims.top_right = (x_offset + self.dims.max_width, h_offset + self.dims.max_height)
        self.dims.bot_right = (x_offset + self.dims.max_width, h_offset)

        self.dims.x_pos = x_offset + pad
        self.dims.y_pos = h_offset + pad

        if self.tips:
            self.tips.build(db, self.dims.top_left[0], self.dims.top_left[1])


    def update(self, context, event, db):
        if self.tips: self.tips.update()
        self.locked = False
        self.mouse_over = is_mouse_in_quad(self.dims.quad(), db.mouse_pos, tolerance=-1)
        self.__set_colors(db, self.mouse_over)
        if self.mouse_over:
            self.__mouse_over_actions(context, event, db)
        
        if self.obj == None or self.attr == "": return                
        self.text = self.__get_value()


    def __set_colors(self, db, mouse_over):
        self.border_color = db.color.border
        # Mouse over
        if mouse_over:
            self.bg_color = db.color.mouse_over
        # Standard color
        else:
            self.bg_color = db.color.cell_background


    def __mouse_over_actions(self, context, event, db):
        if db.locked_element: return

        # Clicked down
        if db.clicked == True:
            self.__on_active_callback()
            # Locked State
            db.locked_element = self
            self.entry_string = self.__get_value()
            if self.timer == None:
                self.timer = context.window_manager.event_timer_add(0.025, window=context.window)


    def __on_active_callback(self):
        if self.on_active_callback:
            self.on_active_callback()


    def locked_update(self, context, event, db):

        self.locked = True

        # Set highlight color during focus mode
        self.border_color = db.color.mods_highlight

        invalid = {'\\', '/', ':', '*', '?', '"', '<', '>', '|', '.'}

        # Append text
        if event.ascii not in invalid and event.value == 'PRESS':
            self.entry_string += str(event.ascii)

        # Finish
        if event.type in {'RET', 'NUMPAD_ENTER', 'SPACE', 'LEFTMOUSE', 'TAB'} and event.value == 'PRESS':
            self.__set_value(self.entry_string)

            # Unlock / Set
            self.text = self.__get_value()
            db.locked_element = None
            self.entry_string = ""
            self.__remove_timer(context)

        # Edit
        elif event.type == 'BACK_SPACE' and event.value == 'PRESS':
            if event.ctrl:
                self.entry_string = ""
            else:
                self.entry_string = self.entry_string[:-1]


    def __get_value(self):
        val = getattr(self.obj, self.attr)
        return str(val)


    def __set_value(self, val):
        setattr(self.obj, self.attr, val)


    def draw(self, db):
        render_quad(self.dims.quad(), color=self.bg_color)

        color = self.__faded_color()
        draw_border_lines(self.dims.quad(), color=color)

        text = self.entry_string if self.locked else self.text
        render_text(text, (self.dims.x_pos, self.dims.y_pos), self.font_size, self.font_color)


    def __faded_color(self):
        if self.locked:
            self.alpha = sin(time.time() * 10)
            return (self.border_color[0], self.border_color[1], self.border_color[2], self.alpha)

        return self.border_color


    def draw_tips(self, db):
        if self.tips and self.mouse_over:
            self.tips.draw()


    def shut_down(self, context):
        self.__remove_timer(context)


    def __remove_timer(self, context):
        if self.timer:
            context.window_manager.event_timer_remove(self.timer)
            self.timer = None