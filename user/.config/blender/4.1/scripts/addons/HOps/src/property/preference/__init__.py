import bpy

from bpy.utils import register_class, unregister_class
from bpy.types import AddonPreferences
from bpy.props import EnumProperty, PointerProperty, StringProperty, BoolProperty
import importlib

from . import behavior, display, expand, color, info, keymap, links, addons, ui, property
from . operators import operators, mirror
from .... utility import addon
from .... icons import get_icon_id
from .... import bl_info
from .... utils.blender_ui import get_dpi_factor
from .... utils.addons import addon_exists

# label row text names


class Hardops(AddonPreferences):
    bl_idname = addon.name

    settings: EnumProperty(
        name = 'Settings',
        description = 'Settings to display',
        items = [
            ('UI', 'Ui', ''),
            ('PROPERTY', 'Properties', ''),
            # ('BEHAVIOR', 'Behaviors', ''),
            ('COLOR', 'Color', ''),
            # ('DISPLAY', 'Display', ''),
            ('INFO', 'Info', ''),
            ('KEYMAP', 'Keymap', ''),
            ('LINKS', 'Links/Help', ''),
            ('ADDONS', 'Addons', '')],
        default = 'UI')

    # TODO: add update handler to gizmo toggles that calls gizmo ot

    behavior: PointerProperty(type=behavior.hardflow)
    ui: PointerProperty(type=ui.hops)
    color: PointerProperty(type=color.hops)
    display: PointerProperty(type=display.hardflow)
    expand: PointerProperty(type=expand.hardflow)
    property: PointerProperty(type=property.hops)
    keymap: PointerProperty(type=keymap.hops)
    needs_update: StringProperty()
    check_update: BoolProperty(name='Check Updates', default=True)
    wrap_text: BoolProperty(default=True)
    operator: PointerProperty(type=operators)

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.prop(self, 'check_update')
        if not self.check_update:
            pass

        elif self.needs_update:
            col = layout.column_flow()
            row = col.row()
            row.separator()
            row.alert = True
            row.label(text=self.needs_update)

            row.operator("wm.url_open", text="", icon_value=get_icon_id("bmarket")).url = "https://www.blendermarket.com/account/orders"
            row.operator("wm.url_open", text="", icon_value=get_icon_id("artstation")).url = "https://www.artstation.com/marketplace/orders"
            row.operator("wm.url_open", text="", icon_value=get_icon_id("gumroad")).url = "https://gumroad.com/library"
            row.operator("wm.url_open", text="", icon="INFO").url = "https://hardops-manual.readthedocs.io/en/latest/faq/#how-do-i-update-hard-ops-boxcutter"
        else:
            col = layout.column_flow()
            row = col.row()
            row.separator()
            row.label(text='Hardops is up-to-date')

        column = layout.column(align=True)

        row = column.row(align=True)
        row.prop(addon.preference(), 'settings', expand=True)

        box = column.box()
        globals()[addon.preference().settings.lower()].draw(addon.preference(), context, box)
        # context.area.tag_redraw()


class HOPS_OT_pref_helper(bpy.types.Operator):
    bl_idname = 'hops.pref_helper'
    bl_description = f'''Configure the preferences of {bl_info['description']}
    ***save prefs to keep across sessions***

    '''
    bl_label = '''Preferences'''
    bl_options = {'UNDO'}

    panels: dict = {}
    label: bool = False

    @classmethod
    def poll(cls, context): # need a poll for panel lookup
        return True

    def check(self, context):
        return True

    def invoke(self, context, event):
        preference = addon.preference()

        if not property.bc(): # reset toggle just incase
            preference.ui.bc_hops_toggle = 'HOPS'

        preference.wrap_text = False

        if preference.ui.use_helper_popup:
            self.label = True
            return context.window_manager.invoke_popup(self, width=int(400 * get_dpi_factor(force=False)))
        else:
            return context.window_manager.invoke_props_dialog(self, width=int(400 * get_dpi_factor(force=False)))


    def cancel(self, context):
        addon.preference().wrap_text = True
        return


    def execute(self, context):
        addon.preference().wrap_text = True
        return {'FINISHED'}


    def draw(self, context):
        preference = addon.preference()
        bc = property.bc()

        layout = self.layout

        if bc:
            row = layout.row()
            row.prop(preference.ui, 'bc_hops_toggle', expand=True)

            col = layout.column()
            col.separator()

        if preference.ui.bc_hops_toggle == 'BC':
            bc.layout = layout
            bc.draw(context)

        else:
            preference.layout = layout
            preference.draw(context)

        layout.separator()

        row = layout.row()
        row.operator_context = 'EXEC_AREA'

        row.menu('USERPREF_MT_save_load', text='', icon='COLLAPSEMENU')

        prefs = context.preferences
        if not prefs.use_preferences_save or bpy.app.use_userpref_skip_save_on_exit:
            row.operator('wm.save_userpref', text=F'Save Preferences{" *" if prefs.is_dirty else ""}'.format())


classes = (
    mirror.props,
    operators,
    keymap.hops,
    HOPS_OT_pref_helper,
    property.hops,
    behavior.hardflow,
    color.hops,
    ui.hops,
    display.hardflow,
    expand.hardflow,
    Hardops)


def init_recent_sort_char():
    from .... utility import modifier
    from . import property

    def _init_recent_sort_char():
        if not bpy.context:
            return 0.1

        preference = addon.preference()

        for option in dir(preference.property):
            if not option.endswith('_char'):
                continue

            property.recent_sort_char[option] = getattr(preference.property, option)
            flag = option.replace('sort_', '').replace('_char', '')
            if flag == 'char':
                flag = 'sort'

            if flag == 'lock_above':
                flag = 'lock_below'

            elif flag == 'lock_below':
                flag = 'lock_above'

            flag += '_flag'
            setattr(modifier, flag, getattr(preference.property, option))

        return

    bpy.app.timers.register(_init_recent_sort_char, first_interval=0.1)


def register():
    init_recent_sort_char()
    for cls in classes:
        register_class(cls)
    ui.update_hops_panels(None,None)


def unregister():
    for cls in classes:
        unregister_class(cls)
