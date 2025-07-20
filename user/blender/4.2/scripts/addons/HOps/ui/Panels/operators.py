import bpy
from bpy.types import Panel

from ... utility import addon


class HOPS_PT_operators(Panel):
    bl_label = 'Operators'
    bl_space_type = 'VIEW_3D'
    bl_category = 'HardOps'
    bl_region_type = 'UI'

    def draw(self, context):
        layout = self.layout
        preference = addon.preference().property

        column = layout.column(align=True)
