import bpy
import gpu, time
from gpu_extras.batch import batch_for_shader
from mathutils import Vector
from math import sin, cos
from ...utility.screen import dpi_factor
from ... utility import addon
from ... utils.cursor_warp import get_screen_warp_padding
from .. graphics.draw import draw_border_lines
from .. graphics.draw import render_quad
from .. utils.checks import is_mouse_in_quad
from .. utils.geo import get_blf_text_dims
from . elements import Dims, Tips, Stats


class Row:
    def __init__(self):
        self.elements = []
        self.label = ''
        self.active = True
    

    def add_element(self, element):
        self.elements.append(element)


class DB:
    def __init__(self, context, event):
        prefs = addon.preference()
        # Colors
        self.color = Color()
        # Screen
        self.screen_width = context.area.width
        self.screen_height = context.area.height
        self.warp_pad = get_screen_warp_padding()
        # States
        self.mouse_over_form = False
        self.move_locked = False
        self.over_dot = False
        self.dot_open = False
        self.dot_dragging = False
        self.menu_just_opened = False
        self.operator_stop_building = False
        # Left
        self.form_bot_left = prefs.ui.form_pos
        # Event
        self.mouse_pos = (0,0)
        self.clicked = False
        self.click_release = True
        self.increment = 0
        self.shift = False
        self.ctrl = False
        self.alt = False
        # Locked elem
        self.locked_element = None
        self.locked_popup = None
        # Maps
        self.increment_maps = {"WHEELUPMOUSE", 'NUMPAD_PLUS', 'EQUAL', 'UP_ARROW'}
        self.decrement_maps = {"WHEELDOWNMOUSE", 'NUMPAD_MINUS', 'DOWN_ARROW', 'MINUS'}

        self.update(context, event)


    def update(self, context, event):
        self.mouse_pos = (event.mouse_region_x, event.mouse_region_y)
        self.clicked = True if event.type == 'LEFTMOUSE' and event.value == 'PRESS' else False
        self.click_release = True if event.value == 'RELEASE' else False
        self.shift = event.shift
        self.ctrl = event.ctrl
        self.alt = event.alt

        self.increment = 0
        if event.type in self.increment_maps and event.value == 'PRESS': self.increment = 1
        elif event.type in self.decrement_maps and event.value == 'PRESS': self.increment = -1


class Color:
    def __init__(self):
        c = addon.preference().color
        self.text            = c.Hops_UI_text_color
        self.secondary_text  = c.Hops_UI_secondary_text_color
        self.highlight       = c.Hops_UI_highlight_color
        self.highlight_drag  = c.Hops_UI_highlight_drag_color
        self.background      = c.Hops_UI_background_color
        self.cell_background = c.Hops_UI_cell_background_color
        self.tips_background = c.tips_background
        self.dropshadow      = c.Hops_UI_dropshadow_color
        self.border          = c.Hops_UI_border_color
        self.mouse_over      = c.Hops_UI_mouse_over_color
        self.text_highlight  = c.Hops_UI_text_highlight_color
        self.mods_highlight  = c.Hops_UI_mods_highlight_color


class Form:
    def __init__(self, context, event, dot_open=True):
        self.db = DB(context, event)
        self.db.dot_open = dot_open
        self.dims = Dims()
        self.bracket = Move_Bracket(context, self.db)
        self.dot = Dot(self.db)
        self.rows = []
        self.row_presets = {}
        self.clamped_first_launch = False
        self.menu_tollerance = 8 * dpi_factor(min=0.5)
        self.set_FAS = False
        self.FAS_OG_option = addon.preference().ui.Hops_modal_fast_ui_loc_options
        self.stats = None

    # --- ROW --- #

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

    # --- DOT --- #

    def dot_calls(self, LR_callback=None, LR_args=None, UD_callback=None, UD_args=None, scroll_func=None, scroll_pos_args=None, scroll_neg_args=None, tips=[], font_size=12):
        '''Pass in functions and tuples for dot callbacks.'''

        self.dot.tips = Tips(tips, font_size)
        self.dot.drag_LR_func = LR_callback
        self.dot.drag_LR_args = LR_args
        self.dot.drag_UD_func = UD_callback
        self.dot.drag_UD_args = UD_args
        self.dot.scroll_func = scroll_func
        self.dot.scroll_pos_args = scroll_pos_args
        self.dot.scroll_neg_args = scroll_neg_args


    def insert_stats(self, stats=[], font_size=12):
        self.stats = Stats(stats=stats, font_size=font_size)


    def close_dot(self):
        self.db.dot_open = False


    def open_dot(self):
        self.db.dot_open = True


    def is_dot_open(self):
        return self.db.dot_open


    def active(self):
        # Just when dot is showing
        if self.db.dot_open == False:
            if self.db.over_dot: return True
            if self.db.dot_dragging: return True
            return False

        # Full open menu
        if self.db.locked_element: return True
        if self.db.locked_popup: return True
        if self.db.move_locked: return True
        if self.db.mouse_over_form: return True
        if self.db.over_dot: return True
        return False

    # --- OP --- #

    def operator_stop_building(self):
        return self.db.operator_stop_building

    # --- BASE --- #

    def build(self, preserve_top_left=False):

        self.db.operator_stop_building = True

        # Preserve
        top_left_y = self.dims.top_left[1]

        bot_left = self.db.form_bot_left

        h_offset = bot_left[1]
        for row in reversed(self.rows):
            if row.active == False: continue

            x_offset = bot_left[0]

            max_height = 0
            for elem in row.elements:
                elem.build(self.db, x_offset, h_offset)
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
        self.dims.max_height = abs(self.dims.top_left[1] - self.dims.bot_left[1]) + self.dot.radius * 2

        if self.clamped_first_launch == False:
            self.clamped_first_launch = True
            self.bracket.clamp(self.db, self.dims)
            self.build()

        self.bracket.build(self.dims)
        self.dot.build(self.db, self.dims)

        if self.stats:
            y = self.dims.top_right[1] - get_blf_text_dims("XyZ", self.stats.font_size)[1]
            self.stats.build(self.db, top_left_x=self.dims.top_right[0] + pad, top_left_y=y)

        # Preserve
        if preserve_top_left:
            x = self.db.form_bot_left[0]
            y = self.db.form_bot_left[1]
            diff = top_left_y - self.dims.top_left[1]
            addon.preference().ui.form_pos = (x, y + diff)
            self.build()


    def update(self, context, event, return_on_timer=True):

        self.db.operator_stop_building = False

        self.db.update(context, event)

        # Closed menu update
        if self.db.dot_open == False:
            # FAS
            if self.set_FAS:
                self.set_FAS = False
                addon.preference().ui.Hops_modal_fast_ui_loc_options = self.FAS_OG_option
            # DOT
            self.dot.update(event, self.db)
            return

        # Locked : Dot
        if self.dot.drag_locked:
            self.dot.update(event, self.db)
            return

        # Locked : Popup
        if self.db.locked_popup:
            self.db.locked_popup.locked_update(context, event, self.db)
            return

        # Locked : Element
        if self.db.locked_element:
            self.db.locked_element.locked_update(context, event, self.db)
            return

        # Locked : Move
        elif self.db.move_locked:
            self.bracket.move(self.db)
            self.bracket.clamp(self.db, self.dims)
            self.build()
            return

        # Clamp Window Location
        if self.bracket.clamp(self.db, self.dims):
            self.build()

        # Change FAS UI Loc
        if self.db.dot_open:
            self.set_FAS = True
            addon.preference().ui.Hops_modal_fast_ui_loc_options = 1

        if return_on_timer:
            if event.type == 'TIMER': return

        self.dot.update(event, self.db)

        self.bracket.update(self.db)

        self.db.mouse_over_form = is_mouse_in_quad(self.dims.quad(), self.db.mouse_pos, tolerance=self.menu_tollerance)

        for row in self.rows:
            if row.active == False: continue

            for elem in row.elements:
                elem.update(context, event, self.db)


    def draw(self):
        # Dot
        self.dot.draw()
        if self.db.dot_open == False: return

        # Stats
        if self.stats:
            self.stats.draw()

        # Background
        render_quad(self.dims.quad(), color=self.db.color.cell_background)
        draw_border_lines(self.dims.quad(), color=self.db.color.border)
        # Bracket
        self.bracket.draw()
        # Elements
        for row in self.rows:
            if row.active == False: continue

            for elem in row.elements:
                if elem != self.db.locked_element:
                    elem.draw(self.db)
        
        # Tips
        if not self.db.locked_popup:
            for row in self.rows:
                if row.active == False: continue
                for elem in row.elements:
                    if elem != self.db.locked_element:
                        elem.draw_tips(self.db)

        # Locked : Popup
        if self.db.locked_popup:
            self.db.locked_popup.draw(self.db)
            return

        # Locked : Element
        if self.db.locked_element:
            self.db.locked_element.draw(self.db)
            return


    def shut_down(self, context):
        for row in self.rows:
            for elem in row.elements:
                elem.shut_down(context)


class Move_Bracket:
    def __init__(self, context, db):
        self.v_dims = Dims()
        self.h_dims = Dims()
        self.pad = 6 * dpi_factor(min=0.5)
        self.bg_color = db.color.cell_background
        self.border_color = db.color.border
        self.mouse_move_offset = (0,0)

    
    def build(self, form_dims):

        thick = 4 * dpi_factor(min=0.5)
        bot_x = form_dims.bot_left[0] - self.pad - thick
        bot_y = form_dims.bot_left[1] - self.pad - thick
        
        h = abs(form_dims.top_left[1] - form_dims.bot_left[1]) * .75
        w = abs(form_dims.bot_right[0] - form_dims.bot_left[0]) * .75

        self.v_dims.bot_left  = (bot_x, bot_y)
        self.v_dims.top_left  = (bot_x, bot_y + h)
        self.v_dims.top_right = (bot_x + thick, bot_y + h)
        self.v_dims.bot_right = (bot_x + thick, bot_y)

        bot_x += thick
        self.h_dims.bot_left  = (bot_x, bot_y)
        self.h_dims.top_left  = (bot_x, bot_y + thick)
        self.h_dims.top_right = (bot_x + w, bot_y + thick)
        self.h_dims.bot_right = (bot_x + w, bot_y)


    def update(self, db):
        over_v = is_mouse_in_quad(self.v_dims.quad(), db.mouse_pos, tolerance=self.pad)
        over_h = is_mouse_in_quad(self.h_dims.quad(), db.mouse_pos, tolerance=self.pad)
        if over_v or over_h:
            self.bg_color = db.color.mouse_over
            if db.clicked:
                db.move_locked = True
                self.mouse_move_offset = (
                    db.form_bot_left[0] - db.mouse_pos[0],
                    db.form_bot_left[1] - db.mouse_pos[1])
        else:
            self.bg_color = db.color.cell_background
            db.move_locked = False


    def move(self, db):
        if db.click_release:
            db.move_locked = False
            return

        x = db.mouse_pos[0] + self.mouse_move_offset[0]
        y = db.mouse_pos[1] + self.mouse_move_offset[1]
        addon.preference().ui.form_pos = (x, y)


    def clamp(self, db, dims):

        x, y = addon.preference().ui.form_pos
        new_x = x
        new_y = y

        dot_offset = addon.preference().ui.Hops_form_dot_offset * dpi_factor(min=0.5) 
        dot_diam = 20 * dpi_factor(min=0.5) 

        max_x = db.screen_width - db.warp_pad - dims.max_width
        max_y = db.screen_height - db.warp_pad - dims.max_height - dot_offset

        min_x = db.warp_pad + dot_offset + dot_diam

        # Left
        if x < min_x:
            new_x = min_x
        # Right
        if x > max_x:
            new_x = max_x
        # Top
        if y > max_y:
            new_y = max_y
        # Bottom
        if y < db.warp_pad:
            new_y = db.warp_pad

        addon.preference().ui.form_pos = (new_x, new_y)

        if (new_x != x) or (new_y != y):
            return True
        else:
            return False


    def draw(self):
        render_quad(self.v_dims.quad(), color=self.bg_color, bevel_corners=False)
        render_quad(self.h_dims.quad(), color=self.bg_color, bevel_corners=False)


class Dot:
    def __init__(self, db):
        # Dims
        self.pos = (0,0)
        self.radius = 10 * dpi_factor(min=0.5)
        # Shader / Settings
        built_in_shader = 'UNIFORM_COLOR' if bpy.app.version[0] >=4 else '2D_UNIFORM_COLOR'
        self.shader = gpu.shader.from_builtin(built_in_shader)
        self.segments = 32
        # Outer
        self.outer_color = db.color.border
        self.outer_verts = []
        self.outer_batch = None
        # Inner
        self.inner_color = db.color.cell_background
        self.inner_verts = []
        self.inner_indices = []
        self.inner_batch = None
        # State
        self.drag_locked = False
        self.mouse_over = False
        self.mouse_start_pos = (0,0)
        self.mouse_distance = 0
        self.mouse_step = 0
        self.drag_testing = False
        # Tips
        self.tips = None
        # Drag States : Left Right
        self.drag_LR_running = False
        self.drag_LR_func = None
        self.drag_LR_args = None
        # Drag States : Up Down
        self.drag_UD_running = False
        self.drag_UD_func = None
        self.drag_UD_args = None
        # Scroll
        self.scroll_func = None
        self.scroll_pos_args = None
        self.scroll_neg_args = None
        # Dot Detection
        self.dot_detection_padding = addon.preference().ui.Hops_dot_detection_padding
        self.dot_offset = addon.preference().ui.Hops_form_dot_offset * dpi_factor(min=0.5) 


    def build(self, db, dims):
        # Update
        self.pos = (
            dims.top_left[0] - self.dot_offset,
            dims.top_left[1] + self.dot_offset)
        # Build
        self.__outer_batch()
        self.__inner_batch()

        if not self.tips: return
        bot_x = self.pos[0] + self.radius
        bot_y = self.pos[1] + self.radius
        self.tips.build(db, bot_x, bot_y)


    def __outer_batch(self):
        # Clear
        self.outer_verts = []
        self.outer_batch = None
        # Build
        for i in range(self.segments):
            index = i + 1
            angle = i * 3.14159 * 2 / self.segments
            x = (cos(angle) * self.radius) + self.pos[0]
            y = (sin(angle) * self.radius) + self.pos[1]
            self.outer_verts.append((x, y))
        self.outer_verts.append(self.outer_verts[0])
        # Batch
        self.outer_batch = batch_for_shader(self.shader, 'LINE_STRIP', {"pos": self.outer_verts})


    def __inner_batch(self):
        # Clear
        self.inner_batch = None
        self.inner_indices = []
        # Build
        self.inner_verts = self.outer_verts[:]
        for i in range(self.segments):
            if i == len(self.inner_verts): break
            self.inner_indices.append((0, i, i + 1))
        # Batch
        self.inner_batch = batch_for_shader(self.shader, 'TRIS', {'pos': self.inner_verts}, indices=self.inner_indices)


    def update(self, event, db):
        
        # Reset
        self.mouse_over = False
        db.menu_just_opened = False
        db.dot_dragging = False

        # Drag locked
        if self.drag_locked:
            db.dot_dragging = True
            self.__drag_event(event, db)
            return

        # Testing for drag / regular click
        if self.drag_testing:
            db.over_dot = True
            self.__drag_test(event, db)
            return

        # Mouse over
        radius = self.radius
        if db.dot_open == False: # Increase detection size when closed
            radius += self.dot_detection_padding
        if abs(db.mouse_pos[0] - self.pos[0]) < radius:
            if abs(db.mouse_pos[1] - self.pos[1]) < radius:
                self.mouse_over = True

        # Color
        if self.mouse_over: self.outer_color = db.color.mods_highlight
        else: self.outer_color = db.color.border

        # Start click
        self.drag_locked = False
        self.drag_testing = False
        if self.mouse_over:
            db.over_dot = True
            self.__click_event(event, db)
            self.__scroll_event(event, db)
        else:
            db.over_dot = False


    def __click_event(self, event, db):
        if db.clicked:
            self.drag_testing = True
            self.mouse_start_pos = db.mouse_pos
            self.mouse_distance = 0
            self.mouse_step = 0


    def __scroll_event(self, event, db):
        if self.drag_testing: return
        if not db.increment: return
        if not self.scroll_func: return

        if db.increment > 0:
            if self.scroll_pos_args:
                self.scroll_func(*self.scroll_pos_args)
            else: self.scroll_func()
        else:
            if self.scroll_neg_args:
                self.scroll_func(*self.scroll_neg_args)
            else: self.scroll_func()


    def __drag_test(self, event, db):

        self.mouse_distance = (Vector(self.mouse_start_pos) - Vector(db.mouse_pos)).magnitude

        # No turning back now
        if self.mouse_distance > self.radius:
            self.drag_locked = True
            self.drag_LR_running = False
            self.drag_UD_running = False

            # Test for angle
            up = Vector((0, 1))
            down = Vector((0,-1))
            left = Vector((-1, 0))
            right = Vector((1, 0))

            mouse_vec = Vector(self.mouse_start_pos) - Vector(db.mouse_pos)
            mouse_vec.normalize()

            angles = [
                up.angle(mouse_vec),
                down.angle(mouse_vec),
                left.angle(mouse_vec),
                right.angle(mouse_vec)]

            minpos = angles.index(min(angles))

            if minpos in (0, 1): self.drag_UD_running = True
            else: self.drag_LR_running = True
            return

        # Just a click and exit
        if db.click_release:
            self.drag_testing = False
            self.drag_locked = False
            db.menu_just_opened = True
            db.dot_open = not db.dot_open


    def __drag_event(self, event, db):

        self.mouse_distance = (Vector(self.mouse_start_pos) - Vector(db.mouse_pos)).magnitude

        # Finished
        if db.click_release:
            self.drag_testing = False
            self.drag_locked = False
            return

        # Step amount
        step = 75 * dpi_factor(min=0.5) if event.shift else 50 * dpi_factor(min=0.5)
        if self.mouse_distance > step:
            self.mouse_start_pos = db.mouse_pos
        else: return

        # Drag : Shift
        if self.drag_LR_running:
            if self.drag_LR_func:
                if self.drag_LR_args:
                    self.drag_LR_func(*self.drag_LR_args)
                else:
                    self.drag_LR_func()

        # Drag : Default
        else:
            if self.drag_UD_func:
                if self.drag_UD_args:
                    self.drag_UD_func(*self.drag_UD_args)
                else:
                    self.drag_UD_func()


    def draw(self):
        #Enable(bgl.GL_LINE_SMOOTH)
        gpu.state.blend_set('ALPHA')

        self.shader.bind()

        if self.inner_batch:
            self.shader.uniform_float("color", self.inner_color)
            self.inner_batch.draw(self.shader)

        if self.outer_batch:
            gpu.state.line_width_set(3)
            self.shader.uniform_float("color", self.outer_color)
            self.outer_batch.draw(self.shader)

        if self.mouse_over and self.tips:
            self.tips.draw()

        #Disable(bgl.GL_LINE_SMOOTH)
        gpu.state.blend_set('NONE')