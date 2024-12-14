import bpy
from ....utility.screen import dpi_factor
from ... graphics.draw import render_text, draw_border_lines, render_quad
from ... graphics.load import load_image_file
from ... utils.geo import get_blf_text_dims


'''
IMAGE NOTES  ::  
img=""                        : Use single image thats instanced per button
glob_img_key=None             : The key to use to access GLOB_IMG_GROUP with (Global level instance)
glob_img_key_update_func=None : This function should return the access key for GLOB_IMG_GROUP 
glob_img_key_update_args=None : Args to unpack into glob_img_key_update_func if needed 
'''


GLOB_IMG_GROUP = {}


def setup_image_group(img_names=[]):
  
    global GLOB_IMG_GROUP
    GLOB_IMG_GROUP = {}

    if not img_names: return

    for name in img_names:

        if name in GLOB_IMG_GROUP:
            # Set junk to None Type
            if type(GLOB_IMG_GROUP[name]) != bpy.types.Image:
                GLOB_IMG_GROUP[name] = None
            # Already loaded
            else: continue

        img = load_image_file(name)
        if img:
            GLOB_IMG_GROUP[name] = img
        else:
            GLOB_IMG_GROUP[name] = None


def image_group():
    global GLOB_IMG_GROUP
    return GLOB_IMG_GROUP


def clear_img_group():
    global GLOB_IMG_GROUP
    if GLOB_IMG_GROUP:
        for key, img in GLOB_IMG_GROUP.items():
            if type(img) != bpy.types.Image: continue
            try: bpy.data.images.remove(img)
            except: pass
    GLOB_IMG_GROUP = {}


class Dims:
    def __init__(self):
        # Bounds
        self.bot_left  = (0,0)
        self.top_left  = (0,0)
        self.top_right = (0,0)
        self.bot_right = (0,0)
        # Spacing
        self.padding = 6 * dpi_factor(min=0.5)
        # Max
        self.max_height = 0
        self.max_width = 0
        # Text
        self.x_pos = 0
        self.y_pos = 0


    def quad(self):
        return (self.top_left, self.bot_left, self.top_right, self.bot_right)


    def img_quad(self):
        return (self.bot_left, self.bot_right, self.top_right, self.top_left)


class Tips:
    def __init__(self, tips, font_size=10):
        self.dims = Dims()
        self.tips = tips
        self.font_size = font_size
        self.font_color = (0,0,0,1)
        self.bg_color = (0,0,0,1)
        self.border_color = (0,0,0,1)

        # Set at any point to force soft re-builds
        self.update_func = None
        self.update_args = None

    
    def build(self, db, bot_x, bot_y):
        self.font_color = db.color.text
        self.bg_color = (db.color.tips_background[0], db.color.tips_background[1], db.color.tips_background[2], 1)
        self.border_color = db.color.mods_highlight

        pad = self.dims.padding
        bot_x += pad
        bot_y += pad * .5
        w = 0
        h = pad
        for tip in self.tips:
            dims = get_blf_text_dims(tip, self.font_size)
            w = dims[0] if dims[0] > w else w
            h += dims[1] + pad
        w += pad * 2

        self.dims.bot_left  = (bot_x, bot_y)
        self.dims.top_left  = (bot_x, bot_y + h)
        self.dims.top_right = (bot_x + w, bot_y + h)
        self.dims.bot_right = (bot_x + w, bot_y)


    def update(self):
        self.__soft_rebuild()


    def __soft_rebuild(self):

        if self.update_func:
            if self.update_args:
                self.tips = self.update_func(*self.update_args)
            else:
                self.tips = self.update_func()
        else: return

        pad = self.dims.padding
        bot_x = self.dims.bot_left[0]
        bot_y = self.dims.bot_left[1]
        w = 0
        h = pad
        for tip in self.tips:
            dims = get_blf_text_dims(tip, self.font_size)
            w = dims[0] if dims[0] > w else w
            h += dims[1] + pad
        w += pad * 2

        self.dims.top_left  = (bot_x, bot_y + h)
        self.dims.top_right = (bot_x + w, bot_y + h)
        self.dims.bot_right = (bot_x + w, bot_y)


    def draw(self):

        render_quad(self.dims.quad(), color=self.bg_color)
        draw_border_lines(self.dims.quad(), color=self.border_color)

        pad = self.dims.padding
        x = self.dims.bot_left[0] + pad
        y = self.dims.bot_left[1] + pad

        for tip in reversed(self.tips):
            render_text(tip, (x, y), self.font_size, self.font_color)
            y += get_blf_text_dims(tip, self.font_size)[1] + pad


class Stats:
    def __init__(self, stats=[], font_size=12):
        ''' Stat item example = tuple = ("LABEL", obj, attr)  where obj is the object in mem and attr is a string attribute for getattr(obj, attr)'''
        self.stats = stats
        self.font_size = font_size
        self.font_color = (0,0,0,1)
        self.pos = (0,0)
        self.pad = 8 * dpi_factor(min=0.5)


    def build(self, db, top_left_x=0, top_left_y=0):
        self.font_color = db.color.text
        self.pos = (top_left_x, top_left_y)

    
    def draw(self):
        x = self.pos[0]
        y = self.pos[1]
        for stat in self.stats:
            if len(stat) != 3: continue
            label, obj, attr = stat
            if not hasattr(obj, attr): return

            text = f'{label} : {getattr(obj, attr)}'
            render_text(text, (x, y), self.font_size, self.font_color)
            y -= get_blf_text_dims(text, self.font_size)[1] + self.pad
            