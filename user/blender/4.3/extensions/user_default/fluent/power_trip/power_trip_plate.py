import bpy
from bpy.types import Operator

class FLUENT_OT_Plate(Operator):
    """Turn faces into plates"""
    bl_idname = "fluent.plates"
    bl_label = "Fluent plates"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.object and context.object.mode == 'OBJECT':
            return True
        else:
            return False

    def invoke(self, context, event):
        bpy.ops.fluent.faceextraction('INVOKE_DEFAULT', call_by='plate')
        return {'FINISHED'}


classes = FLUENT_OT_Plate