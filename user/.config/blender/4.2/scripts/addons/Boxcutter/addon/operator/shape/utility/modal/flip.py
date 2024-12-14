import bmesh

from mathutils import Matrix, Vector
from .... utility import addon


def shape(op, context, event, report=True):
    preference = addon.preference()
    bc = context.scene.bc

    bc.shape.data.transform(Matrix.Scale(-1, 4, Vector((0, 0, 1))))

    bm = bmesh.new()
    bm.from_mesh(bc.shape.data)

    bm.faces.ensure_lookup_table()
    #bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bmesh.ops.reverse_faces(bm, faces=bm.faces)

    if bc.shape.data.bc.q_beveled and (op.shape_type == 'BOX' or (op.shape_type == 'CIRCLE' and addon.preference().shape.circle_type != 'MODIFIER')):
        op.reverse_bevel = True
        indices = op.geo['indices']['bot_face']# if op.flip_z else []
        bmesh.ops.reverse_faces(bm, faces=[bm.faces[index] for index in indices])
    preference.shape.bevel_both = preference.shape.bevel_both

    bm.to_mesh(bc.shape.data)
    bm.free()

    if report:
        op.report({'INFO'}, 'Flipped Shape on Z')
