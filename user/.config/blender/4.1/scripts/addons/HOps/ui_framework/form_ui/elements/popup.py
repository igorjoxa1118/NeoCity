import bpy
from bpy.types import Image
from ....utility.screen import dpi_factor
from ... graphics.draw import render_text, draw_border_lines, render_quad
from ... utils.geo import get_blf_text_dims
from ... utils.checks import is_mouse_in_quad
from ..form import Row
from . import Dims


class Popup:
    def __init__(self, update_func=None, update_args=None):
        self.dims = Dims()
        self.rows = []
        self.bg_color = (0,0,0,1)
        self.border_color = (0,0,0,1)
        self.update_func = update_func
        self.update_args = update_args
        self.needs_rebuild = False


    def row(self):
        return Row()


    def row_insert(self, row, label='', active=True):
        self.rows.append(row)
        row.label = label
        row.active = active


    def row_activation(self, label='', active=True):
        for row in self.rows:
            if row.label == label:
                row.active = active


    def get_row_status(self, label=''):
        for row in self.rows:
            if row.label == label:
                return row.active
        return False


    def trigger_rebuild(self):
        self.needs_rebuild = True


    def build(self, db, x_offset, h_offset):

        self.bg_color = (db.color.tips_background[0], db.color.tips_background[1], db.color.tips_background[2], 1)
        self.border_color = db.color.mods_highlight

        bot_left = (x_offset, h_offset)

        h_offset = bot_left[1]
        for row in reversed(self.rows):
            if row.active == False: continue

            x_offset = bot_left[0]

            max_height = 0
            for elem in row.elements:
                elem.build(db, x_offset, h_offset)
                x_offset += elem.dims.max_width
                max_height = elem.dims.max_height if elem.dims.max_height > max_height else max_height

            h_offset += max_height

        # Get overall dims
        max_w = 0
        max_h = 0
        for row in reversed(self.rows):
            if row.active == False: continue

            w = sum([e.dims.max_width for e in row.elements])
            if w > max_w: max_w = w

            h = 0
            for elem in row.elements:
                h = elem.dims.max_height if elem.dims.max_height > h else h

            max_w = w if w > max_w else max_w
            max_h += h

        # Set dims
        pad = self.dims.padding
        self.dims.bot_left  = (bot_left[0] - pad        , bot_left[1] - pad)
        self.dims.top_left  = (bot_left[0] - pad        , bot_left[1] + max_h + pad)
        self.dims.top_right = (bot_left[0] + pad + max_w, bot_left[1] + max_h + pad)
        self.dims.bot_right = (bot_left[0] + pad + max_w, bot_left[1] - pad)

        self.dims.max_width = abs(self.dims.bot_right[0] - self.dims.bot_left[0])
        self.dims.max_height = abs(self.dims.top_left[1] - self.dims.bot_left[1])


    def locked_update(self, context, event, db):

        if self.needs_rebuild:
            self.needs_rebuild = False
            self.build(db, x_offset=self.dims.bot_left[0] + self.dims.padding, h_offset=self.dims.bot_left[1] + self.dims.padding)

        self.mouse_over = is_mouse_in_quad(self.dims.quad(), db.mouse_pos, tolerance=-1)

        # Locked Element
        if db.locked_element:
            db.locked_element.locked_update(context, event, db)
            if db.locked_element: return

        # Exit Popup
        if not self.mouse_over and not db.locked_element:
            db.locked_popup = None
            return

        # Update elements
        for row in self.rows:
            if row.active == False: continue

            for elem in row.elements:
                elem.update(context, event, db)

        if self.update_func:
            if self.update_args:
                self.update_func(*self.update_args)
            else:
                self.update_func()


    def draw(self, db):

        # Background
        render_quad(self.dims.quad(), color=self.bg_color)
        draw_border_lines(self.dims.quad(), width=3, color=self.border_color)

        # Elements
        for row in self.rows:
            if row.active == False: continue

            for elem in row.elements:
                if elem != db.locked_element:
                    elem.draw(db)
        
        # Tips
        for row in self.rows:
            if row.active == False: continue
            for elem in row.elements:
                if elem != db.locked_element:
                    elem.draw_tips(db)

        if db.locked_element:
            db.locked_element.draw(db)


    def draw_tips(self, db): pass


    def shut_down(self, context): pass