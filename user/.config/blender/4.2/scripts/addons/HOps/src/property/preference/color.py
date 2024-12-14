import bpy

from mathutils import Vector

from bpy.types import PropertyGroup
from bpy.props import BoolProperty, FloatVectorProperty, FloatProperty, EnumProperty

from ... utilityremove import names
from .... utility import addon

class hops(PropertyGroup):

    colection_color: EnumProperty(
        name = 'Collection Color',
        description = 'Set Cutters Collection Color',
        items = [
            ('NONE','None','', '', 0),
            ('COLOR_01','Red','', 'COLLECTION_COLOR_01', 1),
            ('COLOR_02','Orange','', 'COLLECTION_COLOR_02', 2),
            ('COLOR_03','Yellow','', 'COLLECTION_COLOR_03', 3),
            ('COLOR_04','Green','', 'COLLECTION_COLOR_04', 4),
            ('COLOR_05','Blue','', 'COLLECTION_COLOR_05', 5),
            ('COLOR_06','Violet','', 'COLLECTION_COLOR_06', 6),
            ('COLOR_07','Pink','', 'COLLECTION_COLOR_07', 7),
            ('COLOR_08','Brown','', 'COLLECTION_COLOR_08', 8)],
        default = 'COLOR_01')

    wire: FloatVectorProperty(
        name = names['wire'],
        description = 'Color of the shape\'s wire',
        size = 4,
        min = 0,
        max = 1,
        subtype='COLOR',
        default = (0.0, 0.0, 0.0, 0.33))

    show_shape_wire: FloatVectorProperty(
        name = names['show_shape_wire'],
        description = 'Color of the shape\'s wire when the object is to be shown',
        size = 4,
        min = 0,
        max = 1,
        subtype='COLOR',
        default = (0.23, 0.7, 0.15, 0.33))

    dot2: FloatVectorProperty(
        name = 'Dot 2',
        description = 'Color of Dot 2',
        size = 4,
        min = 0,
        max = 1,
        subtype='COLOR',
        default = (0.35, 1, 0.29, 0.9))

    dot3: FloatVectorProperty(
        name = 'Dot 3',
        description = 'Color of Dot 3',
        size = 4,
        min = 0,
        max = 1,
        subtype='COLOR',
        default = (1, 0.133, 0.133, 0.9))

    dot4: FloatVectorProperty(
        name = 'Dot 4',
        description = 'Color of Dot 4',
        size = 4,
        min = 0,
        max = 1,
        subtype='COLOR',
        default = (1, 0.9, 0.03, 0.9))

    dot5: FloatVectorProperty(
        name = 'Dot 5',
        description = 'Color of Dot 5',
        size = 4,
        min = 0,
        max = 1,
        subtype='COLOR',
        default = (0.32, 0.67, 1, 0.9))

    dot6: FloatVectorProperty(
        name = 'Dot 5',
        description = 'Color of Dot 6',
        size = 4,
        min = 0,
        max = 1,
        subtype='COLOR',
        default = (0.88, 0.19, 1, 0.9))

    dot7: FloatVectorProperty(
        name = 'Dot 5',
        description = 'Color of Dot 7',
        size = 4,
        min = 0,
        max = 1,
        subtype='COLOR',
        default = (1, 0.57, 0.176, 0.9))

    displace_x: FloatVectorProperty(
        name = 'displace_x',
        description = 'Color of displace_x',
        size = 4,
        min = 0,
        max = 1,
        subtype='COLOR',
        default = (1, 0.2, 0.322, 0.9))

    displace_y: FloatVectorProperty(
        name = 'displace_y',
        description = 'Color of displace_y',
        size = 4,
        min = 0,
        max = 1,
        subtype='COLOR',
        default = (0.54, 0.83, 0, 0.9))

    displace_z: FloatVectorProperty(
        name = 'displace_z',
        description = 'Color of displace_z',
        size = 4,
        min = 0,
        max = 1,
        subtype='COLOR',
        default = (0.157, 0.565, 1, 0.9))

    screw_x: FloatVectorProperty(
        name = 'screw_x',
        description = 'Color of screw_x',
        size = 4,
        min = 0,
        max = 1,
        subtype='COLOR',
        default = (0.4, 1, 0.9, 0.9))

    screw_y: FloatVectorProperty(
        name = 'screw_y',
        description = 'Color of screw_y',
        size = 4,
        min = 0,
        max = 1,
        subtype='COLOR',
        default = (0.4, 1, 0.9, 0.9))

    screw_z: FloatVectorProperty(
        name = 'screw_z',
        description = 'Color of screw_z',
        size = 4,
        min = 0,
        max = 1,
        subtype='COLOR',
        default = (0.4, 1, 0.9, 0.9))

    solidify_x: FloatVectorProperty(
        name = 'solidify_x',
        description = 'Color of solidify_x',
        size = 4,
        min = 0,
        max = 1,
        subtype='COLOR',
        default = (0.4, 1, 0.9, 0.9))

    solidify_y: FloatVectorProperty(
        name = 'solidify_y',
        description = 'Color of solidify_y',
        size = 4,
        min = 0,
        max = 1,
        subtype='COLOR',
        default = (0.4, 1, 0.9, 0.9))

    solidify_z: FloatVectorProperty(
        name = 'solidify_z',
        description = 'Color of solidify_z',
        size = 4,
        min = 0,
        max = 1,
        subtype='COLOR',
        default = (0.4, 1, 0.9, 0.9))

    solidify_c: FloatVectorProperty(
        name = 'solidify_c',
        description = 'Color of solidify_c',
        size = 4,
        min = 0,
        max = 1,
        subtype='COLOR',
        default = (0.157, 0.565, 1, 0.9))

    array_x: FloatVectorProperty(
        name = 'array_x',
        description = 'Color of array_x',
        size = 4,
        min = 0,
        max = 1,
        subtype='COLOR',
        default = (0.875, 0.832, 0, 0.9))

    array_y: FloatVectorProperty(
        name = 'array_y',
        description = 'Color of array_y',
        size = 4,
        min = 0,
        max = 1,
        subtype='COLOR',
        default = (0.875, 0.832, 0, 0.9))

    array_z: FloatVectorProperty(
        name = 'array_z',
        description = 'Color of array_z',
        size = 4,
        min = 0,
        max = 1,
        subtype='COLOR',
        default = (0.875, 0.832, 0, 0.9))

    simple_deform_x: FloatVectorProperty(
        name = 'simple_deform_x',
        description = 'Color of simple_deform_x',
        size = 4,
        min = 0,
        max = 1,
        subtype='COLOR',
        default = (0.939, 0.236, 1, 0.9))

    simple_deform_y: FloatVectorProperty(
        name = 'simple_deform_y',
        description = 'Color of simple_deform_y',
        size = 4,
        min = 0,
        max = 1,
        subtype='COLOR',
        default = (0.939, 0.236, 1, 0.9))

    simple_deform_z: FloatVectorProperty(
        name = 'simple_deform_z',
        description = 'Color of simple_deform_z',
        size = 4,
        min = 0,
        max = 1,
        subtype='COLOR',
        default = (0.939, 0.236, 1, 0.9))

    wireframe_c: FloatVectorProperty(
        name = 'wireframe_c',
        description = 'Color of wireframe_c',
        size = 4,
        min = 0,
        max = 1,
        subtype='COLOR',
        default = (0.939, 0.236, 1, 0.9))

    bevel_c: FloatVectorProperty(
        name = 'bevel_c',
        description = 'Color of bevel_c',
        size = 4,
        min = 0,
        max = 1,
        subtype='COLOR',
        default = (0.4, 1, 0.9, 0.9))

    dot: FloatVectorProperty(
        name = names['dot'],
        description = 'Color of snapping points',
        size = 4,
        min = 0,
        max = 1,
        subtype='COLOR',
        default = (0.4, 1, 0.9, 0.9))

    dot_highlight: FloatVectorProperty(
        name = names['dot_highlight'],
        description = 'Color of snapping points highlighted',
        size = 4,
        min = 0,
        max = 1,
        subtype='COLOR',
        default = (1, 0.597, 0.133, 0.9))

    enable_tool_overlays: BoolProperty(
        name='Enable tool overlays',
        description='Enable tool overlays',
        default=True)

    Hops_text_color: FloatVectorProperty(
        name="",
        default=Vector((0.6, 0.6, 0.6, 0.9)),
        size=4,
        min=0, max=1,
        subtype='COLOR')

    Hops_text2_color: FloatVectorProperty(
        name="",
        default=Vector((0.6, 0.6, 0.6, 0.9)),
        size=4,
        min=0, max=1,
        subtype='COLOR')

    Hops_border_color: FloatVectorProperty(
        name="",
        default=Vector((0.235, 0.235, 0.235, 0.8)),
        size=4,
        min=0, max=1,
        subtype='COLOR')

    Hops_border2_color: FloatVectorProperty(
        name="",
        default=Vector((0.692, 0.298, 0.137, 0.718)),
        size=4,
        min=0, max=1,
        subtype='COLOR')

    Hops_logo_color: FloatVectorProperty(
        name="",
        default=(0.448, 0.448, 0.448, 0.1),
        size=4,
        min=0, max=1,
        subtype='COLOR')

    Hops_logo_color_csharp: FloatVectorProperty(
        name="",
        default=(1, 0.597, 0.133, 0.9),
        size=4,
        min=0, max=1,
        subtype='COLOR')

    Hops_logo_color_cstep: FloatVectorProperty(
        name="",
        default=(0.29, 0.52, 1.0, 0.9),
        size=4,
        min=0, max=1,
        subtype='COLOR')

    Hops_logo_color_boolshape2: FloatVectorProperty(
        name="",
        default=(1, 0.133, 0.133, 0.53),
        size=4,
        min=0, max=1,
        subtype='COLOR')

    Hops_logo_color_boolshape: FloatVectorProperty(
        name="",
        default=(0.35, 1, 0.29, 0.53),
        size=4,
        min=0, max=1,
        subtype='COLOR')

    Hops_hud_color: FloatVectorProperty(
        name="",
        default=(0.17, 0.17, 0.17, 1),
        size=4,
        min=0, max=1,
        subtype='COLOR')

    Hops_hud_text_color: FloatVectorProperty(
        name="",
        default=(0.831, 0.831, 0.831, 1),
        size=4,
        min=0, max=1,
        subtype='COLOR')

    Hops_hud_help_color: FloatVectorProperty(
        name="",
        default=(0.250, 0.750, 1, 0.7),
        size=4,
        min=0, max=1,
        subtype='COLOR')

    Hops_display_logo: BoolProperty(name="Display Logo", default=False)

    Bool_Dots_Text: BoolProperty(name="Display Dots Text", default=True)

    Hops_logo_size: FloatProperty(
        name="HardOps Indicator Size",
        description="BoxCutter indicator size",
        default=2, min=0, max=100)

    Hops_logo_x_position: FloatProperty(
        name="HardOps Indicator X Position",
        description="BoxCutter Indicator X Position",
        default=-203)

    Hops_logo_y_position: FloatProperty(
        name="HardOps Indicator Y Position",
        description="BoxCutter Indicator Y Position",
        default=19)

    Hops_mirror_modal_scale: FloatProperty(
        name="Modal Mirror Operators Scale",
        description="Modal Mirror Operators Scale",
        default=5, min=0.1, max=100)

    Hops_mirror_modal_sides_scale: FloatProperty(
        name="Modal Mirror Operators Sides Scale",
        description="Modal Mirror Operators Sides Scale",
        default=0.20, min=0.01, max=0.99)

    expand: BoolProperty(name="expand color options", default=False)
    hud_expand: BoolProperty(name="Hud color options", default=False)
    col_expand: BoolProperty(name="Collection color options", default=False)

    #UI SYSTEM
    Hops_UI_text_color: FloatVectorProperty(
        name="",
        default=(1, 1, 1, 1),
        size=4,
        min=0, max=1,
        subtype='COLOR')

    Hops_UI_secondary_text_color: FloatVectorProperty(
        name="",
        default=(1, 1, 1, 1),
        size=4,
        min=0, max=1,
        subtype='COLOR')

    Hops_UI_mods_highlight_color: FloatVectorProperty(
        name="",
        default=(.879, .669, .229, 1), #RGB
        size=4,
        min=0, max=1,
        subtype='COLOR')

    Hops_UI_highlight_color: FloatVectorProperty(
        name="",
        default=(0, 0, 1, .025),
        size=4,
        min=0, max=1,
        subtype='COLOR')

    Hops_UI_highlight_drag_color: FloatVectorProperty(
        name="",
        default=(1, 0, 0, .25),
        size=4,
        min=0, max=1,
        subtype='COLOR')

    Hops_UI_background_color: FloatVectorProperty(
        name="",
        default=(.75, .75, .75, 0),
        size=4,
        min=0, max=1,
        subtype='COLOR')

    Hops_UI_cell_background_color: FloatVectorProperty(
        name="",
        default=(.411, .411, .411, .35),
        size=4,
        min=0, max=1,
        subtype='COLOR',
        description = "Background color for modals")

    tips_background: FloatVectorProperty(
        name="",
        default=(.411, .411, .411),
        size=3,
        min=0, max=1,
        subtype='COLOR',
        description = "Background color for Dot UI Tips")

    Hops_UI_dropshadow_color: FloatVectorProperty(
        name="",
        default=(0, 0, 0, .15),
        size=4,
        min=0, max=1,
        subtype='COLOR')

    Hops_UI_border_color: FloatVectorProperty(
        name="",
        default=(0.2, 0.2, 0.2, .7),
        size=4,
        min=0, max=1,
        subtype='COLOR')

    Hops_UI_mouse_over_color: FloatVectorProperty(
        name="",
        default=(0, 0, .25, .5),
        size=4,
        min=0, max=1,
        subtype='COLOR')

    Hops_UI_text_highlight_color: FloatVectorProperty(
        name="",
        default=(1, 1, 0, 1),
        size=4,
        min=0, max=1,
        subtype='COLOR')

    Hops_UI_uv_color: FloatVectorProperty(
        name="",
        default=(.25, .25, .25, .875),
        size=4,
        min=0, max=1,
        subtype='COLOR')

    # Hops extra drawing
    Hops_wire_mesh: FloatVectorProperty(
        name="",
        default=(1, .5, 0, 1),
        size=4,
        min=0, max=1,
        subtype='COLOR')

    poly_debug_alpha: FloatProperty(
        name="Poly Debug Alpha",
        default=0.20, min=0.001, max=1)

    # --- OPERATIONMS --- #
    grid_system_color: FloatVectorProperty(
        name="",
        default=(1, 1, 1, .5),
        size=4,
        min=0, max=1,
        subtype='COLOR')

    # Form UI : PRIVATE DATA
    form_color_prop_1: FloatVectorProperty(
        name="form_color_prop_1",
        size = 4, min = 0, max = 1,
        subtype='COLOR',
        default = (0, 0, 0, 1))

    form_color_prop_2: FloatVectorProperty(
        name="form_color_prop_2",
        size = 4, min = 0, max = 1,
        subtype='COLOR',
        default = (0, 0, 0, 1))

    form_color_prop_2: FloatVectorProperty(
        name="form_color_prop_3",
        size = 4, min = 0, max = 1,
        subtype='COLOR',
        default = (0, 0, 0, 1))


def header_row(row, prop, label='', emboss=False):
    preference = addon.preference()
    icon = 'DISCLOSURE_TRI_RIGHT' if not getattr(preference.color, prop) else 'DISCLOSURE_TRI_DOWN'
    row.alignment = 'LEFT'
    row.prop(preference.color, prop, text='', emboss=emboss)

    sub = row.row(align=True)
    sub.scale_x = 0.25
    sub.prop(preference.color, prop, text='', icon=icon, emboss=emboss)
    row.prop(preference.color, prop, text=F'{label}', emboss=emboss)

    sub = row.row(align=True)
    sub.scale_x = 0.75
    sub.prop(preference.color, prop, text=' ', icon='BLANK1', emboss=emboss)


def label_row(path, prop, row, label=''):
    row.label(text=label if label else names[prop])
    row.prop(path, prop, text='')


def draw(preference, context, layout):

    # --- Collection --- #
    box = layout.box()
    header_row(box.row(align=True), 'col_expand', label='Collection Display')
    box.separator()
    if preference.color.col_expand:
        label_row(preference.color, 'colection_color', box.row(), label='Collection Color')


    # --- HUD --- #
    box = layout.box()
    header_row(box.row(align=True), 'hud_expand', label='HUD Display')
    box.separator()
    if preference.color.hud_expand:

        # Logo
        main_split = box.split()
        split = main_split.box()
        sub_box = split.box()
        sub_box.label(text="Logo")
        sub_box = sub_box.box()
        label_row(preference.color, 'Hops_display_logo', sub_box.row(), label='Show Logo')
        label_row(preference.color, 'Hops_logo_color', sub_box.row(), label='Color')
        label_row(preference.color, 'Hops_logo_color_boolshape', sub_box.row(), label='Boolshape')
        label_row(preference.color, 'Hops_logo_size', sub_box.row(), label='Size')
        label_row(preference.color, 'Hops_logo_x_position', sub_box.row(), label='Logo X')
        label_row(preference.color, 'Hops_logo_y_position', sub_box.row(), label='Logo Y')

        # Gizmo
        sub_box = split.box()
        sub_box.label(text="Gizmo")
        sub_box = sub_box.box()
        label_row(preference.operator.mirror, 'scale', sub_box.row(), label='Mirror Scale')
        label_row(preference.operator.mirror, 'width', sub_box.row(), label='Mirror Width')

        # Logo
        sub_box = split.box()
        sub_box.label(text="Active tool")
        sub_box = sub_box.box()
        label_row(preference.color, 'wire', sub_box.row())
        label_row(preference.color, 'show_shape_wire', sub_box.row())

        # --- UI System --- #
        split = main_split.split()
        sub_box = split.box()
        sub_box.label(text="UI System")
        sub_box = sub_box.box()
        label_row(preference.color, 'Hops_UI_cell_background_color', sub_box.row(), label='Cell BG')
        label_row(preference.color, 'tips_background', sub_box.row(), label='Tips Background')
        label_row(preference.color, 'Hops_UI_text_color', sub_box.row(), label='Main Text')
        label_row(preference.color, 'Hops_UI_secondary_text_color', sub_box.row(), label='Secoundary Text')
        label_row(preference.color, 'Hops_UI_mods_highlight_color', sub_box.row(), label='Text Highlight')
        label_row(preference.color, 'Hops_UI_background_color', sub_box.row(), label='Background')
        label_row(preference.color, 'Hops_UI_highlight_color', sub_box.row(), label='Highlight')
        label_row(preference.color, 'Hops_UI_dropshadow_color', sub_box.row(), label='Drop Shadow')
        label_row(preference.color, 'Hops_UI_border_color', sub_box.row(), label='Border')
        label_row(preference.color, 'Hops_UI_mouse_over_color', sub_box.row(), label='Hover')
        label_row(preference.color, 'Hops_UI_highlight_drag_color', sub_box.row(), label='Drag')
        label_row(preference.color, 'Hops_UI_uv_color', sub_box.row(), label='UV')
        label_row(preference.color, 'Hops_wire_mesh', sub_box.row(), label='Mesh Wire')
        label_row(preference.color, 'poly_debug_alpha', sub_box.row(), label='Poly Debug Alpha')

        # --- UI System --- #
        main_split = box.split()
        sub_box = main_split.box()
        sub_box.label(text="Operations")
        sub_box = sub_box.box()
        label_row(preference.color, 'grid_system_color', sub_box.row(), label='Grids')

    # --- DOTS --- #
    box = layout.box()
    header_row(box.row(align=True), 'expand', label='Dots Display')
    box.separator()
    if preference.color.expand:

        # Booleandots
        split = box.split()
        sub_box = split.box()
        sub_box.label(text="Booleandots")
        sub_box = sub_box.box()
        label_row(preference.color, 'dot2', sub_box.row(), label='Union')
        label_row(preference.color, 'dot3', sub_box.row(), label='Difference')
        label_row(preference.color, 'dot4', sub_box.row(), label='Slash')
        label_row(preference.color, 'dot5', sub_box.row(), label='Knife')
        label_row(preference.color, 'dot6', sub_box.row(), label='Inset')
        label_row(preference.color, 'dot7', sub_box.row(), label='Intersect')

        # Solidify
        sub_box = split.box()
        sub_box.label(text="Solidify")
        sub_box = sub_box.box()
        label_row(preference.color, 'solidify_x', sub_box.row(), label='Solidify X')
        label_row(preference.color, 'solidify_y', sub_box.row(), label='Solidify Y')
        label_row(preference.color, 'solidify_z', sub_box.row(), label='Solidify Z')
        label_row(preference.color, 'solidify_c', sub_box.row(), label='Solidify C')

        # Displace
        split = box.split()
        sub_box = split.box()
        sub_box.label(text="Displace")
        sub_box = sub_box.box()
        label_row(preference.color, 'displace_x', sub_box.row(), label='Displace X')
        label_row(preference.color, 'displace_y', sub_box.row(), label='Displace Y')
        label_row(preference.color, 'displace_z', sub_box.row(), label='Displace Z')

        # Screw
        sub_box = split.box()
        sub_box.label(text="Screw")
        sub_box = sub_box.box()
        label_row(preference.color, 'screw_x', sub_box.row(), label='Screw X')
        label_row(preference.color, 'screw_y', sub_box.row(), label='Screw Y')
        label_row(preference.color, 'screw_z', sub_box.row(), label='Screw Z')

        # Array
        split = box.split()
        sub_box = split.box()
        sub_box.label(text="Array")
        sub_box = sub_box.box()
        label_row(preference.color, 'array_x', sub_box.row(), label='Array X')
        label_row(preference.color, 'array_y', sub_box.row(), label='Array Y')
        label_row(preference.color, 'array_z', sub_box.row(), label='Array Z')

        # Simple Deform
        sub_box = split.box()
        sub_box.label(text="Simple Deform")
        sub_box = sub_box.box()
        label_row(preference.color, 'simple_deform_x', sub_box.row(), label='Deform X')
        label_row(preference.color, 'simple_deform_y', sub_box.row(), label='Deform Y')
        label_row(preference.color, 'simple_deform_z', sub_box.row(), label='Deform Z')

        # Basic Dots
        split = box.split()
        sub_box = split.box()
        sub_box.label(text="Basic Dots")
        sub_box = sub_box.box()
        label_row(preference.color, 'dot', sub_box.row())
        label_row(preference.color, 'dot_highlight', sub_box.row())

        # Wireframe
        sub_box = split.box()
        sub_box.label(text="Wireframe")
        sub_box = sub_box.box()
        label_row(preference.color, 'wireframe_c', sub_box.row(), label='Wireframe')

        # Bevel
        sub_box = split.box()
        sub_box.label(text="Bevel")
        sub_box = sub_box.box()
        label_row(preference.color, 'bevel_c', sub_box.row(), label='Bevel')

        # Dots Text
        split = box.split()
        sub_box = split.box()
        sub_box.label(text="Dots Text")
        sub_box = sub_box.box()        
        label_row(preference.color, 'Bool_Dots_Text', sub_box.row(), label='Display Dots Text')
        layout.separator()