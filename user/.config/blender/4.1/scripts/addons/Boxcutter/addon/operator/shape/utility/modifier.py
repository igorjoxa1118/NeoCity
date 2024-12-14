import bpy
import bmesh

from mathutils import Vector, Matrix

from . import mesh
from ..... utility import addon, object
from ..... utility.modifier import apply, sort, new, unmodified_bounds, bevels, move_to_index
from ..... utility.ct_modifier import mod_move_to_index, mod_move_down, mod_move_up


def shape_bool(obj):
    bc = bpy.context.scene.bc

    if obj:
        for mod in reversed(obj.modifiers):
            if mod.type == 'BOOLEAN' and mod.object == bc.shape and (not hasattr(mod, 'operand_type') or mod.operand_type != 'COLLECTION'):
                return mod

    return None


def update(op, context, force_edit_mode=True):
    bc = context.scene.bc
    original_active = context.active_object

    slices = op.datablock['slices']
    targets = op.datablock['targets']

    if not op.datablock['overrides']:
        bpy.ops.mesh.select_all(action='DESELECT')
        overrides = targets + slices

        for obj in overrides:
            bm = bmesh.from_edit_mesh(obj.data)
            obj.update_from_editmode()

        op.datablock['overrides'] = [obj.data.copy() for obj in overrides]

        for obj in op.datablock['slices']:
            for mod in obj.modifiers:
                if mod.type == 'BOOLEAN' and mod.object == bc.shape:
                    mod.show_viewport = True

    evaluated_objs = []

    evaluated = bc.shape.evaluated_get(context.evaluated_depsgraph_get())
    me = evaluated.to_mesh()
    evaluated_objs.append(evaluated)

    for poly in me.polygons:
        poly.select = True

    for index, obj in enumerate(targets):
        override = op.datablock['overrides'][index]

        bm = bmesh.from_edit_mesh(obj.data)
        cutter_mesh = me
        matrix = obj.matrix_world.inverted() @ bc.shape.matrix_world

        if op.mode == 'INSET':
            evaluated = op.datablock['insets'][index].evaluated_get(context.evaluated_depsgraph_get())
            cutter_mesh = evaluated.to_mesh()
            matrix = Matrix()

            for poly in cutter_mesh.polygons:
                poly.select = True

            evaluated_objs.append(evaluated)

        bmesh.ops.delete(bm, geom=bm.verts, context='VERTS')

        bm.from_mesh(cutter_mesh)

        bevel = mesh.bevel_weight_verify(bm)

        for edge in bm.edges:
            edge[bevel] = False

        bmesh.ops.transform(bm, matrix=matrix, verts=bm.verts)
        bm.from_mesh(override)
        bm.faces.active = None # XXX: prevents active face flicker
        bmesh.update_edit_mesh(obj.data)

    operation = 'UNION' if op.mode == 'JOIN' else 'INTERSECT'

    if op.mode in {'CUT', 'INSET', 'SLICE', 'EXTRACT'}:
        operation = 'DIFFERENCE'

    # elif op.mode == 'JOIN':
    #     operation = 'UNION'

    # elif op.mode == 'INTERSECT':
    #     operation = 'INTERSECT'

    if bpy.app.version[:2] < (2, 91):
        bpy.ops.mesh.intersect_boolean(operation=operation)
    else:
        bpy.ops.mesh.intersect_boolean(operation=operation, solver='FAST')

    if op.mode in {'SLICE', 'EXTRACT', 'INSET'}:
        evaluated = bc.shape.evaluated_get(context.evaluated_depsgraph_get())
        me = evaluated.to_mesh()

        for poly in me.polygons:
            poly.select = True

        overrides = op.datablock['overrides'][len(slices)-1:]

        for index, obj in enumerate(slices):
            override = overrides[index]

            bm = bmesh.from_edit_mesh(obj.data)
            cutter_mesh = me
            matrix = obj.matrix_world.inverted() @ bc.shape.matrix_world

            if op.mode == 'INSET':
                evaluated = op.datablock['insets'][index].evaluated_get(context.evaluated_depsgraph_get())
                cutter_mesh = evaluated.to_mesh()
                matrix = Matrix()

                for poly in cutter_mesh.polygons:
                    poly.select = True

                evaluated_objs.append(evaluated)

            bmesh.ops.delete(bm, geom=bm.verts, context='VERTS')

            bm.from_mesh(cutter_mesh)

            bevel = mesh.bevel_weight_verify(bm)

            for edge in bm.edges:
                edge[bevel] = False

            bmesh.ops.transform(bm, matrix=matrix, verts=bm.verts)
            bm.from_mesh(override)
            bm.faces.active = None # XXX: prevents active face flicker
            bmesh.update_edit_mesh(obj.data)

        if bpy.app.version[:2] < (2, 91):
            bpy.ops.mesh.intersect_boolean(operation='INTERSECT')

        else:
            bpy.ops.mesh.intersect_boolean(operation='INTERSECT', solver='FAST')

    for obj in evaluated_objs:
        obj.to_mesh_clear()

    context.view_layer.objects.active = original_active

    if not force_edit_mode:
        bpy.ops.object.mode_set(mode='OBJECT')


def clean(op, modifier_only=False):
    for obj in op.datablock['targets']:
        if shape_bool(obj):
            obj.modifiers.remove(shape_bool(obj))

    if not modifier_only:
        for obj in op.datablock['slices']:
            bpy.data.meshes.remove(obj.data)

        for obj in op.datablock['insets']:
            bpy.data.meshes.remove(obj.data)

        op.datablock['slices'] = list()
        op.datablock['insets'] = list()


def move(op, context, down:bool):
    if op.behavior == 'DESTRUCTIVE' : return

    bc = context.scene.bc
    move_func = mod_move_up if not down else mod_move_down

    op.inset_skip_move_bevel = True

    up = not down # i agree

    # if mod doesn't exist mid cut, then something else went wrong
    def bool_mod(obj, bool_obj):
        for mod in reversed(obj.modifiers):
            if mod.type == 'BOOLEAN' and mod.object == bool_obj:
                index = obj.modifiers[:].index(mod)
                return (mod, index)

    if op.mode != 'INSET':
        for col in (op.datablock['targets'],  op.datablock['slices']):
            for obj in col:
                mod, index = bool_mod(obj, bc.shape)
                move_func(mod)
                obj.data.update()

        return

    # consider target and inset slice pairs
    for target, inset in zip(op.datablock['targets'], op.datablock['insets']):
        mod, index = bool_mod(target, inset)

        can_move = (up and index and len(inset.modifiers) > 2) or (down and index + 1 < len(target.modifiers))

        # usually the whole add/remove approach is bad for performance
        if up and can_move:

            remove_index = -3
            target_index = index - 1 if target.modifiers[index - 1].type != 'BOOLEAN' or not (target.modifiers[index - 1].object in {bc.shape, bc.inset}) else index - 2

            skip = False
            while inset.modifiers[remove_index].type != target.modifiers[target_index].type:
                remove_index -= 1

                if remove_index < -len(inset.modifiers):
                    skip = True
                    break

            if not skip:
                inset.modifiers.remove(inset.modifiers[remove_index])

        # strip extra mods on up
        elif up and len(inset.modifiers) > 2:
            inset.modifiers.remove(inset.modifiers[-3])

        # inset is an exception, because we have underlying goals to achieve
        elif down and can_move:
            tgt_index = index + 1
            base_mod = target.modifiers[tgt_index]

            # we don't want to copy the main bool mods to the inset
            make_new = True
            if base_mod.type == 'BOOLEAN' and (base_mod.object == bc.shape or base_mod.object == bc.inset) and len(target.modifiers) > index + 2:
                tgt_index += 1

            # basic name comparison to prevent duplicates
            if len(inset.modifiers) > 2 and inset.modifiers[-3].name == target.modifiers[tgt_index].name:
                make_new = False

            base_mod = target.modifiers[tgt_index]

            if make_new:
                m = new(inset, name=base_mod.name, _type=base_mod.type, mod=base_mod)
                mod_move_up(m)
                mod_move_up(m)

        # elif not can_move: # i just wanted to see it

        # skip our main boolean on scroll up/down (hidden)
        if up and can_move and target.modifiers[index-1].type == 'BOOLEAN' and target.modifiers[index-1].object in {bc.shape, bc.inset}:
            move_func(mod) # extra call

        elif down and can_move and target.modifiers[index+1].type == 'BOOLEAN' and target.modifiers[index+1].object in {bc.shape, bc.inset}:
            move_func(mod) # extra call

        move_func(mod)


# TODO: move array here
class create:


    def __init__(self, op):
        self.boolean(op)


    @staticmethod
    def boolean(op, show=False):
        wm = bpy.context.window_manager
        preference = addon.preference()
        bc = bpy.context.scene.bc

        if not op.datablock['targets'] or (not op.live and not show):
            return

        # if shape_bool(op.datablock['targets'][0]):
        if bc.shape or bc.slice or bc.inset:
            for obj in op.datablock['targets']:
                if shape_bool(obj):
                    obj.modifiers.remove(shape_bool(obj))

            if bc.slice and not op.datablock['slices']:
                bpy.data.objects.remove(bc.slice)

            elif bc.inset and not op.datablock['insets']:
                bpy.data.objects.remove(bc.inset)

            for obj in op.datablock['slices']:
                bpy.data.objects.remove(obj)

            for obj in op.datablock['insets']:
                bpy.data.objects.remove(obj)

            op.datablock['slices'] = []
            op.datablock['insets'] = []

            bc.slice = None
            bc.inset = None

        bc.shape.display_type = 'WIRE' if op.mode != 'MAKE' else 'TEXTURED'
        bc.shape.hide_set(True)

        for obj in op.datablock['targets']:
            if not op.active_only or obj == bpy.context.view_layer.objects.active:
                mod = obj.modifiers.new(name='Boolean', type='BOOLEAN')

                if hasattr(mod, 'solver'):
                    mod.solver = 'EXACT' if op.mode == 'JOIN' and preference.behavior.join_exact else addon.preference().behavior.boolean_solver

                mod.show_viewport = show
                mod.show_expanded = False

                if bpy.app.version[:2] >= (2, 91):
                    mod.show_in_editmode = True

                mod.object = bc.shape
                mod.operation = 'DIFFERENCE' if op.mode not in {'JOIN', 'INTERSECT'} else 'UNION' if op.mode == 'JOIN' else 'INTERSECT'

                if op.mode != 'EXTRACT' or (op.mode == 'EXTRACT' and not preference.behavior.surface_extract):

                    if op.behavior == 'DESTRUCTIVE':
                        mod_move_to_index(mod, 0, force=True)
                    elif op.mode != 'KNIFE':
                        sort(obj, option=preference.behavior)
                elif op.mode != 'KNIFE':
                    sort(obj, types=['WEIGHTED_NORMAL'], last=True)

                if op.mode in {'INSET', 'SLICE', 'EXTRACT'}:
                    new = obj.copy()
                    new.data = obj.data.copy()

                    if op.mode in {'SLICE', 'EXTRACT'}:
                        if obj.users_collection:
                            for collection in obj.users_collection:
                                if bpy.context.scene.rigidbody_world and collection == bpy.context.scene.rigidbody_world.collection:
                                    continue

                                collection.objects.link(new)
                        else:
                            bpy.context.scene.collection.objects.link(new)

                        bc.slice = new

                    else:
                        bc.collection.objects.link(new)
                        new.bc.inset = True

                    new.select_set(True)

                    new.name = op.mode.title()
                    new.data.name = op.mode.title()

                    if op.mode == 'SLICE' and preference.behavior.recut:
                        for mod in new.modifiers:
                            if mod.type == 'BOOLEAN' and mod != shape_bool(new):
                                new.modifiers.remove(mod)

                    if op.mode not in {'SLICE', 'EXTRACT'}:
                        new.hide_set(True)

                    shape_bool(new).operation = 'INTERSECT'

                    # if op.mode == 'INSET':
                        # if op.original_mode == 'EDIT_MESH' or preference.behavior.recut:
                        #     new.modifiers.clear()

                        # else:
                        #     for mod in reversed(new.modifiers):
                        #         if mod.type == 'BOOLEAN' and mod.object == bc.shape:
                        #             new.modifiers.remove(mod)
                        #             break
                        #         new.modifiers.remove(mod)

                        #     apply(new)

                    if op.mode == 'INSET':
                        if op.original_mode == 'EDIT_MESH' or preference.behavior.recut and not preference.behavior.inset_bevel:
                            new.modifiers.clear()

                        new.display_type = 'WIRE'

                        object.hide_set(new, True, viewport=False)

                        # new.data.use_customdata_vertex_bevel = False
                        # new.data.use_customdata_edge_bevel = False
                        # new.data.use_customdata_edge_crease = False

                        solidify = new.modifiers.new(name='Solidify', type='SOLIDIFY')
                        solidify.thickness = op.last['thickness']
                        solidify.offset = 0
                        solidify.show_on_cage = True
                        solidify.use_even_offset = True
                        solidify.use_quality_normals = True

                        default_boolean = shape_bool(new)

                        if default_boolean:
                            new.modifiers.remove(default_boolean)

                        mod = new.modifiers.new(name='Boolean', type='BOOLEAN')
                        mod.show_viewport = True
                        mod.show_expanded = False
                        if bpy.app.version[:2] >= (2, 91):
                            mod.show_in_editmode = True
                        mod.object = bc.shape
                        mod.operation = 'INTERSECT'

                        for mod in bc.shape.modifiers:
                            if mod.type == 'SOLIDIFY':
                                bc.shape.modifiers.remove(mod)

                        bool = None
                        for mod in reversed(obj.modifiers):
                            if mod.type == 'BOOLEAN' and mod.object == new:
                                bool = mod
                                break

                        if not bool:
                            mod = obj.modifiers.new(name='Boolean', type='BOOLEAN')

                            if hasattr(mod, 'solver'):
                                mod.solver = addon.preference().behavior.boolean_solver

                            mod.show_viewport = show
                            mod.show_expanded = False
                            if bpy.app.version[:2] >= (2, 91):
                                mod.show_in_editmode = True
                            mod.object = new
                            mod.operation = 'DIFFERENCE'

                            if hasattr(wm, 'Hard_Ops_material_options'):
                                new.hops.status = 'BOOLSHAPE'

                            if op.behavior != 'DESTRUCTIVE':
                                sort(obj, option=preference.behavior)

                        bc.inset = new

                        for mod in bc.inset.modifiers[:]:
                            if mod.type == 'WEIGHTED_NORMAL':
                                bc.inset.modifiers.remove(mod)

                        original_active = bpy.context.active_object
                        bpy.context.view_layer.objects.active = new
                        bpy.ops.mesh.customdata_custom_splitnormals_clear()
                        bpy.context.view_layer.objects.active = original_active

                        if preference.behavior.inset_slice and not preference.behavior.inset_bevel:
                            slice_inset = obj.copy()
                            slice_inset.data = obj.data.copy()

                            for mod in slice_inset.modifiers[:]:
                                if mod.type == 'BOOLEAN':
                                    if mod.object is new:
                                        mod.operation = 'INTERSECT'

                                    elif mod.object == bc.shape:
                                        slice_inset.modifiers.remove(mod)

                            for col in obj.users_collection:
                                col.objects.link(slice_inset)

                            op.datablock['slices'].append(slice_inset)

                        op.datablock['insets'].append(new)

                        # if preference.behavior.inset_bevel:
                        #     preference.behavior.inset_bevel = False
                        #     preference.behavior.inset_bevel = True

                    else:
                        op.datablock['slices'].append(new)

        if op.mode == 'INSET' and preference.behavior.inset_bevel:
            preference.behavior.inset_bevel = False
            preference.behavior.inset_bevel = True

        hops = getattr(wm, 'Hard_Ops_material_options', False)

        if not len(bpy.data.materials[:]):
            hops = False

        if hops and hops.active_material:
            active_material = bpy.data.materials[hops.active_material]

            bc.shape.data.materials.clear()

            if op.mode not in {'SLICE', 'INSET', 'KNIFE', 'EXTRACT'}:
                bc.shape.data.materials.append(active_material)

                if op.mode != 'MAKE':
                    for obj in op.datablock['targets']:
                        mats = [slot.material for slot in obj.material_slots if slot.material]

                        obj.data.materials.clear()

                        for index, mat in enumerate(mats):
                            if not index or (mat != active_material or mat in op.existing[obj]['materials']):
                                obj.data.materials.append(mat)

                        if active_material not in obj.data.materials[:]:
                            obj.data.materials.append(active_material)

            elif op.mode in {'SLICE', 'INSET'}:
                for obj in op.datablock['targets']:
                    mats = [slot.material for slot in obj.material_slots if slot.material]

                    obj.data.materials.clear()

                    for index, mat in enumerate(mats):
                        if not index or (mat != active_material or mat in op.existing[obj]['materials']):
                            obj.data.materials.append(mat)

                    if op.mode == 'INSET' and active_material not in obj.data.materials[:]:
                        obj.data.materials.append(active_material)

                for obj in op.datablock['slices']:
                    obj.data.materials.clear()
                    obj.data.materials.append(active_material)

                for obj in op.datablock['insets']:
                    obj.data.materials.append(active_material)
                    mats = [slot.material for slot in obj.material_slots]
                    index = mats.index(active_material)

                    for mod in obj.modifiers:
                        if mod.type == 'SOLIDIFY':
                            mod.material_offset = index

                            break

        # XXX: ensure edit mode state
        if op.datablock['slices'] and op.original_mode == 'EDIT_MESH':
            for obj in op.datablock['slices']:
                obj.select_set(True)

            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.mode_set(mode='EDIT')
