import bpy

from bpy.utils import register_class, unregister_class
from bpy.types import AddonPreferences
from bpy.props import *

from . import behavior, color, display, expand, keymap, shape, snap

from .... utility import addon
from ... property.utility import names


class bc(AddonPreferences):
    bl_idname = addon.name

    debug: BoolProperty(
        name = 'Debug',
        description = 'Allow errors to print that would otherwise be hidden through management',
        default = True)

    settings: EnumProperty(
        name = 'Settings',
        description = 'Settings to display',
        items = [
            ('BEHAVIOR', 'Behavior', ''),
            ('COLOR', 'Color', ''),
            ('DISPLAY', 'Display', ''),
            ('SHAPE', 'Shape', ''),
            ('KEYMAP', 'Input', '')],
        default = 'BEHAVIOR')

    # TODO: add update handler to gizmo toggles that calls gizmo ot
    grid_gizmo: BoolProperty(
        name = names['grid_gizmo'],
        description = 'Show grid gizmo',
        default = False)

    cursor: BoolProperty(
        name = names['cursor'],
        description = 'Show cursor gizmo',
        default = False)

    transform_gizmo: BoolProperty(
        name = names['transform_gizmo'],
        description = 'Show transform gizmo',
        default = False)

    axis: EnumProperty(
        name = 'Axis',
        description = 'Axis to be used',
        items = [
            ('X', 'X', ''),
            ('Y', 'Y', ''),
            ('Z', 'Z', '')],
        default = 'Z')

    surface: EnumProperty(
        name = 'Surface',
        description = 'Draw Surface',
        items = [
            ('OBJECT', 'Object', '\n Align Shape to Surface\n\n'
                                ' Object orients the drawing to the surface on draw\n'
                                ' BC will calculate the orientation based on surface geo.\n'
                                ' Typically the default', 'OBJECT_DATA', 0),
            ('VIEW', 'View', '\n Align shape to View\n\n'
                             ' View orients the drawing off the surface to the view on draw\n'
                             ' BC will calculate the orientation based on the viewport.\n'
                             ' Sets knife to work via knife project. Supporting (edge-only) 2d custom shapes.\n'
                             ' Typically used for cut projection', 'LOCKVIEW_ON', 1),
            ('CURSOR', 'Cursor', '\n Align Shape to 3d Cursor\n\n'
                                ' Cursor orients the drawing to the 3d cursor on draw\n'
                                ' Grid Gizmo being enabled shows grid.\n'
                                ' Cursor best aligns on Z axis.\n\n'
                                ' Gizmo may be disabled leaving only grid', 'PIVOT_CURSOR', 2),
            ('WORLD', 'World', '\n Align Shape to World Axis\n\n'
                                '\n Draws shape in 0,0,0 of the world\n'
                                '\n World is the final fallback utilizing the world for orientation\n'
                                '\n Typically used with make box for creation', 'WORLD', 3)],
        default = 'OBJECT')

    behavior: PointerProperty(type=behavior.bc)
    color: PointerProperty(type=color.bc)
    display: PointerProperty(type=display.bc)
    keymap: PointerProperty(type=keymap.bc)
    expand: PointerProperty(type=expand.bc)
    shape: PointerProperty(type=shape.bc)
    snap: PointerProperty(type=snap.bc)


    def draw(self, context):
        layout = self.layout

        column = layout.column(align=True)
        row = column.row(align=True)
        row.prop(self, 'settings', expand=True)

        box = column.box()
        globals()[self.settings.lower()].draw(self, context, box)

        column.separator()

        row = column.row(align=True)
        row.alignment = 'RIGHT'

        sub = row.row()
        sub.alignment = 'RIGHT'
        sub.active = self.debug
        sub.prop(self, 'debug', text='Debug', toggle=True, emboss=False)

        row.prop(self, 'debug', text='')
        row.separator()


classes = (
    behavior.helper_expand,
    behavior.bc_helper,
    behavior.bc,
    color.bc,
    display.bc,
    keymap.shift_operations,
    keymap.bc,
    expand.bc,
    shape.bc,
    snap.bc,
    bc)


def init_recent_sort_char():
    from .... utility import modifier
    from . utility import update

    def _init_recent_sort_char():
        if not bpy.context:
            return 0.1

        preference = addon.preference()

        for option in dir(preference.behavior):
            if not option.endswith('_char'):
                continue

            update.recent_sort_char[option] = getattr(preference.behavior, option)
            flag = option.replace('sort_', '').replace('_char', '')
            if flag == 'char':
                flag = 'sort'

            if flag == 'lock_above':
                flag = 'lock_below'

            elif flag == 'lock_below':
                flag = 'lock_above'

            flag += '_flag'
            setattr(modifier, flag, getattr(preference.behavior, option))

        return

    bpy.app.timers.register(_init_recent_sort_char, first_interval=0.1)


def register():
    init_recent_sort_char()

    for cls in classes:
        register_class(cls)


def unregister():
    for cls in classes:
        unregister_class(cls)
