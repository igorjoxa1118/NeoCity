import bpy
from bpy.types import Operator

from .. import toolbar
from ... utility import addon


class BC_OT_helper(Operator):
    bl_idname = 'bc.helper'
    bl_label = 'Helper'
    bl_options = {'INTERNAL'}


    def execute(self, context):
        preference = addon.preference()
        op = toolbar.option()
        bc = context.scene.bc

        if op and preference.behavior.helper.shape_type != op.shape_type: # XXX: beware of shape type update method
            preference.behavior.helper.shape_type = op.shape_type

        if bc.running:
            for mod in bc.shape.modifiers:
                if mod.type != 'MIRROR':
                    continue

                preference.shape['mirror_axis'] = mod.use_axis
                preference.shape['mirror_bisect_axis'] = mod.use_bisect_axis
                preference.shape['mirror_flip_axis'] = mod.use_bisect_flip_axis

                break

        bpy.ops.wm.call_panel(name='BC_PT_helper', keep_open=True)

        return {'FINISHED'}


