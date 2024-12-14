import bpy
import bmesh

from math import radians
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

from . import addon, math
from . view3d import location2d_to_origin3d, location2d_to_vector3d


class cast:
    origin: Vector = (0, 0)
    direction: Vector = (0, 0)


    def __new__(self, x, y, selected=False, object_data=None, mesh_data=None, bmesh_data=None, use_copy=False, transform_by=None, types={'MESH'}, edit_mode=True):
        context = bpy.context
        self.origin = location2d_to_origin3d(x, y)
        self.direction = location2d_to_vector3d(x, y)
        self.object_data = object_data
        self.mesh_data = mesh_data
        self.bmesh_data = bmesh_data
        self.use_copy = use_copy
        self.transform_by = transform_by

        if object_data:
            return self.object(self, context)

        elif mesh_data:
            return self.mesh(self, context)

        elif bmesh_data:
            return self.bmesh(self, context)

        return self.scene_edit_mesh(self, context, selected=selected) if edit_mode and context.mode == 'EDIT_MESH' else self.scene(self, context, selected)


    def object(self, context):
        mesh = self.object_data.data

        if self.mesh_data:
            self.object_data.data = self.mesh_data

        matrix = self.transform_by if self.transform_by else Matrix()
        matrix_inv = matrix.inverted()

        origin_local = matrix_inv @ self.origin
        direction_local = matrix_inv @ (self.direction + self.origin) - origin_local

        hit, location, normal, index = self.object_data.ray_cast(origin_local, direction_local, depsgraph=context.evaluated_depsgraph_get())

        if self.mesh_data:
            self.object_data.data = mesh

        if hit:
            return hit, matrix @ location, (matrix_inv.transposed() @ normal).normalized(), index

        else:
            return False, Vector(), Vector((0, 0, 1)), -1


    def mesh(self, context):
        obj = bpy.data.objects.new(name='snap_mesh', object_data=self.mesh_data)
        bpy.context.scene.collection.objects.link(obj)
        matrix = Matrix()

        if self.transform_by:
            matrix = self.transform_by

            if not self.use_copy:
                matrix = Matrix()
                self.mesh_data.transform(self.transform_by)

        matrix_inv = matrix.inverted()
        origin_local = matrix_inv @ self.origin
        direction_local = matrix_inv @ (self.direction + self.origin) - origin_local

        hit, location, normal, index = obj.ray_cast(origin_local, direction_local, depsgraph=bpy.context.evaluated_depsgraph_get())

        bpy.data.objects.remove(obj)

        del obj

        if hit:
            return True, matrix @ location, (matrix_inv.transposed() @ normal).normalized(), index

        else:
            return False, Vector(), Vector((0, 0, 1)), -1


    def scene(self, context, selected, types={'MESH'}):
        view_layer = context.view_layer if bpy.app.version[:2] < (2, 91) else context.view_layer.depsgraph
        hit, location, normal, index, object, matrix = context.scene.ray_cast(view_layer, self.origin, self.direction)

        hidden = []
        selection = {obj for obj in context.selected_objects if obj.type in types}

        while object and object not in selection and (not object.visible_in_viewport_get(context.space_data) or object.visible_get()):
            hidden.append(object)
            object.hide_viewport = True

            hit, location, normal, index, object, matrix = context.scene.ray_cast(view_layer, self.origin, self.direction)

        for obj in hidden:
            obj.hide_viewport = False

        return hit, location, normal, index, object, matrix


    def bmesh(self, context):
        matrix = Matrix()

        if self.transform_by:
            matrix = self.transform_by

        matrix_inv = matrix.inverted()

        origin_local = matrix_inv @ self.origin
        direction_local = matrix_inv @ (self.direction + self.origin) - origin_local

        temp_mesh = bpy.data.meshes.new('tmp')
        self.bmesh_data.to_mesh(temp_mesh)
        temp_obj = bpy.data.objects.new('tmp', temp_mesh)
        context.collection.objects.link(temp_obj)

        hit, location, normal, index = temp_obj.ray_cast(self.origin, self.direction)
        bpy.data.objects.remove(temp_obj)
        bpy.data.meshes.remove(temp_mesh)

        if hit:
            return True, matrix @ location, (matrix_inv.transposed() @ normal).normalized(), index

        else:
            return False, Vector(), Vector((0, 0, 1)), -1


    def scene_edit_mesh(self, context, selected=True):
        sequence = context.selected_objects if selected else context.visible_objects
        objects = [o for o in sequence if o.type =='MESH' and o.mode == 'EDIT']

        distance = None
        cast = (False, Vector(), Vector((0, 0, 1)), -1, None, None)

        temp_mesh = bpy.data.meshes.new('tmp')
        temp_object = bpy.data.objects.new('tmp', temp_mesh)
        context.collection.objects.link(temp_object)

        for obj in objects:
            obj.update_from_editmode()
            temp_object.data = obj.data
            bounds = [Vector(v) for v in temp_object.bound_box]

            center = math.coordinates_center(bounds)
            sca = math.coordinates_dimension(bounds)
            bm = bmesh.new()
            bmesh.ops.create_cube(bm, matrix=Matrix.Translation(center) @ Matrix.Diagonal((*sca, 1)))
            bm.to_mesh(temp_mesh)
            temp_object.data = temp_mesh

            matrix_inv = obj.matrix_world.inverted()
            origin_local = matrix_inv @ self.origin
            direction_local = matrix_inv @ (self.direction + self.origin) - origin_local

            hit, *_ = temp_object.ray_cast(origin_local, direction_local)

            if not hit: continue

            temp_object.data = obj.data
            hit, location, normal, index = temp_object.ray_cast(origin_local, direction_local)

            if hit:
                dist = (location - self.origin).length

                if  distance is None or dist < distance:
                    distance = dist
                    cast = (True, obj.matrix_world @ location, (matrix_inv.transposed() @ normal).normalized(), index, obj, obj.matrix_world.copy())

        bpy.data.objects.remove(temp_object)
        bpy.data.meshes.remove(temp_mesh)
        return cast


def bmesh_cast(bm, origin_world, direction_world, matrix=None):
    if not matrix:
        matrix = Matrix()

    matrix_inv = matrix.inverted()
    origin_local = matrix_inv @ origin_world
    direction_local = matrix_inv @ (direction_world + origin_world) - origin_local
    tree = BVHTree.FromBMesh(bm)

    location, normal, index, _ = tree.ray_cast(origin_local, direction_local)

    if location:
        return True, matrix @ location, (matrix_inv.transposed() @ normal).normalized(), index

    else:
        return False, Vector(), Vector((0, 0, 1)), -1

