import bpy

from bpy.types import Panel

from ... utility import tool, addon
from .. property.utility import names
from . utility import preset
from .. import toolbar


class BC_PT_operation(Panel):
    bl_label = 'Operations'
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
        layout.ui_units_x = 15

        column = layout.column()
        column.scale_x = 1.5
        column.scale_y = 1.5

        row = column.row(align=True)

        if self.is_popover:
            row.active = bc.running
            row.prop(op, 'operation', expand=True)
            preset.shift_operation_draw(layout.row(align=True), context)

        else:
            row.prop(bc, 'start_operation', expand=True, icon_only=True)
            sub = row.row(align=True)
            sub.active = bc.running
            sub.prop(op, 'operation', text='', icon_only=True)

        if op.operation == 'ARRAY':
            self.label_row(layout.row(align=True), preference.shape, 'array_count', label='Count')

            if not bc.running:
                self.label_row(layout.row(align=True), preference.shape, 'array_axis', label='Axis')

            # if not bc.running:
            #     self.label_row(layout.row(align=True), preference.shape, 'array_around_cursor', label='3D Cursor')

        elif op.operation == 'BEVEL':
            self.label_row(layout.row(align=True), preference.shape, 'bevel_width', label='Width')
            self.label_row(layout.row(align=True), preference.shape, 'bevel_segments', label='Segments')
            self.label_row(layout.row(align=True), preference.shape, 'quad_bevel')

            if op.shape_type == 'BOX':
                self.label_row(layout.row(align=True), bc, 'bevel_front_face')

            # if preference.shape.quad_bevel:
            #     self.label_row(layout.row(align=True), preference.shape, 'straight_edges')

        elif op.operation == 'SOLIDIFY':
            self.label_row(layout.row(align=True), preference.shape, 'solidify_thickness', label='Thickness')

        elif op.operation == 'TAPER':
            self.label_row(layout.row(align=True), preference.shape, 'taper', label='Taper')
            self.label_row(layout.row(), preference.behavior, 'persistent_taper', label='Persistent')


    def label_row(self, row, path, prop, label=''):
        if prop in {'array_count', 'bevel_width', 'bevel_segments', 'taper'}:
            column = self.layout.column(align=True)
            row = column.row(align=True)
        else:
            row.scale_x = 1.2

        row.label(text=label if label else names[prop])
        row.prop(path, prop, text='')

        values = {
            'Count': preset.array,
            'Width': preset.width,
            'Segments': preset.segment,
            'Taper': preset.taper}

        if prop in {'array_count', 'bevel_width', 'bevel_segments', 'taper'}:
            row = column.row(align=True)
            split = row.split(factor=0.49, align=True)
            sub = split.row(align=True)
            sub = split.row(align=True)

            for value in values[label]:
                ot = sub.operator(F'wm.context_set_{"int" if prop not in {"bevel_width", "taper"} else "float"}', text=str(value))
                ot.data_path = F'preferences.addons["{__name__.partition(".")[0]}"].preferences.shape.{prop}'
                ot.value = value

            column.separator()
