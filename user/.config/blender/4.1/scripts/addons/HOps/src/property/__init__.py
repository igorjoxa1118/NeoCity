import bpy

from bpy.utils import register_class, unregister_class
from bpy.types import PropertyGroup, Object, Collection
from bpy.props import *

from . import preference, data, last, object, dots, helper
from ... utility import addon, modifier

auto_smooth_override = False


def translate(string):
    return ' '.join([bpy.app.translations.pgettext_data(n) for n in string.split(' ')])


def use_auto_smooth(mesh, context):
    import bpy
    import bmesh
    from math import radians

    objects = [o for o in context.visible_objects if o.data == mesh]

    for obj in objects:
        obj.auto_smooth_modifier = ''

        for mod in reversed(obj.modifiers):
            if mod.type != 'NODES':
                continue

            if modifier.hashed_graph(mod) != 'Auto Smooth':
                continue

            if not mod.name.startswith(F'{modifier.sort_last_flag*2}'):
                mod.name = F'{modifier.sort_last_flag*2}{mod.name}'

            obj.auto_smooth_modifier = mod.name
            # mesh.auto_smooth_angle = mod[mod.node_group.interface.items_tree[2].identifier]

            break

    for obj in objects:
        name = obj.auto_smooth_modifier

        if mesh.use_auto_smooth and not name or name not in obj.modifiers:
            if not name:
                name = F'{modifier.sort_last_flag*2}Auto Smooth'

            mod = obj.modifiers.new(name, 'NODES')
            mod.name = name
            mod.show_group_selector = False

            if translate('Auto Smooth') not in bpy.data.node_groups:
                new = bpy.data.node_groups.new(translate('Auto Smooth'), 'GeometryNodeTree')

                socket = new.interface.new_socket('Mesh', in_out='OUTPUT', socket_type='NodeSocketGeometry')

                socket = new.interface.new_socket('Mesh', in_out='INPUT', socket_type='NodeSocketGeometry')

                socket = new.interface.new_socket('Angle', in_out='INPUT', socket_type='NodeSocketFloat')
                socket.subtype = 'ANGLE'
                socket.min_value = radians(0)
                socket.max_value = radians(180)

                socket = new.interface.new_socket('Ignore Sharpness', in_out='INPUT', socket_type='NodeSocketBool')
                socket.force_non_field = True

                input1 = new.nodes.new('NodeGroupInput')
                input1.location = (-440, -460)
                input1.select = False

                input1.outputs[0].hide = True
                input1.outputs[1].hide = True
                input1.outputs[-1].hide = True

                smooth = new.nodes.new('GeometryNodeInputShadeSmooth')
                smooth.location = (-440, -396)
                smooth.select = False

                input2 = new.nodes.new('NodeGroupInput')
                input2.location = (-440, -330)
                input2.select = False

                input2.outputs[0].hide = True
                input2.outputs[2].hide = True
                input2.outputs[-1].hide = True

                angle = new.nodes.new('GeometryNodeInputMeshEdgeAngle')
                angle.location = (-440, -240)
                angle.select = False

                or1 = new.nodes.new('FunctionNodeBooleanMath')
                or1.location = (-260, -380)
                or1.select = False
                or1.operation = 'OR'
                or1.show_options = False

                new.links.new(input1.outputs[2], or1.inputs[1])
                new.links.new(smooth.outputs[0], or1.inputs[0])

                compare = new.nodes.new('FunctionNodeCompare')
                compare.location = (-260, -260)
                compare.select = False
                compare.data_type = 'FLOAT'
                compare.operation = 'LESS_EQUAL'
                compare.show_options = False

                new.links.new(input2.outputs[1], compare.inputs[1])
                new.links.new(angle.outputs[0], compare.inputs[0])

                input3 = new.nodes.new('NodeGroupInput')
                input3.location = (-260, -188)
                input3.select = False

                input3.outputs[0].hide = True
                input3.outputs[1].hide = True
                input3.outputs[-1].hide = True

                edge_smooth = new.nodes.new('GeometryNodeInputEdgeSmooth')
                edge_smooth.location = (-260, -120)
                edge_smooth.select = False

                and1 = new.nodes.new('FunctionNodeBooleanMath')
                and1.location = (-80, -260)
                and1.select = False
                and1.operation = 'AND'
                and1.show_options = False

                new.links.new(or1.outputs[0], and1.inputs[1])
                new.links.new(compare.outputs[0], and1.inputs[0])

                or2 = new.nodes.new('FunctionNodeBooleanMath')
                or2.location = (-80, -150)
                or2.select = False
                or2.operation = 'OR'
                or2.show_options = False

                new.links.new(input3.outputs[2], or2.inputs[1])
                new.links.new(edge_smooth.outputs[0], or2.inputs[0])

                input4 = new.nodes.new('NodeGroupInput')
                input4.location = (-80, -80)
                input4.select = False

                input4.outputs[1].hide = True
                input4.outputs[2].hide = True
                input4.outputs[-1].hide = True

                set_smooth1 = new.nodes.new('GeometryNodeSetShadeSmooth')
                set_smooth1.location = (120, -80)
                set_smooth1.select = False
                set_smooth1.domain = 'EDGE'

                new.links.new(and1.outputs[0], set_smooth1.inputs[2])
                new.links.new(or2.outputs[0], set_smooth1.inputs[1])
                new.links.new(input4.outputs[0], set_smooth1.inputs[0])

                set_smooth2 = new.nodes.new('GeometryNodeSetShadeSmooth')
                set_smooth2.location = (300, -80)
                set_smooth2.select = False
                set_smooth2.domain = 'FACE'

                new.links.new(set_smooth1.outputs[0], set_smooth2.inputs[0])

                output = new.nodes.new('NodeGroupOutput')
                output.location = (480, -80)
                output.select = False

                new.links.new(set_smooth2.outputs[0], output.inputs[0])

            mod.node_group = bpy.data.node_groups[translate('Auto Smooth')]
            mod[mod.node_group.interface.items_tree[2].identifier] = mesh.auto_smooth_angle

            obj.auto_smooth_modifier = mod.name

        elif not mesh.use_auto_smooth and name in obj.modifiers:
            obj.modifiers.remove(obj.modifiers[name])

            if obj.mode == 'EDIT':
                bm = bmesh.from_edit_mesh(obj.data)

                for edge in bm.edges:
                    edge.smooth = False

                bmesh.update_edit_mesh(obj.data, False, False)

            else:
                for edge in obj.data.edges:
                    edge.use_edge_sharp = False

            obj.auto_smooth_modifier = ''


def auto_smooth_angle(mesh, context):
    objects = [o for o in context.visible_objects if o.data == mesh]

    for obj in objects:
        if not obj.auto_smooth_modifier in obj.modifiers:
            continue

        mod = obj.modifiers[obj.auto_smooth_modifier]
        mod[mod.node_group.interface.items_tree[2].identifier] = mesh.auto_smooth_angle


class option(PropertyGroup):
    running: BoolProperty()
    dots: PointerProperty(type=dots.option)
    helper: PointerProperty(type=helper.option)


classes = [
    dots.Points,
    dots.option,
    helper.option,
    option]


def register():
    global auto_smooth_override

    for cls in classes:
        register_class(cls)

    bpy.types.WindowManager.hardflow = PointerProperty(type=option)

    if addon.bc():
        bc = __import__(bpy.context.window_manager.bc.addon)

        if hasattr(bc.addon.property, 'auto_smooth_override'):
            auto_smooth_override = bc.addon.property.auto_smooth_override

    if not 'use_auto_smooth' in bpy.types.Mesh.bl_rna.properties:
        from math import radians

        auto_smooth_override = True

        bpy.types.Object.auto_smooth_modifier = StringProperty()
        bpy.types.Mesh.use_auto_smooth = BoolProperty(update=use_auto_smooth)
        bpy.types.Mesh.auto_smooth_angle = FloatProperty(update=auto_smooth_angle, subtype='ANGLE', default=radians(30))

    preference.register()


def unregister():
    global auto_smooth_override

    for cls in classes:
        unregister_class(cls)

    del bpy.types.WindowManager.hardflow

    if auto_smooth_override and not addon.bc():
        del bpy.types.Object.auto_smooth_modifier
        del bpy.types.Mesh.use_auto_smooth
        del bpy.types.Mesh.auto_smooth_angle

        auto_smooth_override = False

    preference.unregister()
