import bpy
import blf

from .. utils.blender_ui import get_dpi_factor

dpi = 72


def set_drawing_dpi(new_dpi):
    global dpi
    dpi = new_dpi


def draw_boolean(state, x, y, size=12, alpha=1):
    if state:
        draw_text("ON", x, y, align="LEFT", size=size,
                  color=(0.8, 1, 0.8, alpha))
    else:
        draw_text("OFF", x, y, align="LEFT", size=size,
                  color=(1, 0.8, 0.8, alpha))


def draw_text(text, x, y, align="LEFT", size=12, color=(1, 1, 1, 1)):
    font = 0
    if bpy.app.version[0] >= 4:
        blf.size(font, size * (dpi / 72.0))
    else:
        blf.size(font, size, int(dpi))
    blf.color(font, *color)

    if align == "LEFT":
        blf.position(font, x, y, 0)
    else:
        width, height = blf.dimensions(font, text)
        if align == "RIGHT":
            blf.position(font, x - width, y, 0)

    blf.draw(font, text)
