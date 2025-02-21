import bpy
from bpy.app.handlers import persistent

from mathutils import Matrix, Vector

from .. addon import shader
from .. utility.addon import preference
from . operator.shape.utility import lattice


vertice = [3, 6, 8, 32, 64]
array = [2, 4, 6, 8, 10]
width = [0.02, 0.05, 0.1]
segment = [1, 2, 3, 4, 6]
angle = [5, 15, 30, 45, 90]
line_angle = [1, 5, 10, 15]


@persistent
def cleanup_operators(_):
    context = bpy.context
    bc = getattr(context.scene, 'bc', None)

    if not bc:
        return

    # if bc.operator:
    #     bc.operator.cancel(context)

    if bc.snap.operator:
        bc.snap.operator.exit(context)

    bc.running = False
    bc.collection = None
    bc.shape = None
    # bc.material = None

    bc.snap.hit = False

    if shader.handlers:
        for handler in shader.handlers[:]:
            handler.remove(force=True)

        if context.screen:
            for area in context.screen.areas:
                if area.type != 'VIEW_3D':
                    continue

                area.tag_redraw()

    bc.__class__.operator = None
    bc.__class__.shader = None


def adjust_shapez_to_solver(behavior, bc, op, solver=''):
    if op.custom_offset:
        return

    offset = preference().shape.offset

    _solver = solver if solver else behavior.boolean_solver

    off = offset + op.start['offset'] if op.operation not in {'EXTRUDE', 'OFFSET'} else offset
    off = round(off, 8)

    if _solver == 'EXACT' or (op.start_exact_join and op.last['mode_set'] == 'JOIN'):
        off = -off

    # keep if
    if _solver == 'EXACT' and op.start_exact_join and op.last['mode_set'] != 'JOIN':
        off = -off

    matrix = op.start['matrix'] @ Matrix.Translation(Vector((0, 0, off)))
    bc.shape.matrix_world.translation = matrix.translation
    bc.plane.matrix_world.translation = matrix.translation
    bc.lattice.matrix_world.translation = matrix.translation
    op.start['matrix'] = matrix
