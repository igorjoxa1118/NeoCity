import bpy

from bpy.utils import register_class, unregister_class

from . import transform, mirror

classes = (
    transform.BC_OT_transform_translate,
    transform.BC_OT_transform_rotate,
    transform.BC_OT_transform_resize,
    transform.BC_WGT_transform_gizmo_group,
    transform.BC_OT_transform_add_gizmo,
    transform.BC_OT_transform_remove_gizmo,
    transform.BC_GT_transform_gizmo,
    mirror.BC_GGT_Mirror_GizmoGroup,
    mirror.BC_OT_Mirror_Gizmo_Xp,
    mirror.BC_OT_Mirror_Gizmo_Yp,
    mirror.BC_OT_Mirror_Gizmo_Zp,
    mirror.BC_OT_Mirror_Gizmo_Xn,
    mirror.BC_OT_Mirror_Gizmo_Yn,
    mirror.BC_OT_Mirror_Gizmo_Zn,
    mirror.BC_OT_Mirror_Gizmo_Toggle,
    mirror.BC_OT_Mirror_Gizmo_Disabled)


def register():
    for cls in classes:
        register_class(cls)


def unregister():
    for cls in classes:
        unregister_class(cls)
