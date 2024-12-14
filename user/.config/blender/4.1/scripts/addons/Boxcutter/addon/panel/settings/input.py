import bpy

from bpy.types import Panel

from .. utility import preset
from .... utility import addon, tool
from ... import toolbar
from ... property.utility import names


class BC_PT_input_settings(Panel):
    bl_label = 'Input'
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

        self.label_row(layout.row(), context.preferences.inputs, 'drag_threshold', label='Drag Threshold')

        if op.shape_type == 'NGON':
            self.label_row(layout.row(), preference.keymap, 'ngon_last_line_threshold')

        self.label_row(layout.row(), preference.keymap, 'repeat_threshold', label='Repeat Threshold')
        self.label_row(layout.row(), preference.keymap, 'ctrl_multiplier', label='Ctrl Factor')

        preset.shift_operation_draw(layout.row(align=True), context)

        self.label_row(layout.row(), preference.keymap, 'release_lock', label='Release Lock')
        self.label_row(layout.row(), preference.keymap, 'release_lock_lazorcut', label='Lazorcut Lock')
        self.label_row(layout.row(), preference.keymap, 'release_lock_repeat')
        self.label_row(layout.row(), preference.keymap, 'repeat_single_click')
        self.label_row(layout.row(), preference.keymap, 'quick_execute')
        self.label_row(layout.row(), preference.keymap, 'make_active')

        # self.label_row(layout.row(), preference.keymap, 'enable_surface_toggle')
        self.label_row(layout.row(), preference.keymap, 'enable_toolsettings', label='Enable Topbar')
        self.label_row(layout.row(), preference.keymap, 'allow_selection', label='Allow Selection')

        if tool.active().mode == 'EDIT_MESH':
            self.label_row(layout.row(), preference.keymap, 'edit_disable_modifiers', label='Disable Ctrl & Shift LMB')

        self.label_row(layout.row(), preference.keymap, 'view_pie', label='View Pie')

        self.label_row(layout.row(), preference.keymap, 'rmb_cancel_ngon', label='RMB Cancel Ngon')
        self.label_row(layout.row(), preference.keymap, 'rmb_preserve', label='Preserve RMB')

        self.label_row(layout.row(), preference.keymap, 'alt_preserve', label='Preserve Alt')
        self.label_row(layout.row(), preference.keymap, 'alt_draw', label='Alt Center')
        self.label_row(layout.row(), preference.keymap, 'alt_double_extrude', label='Alt Double Extrude')
        self.label_row(layout.row(), preference.keymap, 'alt_scroll_shape_type', label='Alt Scroll Change Shape')

        self.label_row(layout.row(), preference.keymap, 'shift_draw', label='Shift Uniform')
        self.label_row(layout.row(), preference.keymap, 'scroll_adjust_circle', label='Shift Scroll Adjust Circle')

        self.label_row(layout.row(), preference.keymap, 'd_helper', label='D Key Helper')
        self.label_row(layout.row(), preference.keymap, 'alternate_extrude', label='Alternate Extrude')


    def label_row(self, row, path, prop, label=''):
        row.label(text=label if label else names[prop])
        row.prop(path, prop, text='')
