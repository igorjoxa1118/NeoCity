import bpy

from bpy.types import PropertyGroup
from bpy.props import BoolProperty


class option(PropertyGroup):
    removeable: BoolProperty()
    eval_remove: BoolProperty()
    inset_bevel: BoolProperty()
    q_beveled: BoolProperty()
