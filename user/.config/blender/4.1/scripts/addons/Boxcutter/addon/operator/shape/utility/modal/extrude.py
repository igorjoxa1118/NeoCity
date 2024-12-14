from .. import mesh, lattice


def shape(op, context, event, extrude_only=False):
    bc = context.scene.bc

    if op.shape_type == 'NGON':
        mesh.extrude(op, context, event, extrude_only=extrude_only)

    lattice.extrude(op, context, event)

    for mod in bc.shape.modifiers:
        if mod.type != 'BEVEL' or mod.show_viewport:
            continue

        mod.show_viewport = True
