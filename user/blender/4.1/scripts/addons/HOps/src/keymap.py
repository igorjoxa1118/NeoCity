import bpy

from .. utils.addons import addon_exists

keys = []


def register():
    # global keys

    wm = bpy.context.window_manager
    active_keyconfig = wm.keyconfigs.active
    addon_keyconfig = wm.keyconfigs.addon
    kc = addon_keyconfig
    if not kc:
        print('HardOps: keyconfig unavailable (in batch mode?), no keybinding items registered')
        return

    bpy.utils.register_class(HOPS_TILDEREMAP)

    # register to object tab
    km = kc.keymaps.new(name="Object Mode")

    kmi = km.keymap_items.new("wm.call_menu", "G", "PRESS", shift=True)
    kmi.properties.name = "HOPS_MT_SelectGrouped"
    keys.append((km, kmi))

    # register to 3d view mode tab
    km = kc.keymaps.new(name="3D View", space_type="VIEW_3D")

    kmi = km.keymap_items.new("wm.call_menu_pie", "Q", "PRESS", shift=True)
    kmi.properties.name = "HOPS_MT_MainPie"
    keys.append((km, kmi))

    kmi = km.keymap_items.new("wm.call_menu", "Q", "PRESS")
    kmi.properties.name = "HOPS_MT_MainMenu"
    keys.append((km, kmi))

    kmi = km.keymap_items.new("hops.pref_helper", "K", "PRESS", ctrl=True)
    keys.append((km, kmi))

    kmi = km.keymap_items.new("hops.helper", "ACCENT_GRAVE", "PRESS", ctrl=True)
    # kmi = km.keymap_items.new("wm.call_panel", "ACCENT_GRAVE", "PRESS", ctrl=True)
    # kmi.properties.name = "HOPS_PT_Button"
    # kmi.properties.keep_open = True
    keys.append((km, kmi))

    kmi = km.keymap_items.new("wm.call_menu", "M", "PRESS", alt=True)
    kmi.properties.name = "HOPS_MT_MaterialListMenu"
    keys.append((km, kmi))

    kmi = km.keymap_items.new("wm.call_menu", "V", "PRESS", alt=True)
    kmi.properties.name = "HOPS_MT_ViewportSubmenu"
    keys.append((km, kmi))

    kmi = km.keymap_items.new("hops.mirror_gizmo", 'X', 'PRESS', alt=True)
    keys.append((km, kmi))
    kmi = km.keymap_items.new("hops.bev_multi", 'B', 'PRESS', ctrl=True, shift=True)
    keys.append((km, kmi))
    kmi = km.keymap_items.new("hops.bevel_helper", 'B', 'PRESS', alt=True, shift=True)
    keys.append((km, kmi))
    #tilde remapper
    kmi = km.keymap_items.new(idname ='hops.tilde_remap', type='ACCENT_GRAVE', value='PRESS')
    kmi.active = False
    keys.append((km, kmi))

    kmi = km.keymap_items.new("hops.adjust_logo", 'L', 'PRESS', ctrl=True, shift=True, alt=True)
    keys.append((km, kmi))

    km = kc.keymaps.new(name='Object Mode', space_type='EMPTY')

    kmi = km.keymap_items.new("hops.bool_union_hotkey", 'NUMPAD_PLUS', 'PRESS', ctrl=True, shift=False)
    keys.append((km, kmi))
    kmi = km.keymap_items.new("hops.bool_difference_hotkey", 'NUMPAD_MINUS', 'PRESS', ctrl=True, shift=False)
    keys.append((km, kmi))
    kmi = km.keymap_items.new("hops.bool_intersect_hotkey", 'NUMPAD_ASTERIX', 'PRESS', ctrl=True, shift=False)
    keys.append((km, kmi))
    kmi = km.keymap_items.new("hops.slash_hotkey", 'NUMPAD_SLASH', 'PRESS', ctrl=True, shift=False)
    keys.append((km, kmi))
    kmi = km.keymap_items.new("hops.bool_inset", 'NUMPAD_SLASH', 'PRESS', ctrl=False, shift=True, alt=True)
    keys.append((km, kmi))

    km = kc.keymaps.new(name='Mesh', space_type='EMPTY')

    kmi = km.keymap_items.new("hops.edit_bool_union", 'NUMPAD_PLUS', 'PRESS', ctrl=True, shift=False, alt=True)
    keys.append((km, kmi))
    kmi = km.keymap_items.new("hops.edit_bool_difference", 'NUMPAD_MINUS', 'PRESS', ctrl=True, shift=False, alt=True)

    keys.append((km, kmi))

    if addon_exists('mira_tools'):
        kmi = km.keymap_items.new("mesh.curve_stretch", 'ACCENT_GRAVE', 'PRESS', ctrl=True, alt=False, shift=True)
        keys.append((km, kmi))

    km = kc.keymaps.new(name="Pose", space_type="EMPTY", region_type="WINDOW")

    kmi = km.keymap_items.new("hops.helper", "ACCENT_GRAVE", "PRESS", ctrl=True)
    keys.append((km, kmi))

    km = kc.keymaps.new(name="Armature", space_type="EMPTY", region_type="WINDOW")

    kmi = km.keymap_items.new("hops.helper", "ACCENT_GRAVE", "PRESS", ctrl=True)
    keys.append((km, kmi))

    # Geo Nodes
    km = kc.keymaps.new(name='Node Editor', space_type='NODE_EDITOR', region_type='WINDOW')

    kmi = km.keymap_items.new("wm.call_menu", "Q", "PRESS")
    kmi.properties.name = "HOPS_MT_NodesMenu"
    keys.append((km, kmi))


    # Activate tool
    km = kc.keymaps.new(name='3D View', space_type='VIEW_3D')

    kmi = km.keymap_items.new(idname='hardflow.topbar_activate', type='W', value='PRESS', alt=True, shift=True)
    keys.append((km, kmi))


def unregister():
    # global keys

    for km, kmi in keys:
        km.keymap_items.remove(kmi)

    keys.clear()
    bpy.utils.unregister_class(HOPS_TILDEREMAP)
   

class HOPS_TILDEREMAP(bpy.types.Operator):
    bl_idname = "hops.tilde_remap"
    bl_label = "Hops Tilde Remap"
    bl_options = {'INTERNAL'}


