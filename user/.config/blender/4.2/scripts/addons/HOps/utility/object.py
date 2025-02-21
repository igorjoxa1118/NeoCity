import bpy
from mathutils import Vector, Matrix, Euler

from . import addon, math


def valid_active_mesh(context):
    obj = context.active_object
    if obj == None: return False
    if obj.type != 'MESH': return False
    if not obj.select_get(): return False
    return True


def duplicate(obj, name='', link=False):
    duplicate = obj.copy()
    duplicate.data = obj.data.copy()

    if name:
        duplicate.name = name
        duplicate.data.name = name

    addon.log(value=F'Duplicated {obj.name} as: {duplicate.name}', indent=2)

    if link:
        bpy.context.scene.collection.objects.link(duplicate)
        addon.log(value=F'Linked {duplicate.name} to the scene', indent=2)

    return duplicate


def center(obj, matrix=Matrix()):
    return 0.125 * math.vector_sum(bound_coordinates(obj, matrix=matrix))


def bound_coordinates(obj, matrix=Matrix()):
    return [matrix @ Vector(coord) for coord in obj.bound_box]


def mesh_duplicate(obj, depsgraph, apply_modifiers=True):
    mesh = obj.to_mesh()

    if apply_modifiers:
        obj = obj.evaluated_get(depsgraph)
        mesh = obj.to_mesh()

    return mesh


def apply_scale(obj):
    obj.data.transform(math.get_sca_matrix(obj.scale))
    obj.scale = Vector((1,1,1))


def apply_location(obj):
    obj.data.transform(math.get_loc_matrix(obj.location))
    obj.location = Vector((0,0,0))


def apply_rotation(obj):
    obj.data.transform(math.get_rot_matrix(obj.rotation_quaternion))
    obj.rotation_euler = Euler()


def apply_transforms(obj):
    obj.data.transform(obj.matrix_world)
    clear_transforms(obj)


def clear_transforms(obj):
    obj.matrix_world = Matrix()


def apply_transform_bpy_version():
    '''Apply the transform on the active object.'''

    # TODO: Make a low level version of this.

    if bpy.context.active_object.mode == "EDIT":
        bpy.ops.object.mode_set(mode='OBJECT')

    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    if bpy.context.active_object.mode == "OBJECT":
        bpy.ops.object.mode_set(mode='EDIT')


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
