from ....utility.screen import dpi_factor
from ... graphics.draw import render_text
from ... utils.geo import get_blf_text_dims
from . import Dims


class Label:
    def __init__(self, text="", font_primary=True, font_size=12, width=0, height=0):
        self.dims = Dims()
        self.text = text
        self.font_primary = font_primary
        self.font_size = font_size
        self.width = width * dpi_factor(min=0.5)
        self.height = height * dpi_factor(min=0.5)
        self.font_color = (0,0,0,1)


    def build(self, db, x_offset, h_offset):
        self.font_color = db.color.text if self.font_primary else db.color.secondary_text

        dims = get_blf_text_dims(self.text, self.font_size)
        pad = self.dims.padding

        # Use width
        if self.width:
            self.dims.max_width = self.width
        # Use text
        else:
            self.dims.max_width = dims[0] + pad * 2

        # Use height
        if self.height:
            self.dims.max_height = self.height
        # Use text
        else:
            self.dims.max_height = dims[1] + pad * 2

        self.dims.x_pos = x_offset + pad
        self.dims.y_pos = h_offset + pad


    def update(self, context, event, db): pass


    def draw(self, db):
        render_text(self.text, (self.dims.x_pos, self.dims.y_pos), self.font_size, self.font_color)


    def draw_tips(self, db): pass
    def shut_down(self, context): pass