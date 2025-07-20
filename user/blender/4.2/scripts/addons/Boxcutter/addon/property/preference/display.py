import bpy

from bpy.types import PropertyGroup
from bpy.props import StringProperty, BoolProperty, IntProperty, EnumProperty

from . utility import update, label_split, label_row, header, extra_space_prefix
from ... property.utility import names
from ... sound import time_code

from ... operator.shape.utility import tracked_states


def update_shader(self, context):
    tracked_states.shader_batch = True

class bc(PropertyGroup):
    tab: StringProperty(
        name = names['tab'],
        description = '\n Tab to display BoxCutter in',
        update = update.tab,
        default = 'BoxCutter')

    simple_topbar: BoolProperty(
        name = names['simple_topbar'],
        description = '\n Display Topbar in a simpler state',
        update = update.simple_topbar,
        default = True)

    simple_helper: BoolProperty(
        name = names['simple_helper'],
        description = '\n Display Helper in a simpler state',
        default = False)

    override_headers: BoolProperty(
        name = names['override_headers'],
        description = '\n Display custom headers when bc or hops is active (Disable if you experience issues)',
        default = True)

    snap: BoolProperty(
        name = names['snap'],
        description = '\n Display snap options in topbar',
        default = True)

    destructive_menu: BoolProperty(
        name = names['destructive_menu'],
        description = '\n Display menu for destructive behavior in topbar',
        default = True)

    mode_label: BoolProperty(
        name = names['mode_label'],
        description = '\n Display label for mode in topbar',
        default = True)

    shape_label: BoolProperty(
        name = names['shape_label'],
        description = '\n Display label for shape in topbar',
        default = True)

    operation_label: BoolProperty(
        name = names['operation_label'],
        description = '\n Display label for operation in topbar',
        default = True)

    surface_label: BoolProperty(
        name = names['surface_label'],
        description = '\n Display label for surface in topbar',
        default = True)

    snap_label: BoolProperty(
        name = names['snap_label'],
        description = '\n Display label for snap in topbar',
        default = True)

    wire_only: BoolProperty(
        name = names['wire_only'],
        description = '\n Display only wires for shapes',
        update = update_shader,
        default = False)

    wire_width: IntProperty(
        name = names['wire_width'],
        description = '\n Width of drawn wire in pixels (DPI Factored)',
        subtype = 'PIXEL',
        default = 1)

    stipple_width: IntProperty(
        name = names['stipple_width'],
        description = '\n Width of drawn stipple wire in pixels (DPI Factored)',
        subtype = 'PIXEL',
        default = 2)

    thick_wire: BoolProperty(
        name = names['thick_wire'],
        description = '\n Increases the thickness of wires when displaying wires only',
        default = False)

    wire_size_factor: IntProperty(
        name = 'Size Multiplier',
        description = '\n Multiplier for thick wire setting',
        min = 2,
        soft_max = 5,
        default = 2)

    snap_dot_size: IntProperty(
        name = 'Snap Dot Size',
        description = '\n Snap dot size for snapping points',
        subtype = 'PIXEL',
        soft_min = 5,
        soft_max = 50,
        default = 12)

    dots: BoolProperty(
        name = names['dots'],
        description = '\n Display dots manipulator when in lock state',
        default = True)

    dot_size: IntProperty(
        name = 'Dot Size',
        description = '\n Operation dot size',
        subtype = 'PIXEL',
        soft_min = 5,
        soft_max = 50,
        default = 10)

    snap_dot_factor: IntProperty(
        name = 'Detection Size Factor',
        description = '\n Detection Size Factor',
        soft_min = 1,
        soft_max = 20,
        default = 2)

    dot_factor: IntProperty(
        name = 'Detection Size Factor',
        description = '\n Detection Size Factor',
        soft_min = 1,
        soft_max = 20,
        default = 2)

    dot_size_ngon: IntProperty(
        name = 'Dot Size Ngon',
        description = '\n Ngon dot size',
        subtype = 'PIXEL',
        soft_min = 5,
        soft_max = 50,
        default = 6)

    bounds: BoolProperty(
        name = names['bounds'],
        description = '\n Draw the bound box during the modal',
        default = True)

    topbar_pad: BoolProperty(
        name = 'Topbar Padding',
        description = '\n Add space between elements in the topbar',
        default = True)

    pad_menus: BoolProperty(
        name = 'Pad Menus',
        description = '\n Add padding around right most menu elements in the topbar',
        default = True)

    padding: IntProperty(
        name = 'Padding',
        description = '\n Padding amount to use in the topbar\n\n'
                      ' NOTE: If too high for your window the topbar will hide/collapse\n\n'
                      ' Manually enter numbers above 3',
        # min = 1,
        min = 0,
        soft_max = 3,
        default = 0)

    middle_pad: IntProperty(
        name = 'Middle',
        description = '\n Additional center padding amount to use in the topbar\n\n'
                      ' NOTE: If too high for your window the topbar will hide/collapse\n\n'
                      ' Manually enter numbers above 24',
        min = 0,
        soft_max = 24,
        default = 0)

    update_fps: IntProperty(
        name = 'Shader Update FPS',
        description = '\n Update the shader drawn at this frame rate',
        min = 1,
        soft_min = 30,
        soft_max = 120,
        default = 60)

    shape_fade_time_in: IntProperty(
        name = 'Shape',
        description = '\n Amount of time (milliseconds) it takes for the shape to fade in',
        min = 0,
        soft_max = 200,
        default = 0)

    shape_fade_time_out: IntProperty(
        name = 'Shape Exit',
        description = '\n Amount of time (milliseconds) it takes for the shape to fade out',
        min = 0,
        soft_max = 200,
        default = 60)

    shape_fade_time_out_extract: IntProperty(
        name = 'Shape Exit',
        description = '\n Amount of time (milliseconds) it takes for the extracted shape to fade out',
        min = 0,
        soft_max = 2400,
        default = 700)

    dot_fade_time_in: IntProperty(
        name = 'Dot',
        description = '\n Amount of time (milliseconds) it takes for the dot widgets to fade in',
        min = 0,
        soft_max = 200,
        default = 100)

    dot_fade_time_out: IntProperty(
        name = 'Dot Exit',
        description = '\n Amount of time (milliseconds) it takes for the dot widgets to fade out',
        min = 0,
        soft_max = 200,
        default = 100)

    grid_fade_time_in: IntProperty(
        name = 'Grid',
        description = '\n Amount of time (milliseconds) it takes for the grid to fade in',
        min = 1,
        soft_max = 200,
        default = 0)

    grid_fade_time_out: IntProperty(
        name = 'Grid Exit',
        description = '\n Amount of time (milliseconds) it takes for the grid to fade out',
        min = 0,
        soft_max = 200,
        default = 100)

    grid_mode: BoolProperty(
        name = names['grid_mode'],
        description = '\n Change the grid to match the shape mode',
        default = False)

    sound_volume: IntProperty(
        name = 'Sound Volume',
        description = '\n Volume of sound for sound cutting',
        subtype = 'PERCENTAGE',
        min = 0,
        max = 100,
        default = 10)

    show_shape_wire: BoolProperty(
        name = names['show_shape_wire'],
        description = '\n Display wire color change when shape is to be shown',
        default = False)

    statusbar_display: EnumProperty(
        name = 'Statusbar Display',
        description = 'Allows to choose status bar error mesage placement',
        items = [
            ('DEFAULT', 'Default', '', '', 1),
            ('LEFT', 'Left', '', '', 2),
            ('CENTER', 'Center', '', '', 3),
            ('RIGHT', 'Right', '', '', 4),
            ('REMOVE', 'Remove', '', '', 5)],
        default = 'DEFAULT')

    simple_pie: BoolProperty(
        name = 'Simple Pie Menu',
        description = '\n Use a simple pie menu (D-KEY)',
        default = False)

    mirror_gizmo_loc: EnumProperty(
        name = 'Mirro Gizmo Location',
        description = 'Where to draw mirror gizmo',
        items = [
            ('CENTER', 'Center', 'Center of the shape'),
            ('MIRROR_POINT', 'Mirror Point', 'Point relative to which shape is mirrored')],
        default = 'MIRROR_POINT')

def draw(preference, context, layout):
    column = layout.column(align=True)

    # shape
    header(preference, column.box(), 'display_shape')

    if preference.expand.display_shape:
        box_split = column.box().split(align=True, factor=0.5)

        left = box_split.column(align=True)
        label_split(left, 'WireFrame:')

        label_row(preference.display, 'wire_width', left.row(align=True), 'Width')
        label_row(preference.display, 'wire_size_factor', left.row(align=True), 'Size Multiplier')

        left.separator()
        label_row(preference.display, 'wire_only', left.row(), toggle=True)
        label_row(preference.display, 'thick_wire', left.row(), 'Thick Wires', toggle=True)

        right = box_split.column(align=True)
        label_split(right, 'Fade Time (ms):')
        label_row(preference.display, 'shape_fade_time_in', right.row(align=True), label='In')
        label_row(preference.display, 'shape_fade_time_out', right.row(align=True), label='Out')

        if preference.display.shape_fade_time_out in time_code.keys():
            right.separator()
            label_split(right, 'SFX ENABLED!')
            label_row(preference.display, 'sound_volume', right.row(align=True), label='Volume')

            right.separator()

        else:
            right.label(text='')
            right.label(text='')
            right.separator()
            right.separator()

        label_row(preference.display, 'update_fps', right.row(align=True), 'Update FPS')

    # widget
    column.separator()
    header(preference, column.box(), 'display_widget')

    if preference.expand.display_widget:
        box_split = column.box().split(align=True, factor=0.5)

        left = box_split.column(align=True)
        label_split(left, 'Dots:')
        label_row(preference.display, 'dot_size', left.row(align=True), 'Size')
        label_row(preference.display, 'dot_factor', left.row(align=True), 'Hover Factor')

        left.separator()
        label_split(left, 'Fade Time (ms):')
        label_row(preference.display, 'dot_fade_time_in', left.row(align=True), label='In')
        label_row(preference.display, 'dot_fade_time_out', left.row(align=True), label='Out')

        left.separator()
        label_row(preference.display, 'dots', left.row(align=False), 'Use Dots', toggle=True)

        right = box_split.column(align=True)
        label_split(right, 'Snap Dots:')
        label_row(preference.display, 'snap_dot_size', right.row(align=True), 'Size')
        label_row(preference.display, 'snap_dot_factor', right.row(align=True), 'Hover Factor')

        right.separator()
        label_split(right, 'Grid Fade (ms):')
        label_row(preference.display, 'grid_fade_time_in', right.row(align=True), label='In')
        label_row(preference.display, 'grid_fade_time_out', right.row(align=True), label='Out')
        right.separator()

        label_row(preference.display, 'mirror_gizmo_loc', right.row(align=True), label='Mirror Gizmo')

    # tool interface
    column.separator()
    header(preference, column.box(), 'display_tool_interface')

    if preference.expand.display_tool_interface:
        box_split = column.box().split(align=True, factor=0.5)

        left = box_split.column(align=True)
        # left.separator()

        row = left.row()
        row.alignment = 'CENTER'
        row.label(text='Toolbar')

        label_row(preference.display, 'simple_topbar', left.row(), 'Simple', toggle=True)

        left.separator()
        header(preference, left.box(), 'display_tool_interface_decorations')

        if preference.expand.display_tool_interface_decorations:
            box = left.box()
            label_row(preference.display, 'snap', box.row(), 'Snap Options', toggle=True)
            box.separator()
            label_row(preference.display, 'mode_label', box.row(), toggle=True)
            label_row(preference.display, 'shape_label', box.row(), toggle=True)
            label_row(preference.display, 'operation_label', box.row(), toggle=True)
            label_row(preference.display, 'surface_label', box.row(), toggle=True)
            label_row(preference.display, 'snap_label', box.row(), toggle=True)
            box.separator()
            label_row(preference.display, 'destructive_menu', box.row(), toggle=True)

        left.separator()
        label_split(left, 'Padding:')
        if preference.display.topbar_pad:
            label_row(preference.display, 'padding', left.row(align=True), label='Amount')
            label_row(preference.display, 'middle_pad', left.row(align=True), label='Middle')
            left.separator()
            label_row(preference.display, 'pad_menus', left.row(), label='Pad Menus', toggle=True)

        else:
            label_row(preference.display, 'middle_pad', left.row(align=True), label='Middle')
            left.separator()

        label_row(preference.display, 'topbar_pad', left.row(), label='Enabled', toggle=True)

        right = box_split.column(align=True)

        label_row(preference.display, 'override_headers', right.row(), toggle=True)
        right.separator()

        label_row(preference.display, 'simple_pie', right.row(), 'Simple Pie', toggle=True)
        label_row(preference.display, 'simple_helper', right.row(), toggle=True)
        right.separator()

        right.separator()
        label_row(preference.display, 'statusbar_display', right.row(), 'Error Position')
        label_row(preference.keymap, 'enable_toolsettings', right.row(), 'Display Topbar', toggle=True)
        right.separator()

    column.separator()

    split = column.split(align=True, factor=0.5)

    left = split.column(align=True)
    label_row(preference.display, 'tab', left.row(), 'Tab (N-Panel)')

    right = split.column(align=True)
    label_row(preference.behavior, 'use_dpi_factor', right.row(), label='Use DPI Factoring', toggle=True)
