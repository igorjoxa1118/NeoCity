import bpy

from bpy.types import Operator
from bpy.props import BoolProperty, EnumProperty

from .... utility import addon, object
from .. utility import st3_simple_notification
from ... import toolbar
from mathutils import Matrix


def reset_shape():
    preference = addon.preference()

    preference.behavior.draw_line = False
    preference.shape.wedge = False
    preference.shape.lasso = False
    preference.shape.cyclic = True
    preference.shape.box_grid = False
    preference.shape.taper = 1.0


class BC_OT_box(Operator):
    bl_idname = 'bc.box'
    bl_label = 'Box'
    bl_description = ('Draws using box shape utilizing corner draw by default.\n\n'
                      'Hotkeys :\n\n'
                      'Alt - center draw\n'
                      'Shift - square proportion constrain\n'
                      'Shift + Alt - center box draw\n'
                      'Period during draw toggles center draw if needed')
    bl_options = {'INTERNAL'}


    def execute(self, context):
        preference = addon.preference()
        op = toolbar.option()

        reset_shape()

        op.shape_type = 'BOX'

        if preference.behavior.helper.shape_type != op.shape_type:
            preference.behavior.helper.shape_type = op.shape_type

        context.workspace.tools.update()

        return {'FINISHED'}


class BC_OT_circle(Operator):
    bl_idname = 'bc.circle'
    bl_label = 'Circle'
    bl_description = ('Draws using round plane figure whose boundary consists of points equidistant from the center.\n'
                      'Typically defaults to center draw.\n\n'
                      'Hotkeys :\n\n'
                      'Alt - free constrain\n'
                      'Alt + Shift - center contrain\n'
                      'Period during draw toggles corner / center draw if needed')
    bl_options = {'INTERNAL'}


    def execute(self, context):
        preference = addon.preference()
        op = toolbar.option()

        reset_shape()

        op.shape_type = 'CIRCLE'

        if preference.behavior.helper.shape_type != op.shape_type:
            preference.behavior.helper.shape_type = op.shape_type

        preference.shape.circle_type = 'POLYGON'

        context.workspace.tools.update()

        return {'FINISHED'}


class BC_OT_ngon(Operator):
    bl_idname = 'bc.ngon'
    bl_label = 'Ngon'
    bl_description = ('Draws using custom points determined by the user.\n'
                      'Hold Ctrl during draw to angle snap.\n'
                      'Line is also available by pressing C during draw')
    bl_options = {'INTERNAL'}


    def execute(self, context):
        preference = addon.preference()
        op = toolbar.option()

        reset_shape()

        op.shape_type = 'NGON'

        if preference.behavior.helper.shape_type != op.shape_type:
            preference.behavior.helper.shape_type = op.shape_type

        context.workspace.tools.update()

        return {'FINISHED'}


class BC_OT_custom(Operator):
    bl_idname = 'bc.custom'
    bl_label = 'Custom'
    bl_description = ('Draws utilizing custom shape.\n'
                      'Without a specified mesh the boxcutter logo will be drawn\n'
                      'Specify custom mesh using dropdown in tool options or select mesh and press C\n'
                      'Capable of utilizing itself as cutter for self.cut')
    bl_options = {'INTERNAL'}

    set: BoolProperty(default=False)

    @classmethod
    def poll(cls, context):
        return context.active_object and context.mode == 'OBJECT'

    def execute(self, context):
        bc = context.scene.bc
        op = toolbar.option()

        preference = addon.preference()

        preference.behavior.draw_line = False
        preference.shape.wedge = False

        obj = context.active_object
        assigned = False

        if not self.set:
            op.shape_type = 'CUSTOM'

        if self.set and obj and obj.type in {'MESH', 'FONT', 'CURVE'} and op.shape_type == 'CUSTOM':
            assigned = True
            bc.shape = obj
            text = F'Custom Shape: {bc.shape.name}'
            st3_simple_notification(text)
            self.report({'INFO'}, text)

        op.shape_type = 'CUSTOM'

        if preference.behavior.helper.shape_type != op.shape_type:
            preference.behavior.helper.shape_type = op.shape_type

        context.workspace.tools.update()

        if self.set and not assigned:
            return {'PASS_THROUGH'} # XXX: pass through for circle select

        return {'FINISHED'}


class BC_OT_subtype_scroll(Operator):
    bl_idname = 'bc.subtype_scroll'
    bl_label = 'Shape Type'
    bl_description = 'Scroll through shape types'
    bl_options = {'INTERNAL'}

    direction: EnumProperty(items=[('UP', 'Up', ''), ('DOWN', 'Down', '')])


    def invoke(self, context, event):
        preference = addon.preference()
        bc = context.scene.bc
        op = toolbar.option()

        if bc.running:
            return {'PASS_THROUGH'}

        draw_line = preference.behavior.draw_line
        wedge = preference.shape.wedge
        lasso = preference.shape.lasso
        cyclic = preference.shape.cyclic
        circle_type = preference.shape.circle_type

        order = [
            'CIRCLE',
            'BOX',
            'LINE BOX',
            'WEDGE',
            'CUSTOM',
            'NGON',
            'NONCYCLIC',
            'LASSO',
            'STAR',
        ]

        check = {
            'CIRCLE': op.shape_type == 'CIRCLE' and circle_type == 'POLYGON',
            'BOX': op.shape_type == 'BOX' and not draw_line and not wedge,
            'LINE BOX': op.shape_type == 'BOX' and draw_line and not wedge,
            'WEDGE': op.shape_type == 'BOX' and wedge,
            'CUSTOM': op.shape_type == 'CUSTOM',
            'NGON': op.shape_type == 'NGON' and cyclic and not lasso,
            'NONCYCLIC': op.shape_type == 'NGON' and not cyclic and not lasso,
            'LASSO': op.shape_type == 'NGON' and lasso,
            'STAR': op.shape_type == 'CIRCLE' and circle_type == 'STAR',
        }

        argument = {
            'CIRCLE': {'shape': 'CIRCLE', 'circle_type': 'POLYGON'},
            'BOX': {'shape': 'BOX'},
            'LINE BOX': {'shape': 'BOX', 'draw_line': True},
            'WEDGE': {'shape': 'BOX', 'wedge': True},
            'CUSTOM': {'shape': 'CUSTOM'},
            'NGON': {'shape': 'NGON', 'cyclic': True},
            'NONCYCLIC': {'shape': 'NGON'},
            'LASSO': {'shape': 'NGON', 'lasso': True},
            'STAR': {'shape': 'CIRCLE', 'circle_type': 'STAR'},
        }

        element_count = len(order)
        updated = False
        for index, shape in enumerate(order):
            if not check[shape]:
                continue

            updated = True
            self.update_subtype(**argument[order[index-1] if self.direction == 'DOWN' else order[index+1 if index+1 < element_count else 0]])

            break

        if not updated:
            self.update_subtype()

        return {'FINISHED'}


    def update_subtype(self, shape='BOX', draw_line=False, wedge=False, cyclic=False, lasso=False, circle_type='POLYGON'):
        preference = addon.preference()
        op = toolbar.option()
        op.shape_type = shape

        if preference.behavior.helper.shape_type != op.shape_type:
            preference.behavior.helper.shape_type = op.shape_type

        preference.behavior.draw_line = draw_line
        preference.shape.wedge = wedge
        preference.shape.cyclic = cyclic or lasso
        preference.shape.lasso = lasso
        preference.shape.circle_type = circle_type

        shape_type = shape
        if draw_line:
            shape_type = F'Line {shape_type}'
        elif wedge:
            shape_type = 'Wedge'
        elif cyclic:
            pass
        elif shape == 'NGON' and not cyclic and not lasso:
            shape_type += ' (Line)'
        elif lasso:
            shape_type = 'Lasso'
        elif shape_type == 'CIRCLE':
            shape_type = 'Circle' if circle_type != 'STAR' else 'Star'

        text = F'Shape Type: {shape_type.title()}'
        st3_simple_notification(text)
        self.report({'INFO'}, text)
