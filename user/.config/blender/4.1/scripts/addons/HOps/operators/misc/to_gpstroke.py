import bpy, bmesh
from ... utility import addon, operator_override, context_copy
from math import pi


DESC = """Convert sharp edges to grease pencil object
"""

class HOPS_OT_TO_GPSTROKE(bpy.types.Operator):
    bl_idname = 'hops.to_gpstroke'
    bl_label = 'Create Grease Pencil from mesh'
    bl_options = {'REGISTER', 'UNDO', 'BLOCKING'}
    bl_description = DESC

    modified : bpy.props.BoolProperty(
    name='Modified',
    description='Use modified mesh',
    default=True,
    )

    convert_faces : bpy.props.BoolProperty(
    name='Faces',
    description='Convert Faces into filled strokes',
    default=True,
    )

    thickness : bpy.props.IntProperty(
    name='Thickness',
    description='Stroke Thickness',
    default=5,
    min=0,
    )

    stroke_offset : bpy.props.FloatProperty(
    name='Offset',
    description='Stroke offset',
    default=0.01,
    min=0
    )

    sharpness : bpy.props.FloatProperty(
    name='Sharpness',
    description='Face angle above which edge is considered sharp',
    default=pi/6,
    min=0,
    max = pi,
    subtype='ANGLE',
    )

    stroke_color : bpy.props.FloatVectorProperty(
    name='Stroke Color',
    description='Stroke Color',
    size=4,
    default= [0,0,0,1],
    min=0,
    max=1,
    subtype='COLOR'
    )

    fill_color : bpy.props.FloatVectorProperty(
    name='Fill Color',
    description='Fill Color',
    size=4,
    default= [1,1,1,1],
    min=0,
    max=1,
    subtype='COLOR'
    )

    hide_original : bpy.props.BoolProperty(
    name='Hide Original',
    description='Hide original object(s)',
    default=True,
    )


    object_types = frozenset((
        'MESH', 'CURVE', 'FONT', 'SURFACE', 'META'
    ))

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def draw(self, context):
        self.layout.prop(self, 'modified')
        self.layout.prop(self, 'convert_faces')
        self.layout.prop(self, 'thickness')
        self.layout.prop(self, 'stroke_offset')
        self.layout.prop(self, 'sharpness')
        self.layout.prop(self, 'stroke_color')

        if self.convert_faces:
            self.layout.prop(self, 'fill_color')

        self.layout.prop(self, 'hide_original')

    def invoke(self, context, event):
        self.notify = lambda val, sub='': bpy.ops.hops.display_notification(info=val, subtext=sub) if addon.preference().ui.Hops_extra_info else lambda val, sub=None: None
        self.selection = {o.name for o in context.selected_objects if o.type in self.object_types}
        self.active_obj_name = context.active_object.name

        if not self.selection:
            msg = 'No meshes in selection'
            self.notify('CANCELLED', msg)
            self.report({'INFO'}, msg)
            return {'CANCELLED'}

        return self.execute(context)

    def execute(self, context):
        created_objects = []

        bpy.ops.object.select_all(action='DESELECT')

        for name in self.selection:
            obj = bpy.data.objects[name]

            if self.modified:
                obj_eval = obj.evaluated_get(context.evaluated_depsgraph_get())
                mesh = obj_eval.data if obj.type == 'MESH' else obj_eval.to_mesh()
                bm = self.create_bmesh_data(mesh)
                obj_eval.to_mesh_clear()

            else:
                mesh = obj.data if obj.type == 'MESH' else obj.to_mesh()
                bm = self.create_bmesh_data(mesh)

            if not bm: continue

            new_data = bpy.data.meshes.new('Stroke')
            new_obj = bpy.data.objects.new('Stroke', new_data)
            new_obj.matrix_world = obj.matrix_world
            bm.to_mesh(new_data)

            context.collection.objects.link(new_obj)
            new_obj.select_set(True)

            override = context_copy(context)
            override['object'] = new_obj
            override['active_object'] = new_obj
            mod = new_obj.modifiers.new(type='TRIANGULATE', name='tri')
            mod.min_vertices = 5

            operator_override(context, bpy.ops.object.convert, override, target='GPENCIL', seams=True, faces=self.convert_faces, thickness=self.thickness, offset=self.stroke_offset)

            stroke = context.active_object
            created_objects.append(stroke)

            for slot in stroke.material_slots:
                slot.material.grease_pencil.color = self.stroke_color
                slot.material.grease_pencil.fill_color = self.fill_color

            if self.hide_original: obj.hide_set(True)

        if not created_objects:
            for name in self.selection:
                obj = bpy.data.objects[name]
                obj.select_set(True)

            context.view_layer.objects.active = bpy.data.objects[self.active_obj_name]
            msg ='No valid geometry in selection or sharpenss angle is too high'
            self.notify('CANCELLED', msg)
            self.report({'INFO'}, msg)

            return {'FINISHED'}

        for stroke in created_objects:
            stroke.select_set(True)

        msg = f'Created {len(created_objects)}/{len(self.selection)} strokes'
        self.notify('TO_STROKE', msg)

        self.report({'INFO'}, msg)
        return {'FINISHED'}

    def create_bmesh_data(self, input):
        bm = bmesh.new()
        bm.from_mesh(input)
        counter = 0

        for edge in bm.edges:
            flag = not edge.smooth or edge.calc_face_angle(4) >= self.sharpness
            edge.seam = flag
            counter += flag

        if self.convert_faces:
            if not counter and not bm.faces: return False

        else:
            if not counter: return False

        return bm
