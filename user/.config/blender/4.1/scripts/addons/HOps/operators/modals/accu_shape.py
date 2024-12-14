import bpy, mathutils, math, gpu, traceback, bmesh, time
from enum import Enum
from mathutils import Vector, Matrix, Quaternion
from gpu_extras.batch import batch_for_shader
from ... utility import addon
from ... utility.base_modal_controls import Base_Modal_Controls
from ... ui_framework.master import Master
from ... ui_framework.graphics.draw import render_text, render_quad, draw_border_lines
from ... ui_framework.utils.geo import get_blf_text_dims
from ... ui_framework.utils.checks import is_mouse_in_quad
from ... utils.toggle_view3d_panels import collapse_3D_view_panels
from ... utils.space_3d import get_3D_point_from_mouse, scene_ray_cast, get_2d_point_from_3d_point
from ... utils.modal_frame_drawing import draw_modal_frame
from ... utils.cursor_warp import mouse_warp
from ... utility import method_handler
from ...utility.screen import dpi_factor
from ... utility import math as hops_math
from ... utility import object

ACTIVE_LENGTH = "Meters"
UNIT_SCALE_FACTOR = 1

class State(Enum):
    POINT_1 = 0
    POINT_2 = 1
    POINT_3 = 2
    ADJUST = 3
    SCALE = 4
    FACE = 5


class Bounds:
    def __init__(self):
        self.bot_front_left  = Vector((0,0,0))
        self.bot_front_right = Vector((0,0,0))
        self.bot_back_left   = Vector((0,0,0))
        self.bot_back_right  = Vector((0,0,0))

        self.top_front_left  = Vector((0,0,0))
        self.top_front_right = Vector((0,0,0))
        self.top_back_left   = Vector((0,0,0))
        self.top_back_right  = Vector((0,0,0))


    def get_corner_points(self):
        points = [
            self.bot_front_left,
            self.bot_front_right,
            self.bot_back_left,
            self.bot_back_right,
            self.top_front_left,
            self.top_front_right,
            self.top_back_left,
            self.top_back_right]
        return points


    def get_center_face_points(self):
        top   = hops_math.coords_to_center([ self.top_front_left, self.top_front_right, self.top_back_right , self.top_back_left  ])
        bot   = hops_math.coords_to_center([ self.bot_front_left, self.bot_front_right, self.bot_back_right , self.bot_back_left  ])
        left  = hops_math.coords_to_center([ self.bot_back_left , self.bot_front_left , self.top_front_left , self.top_back_left  ])
        right = hops_math.coords_to_center([ self.bot_back_right, self.bot_front_right, self.top_front_right, self.top_back_right ])
        front = hops_math.coords_to_center([ self.bot_front_left, self.bot_front_right, self.top_front_right, self.top_front_left ])
        back  = hops_math.coords_to_center([ self.bot_back_left , self.bot_back_right,  self.top_back_right , self.top_back_left  ])
        return [ top, bot, left, right, front, back ]


    def get_center_point(self):
        bounds = hops_math.coords_to_bounds(self.get_corner_points())
        center = hops_math.coords_to_center(bounds)
        return center


class Dims:
    def __init__(self):
        self.bot_left  = (0,0)
        self.top_left  = (0,0)
        self.top_right = (0,0)
        self.bot_right = (0,0)


class Static_Menu:
    def __init__(self, context):
        
        # Bounds
        self.dims = Dims()

        # Font
        self.f_size = 14
        self.f_color = addon.preference().color.Hops_UI_text_color

        # Scale / Padding
        self.scale_factor = dpi_factor(min=.25)
        self.padding      = 8 * self.scale_factor
        self.left_spacing = 80 * self.scale_factor
        self.top_spacing  = 130 * self.scale_factor
        self.font_height  = get_blf_text_dims("Qjq`", self.f_size)[1]

        # Colors
        self.highlight_color = addon.preference().color.Hops_UI_highlight_color
        self.cell_bg_color   = addon.preference().color.Hops_UI_cell_background_color
        self.border_color    = addon.preference().color.Hops_UI_border_color
        self.hover_color     = addon.preference().color.Hops_UI_mouse_over_color

        # Screen
        self.screen_width = context.area.width
        self.screen_height = context.area.height

        # Operator data
        self.op_length = 0
        self.op_width = 0
        self.op_height = 0

        # States
        self.mouse_is_over = False
        self.input_locked = False

        # Entry boxes
        self.entry_box_width = get_blf_text_dims("0000000.000000", self.f_size)[0]

        self.entry_length = Entry_Box()
        self.entry_width  = Entry_Box()
        self.entry_height = Entry_Box()

        # Unit Tabs : Metric
        self.unit_metric = Unit_Tabs()
        self.unit_metric.text = "Metric"

        # Unit Tabs : Imperial
        self.unit_imperial = Unit_Tabs()
        self.unit_imperial.text = "Imperial"

        # Length box
        self.length_box = Length_Box()

        # Set active units
        if ACTIVE_LENGTH in self.length_box.metric_opts:
            self.unit_metric.active = True
            self.unit_imperial.active = False
            self.length_box.unit_system = "Metric"
            self.length_box.metric_index = self.length_box.metric_opts.index(ACTIVE_LENGTH)
        else:
            self.length_box.unit_system = "Imperial"
            self.unit_metric.active = False
            self.unit_imperial.active = True
            self.length_box.imperial_index = self.length_box.imperial_opts.index(ACTIVE_LENGTH)

        # Center button
        self.center_dims = Dims()
        self.center_mouse_over = False
        self.center_text = "C"

        # Equalize button
        self.equalize_dims = Dims()
        self.equalize_mouse_over = False
        self.equalize_text = "E"

        # Finish button
        self.fin_button_dims = Dims()
        self.fin_button_clicked = False
        self.mouse_over_fin = False
        self.fin_text = "✓"

        # Drawing Stats
        self.equalize_on = False
        self.auto_center = False
        self.exit_type = ""

        # Move bracket
        self.move_bracket = Move_Bracket(context)

        # Intial build
        self.__setup_dims(context)
        self.move_bracket.setup()


    def __setup_dims(self, context):

        labels = ["Length", "Width", "Height"]

        # Add all the horizontal dims
        widest_label = 0
        for label in labels:
            width = get_blf_text_dims(label, self.f_size)[0]
            if width > widest_label:
                widest_label = width
        width = self.padding + widest_label + self.padding + self.entry_box_width + self.padding

        # Add all the vertical dims
        height = self.padding * 4 + self.font_height * 3
        
        pos = self.move_bracket.pos

        self.dims.bot_left  = (pos[0]        , pos[1] - height)
        self.dims.top_left  = (pos[0]        , pos[1])
        self.dims.top_right = (pos[0] + width, pos[1])
        self.dims.bot_right = (pos[0] + width, pos[1] - height)

        self.move_bracket.height = height + self.padding * 3

        # Length entry box
        left = self.dims.bot_left[0] + self.padding + widest_label + self.padding
        top = self.dims.top_right[1] - self.padding

        self.entry_length.dims.bot_left  = (left                       , top -  self.font_height)
        self.entry_length.dims.top_left  = (left                       , top)
        self.entry_length.dims.top_right = (left + self.entry_box_width, top)
        self.entry_length.dims.bot_right = (left + self.entry_box_width, top -  self.font_height)

        # Width entry box
        top -= self.font_height + self.padding
        self.entry_width.dims.bot_left  = (left                       , top -  self.font_height)
        self.entry_width.dims.top_left  = (left                       , top)
        self.entry_width.dims.top_right = (left + self.entry_box_width, top)
        self.entry_width.dims.bot_right = (left + self.entry_box_width, top -  self.font_height)

        # Height entry box
        top -= self.font_height + self.padding
        self.entry_height.dims.bot_left  = (left                       , top -  self.font_height)
        self.entry_height.dims.top_left  = (left                       , top)
        self.entry_height.dims.top_right = (left + self.entry_box_width, top)
        self.entry_height.dims.bot_right = (left + self.entry_box_width, top -  self.font_height)

        # Unit tabs
        height = self.font_height + self.padding * 2
        width = get_blf_text_dims(self.unit_metric.text, self.unit_metric.f_size)[0] + self.padding * 2
        self.unit_metric.dims.bot_left  = (self.dims.top_left[0], self.dims.top_left[1])
        self.unit_metric.dims.top_left  = (self.dims.top_left[0], self.dims.top_left[1] + height)
        self.unit_metric.dims.top_right = (self.dims.top_left[0] + width, self.dims.top_left[1] + height)
        self.unit_metric.dims.bot_right = (self.dims.top_left[0] + width, self.dims.top_left[1])

        offset = width + self.padding * .5
        width = get_blf_text_dims(self.unit_imperial.text, self.unit_imperial.f_size)[0] + self.padding * 2
        self.unit_imperial.dims.bot_left  = (offset + self.dims.top_left[0], self.dims.top_left[1])
        self.unit_imperial.dims.top_left  = (offset + self.dims.top_left[0], self.dims.top_left[1] + height)
        self.unit_imperial.dims.top_right = (offset + self.dims.top_left[0] + width, self.dims.top_left[1] + height)
        self.unit_imperial.dims.bot_right = (offset + self.dims.top_left[0] + width, self.dims.top_left[1])

        # Length Box
        text_dims = get_blf_text_dims("Centimetersjj", self.length_box.f_size)
        y_offset = text_dims[1] + self.padding * 2
        width = text_dims[0] + self.padding * 2
        self.length_box.dims.bot_left  = (self.dims.bot_left[0]        , self.dims.bot_left[1] - y_offset)
        self.length_box.dims.top_left  = (self.dims.bot_left[0]        , self.dims.bot_left[1])
        self.length_box.dims.top_right = (self.dims.bot_left[0] + width, self.dims.bot_left[1])
        self.length_box.dims.bot_right = (self.dims.bot_left[0] + width, self.dims.bot_left[1] - y_offset)


        # Center Button
        width = get_blf_text_dims(self.center_text, self.length_box.f_size)[0] + self.padding * 2
        x = self.length_box.dims.bot_right[0]
        self.center_dims.bot_left  = (x        , self.dims.bot_left[1] - y_offset)
        self.center_dims.top_left  = (x        , self.dims.bot_left[1])
        self.center_dims.top_right = (x + width, self.dims.bot_left[1])
        self.center_dims.bot_right = (x + width, self.dims.bot_left[1] - y_offset)
        x += width

        # Equalize Button
        width = get_blf_text_dims(self.equalize_text, self.length_box.f_size)[0] + self.padding * 2
        self.equalize_dims.bot_left  = (x        , self.dims.bot_left[1] - y_offset)
        self.equalize_dims.top_left  = (x        , self.dims.bot_left[1])
        self.equalize_dims.top_right = (x + width, self.dims.bot_left[1])
        self.equalize_dims.bot_right = (x + width, self.dims.bot_left[1] - y_offset)
        x += width

        # Finish Button
        width = get_blf_text_dims(self.fin_text, self.length_box.f_size)[0] + self.padding * 2
        self.fin_button_dims.bot_left  = (x        , self.dims.bot_left[1] - y_offset)
        self.fin_button_dims.top_left  = (x        , self.dims.bot_left[1])
        self.fin_button_dims.top_right = (x + width, self.dims.bot_left[1])
        self.fin_button_dims.bot_right = (x + width, self.dims.bot_left[1] - y_offset)


    def update(self, context, event, op):

        # Move bracket
        if self.input_locked == False:
            self.move_bracket.update(context, event)
            if self.move_bracket.locked:
                self.__setup_dims(context)
                self.mouse_is_over = True
                return

        self.mouse_is_over = False

        locked_1 = self.entry_length.update(context, event, op, "length")
        locked_2 = self.entry_width.update(context, event, op, "width")
        locked_3 = self.entry_height.update(context, event, op, "height")

        # For modal
        results = [locked_1, locked_2, locked_3]
        if any(results):
            self.input_locked = True

            # When the user presses TAB this will make it cycle to the next input field
            for index, result in enumerate(results):
                if index == 0:
                    if result and self.entry_length.tabbed_finish:
                        self.entry_width.locked = True
                elif index == 1:
                    if result and self.entry_width.tabbed_finish:
                        self.entry_height.locked = True
        else:
            self.input_locked = False

        # Unit tabs
        self.unit_metric.update(context, event)
        self.unit_imperial.update(context, event)

        if self.unit_metric.just_clicked:
            self.unit_metric.active = True
            self.unit_imperial.active = False
            self.unit_imperial.just_clicked = False

        elif self.unit_imperial.just_clicked:
            self.unit_imperial.active = True
            self.unit_metric.active = False
            self.unit_metric.just_clicked = False

        # Length
        self.length_box.unit_system = "Metric" if self.unit_metric.active else "Imperial"
        self.length_box.update(context, event)

        # Prevent zooming while over menu
        mouse_pos = (event.mouse_region_x, event.mouse_region_y)
        over = [
            is_mouse_in_quad((self.dims.top_left, self.dims.bot_left, self.dims.top_right, self.dims.bot_right), mouse_pos),
            self.length_box.mouse_over, self.unit_metric.mouse_over, self.unit_imperial.mouse_over]
        self.mouse_is_over = True if any(over) else False

        # Finish Button
        self.mouse_over_fin = is_mouse_in_quad((self.fin_button_dims.top_left, self.fin_button_dims.bot_left, self.fin_button_dims.top_right, self.fin_button_dims.bot_right), mouse_pos)
        if self.mouse_over_fin:
            if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
                self.fin_button_clicked = True

        # Equalize Button
        self.equalize_mouse_over = is_mouse_in_quad((self.equalize_dims.top_left, self.equalize_dims.bot_left, self.equalize_dims.top_right, self.equalize_dims.bot_right), mouse_pos)
        if self.equalize_mouse_over:
            if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
                op.equalize = not op.equalize
                msg = "Equalize : ON" if op.equalize else "Equalize : OFF"
                bpy.ops.hops.display_notification(info=msg)

        # Center Button
        self.center_mouse_over = is_mouse_in_quad((self.center_dims.top_left, self.center_dims.bot_left, self.center_dims.top_right, self.center_dims.bot_right), mouse_pos)
        if self.center_mouse_over:
            if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
                op.keep_at_center = not op.keep_at_center
                msg = "Keep Center : ON" if op.keep_at_center else "Keep Center : OFF"
                bpy.ops.hops.display_notification(info=msg)

        # Drawing stats
        self.equalize_on = op.equalize
        self.auto_center = op.keep_at_center
        if op.add_cube:
            self.exit_type = "Exit: Adding Cube"
        elif op.exit_with_empty:
            self.exit_type = "Exit: Adding Empty"
        elif not op.exit_with_empty:
            self.exit_type = "Exit: Adding Lattice"


    def draw_2d(self):

        # Background
        render_quad(quad=(self.dims.top_left, self.dims.bot_left, self.dims.top_right, self.dims.bot_right), color=self.cell_bg_color, bevel_corners=True)
        draw_border_lines(vertices=[self.dims.top_left, self.dims.bot_left, self.dims.top_right, self.dims.bot_right], width=1, color=self.border_color, format_lines=True)

        # Length
        text = "Length"
        pos = (self.dims.top_left[0] + self.padding, self.dims.top_left[1] - self.padding - self.font_height)
        render_text(text=text, position=pos, size=self.f_size, color=self.f_color)

        # Width
        text = "Width"
        pos = (self.dims.top_left[0] + self.padding, self.dims.top_left[1] - self.padding * 2 - self.font_height * 2)
        render_text(text=text, position=pos, size=self.f_size, color=self.f_color)

        # Height
        text = "Height"
        pos = (self.dims.top_left[0] + self.padding, self.dims.top_left[1] - self.padding * 3 - self.font_height * 3)
        render_text(text=text, position=pos, size=self.f_size, color=self.f_color)

        # Draw entry boxes
        self.entry_length.draw_2d()
        self.entry_width.draw_2d()
        self.entry_height.draw_2d()

        # Unit tabs
        self.unit_metric.draw_2d()
        self.unit_imperial.draw_2d()

        # Length
        self.length_box.draw_2d()

        # Stats
        pos = (self.dims.top_right[0] + self.padding, self.dims.top_right[1] - self.font_height)
        text = f'Scene: {bpy.context.scene.unit_settings.length_unit}'
        render_text(text=text, position=pos, size=12, color=self.f_color)

        y_offset = self.font_height + self.padding * .5

        pos = (self.dims.top_right[0] + self.padding, self.dims.top_right[1] - self.font_height - y_offset)
        text = "Equalize: ON" if self.equalize_on else "Equalize: OFF"
        render_text(text=text, position=pos, size=12, color=self.f_color)

        y_offset += self.font_height + self.padding * .5

        pos = (self.dims.top_right[0] + self.padding, self.dims.top_right[1] - self.font_height - y_offset)
        text = "Auto Center: ON" if self.auto_center else "Auto Center: OFF"
        render_text(text=text, position=pos, size=12, color=self.f_color)

        y_offset += self.font_height + self.padding * .5

        pos = (self.dims.top_right[0] + self.padding, self.dims.top_right[1] - self.font_height - y_offset)
        render_text(text=self.exit_type, position=pos, size=12, color=self.f_color)

        # Center Button
        color = self.hover_color if self.center_mouse_over else self.cell_bg_color
        render_quad(quad=(self.center_dims.top_left, self.center_dims.bot_left, self.center_dims.top_right, self.center_dims.bot_right), color=color, bevel_corners=True)
        draw_border_lines(vertices=[self.center_dims.top_left, self.center_dims.bot_left, self.center_dims.top_right, self.center_dims.bot_right], width=1, color=self.border_color, format_lines=True)

        pos = (self.center_dims.bot_left[0] + self.padding, self.center_dims.bot_left[1] + self.padding)
        render_text(text=self.center_text, position=pos, size=self.length_box.f_size, color=self.f_color)

        # Equalize Button
        color = self.hover_color if self.equalize_mouse_over else self.cell_bg_color
        render_quad(quad=(self.equalize_dims.top_left, self.equalize_dims.bot_left, self.equalize_dims.top_right, self.equalize_dims.bot_right), color=color, bevel_corners=True)
        draw_border_lines(vertices=[self.equalize_dims.top_left, self.equalize_dims.bot_left, self.equalize_dims.top_right, self.equalize_dims.bot_right], width=1, color=self.border_color, format_lines=True)

        pos = (self.equalize_dims.bot_left[0] + self.padding, self.equalize_dims.bot_left[1] + self.padding)
        render_text(text=self.equalize_text, position=pos, size=self.length_box.f_size, color=self.f_color)

        # Finish Button
        color = self.hover_color if self.mouse_over_fin else self.cell_bg_color
        render_quad(quad=(self.fin_button_dims.top_left, self.fin_button_dims.bot_left, self.fin_button_dims.top_right, self.fin_button_dims.bot_right), color=color, bevel_corners=True)
        draw_border_lines(vertices=[self.fin_button_dims.top_left, self.fin_button_dims.bot_left, self.fin_button_dims.top_right, self.fin_button_dims.bot_right], width=1, color=self.border_color, format_lines=True)

        pos = (self.fin_button_dims.bot_left[0] + self.padding, self.fin_button_dims.bot_left[1] + self.padding)
        render_text(text=self.fin_text, position=pos, size=self.length_box.f_size, color=self.f_color)

        # Move bracket
        self.move_bracket.draw_2d()


class Move_Bracket:
    def __init__(self, context):
        self.vert_dims = Dims()
        self.hori_dims = Dims()

        self.border_color = addon.preference().color.Hops_UI_border_color
        # self.hover_color  = addon.preference().color.Hops_UI_mouse_over_color

        self.screen_width = context.area.width
        self.screen_height = context.area.height

        self.factor = dpi_factor(min=.25)

        self.left_spacing = 150 * self.factor
        self.top_spacing  = 250 * self.factor

        # self.pos = (self.left_spacing, self.screen_height - self.top_spacing)
        self.pos = addon.preference().ui.accu_pos

        self.width   = 100 * self.factor
        self.height  = 100 * self.factor
        self.thick   = 6  * self.factor
        self.padding = 6   * self.factor

        self.locked = False
        self.mouse_offset = (0,0)
        self.mouse_over = False

        self.setup()
        self.clamp(context)


    def update(self, context, event):

        if self.locked == True:
            self.locked_move(context, event)
            self.setup()

        mouse_pos = (event.mouse_region_x, event.mouse_region_y)
        over_vert = is_mouse_in_quad((self.vert_dims.top_left, self.vert_dims.bot_left, self.vert_dims.top_right, self.vert_dims.bot_right), mouse_pos, tolerance=10 * self.factor)
        over_hori = is_mouse_in_quad((self.hori_dims.top_left, self.hori_dims.bot_left, self.hori_dims.top_right, self.hori_dims.bot_right), mouse_pos, tolerance=10 * self.factor)

        if over_vert or over_hori:
            self.mouse_over = True
            if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
                self.locked = True
                self.mouse_offset = (self.pos[0] - mouse_pos[0], self.pos[1] - mouse_pos[1])
        else:
            self.mouse_over = False


    def locked_move(self, context, event):
        if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            self.locked = False
            return

        mouse_pos = (event.mouse_region_x, event.mouse_region_y)
        self.pos = (mouse_pos[0] + self.mouse_offset[0], mouse_pos[1] + self.mouse_offset[1])
        self.clamp(context)


    def clamp(self, context):
        min_x = self.padding + self.thick
        if self.pos[0] < min_x:
            self.pos = (min_x, self.pos[1])

        max_x = self.screen_width - 300 * self.factor
        if self.pos[0] > max_x:
            self.pos = (max_x, self.pos[1])

        min_y = 125 * self.factor
        if self.pos[1] < min_y:
            self.pos = (self.pos[0], min_y)

        max_y = self.screen_height - 75 * self.factor
        if self.pos[1] > max_y:
            self.pos = (self.pos[0], max_y)

        addon.preference().ui.accu_pos = self.pos
    

    def setup(self):

        # Vertical
        pos_x = self.pos[0] - self.padding
        pos_y = self.pos[1] - self.padding * 2
        self.vert_dims.bot_left  = (pos_x - self.thick, pos_y - self.height)
        self.vert_dims.top_left  = (pos_x - self.thick, pos_y)
        self.vert_dims.top_right = (pos_x             , pos_y)
        self.vert_dims.bot_right = (pos_x             , pos_y - self.height)

        # Horizontal
        pos_x = self.pos[0] - self.padding - self.thick
        pos_y = self.vert_dims.bot_left[1]
        self.hori_dims.bot_left  = (pos_x             , pos_y - self.thick)
        self.hori_dims.top_left  = (pos_x             , pos_y)
        self.hori_dims.top_right = (pos_x + self.width, pos_y)
        self.hori_dims.bot_right = (pos_x + self.width, pos_y - self.thick)


    def draw_2d(self):
        if self.mouse_over or self.locked:
            # color = self.hover_color if self.mouse_over else self.border_color
            color = self.border_color
            render_quad(quad=(self.vert_dims.top_left, self.vert_dims.bot_left, self.vert_dims.top_right, self.vert_dims.bot_right), color=color, bevel_corners=False)
            render_quad(quad=(self.hori_dims.top_left, self.hori_dims.bot_left, self.hori_dims.top_right, self.hori_dims.bot_right), color=color, bevel_corners=False)


class Entry_Box:
    def __init__(self):

        self.dims = Dims()

        # Font
        self.f_size      = 14
        self.f_color     = addon.preference().color.Hops_UI_text_color
        self.font_height = get_blf_text_dims("123456789.", self.f_size)[1]

        # Colors
        self.cell_bg_color = addon.preference().color.Hops_UI_cell_background_color
        self.hover_color   = addon.preference().color.Hops_UI_mouse_over_color
        self.border_color  = addon.preference().color.Hops_UI_border_color

        # Scale / Padding
        self.scale_factor = dpi_factor(min=.25)
        self.padding      = 12 * self.scale_factor

        # Input
        self.value = 0.0
        self.entry_string = ""

        # States
        self.mouse_over = False
        self.locked = False
        self.tabbed_finish = False


    def update(self, context, event, op, dim=""):
        
        if self.locked:
            self.__update_locked_state(event, op, dim)
            return True
        else:
            self.entry_string = ""
            self.tabbed_finish = False

        self.__set_value(op, dim=dim)

        mouse_pos = (event.mouse_region_x, event.mouse_region_y)
        self.mouse_over = is_mouse_in_quad((self.dims.top_left, self.dims.bot_left, self.dims.top_right, self.dims.bot_right), mouse_pos)

        if self.mouse_over:
            if event.type == 'WHEELUPMOUSE':
                self.__set_value(op, dim=dim, additional=.125)

            elif event.type == 'WHEELDOWNMOUSE':
                self.__set_value(op, dim=dim, additional=-.125)

            if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
                self.value = 0
                self.entry_string = ""
                self.locked = True

        return False
    

    def __update_locked_state(self, event, op, dim):

        if event.type == 'TIMER':
            return

        valid = {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '.', '-'}

        if event.ascii in valid and event.value == 'PRESS':
            # Decimal
            decimal_blocked = False
            if '.' in self.entry_string and event.ascii == '.':
                decimal_blocked = True
            
            # Append text
            if decimal_blocked == False:
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

            set_val = 0
            try:
                global UNIT_SCALE_FACTOR
                set_val = float(self.entry_string) / UNIT_SCALE_FACTOR
            except:
                set_val = None

            self.__set_value(op, dim=dim, set_val=set_val)
            self.entry_string = ""
            self.locked = False

        elif event.type == 'BACK_SPACE' and event.value == 'PRESS':
            self.entry_string = self.entry_string[:-1]


    def __set_value(self, op, dim="", additional=None, set_val=None):

        if dim == "length":
            if additional != None:
                op.length += additional

            if set_val != None:
                if op.equalize:
                    op.set_length_equalized(set_val)
                else:
                    op.point_2[0] = op.point_1[0] + set_val

            op.set_back_loc_to_anchor()
            self.value = op.length * UNIT_SCALE_FACTOR

        elif dim == "width":
            if additional != None:
                op.width += additional

            if set_val != None:
                if op.equalize:
                    op.set_width_equalized(set_val)
                else:
                    op.point_2[1] = op.point_1[1] + set_val

            op.set_back_loc_to_anchor()
            self.value = op.width * UNIT_SCALE_FACTOR

        elif dim == "height":
            if additional != None:
                op.height += additional

            if set_val != None:
                if op.equalize:
                    op.set_height_equalized(set_val)
                else:
                    op.point_3[2] = op.point_1[2] + set_val

            op.set_back_loc_to_anchor()
            self.value = op.height * UNIT_SCALE_FACTOR


    def draw_2d(self):

        # Top Left, Bottom Left, Top Right, Bottom Right
        color = self.hover_color if self.mouse_over or self.locked else self.cell_bg_color
        render_quad(quad=(self.dims.top_left, self.dims.bot_left, self.dims.top_right, self.dims.bot_right), color=color, bevel_corners=True)

        # Top Left, Bottom Left, Top Right, Bottom Right
        draw_border_lines(vertices=[self.dims.top_left, self.dims.bot_left, self.dims.top_right, self.dims.bot_right], width=1, color=self.border_color, format_lines=True)

        # Dims text
        padding = ((self.dims.top_left[1] - self.dims.bot_left[1]) - self.font_height) * .5

        clamped_val = "{:.12}".format(round(float(self.value), 6))
        clamped_val.rstrip("0").rstrip(".")
        text = self.entry_string if self.locked else clamped_val
        pos = (self.dims.bot_left[0] + self.padding, self.dims.bot_left[1] + padding)
        render_text(text=text, position=pos, size=self.f_size, color=self.f_color)


class Unit_Tabs:
    def __init__(self):

        self.dims = Dims()

        # Font
        self.f_size      = 14
        self.f_color     = addon.preference().color.Hops_UI_text_color
        self.font_height = get_blf_text_dims("123456789.", self.f_size)[1]

        # Text
        self.text = ""

        # Colors
        self.cell_bg_color = addon.preference().color.Hops_UI_cell_background_color
        self.hover_color   = addon.preference().color.Hops_UI_mouse_over_color
        self.border_color  = addon.preference().color.Hops_UI_border_color

        # Scale / Padding
        self.scale_factor = dpi_factor(min=.25)
        self.padding      = 8 * self.scale_factor

        # States
        self.mouse_over = False
        self.active = False
        self.just_clicked = False


    def update(self, context, event):
        
        mouse_pos = (event.mouse_region_x, event.mouse_region_y)
        mouse_over = is_mouse_in_quad((self.dims.top_left, self.dims.bot_left, self.dims.top_right, self.dims.bot_right), mouse_pos)
        if mouse_over:
            self.mouse_over = True
        else:
            self.mouse_over = False

        if self.mouse_over:
            if event.type == 'LEFTMOUSE' and event.value == "PRESS":
                self.just_clicked = True
                self.active == True
            else:
                self.just_clicked = False


    def draw_2d(self):

        # Top Left, Bottom Left, Top Right, Bottom Right
        color = self.hover_color if self.mouse_over or self.active else self.cell_bg_color
        render_quad(quad=(self.dims.top_left, self.dims.bot_left, self.dims.top_right, self.dims.bot_right), color=color, bevel_corners=True)

        # Top Left, Bottom Left, Top Right, Bottom Right
        draw_border_lines(vertices=[self.dims.top_left, self.dims.bot_left, self.dims.top_right, self.dims.bot_right], width=1, color=self.border_color, format_lines=True)

        # Dims text
        padding = ((self.dims.top_left[1] - self.dims.bot_left[1]) - self.font_height) * .5

        pos = (self.dims.bot_left[0] + self.padding, self.dims.bot_left[1] + padding)
        render_text(text=self.text, position=pos, size=self.f_size, color=self.f_color)


class Length_Box:
    def __init__(self):

        self.dims = Dims()

        # Font
        self.f_size      = 14
        self.f_color     = addon.preference().color.Hops_UI_text_color
        self.font_height = get_blf_text_dims("Qtji.", self.f_size)[1]

        # Units
        self.metric_opts   = ["Kilometers", "Meters", "Centimeters", "Millimeters", "Micrometers"]
        self.imperial_opts = ["Miles", "Feet", "Inches", "Thousandth"]

        # Colors
        self.cell_bg_color = addon.preference().color.Hops_UI_cell_background_color
        self.hover_color   = addon.preference().color.Hops_UI_mouse_over_color
        self.border_color  = addon.preference().color.Hops_UI_border_color

        # Scale / Padding
        self.scale_factor = dpi_factor(min=.25)
        self.padding      = 12 * self.scale_factor

        # States
        self.mouse_over = False
        self.unit_system = "Imperial"
        self.metric_index = 1
        self.imperial_index = 1


    def update(self, context, event):
        
        mouse_pos = (event.mouse_region_x, event.mouse_region_y)
        self.mouse_over = is_mouse_in_quad((self.dims.top_left, self.dims.bot_left, self.dims.top_right, self.dims.bot_right), mouse_pos)

        if self.mouse_over:
            increment = 0
            if event.type == 'LEFTMOUSE' and event.value == "PRESS":
                increment = 1
            if event.type == 'WHEELUPMOUSE':
                increment = 1
            elif event.type == 'WHEELDOWNMOUSE':
                increment = -1

            if increment != 0:
                if self.unit_system == "Imperial":
                    if increment > 0:
                        if self.imperial_index < len(self.imperial_opts) - 1:
                            self.imperial_index += 1
                        else:
                            self.imperial_index = 0
                    elif increment < 0:
                        if self.imperial_index == 0:
                            self.imperial_index = len(self.imperial_opts) - 1
                        else:
                            self.imperial_index -= 1

                elif self.unit_system == "Metric":
                    if increment > 0:
                        if self.metric_index < len(self.metric_opts) - 1:
                            self.metric_index += 1
                        else:
                            self.metric_index = 0
                    elif increment < 0:
                        if self.metric_index == 0:
                            self.metric_index = len(self.metric_opts) - 1
                        else:
                            self.metric_index -= 1

        global ACTIVE_LENGTH
        if self.unit_system == "Imperial":
            ACTIVE_LENGTH = self.imperial_opts[self.imperial_index]

        elif self.unit_system == "Metric":
            ACTIVE_LENGTH = self.metric_opts[self.metric_index]


    def draw_2d(self):

        # Top Left, Bottom Left, Top Right, Bottom Right
        color = self.hover_color if self.mouse_over else self.cell_bg_color
        render_quad(quad=(self.dims.top_left, self.dims.bot_left, self.dims.top_right, self.dims.bot_right), color=color, bevel_corners=True)

        # Top Left, Bottom Left, Top Right, Bottom Right
        draw_border_lines(vertices=[self.dims.top_left, self.dims.bot_left, self.dims.top_right, self.dims.bot_right], width=1, color=self.border_color, format_lines=True)

        # Dims text
        padding = ((self.dims.top_left[1] - self.dims.bot_left[1]) - self.font_height) * .5

        pos = (self.dims.bot_left[0] + self.padding, self.dims.bot_left[1] + padding)
        render_text(text=ACTIVE_LENGTH, position=pos, size=self.f_size, color=self.f_color)


class Popup_Menu:
    def __init__(self, context):
        '''Draw the background and entry boxes for the pop up.'''

        # Bounds
        self.dims = Dims()

        # Font
        self.f_size = 14
        self.f_color = addon.preference().color.Hops_UI_text_color

        # Scale / Padding
        self.scale_factor = dpi_factor(min=.25)
        self.padding      = 12 * self.scale_factor
        self.font_height  = get_blf_text_dims("Qjq`", self.f_size)[1]

        # Colors
        self.highlight_color = addon.preference().color.Hops_UI_highlight_color
        self.cell_bg_color   = addon.preference().color.Hops_UI_cell_background_color
        self.border_color    = addon.preference().color.Hops_UI_border_color

        # Screen
        self.screen_width = context.area.width
        self.screen_height = context.area.height

        # Entry Boxes
        self.x_entry = Popup_Entry_Box()
        self.y_entry = Popup_Entry_Box()
        self.z_entry = Popup_Entry_Box()

        self.show_x, self.show_y, self.show_z = False, False, False
        self.txt_pos_y = 0
        self.txt_pos_x = 0
        self.txt_pos_z = 0

        # States
        self.just_opened = False
        self.open = False

    
    def update(self, context, event, op):

        set_first_call = False
        if self.just_opened:
            set_first_call = True
            self.just_opened = False

        def cleanup_exit():
            self.x_entry.locked = False
            self.x_entry.text = "0"
            self.x_entry.entry_string = ""

            self.y_entry.locked = False
            self.y_entry.text = "0"
            self.y_entry.entry_string = ""

            self.z_entry.locked = False
            self.z_entry.text = "0"
            self.z_entry.entry_string = ""

            self.open = False

        # Exit when clicking off the menu
        if set_first_call == False:
            mouse_pos = (event.mouse_region_x, event.mouse_region_y)
            if not is_mouse_in_quad((self.dims.top_left, self.dims.bot_left, self.dims.top_right, self.dims.bot_right), mouse_pos):
                if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
                    cleanup_exit()
                    return False
        
        self.open = True

        # Update all the entry boxes
        if op.dims_edit_index == 0:
            self.__setup_dims(context, x_label=True, y_label=True, z_label=True)

            self.x_entry.update(context, event, op, index=0, val='x', copy=set_first_call)
            if self.x_entry.tabbed_finish:
                self.x_entry.tabbed_finish = False
                self.y_entry.locked = True
                self.y_entry.skip_frame_for_tab = True
                
            self.y_entry.update(context, event, op, index=0, val='y', copy=set_first_call)
            if self.y_entry.tabbed_finish:
                self.y_entry.tabbed_finish = False
                self.z_entry.locked = True
                self.z_entry.skip_frame_for_tab = True

            self.z_entry.update(context, event, op, index=0, val='z', copy=set_first_call)
            if self.z_entry.tabbed_finish:
                self.z_entry.tabbed_finish = False
                cleanup_exit()
                return False
                
            return True

        elif op.dims_edit_index == 1:
            self.__setup_dims(context, x_label=True, y_label=True)

            self.x_entry.update(context, event, op, index=1, val='x', copy=set_first_call)
            if self.x_entry.tabbed_finish:
                self.x_entry.tabbed_finish = False
                self.y_entry.locked = True
                self.y_entry.skip_frame_for_tab = True

            self.y_entry.update(context, event, op, index=1, val='y', copy=set_first_call)
            if self.y_entry.tabbed_finish:
                self.y_entry.tabbed_finish = False
                cleanup_exit()
                return False

            return True

        elif op.dims_edit_index == 2:
            self.__setup_dims(context, z_label=True)

            self.z_entry.update(context, event, op, index=2, val='z', copy=set_first_call)
            if self.z_entry.tabbed_finish:
                self.z_entry.tabbed_finish = False
                cleanup_exit()
                return False

            return True


    def __setup_dims(self, context, x_label=False, y_label=False, z_label=False):

        # For drawing text
        self.show_x, self.show_y, self.show_z = x_label, y_label, z_label

        entry_count = 0
        if z_label:
            entry_count += 1
        if y_label:
            entry_count += 1
        if x_label:
            entry_count += 1

        # Text Samples
        num_sample   = '00000.00000'
        label_sample = 'XYZ'
        overall_sample = get_blf_text_dims(label_sample + num_sample, self.f_size)
        label_sample   = get_blf_text_dims(label_sample, self.f_size)
        num_sample     = get_blf_text_dims(num_sample, self.f_size)

        # Overall box dims
        overall_width    = overall_sample[0] + self.padding * 5
        overall_height   = self.padding * 2 + ((overall_sample[1] + self.padding * 2) * entry_count)
        overall_x_offset = (self.screen_width - overall_width) * .5
        overall_y_offset = (self.screen_height - overall_height) * .5

        # Entry boxes to build dims
        entry_width    = num_sample[0] + self.padding * 2
        entry_height   = num_sample[1] + self.padding * 2
        entry_x_offset = overall_x_offset + label_sample[0] + self.padding * 2

        entry_y_offset = overall_y_offset + self.padding

        if z_label:
            self.z_entry.setup_dims(width=entry_width, height=entry_height, x_offset=entry_x_offset, y_offset=entry_y_offset)
            self.txt_pos_z = entry_y_offset + self.padding
            entry_y_offset += self.padding * 3

        if y_label:
            self.y_entry.setup_dims(width=entry_width, height=entry_height, x_offset=entry_x_offset, y_offset=entry_y_offset)
            self.txt_pos_y = entry_y_offset + self.padding
            entry_y_offset += self.padding * 3

        if x_label:
            self.x_entry.setup_dims(width=entry_width, height=entry_height, x_offset=entry_x_offset, y_offset=entry_y_offset)
            self.txt_pos_x = entry_y_offset + self.padding

        # Build overall background
        self.dims.bot_left  = (overall_x_offset, overall_y_offset)
        self.dims.top_left  = (overall_x_offset, overall_y_offset + overall_height)
        self.dims.top_right = (overall_x_offset + overall_width, overall_y_offset + overall_height)
        self.dims.bot_right = (overall_x_offset + overall_width, overall_y_offset)


    def draw_2d(self):

        # Top Left, Bottom Left, Top Right, Bottom Right
        render_quad(quad=(self.dims.top_left, self.dims.bot_left, self.dims.top_right, self.dims.bot_right), color=self.cell_bg_color, bevel_corners=True)

        # Top Left, Bottom Left, Top Right, Bottom Right
        draw_border_lines(vertices=[self.dims.top_left, self.dims.bot_left, self.dims.top_right, self.dims.bot_right], width=1, color=self.border_color, format_lines=True)

        # Dims text
        if self.show_z:
            pos = (self.dims.bot_left[0] + self.padding, self.txt_pos_z)
            render_text(text='Z', position=pos, size=self.f_size, color=self.f_color)
            self.z_entry.draw_2d(self.padding)

        if self.show_y:
            pos = (self.dims.bot_left[0] + self.padding, self.txt_pos_y)
            render_text(text='Y', position=pos, size=self.f_size, color=self.f_color)
            self.y_entry.draw_2d(self.padding)

        if self.show_x:
            pos = (self.dims.bot_left[0] + self.padding, self.txt_pos_x)
            render_text(text='X', position=pos, size=self.f_size, color=self.f_color)
            self.x_entry.draw_2d(self.padding)


class Popup_Entry_Box:
    def __init__(self):

        # Bounds
        self.dims = Dims()

        # Font
        self.f_size = 16
        self.f_color = addon.preference().color.Hops_UI_text_color

        # Entry
        self.text = "0"
        self.entry_string = ""

        # Colors
        self.cell_bg_color   = addon.preference().color.Hops_UI_cell_background_color
        self.border_color    = addon.preference().color.Hops_UI_border_color
        self.hover_color     = addon.preference().color.Hops_UI_mouse_over_color

        # States
        self.mouse_over = False
        self.locked = False
        self.tabbed_finish = False
        self.skip_frame_for_tab = False


    def setup_dims(self, width=0, height=0, x_offset=0, y_offset=0):

        self.dims.bot_left  = (x_offset, y_offset)
        self.dims.top_left  = (x_offset, y_offset + height)
        self.dims.top_right = (x_offset + width, y_offset + height)
        self.dims.bot_right = (x_offset + width, y_offset)


    def update(self, context, event, op, index=0, val='', copy=False):
        
        if self.skip_frame_for_tab:
            self.skip_frame_for_tab = False
            return

        mouse_pos = (event.mouse_region_x, event.mouse_region_y)
        self.mouse_over = is_mouse_in_quad((self.dims.top_left, self.dims.bot_left, self.dims.top_right, self.dims.bot_right), mouse_pos)

        if index == 0:
            if val == 'x':
                if copy:
                    self.text = "{:.4f}".format(op.point_1[0])
                else:
                    self.__locked_state_update(event, op.point_1, val='x')
                    self.__scroll_val(event, op.point_1, val='x')

            elif val == 'y':
                if copy:
                    self.text = "{:.4f}".format(op.point_1[1])
                else:
                    self.__locked_state_update(event, op.point_1, val='y')
                    self.__scroll_val(event, op.point_1, val='y')

            elif val == 'z':
                if copy:
                    self.text = "{:.4f}".format(op.point_1[2])
                else:
                    self.__locked_state_update(event, op.point_1, val='z')
                    self.__scroll_val(event, op.point_1, val='z')
        
        elif index == 1:
            if val == 'x':
                if copy:
                    self.text = "{:.4f}".format(op.point_2[0])
                else:
                    self.__locked_state_update(event, op.point_2, val='x')
                    self.__scroll_val(event, op.point_2, val='x')

            elif val == 'y':
                if copy:
                    self.text = "{:.4f}".format(op.point_2[1])
                else:
                    self.__locked_state_update(event, op.point_2, val='y')
                    self.__scroll_val(event, op.point_2, val='y')

        elif index == 2:
            if val == 'z':
                if copy:
                    self.text = "{:.4f}".format(op.point_3[2])
                else:
                    self.__locked_state_update(event, op.point_3, val='z')
                    self.__scroll_val(event, op.point_3, val='z')

    
    def __scroll_val(self, event, vec_ref, val=''):

        if self.mouse_over == False or self.locked == True:
            return

        increment = 0        
        if event.type == 'WHEELUPMOUSE':
            increment = .125

        elif event.type == 'WHEELDOWNMOUSE':
            increment = -.125

        if increment != 0:
            if val == 'x':
                vec_ref[0] += increment
                self.text = "{:.4f}".format(vec_ref[0])
            elif val == 'y':
                vec_ref[1] += increment
                self.text = "{:.4f}".format(vec_ref[1])
            elif val == 'z':
                vec_ref[2] += increment
                self.text = "{:.4f}".format(vec_ref[2])


    def __locked_state_update(self, event, ref_vec, val=''):

        if self.locked:
            if val == 'x':
                if self.__capture_locked_entry(event):
                    set_val = 0
                    try:
                        set_val = float(self.entry_string)
                    except:
                        set_val = None
                    if set_val != None:
                        ref_vec[0] = set_val
                        self.text = "{:.4f}".format(set_val)
                    self.entry_string = ""
                
            elif val == 'y':
                if self.__capture_locked_entry(event):
                    set_val = 0
                    try:
                        set_val = float(self.entry_string)
                    except:
                        set_val = None
                    if set_val != None:
                        ref_vec[1] = set_val
                        self.text = "{:.4f}".format(set_val)
                    self.entry_string = ""
                
            elif val == 'z':
                if self.__capture_locked_entry(event):
                    set_val = 0
                    try:
                        set_val = float(self.entry_string)
                    except:
                        set_val = None
                    if set_val != None:
                        ref_vec[2] = set_val
                        self.text = "{:.4f}".format(set_val)
                    self.entry_string = ""

        if event.type == 'LEFTMOUSE' and event.value == "PRESS":
            if self.mouse_over:
                self.locked = True
            else:
                self.locked = False


    def __capture_locked_entry(self, event):

        valid = {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '.', '-'}

        if event.ascii in valid and event.value == 'PRESS':
            # Decimal
            decimal_blocked = False
            if '.' in self.entry_string and event.ascii == '.':
                decimal_blocked = True
            
            # Append text
            if decimal_blocked == False:
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

            self.locked = False
            return True

        elif event.type == 'BACK_SPACE' and event.value == 'PRESS':
            self.entry_string = self.entry_string[:-1]

        return False


    def draw_2d(self, padding=0):

        # Top Left, Bottom Left, Top Right, Bottom Right
        color = self.hover_color if self.mouse_over or self.locked else self.cell_bg_color
        render_quad(quad=(self.dims.top_left, self.dims.bot_left, self.dims.top_right, self.dims.bot_right), color=color, bevel_corners=True)

        # Top Left, Bottom Left, Top Right, Bottom Right
        draw_border_lines(vertices=[self.dims.top_left, self.dims.bot_left, self.dims.top_right, self.dims.bot_right], width=1, color=self.border_color, format_lines=True)

        # Dims text
        pos = (self.dims.bot_left[0] + padding, self.dims.bot_left[1] + padding)
        text = self.entry_string if self.locked else self.text
        render_text(text=text, position=pos, size=self.f_size, color=self.f_color)


class Face_Editor_Menu:
    def __init__(self, context):
        '''Draw the background and entry boxes for the pop up.'''

        # Bounds
        self.dims = Dims()

        # Font
        self.f_size = 16
        self.f_color = addon.preference().color.Hops_UI_text_color

        # Scale / Padding
        self.scale_factor = dpi_factor(min=.25)
        self.padding      = 12 * self.scale_factor
        self.font_height  = get_blf_text_dims("Qjq`", self.f_size)[1]

        # Colors
        self.highlight_color = addon.preference().color.Hops_UI_highlight_color
        self.cell_bg_color   = addon.preference().color.Hops_UI_cell_background_color
        self.border_color    = addon.preference().color.Hops_UI_border_color

        # Screen
        self.screen_width = context.area.width
        self.screen_height = context.area.height

        # Entry Boxes
        self.length = Face_Entry_Box()
        self.width  = Face_Entry_Box()

        self.txt_pos_length_y = 0
        self.txt_pos_width_y = 0

        # States
        self.just_opened = False
        self.open = False
        self.mouse_over = False
        self.locked = False

    
    def leaving(self):
        '''Called when modal needs to close this system down with no side effects.'''

        self.just_opened = False
        self.open = False
        self.mouse_over = False
        self.locked = False

        self.length.text = "0"
        self.length.entry_string = ""
        self.length.locked = False
        self.length.tabbed_finish = False
        self.length.skip_frame_for_tab = False

        self.width.text = "0"
        self.width.entry_string = ""
        self.width.locked = False
        self.width.tabbed_finish = False
        self.width.skip_frame_for_tab = False


    def update(self, context, event, op, face_controller):

        set_first_call = False
        if self.just_opened:
            set_first_call = True
            self.just_opened = False
        
        def cleanup_exit():
            self.length.locked = False
            self.length.text = "0"
            self.length.entry_string = ""

            self.width.locked = False
            self.width.text = "0"
            self.width.entry_string = ""

            self.open = False
            self.locked = False

        # Exit when clicking off the menu
        mouse_pos = (event.mouse_region_x, event.mouse_region_y)
        self.mouse_over = is_mouse_in_quad((self.dims.top_left, self.dims.bot_left, self.dims.top_right, self.dims.bot_right), mouse_pos)
        if set_first_call == False:
            if not self.mouse_over:
                if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
                    cleanup_exit()
                    return False
        
        self.open = True

        # Update all the entry boxes
        self.__setup_dims(context)

        self.length.update(event, op, 'LENGTH', face_controller)
        if self.length.tabbed_finish:
            self.length.tabbed_finish = False
            cleanup_exit()
            return False

        self.width.update(event, op, 'WIDTH', face_controller)
        if self.width.tabbed_finish:
            self.width.tabbed_finish = False
            self.length.locked = True
            self.length.skip_frame_for_tab = True

        if self.width.locked or self.length.locked:
            self.locked = True
        else:
            self.locked = False

        if face_controller.active != None:
            if self.length.locked == False:
                val = (face_controller.active.quad[0] - face_controller.active.quad[1]).magnitude * UNIT_SCALE_FACTOR
                self.length.text = "{:.3f}".format(val)

            if self.width.locked == False:
                val = (face_controller.active.quad[1] - face_controller.active.quad[2]).magnitude * UNIT_SCALE_FACTOR
                self.width.text = "{:.3f}".format(val)

        op.bounds_update()
        op.face_controller.build_quads(op)

        return True


    def __setup_dims(self, context):

        # Text Samples
        num_sample   = '00000.00000'
        label_sample = 'Length'
        overall_sample = get_blf_text_dims(label_sample + num_sample, self.f_size)
        label_sample   = get_blf_text_dims(label_sample, self.f_size)
        num_sample     = get_blf_text_dims(num_sample, self.f_size)

        # Overall box dims
        overall_width    = overall_sample[0] + self.padding * 5
        overall_height   = self.padding * 2 + ((overall_sample[1] + self.padding * 2) * 2)
        overall_x_offset = (self.screen_width - overall_width) * .5
        overall_y_offset = (self.screen_height - overall_height) * .5

        # Entry boxes to build dims
        entry_width    = num_sample[0] + self.padding * 2
        entry_height   = num_sample[1] + self.padding * 2
        entry_x_offset = overall_x_offset + label_sample[0] + self.padding * 2

        entry_y_offset = overall_y_offset + self.padding

        self.length.setup_dims(width=entry_width, height=entry_height, x_offset=entry_x_offset, y_offset=entry_y_offset)
        self.txt_pos_length_y = entry_y_offset + self.padding
        entry_y_offset += self.padding * 3

        self.width.setup_dims(width=entry_width, height=entry_height, x_offset=entry_x_offset, y_offset=entry_y_offset)
        self.txt_pos_width_y = entry_y_offset + self.padding

        # Build overall background
        self.dims.bot_left  = (overall_x_offset, overall_y_offset)
        self.dims.top_left  = (overall_x_offset, overall_y_offset + overall_height)
        self.dims.top_right = (overall_x_offset + overall_width, overall_y_offset + overall_height)
        self.dims.bot_right = (overall_x_offset + overall_width, overall_y_offset)


    def draw_2d(self):

        # Top Left, Bottom Left, Top Right, Bottom Right
        render_quad(quad=(self.dims.top_left, self.dims.bot_left, self.dims.top_right, self.dims.bot_right), color=self.cell_bg_color, bevel_corners=True)

        # Top Left, Bottom Left, Top Right, Bottom Right
        draw_border_lines(vertices=[self.dims.top_left, self.dims.bot_left, self.dims.top_right, self.dims.bot_right], width=1, color=self.border_color, format_lines=True)

        # Dims text
        pos = (self.dims.bot_left[0] + self.padding, self.txt_pos_length_y)
        render_text(text='Length', position=pos, size=self.f_size, color=self.f_color)
        self.length.draw_2d(self.padding)

        pos = (self.dims.bot_left[0] + self.padding, self.txt_pos_width_y)
        render_text(text='Width', position=pos, size=self.f_size, color=self.f_color)
        self.width.draw_2d(self.padding)


class Face_Entry_Box:
    def __init__(self):

        # Bounds
        self.dims = Dims()

        # Font
        self.f_size = 16
        self.f_color = addon.preference().color.Hops_UI_text_color

        # Entry
        self.text = "0"
        self.entry_string = ""

        # Colors
        self.cell_bg_color = addon.preference().color.Hops_UI_cell_background_color
        self.border_color  = addon.preference().color.Hops_UI_border_color
        self.hover_color   = addon.preference().color.Hops_UI_mouse_over_color

        # States
        self.mouse_over = False
        self.locked = False
        self.tabbed_finish = False
        self.skip_frame_for_tab = False


    def setup_dims(self, width=0, height=0, x_offset=0, y_offset=0):

        self.dims.bot_left  = (x_offset, y_offset)
        self.dims.top_left  = (x_offset, y_offset + height)
        self.dims.top_right = (x_offset + width, y_offset + height)
        self.dims.bot_right = (x_offset + width, y_offset)


    def update(self, event, op, val, face_controller):
        
        if self.skip_frame_for_tab:
            self.skip_frame_for_tab = False
            return

        mouse_pos = (event.mouse_region_x, event.mouse_region_y)
        self.mouse_over = is_mouse_in_quad((self.dims.top_left, self.dims.bot_left, self.dims.top_right, self.dims.bot_right), mouse_pos)

        if self.locked == True:
            self.__locked_state_update(event, op, val, face_controller)
        else:
            self.__scroll_val(event, op, val, face_controller)

        if event.type == 'LEFTMOUSE' and event.value == "PRESS":
            if self.mouse_over:
                self.locked = True
            else:
                self.locked = False


    def __scroll_val(self, event, op, val, face_controller):

        if self.mouse_over == False or self.locked == True: return

        increment = 0        
        if event.type == 'WHEELUPMOUSE':
            increment = .125 * UNIT_SCALE_FACTOR
        elif event.type == 'WHEELDOWNMOUSE':
            increment = -.125 * UNIT_SCALE_FACTOR

        if increment != 0:
            if val == 'LENGTH':
                face_controller.active.set_face_length(op, val, set_val=increment, use_increment=True)
            elif val == 'WIDTH':
                face_controller.active.set_face_width(op, val, set_val=increment, use_increment=True)
  

    def __locked_state_update(self, event, op, val, face_controller):

        if self.__capture_locked_entry(event):
            set_val = 0

            try:
                set_val = float(self.entry_string) / UNIT_SCALE_FACTOR
            except:
                set_val = None

            if set_val != None:
                if val == 'LENGTH':
                    face_controller.active.set_face_length(op, val, set_val)
                elif val == 'WIDTH':
                    face_controller.active.set_face_width(op, val, set_val)

                self.text = "{:.4f}".format(set_val)

            self.entry_string = ""


    def __capture_locked_entry(self, event):

        valid = {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '.', '-'}

        if event.ascii in valid and event.value == 'PRESS':
            # Decimal
            decimal_blocked = False
            if '.' in self.entry_string and event.ascii == '.':
                decimal_blocked = True
            
            # Append text
            if decimal_blocked == False:
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

            self.locked = False
            return True

        elif event.type == 'BACK_SPACE' and event.value == 'PRESS':
            self.entry_string = self.entry_string[:-1]

        return False


    def draw_2d(self, padding=0):
        color = self.hover_color if self.mouse_over or self.locked else self.cell_bg_color
        render_quad(quad=(self.dims.top_left, self.dims.bot_left, self.dims.top_right, self.dims.bot_right), color=color, bevel_corners=True)
        draw_border_lines(vertices=[self.dims.top_left, self.dims.bot_left, self.dims.top_right, self.dims.bot_right], width=1, color=self.border_color, format_lines=True)

        pos = (self.dims.bot_left[0] + padding, self.dims.bot_left[1] + padding)
        text = self.entry_string if self.locked else self.text
        render_text(text=text, position=pos, size=self.f_size, color=self.f_color)


class Face_Data:
    def __init__(self, label):
        self.label = label
        self.quad = []
        self.draw_indices = [(0,1,2), (0,2,3)]
        self.distance_to_center = -1
        self.center = Vector((0,0,0))


    def update(self, context, event):

        self.center = hops_math.coords_to_center(self.quad)
        casted_point = get_2d_point_from_3d_point(context, self.center)
        mouse_pos = Vector((event.mouse_region_x, event.mouse_region_y))

        if casted_point == None:
            self.distance_to_center = -1
            return

        self.distance_to_center = (casted_point - mouse_pos).magnitude


    def set_face_length(self, op, val, set_val=0, use_increment=False):

        center = hops_math.coords_to_center(self.quad)

        if self.label in {"TOP", "BOTTOM", "FRONT", "BACK"}:
            if use_increment == True:
                if op.equalize:
                    set_val += op.length
                    op.set_length_equalized(set_val)
                else:
                    op.point_2[0] += set_val

            elif op.equalize:
                op.set_length_equalized(set_val)

            else:
                sign = 1 if op.point_2[0] > op.point_1[0] else -1
                op.point_2[0] = op.point_1[0] + set_val * sign

        elif self.label in {"LEFT", "RIGHT"}:
            if use_increment == True:
                if op.equalize:
                    set_val += op.width
                    op.set_width_equalized(set_val)
                else:
                    op.point_2[1] += set_val

            elif op.equalize:
                op.set_width_equalized(set_val)

            else:
                sign = 1 if op.point_2[1] > op.point_1[1] else -1
                op.point_2[1] = op.point_1[1] + set_val * sign

        self.recenter_face(op, center)


    def set_face_width(self, op, val, set_val=0, use_increment=False):

        center = hops_math.coords_to_center(self.quad)

        if self.label in {"LEFT", "RIGHT", "FRONT", "BACK"}:
            if use_increment == True:
                if op.equalize:
                    set_val += op.height
                    op.set_height_equalized(set_val)
                else:
                    op.point_3[2] += set_val

            elif op.equalize:
                op.set_height_equalized(set_val)

            else:
                sign = 1 if op.point_3[2] > op.point_1[2] else -1
                op.point_3[2] = op.point_1[2] + set_val * sign

        elif self.label in {"TOP", "BOTTOM"}:
            if use_increment == True:
                if op.equalize:
                    set_val += op.width
                    op.set_width_equalized(set_val)
                else:
                    op.point_2[1] += set_val

            elif op.equalize:
                op.set_width_equalized(set_val)

            else:
                sign = 1 if op.point_2[1] > op.point_1[1] else -1
                op.point_2[1] = op.point_1[1] + set_val * sign

        self.recenter_face(op, center)


    def recenter_face(self, op, old_center=Vector((0,0,0))):
        
        op.bounds_update()
        op.face_controller.build_quads(op)

        new_center = hops_math.coords_to_center(self.quad)
        diff = new_center - old_center
        op.point_1 -= diff
        op.point_2 -= diff
        op.point_3 -= diff


class Face_Controller:
    def __init__(self, context, op):

        # Face Data
        self.active = None
        self.top   = Face_Data(label="TOP")
        self.bot   = Face_Data(label="BOTTOM")
        self.left  = Face_Data(label="LEFT")
        self.right = Face_Data(label="RIGHT")
        self.front = Face_Data(label="FRONT")
        self.back  = Face_Data(label="BACK")

        # Menu
        self.menu = Face_Editor_Menu(context)

        # Drawing
        self.f_color = addon.preference().color.Hops_UI_text_color

        # States
        self.entry_locked = False

        # Build initial data
        self.build_quads(op)


    def leaving(self):
        self.menu.leaving()


    def build_quads(self, op):
        bounds = op.bounds
        self.top.quad   = [ bounds.top_front_left, bounds.top_front_right, bounds.top_back_right , bounds.top_back_left  ]
        self.bot.quad   = [ bounds.bot_front_left, bounds.bot_front_right, bounds.bot_back_right , bounds.bot_back_left  ]
        self.left.quad  = [ bounds.bot_back_left , bounds.bot_front_left , bounds.top_front_left , bounds.top_back_left  ]
        self.right.quad = [ bounds.bot_back_right, bounds.bot_front_right, bounds.top_front_right, bounds.top_back_right ]
        self.front.quad = [ bounds.bot_front_left, bounds.bot_front_right, bounds.top_front_right, bounds.top_front_left ]
        self.back.quad  = [ bounds.bot_back_left , bounds.bot_back_right,  bounds.top_back_right , bounds.top_back_left  ]


    def update(self, context, event, op):

        self.build_quads(op)
        faces = [ self.top, self.bot, self.left, self.right, self.front, self.back ]

        # Build distnaces
        for face in faces:
            face.update(context, event)

        # Run menu
        if self.entry_locked == True:
            self.entry_locked = self.menu.update(context, event, op, self)
            return
        else:
            self.menu.mouse_over = False

        # Get closest
        closest = None
        compare = None
        for face in faces:
            if compare == None:
                if face.distance_to_center > 0:
                    closest = face
                    compare = face.distance_to_center
            else:
                if face.distance_to_center > 0:
                    if face.distance_to_center < compare:
                        closest = face
                        compare = face.distance_to_center

        # Set active
        if closest != None:
            self.active = closest

        # Set lock
        if self.entry_locked == False and op.static_menu.mouse_is_over == False:
            if event.type == 'LEFTMOUSE':
                if self.active != None:
                    if event.value == 'RELEASE' and event.ctrl == True:
                        op.anchor = self.active.label
                        op.anchor_loc = self.active = hops_math.coords_to_center(self.active.quad)
                        op.state = State.ADJUST
                        op.scale_index = None
                        op.scaling_point = False
                        self.entry_locked = False
                    elif event.value == 'PRESS' and event.ctrl == False:
                        self.entry_locked = True
                        self.menu.just_opened = True
                        op.anchor = "DEFAULT"


    def get_all_verts_indices(self):
        '''Function to get all the verts and indices for modal.'''

        faces   = [ self.top, self.bot, self.left, self.right, self.front, self.back ]
        verts   = []
        indices = []

        indices_offset = 0
        for face in faces:
            verts.extend(face.quad)
            indices.append( ( 0 + indices_offset, 1 + indices_offset, 2 + indices_offset ) )
            indices.append( ( 0 + indices_offset, 2 + indices_offset, 3 + indices_offset ) )
            indices_offset += 4

        return verts, indices


    def draw_2d(self, context):

        if self.entry_locked:
            self.menu.draw_2d()

        if not self.active or not self.active.quad: return

        padding = 10 * dpi_factor(min=.25)
        p1 = get_2d_point_from_3d_point(context, (self.active.quad[0] + self.active.quad[1]) * .5)
        p2 = get_2d_point_from_3d_point(context, (self.active.quad[1] + self.active.quad[2]) * .5)

        if p1:
            pos = (p1[0] + padding, p1[1] + padding)
            val = (self.active.quad[0] - self.active.quad[1]).magnitude * UNIT_SCALE_FACTOR
            text = "Length : {:.3f}".format(val)
            render_text(text=text, position=pos, size=14, color=self.f_color)

        if p2:
            pos = (p2[0] + padding, p2[1] + padding)
            val = (self.active.quad[1] - self.active.quad[2]).magnitude * UNIT_SCALE_FACTOR
            text = "Width : {:.3f}".format(val)
            render_text(text=text, position=pos, size=14, color=self.f_color)


    def draw_3d(self):

        if not self.active or not self.active.quad:
            return

        built_in_shader = 'UNIFORM_COLOR' if bpy.app.version[0] >=4 else '3D_UNIFORM_COLOR'
        shader = gpu.shader.from_builtin(built_in_shader)
        batch = batch_for_shader(shader, 'TRIS', {'pos': self.active.quad}, indices=self.active.draw_indices)
        shader.bind()
        shader.uniform_float('color', (0,0,1,.25))
        #Enable(GL_LINE_SMOOTH)
        gpu.state.blend_set('ALPHA')
        batch.draw(shader)
        del shader
        del batch

        built_in_shader = 'UNIFORM_COLOR' if bpy.app.version[0] >=4 else '3D_UNIFORM_COLOR'
        shader = gpu.shader.from_builtin(built_in_shader)
        batch = batch_for_shader(shader, 'POINTS', {'pos': [self.active.center]})
        shader.bind()
        shader.uniform_float('color', (1,0,0,1))
        gpu.state.blend_set('ALPHA')
        gpu.state.point_size_set(8)
        batch.draw(shader)
        del shader
        del batch


description = """Accu Shape V1
Allows for semi-accurate scaling or drawing
Selection - Interactive dimension system for rescaling
No Selection - Box Creation utilizing accushape
Shift - Use the active object as the bounds
Press H for help"""

class HOPS_OT_Accu_Shape(bpy.types.Operator):
    bl_idname = "hops.accu_shape"
    bl_label = "Accu Shape"
    bl_description = description
    bl_options = {"REGISTER", "UNDO", "BLOCKING"}

    def invoke(self, context, event):

        self.objs = [ob for ob in context.selected_objects if ob.type in {'MESH', 'CURVE', 'FONT', 'SURFACE'}]

        # Data
        self.build_static_data()

        # Menu Systems
        self.face_controller = Face_Controller(context, self)
        self.static_menu = Static_Menu(context)
        self.popup_menu = Popup_Menu(context)
        self.__length = 0.0
        self.__width  = 0.0
        self.__height = 0.0

        # States
        self.build_state_data()

        # Anchor Point
        self.anchor = "DEFAULT"
        self.anchor_loc = Vector((0,0,0))

        # Exit / Init
        self.add_cube = True if len(self.objs) == 0 else False
        if self.add_cube == False:
            self.set_initial_points(context, event)

        if bpy.context.scene.unit_settings.scale_length != 1.0:
            bpy.ops.hops.display_notification(info="Warning: Unit Scale is not set to 1.0")

        # Base Systems
        self.master = Master(context=context)
        self.master.only_use_fast_ui = True
        self.base_controls = Base_Modal_Controls(context, event)
        self.original_tool_shelf, self.original_n_panel = collapse_3D_view_panels()
        self.draw_handle_2D = bpy.types.SpaceView3D.draw_handler_add(self.safe_draw_2D, (context,), 'WINDOW', 'POST_PIXEL')
        self.draw_handle_3D = bpy.types.SpaceView3D.draw_handler_add(self.safe_draw_3D, (context,), 'WINDOW', 'POST_VIEW')
        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}


    def build_static_data(self):
        self.point_1 = None
        self.point_2 = None
        self.point_3 = None
        self.bounds = Bounds()
        self.initial_center_point = Vector((0,0,0))
        self.initial_extents = Vector((0,0,0))
        self.scale_factor = dpi_factor(min=.25)
        self.radius = 42 * self.scale_factor


    def build_state_data(self):
        self.state = State.POINT_1
        self.mouse_dragging = False
        self.points_edit_locked = False
        self.points_edit_index = None
        self.dims_change_circle_color = False
        self.dims_edit_locked = False
        self.dims_edit_index = None
        self.ctrl_adjusting_circles = False
        self.scale_index = None
        self.scaling_point = False
        self.equalize = True if len(self.objs) > 0 else False
        self.keep_at_center = True if len(self.objs) > 0 else False
        self.show_solid_view = False
        self.exit_with_empty = False
        self.use_edit_mode = False
        self.use_vert_snap = False # Snap to verts when adjusting points

    @property
    def length(self):
        if self.point_1 and self.point_2:
            self.length = abs(self.point_1[0] - self.point_2[0])
        return self.__length

    @length.setter
    def length(self, var):
        if self.point_1 and self.point_2:
            length = abs(self.point_1[0] - self.point_2[0])
            diff = length - var
            if self.equalize:
                self.equalize_dims(val=diff)
            else:
                self.point_2[0] -= diff
        self.__length = round(var, 4)
        self.bounds_update()

    @property
    def width(self):
        if self.point_1 and self.point_2:
            self.width = abs(self.point_1[1] - self.point_2[1])
        return self.__width

    @width.setter
    def width(self, var):
        if self.point_1 and self.point_2:
            width = abs(self.point_1[1] - self.point_2[1])
            diff = width - var
            if self.equalize:
                self.equalize_dims(val=diff)
            else:
                self.point_2[1] -= diff
        self.__width = round(var, 4)
        self.bounds_update()

    @property
    def height(self):
        if self.point_1 and self.point_3:
            self.height = abs(self.point_1[2] - self.point_3[2])
        return self.__height

    @height.setter
    def height(self, var):
        if self.point_1 and self.point_3:
            height = abs(self.point_1[2] - self.point_3[2])
            diff = height - var
            if self.equalize:
                self.equalize_dims(val=diff)
            else:
                self.point_3[2] -= diff
        self.__height = round(var, 4)
        self.bounds_update()


    def modal(self, context, event):

        #--- Base Systems ---#
        self.master.receive_event(event=event)
        self.base_controls.update(context, event)

        # Warp mouse
        if self.state == State.SCALE:
            if self.scaling_point:
                mouse_warp(context, event)

        # Update menus
        if event.type != "TIMER":
            if self.state in {State.ADJUST, State.FACE}:
                self.static_menu.update(context, event, self)
                self.set_unit_scale(context)

        # Cancel
        if self.base_controls.cancel:
            self.remove_shaders()
            collapse_3D_view_panels(self.original_tool_shelf, self.original_n_panel)
            self.master.run_fade()
            return {'CANCELLED'}

        # Confirm
        elif event.type in {'RET', 'SPACE'} and event.value == 'PRESS':
            if self.static_menu.input_locked == False:
                if self.popup_menu.open == False:
                    if self.face_controller.menu.locked == False:

                        self.confirmed_exit(context)
                        self.remove_shaders()
                        collapse_3D_view_panels(self.original_tool_shelf, self.original_n_panel)
                        self.master.run_fade()
                        return {'FINISHED'}
        
        # Finish Button
        if self.static_menu.fin_button_clicked:
            self.confirmed_exit(context)
            self.remove_shaders()
            collapse_3D_view_panels(self.original_tool_shelf, self.original_n_panel)
            self.master.run_fade()
            return {'FINISHED'}

        # Pass Options
        if self.static_menu.input_locked == False:
            if self.static_menu.mouse_is_over == False:
                if self.face_controller.menu.mouse_over == False:
                    if self.popup_menu.open == False:
                        if event.type in {'Z', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE', 'MIDDLEMOUSE'}:
                            if event.ctrl and event.type == 'Z':
                                pass
                            else:
                                return {'PASS_THROUGH'}

        # Mouse dragging
        if event.type == 'LEFTMOUSE':
            self.mouse_dragging = False if event.value == "RELEASE" else True

        # 3D Mouse
        if 'NDOF' in event.type:
            return {'PASS_THROUGH'}

        # Circle color
        if self.state == State.ADJUST:
            # Display dims edit state
            if (event.shift or self.dims_edit_locked) and self.points_edit_locked == False and self.ctrl_adjusting_circles == False:
                self.dims_change_circle_color = True
            else:
                self.dims_change_circle_color = False

            # Display ctrl circles
            if self.dims_change_circle_color == False and self.points_edit_locked == False and event.ctrl:
                self.ctrl_adjusting_circles = True
            else:
                self.ctrl_adjusting_circles = False

        # Release locked states
        if self.mouse_dragging == False:
            self.points_edit_locked = False
            self.points_edit_index = None

        # Scale mode
        if event.type == 'S' and event.value == 'PRESS':
            if self.state in {State.ADJUST, State.FACE}:
                self.state = State.SCALE
                self.anchor = "DEFAULT"

                # Reset face 
                self.scale_index = None
                self.scaling_point = False
                self.face_controller.leaving()

                # Auto turn off for this mode
                self.keep_at_center = False
                msg = "Keep Center : OFF"
                bpy.ops.hops.display_notification(info=msg)

            elif self.state == State.SCALE:
                self.state = State.ADJUST

            self.scale_index = None
            self.scaling_point = False

        # Face mode
        elif event.type == 'F' and event.value == 'PRESS':
            if self.state in {State.ADJUST, State.SCALE}:
                self.state = State.FACE

                # Reset face 
                self.scale_index = None
                self.scaling_point = False
                self.face_controller.leaving()

                # Auto turn off for this mode
                self.keep_at_center = False
                msg = "Keep Center : OFF (Ctrl Click a face to set as Anchor)"
                bpy.ops.hops.display_notification(info=msg)

            elif self.state == State.FACE:
                self.state = State.ADJUST
                self.face_controller.leaving()

        # Adjust mode
        elif event.type == 'A' and event.value == 'PRESS':
            if self.state in {State.SCALE, State.FACE}:
                self.state = State.ADJUST
                self.scale_index = None
                self.scaling_point = False
                self.face_controller.entry_locked = False

        # Equalize
        elif event.type == 'E' and event.value == 'PRESS':
            if event.shift:
                self.exit_with_empty = not self.exit_with_empty
                msg = "Exit With Empty : ON" if self.exit_with_empty else "Exit With Empty : OFF"
                bpy.ops.hops.display_notification(info=msg)
            else:
                self.equalize = not self.equalize
                msg = "Equalize : ON" if self.equalize else "Equalize : OFF"
                bpy.ops.hops.display_notification(info=msg)

        # Recenter
        elif event.type == 'C' and event.value == 'PRESS':
            if event.shift:
                self.keep_at_center = not self.keep_at_center
                msg = "Keep Center : ON" if self.keep_at_center else "Keep Center : OFF"
                bpy.ops.hops.display_notification(info=msg)

            if self.state in (State.ADJUST, State.SCALE, State.FACE):
                self.recenter_points()

        # Show solid shade
        elif event.type == 'G' and event.value == 'PRESS':
            if self.state not in {State.POINT_1, State.POINT_2, State.POINT_3}:
                self.show_solid_view = not self.show_solid_view

        # Show solid shade
        elif event.type == 'V' and event.value == 'PRESS':
            self.use_vert_snap = not self.use_vert_snap
            msg = "Vert Snap : ON" if self.use_vert_snap else "Vert Snap : OFF"
            bpy.ops.hops.display_notification(info=msg)

        # Restart from step one
        elif event.type == 'R' and event.value == 'PRESS':
            self.build_static_data()
            self.build_state_data()
            self.face_controller.leaving()

        #--- Modal Controls ---#
        if event.type != 'TIMER':
            if self.show_solid_view:
                if self.state != State.FACE:
                    self.face_controller.build_quads(self)

            if self.static_menu.input_locked == False and self.static_menu.mouse_is_over == False:
                self.update(context, event)

        # Continue to recenter
        if self.keep_at_center == True:
            if self.state in (State.ADJUST, State.SCALE, State.FACE):
                if self.static_menu.input_locked == False and self.popup_menu.open == False:
                    self.recenter_points()

        self.draw_master(context=context)
        context.area.tag_redraw()
        return {"RUNNING_MODAL"}


    def draw_master(self, context):
        self.master.setup()
        if self.master.should_build_fast_ui():
            
            # Main
            win_list = []            
            if addon.preference().ui.Hops_modal_fast_ui_loc_options != 1:
                if self.state in {State.POINT_1, State.POINT_2, State.POINT_3}:
                    win_list.append("Click to Confirm")
                elif self.state == State.ADJUST:
                    win_list.append("Adjust Mode")
                elif self.state == State.SCALE:
                    win_list.append("Scale Mode")
                elif self.state == State.FACE:
                    win_list.append("Face Mode")
            else:
                win_list.append("Accu Shape")
                if self.state == State.POINT_1:
                    win_list.append("A : Autobox")
                    win_list.append("Click to Confirm")
                elif self.state == State.POINT_2:
                    win_list.append("Click to Confirm")
                elif self.state == State.POINT_3:
                    win_list.append("Click to Confirm")
                elif self.state == State.ADJUST:
                    win_list.append("Adjust Mode")
                    if self.points_edit_locked:
                        if self.points_edit_index == 0:
                            win_list.append("Ctrl : Raycast")
                        elif self.points_edit_index == 1:
                            win_list.append("Shift : Equalize")
                            win_list.append("Ctrl : Raycast")
                        elif self.points_edit_index == 2:
                            win_list.append("Ctrl : Raycast")
                    if self.points_edit_locked == False and self.dims_edit_locked == False and self.ctrl_adjusting_circles == False:
                        win_list.append("Drag : Adjust Point")
                        win_list.append("Shift : Manual Edit")
                        win_list.append("Ctrl : Move Box")
                elif self.state == State.SCALE:
                    win_list.append("Drag points")
                    win_list.append("Scale Mode")
                elif self.state == State.FACE:
                    win_list.append("Face Mode")

            # Help
            help_items = {"GLOBAL" : [], "STANDARD" : []}

            help_items["GLOBAL"] = [
                ("M", "Toggle mods list"),
                ("H", "Toggle help"),
                ("~", "Toggle UI Display Type"),
                ("O", "Toggle viewport rendering")]

            h_append = help_items["STANDARD"].append

            # Help
            if self.state == State.POINT_1:
                h_append(["A", "Drop a 1x1x1 box at location"])
                h_append(["Ctrl", "Raycast point to objects"])
                h_append(["Click", "Confirm first corner"])
            elif self.state == State.POINT_2:
                h_append(["Shift", "Equalize sides"])
                h_append(["Ctrl",  "Raycast point to objects"])
                h_append(["Click", "Confirm second corner"])
            elif self.state == State.POINT_3:
                h_append(["Ctrl", "Raycast point to objects"])
                h_append(["Click", "Confirm height"])
            elif self.state == State.ADJUST:
                h_append(["S", "Switch to Scale Mode"])
                h_append(["Ctrl", "Toggle move entire box"])
                h_append(["Ctrl", "Raycast point to objects (While Adjusting)"])
                h_append(["", "Scroll / Type in dimensions menu to adjust"])
                h_append(["", "Shift click circles (manual adjust)"])
                h_append(["", "Drag circles to adjust"])
            elif self.state == State.SCALE:
                h_append(["A", "Go to Adjust Mode"])
                h_append(["S", "Switch to Adjust Mode"])
                h_append(["", "Click drag from points"])
            elif self.state == State.FACE:
                h_append(["Ctrl Click", "Set face as Anchor for Dims"])
                h_append(["A", "Go to Adjust Mode"])
                h_append(["", "Click faces to edit"])

            h_append(["", "_____ Tool _____"])

            h_append(["", ""])
            h_append(["Shift C", "Keep at center toggle"])
            h_append(["R", "Restart operations"])
            h_append(["V", "Toggle vert snap"])
            if self.state not in {State.POINT_1, State.POINT_2, State.POINT_3}:
                h_append(["G", "Toggle solid shade"])
            h_append(["F", "Toggle Face edit"])
            h_append(["C", "Recenter box to selection"])
            h_append(["Shift E", "Toggle exit with empty"])
            h_append(["E", "Dimensions Equalize"])
            h_append(["Z", "Shading options"])
            h_append(["", "_____ Base _____"])

            self.master.receive_fast_ui(win_list=win_list, help_list=help_items, image="Display_boolshapes")
        self.master.finished()

    ####################################################
    #   MODAL FUNCTIONS
    ####################################################

    def update(self, context, event):
        
        if self.state == State.POINT_1:
            self.point_one_update(context, event)
        elif self.state == State.POINT_2:
            self.point_two_update(context, event)
        elif self.state == State.POINT_3:
            self.point_three_update(context, event)
        elif self.state == State.ADJUST:
            self.adjust_update(context, event)
        elif self.state == State.SCALE:
            self.adjust_scale(context, event)
        elif self.state == State.FACE:
            self.adjust_face(context, event)

        self.bounds_update()


    def point_one_update(self, context, event, with_confirm=True):
        
        point = Vector((0,0,0))

        if self.use_vert_snap:
            point = self.cast_to_verts(context, event)

        elif event.ctrl:
            point, hit = self.cast_to_surface(context, event)
            if not hit:
                return

        else:
            loc = Vector((0,0,0)) if self.point_1 == None else Vector((0,0,self.point_1[2]))
            point = self.cast_to_plane(context, event, loc, Vector((0,0,1)))

        if point != None:
            self.point_1 = point.copy()

            if with_confirm:
                if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
                    self.state = State.POINT_2

                elif event.type == 'A' and event.value == 'PRESS':
                    self.point_2 = Vector((self.point_1[0] + 1, self.point_1[1] + 1, self.point_1[2]))
                    self.point_3 = Vector((self.point_2[0], self.point_2[1], self.point_2[2] + 1))

                    bounds = hops_math.coords_to_bounds([self.point_1, self.point_2, self.point_3])
                    self.initial_center_point = hops_math.coords_to_center(bounds)

                    self.state = State.ADJUST


    def point_two_update(self, context, event, with_confirm=True):

        point = Vector((0,0,0))

        if self.use_vert_snap:
            point = self.cast_to_verts(context, event)

        elif event.ctrl:
            point, hit = self.cast_to_surface(context, event)
            if not hit:
                return
        
        else:
            point = self.cast_to_plane(context, event, self.point_1, Vector((0,0,1)))

        if point != None:
            point[2] = self.point_1[2]

            if event.shift:
                length = abs(self.point_1[0] - point[0])
                width  = abs(self.point_1[1] - point[1])

                if length > width:
                    sign = 1 if point[1] - self.point_1[1] > 0 else -1
                    point[1] = self.point_1[1] + (length * sign)

                elif width > length:
                    sign = 1 if point[0] - self.point_1[0] > 0 else -1
                    point[0] = self.point_1[0] + (width * sign)

                self.point_2 = point.copy()

            else:
                self.point_2 = point.copy()

            if with_confirm:
                if event.type == 'LEFTMOUSE' and event.value == "PRESS":
                    self.state = State.POINT_3


    def point_three_update(self, context, event, with_confirm=True):

        point = Vector((0,0,0))

        if self.use_vert_snap:
            point = self.cast_to_verts(context, event)

        elif event.ctrl:
            point, hit = self.cast_to_surface(context, event)
            if not hit:
                return

        else:
            center = (self.point_1 + self.point_2) * .5

            view_quat = context.region_data.view_rotation
            up = Vector((0,0,1))
            view_normal = view_quat @ up
            view_normal[2] = 0
            view_normal.normalize()

            point = self.cast_to_plane(context, event, center, view_normal)
            point[0] = center[0]
            point[1] = center[1]

        if point != None:
            self.point_3 = point.copy()

            if with_confirm:
                if event.type == 'LEFTMOUSE' and event.value == "PRESS":
                    self.state = State.ADJUST

                    bounds = hops_math.coords_to_bounds([self.point_1, self.point_2, self.point_3])
                    self.initial_center_point = hops_math.coords_to_center(bounds)
                    self.initial_extents = hops_math.dimensions(bounds)

    # State = ADJUST
    def adjust_update(self, context, event):
        
        if self.points_edit_locked == False and self.dims_edit_locked == False:
            if self.mouse_dragging == False:
                return

            if event.ctrl:
                if self.keep_at_center:
                    bpy.ops.hops.display_notification(info="Turn off keep at center : Shift C")
                self.move_entire_box(context, event)
            else:
                self.capture_adjust_states(context, event)

        if self.points_edit_locked:
            self.adjust_points(context, event)
        
        elif self.dims_edit_locked:
            self.adjust_dims(context, event)

    # Look for point to move
    def capture_adjust_states(self, context, event):

        point_1 = get_2d_point_from_3d_point(context, self.point_1)
        point_2 = get_2d_point_from_3d_point(context, self.point_2)
        point_3 = get_2d_point_from_3d_point(context, self.point_3)
        points = [ point_1, point_2, point_3 ]
        mouse_pos = Vector((event.mouse_region_x, event.mouse_region_y))

        index = None
        compare = None
        for i, point in enumerate(points):
            if point != None:
                mag = (mouse_pos - point).magnitude
                if compare == None:
                    compare = mag
                    index = i                    
                elif mag < compare:
                    compare = mag
                    index = i

        if compare != None:
            if compare >= self.radius:
                return

        # Assign states
        if index != None:
            self.anchor = "DEFAULT"
            # Assign locked state for : DIMS ADJUST
            if event.shift:
                self.dims_edit_locked = True
                self.dims_edit_index = index
                self.popup_menu.just_opened = True

            # Assign locked state for : POINT ADJUST
            else:
                self.points_edit_locked = True
                self.points_edit_index = index

    # Ctrl move
    def move_entire_box(self, context, event):

        point = self.cast_to_plane(context, event, self.point_1, Vector((0,0,1)))
        if point == None:
            return

        self.anchor = "DEFAULT"

        diff = point - self.point_1

        self.point_1 = point
        self.point_2 += diff
        self.point_3 += diff

    # Dragging point
    def adjust_points(self, context, event):

        if self.points_edit_index == 0:
            self.point_one_update(context, event, with_confirm=False)
        elif self.points_edit_index == 1:
            self.point_two_update(context, event, with_confirm=False)
        elif self.points_edit_index == 2:
            self.equalize = False
            self.point_three_update(context, event, with_confirm=False)

    # Popup menu
    def adjust_dims(self, context, event):

        if self.popup_menu.update(context, event, self) == False:
            self.dims_edit_locked = False

    # State = SCALE
    def adjust_scale(self, context, event):

        # Clear state
        if self.mouse_dragging == False:
            self.scale_index = None
            self.scaling_point = False

        # Assign state
        if event.type == 'LEFTMOUSE' and event.value == 'PRESS' and self.scaling_point == False:

            scale_points = []

            # All points
            if self.keep_at_center == False:
                scale_points = self.bounds.get_corner_points()
                scale_points.append(self.bounds.get_center_point())
                scale_points.extend(self.bounds.get_center_face_points())
            
            # Only show center dot
            else:
                self.scale_index = 8
                self.scaling_point = True

            points = []
            for point in scale_points:
                points.append(get_2d_point_from_3d_point(context, point))

            mouse_pos = Vector((event.mouse_region_x, event.mouse_region_y))

            index = None
            compare = None
            for i, point in enumerate(points):
                mag = (mouse_pos - point).magnitude
                if compare == None:
                    compare = mag
                    index = i                    
                elif mag < compare:
                    compare = mag
                    index = i

            # Assign states
            if index != None:
                self.scale_index = index
                self.scaling_point = True

        # Scale is active
        if self.scaling_point == True:

            scale = self.base_controls.mouse * 2

            x = abs(self.point_1[0] - self.point_2[0]) * scale
            y = abs(self.point_1[1] - self.point_2[1]) * scale
            z = abs(self.point_3[2] - self.point_1[2]) * scale

            if self.scale_index == 0:
                self.point_2[0] -= x
                self.point_2[1] -= y
                self.point_3[2] -= z

            elif self.scale_index == 1:
                self.point_1[0] += x
                self.point_2[1] -= y
                self.point_3[2] -= z

            elif self.scale_index == 2:
                self.point_1[1] += y
                self.point_2[0] -= x
                self.point_3[2] -= z

            elif self.scale_index == 3:
                self.point_1[0] += x
                self.point_1[1] += y
                self.point_3[2] -= z
            
            elif self.scale_index == 4:
                self.point_1[2] += z
                self.point_2[0] -= x
                self.point_2[1] -= y
                self.point_2[2] += z

            elif self.scale_index == 5:
                self.point_1[0] += x
                self.point_1[2] += z
                self.point_2[1] -= y
                self.point_2[2] += z

            elif self.scale_index == 6:
                self.point_1[1] += y
                self.point_1[2] += z
                self.point_2[0] -= x
                self.point_2[2] += z

            elif self.scale_index == 7:
                self.point_1[0] += x
                self.point_1[1] += y
                self.point_1[2] += z
                self.point_2[2] -= z

            elif self.scale_index == 8:
                self.point_1[0] += x
                self.point_1[1] += y
                self.point_1[2] += z
                self.point_2[0] -= x
                self.point_2[1] -= y
                self.point_2[2] += z
                self.point_3[2] -= z

            # Face center top
            elif self.scale_index == 9:
                self.point_1[0] += x * .5
                self.point_1[1] += y * .5
                self.point_1[2] += z
                self.point_2[0] -= x * .5
                self.point_2[1] -= y * .5
                self.point_2[2] += z

            # Face center bot
            elif self.scale_index == 10:
                self.point_1[0] += x * .5
                self.point_1[1] += y * .5
                self.point_2[0] -= x * .5
                self.point_2[1] -= y * .5
                self.point_3[2] -= z

            # Face center left
            elif self.scale_index == 11:
                self.point_1[1] += y * .5
                self.point_1[2] += z * .5
                self.point_2[0] -= x
                self.point_2[1] -= y * .5
                self.point_2[2] += z * .5
                self.point_3[2] -= z * .5

            # Face center right
            elif self.scale_index == 12:
                self.point_1[0] += x
                self.point_1[1] += y * .5
                self.point_1[2] += z * .5
                self.point_2[1] -= y * .5
                self.point_2[2] += z * .5
                self.point_3[2] -= z * .5

            # Face center front
            elif self.scale_index == 13:
                self.point_1[0] += x * .5
                self.point_1[2] += z * .5
                self.point_2[0] -= x * .5
                self.point_2[1] -= y
                self.point_2[2] += z * .5
                self.point_3[2] -= z * .5

            # Face center back
            elif self.scale_index == 14:
                self.point_1[0] += x * .5
                self.point_1[1] += y
                self.point_1[2] += z * .5
                self.point_2[0] -= x * .5
                self.point_2[2] += z * .5
                self.point_3[2] -= z * .5

    # Setter func
    def equalize_dims(self, val=0):
        if abs(val) == 0:
            return

        x = abs(self.point_1[0] - self.point_2[0]) * val
        y = abs(self.point_1[1] - self.point_2[1]) * val
        z = abs(self.point_3[2] - self.point_1[2]) * val

        self.point_2[0] += x
        self.point_2[1] += y
        self.point_3[2] += z

    # State = FACE
    def adjust_face(self, context, event):
        self.face_controller.update(context, event, self)


    def set_unit_scale(self, context):
        '''Set the scale value for unit, set inside of static menu update.'''

        global ACTIVE_LENGTH, UNIT_SCALE_FACTOR
        
        # Convert 1 meter to active length
        if ACTIVE_LENGTH == 'Kilometers':
            UNIT_SCALE_FACTOR = 0.001
        elif ACTIVE_LENGTH == 'Meters':
            UNIT_SCALE_FACTOR = 1
        elif ACTIVE_LENGTH == 'Centimeters':
            UNIT_SCALE_FACTOR = 100
        elif ACTIVE_LENGTH == 'Millimeters':
            UNIT_SCALE_FACTOR = 1000
        elif ACTIVE_LENGTH == 'Micrometers':
            UNIT_SCALE_FACTOR = 1000000
        elif ACTIVE_LENGTH == 'Miles':
            UNIT_SCALE_FACTOR = 0.000621371
        elif ACTIVE_LENGTH == 'Feet':
            UNIT_SCALE_FACTOR = 3.28084
        elif ACTIVE_LENGTH == 'Inches':
            UNIT_SCALE_FACTOR = 39.37008
        elif ACTIVE_LENGTH == 'Thousandth':
            UNIT_SCALE_FACTOR = 39370.1


    def bounds_update(self):

        # Bottom square
        if self.point_1 and self.point_2:

            # Fix any broken dims
            self.point_2[2] = self.point_1[2]

            self.bounds.bot_front_left  = self.point_1.copy()
            self.bounds.bot_front_right = Vector(( self.point_2[0], self.point_1[1], self.point_1[2] ))
            self.bounds.bot_back_left   = Vector(( self.point_1[0], self.point_2[1], self.point_1[2] ))
            self.bounds.bot_back_right  = self.point_2.copy()

            # Top square
            if self.point_3:

                # Fix any broken dims
                center = (self.point_1 + self.point_2) * .5
                self.point_3 = Vector((center[0], center[1], self.point_3[2]))

                self.bounds.top_front_left  = Vector(( self.point_1[0], self.point_1[1], self.point_3[2] ))
                self.bounds.top_front_right = Vector(( self.point_2[0], self.point_1[1], self.point_3[2] ))
                self.bounds.top_back_left   = Vector(( self.point_1[0], self.point_2[1], self.point_3[2] ))
                self.bounds.top_back_right  = Vector(( self.point_2[0], self.point_2[1], self.point_3[2] ))

    ####################################################
    #   UTILS
    ####################################################

    def cast_to_verts(self, context, event):
        '''Raycast into scene and get closest vert to point casted.'''

        hit, location, normal, index, obj, matrix = scene_ray_cast(context, event)
        if hit:
            depsgraph = context.evaluated_depsgraph_get()
            object_eval = obj.evaluated_get(depsgraph)
            mesh_eval = object_eval.data

            if len(mesh_eval.polygons) - 1 < index:
                return None

            polygon = mesh_eval.polygons[index]

            compare = None
            point = None
            for vert_index in polygon.vertices:

                if len(mesh_eval.vertices) - 1 < vert_index:
                    return None

                vert = mesh_eval.vertices[vert_index]
                vert_co = obj.matrix_world @ vert.co

                if compare == None:
                    compare = (location - vert_co).magnitude
                    point = vert_co
                    continue

                mag = (location - vert_co).magnitude
                if mag < compare:
                    compare = mag
                    point = vert_co

            if point != None:
                return point

        return None


    def cast_to_surface(self, context, event):
        hit, location, normal, index, object, matrix = scene_ray_cast(context, event)
        return location, hit


    def cast_to_plane(self, context, event, loc, normal):
        mouse_pos = (event.mouse_region_x, event.mouse_region_y)
        point = get_3D_point_from_mouse(mouse_pos, context, loc, normal)
        return point


    def set_initial_points(self, context, event):

        # Capture from edit mode
        if context.mode == 'EDIT_MESH':
            objs = [obj for obj in context.selected_objects if obj.type == 'MESH' and obj.mode == 'EDIT']
            coords = []

            # Get all selected verts
            for obj in objs:
                obj.update_from_editmode()
                bm = bmesh.from_edit_mesh(obj.data)
                selected = [v for v in bm.verts if v.select == True]
                for vert in selected:
                    coords.append(obj.matrix_world @ vert.co)

            if len(coords) > 3:
                bounds = hops_math.coords_to_bounds(coords)
                self.initial_center_point = hops_math.coords_to_center(bounds)
                self.initial_extents = hops_math.dimensions(bounds)
                self.point_1 = bounds[0]
                self.point_2 = bounds[7]
                self.point_3 = bounds[6]
                self.state = State.ADJUST
                self.use_edit_mode = True
                return

        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        objs = [ob for ob in context.selected_objects if ob.type in {'MESH', 'CURVE', 'FONT', 'SURFACE'}]
        if event.shift:
            if context.active_object in objs:
                objs = [context.active_object]
            else:
                bpy.ops.hops.display_notification(info="Active object was not a valid type.")

        coords = []

        depsgraph = context.evaluated_depsgraph_get()

        for obj in objs:
            obj_eval = obj.evaluated_get(depsgraph)
            data_eval = obj_eval.to_mesh()
            coords.extend([obj.matrix_world @ v.co for v in data_eval.vertices])
            obj_eval.to_mesh_clear()

        if len(coords) < 3:
            return

        bounds = hops_math.coords_to_bounds(coords)

        self.initial_center_point = hops_math.coords_to_center(bounds)
        self.initial_extents = hops_math.dimensions(bounds)
        self.point_1 = bounds[0]
        self.point_2 = bounds[7]
        self.point_3 = bounds[6]
        self.state = State.ADJUST

    # Auto Center
    def recenter_points(self):

        points = [self.point_1, self.point_2, self.point_3]
        bounds = hops_math.coords_to_bounds(points)
        cur_center = hops_math.coords_to_center(bounds)

        trans = self.initial_center_point - cur_center
        mat = Matrix.Translation(trans)

        self.point_1 = mat @ self.point_1
        self.point_2 = mat @ self.point_2
        self.point_3 = mat @ self.point_3


    def set_length_equalized(self, val):

        ratio = 1 - abs(val / self.length) if self.length > 0 else 1
        # self.point_2[0] = self.point_1[0] + val
        # self.point_2[1] -= self.width * ratio
        # self.point_3[2] -= self.height * ratio

        p2_x = self.point_1[0] + val
        p2_y = self.width * ratio
        p3_z = self.height * ratio

        self.point_2[0] = p2_x
        self.point_2[1] -= p2_y
        self.point_3[2] -= p3_z


    def set_width_equalized(self, val):

        ratio = 1 - abs(val / self.width) if self.width > 0 else 1
        # self.point_2[0] -= self.length * ratio
        # self.point_2[1] = self.point_1[1] + val
        # self.point_3[2] -= self.height * ratio

        p2_x = self.length * ratio
        p2_y = self.point_1[1] + val
        p3_z = self.height * ratio

        self.point_2[0] -= p2_x
        self.point_2[1] = p2_y
        self.point_3[2] -= p3_z


    def set_height_equalized(self, val):

        ratio = 1 - abs(val / self.height) if self.height > 0 else 1
        # self.point_2[0] -= self.length * ratio
        # self.point_2[1] -= self.width * ratio
        # self.point_3[2] = self.point_1[2] + val

        p2_x = self.length * ratio
        p2_y = self.width * ratio
        p3_z = self.point_1[2] + val

        self.point_2[0] -= p2_x
        self.point_2[1] -= p2_y
        self.point_3[2] = p3_z

    # Face Ctrl Click
    def set_back_loc_to_anchor(self):
        
        if self.keep_at_center == True: return
        if self.anchor == "DEFAULT": return

        self.bounds_update()
        self.face_controller.build_quads(self)

        new_loc = self.get_anchor_center_loc()

        diff = new_loc - self.anchor_loc
        self.point_1 -= diff
        self.point_2 -= diff
        self.point_3 -= diff


    def get_anchor_center_loc(self):

        new_loc = Vector((0,0,0))

        if self.anchor == "TOP":
            new_loc = hops_math.coords_to_center(self.face_controller.top.quad)
        elif self.anchor == "BOTTOM":
            new_loc = hops_math.coords_to_center(self.face_controller.bot.quad)
        elif self.anchor == "LEFT":
            new_loc = hops_math.coords_to_center(self.face_controller.left.quad)
        elif self.anchor == "RIGHT":
            new_loc = hops_math.coords_to_center(self.face_controller.right.quad)
        elif self.anchor == "FRONT":
            new_loc = hops_math.coords_to_center(self.face_controller.front.quad)
        elif self.anchor == "BACK":
            new_loc = hops_math.coords_to_center(self.face_controller.back.quad)

        return new_loc

    ####################################################
    #   EXIT
    ####################################################

    def confirmed_exit(self, context):

        if self.use_edit_mode:
            self.add_lattice_cube(context)
            return

        if self.add_cube:
            self.add_cube_to_bounds(context)
        else:
            if self.exit_with_empty:
                self.use_empty_to_scale(context)
            else:
                self.add_lattice_cube(context)


    def add_cube_to_bounds(self, context):
        
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        bm = bmesh.new()
        bmesh.ops.create_cube(bm)
        coords = [
            self.bounds.bot_front_left,
            self.bounds.bot_front_right,
            self.bounds.bot_back_left,
            self.bounds.bot_back_right,
            self.bounds.top_front_left,
            self.bounds.top_front_right,
            self.bounds.top_back_left,
            self.bounds.top_back_right]

        bounds = hops_math.coords_to_bounds(coords)
        center = hops_math.coords_to_center(bounds)
        extents = hops_math.dimensions(bounds)

        scale_mat = hops_math.get_sca_matrix(extents)
        bmesh.ops.transform(bm, matrix=scale_mat, verts=bm.verts)

        # Finish up, write the bmesh into a new mesh
        me = bpy.data.meshes.new("Mesh")
        bm.to_mesh(me)
        bm.free()

        # Add the mesh to the scene
        obj = bpy.data.objects.new("Object", me)
        context.collection.objects.link(obj)
        obj.location = center

        # Select and make active
        context.view_layer.objects.active = obj
        obj.select_set(True)


    def add_lattice_cube(self, context):

        mod_name = "Accu_Lattice"

        def get_lattice():
            lattice_data = bpy.data.lattices.new('lattice')
            lattice_data.interpolation_type_u = 'KEY_LINEAR'
            lattice_data.interpolation_type_v = 'KEY_LINEAR'
            lattice_data.interpolation_type_w = 'KEY_LINEAR'
            lattice = bpy.data.objects.new('lattice', lattice_data)
            context.collection.objects.link(lattice)
            context.view_layer.objects.active = lattice
            lattice.select_set(True)
            return lattice


        def remove_old_mods(objs):
            for obj in objs:
                for mod in obj.modifiers:
                    if mod.type == 'LATTICE':
                        if mod.name[:12] == mod_name:
                            if mod.object == None:
                                obj.modifiers.remove(mod)


        def add_lattice_mods(objs, with_vg=False):
            for obj in objs:
                mod = obj.modifiers.new(name=mod_name, type="LATTICE")
                mod.object = lattice
                if with_vg:
                    mod.vertex_group = obj.vertex_groups.active.name


        def apply_matrix_lattice(lattice):
            # Add shape key base
            lattice.shape_key_add(name="AccuShapeBase", from_mix=False)

            # Get coords list for accu box
            coords = self.bounds.get_corner_points()

            # Accu box data
            bounds = hops_math.coords_to_bounds(coords)
            center = hops_math.coords_to_center(bounds)
            extents = hops_math.dimensions(bounds)

            # Accubox matrix
            accubox_matrix = Matrix.Translation(center) @ hops_math.get_sca_matrix(extents)

            try:
                # lattice.data.transform(lattice.matrix_world.inverted() @ accubox_matrix)
                # Add deform shape key
                shape_key = lattice.shape_key_add(name="AccuShapeDeform", from_mix=False)
                for val in shape_key.data.values():
                    val.co = lattice.matrix_world.inverted() @ accubox_matrix @ val.co
                shape_key.value = 1

            except:
                bpy.ops.hops.display_notification(info="Nice try bud.")

        # --- Edit Mode ---#
        if self.use_edit_mode:
            objs = [obj for obj in context.selected_objects if obj.type == 'MESH' and obj.mode == 'EDIT']

            # Get vert dims
            coords = []
            for obj in objs:
                obj.update_from_editmode()
                bm = bmesh.from_edit_mesh(obj.data)
                selected = [v for v in bm.verts if v.select == True]
                for vert in selected:
                    coords.append(obj.matrix_world @ vert.co)

            bounds = hops_math.coords_to_bounds(coords)
            center = hops_math.coords_to_center(bounds)
            extents = hops_math.dimensions(bounds)    


            if context.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')

            # Get all selected verts
            good_objs = []
            for obj in objs:
                indexes = [v.index for v in obj.data.vertices if v.select]
                if len(indexes) < 1:
                    continue
                v_group = obj.vertex_groups.new(name='Accu_Lattice')
                v_group.add(index=indexes, weight=1, type='ADD')
                obj.vertex_groups.active_index = v_group.index
                good_objs.append(obj)
            objs = good_objs

            lattice = get_lattice()

            # Locate and scale the lattice to fit the object
            for i in range(3):
                if not extents[i]:
                    extents[i] = 1
            scale_mat = hops_math.get_sca_matrix(extents)
            lattice.matrix_world = scale_mat # write fit transformation in lattice matrix so it's up to date
            lattice.matrix_world.translation = center

            remove_old_mods(objs)
            add_lattice_mods(objs, with_vg=True)

            # Add shape key base
            lattice.shape_key_add(name="AccuShapeBase", from_mix=False)

            # Matrix
            apply_matrix_lattice(lattice)

        # --- Object Mode ---#
        else:
            if context.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')

            objs = [ob for ob in context.selected_objects if ob.type in {'MESH', 'CURVE', 'FONT', 'SURFACE'}]
            bpy.ops.object.select_all(action='DESELECT')

            lattice = get_lattice()
            remove_old_mods(objs)
                
            # Object bounds for the lattice
            coords = []
            for obj in objs:
                coords.extend([obj.matrix_world @ Vector(coord) for coord in obj.bound_box])

            bounds = hops_math.coords_to_bounds(coords)
            center = hops_math.coords_to_center(bounds)
            extents = hops_math.dimensions(bounds)

            # Locate and scale the lattice to fit the object
            for i in range(3):
                if not extents[i]:
                    extents[i] = 1
            scale_mat = hops_math.get_sca_matrix(extents)
            lattice.matrix_world = scale_mat # write fit transformation in lattice matrix so it's up to date
            lattice.matrix_world.translation = center
            
            # Add mods
            add_lattice_mods(objs)

            # Matrix
            apply_matrix_lattice(lattice)


    def use_empty_to_scale(self, context):

        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        selected = [ob for ob in context.selected_objects if ob.type in {'MESH', 'CURVE', 'FONT', 'SURFACE'}]
        bpy.ops.object.select_all(action='DESELECT')

        # Empty
        empty = bpy.data.objects.new("AccuEmpty", None )
        context.collection.objects.link(empty)
        empty.empty_display_type = 'SPHERE'

        # Get coords list for accu box
        coords = self.bounds.get_corner_points()

        # Accu box data
        bounds = hops_math.coords_to_bounds(coords)
        center = hops_math.coords_to_center(bounds)
        extents = hops_math.dimensions(bounds)

        size = max(extents[0], extents[1], extents[2])
        empty.empty_display_size = size * .5

        empty.location = center

        # Parent
        for obj in selected:
            offset = obj.matrix_world.translation - self.initial_center_point
            obj.parent = empty
            obj.location = offset

        # Scale X
        if self.initial_extents[0] != 0:
            sca = extents[0] / self.initial_extents[0]
            empty.scale[0] = sca
            
        # Scale Y
        if self.initial_extents[1] != 0:
            sca = extents[1] / self.initial_extents[1]
            empty.scale[1] = sca

        # Scale Z
        if self.initial_extents[2] != 0:
            sca = extents[2] / self.initial_extents[2]
            empty.scale[2] = sca


    ####################################################
    #   SHADERS
    ####################################################

    def remove_shaders(self):
        '''Remove shader handle.'''

        if self.draw_handle_2D:
            self.draw_handle_2D = bpy.types.SpaceView3D.draw_handler_remove(self.draw_handle_2D, "WINDOW")

        if self.draw_handle_3D:
            self.draw_handle_3D = bpy.types.SpaceView3D.draw_handler_remove(self.draw_handle_3D, "WINDOW")

    # 2D SHADER
    def safe_draw_2D(self, context):
        method_handler(self.draw_shader_2D,
            arguments = (context,),
            identifier = 'Modal Shader 2D',
            exit_method = self.remove_shaders)


    def draw_shader_2D(self, context):
        '''Draw shader handle.'''

        if self.state == State.ADJUST:
            self.static_menu.draw_2d()

            point_1 = get_2d_point_from_3d_point(context, self.point_1)
            point_2 = get_2d_point_from_3d_point(context, self.point_2)
            point_3 = get_2d_point_from_3d_point(context, self.point_3)
            points = [ point_1, point_2, point_3 ]

            if self.ctrl_adjusting_circles:
                self.draw_point_circles(points=[point_1])
                return

            self.draw_point_circles(points)
            self.draw_dims(points)
            self.draw_LWH(context)

            # Draw pop up menu
            if self.dims_edit_locked:
                self.popup_menu.draw_2d()

        elif self.state == State.SCALE:
            if self.scaling_point:
                draw_modal_frame(context)
                self.draw_LWH(context)
            return

        elif self.state == State.FACE:
            self.static_menu.draw_2d()
            self.face_controller.draw_2d(context)
            return

        self.draw_anchor(context)


    def draw_dims(self, points):
        if self.dims_change_circle_color == False:
            return
        
        if self.dims_edit_locked == True:
            return
        
        font_size = 16
        y_height = get_blf_text_dims("Qjq`", font_size)[1]

        for index, point in enumerate(points):
            if point == None:
                continue
            
            if index == 0:
                text = "X : {:.3f}".format(self.point_1[0])
                y_offset = self.radius * 2
                render_text(text, position=(point[0] - self.radius, point[1] - y_offset), size=font_size, color=(0,1,0,1))

                text = "Y : {:.3f}".format(self.point_1[1])
                y_offset = self.radius * 2 + y_height * 1.5
                render_text(text, position=(point[0] - self.radius, point[1] - y_offset), size=font_size, color=(0,1,0,1))

                text = "Z : {:.3f} ".format(self.point_1[2])
                y_offset = self.radius * 2 + y_height * 3
                render_text(text, position=(point[0] - self.radius, point[1] - y_offset), size=font_size, color=(0,1,0,1))

            elif index == 1:
                text = "X : {:.3f}".format(self.point_2[0])
                y_offset = self.radius * 2
                render_text(text, position=(point[0] - self.radius, point[1] - y_offset), size=font_size, color=(0,1,0,1))

                text = "Y : {:.3f}".format(self.point_2[1])
                y_offset = self.radius * 2 + y_height * 1.5
                render_text(text, position=(point[0] - self.radius, point[1] - y_offset), size=font_size, color=(0,1,0,1))

            elif index == 2:
                text = "Z : {:.3f}".format(self.point_3[2])
                y_offset = self.radius * 2
                render_text(text, position=(point[0] - self.radius, point[1] - y_offset), size=font_size, color=(0,1,0,1))


    def draw_point_circles(self, points):

        color = (1,1,0,1)
        if self.dims_change_circle_color:
            color = (0,1,1,1)
        elif self.ctrl_adjusting_circles:
            color = (1,0,1,1)

        for point in points:
            if point == None:
                continue
            verts = []
            segments = 32
            for i in range(segments):
                index = i + 1
                angle = i * 3.14159 * 2 / segments
                x = (math.cos(angle) * self.radius) + point[0]
                y = (math.sin(angle) * self.radius) + point[1]
                verts.append((x, y))
            verts.append(verts[0])
            #Enable(GL_LINE_SMOOTH)
            gpu.state.blend_set('ALPHA')
            gpu.state.line_width_set(1)
            built_in_shader = 'UNIFORM_COLOR' if bpy.app.version[0] >=4 else '2D_UNIFORM_COLOR'
            shader = gpu.shader.from_builtin(built_in_shader)
            batch = batch_for_shader(shader, 'LINE_STRIP', {"pos": verts})
            shader.bind()
            shader.uniform_float("color", color)
            batch.draw(shader)
            gpu.state.blend_set('NONE')
            del shader
            del batch


    def draw_LWH(self, context):
        if self.dims_change_circle_color == True:
            return

        font_size = 14
        color = (1,1,1,1)

        # Length
        pos = get_2d_point_from_3d_point(context, (self.bounds.bot_front_left + self.bounds.bot_front_right) * .5)
        if pos != None:
            text = "L : {:.4f}".format(self.length * UNIT_SCALE_FACTOR)
            render_text(text, position=pos, size=font_size, color=color)

        # Width
        pos = get_2d_point_from_3d_point(context, (self.bounds.bot_front_left + self.bounds.bot_back_left) * .5)
        if pos != None:
            text = "W : {:.4f}".format(self.width * UNIT_SCALE_FACTOR)
            render_text(text, position=pos, size=font_size, color=color)

        # Height
        pos = get_2d_point_from_3d_point(context, (self.bounds.bot_front_left + self.bounds.top_front_left) * .5)
        if pos != None:
            text = "H : {:.4f}".format(self.height * UNIT_SCALE_FACTOR)
            render_text(text, position=pos, size=font_size, color=color)


    def draw_anchor(self, context):
        if self.keep_at_center == True: return
        if self.anchor == "DEFAULT": return

        self.bounds_update()
        self.face_controller.build_quads(self)

        new_loc = self.get_anchor_center_loc()

        pos = get_2d_point_from_3d_point(context, (new_loc))

        if pos != None:
            text = f'Anchor Point : {self.anchor}'
            render_text(text, position=pos, size=16, color=(0,1,0,1))

    # 3D SHADER
    def safe_draw_3D(self, context):
        method_handler(self.draw_shader_3D,
            arguments = (context,),
            identifier = 'Modal Shader 3D',
            exit_method = self.remove_shaders)


    def draw_shader_3D(self, context):
        '''Draw shader handle.'''

        if self.show_solid_view:
            self.draw_shaded()

        points = []
        if self.point_1 != None:
            points.append(self.point_1)
        if self.point_2 != None:
            points.append(self.point_2)
        if self.point_3 != None:
            points.append(self.point_3)

        if len(points) == 2:
            self.draw_bottom_square()
        elif len(points) == 3:
            self.draw_bottom_square()
            self.draw_top_square()
            self.draw_sides()

        if self.state == State.FACE:
            self.face_controller.draw_3d()
            return

        if self.state == State.SCALE:
            if len(points) != 3:
                return
            
            self.draw_scale_points()
            return

        if points:
            built_in_shader = 'UNIFORM_COLOR' if bpy.app.version[0] >=4 else '3D_UNIFORM_COLOR'
            shader = gpu.shader.from_builtin(built_in_shader)
            batch = batch_for_shader(shader, 'POINTS', {'pos': points})
            shader.bind()
            shader.uniform_float('color', (1,0,0,1))
            gpu.state.blend_set('ALPHA')
            gpu.state.point_size_set(8)
            batch.draw(shader)
            del shader
            del batch


    def draw_scale_points(self):

        # Corners and center
        points = []
        if self.keep_at_center == False:
            points = self.bounds.get_corner_points()
            points.append(self.bounds.get_center_point())
        else:
            points = [self.bounds.get_center_point()]

        built_in_shader = 'UNIFORM_COLOR' if bpy.app.version[0] >=4 else '3D_UNIFORM_COLOR'
        shader = gpu.shader.from_builtin(built_in_shader)
        batch = batch_for_shader(shader, 'POINTS', {'pos': points})
        shader.bind()
        shader.uniform_float('color', (1,0,0,1))
        gpu.state.blend_set('ALPHA')
        gpu.state.point_size_set(8)
        batch.draw(shader)
        del shader
        del batch

        # Face centers
        if self.keep_at_center == False:
            built_in_shader = 'UNIFORM_COLOR' if bpy.app.version[0] >=4 else '3D_UNIFORM_COLOR'
            shader = gpu.shader.from_builtin(built_in_shader)
            batch = batch_for_shader(shader, 'POINTS', {'pos': self.bounds.get_center_face_points()})
            shader.bind()
            shader.uniform_float('color', (0,0,1,1))
            gpu.state.blend_set('ALPHA')
            gpu.state.point_size_set(8)
            batch.draw(shader)
            del shader
            del batch


    def draw_bottom_square(self):
        verts = [
            self.bounds.bot_front_left , self.bounds.bot_front_right,
            self.bounds.bot_front_right, self.bounds.bot_back_right,
            self.bounds.bot_back_right,  self.bounds.bot_back_left,
            self.bounds.bot_back_left,   self.bounds.bot_front_left]

        built_in_shader = 'UNIFORM_COLOR' if bpy.app.version[0] >=4 else '3D_UNIFORM_COLOR'
        shader = gpu.shader.from_builtin(built_in_shader)
        batch = batch_for_shader(shader, 'LINES', {'pos': verts})
        shader.bind()
        shader.uniform_float('color', (0,0,0,1))
        #Enable(GL_LINE_SMOOTH)
        gpu.state.blend_set('ALPHA')
        gpu.state.line_width_set(3)
        batch.draw(shader)
        del shader
        del batch


    def draw_top_square(self):
        verts = [
            self.bounds.top_front_left , self.bounds.top_front_right,
            self.bounds.top_front_right, self.bounds.top_back_right,
            self.bounds.top_back_right,  self.bounds.top_back_left,
            self.bounds.top_back_left,   self.bounds.top_front_left]

        built_in_shader = 'UNIFORM_COLOR' if bpy.app.version[0] >=4 else '3D_UNIFORM_COLOR'
        shader = gpu.shader.from_builtin(built_in_shader)
        batch = batch_for_shader(shader, 'LINES', {'pos': verts})
        shader.bind()
        shader.uniform_float('color', (0,0,0,1))
        #Enable(GL_LINE_SMOOTH)
        gpu.state.blend_set('ALPHA')
        gpu.state.line_width_set(3)
        batch.draw(shader)
        del shader
        del batch

    
    def draw_sides(self):
        verts = [
            self.bounds.bot_front_left , self.bounds.top_front_left,
            self.bounds.bot_front_right, self.bounds.top_front_right,
            self.bounds.bot_back_right,  self.bounds.top_back_right,
            self.bounds.bot_back_left,   self.bounds.top_back_left]

        built_in_shader = 'UNIFORM_COLOR' if bpy.app.version[0] >=4 else '3D_UNIFORM_COLOR'
        shader = gpu.shader.from_builtin(built_in_shader)
        batch = batch_for_shader(shader, 'LINES', {'pos': verts})
        shader.bind()
        shader.uniform_float('color', (0,0,0,1))
        #Enable(GL_LINE_SMOOTH)
        gpu.state.blend_set('ALPHA')
        gpu.state.line_width_set(3)
        batch.draw(shader)
        del shader
        del batch


    def draw_shaded(self):
        
        verts, indices = self.face_controller.get_all_verts_indices()
        built_in_shader = 'UNIFORM_COLOR' if bpy.app.version[0] >=4 else '3D_UNIFORM_COLOR'
        shader = gpu.shader.from_builtin(built_in_shader)
        batch = batch_for_shader(shader, 'TRIS', {'pos': verts}, indices=indices)
        shader.bind()
        shader.uniform_float('color', (0,1,0,.0125))
        #Enable(GL_LINE_SMOOTH)
        gpu.state.blend_set('ALPHA')
        batch.draw(shader)
        del shader
        del batch

