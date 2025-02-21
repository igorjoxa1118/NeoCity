import bpy
import math
from ... icons import get_icon_id
from ... utils.addons import addon_exists
from ... utility import addon


class HOPS_MT_ObjectsOperatorsSubmenu(bpy.types.Menu):
    """
    Operations for various mesh utilities and functions in Object Mode

    """
    bl_label = 'Objects Operators Submenu'
    bl_idname = 'HOPS_MT_ObjectsOperatorsSubmenu'

    def draw(self, context):
        layout = self.layout
        object = context.active_object
        is_boolean = len([mod for mod in bpy.context.active_object.modifiers if mod.type == 'BOOLEAN'])
        is_array = len([mod for mod in bpy.context.active_object.modifiers if mod.type == 'ARRAY'])

        layout.operator_context = 'INVOKE_DEFAULT'

        row = layout.column().row()
        row.operator_context = 'INVOKE_DEFAULT'

        if addon.preference().ui.expanded_menu:
                column = row.column()
        else:
            column =self.layout

        #op = column.operator("hops.modifier_scroll", text="Modifier sssScroll", icon_value=get_icon_id("Tris"))
        # op.all=True
        # op.additive=True
        op = column.operator("hops.ever_scroll_v2", text="Modifier Scroll", icon_value=get_icon_id("StatusReset"))
        op.entry_state='MOD'
        op.dot_open=False

        column.operator_context = 'INVOKE_DEFAULT'
        column.operator("hops.bevel_assist", text="Bevel / Edge Manager", icon_value=get_icon_id("CSharpen"))
        column.separator()

        column.operator("hops.sharpen", text="Sharpen", icon_value=get_icon_id("CSharpen"))
        column.operator("hops.step", text="Step", icon_value=get_icon_id("Sstep"))
        column.separator()
        column.operator("hops.complex_sharpen", text="(C) Sharpen", icon_value=get_icon_id("CSharpen"))
        column.separator()

        column.operator("hops.clean_sharps", text="Clear Sharps", icon_value=get_icon_id("CleansharpsE"))
        column.separator()

        # column.label(text='')
        column.operator("view3d.clean_mesh", text="Clean Mesh", icon_value=get_icon_id("FaceGrate"))
        column.operator("hops.apply_modifiers", text="Smart Apply", icon_value=get_icon_id("Applyall")) #.modifier_types='BOOLEAN'
        column.separator()
        column.operator("hops.draw_uv_edit_mode", text="UV Display", icon="UV_DATA")

        separate = False
        if is_boolean:
            separate = True
            if separate:
                column.separator()
            column.operator("hops.late_parent", text="Late Parent", icon_value=get_icon_id("Tris"))

        if is_boolean or is_array:
            column.operator("hops.uniquify_cutters", text="Uniquify ", icon_value=get_icon_id("grey"))

        # if context.active_object.hops.status == 'BOOLSHAPE':
        #     separate = True
        #     if separate:
        #         column.separator()
        #     column.operator("hops.late_paren_t", text="Late Parent", icon_value=get_icon_id("Tris"))

        if addon.preference().ui.expanded_menu:
                column = row.column()
        else:
            column.separator()

        if addon.preference().property.to_shape_type == 'CLASSIC':
            column.operator("hops.to_shape", text="To_Shape", icon_value=get_icon_id("Display_boolshapes"))
        elif addon.preference().property.to_shape_type == 'CLASSIC+':
            column.operator("hops.to_shape_1_5", text="To_Shape v1.5", icon_value=get_icon_id("Display_boolshapes"))
        else:
            column.operator("hops.to_shape_v2", text="To_Shape V2", icon_value=get_icon_id("Frame"))

        if addon.preference().property.accushape_type == 'V2':
            column.operator("hops.accu_shape_v2", text="AccuShape V2", icon_value=get_icon_id("grey"))
        else:
            column.operator("hops.accu_shape", text="AccuShape", icon_value=get_icon_id("grey"))

        #column.operator("hops.edge2curve", text="Curve/Extract", icon_value=get_icon_id("Curve"))
        column.separator()

        column.operator("hops.camera_rig", text="Add Camera", icon='OUTLINER_OB_CAMERA')
        column.operator("hops.blank_light", text="Add Lights", icon='LIGHT')
        column.separator()


        column.operator("hops.mirror_gizmo", text="Mirror", icon_value=get_icon_id("Mirror"))
        column.separator()
        column.operator("hops.poly_debug_display", text="Polygon Debug", icon_value=get_icon_id("sm_logo_white"))
        column.separator()

        column.menu("HOPS_MT_ModSubmenu", text="Add Modifier", icon_value=get_icon_id("Diagonal"))
        if addon_exists("MESHmachine"):
            # column.separator()
            column.menu("MACHIN3_MT_mesh_machine", text="MESHmachine", icon_value=get_icon_id("Machine"))
            column.separator()

        column.operator_context = "INVOKE_DEFAULT"
        column.operator("view3d.sculpt_ops_window", text="(Q) Brush" if addon.preference().property.add_prefix else "Brush ", icon="BRUSH_DATA")
        #column.operator("hops.sculpt_primitives", text="Add Primitive", icon_value=get_icon_id("QGui"))
        #column.separator()


class HOPS_MT_MeshOperatorsSubmenu(bpy.types.Menu):
    """
    Operations for various mesh utilities and functions in Edit Mode

    """
    bl_label = 'Mesh Operators Submenu'
    bl_idname = 'HOPS_MT_MeshOperatorsSubmenu'

    def draw(self, context):
        layout = self.layout

        layout.operator_context = 'INVOKE_DEFAULT'

        layout.menu("HOPS_MT_ModSubmenu", text = 'Add Modifier',  icon_value=get_icon_id("Tris"))
        layout.separator()
        layout.operator("hops.draw_uv_edit_mode", text="UV Display", icon="UV_DATA")
        layout.operator("hops.poly_debug_display", text="Polygon Debug", icon_value=get_icon_id("sm_logo_white"))
        layout.separator()
        layout.operator("hops.cursor_snap", text="Snap Cursor", icon="CURSOR")
        layout.separator()
        layout.operator("hops.meshdisp", text="Display Marks", icon="PLUGIN")
        layout.operator("hops.bevel_weight", text="Adjust Bevel Weight", icon_value=get_icon_id("AdjustBevel"))
        layout.operator("hops.clean1_objects", text="Demote", icon_value=get_icon_id("Demote")).clearsharps = False
        layout.separator()
        layout.operator("hops.mirror_gizmo", text="Mirror", icon_value=get_icon_id("Mirror"))
        #layout.separator()
        #layout.operator("hops.set_edit_sharpen", text="Set SSharp", icon_value=get_icon_id("MakeSharpE"))
        #layout.separator()
        #layout.operator("hops.clean1_objects", text="Clean SSharps", icon_value=get_icon_id("CleansharpsE"))

        layout.separator()

        #layout.operator_context = 'EXEC_DEFAULT'
        op = layout.operator("mesh.spin", text = 'Spin')
        op.steps = 6
        op.angle = 6.28319
        #if event.ctrl:
        #    op.axis =( 0, 1, 0)
        #else:
        #    pass
        #layout.operator("hops.edge2curve", text="Curve/Extract", icon_value=get_icon_id("Curve"))
        if addon.preference().property.accushape_type == 'V2':
            layout.operator("hops.accu_shape_v2", text="AccuShape V2", icon_value=get_icon_id("grey"))
        else:
            layout.operator("hops.accu_shape", text="AccuShape", icon_value=get_icon_id("grey"))

        if addon.preference().property.to_shape_type == 'CLASSIC':
            layout.operator("hops.to_shape", text="To_Shape", icon_value=get_icon_id("Display_boolshapes"))
        elif addon.preference().property.to_shape_type == 'CLASSIC+':
            layout.operator("hops.to_shape_1_5", text="To_Shape v1.5", icon_value=get_icon_id("Display_boolshapes"))
        else:
            layout.operator("hops.to_shape_v2", text="To_Shape V2", icon_value=get_icon_id("Frame"))

        layout.separator()
        layout.operator("hops.floor", text="To_floor", icon_value=get_icon_id("grey"))
        layout.separator()

        layout.operator("hops.to_rope", text="To Rope", icon="STROKE")
        layout.operator("hops.to_thread", text="To Thread", icon_value=get_icon_id("ToThread"))
        layout.separator()
        layout.operator("hops.edge_len", text="Edge Length", icon="NONE")
        #layout.operator("hops.to_plane", text="To_Plane", icon_value=get_icon_id("Booleans"))
        layout.separator()
        layout.menu("HOPS_MT_EditClassicsSubmenu", text = 'Meshtools',  icon_value=get_icon_id("Tris"))
        #layout.operator("view3d.vertcircle", text="Circle", icon_value=get_icon_id("NthCircle"))
        #layout.operator("hops.to_shape", text="To_Shape", icon_value=get_icon_id("Display_boolshapes"))
        #layout.operator("hops.reset_axis_modal", text="Reset Axis / Flatten", icon_value=get_icon_id("Xslap"))
        #layout.operator("view3d.vertcircle", text="Circle (Nth)(E)", icon_value=get_icon_id("NthCircle")).nth_mode = True
        #layout.operator("hops.circle", text="NEW Circle", icon_value=get_icon_id("NthCircle"))
        #layout.separator()
        layout.separator()

        layout.operator("hops.star_connect", text="Star Connect", icon_value=get_icon_id("Machine"))
        # if any("mira_tools" in s for s in bpy.context.preferences.addons.keys()):
        #     layout.separator()
        #     layout.menu("HOPS_MT_MiraSubmenu", text="Mira (T)", icon="PLUGIN")
        # else:
        #     layout.separator()

        if addon_exists("MESHmachine"):
            layout.separator()
            layout.menu("MACHIN3_MT_mesh_machine", text="MESHmachine", icon_value=get_icon_id("Machine"))

        if len(bpy.context.selected_objects) == 2:
            layout.separator()
            layout.operator("object.to_selection", text="Obj To Selection", icon_value=get_icon_id("dots"))
            layout.separator()

        layout.menu("HOPS_MT_PluginSubmenu", text="Plugin", icon="PLUGIN")
        layout.separator()
        #layout.operator("hops.reset_axis", text="Reset Axis / Flatten", icon_value=get_icon_id("Xslap"))

        #layout.menu("HOPS_MT_BoolSumbenu", text="Booleans", icon="MOD_BOOLEAN")
        layout.operator("view3d.clean_mesh", text="Clean Mesh", icon_value=get_icon_id("CleansharpsE"))
        #layout.separator()

class HOPS_MT_MergeOperatorsSubmenu(bpy.types.Menu):
    """
    Operations for merging insert meshes.

    """
    bl_label = 'Merge Operators Submenu'
    bl_idname = 'HOPS_MT_MergeOperatorsSubmenu'

    def draw(self, context):
        layout = self.layout

        layout.operator_context = "INVOKE_DEFAULT"
        layout.operator("hops.parent_merge", text="(C) merge")#, icon_value=get_icon_id("Merge"))
        layout.operator("hops.parent_merge_soft", text="(C) merge(soft)", icon_value=get_icon_id("CSharpen"))
        layout.operator("hops.simple_parent_merge", text="(S) merge")#, icon_value=get_icon_id("Merge"))
        layout.operator("hops.remove_merge", text="Remove Merge")#, icon_value=get_icon_id("Merge"))

class HOPS_MT_EditClassicsSubmenu(bpy.types.Menu):
    """
    Operations Edit Mesh Operators Submenu

    """
    bl_label = 'Edit Mesh Operators Submenu'
    bl_idname = 'HOPS_MT_EditClassicsSubmenu'

    def draw(self, context):
        layout = self.layout

        layout.operator("hops.fgrate_op", text="Grate (Face)", icon_value=get_icon_id("FaceGrate"))
        layout.operator("hops.fknurl_op", text="Knurl (Face)", icon_value=get_icon_id("FaceKnurl"))
        layout.separator()

        layout.operator("hops.quick_panel", text="Panel (Edge)", icon_value=get_icon_id("EdgeRingPanel"))
        layout.operator("hops.entrench_selection", text="Panel (Face)", icon_value=get_icon_id("FacePanel"))
        layout.separator()

        layout.operator("view3d.view_align", text= "Align View", icon_value=get_icon_id("HardOps"))

class HOPS_MT_BoolScrollOperatorsSubmenu(bpy.types.Menu):
    """
    Operations for bool scroll stuff

    """
    bl_label = 'Bool Scroll Operators Submenu'
    bl_idname = 'HOPS_MT_BoolScrollOperatorsSubmenu'

    def draw(self, context):
        layout = self.layout

        layout.operator("hops.scroll_multi", text="Bool/Mod Scroll/Toggle", icon_value=get_icon_id("QuickFav"))

        layout.separator()

        op = layout.operator("hops.modifier_scroll", text="Modifier Scroll", icon_value=get_icon_id("Diagonal"))
        op.additive = True
        op.all = True

        layout.operator_context = "INVOKE_DEFAULT"
        layout.operator("hops.bool_scroll_objects", text="Object Scroll", icon_value=get_icon_id("StatusReset"))

        op = layout.operator("hops.modifier_scroll", text="Cycle Booleans", icon_value=get_icon_id("StatusOveride"))
        op.additive = False
        op.type = 'BOOLEAN'

        op = layout.operator("hops.modifier_scroll", text="Additive Scroll", icon_value=get_icon_id("Diagonal"))
        op.additive = True
        op.type = 'BOOLEAN'

        layout.separator()

        layout.operator("hops.ever_scroll_v2", text="Ever Scroll", icon_value=get_icon_id("QGui"))

        layout.separator()

        layout.operator("view3d.view_align", text= "Align View", icon_value=get_icon_id("HardOps"))

        layout.separator()

        layout.operator("hops.bool_toggle_viewport", text= "Toggle Modifiers", icon_value=get_icon_id("Tris")).all_modifiers = False


class HOPS_MT_EditModePie(bpy.types.Menu):
    """
    Menu to Pie Edit mode operations

    """

    bl_label = 'Edit options Submenu'
    bl_idname = 'HOPS_MT_EditModePie'

    def draw(self, context):
        layout = self.layout

        layout.operator_context = 'INVOKE_DEFAULT'
        layout.operator("hops.edit_multi_tool", text="(s) Mark", icon_value=get_icon_id("MakeSharpE"))
        #layout.operator("hops.set_edit_sharpen", text="Set SSharp", icon_value=get_icon_id("MakeSharpE"))
        #layout.operator("hops.bevel_weight", text="Bweight", icon_value=get_icon_id("AdjustBevel"))
        #layout.menu("HOPS_MT_ModSubmenu", text = 'Add Modifier',  icon_value=get_icon_id("Tris"))
        #layout.operator("hops.array_gizmo", text="Array", icon_value=get_icon_id("Array"))
        layout.separator()
        #layout.operator("hops.clean1_objects", text="Demote", icon_value=get_icon_id("Demote")).clearsharps = False
        layout.menu("HOPS_MT_ModSubmenu", text = 'Add Modifier',  icon_value=get_icon_id("Tris"))
        layout.separator()
        layout.operator("hops.edge2curve", text="Curve/Extract", icon_value=get_icon_id("Curve"))
        layout.operator("view3d.vertcircle", text="Circle" if addon_exists("mesh_looptools") else "Circle (E)", icon_value=get_icon_id("NthCircle"))
        layout.operator("hops.bool_dice_v2", text="Dice V2", icon_value=get_icon_id("Dice"))
        if addon.preference().property.to_shape_type == 'CLASSIC':
            layout.operator("hops.to_shape", text="To_Shape", icon_value=get_icon_id("Display_boolshapes"))
        elif addon.preference().property.to_shape_type == 'CLASSIC+':
            layout.operator("hops.to_shape_1_5", text="To_Shape v1.5", icon_value=get_icon_id("Display_boolshapes"))
        else:
            layout.operator("hops.to_shape_v2", text="To_Shape V2", icon_value=get_icon_id("Frame"))
        layout.separator()

        #if addon.preference().property.st3_meshtools:
        layout.operator("hops.edit_mesh_macro", text="EM_Macro", icon_value=get_icon_id("FaceGrate"))
        layout.menu("HOPS_MT_ST3MeshToolsSubmenu", text="ST3 Mesh Tools", icon="MESH_ICOSPHERE")
        layout.separator()

        layout.menu("HOPS_MT_MeshOperatorsSubmenu", text="Operations", icon_value=get_icon_id("StatusOveride"))

        layout.operator("hops.flatten_align", text="Flatten/Align/Select", icon_value=get_icon_id("Xslap"))
        layout.menu("HOPS_MT_BoolSumbenu", text="Booleans", icon_value=get_icon_id("Booleans"))
        if addon_exists('bezier_mesh_shaper') or addon_exists('MESHmachine') or addon_exists('mira_tools'):
            layout.menu("HOPS_MT_PluginSubmenu", text="Plugin", icon="PLUGIN")
        layout.separator()

        """if object.data.show_edge_crease == False:
            layout.operator("object.showoverlays", text="Show Overlays", icon = "RESTRICT_VIEW_ON")
        else :
            layout.operator("object.hide_overlays", text="Hide Overlays", icon = "RESTRICT_VIEW_OFF")"""

        if bpy.context.object and bpy.context.object.type == 'MESH':
            layout.menu("HOPS_MT_MaterialListMenu", text="Material", icon_value=get_icon_id("StatusOveride"))
