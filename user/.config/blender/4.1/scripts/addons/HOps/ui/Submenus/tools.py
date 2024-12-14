import bpy
from ... icons import get_icon_id
from ... utils.addons import addon_exists
from ... utility import addon


class HOPS_MT_ObjectToolsSubmenu(bpy.types.Menu):
    bl_label = 'Objects Tools Submenu'
    bl_idname = 'HOPS_MT_ObjectToolsSubmenu'

    def draw(self, context):
        layout = self.layout

        row = layout.column().row()

        if addon.preference().ui.expanded_menu:
            column = row.column()
        else:
            column =self.layout

        column.operator("hops.flatten_align", text="Reset Axis/Align/Select", icon_value=get_icon_id("Xslap"))
        column.operator("hops.set_origin", text="Set Origin", icon_value=get_icon_id("CircleSetup"))
        column.operator("hops.floor_object", text="To Floor", icon_value=get_icon_id("grey"))
        column.separator()

        column.operator("hops.bool_dice_v2", text="Dice V2", icon_value=get_icon_id("Dice"))
        column.operator("hops.array_twist", text="Twist 360", icon_value=get_icon_id("ATwist360"))
        if addon.preference().property.radial_array_type == 'CLASSIC':
            column.operator("hops.radial_array", text="Radial Array", icon_value=get_icon_id("ArrayCircle"))
        else:
            column.operator("hops.radial_array_nodes", text="Radial Array V2", icon_value=get_icon_id("ArrayCircle")).from_empty = True
        column.separator()
        column.operator("hops.taper", text = "Taper / Deform", icon_value=get_icon_id("Tris"))
        column.separator()

        column.operator("hops.sphere_cast", text="SphereCast", icon_value=get_icon_id("SphereCast"))
        column.separator()

        column.operator("hops.edge2curve", text="Curve/Extract", icon_value=get_icon_id("Curve"))
        column.operator("view3d.face_extract", text="Face Extract", icon_value=get_icon_id("FacePanel"))
        #column.separator()

        #column.operator("hops.st3_array", text="Array V2", icon_value=get_icon_id("GreyArrayX"))
        # column.separator()

        column.separator() #.modifier_types='BOOLEAN'
        column.operator("hops.apply_modifiers", text="Smart Apply", icon_value=get_icon_id("Applyall"))
        column.operator("hops.adjust_auto_smooth", text="AutoSmooth", icon_value=get_icon_id("Diagonal"))

        if addon.preference().ui.expanded_menu:
            column = row.column()
        else:
            column.separator()

        if bpy.context.active_object and bpy.context.active_object.type == 'MESH':
            column.menu("HOPS_MT_MaterialListMenu", text = "Material List", icon="MATERIAL_DATA")
            if len(context.selected_objects) >= 2:
                column.operator("material.simplify", text="Material Link", icon_value=get_icon_id("Applyall"))
            #column.separator()

        column.operator_context = 'INVOKE_DEFAULT'
        column.operator("material.hops_new", text = 'Add Blank Material', icon="PLUS")

        column.separator()

        column.operator("hops.xunwrap", text="Auto Unwrap", icon_value=get_icon_id("CUnwrap"))
        #column.separator()

        if len(context.selected_objects) == 1:
            column.operator("hops.reset_status", text="HOPS Reset", icon_value=get_icon_id("StatusReset"))
            #column.separator()

        if context.active_object and context.active_object.type == 'MESH':
            column.menu("HOPS_MT_SelectViewSubmenu", text="Selection Options",  icon_value=get_icon_id("ShowNgonsTris"))
            #column.separator()

        column.separator()

        column.menu("HOPS_MT_BoolScrollOperatorsSubmenu", text="Mod Scroll/Toggle", icon_value=get_icon_id("Diagonal"))

        column.separator()

        column.menu("HOPS_MT_Export", text = 'Export', icon="EXPORT")
        column.separator()

        if addon_exists("MESHmachine"):
            column.separator()
            column.menu("MACHIN3_MT_mesh_machine", text="MESHmachine", icon_value=get_icon_id("Machine"))

        if addon_exists("Cablerator"):
            column.menu("VIEW3D_MT_cablerator", text="Cable Ops", icon_value=get_icon_id("Cablerator"))

        if len(context.selected_objects) == 2:
            if addon_exists("conform_object"):
                column.menu("OBJECT_MT_conform_object", text="Conform Object", icon_value=get_icon_id("Cablerator"))
                column.separator()
            column.operator("hops.shrinkwrap2", text="ShrinkTo", icon='GP_MULTIFRAME_EDITING')
        else:
            column.separator()

        column.operator("hops.to_gpstroke", text="To_Stroke", icon="GREASEPENCIL")
        column.separator()
        if addon_exists("nSolve"):
            column.operator("nsolve.swap_mode", text="nSolve", icon_value=get_icon_id("nSolve"))

        column.operator("hops.timer", text="hTimer", icon="TIME")


class HOPS_MT_MeshToolsSubmenu(bpy.types.Menu):
    bl_label = 'Mesh Tools Submenu'
    bl_idname = 'HOPS_MT_MeshToolsSubmenu'

    def draw(self, context):
        layout = self.layout
        is_boolean = len([mod for mod in bpy.context.active_object.modifiers if mod.type == 'BOOLEAN'])

        layout.operator_context = 'INVOKE_DEFAULT'
        layout.operator("hops.helper", text="Modifier Helper", icon="SCRIPTPLUGINS")

        layout.separator()

        layout.operator("hops.bevel_assist", text="Bevel / Edge Manager", icon_value=get_icon_id("CSharpen"))

        layout.separator()

        layout.operator("hops.bevel_helper", text="Bevel Helper", icon_value=get_icon_id("ModifierHelper"))
        layout.operator("hops.sharp_manager", text="Edge Manager", icon_value=get_icon_id("Diagonal"))
        layout.operator("view3d.bevel_multiplier", text="Bevel Exponent", icon_value=get_icon_id("FaceGrate"))

        layout.separator()

        if is_boolean:
            #layout.operator("hops.scroll_multi", text="Bool Multi Scroll ", icon_value=get_icon_id("Diagonal"))
            layout.operator("hops.ever_scroll_v2", text="Ever Scroll", icon_value=get_icon_id("StatusReset"))
            layout.operator("hops.bool_scroll_objects", text="Object Scroll", icon_value=get_icon_id("StatusReset"))
            layout.separator()

        # layout.operator("hops.scroll_multi", text="Mod Scroll/Toggle", icon_value=get_icon_id("StatusReset"))
        layout.operator("hops.ever_scroll_v2", text="Ever Scroll", icon_value=get_icon_id("StatusReset"))

        op = layout.operator("hops.modifier_scroll", text="Modifier Scroll", icon_value=get_icon_id("Diagonal"))
        op.additive = True
        op.all = True

        layout.operator("hops.bool_toggle_viewport", text= "Toggle Modifiers", icon_value=get_icon_id("Ngons")).all_modifiers = False

        layout.separator()

        layout.menu("HOPS_MT_Export", text = 'Export', icon="EXPORT")
