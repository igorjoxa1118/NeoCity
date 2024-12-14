from ...utility.screen import dpi_factor
from .. graphics.draw import render_quad, render_geo, render_text, draw_border_lines
from .. utils.geo import get_blf_text_dims

'''
Callback param must accept one param : it will recieve the string
'''


class Dialogue:

    def __init__(self, context, callback=None, help_text=""):
        self.active = False
        self.string = ""
        self.help_text = help_text
        self.callback = callback
        self.screen_width = context.area.width
        self.screen_height = context.area.height

        self.invalid = {'\\', '/', ':', '*', '?', '"', '<', '>', '|', '.'}
        self.completed = {'LEFTMOUSE', 'RET', 'NUMPAD_ENTER'}
        self.cancel = {'RIGHTMOUSE', 'ESC'}

        self.factor = dpi_factor(min=0.5)


    def start(self):
        self.active = True
        self.string = ""


    def update(self, event):

        # Canceled
        if event.type in self.cancel and event.value == 'PRESS':
            self.active = False
            return

        # Finished
        if event.type in self.completed and event.value == 'PRESS':
            self.active = False
            if self.callback:
                self.callback(self.string)
            return

        # Append
        if event.ascii not in self.invalid and event.value == 'PRESS':
            self.string += event.ascii

        # Backspace
        if event.type == 'BACK_SPACE' and event.value == 'PRESS':
            if event.ctrl:
                self.string = ""
            else:
                self.string = self.string[ : len(self.string) - 1]


    def draw(self):
        if not self.active: return

        help_text_size = 18
        file_text_size = 24

        sample_y = get_blf_text_dims("XyZ`Qq", file_text_size)[1]
        help_text_dims = get_blf_text_dims(self.help_text, help_text_size)
        file_text_dims = get_blf_text_dims(self.string, file_text_size)

        center_x = self.screen_width * .5
        center_y = self.screen_height * .5

        text_padding_y = 30 * self.factor
        text_padding_x = 20 * self.factor

        total_height = text_padding_y * 3 + sample_y + sample_y
        widest_text = help_text_dims[0] if help_text_dims[0] > file_text_dims[0] else file_text_dims[0]
        total_width = text_padding_x * 2 + widest_text

        # TL, BL, TR, BR
        verts = [
            (center_x - total_width * .5, center_y + total_height * .5),
            (center_x - total_width * .5, center_y - total_height * .5),
            (center_x + total_width * .5, center_y + total_height * .5),
            (center_x + total_width * .5, center_y - total_height * .5)]

        render_quad(
            quad=verts,
            color=(0,0,0,.5))

        draw_border_lines(
            vertices=verts,
            width=2,
            color=(0,0,0,.75))

        x_loc = center_x - help_text_dims[0] * .5
        y_loc = center_y - help_text_dims[1] * .5 + file_text_size * self.factor
        render_text(
            text=self.help_text, 
            position=(x_loc, y_loc), 
            size=help_text_size, 
            color=(1,1,1,1))

        x_loc = center_x - file_text_dims[0] * .5
        y_loc = center_y - file_text_dims[1] * .5 - file_text_size * self.factor
        render_text(
            text=self.string, 
            position=(x_loc, y_loc), 
            size=file_text_size, 
            color=(1,1,1,1))
