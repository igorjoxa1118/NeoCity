import bpy

from bpy.types import PropertyGroup
from bpy.props import *

from . utility import label_row, header, extra_space_prefix
from ... property.utility import names


def update_collection(color, context):
    bc = context.scene.bc

    if bc.collection and hasattr(bc.collection, 'color_tag'):
        bc.collection.color_tag = color.collection


class bc(PropertyGroup):
    cut: FloatVectorProperty(
        name = names['cut'],
        description = '\n Color of the shape when cutting',
        size = 4,
        min = 0,
        max = 1,
        subtype='COLOR',
        # default = (0.604, 0.064, 0.064, 0.1))
        default = (0.448, 0.147, 0.147, 0.4))

    slice: FloatVectorProperty(
        name = names['slice'],
        description = '\n Color of the shape when slicing',
        size = 4,
        min = 0,
        max = 1,
        subtype='COLOR',
        # default = (0.604, 0.422, 0.064, 0.1))
        default = (0.604, 0.557, 0.228, 0.5))

    intersect: FloatVectorProperty(
        name = names['intersect'],
        description = '\n Color of the shape when intersecting',
        size = 4,
        min = 0,
        max = 1,
        subtype='COLOR',
        # default = (0.236, 0.064, 0.604, 0.1))
        default = (0.593, 0.321, 0.158, 0.6))

    inset: FloatVectorProperty(
        name = names['inset'],
        description = '\n Color of the shape when insetting',
        size = 4,
        min = 0,
        max = 1,
        subtype='COLOR',
        # default = (0.236, 0.064, 0.604, 0.1))
        default = (0.391, 0.223, 0.692, 0.5))

    join: FloatVectorProperty(
        name = names['join'],
        description = '\n Color of the shape when joining',
        size = 4,
        min = 0,
        max = 1,
        subtype='COLOR',
        # default = (0.217, 0.604, 0.064, 0.1))
        default = (0.286, 0.604, 0.133, 0.4))

    make: FloatVectorProperty(
        name = names['make'],
        description = '\n Color of the shape when making',
        size = 4,
        min = 0,
        max = 1,
        subtype='COLOR',
        # default = (0.604, 0.604, 0.604, 0.1))
        default = (0.604, 0.604, 0.604, 0.5))

    knife: FloatVectorProperty(
        name = names['knife'],
        description = '\n Color of the shape when using knife',
        size = 4,
        min = 0,
        max = 1,
        subtype='COLOR',
        # default = (0.29, 0.52, 1.0, 0.1))
        default = (0.238, 0.411, 0.787, 0.4))

    extract: FloatVectorProperty(
        name = names['extract'],
        description = '\n Color of the shape when extracting',
        size = 4,
        min = 0,
        max = 1,
        subtype='COLOR',
        default = (0.033, 0.033, 0.033, 0.3))

    extract_fade: FloatVectorProperty(
        name = names['extract_fade'],
        description = '\n Color of the extracted shape during fade',
        size = 4,
        min = 0,
        max = 1,
        subtype='COLOR',
        default = (0.926, 0.752, 0.310, 0.471))

    negative: FloatVectorProperty(
        name = names['negative'],
        description = '\n Color of the shape when behind a mesh object',
        size = 4,
        min = 0,
        max = 1,
        subtype='COLOR',
        default = (0.214, 0.214, 0.214, 0.1))

    # bbox: FloatVectorProperty(
    #     name = names['bbox'],
    #     description = '\n Color of the shapes bound region',
    #     size = 4,
    #     min = 0,
    #     max = 1,
    #     subtype='COLOR',
    #     default = (0.1, 0.1, 0.1, 0.033))

    wire: FloatVectorProperty(
        name = names['wire'],
        description = '\n Color of the shape\'s wire',
        size = 4,
        min = 0,
        max = 1,
        subtype='COLOR',
        default = (0.0, 0.0, 0.0, 0.5))

    wire_use_mode: BoolProperty(
        name = names['wire_use_mode'],
        description = '\n Use the mode color for shape wires',
        default = True)

    grid: FloatVectorProperty(
        name = names['grid'],
        description = '\n Color of the grid',
        size = 4,
        min = 0,
        max = 1,
        subtype='COLOR',
        default = (0.2, 0.2, 0.2, 0.2))

    grid_wire: FloatVectorProperty(
        name = names['grid_wire'],
        description = '\n Color of the grid\'s wire',
        size = 4,
        min = 0,
        max = 1,
        subtype='COLOR',
        default = (1.0, 1.0, 1.0, 0.58))

    show_shape_wire: FloatVectorProperty(
        name = names['show_shape_wire'],
        description = '\n Color of the shape\'s wire when the object is to be shown',
        size = 4,
        min = 0,
        max = 1,
        subtype='COLOR',
        default = (0.259, 0.7, 0.66, 0.45))

    snap_point: FloatVectorProperty(
        name = names['snap_point'],
        description = '\n Color of snapping points',
        size = 4,
        min = 0,
        max = 1,
        subtype='COLOR',
        default = (1.0, 1.0, 1.0, 0.4))

    snap_point_highlight: FloatVectorProperty(
        name = names['snap_point_highlight'],
        description = '\n Color of snapping points highlighted',
        size = 4,
        min = 0,
        max = 1,
        subtype='COLOR',
        default = (1.0, 0.02, 0.0, 0.7))

    dot: FloatVectorProperty(
        name = names['dot'],
        description = '\n Color of operation dots',
        size = 4,
        min = 0,
        max = 1,
        subtype='COLOR',
        default = (0.0, 0.0, 0.0, 0.33))

    dot_vert: FloatVectorProperty(
        name = names['dot_vert'],
        description = '\n Color of Ngon verts',
        size = 4,
        min = 0,
        max = 1,
        subtype='COLOR',
        default = (0.195, 0.381, 0.701, 0.4))

    dot_bevel: FloatVectorProperty(
        name = names['dot_bevel'],
        description = '\n Color of bevel operation dots',
        size = 4,
        min = 0,
        max = 1,
        subtype='COLOR',
        default = (0.2, 0.3, 1.0, 0.4))

    dot_highlight: FloatVectorProperty(
        name = names['dot_highlight'],
        description = '\n Color operation dots highlighted',
        size = 4,
        min = 0,
        max = 1,
        subtype='COLOR',
        default = (1.0, 1.0, 1.0, 0.65))

    reduce_opacity_editmode: BoolProperty(
        name = names['reduce_opacity_editmode'],
        description = '\n Reduce opacity of shapes when in edit mode',
        default = True)

    collection: EnumProperty(
        name = names['collection'],
        description = 'Set Cutters Collection Color',
        update = update_collection,
        items = [
            ('NONE','None','', 'OUTLINER_COLLECTION', 0),
            ('RED','Red','', 'COLLECTION_COLOR_01', 1),
            ('ORANGE','Orange','', 'COLLECTION_COLOR_02', 2),
            ('YELLOW','Yellow','', 'COLLECTION_COLOR_03', 3),
            ('GREEN','Green','', 'COLLECTION_COLOR_04', 4),
            ('BLUE','Blue','', 'COLLECTION_COLOR_05', 5),
            ('VIOLET','Violet','', 'COLLECTION_COLOR_06', 6),
            ('PINK','Pink','', 'COLLECTION_COLOR_07', 7),
            ('BROWN','Brown','', 'COLLECTION_COLOR_08', 8)],
        default = 'RED')


# def label_row(path, prop, row, label=''):
#     row.label(text=label if label else names[prop])
#     row.prop(path, prop, text='')


def draw(preference, context, layout):
    column = layout.column(align=True)

    # shape
    header(preference, column.box(), 'color_shape')

    if preference.expand.color_shape:
        box_split = column.box().split(align=True, factor=0.5)

        left = box_split.column(align=True)
        label_row(preference.color, 'negative', left.row(align=True))

        sub = left.split(align=True, factor=0.5)

        subleft = sub.column(align=True)
        subleftrow = subleft.row(align=True)
        subleftrow.enabled = not preference.color.wire_use_mode

        extra_space_prefix(subleftrow)
        subleftrow.label(text='Wire')

        subright = sub.column(align=True)
        subrightrow = subright.row(align=True)

        # extra_space_prefix(subrightrow) # needed if not aligned
        subrightrow.prop(preference.color, 'wire', text='')
        subrightrow.prop(preference.color, 'wire_use_mode', text='', icon='UV_SYNC_SELECT')

        right = box_split.column(align=True)

        sub = right.split(align=True, factor=0.5)

        subleft = sub.column(align=True)
        subleftrow = subleft.row(align=True)

        extra_space_prefix(subleftrow)
        subleftrow.label(text='Show Shape Wire')

        subright = sub.column(align=True)
        subrightrow = subright.row(align=True)

        # extra_space_prefix(subrightrow) # needed if not aligned
        subrightrow.prop(preference.color, 'show_shape_wire', text='')
        subrightrow.prop(preference.display, 'show_shape_wire', text='', icon=F'HIDE_O{"FF" if preference.display.show_shape_wire else "N"}')

        label_row(preference.color, 'extract_fade', right.row(align=True))

        right.separator()
        right.row().label(text='')
        label_row(preference.color, 'reduce_opacity_editmode', right.row(align=True), toggle=True)

    # modes
    column.separator()

    header(preference, column.box(), 'color_mode')

    if preference.expand.color_mode:
        box_split = column.box().split(align=True, factor=0.5)

        left = box_split.column(align=True)
        label_row(preference.color, 'cut', left.row(align=True))
        label_row(preference.color, 'intersect', left.row(align=True))
        label_row(preference.color, 'make', left.row(align=True))
        label_row(preference.color, 'knife', left.row(align=True))

        right = box_split.column(align=True)
        label_row(preference.color, 'join', right.row(align=True))
        label_row(preference.color, 'slice', right.row(align=True))
        label_row(preference.color, 'inset', right.row(align=True))
        label_row(preference.color, 'extract', right.row(align=True))


    # widgets
    column.separator()

    header(preference, column.box(), 'color_widget')

    if preference.expand.color_widget:
        box = column.box()
        box_split = box.split(align=True, factor=0.5)

        left = box_split.column(align=True)
        label_row(preference.color, 'dot', left.row(align=True))

        label_row(preference.color, 'dot_bevel', left.row(align=True))
        label_row(preference.color, 'dot_vert', left.row(align=True))

        label_row(preference.color, 'dot_highlight', left.row(align=True))

        right = box_split.column(align=True)
        sub = right.split(align=True, factor=0.5)

        subleft = sub.column(align=True)
        subleftrow = subleft.row(align=True)
        subleftrow.enabled = not preference.display.grid_mode

        extra_space_prefix(subleftrow)
        subleftrow.label(text='Grid')

        subright = sub.column(align=True)
        subrightrow = subright.row(align=True)

        # extra_space_prefix(subrightrow) # needed if not aligned
        subrightrow.prop(preference.color, 'grid', text='')
        subrightrow.prop(preference.display, 'grid_mode', text='', icon='UV_SYNC_SELECT')

        label_row(preference.color, 'grid_wire', right.row(align=True))
        label_row(preference.color, 'snap_point', right.row(align=True))
        label_row(preference.color, 'snap_point_highlight', right.row(align=True), label='Snap Highlight')

    column.separator()
    split = column.split(align=True, factor=0.5)

    left = split.column()
    label_row(preference.color, 'collection', left.row(align=True))

    right = split.column()
