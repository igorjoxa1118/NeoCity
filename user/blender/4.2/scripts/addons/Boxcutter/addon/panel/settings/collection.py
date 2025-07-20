import bpy

from bpy.types import Panel

from .... utility import tool, addon, modifier
from ... property.utility import names
from ... import toolbar


class BC_PT_collection_settings(Panel):
    bl_label = 'Collection'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'BoxCutter'
    bl_parent_id = 'BC_PT_settings'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        active = tool.active()
        return active and active.idname == tool.name and context.region.type == 'UI'


    def draw(self, context):
        preference = addon.preference()
        option = toolbar.option()
        layout = self.layout
        bc = context.scene.bc

        row = layout.row(align=True)

        self.label_row(layout.row(align=True), bc, 'collection', label='Collection')
        self.label_row(layout.row(align=True), bc, 'recall_collection', label='Recall Col.')
        self.label_row(layout.row(), preference.color, 'collection')

    def label_row(self, row, path, prop, label=''):
        row.label(text=label if label else names[prop])
        row.prop(path, prop, text='')
