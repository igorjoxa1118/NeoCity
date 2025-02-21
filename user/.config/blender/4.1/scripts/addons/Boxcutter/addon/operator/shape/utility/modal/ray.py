import bpy
import bmesh
import numpy
import sys

from math import radians
from mathutils import Vector, Matrix, geometry

from . import refresh

from ...... utility import addon, object, ray, view3d, math


# TODO: intersect verification
# TODO: cursor support
def planar_matrix(context):
    preference = addon.preference()
    view = context.region_data.view_rotation @ Vector((0, 0, 1))
    matrix = Matrix.Rotation(radians(90), 4, preference.axis)

    colinear = lambda v1, v2: round(abs(v1.dot(v2)), 3) == 1

    if colinear(view, Vector((1, 0, 0))):
        matrix = Matrix.Rotation(radians(90), 4, 'Y')

    elif colinear(view, Vector((0, 1, 0))):
        matrix = Matrix.Rotation(radians(90), 4, 'X')

    elif colinear(view, Vector((0, 0, 1))):
        matrix = Matrix()

    return matrix


def custom(op, context, event, axis=None):
    preference = addon.preference()
    bc = context.scene.bc

    snap = (bc.snap.operator.handler if hasattr(bc.snap.operator, 'handler') else bc.snap.operator.snap) if bc.snap.hit else False
    grid_active = (snap.grid.display if hasattr(snap, 'grid') and hasattr(snap.grid, 'display') else snap.grid_active) if snap else False
    point = (snap.points.active if hasattr(snap, 'points') else snap.point) if snap else False

    if bc.snap.operator and bc.snap.hit and hasattr(bc.snap.operator, 'grid_handler'):
        update_shape_transforms(op, context, event, snap.matrix, bc.snap.location)

        return

    size = context.space_data.clip_end * 10

    verts = [Vector(( size,  size, 0.0)), Vector((-size,  size, 0.0)),
             Vector((-size, -size, 0.0)), Vector(( size, -size, 0.0))]

    edges = [(0, 1), (1, 2),
             (2, 3), (3, 0)]

    faces = [(0, 1, 2, 3)]

    data = bpy.data.meshes.new(name='Box')
    data.bc.removeable = True

    if not bc.snap.hit:
        data.from_pydata(verts, edges, faces)

    box = bpy.data.objects.new(name='Box', object_data=data) # if not bc.snap.hit else bc.snap.mesh)
    bpy.context.scene.collection.objects.link(box)

    if not axis:
        axis = preference.axis

    current = {
        'X': 'Y',
        'Y': 'X',
        'Z': 'Z'}

    rotation = Matrix.Rotation(radians(-90 if axis in {'X', 'Y'} else 90), 4, current[axis])

    cursor = context.scene.cursor.rotation_euler.to_matrix().to_4x4()
    cursor.translation = context.scene.cursor.location

    matrix = cursor @ rotation if preference.surface == 'CURSOR' else rotation

    if not bc.snap.hit:
        box.data.transform(matrix)

    if bc.snap.hit:
        # hit, op.ray['location'], op.ray['normal'], _ = ray.cast(*op.mouse['location'], mesh_data=bc.snap.mesh)
        op.ray['location'] = Vector(bc.snap.location[:])
        op.ray['normal'] = Vector(bc.snap.normal[:])

    else:
        hit, op.ray['location'], op.ray['normal'], _ = ray.cast(*op.mouse['location'], object_data=box)

    if not bc.snap.hit:
        if not hit:
            index = [axis == a for a in 'XYZ'].index(True)

            if index > 1:
                index = 0

            else:
                index += 1

            axis = 'XYZ'[index]

            bpy.data.objects.remove(box)

            del box

            op.plane_checks += 1

            if op.plane_checks < 4:
                custom(op, context, event, axis=axis)

            return

    update_shape_transforms(op, context, event, snap.matrix if bc.snap.hit and grid_active else matrix, Vector(op.ray['location'][:] if not bc.snap.hit else bc.snap.location))

    bpy.data.objects.remove(box)


def view_matrix(context, x, y):
    is_perspective = context.region_data.is_perspective
    view = context.space_data.region_3d.view_rotation.to_matrix().to_4x4()

    view_location = context.region_data.view_location + view @ Vector((0, 0, context.region_data.view_distance - context.space_data.clip_start - 0.1))
    origin = view3d.location2d_to_origin3d(x, y)
    normal = view @ Vector((0, 0, -1))
    plane_origin = view_location if is_perspective else origin
    depsgraph = context.evaluated_depsgraph_get()

    distance = sys.float_info.max
    for obj in context.selected_objects:
        if obj.type != 'MESH': continue

        if obj.mode == 'EDIT':
            obj.update_from_editmode()
            eval = obj

        else:
            eval = obj.evaluated_get(depsgraph)

        length = len(eval.data.vertices)

        if not length: continue

        np_normal = numpy.array(normal, dtype='f')
        np_plane_orig = numpy.array(plane_origin, dtype='f')
        verts = numpy.empty([length, 3], dtype = 'f')

        eval.data.vertices.foreach_get('co', numpy.reshape(verts, length * 3))
        verts = verts @ numpy.array(obj.matrix_world.to_3x3().transposed(), dtype='f')
        verts += numpy.array(obj.matrix_world.translation, dtype='f')
        delta = verts - np_plane_orig
        distances = numpy.sum(delta * np_normal, axis=1)

        min_index = numpy.argmin(distances)
        min_distance = distances[min_index]

        if min_distance < distance:
            distance = min_distance
            view.translation = verts[min_index]

    if is_perspective and distance < 0:
        view.translation = view_location

    vectors = [view @ Vector((0, 1, 0)), view @ Vector((1, -1, 0)), view @ Vector((-1, -1, 0))]
    ray = view3d.location2d_to_vector3d(x, y)

    intersect = geometry.intersect_ray_tri(*vectors, ray, origin, False)
    if not intersect:
        intersect = geometry.intersect_ray_tri(*vectors, -ray, origin, False)

    view.translation = intersect

    return view.translation, normal, view


def screen(op, context, event):
    bc = context.scene.bc

    snap = (bc.snap.operator.handler if hasattr(bc.snap.operator, 'handler') else bc.snap.operator.snap) if bc.snap.hit else False
    grid_active = (snap.grid.display if hasattr(snap, 'grid') and hasattr(snap.grid, 'display') else snap.grid_active) if snap else False

    if bc.snap.operator and bc.snap.hit and hasattr(bc.snap.operator, 'grid_handler'):
        update_shape_transforms(op, context, event, snap.matrix, bc.snap.location)

        return

    mouse = (event.mouse_region_x, event.mouse_region_y)

    op.ray['location'], op.ray['normal'], matrix, = view_matrix(context, *mouse)

    if bc.snap.hit and grid_active:
        op.ray['location'], op.ray['normal'], matrix = Vector(bc.snap.location[:]), Vector(bc.snap.normal[:]), snap.matrix

    update_shape_transforms(op, context, event, matrix, op.ray['location'])


def surface_matrix(obj, matrix, location, normal, position, orient_method='LOCAL', face_index=0, edge_index=0, force_edge=False):
    preference = addon.preference()

    track_matrix = view3d.track_matrix(normal, matrix=matrix)

    custom_orient = False
    tangent = Vector((0, 0, 0))
    active_edges = []

    if orient_method == 'EDIT':
        # TODO: needs to check if active edge is part of a hit face in a fast way
        bm = bmesh.from_edit_mesh(obj.data)
        active_edges = [elem for elem in bm.select_history if isinstance(elem, bmesh.types.BMEdge)]

        if active_edges:
            custom_orient = True
            v1, v2 = active_edges[0].verts

            _, rot, _ = matrix.decompose()
            rot_matrix = rot.to_matrix().to_4x4()

            tangent = (rot_matrix @ (v2.co - v1.co)).normalized()

    if orient_method != 'LOCAL' and not active_edges:
        custom_orient = True
        object_eval = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())

        bm = bmesh.new()
        bm.from_mesh(object_eval.data)
        bm.faces.ensure_lookup_table()

        if orient_method == 'TANGENT':
            tangent = bm.faces[face_index].calc_tangent_edge()

        # elif orient_method == 'TANGENTDIAGONAL':
        #     tangent = bm.faces[face_index].calc_tangent_edge_diagonal()

        # elif orient_method == 'TANGENTEDGEPAIR':
        #     tangent = bm.faces[face_index]].calc_tangent_edge_pair()

        # elif orient_method == 'TANGENTVERTDIAGONAL':
        #     tangent = bm.faces[face_index].calc_tangent_vert_diagonal()

        elif orient_method == 'NEAREST':
            bm.edges.ensure_lookup_table()

            face = bm.faces[face_index]
            distance = 0.0
            index = 0

            for i, edge in enumerate(face.edges):
                edge = [obj.matrix_world @ v.co for v in edge.verts]
                current, normalized_distance = geometry.intersect_point_line(location, *edge)

                if normalized_distance > 1:
                    current = edge[1]
                elif normalized_distance < 0:
                    current = edge[0]

                length = (current - location).length

                if length < distance or not distance:
                    distance = length
                    index = i

            tangent = (face.edges[index].verts[0].co - face.edges[index].verts[1].co).normalized()

        elif orient_method == 'EDGE' or force_edge:
            bm.edges.ensure_lookup_table()
            edge = [e for e in bm.faces[face_index].edges][edge_index]
            tangent = (edge.verts[0].co - edge.verts[1].co).normalized()

            if not force_edge:
                if len(set([str(Vector((abs(f) for f in face.normal))) for face in edge.link_faces])) == 1 and len(edge.link_faces) > 1:
                    custom_orient = False

        elif orient_method == 'FACE_FIT':
            face = bm.faces[face_index]
            face_matrix = view3d.track_matrix(normal=face.normal)
            face_matrix.translation = face.calc_center_median()

            local_verts = [(face_matrix.inverted() @ vert.co).to_2d() for vert in face.verts]
            angle = geometry.box_fit_2d(local_verts)
            tangent = face_matrix.to_3x3() @ (Matrix.Rotation(-angle, 2) @ Vector((1, 0))).to_3d()

        tangent = (obj.matrix_world.to_3x3() @ tangent).normalized()

        bm.free()

    if custom_orient:
        mat = Matrix.Identity(3)
        cross = tangent.cross(normal)

        mat.col[0] = cross
        mat.col[1] = tangent
        mat.col[2] = normal

        track_quat = mat.to_quaternion()
        track_matrix = matrix.inverted() @ track_quat.to_matrix().to_4x4()

    track_matrix = matrix @ track_matrix
    track_matrix.translation = position

    return custom_orient, track_matrix


# TODO: consider parent matrix
def surface(op, context, event):
    preference = addon.preference()
    bc = context.scene.bc

    snap = (bc.snap.operator.handler if hasattr(bc.snap.operator, 'handler') else bc.snap.operator.snap) if bc.snap.hit else False
    grid_active = (snap.grid.display if hasattr(snap, 'grid') and hasattr(snap.grid, 'display') else snap.grid_active) if snap else False
    point = (snap.points.active if hasattr(snap, 'points') else snap.point) if snap else False

    if bc.snap.operator and bc.snap.hit and hasattr(bc.snap.operator, 'grid_handler'):
        update_shape_transforms(op, context, event, snap.matrix, bc.snap.location)

        op.custom_orient = point and point.type == 'EDGE' #prevent type filtering as all points share alignment atm
        if preference.snap.dot_alt_draw and bc.snap.operator.grid_handler.nearest_dot:
            op.snap_lock_type = bc.snap.operator.grid_handler.nearest_dot.type

        return

    obj = op.ray['object'] if not snap else snap.object if hasattr(snap, 'object') else snap.obj
    location = op.ray['location'] if not snap else Vector(bc.snap.location[:])
    normal = op.ray['normal'] if not snap else Vector(bc.snap.normal[:])
    face_index = op.ray['index'] if not snap else snap.face_index

    orient_method = 'EDIT' if preference.behavior.orient_active_edge and obj and obj.mode == 'EDIT' else preference.behavior.orient_method

    edge_index = -1
    if snap and not grid_active and point:
        if point.type == 'VERT':
            op.snap_lock_type = 'VERT'

        elif point.type == 'EDGE':
            orient_method = 'EDGE'
            edge_index = point.edge_index
            op.snap_lock_type = 'EDGE'

        elif point.type == 'FACE':
            op.snap_lock_type = 'FACE'

    matrix = obj.matrix_world.to_3x3().to_4x4() if obj else Matrix()

    if orient_method == 'EDGE' or not snap:
        matrix.translation = (0, 0, 0)
        op.custom_orient, matrix = surface_matrix(obj, matrix, location, normal, location, orient_method, face_index, edge_index)

        if not op.custom_orient and orient_method == 'EDGE' and preference.behavior.orient_method != 'LOCAL':
            matrix = obj.matrix_world.to_3x3().to_4x4()
            matrix.translation = (0, 0, 0)
            op.custom_orient, matrix = surface_matrix(obj, matrix, location, normal, location, orient_method if preference.behavior.orient_method == 'NEAREST' else preference.behavior.orient_method, face_index, edge_index, True)

    matrix = snap.matrix if snap and orient_method != 'EDGE' else matrix

    del obj

    update_shape_transforms(op, context, event, matrix.normalized(), location)


def update_shape_transforms(op, context, event, matrix, location):
    bc = context.scene.bc

    # if bc.snap.hit:
    #     snap = bc.snap.operator.handler if hasattr(bc.snap.operator, 'handler') else bc.snap.operator.snap
    #     grid_active = snap.grid.display if hasattr(snap, 'grid') and hasattr(snap.grid, 'display') else snap.grid_active

    #     if grid_active:
    #         addon.preference().behavior.accucut = False

    op.ray['location'] = location

    bc.lattice.matrix_world = matrix
    bc.lattice.matrix_world.translation = location

    bc.shape.matrix_world = bc.lattice.matrix_world
    bc.plane.matrix_world = bc.lattice.matrix_world

    op.start['matrix'] = bc.plane.matrix_world.copy()
    op.start['init_matrix'] = op.start['matrix'].copy()

    bc.location = op.ray['location']

    refresh.shape(op, context, event)
