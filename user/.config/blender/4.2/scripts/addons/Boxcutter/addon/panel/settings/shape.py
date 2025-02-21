import bpy

from bpy.types import Panel

from .... utility import addon, tool
from ... property.utility import names
from ... import toolbar


class BC_PT_shape_settings(Panel):
    bl_label = 'Shape'
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
        bc = context.scene.bc
        op = toolbar.option()
        layout = self.layout

        layout.separator()

        # self.label_row(layout.row(), preference.shape, 'offset')
        # self.label_row(layout.row(), preference.shape, 'lazorcut_limit', label='Lazorcut Thresh')

        if preference.behavior.accucut:
            row = layout.row(align=True)
            self.label_row(row, preference.shape, 'lazorcut_depth', label='Lazorcut Depth')

        row = layout.row(align=True)
        row.label(text='Auto Depth')
        row.prop(preference.shape, 'auto_depth', text='')#, icon='CON_SAMEVOL')

        sub = row.row(align=True)
        sub.enabled = preference.shape.auto_depth
        sub.prop(preference.shape, 'auto_depth_large', text='', icon='FULLSCREEN_ENTER' if preference.shape.auto_depth_large else 'FULLSCREEN_EXIT')
        sub.prop(preference.shape, 'auto_depth_custom_proportions', text='', icon='FILE_NEW')
        sub.prop(preference.shape, 'auto_depth_multiplier', text='')

        layout.separator()

        self.label_row(layout.row(), preference.shape, 'auto_proportions', label='Auto Proportions')

        layout.separator()

        self.label_row(layout.row(), preference.shape, 'circle_vertices')

        layout.separator()

        self.label_row(layout.row(), preference.shape, 'rotate_axis')

        layout.separator()

        self.label_row(layout.row(), preference.shape, 'inset_thickness')

        layout.separator()

        self.label_row(layout.row(), preference.shape, 'array_count')
        self.label_row(layout.row(), preference.shape, 'array_axis')
        # self.label_row(layout.row(), preference.shape, 'array_around_cursor')

        layout.separator()

        self.label_row(layout.row(), preference.shape, 'solidify_thickness')

        layout.separator()

        self.label_row(layout.row(), preference.shape, 'bevel_width')
        self.label_row(layout.row(), preference.shape, 'bevel_segments')
        self.label_row(layout.row(), preference.shape, 'quad_bevel')

        if preference.shape.quad_bevel:
            self.label_row(layout.row(),preference.shape, 'front_bevel_width',  label='Quad Bevel Width')
            self.label_row(layout.row(),preference.shape, 'quad_bevel_segments',  label='Quad Bevel Segments')
        # self.label_row(layout.row(), preference.shape, 'straight_edges')

        if op.shape_type == 'BOX' or (op.shape_type == 'CIRCLE' and preference.shape.circle_type != 'MODIFIER') or op.shape_type == 'NGON':
            self.label_row(layout.row(), bc, 'bevel_front_face')

            if bc.bevel_front_face:
                self.label_row(layout.row(),preference.shape, 'front_bevel_width',  label='Front Bevel Width')
                self.label_row(layout.row(),preference.shape, 'front_bevel_segments',  label='Front Bevel Segments')

        layout.separator()

        self.label_row(layout.row(), preference.shape, 'taper')
        self.label_row(layout.row(), preference.behavior, 'persistent_taper', label='Persistent')
        self.label_row(layout.row(), preference.behavior, 'keep_lattice_taper', label='Keep Taper Lattice')

        layout.separator()

        self.label_row(layout.row(), preference.shape, 'cycle_all')
        self.label_row(layout.row(), preference.shape, 'cycle_dimensions')

        if op.shape_type == 'NGON':
            self.label_row(layout.row(), preference.shape, 'cyclic', label='Cyclic')
            self.label_row(layout.row(), preference.shape, 'lasso', label='Lasso')

            if preference.shape.lasso:
                self.label_row(layout.row(align=True), preference.shape, 'lasso_spacing', label='Spacing')
                self.label_row(layout.row(align=True), preference.shape, 'lasso_adaptive', label='Adaptive')

        self.label_row(layout.row(), preference.shape, 'auto_flip_xy')

    def label_row(self, row, path, prop, label=''):
        row.label(text=label if label else names[prop])
        row.prop(path, prop, text='')
