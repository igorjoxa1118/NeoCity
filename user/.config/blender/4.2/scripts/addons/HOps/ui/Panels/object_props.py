import bpy
from bpy.types import Panel

from math import radians
from ... utility import addon


class HOPS_PT_dimensions_options(Panel):
    bl_label = 'Dimensions'
    bl_space_type = 'VIEW_3D'
    bl_category = 'HardOps'
    bl_region_type = 'UI'


    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        preference = addon.preference().property
        obj = bpy.context.object

        layout.column().prop(obj, 'dimensions', expand=True)


class HOPS_PT_context_object(Panel):
    bl_label = 'Context_object',
    bl_category = 'HardOps',
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"
    bl_options = {'HIDE_HEADER'}

    def draw(self, context):
        layout = self.layout
        space = context.space_data

        row = layout.row()
        row.template_ID(context.view_layer.objects, "active", filter='AVAILABLE')