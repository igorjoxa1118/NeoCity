import bpy

from bpy.types import PropertyGroup
from bpy.props import BoolProperty


class bc(PropertyGroup):

    shape: BoolProperty(
        name = 'Expand Shape',
        default = False)

    display: BoolProperty(
        name = 'Expand Display',
        default = False)

    input: BoolProperty(
        name = 'Expand Input',
        default = False)

    behavior: BoolProperty(
        name = 'Expand Behavior',
        default = False)

    behavior_modifier: BoolProperty(
        name = 'Expand Behavior Modifier',
        default = False)

    behavior_shape: BoolProperty(
        name = 'Expand Behavior Shape',
        default = False)

    color_mode: BoolProperty(
        name = 'Expand Color Mode',
        default = False)

    color_shape: BoolProperty(
        name = 'Expand Color Shape',
        default = False)

    color_widget: BoolProperty(
        name = 'Expand Color Widget',
        default = False)

    display_shape: BoolProperty(
        name = 'Expand Display Shape',
        default = False)

    display_widget: BoolProperty(
        name = 'Expand Display Widget',
        default = False)

    display_tool_interface: BoolProperty(
        name = 'Expand Display Tool Interface',
        default = False)

    display_tool_interface_decorations: BoolProperty(
        name = 'Expand Display Tool Interface Decorations',
        default = False)

    shape_transforms: BoolProperty(
        name = 'Expand Shape Transforms',
        default = False)

    shape_geometry: BoolProperty(
        name = 'Expand Shape Geometry',
        default = False)

    # input_bindings: BoolProperty(
    #     name = 'Expand Input Bindings',
    #     default = False)

    input_behavior: BoolProperty(
        name = 'Expand Input Behavior',
        default = False)

    input_behavior_mouse: BoolProperty(
        name = 'Expand Input Behavior Mouse',
        default = False)

    input_behavior_keyboard: BoolProperty(
        name = 'Expand Input Behavior Keyboard',
        default = False)

    hops: BoolProperty(
        name = 'Expand HardOps',
        default = False)

    collection: BoolProperty(
        name = 'Expand Collection',
        default = False)
