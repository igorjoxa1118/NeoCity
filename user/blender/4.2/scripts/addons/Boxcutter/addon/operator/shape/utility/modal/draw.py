# from ... import shape as _shape
from .. import lattice, mesh
from ...... utility import addon, modifier


def shape(op, context, event):
    bc = context.scene.bc

    # TODO: bc.shader.valid +can return active
    if hasattr(bc.shader, 'widgets') and bc.shader.widgets.active and bc.shader.widgets.active.index != -1:
        op.ngon_point_index = bc.shader.widgets.active.index

        if op.ngon_fit or op.shape_type == 'BOX':
            modifier.apply(bc.shape, types={'LATTICE'})

    if op.shape_type != 'NGON' and op.ngon_point_index == -1:
        if op.draw_line:
            lattice.draw_line(op, context, event)
        else:
            lattice.draw(op, context, event)
    else:
        mesh.draw(op, context, event)

    # points = bc.lattice.data.points
    # location_z = None
    # opposite_co = [points[i].co_deform for i in lattice.front][0].z
    # for point in [p for p in lattice.back if p not in op.wedge_sets[preference().shape.wedge_side]]:

    #     if not location_z:
    #         location_z = points[point].co_deform.z - opposite_co

    #     points[point].co_deform.z = location_z + opposite_co if location_z < -lattice.thickness_clamp(context) else opposite_co - lattice.thickness_clamp(context)
