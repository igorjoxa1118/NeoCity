import bpy
from .. icons import get_icon_id
from .. utils.addons import addon_exists
from .. utils.objects import get_current_selected_status
from .. utility import addon
from .. import bl_info


class HOPS_MT_NodesMenu(bpy.types.Menu):
    bl_idname = "HOPS_MT_NodesMenu"
    bl_label = f"HOps: {bl_info['version'][0]}.{bl_info['version'][1]}.{bl_info['version'][2]}.{bl_info['version'][3]}"

    def draw(self, context):
        layout = self.layout

        if context.area.ui_type == 'GeometryNodeTree':
            geo_nodes_menu(context, layout)

        elif context.area.ui_type == 'ShaderNodeTree':
            shader_nodes_menu(context, layout)

        layout.separator()
        layout.menu("SCREEN_MT_user_menu", text="Quick Favorites", icon_value=get_icon_id("QuickFav"))


def geo_nodes_menu(context, layout):
    layout.operator_context = "INVOKE_DEFAULT"
    layout.operator("hops.cycle_geo_nodes", text="W Cycle Node", icon_value=get_icon_id("Array"))
    layout.menu("NODE_MT_add", text="Add")
    layout.separator()
    # layout.operator("hops.cycle_node_groups", text="Cycle Groups", icon_value=get_icon_id("green"))
    # layout.separator()
    layout.operator("hops.all_geo_nodes", text="All Nodes", icon="MOD_ARRAY")


def shader_nodes_menu(context, layout):
    layout.operator_context = "INVOKE_DEFAULT"
    layout.operator("hops.cycle_geo_nodes", text="W Cycle Node", icon_value=get_icon_id("Array"))
    layout.menu("NODE_MT_add", text="Add")
    layout.separator()
    # layout.operator("hops.cycle_node_groups", text="Cycle Groups", icon_value=get_icon_id("green"))
    # layout.separator()
    layout.operator("hops.all_geo_nodes", text="All Nodes", icon="MOD_ARRAY")