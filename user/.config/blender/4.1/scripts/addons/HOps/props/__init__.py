from . import types
from . import modifiers

import bpy
from bpy.props import PointerProperty
from bpy.types import PropertyGroup


class HOpsSceneProeprties(PropertyGroup):
    collection: PointerProperty(type=bpy.types.Collection)
    modifiers: PointerProperty(type=modifiers.HOpsModifiers)
    timer_running: bpy.props.BoolProperty(default=False)


classes = (
    types.HOpsObjectProperties,
    types.HOpsMeshProperties,
    types.HOpsNodeProperties,
    types.HOpsImgProperties,
    modifiers.HOpsModifiers,
    HOpsSceneProeprties
)


def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    bpy.types.Object.hops = PointerProperty(name="HardOps Properties", type=types.HOpsObjectProperties)
    bpy.types.Mesh.hops = PointerProperty(name="HardOps Mesh Props", type=types.HOpsMeshProperties)
    bpy.types.Node.hops = PointerProperty(name="HardOps Node Props", type=types.HOpsNodeProperties)
    bpy.types.Image.hops = PointerProperty(name="HardOps Node Props", type=types.HOpsImgProperties)
    bpy.types.Scene.hops = PointerProperty(name="HardOps Scene Props", type=HOpsSceneProeprties)


def unregister():
    from bpy.utils import unregister_class
    for cls in classes:
        unregister_class(cls)

    del bpy.types.Object.hops
    del bpy.types.Mesh.hops
    del bpy.types.Node.hops
    del bpy.types.Image.hops
    del bpy.types.Scene.hops
