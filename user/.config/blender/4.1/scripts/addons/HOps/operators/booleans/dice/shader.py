import bpy, bmesh, mathutils, math, gpu, time
from gpu_extras.batch import batch_for_shader
from mathutils import Vector, Matrix
from .... utility import addon
from .... utility import method_handler
from . import Mode
from . struct import get_boxelize_ref

HANDLE_3D = None


class SD:
    '''Shader Data'''

    # States
    draw_modal_running = False
    dice_modal_running = False
    reset_modal = False
    exit_with_no_fade = False
    pause_drawing = False

    # Shader
    built_in_shader = 'UNIFORM_COLOR' if bpy.app.version[0] >=4 else '3D_UNIFORM_COLOR'
    shader = gpu.shader.from_builtin(built_in_shader)

    # Draw Data
    draw_x = False
    draw_y = False
    draw_z = False

    xp_tick_batch = None
    xp_edge_batch = None
    xp_point_batch = None

    yp_tick_batch = None
    yp_edge_batch = None
    yp_point_batch = None

    zp_tick_batch = None
    zp_edge_batch = None
    zp_point_batch = None

    # Settings
    see_though = False

    @staticmethod
    def reset_data():
        SD.draw_x = False
        SD.draw_y = False
        SD.draw_z = False
        SD.xp_line_batch = None
        SD.xp_point_batch = None
        SD.xp_tick_batch = None
        SD.yp_line_batch = None
        SD.yp_point_batch = None
        SD.yp_tick_batch = None
        SD.zp_line_batch = None
        SD.zp_point_batch = None
        SD.zp_tick_batch = None

    @staticmethod
    def reset_states():
        SD.draw_modal_running = False
        SD.dice_modal_running = False
        SD.reset_modal = False 
        SD.exit_with_no_fade = False
        SD.pause_drawing = False


class HOPS_OT_Draw_Dice_V2(bpy.types.Operator):
    '''Dice Modal'''

    bl_idname = "hops.draw_dice_v2"
    bl_label = "Drawing for dice"
    bl_options = {"INTERNAL"}

    def invoke(self, context, event):

        # Global
        SD.reset_data()

        # Registers
        self.shader = Shader(context)
        self.timer = context.window_manager.event_timer_add(0.075, window=context.window)

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


    def modal(self, context, event):

        SD.draw_modal_running = True

        # Resest every thing if new drawing is initialized
        if SD.reset_modal:
            SD.reset_modal = False
            SD.reset_data()
            self.shader.reset()

        # Check for exit after fade
        if SD.dice_modal_running == False:

            # Fast exit
            if SD.exit_with_no_fade or SD.pause_drawing:
                self.__finished(context)
                return {'FINISHED'}

            # Fade exit
            self.shader.should_be_fading = True
            if self.shader.fade_complete == True:
                self.__finished(context)
                return {'FINISHED'}

        # Redraw the viewport
        if context.area != None:
            context.area.tag_redraw()

        return {'PASS_THROUGH'}


    def __finished(self, context):
        '''Remove the timer, shader, and reset Data'''

        # Global
        SD.reset_data()
        SD.exit_with_no_fade = False
        SD.draw_modal_running = False

        # Unregister
        if self.timer != None:
            context.window_manager.event_timer_remove(self.timer)
        if self.shader != None:
            self.shader.destroy()
        if context.area != None:
            context.area.tag_redraw()


class Shader():

    def __init__(self, context):

        self.should_be_fading = False
        self.fade_complete = False
        self.alpha_dice = .75
        self.fade_duration = .25 #addon.preference().ui.Hops_extra_draw_time
        self.fade_start_time = 0
        self.fade_start_time_set = False
        self.__setup_handle(context)
        self.prefs = addon.preference().property

 
    def __setup_handle(self, context):
        '''Setup the draw handle for the UI'''

        global HANDLE_3D
        if HANDLE_3D == None:
            HANDLE_3D = bpy.types.SpaceView3D.draw_handler_add(self.safe_draw_3d, (context, ), "WINDOW", "POST_VIEW")


    def reset(self):
        '''Reboot the shader props.'''

        self.should_be_fading = False
        self.fade_complete = False
        self.alpha_dice = .75
        self.fade_start_time = 0
        self.fade_start_time_set = False


    def safe_draw_3d(self, context):
        method_handler(self.__draw_3d,
            arguments = (context,),
            identifier = 'Dice Fade Draw Shader 3D',
            exit_method = self.destroy)


    def __draw_3d(self, context):
        '''Draw the UVs.'''

        if SD.pause_drawing: return

        # Fade started but there was a modal cancel or to twist so bounce out
        if SD.exit_with_no_fade and self.should_be_fading:
            return

        # Lower alpha during fade
        self.__handle_fade()
        
        #Enable(GL_LINE_SMOOTH)
        gpu.state.blend_set('ALPHA')  
        gpu.state.line_width_set(1)
        if SD.see_though == False:
            gpu.state.depth_test_set('LESS')
            #glDepthFunc(GL_LESS)

        if SD.shader: SD.shader.bind()

        # X Axis
        if SD.draw_x:
            SD.shader.uniform_float("color", (1, 0, 0, self.alpha_dice))

            # Angle Ticks
            if self.prefs.dice_wire_type == 'TICKS' and SD.xp_tick_batch:
                gpu.state.line_width_set(3)
                SD.xp_tick_batch.draw(SD.shader)
            # Full edges
            elif self.prefs.dice_wire_type != 'DOTS' and SD.xp_edge_batch:
                SD.xp_edge_batch.draw(SD.shader)
            # Points
            if SD.xp_point_batch:
                SD.xp_point_batch.draw(SD.shader)
        # Y Axis
        if SD.draw_y:
            SD.shader.uniform_float("color", (0, 1, 0, self.alpha_dice))
            
            # Angle Ticks
            if self.prefs.dice_wire_type == 'TICKS' and SD.yp_tick_batch:
                gpu.state.line_width_set(3)
                SD.yp_tick_batch.draw(SD.shader)
            # Full edges
            elif self.prefs.dice_wire_type != 'DOTS' and SD.yp_edge_batch:
                SD.yp_edge_batch.draw(SD.shader)
            # Points
            if SD.yp_point_batch:
                SD.yp_point_batch.draw(SD.shader)
        # Z Axis
        if SD.draw_z:
            SD.shader.uniform_float("color", (0, 0, 1, self.alpha_dice))
            # Angle Ticks
            if self.prefs.dice_wire_type == 'TICKS' and SD.zp_tick_batch:
                gpu.state.line_width_set(3)
                SD.zp_tick_batch.draw(SD.shader)
            # Full edges
            elif self.prefs.dice_wire_type != 'DOTS' and SD.zp_edge_batch:
                SD.zp_edge_batch.draw(SD.shader)
            # Points
            if SD.zp_point_batch:
                SD.zp_point_batch.draw(SD.shader)

        gpu.state.blend_set('NONE')
        gpu.state.depth_test_set('NONE')
        gpu.state.face_culling_set('NONE')
        gpu.state.depth_test_set('NONE')

        if self.alpha_dice <= 0:
            self.fade_complete = True


    def __handle_fade(self):
        '''Fade alpha if fading is active.'''

        if self.should_be_fading == True:
            # Set the initial fade start time
            if self.fade_start_time_set == False:
                self.fade_start_time_set = True
                self.fade_start_time = time.time()

            # Fade alpha
            diff = time.time() - self.fade_start_time
            ratio = diff / self.fade_duration #if not self.prefs.dice_show_mesh_wire else diff / (self.fade_duration * .5)
            self.alpha_dice = .75 - (.75 * ratio)


    def destroy(self):
        '''Remove the shader.'''

        global HANDLE_3D
        if HANDLE_3D != None:
            bpy.types.SpaceView3D.draw_handler_remove(HANDLE_3D, "WINDOW")
            HANDLE_3D = None

        SD.reset_data()


def build_batches(struct):

    dice_points = []
    dice_lines = []
    dice_ticks = []

    for loop in struct.loops():
        points = [p for p in loop]
        dice_points.extend(points)
        dice_lines.extend([points[0], points[1], points[1], points[2], points[2], points[3], points[3], points[0]])

        # Angle ticks
        for i, point in enumerate(points):
            if i == 0:
                a = point.lerp(points[-1], .125)
                b = point.lerp(points[1], .125)
            elif i == 1:
                a = point.lerp(points[0], .125)
                b = point.lerp(points[2], .125)
            elif i == 2:
                a = point.lerp(points[1], .125)
                b = point.lerp(points[3], .125)
            elif i == 3:
                a = point.lerp(points[2], .125)
                b = point.lerp(points[0], .125)

            if i < 4:
                dice_ticks.extend([
                    a, point,
                    point, b])

    if not SD.shader:
        built_in_shader = 'UNIFORM_COLOR' if bpy.app.version[0] >=4 else '3D_UNIFORM_COLOR'
        SD.shader = gpu.shader.from_builtin(built_in_shader)

    # Angle Ticks
    ticks_batch = batch_for_shader(SD.shader, 'LINES', {"pos": dice_ticks})
    # Full edges
    edges_batch = batch_for_shader(SD.shader, 'LINES', {"pos": dice_lines})
    # Points
    points_batch = batch_for_shader(SD.shader, 'POINTS', {"pos": dice_points})

    return ticks_batch, edges_batch, points_batch


def setup_draw_data(op):
    '''Generate all the draw data.'''

    SD.reset_data()
    
    if op.edit_mode != Mode.DICE_3D: return

    D3D = op.dice_3d

    boxelize = get_boxelize_ref()

    # X Data
    if D3D.x_dice.active or boxelize.active:
        SD.draw_x = True
        SD.xp_tick_batch, SD.xp_edge_batch, SD.xp_point_batch = build_batches(D3D.x_dice)
    # Y Data
    if D3D.y_dice.active or boxelize.active:
        SD.draw_y = True
        SD.yp_tick_batch, SD.yp_edge_batch, SD.yp_point_batch = build_batches(D3D.y_dice)
    # Z Data
    if D3D.z_dice.active or boxelize.active:
        SD.draw_z = True
        SD.zp_tick_batch, SD.zp_edge_batch, SD.zp_point_batch = build_batches(D3D.z_dice)

# --- Remove On App Reload --- #

from bpy.app.handlers import persistent
@persistent
def remove_dice_draw_shader(dummy):
    global HANDLE_3D
    if HANDLE_3D != None:
        bpy.types.SpaceView3D.draw_handler_remove(HANDLE_3D, "WINDOW")
        HANDLE_3D = None

    SD.reset_data()
    SD.reset_states()