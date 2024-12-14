import bpy, time
from math import sin
import mathutils
from mathutils import Vector
from .... utility import addon
from ....utility.screen import dpi_factor
from ... graphics.load import load_image_file
from ... graphics.draw import render_text, draw_border_lines, render_quad, draw_2D_lines
from ... utils.geo import get_blf_text_dims
from ... utils.checks import is_mouse_in_quad
from . import Dims, Tips

''' Pref_color : this is so multiple colors can be used at once.  Set this in the form incrementally. '''

class Color:
    def __init__(self, obj=None, attr="", width=50, height=12, tips=None, tip_size=12, pref_color=1, callback=None):
        self.dims = Dims()
        self.color = (0,0,0,1)
        self.border_color = (0,0,0,1)
        self.obj = obj
        self.attr = attr
        self.width = width * dpi_factor()
        self.height = height * dpi_factor()
        self.tips = Tips(tips, tip_size) if tips else None
        self.pref_color = pref_color
        self.callback = callback
        self.mouse_over = False
        self.just_ran_popover = False


    def build(self, db, x_offset, h_offset):
        self.border_color = db.color.border
        self.__set_pref_color()

        if self.obj == None or self.attr == "": return

        pad = self.dims.padding
        self.dims.max_width = self.width
        self.dims.max_height = self.height + pad * 2

        self.dims.bot_left  = (x_offset, h_offset)
        self.dims.top_left  = (x_offset, h_offset + self.dims.max_height)
        self.dims.top_right = (x_offset + self.dims.max_width, h_offset + self.dims.max_height)
        self.dims.bot_right = (x_offset + self.dims.max_width, h_offset)

        self.dims.x_pos = x_offset + pad
        self.dims.y_pos = h_offset + pad

        if self.tips:
            self.tips.build(db, self.dims.top_left[0], self.dims.top_left[1])


    def update(self, context, event, db):
        
        self.mouse_over = is_mouse_in_quad(self.dims.quad(), db.mouse_pos, tolerance=-1)
        if self.tips: self.tips.update()

        # Color
        if self.mouse_over: self.border_color = db.color.mods_highlight
        else: self.border_color = db.color.border

        if self.just_ran_popover:
            # Was set : now set back to tuple to unlink and set class attr to tuple
            if type(self.color) == bpy.types.bpy_prop_array:
                self.color = (self.color[0], self.color[1], self.color[2], self.color[3])
                setattr(self.obj, self.attr, self.color)

            self.__set_pref_color()

            self.just_ran_popover = False
            if self.callback:
                self.callback()

        # Set color : CREATES -> bpy prop array
        if self.mouse_over:
            if db.clicked:
                context.window_manager.popover(self.__color_popup_draw)

                color = addon.preference().color.form_color_prop_1
                if self.pref_color == 2:
                    color = addon.preference().color.form_color_prop_2
                elif self.pref_color == 3:
                    color = addon.preference().color.form_color_prop_3

                setattr(self.obj, self.attr, color)

            elif db.increment:
                val = getattr(self.obj, self.attr)
                alpha = val[3]
                color = mathutils.Color((val[0], val[1], val[2]))
                
                # Hue
                if event.shift:
                    if color.s == 0:
                        color.s = .25

                    if db.increment > 0:
                        color.h += .05
                    else:
                        color.h -= .05
                
                # Saturation
                elif event.ctrl:
                    if db.increment > 0:
                        color.s += .05
                    else:
                        color.s -= .05

                # Value
                else:
                    if db.increment > 0:
                        color.v += .05
                    else:
                        color.v -= .05

                self.color = (color[0], color[1], color[2], alpha)

                setattr(self.obj, self.attr, self.color)
                if self.callback:
                    self.callback()


    def __set_pref_color(self):
        self.color = getattr(self.obj, self.attr)

        if self.pref_color == 1:
            addon.preference().color.form_color_prop_1 = self.color
        elif self.pref_color == 2:
            addon.preference().color.form_color_prop_2 = self.color
        elif self.pref_color == 3:
            addon.preference().color.form_color_prop_3 = self.color


    def draw(self, db):
        render_quad(self.dims.quad(), color=self.color)
        draw_border_lines(self.dims.quad(), color=self.border_color)


    def draw_tips(self, db):
        if self.tips and self.mouse_over:
            self.tips.draw()


    def shut_down(self, context):
        pass


    def __color_popup_draw(self, op, context):
        self.just_ran_popover = True
        if self.pref_color == 1:
            op.layout.prop(addon.preference().color, 'form_color_prop_1', text='')
        elif self.pref_color == 2:
            op.layout.prop(addon.preference().color, 'form_color_prop_2', text='')
        elif self.pref_color == 3:
            op.layout.prop(addon.preference().color, 'form_color_prop_3', text='')