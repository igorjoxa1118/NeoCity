import bpy

from mathutils import Vector, Matrix
# from .... import toolbar
from . import lattice, mesh
from . modal import refresh, operation, solidify
from ..... utility import addon, modifier
from . modal import refresh, mirror
from math import copysign


last = {
    'mouse': Vector((0, 0)),
    'mode': 'NONE',
    'shape_type': 'BOX',
    'draw_line': False,
    'surface': 'OBJECT',
    'placed_mouse': Vector((0, 0)),
    'track': 0,
    'event_value': '',
    'operation': 'NONE',
    'axis': 'NONE',
    'origin': 'CORNER',
    'thickness': 0.02,
    'depth': float(),
    'draw_location': Vector((0, 0, 0)),
    'modifier': {
        'thickness': -0.01,
        'offset': 0.01,
        'count': 2,
        'segments': 6,
        'bevel_width': 0.02,
        'quad_bevel_width': 0.02,
        'front_bevel_width': 0.02,
        'displace': 0.50},
    'angle': 0.0,
    'matrix': Matrix(),
    'points': list(),
    'wedge_points': list(),
    'geo': {
        'verts': list(),
        'edges': list(),
        'faces': list()}}


def offset(option, context):
    bc = context.scene.bc

    if bc.running:
        offset = Vector((0, 0, option.offset)) @ bc.lattice.matrix_world.inverted()
        bc.lattice.matrix_world.translation = Vector(bc.location[:]) + offset
        bc.shape.matrix_world = bc.lattice.matrix_world
        bc.plane.matrix_world = bc.lattice.matrix_world


def circle_vertices(option, context):
    bc = context.scene.bc

    if not bc.running:
        return

    if option.circle_type == 'MODIFIER':
        for mod in bc.shape.modifiers:
            if mod.type == 'SCREW':
                mod.steps = option.circle_vertices
                mod.render_steps = mod.steps

    else:
        mesh.create_shape(bc.shape.data, shape_type=option.circle_type, operator=bc.operator)


def dimensions_xy(option, context):
    bc = context.scene.bc

    option['circle_diameter'] = option.dimension_x

    if not bc.running:
        return

    if bc.operator.operation != 'NONE':
        operation.change(bc.operator, context, None, to='NONE')

    for bpoint, fpoint in zip(lattice.back, lattice.front):
        back = bc.lattice.data.points[bpoint]
        front = bc.lattice.data.points[fpoint]
        back.co_deform.x = front.co_deform.x
        back.co_deform.y = front.co_deform.y

    center = lattice.center(Matrix())
    half_x = option.dimension_x / 2
    half_y = option.dimension_y / 2

    if bc.operator.origin == 'CENTER':
        for point in bc.lattice.data.points:
            x = point.co_deform.x - center.x
            y = point.co_deform.y - center.y

            point.co_deform.x = center.x + copysign(half_x, x)
            point.co_deform.y = center.y + copysign(half_y, y)
    else:
        corner = bc.operator.last['lattice_corner']
        corner_offset_x = corner.x + copysign(half_x, center.x - corner.x)
        corner_offset_y = corner.y + copysign(half_y, center.y - corner.y)

        for point in bc.lattice.data.points:
            x = point.co_deform.x - center.x
            y = point.co_deform.y - center.y

            point.co_deform.x = corner_offset_x + copysign(half_x, x)
            point.co_deform.y = corner_offset_y + copysign(half_y, y)

    if not bc.operator.ngon_fit or (bc.operator.ngon_fit and bc.operator.extruded):
        lattice.wedge(bc.operator, context)

    event = type('fake_event', (), {'ctrl' : False, 'shift' : False, 'alt' : False})
    refresh.shape(bc.operator, context, event)


def dimension_z(option, context):
    bc = context.scene.bc

    if not bc.running:
        return

    if bc.operator.operation != 'NONE':
        operation.change(bc.operator, context, None, to='NONE')

    if bc.operator.ngon_fit and not bc.operator.extruded:
        matrix = Matrix.Translation((0, 0, 0.5))

        bc.shape.data.transform(matrix)
        #bc.lattice.data.transform(matrix.inverted())

        bc.operator.start['extrude'] = bc.lattice.data.points[lattice.front[0]].co_deform.z - 0.001
        option['dimension_z'] = 0

        mesh.extrude(bc.operator, context, None, amount=-0.5)

    floor = bc.lattice.data.points[lattice.front[0]].co_deform.z
    extrude = floor - option.dimension_z
    bc.operator.view3d['location'].z = bc.operator.start['extrude'] = extrude if not bc.operator.inverted_extrude else -extrude

    event = type('fake_event', (), {'ctrl' : False, 'shift' : False, 'alt' : False})
    bc.operator.alt_extrude = False
    lattice.extrude(bc.operator, context, event)

    # lattice.wedge(bc.operator, context)

    refresh.shape(bc.operator, context, event)

    bc.lattice.data.points.update()


def circle_diameter(option, context):
    option['dimension_x'] = option['dimension_y'] = option.circle_diameter
    dimensions_xy(option, context)


def bevel_width(option, context):
    bc = context.scene.bc

    if bc.running:
        for mod in bc.shape.modifiers:
            if mod.type != 'BEVEL':
                continue

            width_type = 'bevel_width' if mod.name.startswith('Bevel') else F'{mod.name.split(" ")[0].lower()}_bevel_width'

            mod.width = getattr(option, width_type)
            bc.operator.last['modifier'][width_type] = mod.width

        refresh.weld_size(bc.operator, bc)


def bevel_segments(option, context):
    bc = context.scene.bc

    if bc.running:
        for mod in bc.shape.modifiers:
            if mod.type == 'BEVEL':
                mod.segments = option.bevel_segments

                last['modifier']['segments'] = option.bevel_segments


def bevel_both(option, context):
    bc = context.scene.bc

    if bc.running:
        op = bc.operator
        preference = addon.preference()
        for index in op.geo['indices']['top_edge']:
            mesh.index_weight(index, value=bc.shape.data.bc.q_beveled and op.flip_z and preference.shape.bevel_both)


def quad_bevel(option, context):
    bc = context.scene.bc

    if bc.running:
        for mod in bc.shape.modifiers:
            if mod.type == 'BEVEL':
                bc.shape.modifiers.remove(mod)


def quad_bevel_width(option, context):
    bc = context.scene.bc

    if not bc.running:
        return

    for mod in bc.shape.modifiers:
        if mod.type != 'BEVEL':
            continue

        width_type = 'bevel_width' if mod.name.startswith('Bevel') else F'{mod.name.split(" ")[0].lower()}_bevel_width'

        mod.width = option.quad_bevel_width
        bc.operator.last['modifier'][width_type] = mod.width

    refresh.weld_size(bc.operator, bc)


def straight_edges(option, context):
    bc = context.scene.bc

    if bc.running:
        for mod in bc.shape.modifiers:
            if mod.type == 'BEVEL':
                bc.shape.modifiers.remove(mod)


def inset_thickness(option, context):
    bc = context.scene.bc

    if bc.running:
        for mod in bc.inset.modifiers:
            if mod.type == 'SOLIDIFY':
                mod.thickness = option.inset_thickness

        last['thickness'] = option.inset_thickness
        if not bc.bevel:
            return

        for mod in bc.bevel.modifiers:
            if mod.type == 'BEVEL':
                mod.width = option.inset_thickness


def solidify_thickness(option, context):
    bc = context.scene.bc

    if bc.running:
        for mod in bc.shape.modifiers:
            if mod.type == 'SOLIDIFY':
                mod.thickness = option.solidify_thickness

                last['modifier']['thickness'] = option.solidify_thickness


def solidify_offset(option, context):
    bc = context.scene.bc

    if bc.running:
        for mod in bc.shape.modifiers:
            if mod.type == 'SOLIDIFY':
                mod.offset = option.solidify_offset

                last['modifier']['offset'] = option.solidify_offset


def array_circle(bc_shape, context):
    preference = addon.preference()
    bc = context.scene.bc

    if not bc.running:
        return

    array = [mod for mod in bc.shape.modifiers if mod.type == 'ARRAY']

    if not array:
        return

    array = array[0]

    array.use_object_offset = not array.use_object_offset
    array.use_constant_offset = not array.use_object_offset
    array.use_relative_offset = not array.use_relative_offset

    bc_shape['array_circle'] = array.use_object_offset

    if not array.use_object_offset:
        array.offset_object = None

        for m in bc.shape.modifiers:
            if m.type == 'DISPLACE':
                bc.shape.modifiers.remove(m)

                break

    if not array.use_object_offset and bc.empty and not bc.empty.users:
        bpy.data.objects.remove(bc.empty)

    elif array.use_object_offset:
        preference.shape.array_distance = 1.0

        if array.count < 3:
            array.count = 3
            preference.shape.array_count = 3

        displace = None
        for mod in bc.shape.modifiers:
            if mod.type != 'DISPLACE':
                continue

            displace = mod

        if not bc.empty:
            bc.empty = bpy.data.objects.new(name=F'{bc.shape.name} Array Target', object_data=None)
            bc.collection.objects.link(bc.empty)

        mod.offset_object = bc.empty

        if not displace:
            stored_array = modifier.stored(array)
            bc.shape.modifiers.remove(array)

            displace = bc.shape.modifiers.new('Displace', 'DISPLACE')
            displace.strength = preference.shape.array_distance
            displace.direction = 'X'
            displace.mid_level = 0.0

            modifier.new(bc.shape, mod=stored_array)

            array = None
            for mod in bc.shape.modifiers:
                if mod.type == 'ARRAY':
                    array = mod

                    break

            driver = bc.empty.driver_add('rotation_euler', 2).driver
            driver.type == 'SCRIPTED'

            count = driver.variables.new()
            count.name = 'count'
            count.targets[0].id_type = 'OBJECT'
            count.targets[0].id = bc.shape
            count.targets[0].data_path = F'modifiers["{array.name}"].count'

            driver.expression = 'radians(360 / count)'

        refresh.shape(bc.operator, bpy.context, None)


def array_axis(option, context):
    bc = context.scene.bc

    if not bc.running:
        return

    bc.shape.bc.array_axis = option.array_axis
    axis_index = 'XYZ'.index(bc.shape.bc.array_axis)

    negative = bc.operator.last['modifier']['offset'] < 0
    limit = 0.000001 if not negative else -0.000001

    for mod in bc.shape.modifiers:
        if mod.type != 'ARRAY':
            continue

        for index, offset in enumerate(mod.constant_offset_displace[:]):
            if index != axis_index:
                mod.relative_offset_displace[index] = 0.0
                mod.constant_offset_displace[index] = 0.0

                continue

            mod.constant_offset_displace[axis_index] = bc.operator.last['modifier']['offset'] if abs(bc.operator.last['modifier']['offset']) > abs(limit) else limit
            mod.relative_offset_displace[axis_index] = 1.0 if not negative else -1.0


def array_distance(option, context):
    bc = context.scene.bc

    if not bc.running:
        last['modifier']['offset'] = option.array_distance
        return

    axis_index = 'XYZ'.index(bc.shape.bc.array_axis)

    negative = bc.operator.last['modifier']['offset'] < 0
    limit = 0.000001 if not negative else -0.000001

    bc.operator.last['modifier']['offset'] = option.array_distance

    for mod in bc.shape.modifiers:
        if mod.type == 'DISPLACE' and bc.shape.bc.array_circle:
            mod.strength = option.array_distance

        if mod.type != 'ARRAY' or bc.shape.bc.array_circle:
            continue

        for index, offset in enumerate(mod.constant_offset_displace[:]):
            if index != axis_index:
                mod.relative_offset_displace[index] = 0.0
                mod.constant_offset_displace[index] = 0.0

                continue

            mod.constant_offset_displace[axis_index] = bc.operator.last['modifier']['offset'] if abs(bc.operator.last['modifier']['offset']) > abs(limit) else limit
            mod.relative_offset_displace[axis_index] = 1.0 if not negative else -1.0

            bc.operator.last['modifier']['offset'] = mod.constant_offset_displace[axis_index]

        option['array_distance'] = bc.operator.last['modifier']['offset']


def array_count(option, context):
    bc = context.scene.bc

    if not bc.running:
        return

    for mod in bc.shape.modifiers:
        if mod.type != 'ARRAY':
            continue

        mod.count = option.array_count

        bc.operator.last['modifier']['count'] = option.array_count


def mirror_axis(option, context):
    bc = context.scene.bc

    if not bc.running:
        return

    for mod in bc.shape.modifiers:
        if mod.type != 'MIRROR':
            continue

        mod.use_axis = option.mirror_axis

    bc.mirror_axis = option.mirror_axis


def mirror_bisect_axis(option, context):
    bc = context.scene.bc

    if not bc.running:
        return

    for mod in bc.shape.modifiers:
        if mod.type != 'MIRROR':
            continue

        mod.use_bisect_axis = option.mirror_bisect_axis

        mirror.verify(context, mod)

        break


def mirror_flip_axis(option, context):
    bc = context.scene.bc

    if not bc.running:
        return

    for mod in bc.shape.modifiers:
        if mod.type != 'MIRROR':
            continue

        mod.use_bisect_flip_axis = option.mirror_flip_axis

        mirror.verify(context, mod)

        break

    bc.mirror_axis_flip = option.mirror_flip_axis


def allow_selection(option, context):
    wm = context.window_manager
    active_keyconfig = wm.keyconfigs.active
    addon_keyconfig = wm.keyconfigs.addon


    # for kc in (active_keyconfig, addon_keyconfig):
    for kc in (addon_keyconfig, ):
        for mode in ('Object', 'Edit Mesh'):
            for kmi in kc.keymaps[F'3D View Tool: {mode}, BoxCutter'].keymap_items:
                if kmi.idname == 'bc.shape_draw' and not kmi.ctrl and not kmi.shift and kmi.map_type != 'TWEAK':
                    kmi.active = not option.allow_selection

    del active_keyconfig
    del addon_keyconfig


def alt_scroll_shape_type(option, context):
    wm = context.window_manager
    active_keyconfig = wm.keyconfigs.active
    addon_keyconfig = wm.keyconfigs.addon

    # for kc in (active_keyconfig, addon_keyconfig):
    for kc in (addon_keyconfig, ):
        for mode in ('Object', 'Edit Mesh'):
            for kmi in kc.keymaps[F'3D View Tool: {mode}, BoxCutter'].keymap_items:
                if kmi.idname == 'bc.subtype_scroll':
                    kmi.active = option.alt_scroll_shape_type

    del active_keyconfig
    del addon_keyconfig


# TODO: need a ui busy flag (set from panels/menus)
def taper(option, context):
    bc = context.scene.bc

    if bc.lattice:
        lattice.wedge(bc.operator, context)

    option['taper_display'] = option.taper != 1.0

def wedge(option, context):
    bc = context.scene.bc

    if bc.lattice and (not bc.operator.ngon_fit or bc.operator.extruded):
        lattice.wedge(bc.operator, context)


def box_grid(option, context):
    bc = context.scene.bc

    if bc.running and bc.operator.shape_type == 'BOX' and not bc.operator.ngon_fit:
        if not option.box_grid:
            mesh.create_shape(bc.shape.data, shape_type='BOX', operator=bc.operator)

            if option.box_grid_auto_solidify and bc.shape.bc.solidify and bc.operator.mode != 'KNIFE':
                bc.shape.bc.solidify  = False
                for mod in bc.shape.modifiers[:]:
                    if mod.type == 'SOLIDIFY':
                        bc.shape.modifiers.remove(mod)

        else:
            mesh.create_shape(bc.shape.data, shape_type='GRID', operator=bc.operator)

            if option.box_grid_auto_solidify and not bc.shape.bc.solidify and bc.operator.mode != 'KNIFE':
                bc.shape.bc.solidify  = True
                event = type('fake_event', (), {'ctrl' : False, 'shift' : False, 'alt' : False})
                solidify.shape(bc.operator, context, event)


def mirror_gizmo(option, context):
    bc = context.scene.bc
    op = bc.__class__.operator
    event = type('fake_event', (), {'ctrl' : False, 'shift' : False, 'alt' : False})

    if option.mirror_gizmo:
        operation.change(op, context, event, to='MIRROR')

    else:
        operation.change(op, context, event, to=op.last['operation'])

