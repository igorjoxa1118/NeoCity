import bpy
from ... utility import addon


class HOPS_PT_dice_options(bpy.types.Panel):
    bl_label = "Dice"
    bl_category = "HardOps"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'

    def draw(self, context):
        preference = addon.preference().property
        layout = self.layout
        column = layout.column(align=True)
        
        row = column.row(align=True)
        row.label(text='Solver / Adjustment Method')
        row = column.row(align=True)
        row.prop(preference, 'dice_method', text='')
        row.prop(preference, 'dice_adjust', text='')
        
        row = column.row(align=True)
        row.label(text='Initial Pre-Apply / Display Type')
        row = column.row(align=True)
        row.prop(preference, 'smart_apply_dice', text='')
        row.prop(preference, 'dice_wire_type', text='')

        row = column.row(align=True)
        row.prop(preference, 'dice_show_mesh_wire', text='Mesh Wire Fade (on exit)')

        column.separator()
