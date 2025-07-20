import bpy
from ... icons import get_icon_id
from ... utils.addons import addon_exists
from ... utility import addon

class HOPS_MT_Export(bpy.types.Menu):
    bl_idname = "HOPS_MT_Export"
    bl_label = "Export Options"

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        box = layout.column(align=True)

        if (3, 2, 0) <= bpy.app.version: #new exporter in 3.2.0
            ot = box.operator("wm.obj_export", text="OBJ")
            ot.export_selected_objects = True
            ot.export_triangulated_mesh = True
        else:
            ot = box.operator("export_scene.obj", text="OBJ")
            ot.use_selection = True
            ot.use_triangles = True

        ot = box.operator("export_scene.fbx", text="FBX")
        ot.use_selection = True

        ot = box.operator("wm.alembic_export", text="ABC")
        ot.selected = True

# Material
class HOPS_MT_MaterialListMenu(bpy.types.Menu):
    bl_idname = "HOPS_MT_MaterialListMenu"
    bl_label = "Material list"

    def draw(self, context):
        layout = self.layout
        preference = addon.preference().ui
        col = layout.column(align=True)

        object = context.active_object

        filepathprefs = bpy.context.preferences.filepaths

        # draw dot name toggle at the top of the menu
        col.prop(filepathprefs, 'show_hidden_files_datablocks', text="hide .names")

        col.separator()
        col.operator_context = 'INVOKE_DEFAULT'
        col.operator("material.hops_new", text = 'Add Blank Material', icon="PLUS")
        col.operator_context = 'INVOKE_DEFAULT'
        col.operator("hops.material_scroll", text = 'Material Scroll', icon_value=get_icon_id("StatusReset"))
        if len(context.selected_objects) >= 2:
            if object.material_slots:
                col.operator("material.simplify", text="Material Link", icon_value=get_icon_id("Applyall"))
                col.separator()
        else:
            col.operator("hops.map_scroll", text = 'Map Scroll', icon_value=get_icon_id("Plugin"))
            col.separator()

        # filter out dot name materials, based on blender prefs
        materials = None

        if context.object.type == 'GPENCIL':
            if filepathprefs.show_hidden_files_datablocks:
                materials = [mat for mat in bpy.data.materials if mat.grease_pencil and (not mat.name.startswith('.'))]
            else:
                materials = [mat for mat in bpy.data.materials if mat.grease_pencil]

        elif hasattr(context.object, 'material_slots'):
            if filepathprefs.show_hidden_files_datablocks:
                materials = [mat for mat in bpy.data.materials if not mat.grease_pencil and (not mat.name.startswith('.'))]
            else:
                materials = [mat for mat in bpy.data.materials if not mat.grease_pencil]

        if materials:
            col_count = round(len(materials)/preference.Hops_material_count)
            flow = layout.grid_flow(row_major=False, columns=col_count, even_columns=True, even_rows=True, align=False)

            for mat in materials:
                if preference.Hops_material_icons:
                    try:
                        icon_val = layout.icon(mat)
                    except:
                        icon_val = 1
                        print("WARNING [Mat Panel]: Could not get icon value for %s" % mat.name)

                    op = flow.operator("object.apply_material", text=mat.name, icon_value=icon_val)
                    op.mat_to_assign = mat.name

                else:
                    op = flow.operator("object.apply_material", text=mat.name, icon='MATERIAL')
                    op.mat_to_assign = mat.name


class HOPS_MT_SculptSubmenu(bpy.types.Menu):
    bl_label = 'Sculpt'
    bl_idname = 'HOPS_MT_SculptSubmenu'

    def draw(self, context):
        layout = self.layout

        # sculpt = context.tool_settings.sculpt
        # settings = self.paint_settings(context)
        # brush = settings.brush

        layout.prop(context.preferences.inputs, 'use_mouse_emulate_3_button')

        if context.sculpt_object.use_dynamic_topology_sculpting:
            layout.operator("sculpt.dynamic_topology_toggle",text="Disable Dyntopo")
        else:
            layout.operator("sculpt.dynamic_topology_toggle", text="Enable Dyntopo")
        layout.separator()

        if (context.tool_settings.sculpt.detail_type_method == 'CONSTANT'):
            layout.prop(context.tool_settings.sculpt, "constant_detail")
            layout.operator("sculpt.sample_detail_size", text="", icon='EYEDROPPER')
        elif (context.tool_settings.sculpt.detail_type_method == 'BRUSH'):
            layout.prop(context.tool_settings.sculpt, "detail_percent")
        else:
            layout.prop(context.tool_settings.sculpt, "detail_size")
        layout.prop(context.tool_settings.sculpt, "detail_refine_method", text="")
        layout.prop(context.tool_settings.sculpt, "detail_type_method", text="")
        layout.separator()
        layout.prop(context.tool_settings.sculpt, "use_smooth_shading")
        layout.operator("sculpt.optimize")
        if (context.tool_settings.sculpt.detail_type_method == 'CONSTANT'):
            layout.operator("sculpt.detail_flood_fill")
        layout.separator()
        layout.prop(context.tool_settings.sculpt, "symmetrize_direction", text="")
        layout.operator("sculpt.symmetrize")


class HOPS_MT_MiraSubmenu(bpy.types.Menu):
    bl_label = 'Mira Panel'
    bl_idname = 'HOPS_MT_MiraSubmenu'

    def draw(self, context):
        layout = self.layout

        layout = self.layout.column_flow(columns=2)

        # if mira_handler_enabled():
        #     layout.operator("mesh.curve_stretch", text="CurveStretch", icon="RNA")
        #     layout.operator("mesh.curve_guide", text='CurveGuide', icon="RNA")


        layout.operator("mira.curve_stretch", text="CurveStretch", icon="RNA")
        layout.operator("mira.curve_guide", text="CurveGuide", icon="RNA")
        layout.prop(context.scene.mi_cur_stretch_settings, "points_number", text='')
        layout.prop(context.scene.mi_curguide_settings, "points_number", text='')


class HOPS_MT_BasicObjectOptionsSubmenu(bpy.types.Menu):
    bl_label = 'ObjectOptions'
    bl_idname = 'HOPS_MT_BasicObjectOptionsSubmenu'

    def draw(self, context):
        layout = self.layout

        layout = self.layout.column_flow(columns=1)
        row = layout.row()
        sub = row.row()
        sub.scale_y = 1.2

        obj = bpy.context.object

        layout.prop(obj, "name", text="")
        layout.separator()

        obj = bpy.context.object

        layout.prop(obj, "show_name", text="Show object's name"),


class HOPS_MT_FrameRangeSubmenu(bpy.types.Menu):
    bl_label = 'FrameRange'
    bl_idname = 'HOPS_MT_FrameRangeSubmenu'

    def draw(self, context):
        layout = self.layout

        layout = self.layout
        scene = context.scene

        row = layout.row(align=False)
        col = row.column(align=True)

        layout.operator("hops.setframe_end", text="Frame Range", icon_value=get_icon_id("SetFrame"))

        #col.prop(scene, 'frame_start')
        #col.prop(scene, 'frame_end')


class HOPS_MT_SelectViewSubmenu(bpy.types.Menu):
    bl_label = 'Selection'
    bl_idname = 'HOPS_MT_SelectViewSubmenu'

    def draw(self, context):
        layout = self.layout

        m_check = context.window_manager.m_check

        layout.operator("hops.poly_debug_display", text="Polygon Debug", icon_value=get_icon_id("sm_logo_white"))
        layout.separator()

        if bpy.context.object and bpy.context.object.type == 'MESH':
            if m_check.meshcheck_enabled:
                layout.operator("object.remove_materials", text="Hide Ngons/Tris", icon_value=get_icon_id("ShowNgonsTris"))
            else:
                layout.operator("object.add_materials", text="Display Ngons/Tris", icon_value=get_icon_id("ShowNgonsTris"))

            layout.operator("data.facetype_select", text="Ngons Select", icon_value=get_icon_id("Ngons")).face_type = "5"
            layout.operator("data.facetype_select", text="Tris Select", icon_value=get_icon_id("Tris")).face_type = "3"

# Viewport


class HOPS_MT_ViewportSubmenu(bpy.types.Menu):
    bl_label = 'Viewport'
    bl_idname = 'HOPS_MT_ViewportSubmenu'

    def draw(self, context):
        layout = self.layout
        view3d = context.space_data
        scene = bpy.context.scene

        row = layout.column().row()
        row.operator_context = 'INVOKE_DEFAULT'

        if addon.preference().ui.expanded_menu:
            column = row.column()
        else:
            column =self.layout

        column.prop(view3d.overlay, "show_overlays", text = 'Overlays')
        column.prop(view3d.overlay, 'show_face_orientation')
        column.prop(view3d.overlay, 'show_wireframes')
        column.separator()

        #column = row.column()
        column.operator("hops.camera_rig", text="Add Camera", icon='OUTLINER_OB_CAMERA')

        if 'EEVEE' in scene.render.engine:
            column.operator_context = 'INVOKE_DEFAULT'
            column.operator("hops.adjust_viewport", text="(v)Lookdev+", icon_value=get_icon_id("RGui"))
            column.operator("hops.blank_light", text = "Blank Light", icon_value=get_icon_id("GreyTaper"))
            column.separator()
            column.operator("render.setup", text="Eevee HQ", icon="RESTRICT_RENDER_OFF")
            column.operator("hops.renderb_setup", text="Eevee LQ", icon="RESTRICT_RENDER_OFF")
            column.operator("ui.reg", text="Solid / Texture Toggle", icon="RESTRICT_RENDER_OFF")
            column.separator()
            column.operator("view3d.view_align", text= "Align View", icon_value=get_icon_id("HardOps"))
            column.operator("ui.clean", text="Simplify", icon="RESTRICT_RENDER_OFF")

        if scene.render.engine == 'CYCLES':
            column.operator("hops.adjust_viewport", text="(v)Lookdev+", icon_value=get_icon_id("RGui"))
            column.operator("hops.blank_light", text = "Blank Light", icon_value=get_icon_id("GreyTaper"))
            column.separator()
            column.operator("render.setup", text="Cycles HQ", icon="RESTRICT_RENDER_OFF")
            column.operator("hops.renderb_setup", text="Cycles LQ", icon="RESTRICT_RENDER_OFF")
            column.operator("hops.renderc_setup", text="GPU HQ ", icon="RESTRICT_RENDER_OFF")
            column.separator()
            column.operator("view3d.view_align", text= "Align View", icon_value=get_icon_id("HardOps"))
            column.operator("ui.clean", text="Simplify", icon="RESTRICT_RENDER_OFF")

        if view3d.show_region_tool_header == False:
            column.separator()
            column.operator("hops.show_topbar", text = "Show Toolbar")

        if view3d.shading.type == 'MATERIAL':
            column.separator()
            column.prop(view3d.shading, 'use_scene_lights')
            column.prop(view3d.shading, 'use_scene_world')
            column.prop(view3d.overlay, 'show_look_dev')
            column.separator()

        column.separator()

        if view3d.shading.type == 'SOLID':
            if view3d.overlay.show_overlays == True and view3d.overlay.show_wireframes == True:
                column.prop(view3d.overlay, 'wireframe_threshold')
                column.separator()

        if view3d.shading.type == 'WIREFRAME':
            column.prop(view3d.shading, "type", text = "")
            column.separator()

        if addon.preference().ui.expanded_menu:
            column = row.column()
        else:
            column.separator()

        if scene.render.engine == 'BLENDER_EEVEE' or scene.render.engine == 'CYCLES':
            if view3d.shading.type != 'WIREFRAME' and view3d.shading.type != 'RENDERED':
                if view3d.shading.light in ["STUDIO", "MATCAP"]:
                    column.template_icon_view(view3d.shading, "studio_light", show_labels=True, scale=3)
                    column.label(text='')

            if view3d.shading.type != 'WIREFRAME':
                if view3d.shading.type != 'RENDERED':
                    column.separator()
                column.prop(view3d.shading, "type", text = "")
                column.separator()

            # if view3d.shading.type == 'MATERIAL' or (view3d.shading.type == 'RENDERED' and scene.render.engine == 'BLENDER_EEVEE'):
            #     column.separator()
            #     column.prop(scene.eevee, "taa_samples", text = "Viewport Samples")
            #     column.prop(scene.eevee, "gi_diffuse_bounces", text = "Indirect Bounces")

            #     if scene.eevee.use_motion_blur:
            #         column.prop(scene.eevee, "motion_blur_samples", text = "Motion Blur Samples")

            #     column.separator()

            if view3d.shading.type == 'MATERIAL' or (view3d.shading.type == 'RENDERED' and scene.render.engine == 'BLENDER_EEVEE'):
                column.prop(scene.eevee, "use_bloom", text = "Bloom")
                column.prop(scene.eevee, "use_ssr", text = "Screen Space Reflections")

                if scene.eevee.use_ssr == True:
                    column.prop(scene.eevee, "use_ssr_halfres", text = "Half Res")

            if view3d.shading.type == 'MATERIAL' or scene.render.engine == 'BLENDER_EEVEE' and view3d.shading.type not in {'WIREFRAME', 'SOLID'}:
                column.prop(scene.eevee, "use_gtao", text = "AO")
                column.prop(scene.eevee, "use_soft_shadows", text = "Soft Shadows")

            if view3d.shading.type == 'MATERIAL' or (view3d.shading.type == 'RENDERED' and scene.render.engine == 'BLENDER_EEVEE'):
                column.prop(scene.eevee, "use_motion_blur", text = "Motion Blur")

        if view3d.shading.type == 'SOLID':
            column.separator()
            column.prop(view3d.shading, 'show_cavity')
            column.prop(view3d.shading, 'show_shadows')

            column.separator()
            column.prop(view3d.shading, "light", text = "")
            column.prop(view3d.shading, "color_type", text = "")
            column.prop(view3d.shading, "background_type", text = "")

        column.separator()

        column.operator_context = 'INVOKE_DEFAULT'
        column.operator("hops.modal_ui_purge", text="Purge Dead UI", icon_value=get_icon_id("Tris"))

class HOPS_MT_RenderSetSubmenuLQ(bpy.types.Menu):
    bl_label = 'RenderSet_submenu_LQ'
    bl_idname = 'HOPS_MT_RenderSetSubmenuLQ'

    def draw(self, context):
        layout = self.layout
        layout.prop(addon.preference().property, "Eevee_preset_LQ", expand=True)


class HOPS_MT_RenderSetSubmenuHQ(bpy.types.Menu):
    bl_label = 'RenderSet_submenu_HQ'
    bl_idname = 'HOPS_MT_RenderSetSubmenuHQ'

    def draw(self, context):
        layout = self.layout
        layout.prop(addon.preference().property, "Eevee_preset_HQ", expand=True)


class HOPS_MT_RenderSetSubmenu(bpy.types.Menu):
    bl_label = 'RenderSet_submenu'
    bl_idname = 'HOPS_MT_RenderSetSubmenu'

    def draw(self, context):
        layout = self.layout

        c = bpy.context.scene
        if c.render.engine == 'CYCLES':
            layout.operator("render.setup", text="Render (1)", icon="RESTRICT_RENDER_OFF")
            layout.operator("hops.renderb_setup", text="Render (2)", icon="RESTRICT_RENDER_OFF")
            layout.operator("hops.renderc_setup", text="Cycles GPU HQ Grumble", icon="RESTRICT_RENDER_OFF")
        if c.render.engine == 'BLENDER_EEVEE':
            layout.operator("render.setup", text="Eevee HQ", icon="RESTRICT_RENDER_OFF")
            layout.menu("HOPS_MT_RenderSetSubmenuHQ", text="HQ Settings")
            layout.operator("hops.renderb_setup", text="Eevee LQ", icon="RESTRICT_RENDER_OFF")
            layout.menu("HOPS_MT_RenderSetSubmenuLQ", text="LQ Settings")
        else:
            pass

        layout.separator()

        row = layout.row(align=False)
        col = row.column(align=True)

        view_settings = context.scene.view_settings
        col.prop(view_settings, "view_transform", text="")
        col.prop(view_settings, "look", text="")


class HOPS_MT_ResetAxiSubmenu(bpy.types.Menu):
    bl_idname = "HOPS_MT_ResetAxiSubmenu"
    bl_label = "Reset Axis Submenu"

    def draw(self, context):
        layout = self.layout
        #layout = self.layout.column_flow(columns=2)
        #row = layout.row()
        #sub = row.row()
        #sub.scale_y = 1.0
        #sub.scale_x = 0.05

        layout.operator("hops.reset_axis", text=" X ", icon_value=get_icon_id("Xslap")).set_axis = "X"
        layout.operator("hops.reset_axis", text=" Y ", icon_value=get_icon_id("Yslap")).set_axis = "Y"
        layout.operator("hops.reset_axis", text=" Z ", icon_value=get_icon_id("Zslap")).set_axis = "Z"


class HOPS_MT_SymmetrySubmenu(bpy.types.Menu):
    bl_idname = "HOPS_MT_SymmetrySubmenu"
    bl_label = "Symmetry Submenu"

    def draw(self, context):
        layout = self.layout

        layout.operator_context = 'INVOKE_DEFAULT'
        layout.operator("hops.mirror_gizmo", text="Mirror", icon_value=get_icon_id("Mirror"))

class HOPS_MT_MiscSubmenu(bpy.types.Menu):
    bl_idname = "HOPS_MT_MiscSubmenu"
    bl_label = "Misc Submenu"

    def draw(self, context):
        layout = self.layout

        layout.operator_context = 'INVOKE_DEFAULT'
        layout.operator("hops.mirror_gizmo", text="Mirror", icon_value=get_icon_id("Mirror"))
        layout.separator()
        layout.operator("hops.bevel_helper", text="Bevel Helper", icon_value=get_icon_id("CSharpen"))
        layout.operator("hops.sharp_manager", text="Edge Manager", icon_value=get_icon_id("Diagonal"))
        layout.operator("view3d.bevel_multiplier", text="Bevel Exponent", icon_value=get_icon_id("BevelMultiply"))

class HOPS_MT_PluginSubmenu(bpy.types.Menu):
    bl_label = 'Plugin Tools Submenu'
    bl_idname = 'HOPS_MT_PluginSubmenu'

    def draw(self, context):
        layout = self.layout

        #        if any("kk_QuickLatticeCreate" in s for s in bpy.context.preferences.addons.keys()):
        #            layout.operator("object.easy_lattice", text="Easy Lattice", icon_value=get_icon_id("Easylattice"))

        #        if any("mesh_snap" in s for s in bpy.context.preferences.addons.keys()):
        #            layout.operator("mesh.snap_utilities_line", text="Snap Line")
        #            layout.operator("mesh.snap_push_pull", text="Push Pull Faces")

        object = context.active_object

        if object.mode == "EDIT" and object.type == "MESH":
            if addon_exists('mira_tools'):
                layout.label(text = "Mira Tools")
                layout.separator()
                op = layout.operator("mesh.curve_stretch", text="Curve Stretch")#,
                layout.operator("mira.curve_stretch", text="MI_CurveStretch", icon="STYLUS_PRESSURE")
                #layout.prop(bpy.context.scene.mi_cur_stretch_settings, "points_number", text='Curve Count')
                layout.separator()
            if addon_exists('bezier_mesh_shaper'):
                layout.separator()
                layout.label(text = "Bezier Mesh Shaper")
                layout.separator()
                op = layout.operator("mesh.bezier_mesh_shaper", text="Curved")#, icon_value=get_icon_id("Easylattice"))
                op.startupAction = 'NORMAL'

                op = layout.operator("mesh.bezier_mesh_shaper", text="Straight")#, icon_value=get_icon_id("Easylattice"))
                op.startupAction ='SNAP_STRAIGHT'
                layout.separator()

        if object.mode == "OBJECT" or object.mode == "EDIT":
            if addon_exists("MESHmachine"):
                layout.label(text = "MeshMachine")
                layout.separator()
                layout.menu("MACHIN3_MT_mesh_machine", text="MESHmachine", icon_value=get_icon_id("Machine"))
                layout.separator()


class HOPS_MT_BoolSumbenu(bpy.types.Menu):
    bl_label = 'Bool Submenu'
    bl_idname = 'HOPS_MT_BoolSumbenu'

    def draw(self, context):
        layout = self.layout

        object = context.active_object

        if object.mode == "OBJECT" and object.type == "MESH":
            layout.operator_context = 'INVOKE_DEFAULT'
            layout.operator("hops.bool_modal", text="Interactive Boolean", icon_value=get_icon_id("InteractiveBoolean"))
            layout.separator()
            layout.operator("hops.bool_difference", text="Difference", icon_value=get_icon_id("Difference"))
            layout.operator("hops.bool_union", text="Union", icon_value=get_icon_id("Union"))
            layout.operator("hops.slash", text="Slash", icon_value=get_icon_id("Slash"))
            layout.separator()
            layout.operator("hops.bool_inset", text="Inset / Outset", icon_value=get_icon_id("InsetOutset"))
            layout.operator("hops.bool_knife", text="Knife", icon_value=get_icon_id("Knife"))
            layout.operator("hops.bool_intersect", text="Intersection", icon_value=get_icon_id("Intersection"))
            layout.separator()
            layout.operator("hops.cut_in", text="Cut-in", icon_value=get_icon_id("Cutin"))

        if object.mode == "EDIT" and object.type == "MESH":
            layout.operator_context = 'INVOKE_DEFAULT'
            layout.operator("hops.bool_modal", text="Interactive Boolean", icon_value=get_icon_id("InteractiveBoolean"))
            layout.operator("hops.sel_to_bool_v3", text="Selection to Boolean", icon="MOD_BOOLEAN")
            layout.separator()
            layout.operator("hops.edit_bool_difference", text="Difference", icon_value=get_icon_id("Difference"))
            layout.operator("hops.edit_bool_union", text="Union", icon_value=get_icon_id("Union"))
            layout.operator("hops.edit_bool_slash", text="Slash", icon_value=get_icon_id("Slash"))
            layout.separator()
            layout.operator("hops.edit_bool_inset", text="Inset / Outset", icon_value=get_icon_id("InsetOutset"))
            layout.operator("hops.edit_bool_knife", text="Knife", icon_value=get_icon_id("Knife"))
            layout.operator("hops.edit_bool_intersect", text="Intersection", icon_value=get_icon_id("Intersection"))

class HOPS_MT_ModSubmenu(bpy.types.Menu):
    bl_label = 'Mod Submenu'
    bl_idname = 'HOPS_MT_ModSubmenu'

    def draw(self, context):
        layout = self.layout

        object = context.active_object

        if object.mode == "OBJECT" and object.type == "MESH":
            row = layout.column().row()
            if addon.preference().ui.expanded_menu:
                column = row.column()
            else:
                column =self.layout

            column.operator_context = 'INVOKE_DEFAULT'
            column.operator("hops.adjust_bevel", text="Bevel", icon="MOD_BEVEL")
            column.operator("hops.adjust_tthick", text="Solidify", icon="MOD_SOLIDIFY")
            column.operator("hops.st3_array", text="Array V2", icon_value=get_icon_id("GreyArrayX"))

            column.operator("hops.mirror_gizmo", text="Mirror", icon="MOD_MIRROR")

            if addon.preference().ui.expanded_menu:
                column.separator()
                column.operator("hops.helper", text="Modifier Helper", icon="SCRIPTPLUGINS")
                column.operator("hops.bool_toggle_viewport", text= "Toggle Modifiers", icon_value=get_icon_id("Tris")).all_modifiers = True
                #column.separator()
                column.operator("hops.mod_apply", text="Apply Modifiers", icon="REC")
                column.separator()
                column.operator("hops.bool_stack", text="Stack / Unstack", icon="NODETREE")

            if addon.preference().ui.expanded_menu:
                column = row.column()
            else:
                column.separator()

            column.operator("hops.mod_lattice", text="Lattice", icon="MOD_LATTICE")
            column.operator("hops.mod_screw", text="Screw", icon="MOD_SCREW")
            if (2, 82, 4) < bpy.app.version:
                column.operator("hops.mod_weld", text="Weld", icon="AUTOMERGE_OFF")
            column.operator("hops.mod_displace", text="Displace", icon="MOD_DISPLACE")
            column.operator("hops.mod_decimate", text="Decimate", icon="MOD_DECIM")
            column.operator("hops.mod_triangulate", text="Triangulate", icon="MOD_TRIANGULATE")
            column.operator("hops.mod_wireframe", text="Wireframe", icon="MOD_WIREFRAME")
            column.operator("hops.mod_weighted_normal", text="Weighted Normal", icon="MOD_NORMALEDIT")
            column.operator("hops.mod_curve", text="Curve", icon="MOD_CURVE")

            if addon.preference().ui.expanded_menu:
                column = row.column()
            else:
                column.separator()

            column.operator("hops.mod_smooth", text="Smooth", icon="MOD_SMOOTH")
            column.operator("hops.mod_cloth", text="Cloth", icon="MOD_CLOTH")
            #column.operator("hops.mod_lsmooth", text="Laplacian Smooth", icon="MOD_SMOOTH")
            column.operator("hops.mod_simple_deform", text="Simple Deform", icon="MOD_SIMPLEDEFORM")
            column.operator("hops.mod_subdivision", text="Subdivision", icon="MOD_SUBSURF")
            column.operator("hops.mod_shrinkwrap", text="Shrinkwrap", icon="MOD_SHRINKWRAP")
            column.operator("hops.mod_cast", text="Cast", icon="MOD_CAST")
            column.operator("hops.mod_skin", text="Skin", icon="MOD_SKIN")
            column.operator("hops.mod_uv_project", text="UV Project", icon="MOD_UVPROJECT")
            #column.separator()


            #Classic Q Menu Style
            if addon.preference().ui.expanded_menu == False:
                column.separator()
                column.operator("hops.helper", text="Modifier Helper", icon="SCRIPTPLUGINS")
                column.operator("hops.bool_toggle_viewport", text= "Toggle Modifiers", icon_value=get_icon_id("Tris")).all_modifiers = True
                #column.separator()
                column.operator("hops.mod_apply", text="Apply Modifiers", icon="REC")

        if object.mode == "EDIT" and object.type == "MESH":
            layout.operator_context = 'INVOKE_DEFAULT'

            layout.operator("hops.adjust_bevel", text="Bevel", icon="MOD_BEVEL")
            if (2, 82, 4) < bpy.app.version:
                layout.operator("hops.mod_weld", text="Weld", icon="AUTOMERGE_OFF")
            layout.operator("hops.mod_lattice", text="Lattice", icon="MOD_LATTICE")
            layout.operator("hops.mod_hook", text="Hook", icon="HOOK")
            layout.operator("hops.mod_mask", text="Mask", icon="MOD_MASK")
            # if (2, 82, 4) < bpy.app.version:
            #     layout.operator("hops.mod_weld", text="Weld", icon="AUTOMERGE_OFF")
            layout.operator("hops.mirror_gizmo", text="Mirror", icon_value=get_icon_id("Mirror"))
            layout.operator("hops.mod_smooth", text="Smooth", icon="MOD_SMOOTH")
            layout.operator("hops.mod_decimate", text="Decimate", icon="MOD_DECIM")


class HOPS_MT_ST3MeshToolsSubmenu(bpy.types.Menu):
    bl_label = 'ST3 Mesh Tools Submenu'
    bl_idname = 'HOPS_MT_ST3MeshToolsSubmenu'

    def draw(self, context):
        layout = self.layout

        object = context.active_object

        if object.mode == "EDIT" and object.type == "MESH":
            if addon_exists("nSolve"):
                layout.operator("nsolve.swap_mode", text="nSolve", icon_value=get_icon_id("nSolve"))
            layout.separator()

            layout.operator_context = 'INVOKE_DEFAULT'
            layout.operator("hops.curve_extrude", text="Curve Extrude", icon="CURVE_DATA")
            layout.operator("hops.flatten_to_face", text="Flatten to Face", icon="FACESEL")
            layout.operator("hops.mesh_align", text="Align to Face", icon="MOD_EXPLODE")
            layout.separator()
            layout.operator("hops.vertext_align", text="Align Vertices Tool", icon="CON_TRACKTO")
            layout.operator("hops.sel_to_bool_v3", text="Selection to Boolean", icon="MOD_BOOLEAN")
            layout.operator("hops.fast_mesh_editor", text="Edit Multi Tool", icon="MOD_REMESH")
            layout.separator()
            layout.operator("view3d.view_align", text= "Align View", icon_value=get_icon_id("HardOps"))
            layout.operator("hops.floor", text="To_floor", icon_value=get_icon_id("grey"))
            layout.separator()
            #layout.operator("hops.face_solver", text="Face Solver", icon_value=get_icon_id("grey"))
            layout.operator("hops.clean_border", text="Clean Borders", icon="MEMORY")
