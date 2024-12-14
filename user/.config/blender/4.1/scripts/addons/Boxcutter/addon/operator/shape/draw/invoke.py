import bpy
import bmesh

from mathutils import Vector, Matrix

from ..... utility import addon, tool, ray, view3d, context_copy, math, object, collection
from .... import toolbar
from ... shape.utility.change import last
from ... shape.utility import modifier
# from ... utility import shape #, lattice, mesh
from .. import utility
# from .. utility import statusbar
# from .. utility import shader
# from .. draw import new
from .. utility import tracked_states
from .... property import new
from .. utility import statusbar
from .....addon.property.scene import option as bc_scene_type


def operator(op, context, event):
    preference = addon.preference()
    bc = context.scene.bc

    op.original_mode = tool.active().mode

    if op.original_mode == 'EDIT_MESH' and preference.keymap.allow_selection and preference.keymap.edit_disable_modifiers:
        if not bc.snap.hit:
            if event.ctrl or (event.ctrl and event.shift):
                return {'PASS_THROUGH'}

    if preference.keymap.enable_toolsettings:
        context.space_data.show_region_tool_header = True
        context.space_data.show_region_header = True

    bc.running = True
    bc_scene_type.operator = op

    op.cancelled = False

    # TODO: move to addon.operator.draw.utility.collection.find()
    #       add collection data property group; add type stringprop

    if bc.collection and bc.collection not in context.scene.collection.children_recursive[:]:
        bc.collection = None

    if not bc.collection:

        for col in bpy.data.collections:
            # if collection.child_of(col.name):

            #     for obj in col.objects:
            #         if obj.bc.shape:
            #             bc.collection = col
            #             break

            if not col.hopscutter:
                continue

            bc.collection = col

            break

    name = bc.collection.name.split('.')[0] if bc.collection else 'Cutters'
    if not bc.collection and addon.hops():
        name = context.scene.hops.collection.name if context.scene.hops.collection else 'Cutters'

    bc.collection = collection.get(name, collection.new(name, color=preference.color.collection))
    bc.collection.hide_render = True

    count = len([c for c in bpy.data.collections if name in c.name])

    prev_count = str(count - 1)
    prev_name = F'{name}.{prev_count.zfill(3)}'

    if collection.child_of(prev_name):
        bc.collection = collection.get(prev_name)

    elif count >= 1 and not collection.child_of(name):
        count_string = str(count)
        counted_name = F'{name}.{count_string.zfill(3)}'

        bc.collection = collection.new(counted_name, color=preference.color.collection, hopscutter=True)
        bc.collection.hide_render = True
    ##

    collection.view_layer_unhide(bc.collection)

    if op.shape_type != 'CUSTOM':
        bc.shape = None

    elif not bc.shape:
        dat = bpy.data.meshes.new(name='Cutter')

        dat.from_pydata(new.logo_verts, new.logo_edges, new.logo_faces, shade_flat=True)
        dat.validate()

        bc.shape = bpy.data.objects.new(name='Cutter', object_data=dat)
        del dat

        bc.shape.display_type = 'WIRE' if op.mode != 'MAKE' else 'TEXTURED'
        bc.shape.bc.shape = True

        bc.collection.objects.link(bc.shape)

        if addon.preference().behavior.auto_smooth:
            if bpy.app.version < (4, 1):
                bc.shape.data.use_auto_smooth =  True

            for face in bc.shape.data.polygons:
                face.use_smooth = True

        bc.shape.hide_set(True)

    if bc.shape:
        collected = False
        for col in bpy.data.collections:
            if bc.shape.name in col.objects:
                collected = True
                bc.collection = col

                break

        if not collected:
            if 'Cutters' not in bpy.data.collections:
                bc.collection = bpy.data.collections.new(name='Cutters')

            else:
                bc.collection = bpy.data.collections['Cutters']

            bc.collection.objects.link(bc.shape)

    if preference.shape.auto_depth:
        op.start['release_lock'] = preference.keymap.release_lock
        op.start['release_lock_lazorcut'] = preference.keymap.release_lock_lazorcut
        op.start['quick_execute'] = preference.keymap.release_lock_lazorcut
        op.start['lazorcut_depth'] = preference.shape.lazorcut_depth

        preference.keymap['release_lock'] = True
        preference.keymap.release_lock_lazorcut = True
        preference.keymap.quick_execute = True
        op.extruded = op.shape_type != 'NGON'

    op.alt_toggle_extrude = False

    op.start['accucut'] = preference.behavior.accucut

    op.alt_skip = True
    op.alt_e = False
    op.alt = event.alt
    op.ctrl = event.ctrl
    op.shift = event.shift
    op.lmb = True
    op.mmb = False
    op.rmb = False
    op.alt_lock = False
    op.click_count = 0
    op.add_point_lock = False
    op.modified = False
    op.datablock = new.datablock.copy()
    op.last = last
    op.last['vert_weight'] = []
    op.last['edge_weight'] = []
    op.ray = new.ray_cast.copy()
    op.start = new.start.copy()
    op.start['extrude'] = 0.0
    op.geo = new.geo.copy()
    op.geo['indices']['extrusion'] = []
    op.geo['indices']['offset'] = []
    op.mouse = new.mouse.copy()
    op.rotated = False
    op.scaled = False
    op.view3d = new.view3d.copy()
    op.segment_state = False
    op.width_state = False
    op.wires_displayed = False
    op.orthographic = False
    op.auto_ortho = False
    op.existing = {}
    op.release_lock = preference.keymap.release_lock
    op.move_lock = False
    op.lazorcut_performed = False
    op.plane_checks = 0
    op.ngon_fit = False
    op.ngon_point_index = -1
    op.ngon_point_bevel = False
    op.ngon_point_bevel_reset = 0.0
    op.draw_line = preference.behavior.draw_line and op.shape_type !='NGON'
    op.wedge_cycle = 0
    op.bounds = [Vector((0, 0, 0)) for _ in range(8)]
    op.repeat_check = preference.keymap.repeat_single_click
    op.wedge_check = preference.shape.wedge
    op.repeat = False
    op.snap_lock_type = ''
    op.reverse_bevel = False
    op.alt_extrude = True
    op.custom_orient = False
    op.inverted_extrude = False
    op.clamp_extrude = True
    op.flip_x = False
    op.flip_y = False
    op.flipped_normals = False
    op.proportional_draw = False
    op.start_exact = preference.behavior.boolean_solver == 'EXACT'
    op.start_exact_join = op.mode == 'JOIN' and preference.behavior.join_exact
    op.custom_offset = False

    op.init_mouse = Vector((event.mouse_region_x, event.mouse_region_y))
    op.mouse['location'] = op.init_mouse
    op.mouse['offset'] = Vector((0, 0))
    op.start['mouse'] = op.init_mouse
    op.last['mouse'] = op.init_mouse
    op.last['draw_delta'] = Vector((0, 0, 0))
    op.last['depth'] = 0.0
    op.datablock['targets'] = [obj for obj in context.selected_objects if obj.type == 'MESH']
    op.datablock['slices'] = []
    op.datablock['insets'] = []
    op.datablock['wire_targets'] = [obj for obj in op.datablock['targets'] if obj.show_wire]
    op.datablock['bounds'] = []
    op.datablock['dimensions'] = Vector((1, 1, 1))
    op.datablock['shape_proportions'] = Vector((1, 1, 1))
    op.last['taper'] = preference.shape.taper
    op.lasso_view_factor = 0
    op.last['line'] = 0.0
    op.start['view_rotation'] = context.region_data.view_rotation.to_matrix().to_4x4()
    op.start['view_matrix'] = context.region_data.view_matrix.copy()
    op.start['intersect'] = Vector()
    op.start['inset_bevel'] = preference.behavior.inset_bevel
    op.inset_skip_move_bevel = False
    op.last['wedge_axis_map'] = {False : 'X', True : 'Y'}
    op.last['wedge_points'] = [0, 1]
    op.input_plane = Vector()
    op.mirror_gizmo_higlight = False
    op.element_snap_vec = None

    tracked_states.make_fallback = not bool(op.datablock['targets'])

    preference.shape['mirror_gizmo'] = False

    if preference.behavior.show_wire:
        for obj in op.datablock['targets']:
            if obj not in op.datablock['wire_targets']:
                obj.show_wire = True
                obj.show_all_edges = True

    if not op.datablock['targets'] and op.original_mode != 'EDIT_MESH':
        context.view_layer.objects.active = None

    elif op.original_mode == 'EDIT_MESH':
        context.active_object.select_set(True)
        if context.active_object not in op.datablock['targets']:
            op.datablock['targets'].append(context.active_object)

    for lat in bpy.data.lattices:
            lat.bc.removeable = False

    for obj in op.datablock['targets']:
        if bpy.app.version[:2] < (3, 4):
            obj.data.use_customdata_vertex_bevel = True
            obj.data.use_customdata_edge_bevel = True
            obj.data.use_customdata_edge_crease = True

        op.existing[obj] = {}
        op.existing[obj]['materials'] = [slot.material for slot in obj.material_slots if slot.material]

    op.snap = preference.snap.enable and event.ctrl

    bc.original_active = None

    if not context.active_object and op.datablock['targets']:
        context.view_layer.objects.active = op.datablock['targets'][0]

    op.original_selected = context.selected_objects[:]
    op.original_visible = context.visible_objects[:]

    for obj in op.datablock['targets']:
        if obj == context.active_object:
            bc.original_active = obj

        if preference.behavior.apply_scale:
            for axis in obj.scale:
                if axis != 1.0:
                    matrix = Matrix()
                    matrix[0][0] = obj.scale[0]
                    matrix[1][1] = obj.scale[1]
                    matrix[2][2] = obj.scale[2]

                    if context.mode == 'EDIT_MESH':
                        bm = bmesh.from_edit_mesh(obj.data)

                        bmesh.ops.transform(bm, verts=bm.verts, matrix=matrix)
                        bmesh.update_edit_mesh(obj.data)
                        obj.update_from_editmode()

                    else:
                        obj.data.transform(matrix)

                    for child in obj.children:
                        child.matrix_local = matrix @ child.matrix_local

                    obj.scale = Vector((1.0, 1.0, 1.0))

                    break
        # del obj

    if op.datablock['targets']:
        selection_bounds=[]
        for obj in op.datablock['targets']:
            selection_bounds.extend(object.bound_coordinates(obj))

        op.datablock['bounds'] = math.coordinate_bounds(selection_bounds)
        op.datablock['dimensions'] = math.coordinates_dimension(op.datablock['bounds'])

        del selection_bounds

    updated = toolbar.update_operator(op, context)
    if not updated:
        bc.running = False
        return {'PASS_THROUGH'}

    op.last['start_mode'] = op.mode
    op.last['mode_set'] = op.mode
    op.last['start_operation'] = op.operation
    op.last['shape_type'] = op.shape_type
    op.last['draw_line'] = preference.behavior.draw_line
    op.last['lasso'] = preference.shape.lasso

    # if op.shape_type == 'BOX' and preference.behavior.draw_line:
        # op.shape_type = 'NGON'
        # preference.shape.lasso = False

    # elif op.shape_type == 'NGON' and preference.behavior.draw_line:
        # preference.behavior.draw_line = False

    if not op.datablock['targets'] and preference.surface == 'OBJECT':
        op.last['surface'] = preference.surface
        bc.last.surface = preference.surface
        preference.surface = 'WORLD'

    else:
        op.last['surface'] = preference.surface
        bc.last.surface = preference.surface

    if op.draw_line and op.shape_type != 'NGON':
        op.origin = 'CORNER'
        toolbar.change_prop(context, 'origin', 'CORNER')

    if preference.behavior.auto_smooth and op.mode not in {'KNIFE', 'MAKE', 'EXTRACT'}:
        for obj in op.datablock['targets']:

            if not obj.data.use_auto_smooth:
                for face in obj.data.polygons:
                    face.use_smooth = True

                obj.data.update()

            obj.data.use_auto_smooth = True

    objects = bc.collection.objects[:]

    for obj in objects:
        active = bc.original_active and obj == bc.original_active
        selected = obj in op.original_selected[:]
        visible = obj in op.original_visible[:]
        hide = preference.behavior.autohide_shapes and not active and not selected

        if (not active and (not selected and not visible or hide) and obj.display_type in {'WIRE', 'BOUNDS'}) and not obj.hide_get():
            obj.hide_set(True)
        elif not obj.hide_get():
            obj.hide_set(False)

    del objects

    if bc.original_active and bc.original_active.select_get():
        bpy.context.view_layer.objects.active = bc.original_active

    for obj in op.original_selected:
        obj.select_set(True)

    if op.mode == 'KNIFE' and not preference.behavior.show_wire:
        op.datablock['wireframes'] = [(obj.show_wire, obj.show_all_edges) for obj in op.datablock['targets']]
        op.wires_displayed = True
        for obj in op.datablock['targets']:
                obj.show_wire = True
                obj.show_all_edges = True

    # XXX: edit mode can lose active object info on undo
    if op.original_mode == 'EDIT_MESH':
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.mode_set(mode='EDIT')

    utility.data.create(op, context, event, custom_cutter=bc.shape)

    if op.operation == 'SOLIDIFY':
        bc.shape.bc.solidify = True
        utility.modal.solidify.shape(op, context, event)

    elif op.operation == 'ARRAY':
        bc.shape.bc.array = True

        if bc.axis == 'NONE':
            utility.modal.axis.change(op, context, to='X')

        utility.modal.array.shape(op, context, event)

    elif op.operation == 'BEVEL' and op.shape_type != 'NGON' and not op.ngon_fit:
        bc.shape.data.bc.q_beveled = bc.q_bevel

        utility.modal.bevel.shape(op, context, event)

    utility.modal.operation.change(op, context, event, to='DRAW', modified=False, init=True)

    bc.lattice.hide_set(True)
    bc.shape.hide_set(True)
    bc.empty.hide_set(True)

    op.report({'INFO'}, 'Drawing')

    # op.shader = shader.shape.setup(op)
    # op.widgets = shader.widgets.setup(op)
    statusbar.add()
    op.mode = op.mode # trigger update method

    if not op.start_exact and op.mode == 'JOIN' and preference.behavior.join_exact:
        preference.behavior.boolean_solver = 'EXACT'

    # if not preference.display.dots:
    #     op.widgets.exit = True

    # if not context.space_data.region_3d.is_perspective:
    #     op.orthographic = True
    #     bpy.ops.view3d.view_persportho('INVOKE_DEFAULT')

    hops = getattr(context.window_manager, 'Hard_Ops_material_options', False)

    if hops:
        if hops.material_mode == "BLANK":
            bpy.types.HOPS_PT_material_hops.blank_cut()

        if op.mode == 'MAKE' and hops.active_material:
            bc.shape.data.materials.append(bpy.data.materials[hops.active_material])

    op.show_region_toolbar = context.space_data.show_region_toolbar
    op.show_region_ui = context.space_data.show_region_ui

    hops_pref = addon.hops()

    if hops_pref:
        if hops_pref.ui.Hops_auto_hide_t_panel:
            context.space_data.show_region_toolbar = False

        if hops_pref.ui.Hops_auto_hide_n_panel:
            context.space_data.show_region_ui = False

    if op.mode == 'MAKE' or tracked_states.make_fallback:
        preference.behavior.hide_make_shapes = preference.behavior.hide_make_shapes

    if preference.surface == 'OBJECT' and bc.snap_type != 'VIEW' and (not preference.behavior.ortho_view_align or context.space_data.region_3d.is_perspective):
        hit, op.ray['location'], op.ray['normal'], op.ray['index'], op.ray['object'], *_ = ray.cast(*op.mouse['location'], selected=True)

        if hit or bc.snap.hit:
            utility.modal.ray.surface(op, context, event)

            if op.last['start_operation'] == 'MIRROR':
                utility.modal.mirror.shape(op, context, event, init=True)

            if bc.rotated_inside and preference.shape.rotation_by_90:
                utility.modal.rotate.by_90(op, context, event, init=True)

            # if op.repeat:
            #     op.execute(context)
            #     op.update()
            #     return {'FINISHED'}

            op.start['alignment'] = 'OBJECT'
            utility.modal.mode.change(op, context, event, to=op.mode, init=True)

            # if op.orthographic:
            #     bpy.ops.view3d.view_persportho('INVOKE_DEFAULT')

            context.window_manager.modal_handler_add(op)
            op.update()

            bpy.ops.bc.shader('INVOKE_DEFAULT')

            return {'RUNNING_MODAL'}

    if preference.surface in {'OBJECT', 'VIEW'} or bc.snap_type == 'VIEW':
        op.start['alignment'] = preference.surface
        preference.surface = 'VIEW'
        utility.modal.ray.screen(op, context, event)

        if op.last['start_operation'] == 'MIRROR':
            utility.modal.mirror.shape(op, context, event, init=True)

        if bc.rotated_inside and preference.shape.rotation_by_90:
            utility.modal.rotate.by_90(op, context, event, init=True)

        # if op.repeat:
        #     op.execute(context)
        #     op.update()
        #     return {'PASS_THROUGH'}

        utility.modal.mode.change(op, context, event, to=op.mode if op.datablock['targets'] else 'MAKE', init=True)

        # if op.orthographic:
        #     bpy.ops.view3d.view_persportho('INVOKE_DEFAULT')

        if preference.behavior.auto_ortho and context.space_data.region_3d.is_perspective:
            op.auto_ortho = True
            bpy.ops.view3d.view_persportho('INVOKE_DEFAULT')

        context.window_manager.modal_handler_add(op)
        op.update()

        bpy.ops.bc.shader('INVOKE_DEFAULT')

        return {'RUNNING_MODAL'}

    else:
        utility.modal.ray.custom(op, context, event)

        if op.plane_checks > 3:
            op.cancel(context)
            op.update()
            op.report({'WARNING'}, 'No coordinates for placing the shape were found')
            return {'PASS_THROUGH'}

        if op.last['start_operation'] == 'MIRROR':
            utility.modal.mirror.shape(op, context, event, init=True)

        if bc.rotated_inside and preference.shape.rotation_by_90:
            utility.modal.rotate.by_90(op, context, event, init=True)

        # if op.repeat:
        #     op.execute(context)
        #     op.update()
        #     return {'FINISHED'}

        op.start['alignment'] = preference.surface

        if op.datablock['targets']:
            mode = op.mode
        else:
            mode = 'MAKE'
            bc.shape.display_type = 'TEXTURED'

        utility.modal.mode.change(op, context, event, to=mode, init=True)

        # if op.orthographic:
        #     bpy.ops.view3d.view_persportho('INVOKE_DEFAULT')

        if preference.behavior.auto_ortho and context.space_data.region_3d.is_perspective:
            op.auto_ortho = True
            bpy.ops.view3d.view_persportho('INVOKE_DEFAULT')

        context.window_manager.modal_handler_add(op)
        op.update()

        bpy.ops.bc.shader('INVOKE_DEFAULT')

        return {'RUNNING_MODAL'}

    bc.running = False

    op.update()
    return {'PASS_THROUGH'}
