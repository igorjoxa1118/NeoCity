import bpy
import bmesh

from math import cos, sin, radians, degrees
from mathutils import Vector, Matrix, geometry

from . import lattice
from ..... utility import addon, view3d, object, mesh
from . modal import flip


def index_weight(index, mesh=None, vert=False, value=None, member=False):
    bc = bpy.context.scene.bc

    #TODO: fix input value being negative
    if value:
        value = abs(value)

    mesh = bc.shape.data if not mesh else mesh

    if bpy.app.version < (4, ):
        if value is not None:
            if vert:
                mesh.vertices[index].bevel_weight = value
            else:
                mesh.edges[index].bevel_weight = value

        if member:
            return mesh.vertices[index] if vert else mesh.edges[index]

        return mesh.vertices[index].bevel_weight if vert else mesh.edges[index].bevel_weight

    attribute = F'bevel_weight_{"vert" if vert else "edge"}'

    if not mesh.attributes.get(attribute):
        mesh.attributes.new(attribute, 'FLOAT', 'POINT' if vert else 'EDGE')

    if value is not None:
        mesh.attributes[attribute].data[index].value = value

    if member:
        return mesh.attributes[attribute].data[index]

    return mesh.attributes[attribute].data[index].value


def bevel_weight_verify(bm):
    if bpy.app.version < (4, ):
        return bm.edges.layers.bevel_weight.verify()

    bevel = bm.edges.layers.float.get('bevel_weight_edge')

    if bevel is None:
        bevel = bm.edges.layers.float.new('bevel_weight_edge')

    return bevel


def crease_verify(bm):
    if bpy.app.version < (4, ):
        return bm.edges.layers.crease.verify()

    crease = bm.edges.layers.float.get('crease_edge')

    if crease is None:
        crease = bm.edges.layers.float.new('crease_edge')

    return crease


def thickness_clamp(context):
    bc = context.scene.bc
    factor = 0.005
    thickness = min(bc.lattice.dimensions[:-1]) * factor

    offset = preference.shape.offset if boolean_solver() == 'FAST' else 0

    return thickness if thickness < offset else offset - 0.001


def remove_point(op, context, event, index=-1, fill=True):
    preference = addon.preference()
    bc = context.scene.bc

    bm = bmesh.new()
    bm.from_mesh(bc.shape.data)

    bm.verts.ensure_lookup_table()
    if len(bm.verts) > 2 or index != -1:
        bm.verts.remove(bm.verts[index])

        if fill and len(bm.verts) > 2 and preference.shape.cyclic:
            bm.verts.ensure_lookup_table()
            bm.faces.new(bm.verts[:])

    bm.to_mesh(bc.shape.data)
    bm.free()

    op.geo['indices']['offset'] = [v.index for v in bc.shape.data.vertices]
    op.geo['indices']['top_edge'] = [e.index for e in bc.shape.data.edges]

    op.last['vert_weight'] = [index_weight(i, vert=True) for i in op.geo['indices']['offset']]


def add_point(op, context, event):
    preference = addon.preference()
    bc = context.scene.bc

    bm = bmesh.new()
    bm.from_mesh(bc.shape.data)

    if len(bm.verts) > 2:
        if len(bm.faces):
            bm.faces.ensure_lookup_table()
            bm.faces.remove(bm.faces[0])

    if len(bm.edges) == len(bm.verts):
        bm.edges.ensure_lookup_table()
        bm.edges.remove(bm.edges[-1])

    bm.verts.ensure_lookup_table()
    bm.verts.new((0.0, 0.0, 0.0))

    # if bpy.app.version[:2] < (3, 4):
    #   if bc.shape.data.use_customdata_vertex_bevel:
    #     new[bm.verts.layers.bevel_weight.verify()] = 1

    bm.verts.ensure_lookup_table()
    bm.edges.new(bm.verts[-2:])

    if len(bm.verts) > 2 and preference.shape.cyclic:
        bm.edges.ensure_lookup_table()
        bm.edges.new([bm.verts[0], bm.verts[-1]])

        bm.faces.ensure_lookup_table()
        bm.faces.new(bm.verts[:])

    bm.to_mesh(bc.shape.data)
    bm.free()

    op.geo['indices']['offset'] = [v.index for v in bc.shape.data.vertices]
    op.geo['indices']['top_edge'] = [e.index for e in bc.shape.data.edges]

    op.last['vert_weight'] = [index_weight(i, vert=True) for i in op.geo['indices']['offset']]


# TODO: edge length based on increment snap, snap to draw dots
def draw(op, context, event):
    bc = context.scene.bc
    preference = addon.preference()

    if preference.keymap.alt_preserve and op.alt and not op.alt_skip:
        return {'PASS_THROUGH'}

    location_x = op.view3d['location'].x

    snap = preference.snap.enable and (preference.snap.incremental or (preference.snap.grid and bc.snap.display))
    snap_lock = snap and preference.snap.increment_lock
    snap_angle_lock = not bc.snap.display and ((preference.snap.angle_lock and not event.ctrl) or (not preference.snap.angle_lock and event.ctrl))

    if bc.snap.operator and hasattr(bc.snap.operator, 'grid_handler'):
        grid_handler = bc.snap.operator.grid_handler

        if grid_handler.snap_type == 'DOTS':
            if preference.snap.dot_dot_snap:
                grid_handler.update(context, event)

                if grid_handler.nearest_dot:
                    location = bc.shape.matrix_world.inverted() @ grid_handler.snap_world
                    op.view3d['location'].x = location.x
                    op.view3d['location'].y = location.y
                    location_x = op.view3d['location'].x

                    snap = snap_lock = snap_angle_lock = False

        else:
            grid_handler.mode = 'NONE'

            grid_lock = preference.snap.increment_lock and preference.snap.grid
            grid_handler.draw = (grid_lock or grid_handler.frozen) != event.ctrl
            grid_handler.update(context, event)

            location = bc.shape.matrix_world.inverted() @ grid_handler.snap_world
            op.view3d['location'].x = location.x
            op.view3d['location'].y = location.y
            location_x = op.view3d['location'].x

            snap = snap_lock = snap_angle_lock = False

    lasso = preference.shape.lasso

    if bc.shape.bc.array and bc.shape.bc.array_circle:
        displace = None

        for mod in bc.shape.modifiers:
            if mod.type == 'DISPLACE':
                displace = mod

                break

        if displace:
            location_x = op.view3d['location'].x - displace.strength / 2

    index = op.ngon_point_index if op.ngon_point_index < len(bc.shape.data.vertices) else -1

    vert = bc.shape.data.vertices[index]

    if op.add_point_lock and op.ngon_point_index != -1:
        op.add_point_lock = False

    if not op.add_point and not op.add_point_lock:
        increment_amount = round(preference.snap.increment, 8) * 10
        split = str(increment_amount).split('.')[1]
        increment_length = len(split) if int(split) != 0 else 0

        vert.co = (location_x, op.view3d['location'].y, vert.co.z)

        if not lasso and len(bc.shape.data.vertices) > 2:
            point1 = vert.co.xy

            n = index+1 if index+2 < len(bc.shape.data.vertices) else 0
            point2 = bc.shape.data.vertices[n].co.xy

            l = index+2 if index+3 < len(bc.shape.data.vertices) else 1
            point3 = bc.shape.data.vertices[l].co.xy

            point_origin = vert.co.xy

            edge_angle = (point3 - point2).angle_signed(Vector((1, 0)), 0.0)

            delta = point1 - point3
            angle = delta.angle_signed(Vector((1, 0)), 0.0)

            step = radians(90)

            angle = round((angle - edge_angle)/step) * step + edge_angle

            if abs(round(degrees(angle - edge_angle))) not in {89, 90, 91, 269, 270, 271}:
                angle += radians(90)

            direction = Vector((cos(angle), sin(angle)))

            point1 = point3 + delta.project(direction)

            vert.co = Vector((point1.x, point1.y, vert.co.z))

            edge_angle = (point1 - point3).angle_signed(Vector((1, 0)), 0.0)

            delta = point_origin - point1
            angle = delta.angle_signed(Vector((1, 0)), 0.0)

            step = radians(90)

            angle = round((angle - edge_angle)/step) * step + edge_angle
            direction = Vector((cos(angle), sin(angle)))

            projection = point1 + delta.project(direction)

            vert.co = Vector((projection.x, projection.y, vert.co.z))

        elif lasso and preference.shape.lasso_spacing > 0 and len(bc.shape.data.vertices) > 1 and not event.shift:
            if not op.lasso_view_factor:
                if preference.shape.lasso_adaptive:

                    orig1 = view3d.location2d_to_origin3d(0,0)
                    orig2 = view3d.location2d_to_origin3d( context.region.width, context.region.height)

                    ray1 = view3d.location2d_to_vector3d(0,0)
                    ray2 = view3d.location2d_to_vector3d(context.region.width, context.region.height)

                    alignment = Matrix.Translation(op.start['matrix'].translation) @ context.region_data.view_rotation.to_matrix().to_4x4()

                    v1 = alignment @ Vector((0,1,0))
                    v2 = alignment @ Vector((1,-1,0))
                    v3 = alignment @ Vector((-1,-1,0))

                    vec1 = geometry.intersect_ray_tri(v1, v2, v3, ray1, orig1, False)
                    vec2 = geometry.intersect_ray_tri(v1, v2, v3, ray2, orig2, False)

                    if not vec1:
                        vec1 = geometry.intersect_ray_tri(v1, v2, v3, -ray1, orig1, False)

                    if not vec2:
                        vec2 = geometry.intersect_ray_tri(v1, v2, v3, -ray2, orig2, False)

                    op.lasso_view_factor = (vec2 - vec1).length/8 if (vec1 and vec2) else 1

                else:
                    op.lasso_view_factor = 1

            lasso_spacing = op.lasso_view_factor*preference.shape.lasso_spacing

            vert.co.z = 0
            prev_point_co = bc.shape.data.vertices[index - 1].co
            prev_point_co.z = 0
            delta = vert.co - prev_point_co

            unit_vector = Vector((0, 0, 1))
            delta_quat = delta.rotation_difference(unit_vector)
            unit_vector.rotate(delta_quat)

            bm = bmesh.new()
            bm.from_mesh(bc.shape.data)
            bm.verts.ensure_lookup_table()

            last_index = len(bm.verts) - 1
            num = int(delta.length / lasso_spacing)

            last_vert = bm.verts[last_index]

            bmesh.ops.delete(bm, geom=[last_vert], context='VERTS')

            for i in range(1, num):
                vec = prev_point_co - (unit_vector * lasso_spacing * i)
                bm.verts.new(vec)

            bm.verts.ensure_lookup_table()

            if preference.shape.cyclic:
                if len(bm.verts) > 2:
                    bmesh.ops.delete(bm, geom=bm.edges, context='EDGES_FACES')
                    bm.faces.new(bm.verts)

            else:
                for i in range(num - 1):
                    bm.edges.new((bm.verts[last_index - 1 + i], bm.verts[last_index + i]))

            bm.to_mesh(bc.shape.data)
            bc.shape.data.update()
            bm.free()

        if (snap and event.ctrl or snap_lock or snap_angle_lock) and not lasso:
            if ((snap and event.ctrl) or snap_lock) and not snap_angle_lock:
                if not preference.snap.static_grid and preference.snap.grid and bc.snap.display:
                    location = bc.shape.matrix_world.inverted() @ Vector(bc.snap.location)
                    location_x = location.x
                    location_y = location.y

                else:
                    location_x = round(round(vert.co.x * 10 / increment_amount) * increment_amount, increment_length)
                    location_x *= 0.1
                    location_y = round(round(vert.co.y * 10 / increment_amount) * increment_amount, increment_length)
                    location_y *= 0.1

                vert.co = Vector((location_x, location_y, vert.co.z))

            elif snap_angle_lock:
                # step = pi*2/(360/preference.snap.ngon_angle)
                step = 0.017453292519943295 * preference.snap.ngon_angle

                point1 = vert.co.xy
                point2 = bc.shape.data.vertices[index-1].co.xy
                point3 = None

                edge_angle = 0.0

                if preference.snap.ngon_previous_edge and len(bc.shape.data.vertices) > 2:
                    point3 = bc.shape.data.vertices[index-2].co.xy
                    edge_angle = (point2 - point3).angle_signed(Vector((1, 0)), 0.0)

                delta = point1 - point2
                angle = round((delta.angle_signed(Vector((1, 0)), 0.0) - edge_angle)/step)*step + edge_angle

                direction = Vector((cos(angle), sin(angle)))
                projection = point2 + delta.project(direction)

                if bc.shader and bc.shader.widgets.active and bc.shader.widgets.active.type == 'SNAP' and bc.shader.widgets.active.highlight:
                    vert.co = bc.shader.widgets.active.location
                elif op.shape_type != 'BOX' or op.ngon_fit:
                    vert.co = Vector((projection.x, projection.y, vert.co.z))

        # vert.co.z = 0.0 if not op.inverted_extrude else op.last['depth']

        if op.ngon_fit or op.shape_type == 'BOX':
            indices = op.geo['indices']
            sides = ('extrusion', 'offset')
            flip = op.inverted_extrude

            side = indices[sides[not flip]]
            if index in side:
                oppo = indices[sides[flip]]
                oppo_index = side.index(index)

                if oppo_index < len(oppo) and oppo[oppo_index] < len(bc.shape.data.vertices):
                    back_point = bc.shape.data.vertices[oppo[oppo_index]]
                    prev_z = back_point.co.z
                    back_point.co = vert.co

                    back_point.co.z = prev_z

    op.last['draw_location'] = op.view3d['location']


def offset(op, context, event):
    preference = addon.preference()
    offset = preference.shape.offset if boolean_solver() == 'FAST' else 0

    if op.mode == 'MAKE':
        offset = 0

    # offset = preference.shape.offset

    # if not op.modified:
    #     if op.mode == 'MAKE':
    #         offset = 0
    #     elif op.mode == 'JOIN':
    #         offset = -offset
    # else:
    #     offset = 0

    bc = context.scene.bc
    snap = preference.snap.enable and (preference.snap.incremental or preference.snap.grid)
    snap_lock = snap and preference.snap.increment_lock

    if not op.extruded:
        extrude(op, context, event)

    location_z = op.view3d['location'].z

    if snap and event.ctrl or snap_lock:
        increment_amount = round(preference.snap.increment, 8)
        split = str(increment_amount).split('.')[1]
        increment_length = len(split) if int(split) != 0 else 0

        if event.shift:
            location_z = round(round(location_z * 10 / increment_amount) * increment_amount, increment_length)
            location_z *= 0.1

        else:
            location_z = round(round(location_z / increment_amount) * increment_amount, increment_length)

    location = location_z + offset
    matrix = op.start['matrix'] @ Matrix.Translation(Vector((0, 0, location)))

    points = {bc.shape.data.vertices[point] for point in op.geo['indices']['extrusion']}
    opposite_point_co = [v for v in bc.shape.data.vertices if v not in points][0].co.z

    thickness = opposite_point_co - (-location_z + op.start['extrude'])
    limit = 0.001

    if thickness < limit:
        clamp = limit - thickness
        quat = bc.shape.matrix_world.to_quaternion()
        scale = bc.shape.matrix_world.to_scale()
        clamp_vector = quat @ Vector((0, 0, clamp * scale.z))

        location_z += clamp
        matrix.translation += clamp_vector

    bc.shape.matrix_world.translation = matrix.translation
    bc.lattice.matrix_world.translation = matrix.translation

    for point in points:
        point.co.z = -location_z + op.start['extrude']


def extrude(op, context, event, extrude_only=True, amount=-0.001):
    preference = addon.preference()
    bc = context.scene.bc
    snap = preference.snap.enable and (preference.snap.incremental or preference.snap.grid)
    snap_lock = snap and preference.snap.increment_lock
    shape = bc.shape

    if not op.extruded:
        bm = bmesh.new()
        bm.from_mesh(shape.data)

        op.geo['indices']['offset'] = [vert.index for vert in bm.verts[:]]
        initial_verts = bm.verts[:]

        top_face = None
        if bm.faces:
            top_face = bm.faces[:][0]
            top_verts = set(bm.verts)

        ret = bmesh.ops.extrude_face_region(bm, geom=bm.edges[:] + bm.faces[:])
        extruded_verts = [ele for ele in ret['geom'] if isinstance(ele, bmesh.types.BMVert)]
        op.geo['indices']['extrusion'] = [vert.index for vert in extruded_verts]

        if top_face:
            op.geo['indices']['top_face'] = [top_face.index]
            op.geo['indices']['bot_face'] = [f.index for f in extruded_verts[0].link_faces  if not top_verts.intersection(f.verts)]
        del ret

        for point in extruded_verts:
            point.co.z = amount

        mid_edges = []
        bot_edges = [e for e in bm.edges if (e.verts[0] in extruded_verts and e.verts[1] in extruded_verts)]

        initial_set = set(initial_verts)
        for v in initial_verts:
            for e in v.link_edges:
                if not initial_set.issuperset(e.verts):
                    mid_edges.append(e)

        op.geo['indices']['mid_edge'] = [edge.index for edge in mid_edges]
        op.geo['indices']['bot_edge'] = [edge.index for edge in bot_edges]

        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

        if preference.behavior.auto_smooth:
            for f in bm.faces:
                f.smooth = True

        bm.to_mesh(shape.data)
        bm.free()

        shape.data.update()

        for front in op.geo['indices']['offset']:
            vert = bc.shape.data.vertices[front]

            for index in op.geo['indices']['mid_edge']:
                edge = bc.shape.data.edges[index]

                if vert.index not in edge.vertices:
                    continue

                index_weight(edge.index, value=index_weight(front, vert=True))

        op.extruded = True

    if not extrude_only: # TODO: rename: ignore_input
        location_z = op.view3d['location'].z

        if snap and event.ctrl or snap_lock:
            increment_amount = round(preference.snap.increment, 8)
            split = str(increment_amount).split('.')[1]
            increment_length = len(split) if int(split) != 0 else 0

            if event.shift:
                location_z = round(round(location_z * 10 / increment_amount) * increment_amount, increment_length)
                location_z *= 0.1

            else:
                location_z = round(round(location_z / increment_amount) * increment_amount, increment_length)

        points = {shape.data.vertices[i] for i in op.geo['indices']['extrusion']}
        opposite_point_co = [v for v in shape.data.vertices if v not in points][0].co.z
        limit = opposite_point_co - 0.001
        location_z = location_z if location_z < limit else limit

        for point in points:
            point.co.z = location_z

        shape.data.update()

    # if op.shape_type == 'NGON' and preference.behavior.draw_line and len(bc.shape.data.vertices) > 2 and preference.shape.wedge:
    #     for face in bc.shape.data.polygons:
    #         if 0 in face.vertices[:] and 1 in face.vertices[:]:
    #             for index in face.vertices[:]:
    #                 if index in op.geo['indices']['extrusion']:
    #                     bc.shape.data.vertices[index].co.z = -0.001


def vertex_group(op, context, event, q_only=False):
    bc = context.scene.bc
    shape = bc.shape

    if (op.shape_type == 'NGON' or op.ngon_fit and not op.extruded):
        return

    if (op.shape_type == 'CIRCLE' and addon.preference().shape.circle_type == 'MODIFIER'):
        if 'bottom' not in shape.vertex_groups:
            group = shape.vertex_groups.new(name='bottom')
            indices = ([0] if shape.data.vertices[0].co.z < 0 else [1])
            group.add(index=indices, weight=1.0, type='ADD')

    if not q_only:
        mid_group = None
        for grp in shape.vertex_groups:
            if grp.name[:4] == 'edge':
                mid_group = grp
                break

        if not mid_group:
            for index, mid_edge in enumerate(op.geo['indices']['mid_edge']):
                group = shape.vertex_groups.new(name=F'edge{index + 1}')
                group.add(index=shape.data.edges[mid_edge].vertices[:], weight=1.0, type='ADD')

    bot_group = None
    for grp in shape.vertex_groups:
        if grp.name == 'bottom':
            bot_group = grp
            break

    if not bot_group and shape.data.bc.q_beveled:
        verts = []
        for index in op.geo['indices']['bot_edge']:
            for vert_index in shape.data.edges[index].vertices:
                if vert_index not in verts:
                    verts.append(vert_index)

        group = shape.vertex_groups.new(name='bottom')
        group.add(index=verts, weight=1.0, type='ADD')

    elif (op.shape_type != 'CIRCLE' or addon.preference().shape.circle_type != 'MODIFIER') and bot_group and not shape.data.bc.q_beveled:
        shape.vertex_groups.remove(shape.vertex_groups['bottom'])


def bevel_weight(op, context, event):
    bc = context.scene.bc
    preference = addon.preference()
    shape = bc.shape

    # if op.shape_type == 'NGON' or op.ngon_fit:
    #     return

    if (op.shape_type == 'CIRCLE' and preference.shape.circle_type == 'MODIFIER') or bc.q_back_only:
        vertex_group(op, context, event, q_only=True)

        return

    if bpy.app.version[:2] < (3, 4):
        shape.data.use_customdata_vertex_bevel = True
        shape.data.use_customdata_edge_bevel = True

    ngon = op.shape_type == 'NGON' or op.ngon_fit
    boxgon = op.shape_type == 'BOX' and not op.ngon_fit and (op.ngon_point_index != -1 or op.ngon_point_bevel)

    if not ngon and not boxgon:
        for vindex in op.geo['indices']['offset']:
            vert = bc.shape.data.vertices[vindex]

            value = index_weight(vindex, vert=True)
            index_weight(vindex, vert=True, value=1.0 if not value else value)

        for vindex in op.geo['indices']['offset']:
            for eindex in op.geo['indices']['mid_edge']:
                index_weight(eindex, value=index_weight(vindex, vert=True))

    if preference.shape.quad_bevel:
        vertex_group(op, context, event, q_only=True)

        if preference.shape.bevel_both:
            for index in op.geo['indices']['top_edge']:
                index_weight(index, value=shape.data.bc.q_beveled and op.flip_z)

        return

    for index in op.geo['indices']['bot_edge']:
        index_weight(index, value=shape.data.bc.q_beveled)


def knife(op, context, event):
    from . import dimensions
    bc = context.scene.bc

    targets = op.datablock['targets']
    overrides = op.datablock['overrides']

    original_active = context.active_object
    original_selected = context.selected_objects[:]

    # dimension_z = bc.lattice.dimensions[2]
    dimension_z = dimensions()[2]
    lazorcut_limit = addon.preference().shape.lazorcut_limit
    too_thin = dimension_z < lazorcut_limit and not op.extruded
    aligned = not op.extruded and op.align_to_view

    if (not op.extruded or too_thin or aligned) and not op.lazorcut_performed:
        return

    for obj in targets:
        obj.select_set(True)

    context.view_layer.objects.active = bc.original_active
    bpy.ops.object.mode_set(mode='EDIT')

    if not op.datablock['overrides']:
        bpy.ops.mesh.select_all(action='DESELECT')

        for obj in targets:
            obj.update_from_editmode()

        overrides = op.datablock['overrides'] = [obj.data.copy() for obj in targets]

    bc.shape.matrix_world.translation = bc.shape.location

    evaluated = bc.shape.evaluated_get(context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()

    for poly in mesh.polygons:
        poly.select = True

    target = []
    for pair in zip(targets, overrides):
        obj = pair[0]
        override = pair[1]
        bm = bmesh.from_edit_mesh(obj.data)

        bmesh.ops.delete(bm, geom=bm.verts, context='VERTS')

        bm.from_mesh(override)
        bm.from_mesh(mesh)

        faces = [f for f in bm.faces if f.select]
        verts = list({vert for face in faces for vert in face.verts})

        bmesh.ops.transform(bm, matrix=obj.matrix_world.inverted() @ bc.shape.matrix_world, verts=verts)
        bmesh.update_edit_mesh(obj.data)

        target.append((obj, bm, faces))

    if bpy.app.version[:2] < (2, 91):
        bpy.ops.mesh.intersect(mode='SELECT_UNSELECT', separate_mode='CUT')

    else:
        bpy.ops.mesh.intersect(mode='SELECT_UNSELECT', separate_mode='CUT', solver='FAST')

    for trio in target:
        obj = trio[0]
        bm = trio[1]
        faces = trio[2]

        while True:
            region_extend = bmesh.ops.region_extend(bm, geom=faces, use_faces=True, use_face_step=True)

            if not region_extend['geom']:
                break

            faces.extend(region_extend['geom'])

        bmesh.ops.delete(bm, geom=faces, context='FACES')

        hops = addon.hops()
        if hops and addon.preference().behavior.hops_mark:
            pref = hops.property
            bevel = 0.0

            bevel = bevel_weight_verify(bm)
            crease = crease_verify(bm)
            edges = [edge for edge in bm.edges if edge.select]

            for edge in edges:
                edge[crease] = pref.sharp_use_crease
                edge[bevel] = pref.sharp_use_bweight
                edge.seam = pref.sharp_use_seam
                edge.smooth = not pref.sharp_use_sharp

        bmesh.update_edit_mesh(obj.data)

    bpy.ops.mesh.normals_make_consistent(inside=False)
    # bpy.ops.mesh.loop_to_region()

    evaluated.to_mesh_clear()

    del targets
    del overrides

    if op.original_mode == 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

    bpy.context.view_layer.objects.active = original_active

    del original_active

    for obj in original_selected:
        obj.select_set(True)

    del original_selected


def inset(op, context, event):
    pass


def pivot(op, context, transform=True):
    bc = context.scene.bc
    preference = addon.preference()

    if bc.shape and not bc.shape.bc.array_circle:
        eval = bc.shape.evaluated_get(context.evaluated_depsgraph_get())

        if preference.behavior.set_origin == 'MOUSE':

            return Vector()

        elif preference.behavior.set_origin == 'CENTER':
            bounds = [eval.bound_box[i] for i in (1, 2, 5, 6)]
            local_location = 0.25 * sum((Vector(b) for b in bounds), Vector())
            global_location = bc.shape.matrix_world @ local_location

        elif preference.behavior.set_origin == 'BBOX':
            local_location = 0.125 * sum((Vector(b) for b in eval.bound_box), Vector())
            global_location = bc.shape.matrix_world @ local_location

        elif preference.behavior.set_origin == 'ACTIVE':
            local_location = bc.shape.matrix_world.inverted() @ bc.original_active.matrix_world.translation
            global_location = bc.original_active.matrix_world.normalized()

        if transform:

            if op.shape_type == 'CIRCLE' and preference.behavior.keep_screw:
                local_location = sum((bc.shape.data.vertices[i].co for i in (2, 3)), Vector()) / 2
                global_location = bc.shape.matrix_world @ local_location

            object.set_origin(bc.shape, global_location)

        return local_location

    elif bc.shape and bc.shape.bc.array_circle and preference.shape.array_around_cursor:
        cursor_location = context.scene.cursor.location
        local_location = bc.shape.matrix_world.inverted() @ cursor_location
        global_location = cursor_location

        if transform:
            bc.shape.location = global_location
            bc.shape.data.transform(Matrix.Translation(-local_location))

        return local_location

    return Vector()


def eval_shape(context):
    bc = context.scene.bc

    mods = []
    for mod in bc.shape.modifiers[:]:
        if mod.type in {'BEVEL', 'ARRAY', 'SOLIDIFY', 'SCREW', 'MIRROR', 'WELD'}:
            mod.show_viewport = False
            mods.append(mod)

    eval = bc.shape.evaluated_get(context.evaluated_depsgraph_get()).data
    new_vert = lambda v: type('vertex', (), {'co': v.co.xyz, 'index': v.index})
    new_edge = lambda e: type('edge', (), {'vertices': e.vertices, 'index': e.index})
    shape = type('shape', (), {
        'vertices': [new_vert(v) for v in eval.vertices],
        'edges': [new_edge(e) for e in eval.edges],
    })

    for mod in mods:
        mod.show_viewport = True

    return shape


class create:

    @staticmethod
    def shape(op, context, event):
        preference = addon.preference()
        bc = context.scene.bc

        verts = [
            Vector((-0.5, -0.5, 0.0)), Vector(( 0.5, -0.5, 0.0)),
            Vector((-0.5,  0.5, 0.0)), Vector(( 0.5,  0.5, 0.0))]

        edges = [
            (0, 2), (0, 1),
            (1, 3), (2, 3)]

        faces = [(0, 1, 3, 2)]

        dat = bpy.data.meshes.new(name='Plane')
        dat.bc.removeable = True

        dat.from_pydata(verts, edges, faces)
        dat.validate()

        op.datablock['plane'] = bpy.data.objects.new(name='Plane', object_data=dat)
        bc.plane = op.datablock['plane']

        verts = [
            Vector((-0.5, -0.5, -0.5)), Vector((-0.5, -0.5,  0.5)),
            Vector((-0.5,  0.5, -0.5)), Vector((-0.5,  0.5,  0.5)),
            Vector(( 0.5, -0.5, -0.5)), Vector(( 0.5, -0.5,  0.5)),
            Vector(( 0.5,  0.5, -0.5)), Vector(( 0.5,  0.5,  0.5))]

        edges = [
            (0, 2), (0, 1), (1, 3), (2, 3),
            (2, 6), (3, 7), (6, 7), (4, 6),
            (5, 7), (4, 5), (0, 4), (1, 5)]

        faces = [
            (0, 1, 3, 2), (2, 3, 7, 6),
            (6, 7, 5, 4), (4, 5, 1, 0),
            (2, 6, 4, 0), (7, 3, 1, 5)]

        op.geo['indices']['offset'] = [1, 3, 5, 7]

        if op.shape_type != 'NGON' and not op.ngon_fit:
            op.geo['indices']['extrusion'] = [0, 2, 4, 6]

        dat = bpy.data.meshes.new(name=F'Bound Box')
        dat.bc.removeable = True

        dat.from_pydata(verts, edges, faces)
        dat.validate()

        op.last['vert_weight'] = [index_weight(i, mesh=dat, vert=True) for i in op.geo['indices']['offset']]

        del dat

        op.geo['indices']['top_face'] = []
        op.geo['indices']['bot_face'] = []

        op.geo['indices']['bot_edge'] = []
        op.geo['indices']['mid_edge'] = []
        op.geo['indices']['top_edge'] = []

        if op.shape_type == 'BOX':
            if bpy.app.version[:2] >= (2, 91) and bpy.app.version[:2] < (4, 2):
                op.geo['indices']['bot_edge'] = [2, 4, 6, 11]
                op.geo['indices']['mid_edge'] = [0, 1, 5, 10]
                op.geo['indices']['top_edge'] = [3, 7, 8, 9]
            else:
                op.geo['indices']['bot_edge'] = [0, 4, 7, 10]
                op.geo['indices']['mid_edge'] = [1, 3, 6, 9]
                op.geo['indices']['top_edge'] = [2, 5, 8, 11]

            op.geo['indices']['top_face'] = [5]
            op.geo['indices']['bot_face'] = [4]

        elif op.shape_type == 'CIRCLE':
            verts = [
                Vector((0.0, -0.5, -0.5)), Vector((0.0, -0.5,  0.5)),
                Vector((0.0,  0.0, -0.5)), Vector((0.0,  0.0,  0.5))]

            edges = [(0, 2), (0, 1), (1, 3)]

            faces = []

            op.geo['indices']['top_edge'] = [2]
            op.geo['indices']['mid_edge'] = [1]
            op.geo['indices']['bot_edge'] = [0]


        elif op.shape_type == 'NGON':
            verts = [Vector((0.0, 0.0, 0.0)), Vector((0.0, 0.0, 0.0))]

            edges = [(0, 1)]

            faces = []

            op.geo['indices']['top_edge'] = []
            op.geo['indices']['mid_edge'] = []
            op.geo['indices']['bot_edge'] = []

        dat = bpy.data.meshes.new(name='Cutter')

        dat.from_pydata(verts, edges, faces, shade_flat=True)

        if op.shape_type == 'CIRCLE' and bc.snap.hit:
            dat.transform(Matrix.Rotation(radians(0.002), 4, Vector((0, 0, 1))))

        dat.validate()

        if op.shape_type == 'BOX' and preference.shape.box_grid:
            create_shape(dat, shape_type='GRID', operator=op)

        bc.shape = bpy.data.objects.new(name='Cutter', object_data=dat)
        bc.shape.bc.array_axis = preference.shape.array_axis

        del dat

        bc.shape.bc.shape = True

        bc.collection.objects.link(bc.shape)
        # bc.shape.hide_render = True

        if op.mode != 'MAKE':
            bc.shape.display_type = 'WIRE'

            object.hide_set(bc.shape, True, viewport=False)

        if addon.preference().behavior.auto_smooth:
            if bpy.app.version < (4, 1):
                bc.shape.data.use_auto_smooth = True

            for face in bc.shape.data.polygons:
                face.use_smooth = True

        if op.shape_type == 'CIRCLE':
            circle_type = addon.preference().shape.circle_type

            if circle_type == 'MODIFIER':
                mod = bc.shape.modifiers.new(name='Screw', type='SCREW')
                mod.steps = preference.shape.circle_vertices
                mod.render_steps = mod.steps
                mod.use_normal_calculate = True
                mod.use_normal_flip = True
                mod.use_smooth_shade = True
                mod.use_merge_vertices = True
                mod.merge_threshold = 0.0000001

                mod = bc.shape.modifiers.new(name='Decimate', type='DECIMATE')
                mod.decimate_type = 'DISSOLVE'
                mod.angle_limit = radians(1)
                mod.use_dissolve_boundaries = True

            else:
                create_shape(bc.shape.data, shape_type=circle_type, operator=op)

        if addon.preference().behavior.cutter_uv:
            bc.shape.data.uv_layers.new(name='UVMap', do_init=True)

        if bpy.app.version[:2] < (3, 4):
            bc.shape.data.use_customdata_vertex_bevel = True
            bc.shape.data.use_customdata_edge_bevel = True
            bc.shape.data.use_customdata_edge_crease = True


def create_shape(me, shape_type='GRID', operator=None):
    bm = bmesh.new()
    shape = addon.preference().shape

    bot_faces = []
    top_faces = []
    top_verts = []
    bot_verts = []

    if shape_type == 'GRID':
        x, y = shape.box_grid_divisions
        top_verts, bot_verts = bmesh_grid(bm, x=x, y=y, boundary=shape.box_grid_border, fill_bottom=shape.box_grid_fill_back)

    elif shape_type == 'POLYGON':
        top_faces, bot_faces, top_verts, bot_verts = bmesh_polygon(bm, segments=shape.circle_vertices)

    elif shape_type == 'STAR':
        top_faces, bot_faces, top_verts, bot_verts = bmesh_star(bm, points=shape.circle_vertices, factor=shape.circle_star_factor)

    elif shape_type == 'BOX':
        bmesh.ops.create_cube(bm, size=1)
        bot_faces = [face.index for face in bm.faces if all([vert.co.z < 0 for vert in face.verts])]
        top_faces = [face.index for face in bm.faces if all([vert.co.z > 0 for vert in face.verts])]
        top_verts = [v.index for v in bm.verts if v.co.z > 0]
        bot_verts = [v.index for v in bm.verts if v.co.z < 0]

    z_plus = []
    middle = []
    z_minus = []

    for edge in bm.edges:
        v1,v2 = edge.verts

        if v1.co[2] == v2.co[2]:
            if v1.co[2] > 0:
                z_plus.append(edge.index)
            else:
                z_minus.append(edge.index)
        else:
            middle.append(edge.index)

    if addon.preference().behavior.auto_smooth:
        for face in bm.faces:
            face.smooth = True

    bm.to_mesh(me)
    bm.free()
    me.update()

    if operator:
        operator.geo['indices']['top_edge'] = z_plus
        operator.geo['indices']['mid_edge'] = middle
        operator.geo['indices']['bot_edge'] = z_minus
        operator.geo['indices']['top_face'] = top_faces
        operator.geo['indices']['bot_face'] = bot_faces
        operator.geo['indices']['offset'] = top_verts
        operator.geo['indices']['extrusion'] = bot_verts

        bc = bpy.context.scene.bc

        if shape_type == 'GRID' and not operator.extruded:
            for i in top_verts:
                me.vertices[i].co.z += 0.005

        if bc.shape and [mod for mod in bc.shape.modifiers if mod.type == 'BEVEL']:
            if operator.shape_type == 'CIRCLE' and addon.preference().shape.circle_type == 'POLYGON' and addon.preference().shape.circle_vertices > 12:
                operator.geo['indices']['mid_edge'] = []

            bc.shape.vertex_groups.clear()
            bevel_weight(operator, bpy.context, None)

            if bc.bevel_front_face and (bc.q_bevel and not bc.q_back_only and operator.geo['indices']['top_face']):
                mesh.recalc_normals(bc.shape, face_indices=operator.geo['indices']['top_face'], inside=not operator.inverted_extrude)

            if operator.flip_z:
                flip.shape(operator, bpy.context, None, report=False)

    return z_plus, middle, z_minus


def bmesh_grid(bm, x=5, y=5, boundary=True, extrude=0.5, fill_bottom=False):
    xp_yp = bm.verts.new((0.5, 0.5, -extrude))
    xn_yp = bm.verts.new((-0.5, 0.5, -extrude))
    xn_yn = bm.verts.new((-0.5, -0.5, -extrude))
    xp_yn = bm.verts.new((0.5, -0.5, -extrude))
    xn_e = bm.edges.new((xn_yp, xn_yn))
    xp_e = bm.edges.new((xp_yn, xp_yp))
    yn_e = bm.edges.new((xn_yn, xp_yn))
    yp_e = bm.edges.new((xp_yp, xn_yp))

    bmesh.ops.subdivide_edges(bm, edges=(xn_e, xp_e), cuts=x)
    out = bmesh.ops.subdivide_edges(bm, edges=(yn_e, yp_e), cuts=y)
    loops = [elem for elem in out['geom'] if isinstance(elem, bmesh.types.BMEdge)]
    bmesh.ops.grid_fill(bm, edges=loops, use_interp_simple=True)

    if not boundary and (x or y):
        bmesh.ops.delete(bm, geom=[e for e in bm.edges if e.is_boundary], context ='EDGES')

    if not fill_bottom:
        bmesh.ops.delete(bm, geom=bm.faces, context ='FACES_ONLY')

    elif bm.faces and not boundary:
        bmesh.ops.delete(bm, geom=[e for e in bm.edges if e.is_wire], context ='EDGES')

    z_minus_vi = [v.index for v in bm.verts]

    extrusion = bmesh.ops.extrude_edge_only(bm, edges=bm.edges, use_normal_flip=True)
    generated_verts = [v for v in extrusion['geom'] if type(v) == bmesh.types.BMVert]
    bmesh.ops.translate(bm, verts=generated_verts, vec=[0,0, extrude*2])

    return [v.index for v in generated_verts], z_minus_vi


def bmesh_polygon(bm, segments=6, grid=False, boundary=True, extrude=0.5):
    z_plus_faces = []
    z_minus_faces = []
    z_plus_verts = []
    z_minus_verts = []

    if grid:
        matrix = Matrix.Translation(Vector((0, 0, -extrude)))
        bmesh.ops.create_circle(bm, cap_ends=True, cap_tris=True, segments=segments, radius=0.5, matrix=matrix)
        z_minus_verts = [v.index for v in bm.verts]

        if not boundary:
            bmesh.ops.delete(bm, geom=[e for e in bm.edges if e.is_boundary], context ='EDGES')

        bmesh.ops.delete(bm, geom=bm.faces, context ='FACES_ONLY')
        result = bmesh.ops.extrude_edge_only(bm, edges=bm.edges, use_normal_flip=True)
        z_plus_verts = [v for v in result['geom'] if type(v) == bmesh.types.BMVert]
        bmesh.ops.translate(bm, verts=z_plus_verts, vec=[0,0, extrude*2])

    else:
        bmesh.ops.create_circle(bm, cap_ends=True, cap_tris=False, segments=segments, radius=0.5, matrix=Matrix.Translation((0, 0, -extrude)))
        bmesh.ops.create_circle(bm, cap_ends=True, cap_tris=False, segments=segments, radius=0.5, matrix=Matrix.Translation((0, 0, extrude)))

        z_n, z_p = bm.faces[:]

        bmesh.ops.bridge_loops(bm, edges=bm.edges)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

        z_plus_faces.append(z_p.index)
        z_minus_faces.append(z_n.index)
        z_plus_verts = [v.index for v in z_p.verts]
        z_minus_verts = [v.index for v in z_n.verts]

    return z_plus_faces, z_minus_faces, z_plus_verts, z_minus_verts


def bmesh_star(bm, points=5, grid=False, extrude=0.5, factor = 0.5):
    matrix = Matrix.Translation(Vector((0, 0, -extrude)))
    bmesh.ops.create_circle(bm, cap_ends=True, cap_tris=False, segments=points * 2, radius=0.5, matrix=matrix)
    scale = Matrix.Diagonal((factor, factor, 1, 1))
    odd_verts = [v for i, v in enumerate(bm.verts) if i % 2]
    bmesh.ops.transform(bm, matrix=scale, verts=odd_verts)

    z_plus_faces = []
    z_minus_faces = []
    z_plus_verts = []
    z_minus_verts = [v.index for v in bm.verts]

    if grid:
        bmesh.ops.delete(bm, geom=bm.faces, context ='FACES_ONLY')
        result = bmesh.ops.extrude_edge_only(bm, edges=bm.edges, use_normal_flip=True)
        z_plus_verts = [v for v in result['geom'] if type(v) == bmesh.types.BMVert]
        bmesh.ops.translate(bm, verts=z_plus_verts, vec=[0, 0, extrude * 2])

    else:
        result = bmesh.ops.duplicate(bm, geom= bm.verts[:] + bm.edges[:] + bm.faces[:])
        bmesh.ops.translate(bm, verts=[v for v in result['geom'] if type(v) == bmesh.types.BMVert], vec=[0, 0, extrude * 2])

        for face in bm.faces:
            if face.verts[0].co.z > 0:
                z_p = face
            else:
                z_n = face

        bmesh.ops.bridge_loops(bm, edges=bm.edges)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

        z_plus_faces.append(z_p.index)
        z_minus_faces.append(z_n.index)
        z_plus_verts = [v.index for v in z_p.verts]
        z_minus_verts = [v.index for v in z_n.verts]

    return z_plus_faces, z_minus_faces, z_plus_verts, z_minus_verts
