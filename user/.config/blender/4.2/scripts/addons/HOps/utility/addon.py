import os
import bpy

name = __name__.partition('.')[0]

icons = {}


class path:

    def __new__(self):
        return os.path.abspath(os.path.join(__file__, '..', '..', '..'))

    def icons():
        return os.path.join(path(), 'icons')


def preference():
    preference = bpy.context.preferences.addons[name].preferences

    return preference


def hops():
    wm = bpy.context.window_manager

    if hasattr(wm, 'Hard_Ops_folder_name'):
        return bpy.context.preferences.addons[wm.Hard_Ops_folder_name].preferences

    return False


def bc():
    wm = bpy.context.window_manager

    if hasattr(wm, 'bc'):
        return bpy.context.preferences.addons[wm.bc.addon].preferences

    return False


def kitops():
    wm = bpy.context.window_manager

    if hasattr(wm, 'kitops'):
        return bpy.context.preferences.addons[wm.kitops.addon].preferences

    return False


def powersave():
    wm = bpy.context.window_manager

    if hasattr(wm, 'powersave'):
        return bpy.context.preferences.addons[wm.powersave.addon].preferences

    return False


def powerlink():
    wm = bpy.context.window_manager

    if hasattr(wm, 'powerlink'):
        return bpy.context.preferences.addons[wm.powerlink.addon].preferences

    return False


def log(value='', indent=1):
    if preference().debug:
        if value:
            print(F'{"|  "*indent}{value}')
