import bpy, time, math, numpy
from math import sin
from mathutils import Vector
from ....utility.screen import dpi_factor
from ... graphics.load import load_image_file
from ... graphics.draw import render_text, draw_border_lines, render_quad, draw_2D_lines
from ... utils.geo import get_blf_text_dims
from ... utils.checks import is_mouse_in_quad
from . import Dims, Tips


class Taps:
    def __init__(self, font_color, bg_color, border_color, tag=""):
        self.dims = Dims()
        self.font_color = font_color
        self.bg_color = bg_color
        self.border_color = border_color
        self.tag = tag
        self.verts = []


    def draw(self):
        render_quad(self.dims.quad(), color=self.bg_color)
        draw_border_lines(self.dims.quad(), color=self.border_color)
        draw_2D_lines(self.verts, width=2, color=self.font_color)


'''
decimal_draw_precision
    - pass an INT in this param to clamp the drawing percision (doesnt effect the actual setter)
handle_radians
    - when true, this will display the values to the screen in degrees (does not alter the increment)
attr_index
    - if the item is a list item use this to specify the slot to get / set
'''


class Input:
    def __init__(self,
        obj=None, attr="", font_size=12, width=50, height=0,
        tips=None, tip_size=12, limit=6, increment=.5, use_mod_keys=True,
        on_active_callback=None, ctrl_scroll_callback=None,
        decimal_draw_precision=None, handle_radians=False,
        attr_index=None):
        
        self.dims = Dims()
        self.font_color = (0,0,0,1)
        self.bg_color = (0,0,0,1)
        self.border_color = (0,0,0,1)
        self.obj = obj
        self.attr = attr
        self.font_size = font_size
        self.width = width * dpi_factor(min=0.5)
        self.height = height * dpi_factor(min=0.5)
        self.limit = limit
        self.increment = increment
        self.use_mod_keys = use_mod_keys
        self.text = ""
        self.tips = Tips(tips, tip_size) if tips else None
        self.mouse_over = False
        self.on_active_callback = on_active_callback
        self.ctrl_scroll_callback = ctrl_scroll_callback
        self.decimal_draw_precision = decimal_draw_precision
        self.handle_radians = handle_radians
        self.attr_index = attr_index
        # Drag
        self.drag_was_used = False
        self.test_for_drag = True
        self.click_loc = (0,0)
        self.track_dist = 0
        self.drag_dist = 0
        # Taps
        self.taps = []
        self.using_taps = False
        self.shift_pressed_on_entry = False
        # Double Click
        self.click_time = 0
        self.double_click_duration = .25
        # Notify
        self.timer = None
        self.locked = False
        self.alpha = 1
        # Input
        self.entry_string = ""
        self.tabbed_finish = False


    def build(self, db, x_offset, h_offset):
        self.font_color = db.color.text
        self.bg_color = db.color.cell_background
        self.border_color = db.color.border

        if self.obj == None or self.attr == "": return

        self.text = self.__get_value(use_convert=True, as_string=True)
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

        # Taps
        self.taps = []
        bg_color = (db.color.mouse_over[0], db.color.mouse_over[1], db.color.mouse_over[2], 1)
        width = abs(self.dims.top_left[1] - self.dims.bot_left[1])
        bot_x = self.dims.bot_left[0]
        bot_y = self.dims.bot_left[1]
        
        #--- LEFT ---#
        tap = Taps(font_color=db.color.text, bg_color=bg_color, border_color=db.color.mods_highlight, tag="LEFT")
        dims = tap.dims
        dims.bot_left  = (bot_x - width, bot_y)
        dims.top_left  = (bot_x - width, bot_y + width)
        dims.top_right = (bot_x, bot_y + width)
        dims.bot_right = (bot_x, bot_y)

        pad = width * .25
        tap.verts = [
            (bot_x - width + pad, bot_y + width * .5), # Tip
            (bot_x - pad, bot_y + pad),
            (bot_x - pad, bot_y + width - pad),
            (bot_x - width + pad, bot_y + width * .5)] # Tip

        self.taps.append(tap)

        #--- RIGHT ---#
        bot_x = self.dims.bot_right[0]

        tap = Taps(font_color=db.color.text, bg_color=bg_color, border_color=db.color.mods_highlight, tag="RIGHT")
        dims = tap.dims
        dims.bot_left  = (bot_x, bot_y)
        dims.top_left  = (bot_x, bot_y + width)
        dims.top_right = (bot_x + width, bot_y + width)
        dims.bot_right = (bot_x + width, bot_y)

        pad = width * .25
        tap.verts = [
            (bot_x + pad, bot_y + pad), # Bottom
            (bot_x + width - pad, bot_y + width * .5), # Tip
            (bot_x + pad, bot_y + width - pad),
            (bot_x + pad, bot_y + pad)]

        self.taps.append(tap)

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
        self.text = self.__get_value(use_convert=True, as_string=True)


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
            # Drag testing
            self.drag_was_used = False
            self.test_for_drag = True
            self.click_loc = (event.mouse_region_x, event.mouse_region_y)
            self.track_dist = 0
            self.drag_dist = 0
            # Taps
            self.shift_pressed_on_entry = event.shift
            # Double Click
            self.click_time = time.time()
            # Notify
            self.notified_of_entry = False
            # Locked State
            db.locked_element = self
            self.entry_string = ""
            self.tabbed_finish = False

        # Scroll : Up
        elif db.increment > 0:
            self.__on_active_callback()
            self.__ctrl_scroll(event)

            val = self.__get_value()
            if event.shift:
                self.__set_value(val + self.increment * .1)
            elif event.alt:
                self.__set_value(val * 2)
            else:
                self.__set_value(val + self.increment)

            self.__ctrl_scroll(event, before=False)

        # Scroll : Down
        elif db.increment < 0:
            self.__on_active_callback()
            self.__ctrl_scroll(event)

            val = self.__get_value()
            if event.shift:
                self.__set_value(val - self.increment * .1)
            elif event.alt:
                self.__set_value(val / 2)
            else:
                self.__set_value(val - self.increment)
                
            self.__ctrl_scroll(event, before=False)


    def __on_active_callback(self):
        if self.on_active_callback:
            self.on_active_callback()


    def __ctrl_scroll(self, event, before=True):
        if event.ctrl and self.ctrl_scroll_callback:
            if before:
                self.ctrl_scroll_callback(opt='before')
            else:
                self.ctrl_scroll_callback(opt='after')


    def locked_update(self, context, event, db):

        self.locked = True

        # Test for mouse drag event first
        if self.test_for_drag:
            if event.value != 'RELEASE':
                self.drag_dist = (Vector(self.click_loc) - Vector((event.mouse_region_x, event.mouse_region_y))).magnitude
                if self.drag_dist > 5:
                    self.drag_was_used = True
                    self.__drag(context, event, db)
                    return
            else:
                # Clear out drag event after use
                self.test_for_drag = False
                if self.drag_was_used:
                    db.locked_element = None
                    self.entry_string = ""
                    return

                # Set for taps
                if self.shift_pressed_on_entry:
                    self.using_taps = True

                self.timer = context.window_manager.event_timer_add(0.025, window=context.window)

        # Double click
        if not self.using_taps:
            if db.clicked:
                if time.time() - self.click_time < self.double_click_duration:
                    self.using_taps = True
                    return

        # Set highlight color during focus mode
        self.border_color = db.color.mods_highlight

        if self.using_taps:
            self.__taps(context, event, db)
            return

        valid = {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '.', '-'}

        if event.ascii in valid and event.value == 'PRESS':
            # Decimal
            decimal_blocked = False
            if '.' in self.entry_string and event.ascii == '.':
                decimal_blocked = True
            
            # Append text
            if decimal_blocked == False:
                if len(self.entry_string) <= self.limit:
                    self.entry_string += str(event.ascii)

            # Negative
            if self.entry_string.count('-') > 1:
                self.entry_string = self.entry_string.replace('-', '')
            elif self.entry_string.count('-') == 1:
                self.entry_string = self.entry_string.replace('-', '')
                self.entry_string = '-' + self.entry_string

        # Finish
        if event.type in {'RET', 'NUMPAD_ENTER', 'SPACE', 'LEFTMOUSE', 'TAB'} and event.value == 'PRESS':
            if event.type == 'TAB':
                self.tabbed_finish = True

            if self.entry_string != "":
                value = None
                try:
                    value = float(self.entry_string) if self.entry_string else 0
                except: pass

                if value != None:
                    if self.handle_radians:
                        value = math.radians(value)

                    self.__set_value(value)

            # Unlock / Set
            self.text = self.__get_value(use_convert=True, as_string=True)
            db.locked_element = None
            self.entry_string = ""
            self.__remove_timer(context)

        # Edit
        elif event.type == 'BACK_SPACE' and event.value == 'PRESS':
            self.entry_string = self.entry_string[:-1]


    def __drag(self, context, event, db):
        
        if abs(self.drag_dist - self.track_dist) > 10 * dpi_factor(min=0.5):
            self.track_dist = self.drag_dist
            value = float(self.__get_value())

            if event.mouse_x > event.mouse_prev_x:
                if event.shift and self.use_mod_keys:
                    value += self.increment * .1
                else:
                    value += self.increment
            else:
                if event.shift and self.use_mod_keys:
                    value -= self.increment * .1
                else:
                    value -= self.increment

            self.__set_value(value)
            self.text = self.__get_value(use_convert=True, as_string=True)


    def __taps(self, context, event, db):
        
        mouse_over_any = False
        for tap in self.taps:
            mouse_over = is_mouse_in_quad(tap.dims.quad(), db.mouse_pos)

            if mouse_over_any == False and mouse_over:
                mouse_over_any = True

            if mouse_over and db.clicked:
                if tap.tag == "LEFT":
                    val = self.__get_value()

                    if event.shift and self.use_mod_keys:
                        val -= self.increment * .1
                    else:
                        val -= self.increment

                    self.__set_value(val)
                    self.text = self.__get_value(use_convert=True, as_string=True)

                elif tap.tag == "RIGHT":
                    val = self.__get_value()

                    if event.shift and self.use_mod_keys:
                        val += self.increment * .1
                    else:
                        val += self.increment

                    self.__set_value(val)

                    self.text = self.__get_value(use_convert=True, as_string=True)

        # Click off : Reset
        if mouse_over_any == False and db.clicked:
            self.using_taps = False
            db.locked_element = None
            self.__remove_timer(context)


    def __get_value(self, use_convert=False, as_string=False):
        val = getattr(self.obj, self.attr)

        if self.attr_index != None:
            val = val[self.attr_index]

        if self.handle_radians and use_convert:
            if type(val) in {float, int}:
                val = round(math.degrees(val))

        if as_string:
            if type(val) == float:
                return numpy.format_float_positional(val, trim='-')
            return str(val)
                
        return val


    def __set_value(self, val):
        if self.attr_index != None:
            item = getattr(self.obj, self.attr)
            item[self.attr_index] = val
            val = item
        setattr(self.obj, self.attr, val)


    def draw(self, db):
        render_quad(self.dims.quad(), color=self.bg_color)

        color = self.__faded_color()
        draw_border_lines(self.dims.quad(), color=color)

        if self.using_taps:
            self.__draw_taps()
            return

        text = self.entry_string if self.entry_string else self.text
        
        text = self.__decimal_clamped_text(text)

        render_text(text, (self.dims.x_pos, self.dims.y_pos), self.font_size, self.font_color)


    def draw_tips(self, db):
        if self.tips and self.mouse_over:
            self.tips.draw()


    def __faded_color(self):
        if self.locked and not self.test_for_drag and not self.using_taps:
            self.alpha = sin(time.time() * 10)
            return (self.border_color[0], self.border_color[1], self.border_color[2], self.alpha)

        return self.border_color


    def __draw_taps(self):

        text = self.__decimal_clamped_text(self.text)

        render_text(text, (self.dims.x_pos, self.dims.y_pos), self.font_size, self.font_color)

        for tap in self.taps:
            tap.draw()


    def __decimal_clamped_text(self, text):
        if self.decimal_draw_precision == None: return text
        if '.' not in text: return text

        split = text.split('.') 
        if self.decimal_draw_precision == 0:
            return split[0]
        else:
            return f'{split[0]}.{split[1][:self.decimal_draw_precision]}'


    def shut_down(self, context):
        self.__remove_timer(context)


    def __remove_timer(self, context):
        if self.timer:
            context.window_manager.event_timer_remove(self.timer)