import bpy
from ... utils.context import ExecutionContext
from ... utility import object


class HOPS_OT_ResetStatus(bpy.types.Operator):
    bl_idname = "hops.reset_status"
    bl_label = "Reset Status"
    bl_description = """Resets properties related to hops w/ selected mesh
    EX: reset a boolshape to a normal mesh
    """
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        obj = bpy.context.active_object

        enableCyclesVisibility(obj)
        enableVisibility(obj)
        obj.hops.status = "UNDEFINED"

        try:
            bpy.data.collections['Hardops'].objects.unlink(obj)
        except:
            pass

        # bpy.ops.object.mode_set(mode='EDIT')
        # original_selection_mode = tuple(bpy.context.tool_settings.mesh_select_mode)
        # bpy.context.tool_settings.mesh_select_mode = (False, True, False)
        # bpy.ops.mesh.mark_sharp(clear=True)
        # bpy.ops.transform.edge_bevelweight(value=-1)
        # bpy.ops.transform.edge_crease(value=-1)
        # bpy.context.tool_settings.mesh_select_mode = original_selection_mode
        # bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.hops.draw_wire_mesh_launcher('INVOKE_DEFAULT', target='SELECTED')
        bpy.ops.hops.display_notification(info="Status Reset")


        return {"FINISHED"}


def enableCyclesVisibility(obj):
    with ExecutionContext(mode="OBJECT", active_object=obj):
        object.hide_set(obj, False, viewport=False, render=False)
        bpy.context.object.display_type = 'SOLID'


def enableVisibility(obj):
    with ExecutionContext(mode="OBJECT", active_object=obj):
        #Enable Renderability
        bpy.context.object.hide_render = False
        bpy.context.object.display_type = 'TEXTURED'
