import bpy
from bpy.types import Panel

from ... utility import addon


class HOPS_PT_mesh_clean_options(Panel):
    bl_label = 'Mesh Clean / Dice'
    bl_space_type = 'VIEW_3D'
    bl_category = 'HardOps'
    bl_region_type = 'UI'


    def draw(self, context):
        layout = self.layout
        preference = addon.preference().property

        column = layout.column(align=True)
        box = column.box()

        box.label(text="Mesh Clean")

        row = box.row(align=True)
        row.prop(preference, 'meshclean_mode', expand=True)

        row = box.row(align=True)
        row.prop(preference, 'meshclean_dissolve_angle', text="Limited Dissolve Angle")
        row.prop(preference, 'meshclean_remove_threshold', text="Remove Threshold")
        row.prop(preference, 'meshclean_degenerate_iter', text="Degenerate Pass")

        row = box.row(align=True)
        row.prop(preference, 'meshclean_unhide_behavior', text="Unhide Mesh")
        row.prop(preference, 'meshclean_delete_interior', text="Delete Interior Faces")

        box.separator()

        column = layout.column(align=True)
        box = column.box()

        box.label(text='Dice')

        row = box.row(align=True)
        row.label(text='Solver / Pre-Apply ')
        row.prop(preference, 'dice_method', text='')
        row.prop(preference, 'smart_apply_dice', text='')

        row = box.row(align=True)
        row.label(text='Display ')
        row.prop(preference, 'dice_wire_type', text='')
        row.prop(preference, 'dice_show_mesh_wire', text='Wire Fade')
