import bpy

from bpy.types import Operator
from bpy.props import StringProperty, IntProperty, FloatProperty, BoolProperty

from .... utility import tool


def set_prop(data_path, value):
        if data_path[:3] != 'bpy':
            data_path = 'bpy.context.' + data_path

        data = ".".join(data_path.split('.')[:-1])
        prop = data_path.split('.')[-1]

        setattr(eval(data), prop, value)


class BC_OT_set_int(Operator):
    bl_idname = 'bc.set_int'
    bl_label = 'Set Integer'
    bl_options = {'INTERNAL'}

    data_path: StringProperty()
    value: IntProperty()


    def execute(self, context):
        set_prop(self.data_path, self.value)

        return {'FINISHED'}


class BC_OT_set_float(Operator):
    bl_idname = 'bc.set_float'
    bl_label = 'Set Float'
    bl_options = {'INTERNAL'}

    data_path: StringProperty()
    value: FloatProperty()


    def execute(self, context):
        set_prop(self.data_path, self.value)

        return {'FINISHED'}


class BC_OT_set_bool(Operator):
    bl_idname = 'bc.set_bool'
    bl_label = 'Set Boolean'
    bl_options = {'INTERNAL'}

    data_path: StringProperty()
    value: BoolProperty()


    def execute(self, context):
        set_prop(self.data_path, self.value)

        return {'FINISHED'}


class BC_OT_set_enum(Operator):
    bl_idname = 'bc.set_enum'
    bl_label = 'Set Enum'
    bl_options = {'INTERNAL'}

    data_path: StringProperty()
    value: StringProperty()


    def execute(self, context):
        set_prop(self.data_path, self.value)

        return {'FINISHED'}

