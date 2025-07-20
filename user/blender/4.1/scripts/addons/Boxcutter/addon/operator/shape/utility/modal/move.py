from mathutils import Matrix, Vector
from ...... utility import view3d, addon


def shape(op, context, event):
    bc = context.scene.bc
    preference = addon.preference()

    if event.type in {'X', 'Y', 'Z'}:
        if event.value == 'RELEASE':
            op.last['view3d_location'] = op.view3d['location']
            if event.type == op.last['axis']:
                op.last['axis'] = 'XY'
            else:
                op.last['axis'] = event.type

    if bc.snap.operator:
        location = None
        grid_snap = False
        if hasattr(bc.snap.operator, 'grid_handler'):
            grid_handler = bc.snap.operator.grid_handler
            grid_handler.mode = 'NONE'
            grid_handler.draw = False

            # grid_lock = preference.snap.increment_lock and preference.snap.grid
            # grid_handler.draw = (grid_lock or grid_handler.frozen) != event.ctrl
            if event.ctrl:
                grid_handler.draw = True
                grid_snap = True

            grid_handler.update(context, event)

            location = (op.last['shape'].matrix_world.inverted() @ grid_handler.snap_world) + op.last['view3d_location']

        else:
            grid_snap = bc.snap.display
            location = (op.last['shape'].matrix_world.inverted() @ Vector(bc.snap.location)) + op.last['view3d_location']

        if grid_snap:
            op.view3d['location'].x = location.x
            op.view3d['location'].y = location.y
            op.view3d['location'].z = location.z

    if event.type == 'G': #XXX handle modal side
        if event.value == 'RELEASE':
            op.last['view3d_location'] = op.view3d['location']

    loc_x = loc_y = loc_z = 0

    if 'X' in op.last['axis']:
        loc_x = op.view3d['location'].x - op.last['view3d_location'].x
    if 'Y' in op.last['axis']:
        loc_y = op.view3d['location'].y - op.last['view3d_location'].y
    if 'Z' in op.last['axis']:
        loc_z = op.view3d['location'].z - op.last['view3d_location'].z

    move_matrix = Matrix.Translation(Vector((loc_x, loc_y, loc_z)))

    if op.shape_type == 'NGON':
        # bc.shape.matrix_world = op.last['shape'].matrix_world @ move_matrix
        bc.shape.matrix_world = bc.shape.matrix_world @ move_matrix

    else:
        # bc.lattice.matrix_world = op.last['lattice'].matrix_world @ move_matrix
        bc.lattice.matrix_world = bc.lattice.matrix_world @ move_matrix
        # bc.shape.matrix_world = op.last['shape'].matrix_world @ move_matrix
        bc.shape.matrix_world = bc.shape.matrix_world @ move_matrix
