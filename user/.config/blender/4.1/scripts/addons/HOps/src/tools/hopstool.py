import os
import bpy

from ...utility import screen
from ... icons import get_icon_id
from ... utils.blender_ui import get_dpi_factor
from ... import bl_info
from ... operators.meshtools.poly_debug_display import DATA as poly_data
from ... utility import addon
from . mirror import draw_mirror


def change_prop(context, prop, value):
    context.workspace.tools.update()


def modifier_operators(context, layout, labels=False):
    selected = context.selected_objects
    layout.enabled = getattr(context.active_object, "type", "") == "MESH" and context.active_object in selected

    # Keep the icons alive if also a curve is in the mix
    if any(o.type == 'MESH' for o in selected) and any(o.type == 'CURVE' for o in selected):
        layout.enabled = True

    grey = 'Grey' if not layout.enabled else ''

    layout.operator(
        'hops.add_mod_displace',
        text = '' if not labels else 'Move X',
        icon_value=get_icon_id(F"{grey}MoveX")).axis = 'X'

    layout.operator(
        'hops.add_mod_displace',
        text = '' if not labels else 'Move Y',
        icon_value = get_icon_id(F"{grey}MoveY")).axis = 'Y'

    layout.operator(
        'hops.add_mod_displace',
        text = '' if not labels else 'Move Z',
        icon_value = get_icon_id(F"{grey}MoveZ")).axis = 'Z'

    layout.operator(
        'hops.add_mod_extrude',
        text = '' if not labels else 'Extrude X',
        icon_value = get_icon_id(F"{grey}ExtrudeX")).axis = 'X'

    layout.operator(
        'hops.add_mod_extrude',
        text = '' if not labels else 'Extrude Y',
        icon_value = get_icon_id(F"{grey}ExtrudeY")).axis = 'Y'

    layout.operator(
        'hops.add_mod_extrude',
        text = '' if not labels else 'Extrude Z',
        icon_value = get_icon_id(F"{grey}ExtrudeZ")).axis = 'Z'

    layout.operator(
        'hops.add_mod_screw',
        text = '' if not labels else 'Screw',
        icon = 'MOD_SCREW').axis = 'X'

    layout.operator(
        'hops.add_mod_solidify',
        text = '' if not labels else 'Solidify Z',
        icon = 'FACESEL').axis = 'Z'

    layout.operator(
        'hops.add_mod_solidify',
        text = '' if not labels else 'Solidify',
        icon = 'MOD_SOLIDIFY').axis = 'C'

    layout.operator(
        'hops.add_mod_decimate',
        text = '' if not labels else 'Decimate',
        icon = 'MOD_DECIM')

    layout.operator(
        'hops.add_mod_weld',
        text = '' if not labels else 'Weld',
        icon = 'AUTOMERGE_OFF')

    layout.operator(
        'hops.add_mod_split',
        text = '' if not labels else 'Edge Split',
        icon = 'MOD_EDGESPLIT')

    layout.operator(
        'hops.add_mod_bevel_corners',
        text = '' if not labels else 'Bevel Corners',
        icon_value = get_icon_id(F"{grey}BevelCorners"))

    layout.operator(
        'hops.add_mod_bevel_chamfer',
        text = '' if not labels else 'Chamfer',
        icon_value = get_icon_id(F"{grey}BevelChamfer"))

    layout.operator(
        'hops.add_mod_bevel',
        text = '' if not labels else 'Bevel',
        icon_value = get_icon_id(F"{grey}BevelAll"))

    layout.operator(
        'hops.add_mod_triangulate',
        text = '' if not labels else 'Triangulate',
        icon = 'MOD_TRIANGULATE')

    layout.operator(
        'hops.add_mod_wireframe',
        text = '' if not labels else 'Wireframe',
        icon = 'MOD_WIREFRAME')

    layout.operator(
        'hops.add_mod_lattice',
        text = '' if not labels else 'Lattice',
        icon = 'MOD_LATTICE')

    layout.operator(
        'hops.add_mod_subsurf',
        text = '' if not labels else 'Subsurface',
        icon = 'MOD_SUBSURF')

    twist = layout.operator(
        'hops.add_mod_deform',
        text = '' if not labels else 'Twist',
        icon_value = get_icon_id(F"{grey}Twist"))
    twist.axis = 'Z'
    twist.mode = 'TWIST'
    twist.name = 'HOPS_twist_z'

    bend = layout.operator(
        'hops.add_mod_deform',
        text = '' if not labels else 'Bend',
        icon_value = get_icon_id(F"{grey}Bend"))
    bend.axis = 'Z'
    bend.mode = 'BEND'
    bend.name = 'HOPS_bend_z'

    taper = layout.operator(
        'hops.add_mod_deform',
        text = '' if not labels else 'Taper',
        icon_value = get_icon_id(F"{grey}Taper"))
    taper.axis = 'Z'
    taper.mode = 'TAPER'
    taper.name = 'HOPS_taper_z'

    strech = layout.operator(
        'hops.add_mod_deform',
        text = '' if not labels else 'Stretch',
        icon_value = get_icon_id(F"{grey}Stretch"))
    strech.axis = 'Z'
    strech.mode = 'STRETCH'
    strech.name = 'HOPS_strech_z'

    layout.operator(
        'hops.add_mod_curve',
        text = '' if not labels else 'Curve',
        icon = 'MOD_CURVE')

    layout.operator(
        'hops.mod_curve',
        text = '' if not labels else 'To_Curve',
        icon = 'CURVE_PATH')
 
    layout.operator(
        'hops.add_mod_array',
        text = '' if not labels else 'Array X',
        icon_value = get_icon_id(F"{grey}ArrayX")).axis = 'X'

    layout.operator(
        'hops.add_mod_array',
        text = '' if not labels else 'Array Y',
        icon_value = get_icon_id(F"{grey}ArrayY")).axis = 'Y'

    layout.operator(
        'hops.add_mod_array',
        text = '' if not labels else 'Array Z',
        icon_value = get_icon_id(F"{grey}ArrayZ")).axis = 'Z'

    layout.operator(
        'hops.add_mod_circle_array',
        text = '' if not labels else 'Circle Array',
        icon_value = get_icon_id(F"{grey}ArrayCircle")).axis = 'X'

    op = layout.operator(
        'hops.ever_scroll_v2',
        text = '' if not labels else 'Ever Scroll',
        icon_value = get_icon_id("StatusReset"))
    op.dot_open = True
    op.entry_state = 'MOD'


def scale(value, factor=1, use_dpi_factor=False):
    factor = 1 if not addon.preference().display.use_label_factor else factor
    return (value * factor) * screen.dpi_factor() if use_dpi_factor else value * factor


def keymap():
    mouse_type = 'MOUSE' if bpy.app.version[:2] > (3, 1) else 'TWEAK'
    value_type = 'CLICK_DRAG' if mouse_type == 'MOUSE' else 'ANY'
    kwargs_drag = {'type': 'LEFTMOUSE', 'value': value_type}
    kwargs_press = {'type': 'LEFTMOUSE', 'value': 'PRESS', 'ctrl': True}
    map_type = [('map_type', mouse_type)] if mouse_type != 'MOUSE' else []

    if mouse_type == 'MOUSE':
        kwargs_drag['direction'] = 'ANY'

    bl_keymap = (
        ('hops.hopstool_helper',
            {'type': 'D', 'value': 'PRESS'},
            {'properties': []},
        ),
        ('hardflow_om.display',
            {'type': 'LEFT_CTRL', 'value': 'PRESS'},
            {'properties': []},
        ),
        ('hardflow_om.display',
            {'type': 'RIGHT_CTRL', 'value': 'PRESS'},
            {'properties': []},
        ),
    )

    return bl_keymap


class Hops(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'
    bl_idname = "Hops"
    bl_label = "HardOps"
    bl_description = f'''HOps: {bl_info['version'][0]}.{bl_info['version'][1]}.{bl_info['version'][2]}.{bl_info['version'][3]}\n
        {bl_info['description']}'''
    bl_icon = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'icons', 'hardops')
    bl_widget = None
    # bl_keymap = '3D View Tool: Hops'
    bl_keymap = keymap()

    def draw_settings(context, layout, tool):
        preference = addon.preference()

        if bpy.app.version[:2] < (3, 0):
            if preference.property.toolshelf == 'MIRROR':
                draw_hopstool_blank(context, layout, tool)
            else:
                draw_hopstool(context, layout, tool)
        else:
            if preference.property.toolshelf == 'MIRROR':
                draw_mirror(context, layout, tool)
            else:
                draw_hopstool(context, layout, tool)


class HopsEdit(bpy.types.WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'EDIT_MESH'
    bl_idname = "Hopsedit"
    bl_label = "HardOps"
    bl_description = f'''HOps: {bl_info['version'][0]}.{bl_info['version'][1]}.{bl_info['version'][2]}.{bl_info['version'][3]}\n
        {bl_info['description']}'''
    bl_icon = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'icons', 'hardops')
    bl_widget = None
    # bl_keymap = '3D View Tool: Hops'
    bl_keymap = keymap()

    def draw_settings(context, layout, tool):
        preference = addon.preference()

        if bpy.app.version[:2] < (3, 0):
            draw_hopstool_blank(context, layout, tool)
        else:
            if preference.property.toolshelf == 'MIRROR':
                draw_mirror(context, layout, tool)
            else:
                draw_hopstool_blank(context, layout, tool)


def draw_hopstool(context, layout, tool):
    if context.region.type not in {'UI', 'WINDOW'}:

        row = layout.row(align=True)

        # Poly Debug
        ico = 'PLAY' if poly_data.running else 'PAUSE'
        row.operator("hops.poly_debug_display", text="", icon=ico)
        row.separator()

        row.popover(panel='HOPS_PT_settings', text='', icon='PREFERENCES')

        layout.separator()

        row = layout.row(align=True)
        row.prop(addon.preference().behavior, "display_gizmo", text="", icon="OBJECT_ORIGIN")
        row.prop(addon.preference().behavior, "display_dots", text="", icon_value=get_icon_id("Display_dots"))
        row.prop(addon.preference().behavior, "display_operators", text="", icon_value=get_icon_id("Display_operators"))
        row.prop(addon.preference().behavior, "display_boolshapes", text="", icon_value=get_icon_id("Display_boolshapes"))

        layout.separator()

        row = layout.row(align=True)
        # row.scale_x = 1.25
        # row.scale_y = 1.25
        if addon.preference().display.display_smartshape:
            if addon.preference().property.accushape_type == 'V2':
                row.operator("hops.accu_shape_v2", text="AccuShape V2", icon_value=get_icon_id("grey"))
            else: 
                row.operator("hops.accu_shape", text="AccuShape", icon_value=get_icon_id("grey"))
            row.operator('hops.add_vertex', text='', icon='DOT')
            row.operator('hops.add_plane', text='', icon='MESH_PLANE')
            row.operator('hops.add_box', text='', icon='MESH_CUBE')
            row.operator('hops.add_bbox', text='', icon='META_CUBE')
            row.menu('HOPS_MT_Tool_grid', text='', icon='MESH_GRID')
            row.operator('hops.add_circle', text='', icon='MESH_CIRCLE')
            row.operator('hops.add_sphere', text='', icon='MESH_UVSPHERE')
            row.operator('hops.add_cylinder', text='', icon='MESH_CYLINDER')
            row.operator('hops.add_cone', text='', icon='MESH_CONE')
            row.operator('hops.add_ring', text='', icon='MESH_TORUS')
            row.operator('hops.add_screw', text='', icon='MOD_SCREW')
            row.operator('hops.add_rope', text='', icon='STROKE')
            row.operator('hops.add_pillow', text='', icon = 'MOD_CLOTH')
        row.popover(panel='HARDFLOW_PT_display_smartshapes', text='')

        box = row.box()
        box.ui_units_x = 3.2 * get_dpi_factor()
        # box.scale_y = 0.5
        box.scale_y = scale(0.5, factor=1 if bpy.app.version < (2, 82, 0) else 2)
        box.label(text='Shapes')

        row.separator()
        row.separator()

        if addon.preference().display.display_modifiers:

            modifier_operators(context, row.row(align=True))

        row.popover(panel='HARDFLOW_PT_display_modifiers', text='')
        box = row.box()
        box.ui_units_x = 3.6 * get_dpi_factor()
        # box.scale_y = 0.5
        box.scale_y = scale(0.5, factor=1 if bpy.app.version < (2, 82, 0) else 2)
        box.label(text='Modifiers')

        row.separator()
        row.separator()
        if addon.preference().display.display_misc:
            row.operator("hops.mirror_gizmo", text="", icon="MOD_MIRROR")
            row.operator("view3d.view_align", text="", icon_value=get_icon_id("HardOps"))

        row.popover(panel='HARDFLOW_PT_display_miscs', text='')
        box = row.box()
        box.ui_units_x = 2.3 * get_dpi_factor()
        # box.scale_y = 0.5
        box.scale_y = scale(0.5, factor=1 if bpy.app.version < (2, 82, 0) else 2)
        box.label(text='Misc')


def draw_hopstool_blank(context, layout, tool):
    layout.label(text='')
