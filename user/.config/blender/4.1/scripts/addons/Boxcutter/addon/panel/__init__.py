import bpy

from bpy.types import Panel
from bpy.utils import register_class, unregister_class

from .. operator.property.operation import shift_operations
from ... utility import addon
from .. import toolbar
from . utility import preset
from . import behavior, error, grid, mode, operation, release_lock, set_origin, shape, surface, snap, settings, help


class BC_PT_shift_operation(Panel):
    bl_label = 'Exclude Operations'
    bl_region_type = 'HEADER'
    bl_space_type = 'VIEW_3D'

    @staticmethod
    def label_prop(path, prop, layout, label=''):
        layout.label(text=label if label else names[prop])
        layout.prop(path, prop, text='')


    def draw(self, context):
        preference = addon.preference()
        has_presets = len(preference.keymap.shift_operation_presets)

        layout = self.layout

        row = layout.row(align=True)

        if has_presets and preference.keymap.shift_operation_preset:
            if preference.keymap.shift_operation_preset == 'New Preset':
                row.prop(preference.keymap.shift_operation_presets[preference.keymap.shift_operation_preset], 'name', text='')
            else:
                row.prop_search(preference.keymap, 'shift_operation_preset', preference.keymap, 'shift_operation_presets', text='')
        else:
            row.operator('bc.shift_operation_preset_add', text='New Preset', icon='ADD')

        row.operator('bc.shift_operation_preset_remove', text='', icon='REMOVE')
        row.operator('bc.shift_operation_preset_add', text='', icon='ADD')

        for operation in shift_operations:
            if operation == preference.keymap.shift_operation:
                continue

            self.label_prop(preference.keymap.shift_in_operations, operation.lower(), layout.row(), label=operation.title())


classes = [
    BC_PT_shift_operation,
    help.BC_PT_help,
    help.BC_PT_help_npanel_tool,
    help.BC_PT_help_npanel,
    help.general.BC_PT_help_general,
    help.general.BC_PT_help_general_npanel_tool,
    help.general.BC_PT_help_general_npanel,
    help.start_operation.BC_PT_help_start_operation,
    help.start_operation.BC_PT_help_start_operation_npanel_tool,
    help.start_operation.BC_PT_help_start_operation_npanel,
    behavior.BC_PT_helper,
    error.BC_PT_error_log,
    mode.BC_PT_mode,
    shape.BC_PT_shape,
    release_lock.BC_PT_release_lock,
    set_origin.BC_PT_set_origin,
    operation.BC_PT_operation,
    surface.BC_PT_surface,
    snap.BC_PT_snap,
    grid.BC_PT_grid,
    settings.BC_PT_settings,
    settings.behavior.BC_PT_behavior_settings,
    settings.sort_last.BC_PT_sort_last,
    settings.shape.BC_PT_shape_settings,
    settings.input.BC_PT_input_settings,
    settings.display.BC_PT_display_settings,
    settings.hardops.BC_PT_hardops_settings,
    settings.collection.BC_PT_collection_settings,
    settings.display.BC_OT_display_fade_next,
    settings.display.BC_OT_display_fade_prev,]


def register():
    for cls in classes:
        if hasattr(cls, 'bl_category') and cls.bl_category and cls.bl_category != 'Tool':
            cls.bl_category = addon.preference().display.tab
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
