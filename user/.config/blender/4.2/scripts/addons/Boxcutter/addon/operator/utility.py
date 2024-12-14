import bpy

from importlib import import_module

from ... utility import addon


def st3_simple_notification(text):
    if addon.hops() and addon.hops().display.bc_notifications:
        HOps = import_module(bpy.context.window_manager.Hard_Ops_folder_name)
        HOps.src.operator.bc_notifications.new_notification(text)
