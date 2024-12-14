import bpy

from bpy.types import PropertyGroup
from bpy.props import BoolProperty, IntProperty, EnumProperty, PointerProperty, CollectionProperty, StringProperty

from . utility import update, label_row, header
from .... utility import addon, modifier
from ... import toolbar
from ... property.utility import names

from ... operator.shape.utility import tracked_states


def shape_type(self, context):
    if toolbar.option().shape_type != self.shape_type:
        if self.shape_type == 'CUSTOM':
            if context.active_object and context.mode == 'OBJECT': # custom poll
                return bpy.ops.bc.custom()

            op = toolbar.option()
            op.shape_type = 'CUSTOM'
            context.workspace.tools.update()

            return

        getattr(bpy.ops.bc, self.shape_type.lower())()

def update_shader(self, context):
    tracked_states.shader_batch = True


class helper_expand(PropertyGroup):
    value: BoolProperty(default=False)


class bc_helper(PropertyGroup):
    expand: CollectionProperty(type=helper_expand)

    shape_type: EnumProperty(
        name = 'Shape Type',
        # description = 'Shape',
        update = shape_type,
        items = [
            ('CIRCLE', 'Circle', 'Circle\n\n Draws using circle shape utilizing center draw by default.\n\n'
                                , 'MESH_CIRCLE', 0),
            ('BOX', 'Box', 'Box\n\n Draws using box shape utilizing corner draw by default.\n\n'
                                , 'MESH_PLANE', 1),
            ('NGON', 'Ngon', 'Ngon\n\n Draws using custom points determined by the user.\n\n'
                                'Usage of C during draw to draw toggles closed ngon or open solid line'
                                , 'MOD_SIMPLIFY', 2),
            ('CUSTOM', 'Custom', 'Custom\n\n Draws utilizing custom shape.\n\n'
                                 ' Without a specified mesh the boxcutter logo will be drawn\n'
                                 ' Specify custom mesh using dropdown in tool options or select mesh and press C\n'
                                 ' Capable of utilizing itself as cutter for self.cut. itterative generation\n\n'
                                , 'FILE_NEW', 3)],
        default = 'BOX')



class bc(PropertyGroup):

    # quick_execute: BoolProperty(
    #     name = names['quick_execute'],
    #     description = '\n Quickly execute cuts on release',
    #     default = False)

    auto_ortho: BoolProperty(
        name = names['auto_ortho'],
        description = '\n Automatically enter orthographic for view project cuts',
        default = False)

    ortho_view_align: BoolProperty(
        name = names['ortho_view_align'],
        description = '\n Automatically enter view project when the viewport is orthographic',
        default = False)

    boolean_solver: EnumProperty(
        name=names['boolean_solver'],
        description='',
        items=[('FAST', 'Fast', 'fast solver for booleans'),
               ('EXACT', 'Exact', 'exact solver for booleans')],
        update=update.boolean_solver,
        default='FAST')

    parent_shape: BoolProperty(
        name = names['parent_shape'],
        description = '\n Parent cutters to the target',
        default = True)

    autohide_shapes: BoolProperty(
        name = 'Auto Hide Shapes',
        description = '\n Hide previously made unselected cutters on cut',
        default = True)

    hide_make_shapes: BoolProperty(
        name = names['hide_make_shapes'],
        description = '\n Hide gray (make) shape during shape creation',
        update = update.hide_make_shapes,
        default = False)

    apply_slices: BoolProperty(
        name = names['apply_slices'],
        description = '\n Apply slice cuts on the slice objects',
        default = False)

    inset_bevel: BoolProperty(
        name = names['inset_bevel'],
        description = '\n Attempt to only bevel edges within the inset region (Experimental)',
        update = update.inset_bevel,
        default = False)

    recut: BoolProperty(
        name = names['recut'],
        description = '\n Strip slice objects of previously existing booleans',
        update = update.rebool,
        default = False)

    inset_slice: BoolProperty(
        name = names['inset_slice'],
        description = '\n Create slice(s) from inset',
        update = update.rebool,
        default = False)

    show_wire: BoolProperty(
        name = names['show_wire'],
        description = '\n Display wires on target',
        default = False)

    apply_scale: BoolProperty(
        name = names['apply_scale'],
        description = '\n Apply scale on the target if it is scaled',
        default = True)

    auto_smooth: BoolProperty(
        name = names['auto_smooth'],
        description = '\n Auto smooth geometry when cutting into it',
        default = True)

    join_flip_z: BoolProperty(
        name = names['join_flip_z'],
        description = '\n Flip the shape fitted for custom shape on the z axis during a join operation',
        default = True)

    join_exact: BoolProperty(
        name = names['join_exact'],
        description = '\n Allows the Join shape to use exact boolean mode without the offset from the main shape',
        default = False)

    # make_active: BoolProperty(
    #     name = names['make_active'],
    #     description = '\n Make the shape active when holding shift to keep it',
    #     default = True)

    draw_line: BoolProperty(
        name = names['draw_line'],
        description = '\n Draw a orientation line first',
        update = update.shape_type,
        default = False)

    hops_mark: BoolProperty(
        name = names['hops_mark'],
        description = '\n Marks boundary using hardOps helper specified markings ',
        default = False)

    cut_through: BoolProperty(
        name = names['cut_through'],
        description = "\n Cut through mesh for view projection lazorcut\n (Triggers if view hasn't been changed) ",
        default = True)

    set_origin: EnumProperty(
        name = names['set_origin'],
        description = 'Origin',
        items = [
            ('MOUSE', 'Mouse Position', '\n Mouse Position', 'RESTRICT_SELECT_OFF', 1),
            ('CENTER', 'Center', '\n Initial Centered', 'SNAP_FACE_CENTER', 2),
            ('BBOX', 'Bounding Box Center', '\n Bounding Box Center', 'PIVOT_BOUNDBOX', 3),
            ('ACTIVE', 'Active Element', '\n Active Element', 'PIVOT_ACTIVE', 4)],
        default = 'BBOX')

    show_shape: BoolProperty(
        name = names['show_shape'],
        description = '\n Display the shape object when finished',
        update = update_shader,
        default = False)

    accucut: BoolProperty(
        name = names['accucut'],
        description = 'Accurate positioning on view align and lazorcut for a better fit',
        default = True)

    simple_trace: BoolProperty(
        name = names['simple_trace'],
        description = '\n Use simple bound cubes when ray tracing (Faster)',
        default = False)

    orient_method: EnumProperty(
        name = names['orient_method'],
        description = 'Orient drawing using specified method',
        items = [
            ('LOCAL', 'Local', '\n Local'),
            ('NEAREST', 'Nearest Edge', '\n Nearest Edge'),
            ('TANGENT', 'Longest Edge', '\n Longest Edge'),
            ('FACE_FIT', 'Face Fit', '\n Face Fit'),
            # ('TANGENTDIAGONAL', 'Farthest Edge', '\n Edge farthest from any vertex'),
            # ('TANGENTEDGEPAIR', 'Longest Disconnected Edges', '\n Longest Disconnected Edges'),
            # ('TANGENTVERTDIAGONAL', 'Most Distant Vertices', '\n Most Distant Vertices'),
            ],
        default = 'LOCAL')

    orient_active_edge: BoolProperty(
        name = 'Use active edge to orient',
        description = '\n if available active edge will be used as orientation',
        default = True)

    cutter_uv: BoolProperty(
        name = 'Cutter UV',
        description = '\n Add UV to cutters',
        default = False)

    use_dpi_factor: BoolProperty(
        name = 'Use DPI Factor',
        description = ('\n Use DPI factoring when drawing and choosing dimensions.\n'
                       ' Note: Having this enabled can cause behavior issues on some machines'),
        default = True)

    surface_extract: BoolProperty(
        name = 'Surface Extract',
        description = ('\n Use Suface Extract algorithm for Extract mode. Uncheck to use classic Boolean Extraction\n'),
        default = True)

    persistent_taper: BoolProperty(
        name = names['persistent_taper'],
        description = '\n Keep taper amount persistent',
        default = False)

    clamp_inset: BoolProperty(
        name = names['clamp_inset'],
        description = '\n Automatically clamp inset',
        default = False)

    helper: PointerProperty(type=bc_helper)

    sort_modifiers: BoolProperty(
        name = names['sort_modifiers'],
        description = '\n Sort modifier order',
        update = update.sync_sort,
        default = True)

    sort_nodes: BoolProperty(
        name = 'Sort Nodes',
        description = '\n Ensure Geometry Nodes modifiers are placed after any boolean modifiers created',
        update = update.sync_sort,
        default = False)

    sort_bevel: BoolProperty(
        name = 'Sort Bevel',
        description = '\n Ensure bevel modifiers are placed after any boolean modifiers created',
        update = update.sync_sort,
        default = True)

    sort_weighted_normal: BoolProperty(
        name = 'Sort Weighted Normal',
        description = '\n Ensure weighted normal modifiers are placed after any boolean modifiers created',
        update = update.sync_sort,
        default = True)

    sort_array: BoolProperty(
        name = 'Sort Array',
        description = '\n Ensure array modifiers are placed after any boolean modifiers created',
        update = update.sync_sort,
        default = True)

    sort_mirror: BoolProperty(
        name = 'Sort Mirror',
        description = '\n Ensure mirror modifiers are placed after any boolean modifiers created',
        update = update.sync_sort,
        default = True)

    sort_solidify: BoolProperty(
        name = 'Sort Soldify',
        description = '\n Ensure solidify modifiers are placed after any boolean modifiers created',
        update = update.sync_sort,
        default = False)

    sort_triangulate: BoolProperty(
        name = 'Sort Triangulate',
        description = '\n Ensure triangulate modifiers are placed after any boolean modifiers created',
        update = update.sync_sort,
        default = True)

    sort_simple_deform: BoolProperty(
        name = 'Sort Simple Deform',
        description = '\n Ensure simple deform modifiers are placed after any boolean modifiers created',
        update = update.sync_sort,
        default = True)

    sort_decimate: BoolProperty(
        name = 'Sort Decimate',
        description = '\n Ensure decimate modifiers are placed after any boolean modifiers created',
        update = update.sync_sort,
        default = False)

    sort_remesh: BoolProperty(
        name = 'Sort Remesh',
        description = '\n Ensure remesh modifiers are placed after any boolean modifiers created',
        update = update.sync_sort,
        default = True)

    sort_subsurf: BoolProperty(
        name = 'Sort Subsurf',
        description = '\n Ensure subsurf modifiers are placed after any boolean modifiers created',
        update = update.sync_sort,
        default = False)

    sort_weld: BoolProperty(
        name = 'Sort Weld',
        description = '\n Ensure weld modifiers are placed after any boolean modifiers created',
        update = update.sync_sort,
        default = False)

    sort_uv_project: BoolProperty(
        name = 'Sort UV Project',
        description = '\n Ensure uv project modifiers are placed after any boolean modifiers created',
        update = update.sync_sort,
        default = True)

    sort_bevel_last: BoolProperty(
        name = 'Sort Bevel',
        description = '\n Only effect the most recent bevel modifier when sorting',
        update = update.sync_sort,
        default = True)

    sort_weighted_normal_last: BoolProperty(
        name = 'Sort Weighted Normal Last',
        description = '\n Only effect the most recent weighted normal modifier when sorting',
        update = update.sync_sort,
        default = True)

    sort_array_last: BoolProperty(
        name = 'Sort Array Last',
        description = '\n Only effect the most recent array modifier when sorting',
        update = update.sync_sort,
        default = True)

    sort_nodes_last: BoolProperty(
        name = 'Sort Nodes last',
        description = '\n Only effect the most recent nodes modifier when sorting',
        update = update.sync_sort,
        default = True)

    sort_mirror_last: BoolProperty(
        name = 'Sort Mirror Last',
        description = '\n Only effect the most recent mirror modifier when sorting',
        update = update.sync_sort,
        default = True)

    sort_solidify_last: BoolProperty(
        name = 'Sort Soldify Last',
        description = '\n Only effect the most recent solidify modifier when sorting',
        update = update.sync_sort,
        default = False)

    sort_triangulate_last: BoolProperty(
        name = 'Sort Triangulate Last',
        description = '\n Only effect the most recent triangulate modifier when sorting',
        update = update.sync_sort,
        default = True)

    sort_simple_deform_last: BoolProperty(
        name = 'Sort Simple Deform Last',
        description = '\n Only effect the most recent simple deform modifier when sorting',
        update = update.sync_sort,
        default = True)

    sort_decimate_last: BoolProperty(
        name = 'Sort Decimate Last',
        description = '\n Only effect the most recent decimate modifier when sorting',
        update = update.sync_sort,
        default = False)

    sort_remesh_last: BoolProperty(
        name = 'Sort Remesh Last',
        description = '\n Only effect the most recent remesh modifier when sorting',
        update = update.sync_sort,
        default = True)

    sort_subsurf_last: BoolProperty(
        name = 'Sort Subsurf Last',
        description = '\n Only effect the most recent subsurface modifier when sorting',
        update = update.sync_sort,
        default = False)

    sort_weld_last: BoolProperty(
        name = 'Sort Weld Last',
        description = '\n Only effect the most recent weld modifier when sorting',
        update = update.sync_sort,
        default = True)

    sort_uv_project_last: BoolProperty(
        name = 'Sort UV Project Last',
        description = '\n Only effect the most recent uv project modifier when sorting',
        update = update.sync_sort,
        default = True)

    sort_bevel_ignore_weight: BoolProperty(
        name = 'Ignore Weight Bevels',
        description = '\n Ignore bevel modifiers that are using the weight limit method while sorting',
        update = update.sync_sort,
        default = True)

    sort_bevel_ignore_vgroup: BoolProperty(
        name = 'Ignore VGroup Bevels',
        description = '\n Ignore bevel modifiers that are using the vertex group limit method while sorting',
        update = update.sync_sort,
        default = True)

    sort_bevel_ignore_only_verts: BoolProperty(
        name = 'Ignore Only Vert Bevels',
        description = '\n Ignore bevel modifiers that are using the only vertices option while sorting',
        update = update.sync_sort,
        default = True)

    sort_depth: IntProperty(
        name = 'Sort Depth',
        description = '\n Number of sortable mods from the end (bottom) of the stack. 0 to sort whole stack',
        update = update.sort_depth,
        min = 0,
        default = 6)

    sort_char: StringProperty(
        name = 'Sort Flag',
        description = '\n Prefix a modifier name with this text character and it will sort the modifier\n  Note: Check the above options before utilizing these flags\n             Many of the behaviors exist for common modifiers',
        update = update.sort_char,
        maxlen = 1,
        default = '*')

    sort_ignore_char: StringProperty(
        name = 'Ignore Flag',
        description = '\n Prefix the modifier name with this text character and it will be ignored.\n  Default: Space',
        update = update.sort_ignore_char,
        maxlen = 1,
        default = ' ')

    sort_last_char: StringProperty(
        name = 'Sort Last Flag',
        description = '\n Prefix the modifier name with this text character and it will be treated like the most recent modifier of the type when sorted.\n  Note: The lowest modifier in the stack with this flag takes precedence\n\n Prefix twice to force',
        update = update.sort_last_char,
        maxlen = 1,
        default = '!')

    sort_lock_above_char: StringProperty(
        name = 'Lock Above Flag',
        description = '\n Prefix a modifier name with this text character and it will keep itself below the modifier above it',
        update = update.sort_lock_above_char,
        maxlen = 1,
        default = '^')

    sort_lock_below_char: StringProperty(
        name = 'Lock Below Flag',
        description = '\n Prefix a modifier name with this text character and it will keep itself above the modifier below it',
        update = update.sort_lock_below_char,
        maxlen = 1,
        default = '.')

    sort_stop_char: StringProperty(
        name = 'Stop Flag',
        description = '\n Prefix a modifier name with this text character and it will not sort it or any modifiers above it in the stack.\n   Note: Including those with prefixes',
        update = update.sort_stop_char,
        maxlen = 1,
        default = '_')

    keep_modifiers: BoolProperty(
        name = names['keep_modifiers'],
        description = '\n Choose what modifiers are applied on the shape',
        default = True)

    keep_array: BoolProperty(
        name = 'Keep Array',
        description = '\n Keep shape array modifier',
        default = True)

    keep_bevel: BoolProperty(
        name = 'Keep Bevel',
        description = '\n Keep shape bevel modifiers',
        default = True)

    keep_solidify: BoolProperty(
        name = 'Keep Soldify',
        description = '\n Keep shape solidify modifier',
        default = True)

    keep_weld: BoolProperty(
        name = 'Keep Weld',
        description = '\n Keep shape weld modifier',
        default = True)

    keep_mirror: BoolProperty(
        name = 'Keep Mirror',
        description = '\n Keep shape mirror modifier',
        default = True)

    keep_screw: BoolProperty(
        name = 'Keep Screw',
        description = '\n Keep shape spin modifier \n *Requires Modifier Circle',
        default = False)

    keep_lattice: BoolProperty(
        name = 'Keep Lattice',
        description = '\n Keep shape lattice modifier',
        default = False)

    keep_lattice_taper: BoolProperty(
        name = 'Keep Taper Lattice',
        description = '\n Keep shape lattice modifier if tapered',
        default = False)


def draw(preference, context, layout):
    column = layout.column(align=True)

    box = column.box()
    header(preference, box, 'behavior_modifier')

    if preference.expand.behavior_modifier:
        box = column.box()
        box_split = box.split(align=True, factor=0.65)

        left = box_split.column(align=True)
        label_row(preference.behavior, 'sort_modifiers', left.row(align=True), toggle=True)

        if preference.behavior.sort_modifiers:
            row = left.row(align=True)
            row.alignment = 'RIGHT'
            split = left.split(align=True, factor=0.85)

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
                elif icon == 'MOD_UV_PROJECT':
                    icon = 'MOD_UVPROJECT'
                elif icon == 'MOD_NODES':
                    icon = 'GEOMETRY_NODES'
                row.prop(preference.behavior, F'sort_{type.lower()}', text='', icon=icon)

            row = split.row(align=True)
            row.scale_x = 1.5
            row.popover('BC_PT_sort_last', text='', icon='SORT_ASC')

        left.separator()
        label_row(preference.behavior, 'keep_modifiers', left.row(align=True), toggle=True)

        if preference.behavior.keep_modifiers:
            # row = layout.row(align=True)
            row = left.row(align=True)
            row.alignment = 'LEFT'
            row.prop(preference.behavior, 'keep_bevel', text='', icon='MOD_BEVEL')
            row.prop(preference.behavior, 'keep_solidify', text='', icon='MOD_SOLIDIFY')
            row.prop(preference.behavior, 'keep_array', text='', icon='MOD_ARRAY')
            if bpy.app.version[:2] >= (2, 82):
                row.prop(preference.behavior, 'keep_weld', text='', icon='AUTOMERGE_OFF')
            row.prop(preference.behavior, 'keep_mirror', text='', icon='MOD_MIRROR')
            row.prop(preference.behavior, 'keep_screw', text='', icon='MOD_SCREW')
            row.prop(preference.behavior, 'keep_lattice', text='', icon='MOD_LATTICE')

        left.separator()

        #right = box_split.column(align=True)
        if bpy.app.version[:2] >= (2, 91):

            if preference.behavior.keep_modifiers:
                left.separator()
                left.separator()

            left.separator()
            label_row(preference.behavior, 'boolean_solver', left.row())
            left.separator()

    column.separator()

    box = column.box()
    header(preference, box, 'behavior_shape')

    # label_row(preference.behavior, 'quick_execute', layout.row())
    if preference.expand.behavior_shape:
        box = column.box()
        box_split = box.split(align=True, factor=0.5)

        left = box_split.column(align=True)

        label_row(preference.behavior, 'orient_method', left.row())

        left.separator()
        label_row(preference.behavior, 'auto_smooth', left.row(), toggle=True)
        label_row(preference.behavior, 'apply_scale', left.row(), toggle=True)
        label_row(preference.behavior, 'apply_slices', left.row(), toggle=True)
        label_row(preference.behavior, 'cutter_uv', left.row(), label='Cutter UVs', toggle=True)
        label_row(preference.behavior, 'auto_ortho', left.row(), toggle=True)
        label_row(preference.behavior, 'ortho_view_align', left.row(), toggle=True)

        right = box_split.column(align=True)
        right.separator()
        label_row(preference.behavior, 'orient_active_edge', right.row(), label='Use Active Edge', toggle=True)
        label_row(preference.behavior, 'show_shape', right.row(), toggle=True)
        label_row(preference.behavior, 'hide_make_shapes', right.row(), toggle=True)
        label_row(preference.behavior, 'surface_extract', right.row(), label='Surface Extract', toggle=True)
        label_row(preference.behavior, 'persistent_taper', right.row(), toggle=True)
        label_row(preference.behavior, 'accucut', right.row(), toggle=True)
        label_row(preference.behavior, 'join_flip_z', right.row(), toggle=True)
        #label_row(preference.behavior, 'draw_line', right.row(), toggle=True)
        #label_row(preference.behavior, 'recut', right.row(), toggle=True)
        label_row(preference.behavior, 'join_exact', right.row(), toggle=True)

    # start behavior, invoke behavior, init behavior
    split = layout.split()
    left = split.column()
    label_row(preference.behavior, 'parent_shape', left.row(), toggle=True)

    right = split.column()
    label_row(preference.behavior, 'show_wire', right.row(), toggle=True)
    #label_row(preference.behavior, 'use_dpi_factor', right.row(), label='Use DPI Factoring', toggle=True)
