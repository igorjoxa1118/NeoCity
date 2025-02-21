import traceback, itertools

import bpy
import bmesh

from math import radians

from mathutils import Matrix, Vector

from .... import toolbar

from ..... utility import addon, object, math, operator_override
from ..... utility import mesh as _mesh
from ..... utility import modifier as _modifier
# from .. shape import lattice, mesh, modifier, modal
from . import lattice, mesh, modifier, modal, custom
from . modal.bevel import clamp
# from .. shape import custom as _custom


def restore_overrides(op, clear=True):
    slices = op.datablock['slices'] if op.mode != 'INSET' else []

    for pair in zip(op.datablock['targets'] + slices, op.datablock['overrides']):
        obj = pair[0]
        override = pair[1]

        if bpy.context.mode == 'OBJECT':
            old_data = obj.data
            obj.data.user_remap(override if clear else override.copy())
            obj.data.name = old_data.name
            bpy.data.meshes.remove(old_data)

        else:
            bm = bmesh.from_edit_mesh(obj.data)
            bmesh.ops.delete(bm, geom = bm.verts, context = 'VERTS')
            bm.from_mesh(override)
            bm.faces.active = None
            bmesh.update_edit_mesh(obj.data)
            obj.update_from_editmode()

            if clear:
                bpy.data.meshes.remove(override)

    if clear:
        op.datablock['overrides'] = list()


def create(op, context, event, custom_cutter=None):
    bc = context.scene.bc
    preference = addon.preference()

    mesh.create.shape(op, context, event)
    lattice.create(op, context, event)

    if custom_cutter:
        custom.cutter(op, context, custom=custom_cutter)

    bc.empty = bpy.data.objects.new(name=F'{bc.shape.name} Array Target', object_data=None)
    bc.collection.objects.link(bc.empty)
    bc.empty.empty_display_type = 'SINGLE_ARROW'
    bc.empty.parent = bc.shape
    # bc.empty.hide_set(True)

    if op.shape_type == 'BOX' and op.mode != 'KNIFE' and preference.shape.box_grid and preference.shape.box_grid_auto_solidify:
        bc.shape.bc.solidify = True
        modal.solidify.shape(op, context, event)


def repeat(op, context, collect=False):
    bc = context.scene.bc
    preference = addon.preference()
    repeated = False
    repeat_name = '_bc_repeat'

    if not collect:
        if repeat_name in bpy.data.meshes:
            repeated = True
            repeat_mesh = bpy.data.meshes[repeat_name].copy()

            bc.shape.vertex_groups.clear()

            for name in bc.repeat_data['vertex_groups']:
                bc.shape.vertex_groups.new(name=name)

            name = bc.shape.name
            me = bc.shape.data
            bc.shape.data.user_remap(repeat_mesh)
            bc.shape.data.name = name
            bpy.data.meshes.remove(me)

            bc.shape.modifiers.clear()

            _, rot, sca =  bc.repeat_data['delta_matrix'].decompose()
            quat = bc.shape.matrix_world.to_quaternion() @ rot
            bc.shape.matrix_world = bc.lattice.matrix_world = bc.plane.matrix_world = Matrix.Translation(bc.shape.matrix_world.translation) @ quat.to_matrix().to_4x4() @ Matrix.Diagonal(sca).to_4x4()

            if repeat_name in bpy.data.objects:
                repeat_obj = bpy.data.objects[repeat_name]

                override = {'object': repeat_obj, 'active_object': repeat_obj, 'selected_editable_objects': [bc.shape], 'selected_objects': [bc.shape]}
                operator_override(context, bpy.ops.object.make_links_data, override, type='MODIFIERS')

                for mod in bc.shape.modifiers: # remap object references or exception
                    if mod.type == 'LATTICE':
                        mod.object = bc.lattice

                    elif mod.type == 'ARRAY':
                        if mod.offset_object:
                            mod.offset_object = bc.empty

                            if bc.repeat_data['array_circle']:
                                bc.empty.driver_remove('rotation_euler', 2)
                                driver = bc.empty.driver_add('rotation_euler', 2).driver
                                driver.type == 'SCRIPTED'

                                count = driver.variables.new()
                                count.name = 'count'
                                count.targets[0].id_type = 'OBJECT'
                                count.targets[0].id = bc.shape
                                count.targets[0].data_path = F'modifiers["{mod.name}"].count'

                                driver.expression = 'radians(360 / count)'

                    elif mod.type == 'MIRROR':
                        mod.mirror_object = bc.original_active

            for vec, point in zip (bc.repeat_data['lattice_deform'], bc.lattice.data.points):
                point.co_deform = vec

            bc.shape.bc.array = bc.repeat_data['array']
            bc.shape.bc['array_circle'] = bc.repeat_data['array_circle']
            bc.shape.bc.bevel = bc.repeat_data['bevel']
            bc.shape.bc.solidify = bc.repeat_data['solidify']

            op.start['extrude'] = op.last['depth'] = bc.repeat_data['last_depth']

            op.ngon_fit = bc.repeat_data['ngon_fit']
            op.shape_type = bc.repeat_data['shape_type']
            op.last['wedge_points'] = bc.repeat_data['wedge_points']
            preference.shape.taper = bc.repeat_data['taper']
            op.inverted_extrude = bc.repeat_data['inverted_extrude']
            op.clamp_extrude = bc.repeat_data['clamp_extrude']
            op.flipped_normals = bc.repeat_data['flipped_normals']
            op.flip_x = bc.repeat_data['flip_x']
            op.flip_y = bc.repeat_data['flip_y']
            op.flip_z = bc.repeat_data['flip_z']
            op.proportional_draw = bc.repeat_data['proportional_draw']

            op.geo['indices']['top_edge'] = bc.repeat_data['geo_indices']['top_edge']
            op.geo['indices']['mid_edge'] = bc.repeat_data['geo_indices']['mid_edge']
            op.geo['indices']['bot_edge'] = bc.repeat_data['geo_indices']['bot_edge']
            op.geo['indices']['top_face'] = bc.repeat_data['geo_indices']['top_face']
            op.geo['indices']['bot_face'] = bc.repeat_data['geo_indices']['bot_face']
            op.geo['indices']['offset'] = bc.repeat_data['geo_indices']['offset']
            op.geo['indices']['extrusion'] = bc.repeat_data['geo_indices']['extrusion']

    if not repeated or collect:
        if repeat_name in bpy.data.meshes: #TODO: add mesh property to track repeat basis
            bpy.data.meshes.remove(bpy.data.meshes[repeat_name])

        if repeat_name in bpy.data.objects:
            bpy.data.objects.remove(bpy.data.objects[repeat_name])

        repeat_obj = bc.shape.copy()
        repeat_obj.name = repeat_name
        repeat_obj.use_fake_user = True

        repeat_mesh = bc.shape.data.copy()
        repeat_mesh.name = repeat_name
        repeat_mesh.use_fake_user = True

        bc.repeat_data['modifiers'] = [_modifier.stored(mod) for mod in bc.shape.modifiers]
        bc.repeat_data['lattice_deform'] = [Vector(point.co_deform) for point in bc.lattice.data.points]
        bc.repeat_data['array'] = bc.shape.bc.array
        bc.repeat_data['array_circle'] = bc.shape.bc.array_circle
        bc.repeat_data['bevel'] = bc.shape.bc.bevel
        bc.repeat_data['solidify'] = bc.shape.bc.solidify
        bc.repeat_data['last_depth'] = op.last['depth']
        bc.repeat_data['ngon_fit'] = op.ngon_fit
        bc.repeat_data['shape_type'] = op.shape_type
        bc.repeat_data['wedge_points'] = op.last['wedge_points']
        bc.repeat_data['taper'] = preference.shape.taper
        bc.repeat_data['delta_matrix'] = op.start['init_matrix'].inverted() @ bc.shape.matrix_world
        bc.repeat_data['vertex_groups'] = [group.name for group in bc.shape.vertex_groups]
        bc.repeat_data['inverted_extrude'] =  op.inverted_extrude
        bc.repeat_data['clamp_extrude'] = op.clamp_extrude
        bc.repeat_data['flipped_normals'] = op.flipped_normals
        bc.repeat_data['flip_x'] = op.flip_x
        bc.repeat_data['flip_y'] = op.flip_y
        bc.repeat_data['flip_z'] = op.flip_z
        bc.repeat_data['proportional_draw'] = op.proportional_draw

        bc.repeat_data['geo_indices']['top_edge'] = op.geo['indices']['top_edge']
        bc.repeat_data['geo_indices']['mid_edge'] = op.geo['indices']['mid_edge']
        bc.repeat_data['geo_indices']['bot_edge'] = op.geo['indices']['bot_edge']
        bc.repeat_data['geo_indices']['top_face'] = op.geo['indices']['top_face']
        bc.repeat_data['geo_indices']['bot_face'] = op.geo['indices']['bot_face']
        bc.repeat_data['geo_indices']['offset'] = op.geo['indices']['offset']
        bc.repeat_data['geo_indices']['extrusion'] = op.geo['indices']['extrusion']

    return repeated


def clean(op, context, clean_all=False):
    preference = addon.preference()
    bc = context.scene.bc
    type_to_custom = False

    for obj in context.selected_objects:
        obj.select_set(False)

    if op.wires_displayed:
        for pair in zip(op.datablock['targets'], op.datablock['wireframes']):
            obj = pair[0]
            wire_data = pair[1]
            obj.show_wire = wire_data[0]
            obj.show_all_edges = wire_data[1]

    if not op.cancelled and not op.live and op.mode in {'CUT', 'SLICE', 'INTERSECT', 'INSET', 'JOIN', 'EXTRACT'}:
        modifier.create.boolean(op, show=True)

    if not op.start_exact and preference.behavior.boolean_solver == 'EXACT':
        preference.behavior['boolean_solver'] = 'FAST'

    if bc.shape:
        bc.shape.hide_set(False)

    if bc.lattice:
        bc.lattice.hide_set(False)

    if context.space_data.show_region_toolbar != op.show_region_toolbar:
        context.space_data.show_region_toolbar = op.show_region_toolbar

    if context.space_data.show_region_ui != op.show_region_ui:
        context.space_data.show_region_ui = op.show_region_ui

    context.view_layer.update()

    if bc.shape:
        bc.shape.data.update()

    for mod in bc.shape.modifiers:
        mod.show_viewport = True

        if mod.type == 'BEVEL':
            if mod.name.startswith('Quad'):
                preference.shape['quad_bevel_segments'] = mod.segments

            elif mod.name.startswith('Front'):
                preference.shape['front_bevel_segments'] = mod.segments

            else:
                preference.shape['bevel_segments'] = mod.segments

    for obj in itertools.chain(op.datablock['targets'], op.datablock['slices'], op.datablock['insets']):
        for mod in obj.modifiers:
            if mod.type == 'BOOLEAN' and mod.object == bc.shape:
                mod.show_viewport = True

    for obj in context.visible_objects:
        if obj not in op.datablock['wire_targets']:
            obj.show_wire = False
            obj.show_all_edges = False

    if not clean_all and op.shape_type == 'CIRCLE' and preference.shape.circle_type == 'MODIFIER' and not preference.behavior.keep_screw:
        deletable = [mod for mod in bc.shape.modifiers if mod.type in {'SCREW', 'DECIMATE'}]
        for mod in deletable:
            bc.shape.modifiers.remove(mod)

        bm = bmesh.new()
        bm.from_mesh(bc.shape.data)
        bmesh.ops.spin(bm, geom=bm.verts[:] + bm.edges[:], cent=(0, 0, 0), axis=(0, 0, 1), steps=preference.shape.circle_vertices, angle=radians(360), use_merge=True)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.01)
        bmesh.ops.dissolve_limit(bm, angle_limit=0.01, use_dissolve_boundaries=False, verts=bm.verts, edges=bm.edges)

        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

        if preference.behavior.auto_smooth:
            for face in bm.faces:
                face.smooth = True

        bm.to_mesh(bc.shape.data)
        bc.shape.data.update()

    keep_types = [type for type in ('BEVEL', 'SOLIDIFY', 'ARRAY', 'MIRROR', 'SCREW', 'LATTICE') if getattr(preference.behavior, F'keep_{type.lower()}')] if preference.behavior.keep_modifiers else []
    keep_types.append('DISPLACE')
    keep_types.append('DECIMATE')

    if 'BEVEL' in keep_types:
        keep_types.append('VERTEX_WEIGHT_MIX')
        keep_types.append('VERTEX_WEIGHT_EDIT')

    if bpy.app.version[:2] >= (2, 82):
        keep_types.append('WELD')

    if preference.behavior.keep_lattice_taper and preference.shape.taper != 1:
        keep_types.append('LATTICE')

    if op.mode != 'KNIFE':
        modifier.apply(bc.shape, ignore=[mod for mod in bc.shape.modifiers if mod.type in keep_types])

    live = op.live if bpy.app.version[:2] < (2, 91) else False if op.behavior == 'DESTRUCTIVE' else op.live

    if not clean_all and not live and not op.lazorcut and op.original_mode == 'EDIT_MESH' and op.mode not in {'EXTRACT', 'KNIFE'}:
        if op.mode == 'INSET':

            for obj in op.datablock['targets'] + op.datablock['slices']:
                for mod in reversed(obj.modifiers[:]):
                    if mod.type == 'BOOLEAN' and mod.object == bc.shape and (not hasattr(mod, 'operand_type') or mod.operand_type != 'COLLECTION'):
                        obj.modifiers.remove(mod)

                        break

        if bpy.app.version[:2] < (2, 91) or op.behavior == 'DESTRUCTIVE' and op.mode != 'MAKE':
            modifier.update(op, context, force_edit_mode=False)

            for obj in op.datablock['slices']:
                bpy.data.objects.remove(obj)

            op.datablock['slices'].clear()

            for obj in op.datablock['insets']:
                bpy.data.objects.remove(obj)

            op.datablock['insets'].clear()

    if not clean_all and op.lazorcut:
        if op.mode not in {'MAKE', 'KNIFE', 'EXTRACT'} and op.original_mode == 'EDIT_MESH':
            if op.mode == 'INSET':

                for obj in op.datablock['targets'] + op.datablock['slices']:
                    for mod in reversed(obj.modifiers):
                        if mod.type == 'BOOLEAN' and mod.object == bc.shape and (not hasattr(mod, 'operand_type') or mod.operand_type != 'COLLECTION'):
                            obj.modifiers.remove(mod)
                            break

            if bpy.app.version[:2] < (2, 91) or op.behavior == 'DESTRUCTIVE':
                modifier.update(op, context, force_edit_mode=False)

                for obj in op.datablock['slices']:
                    bpy.data.objects.remove(obj)

                op.datablock['slices'].clear()

                for obj in op.datablock['insets']:
                    bpy.data.objects.remove(obj)

                op.datablock['insets'].clear()

        elif op.mode == 'KNIFE':
            shape_select = bc.shape.select_get()
            bc.shape.select_set(False) # assume bc.shape in object mode!

            if preference.surface != 'VIEW' or op.start['view_matrix'] != context.region_data.view_matrix:
                op.extruded = True
                mesh.knife(op, context, None)

            else:
                clean_all = True
                split = bc.shape.modifiers.new(type ='EDGE_SPLIT', name = 'EDGESPLIT')

                split.use_edge_angle = True
                split.split_angle = 0

                hops_mark = addon.hops() and addon.preference().behavior.hops_mark

                for obj in op.datablock['targets']:
                    context.view_layer.objects.active = obj
                    obj.select_set(True)

                    bpy.ops.object.mode_set(mode='EDIT')

                    bm = bmesh.from_edit_mesh(obj.data)
                    orig_verts = set(bm.verts)

                    bc.shape.select_set(True)
                    bpy.ops.mesh.knife_project(cut_through=preference.behavior.cut_through)
                    bpy.ops.mesh.select_all(action='DESELECT')
                    bc.shape.select_set(False)

                    bmesh.ops.remove_doubles(bm, verts = bm.verts, dist = 0.0001)

                    new_verts = [v for v in bm.verts if v not in orig_verts]

                    for vert in new_verts:
                        vert.select = True

                    bm.select_flush(True)

                    if hops_mark:
                        pref = addon.hops().property

                        bevel = mesh.bevel_weight_verify(bm)
                        crease = mesh.crease_verify(bm)

                        selected_faces = {face for face in bm.faces if face.select}
                        selected_edges = set()

                        for face in selected_faces:
                            selected_edges.update(face.edges)

                        boundary = [edge for edge in selected_edges if not selected_faces.issuperset(edge.link_faces)] if selected_faces else [edge for edge in bm.edges if edge.select]

                        for edge in boundary:
                            edge[crease] = pref.sharp_use_crease
                            edge[bevel] = pref.sharp_use_bweight
                            edge.seam = pref.sharp_use_seam
                            edge.smooth  = not pref.sharp_use_sharp

                    bmesh.update_edit_mesh(obj.data)

                    bpy.ops.object.mode_set(mode='OBJECT')

                    obj.select_set(False)
                    bc.shape.select_set(shape_select)

                context.view_layer.objects.active = bc.original_active

                for obj in op.datablock['targets']:
                    obj.select_set(True)

                if op.original_mode == 'EDIT_MESH':
                    bpy.ops.object.mode_set(mode='EDIT')

        elif op.mode == 'MAKE':
            bm = bmesh.new()
            bm.from_mesh(bc.shape.data)

            bmesh.ops.recalc_face_normals(bm, faces = bm.faces)

            bm.to_mesh(bc.shape.data)
            bc.shape.data.update()
            bm.free()

    # modal.bevel_modifiers = list()

    if context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

    context.view_layer.objects.active = bc.shape

    if not clean_all:
        if op.mode == 'EXTRACT':
            type_to_custom = True

            restore_overrides(op)

            for obj in op.datablock['targets']:
                for mod in obj.modifiers[:]:
                    if mod.type == 'BOOLEAN' and mod.object == bc.shape and (not hasattr(mod, 'operand_type') or mod.operand_type != 'COLLECTION'):
                        obj.modifiers.remove(mod)

            if preference.behavior.surface_extract:
                slice_bound_coordinates = []

                for obj in op.datablock['slices']:
                    for mod in obj.modifiers[:]:
                        if mod.type == 'BEVEL':
                            obj.modifiers.remove(mod)

                    context.view_layer.update()

                    modifier.apply(obj)

                    object.apply_transforms(obj)
                    obj.data.transform(bc.shape.matrix_world.inverted())

                    slice_bound_coordinates.extend(object.bound_coordinates(obj, local=True))

                if slice_bound_coordinates:
                    new = bc.shape.copy()
                    new.data = bc.shape.data.copy()
                    new.name = 'Extraction'

                    object.clear_transforms(new)

                    bc.collection.objects.link(new)

                    trim = bpy.data.objects.new('trim', bpy.data.meshes.new('trim'))
                    bc.collection.objects.link(trim)

                    bm = bmesh.new()

                    bmesh.ops.create_cube(bm)

                    bm.to_mesh(trim.data)
                    bm.free()

                    bbox_coords = math.coordinate_bounds(slice_bound_coordinates)
                    trim.location = math.coordinates_center(bbox_coords)
                    trim.dimensions = math.coordinates_dimension(bbox_coords)

                    mod = new.modifiers.new(name='Displace', type='DISPLACE')
                    mod.mid_level = 0
                    mod.strength = -0.0001

                    mod = new.modifiers.new(name='Boolean', type='BOOLEAN')
                    mod.operation = 'INTERSECT'
                    mod.object = trim

                    mod = new.modifiers.new(name='Displace', type='DISPLACE')
                    mod.mid_level = 0
                    mod.strength = -0.002

                    for obj in op.datablock['slices']:
                        mod = new.modifiers.new(name='Boolean', type='BOOLEAN')
                        mod.operation = 'DIFFERENCE'
                        mod.object = obj

                    modifier.apply(new)
                    bpy.data.objects.remove(trim)

            else:

                slice_duplicates = []
                for obj in op.datablock['slices']:
                    for mod in obj.modifiers[:]:

                        if mod.type in {'BEVEL', 'MIRROR'}:
                            obj.modifiers.remove(mod)

                    context.view_layer.update()

                    object.apply_transforms(obj)

                    new = obj.copy()
                    slice_duplicates.append(new)
                    obj.data = obj.data.copy()

                    bc.collection.objects.link(new)

                    modifier.apply(obj)

                me = bpy.data.meshes.new(name='Extraction')
                bm = bmesh.new()
                for obj in slice_duplicates:
                    for mod in obj.modifiers[:]:

                        if mod.type == 'BOOLEAN' and mod.operation != 'INTERSECT':
                            obj.modifiers.remove(mod)

                    context.view_layer.update()

                    modifier.apply(obj)

                    center = object.center(obj, local=True)
                    obj.location = obj.matrix_world @ center
                    obj.data.transform(Matrix.Translation(-center))

                    _mesh.transform_scale(obj.data, uniform=0.998)

                    obj.data.transform(Matrix.Translation(obj.location))

                    bm.from_mesh(obj.data)

                    bpy.data.objects.remove(obj)
                bm.to_mesh(me)
                bm.free()

                new = bpy.data.objects.new(name='Extraction', object_data=me)
                bc.collection.objects.link(new)

                for obj in op.datablock['slices']:
                    mod = new.modifiers.new(name='Boolean', type='BOOLEAN')
                    mod.operation = 'DIFFERENCE'
                    mod.object = obj

                context.view_layer.update()

                modifier.apply(new)

                new.data.transform(bc.shape.matrix_world.inverted())

            context.view_layer.update()

            if addon.preference().behavior.auto_smooth:
                if bpy.app.version < (4, 1):
                    new.data.use_auto_smooth = True
                    new.data.auto_smooth_angle = radians(15)

                for face in obj.data.polygons:
                    face.use_smooth = True

            if bpy.app.version[:2] < (3, 4):
                new.data.use_customdata_vertex_bevel = True
                new.data.use_customdata_edge_bevel = True
                new.data.use_customdata_edge_crease = True

            if sum(new.dimensions) > 0.001:
                bc.__class__.extract_matrix = bc.shape.matrix_world.copy()

                center = object.center(new, local=True)

                new.location = obj.matrix_world @ center
                new.data.transform(Matrix.Translation(-center))

                object.clear_transforms(new)

                bc.stored_shape = new
                new.hide_set(True)

                bc.extract_name = new.name
                bc.extract_matrix.translation = bc.extract_matrix @ center

            else:
                bpy.data.objects.remove(new)
                op.report({'INFO'}, F'Cancelled. Extracted volume is too small')

            bpy.data.objects.remove(bc.shape)
            bc.shape = None

            for obj in op.datablock['slices']:
                bpy.data.objects.remove(obj)

            if bc.original_active:
                context.view_layer.objects.active = bc.original_active

            for obj in op.original_selected:
                obj.select_set(True)

            restore_overrides(op)

        elif op.mode != 'KNIFE':
            if op.mode != 'MAKE':
                if op.original_mode != 'EDIT_MESH':
                    if (op.shape_type == 'CIRCLE' and preference.shape.circle_type == 'MODIFIER') or op.shape_type == 'NGON':
                        bm = bmesh.new()
                        bm.from_mesh(bc.shape.data)
                        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.00001)

                        if bm.faces:
                            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

                        bm.to_mesh(bc.shape.data)
                        bc.shape.data.update()

                    if op.behavior != 'DESTRUCTIVE':
                        bc.shape.bc.applied = True

            else:
                # TODO: if in edit mode join made geo with active object
                bc.collection.objects.unlink(bc.shape)

                if bc.original_active and bc.original_active.users_collection:
                    for collection in bc.original_active.users_collection:
                        collection.objects.link(bc.shape)
                else:
                    context.collection.objects.link(bc.shape)

                context.view_layer.objects.active = bc.shape

                if (op.shape_type == 'CIRCLE' and preference.shape.circle_type == 'MODIFIER') or op.shape_type == 'NGON':
                    bm = bmesh.new()
                    bm.from_mesh(bc.shape.data)
                    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.00001)

                    if bm.faces:
                        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

                    bm.to_mesh(bc.shape.data)
                    bc.shape.data.update()

                bc.shape.name = op.shape_type.title()
                bc.shape.data.name = op.shape_type.title()
                bc.shape.bc.applied = True

                object.hide_set(bc.shape, False)

                if addon.preference().behavior.auto_smooth:
                    bc.shape.data.use_auto_smooth = True
                    # bc.shape.data.auto_smooth_angle = radians(15)

            if op.show_shape:
                bc.shape.hide_set(False)

                if (not preference.keymap.make_active and op.datablock['targets']) or (not op.shift and op.datablock['targets']):
                    context.view_layer.objects.active = bc.original_active
                    bc.original_active.select_set(True)
                    bc.shape.select_set(False)

                else:
                    bc.shape.select_set(op.mode != 'INSET')

                    for obj in context.visible_objects:
                        if obj != bc.shape:
                            obj.select_set(False)

                        # elif not bc.original_active:
                        #     context.view_layer.objects.active = obj
                        #     obj.select_set(True)

                    if op.mode == 'INSET':
                        if bc.bevel:
                            bc.bevel.hide_set(False)
                            bc.bevel.select_set(True)
                            context.view_layer.objects.active = bc.bevel

                        else:
                            bc.inset.hide_set(False)
                            bc.inset.select_set(True)
                            context.view_layer.objects.active = bc.inset

                if op.original_mode == 'EDIT_MESH' and op.datablock['targets']:
                    restore_overrides(op)
                    context.view_layer.objects.active = bc.shape

            else:
                if op.mode != 'MAKE':
                    bc.shape.hide_set(preference.behavior.autohide_shapes)

                    if op.mode == 'INSET':
                        bc.shape.select_set(False)

                        for obj in op.datablock['insets']:
                            obj.hide_set(preference.behavior.autohide_shapes)

                    if op.original_mode == 'EDIT_MESH':
                        if bpy.app.version[:2] < (2, 91) or op.behavior == 'DESTRUCTIVE':

                            for obj in op.datablock['slices']:
                                obj.select_set(True)

                                for mod in obj.modifiers[:]:
                                    if mod.type == 'BOOLEAN' and mod.object == bc.shape and (not hasattr(mod, 'operand_type') or mod.operand_type != 'COLLECTION'):
                                        obj.modifiers.remove(mod)

                            for obj in op.datablock['slices']:
                                bpy.data.objects.remove(obj)

                            op.datablock['slices'].clear()

                            for obj in op.datablock['insets']:
                                bpy.data.objects.remove(obj)

                            op.datablock['insets'].clear()

                if op.datablock['targets']:
                    context.view_layer.objects.active = bc.original_active
                    bc.original_active.select_set(True)

                    bpy.ops.object.mode_set(mode='OBJECT')

                    for obj in op.original_selected:
                        obj.select_set(True)

                    if op.behavior == 'DESTRUCTIVE' and op.original_mode != 'EDIT_MESH' and op.mode not in {'MAKE', 'EXTRACT'}:
                        for obj in op.datablock['targets']:
                            for mod in obj.modifiers[:]:
                                if op.mode == 'INSET' and mod.type == 'BOOLEAN' and mod.object == bc.shape and (not hasattr(mod, 'operand_type') or mod.operand_type != 'COLLECTION'):
                                    obj.modifiers.remove(mod)

                        for obj in op.datablock['targets']:
                            # modifier.apply(obj, mod=modifier.shape_bool(obj))

                            if op.mode == 'INSET':

                                for mod in obj.modifiers[:]:
                                    if mod.type == 'BOOLEAN' and mod.object in op.datablock['insets']:
                                        modifier.apply(obj, mod=mod)

                            else:
                                modifier.apply(obj, mod=modifier.shape_bool(obj))

                        for obj in op.datablock['slices']:
                            modifier.apply(obj, mod=modifier.shape_bool(obj))
                            obj.select_set(True)

                        for obj in op.datablock['insets']:
                            bpy.data.objects.remove(obj)

                        op.datablock['insets'].clear()

                    elif op.mode == 'SLICE' and preference.behavior.apply_slices and op.original_mode != 'EDIT_MESH':

                        for obj in op.datablock['slices']:

                            bvls = [mod for mod in obj.modifiers if mod.type == 'BEVEL'][-1:]
                            wns = [mod for mod in obj.modifiers if mod.type == 'WEIGHTED_NORMAL']
                            ignore = bvls + wns

                            modifier.apply(obj, ignore=ignore)
                            obj.select_set(True)

                            bvl = [mod for mod in obj.modifiers if mod.type == 'BEVEL'][-1:]
                            wn = [mod for mod in obj.modifiers if mod.type == 'WEIGHTED_NORMAL'][-1:]

                            if bvl and True not in [d < 0.0001 for d in obj.dimensions]:
                                if bpy.app.version[:2] < (2, 90):
                                    bvl[0].use_only_vertices = False
                                else:
                                    bvl[0].affect = 'EDGES'

                            for mod in obj.modifiers[:]:
                                if (not bvl or mod != bvl[0]) and (not wn or mod != wn[0]):
                                    obj.modifiers.remove(mod)

                    elif op.mode == 'SLICE':
                        for obj in op.datablock['slices']:
                            obj.select_set(True)

                    if op.original_mode == 'EDIT_MESH':
                        if bpy.app.version[:2] < (2, 91) or op.behavior == 'DESTRUCTIVE':
                            for obj in op.datablock['targets']:
                                for mod in obj.modifiers[:]:
                                    if mod.type == 'BOOLEAN':
                                        if mod.object == bc.shape or mod.object in op.datablock['insets'] and (not hasattr(mod, 'operand_type') or mod.operand_type != 'COLLECTION'):
                                            obj.modifiers.remove(mod)

                            bpy.ops.object.mode_set(mode='EDIT')

            if op.mode == 'INSET':
                for obj in op.datablock['targets'] + op.datablock['slices']:
                    for mod in obj.modifiers[:]:
                        if mod.type == 'BOOLEAN' and (mod.object == bc.shape or not mod.object) and (not hasattr(mod, 'operand_type') or mod.operand_type != 'COLLECTION'):
                            obj.modifiers.remove(mod)

            if hasattr(bc.shape, 'hops'):
                bc.shape.hops.status = 'BOOLSHAPE' if op.mode != 'MAKE' else 'UNDEFINED'

            clean_welds = True
            if op.shape_type == 'CUSTOM' or bc.shape.data.bc.q_beveled:
                clean_welds = False
            # if op.shape_type == 'NGON' or op.ngon_fit:
            #     clean_welds = False
            for mod in bc.shape.modifiers[:]:
                mod.show_render = True

                if mod.type in {'ARRAY', 'BEVEL'}:
                    clean_welds = False

                if mod.name.startswith('Bevel'):
                    if preference.shape.quad_bevel and op.shape_type == 'CIRCLE':
                       if  (preference.shape.circle_type == 'POLYGON' and preference.shape.circle_vertices > 12 and not preference.shape.bevel_both) or preference.shape.circle_type == 'MODIFIER':
                            bc.shape.modifiers.remove(mod)

            if clean_welds and not op.repeat and not op.reverse_bevel:
                for mod in bc.shape.modifiers[:]:
                    if mod.type == 'WELD':
                        bc.shape.modifiers.remove(mod)

        else:

            if not op.live:
                op.extruded = True
                mesh.knife(op, context, None)

            bpy.data.objects.remove(bc.shape)
            bc.shape = None

            context.view_layer.objects.active = bc.original_active
            bc.original_active.select_set(True)

            for obj in op.original_selected:
                obj.select_set(True)

            if op.original_mode == 'EDIT_MESH':
                bpy.ops.object.mode_set(mode='EDIT')

        if not preference.behavior.keep_lattice and not (preference.behavior.keep_lattice_taper and preference.shape.taper != 1):
            bpy.data.objects.remove(bc.lattice)

        else:
            bc.lattice.data.bc.removeable = False
            bc.lattice.hide_set(not op.show_shape)

        bpy.data.objects.remove(op.datablock['plane'])

        rem_meshes = [me for me in bpy.data.meshes[:] if me.bc.removeable or me.bc.eval_remove]
        for me in rem_meshes[:]:
            bpy.data.meshes.remove(me)

        for lat in bpy.data.lattices[:]:
            if lat.bc.removeable:
                bpy.data.lattices.remove(lat)

        array = None

        if bc.shape:
            bc.shape.data.name = bc.shape.name

            for mod in bc.shape.modifiers:
                if mod.type == 'ARRAY':
                    array = mod

                    break

            if array and array.use_object_offset:

                bc.empty.driver_remove('rotation_euler', 2)
                driver = bc.empty.driver_add('rotation_euler', 2).driver
                driver.type == 'SCRIPTED'

                count = driver.variables.new()
                count.name = 'count'
                count.targets[0].id_type = 'OBJECT'
                count.targets[0].id = bc.shape
                count.targets[0].data_path = F'modifiers["{array.name}"].count'

                driver.expression = 'radians(360 / count)'

            else:
                bpy.data.objects.remove(bc.empty)
                bc.empty = None

        else:
            bpy.data.objects.remove(bc.empty)
            bc.empty = None

    else:
        if bc.original_active:
            bpy.ops.object.mode_set(mode='OBJECT')
            try:
                context.view_layer.objects.active = bc.original_active
                bc.original_active.select_set(True)

                if op.cancelled:
                    if op.datablock['overrides']:
                        for pair in zip(op.datablock['targets'], op.datablock['overrides']):
                            obj = pair[0]
                            override = pair[1]

                            name = obj.data.name
                            obj.data.name = 'tmp'

                            obj.data = override
                            obj.data.name = name

                            for mod in obj.modifiers:
                                mod.show_viewport = True

                        op.datablock['overrides'] = list()
            except:
                traceback.print_exc()

        for obj in bc.shape.children:
            if obj.data:
                obj.data.bc.removeable = True

            bpy.data.objects.remove(obj)

        bpy.data.objects.remove(bc.shape)
        bpy.data.objects.remove(bc.lattice)

        if bc.empty:
            bpy.data.objects.remove(bc.empty)
            bc.empty = None

        for obj in op.datablock['targets']:
            for mod in obj.modifiers[:]:
                if mod.type == 'BOOLEAN' and not mod.object and (not hasattr(mod, 'operand_type') or mod.operand_type != 'COLLECTION'):
                    obj.modifiers.remove(mod)

        for obj in op.datablock['slices']:
            bpy.data.objects.remove(obj)

        op.datablock['slices'].clear()

        for obj in op.datablock['insets']:
            bpy.data.objects.remove(obj)

        op.datablock['insets'].clear()

        if op.original_mode == 'EDIT_MESH':
            bpy.ops.object.mode_set(mode='EDIT')

    if bc.shape and op.original_mode == 'EDIT_MESH' and not op.show_shape and op.mode != 'MAKE':
        if bpy.app.version[:2] < (2, 91) or op.behavior == 'DESTRUCTIVE':

            bc.shape.data.bc.removeable = True
            bpy.data.objects.remove(bc.shape)

    rem_meshes = [me for me in bpy.data.meshes if me.bc.removeable]
    for me in rem_meshes:
        bpy.data.meshes.remove(me)

    for lat in bpy.data.lattices[:]:
        if lat.bc.removeable:
            bpy.data.lattices.remove(lat)

    bc.lattice = None

    for obj in op.datablock['targets']:
        for mod in obj.modifiers[:]:
            if mod.type == 'BOOLEAN':
                if not mod.object and (not hasattr(mod, 'operand_type') or mod.operand_type != 'COLLECTION') or (mod.object == bc.shape and op.mode == 'MAKE'):
                    obj.modifiers.remove(mod)

    applied_cutters = [obj for obj in bpy.data.objects if obj.bc.shape and obj.bc.applied_cycle ]

    for obj in applied_cutters:
        bpy.data.objects.remove(obj)

    if op.original_mode == 'EDIT_MESH':
            bpy.ops.object.mode_set(mode='OBJECT')

    mesh.pivot(op, context)

    if op.original_mode == 'EDIT_MESH':
            bpy.ops.object.mode_set(mode='EDIT')

    if not clean_all and bc.original_active and preference.behavior.parent_shape and op.mode not in {'KNIFE', 'EXTRACT'}:
        if bc.shape:
            bc.shape.matrix_world.translation = bc.shape.location
            object.parent(bc.shape, bc.original_active)

        for target, slice in zip(op.datablock['targets'], op.datablock['slices']):
            object.parent(slice, target)

        for target, slice in zip(op.datablock['targets'], op.datablock['insets']):
            object.parent(slice, target)

    bc.plane = None
    bc.slice = None
    bc.inset = None

    if bc.bevel and clean_all:
        for obj in op.datablock['targets']:
            for i, mod in enumerate(obj.modifiers):
                if mod.type != 'BOOLEAN' or mod.object != bc.bevel:
                    continue

                obj.modifiers.remove(obj.modifiers[i + 1])
                break

        bpy.data.objects.remove(bc.bevel)

    bc.bevel = None

    bc.location = Vector()

    # bc.snap.display = True

    if preference.surface != op.last['surface'] and op.last['surface'] != 'WORLD':
        preference.surface = op.last['surface']
    # else: # TODO: Add pref for return to object
        # preference.surface = 'OBJECT'

    if op.behavior == 'DESTRUCTIVE' and op.mode != 'MAKE' and bc.shape and not op.show_shape:
        bpy.data.meshes.remove(bc.shape.data)

    if bc.collection and not bc.collection.objects:
        bpy.data.collections.remove(bc.collection)

    if type_to_custom:
        toolbar.change_prop(context, 'shape_type', 'CUSTOM')

    if op.mode != 'KNIFE':
        toolbar.change_prop(context, 'mode', op.last['start_mode'] if not type_to_custom else 'CUT')
    # elif preference.behavior.hops_mark:
    #     preference.behavior.hops_mark = False

    preference.behavior.recut = False
    preference.behavior.inset_slice = False

    toolbar.change_prop(context, 'operation', op.last['start_operation'])

    if not type_to_custom:
        toolbar.change_prop(context, 'shape_type', op.last['shape_type'])

    preference.behavior['draw_line'] = op.last['draw_line']
    preference.shape['lasso'] = op.last['lasso']

    if preference.shape.auto_depth:
        preference.keymap['release_lock'] = op.start['release_lock']
        preference.keymap.release_lock_lazorcut = op.start['release_lock_lazorcut']
        preference.keymap.quick_execute = op.start['quick_execute']
        preference.shape.lazorcut_depth = op.start['lazorcut_depth']

    preference.behavior.accucut = op.start['accucut']

    preference.shape.circle_diameter = 0.0001
    preference.shape.dimension_x = 0.0001
    preference.shape.dimension_y = 0.0001
    preference.shape.dimension_z = 0.0001

    if not preference.behavior.persistent_taper:
        preference.shape['taper'] = 1.0

    if not op.datablock['targets'] and op.mode == 'MAKE' and not op.show_shape:
        if bc.shape:
            bc.shape.select_set(False)
        context.view_layer.objects.active = None

    # for obj in op.datablock['targets']:
    #     for mod in obj.modifiers:
    #         if mod.type == 'MIRROR' and (op.mode == 'KNIFE' or op.original_mode == 'EDIT_MESH'):
    #             mod.show_viewport = True

    if clean_all:
        context.view_layer.objects.active = bc.original_active

        for obj in op.datablock['targets']:
            obj.select_set(True)

        if op.original_mode == 'EDIT_MESH':
            bpy.ops.object.mode_set(mode='EDIT')

        if bc.shape and op.shape_type != 'CUSTOM':
            bpy.data.objects.remove(bc.shape)

        if bc.lattice:
            bpy.data.objects.remove(bc.lattice)

        for obj in op.datablock['slices']:
            bpy.data.objects.remove(obj)

        op.datablock['slices'].clear()

        for obj in op.datablock['insets']:
            bpy.data.objects.remove(obj)

        op.datablock['insets'].clear()

        if op.ngon_point_bevel_reset:
            op.last['modifier']['bevel_width'] = op.ngon_point_bevel_reset
            op.last['modifier']['quad_bevel_width'] = op.ngon_point_bevel_reset
            op.last['modifier']['front_bevel_width'] = op.ngon_point_bevel_reset

        for obj in op.datablock['targets']:
            for mod in reversed(obj.modifiers):
                if mod.type != 'BOOLEAN':
                    continue

                if not mod.object:
                    obj.modifiers.remove(mod)
                    break

        if bc.collection and not bc.collection.objects:
            bpy.data.collections.remove(bc.collection)
            bc.collection = None

    op.datablock['targets'] = []
    op.datablock['slices'] = []
    op.datablock['insets'] = []

    op.view3d['location'] = Vector((0, 0, 0))

    op.alt_extrude = True

    if not op.start['inset_bevel']:
        preference.behavior.inset_bevel = False

    del op.tool
    bc.original_active = None
    op.original_selected = []
    op.original_visible = []
    op.material = ''
    del op.datablock
    del op.last
    del op.ray
    del op.start
    del op.geo
    del op.mouse
    del op.view3d
    del op.existing

    bc.shape = None if not bc.stored_shape else bc.stored_shape

    # if op.shape_type != 'BOX':
    #     preference.shape.wedge = False

    custom.clear_sum()

    # if bc.original_active and not op.show_shape:
    #     bc.original_active.select_set(True)

    # if op.snap:
    #     op.snap = False

    #     if bc.snap.operator:
    #         bc.snap.operator.should_run = False

    #     bpy.ops.bc.shape_snap('INVOKE_DEFAULT')

    orphans = [ob for ob in bpy.data.objects if not ob.users]
    for ob in orphans:
        bpy.data.objects.remove(ob)

    orphans = [me for me in bpy.data.meshes if not me.users]
    for me in orphans:
        bpy.data.meshes.remove(me)
