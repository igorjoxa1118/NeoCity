import bpy
from ... utility import addon
from ...ui_framework.operator_ui import Master

class HOPS_OT_MOD_Subdivision(bpy.types.Operator):
    bl_idname = "hops.mod_subdivision"
    bl_label = "Add Subdivision Modifier"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = """LMB - Add Subdivision Modifier
LMB + Shift - Use Simple Option
LMB + CTRL - Add new Subdivision Modifier
LMB + ALT - Add Sub-d Modifier First In Stack (alt + shift)

"""
    sub_d_level: bpy.props.IntProperty(
        name="Sub-d Level",
        description="Amount Of Sub-d to add",
        default=2)

    simple: bpy.props.BoolProperty(
        name="Sub-d Level",
        description="method",
        default=False)

    make_first: bpy.props.BoolProperty(
        name="Make Sub-D first",
        description="Order",
        default=False)

    ctrl = False
    called_ui = False

    def __init__(self):

        HOPS_OT_MOD_Subdivision.called_ui = False

    @classmethod
    def poll(cls, context):
        return any(o.type == 'MESH' for o in context.selected_objects)

    def draw(self, context):
        self.layout.prop(self, "sub_d_level")

    def invoke(self, context, event):

        if event.ctrl:
            self.ctrl = True
        else:
            self.ctrl = False

        if event.alt or event.alt and event.shift:
            self.make_first = True
        else:
            self.make_first = False

        if event.shift and not event.alt:
            self.simple = True
        else:
            self.simple = False

        self.execute(context)

        bpy.ops.hops.draw_wire_mesh_launcher('INVOKE_DEFAULT', target='SELECTED')
        # Operator UI
        if not HOPS_OT_MOD_Subdivision.called_ui:
            HOPS_OT_MOD_Subdivision.called_ui = True

            ui = Master()
            draw_data = [
                ["SUBDIVISION (first)" if self.make_first else "SUBDIVISION"],
                ["Placement Order" if self.make_first else "Total Modifiers", '1' if self.make_first else f'{len(context.active_object.modifiers[:])}'],
                ["Subdivision Level", self.sub_d_level]]
                
            ui.receive_draw_data(draw_data=draw_data)
            ui.draw(draw_bg=addon.preference().ui.Hops_operator_draw_bg, draw_border=addon.preference().ui.Hops_operator_draw_border)

        return {"FINISHED"}

    def execute(self, context):

        for object in [o for o in context.selected_objects if o.type == 'MESH']:
            if self.ctrl:
                self.add_Subdivision_modifier(object, self.sub_d_level, self.simple, self.make_first)
            else:
                if not self.Subdivision_modifiers(object):
                    self.add_Subdivision_modifier(object, self.sub_d_level, self.simple, self.make_first)



        return {"FINISHED"}


    @staticmethod
    def Subdivision_modifiers(object):
        return [modifier for modifier in object.modifiers if modifier.type == "SUBSURF"]

    def add_Subdivision_modifier(self, object, sub_d_level, simple, make_first):
        subsurf_mod = object.modifiers.new(name="Subdivision", type="SUBSURF")
        if simple:
            subsurf_mod.subdivision_type = 'SIMPLE'
            subsurf_mod.levels = sub_d_level
        else:
            subsurf_mod.subdivision_type = 'CATMULL_CLARK'
            subsurf_mod.levels = sub_d_level
        if make_first:
            bpy.ops.object.modifier_move_to_index(modifier="Subdivision", index=0)
