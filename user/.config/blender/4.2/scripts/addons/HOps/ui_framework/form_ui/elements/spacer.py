from . import Dims
from ....utility.screen import dpi_factor
from ... graphics.draw import draw_2D_lines

class Spacer:
    def __init__(self, width=0, height=0, draw_bar=False):
        self.dims = Dims()
        self.width = width * dpi_factor(min=0.5)
        self.height = height * dpi_factor(min=0.5)
        self.draw_bar = draw_bar
        self.bar_color = (0,0,0,0)
        self.bar_verts = []


    def build(self, db, x_offset, h_offset):

        self.bar_color = db.color.border

        self.dims.max_width = self.width
        self.dims.max_height = self.height

        self.dims.bot_left  = (x_offset, h_offset)
        self.dims.top_left  = (x_offset, h_offset + self.dims.max_height)
        self.dims.top_right = (x_offset + self.dims.max_width, h_offset + self.dims.max_height)
        self.dims.bot_right = (x_offset + self.dims.max_width, h_offset)

        height = abs(self.dims.top_left[1] - self.dims.bot_left[1])
        mid_y = self.dims.bot_left[1] + height * .5
        self.bar_verts = [
            (self.dims.bot_left[0], mid_y),
            (self.dims.bot_right[0], mid_y)]


    def update(self, context, event, db): pass


    def draw(self, db):
        if not self.draw_bar: return

        draw_2D_lines(vertices=self.bar_verts, width=3, color=self.bar_color)


    def draw_tips(self, db): pass
    def shut_down(self, context): pass