import bpy, bmesh

from mathutils import Vector

from ..... utility import addon, object, modifier
# from ... utility.shape.change import last
from .. utility.change import last
from .. import utility
from .. utility import statusbar, dimensions
# from .. utility import statusbar
from .... sound import time_code

# from .... property import prop

# TODO: dimension check determine if user made too small of a shape
#  - view distance factored (determining work scale)
#  - create warning dialogue
#  - create pref for displaying warning dialogue
#    - offer in dialogue
#      ~ pref should warn against disable (i.e. garbage cuts)
#      - dialogue offers cancel, ok
#      - op called in prop update and feeds prop path key
def operator(op, context):
    preference = addon.preference()
    bc = context.scene.bc

    bc.__class__.operator = None
    bc.__class__.shader = None

    bc.running = False

    statusbar.remove()

    bc.shape.bc.target = context.active_object if op.mode != 'MAKE' else None

    if op.original_mode == 'EDIT_MESH':
        bpy.ops.object.mode_set(mode='OBJECT')

    for mod in bc.shape.modifiers:
        if mod.type == 'SOLIDIFY':
            mod.show_viewport = True if (op.shape_type == 'NGON' or op.ngon_fit) and not preference.shape.cyclic else False

        if mod.type == 'MIRROR':
            mod.show_viewport = False

    if op.shape_type == 'BOX' and preference.shape.box_grid and not op.ngon_fit and not op.extruded:
        for i in op.geo['indices']['offset']:
            bc.shape.data.vertices[i].co.z = 0.5

    context.view_layer.update()

    # dimensions = bc.lattice.dimensions if not (op.shape_type == 'NGON' and not op.modified) else bc.shape.dimensions
    dim = dimensions()[2]
    dim -= dim * 0.001 # trim by 0.1%
    if dim < preference.shape.lazorcut_limit * (2 if op.mode in {'MAKE', 'JOIN'} else 1) and not op.repeat:
        utility.accucut(op, context)

    if not op.repeat:
        utility.data.repeat(op, context, collect=True)

    if not op.repeat and op.mode == 'KNIFE' and preference.surface == 'VIEW' and dimensions()[2] < preference.shape.lazorcut_limit:
        op.lazorcut = True

    for mod in bc.shape.modifiers:
        if mod.type == 'MIRROR':
            mod.show_viewport = True

    last['origin'] = op.origin
    last['points'] = [Vector(point.co_deform) for point in bc.lattice.data.points]

    for mod in bc.shape.modifiers:
        if mod.type == 'ARRAY' and not mod.use_object_offset:
            offsets = [abs(o) for o in mod.constant_offset_displace]
            if sum(offsets) < 0.0005:
                bc.shape.modifiers.remove(mod)

            else:
                index = offsets.index(max(offsets))
                last['modifier']['offset'] = mod.constant_offset_displace[index]
                last['modifier']['count'] = mod.count

        elif mod.type == 'BEVEL':
            if mod.width < 0.0005:
                bc.shape.modifiers.remove(mod)

            else:
                width_type = 'bevel_width' if mod.name.startswith('Bevel') else F'{mod.name.split(" ")[0].lower()}_bevel_width'
                last['modifier'][width_type] = mod.width if not op.ngon_point_bevel else op.ngon_point_bevel_reset
                last['modifier']['segments'] = mod.segments

        elif mod.type == 'SOLIDIFY':
            if abs(mod.thickness) < 0.0005:
                bc.shape.modifiers.remove(mod)

            else:
                last['modifier']['thickness'] = mod.thickness

    if op.original_mode == 'EDIT_MESH':
        bpy.ops.object.mode_set(mode='EDIT')

    op.update()

    utility.data.clean(op, context)

    key = preference.display.shape_fade_time_out
    if key in time_code.keys():
        utility.sound.play(time_code[key])

    op.report({'INFO'}, 'Executed')

    return {'FINISHED'}
