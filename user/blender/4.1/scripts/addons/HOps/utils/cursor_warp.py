import bpy
from ..utility.screen import dpi_factor
from .. utility import addon


def get_screen_warp_padding():
    '''The padding around the modal frame.'''

    tolerance = addon.preference().ui.Hops_warp_mode_padding
    return int(tolerance * dpi_factor())


def mouse_warp(context, event):
    '''Warp the mouse in the screen region.'''

    if not addon.preference().ui.Hops_warp_on: return

    if event.type == 'INBETWEEN_MOUSEMOVE':
        return False
        
    mouse_warped = False

    mouse_pos = (event.mouse_region_x, event.mouse_region_y)
    x_pos = mouse_pos[0]
    y_pos = mouse_pos[1]
    tolerance = get_screen_warp_padding()
    padding = 5

    # X Warp
    if mouse_pos[0] + tolerance > context.area.width:
        x_pos = tolerance + padding
    elif mouse_pos[0] - tolerance < 0:
        x_pos = context.area.width - (tolerance + padding)

    # Y Warp
    if mouse_pos[1] + tolerance > context.area.height:
        y_pos = tolerance + padding
    elif mouse_pos[1] - tolerance < 0:
        y_pos = context.area.height - (tolerance + padding)

    if x_pos != mouse_pos[0] or y_pos != mouse_pos[1]:
        x_pos += context.area.x
        y_pos += context.area.y

        context.window.cursor_warp(x_pos, y_pos)
        mouse_warped = True

    return mouse_warped