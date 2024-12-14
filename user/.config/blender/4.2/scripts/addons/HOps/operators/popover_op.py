import bpy
from bpy.props import StringProperty
from .modals.adjust_bevel import HOPS_OT_AdjustBevelOperator
from .modals.st3_array import HOPS_OT_ST3_Array
from .meshtools.selection_to_boolean_v3 import HOPS_OT_Sel_To_Bool_V3
from .modals.face_extract import HOPS_OT_FaceExtract
from ..operators.booleans.bool_modal import HOPS_OT_BoolModal


class HOPS_OT_POPOVER(bpy.types.Operator):
    bl_idname = "hops.popover_data"
    bl_label = "HopsPopOverData"
    bl_description = "Popover Data"
    bl_options = {"INTERNAL"}

    calling_ops: StringProperty(default="")

    str_1: StringProperty(default="")


    def execute(self, context):

        if self.calling_ops == 'BEVEL_ADJUST':
            HOPS_OT_AdjustBevelOperator.mod_selected = self.str_1

        elif self.calling_ops == 'ARRAY_V2':
            HOPS_OT_ST3_Array.operator.mod_selected = self.str_1

        elif self.calling_ops == 'BOOL_MODAL':
            HOPS_OT_BoolModal.selected_operation = self.str_1

        elif self.calling_ops == 'SELECT_TO_BOOLEAN':
            HOPS_OT_Sel_To_Bool_V3.selected_operation = self.str_1

        elif self.calling_ops == 'FACE_EXTRACT':
            HOPS_OT_FaceExtract.selected_operation = self.str_1

        return {'FINISHED'}