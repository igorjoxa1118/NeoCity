import bpy
from bpy.props import BoolProperty
from ... utility import addon


class HOPS_OT_DecalMachineFix(bpy.types.Operator):
    bl_idname = "hops.decalmachine_fix"
    bl_label = "Enable/Disable DM Fix"
    bl_description = "Enable/Disable DM Fix"
    bl_options = {"REGISTER", "UNDO"}

    option : BoolProperty(name="enable/disable", default=False)

    def execute(self, context):
        addon.preference().property.decalmachine_fix = self.option

        return {"FINISHED"}
