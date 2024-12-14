import bpy

from bpy.types import Panel

from ... utility import tool, addon
from .. property.utility import names
from . utility import preset
from .. import toolbar


class BC_PT_shape(Panel):
    bl_label = 'Shape'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'BoxCutter'


    @classmethod
    def poll(cls, context):
        active = tool.active()
        return active and active.idname == tool.name


    def draw(self, context):
        preference = addon.preference()
        bc = context.scene.bc
        op = toolbar.option()

        layout = self.layout
        column = layout.column()

        row = column.row()
        row.scale_x = 2.0
        row.scale_y = 1.5

        sub = row.row()
        sub.enabled = not bc.running
        sub.prop(op, 'shape_type', expand=True, text='')

        sub = row.row()
        sub.enabled = op.shape_type != 'NGON'
        sub.prop(op, 'origin', expand=True, text='')

        if op.shape_type == 'CIRCLE':
            self.label_row(layout.row(), preference.shape, 'circle_type', label='Type')
            self.label_row(layout.row(), preference.shape, 'circle_vertices', label='Vertices')
            if preference.shape.circle_type == 'STAR':
                self.label_row(layout.row(), preference.shape, 'circle_star_factor', label='Factor')

        # elif op.shape_type == 'NGON':
        #     self.label_row(layout.row(), preference.snap, 'ngon_angle', label='Snap Angle')

        elif op.shape_type == 'CUSTOM':
            self.label_row(layout.row(), bc, 'collection', label='Collection')

            if not bc.collection:
                self.label_row(layout.row(), bc, 'shape', label='Shape')

            else:
                row = layout.row()
                split = row.split(factor=0.5)
                split.label(text='Shape')
                split.prop_search(bc, 'shape', bc.collection, 'objects', text='')

        if op.shape_type != 'NGON':
            self.label_row(layout.row(), preference.behavior, 'draw_line')

        self.label_row(layout.row(align=True), preference.shape, 'wedge')
        if preference.shape.wedge:
            self.label_row(layout.row(align=True), preference.shape, 'wedge_factor', label='Factor')
            self.label_row(layout.row(align=True), preference.shape, 'wedge_width', label='Width')
            self.label_row(layout.row(align=True), preference.shape, 'wedge_lazorcut')

        if op.shape_type == 'BOX':
            self.label_row(layout.row(align=True), preference.shape, 'box_grid', label='Grid')

            if preference.shape.box_grid:
                self.label_row(layout.row(align=True), preference.shape, 'box_grid_border', label='Border')
                self.label_row(layout.row(align=True), preference.shape, 'box_grid_auto_solidify', label='Auto Solidify')
                self.label_row(layout.row(align=True), preference.shape, 'box_grid_fill_back', label='Fill Back Faces')
                self.label_row(layout.row(align=True), preference.shape, 'box_grid_divisions', label='Divisions')

        elif op.shape_type == 'NGON':
            self.label_row(layout.row(), preference.shape, 'cyclic', label='Cyclic')
            self.label_row(layout.row(), preference.shape, 'lasso', label='Lasso')

            if preference.shape.lasso:
                self.label_row(layout.row(align=True), preference.shape, 'lasso_spacing', label='Spacing')
                self.label_row(layout.row(align=True), preference.shape, 'lasso_adaptive', label='Adaptive')

    def label_row(self, row, path, prop, label=''):
        if prop in {'circle_vertices'}:
            column = self.layout.column(align=True)
            row = column.row(align=True)

        row.label(text=label if label else names[prop])
        row.prop(path, prop, text='')

        values = {
            'Vertices': preset.vertice,
            'Snap Angle': preset.angle}

        if prop in {'circle_vertices'}:
            row = column.row(align=True)
            split = row.split(factor=0.48, align=True)
            sub = split.row(align=True)
            sub = split.row(align=True)

            pointer = '.shape.'
            for value in values[label]:
                ot = sub.operator('wm.context_set_int', text=str(value))
                ot.data_path = F'preferences.addons[\"{__name__.partition(".")[0]}\"].preferences{pointer}{prop}'
                ot.value = value
