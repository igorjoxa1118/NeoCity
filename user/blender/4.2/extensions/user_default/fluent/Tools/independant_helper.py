import os.path
import re

import bpy
import math
from .constants import fluent_modifiers_name


def get_addon_preferences():
    addon_key = __package__.split('.fluent')[0]+'.fluent'
    addon_prefs = bpy.context.preferences.addons[addon_key].preferences

    return addon_prefs


def get_version_from_manifest():
    content = open(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'blender_manifest.toml')).read()
    pattern = r'^version\s*=\s*"(\d+\.\d+\.\d+)"'
    match = re.search(pattern, content, re.MULTILINE)

    # Extract and print the version number if a match is found
    if match:
        return match.group(1)
    else:
        print("No version number found.")
        return 'x.x.x'


def active_object(action = 'GET', obj = None, solo = False):
    if solo:
        for ob in bpy.data.objects:
            ob.select_set(False)
    if action == 'SET':
        if obj != None:
            obj.hide_set(False)
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
        return obj
    elif action == 'GET':
        return bpy.context.active_object


def auto_bevel_segments(bevel=None, displace=None, revolver_obj=None, pre_bevel=None, obj=None):
    longueur = 1
    min_segments = 0
    if bevel or pre_bevel:
        if bevel:
            if bevel.name == fluent_modifiers_name['second_bevel_top']:
                rayon = obj.modifiers[fluent_modifiers_name['pre_second_bevel_top']]['Input_4']
            elif bevel.name == fluent_modifiers_name['second_bevel_bottom']:
                rayon = obj.modifiers[fluent_modifiers_name['pre_second_bevel_bottom']]['Input_4']
            else:
                rayon = bevel.width
        if pre_bevel:
            rayon = pre_bevel['Input_4']
        longueur = math.pi*rayon/2

        if bpy.context.scene.fluentProp.min_auto_bevel_segments != 0:
            min_segments = bpy.context.scene.fluentProp.min_auto_bevel_segments
    if displace:
        rayon = displace.strength
        longueur = 2*math.pi*rayon

        if bpy.context.scene.fluentProp.min_auto_cylinder_segments != 0:
            min_segments = bpy.context.scene.fluentProp.min_auto_cylinder_segments
    if revolver_obj:
        rayon = 0
        for v in revolver_obj.data.vertices:
            if math.fabs(v.co.x) > rayon:
                rayon = math.fabs(v.co.x)
        longueur = 2 * math.pi * rayon

        if bpy.context.scene.fluentProp.min_auto_cylinder_segments != 0:
            min_segments = bpy.context.scene.fluentProp.min_auto_cylinder_segments

    segments = longueur*bpy.context.scene.fluentProp.model_resolution
    if segments < min_segments:
        segments = min_segments

    return math.ceil(segments)


def use_auto_smooth(data, value=True):
    if bpy.app.version < (4, 1, 0):
        data.use_auto_smooth = value

