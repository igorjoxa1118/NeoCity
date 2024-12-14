import bpy
import textwrap


from bpy.types import PropertyGroup, Panel
from bpy.props import BoolProperty, IntProperty, EnumProperty
from .... import bl_info
from .... utility import addon
from .... utils.blender_ui import get_dpi_factor

import rna_keymap_ui


def get_hotkey_entry_item(km, kmi_name, kmi_value, properties):
    for i, km_item in enumerate(km.keymap_items):
        if km.keymap_items.keys()[i] == kmi_name:
            if properties == 'name':
                if km.keymap_items[i].properties.name == kmi_value:
                    return km_item
            elif properties == 'tab':
                if km.keymap_items[i].properties.tab == kmi_value:
                    return km_item
            elif properties == 'none':
                return km_item
    return None

sharp_modes = [
    ("SSHARP", "Ssharp", ""),
    ("CSHARP", "Csharp", ""),
    ("RESHARP", "Resharp", ""),
    ("CSHARPBEVEL", "CsharpBevel", ""),
    ("SSHARPWN", "Weighted Mod", ""),
    ("AUTOSMOOVE", "Autosmooth", ""),
    ("CLEANSHARP", "Cleansharp", ""),
    ("SMART_APPLY", "Smart Apply", "")]


class hops(PropertyGroup):

    # Modal Controls
    spacebar_accept: BoolProperty(name="Spacebar Accept", default=False, description=f'Disabling allows spacebar to use menu in-tool in addition to tab on select modals.\n ie: Bevel, Boolshift, To_Shape 1.5')

    rmb_cancel: BoolProperty(name="RMB Cancel", default=True, description=f'Use right mouse button to cancel an operator')

    # Sharps
    sharp: EnumProperty(
        name="Sharp Modes",
        default='SSHARP',
        items=sharp_modes)

    sharp_alt: EnumProperty(
        name="Sharp Modes",
        default='SSHARPWN',
        items=sharp_modes)

    sharp_ctrl: EnumProperty(
        name="Sharp Modes",
        default='CSHARP',
        items=sharp_modes)

    sharp_shift: EnumProperty(
        name="Sharp Modes",
        default='AUTOSMOOVE',
        items=sharp_modes)

    sharp_alt_ctrl: EnumProperty(
        name="Sharp Modes",
        default='SSHARP',
        items=sharp_modes)

    sharp_shift_ctrl: EnumProperty(
        name="Sharp Modes",
        default='RESHARP',
        items=sharp_modes)

    sharp_alt_shift: EnumProperty(
        name="Sharp Modes",
        default='SSHARP',
        items=sharp_modes)

    # Menu drop downs
    expand_modals: BoolProperty(name="Show Modal Operators hotkeys", default=False)
    expand_sharpen: BoolProperty(name="Show sharpen options", default=False)
    show_main_pie: BoolProperty(name="Show main pie", default=False)
    show_main_menu: BoolProperty(name="Show main menu", default=False)
    show_menu_sys: BoolProperty(name="Show menu systems", default=False)
    show_booleans: BoolProperty(name="Show booleans", default=False)
    show_operators: BoolProperty(name="Show operators", default=False)
    show_edit_mode: BoolProperty(name="Show edit mode", default=False)
    show_third_party: BoolProperty(name="Show third party", default=False)
    show_extended: BoolProperty(name="Show extended", default=False)


def header_row(row, prop, label='', emboss=False):
    preference = addon.preference()
    icon = 'DISCLOSURE_TRI_RIGHT' if not getattr(preference.keymap, prop) else 'DISCLOSURE_TRI_DOWN'
    row.alignment = 'LEFT'
    row.prop(preference.keymap, prop, text='', emboss=emboss)

    sub = row.row(align=True)
    sub.scale_x = 0.25
    sub.prop(preference.keymap, prop, text='', icon=icon, emboss=emboss)
    row.prop(preference.keymap, prop, text=F'{label}', emboss=emboss)

    sub = row.row(align=True)
    sub.scale_x = 0.75
    sub.prop(preference.keymap, prop, text=' ', icon='BLANK1', emboss=emboss)


class HOPS_PT_Keys_info(Panel):
    bl_label = 'Keys info'
    bl_space_type = 'VIEW_3D'
    bl_category = 'HardOps'
    bl_region_type = 'UI'

    def draw(self, context):
        layout = self.layout
        preference = addon.preference()

        layout.label(text=f'''{bl_info['description']}''')

        if addon.preference().needs_update:# and not 'Connection Failed':
            text = "Needs Update"
            layout.label(text=f'''{bl_info['version'][0]}.{bl_info['version'][1]}.{bl_info['version'][2]}.{bl_info['version'][3]} : {text}''', icon='ERROR')
        elif addon.preference().needs_update == 'Connection Failed':
            text = "Unknown"
            layout.label(text=f'''{bl_info['version'][0]}.{bl_info['version'][1]}.{bl_info['version'][2]}.{bl_info['version'][3]} : {text}''', icon='ERROR')
        else:
            text = "Current"
            layout.label(text=f'''{bl_info['version'][0]}.{bl_info['version'][1]}.{bl_info['version'][2]}.{bl_info['version'][3]} : {text}''', icon='FUND')

        row = layout.row(align=True)

        layout.label(text='Menus')

        row = layout.row(align=True)
        layout.label(text='Main Menu', icon='EVENT_Q')

        row.label(text='', icon='EVENT_SHIFT')
        row.label(text='Pie Menu', icon='EVENT_Q')

        row = layout.row(align=True)
        row.label(text='', icon='EVENT_CTRL')
        row.label(text='`  Hops Helper')

        row = layout.row(align=True)
        row.label(text='', icon='EVENT_CTRL')
        row.label(text='Preference / Keymap Helper', icon='EVENT_K')

        # row = layout.row(align=True)
        # row.label(text='', icon='EVENT_CTRL')
        # row.label(text='Multi assist', icon='EVENT_O')

        row = layout.row(align=True)
        row.label(text='', icon='EVENT_ALT')
        row.label(text='Material List', icon='EVENT_M')

        row = layout.row(align=True)
        row.label(text='', icon='EVENT_ALT')
        row.label(text='Viewport Submenu', icon='EVENT_V')

        layout.separator()
        layout.label(text='Boolean Multi Tool')
        row = layout.row(align=True)
        row.label(text='', icon='EVENT_CTRL')
        row.label(text='', icon='EVENT_SHIFT')
        row.label(text='Bevel/Bool Multi Tool', icon='EVENT_B')

        layout.separator()

        layout.label(text='Operators')
        row = layout.row(align=True)
        row.label(text='', icon='EVENT_ALT')
        row.label(text='Interactive Mirror', icon='EVENT_X')
        layout.separator()

        layout.label(text='Booleans')
        row = layout.row(align=True)
        row.label(text='', icon='EVENT_CTRL')
        row.label(text='Union', icon='ADD')

        row = layout.row(align=True)
        row.label(text='', icon='EVENT_CTRL')
        row.label(text='Difference', icon='REMOVE')

        row = layout.row(align=True)
        row.label(text='', icon='EVENT_CTRL')
        row.label(text='Slash', icon='IPO_LINEAR')

        row = layout.row(align=True)
        row.label(text='', icon='EVENT_CTRL')
        row.label(text='Intersect', icon='SORTBYEXT')

        row = layout.row(align=True)
        row.label(text='', icon='EVENT_ALT')
        row.label(text='', icon='EVENT_SHIFT')
        row.label(text='Inset', icon='IPO_LINEAR')
        layout.separator()

        layout.label(text='Edit Mode')
        row = layout.row(align=True)
        row.label(text='', icon='EVENT_CTRL')
        row.label(text='', icon='EVENT_ALT')
        row.label(text='Union', icon='ADD')

        row = layout.row(align=True)
        row.label(text='', icon='EVENT_CTRL')
        row.label(text='', icon='EVENT_ALT')
        row.label(text='Difference', icon='REMOVE')

        if addon_exists('mira_tools'):
            layout.separator()
            layout.label(text='3rd Party')
            row = layout.row(align=True)
            row.label(text='', icon='EVENT_CTRL')
            row.label(text='', icon='EVENT_SHIFT')
            row.label(text='`  Mira Curve Stretch Helper')

        layout.separator()
        layout.label(text='Others')
        row = layout.row(align=True)
        row.label(text='', icon='EVENT_CTRL')
        row.label(text='', icon='EVENT_ALT')
        row.label(text='', icon='EVENT_SHIFT')
        row.label(text='', icon='EVENT_L')
        row.label(text='Logo Adjust', icon='REMOVE')

        layout.separator()


class HOPS_PT_Keys(Panel):
    bl_label = 'Keys Options'
    bl_space_type = 'VIEW_3D'
    bl_category = 'HardOps'
    bl_region_type = 'UI'

    def draw(self, context, layout):
        preference = addon.preference()
        draw(preference, context, layout)


def draw(preference, context, layout):

    box = layout.box()
    split = box.split()
    col = split.column()

    col.label(text='Do not remove hotkeys, disable them instead.')

    # Modal Controls
    sub_box = col.box()
    header_row(sub_box.row(align=True), 'expand_modals', label='Modal Operators')
    if preference.keymap.expand_modals:
        sub_box = sub_box.box()
        sub_box.label(text='Modal Operators')
        sub_box.separator()
        sub_box.prop(preference.keymap, "spacebar_accept", text="Spacebar Accept")
        sub_box.prop(preference.keymap, "rmb_cancel")

    # Sharpen
    sub_box = col.box()
    header_row(sub_box.row(align=True), 'expand_sharpen', label='Sharpen')
    if preference.keymap.expand_sharpen:
        sub_box = sub_box.box()
        sub_box.label(text='Sharpen Activation')
        sub_box.separator()
        sub_box.prop(preference.keymap, "sharp", text="Main")
        sub_box.prop(preference.keymap, "sharp_alt", text="Alt")
        sub_box.prop(preference.keymap, "sharp_ctrl", text="Ctrl")
        sub_box.prop(preference.keymap, "sharp_shift", text="Shift")
        sub_box.prop(preference.keymap, "sharp_alt_shift", text="Alt + Shift")
        sub_box.prop(preference.keymap, "sharp_alt_ctrl", text="Alt + Ctrl")
        sub_box.prop(preference.keymap, "sharp_shift_ctrl", text="Ctrl + Shift")
        sub_box.separator()
        sub_box.separator()

    wm = bpy.context.window_manager
    kc = wm.keyconfigs.user

    # Main Pie
    sub_box = col.box()
    header_row(sub_box.row(align=True), 'show_main_pie', label='Main Pie')
    if preference.keymap.show_main_pie:
        sub_box = sub_box.box()

        km = kc.keymaps['3D View']
        kmi = get_hotkey_entry_item(km, 'wm.call_menu_pie', 'HOPS_MT_MainPie', 'name')
        if kmi:
            sub_box.context_pointer_set("keymap", km)
            rna_keymap_ui.draw_kmi([], kc, km, kmi, sub_box, 0)
        else:
            sub_box.label(text="No hotkey entry found")
            sub_box.label(text="restore hotkeys from interface tab")

    # Main Menu
    sub_box = col.box()
    header_row(sub_box.row(align=True), 'show_main_menu', label='Main Menu')
    if preference.keymap.show_main_menu:
        sub_box = sub_box.box()

        km = kc.keymaps['3D View']
        kmi = get_hotkey_entry_item(km, 'wm.call_menu', 'HOPS_MT_MainMenu', 'name')
        if kmi:
            sub_box.context_pointer_set("keymap", km)
            rna_keymap_ui.draw_kmi([], kc, km, kmi, sub_box, 0)
        else:
            sub_box.label(text="No hotkey entry found")
            sub_box.label(text="restore hotkeys from interface tab")

    # Menus & Systems
    sub_box = col.box()
    header_row(sub_box.row(align=True), 'show_menu_sys', label='Menus & Systems')
    if preference.keymap.show_menu_sys:
        sub_box = sub_box.box()

        km = kc.keymaps['3D View']
        kmi = get_hotkey_entry_item(km, 'hops.helper', 'none', 'none')
        if kmi:
            sub_box.context_pointer_set("keymap", km)
            rna_keymap_ui.draw_kmi([], kc, km, kmi, sub_box, 0)
        else:
            sub_box.label(text="No hotkey entry found")
            sub_box.label(text="restore hotkeys from interface tab")

        sub_box.separator()
        km = kc.keymaps['3D View']
        kmi = get_hotkey_entry_item(km, 'hops.pref_helper', 'none', 'none')
        if kmi:
            sub_box.context_pointer_set("keymap", km)
            rna_keymap_ui.draw_kmi([], kc, km, kmi, sub_box, 0)
        else:
            sub_box.label(text="No hotkey entry found")
            sub_box.label(text="restore hotkeys from interface tab")

        sub_box.separator()
        km = kc.keymaps['3D View']
        kmi = get_hotkey_entry_item(km, 'wm.call_menu', 'HOPS_MT_MaterialListMenu', 'name')
        if kmi:
            sub_box.context_pointer_set("keymap", km)
            rna_keymap_ui.draw_kmi([], kc, km, kmi, sub_box, 0)
        else:
            sub_box.label(text="No hotkey entry found")
            sub_box.label(text="restore hotkeys from interface tab")

        sub_box.separator()
        km = kc.keymaps['3D View']
        kmi = get_hotkey_entry_item(km, 'wm.call_menu', 'HOPS_MT_ViewportSubmenu', 'name')
        if kmi:
            sub_box.context_pointer_set("keymap", km)
            rna_keymap_ui.draw_kmi([], kc, km, kmi, sub_box, 0)
        else:
            sub_box.label(text="No hotkey entry found")
            sub_box.label(text="restore hotkeys from interface tab")

    # Booleans
    sub_box = col.box()
    header_row(sub_box.row(align=True), 'show_booleans', label='Booleans')
    if preference.keymap.show_booleans:
        sub_box = sub_box.box()

        km = kc.keymaps['Object Mode']
        kmi = get_hotkey_entry_item(km, 'hops.bool_union_hotkey', 'none', 'none')
        if kmi:
            sub_box.context_pointer_set("keymap", km)
            rna_keymap_ui.draw_kmi([], kc, km, kmi, sub_box, 0)
        else:
            sub_box.label(text="No hotkey entry found")
            sub_box.label(text="restore hotkeys from interface tab")

        sub_box.separator()
        km = kc.keymaps['Object Mode']
        kmi = get_hotkey_entry_item(km, 'hops.bool_difference_hotkey', 'none', 'none')
        if kmi:
            sub_box.context_pointer_set("keymap", km)
            rna_keymap_ui.draw_kmi([], kc, km, kmi, sub_box, 0)
        else:
            sub_box.label(text="No hotkey entry found")
            sub_box.label(text="restore hotkeys from interface tab")

        sub_box.separator()
        km = kc.keymaps['Object Mode']
        kmi = get_hotkey_entry_item(km, 'hops.bool_intersect_hotkey', 'none', 'none')
        if kmi:
            sub_box.context_pointer_set("keymap", km)
            rna_keymap_ui.draw_kmi([], kc, km, kmi, sub_box, 0)
        else:
            sub_box.label(text="No hotkey entry found")
            sub_box.label(text="restore hotkeys from interface tab")

        sub_box.separator()
        km = kc.keymaps['Object Mode']
        kmi = get_hotkey_entry_item(km, 'hops.slash_hotkey', 'none', 'none')
        if kmi:
            sub_box.context_pointer_set("keymap", km)
            rna_keymap_ui.draw_kmi([], kc, km, kmi, sub_box, 0)
        else:
            sub_box.label(text="No hotkey entry found")
            sub_box.label(text="restore hotkeys from interface tab")

        sub_box.separator()
        km = kc.keymaps['Object Mode']
        kmi = get_hotkey_entry_item(km, 'hops.bool_inset', 'none', 'none')
        if kmi:
            sub_box.context_pointer_set("keymap", km)
            rna_keymap_ui.draw_kmi([], kc, km, kmi, sub_box, 0)
        else:
            sub_box.label(text="No hotkey entry found")
            sub_box.label(text="restore hotkeys from interface tab")

    # Operators
    sub_box = col.box()
    header_row(sub_box.row(align=True), 'show_operators', label='Operators')
    if preference.keymap.show_operators:
        sub_box = sub_box.box()

        km = kc.keymaps['3D View']
        kmi = get_hotkey_entry_item(km, 'hops.mirror_gizmo', 'none', 'none')
        if kmi:
            sub_box.context_pointer_set("keymap", km)
            rna_keymap_ui.draw_kmi([], kc, km, kmi, sub_box, 0)
        else:
            sub_box.label(text="No hotkey entry found")
            sub_box.label(text="restore hotkeys from interface tab")

        sub_box.separator()
        km = kc.keymaps['3D View']
        kmi = get_hotkey_entry_item(km, 'hops.bev_multi', 'none', 'none')
        if kmi:
            sub_box.context_pointer_set("keymap", km)
            rna_keymap_ui.draw_kmi([], kc, km, kmi, sub_box, 0)
        else:
            sub_box.label(text="No hotkey entry found")
            sub_box.label(text="restore hotkeys from interface tab")

    # Edit Mode
    sub_box = col.box()
    header_row(sub_box.row(align=True), 'show_edit_mode', label='Edit Mode')
    if preference.keymap.show_edit_mode:
        sub_box = sub_box.box()

        km = kc.keymaps['Mesh']
        kmi = get_hotkey_entry_item(km, 'hops.edit_bool_union', 'none', 'none')
        if kmi:
            sub_box.context_pointer_set("keymap", km)
            rna_keymap_ui.draw_kmi([], kc, km, kmi, sub_box, 0)
        else:
            sub_box.label(text="No hotkey entry found")
            sub_box.label(text="restore hotkeys from interface tab")

        sub_box.separator()
        km = kc.keymaps['Mesh']
        kmi = get_hotkey_entry_item(km, 'hops.edit_bool_difference', 'none', 'none')
        if kmi:
            sub_box.context_pointer_set("keymap", km)
            rna_keymap_ui.draw_kmi([], kc, km, kmi, sub_box, 0)
        else:
            sub_box.label(text="No hotkey entry found")
            sub_box.label(text="restore hotkeys from interface tab")

    # 3rd Part
    sub_box = col.box()
    header_row(sub_box.row(align=True), 'show_third_party', label='3rd Party')
    if preference.keymap.show_third_party:
        sub_box = sub_box.box()

        if addon_exists('mira_tools'):
            sub_box = sub_box.box()
            sub_box.label(text="Mira")
            km = kc.keymaps['Mesh']
            kmi = get_hotkey_entry_item(km, 'mesh.curve_stretch', 'none', 'none')
            if kmi:
                sub_box.context_pointer_set("keymap", km)
                rna_keymap_ui.draw_kmi([], kc, km, kmi, sub_box, 0)
            else:
                sub_box.label(text="No hotkey entry found")
                sub_box.label(text="restore hotkeys from interface tab")
        else:
            sub_box.label(text="nothing to see here")

    # Extended
    sub_box = col.box()
    header_row(sub_box.row(align=True), 'show_extended', label='Extended')
    if preference.keymap.show_extended:
        sub_box = sub_box.box()

        km = kc.keymaps['3D View']
        kmi = get_hotkey_entry_item(km, 'hops.tilde_remap', 'none', 'none')
        if kmi:
            sub_box.context_pointer_set("keymap", km)
            rna_keymap_ui.draw_kmi([], kc, km, kmi, sub_box, 0)
        else:
            sub_box.label(text="No hotkey entry found")
            sub_box.label(text="restore hotkeys from interface tab")


def addon_exists(name):
    for addon_name in bpy.context.preferences.addons.keys():
        if name in addon_name: return True
    return False
