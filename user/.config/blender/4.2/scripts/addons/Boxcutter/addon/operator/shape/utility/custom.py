import bpy
import bmesh

from math import radians
from mathutils import Matrix, Vector

from . import modifier
from ..... utility import addon


current_index = 0
sum_index = 0


def clear_sum():
    global sum_index
    sum_index = 0


def cutter(op, context, index=1, custom=None):
    global current_index
    global sum_index

    preference = addon.preference()
    bc = context.scene.bc

    cutters_collection = bc.recall_collection if bc.recall_collection else bc.collection

    font = False

    if len([obj for obj in cutters_collection.objects if obj.type in {'MESH', 'FONT', 'CURVE'} and obj is not bc.shape]) < 1:
        if not custom or (custom and custom.type not in {'FONT', 'CURVE'}):
            return

    bc.lattice.hide_set(False)

    original_active = context.active_object
    context.view_layer.objects.active = bc.shape
    bc.shape.select_set(True)

    matrix = bc.shape.matrix_world.copy()

    if not custom and not bc.shape.bc.applied and not bc.shape.bc.applied_cycle:
        bc.shape.bc.applied_cycle = True
        keep_modifiers = [type for type in ['ARRAY', 'BEVEL', 'SOLIDIFY', 'SCREW', 'MIRROR'] if getattr(preference.behavior, F'keep_{type.lower()}')]
        modifier.apply(bc.shape, ignore=[mod for mod in bc.shape.modifiers if mod.type in keep_modifiers])

        for obj in op.datablock['targets']:
            if modifier.shape_bool(obj):
                modifier.shape_bool(obj).object = None

        for obj in op.datablock['slices']:
            if modifier.shape_bool(obj):
                modifier.shape_bool(obj).object = None

        for obj in op.datablock['insets']:
            if modifier.shape_bool(obj):
                modifier.shape_bool(obj).object = None

    objects = []
    for obj in cutters_collection.objects:
        holdout = obj.bc.applied_cycle and not (sum_index > len(cutters_collection.objects) - 1) or (obj.bc.copy and not preference.shape.cycle_all)

        if obj.type in {'MESH', 'FONT', 'CRUVE'} and obj != bc.shape and not holdout:
            objects.append(obj)

    obj = None
    if not custom:
        next_index = current_index + index

        if next_index > len(objects) - 1:
            next_index = 0

        elif next_index < -1:
            next_index = len(objects) - 1

        current_index = next_index
        sum_index += 1

        if objects:
            obj = objects[next_index if next_index < len(objects) else 0]
        else:
            return

    del objects

    if bc.shape.bc.copy:
        bpy.data.objects.remove(bc.shape)

    obj = obj if obj else custom

    if custom:
        bpy.data.objects.remove(bc.shape)
        bc.shape = None

    if obj.type == 'MESH':
        bc.shape = obj.copy()
        count = len([obj.name for obj in cutters_collection.objects if 'Cutter' in obj.name])
        bc.shape.name = F'Cutter{"." + str(count).zfill(3) if count else ""}'
        bc.collection.objects.link(bc.shape)

        bc.shape.hide_render = True
        context.view_layer.objects.active = bc.shape

        bc.shape.bc.copy = True
        bc.shape.data = obj.data.copy()
        bc.shape.data.name = bc.shape.name

    else:
        font = True

        used = False
        for collection in bpy.data.collections:
            if obj in collection.objects[:] and collection != cutters_collection:
                used = True
            elif obj in context.scene.collection.objects[:]:
                used = True

                break

        if used:
            cutters_collection.objects.unlink(obj)

        bc.shape = bpy.data.objects.new(obj.name, bpy.data.meshes.new_from_object(obj))

        if obj.type == 'FONT':
            bm = bmesh.new()
            bm.from_mesh(bc.shape.data)
            dist = 0.000001

            bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=dist)
            # characters like T require 2 passes
            bmesh.ops.dissolve_degenerate(bm, dist=dist, edges=bm.edges)
            bmesh.ops.dissolve_degenerate(bm, dist=dist, edges=bm.edges)

            bm.to_mesh(bc.shape.data)

        bc.collection.objects.link(bc.shape)

    if addon.preference().behavior.auto_smooth:
        if bpy.app.version < (4, 1):
            bc.shape.data.use_auto_smooth = True

        for face in bc.shape.data.polygons:
            face.use_smooth = True

    if bc.empty:
        bc.empty.parent = bc.shape

    shape_2d = False

    eval = bc.shape.evaluated_get(context.evaluated_depsgraph_get())

    if True in [dimension < 0.00001 for dimension in eval.dimensions] and len(bc.shape.data.polygons[:]):
        mod = bc.shape.modifiers.new('Solidify', type='SOLIDIFY')
        mod.thickness = 1
        mod.offset = 0
        shape_2d = True

    if font:
        mod = bc.shape.modifiers.new(name='Decimate', type='DECIMATE')
        mod.decimate_type = 'DISSOLVE'
        mod.angle_limit = radians(1)
        mod.use_dissolve_boundaries = True

    del obj

    modifier.apply(bc.shape, ignore=[mod for mod in bc.shape.modifiers if mod.type == 'BEVEL'] if not shape_2d else [])

    center = 0.125 * sum((Vector(point) for point in eval.bound_box), Vector())
    bc.shape.data.transform(Matrix.Translation(-center))

    scale = bc.shape.matrix_world.to_scale()
    dimensions = eval.dimensions
    bc.shape.data.transform(Matrix.Diagonal((scale.x, scale.y, scale.z, 1)))
    bc.shape.matrix_world = Matrix()

    scale_x = 1 / dimensions[0] if dimensions[0] else 1
    scale_y = 1 / dimensions[1] if dimensions[1] else 1
    scale_z = 1 / dimensions[2] if dimensions[2] else 1

    x_dim = dimensions.x if dimensions.x else 1
    op.datablock['shape_proportions'] = dimensions / x_dim

    if bc.shape.bc.shape and len(op.datablock['targets']):
        scale_x = -scale_x

    # if not bc.shape.bc.shape and op.shape_type == 'CUSTOM':
    #     scale_y = -scale_y

    flip_join = op.mode == 'JOIN' and preference.behavior.join_flip_z
    scale_z = -scale_z if flip_join else scale_z

    bc.shape.data.transform(Matrix.Diagonal((scale_x, scale_y, scale_z, 1)))

    bm = bmesh.new()
    bm.from_mesh(bc.shape.data)

    # bm.faces.ensure_lookup_table()
    # bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

    if ((scale_x < 0) + (scale_y < 0) + (scale_z < 0)) % 2 != 0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces)

    if addon.preference().behavior.auto_smooth:
        for f in bm.faces:
            f.smooth = True

    bm.to_mesh(bc.shape.data)
    bm.free()

    for obj in op.datablock['targets']:
        for mod in obj.modifiers:
            if mod.type == 'BOOLEAN' and not mod.object:
                mod.object = bc.shape

    for obj in op.datablock['slices']:
        for mod in obj.modifiers:
            if mod.type == 'BOOLEAN' and not mod.object:
                mod.object = bc.shape

    for obj in op.datablock['insets']:
        for mod in obj.modifiers:
            if mod.type == 'BOOLEAN' and not mod.object:
                mod.object = bc.shape

    bc.lattice.matrix_world = Matrix()

    points = [Vector(point.co_deform) for point in bc.lattice.data.points]
    bc.lattice.data.points[0].co_deform = Vector((-0.5, -0.5, -0.5))
    bc.lattice.data.points[1].co_deform = Vector(( 0.5, -0.5, -0.5))
    bc.lattice.data.points[2].co_deform = Vector((-0.5,  0.5, -0.5))
    bc.lattice.data.points[3].co_deform = Vector(( 0.5,  0.5, -0.5))
    bc.lattice.data.points[4].co_deform = Vector((-0.5, -0.5,  0.5))
    bc.lattice.data.points[5].co_deform = Vector(( 0.5, -0.5,  0.5))
    bc.lattice.data.points[6].co_deform = Vector((-0.5,  0.5,  0.5))
    bc.lattice.data.points[7].co_deform = Vector(( 0.5,  0.5,  0.5))

    mod = bc.shape.modifiers.new(name='Lattice', type='LATTICE')
    mod.object = bc.lattice

    if bpy.app.version[:2] >= (2, 82):
        bevel = None
        for mod in bc.shape.modifiers:
            if mod.type == 'BEVEL':
                bevel = mod

                break

        if bevel:
            bc.shape.modifiers.new(name='Weld', type='WELD')

    modifier.sort(bc.shape, types=['LATTICE'], first=True)

    bc.lattice.data.transform(Matrix.Translation(Vector((0, 0, -0.5))))

    if op.origin == 'CORNER':
        bc.lattice.data.transform(Matrix.Translation(Vector((0.5, 0.5, 0))))

    for pair in zip(points, bc.lattice.data.points):
        pair[1].co_deform = pair[0]

    bc.shape.display_type = 'WIRE' if op.mode != 'MAKE' else 'TEXTURED'

    bc.lattice.matrix_world = matrix
    bc.shape.matrix_world = matrix

    bc.shape.hide_set(True)
    bc.lattice.hide_set(True)

    bpy.context.view_layer.objects.active = bc.shape
    bpy.ops.mesh.customdata_custom_splitnormals_clear()
    bpy.context.view_layer.objects.active = original_active

    context.view_layer.objects.active = original_active

    if op.shape_type != 'CUSTOM':
        op.shape_type = 'CUSTOM'


    if preference.shape.cycle_dimensions and not custom:
        preference.shape.dimension_x = dimensions.x
        preference.shape.dimension_y = dimensions.y
        if op.extruded:
            preference.shape.dimension_z = dimensions.z

        context.view_layer.update()

    return True
