import bpy
import bmesh
import sys

from mathutils import Vector, Matrix, geometry
from bpy_extras.view3d_utils import region_2d_to_origin_3d, region_2d_to_vector_3d

from ..... utility import addon, math, modifier, view3d, screen, mesh
from math import radians, copysign

front = (4, 5, 6, 7)
back = (0, 1, 2, 3)
left = (0, 2, 4, 6)
right = (1, 3, 5, 7)
top = (2, 3, 6, 7)
bottom = (0, 1, 4, 5)


def boolean_solver():
    bc = bpy.context.scene.bc
    for o in bc.operator.datablock['targets']:
        for mod in o.modifiers:
            if mod.type != 'BOOLEAN' or mod.object != bc.shape:
                continue

            return mod.solver


def thickness_clamp(op, context):
    from . import dimensions
    preference = addon.preference()
    bc = context.scene.bc
    factor = 0.005
    # thickness = min(bc.lattice.dimensions[:-1]) * factor
    thickness = min(dimensions()[:-1]) * factor

    offset = preference.shape.offset

    return thickness if thickness < offset else offset - 0.001


def create(op, context, event, zero=True):
    preference = addon.preference()
    bc = context.scene.bc

    dat = bpy.data.lattices.new(name='Lattice')
    dat.bc.removeable = True
    bc.lattice = bpy.data.objects.new(name='Lattice', object_data=dat)
    # bc.lattice = bc.lattice

    bc.collection.objects.link(bc.lattice)

    dat.interpolation_type_u = 'KEY_LINEAR'
    dat.interpolation_type_v = 'KEY_LINEAR'
    dat.interpolation_type_w = 'KEY_LINEAR'

    del dat

    if op.shape_type != 'NGON':
        mod = bc.shape.modifiers.new(name='Lattice', type='LATTICE')
        mod.object = bc.lattice
        modifier.sort(bc.shape, types=['LATTICE'], first=True)

    # bc.lattice.hide_set(True)
    # bc.shape.hide_set(True)

    bc.lattice.data.transform(bc.lattice.matrix_world.copy().Translation(Vector((0.0, 0.0, -0.5))))

    if op.origin == 'CORNER':
        bc.lattice.data.transform(bc.lattice.matrix_world.copy().Translation(Vector((0.5, 0.5, 0.0))))

    if zero:
        for point in (0, 1, 2, 3, 4, 5, 6, 7):
            bc.lattice.data.points[point].co_deform.x = 0
            bc.lattice.data.points[point].co_deform.y = 0

        for point in front:
            bc.lattice.data.points[point].co_deform.z = 0

        for point in back:
            bc.lattice.data.points[point].co_deform.z = -preference.shape.offset if preference.behavior.boolean_solver == 'FAST' else 0


def center(matrix, side=''):
    bc = bpy.context.scene.bc
    sides = {
        'front': front,
        'back': back,
        'left': left,
        'right': right,
        'top': top,
        'bottom': bottom}

    if not side:
        return matrix @ (0.125 * sum((Vector(bc.lattice.data.points[point].co_deform[:]) for point in (0, 1, 2, 3, 4, 5, 6, 7)), Vector()))

    return matrix @ (0.25 * sum((Vector(bc.lattice.data.points[point].co_deform[:]) for point in sides[side]), Vector()))


def draw(op, context, event):
    preference = addon.preference()
    bc = context.scene.bc

    snap = preference.snap.enable and (preference.snap.incremental or (preference.snap.grid and bc.snap.display))
    snap_lock = snap and preference.snap.increment_lock

    # not_snap_grid = preference.snap.enable and not preference.snap.grid and not op.modified
    # snap_operator_handler = (bc.snap.operator.handler if hasattr(bc.snap.operator, 'handler') else bc.snap.operator.snap) if bc.snap.operator else None
    # snap_operator_point_exists = snap_operator_handler and (snap_operator_handler.points.active if hasattr(snap_operator_handler, 'points') else snap_operator_handler.point)

    # if snap_operator_point_exists and not_snap_grid:
    #     if preference.snap.edges and bc.snap.operator.snap.point.type == 'VERT':
    #         op.snap_lock_type = 'VERT'

    #     if preference.snap.edges and bc.snap.operator.snap.point.type == 'EDGE' and op.custom_orient:
    #         op.snap_lock_type = 'EDGE'

    #     if preference.snap.edges and bc.snap.operator.snap.point.type == 'FACE':
    #         op.snap_lock_type = 'FACE'

    if event.alt or event.shift:
        op.snap_lock_type = ''

    vert_lock = op.snap_lock_type == 'VERT'
    edge_lock = op.snap_lock_type == 'EDGE'
    face_lock = op.snap_lock_type == 'FACE'

    if op.init_mouse == op.mouse['location']:
        return

    if op.origin == 'CENTER' or event.alt:
        origin_offset = op.last['lattice_center']

    else:
        origin_offset = op.last['lattice_corner']

    mask_shift = False
    if bc.snap.operator:
        if hasattr(bc.snap.operator, 'grid_handler'):
            grid_handler = bc.snap.operator.grid_handler

            if grid_handler.snap_type == 'DOTS':
                if grid_handler.dot_divisions:
                    vert_lock = edge_lock = face_lock = False

                if preference.snap.dot_dot_snap:
                    grid_handler.update(context, event)

                    if grid_handler.nearest_dot:
                        location = bc.shape.matrix_world.inverted() @ grid_handler.snap_world
                        op.view3d['location'].x = location.x
                        op.view3d['location'].y = location.y

                        snap = snap_lock = False
            else:
                grid_handler.mode = 'NONE'

                grid_lock = preference.snap.increment_lock and preference.snap.grid
                grid_handler.draw = (grid_lock or grid_handler.frozen) != event.ctrl
                grid_handler.update(context, event)

                location = bc.shape.matrix_world.inverted() @ grid_handler.snap_world
                op.view3d['location'].x = location.x
                op.view3d['location'].y = location.y

                snap = snap_lock = False

        elif not bc.snap.operator.handler.exit and not preference.snap.static_grid and preference.snap.grid and bc.snap.operator.handler.grid.display and bc.snap.display:
            location = bc.shape.matrix_world.inverted() @ Vector(bc.snap.location)
            op.view3d['location'].x = location.x
            op.view3d['location'].y = location.y

            snap = snap_lock = False

            if bc.snap.operator.handler.micro:
                mask_shift = True

    location_x = op.view3d['location'].x - origin_offset.x
    location_y = op.view3d['location'].y - origin_offset.y

    if preference.shape.auto_flip_xy and (op.shape_type == 'CUSTOM' or op.shape_type == 'BOX' and op.ngon_fit):
        if (location_x < 0 and  op.flip_x) or (location_x > 0 and not op.flip_x):
            op.flip_x = not op.flip_x
            op.flipped_normals = not op.flipped_normals
            mesh.flip_mesh(bc.shape.data, axis='X')

        if (location_y < 0 and  op.flip_y) or (location_y > 0 and not op.flip_y):
            op.flip_y = not op.flip_y
            op.flipped_normals = not op.flipped_normals
            mesh.flip_mesh(bc.shape.data, axis='Y')

    if bc.shape.bc.array and bc.shape.bc.array_circle:
        displace = None

        for mod in bc.shape.modifiers:
            if mod.type == 'DISPLACE':
                displace = mod

                break

    if preference.behavior.draw_line and not op.extruded and not op.ngon_fit and not event.shift and not event.ctrl and not event.alt:
        location_x = op.last['line']

    if snap and event.ctrl or snap_lock:
        increment_amount = round(preference.snap.increment, 8)
        split = str(increment_amount).split('.')[1]

        increment_length = len(split) if int(split) != 0 else 0

        if event.shift:
            location_x = round(round(location_x * 10 / increment_amount) * increment_amount, increment_length)
            location_x *= 0.1
            limit = increment_amount * 0.1

            if op.view3d['location'].x < 0:
                limit = -limit

            if location_x == 0:
                location_x += limit

            location_y = round(round(location_y * 10 / increment_amount) * increment_amount, increment_length)
            location_y *= 0.1

            if location_y == 0:
                location_y += limit

        else:
            location_x = round(round(location_x / increment_amount) * increment_amount, increment_length)
            limit = preference.snap.increment

            if op.view3d['location'].x < 0:
                limit = -limit

            if location_x == 0:
                location_x += limit

            location_y = round(round(location_y / increment_amount) * increment_amount, increment_length)

            if location_y == 0:
                location_y += limit

    points = bc.lattice.data.points

    index1 = 0 if op.view3d['location'].x < origin_offset.x else 1

    draw_dot_index = ((2, 1), (6, 5))
    draw_dot_index = draw_dot_index[index1]

    sides = ('left', 'right')
    side = globals()[sides[index1]]
    clear = globals()[sides[not index1]]

    use_alt = (event.alt and preference.keymap.alt_draw) or ((vert_lock or edge_lock or face_lock) and not event.alt)
    use_shift = ((event.shift and preference.keymap.shift_draw) or (face_lock or vert_lock or (edge_lock and op.shape_type == 'CIRCLE')) and not event.shift) and not mask_shift

    if op.shape_type == 'CUSTOM':
        if preference.shape.auto_depth:
            use_shift = use_shift != preference.shape.auto_depth_custom_proportions

        else:
            op.proportional_draw = use_shift = (event.shift and preference.keymap.shift_draw) != preference.shape.auto_proportions
            use_shift = use_shift != (op.origin == 'CENTER' and preference.shape.auto_proportions)

    if use_alt and not use_shift:
        for point in side:
            points[point].co_deform.x = location_x

        for point in clear:
            points[point].co_deform.x = -location_x

    elif use_shift and not use_alt:
        for point in side:
            points[point].co_deform.x = location_x

        for point in clear:
            points[point].co_deform.x = 0

    elif use_shift and use_alt:
        for point in side:
            points[point].co_deform.x = location_x

        for point in clear:
            points[point].co_deform.x = -location_x

    elif not use_alt or not use_shift:
        for point in side:
            points[point].co_deform.x = location_x

        if op.origin == 'CORNER':
            for point in clear:
                points[point].co_deform.x = 0

        elif op.origin == 'CENTER':
            for point in clear:
                points[point].co_deform.x = -location_x

    preference.shape['dimension_x'] = preference.shape['circle_diameter'] =  abs(points[side[0]].co_deform.x * 2) if op.origin == 'CENTER' else abs(points[side[0]].co_deform.x)

    index2 = 0 if op.view3d['location'].y > origin_offset.y else 1

    draw_dot_index = draw_dot_index[index2]

    sides = ('bottom', 'top')
    side = globals()[sides[not index2]]
    clear = globals()[sides[index2]]

    side_ratio = op.datablock['shape_proportions'].y

    if use_alt and not use_shift:
        for point in side:
            points[point].co_deform.y = location_y

        for point in clear:
            points[point].co_deform.y = -location_y

    elif use_shift and not use_alt:
        for point in side:
            points[point].co_deform.y = (location_x if index1 != index2 else -location_x) * side_ratio

        for point in clear:
            points[point].co_deform.y = 0

    elif use_shift and use_alt:
        for point in side:
            points[point].co_deform.y = (location_x if index1 != index2 else -location_x) * side_ratio

        for point in clear:
            points[point].co_deform.y = (-location_x if index1 != index2 else location_x) * side_ratio

    elif not use_alt or not use_shift:
        if op.origin == 'CENTER':
            for point in side:
                points[point].co_deform.y = (location_x if index1 != index2 else -location_x) * side_ratio

        else:
            for point in side:
                points[point].co_deform.y = location_y

        if op.origin == 'CENTER':
            for point in clear:
                points[point].co_deform.y = (-location_x if index1 != index2 else location_x) * side_ratio

        else:
            for point in clear:
                points[point].co_deform.y = 0

    op.draw_dot_index = draw_dot_index

    preference.shape['dimension_y'] = abs(points[side[0]].co_deform.y * 2) if op.origin == 'CENTER' else abs(points[side[0]].co_deform.y)

    for point in points:
        point.co_deform.x += origin_offset.x
        point.co_deform.y += origin_offset.y

    op.last['draw_location'] = op.view3d['location']

    if preference.shape.auto_depth and not op.align_to_view:
        points = bc.lattice.data.points
        pairs = ((0, 1), (1, 3), (2, 3), (0, 2))

        length = 0.0
        for pair in pairs:
            current = (points[front[pair[0]]].co_deform.to_2d() - points[front[pair[1]]].co_deform.to_2d()).length

            if not preference.shape.auto_depth_large:
                if not length or current < length:
                    length = current

                continue

            if current > length:
                length = current

        length *= preference.shape.auto_depth_multiplier

        if (event.shift != (preference.shape.auto_depth_custom_proportions and op.shape_type == 'CUSTOM')):
            length = preference.shape['dimension_x'] * op.datablock['shape_proportions'].z

        if op.mode in {'MAKE', 'JOIN'}:
            length = -length

        if op.mode in {'MAKE', 'JOIN'} or not op.clamp_extrude:
            delta = -length - points[front[0]].co_deform.z
            if (delta > 0 and not op.inverted_extrude) or (delta < 0 and op.inverted_extrude):
                op.inverted_extrude = not op.inverted_extrude
                op.clamp_extrude = False
                op.flipped_normals = not op.flipped_normals

                mesh.flip_normals(bc.shape.data)

        op.last['depth'] = -length
        op.start['extrude'] = -length

        preference.shape.lazorcut_depth = length

    if op.ngon_fit and not op.extruded:
        return

    wedge(op, context, event=event)


def draw_line(op, context, event):
    preference = addon.preference()
    bc = context.scene.bc

    matrix = bc.shape.matrix_world.copy()

    location = op.view3d['location'].to_2d()

    grid_handler = getattr(bc.snap.operator, 'grid_handler', None)
    if grid_handler:

        grid_handler.update(context, event)

        if grid_handler.snap_type == 'GRID' or (preference.snap.dot_dot_snap and grid_handler.nearest_dot):
            location = (bc.shape.matrix_world.inverted() @ grid_handler.snap_world).to_2d()

    else:
        points = [Vector((0, 1, 0)), Vector((1, -1, 0)), Vector((-1, -1, 0))]
        tri = [matrix @ point for point in points]

        ray = view3d.location2d_to_vector3d(*op.mouse['location'])
        origin =  view3d.location2d_to_origin3d(*op.mouse['location'])

        args = (*tri, ray, origin, False)

        intesect = geometry.intersect_ray_tri(*args)

        if intesect:
            location = (matrix.inverted() @ intesect).to_2d()

    points = bc.lattice.data.points

    for point in points:
        point.co_deform = [0, 0, 0]

    for i in left:
        points[i].co_deform.x = location.length

    angle = location.angle_signed(Vector((1, 0)), 0)

    if event.ctrl and not preference.snap.angle_lock or not event.ctrl and preference.snap.angle_lock:
        snap_increment = radians(preference.snap.draw_line_angle)
        angle = round(angle / snap_increment) * snap_increment

    bc.shape.matrix_world = bc.lattice.matrix_world = matrix @ Matrix.Rotation(angle, 4, 'Z')

    op.last['line'] = location.length

    wedge(op, context)


def offset(op, context, event):
    preference = addon.preference()
    bc = context.scene.bc

    offset = preference.shape.offset if boolean_solver() == 'FAST' else 0

    if op.mode == 'MAKE':
        offset = 0

    # if not op.modified:
    #     if op.mode == 'MAKE':
    #         offset = 0

    #     elif op.mode == 'JOIN':
    #         offset = 0 if preference.behavior.join_exact else -offset if preference.shape.offset != 0 else offset
    # else:
    #     offset = 0

    snap = preference.snap.enable and (preference.snap.incremental or preference.snap.grid)
    snap_lock = snap and preference.snap.increment_lock
    double_offset = event.alt and preference.keymap.alt_double_extrude and not preference.keymap.alt_preserve and not bc.operator.alt_e

    shape = bc.shape
    lat = bc.lattice
    points = lat.data.points

    location_z = op.view3d['location'].z

    if preference.snap.mesh_element != 'NONE' and event.ctrl:
       location_z = element_snap(op, context, location_z)

    elif snap and event.ctrl or snap_lock:
        increment_amount = round(preference.snap.increment, 8)
        split = str(increment_amount).split('.')[1]
        increment_length = len(split) if int(split) != 0 else 0

        if event.shift:
            location_z = round(round(location_z * 10 / increment_amount) * increment_amount, increment_length)
            location_z *= 0.1

        else:
            location_z = round(round(location_z / increment_amount) * increment_amount, increment_length)

    # location = location_z + offset
    # matrix = op.start['matrix'] @ Matrix.Translation(Vector((0, 0, location)))

    extrude = op.start['extrude']
    center = op.last['bounds_center']
    if double_offset:
        extrude = center.z - (location_z - center.z)

    thickness = location_z - points[back[0]].co_deform.z

    limit = thickness_clamp(op, context)

    if op.mode in {'MAKE', 'JOIN'} or not op.clamp_extrude:
        delta = -thickness
        if (delta > 0 and not op.inverted_extrude) or (delta < 0 and op.inverted_extrude):
            op.inverted_extrude = not op.inverted_extrude
            op.clamp_extrude = False
            op.flipped_normals = not op.flipped_normals

            mesh.flip_normals(bc.shape.data)
    else:
        if location_z <= extrude and double_offset:
            extrude = center.z

        if thickness < limit:
            clamp = limit - thickness
            # quat = lat.matrix_world.to_quaternion()
            # scale = lat.matrix_world.to_scale()
            # clamp_vector = quat @ Vector((0, 0, clamp * scale.z))

            location_z += clamp
            # matrix.translation += clamp_vector

    for i in front:
        points[i].co_deform.z = location_z

    op.last['depth'] = extrude

    wedge(op, context)


def extrude(op, context, event):
    preference = addon.preference()
    bc = context.scene.bc

    snap = preference.snap.enable and (preference.snap.incremental or (preference.snap.grid and (bc.snap.display or event.ctrl)))
    snap_lock = snap and preference.snap.increment_lock
    double_extrude = event.alt and preference.keymap.alt_double_extrude and not preference.keymap.alt_preserve and not bc.operator.alt_e

    points = bc.lattice.data.points

    location_z = op.view3d['location'].z

    increment_amount = round(preference.snap.increment, 8)
    split = str(increment_amount).split('.')[1]
    increment_length = len(split) if int(split) != 0 else 0

    if not op.extruded:
        op.extruded = True

    if snap and event.ctrl or (snap_lock and not event.ctrl):
        if event.shift:
            location_z = round(round(location_z * 10 / increment_amount) * increment_amount, increment_length)
            location_z *= 0.1

        else:
            location_z = round(round(location_z / increment_amount) * increment_amount, increment_length)

    offset = op.input_plane.z if preference.behavior.boolean_solver == 'FAST' else 0
    center = op.last['bounds_center']

    if double_extrude:
        offset = center.z - (location_z - center.z)

    if op.mode in {'MAKE', 'JOIN'} or not op.clamp_extrude:
        delta = location_z - points[front[0]].co_deform.z
        if (delta > 0 and not op.inverted_extrude) or (delta < 0 and op.inverted_extrude):
            op.inverted_extrude = not op.inverted_extrude
            op.clamp_extrude = False
            op.flipped_normals = not op.flipped_normals

            mesh.flip_normals(bc.shape.data)

    else:
        if location_z >= offset and double_extrude:
            offset = center.z

        clamp = offset - thickness_clamp(op, context)
        location_z = location_z if location_z < clamp else clamp

    for i in front:
        points[i].co_deform.z = offset if preference.behavior.boolean_solver == 'FAST' else 0

    dpi_factor = screen.dpi_factor(ui_scale=False, integer=True)

    threshold = context.preferences.inputs.drag_threshold_mouse * 3 * dpi_factor
    distance = (op.mouse['location'] - op.last['mouse']).length / dpi_factor

    width = -(op.draw_exit_width - view3d.location2d_to_location3d(*op.mouse['location'], op.ray['location'])).length

    if preference.snap.mesh_element != 'NONE' and event.ctrl:
       location_z = element_snap(op, context, location_z)

    elif snap and event.ctrl or (snap_lock and not event.ctrl):

        if event.shift:
            location_z = round(round(location_z * 10 / increment_amount) * increment_amount, increment_length)
            location_z *= 0.1

        else:
            width = round(round(width / increment_amount) * increment_amount, increment_length)

    elif event.ctrl and preference.keymap.ctrl_multiplier > 0 and -width * preference.keymap.ctrl_multiplier > preference.shape.offset:
        width *= -width * preference.keymap.ctrl_multiplier

    if op.alt_toggle_extrude:
        op.alt_extrude = not op.alt_extrude

    view = context.region_data.view_rotation.to_matrix().to_4x4()
    view_changed = op.start['view_rotation'] != view
    view_locked = not view_changed and distance > threshold

    if preference.behavior.accucut and op.live and not view_locked and not view_changed:
        location_z = op.start['extrude']

    # view_extrude = False

    # if not op.modified:
    #     rounded = lambda matrix: [round(abs(matrix.decompose()[1][i]), 3) for i in range(4)]
    #     view_extrude = sorted(rounded(op.start['view_rotation'])) == sorted(rounded(op.start['matrix']))

    location_z = location_z if not preference.keymap.alternate_extrude or not op.alt_extrude or not op.live or not view_locked or op.mode in {'MAKE', 'JOIN'} or not op.clamp_extrude else width

    if event.ctrl and preference.shape.wedge or event.ctrl and op.shape_type == 'CUSTOM':
        location_z = copysign(preference.shape['dimension_x'] * op.datablock['shape_proportions'].z, location_z)

    op.last['depth'] = location_z if not preference.behavior.accucut or not op.live or op.modified or abs(location_z) < op.last['accucut_depth'] or preference.shape.wedge or op.mode in {'MAKE', 'JOIN'} or not op.alt_extrude or not op.clamp_extrude else -op.last['accucut_depth']

    thickness = op.last['depth'] - points[front[0]].co_deform.z

    if (thickness > 0 and not op.inverted_extrude) or (thickness < 0 and op.inverted_extrude):
        op.last['depth'] = -op.last['depth']

    if op.ngon_fit:
        for i in op.geo['indices']['offset']:
            if i < len(bc.shape.data.vertices):
                bc.shape.data.vertices[i].co.z = 0.5

    wedge(op, context, event=event)


def wedge(op, context, event=None):
    from . import bound_box

    preference = addon.preference()
    bc = context.scene.bc
    wedge_factor = preference.shape.wedge_factor
    wedge_width = preference.shape.wedge_width

    points = bc.lattice.data.points
    pairs = ((0, 1), (1, 3), (2, 3), (0, 2)) #y-, x+, y+, x-
    pair_axis = {0:'Y', 1:'X', 2:'Y', 3:'X'}
    axis_pair = {'-Y':0, '+X':1, '+Y':2, '-X':3}

    corner = center(Matrix(), 'front') * 2 - Vector(bound_box()[op.draw_dot_index])
    reference = op.last['draw_location'].to_2d() - corner.to_2d()

    if (not op.modified or not op.extruded) and not preference.shape.auto_depth:
        op.last['wedge_axis_map'] = dict()
        if abs(reference.x) < abs(reference.y):
            op.last['wedge_axis_map'][False] = 'X'
            op.last['wedge_axis_map'][True] = 'Y'

        else:
            op.last['wedge_axis_map'][False] = 'Y'
            op.last['wedge_axis_map'][True] = 'X'

    axis = op.last['wedge_axis_map'][bc.wedge_slim]

    signed_axis = ('-' if reference['XY'.index(axis)] > 0 else '+') + axis
    bc.wedge_point = axis_pair[signed_axis]

    # distance = [(op.last['draw_location'].to_2d() - points[i].co_deform.to_2d()).length for i in front]

    # reference = distance.index(max(distance))

    # length = 0.0
    # index = 0
    # for i, pair in enumerate(pairs):
    #     if reference in pair:
    #         current = (points[front[pair[0]]].co_deform.to_2d() - points[front[pair[1]]].co_deform.to_2d()).length

    #         if bc.wedge_slim:
    #             if not length or current < length:
    #                 length = current
    #                 index = i

    #             continue

    #         if current > length:
    #             length = current
    #             index = i

    # bc.wedge_point = index + bc.wedge_point_delta

    # if bc.wedge_point > 3:
    #     bc.wedge_point = (bc.wedge_point + 1 - 4) - 1

    lock = [back[pairs[bc.wedge_point][0]], back[pairs[bc.wedge_point][1]]]
    lock_offset = preference.shape.offset - 0.001 if preference.behavior.boolean_solver == 'FAST' else 0
    lock_val = points[front[0]].co_deform.z + (lock_offset if op.inverted_extrude else -lock_offset)
    clamp = points[front[0]].co_deform.z + thickness_clamp(op, context)

    factor_axis = 'XY'.index(pair_axis[bc.wedge_point])
    width_axis = 1 if factor_axis == 0 else 0

    op.last['wedge_points'] = lock
    front_center = center(Matrix(), side='front')

    if op.mode == 'JOIN' and preference.shape.wedge:
        lock_val *= -1

    if preference.shape.wedge and (op.operation != 'DRAW' or preference.shape.auto_depth) and event and event.ctrl:
        thickness = abs(reference[factor_axis]) * (0.5 + abs(0.5 - wedge_factor) )
        op.lazorcut = thickness < preference.shape.lazorcut_limit
        op.last['depth'] = lock_val + (thickness if op.inverted_extrude else -thickness)

    depth = op.last['depth']
    if op.mode == 'JOIN' and preference.shape.wedge and depth > 0:
        depth *= -1
        mesh.flip_normals(bc.shape.data)

    for bpoint, fpoint in zip(back, front):
        points[bpoint].co_deform.x = points[fpoint].co_deform.x
        points[bpoint].co_deform.y = points[fpoint].co_deform.y
        if bpoint in lock and preference.shape.wedge and not op.lazorcut:
            points[bpoint].co_deform.z = lock_val

            continue

        points[bpoint].co_deform.z = depth if depth else clamp
        if preference.shape.wedge:
            ref_vec = points[front[lock[0]]].co_deform

            points[bpoint].co_deform[factor_axis] = ref_vec[factor_axis] + ((points[fpoint].co_deform[factor_axis] - ref_vec[factor_axis]) * wedge_factor)
            points[bpoint].co_deform[width_axis] = front_center[width_axis] + ((points[fpoint].co_deform[width_axis] - front_center[width_axis]) * wedge_width)

    taper(op, context)


def taper(op, context, amount=0.0):
    preference = addon.preference()
    bc = context.scene.bc

    if not amount:
        amount = preference.shape.taper

    points = bc.lattice.data.points

    front_center = center(Matrix(), side='front')
    for index in back:
        if preference.shape.wedge and index in op.last['wedge_points']:
            continue

        point = points[index]
        point.co_deform.x = front_center.x + (point.co_deform.x - front_center.x) * amount
        point.co_deform.y = front_center.y + (point.co_deform.y - front_center.y) * amount


def fit(op, context, ngon=True):
    preference = addon.preference()
    bc = context.scene.bc

    for mod in bc.shape.modifiers:
        if mod.type == 'LATTICE':
            modifier.apply(bc.shape, mod)
            break

    tmp = bpy.data.objects.new('tmp', bc.shape.data)
    context.collection.objects.link(tmp)

    bounds = [Vector(v) for v in tmp.bound_box]
    bpy.data.objects.remove(tmp)

    center = math.coordinates_center(bounds)
    scale = math.coordinates_dimension(bounds)

    scale.x = 0.0001 if not scale.x else scale.x
    scale.y = 0.0001 if not scale.y else scale.y
    scale.z = 0.0001 if not scale.z or (not op.extruded and ngon) else scale.z

    if op.inverted_extrude:
        scale.z = -scale.z

    preference.shape['dimension_x'] = scale.x
    preference.shape['dimension_y'] = scale.y
    preference.shape['dimension_z'] = scale.z if not ngon or op.extruded else 0

    op.datablock['shape_proportions'] = scale / scale.x
    op.datablock['shape_proportions'].z = 1

    matrix = Matrix.Diagonal(scale).to_4x4()
    matrix.translation = center

    bm = bmesh.new()
    bm.from_mesh(bc.shape.data)

    bmesh.ops.transform(bm, verts=bm.verts , matrix=matrix.inverted())
    # bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

    bm.to_mesh(bc.shape.data)
    bc.shape.data.update()

    for point in bc.lattice.data.points:
        point.co_deform = point.co

    bc.lattice.data.transform(matrix)
    bc.lattice.data.points.update()

    if ngon and op.extruded and op.mode not in {'MAKE', 'JOIN'} or not op.ngon_fit:
        for index in back:
            bc.lattice.data.points[index].co_deform.z = op.last['depth']

    mod = bc.shape.modifiers.new(name='Lattice', type='LATTICE')
    mod.object = bc.lattice

    modifier.sort(bc.shape, types=['LATTICE'], first=True)

    context.view_layer.update()
    bc.lattice.matrix_world = bc.shape.matrix_world

    if ngon:
        op.draw_dot_index = 1

def element_snap(op, context, location_z) -> float:

    def nearest_edge_pair(eval_data, face_i, location) -> (Vector, Vector, Vector):
        smallest = sys.float_info.max
        v1 = Vector()
        v2 = Vector ()
        projection = Vector ()

        for i, j in eval_data.polygons[face_i].edge_keys:
            co1 = eval_data.vertices[i].co
            co2 = eval_data.vertices[j].co
            dloc = location - co1

            proj = dloc.project(co2 - co1)
            dist = (proj - dloc).magnitude

            if dist < smallest:
                smallest = dist
                projection = proj + co1
                v1 = co1.copy()
                v2 = co2.copy()

        return (v1, v2, projection)

    bc = context.scene.bc
    preference = addon.preference()
    element_type = preference.snap.mesh_element
    op.element_snap_vec = None

    coord2d = op.mouse['location']
    origin = region_2d_to_origin_3d(context.region, context.space_data.region_3d, coord2d)
    direction = region_2d_to_vector_3d(context.region, context.space_data.region_3d, coord2d)
    view_layer = context.view_layer if bpy.app.version[:2] < (2, 91) else context.view_layer.depsgraph
    hit, location, normal, index, object, matrix = context.scene.ray_cast(view_layer, origin, direction)

    if not hit or object.type != 'MESH': return location_z
    eval_data = object.evaluated_get(context.evaluated_depsgraph_get()).data

    if index > len(eval_data.polygons) - 1 : return location_z

    if element_type == 'VERT':
        local = matrix.inverted() @ location
        min_co = Vector()
        smallest = sys.float_info.max

        for i in eval_data.polygons[index].vertices:
            co = eval_data.vertices[i].co

            dist = (co - local).magnitude

            if dist < smallest:
                smallest = dist
                min_co = co

        op.element_snap_vec = bc.lattice.matrix_world.inverted() @ matrix @ min_co
        location_z = op.element_snap_vec.z

    elif element_type == 'EDGE':
        local = matrix.inverted() @ location

        *_, projection = nearest_edge_pair(eval_data, index, local)

        op.element_snap_vec = bc.lattice.matrix_world.inverted() @ ( matrix @ projection)
        location_z = op.element_snap_vec.z

    elif element_type == 'EDGE_CENTER':
        local = matrix.inverted() @ location

        v1, v2, _ = nearest_edge_pair(eval_data, index, local)
        center = (v1 + v2) * 0.5

        op.element_snap_vec = (bc.lattice.matrix_world.inverted() @ matrix @ center).z
        location_z = op.element_snap_vec.z

    elif element_type == 'FACE':
        op.element_snap_vec = bc.lattice.matrix_world.inverted() @ location
        location_z = op.element_snap_vec.z

    if preference.snap.mesh_element_exact and not preference.behavior.boolean_solver == 'EXACT':
        preference.behavior.boolean_solver = 'EXACT'

    return location_z
