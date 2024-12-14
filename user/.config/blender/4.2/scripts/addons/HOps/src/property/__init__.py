import bpy

from bpy.utils import register_class, unregister_class
from bpy.types import PropertyGroup, Object, Collection
from bpy.props import *

from . import preference, data, last, object, dots, helper
from ... utility import addon, modifier
from ... utility.geomerty_nodes import SmoothByAngle

auto_smooth_override = False


def translate(string):
    return ' '.join([bpy.app.translations.pgettext_data(n) for n in string.split(' ')])


def use_auto_smooth(mesh, context):
    import bmesh

    objects = [o for o in context.visible_objects if o.data == mesh]

    for obj in objects:
        auto_smooth_mods = list(filter(SmoothByAngle.is_valid_modifier, obj.modifiers))

        if mesh.use_auto_smooth and not auto_smooth_mods:
            mod = SmoothByAngle.from_object(obj)
            mod.name = F'{modifier.sort_last_flag*2}{mod.name}'
            mod.angle = obj.data.auto_smooth_angle

        elif not mesh.use_auto_smooth:
            for mod in auto_smooth_mods:
                obj.modifiers.remove(obj)

            if obj.mode == 'EDIT':
                bm = bmesh.from_edit_mesh(obj.data)

                for edge in bm.edges:
                    edge.smooth = False

                bmesh.update_edit_mesh(obj.data, False, False)

            else:
                for edge in obj.data.edges:
                    edge.use_edge_sharp = False


def auto_smooth_angle(mesh, context):
    objects = [o for o in context.visible_objects if o.data == mesh]

    for obj in objects:
        auto_smooth_mods = list(filter(SmoothByAngle.is_valid_modifier, obj.modifiers))

        if not auto_smooth_mods: continue

        mod = SmoothByAngle.new(auto_smooth_mods[-1])
        mod.angle = mesh.auto_smooth_angle


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
