import bpy

from .. utility import addon

keys = []

def register():
    global keys

    wm = bpy.context.window_manager
    active_keyconfig = wm.keyconfigs.active
    addon_keyconfig = wm.keyconfigs.addon

    kc = addon_keyconfig
    if not kc:
        print('BoxCutter: keyconfig unavailable (in batch mode?), no keybinding items registered')
        return

    # Activate tool
    km = kc.keymaps.new(name='3D View', space_type='VIEW_3D')

    kmi = km.keymap_items.new(idname='bc.tool_activate', type='W', value='PRESS', alt=True)
    keys.append((km, kmi))


def unregister():
    global keys

    for km, kmi in keys:
        km.keymap_items.remove(kmi)

    keys.clear()
