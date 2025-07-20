import bpy

from bpy.types import PropertyGroup
from bpy.props import *

from ... property.utility import names

last_grid_unit = 0
def even_grid_units(snap, context):
    global last_grid_unit

    if not last_grid_unit:
        last_grid_unit = snap.grid_units

    if snap.grid_units != 0 and snap.grid_units % 2 != 0:
        if last_grid_unit <= snap.grid_units:
            snap['grid_units'] = snap.grid_units + 1
        else:
            snap['grid_units'] = snap.grid_units - 1

    last_grid_unit = snap.grid_units


def enable_snap_grid(snap, context):
    enable_snap(snap, snap.grid)

    if not snap.grid and not snap.incremental:
        snap['increment_lock'] = False


def enable_incremental(snap, context):
    enable_snap(snap, snap.incremental)

    if not snap.grid and not snap.incremental:
        snap['increment_lock'] = False

    if snap['incremental']:
        snap['mesh_element'] = 'NONE'


def enable_snap_lock(snap, context):
    enable_snap(snap, snap.increment_lock)

    if not snap.incremental:
        snap.grid = snap.increment_lock


def enable_snap_verts(snap, context):
    enable_snap(snap, snap.verts)


def enable_snap_edges(snap, context):
    enable_snap(snap, snap.edges)


def enable_snap_faces(snap, context):
    enable_snap(snap, snap.faces)


def enable_snap(snap, prop):
    if not snap.enable and prop:
        snap.enable = True

    if not snap.incremental and not snap.grid and not snap.verts and not snap.edges and not snap.faces:
        snap.enable = False


def toggle_dot_show_subdivision(snap, context):
    bc = context.scene.bc

    if bc.snap.operator and hasattr(bc.snap.operator, 'grid_handler'):
        grid_handler = bc.snap.operator.grid_handler
        grid_handler.draw_dots_wire = snap.dot_show_subdivision
        grid_handler.create_dots()


def enabled_mode(snap):
    return snap.enable_edit if bpy.context.mode == 'EDIT_MESH' else snap.enable_object


def mode(snap, value):
    if bpy.context.mode == 'EDIT_MESH':
        snap.enable_edit = value
    else:
        snap.enable_object = value

def mesh_element(snap, _):
    if snap.mesh_element != 'NONE':
        snap['incremental'] = False
        snap['enable'] = False

class bc(PropertyGroup):
    enable_object: BoolProperty()
    enable_edit: BoolProperty()

    enable: BoolProperty(
        name = 'Snap',
        description = '\n Snap points when holding CTRL',
        get = enabled_mode,
        set = mode,
        default = False)

    incremental: BoolProperty(
        name = 'Snap Incremental',
        description = '\n Snap to increments',
        update = enable_incremental,
        default = False)

    increment: FloatProperty(
        name = 'Increment Amount',
        description = '\n Snap increment amount',
        subtype = 'DISTANCE',
        unit = 'LENGTH',
        min = 0.0,
        default = 0.25)

    increment_lock: BoolProperty(
        name = 'Increment Lock',
        description = '\n Snap increment/grid without holding CTRL',
        update = enable_snap_lock,
        default = False)

    angle_lock: BoolProperty(
        name = 'Angle Lock',
        description = '\n Snap angle lock without holding CTRL',
        default = True)

    mesh_element: EnumProperty(
        name = 'Mesh Element',
        description = '\n Extrude/Offset to Mesh element',
        items = [
            ('NONE', 'Disabled', ''),
            ('VERT', 'Vert', 'Snap to nearest Vert'),
            ('EDGE', 'Edge', 'Snap to nearest point of an  Edge'),
            ('EDGE_CENTER', 'Edge Center', 'Snap to center point of an  Edge'),
            ('FACE', 'Face', 'Snap to nearest point of a Face'),
        ],
        update = mesh_element,
        default = 'NONE')

    mesh_element_exact: BoolProperty(
        name = 'Auto Exact',
        description = '\n Automatically switch to Exact solver when snapping to element',
        default = True)

    # smart_grid_increment: IntProperty(
    #     name = 'Smart Grid Increment Amount',
    #     description = 'Smart Grid increment amount',
    #     min = 2,
    #     soft_max = 50,
    #     max = 100,
    #     default =5)

    # snap_smart_grid: BoolProperty(
    #     name = 'Snap Smart Grid',
    #     description = 'Snap to face grid',
    #     default = False)

    grid: BoolProperty(
        name = 'Snap Grid',
        description = '\n Display and snap to grid',
        update = enable_snap_grid,
        default = False)

    grid_units: IntProperty(
        name = 'Grid Units Span',
        description = '\n Number of grid rows and columns to display.',
        update = even_grid_units,
        min = 0,
        soft_max = 20,
        max = 1000,
        default = 10)

    static_grid: BoolProperty(
        name = 'Static Grid',
        description = '\n Grid snapping tool behavior',
        # update = enable_snap_grid,
        default = False)

    static_dot: BoolProperty(
        name = 'Static Dot',
        description = '\n Dot snapping tool behavior',
        # update = enable_snap_grid,
        default = False)

    # grid_type: EnumProperty(
    #     name = 'Grid type',
    #     description = 'Type of grid to use',
    #     items = [
    #         ('CLASSIC', 'Infinite', ''),
    #         ('STATIC', 'Static','')],
    #     default = 'CLASSIC')

    # dot_type: EnumProperty(
    #     name = 'Dot type',
    #     description = 'Type of dots to use',
    #     items = [
    #         ('CLASSIC', 'Dynamic', ''),
    #         ('STATIC', 'Static','')],
    #     default = 'CLASSIC')

    adaptive: BoolProperty(
        name = 'Adaptive',
        description = '\n Update grid orientation to match the face under the mouse',
        default = False)

    grid_relative_size: BoolProperty(
        name = 'Grid Relative Size',
        description = '\n Size grid relative to target when applicable',
        default = False)

    verts: BoolProperty(
        name = 'Snap Vertices',
        description = '\n Snap to verts',
        update = enable_snap_verts,
        default = True)

    edges: BoolProperty(
        name = 'Snap Edges',
        description = '\n Snap to mid points of edges',
        update = enable_snap_edges,
        default = True)

    faces: BoolProperty(
        name = 'Snap Faces',
        description = '\n Snap to face centers',
        update = enable_snap_faces,
        default = True)

    fade_distance: FloatProperty(
        name = 'Fade Distance',
        description = '\n Distance to Fade snapping points',
        soft_min = 0.1,
        soft_max = 10,
        subtype = 'DISTANCE',
        unit = 'LENGTH',
        default = 1.4)

    rotate_angle: IntProperty(
        name = names['rotate_angle'],
        description = '\n Snap angle when rotating',
        min = 1,
        soft_max = 90,
        max = 360,
        subtype = 'ANGLE',
        default = 15)

    ngon_angle: IntProperty(
        name = names['ngon_angle'],
        description = '\n Snap angle when using ngon',
        min = 1,
        soft_max = 45,
        max = 180,
        subtype = 'ANGLE',
        default = 15)

    draw_line_angle: IntProperty(
        name = names['draw_line_angle'],
        description = '\n Snap angle when using draw line',
        min = 1,
        soft_max = 45,
        max = 180,
        subtype = 'ANGLE',
        default = 15)

    ngon_previous_edge: BoolProperty(
        name = names['ngon_previous_edge'],
        description = '\n Calculate snap angle relative to previous edge\n'
                      ' Note - Angle is based on cut alignment when disabled',
        default = False)

    dot_preview: BoolProperty(
        name = 'Dot Preview',
        description = 'Enable alignment preview w/ dots',
        default = False)

    dot_preview_scale: FloatProperty(
        name = 'Preview scale',
        description = 'Scale multiplier alignment preview w/ dots',
        default = 3)

    dot_show_subdivision: BoolProperty(
        name = 'Show Subdivision',
        description = 'Show wireframe of subdivided face w/ dots (Static Only)',
        update = toggle_dot_show_subdivision,
        default = False)

    dot_dot_snap: BoolProperty(
        name = 'Dot-Dot snapping',
        description = 'Snap to dots while drawing w/ dots (Static Only)',
        default = False)

    dot_alt_draw: BoolProperty(
        name = 'Alt Draw',
        description = 'Enable Alt-draw w/ dots (Static Only)',
        default = False)

    toggle_ortho_grid: BoolProperty(
        name = 'Toggle Grid Overlay',
        description = 'Toggle Side View grid overlay',
        default = False)

    toggle_floor: BoolProperty(
        name = 'Toggle Floor Overlay',
        description = 'Toggle Floor grid overlay',
        default = False)

    front_draw: BoolProperty(
        name = 'Always in Front',
        description = 'Always draw grid in front of other objects',
        default = False)

    auto_transparency: BoolProperty(
        name = 'Auto Transparency',
        description = 'Make grid more transparent when cutting',
        default = True)

