import bpy

from bpy.utils import register_class, unregister_class

from . import change, draw, snap
from . draw import shader


classes = (
    change.BC_OT_shape_change,
    change.BC_OT_shape_rotate_inside,
    change.BC_OT_shape_rotate_shape,
    change.BC_OT_shape_flip_z,
    draw.BC_OT_shape_draw,
    shader.BC_OT_shader,
    snap.BC_OT_shape_snap)


def register():
    for cls in classes:
        register_class(cls)


def unregister():
    for cls in classes:
        unregister_class(cls)
