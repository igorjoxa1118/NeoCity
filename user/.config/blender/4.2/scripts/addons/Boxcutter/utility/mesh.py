import bmesh

import numpy

from statistics import median
from mathutils import Matrix, Vector


def recalc_normals(obj, face_indices=None, inside=False, flip_multires=False):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.faces.ensure_lookup_table()

    faces = [bm.faces[index] for index in face_indices] if face_indices else bm.faces

    if bm.faces:
        bmesh.ops.recalc_face_normals(bm, faces=faces)

    if inside:
        bmesh.ops.reverse_faces(bm, faces=faces, flip_multires=flip_multires)

    bm.to_mesh(obj.data)

    obj.data.update()


def remove_doubles(obj, distance=0.00001):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.faces.ensure_lookup_table()

    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=distance)

    if bm.faces:
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

    bm.to_mesh(obj.data)

    obj.data.update()


def longest_edge_median(face, verts):
    center = Vector()
    max_length = 0.0
    for current in face.vertices:
        for check in face.vertices:
            if check == current:
                continue

            length = (verts[current].co - verts[check].co).length

            if length < max_length:
                continue

            current_mid = median((verts[current].co, verts[check].co))

            max_length = length
            center = current_mid

    return center


def transform_scale(mesh, x=0.0, y=0.0, z=0.0, uniform=0.0, magnitude=1):
    if x: mesh.transform(Matrix.Scale(x, 4, Vector((magnitude, 0, 0)) ))
    if y: mesh.transform(Matrix.Scale(y, 4, Vector((0, magnitude, 0)) ))
    if z: mesh.transform(Matrix.Scale(z, 4, Vector((0, 0, magnitude)) ))

    if uniform:
        mesh.transform(Matrix.Scale(uniform, 4, Vector((magnitude, 0, 0)) ))
        mesh.transform(Matrix.Scale(uniform, 4, Vector((0, magnitude, 0)) ))
        mesh.transform(Matrix.Scale(uniform, 4, Vector((0, 0, magnitude)) ))


def indices(mesh):
    loop_len = len(mesh.loop_triangles)
    loop_index = numpy.ones([loop_len, 3], dtype='i')

    mesh.loop_triangles.foreach_get('vertices', numpy.reshape(loop_index, loop_len * 3))

    edge_len = len(mesh.edges)
    edge_index = numpy.ones([edge_len, 2], dtype='i')

    mesh.edges.foreach_get('vertices', numpy.reshape(edge_index, edge_len * 2))

    return loop_index, edge_index


def flip_normals(mesh):
    bm = bmesh.new()
    bm.from_mesh(mesh)

    bmesh.ops.reverse_faces(bm, faces=bm.faces)
    bm.to_mesh(mesh)

    mesh.update()


def flip_mesh(mesh, axis='X'):
    bm = bmesh.new()
    bm.from_mesh(mesh)

    scale_vec = Vector((1, 1, 1, 1))
    setattr(scale_vec, axis.lower(), -1)

    bmesh.ops.transform(bm, verts=bm.verts, matrix=Matrix.Diagonal(scale_vec))
    bmesh.ops.reverse_faces(bm, faces=bm.faces)

    bm.to_mesh(mesh)
    mesh.update()

