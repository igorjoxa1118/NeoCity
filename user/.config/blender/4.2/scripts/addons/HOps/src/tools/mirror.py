import os
import bpy

from ... utility import addon


class HopsMirror(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'
    bl_idname = "hops.mirror"
    bl_label = "HardOps Mirror"
    bl_description = "HardOps Mirror"
    bl_icon = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'icons', 'toolbar')
    bl_widget = "hops.mirror_gizmogroup"
    bl_keymap = '3D View Tool: Hops'

    def draw_settings(context, layout, tool):
        draw_mirror(context, layout, tool)


def draw_mirror(context, layout, tool):

    preference = addon.preference()
    mir = preference.operator.mirror
    selected = context.selected_objects

    layout.label(text=f'Mirror mode:')
    layout.prop_with_popover(preference.operator.mirror, "mode", text="", panel="HOPS_PT_mirror_mode")
    if preference.operator.mirror.mode == 'MODIFIER':
        layout.label(text=f'Modifier:')
        layout.prop(preference.operator.mirror, "modifier", text="")

    layout.prop(preference.operator.mirror, 'advanced', text="", toggle=True, icon='ORIENTATION_GIMBAL')

    if preference.operator.mirror.advanced:
        if preference.operator.mirror.mode != 'SYMMETRY':
            layout.label(text=f'Orientation:')
            layout.prop_with_popover(preference.operator.mirror, "orientation", text="", panel="HOPS_PT_mirror_transform_orientations")
            layout.label(text=f'Pivot:')
            layout.prop_with_popover(preference.operator.mirror, "pivot", text="", panel="HOPS_PT_mirror_pivot")
    layout.label(text=f'Options:')
    layout.popover('HOPS_PT_MirrorOptions', text='', icon="SETTINGS")

    layout.separator_spacer()

    layout.prop(preference.operator.mirror, 'close', text="Close after operation", toggle=True)
    layout.operator('hops.mirror_exit', text='Exit')
