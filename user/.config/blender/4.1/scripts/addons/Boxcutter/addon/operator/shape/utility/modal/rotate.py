from math import radians
from mathutils import Matrix, Vector
from ...... utility import view3d, addon, object
from ...... utility.math import increment_round, angle_to
# from ... import shape as _shape
from .. import mesh, lattice


def by_90(op, context, event, init=False):
    preference = addon.preference()
    bc = context.scene.bc
    prev_rot = 0

    if op.shape_type != 'NGON':
        if not init:
            prev_rot = bc.rotated_inside

            if bc.rotated_inside > 3:
                bc.rotated_inside = 0

            bc.rotated_inside += 1

        bc.shape.data.transform(Matrix.Rotation(radians(90 * (bc.rotated_inside - prev_rot) ), 4, 'Z'))

    if preference.shape.wedge and not init:
        bc.wedge_point_delta += 1

        if bc.wedge_point_delta > 3:
            bc.wedge_point_delta = 0

        lattice.wedge(op, context)

def by_90_shape(op, context):
    bc = context.scene.bc
    pivot = object.center(bc.shape)
    bc.shape.matrix_world = bc.lattice.matrix_world = bc.plane.matrix_world = matrix_by_angle(bc.shape.matrix_world, pivot=pivot, axis='Z', angle_rad=radians(90))

def matrix_by_angle(matrix, pivot=None, axis='Z', angle_rad=0):
    rotate_matrix = Matrix.Rotation(angle_rad, 4, axis)
    pivot_matrix = matrix.normalized()
    if pivot: pivot_matrix.translation = pivot

    return pivot_matrix @ rotate_matrix @ pivot_matrix.inverted() @ matrix


def shape(op, context, event):
    preference = addon.preference()
    bc = context.scene.bc

    round_to = 1 if event.shift and op.prior_to_shift == 'NONE' else preference.snap.rotate_angle
    angle = increment_round(angle_to(op.last['mouse'], op.mouse['location'], view3d.location3d_to_location2d(op.last['global_pivot'])), round_to)

    if event.type in {'X', 'Y', 'Z'}:
        if event.value == 'RELEASE':
            preference.shape.rotate_axis = event.type


    if bc.snap.operator:
        space_matrix = None
        snap_world = None
        grid_snap = False
        if hasattr(bc.snap.operator, 'grid_handler'):
            grid_handler = bc.snap.operator.grid_handler
            grid_handler.mode = 'NONE'
            grid_handler.draw = False

            # grid_lock = preference.snap.increment_lock and preference.snap.grid
            # grid_handler.draw = (grid_lock or grid_handler.frozen) != event.ctrl
            if event.ctrl:
                grid_snap = True
                grid_handler.draw = True
                grid_handler.update(context, event)
                space_matrix = grid_handler.snap_matrix.normalized()
                snap_world = grid_handler.snap_world


        elif not bc.snap.operator.handler.exit and not preference.snap.static_grid and preference.snap.grid and bc.snap.operator.handler.grid.display:
            grid_snap = bc.snap.display
            space_matrix = bc.snap.operator.handler.matrix.normalized()
            space_matrix.translation = bc.snap.operator.handler.location
            snap_world = Vector(bc.snap.location)

        if grid_snap:
            ref_vec = op.last['snap_location']
            shape_loc_proj = space_matrix.inverted() @ op.last['shape'].matrix_world.translation
            shape_loc_proj.z = 0
            shape_loc_proj = space_matrix @ shape_loc_proj
            space_matrix.translation = shape_loc_proj
            space_matrix_inv = space_matrix.inverted()

            angle = - (space_matrix_inv @ ref_vec).to_2d().angle_signed((space_matrix_inv @ snap_world).to_2d() , 0)
            rotate_matrix = Matrix.Rotation(angle, 4, 'Z')
            space_matrix.translation = op.last['shape'].matrix_world.translation
            bc.lattice.matrix_world = bc.shape.matrix_world = space_matrix @ rotate_matrix @ space_matrix.inverted() @ op.last['shape'].matrix_world
            return

    bc.lattice.matrix_world = bc.shape.matrix_world = matrix_by_angle(op.last['shape'].matrix_world, pivot=op.last['global_pivot'], axis=preference.shape.rotate_axis, angle_rad=radians(-angle))