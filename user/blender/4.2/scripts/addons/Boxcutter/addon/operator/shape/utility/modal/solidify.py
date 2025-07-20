import bpy
from ...... utility import addon, screen


def shape(op, context, event):
    preference = addon.preference()
    bc = context.scene.bc
    snap = preference.snap.enable and preference.snap.incremental

    objects = [bc.shape] if op.mode != 'INSET' else op.datablock['insets']
    last = op.last['modifier']['thickness'] if op.mode != 'INSET' else op.last['thickness']

    thickness = (op.mouse['location'].x - op.last['mouse'].x) / screen.dpi_factor(ui_scale=False, integer=True) * 0.001

    if snap and event.ctrl:
        if event.shift and op.prior_to_shift == 'NONE':
            thickness = -round(thickness, 1)

        else:
            thickness = -round(thickness)

    elif event.shift and op.prior_to_shift == 'NONE':
        thickness = (op.mouse['location'].x - op.last['mouse'].x) / screen.dpi_factor(ui_scale=False, integer=True) * 0.0001

    absolute = bpy.app.version > (2, 9) and op.shape_type == 'BOX' and preference.shape.box_grid
    for obj in objects:
        solidify = None
        for mod in obj.modifiers:
            if mod.type == 'SOLIDIFY':
                solidify = mod
                mod.thickness = last + thickness

                if op.mode != 'INSET':
                    preference.shape['solidify_thickness'] = mod.thickness
                else:
                    preference.shape['inset_thickness'] = mod.thickness

                if event.ctrl:
                    mod.thickness = round(mod.thickness, 2 if event.shift and op.prior_to_shift == 'NONE' else 1)
                else:
                    if op.mode != 'INSET':
                        op.last['modifier']['thickness'] = mod.thickness
                    else:
                        op.last['thickness'] = mod.thickness
                    op.last['mouse'].x = op.mouse['location'].x

                if absolute:
                    mod.thickness = abs(mod.thickness)

                break

        if not solidify:
            mod = obj.modifiers.new(name='Solidify', type='SOLIDIFY')
            mod.show_in_editmode = False
            mod.offset = -1 if (op.shape_type != 'NGON' or op.extruded) else 0
            mod.use_even_offset = True
            mod.use_quality_normals = True
            mod.thickness = last

            if absolute:
                mod.thickness = abs(mod.thickness)

            if hasattr(mod, 'solidify_mode') and preference.shape.box_grid and op.shape_type == 'BOX' and not op.ngon_fit:
                mod.solidify_mode = 'NON_MANIFOLD'
                mod.offset = 0

    del objects

