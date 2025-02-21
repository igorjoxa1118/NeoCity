import bpy, bmesh
from mathutils import Vector, Matrix
from numpy import ones, reshape, array, append, delete

from . import addon, math


def duplicate(obj, name='', link=None):
    duplicate = obj.copy()
    duplicate.data = obj.data.copy()

    if name:
        duplicate.name = name
        duplicate.data.name = name

    if link:
        link.objects.link(duplicate)

    return duplicate


def center(obj, local=False, matrix=Matrix()):
    return 0.125 * math.vector_sum(bound_coordinates(obj, matrix=matrix if matrix != Matrix() else obj.matrix_world if not local else matrix
))


def bound_coordinates(obj, local=False, matrix=Matrix()):
    matrix = matrix if matrix != Matrix() or local else obj.matrix_world
    return [matrix @ Vector(coord) for coord in obj.bound_box]


def mesh_coordinates(obj, evaluated=True, local=False):
    from . mesh import indices
    from . math import transform_coordinates

    mesh = obj.data
    matrix = obj.matrix_world

    if evaluated:
        mesh = (obj.evaluated_get(bpy.context.evaluated_depsgraph_get())).to_mesh()
        obj.to_mesh_clear()

    mesh.update()
    mesh.calc_loop_triangles()

    length = len(mesh.vertices)
    coords = ones([length, 3], dtype='f')

    mesh.vertices.foreach_get('co', reshape(coords, length * 3))

    if not local:
        coords = transform_coordinates(matrix, coords)

    loop_index, edge_index = indices(mesh)
    return coords, loop_index, edge_index, mesh


def selected_bound_coordinates(local=False, matrix=Matrix(), combined=True):
    selected = bpy.context.selected_objects
    bounds = lambda o: bound_coordinates(o, local, matrix)
    return [v for o in selected for v in bounds(o)] if combined else [bounds(o) for o in selected]


def apply_transforms(obj):
    obj.data.transform(obj.matrix_world)
    clear_transforms(obj)


def clear_transforms(obj):
    obj.matrix_world = Matrix()


def parent(obj, target):
    matrix = obj.matrix_world.copy()
    obj.parent = target
    obj.matrix_parent_inverse = target.matrix_world.inverted()
    obj.matrix_world = matrix


def hide_set(obj, value=False, viewport=True, render=True):
    if hasattr(obj, 'cycles_visibility'):
        obj.cycles_visibility.camera = not value
        obj.cycles_visibility.diffuse = not value
        obj.cycles_visibility.glossy = not value
        obj.cycles_visibility.transmission = not value
        obj.cycles_visibility.scatter = not value
        obj.cycles_visibility.shadow = not value

    if hasattr(obj, 'visible_camera'):
        obj.visible_camera = not value

    if hasattr(obj, 'visible_diffuse'):
        obj.visible_diffuse = not value

    if hasattr(obj, 'visible_glossy'):
        obj.visible_glossy = not value

    if hasattr(obj, 'visible_transmission'):
        obj.visible_transmission = not value

    if hasattr(obj, 'visible_volume_scatter'):
        obj.visible_volume_scatter = not value

    if hasattr(obj, 'visible_shadow'):
        obj.visible_shadow = not value

    if viewport:
        obj.hide_set(value)

    if render:
        obj.hide_render = value


def set_origin(obj, transform_world, preserve_scale=True):
    '''
    Set origin origin of an object. \n
    transform_world - world space 4x4 Matrix or 3d Vector\n
    preserve_scale - preserve or apply basis scale of the object\n

    setting world space scale is not supported; negative scale might not be preserved.
    '''
    parent_transform = obj.parent.matrix_world @ obj.matrix_parent_inverse if obj.parent else Matrix()
    if isinstance(transform_world, Matrix):

        local = parent_transform.inverted() @ transform_world
        loc, rot, _ = local.decompose()

        scale = Matrix.Diagonal((*obj.matrix_basis.decompose()[2], 1)) if preserve_scale else Matrix()
        local = Matrix.Translation(loc) @ rot.to_matrix().to_4x4() @ scale
        matrix_world = parent_transform @ local

    else:
        local = obj.matrix_basis.copy()
        local.translation = parent_transform.inverted() @ transform_world
        matrix_world = obj.matrix_world.copy()
        matrix_world.translation = transform_world

    delta_matrix = obj.matrix_basis.inverted() @ local
    delta_matrix_inv = delta_matrix.inverted()


    def update_children(obj, matrix):
        for child in obj.children:
            child.matrix_parent_inverse = matrix @ child.matrix_parent_inverse

    if obj.mode == 'OBJECT':
        if hasattr(obj.data, 'transform'):
            obj.data.transform(delta_matrix_inv)

        child_delta = obj.matrix_world.inverted() @ parent_transform @ local
        obj.matrix_basis = local
        obj.matrix_world = matrix_world
        update_children(obj, child_delta.inverted())

    elif obj.mode == 'EDIT' and obj.type == 'MESH':
        bm = bmesh.from_edit_mesh(obj.data)
        bmesh.ops.transform(bm, verts=bm.verts, matrix=delta_matrix_inv)
        bmesh.update_edit_mesh(obj.data)

        child_delta = obj.matrix_world.inverted() @ parent_transform @ local
        obj.matrix_basis = local
        obj.matrix_world = matrix_world
        update_children(obj, child_delta.inverted())
