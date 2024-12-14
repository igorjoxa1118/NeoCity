import bpy
import blf
import gpu
from gpu_extras.batch import batch_for_shader


###############################################################
#   2D Drawing
###############################################################


def draw_2D_geo(vertices, indices, color=(1,1,1,1)):
    '''Render geo to the screen.'''

    built_in_shader = 'UNIFORM_COLOR' if bpy.app.version[0] >=4 else '2D_UNIFORM_COLOR'
    shader = gpu.shader.from_builtin(built_in_shader)
    batch = batch_for_shader(shader, 'TRIS', {"pos": vertices}, indices=indices)
    shader.bind()
    shader.uniform_float("color", color)
    gpu.state.blend_set('ALPHA')
    batch.draw(shader)
    gpu.state.blend_set('NONE')

    del shader
    del batch


def draw_2D_lines(vertices, width=1, color=(0,0,0,1)):
    '''Draw lines to the screen.'''

    built_in_shader = 'UNIFORM_COLOR' if bpy.app.version[0] >=4 else '2D_UNIFORM_COLOR'
    shader = gpu.shader.from_builtin(built_in_shader)
    #Enable(GL_LINE_SMOOTH)
    gpu.state.blend_set('ALPHA')
    gpu.state.line_width_set(width)
    batch = batch_for_shader(shader, 'LINE_STRIP', {"pos": vertices})
    shader.bind()
    shader.uniform_float("color", color)
    batch.draw(shader)
    gpu.state.blend_set('NONE')

    del shader
    del batch


def draw_2D_points(vertices, size=3, color=(0,0,0,1)):
    '''Draw lines to the screen.'''

    built_in_shader = 'UNIFORM_COLOR' if bpy.app.version[0] >=4 else '2D_UNIFORM_COLOR'
    shader = gpu.shader.from_builtin(built_in_shader)
    gpu.state.point_size_set(size)
    gpu.state.blend_set('ALPHA')
    batch = batch_for_shader(shader, 'POINTS', {"pos": vertices})
    shader.bind()
    shader.uniform_float("color", color)
    batch.draw(shader)
    gpu.state.blend_set('NONE')

    del shader
    del batch


def draw_2D_text(text, x, y, size=12, color=(1,1,1,1), dpi=72):
    '''Draw text to the screen.'''

    font_id = 0
    blf.position(font_id, x, y, 0)
    if bpy.app.version[0] >= 4:
        blf.size(font_id, size * (dpi / 72.0))
    else:
        blf.size(font_id, size, dpi)
    blf.color(font_id, *color)
    blf.draw(font_id, text)