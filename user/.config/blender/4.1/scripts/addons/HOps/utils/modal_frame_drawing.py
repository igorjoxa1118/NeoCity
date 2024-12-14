import bpy, blf, math, gpu
from gpu_extras.batch import batch_for_shader
from .cursor_warp import get_screen_warp_padding
from ..ui_framework.graphics.draw import draw_2D_lines
from ..utility.screen import dpi_factor
from .. utility import addon


def draw_modal_frame(context: bpy.context):
    '''Draw the frame around the modal screen.'''

    if addon.preference().ui.Hops_warp_on == False:
        return
    if addon.preference().ui.Hops_warp_border_display == False:
        return

    scale_factor = dpi_factor()
    tolerance = get_screen_warp_padding()

    width = addon.preference().ui.Hops_warp_line_width

    if addon.preference().ui.Hops_warp_border_display_style == 'BORDER':

        vertices = [
            # Bottom Left
            (tolerance, tolerance),
            # Top Left
            (tolerance, context.area.height - tolerance),
            # Top Right
            (context.area.width - tolerance, context.area.height - tolerance),
            # Bottom Right
            (context.area.width - tolerance, tolerance),
            # Bottom Left
            (tolerance, tolerance)]

        color = addon.preference().color.Hops_UI_cell_background_color

        draw_2D_lines(vertices, width=width, color=color)

    if addon.preference().ui.Hops_warp_border_display_style == 'CORNERS':

        length = addon.preference().ui.Hops_warp_line_length

        vertices = [
            (tolerance, tolerance + length),
            (tolerance, tolerance),
            (tolerance + length, tolerance),
        
            (tolerance, context.area.height - tolerance - length),
            (tolerance, context.area.height - tolerance),
            (tolerance + length, context.area.height - tolerance),
        
            (context.area.width - tolerance, context.area.height - tolerance - length),
            (context.area.width - tolerance, context.area.height - tolerance),
            (context.area.width - tolerance - length, context.area.height - tolerance),
        
            (context.area.width - tolerance, tolerance + length),
            (context.area.width - tolerance, tolerance),
            (context.area.width - length - tolerance, tolerance)]

        indices = [
            (0,1),
            (1,2),

            (3,4),
            (4,5),

            (6,7),
            (7,8),

            (9,10),
            (10,11)]

        color = addon.preference().color.Hops_UI_cell_background_color

        built_in_shader = 'UNIFORM_COLOR' if bpy.app.version[0] >=4 else '2D_UNIFORM_COLOR'
        shader = gpu.shader.from_builtin(built_in_shader)
        #Enable(GL_LINE_SMOOTH)
        gpu.state.blend_set('ALPHA')
        gpu.state.line_width_set(width)
        batch = batch_for_shader(shader, 'LINES', {"pos": vertices}, indices=indices)
        shader.bind()
        shader.uniform_float("color", color)
        batch.draw(shader)
        gpu.state.blend_set('NONE')

        del shader
        del batch