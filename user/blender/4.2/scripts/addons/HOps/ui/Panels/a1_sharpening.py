import bpy
from bpy.props import *
from bpy.types import (Panel,
                       Operator,
                       AddonPreferences,
                       PropertyGroup,
                       )
from math import radians, degrees
from ... icons import get_icon_id
from ... utility import addon


class HOPS_PT_SharpPanel(bpy.types.Panel):
    bl_label = "Sharp"
    # bl_category = "HardOps"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)

        colrow = col.row(align=True)
        colrow.prop(addon.preference().property, "sharp_use_crease", text="Crease")
        colrow.prop(addon.preference().property, "sharp_use_bweight", text="Bweight")
        colrow.prop(addon.preference().property, "sharp_use_seam", text="Seam")
        colrow.prop(addon.preference().property, "sharp_use_sharp", text="Sharp")

        colrow = col.row(align=True)
        colrow.operator("hops.set_sharpness_30", text="30")
        colrow.operator("hops.set_sharpness_45", text="45")
        colrow.operator("hops.set_sharpness_60", text="60")

        col.prop(addon.preference().property, "sharpness", text="Sharpness")

        col.separator()
        col.operator("hops.sharp_manager", text="Sharps Manager")