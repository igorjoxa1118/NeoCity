import bpy
from ... utility import ops
from ... utils.context import ExecutionContext
from ... utility import addon
from ... ui_framework.operator_ui import Master

class HOPS_OT_SphereCast(bpy.types.Operator):
    bl_idname = "hops.sphere_cast"
    bl_label = "Sphere / Cast"
    bl_description = "Adds subdivision and cast modifier to object making it a sphere"
    bl_options = {"REGISTER", "UNDO"}

    called_ui = False

    def __init__(self):

        HOPS_OT_SphereCast.called_ui = False

    @classmethod
    def poll(cls, context):
        return True


    def execute(self, context):
        object = bpy.context.active_object
        sphereCast(object)

        # Operator UI
        if not HOPS_OT_SphereCast.called_ui:
            HOPS_OT_SphereCast.called_ui = True

            ui = Master()
            draw_data = [
                ["Spherecast"],
                ["Subdivision/Cast", "Added"],
                ["Converted To Sphere"]
                ]
            ui.receive_draw_data(draw_data=draw_data)
            ui.draw(draw_bg=addon.preference().ui.Hops_operator_draw_bg, draw_border=addon.preference().ui.Hops_operator_draw_border)


        return {"FINISHED"}


def sphereCast(object):
    with ExecutionContext(mode="OBJECT", active_object=object):
        bpy.ops.object.subdivision_set(level=4)
        bpy.ops.object.modifier_add(type='CAST')
        bpy.context.object.modifiers["Cast"].factor = 1
        for mod in object.modifiers: 
            if hasattr(mod, 'levels'):
                if hasattr(mod, 'render_levels'):
                    if mod.levels != mod.render_levels:
                        mod.render_levels = mod.levels
        ops.shade_smooth()
