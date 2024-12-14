import bpy
from bpy.props import BoolProperty


class HOPS_OT_Curosr3d(bpy.types.Operator):
    bl_idname = "hops.cursor3d"
    bl_label = "Hops set 3d cursor"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = """Set Boolshape Status"""


    def execute(self, context):

        prefs = context.window_manager.keyconfigs[bpy.context.preferences.keymap.active_keyconfig].preferences
        if 'select_mouse' in prefs:
            if prefs['select_mouse'] == 1:
                return {'PASS_THROUGH'}
        
        #py.ops.transform.translate(cursor_transform=True)

        bpy.ops.view3d.cursor3d('INVOKE_DEFAULT', orientation='GEOM')

        return {'FINISHED'}
