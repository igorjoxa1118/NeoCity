import bpy
from bpy.types import Operator

from .... utility import addon
from ... operator.property import operation

shift_operations = [
    'DRAW',
    'EXTRUDE',
    'OFFSET',
    'MOVE',
    'ROTATE',
    'SCALE',
    'ARRAY',
    'SOLIDIFY',
    'BEVEL',
    'DISPLACE',
    'TAPER',
]


class BC_OT_shift_operation_preset_add(Operator):
    bl_idname = 'bc.shift_operation_preset_add'
    bl_label = 'Add Preset'
    bl_options = {'INTERNAL'}


    @classmethod
    def poll(cls, context):
        return 'New Preset' not in addon.preference().keymap.shift_operation_presets


    def execute(self, context):
        preference = addon.preference()

        preset = preference.keymap.shift_operation_presets.add()
        preset.name = 'New Preset'
        preset.operation = preference.keymap.shift_operation

        for shift_operation in operation.shift_operations:
            setattr(preset, shift_operation.lower(), getattr(preference.keymap.shift_in_operations, shift_operation.lower()))

        preference.keymap.shift_operation_preset = preset.name

        return {'FINISHED'}


class BC_OT_shift_operation_preset_remove(Operator):
    bl_idname = 'bc.shift_operation_preset_remove'
    bl_label = 'Remove Preset'
    bl_options = {'INTERNAL'}


    @classmethod
    def poll(cls, context):
        return addon.preference().keymap.shift_operation_preset


    def execute(self, context):
        preference = addon.preference()

        preset_name = preference.keymap.shift_operation_preset
        preset = preference.keymap.shift_operation_presets[preset_name]
        index = preference.keymap.shift_operation_presets[:].index(preset)

        if len(preference.keymap.shift_operation_presets) < 2:
            preference.keymap.shift_operation_presets.remove(index)
            preference.keymap.shift_operation_preset = ''
            return {'FINISHED'}

        prev_index = index - 1

        if prev_index < -1:
            prev_index = 0

        preference.keymap.shift_operation_preset = preference.keymap.shift_operation_presets[prev_index].name
        preference.keymap.shift_operation_presets.remove(index)

        return {'FINISHED'}
