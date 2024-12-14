import bpy

from bpy.types import Operator
from bpy.props import IntProperty

from . import utility


class BC_OT_shape_change(Operator):
    bl_idname = 'bc.shape_change'
    bl_label = 'Shape Change'
    bl_description = '\n Swap the current cutter with the next/previous cutter available in the collection'
    bl_options = {'INTERNAL'}

    index: IntProperty(default=1)

    def execute(self, context):
        bc = context.scene.bc

        if not bc.running:
            return {'CANCELLED'}

        utility.custom.cutter(bc.operator, context, index=self.index)

        return {'FINISHED'}


class BC_OT_shape_rotate_inside(Operator):
    bl_idname = 'bc.shape_rotate_inside'
    bl_label = 'Shape Rotate Inside'
    bl_description = '\n Rotate the shape on its local Z axis by 90 within the drawn proportions'
    bl_options = {'INTERNAL'}

    index: IntProperty(default=1)

    def execute(self, context):
        bc = context.scene.bc

        if not bc.running:
            return {'CANCELLED'}

        utility.modal.rotate.by_90(bc.operator, context, None)

        return {'FINISHED'}


class BC_OT_shape_rotate_shape(Operator):
    bl_idname = 'bc.shape_rotate_shape'
    bl_label = 'Shape Rotate'
    bl_description = '\n Rotate the shape on its local Z axis by 90'
    bl_options = {'INTERNAL'}

    index: IntProperty(default=1)

    def execute(self, context):
        bc = context.scene.bc

        if not bc.running:
            return {'CANCELLED'}

        utility.modal.rotate.by_90_shape(bc.operator, context)

        return {'FINISHED'}


class BC_OT_shape_flip_z(Operator):
    bl_idname = 'bc.shape_flip_z'
    bl_label = 'Shape Flip'
    bl_description = '\n Flip the shape on its local Z axis'
    bl_options = {'INTERNAL'}

    index: IntProperty(default=1)

    def execute(self, context):
        preference = utility.addon.preference()
        bc = context.scene.bc

        if not bc.running:
            return {'CANCELLED'}

        bc.operator.flip_z = not bc.operator.flip_z
        utility.modal.flip.shape(bc.operator, context, None)

        bevels = [m for m in bc.shape.modifiers if m.type == 'BEVEL']

        if not bevels:
            return {'FINISHED'}

        if preference.shape.bevel_both:
            preference.shape.bevel_both = False

            context.view_layer.update()

            preference.shape.bevel_both = True

        bevels = (m for m in bc.shape.modifiers if m.type == 'BEVEL')
        max_segments = max([m.segments for m in bevels])
        for i, m in enumerate(bevels):
            if i > 0:
                if bc.operator.flip_z:
                    m.segments = 1
                else:
                    m.segments = max_segments

        return {'FINISHED'}
