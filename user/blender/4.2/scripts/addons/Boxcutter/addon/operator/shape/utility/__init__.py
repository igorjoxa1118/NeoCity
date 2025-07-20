import bpy
import bmesh

from mathutils import Matrix, Vector, Euler

from . import modal, change, custom, data, lattice, mesh, modifier, sound
from ..... utility import addon, object, math
from ..... utility.mesh import flip_normals


# XXX: deprecated
class tracked_events:
    mouse: dict = {}
    lmb: bool = False
    mmb: bool = False
    rmb: bool = False
    ctrl: bool = False
    alt: bool = False
    shift: bool = False


class tracked_states:
    running = None
    widgets = None
    widget = None

    mode: str = 'CUT'
    operation: str = 'DRAW'
    shape_type: str = 'BOX'
    origin: str = 'CENTER'
    rotated: bool = False
    scaled: bool = False
    cancelled: bool = False
    rmb_lock: bool = False
    modified: bool = False
    bounds: list = []
    thin: bool = False
    draw_dot_index: int = 0
    lazorcut: bool = False
    make_fallback: bool = False

    # partition('_')[-1] is used in hops notification text
    active_only: bool = False
    array_distance: float = 0.0

    shader_batch: bool = False


def bound_box(lattice=False):
    bc = bpy.context.scene.bc

    if bpy.app.version >= (4, 1) and not lattice:
        if not bc.shape:
            return []

        return bc.shape.bound_box


    if not bc.lattice:
        return []

    points = bc.lattice.data.points
    bounds = math.coordinate_bounds([p.co_deform for p in points])

    return bounds


def dimensions(lattice=False):
    bc = bpy.context.scene.bc

    if bpy.app.version >= (4, 1) and not lattice:
        if not bc.shape:
            return []

        return bc.shape.dimensions

    if not bc.lattice:
        return Vector([0, 0, 0])

    return bc.lattice.dimensions



def accucut_reset(op, bc, props=True, extrude=False, coord=[Matrix(), []]):
    if props:
        op.lazorcut = False
        op.lazorcut_performed = False

        op.start['offset'] = 0.0
        op.start['extrude'] = 0.0
        op.last['depth'] = 0.0

    if extrude:
        for index in lattice.back:
            bc.lattice.data.points[index].co_deform.z = op.start['extrude']

        bpy.context.view_layer.update()

    if coord and coord[1]:
        op.start['matrix'] = coord[0]
        bc.shape.matrix_world = coord[0]
        bc.plane.matrix_world = coord[0]
        bc.lattice.matrix_world = coord[0]

        for index, vector in enumerate(coord[1]):
            bc.lattice.data.points[index].co_deform = vector

        bpy.context.view_layer.update()


def accucut(op, context, extrude=True, reset=False):
    preference = addon.preference()
    bc = context.scene.bc

    matrix = bc.lattice.matrix_world.copy()
    points = [p.co_deform for p in bc.lattice.data.points]

    distance, depth = lazorcut(op, context)

    if reset:
        accucut_reset(op, bc, extrude=extrude, coord=[matrix, points] if reset else [])

    return (distance, depth)


def lazorcut(op, context):
    preference = addon.preference()
    bc = context.scene.bc

    boolean = False

    if op.mode == 'KNIFE' and preference.surface == 'VIEW' and op.start['view_matrix'] == context.region_data.view_matrix:
        return (0.0, 0.0)

    if op.shape_type == 'NGON' or op.ngon_fit:
        if not op.ngon_fit:
            lattice.fit(op, context)
            op.shape_type = 'BOX'
            op.ngon_fit = True

        if not op.extruded:
            amount = -0.5
            matrix = Matrix.Translation((0, 0, 0.5))
            bc.shape.data.transform(matrix)
            lattice.wedge(op, context)
            mesh.extrude(op, context, None, amount=amount)

        for mod in bc.shape.modifiers:
            if mod.type == 'BEVEL':
                bc.shape.modifiers.remove(mod)
                modal.bevel.shape(op, context, None)
                break

        if not preference.shape.cyclic:
            for mod in bc.shape.modifiers:
                if mod.type == 'SCREW':
                    bc.shape.modifiers.remove(mod)

                    break

    if op.shape_type == 'CUSTOM' and op.proportional_draw:
        op.lazorcut = True
        depth = preference.shape['dimension_x'] * op.datablock['shape_proportions'].z
        extrude_delta = -depth

        if op.mode in {'MAKE', 'JOIN'}:
            extrude_delta = -extrude_delta
            flip_normals(bc.shape.data)
            op.flipped_normals = not op.flipped_normals

        extrude = bc.lattice.data.points[lattice.front[0]].co_deform.z + extrude_delta
        for i in lattice.back:
            bc.lattice.data.points[i].co_deform.z = extrude

        boolean = bool([mod for obj in op.datablock['targets'] for mod in obj.modifiers if mod.type == 'BOOLEAN' and mod.object is bc.shape])

        if not boolean:
            modifier.create.boolean(op, show=op.live)

        return (0, depth)

    if preference.shape.wedge and preference.shape.wedge_lazorcut:
        op.lazorcut = True
        event = type("fake_event", (), {'ctrl': True})

        if op.mode in {'MAKE', 'JOIN'}:
            op.inverted_extrude = True
            flip_normals(bc.shape.data)
            op.flipped_normals = not op.flipped_normals

        operation = op.operation
        op.operation = 'EXTRUDE'
        lattice.wedge(op, context, event=event)
        op.operation = operation

        boolean = bool([mod for obj in op.datablock['targets'] for mod in obj.modifiers if mod.type == 'BOOLEAN' and mod.object is bc.shape])
        if not boolean:
            modifier.create.boolean(op, show=op.live)

        return(0, op.last['depth'])

    start = bc.lattice.matrix_world.translation

    if op.mode == 'MAKE':
        bc.shape.display_type = 'TEXTURED'

    for obj in op.datablock['targets']:
        for mod in reversed(obj.modifiers[:]):
            if mod.type == 'BOOLEAN' and mod.object == bc.shape:
                boolean = True
                mod.show_viewport = True

    op.lazorcut = True

    if op.mode != 'MAKE' and not boolean:
        modifier.create.boolean(op, show=op.live)

    if op.datablock['targets'] and op.mode not in {'MAKE', 'JOIN'}:
        init_point_positions(op, bc, context)

    else:
        pref_depth = preference.shape.lazorcut_depth
        pref_depth = pref_depth if pref_depth > 0 else 0.5
        init_point_positions(op, bc, context, depth=pref_depth)

        return (0.0, 0.0)

    alignment = op.start['alignment']
    if not preference.behavior.accucut or not alignment or not op.datablock['targets']:
        return (0.0, 0.0)

    objects = [obj.copy() for obj in op.datablock['targets'] if obj.type == 'MESH']

    for obj in objects:
        context.scene.collection.objects.link(obj)

    context.view_layer.update()

    for obj in objects:

        for mod in obj.modifiers:
            if mod.type == 'BOOLEAN' and mod.object == bc.shape and (not hasattr(mod, 'operand_type') or mod.operand_type != 'COLLECTION'):
                obj.modifiers.remove(mod)

    tmp = bpy.data.meshes.new(name='TMP')
    bm = bmesh.new()

    # for o, obj in zip(op.datablock['targets'], objects):
    #     obj.matrix_world = o.matrix_world

    # context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    for obj in objects:
        me = obj.evaluated_get(depsgraph).to_mesh()
        me.transform(obj.matrix_world)
        bm.from_mesh(me)
        # obj.location = Vector()

        bpy.data.objects.remove(obj)

    del objects

    bm.to_mesh(tmp)
    bm.free()

    obj = bpy.data.objects.new(name='TMP', object_data=tmp)
    obj.display_type = 'WIRE'
    context.scene.collection.objects.link(obj)
    obj.bc.removeable = True
    obj.data.bc.removeable = True

    # mod = obj.modifiers.new(name='TMP', type='DISPLACE')
    # mod.mid_level = 0
    # mod.strength = preference.shape.offset

    # TODO: manifold thin shape check method
    if True in [dimension < 0.00001 for dimension in obj.dimensions[:]] and (op.shape_type == 'CUSTOM' or (op.shape_type == 'NGON' and not op.extruded)):
        mod = obj.modifiers.new(name='TMP', type='SOLIDIFY')
        mod.offset = 0.0
        mod.thickness = 0.0001

    mod = obj.modifiers.new(name='TMP', type='BOOLEAN')

    if hasattr(mod, 'solver'):
        mod.solver = addon.preference().behavior.boolean_solver

    mod.operation = 'INTERSECT'
    mod.object = bc.shape

    obj.data.transform(bc.shape.matrix_world.inverted())
    obj.matrix_world = bc.shape.matrix_world

    context.view_layer.update()

    front = (1, 2, 5, 6)
    location = (0.25 * sum((Vector(bound_box()[point][:]) for point in front), Vector()))
    location_to = (0.25 * sum((Vector(obj.bound_box[point][:]) for point in front), Vector()))
    difference = (location - location_to)
    difference.z -= preference.shape.offset if preference.behavior.boolean_solver == 'FAST' else 0.0

    # if obj.dimensions[2] < 0.001:
    #     print('here')
    #     return

    # aligned = op.mode == 'KNIFE' and op.align_to_view
    depth = preference.shape.lazorcut_depth + (preference.shape.offset if preference.behavior.boolean_solver == 'FAST' else 0)
    for point in lattice.back:
        bc.lattice.data.points[point].co_deform.z = -(obj.dimensions[2] + difference.z + (preference.shape.offset + 0.01) if not preference.shape.lazorcut_depth else depth)

    if op.shape_type == 'NGON':
        bevel = False
        segment_count = preference.shape.bevel_segments
        for mod in bc.shape.modifiers:
            if mod.type == 'BEVEL':
                bevel = True

                if mod.segments != segment_count:
                    segment_count = mod.segments

                bc.shape.modifiers.remove(mod)

        if not op.extruded:
            modal.extrude.shape(op, context, None, extrude_only=True)

        if bevel:
            modal.bevel.shape(op, context, None)

        for mod in bc.shape.modifiers:
            if mod.type == 'BEVEL':
                if mod.segments != segment_count:
                    mod.segments = segment_count

        verts = [vert for vert in bc.shape.data.vertices[:] if vert.index in op.geo['indices']['extrusion']]

        for vert in verts:
            vert.co.z = -(obj.dimensions[2] + ((preference.shape.offset + 0.01 if preference.behavior.boolean_solver == 'FAST' else 0)) if not preference.shape.lazorcut_depth else depth)

    # matrix = bc.shape.matrix_world.inverted()

    current = bc.shape.location
    location = Vector((0, 0, -difference.z)) @ bc.shape.matrix_world.inverted()

    # for point in (0, 1, 2, 3, 4, 5, 6, 7):
    #     bc.lattice.data.points[point].co_deform = bc.lattice.data.points[point].co_deform + location
    bc.lattice.location = current + location
    bc.shape.location = current + location

    context.view_layer.update()

    op.start['matrix'] = bc.shape.matrix_world.copy()

    obj.data.bc.removeable = True
    bpy.data.objects.remove(obj)

    del obj

    op.lazorcut_performed = not preference.shape.auto_depth
    points = bc.lattice.data.points
    op.start['offset'] = points[lattice.front[0]].co_deform.z
    op.start['extrude'] = points[lattice.back[0]].co_deform.z
    op.last['depth'] = points[lattice.back[0]].co_deform.z

    lattice.wedge(op, context)

    return (start - (current + location)).length, abs(bc.lattice.data.points[0].co_deform.z)


def init_point_positions(op, bc, context, depth=None):
    aligned = op.mode == 'KNIFE' and op.align_to_view
    if op.shape_type != 'NGON':
        for point in lattice.back:
            if context.active_object and not depth:
                bc.lattice.data.points[point].co_deform.z -= max(op.datablock['dimensions']) * 2
            elif depth:
                bc.lattice.data.points[point].co_deform.z -= depth
            else:
                bc.lattice.data.points[point].co_deform.z -= 0.5

    elif not aligned:
        if not op.extruded:
            # modal.extrude.shape(op, context, None)
            mesh.extrude(op, context, None)

        verts = [vert for vert in bc.shape.data.vertices[:] if vert.index in op.geo['indices']['extrusion']]

        for vert in verts:
            if bc.original_active and not depth:
                vert.co.z -= max(op.datablock['dimensions']) * 2
            elif depth:
                vert.co.z -= depth
            else:
                vert.co.z -= 0.5
