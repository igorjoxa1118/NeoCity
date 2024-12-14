from mathutils import Matrix, Vector
from ...... utility import view3d, addon
# from ... import shape as _shape
from .. import mesh


def shape(op, context, event):
    bc = context.scene.bc
    preference = addon.preference()

    amount = ((view3d.location3d_to_location2d(op.last['global_pivot']) - op.mouse['location']).length) / op.last['scale']

    if event.type in {'X', 'Y', 'Z'}:
        if event.value == 'RELEASE':
            if event.type == op.last['axis']:
                op.last['axis'] = 'XYZ'

            else:
                op.last['axis'] = event.type

    x = y = z = 1

    if op.last['axis'] == 'XYZ':
        x = y = z = amount

    elif op.last['axis'] == 'X':
        x = amount

    elif op.last['axis'] == 'Y':
        y = amount

    elif op.last['axis'] == 'Z':
        z = amount

    scale = Matrix.Diagonal((x, y, z, 1))

    matrix = op.last['shape'].matrix_world.copy()
    matrix.translation = op.last['global_pivot']

    for point, vec in zip(bc.lattice.data.points, op.last['lattice_points']):
        point.co_deform = vec

    matrix = matrix @ scale @ matrix.inverted() @ op.last['shape'].matrix_world

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
            space_matrix_inv = space_matrix.inverted()

            sca_vec = (space_matrix_inv @ snap_world) - (space_matrix_inv @ ref_vec) - Vector((1, 1, 1))
            sca_mat = Matrix.Diagonal((abs(sca_vec.x), abs(sca_vec.y), 1, 1))

            space_matrix.translation = op.last['global_pivot'] # op.last['shape'].matrix_world.translation

            matrix = space_matrix @ sca_mat @ space_matrix.inverted() @ op.last['shape'].matrix_world


    scale = Matrix.Diagonal((*matrix.to_scale(), 1))
    loc = matrix.translation
    matrix.normalize()
    matrix.translation = loc

    bc.lattice.data.transform(scale)

    bc.lattice.matrix_world = bc.shape.matrix_world = matrix