import bpy
import blf
from ... utility import addon
from ... utils.blender_ui import get_dpi


def bevel_verts(quad=((0,1), (0,0), (1,1), (0,1))):
    '''Return beveled quad, indices. \n
        Top Left, Bottom Left, Top Right, Bottom Right
    '''

    radius = 2
    vertices = []

    top_left = quad[0]
    bottom_left = quad[1]
    top_right = quad[2]
    bottom_right = quad[3]

    vertices = []

    #Top Left
    vertices.append((top_left[0] + radius, top_left[1]))
    vertices.append((top_left[0], top_left[1] - radius))

    #Bottom Left
    vertices.append((bottom_left[0], bottom_left[1] + radius))
    vertices.append((bottom_left[0] + radius, bottom_left[1]))

    #Bottom Right
    vertices.append((bottom_right[0] - radius, bottom_right[1]))
    vertices.append((bottom_right[0], bottom_right[1] + radius))

    #Top Right
    vertices.append((top_right[0], top_right[1] - radius))
    vertices.append((top_right[0] - radius, top_right[1]))

    #Make indices

    indices = [
        (0, 1, 2),
        (0, 2, 3),
        (0, 3, 4),
        (0, 4, 5),
        (0, 5, 6),
        (0, 6, 7),
    ]

    return vertices, indices


def get_blf_text_dims(text, size):
    '''Return the total width of the string'''
    #Prefs
    prefs = addon.preference()
    prefs_ui_scale = prefs.ui.Hops_modal_size

    dpi = int(get_dpi() * prefs_ui_scale)
    if bpy.app.version[0] >= 4:
        blf.size(0, size * (dpi / 72.0))
    else:
        blf.size(0, size, dpi)
    dims = blf.dimensions(0, str(text))

    return dims
