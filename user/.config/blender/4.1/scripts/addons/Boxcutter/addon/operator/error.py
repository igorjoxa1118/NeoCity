import bpy

from bpy.types import Operator
from bpy.props import StringProperty, BoolProperty

from ... import utility


class BC_OT_error_log(Operator):
    bl_idname = 'bc.error_log'
    bl_label = 'Error Encountered'
    bl_description = '\n  Click to view error log'
    bl_options = {'INTERNAL'}


    def execute(self, context):
        from .. utility import cleanup_operators
        utility.handled_error = False

        element_default = {
            'expand': False,
            'count': 1,
            'header': '',
            'body': '',
        }

        utility.error_elem = {}

        for error in utility.error_log:
            if error not in utility.error_elem:
                utility.error_elem[error] = element_default.copy()
                utility.error_elem[error]['header'] = error.split('\n')[-1]
                utility.error_elem[error]['body'] = error
            else:
                utility.error_elem[error]['count'] += 1

        cleanup_operators(None)

        bpy.ops.wm.call_panel(name='BC_PT_error_log', keep_open=True)
        return {'FINISHED'}


class BC_OT_error_clean(Operator):
    bl_idname = 'bc.error_clean'
    bl_label = 'BC Cleanup'
    bl_description = '\n  Cleanup boxcutter scene data'
    # bl_options = {'INTERNAL'}


    def execute(self, context):
        from .. utility import cleanup_operators
        cleanup_operators(None)

        return {'FINISHED'}
