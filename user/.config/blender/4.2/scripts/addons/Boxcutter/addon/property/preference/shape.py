import bpy

from bpy.types import PropertyGroup
from bpy.props import *

from . utility import update, header, label_split, label_row
# from ... import toolbar
from ... operator.shape.utility import change
from ... property.utility import names


def taper_display(option, context):
    if option.taper == 1.0:
        option.taper = 0.75
    else:
        option.taper = 1.0


class bc(PropertyGroup):
    offset: FloatProperty(
        name = names['offset'],
        description = 'Shape offset along z axis',
        update = change.offset,
        precision = 3,
        subtype = 'DISTANCE',
        unit = 'LENGTH',
        default = 0.005)

    lazorcut_limit: FloatProperty(
        name = names['lazorcut_limit'],
        description = '\n How thin the shape must be before triggering a lazorcut cut',
        precision = 3,
        subtype = 'DISTANCE',
        unit = 'LENGTH',
        default = 0.005)

    lazorcut_depth: FloatProperty(
        name = names['lazorcut_depth'],
        description = 'Extent to extend the cutters depth when using Accucut (Behavior) Lazorcut',
        precision = 3,
        min = 0,
        subtype = 'DISTANCE',
        unit = 'LENGTH',
        default = 0.0)

    auto_depth: BoolProperty(
        name = names['auto_depth'],
        description = '\n Automatically extrude to a depth',
        default = False)

    auto_depth_large: BoolProperty(
        name = names['auto_depth_large'],
        description = '\n Choose a larger depth (Auto Depth)',
        default = False)

    auto_depth_custom_proportions: BoolProperty(
        name = names['auto_depth_custom_proportions'],
        description = '\n Constrain to proportions of Custom shape by default. (Auto Depth)',
        default = False)

    auto_depth_multiplier: FloatProperty(
        name = names['auto_depth_multiplier'],
        description = '\n Depth multiplier. (Auto Depth)',
        min = 0,
        default = 1)

    circle_vertices: IntProperty(
        name = names['circle_vertices'],
        description = '\n Vertex Count',
        update = change.circle_vertices,
        min = 1,
        max = 512,
        soft_max = 64,
        default = 32)

    circle_diameter: FloatProperty(
        name = names['circle_diameter'],
        description = 'Set diameter of currently drawn circle',
        update = change.circle_diameter,
        subtype = 'DISTANCE',
        min = 0.0001,
        default = 0.0001)

    circle_type: EnumProperty(
        name = 'Type',
        description = '\n Circle type \n Modifier - Default (bevels base of shape) \n Polygon - Allows for bevelling edges instead of base \n Star - Creates a star in place of surface. Adjustable factor available \n',
        items = [
            ('POLYGON', 'Polygon', 'Static Mesh Circle'),
            ('MODIFIER', 'Modifier', 'Screw Modifier Circle'),
            ('STAR', 'Star', 'Static Mesh Star')],
        default = 'POLYGON')

    circle_star_factor: FloatProperty(
        name = 'Factor',
        description = '\n Star factor',
        update = change.circle_vertices,
        min = 0,
        max = 1,
        default = 0.5)

    dimension_x: FloatProperty(
        name = names['dimension_x'],
        description = 'Set X dimension of currently drawn shape',
        update = change.dimensions_xy,
        subtype = 'DISTANCE',
        min = 0.0001,
        default = 0.0001)

    dimension_y: FloatProperty(
        name = names['dimension_y'],
        description = 'Set Y dimension of currently drawn shape',
        update = change.dimensions_xy,
        subtype = 'DISTANCE',
        min = 0.0001,
        default = 0.0001)

    dimension_z: FloatProperty(
        name = names['dimension_z'],
        description = 'Set Z dimension of currently drawn shape',
        update = change.dimension_z,
        subtype = 'DISTANCE',
        min = 0.0001,
        default = 0.0001)

    inset_thickness: FloatProperty(
        name = names['inset_thickness'],
        description = '\n Shape inset thickness (or inset bevel width)',
        update = change.inset_thickness,
        precision = 4,
        subtype = 'DISTANCE',
        unit = 'LENGTH',
        default = 0.02)

    solidify_thickness: FloatProperty(
        name = names['solidify_thickness'],
        description = '\n Shape solidify thickness',
        update = change.solidify_thickness,
        subtype = 'DISTANCE',
        unit = 'LENGTH',
        precision = 4,
        default = 0.01)

    solidify_offset: FloatProperty(
        name = names['solidify_offset'],
        description = '\n Shape solidify offset',
        update = change.solidify_offset,
        subtype = 'DISTANCE',
        unit = 'LENGTH',
        precision = 4,
        default = 0.0)

    bevel_width: FloatProperty(
        name = names['bevel_width'],
        description = '\n Bevel width',
        update = change.bevel_width,
        subtype = 'DISTANCE',
        unit = 'LENGTH',
        min = 0,
        precision = 3,
        default = 0.02)

    bevel_segments: IntProperty(
        name = names['bevel_segments'],
        description = '\n Bevel segments',
        update = change.bevel_segments,
        min = 1,
        soft_max = 20,
        max = 100,
        default = 6)

    bevel_segments_default: IntProperty(
        name = names['bevel_segments'],
        description = '\n Bevel segments default value',
        # update = change.bevel_segments, # TODO: exec set bevel segments
        min = 1,
        soft_max = 20,
        max = 100,
        default = 6)

    bevel_both: BoolProperty(
        name = names['bevel_both'],
        description = '\n Bevel bottom edge using weights when using front face bevel',
        update = change.bevel_both,
        default = False)

    quad_bevel: BoolProperty(
        name = names['quad_bevel'],
        description = '\n Use two bevel modifiers to achieve better corner topology',
        update = change.quad_bevel,
        default = True)

    quad_bevel_segments: IntProperty(
        name = names['bevel_segments'],
        description = '\n Bevel segments',
        #update = change.bevel_segments,
        min = 1,
        soft_max = 20,
        max = 100,
        default = 6)

    quad_bevel_width: FloatProperty(
        name = names['bevel_width'],
        description = '\n Bevel width',
        update = change.quad_bevel_width,
        subtype = 'DISTANCE',
        unit = 'LENGTH',
        min = 0,
        precision = 3,
        default = 0.02)

    front_bevel_width: FloatProperty(
        name = names['bevel_width'],
        description = '\n Bevel width',
        update = change.bevel_width,
        subtype = 'DISTANCE',
        unit = 'LENGTH',
        min = 0,
        precision = 3,
        default = 0.02)

    front_bevel_segments: IntProperty(
        name = names['bevel_segments'],
        description = '\n Bevel segments',
        #update = change.bevel_segments,
        min = 1,
        soft_max = 20,
        max = 100,
        default = 6)

    straight_edges: BoolProperty(
        name = names['straight_edges'],
        description = '\n Use a series of bevel modifiers to provide straight edge flow in corners',
        update = change.straight_edges,
        default = False)

    rotate_axis: EnumProperty(
        name = names['rotate_axis'],
        description = 'Default Axis',
        items = [
            ('X', 'X', '\n X axis'),
            ('Y', 'Y', '\n Y axis'),
            ('Z', 'Z', '\n Z axis')],
        default = 'Z')

    mirror_axis: BoolVectorProperty(
        name = names['mirror_axis'],
        description = 'Mirror Axis',
        update = change.mirror_axis,
        size = 3,
        default = (True, False, False))

    mirror_bisect_axis: BoolVectorProperty(
        name = names['mirror_bisect_axis'],
        description = 'Mirror Bisect Axis',
        update = change.mirror_bisect_axis,
        size = 3,
        default = (False, False, False))

    mirror_flip_axis: BoolVectorProperty(
        name = names['mirror_flip_axis'],
        description = 'Mirror Flip Axis',
        update = change.mirror_flip_axis,
        size = 3,
        default = (False, False, False))

    mirror_gizmo: BoolProperty(
        name = 'Mirror Gizmo',
        description = 'Mirror Gizmo',
        update = change.mirror_gizmo,
        default = False)

    array_axis: EnumProperty(
        name = names['array_axis'],
        description = 'Array Axis',
        update = change.array_axis,
        items = [
            ('X', 'X', '\n X axis'),
            ('Y', 'Y', '\n Y axis'),
            ('Z', 'Z', '\n Z axis')],
        default = 'X')

    array_distance: FloatProperty(
        name = names['array_distance'],
        description = '\n Array count',
        update = change.array_distance,
        default = 0.0)

    array_count: IntProperty(
        name = names['array_count'],
        description = '\n Array count',
        update = change.array_count,
        min = 1,
        soft_max = 32,
        default = 2)

    array_around_cursor: BoolProperty(
        name = names['array_around_cursor'],
        description = '\n Use the 3D Cursor when Circle Arraying',
        default = False)

    cycle_all: BoolProperty(
        name = names['cycle_all'],
        description = '\n Do not skip cutters available in the collection when cycling',
        default = True)

    cycle_dimensions: BoolProperty(
        name = names['cycle_dimensions'],
        description = '\n Modify drawn shape to match dimensions of recalled shape',
        default = False)

    wedge: BoolProperty(
        name = names['wedge'],
        description = '\n Wedge the shape',
        update = change.wedge,
        default = False)

    wedge_lazorcut: BoolProperty(
        name = names['wedge'],
        description = '\n Set lazorcut to proportional wedge',
        default = False)

    cyclic: BoolProperty(
        name = 'Cyclic',
        description = '\n Connect the final point of the NGon with the first point',
        default = True)

    lasso: BoolProperty(
        name = 'Lasso',
        description = '\n Allow lasso draw mode',
        default = False)

    lasso_spacing: FloatProperty(
        name = 'Lasso Spacing',
        description = '\n Set Spacing value for points during lasso draw',
        min = 0,
        subtype = 'DISTANCE',
        default = 0.07)

    wedge_side: EnumProperty(
        name = 'Wedge Side',
        description = 'Wedge Side',
        items = [
            ('X+', '+X', '\n +X axis'),
            ('X-', '- X', '\n - X axis'),
            ('Y+', '+Y', '\n +Y axis'),
            ('Y-', '- Y', '\n - Y axis')],
        default = 'X+')

    lasso_adaptive: BoolProperty(
        name = 'Adaptive',
        description = '\n Calculate spacing relative to visible 3d area',
        default = True)

    taper_display: BoolProperty(
        name = 'Taper',
        description = '\n Taper Shape',
        update = taper_display,
        default = False)

    taper: FloatProperty(
        name = 'Taper',
        description = '\n Taper Amount',
        update = change.taper,
        min = 0.0,
        soft_max = 2.0,
        default = 1.0)

    box_grid: BoolProperty(
        name = 'Grid',
        description = 'Use grid',
        update = change.box_grid,
        default = False)

    box_grid_border: BoolProperty(
        name = 'Border',
        description = 'Border Faces',
        update = change.box_grid,
        default = True)

    box_grid_divisions: IntVectorProperty(
        name = 'Divisions',
        description = 'X and Y divisions',
        subtype = 'XYZ',
        size = 2,
        min = 0,
        update = change.box_grid,
        default = (5, 5))

    box_grid_auto_solidify: BoolProperty(
        name = 'Auto Solidify',
        description = 'Automatically add Solidify mod when drawing. Excludes Knife',
        default = True)

    box_grid_fill_back: BoolProperty(
        name = 'Fill Back Faces',
        description = 'Fill back faces for creating floating geometry',
        update = change.box_grid,
        default = False)

    wedge_factor: FloatProperty(
        name = 'Wedge Factor',
        description = '\n A relative position of the wedge between sides',
        update = change.wedge,
        min = 0,
        max = 1,
        default = 1)

    wedge_width: FloatProperty(
        name = 'Wedge Width',
        description = '\n A relative scale of the wedge edge',
        update = change.wedge,
        min = 0,
        default = 1)

    displace: FloatProperty(
        name = 'Displacement',
        description = '\n Displacement Strength',
        default = 0)

    auto_flip_xy: BoolProperty(
        name = 'Auto Flip Draw',
        description = 'Automatically flip shape on X,Y, or both when intersecting shape origin during draw',
        default = True)

    auto_proportions: BoolProperty(
        name = 'Auto Proportions',
        description = '\n Automatically constrain draw to propotions of Custom cutter',
        default = True)

    rotation_by_90: BoolProperty(
        name = 'Persistent Rotation (Inside)',
        description = '\n Keeps inside rotation between uses',
        default = False)


def draw(preference, context, layout):
    column = layout.column(align=True)

    # transforms
    header(preference, column.box(), 'shape_transforms')

    if preference.expand.shape_transforms:
        box_split = column.box().split(align=True, factor=0.5)

        left = box_split.column(align=True)
        label_row(preference.shape, 'offset', left.row(align=True))
        label_row(preference.shape, 'lazorcut_limit', left.row(align=True))

        left.separator()
        label_row(preference.shape, 'rotation_by_90', left.row(align=True), label='Persistent Rotation (Inside)')
        label_row(preference.shape, 'auto_flip_xy', left.row(), 'Auto Flip on Draw', toggle=True)
        # label_row(preference.shape, 'array_around_cursor', left.row(), toggle=True)

        right = box_split.column(align=True)
        label_row(preference.shape, 'rotate_axis', right.row(align=True))

    # geometry
    column.separator()
    header(preference, column.box(), 'shape_geometry')

    if preference.expand.shape_geometry:
        box_split = column.box().split(align=True, factor=0.5)

        left = box_split.column(align=True)
        label_split(left, 'Solidify:')
        label_row(preference.shape, 'inset_thickness', left.row(align=True), label='Thickness')
        label_row(preference.shape, 'solidify_thickness', left.row(align=True), label='Inset')

        left.separator()

        label_split(left, 'Array:')
        label_row(preference.shape, 'array_count', left.row(align=True), label='Count')
        label_row(preference.shape, 'array_axis', left.row(align=True), label='Axis')

        left.label(text='')
        left.separator()
        label_row(preference.shape, 'circle_vertices', left.row(align=True))

        left.label(text='')
        label_row(preference.shape, 'taper', left.row(align=True))
        label_row(preference.behavior, 'persistent_taper', left.row(), toggle=True)
        #label_row(preference.behavior, 'keep_lattice_taper', left.row(), toggle=True)

        right = box_split.column(align=True)
        label_split(right, 'Bevel:')
        label_row(preference.shape, 'bevel_width', right.row(align=True), label='Width')
        label_row(preference.shape, 'bevel_segments_default', right.row(align=True), label='Segments')

        if preference.shape.quad_bevel:
            right.separator()
            label_row(preference.shape, 'quad_bevel_width', right.row(align=True), label='Quad Width')
            label_row(preference.shape, 'quad_bevel_segments', right.row(align=True), label='Quad Segments')

        right.separator()
        # label_row(preference.shape, 'straight_edges', right.row(), toggle=True)
        label_row(preference.shape, 'quad_bevel', right.row(), toggle=True)

        label_split(right, 'Lasso:')
        label_row(preference.shape, 'lasso_spacing', right.row(align=True), label='Spacing')
        label_row(preference.shape, 'cyclic', right.row(), label='Cyclic', toggle=True)
        label_row(preference.shape, 'lasso', right.row(), label='Lasso', toggle=True)

    column.separator()
    split = column.split(align=True, factor=0.5)

    left =  split.column(align=True)
    label_row(preference.shape, 'cycle_all', left.row(), 'Cycle All Cutters', toggle=True)

    right =  split.column(align=True)
    #label_row(preference.shape, 'auto_flip_xy', right.row(), 'Auto Flip on Draw', toggle=True)

