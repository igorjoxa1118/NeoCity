import os

import bpy

from bpy.types import WorkSpaceTool

from bpy.utils import register_class, unregister_class
from bpy.utils.toolsystem import ToolDef

from bl_ui import space_view3d
from bl_ui.space_toolsystem_toolbar import VIEW3D_PT_tools_active as view3d_tools

from . import icon, operator
from .. utility import method_handler, addon, screen, tool
from .. import bl_info

normaltoolbar = None
tool_header = space_view3d.VIEW3D_HT_tool_header
operator_id = 'bc.shape_draw'
label = 'BoxCutter'

version = '.'.join(str(bl_info['version'])[1:-1].replace(' ', '').replace("'", '').replace('"', '').split(','))
version_name = bl_info['description'].split(' ')[-1]
description = F'BC: {version}\n\n{" " * 8}{bl_info["description"]}'


def option():
    return tool.option(addon.name, operator_id)


def change_prop(context, prop, value):
    for tooldef in context.workspace.tools:
        if not tooldef:
            continue

        if tooldef.idname == tool.active().idname:
            setattr(option(), prop, value)

    context.workspace.tools.update()

keep = True
def change_mode_behavior(op, context):
    global keep

    preference = addon.preference()
    bc = context.scene.bc

    if not bc.running:
        if op.shape_type == 'BOX':
            change_prop(context, 'origin', op.origin if keep else 'CORNER')
            keep = True

            return

        elif op.shape_type == 'CIRCLE':
            change_prop(context, 'origin', 'CENTER')

        elif op.shape_type == 'NGON':
            change_prop(context, 'origin', 'CORNER')

        elif op.shape_type == 'CUSTOM':
            #bc.collection = bc.stored_collection
            bc.shape = bc.stored_shape

        keep = False


def change_mode(op, context):
    bc = context.scene.bc

    if not bc.running:
        # if op.mode == 'KNIFE':
        #     change_prop(context, 'shape_type', 'BOX')
        #     change_mode_behavior(op, context)

        if op.mode == 'EXTRACT':
            change_prop(context, 'shape_type', 'BOX')
            change_mode_behavior(op, context)

    elif op.mode == 'MAKE' and bc.shape and bc.shape.display_type != 'TEXTURED':
        bc.shape.display_type = 'TEXTURED'

    elif op.mode != 'MAKE' and op.shape_type != 'CUSTOM' and bc.shape and bc.shape.display_type != 'WIRE':
        bc.shape.display_type = 'WIRE'


def update_operator(op, context):
    for tooldef in context.workspace.tools:
        if tooldef.idname == tool.active().idname and tooldef.mode == tool.active().mode:
            prop = tooldef.operator_properties(operator_id)

            op.tool = tooldef
            op.mode = prop.mode
            op.shape_type = prop.shape_type
            op.operation = prop.operation
            op.behavior = prop.behavior
            # bc.axis = prop.axis
            op.origin = prop.origin
            op.align_to_view = prop.align_to_view
            op.live = prop.live
            op.active_only = prop.active_only

            return True

    return False


def ui_scale(value, factor=1):
    return value * factor


def add():
    global normaltoolbar

    if not normaltoolbar:
        normaltoolbar = tool_header.draw

    tool_header.draw = draw_handler


def remove():
    tool_header.draw = normaltoolbar


def draw_handler(hd, context):
    preference = addon.preference()

    if bpy.app.version[:2] >= (3, 0) or not preference.display.override_headers or tool.active().idname not in {tool.name, 'Hops'}:
        return normaltoolbar(hd, context)

    method_handler(draw,
        arguments = (hd, context),
        identifier = 'Toolbar',
        exit_method = remove)


def draw(hd, context):
    layout = hd.layout

    layout.row(align=True).template_header()

    hd.draw_tool_settings(context)

    layout.separator_spacer()

    hd.draw_mode_settings(context)


def keymap():
    mouse_type = 'MOUSE' if bpy.app.version[:2] > (3, 1) else 'TWEAK'
    value_type = 'CLICK_DRAG' if mouse_type == 'MOUSE' else 'ANY'
    kwargs_drag = {'type': 'LEFTMOUSE', 'value': value_type}
    kwargs_press = {'type': 'LEFTMOUSE', 'value': 'PRESS', 'ctrl': True}
    map_type = [('map_type', mouse_type)] if mouse_type != 'MOUSE' else []

    if mouse_type == 'MOUSE':
        kwargs_drag['direction'] = 'ANY'

    bl_keymap = (
        ('wm.call_menu_pie',
            {'type': 'D', 'value': 'PRESS'},
            {'properties': [('name', 'BC_MT_pie')]},
        ),
        ('wm.call_panel',
            {'type': 'V', 'value': 'PRESS', 'shift': True},
            {'properties': [('name', 'BC_PT_surface')]},
        ),
        ('bc.helper',
            {'type': 'D', 'value': 'PRESS', 'ctrl': True},
            {'properties': []},
        ),
        ('bc.shape_draw',
            {**kwargs_drag},
            {'properties': map_type},
        ),
        ('bc.shape_draw',
            {**kwargs_drag, 'alt': True},
            {'properties': map_type},
        ),
        ('bc.shape_draw',
            {**kwargs_drag, 'shift': True},
            {'properties': map_type},
        ),
        ('bc.shape_draw',
            {**kwargs_drag, 'alt': True, 'shift': True},
            {'properties': map_type},
        ),
        ('bc.shape_draw',
            {**kwargs_press},
            {'properties': []},
        ),
        ('bc.shape_draw',
            {**kwargs_press, 'shift': True},
            {'properties': []},
        ),
        ('bc.shape_snap',
            {'type': 'LEFT_CTRL', 'value': 'PRESS'},
            {'properties': []},
        ),
        ('bc.shape_snap',
            {'type': 'RIGHT_CTRL', 'value': 'PRESS'},
            {'properties': []},
        ),
        ('bc.custom',
            {'type': 'C', 'value': 'PRESS'},
            {'properties': [('set', True)]},
        ),
        ('bc.subtype_scroll', # kmi.active = addon.preference().keymap.alt_scroll_shape_type
            {'type': 'WHEELUPMOUSE', 'value': 'PRESS', 'alt': True},
            {'properties': [('direction', 'UP')]},
        ),
        ('bc.subtype_scroll', # kmi.active = addon.preference().keymap.alt_scroll_shape_type
            {'type': 'WHEELDOWNMOUSE', 'value': 'PRESS', 'alt': True},
            {'properties': [('direction', 'DOWN')]},
        ),
        ('bc.subtype_scroll', # kmi.active = addon.preference().keymap.alt_scroll_shape_type
            {'type': 'UP_ARROW', 'value': 'PRESS', 'alt': True},
            {'properties': [('direction', 'UP')]},
        ),
        ('bc.subtype_scroll', # kmi.active = addon.preference().keymap.alt_scroll_shape_type
            {'type': 'DOWN_ARROW', 'value': 'PRESS', 'alt': True},
            {'properties': [('direction', 'DOWN')]},
        ),
    )

    return bl_keymap


class BC_WT_object(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'
    bl_idname = addon.name
    bl_description = description
    bl_label = label
    bl_icon = os.path.join(os.path.dirname(__file__), '.', 'icon', 'boxcutter')
    # bl_keymap = '3D View Tool: BoxCutter'
    bl_keymap = keymap()

    def draw_settings(context, layout, tool):
        bc = context.scene.bc
        preference = addon.preference()
        op = option()

        if context.region.type not in {'UI', 'WINDOW'}:
            icons = {
                'CUT': icon.id('red'),
                'SLICE': icon.id('yellow'),
                'INTERSECT': icon.id('orange'),
                'INSET': icon.id('purple'),
                'JOIN': icon.id('green'),
                'KNIFE': icon.id('blue'),
                'EXTRACT': icon.id('black'),
                'MAKE': icon.id('grey')}

            row = layout.row(align=True)

            if not preference.display.simple_topbar:
                row.prop(op, 'mode', text='', expand=True, icon_only=True)

            row.popover(panel='BC_PT_helper', text='', icon_value=icons[op.mode])
            # row.popover(panel='BC_PT_mode', text='', icon_value=icons[op.mode])

            if preference.display.mode_label:
                box = row.box()
                box.ui_units_x = 2.9
                box.scale_y = ui_scale(0.5, factor=1 if bpy.app.version[:2] < (2, 82) else 2)
                box.alert = bool(hasattr(bc.operator, 'last') and bc.operator.last and op.mode != bc.operator.last['mode'])
                box.label(text=F' {op.mode.title()}')

            if preference.display.simple_topbar:
                row.prop(op, 'knife', text='', icon_value=icon.id('blue'))

            if preference.display.topbar_pad:
                for _ in range(preference.display.padding):
                    layout.separator()

            icons = {
                'BOX': 'MESH_PLANE',
                'CIRCLE': 'MESH_CIRCLE',
                'NGON': 'MOD_SIMPLIFY',
                'CUSTOM': 'FILE_NEW'}

            row = layout.row(align=True)

            if not preference.display.simple_topbar:
                row.prop(op, 'shape_type', expand=True, text='')

            row.popover(panel='BC_PT_shape', text='', icon=icons[op.shape_type])

            if preference.display.shape_label:
                box = row.box()
                box.ui_units_x = 3.8
                box.scale_y = ui_scale(0.5, factor=1 if bpy.app.version[:2] < (2, 82) else 2)
                shape_type = op.shape_type

                if shape_type == 'BOX' and preference.shape.box_grid:
                    shape_type = 'Grid'

                prefix = 'Wedge' if preference.shape.wedge else 'Line'
                if shape_type != 'NGON' and preference.behavior.draw_line or shape_type == 'NGON' and not preference.shape.cyclic and not preference.shape.lasso:

                    if shape_type == 'NGON' and prefix == 'Line':
                        box.label(text=F' Ngon (Line)')

                    elif prefix != 'Wedge':
                        box.label(text=F' {prefix} {shape_type.title()}')

                    else:
                        box.label(text=F' Wedge {shape_type.title()}')

                elif shape_type == 'NGON' and preference.shape.lasso:
                    box.label(text=F'{prefix if preference.shape.wedge else ""} Lasso{" (Line)" if not preference.shape.cyclic else ""}')

                elif shape_type == 'CIRCLE':
                    if preference.shape.circle_type == 'STAR':
                        box.label(text=F'{prefix if preference.shape.wedge else ""} {preference.shape.circle_type.title()} ({preference.shape.circle_vertices})')
                    else:
                        box.label(text=F'{prefix if preference.shape.wedge else ""} {shape_type.title()} ({preference.shape.circle_vertices})')

                else:
                    box.label(text=F'{prefix if preference.shape.wedge else ""} {shape_type.title()}')

            # if preference.display.simple_topbar:
            if op.shape_type in {'BOX', 'CIRCLE', 'CUSTOM'}:
                if op.shape_type == 'BOX' and not preference.display.simple_topbar:
                    row.prop(preference.shape, 'box_grid', text='', icon='MESH_GRID')

                row.prop(preference.behavior, 'draw_line', text='', icon='DRIVER_DISTANCE')

            elif op.shape_type == 'NGON':
                sub = row.row(align=True)
                sub.enabled = not bc.running #TODO: Fix in modal toggle (update func?)
                sub.prop(preference.shape, 'cyclic', text='', icon=F'RESTRICT_INSTANCED_O{"FF" if preference.shape.cyclic else "N"}')

            icons = {
                'MOUSE': 'RESTRICT_SELECT_OFF',
                'CENTER': 'SNAP_FACE_CENTER',
                'BBOX': 'PIVOT_BOUNDBOX',
                'ACTIVE': 'PIVOT_ACTIVE'}

            row.popover(panel='BC_PT_set_origin', text='', icon=icons[preference.behavior.set_origin])

            if preference.display.topbar_pad:
                for _ in range(preference.display.padding):
                    layout.separator()

            row = layout.row(align=True)

            if not preference.display.simple_topbar:
                row.prop(bc, 'start_operation', expand=True, icon_only=True)

            icons = {
                'NONE': 'LOCKED',
                'DRAW': 'GREASEPENCIL',
                'EXTRUDE': 'ORIENTATION_NORMAL',
                'OFFSET': 'MOD_OFFSET',
                'MOVE': 'RESTRICT_SELECT_ON',
                'ROTATE': 'DRIVER_ROTATIONAL_DIFFERENCE',
                'SCALE': 'FULLSCREEN_EXIT',
                'ARRAY': 'MOD_ARRAY',
                'SOLIDIFY': 'MOD_SOLIDIFY',
                'BEVEL': 'MOD_BEVEL',
                'DISPLACE': 'MOD_DISPLACE',
                'MIRROR': 'MOD_MIRROR',
                'TAPER': 'FULLSCREEN_ENTER',
                'GRID': 'MOD_LATTICE'}

            row.popover(panel='BC_PT_operation', text='', icon=icons[op.operation])

            if preference.display.operation_label:
                box = row.box()
                box.ui_units_x = 3.5
                box.scale_y = ui_scale(0.5, factor=1 if bpy.app.version[:2] < (2, 82) else 2)
                lock_label = 'Locked' if bc.running else 'Default'
                box.label(text=F' {op.operation.title()}' if op.operation != 'NONE' else F' {lock_label}')

            row.prop(preference.keymap, 'release_lock', text='', icon=F'RESTRICT_SELECT_O{"FF" if preference.keymap.release_lock else "N"}')

            icons = {
                'OBJECT': 'OBJECT_DATA',
                'VIEW': 'LOCKVIEW_ON',
                'CURSOR': 'PIVOT_CURSOR',
                'WORLD': 'WORLD'}

            if preference.display.topbar_pad:
                for _ in range(preference.display.padding):
                    layout.separator()

            row = layout.row(align=True)

            if not preference.display.simple_topbar:
                row.prop(preference, 'surface', expand=True, text='')

            row.popover(panel='BC_PT_surface', text='', icon=icons[preference.surface])

            if preference.display.surface_label:
                box = row.box()
                box.ui_units_x = 3.25
                box.scale_y = ui_scale(0.5, factor=1 if bpy.app.version[:2] < (2, 82) else 2)

                box.alert = bool((hasattr(bc.operator, 'last') and preference.surface != bc.operator.last['surface']) or bc.snap_type and bc.snap_type != preference.surface)
                box.label(text=F' {preference.surface.title() if not bc.snap_type else bc.snap_type.title()}')

            row.prop(op, 'align_to_view', text='', icon='LOCKVIEW_ON')

            for _ in range(preference.display.middle_pad):
                layout.separator()

            if preference.display.snap:
                # layout.separator()

                row = layout.row(align=True)
                row.prop(preference.snap, 'enable', text='', icon=F'SNAP_O{"N" if preference.snap.enable else "FF"}')
                sub = row.row(align=True)
                sub.active = preference.snap.enable
                sub.alert = bool(preference.snap.grid and preference.snap.increment_lock and bc.snap.operator and (bc.snap.operator.handler.grid.display if hasattr(bc.snap.operator, 'handler') else bc.snap.operator.snap.grid_active))
                sub.prop(preference.snap, 'grid', text='', icon='SNAP_GRID')

                if not preference.display.simple_topbar:
                    row.prop(preference.snap, 'verts', text='', icon='VERTEXSEL')
                    row.prop(preference.snap, 'edges', text='', icon='EDGESEL')
                    row.prop(preference.snap, 'faces', text='', icon='FACESEL')

                row.popover('BC_PT_snap', text='', icon='SNAP_INCREMENT')

                if preference.display.snap_label:
                    snap = [preference.snap.verts, preference.snap.edges, preference.snap.faces]
                    snap_sub_labels = ['Verts', 'Edges', 'Faces']
                    snap_type = "" if snap.count(True) > 1 or True not in snap else snap_sub_labels[snap.index(True)]

                    box = row.box()
                    box.ui_units_x = 3.8
                    box.scale_y = ui_scale(0.5, factor=1 if bpy.app.version[:2] < (2, 82) else 2)

                    if not preference.snap.enable:
                        box.label(text=' Disabled')

                    elif preference.snap.grid:
                        box.label(text=F' {"Static " if preference.snap.static_grid else ""}Grid {snap_type}')

                    elif True in snap:
                        box.label(text=F' {"Static " if preference.snap.static_dot else ""}Dot{" " + snap_type[:-1] if snap_type and not preference.snap.static_dot else ""}s')

                    elif preference.snap.incremental:
                        box.label(text=F' Increment')

                    else:
                        box.label(text=F' None')

                row.prop(preference.snap, 'increment_lock', text='', icon=F'{"" if preference.snap.increment_lock else "UN"}LOCKED')

            if preference.display.topbar_pad and preference.display.pad_menus:
                padding = preference.display.padding

                if not preference.display.destructive_menu:
                    padding = 0

                for _ in range(padding):
                    layout.separator()

            if preference.display.destructive_menu:
                row = layout.row(align=True)
                sub = row.row(align=True)
                if bpy.app.version[:2] < (2, 91):
                    sub.active = tool.active().mode == 'OBJECT'
                sub.prop(op, 'behavior', text='')
                sub = row.row(align=True)
                ot = sub.operator('bc.smart_apply', text='', icon='IMPORT')
                ot.use_loose = True


            if preference.display.topbar_pad and preference.display.pad_menus:
                for _ in range(preference.display.padding):
                    layout.separator()

            row = layout.row(align=True)
            row.popover(panel='BC_PT_settings', text='', icon='PREFERENCES')
            row.prop(op, 'live', text='', icon='PLAY' if not op.live else 'PAUSE')

            layout.separator()

            layout.operator('bc.help_link', text='', icon='QUESTION', emboss=False)

            layout.separator()

            row = layout.row()
            from .. utility import handled_error
            row.alert = handled_error
            row.label(text=version)

            if handled_error:
                sub = row.row()
                sub.alert = False
                sub.operator('bc.error_log', text='', icon='ERROR', emboss=False)


class BC_WT_edit(BC_WT_object):
    bl_context_mode = 'EDIT_MESH'


classes = (
    BC_WT_object,
    BC_WT_edit,
)


def register():
    mode_class = zip(('OBJECT', 'EDIT_MESH'), classes)

    for mode, cls in mode_class:
        after = 'Hopsedit' if addon.hops() else None
        bpy.utils.register_tool(cls, after=after, separator=not after, group=False)


def unregister():
    for cls in classes:
        bpy.utils.unregister_tool(cls)

