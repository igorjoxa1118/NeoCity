import bpy
from bpy.types import Operator
from bpy.props import FloatProperty
from ..Tools.independant_helper import*


class FLUENT_OT_Text2Mesh(Operator):
    "Convert a flat text into an object and clean the mesh"
    bl_idname = "fluent.texttomesh"
    bl_label = "Text2Mesh"
    bl_options = {'REGISTER', 'UNDO'}

    limit: FloatProperty(
        name="Angle limit",
        description="Remove vertices under this value.",
        min=0, max=179,
        default=5
    )

    thickness: FloatProperty(
        name="Thickness",
        description="Thickness of the solidify modifier.",
        min=0,
        default=0.2
    )

    def convert(self, obj):
        active_object('SET', obj, True)
        move = obj.dimensions[1] / 1000
        limit_angle = self.limit
        bpy.ops.object.convert(target='MESH')
        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.select_mode(type='FACE')
        bpy.ops.mesh.dissolve_limited(angle_limit=math.radians(limit_angle))
        bpy.ops.object.editmode_toggle()

        v_moved_01 = []

        for i in range(len(obj.data.vertices) - 1):
            v = obj.data.vertices
            try:
                if v[i].co.y == v[i + 1].co.y:
                    v[i].co.y = v[i].co.y + move
                    v_moved_01.append(v[i].co)
            except:
                if v[i].co.y == v[0].co.y:
                    v[i].co.y = v[i].co.y + move
                    v_moved_01.append(v[i].co)
        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.dissolve_limited(angle_limit=math.radians(0.1))
        bpy.ops.object.editmode_toggle()

        v_moved_02 = []
        for v in obj.data.vertices:
            for moved in v_moved_01:
                if v.co == moved:
                    v.co.y = v.co.y - (2 * move)
                    v_moved_02.append(v.co)
        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.dissolve_limited(angle_limit=math.radians(0.1))
        bpy.ops.object.editmode_toggle()

        for v in obj.data.vertices:
            for moved in v_moved_02:
                if v.co == moved:
                    v.co.y = v.co.y + move

        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.select_mode(type='VERT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles(threshold=0.0005)
        bpy.ops.object.editmode_toggle()

        modif = obj.modifiers.new(name='Solidify', type='SOLIDIFY')
        modif.offset = 0
        modif.thickness = self.thickness
        bpy.context.object.modifiers["Solidify"].show_in_editmode = False
        bpy.context.object.show_wire = True

    def execute(self, context):
        objs = bpy.context.selected_objects
        for obj in objs:
            if obj.type in {'FONT', 'CURVE'}:
                self.convert(obj)
        return {'FINISHED'}


classes = FLUENT_OT_Text2Mesh