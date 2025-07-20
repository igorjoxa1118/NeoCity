import bpy
from bpy.types import Menu, Panel
from ..Tools.helper import load_icons
from ..Tools.translation import translate
from ..Tools.independant_helper import get_addon_preferences, get_version_from_manifest

init_pref = False

nb_version = get_version_from_manifest()


def get_init_pref():
    global init_pref
    return init_pref


class FLUENT_MT_PieMenu(Menu):
    bl_label = 'Fluent '+nb_version

    def __init__(self):
        global init_pref
        if not init_pref:
            bpy.context.scene.fluentProp.model_resolution = get_addon_preferences().model_resolution
            bpy.context.scene.fluentProp.width = get_addon_preferences().latest_bevel_width_preference
            bpy.context.scene.fluentProp.min_auto_bevel_segments = get_addon_preferences().min_auto_bevel_segments
            bpy.context.scene.fluentProp.min_auto_cylinder_segments = get_addon_preferences().min_auto_cylinder_segments

            init_pref = True

    def menu_zero(self, context):
        icons = load_icons()
        autocomplete_one_ico = icons.get("autocomplete_one").get('previews')
        latest_bevel_ico = icons.get("latest_bevel").get('previews')
        sym_ico = icons.get("sym").get('previews')
        show_bool_ico = icons.get("show_bool").get('previews')
        cut_ico = icons.get("cut").get('previews')
        slice_ico = icons.get("slice").get('previews')
        inset_ico = icons.get("inset").get('previews')
        creation_ico = icons.get("creation").get('previews')
        wireframe_ico = icons.get("wireframe").get('previews')
        duplicate_ico = icons.get("duplicate").get('previews')
        warning_ico = icons.get("warning").get('previews')
        preset_ico = icons.get("preset").get('previews')
        edit_ico = icons.get("edit").get('previews')
        boolean_ico = icons.get("boolean").get('previews')
        wire_ico = icons.get("wire").get('previews')
        pipe_ico = icons.get("pipe").get('previews')
        plate_ico = icons.get("plate").get('previews')
        grid_ico = icons.get("grid").get('previews')
        settings_ico = icons.get("settings").get('previews')
        normal_ico = icons.get("normal").get('previews')
        cloth_ico = icons.get("cloth").get('previews')
        tool_ico = icons.get("tool").get('previews')
        td_ico = icons.get("technical_display").get('previews')
        show_bool_02_ico = icons.get("show_bool_02").get('previews')
        screw_ico = icons.get("screw").get('previews')

        layout = self.layout
        scn = context.scene

        pie = layout.menu_pie()

        # gauche
        box = pie.column(align=True)
        line_01 = box.row(align=True)
        line_01.scale_x = 1.2
        line_01.scale_y = 1.5
        line_01.operator('fluent.cutstarter', text='', icon_value=cut_ico.icon_id)
        line_01.operator('fluent.slicestarter', text='', icon_value=slice_ico.icon_id)

        line_02 = box.row(align=True)
        line_02.scale_x = 1.2
        line_02.scale_y = 1.5
        line_02.operator('fluent.insetstarter', text='', icon_value=inset_ico.icon_id)
        line_02.operator('fluent.booleanoperator', text='', icon_value=boolean_ico.icon_id)

        line_03 = box.row(align=True)
        line_03.scale_x = 1.2
        line_03.scale_y = 1.5
        line_03.operator('fluent.createstarter', text='', icon_value=creation_ico.icon_id)
        line_03.operator("fluent.booleanduplicate", text='', icon_value=duplicate_ico.icon_id)

        # droite
        box = pie.column(align=True)
        box.scale_x = 1.2
        box.scale_y = 1.5

        if 'fluent_catalyst' in bpy.context.preferences.addons:
            dr_02 = box.row(align=True)
            dr_02.operator('fluent.editor', text='', icon_value=edit_ico.icon_id).operation = 'EDIT'
            dr_02.operator('fluentcatalyst.geometrymenu', text='', icon='OUTLINER_DATA_GP_LAYER')
        else:
            box.operator('fluent.editor', text='', icon_value=edit_ico.icon_id).operation = 'EDIT'

        box.operator("fluent.autocompleteone", text='', icon_value=autocomplete_one_ico.icon_id)
        box.operator("fluent.normalrepair", text='', icon_value=normal_ico.icon_id)
        dr_03 = box.row(align=True)
        if get_addon_preferences().pie_option_other_adjustments:
            dr_03.operator("fluent.otheradjustments", text='', icon_value=settings_ico.icon_id)
        if get_addon_preferences().pie_option_toolbox:
            dr_03.menu("FLUENT_MT_ToolBox_Menu", text='', icon_value=tool_ico.icon_id)

        # bas
        box = pie.column(align=True)
        box.alignment = 'CENTER'
        r_01 = box.row(align=False)

        box.operator('fluent.addlatestbevel', text=translate('addLatestBevel'))

        box.prop(context.scene.fluentProp, 'width', text=translate('latestBevelWidth'))

        box.prop(context.scene.fluentProp, 'bevel_angle_limit', text=translate('angleLimit'))

        try:
            if get_addon_preferences().pie_option_pt:
                box.separator()
                power_trip = box.column(align=True)
                power_trip.scale_x = 1.2
                power_trip.scale_y = 1.5

                pt_01 = power_trip.row(align=True)
                pt_01.alignment = 'CENTER'
                pt_01.operator("fluent.plates", text='', icon_value=plate_ico.icon_id)
                pt_01.operator("fluent.screw", text='', icon_value=screw_ico.icon_id).operation = 'ADD'
                pt_01.operator("fluent.grids", text='', icon_value=grid_ico.icon_id).operation = 'ADD'

                pt_02 = power_trip.row(align=True)
                pt_02.alignment = 'CENTER'
                pt_02.operator("fluent.wire", text='', icon_value=wire_ico.icon_id).operation = 'ADD'
                pt_02.operator("fluent.pipe", text='', icon_value=pipe_ico.icon_id).operation = 'ADD'

                pt_03 = power_trip.row(align=True)
                pt_03.alignment = 'CENTER'
                pt_03.operator("fluent.clothpanel", text='', icon_value=cloth_ico.icon_id)
                pt_03.operator("fluent.clothsettings", text='', icon='OPTIONS')
        except:
            pass

        # haut
        box = pie.row(align=True)
        box.scale_x = 1.2
        box.scale_y = 1.5
        box.operator("fluent.technicaldisplay", text='', icon_value=td_ico.icon_id)
        box.operator("fluent.booleandisplay", text='', icon_value=show_bool_02_ico.icon_id)
        box.operator("fluent.wireframedisplay", text='', icon_value=wireframe_ico.icon_id)

    def draw(self, context):
        self.menu_zero(context)


class FLUENT_MT_ToolBox_Menu(Menu):
    bl_label = "Toolbox"

    def draw(self, context):
        icons = load_icons()
        sym_ico = icons.get("sym").get('previews')
        become_ico = icons.get("become").get('previews')

        layout = self.layout
        scn = context.scene

        # box = layout.column()
        # layout.operator("fluent.alignview", text='Align view')
        layout.operator("fluent.alignview", text=translate('angleView'))
        layout.operator("fluent.vgcleaner", text=translate('cleanVertexGroup'))
        layout.separator()

        layout.operator("fluent.allcuttermirror", icon_value=sym_ico.icon_id)
        layout.operator("fluent.becomefluent", icon_value=become_ico.icon_id)
        layout.separator()
        try:
            layout.operator("fluent.texttomesh", text=translate('text2Mesh'))
            layout.operator("fluent.chaintomesh", text=translate('chainToMesh'))
        except:
            pass
        layout.separator()

        layout.operator("fluent.autosupport", text=translate('cleanBooleanApplication'))
        layout.operator("fluent.applytoboolean", text=translate('applyToBoolean'))
        layout.separator()

        layout.operator("fluent.booleansynchronization", text=translate('booleanSync'))
        layout.separator()

        layout.operator("fluent.cleanbooleanobjects", text=translate('removeUnusedBoolean'))
        layout.operator("fluent.slicecleaner", text=translate('sliceCleaner'))


class FLUENT_PT_Basic_Panel(Panel):
    "Fluent"
    bl_idname='FLUENT_PT_Basic_Panel'
    bl_label = "Fluent"
    bl_name = "Fluent"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = 'Fluent'

    def __init__(self):
        global init_pref
        if not init_pref:
            bpy.context.scene.fluentProp.model_resolution = get_addon_preferences().model_resolution
            bpy.context.scene.fluentProp.width = get_addon_preferences().latest_bevel_width_preference
            bpy.context.scene.fluentProp.min_auto_bevel_segments = get_addon_preferences().min_auto_bevel_segments
            bpy.context.scene.fluentProp.min_auto_cylinder_segments = get_addon_preferences().min_auto_cylinder_segments

            init_pref = True

    def draw_header(self, context: bpy.types.Context):
        icons = load_icons()
        self.layout.label(text="", icon_value=icons.get("powertrip_icon").get('previews').icon_id)

    def draw(self, context):
        icons = load_icons()
        autocomplete_one_ico = icons.get("autocomplete_one").get('previews')
        latest_bevel_ico = icons.get("latest_bevel").get('previews')
        sym_ico = icons.get("sym").get('previews')
        show_bool_ico = icons.get("show_bool").get('previews')
        cut_ico = icons.get("cut").get('previews')
        slice_ico = icons.get("slice").get('previews')
        inset_ico = icons.get("inset").get('previews')
        creation_ico = icons.get("creation").get('previews')
        wireframe_ico = icons.get("wireframe").get('previews')
        duplicate_ico = icons.get("duplicate").get('previews')
        warning_ico = icons.get("warning").get('previews')
        preset_ico = icons.get("preset").get('previews')
        edit_ico = icons.get("edit").get('previews')
        boolean_ico = icons.get("boolean").get('previews')
        wire_ico = icons.get("wire").get('previews')
        pipe_ico = icons.get("pipe").get('previews')
        plate_ico = icons.get("plate").get('previews')
        grid_ico = icons.get("grid").get('previews')
        settings_ico = icons.get("settings").get('previews')
        normal_ico = icons.get("normal").get('previews')
        cloth_ico = icons.get("cloth").get('previews')
        tool_ico = icons.get("tool").get('previews')
        td_ico = icons.get("technical_display").get('previews')
        show_bool_02_ico = icons.get("show_bool_02").get('previews')

        layout = self.layout
        scn = context.scene

        box = layout.column(align=True)
        box.scale_x = 1.2
        box.scale_y = 1.5
        line_01 = box.row(align=True)
        line_01.operator("fluent.technicaldisplay", text=translate('technicalDisplay'), icon_value=td_ico.icon_id)
        line_02 = box.row(align=True)
        line_02.operator("fluent.booleandisplay", text=translate('showBoolean'), icon_value=show_bool_02_ico.icon_id)
        line_02.operator("fluent.wireframedisplay", text=translate('wireframe'), icon_value=wireframe_ico.icon_id)

        # gauche
        box = layout.column(align=True)
        line_01 = box.row(align=True)
        line_01.scale_x = 1.2
        line_01.scale_y = 1.5
        line_01.operator('fluent.cutstarter', text=translate('cutAdd'), icon_value=cut_ico.icon_id)
        line_01.operator('fluent.slicestarter', text=translate('slice'), icon_value=slice_ico.icon_id)

        line_02 = box.row(align=True)
        line_02.scale_x = 1.2
        line_02.scale_y = 1.5
        line_02.operator('fluent.insetstarter', text=translate('inset'), icon_value=inset_ico.icon_id)
        line_02.operator('fluent.booleanoperator', text=translate('boolean'), icon_value=boolean_ico.icon_id)

        line_03 = box.row(align=True)
        line_03.scale_x = 1.2
        line_03.scale_y = 1.5
        line_03.operator('fluent.createstarter', text=translate('creation'), icon_value=creation_ico.icon_id)
        line_03.operator("fluent.booleanduplicate", text=translate('duplicateExtract'), icon_value=duplicate_ico.icon_id)

        # droite
        box = layout.column(align=True)
        box.scale_x = 1.2
        box.scale_y = 1.5
        box.operator('fluent.editor', text=translate('edit'), icon_value=edit_ico.icon_id).operation = 'EDIT'
        finish = box.row(align=True)
        finish.scale_x = 1.2
        box.operator("fluent.autocompleteone", text=translate('complete'), icon_value=autocomplete_one_ico.icon_id)
        box.operator("fluent.normalrepair", text=translate('nRepair'), icon_value=normal_ico.icon_id)
        box.operator("fluent.otheradjustments", text=translate('otherAdjustment'), icon_value=settings_ico.icon_id)
        box.menu("FLUENT_MT_ToolBox_Menu", text=translate('toolBox'), icon_value=tool_ico.icon_id)

        # bas
        box = layout.column()
        bevel_tool = box.column(align=True)
        bevel_tool.operator('fluent.addlatestbevel', text=translate('addLatestBevel'))
        bevel_tool.prop(context.scene.fluentProp, 'width', text=translate('latestBevelWidth'))
        bevel_tool.prop(context.scene.fluentProp, 'bevel_angle_limit', text=translate('angleLimit'))
        bevel_tool.operator("fluent.toggleloopslide", text=translate('toggleLoopSlide'))

        box = layout.column(align=True)
        box.operator('fluent.buildinganimation')
        box.operator('fluent.clothanimation')
        box.prop(context.scene.fluentProp, 'anim_speed')
