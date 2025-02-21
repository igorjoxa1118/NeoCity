from ....utility.screen import dpi_factor
from ... graphics.draw import render_text, draw_border_lines, render_quad
from ... utils.geo import get_blf_text_dims
from ... utils.checks import is_mouse_in_quad
from . import Dims, Tips


class Option:
    def __init__(self, text, bg_color, border_color):
        self.dims = Dims()
        self.text = text
        self.bg_color = bg_color
        self.border_color = border_color

'''
OBJ / ATTR Usage Notes
If using obj with attr props, do NOT supply : Callback, Update Hook, Additional Args
obj / attr : supplying this will automatically manage setting the attr
USE getter setters to enable callbacks
'''


class Dropdown:
    '''Expects a call back function that takes one arg (the string option selected)\n
        Update Hook is a function that expects a return value to match options (must return string)'''
    
    def __init__(self,
        font_size=12, width=0, tips=None, tip_size=12,
        options=[], callback=None, additional_args=None, index=0,
        update_hook=None, hook_args=None,
        cyclic_scroll=False,
        obj=None, attr=None):

        self.dims = Dims()
        self.font_color = (0,0,0,1)
        self.bg_color = (0,0,0,1)
        self.border_color = (0,0,0,1)
        self.font_size = font_size
        self.width = width * dpi_factor(min=0.5)
        self.options = options
        self.callback = callback
        self.update_hook = update_hook
        self.hook_args = hook_args
        self.cyclic_scroll = cyclic_scroll
        self.tips = Tips(tips, tip_size) if tips else None
        self.additional_args = additional_args
        self.mouse_over = False
        self.obj = obj
        self.attr = attr
        # POP
        self.pop_bg_color = (0,0,0,1)
        self.index = index
        self.draw_pop = False
        self.pop_opts = []
        self.pop_dims = Dims()


    def build(self, db, x_offset, h_offset):
        self.font_color = db.color.text
        self.bg_color = db.color.cell_background
        self.border_color = db.color.border

        self.pop_bg_color = (db.color.cell_background[0], db.color.cell_background[1], db.color.cell_background[2], 1)

        dims = get_blf_text_dims("X", self.font_size)
        pad = self.dims.padding

        # Auto width
        if self.width == 0:
            widest = 0
            for label in self.options:
                if type(label) != str: continue
                temp = get_blf_text_dims(label, self.font_size)[0]
                if temp > widest: widest = temp
            self.width = widest + (pad * 4)

        self.dims.max_width = self.width
        self.dims.max_height = dims[1] + pad * 2

        self.dims.bot_left  = (x_offset, h_offset)
        self.dims.top_left  = (x_offset, h_offset + self.dims.max_height)
        self.dims.top_right = (x_offset + self.dims.max_width, h_offset + self.dims.max_height)
        self.dims.bot_right = (x_offset + self.dims.max_width, h_offset)

        self.dims.x_pos = x_offset + pad
        self.dims.y_pos = h_offset + pad

        # Pop build
        self.pop_opts = []
        self.pop_dims_bg = Dims()

        # Build options
        pad = self.dims.padding * .75
        width = abs(self.dims.bot_right[0] - self.dims.bot_left[0])
        height = abs(self.dims.top_left[1] - self.dims.bot_left[1])
        bot_x = self.dims.bot_left[0]
        bot_y = self.dims.bot_left[1] - height - pad

        for option in self.options:
            opt = Option(text=option, bg_color=db.color.cell_background, border_color=db.color.border)
            dims = opt.dims

            dims.bot_left  = (bot_x + pad, bot_y)
            dims.top_left  = (bot_x + pad, bot_y + height)
            dims.top_right = (bot_x - pad + width, bot_y + height)
            dims.bot_right = (bot_x - pad + width, bot_y)

            dims.x_pos = bot_x + pad * 2
            dims.y_pos = bot_y + pad

            bot_y -= height + pad

            self.pop_opts.append(opt)

        # Remove last loop call
        bot_y += height + pad

        # Pop background
        top_y = self.dims.bot_left[1]

        self.pop_dims.bot_left  = (bot_x, bot_y - pad)
        self.pop_dims.top_left  = (bot_x, top_y)
        self.pop_dims.top_right = (bot_x + width, top_y)
        self.pop_dims.bot_right = (bot_x + width, bot_y - pad)

        if self.tips:
            self.tips.build(db, self.dims.top_left[0], self.dims.top_left[1])


    def update(self, context, event, db):
        self.draw_pop = False
        if self.tips: self.tips.update()

        # Update hook
        if self.update_hook:
            if self.hook_args:
                val = self.update_hook(*self.hook_args)
            else:
                val = self.update_hook()
            if val in self.options:
                self.index = self.options.index(val)
        
        elif self.obj != None and self.attr != None:
            if hasattr(self.obj, self.attr):
                val = getattr(self.obj, self.attr)
                if val in self.options:
                    self.index = self.options.index(val)

        self.index_ensure()
        
        self.mouse_over = is_mouse_in_quad(self.dims.quad(), db.mouse_pos, tolerance=-1)

        # Color
        self.border_color = db.color.border
        if self.mouse_over:
            self.bg_color = db.color.mouse_over
        else:
            self.bg_color = db.color.cell_background

        # Clicked
        if self.mouse_over and db.clicked:
            db.locked_element = self
            return

        # Scrolled
        if self.mouse_over and db.increment:
            if db.increment > 0:
                self.index += 1

                if self.index > len(self.options) - 1:
                    if self.cyclic_scroll:
                        self.index = 0
                    else:
                        self.index = len(self.options) - 1

            elif db.increment < 0:
                self.index -= 1

                if self.index < 0:
                    if self.cyclic_scroll:
                        self.index = len(self.options) - 1
                    else:
                        self.index = 0

            # OBJ ATTR Version
            if self.obj != None and self.attr != None:
                if hasattr(self.obj, self.attr):
                    setattr(self.obj, self.attr, self.options[self.index])

            # Callback Version
            if self.callback == None: return
            if self.additional_args:
                self.callback(self.options[self.index], *self.additional_args)
            else:
                self.callback(self.options[self.index])


    def index_ensure(self):
        if self.index > len(self.options) - 1:
            self.index = len(self.options) - 1
        elif self.index < 0:
            self.index = 0


    def locked_update(self, context, event, db):

        # Validate
        if self.callback == None and self.obj == None and self.attr == None:
            db.locked_element = None
            self.draw_pop = False
            return

        self.draw_pop = True
        mouse_over_any = False

        for index, opt in enumerate(self.pop_opts):
            mouse_over = is_mouse_in_quad(opt.dims.quad(), db.mouse_pos)

            if mouse_over_any == False and mouse_over:
                mouse_over_any = True

            # Colors
            if mouse_over:
                opt.bg_color = db.color.mouse_over
                opt.border_color = db.color.mods_highlight
            else:
                opt.bg_color = db.color.cell_background
                opt.border_color = db.color.border

            # Event
            if mouse_over and db.clicked:
                self.index = index

                # OBJ ATTR Version
                if self.obj != None and self.attr != None:
                    if hasattr(self.obj, self.attr):
                        setattr(self.obj, self.attr, self.options[self.index])
                        self.__close_pop(db)
                        return

                # Callback Version
                if self.additional_args:
                    self.callback(self.options[self.index], *self.additional_args)
                else:
                    self.callback(self.options[self.index])
                self.__close_pop(db)
                return

        # Click off : Reset
        if mouse_over_any == False and db.clicked:
            self.__close_pop(db)


    def __close_pop(self, db):
        for opt in self.pop_opts:
            opt.bg_color = db.color.cell_background
            opt.border_color = db.color.border

        db.locked_element = None
        self.draw_pop = False


    def draw(self, db):
        render_quad(self.dims.quad(), color=self.bg_color)
        draw_border_lines(self.dims.quad(), color=self.border_color)

        render_text(self.options[self.index], (self.dims.x_pos, self.dims.y_pos), self.font_size, self.font_color)

        # Start drawing POP
        if not self.draw_pop: return

        render_quad(self.pop_dims.quad(), color=self.pop_bg_color)
        draw_border_lines(self.pop_dims.quad(), color=self.border_color)

        for opt in self.pop_opts:
            render_quad(opt.dims.quad(), color=opt.bg_color)
            draw_border_lines(opt.dims.quad(), color=opt.border_color)

            render_text(opt.text, (opt.dims.x_pos, opt.dims.y_pos), self.font_size, self.font_color)    


    def draw_tips(self, db):
        if self.tips and self.mouse_over:
            self.tips.draw()


    def shut_down(self, context):
        pass