import bpy
from .. utility import addon
from ..utils.blender_ui import get_dpi_factor

def mod_list_template(layout, object):
    layout.template_list("HOPS_UL_Modlist", "", object, "modifiers", object.hops, "active_modifier_index", sort_reverse = False)


class HOPS_OT_ModVis(bpy.types.Operator):
    """Realtime
    Display modifier in viewport"""
    bl_idname = "hops.ui_mod_vis_toggle"
    bl_label = "Simple Object Operator"

    index: bpy.props.IntProperty()

    def execute(self, context):
        ob = context.object
        mod = ob.modifiers[self.index]
        mod.show_viewport = not mod.show_viewport
        return {'FINISHED'}

class HOPS_OT_ModRenderVis(bpy.types.Operator):
    """Render
    Use modifier during render"""
    bl_idname = "hops.ui_mod_rendervis_toggle"
    bl_label = "Toggle render visibility"

    index: bpy.props.IntProperty()

    def execute(self, context):
        ob = context.object
        mod = ob.modifiers[self.index]
        mod.show_render = not mod.show_render
        return {'FINISHED'}

class HOPS_OT_ModRemove(bpy.types.Operator):
    """Remove'
    Remove Modifier"""
    bl_idname = "hops.ui_mod_test_remove"
    bl_label = "Remove modifier"

    index: bpy.props.IntProperty()

    def execute(self, context):
        ob = context.object
        mod = ob.modifiers[self.index]
        ob.modifiers.remove(mod)
        return {'FINISHED'}


class HOPS_UL_Modlist(bpy.types.UIList):
    """UIlist for modifier stack"""
    use_name: bpy.props.BoolProperty(name='Name filter', description='Filter by name instead of type')
    allow_removal: False

    def __init__(self):
        self.use_filter_show = True # always show filter. popovers really don't like ui lists

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index=0):
        mod = item
        if self.layout_type in {'DEFAULT', 'COMPACT'}:

            if item:
                row = layout.row(align=True)
                row.alignment = 'LEFT'
                row.label(text=str(index + 1))

                row= row.row(align=True)
                row.prop(mod, "name", text="", emboss=False,)
                row.label(text=mod.type)

                row = row.row(align=True)
                row.alignment = 'RIGHT'
                props = row.operator("hops.ui_mod_vis_toggle", icon='RESTRICT_VIEW_OFF' if mod.show_viewport else 'RESTRICT_VIEW_ON', text = '')
                props.index = index
                # props = row.operator("hops.ui_mod_rendervis_toggle", icon='RESTRICT_RENDER_OFF' if mod.show_render else 'RESTRICT_RENDER_ON', text = '')
                # props.index = index

                if self.allow_removal:
                    props = row.operator("hops.ui_mod_test_remove", icon='X', text = '')
                    props.index = index
            else:
                layout.label(text="", translate=False, icon_value=icon)

        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)

    def draw_filter(self, context, layout):
        layout = layout.row()
        layout.prop(self, 'filter_name', text='')
        layout.prop(self, 'use_filter_invert', text='', icon='ARROW_LEFTRIGHT')
        layout.prop(self, 'use_name', icon='SYNTAX_OFF', text='')

    def filter_items(self, context, data, propname):
        flags = []
        order = []

        name_type = 'name' if self.use_name else 'type'
        flags = bpy.types.UI_UL_list.filter_items_by_name(self.filter_name, self.bitflag_filter_item, data.modifiers, name_type, reverse=False)

        return flags, order


class HOPS_OT_ModListPopover(bpy.types.Operator):
    bl_label = "Mod List"
    bl_idname = "hops.modlist_popover"

    allow_removal: bpy.props.BoolProperty()
    object_name: bpy.props.StringProperty()
    _object = bpy.props.PointerProperty(type=bpy.types.Object)

    def draw(self, context):
        layout = self.layout

        mod_list_template(layout, self._object)

    def execute(self, context):
        HOPS_UL_Modlist.allow_removal = self.allow_removal
        preference = addon.preference().ui
        self._object = bpy.data.objects[self.object_name] if self.object_name else context.active_object
        self.object_name = ''
        self.allow_removal = False
        return bpy.context.window_manager.invoke_popup(self, width=int(preference.Hops_helper_width * get_dpi_factor(force=False) * 0.6))