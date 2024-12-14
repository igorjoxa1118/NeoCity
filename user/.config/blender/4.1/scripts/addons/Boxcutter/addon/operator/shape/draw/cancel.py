from ..... utility import addon, method_handler
from .. import utility
from .. utility import statusbar
# from .. utility import statusbar
# from ... utility import shape
# from .. draw import prop

# from .... property import prop


def operator(op, context):
    wm = context.window_manager
    bc = context.scene.bc

    bc.__class__.operator = None
    bc.__class__.shader = None

    bc.running = False
    statusbar.remove()

    op.cancelled = True

    op.update()

    op.geo['indices']['extrusion'].clear()

    if op.datablock['overrides']:
        utility.data.restore_overrides(op, clear=True)

    hops = getattr(wm, 'Hard_Ops_material_options', False)
    if hops and hops.active_material:
        for obj in op.datablock['targets']:
            obj.data.materials.clear()

            for mat in op.existing[obj]['materials']:
                obj.data.materials.append(mat)

    method_handler(utility.data.clean, (op, context, True))

    op.report({'INFO'}, 'Cancelled')

    return {'CANCELLED'}
