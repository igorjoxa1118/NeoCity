import bpy

from bl_ui.space_toolsystem_toolbar import VIEW3D_PT_tools_active as tools
from bl_ui.space_toolsystem_common import activate_by_id as activate_by_id

name = __name__.partition('.')[0]


def active():
    active_tool = None

    if bpy.context.space_data:
        active_tool = tools.tool_active_from_context(bpy.context)

    return active_tool if active_tool else type('fake_tool', (), {'idname': 'NONE', 'mode': 'OBJECT', 'operator_properties': lambda *_: None})


def option(name, operator_id):
    if not active():
        return None

    for tooldef in bpy.context.workspace.tools:
        if not tooldef:
            continue

        if tooldef.idname == name and tooldef.mode == active().mode:
            return tooldef.operator_properties(operator_id)

    return None


activate = lambda: activate_by_id(bpy.context, 'VIEW_3D', name)
