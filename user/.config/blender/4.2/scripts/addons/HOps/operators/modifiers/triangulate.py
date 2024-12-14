from cgitb import text
import bpy
from bpy.props import BoolProperty

from ... utility import addon
from ... ui_framework.operator_ui import Master


DESC = """LMB - Add Triangulate Modifier
LMB + CTRL - Add new Triangulate Modifier
"""


class HOPS_OT_MOD_Triangulate(bpy.types.Operator):
    bl_idname = "hops.mod_triangulate"
    bl_label = "Add Triangulate Modifier"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = DESC

    keep_custom_normals: BoolProperty(
        name='keep_custom_normals',
        description='Keep Custom Normals',
        default=False)

    called_ui = False

    def __init__(self):
        HOPS_OT_MOD_Triangulate.called_ui = False

    @staticmethod
    def triangulate_modifiers(object):
        return [modifier for modifier in object.modifiers if modifier.type == "TRIANGULATE"]

    @classmethod
    def poll(cls, context):
        return any(o.type == 'MESH' for o in context.selected_objects)


    def invoke(self, context, event):
        self.ctrl = event.ctrl
        return self.execute(context)
        

    def execute(self, context):
      
        for object in [o for o in context.selected_objects if o.type == 'MESH']:
      
            if self.ctrl:
                self.add_triangulate_modifier(object)
      
            else:
                if not self.triangulate_modifiers(object):
                    self.add_triangulate_modifier(object)
                else:
                    bpy.ops.hops.display_notification(info=F'No Triangulate Added ', name='Use Ctrl to Add')
                    bpy.ops.hops.draw_wire_mesh_launcher('INVOKE_DEFAULT', target='SELECTED')
                    return {"CANCELLED"}

        # Operator UI
        if not HOPS_OT_MOD_Triangulate.called_ui:
            HOPS_OT_MOD_Triangulate.called_ui = True

            ui = Master()
            draw_data = [
                ["TRIANGULATE"],
                ["Min Vertices : ", self.tri_mod.min_vertices]]
            ui.receive_draw_data(draw_data=draw_data)
            ui.draw(draw_bg=addon.preference().ui.Hops_operator_draw_bg, draw_border=addon.preference().ui.Hops_operator_draw_border)
      
        return {'FINISHED'}


    def draw(self, context):
        layout = self.layout
        column = layout.column()
        row = column.row()
        row.prop(self, 'keep_custom_normals', text='Keep Custom Normals')


    def add_triangulate_modifier(self, object):
        self.tri_mod = object.modifiers.new(name="Triangulate", type="TRIANGULATE")
        self.tri_mod.min_vertices = 5
        self.tri_mod.show_in_editmode = False
        #self.tri_mod.keep_custom_normals = self.keep_custom_normals
        bpy.ops.hops.draw_wire_mesh_launcher('INVOKE_DEFAULT', target='SELECTED')
