import bpy
import math
import mathutils
import bmesh
import sys
from mathutils import Vector, Matrix
from bpy_extras import view3d_utils
from .. utility.math import dimensions, coords_to_center


def centroid(points):
    x = [p[0] for p in points]
    y = [p[1] for p in points]
    z = [p[2] for p in points]
    centroid = (sum(x) / len(points), sum(y) / len(points), sum(z) / len(points))

    return centroid


def scale(origin, point, value):
        ox, oy, oz = origin
        px, py, pz = point

        px = (px-ox)*value+ox
        py = (py-oy)*value+oy
        pz = (pz-oz)*value+oz

        return px, py, pz


def transform3D(point, location1, location2):
        px, py, pz = point
        x = [0, 0, 0]

        x[0] = location1[0] - px
        x[1] = location1[1] - py
        x[2] = location1[2] - pz
        px = location2[0] - x[0]
        py = location2[1] - x[1]
        pz = location2[2] - x[2]

        return px, py, pz


def rotate_z(origin, point, angle):
    ox, oy, oz = origin
    px, py, pz = point

    # Z rotation
    qx = ox + math.cos(angle) * (px - ox) - math.sin(angle) * (py - oy)
    qy = oy + math.sin(angle) * (px - ox) + math.cos(angle) * (py - oy)
    qz = pz

    return qx, qy, qz


def rotate_x(origin, point, angle):
    ox, oy, oz = origin
    px, py, pz = point

    # X rotation
    qx = px
    qz = oz + math.sin(angle) * (pz - oz) - math.cos(angle) * (py - oy)
    qy = oy + math.cos(angle) * (pz - oz) + math.sin(angle) * (py - oy)

    return qx, qy, qz


def rotate_y(origin, point, angle):
    ox, oy, oz = origin
    px, py, pz = point

    # Y rotation
    qy = py
    qx = ox + math.sin(angle) * (px - ox) - math.cos(angle) * (pz - oz)
    qz = oz + math.cos(angle) * (px - ox) + math.sin(angle) * (pz - oz)

    return qx, qy, qz


def get_3D_point_from_mouse(mouse_pos: Vector, context: bpy.context, point: Vector, normal: Vector):
        '''Point = The planes origin\n
           Normal = The direction the plane is facing'''

        # get the context arguments
        region = context.region
        rv3d = context.region_data

        intersection = Vector((0,0,0))
        try:
            #Camera Origin
            origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, mouse_pos)

            #Mouse origin
            mouse = view3d_utils.region_2d_to_vector_3d(region, rv3d, mouse_pos)

            #Camera Origin + Mouse
            ray_origin = origin + mouse

            #From the mouse to the viewport
            loc = view3d_utils.region_2d_to_location_3d(region, rv3d, mouse_pos, ray_origin - origin)

            #Ray to plane
            intersection = mathutils.geometry.intersect_line_plane(ray_origin, loc, point, normal)

        except:
            intersection = Vector((0,0,0))

        if(intersection == None):
            intersection = Vector((0,0,0))

        return intersection


def scene_ray_cast(context, event):
    '''Raycast from mouse into scene.'''

    view_layer = context.view_layer if bpy.app.version[:2] < (2, 91) else context.view_layer.depsgraph
    mouse_pos = (event.mouse_region_x, event.mouse_region_y)
    origin = view3d_utils.region_2d_to_origin_3d(bpy.context.region, bpy.context.region_data, mouse_pos)
    direction = view3d_utils.region_2d_to_vector_3d(bpy.context.region, bpy.context.region_data, mouse_pos)

    hit, location, normal, index, object, matrix = context.scene.ray_cast(view_layer, origin, direction)
    return hit, location, normal, index, object, matrix


def get_2d_point_from_3d_point(context, point3d):
    ''' Get a 2D screen point from a 3D point.\n
        Params:\n
        \tcontext : type = bpy.context
        \tpoint3d : type = Vector, desc = the 3D space location
        Returns -> Tuple (0, 0) : ELSE -> None'''

    # Validate
    if hasattr(context, 'region'):
        if hasattr(context, 'space_data'):
            if hasattr(context.space_data, 'region_3d'):
                region = context.region
                rv3d = context.space_data.region_3d
                return view3d_utils.location_3d_to_region_2d(region, rv3d, point3d)

    # Context is incorrect
    return None


def ray_cast_objects(context, origin_world, direction_world, objects, evaluated=True) -> tuple:
    '''Cast a ray on a list of MESH objects\n
        returns: result, location, normal, index, object, matrix'''

    depsgraph = context.evaluated_depsgraph_get()

    if evaluated:
        hit, location, normal, index, obj, matrix = context.scene.ray_cast(context.view_layer if bpy.app.version[:2] < (2, 91) else depsgraph, origin_world, direction_world)

        if not hit:
            return False, Vector((0, 0, 0)), Vector((0, 0,-1)), -1, None, Matrix()

        if obj in set(objects):
            return hit, location, normal, index, obj, matrix

    cast = None
    hit_object = None
    distance = None
    to_clear = []
    removeable_objects = []
    removeable_meshes = []

    cast_mesh = bpy.data.meshes.new('tmp')
    cast_obj = bpy.data.objects.new('tmp', cast_mesh)
    bpy.context.collection.objects.link(cast_obj)
    removeable_meshes.append(cast_mesh)
    removeable_objects.append(cast_obj)

    bm = bmesh.new()
    bmesh.ops.create_cube(bm)
    bm.to_mesh(cast_mesh)
    bm.free()
    verts_co = [v.co.copy() for v in cast_mesh.vertices]

    def quad_cast(mesh, origin, direction):
        distance = sys.float_info.max
        hit = False
        vec = Vector()
        normal = Vector((0, 0, -1))
        index = -1
        for p in mesh.polygons:

            v1 = mesh.vertices[p.vertices[0]].co
            v2 = mesh.vertices[p.vertices[1]].co
            v3 = mesh.vertices[p.vertices[2]].co

            point = mathutils.geometry.intersect_ray_tri(v1, v2, v3, direction, origin, True)
            if point is not None:
                dist = (point - origin).magnitude
                if dist < distance:
                    hit = True
                    vec = point
                    normal = p.normal
                    index = p.index
                    distance = dist

            else:
                v1 = mesh.vertices[p.vertices[2]].co
                v2 = mesh.vertices[p.vertices[3]].co
                v3 = mesh.vertices[p.vertices[0]].co

                point = mathutils.geometry.intersect_ray_tri(v1, v2, v3, direction, origin, True)

                if point is not None:
                    dist = (point - origin).magnitude
                    if dist < distance:
                        hit = True
                        vec = point
                        normal = p.normal
                        index = p.index
                        distance = dist

        return hit, vec, normal, index

    for obj in objects:
        inverted = obj.matrix_world.inverted()
        orig = inverted @ origin_world
        direction = inverted @ (direction_world + origin_world) - orig
        use_evaluated = evaluated

        bounds = obj.bound_box

        if obj.mode == 'EDIT':
            obj.update_from_editmode()

        if not use_evaluated:
            tmp = bpy.data.objects.new('tmp', obj.data)
            context.collection.objects.link(tmp)
            bounds = [Vector(v) for v in tmp.bound_box]
            bpy.data.objects.remove(tmp)

        center = coords_to_center(bounds)
        sca = dimensions(bounds)
        matrix = Matrix.Translation(center) @ Matrix.Diagonal((*sca, 1))

        for v, co in zip(cast_mesh.vertices, verts_co):
            v.co = matrix @ co

        hit, *_ = quad_cast(cast_mesh, orig, direction)

        if not hit:
            continue

        if obj.mode == 'EDIT' and obj.type == 'MESH':
            obj.update_from_editmode()
            cast_obj.data = obj.data

            hit, location, normal, index = cast_obj.ray_cast(orig, direction)

            if hit:
                location = obj.matrix_world @ location
                dist = location - origin_world

                if dist < distance or not distance:
                    distance = dist
                    cast = (hit, location, normal, index)
                    hit_object = obj
                    hit_mesh = obj.data

        elif obj.mode == 'OBJECT' and obj.type == 'MESH':
            hit, location, normal, index = obj.ray_cast(orig, direction, depsgraph=depsgraph if use_evaluated else None)

            if hit:
                location = obj.matrix_world @ location
                dist = location - origin_world

                if dist < distance or not distance:
                    distance = dist
                    cast = (hit, location, normal, index)
                    hit_object = obj

        else:
            eval_obj = obj.evaluated_get(depsgraph) if use_evaluated else obj
            temp_mesh = bpy.data.meshes.new_from_object(eval_obj)
            cast_obj.data = temp_mesh

            hit, location, normal, index  = cast_obj.ray_cast(orig, direction)

            removeable_meshes.append(temp_mesh)

            if hit:
                location = obj.matrix_world @ location
                dist = location - origin_world

                if dist < distance or not distance:
                    distance = dist
                    cast = (hit, location, normal, index)
                    hit_object = obj

    if not cast:
        cast = (False, Vector((0,0,0)), Vector((0,0,-1)), -1, None, Matrix())

    elif cast[0] and cast[3] < 0: # invalid index from screw modifier
        hit, location, normal, index = cast
        inverted = hit_object.matrix_world.inverted()
        orig = inverted @ origin_world
        direction = inverted @ (direction_world + origin_world) - orig

        mesh = bpy.data.meshes.new_from_object(hit_object.evaluated_get(depsgraph))
        removeable_meshes.append(mesh)
        cast_obj.data = mesh
        _, _, _, index = cast_obj.ray_cast(orig, direction)

        normal = (hit_object.matrix_world.inverted().transposed() @ normal).normalized()
        cast = True, location, normal, index, hit_object, hit_object.matrix_world.copy()

    else:
        hit, location, normal, index = cast
        normal = (hit_object.matrix_world.inverted().transposed() @ normal).normalized()
        cast = True, location, normal, index, hit_object, hit_object.matrix_world.copy()

    for obj in removeable_objects: bpy.data.objects.remove(obj)
    for mesh in  removeable_meshes: bpy.data.meshes.remove(mesh)

    for obj in to_clear:
        obj.to_mesh_clear()

    return cast
