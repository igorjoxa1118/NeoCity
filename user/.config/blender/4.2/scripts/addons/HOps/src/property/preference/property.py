import bpy, os
from pathlib import Path
from math import radians
from mathutils import Vector
from bpy.types import PropertyGroup
from bpy.props import BoolProperty, FloatVectorProperty, FloatProperty, StringProperty, EnumProperty, IntProperty

from .... utility import addon, modifier
from .... import bl_info
from ... utilityremove import names


def update_HardOps_Panel_Tools(self, context):
    panel = getattr(bpy.types, "hops_main_panel", None)
    if panel is not None:
        bpy.utils.unregister_class(panel)
        panel.bl_category = addon.preference().toolbar_category_name
        bpy.utils.register_class(panel)


def category_name_changed(self, context):
    category = addon.preference().toolbar_category_name
    change_hard_ops_category(category)


def profile_dir():
    return Path(__file__).parents[5].joinpath('presets', 'profiles')

# Edit mode properties

Eevee_presets = [
    ("64", "64", "64"),
    ("128", "128", "128"),
    ("256", "256", "256"),
    ("512", "512", "512"),
    ("1024", "1024", "1024"),
    ("2048", "2048", "2048"),
    ("4096", "4096", "4096")]


booleans_modes = [
    ("BMESH", "Bmesh", ""),
    ("CARVE", "Carve", "")]

settings_tabs_items = [
    ("UI", "UI", ""),
    ("DRAWING", "Drawing", ""),
    ("INFO", "Info", ""),
    ("KEYMAP", "Keymap", ""),
    ("LINKS", "Links / Help", ""),
    ("ADDONS", "Addons", "")]

mirror_modes = [
    ("MODIFIER", "Mod", ""),
    ("BISECT", "Bisect", ""),
    ("SYMMETRY", "Symmetry", "")]

mirror_modes_multi = [
    ("VIA_ACTIVE", "Mod", ""),
    ("MULTI_SYMMETRY", "Symmetry", "")]

mirror_direction = [
    ("-", "-", ""),
    ("+", "+", "")]

ko_popup_type = [
    ("DEFAULT", "Default", ""),
    ("ST3", "St3", "")]

# menu_array_type = [
#     ("DEFAULT", "Default", ""),
#     ("ST3", "St3 V1", ""),
#     ("ST3_V2", "St3 V2", "")]

array_type = [
    ("CIRCLE", "Circle", ""),
    ("DOT", "Dot", "")]

symmetrize_type = [
    ("DEFAULT", "Default", ""),
    ("Machin3", "Machin3", "")]

accu_length_opts = [
    ('Kilometers', 'Kilometers', ''),
    ('Meters', 'Meters', ''),
    ('Centimeters', 'Centimeters', ''),
    ('Millimeters', 'Millimeters', ''),
    ('Micrometers', 'Micrometers', ''),
    ('Miles', 'Miles', ''),
    ('Feet', 'Feet', ''),
    ('Inches', 'Inches', ''),
    ('Thousandth', 'Thousandth', '')]

recent_sort_char = {}

sort_options = (
    'sort_modifiers',
    'sort_nodes',
    'sort_bevel',
    'sort_array',
    'sort_mirror',
    'sort_solidify',
    'sort_weighted_normal',
    'sort_simple_deform',
    'sort_triangulate',
    'sort_decimate',
    'sort_remesh',
    'sort_subsurf',
    'sort_bevel_last',
    'sort_array_last',
    'sort_mirror_last',
    'sort_nodes_last',
    'sort_solidify_last',
    'sort_weighted_normal_last',
    'sort_simple_deform_last',
    'sort_triangulate_last',
    'sort_decimate_last',
    'sort_remesh_last',
    'sort_subsurf_last')


def bc():
    wm = bpy.context.window_manager

    if hasattr(wm, 'bc'):
        return bpy.context.preferences.addons[wm.bc.addon].preferences

    return False


def kitops():
    wm = bpy.context.window_manager

    if hasattr(wm, 'kitops'):
        return bpy.context.preferences.addons[wm.kitops.addon].preferences

    return False


def sync_sort(prop, context):
    for option in sort_options:

        if bc() and hasattr(bc().behavior, option):
            bc().behavior[option] = getattr(prop, option)
        # else:
        #     print(F'Unable to sync sorting options with Box Cutter; Hard Ops {option}\nUpdate Box Cutter!')


def validate_char(prop, context, option):
    for other in dir(prop):
        if not other.endswith('_char'):
            continue

        if option == other:
            if not getattr(prop, option):
                value = prop.__annotations__[option].keywords['default']
                recent_sort_char[option] = value
                setattr(prop, option, value)

                return

            continue

        if getattr(prop, option) == getattr(prop, other):
            setattr(prop, other, recent_sort_char[option])
            recent_sort_char[option] = getattr(prop, option)

            return

    recent_sort_char[option] = getattr(prop, option)


def sort_depth(prop, context):
    sync_sort(prop, context)

    # modifier.sort_depth = prop.sort_depth


def sort_char(prop, context):
    validate_char(prop, context, 'sort_char')
    sync_sort(prop, context)

    modifier.sort_flag = prop.sort_char


def sort_ignore_char(prop, context):
    validate_char(prop, context, 'sort_ignore_char')
    sync_sort(prop, context)

    modifier.ignore_flag = prop.sort_ignore_char


def sort_last_char(prop, context):
    validate_char(prop, context, 'sort_last_char')
    sync_sort(prop, context)

    modifier.sort_last_flag = prop.sort_last_char


def sort_lock_above_char(prop, context):
    validate_char(prop, context, 'sort_lock_above_char')
    sync_sort(prop, context)

    modifier.lock_below_flag = prop.sort_lock_above_char


def sort_lock_below_char(prop, context):
    validate_char(prop, context, 'sort_lock_below_char')
    sync_sort(prop, context)

    modifier.lock_above_flag = prop.sort_lock_below_char


def sort_stop_char(prop, context):
    validate_char(prop, context, 'sort_stop_char')
    sync_sort(prop, context)

    modifier.stop_flag = prop.sort_stop_char


class hops(PropertyGroup):

    bl_idname = f"HOps: {bl_info['version'][0]}.{bl_info['version'][1]}.{bl_info['version'][2]}.{bl_info['version'][3]}"

    debug: BoolProperty(name="debug", default=False)

    # Not shown in pref
    show_presets: BoolProperty(
        name = "Show Presets",
        description = "Show presets in helper",
        default = True)

    toolshelf: EnumProperty(
        name="hopstool", description="",
        items=[
            ('HOPSTOOL', "Hopstool", ""),
            ('MIRROR', "Mirror", "")],
        default='HOPSTOOL')

    # Convert BC notifications
    bc_dimensions_converter: EnumProperty(
        name="Dimensions",
        description="BC Dimensions Converter",
        items=[
            ("Kilometers", "Kilometers", ""),
            ("Meters", "Meters", ""),
            ("Centimeters", "Centimeters", ""),
            ("Millimeters", "Millimeters", ""),
            ("Micrometers", "Micrometers", ""),
            ("Miles", "Miles", ""),
            ("Feet", "Feet", ""),
            ("Inches", "Inches", ""),
            ("Thousandth", "Thousandth", "")],
        default='Meters')

    accu_length: EnumProperty(
        name="Accu Length",
        description="Length to start with accu",
        items=accu_length_opts,
        default='Meters')

    bevel_miter_outer: EnumProperty(
        name="Outer Miter",
        description="Outer Miter",
        items=[
            ("MITER_SHARP", "Sharp", ""),
            ("MITER_PATCH", "Patch", ""),
            ("MITER_ARC", "Arc", "")],
        default='MITER_ARC')

    bevel_miter_inner: EnumProperty(
        name="Inner Miter",
        description="Inner Miter",
        items=[
            ("MITER_SHARP", "Sharp", ""),
            ("MITER_ARC", "Arc", "")],
        default='MITER_SHARP')

    map_scroll_ftype: EnumProperty(
        name="Map Scroll File Types",
        description="Map Scroll File Types",
        items=[
            ("PNG", "PNG", ""),
            ("JPG", "JPG", ""),
            ("BMP", "BMP", ""),
            ("TIFF", "TIFF", ""),
            ("PNG-JPG", "PNG-JPG", ""),
            ("ALL", "ALL", "")],
        default='PNG')

    decalmachine_fix: BoolProperty(name="Use Setup For DECALmachine", default=False)

    adaptivemode: BoolProperty("Adaptive Segments", default=False, description='Dynamic segment adjustment during bevel')
    adaptiveoffset: FloatProperty("Adaptive Offset", default=10, min=0)
    adaptivewidth: BoolProperty("Adaptive Segments", default=False)

    auto_bweight: BoolProperty("auto bweight", default=False, description="Jump to Adjust Bevel post Csharpen")
    bevel_profile: FloatProperty("default bevel profile", default=0.70, min=0, max=1, description="Default bevel profile for modals")
    default_segments: IntProperty(name="Default Segments", description="Default segments for new bevel", default=3, min=1, max=36)
    use_default_profiles: BoolProperty("Default Profiles", default=True)

    profile_folder: StringProperty("Profile Folder", default=str(Path(__file__).parents[5].joinpath('presets', 'profiles')), subtype='DIR_PATH')
    lights_folder: StringProperty("Lights Folder", default=str(Path(__file__).parents[5].joinpath('presets', 'lights')), subtype='DIR_PATH')
    maps_folder: StringProperty("Roughness Folder", default=str(Path(__file__).parents[5].joinpath('maps')), subtype='DIR_PATH')
    font_folder: StringProperty("Font Folder", default=bpy.context.preferences.filepaths.font_directory, subtype='DIR_PATH')

    keep_cutin_bevel: BoolProperty(name="Keep Cut In Bevel", default=True, description='Keeps bevel during cut-in process. By default bevel is omitted.')
    force_array_reset_on_init: BoolProperty(name="Force Array Reset", default=False)
    force_array_apply_scale_on_init: BoolProperty(name="Force Array Apply Scale", default=False)
    force_thick_reset_solidify_init: BoolProperty(name="Force Reset Solidify", default=False)

    ko_popup_type: EnumProperty(
        name="KitOps Popup Type",
        description="Asset Loader Toggle\n\nKitops popup toggle for expansive or classic\nDefault - classic kitops popup\nExpansive - digital loader for both kitops and decalmachine",
        items=[("DEFAULT", "Default", ""),
        ("ST3", "Expansive", "")],
        default='ST3')

    # array_type: EnumProperty(
    #     name="Array V1 Gizmo Type",
    #     description="Array V1 Circle / DOT",
    #     items=[
    #         ("CIRCLE", "Circle", ""),
    #         ("DOT", "Dot", "")],
    #         default='CIRCLE')

    radial_array_type: EnumProperty(
        name="Radia_Array Type",
        description="Radial Array Option Type \n Classic supports only meshes and uses 2 modifiers \n Nodes is a single modifier and supports curves as well \n ",
        items=[
            ("CLASSIC", "Classic", ""),
            ("NODES", "Nodes (V2)", "")],
            default='CLASSIC')

    to_shape_type: EnumProperty(
        name="To_Shape Type",
        description="To_Shape Interface Type",
        items=[
            ("CLASSIC", "Classic ", ""),
            ("CLASSIC+", "To_Shape 1.5 ", "")],
            default='CLASSIC+')

    multi_tool_entry: EnumProperty(
        name="Multi Tool Entry",
        description="Multi tool entry point",
        items=[
            ("SELECT", "SELECT", ""),
            ("SPIN", "SPIN", ""),
            ("MERGE", "MERGE", ""),
            ("DISSOLVE", "DISSOLVE", ""),
            ("JOIN", "JOIN", ""),
            ("KNIFE", "KNIFE", "")],
            default='SELECT')

    menu_style_selector: EnumProperty(
        name="Menu Style Selector",
        description="Menu style selector",
        items=[
            ("DEFAULT", "Default", ""),
            ("BLENDER", "Blender", "")],
            default='DEFAULT')

    array_v2_use_2d: EnumProperty(
        name="Array V2 Adjust Mode",
        description="Method for Array V2",
        items=[
            ("2D", "2D", ""),
            ("3D", "3D", "")],
            default='2D')

    # st3_meshtools: BoolProperty(name="Enable ST3 Meshtools", default=False, description="Enable experimental ST3 Meshtools in edit")

    meshclean_mode: EnumProperty(
        name="Mode", description="",
        items=[
            ('ACTIVE', "Active", "Effect all the active object geometry"),
            ('SELECTED', "Selected", "Effect only selected geometry or selected objects geometry"),
            ('VISIBLE', "Visible", "Effect only visible geometry")],
            default='ACTIVE')

    meshclean_dissolve_angle: FloatProperty(
        name="Limited Dissolve Angle",
        default=radians(0.5),
        min=radians(0),
        max=radians(30),
        subtype="ANGLE")

    meshclean_remove_threshold: FloatProperty(
        name="Remove Threshold Amount",
        description="Remove Double Amount",
        default=0.001,
        min=0.0001,
        max=1.00)

    meshclean_unhide_behavior: BoolProperty(default=True)
    meshclean_delete_interior: BoolProperty(default=False)
    #to_cam_jump: BoolProperty(default=True, description="To_Camera activate new camera as active")
    to_cam: EnumProperty(
        name="To_Cam Behavior",
        description="To_Cam Behavior\n\nFrontal - places camera in front of central model\nView - Aligns camera to view which can be preferred",
        items=[
            ("DEFAULT", "Frontal", ""),
            ("VIEW", "View", "")],
            default='VIEW')

    meshclean_degenerate_iter: IntProperty(
        name='Degenerate Pass',
        description='Number of passes for degenerate geometry',
        default=1,
        min=0)

    # dice_version: EnumProperty(
    #     name="Dice Behavior",
    #     description="Dice Behavior\n\nV1: Classic Dice\nV2: New Dice \n",
    #     items=[
    #         ("V1", "Original", ""),
    #         ("V2", "Version 2", "")],
    #         default='V2')

    to_render_jump: BoolProperty(default=False, description="Lookdev settings to render settings on confirm of viewport+")
    to_light_constraint: BoolProperty(default=False, description="Blank / Add light utilizes track to")

    add_prefix: BoolProperty(default=False, description="Add Prefix On Select Q menu Items")

    accushape_type: EnumProperty(
        name="Default Accushape Version",
        description="What technique to use for accushape",
        items=[
            ('CLASSIC', "Classic", "Original version of accushape"),
            ('V2', "V2", "Refined redesigned optimal aimed for mobility")],
        default='V2')

    bool_scroll: EnumProperty(
        name="Default Boolscroll Method",
        description="What technique to use to boolscroll",
        items=[
            ('CLASSIC', "Classic", "Isolate cutters then begin showing cutters via scroll"),
            ('ADDITIVE', "Additive", "Do not hide previous cutters when beginning scroll")],
        default='CLASSIC')

    bool_scroll_type: EnumProperty(
        name="Default Scroll System",
        description="Which system of scroll",
        items=[
            ('CLASSIC', "Classic", "Classic Bool/Mod scroller"),
            ('EVERY', "Every", "Unified scroll system")],
        default='EVERY')

    ever_scroll_dot_open: EnumProperty(
        name="Default Launch UI",
        description="Launch EverScroll with Dot Open / Closed",
        items=[
            ('DOT', "Dot UI", "Use Dot UI"),
            ('FAS', "FAS UI", "Dot will be closed")],
        default='FAS')

    dice_method: EnumProperty(
        name="Default Dice Method",
        description="What technique to use to cut the object",
        items=[
            ('KNIFE_PROJECT', "Knife Project", "Use knife project to cut the object"),
            ('MESH_INTERSECT', "Mesh Intersect", "Use mesh intersect to cut the object")],
        default='KNIFE_PROJECT')

    dice_adjust: EnumProperty(
        name="Default Dice Adjust",
        description="What variable to start out adjusting with the mouse",
        items=[
            ('AXIS', "Axis", "Use the mouse to adjust the dicing axis"),
            ('SEGMENTS', "Segments", "Use the mouse to adjust the amount of cuts"),
            ('NONE', "None", "Don't use the mouse to adjust anything")],
        default='AXIS')

    dice_show_mesh_wire: BoolProperty(
        name="Dice Show Mesh Wire",
        description="Show the wireframe of the mesh after it has been cut",
        default=True)

    dice_wire_type: EnumProperty(
        name="Dice Wire Type",
        description="What type of wire drawing to use",
        items=[
            ('LINES', "Lines", "Draw the dice shader with lines"),
            ('TICKS', "Ticks", "Draw the dice shader with ticks (angle brackets)"),
            ('DOTS', "Dots", "Draw the dice shader with dots")],
        default='LINES')

    smart_apply_dice: EnumProperty(
        name="Default Dice Adjust",
        description="Initial optional apply behavior on dice launch",
        items=[
            ('SMART_APPLY', "Smart Apply", "Smart apply prior to dice"),
            ('APPLY', "Apply", "Convert to mesh prior to dice."),
            ('NONE', "None", "Do not apply. Just Dice.")],
        default='NONE')

    bool_bstep: BoolProperty(
        name="Bool Bevel Step",
        description="Add new bevel during sort bypass on Ctrl + click boolean operations",
        default=True)

    boolean_solver: EnumProperty(
        name="Boolean Solver",
        description="",
        items=[('FAST', "Fast", "Fast solver for booleans (Default)"),
               ('EXACT', "Exact", "Exact solver for booleans (Slower)")],
        default='FAST')

    sharp_use_crease: BoolProperty(name="Allow Sharpening To Use Crease", default=True, description="Sharpen / Mark to mark using crease 1.0")
    sharp_use_bweight: BoolProperty(name="Allow Sharpening To Use Bevel Weight", default=True, description="Sharpen / Mark to mark using bevel weight 1.0")
    sharp_use_seam: BoolProperty(name="Allow Sharpening To Use Seams", default=False, description="Sharpen / Mark to mark using seams. Assists with face selection")
    sharp_use_sharp: BoolProperty(name="Allow Sharpening To Use Sharp Edges", default=True, description="Sharpen / Mark to mark using sharp marking. Assists autosmoothing")

    sort_modifiers: BoolProperty(
        name = 'Sort Modifiers',
        description = '\n Sort modifier order',
        update = sync_sort,
        default = True)

    sort_bevel: BoolProperty(
        name = 'Sort Bevel',
        description = '\n Ensure bevel modifiers are placed after any boolean modifiers created',
        update = sync_sort,
        default = True)

    sort_weighted_normal: BoolProperty(
        name = 'Sort Weighted Normal',
        description = '\n Ensure weighted normal modifiers are placed after any boolean modifiers created',
        update = sync_sort,
        default = True)

    sort_array: BoolProperty(
        name = 'Sort Array',
        description = '\n Ensure array modifiers are placed after any boolean modifiers created',
        update = sync_sort,
        default = True)

    sort_mirror: BoolProperty(
        name = 'Sort Mirror',
        description = '\n Ensure mirror modifiers are placed after any boolean modifiers created',
        update = sync_sort,
        default = True)

    sort_solidify: BoolProperty(
        name = 'Sort Soldify',
        description = '\n Ensure solidify modifiers are placed after any boolean modifiers created',
        update = sync_sort,
        default = False)

    sort_triangulate: BoolProperty(
        name = 'Sort Triangulate',
        description = '\n Ensure triangulate modifiers are placed after any boolean modifiers created',
        update = sync_sort,
        default = True)

    sort_simple_deform: BoolProperty(
        name = 'Sort Simple Deform',
        description = '\n Ensure simple deform modifiers are placed after any boolean modifiers created',
        update = sync_sort,
        default = True)

    sort_decimate: BoolProperty(
        name = 'Sort Decimate',
        description = '\n Ensure decimate modifiers are placed after any boolean modifiers created',
        update = sync_sort,
        default = False)

    sort_nodes: BoolProperty(
        name = 'Sort Nodes',
        description = '\n Ensure Geometry Nodes modifiers are placed after any boolean modifiers created',
        update = sync_sort,
        default = False)

    sort_remesh: BoolProperty(
        name = 'Sort Remesh',
        description = '\n Ensure remesh modifiers are placed after any boolean modifiers created',
        update = sync_sort,
        default = True)

    sort_subsurf: BoolProperty(
        name = 'Sort Subsurf',
        description = '\n Ensure subsurf modifiers are placed after any boolean modifiers created',
        update = sync_sort,
        default = False)

    sort_weld: BoolProperty(
        name = 'Sort Weld',
        description = '\n Ensure weld modifiers are placed after any boolean modifiers created',
        update = sync_sort,
        default = False)

    sort_uv_project: BoolProperty(
        name = 'Sort UV Project',
        description = '\n Ensure uv project modifiers are placed after any boolean modifiers created',
        update = sync_sort,
        default = True)

    sort_bevel_last: BoolProperty(
        name = 'Sort Bevel',
        description = '\n Only effect the most recent bevel modifier when sorting',
        update = sync_sort,
        default = True)

    sort_weighted_normal_last: BoolProperty(
        name = 'Sort Weighted Normal Last',
        description = '\n Only effect the most recent weighted normal modifier when sorting',
        update = sync_sort,
        default = True)

    sort_array_last: BoolProperty(
        name = 'Sort Array Last',
        description = '\n Only effect the most recent array modifier when sorting',
        update = sync_sort,
        default = True)

    sort_mirror_last: BoolProperty(
        name = 'Sort Mirror Last',
        description = '\n Only effect the most recent mirror modifier when sorting',
        update = sync_sort,
        default = True)

    sort_solidify_last: BoolProperty(
        name = 'Sort Soldify Last',
        description = '\n Only effect the most recent solidify modifier when sorting',
        update = sync_sort,
        default = False)

    sort_triangulate_last: BoolProperty(
        name = 'Sort Triangulate Last',
        description = '\n Only effect the most recent triangulate modifier when sorting',
        update = sync_sort,
        default = True)

    sort_simple_deform_last: BoolProperty(
        name = 'Sort Simple Deform Last',
        description = '\n Only effect the most recent simple deform modifier when sorting',
        update = sync_sort,
        default = True)

    sort_decimate_last: BoolProperty(
        name = 'Sort Decimate Last',
        description = '\n Only effect the most recent decimate modifier when sorting',
        update = sync_sort,
        default = False)

    sort_nodes_last: BoolProperty(
        name = 'Sort Nodes last',
        description = '\n Only effect the most recent nodes modifier when sorting',
        update = sync_sort,
        default = True)

    sort_remesh_last: BoolProperty(
        name = 'Sort Remesh Last',
        description = '\n Only effect the most recent remesh modifier when sorting',
        update = sync_sort,
        default = True)

    sort_subsurf_last: BoolProperty(
        name = 'Sort Subsurf Last',
        description = '\n Only effect the most recent subsurface modifier when sorting',
        update = sync_sort,
        default = False)

    sort_weld_last: BoolProperty(
        name = 'Sort Weld Last',
        description = '\n Only effect the most recent weld modifier when sorting',
        update = sync_sort,
        default = True)

    sort_uv_project_last: BoolProperty(
        name = 'Sort UV Project Last',
        description = '\n Only effect the most recent uv project modifier when sorting',
        update = sync_sort,
        default = True)

    sort_bevel_ignore_weight: BoolProperty(
        name = 'Ignore Weight Bevels',
        description = '\n Ignore bevel modifiers that are using the weight limit method while sorting',
        update = sync_sort,
        default = True)

    sort_bevel_ignore_vgroup: BoolProperty(
        name = 'Ignore VGroup Bevels',
        description = '\n Ignore bevel modifiers that are using the vertex group limit method while sorting',
        update = sync_sort,
        default = True)

    sort_bevel_ignore_only_verts: BoolProperty(
        name = 'Ignore Only Vert Bevels',
        description = '\n Ignore bevel modifiers that are using the only vertices option while sorting',
        update = sync_sort,
        default = True)

    sort_depth: IntProperty(
        name = 'Sort Depth',
        description = '\n Number of sortable mods from the end (bottom) of the stack. 0 to sort whole stack',
        update = sort_depth,
        min = 0,
        default = 6)

    sort_char: StringProperty(
        name = 'Sort Flag',
        description = '\n Prefix a modifier name with this text character and it will sort the modifier\n  Note: Check the above options before utilizing these flags\n             Many of the behaviors exist for common modifiers',
        update = sort_char,
        maxlen = 1,
        default = '*')

    sort_ignore_char: StringProperty(
        name = 'Ignore Flag',
        description = '\n Prefix the modifier name with this text character and it will be ignored.\n  Default: Space',
        update = sort_ignore_char,
        maxlen = 1,
        default = ' ')

    sort_last_char: StringProperty(
        name = 'Sort Last Flag',
        description = '\n Prefix the modifier name with this text character and it will be treated like the most recent modifier of the type when sorted.\n  Note: The lowest modifier in the stack with this flag takes precedence\n\n Prefix twice to force',
        update = sort_last_char,
        maxlen = 1,
        default = '!')

    sort_lock_above_char: StringProperty(
        name = 'Lock Above Flag',
        description = '\n Prefix a modifier name with this text character and it will keep itself below the modifier above it',
        update = sort_lock_above_char,
        maxlen = 1,
        default = '^')

    sort_lock_below_char: StringProperty(
        name = 'Lock Below Flag',
        description = '\n Prefix a modifier name with this text character and it will keep itself above the modifier below it',
        update = sort_lock_below_char,
        maxlen = 1,
        default = '.')

    sort_stop_char: StringProperty(
        name = 'Stop Flag',
        description = '\n Prefix a modifier name with this text character and it will not sort it or any modifiers above it in the stack.\n   Note: Including those with prefixes',
        update = sort_stop_char,
        maxlen = 1,
        default = '_')

    workflow: EnumProperty(
        name="Mode", description="Default mode of boolean usage.",
        items=[
            ('NONDESTRUCTIVE', "NonDestructive", "Keep boolean modifiers unapplied initially"),
            ('DESTRUCTIVE', "Destructive", "Apply boolean modifiers immediately")],
            default='NONDESTRUCTIVE')

    workflow_mode: EnumProperty(
        name="Mode", description="Default mode of bevel mod usage.",
        items=[
            ('ANGLE', "Angle", "Default bevel utilizing mesh angle for calculation"),
            ('WEIGHT', "Weight", "Utilizies bevel working from weighted edges")],
            default='ANGLE')

    # add_weighten_normals_mod: BoolProperty(name="WN", default=False, description="Adds weighted normal mod via Csharp at end of stack (antiquated)")
    use_harden_normals: BoolProperty(name="HN", default=False, description="Enables Harden normals on Bevel use")

    helper_tab: StringProperty(name="Helper Set Category", default="MODIFIERS")

    Eevee_preset_HQ: EnumProperty(items=Eevee_presets, default="2048")
    Eevee_preset_LQ: EnumProperty(items=Eevee_presets, default="64")

    tab: EnumProperty(name="Tab", items=settings_tabs_items)

    toolbar_category_name: StringProperty(
        name="Toolbar Category",
        default="HardOps",
        description="Name of the tab in the toolshelf in the 3d view",
        update=category_name_changed)

    bev_bool_helper: BoolProperty(
        name="Bevel / Boolean Helper",
        default=True,
        description="Toggles bevel / boolean helper with bevel boolean multi tool \n Ctrl + Shift + B \n Intended for laptop usage and workflow simplification")

    bevel_loop_slide: BoolProperty(
        name="Bweight loop slide",
        default=True,
        description="Enables loop slide on bevel modifiers")

    pie_mod_expand: BoolProperty(
        name="Pie Mod Expand",
        default=False,
        description="Expand Pie")

    right_handed: BoolProperty(
        name="Right Handed",
        default=True,
        description="Reverse The X Mirror For Right Handed People")

    BC_unlock: BoolProperty(
        name="BC",
        default=False,
        description="BC Support")

    hops_modal_help: BoolProperty(
        name="Modal Help",
        default=False,
        description="Enables help for modal operators")

    Hops_sharp_remove_cutters: BoolProperty(
        name="Remove Cutters",
        description="Remove Cutters on Csharp apply",
        default=False)

    Hops_smartapply_remove_cutters: BoolProperty(
        name="Smart Apply Remove Cutters",
        description="Smart Apply Remove Cutters\n\nExperimental:\nCan have issues with multi mesh smart apply or shared cutters.\nWork in progress",
        default=False)

    sharpness: FloatProperty(name="angle edge marks are applied to", default=radians(30), min=radians(1), max=radians(180), precision=3, unit='ROTATION')
    auto_smooth_angle: FloatProperty(name="angle edge marks are applied to", default=radians(60), min=radians(1), max=radians(180), precision=3, unit='ROTATION')

    # operators
    Hops_mirror_modes: EnumProperty(name="Mirror Modes", items=mirror_modes, default='MODIFIER')
    Hops_mirror_modes_multi: EnumProperty(name="Mirror Modes Multi", items=mirror_modes_multi, default='VIA_ACTIVE')
    Hops_mirror_direction: EnumProperty(name="Mirror Direction", items=mirror_direction, default='+')

    Hops_gizmo_mirror_block_x: BoolProperty(name="Mirror X Gizmo Block", default=False)
    Hops_gizmo_mirror_block_y: BoolProperty(name="Mirror Y Gizmo Block", default=False)
    Hops_gizmo_mirror_block_z: BoolProperty(name="Mirror Z Gizmo Block", default=False)

    Hops_gizmo_mirror_u: BoolProperty(name="Mirror UV", default=False)
    Hops_gizmo_mirror_v: BoolProperty(name="Mirror UV", default=False)

    Hops_mirror_modal_mod_on_bisect: BoolProperty(
        name="Modal Mirror Bisect Modifier",
        default=True,
        description="use modifier for modal mirror bisect")

    Hops_mirror_modal_use_cursor: BoolProperty(
        name="Modal Mirror Uess Cursor",
        default=False,
        description="uses cursor for modal mirror")

    Hops_mirror_modal_revert: BoolProperty(
        name="Modal Mirror Revert",
        default=True,
        description="reverts modal mirror")

    Hops_mirror_modal_Interface_scale: FloatProperty(
        name="Modal Mirror Interface Scale",
        description="Modal Mirror Interface Scale",
        default=0.7, min=0.1, max=50)

    Hops_gizmo_array: FloatProperty(
        name="Array gizmo",
        description="Array gizmo",
        default=0
        )

    Hops_modal_percent_scale: FloatProperty(
        name="Modal Operators Scale",
        description="Modal Operators Scale",
        default=1, min=0.001, max=100)

    Hops_twist_radial_sort: BoolProperty(
        name="Twist / Radial Bypass",
        default=True,
        description="Determines render visibility for twist360/radial\n\nBypasses sort bypass / edit display on twist / radial 360\n*bypassing sort can be useful for cutting radial shapes as a whole*")

    auto_scroll_time_interval: FloatProperty(
        name="Auto Scroll Interval",
        description="Auto Scroll Time Interval in seconds",
        default=1, min=0.1, max=60)

    # Edit mode properties

    adjustbevel_use_1_segment: BoolProperty(name="use 1 segment", default=True)

    Hops_circle_size: FloatProperty(
        name="Bevel offset step",
        description="Bevel offset step",
        default=0.0001, min=0.0001)

    Hops_gizmo: BoolProperty(name="Display Mirror Gizmo", default=True)
    Hops_gizmo_fail: BoolProperty(name="gizmo failed", default=False)
    Hops_gizmo_mirror: BoolProperty(name="Display Mirror Gizmo", default=False)
    Hops_gizmo_qarray: BoolProperty(name="Display Array Gizmo", default=False)

    circle_divisions: IntProperty(name="Division Count", description="Amount Of Vert divisions for circle", default=5, min=1, max=12)

    dots_snap: EnumProperty(
        name="Mode", description="",
        items=[
            ('ORIGIN', "Origin", ""),
            ('FIXED', "Fixed", ""),
            ('CURSOR', "Cursor", "")],
        default='CURSOR')

    modal_handedness: EnumProperty(
        name="Handedness",
        description="Orientation Style for modal operation\n\nprotip: Use left.\n",
        items=[
            ('LEFT', "Left", ""),
            ('RIGHT', "Right", "")],
        default='LEFT')

    dots_x_cursor: FloatProperty("dots x", default=100)
    dots_y_cursor: FloatProperty("dots y", default=0)

    dots_x: FloatProperty("dots x", default=100)
    dots_y: FloatProperty("dots y", default=100)

    parent_boolshapes: BoolProperty(name="Parent Boolshapes", default=False, description="Parents cutter to the target allowing for transformation")

    view_align_filter_empties: BoolProperty(
        name = 'View Align Filter Empties',
        description = 'View Align Filter Empties',
        default = False)

    # Map Scroll
    map_scroll_folder_count: IntProperty(name="Map Scroll Folder Count", description="Map Scroll Folder Count", default=3, min=3, max=8)
    map_scroll_file_count: IntProperty(name="Map Scroll File Count", description="Map Scroll File Count", default=3, min=3, max=8)

    # UI Toggles
    show_hardops_properties: BoolProperty(name="Show Hard-Ops Properties", default=False)
    show_sharp_options: BoolProperty(name="Show Sharp Options", default=False)
    show_cutter_options: BoolProperty(name="Show Cutter Options", default=False)

    # Sculpt PreUse Options
    add_primitive_newobject: BoolProperty(name="Added primitive becomes new object", default=False)

    show_misc_options: BoolProperty(name="Show Misc Options", default=False)

    in_tool_popup_style: EnumProperty(
        name="In-Tool pop-up Style",
        description="Style of popup when applicable ",
        items=[
            ('DEFAULT', "Default", "Default style"),
            ('BLENDER', "Blender", "Blender style")],
        default='DEFAULT')

    # Modifier prefixes
    mod_prefix_WN: StringProperty(
        name="Weighted Normals Prefix",
        description="Name Prefix for Weighted Normals Modifier",
        default="")

def label_row(path, prop, row, label=''):
    row.label(text=label if label else names[prop])
    row.prop(path, prop, text='')


def header_row(row, prop, label='', emboss=False):
    preference = addon.preference()
    icon = 'DISCLOSURE_TRI_RIGHT' if not getattr(preference.property, prop) else 'DISCLOSURE_TRI_DOWN'
    row.alignment = 'LEFT'
    row.prop(preference.property, prop, text='', emboss=emboss)

    sub = row.row(align=True)
    sub.scale_x = 0.25
    sub.prop(preference.property, prop, text='', icon=icon, emboss=emboss)
    row.prop(preference.property, prop, text=F'{label}', emboss=emboss)

    sub = row.row(align=True)
    sub.scale_x = 0.75
    sub.prop(preference.property, prop, text=' ', icon='BLANK1', emboss=emboss)


def draw(preference, context, layout):

    # --- HARD-OPS PROPS --- #
    box = layout.box()
    header_row(box.row(align=True), 'show_hardops_properties', label='Hardops Properties')
    box.separator()
    if preference.property.show_hardops_properties:
        # Controls
        split = box.split()
        sub_box = split.box()
        sub_box.label(text="Modal Controls")
        sub_box = sub_box.box()
        label_row(preference.property, 'modal_handedness', sub_box.row(), label='Left/Right')

        # Menu
        split = box.split()
        sub_box = split.box()
        sub_box.label(text="Menu Options")
        sub_box = sub_box.box()
        label_row(preference.property, 'ko_popup_type', sub_box.row(), label='KitOps Popup')
        #label_row(preference.property, 'dice_version', sub_box.row(), label='Dice')
        label_row(preference.property, 'to_shape_type', sub_box.row(), label='To_Shape')
        label_row(preference.property, 'accushape_type', sub_box.row(), label='Accushape')
        label_row(preference.property, 'radial_array_type', sub_box.row(), label='Radial Array')

        # Controls
        sub_box = split.box()
        sub_box.label(text="Scroll Options")
        sub_box = sub_box.box()
        #label_row(preference.property, 'bool_scroll_type', sub_box.row(), label='Scroll Type')
        label_row(preference.property, 'bool_scroll', sub_box.row(), label='Bool Scroll')
        #if addon.preference().property.bool_scroll_type != 'CLASSIC':
        label_row(preference.property, 'ever_scroll_dot_open', sub_box.row(), label='Scroll UI')
        label_row(preference.property, 'auto_scroll_time_interval', sub_box.row(), label='Time Interval')

        # Bevel
        split = box.split()
        sub_box = split.box()
        sub_box.label(text="Bevel Defaults")
        sub_box = sub_box.box()
        label_row(preference.property, 'workflow_mode', sub_box.row(), label='Workflow Mode')
        label_row(preference.property, 'default_segments', sub_box.row(), label='Segments')
        label_row(preference.property, 'bevel_profile', sub_box.row(), label='Profile')
        label_row(preference.property, 'bevel_miter_outer', sub_box.row(), label='Miter Outer')
        label_row(preference.property, 'bevel_miter_inner', sub_box.row(), label='Miter Inner')
        label_row(preference.property, 'use_default_profiles', sub_box.row(), label='Default Profiles')
        label_row(preference.property, 'use_harden_normals', sub_box.row(), label='Harden Normals')

        # Clean
        sub_box = split.box()
        sub_sub_box = sub_box.box()
        sub_sub_box.label(text="In-Tool")
        label_row(preference.property, 'array_v2_use_2d', sub_sub_box.row(), label='Array Method')
        label_row(preference.property, 'multi_tool_entry', sub_sub_box.row(), label='Select Tool ')
        label_row(preference.property, 'in_tool_popup_style', sub_sub_box.row(), label='Pop-up Style')
        label_row(preference.property, 'menu_style_selector', sub_sub_box.row(), label='Menu Style')

        # Modifier
        sub_box = sub_box.box()
        sub_box.label(text="Modifier")
        sub_box = sub_box.box()
        label_row(preference.property, 'mod_prefix_WN', sub_box.row(), label='WN Prefix')

        # Operators
        split = box.split()
        sub_box = split.box()
        sub_box.label(text="Operator")
        sub_box = sub_box.box()
        label_row(preference.behavior, 'mat_viewport', sub_box.row(), label='Blank Material (view)')
        label_row(preference.property, 'Hops_twist_radial_sort', sub_box.row(), label='Radial / Twist Render')
        label_row(preference.property, 'to_render_jump', sub_box.row(), label='Viewport+ Set Render')
        label_row(preference.property, 'view_align_filter_empties', sub_box.row(), label='View Align Filter')
        label_row(preference.property, 'meshclean_mode', sub_box.row(), label='Meshclean ')
        label_row(preference.property, 'accu_length', sub_box.row(), label='Accushape ')
        label_row(preference.property, 'add_primitive_newobject', sub_box.row(), label='Add Primitive - New Object ')

        # Misc
        sub_box = split.box()
        sub_box.label(text=" ")
        sub_box = sub_box.box()
        label_row(preference.property, 'to_light_constraint', sub_box.row(), label='Blank Light Constraint')
        label_row(preference.property, 'to_cam', sub_box.row(), label='To_Cam ')
        label_row(preference.property, 'map_scroll_ftype', sub_box.row(), label='Map Scroll')
        label_row(preference.property, 'map_scroll_folder_count', sub_box.row(), label='Map Scroll Folders')
        label_row(preference.property, 'map_scroll_file_count', sub_box.row(), label='Map Scroll Files')

        # Paths
        split = box.split()
        sub_box = split.box()
        sub_box.label(text="Paths")
        sub_box = sub_box.box()
        label_row(preference.property, 'profile_folder', sub_box.row(), label='Profile Folder')
        label_row(preference.property, 'lights_folder', sub_box.row(), label='Lights Folder')
        label_row(preference.property, 'maps_folder', sub_box.row(), label='Maps Folder')
        label_row(preference.property, 'font_folder', sub_box.row(), label='Font Folder')

    # --- MARK & SHARPEN --- #
    box = layout.box()
    header_row(box.row(align=True), 'show_sharp_options', label='Mark & Sharpen')
    box.separator()
    if preference.property.show_sharp_options:

        split = box.split()
        sub_box = split.box()
        sub_box.label(text="Mark")
        sub_box = sub_box.box()
        label_row(preference.property, 'sharp_use_crease', sub_box.row(), label='Crease')
        label_row(preference.property, 'sharp_use_bweight', sub_box.row(), label='Bevel Weight')
        label_row(preference.property, 'sharp_use_seam', sub_box.row(), label='Seam')
        label_row(preference.property, 'sharp_use_sharp', sub_box.row(), label='Sharp')

        sub_box = split.box()
        sub_box.label(text="Sharp Defaults")
        sub_box = sub_box.box()
        label_row(preference.property, 'sharpness', sub_box.row(), label='Angle')

    # --- CUTTERS --- #
    box = layout.box()
    header_row(box.row(align=True), 'show_cutter_options', label='Cutter Removal')
    box.separator()
    if preference.property.show_cutter_options:
        box = box.box()
        label_row(preference.property, 'Hops_sharp_remove_cutters', box.row(), label='Csharp ')
        label_row(preference.property, 'Hops_smartapply_remove_cutters', box.row(), label='Smart Apply ')

    # --- MISC --- #
    box = layout.box()
    header_row(box.row(align=True), 'show_misc_options', label='Misc Options')
    box.separator()
    if preference.property.show_misc_options:
        box = box.box()
        label_row(preference.property, 'bev_bool_helper', box.row(), label='Bevel / Boolean Multi Hotkey')

    # --- DEBUG --- #
    layout.separator()
    label_row(preference.property, 'debug', layout.row(), label='Debug Options')
    if addon.preference().property.debug:
        draw_debug_options(addon.preference(), layout)


def draw_debug_options(preference, layout):

    #label_row(preference.property, 'st3_meshtools', layout.row(), label='St3 Meshtools')
    label_row(preference.property, 'decalmachine_fix', layout.row(), label='Use Decalmachine Fix')
    label_row(preference.property, 'show_presets', layout.row(), label='show_presets')
    label_row(preference.property, 'adaptivemode', layout.row(), label='Use Adaptive Mode')
    label_row(preference.property, 'adaptiveoffset', layout.row(), label='Use Adaptive Offset')
    label_row(preference.property, 'adaptivewidth', layout.row(), label='Use Adaptive Width')
    label_row(preference.property, 'auto_bweight', layout.row(), label='Use Auto Bweight')
    label_row(preference.property, 'keep_cutin_bevel', layout.row(), label='keep_cutin_bevel')
    label_row(preference.property, 'force_array_reset_on_init', layout.row(), label='force_array_reset_on_init')
    label_row(preference.property, 'force_array_apply_scale_on_init', layout.row(), label='force_array_apply_scale_on_init')
    label_row(preference.property, 'force_thick_reset_solidify_init', layout.row(), label='force_thick_reset_solidify_init')
    label_row(preference.property, 'meshclean_dissolve_angle', layout.row(), label='meshclean_dissolve_angle')
    label_row(preference.property, 'meshclean_remove_threshold', layout.row(), label='meshclean_remove_threshold')
    label_row(preference.property, 'meshclean_degenerate_iter', layout.row(), label='degenerate pass')
    label_row(preference.property, 'meshclean_unhide_behavior', layout.row(), label='meshclean_unhide_behavior')
    label_row(preference.property, 'meshclean_delete_interior', layout.row(), label='meshclean_delete_interior')
    label_row(preference.property, 'Hops_gizmo_mirror_u', layout.row(), label='mirror U')
    label_row(preference.property, 'Hops_gizmo_mirror_v', layout.row(), label='mirror V')
    #label_row(preference.property, 'hops_modal_help', layout.row(), label='Show Help For modal Operators')
    # label_row(preference.property, 'sort_bevel', layout.row(), label='sort_bevel')
    # label_row(preference.property, 'sort_solidify', layout.row(), label='sort_solidify')
    # label_row(preference.property, 'sort_array', layout.row(), label='sort_array')
    # label_row(preference.property, 'sort_mirror', layout.row(), label='sort_mirror')
    # label_row(preference.property, 'sort_weighted_normal', layout.row(), label='sort_weighted_normal')
    # label_row(preference.property, 'sort_simple_deform', layout.row(), label='sort_simple_deform')
    # label_row(preference.property, 'sort_triangulate', layout.row(), label='sort_triangulate')
    # label_row(preference.property, 'sort_decimate', layout.row(), label='sort_decimate')

    if preference.property.sort_modifiers:
        row = layout.row(align=True)
        row.alignment = 'RIGHT'
        split = row.split(align=True, factor=0.85)

        row = split.row(align=True)
        for type in modifier.sort_types:
            icon = F'MOD_{type}'
            if icon == 'MOD_WEIGHTED_NORMAL':
                icon = 'MOD_NORMALEDIT'
            elif icon == 'MOD_SIMPLE_DEFORM':
                icon = 'MOD_SIMPLEDEFORM'
            elif icon == 'MOD_DECIMATE':
                icon = 'MOD_DECIM'
            elif icon == 'MOD_WELD':
                icon = 'AUTOMERGE_OFF'

            # Fix
            if icon == 'MOD_UV_PROJECT':
                icon = 'MOD_UVPROJECT'
            elif icon == 'MOD_NODES':
                icon = 'GEOMETRY_NODES'

            row.prop(preference.property, F'sort_{type.lower()}', text='', icon=icon)

        row = split.row(align=True)
        row.scale_x = 1.5
        row.popover('HOPS_PT_sort_last', text='', icon='SORT_ASC')


    label_row(preference.property, 'workflow', layout.row(), label='workflow')
    label_row(preference.property, 'workflow_mode', layout.row(), label='workflow_mode')
    #label_row(preference.property, 'add_weighten_normals_mod', layout.row(), label='add_weighten_normals_mod')
    label_row(preference.property, 'use_harden_normals', layout.row(), label='use_harden_normals')
    label_row(preference.property, 'helper_tab', layout.row(), label='helper_tab')
    label_row(preference.property, 'tab', layout.row(), label='tab')
    label_row(preference.property, 'toolbar_category_name', layout.row(), label='toolbar_category_name')
    label_row(preference.property, 'bevel_loop_slide', layout.row(), label='bevel_loop_slide')
    label_row(preference.property, 'pie_mod_expand', layout.row(), label='pie_mod_expand')
    label_row(preference.property, 'right_handed', layout.row(), label='right_handed')
    label_row(preference.property, 'BC_unlock', layout.row(), label='BC_unlock')
    label_row(preference.property, 'auto_smooth_angle', layout.row(), label='auto_smooth_angle')
    label_row(preference.property, 'Hops_mirror_modes', layout.row(), label='Hops_mirror_modes')
    label_row(preference.property, 'Hops_mirror_modes_multi', layout.row(), label='Hops_mirror_modes_multi')
    label_row(preference.property, 'Hops_mirror_direction', layout.row(), label='Hops_mirror_direction')
    label_row(preference.property, 'Hops_mirror_modal_use_cursor', layout.row(), label='Hops_mirror_modal_use_cursor')
    label_row(preference.property, 'Hops_mirror_modal_revert', layout.row(), label='Hops_mirror_modal_revert')
    label_row(preference.property, 'Hops_mirror_modal_Interface_scale', layout.row(), label='Hops_mirror_modal_Interface_scale')
    label_row(preference.property, 'Hops_gizmo_array', layout.row(), label='Hops_gizmo_array')
    label_row(preference.property, 'Hops_modal_percent_scale', layout.row(), label='Hops_modal_percent_scale')
    label_row(preference.property, 'adjustbevel_use_1_segment', layout.row(), label='adjustbevel_use_1_segment')
    label_row(preference.property, 'Hops_circle_size', layout.row(), label='Hops_circle_size')
    label_row(preference.property, 'Hops_gizmo', layout.row(), label='Hops_gizmo')
    label_row(preference.property, 'Hops_gizmo_fail', layout.row(), label='Hops_gizmo_fail')
    label_row(preference.property, 'Hops_gizmo_mirror', layout.row(), label='Hops_gizmo_mirror')
    label_row(preference.property, 'Hops_gizmo_qarray', layout.row(), label='Hops_gizmo_qarray')
    label_row(preference.property, 'parent_boolshapes', layout.row(), label='Parent Boolshapes')
