from bpy.types import Operator, Menu
from .Tools.helper import *
from .Tools.constants import *


class FLUENT_OT_AddPrimitive(Operator):
    "Add Fluent primitive"
    bl_idname = "fluent.addprimitive"
    bl_label="Add Fluent primitive"
    bl_options={'REGISTER','UNDO'}

    type : bpy.props.StringProperty(
    description = "primitive name",
    name        = "type",
    default     = "CUBE"
    )

    def execute(self,context):
        if self.type == 'CUBE':
            bpy.ops.mesh.primitive_plane_add(size=2, enter_editmode=False, align='WORLD')
            bpy.ops.fluent.becomefluent('INVOKE_DEFAULT', call_from='PRIMITIVE')
        elif self.type == 'CYLINDER':
            bool_obj = make_prism()
            bool_obj['fluent_type'] = 'prism'
            radius = bool_obj.modifiers[fluent_modifiers_name['radius']]
            radius.strength = 0.5
            screw = bool_obj.modifiers[fluent_modifiers_name['screw']]
            screw.steps = screw.render_steps = auto_bevel_segments(displace=radius)

            active_object('SET', bool_obj, True)
            use_auto_smooth(bpy.context.object.data)
            bpy.ops.view3d.snap_selected_to_cursor()

            bpy.ops.fluent.editor('INVOKE_DEFAULT', bool_obj_name=bool_obj.name, cut_obj_name='',
                                  operation='CREATION')
        elif self.type == 'SPHERE':
            bool_obj = make_sphere()
            bool_obj['fluent_type'] = 'sphere'
            radius = bool_obj.modifiers[fluent_modifiers_name['radius']]

            radius.strength = 0.5
            screw_2 = bool_obj.modifiers[fluent_modifiers_name['screw_2']]
            screw_2.steps = screw_2.render_steps = int(auto_bevel_segments(displace=bool_obj.modifiers[fluent_modifiers_name['radius']]) / 2)
            screw = bool_obj.modifiers[fluent_modifiers_name['screw']]
            screw.steps = screw.render_steps = int(screw_2.steps / 3)

            active_object('SET', bool_obj, True)
            use_auto_smooth(bpy.context.object.data)
            bpy.ops.view3d.snap_selected_to_cursor()
            bpy.ops.fluent.editor('INVOKE_DEFAULT', bool_obj_name=bool_obj.name, cut_obj_name='',
                                  operation='CREATION')

        return {'FINISHED'}


class FLUENT_MT_Primitive_Menu(Menu):
    bl_label = "Fluent primitives"

    def draw(self, context):
        self.layout.operator('fluent.addprimitive', text='F Cube', icon='MESH_CUBE').type='CUBE'
        self.layout.operator('fluent.addprimitive', text='F Cylinder', icon='MESH_CYLINDER').type='CYLINDER'
        self.layout.operator('fluent.addprimitive', text='F Sphere', icon='MESH_UVSPHERE').type='SPHERE'


def primitive_add(self, context):
    self.layout.menu("FLUENT_MT_Primitive_Menu", text='Fluent Primitives')