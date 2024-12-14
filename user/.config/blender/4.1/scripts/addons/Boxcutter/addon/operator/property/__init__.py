import bpy

from bpy.utils import register_class, unregister_class

from . import operation, shape_type, set

classes = (
    operation.BC_OT_shift_operation_preset_add,
    operation.BC_OT_shift_operation_preset_remove,
    shape_type.BC_OT_box,
    shape_type.BC_OT_circle,
    shape_type.BC_OT_ngon,
    shape_type.BC_OT_custom,
    shape_type.BC_OT_subtype_scroll,
    set.BC_OT_set_int,
    set.BC_OT_set_float,
    set.BC_OT_set_bool,
    set.BC_OT_set_enum,
    )


def register():
    for cls in classes:
        register_class(cls)


def unregister():
    for cls in classes:
        unregister_class(cls)
