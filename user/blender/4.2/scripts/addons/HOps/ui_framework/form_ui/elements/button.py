import re
import bpy
from ....utility.screen import dpi_factor
from ... graphics.draw import render_text, draw_border_lines, render_quad, render_image
from ... graphics.load import load_image_file
from ... utils.geo import get_blf_text_dims
from ... utils.checks import is_mouse_in_quad
from . import Dims, Tips, clear_img_group, image_group


'''
obj / attr
    - Use this for simple boolean types
attr_index
    - if the item in the list is a (BOOL) use this to specify the slot to get / set
'''


class Button:
    def __init__(self,
        text="", shift_text="", highlight_text="", ctrl_text="", alt_text="",
        width=0, height=0, use_padding=True,
        tips=None, tip_size=12,
        font_size=12, font_primary=True,
        scroll_enabled=True,
        img="", glob_img_key=None, glob_img_key_update_func=None, glob_img_key_update_args=None,
        shift_img="",
        callback=None, pos_args=None, neg_args=None,
        alt_callback=None, alt_args=None,
        ctrl_callback=None, ctrl_args=None,
        highlight_hook=None, highlight_hook_args=None, highlight_hook_obj=None, highlight_hook_attr=None,
        shift_ctrl_callback=None, shift_ctrl_args=None,
        popup=None, popup_modifier_key='',
        obj=None, attr="", attr_index=None):
        
        self.dims = Dims()
        self.text = text
        self.shift_text = shift_text
        self.highlight_text = highlight_text
        self.alt_text = alt_text
        self.width = width * dpi_factor(min=0.5)
        self.height = height * dpi_factor(min=0.5)
        self.font_primary = font_primary
        self.font_size = font_size
        self.scroll_enabled = scroll_enabled
        self.img = img
        self.shift_img_name = shift_img
        self.shift_img = None
        self.loaded_img = None
        self.glob_img_key = glob_img_key
        self.glob_img_key_update_func = glob_img_key_update_func
        self.glob_img_key_update_args = glob_img_key_update_args
        self.callback = callback
        self.pos_args = pos_args
        self.neg_args = neg_args
        self.alt_callback = alt_callback
        self.alt_args = alt_args
        self.ctrl_callback = ctrl_callback
        self.ctrl_args = ctrl_args
        self.ctrl_text = ctrl_text
        self.tips = Tips(tips, tip_size) if tips else None
        self.highlight_hook = highlight_hook
        self.highlight_hook_args = highlight_hook_args
        self.highlight_hook_obj = highlight_hook_obj
        self.highlight_hook_attr = highlight_hook_attr
        self.use_padding = use_padding
        self.shift_ctrl_callback = shift_ctrl_callback
        self.shift_ctrl_args = shift_ctrl_args
        self.popup = popup
        self.popup_modifier_key = popup_modifier_key
        self.obj = obj
        self.attr = attr
        self.attr_index = attr_index
        self.font_color = (0,0,0,1)
        self.bg_color = (0,0,0,1)
        self.border_color = (0,0,0,1)
        self.mouse_over = False


    def build(self, db, x_offset, h_offset):
        self.font_color = db.color.text
        self.bg_color = db.color.cell_background
        self.border_color = db.color.border
        self.__highlight_hook_color(db)

        if self.img and not self.loaded_img:
            self.loaded_img = load_image_file(self.img)
        
        if self.shift_img_name:
            if not self.shift_img:
                self.shift_img = load_image_file(self.shift_img_name)

        pad = self.dims.padding

        text_w = 0
        text_h = 0
        if self.text:
            text_w = get_blf_text_dims(self.text, self.font_size)[0]
            text_h = get_blf_text_dims('SAMPLE', self.font_size)[1]

        # Image Group
        group = image_group()
        if self.glob_img_key and group:
            if self.glob_img_key in group:
                if type(group[self.glob_img_key]) == bpy.types.Image:
                    self.loaded_img = group[self.glob_img_key]

        # Image
        if self.loaded_img:
            if self.width:
                self.dims.max_width = self.width
                h = self.height if self.height else self.width
                self.dims.max_height = h
            else:
                y_dim = get_blf_text_dims("X", self.font_size)[1]
                self.dims.max_width = y_dim + pad * 2
                self.dims.max_height = y_dim + pad * 2

        # Manual Width
        elif self.width:
            self.dims.max_width = self.width
            h = self.height if self.height else text_h
            self.dims.max_height = h + pad * 2 if self.use_padding else h

        # Font Width
        else:
            self.dims.max_width = text_w + pad * 2
            h = self.height if self.height else text_h
            self.dims.max_height = h + pad * 2 if self.use_padding else h

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

        # Image Key
        self.__image_key_callback()

        # Color
        self.__set_color(event, db)

        # Not over button
        if not self.mouse_over: return

        # Attributes
        if db.clicked or db.increment:
            valid = True
            
            if self.scroll_enabled == False and db.increment:
                valid = False
            
            if valid:    
                if self.__attribute_setter(): return

        # No default call back
        if not self.callback: return

        # Scroll Event
        if db.increment:
            if self.scroll_enabled:
                self.__scroll_event(event, db)
        # Click Event
        elif db.clicked:
            self.__click_event(event, db)


    def __image_key_callback(self):
        if self.glob_img_key_update_func:
            key = None
            if self.glob_img_key_update_args:
                key = self.glob_img_key_update_func(*self.glob_img_key_update_args)
            else:
                key = self.glob_img_key_update_func()
            if type(key) == str:
                self.change_image_group_key(key=key)


    def __set_color(self, event, db):
        self.border_color = db.color.border

        # Attributes
        if self.__obj_attr_colors(db): return True
        
        if self.__highlight_hook_color(db): return

        if self.mouse_over:
            self.bg_color = db.color.mouse_over
            if event.shift:
                self.border_color = db.color.mods_highlight
        else:
            self.bg_color = db.color.cell_background


    def __highlight_hook_color(self, db):

        if self.highlight_hook:

            if self.highlight_hook_args:
                if self.highlight_hook(*self.highlight_hook_args):
                    self.border_color = db.color.mods_highlight
                    self.bg_color = db.color.cell_background
                    return True
            else:
                if self.highlight_hook():
                    self.border_color = db.color.mods_highlight
                    self.bg_color = db.color.cell_background
                    return True

        if self.highlight_hook_obj:
            if self.highlight_hook_attr:
                if hasattr(self.highlight_hook_obj, self.highlight_hook_attr):
                    val = getattr(self.highlight_hook_obj, self.highlight_hook_attr)
                    if val: self.border_color = db.color.mods_highlight
                    else: self.border_color = db.color.border

        if self.__obj_attr_colors(db): return True

        return False


    def __obj_attr_colors(self, db):
        if not self.obj: return False
    
        if not hasattr(self.obj, self.attr): return False
    
        val = getattr(self.obj, self.attr)
        if self.attr_index != None:
            val = val[self.attr_index]
        if val: self.border_color = db.color.mods_highlight
        else: self.border_color = db.color.border
        return True
    

    def __scroll_event(self, event, db):
        if db.increment > 0:
            if self.pos_args: self.callback(*self.pos_args)
            else: self.callback()
        elif db.increment < 0:
            if self.neg_args: self.callback(*self.neg_args)
            else: self.callback()


    def __click_event(self, event, db):

        if self.__popup(event, db): return

        # CTRL SHIFT
        if event.shift and event.ctrl:
            if self.shift_ctrl_callback:
                if self.shift_ctrl_args:
                    self.shift_ctrl_callback(*self.shift_ctrl_args)
                else:
                    self.shift_ctrl_callback()

        # SHIFT
        if event.shift:
            if self.neg_args:
                self.callback(*self.neg_args)
                return

        # ALT
        elif event.alt:
            if self.alt_callback:
                if self.alt_args:
                    self.alt_callback(*self.alt_args)
                else:
                    self.alt_callback()
                return

        # CTRL
        elif event.ctrl:
            if self.ctrl_callback:
                if self.ctrl_args:
                    self.ctrl_callback(*self.ctrl_args)
                else:
                    self.ctrl_callback()
                return

        # --- Not modifier keys --- #

        # Call positive version : with args
        if self.pos_args:
            self.callback(*self.pos_args)
            return

        # Call standard
        if not self.pos_args and not self.neg_args:
            self.callback()


    def __popup(self, event, db):
        if not self.popup: return False

        setup = False
        if self.popup_modifier_key == 'SHIFT':
            if event.shift == True and event.ctrl == False and event.alt == False:
                setup = True
        elif self.popup_modifier_key == 'CTRL':
            if event.shift == False and event.ctrl == True and event.alt == False:
                setup = True
        elif self.popup_modifier_key == 'ALT':
            if event.shift == False and event.ctrl == False and event.alt == True:
                setup = True
        elif self.popup_modifier_key == '':
            if event.shift == False and event.ctrl == False and event.alt == False:
                setup = True
        if not setup: return False

        self.popup.build(db, x_offset=db.mouse_pos[0], h_offset=db.mouse_pos[1])
        db.locked_popup = self.popup
        return True


    def __attribute_setter(self):
        if not self.obj: return False
        if not hasattr(self.obj, self.attr): return False
        val = getattr(self.obj, self.attr)

        if self.attr_index != None:
            val = val[self.attr_index]
            if type(val) != bool: return False
            item = getattr(self.obj, self.attr)
            item[self.attr_index] = not val
            setattr(self.obj, self.attr, item)
            return True

        else:
            if type(val) != bool: return False
            setattr(self.obj, self.attr, not val)
            return True
        

    def change_image_group_key(self, key=''):
        '''Update the active image'''

        group = image_group()
        if not group: return
        if key in group:
            if type(group[key]) == bpy.types.Image:
                self.loaded_img = group[key]
                self.glob_img_key = key


    def draw(self, db):
        render_quad(self.dims.quad(), color=self.bg_color)
        draw_border_lines(self.dims.quad(), color=self.border_color)

        if db.shift and self.shift_img:
            render_image(self.shift_img, self.dims.img_quad())

        elif self.loaded_img:
            render_image(self.loaded_img, self.dims.img_quad())

        text = self.shift_text if db.shift and self.shift_text else self.text
        text = self.highlight_text if self.border_color == db.color.mods_highlight and self.highlight_text else text
        text = self.ctrl_text if db.ctrl and self.ctrl_text else text
        text = self.alt_text if db.alt and self.alt_text else text

        render_text(text, (self.dims.x_pos, self.dims.y_pos), self.font_size, self.font_color)


    def draw_tips(self, db):
        if self.tips and self.mouse_over:
            self.tips.draw()


    def shut_down(self, context):
        clear_img_group()

        if self.shift_img:
            try: bpy.data.images.remove(self.shift_img)
            except: pass

        if not self.loaded_img: return
        try: bpy.data.images.remove(self.loaded_img)
        except: pass