import bpy
from . import icon, operator, panel, property, header, keymap, pie, toolbar, utility


def register():
    property.preference.register()
    property.register()

    operator.register()
    panel.register()
    pie.register()
    toolbar.register()

    keymap.register()

    header.add()
    toolbar.add()

    bpy.app.handlers.save_pre.append(utility.cleanup_operators)
    bpy.app.handlers.load_pre.append(utility.cleanup_operators)

    from .. utility import addon
    addon.preference().keymap.d_helper = addon.preference().keymap.d_helper


def unregister():
    utility.cleanup_operators(None)

    property.preference.unregister()
    property.unregister()

    operator.unregister()
    panel.unregister()
    pie.unregister()
    toolbar.unregister()

    keymap.unregister()

    header.remove()
    toolbar.remove()
