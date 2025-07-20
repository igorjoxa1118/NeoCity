import bpy, bmesh, mathutils, math
from mathutils import Vector, Matrix, Quaternion
from enum import Enum
from .... utility import math as hops_math

bound_map = [
    Vector((-1.0, -1.0, -1.0)),
    Vector((-1.0, -1.0, 1.0)),
    Vector((-1.0, 1.0, 1.0)),
    Vector((-1.0, 1.0, -1.0)),
    Vector((1.0, -1.0, -1.0)),
    Vector((1.0, -1.0, 1.0)),
    Vector((1.0, 1.0, 1.0)),
    Vector((1.0, 1.0, -1.0)),
]


class Boxelize:
    active = False
    segments = 10
    index = 0

    @staticmethod
    def deactivate():
        Boxelize.active = False
        Boxelize.index = 0


def get_boxelize_ref():
    return Boxelize


class Axis(Enum):
    X = 0
    Y = 1
    Z = 2


class Dice_Box_3D:

    def __init__(self, axis=Axis.X, active=False, segments=5):
        self.axis = axis
        self.active = active
        self.bounds = []
        self.center = Vector()
        self.matrix = Matrix()

        self.pending_update = False
        self.__segments = segments


    def loops(self, use_normal_offset=True, use_transform_matrix=True):
        if self.dims()[self.axis.value] <= 0: return []

        segments = self.segments
        bounds = self.bounds
        width = self.dims()[self.axis.value]
        gap = width / (self.segments + 1) if self.segments > 0 else 1

        if Boxelize.active:
            _, _, sca = self.matrix.decompose()
            sca_mat = Matrix.Diagonal(sca)
            dims = sca_mat @ self.dims()
            dims = Vector((abs(dims.x), abs(dims.y), abs(dims.z)))

            boxelize_width = abs(dims[Boxelize.index])

            if Boxelize.segments <= 0: Boxelize.segments = 1

            boxelize_gap = boxelize_width / Boxelize.segments

            scaled_width = dims[self.axis.value]

            if boxelize_gap <= 0: return []
            segments = int(scaled_width / boxelize_gap)

            if segments <= 0: return []
            gap = width / segments

        if not Boxelize.active:
            segments += 1

        faces = []

        dimensions = self.dims()
        offset = Vector()
        offset_val = 0.005
        eps = 0.00001
        for i in range(segments):
            if i == 0: continue
            factor = (gap * i) / width
            if self.axis == Axis.X:
                if dimensions[2] < eps:
                    offset[2] = offset_val

                if dimensions[1] < eps:
                    offset[1] = offset_val

                faces.append((
                    bounds[0].lerp(bounds[4], factor) + (offset * bound_map[0]),
                    bounds[1].lerp(bounds[5], factor) + (offset * bound_map[1]),
                    bounds[2].lerp(bounds[6], factor) + (offset * bound_map[2]),
                    bounds[3].lerp(bounds[7], factor) + (offset * bound_map[3]),))
            elif self.axis == Axis.Y:
                if dimensions[2] < eps:
                    offset[2] = offset_val

                if dimensions[0] < eps:
                    offset[0] = offset_val

                faces.append((
                    bounds[0].lerp(bounds[3], factor) + (offset * bound_map[0]),
                    bounds[1].lerp(bounds[2], factor) + (offset * bound_map[1]),
                    bounds[5].lerp(bounds[6], factor) + (offset * bound_map[5]),
                    bounds[4].lerp(bounds[7], factor) + (offset * bound_map[4]),))
            elif self.axis == Axis.Z:
                if dimensions[0] <= eps:
                    offset[0] = offset_val

                if dimensions[1] <= eps:
                    offset[1] = offset_val

                faces.append((
                    bounds[0].lerp(bounds[1], factor) + (offset * bound_map[0]),
                    bounds[3].lerp(bounds[2], factor) + (offset * bound_map[3]),
                    bounds[7].lerp(bounds[6], factor) + (offset * bound_map[7]),
                    bounds[4].lerp(bounds[5], factor) + (offset * bound_map[4]),))

        ret_faces = []
        for face in faces:
            center = hops_math.coords_to_center(face)
            new_face = []
            for i in range(len(face)):
                point = face[i]

                if use_normal_offset:
                    normal = (face[i] - center).normalized()
                    point = face[i] + (normal * .05)

                if use_transform_matrix:
                    point = self.matrix @ point

                new_face.append(point)

            ret_faces.append(new_face)
        return ret_faces


    def create_mesh(self, context, use_normal_offset=True):
        if not self.loops(): return None

        bm = bmesh.new()
        for face in self.loops(use_normal_offset=use_normal_offset, use_transform_matrix=False):
            verts = []
            for point in face:
                verts.append(bm.verts.new(point))
            bm.faces.new(verts)

        mesh = bpy.data.meshes.new(f"Mesh {self.axis.name}")
        bm.to_mesh(mesh)
        bm.free()

        obj = bpy.data.objects.new(f"Obj {self.axis.name}", mesh)
        obj.matrix_world = self.matrix
        context.collection.objects.link(obj)
        obj.select_set(True)
        return obj


    def dims(self):
        return hops_math.dimensions(self.bounds)

    # --- FORM --- #

    @property
    def segments(self):
        return self.__segments

    @segments.setter
    def segments(self, val):
        self.pending_update = True
        val = min(val, 1000)
        self.__segments = int(max(val, 1))


    def toggle_active(self):
        self.pending_update = True
        self.active = not self.active


    def activate(self):
        '''Used for turning on the axis when scrolling over the input field'''
        if not self.active: self.pending_update = True
        self.active = True


    def active_hook(self):
        return self.active


def selection_boundary(context, objs, matrix, empty_matrix=None):
    # empty_matrix : use this to support the rotated bounds of each object and its original bounds

    bound_boxes = []
    if context.mode == "EDIT_MESH":
        for obj in objs:
            obj.update_from_editmode()
            points = [obj.matrix_world @ v.co for v in obj.data.vertices if v.select]

            if empty_matrix:
                points.extend([empty_matrix @ v.co for v in obj.data.vertices if v.select])

            bound_boxes.extend(points)
    elif context.mode == "OBJECT":
        for obj in objs:
            points = [obj.matrix_world @ v.co for v in obj.data.vertices]

            if empty_matrix:
                points.extend([empty_matrix @ v.co for v in obj.data.vertices])

            bound_boxes.extend(points)
    if not bound_boxes: return None

    if empty_matrix:
        return hops_math.coords_to_bounds([empty_matrix.inverted() @ p for p in bound_boxes])

    return hops_math.coords_to_bounds([matrix.inverted() @ p for p in bound_boxes])