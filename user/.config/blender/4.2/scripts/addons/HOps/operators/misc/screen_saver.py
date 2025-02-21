import bpy, bmesh, mathutils, math, time, random
from gpu_extras.batch import batch_for_shader
from mathutils import Vector
from .screen_saver_tips import tips
from ... utility import method_handler
from ... utility import addon
from ... utility.base_modal_controls import Base_Modal_Controls
from ... ui_framework.master import Master
from ... ui_framework.graphics.draw import render_text, render_quad, draw_2D_lines
from ... ui_framework.utils.geo import get_blf_text_dims
from ... utils.blender_ui import get_dpi_factor

##############################################################################
# Draw Data
##############################################################################

HANDLE_2D = None

class Data:
    # States
    screen_saver_running = False
    restart_screen_saver = False

    @staticmethod
    def reset_states():
        Data.screen_saver_running = False
        Data.restart_screen_saver = False


##############################################################################
# Launch Operator
##############################################################################

class HOPS_OT_Draw_Screen_Saver_Launcher(bpy.types.Operator):
    bl_idname = "hops.draw_screen_saver_launcher"
    bl_label = "Screen Saver Draw Launcher"
    bl_options = {"INTERNAL"}

    def execute(self, context):

        # Trigger modal to reset its timers and start over again
        if Data.screen_saver_running == True:
            Data.restart_screen_saver = True
        # Call a fresh operator if none is currently running
        else:
            bpy.ops.hops.draw_screen_saver('INVOKE_DEFAULT')

        return {'FINISHED'}


##############################################################################
# Drawing Modal
##############################################################################

class HOPS_OT_Draw_Screen_Saver(bpy.types.Operator):
    bl_idname = "hops.draw_screen_saver"
    bl_label = "Drawing for screen saver"
    bl_options = {"INTERNAL"}

    def invoke(self, context, event):

        self.master = Master(context=context)
        self.master.only_use_fast_ui = True
        self.base_controls = Base_Modal_Controls(context, event)

        # Registers
        self.shader = Shader(context)
        self.timer = context.window_manager.event_timer_add(0.075, window=context.window)
        context.window_manager.modal_handler_add(self)

        return {'RUNNING_MODAL'}


    def modal(self, context, event):

        # Base Systems
        self.master.receive_event(event=event)
        self.base_controls.update(context, event)

        Data.screen_saver_running = True

        # Resest every thing if new drawing is initialized
        if Data.restart_screen_saver == True:
            Data.restart_screen_saver = False
            self.shader.reset()

        # Reset everything
        if self.shader.fade_complete:
            self.shader.reset()

        # Exit and Reset
        if event.type in {'SPACE', 'LEFTMOUSE', 'ESC', 'RIGHTMOUSE'}:
            self.__finished(context)
            self.master.run_fade()
            return {'FINISHED'}

        # Redraw the viewport
        if context.area != None:
            context.area.tag_redraw()

        # Toggle the viewport animation
        if event.type == "A" and event.value == "PRESS":
            bpy.ops.screen.animation_play('INVOKE_DEFAULT')

        self.draw_master(context)

        if self.base_controls.pass_through:
            return {'PASS_THROUGH'}

        return {'PASS_THROUGH'}


    def __finished(self, context):
        '''Remove the timer, shader, and reset Data'''

        # Global
        Data.reset_states()

        # Unregister
        if self.timer != None:
            context.window_manager.event_timer_remove(self.timer)
        if self.shader != None:
            self.shader.destroy()
        if context.area != None:
            context.area.tag_redraw()


    def draw_master(self, context):

        self.master.setup()
        if self.master.should_build_fast_ui():

            # Help
            help_items = {"GLOBAL" : [], "STANDARD" : []}
            help_items["STANDARD"] = [
                ("A", "Toggle play animation")]

            self.master.receive_fast_ui(help_list=help_items)
        self.master.finished()


class Shader():

    def __init__(self, context):

        self.hold_duration = addon.preference().ui.Hops_screen_saver_fade
        self.fade_duration = 2

        self.screen_width = context.area.width
        self.screen_height = context.area.height
        self.scale = get_dpi_factor()

        self.header_size = 26     # Header font size
        self.header_dims = (0,0)  # Header font size X / Y
        self.body_size = 16       # Body font size
        self.body_line_height = 0 # Tallest line height from body
        self.body_dims = (0,0)    # Bounding box for body

        self.tip_index = 0      # Tips index chosen random

        self.text_area_dims = (0,0)    # Full text dims
        self.padding = 16 * self.scale # Font padding

        self.reset()
        self.__setup_handle(context)


    def reset(self):
        '''Restart the shader.'''

        # States
        self.fade_complete = False
        self.start_time = time.time()

        # Font color / alpha
        color = addon.preference().color.Hops_UI_text_color
        self.font_alpha = color[3]
        self.og_font_alpha = color[3]
        self.font_color = (color[0], color[1], color[2], self.font_alpha)

        # BG color / alpha
        color = addon.preference().color.Hops_border_color
        self.bg_alpha = color[3]
        self.og_bg_alpha = color[3]
        self.bg_color = (color[0], color[1], color[2], self.bg_alpha)

        # Trim color
        color = addon.preference().color.Hops_UI_cell_background_color
        self.trim_color = (color[0], color[1], color[2], self.bg_alpha)

        self.__setup_next_tip()


    def __setup_next_tip(self):
        
        # Get the current tip
        self.tip_index = random.randint(0, len(tips) - 1)
        tip = tips[self.tip_index]

        # Get header dims
        header_text = tip[0]
        self.header_dims = get_blf_text_dims(text=header_text, size=self.header_size)

        # Get body dims
        x, y, tallest_line = 0, 0, 0
        for item in tip[1:]:
            dims = get_blf_text_dims(text=item, size=self.body_size)

            if dims[0] > x:
                x = dims[0]

            if dims[1] > tallest_line:
                tallest_line = dims[1]

            y += dims[1] + self.padding

        self.body_line_height = tallest_line
        self.body_dims = (x, y)

        # Over all
        over_all_x = x if x > self.header_dims[0] else self.header_dims[0] # Widest line
        y += self.header_dims[1] + self.padding
        self.text_area_dims = (over_all_x, y)


    def destroy(self):
        '''Remove the shader.'''

        global HANDLE_2D
        if HANDLE_2D != None:
            bpy.types.SpaceView3D.draw_handler_remove(HANDLE_2D, "WINDOW")
            HANDLE_2D = None
            print("Screen Saver Removed")


    def __setup_handle(self, context):
        '''Setup the draw handle for the UI'''

        global HANDLE_2D
        if HANDLE_2D == None:
            HANDLE_2D = bpy.types.SpaceView3D.draw_handler_add(self.__safe_draw_2d, (context, ), "WINDOW", "POST_PIXEL")


    def __safe_draw_2d(self, context):
        method_handler(self.__draw_2d,
            arguments = (context,),
            identifier = 'Screen Saver 2D Shader',
            exit_method = self.destroy)


    def __draw_2d(self, context):
        '''Draw the UVs.'''

        self.__handle_fade()

        # Trigger exit
        if self.font_alpha <= 0:
            self.fade_complete = True

        # Draw Tips
        self.__draw_tips_box()
        self.__draw_under_line()
        self.__draw_tips()

    
    def __draw_tips_box(self):

        x = self.screen_width
        y = self.screen_height * .75
        o = self.header_dims[1] + self.padding
        h = y - self.text_area_dims[1]

        # Trim
        top_left  = (0, self.padding * .25 + y + o)
        bot_left  = (0, y + o)
        top_right = (x, self.padding * .25 + y + o)
        bot_right = (x, y + o)

        render_quad(
            quad=(top_left, bot_left, top_right, bot_right),
            color=(self.trim_color[0], self.trim_color[1], self.trim_color[2], self.bg_alpha),
            bevel_corners=False)

        # BG
        top_left  = (0, y + o)
        bot_left  = (0, h)
        top_right = (x, y + o)
        bot_right = (x, h)

        render_quad(
            quad=(top_left, bot_left, top_right, bot_right),
            color=(self.bg_color[0], self.bg_color[1], self.bg_color[2], self.bg_alpha),
            bevel_corners=False)

        draw_2D_lines(
            vertices=[top_left, top_right, top_right, bot_right, bot_right, bot_left, bot_left, top_left],
            width=3,
            color=(self.bg_color[0], self.bg_color[1], self.bg_color[2], self.bg_alpha))


    def __draw_under_line(self):

        x = self.screen_width * .25
        y = (self.screen_height * .75) - self.padding * .5
        o = self.header_dims[0] * 1.75
        draw_2D_lines(
            vertices=[(x, y), (x + o, y)],
            width=2,
            color=(self.bg_color[0], self.bg_color[1], self.bg_color[2], self.bg_alpha))


    def __draw_tips(self):

        # Tips
        tip = tips[self.tip_index]

        # Header
        x = self.screen_width * .25
        y = self.screen_height * .75

        render_text(
            text=tip[0],
            position=(x, y),
            size=self.header_size,
            color=(self.font_color[0], self.font_color[1], self.font_color[2], self.font_alpha))

        # Body
        y -= self.header_dims[1] + self.padding
        for item in tip[1:]:
            render_text(
                text=item,
                position=(x, y),
                size=self.body_size,
                color=(self.font_color[0], self.font_color[1], self.font_color[2], self.font_alpha))

            y -= self.body_line_height + self.padding


    def __handle_fade(self):
        '''Fade the alpha based on current time and Global DURATION variable'''

        if time.time() - self.start_time > self.hold_duration:
            diff = time.time() - (self.start_time + self.hold_duration)
            ratio = diff / self.fade_duration

            # Font
            self.font_alpha = self.og_font_alpha - (self.og_font_alpha * ratio)

            # BG
            self.bg_alpha = self.og_bg_alpha - (self.og_bg_alpha * ratio)


##############################################################################
# Remove On App Reload
##############################################################################

from bpy.app.handlers import persistent
@persistent
def remove_screen_saver_shader(dummy):
    global HANDLE_2D
    if HANDLE_2D != None:
        bpy.types.SpaceView3D.draw_handler_remove(HANDLE_2D, "WINDOW")
        HANDLE_2D = None

    Data.reset_states()

