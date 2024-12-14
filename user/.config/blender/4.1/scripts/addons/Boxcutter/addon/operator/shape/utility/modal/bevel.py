import bpy

from math import radians
from mathutils import Vector

from .. import mesh
from ...... utility import addon, screen, modifier

rounded = lambda n: round(n, 8)

# XXX: bevel before array
def shape(op, context, event):
    from .. import dimensions

    preference = addon.preference()
    bc = context.scene.bc

    if bc.shape.data.bc.inset_bevel:
        segment_state = False
        update = True

        mod = None
        for m in bc.bevel.modifiers:
            if m.type == 'BEVEL':
                mod = m
                break

        # snap = preference.snap.enable and preference.snap.incremental

        # max_dimension = max(bc.lattice.dimensions[:-1])
        max_dimension = max(dimensions()[:-1])
        clamped = False
        clamp_offset = clamp(op)

        width_input = ((op.mouse['location'].x - op.last['mouse'].x) / screen.dpi_factor(ui_scale=False, integer=True)) * max_dimension
        factor = 0.0001 / max_dimension if event and event.shift else 0.001 / max_dimension

        _input = lambda n: rounded(n + width_input * factor)
        last = op.last['thickness']
        width = (_input(last) if last < clamp_offset else _input(clamp_offset))

        if width < 0.0004:
            width = 0.0004

        if width >= clamp_offset:
            clamped = True
            width = clamp_offset
            update = False

        # if snap and event and event.ctrl:
        #     width = round(width, 2 if event and event.shift else 1) # and op.prior_to_shift == 'NONE' else 1)

        if not clamped:
            if width < 0.001 and not op.width_state or segment_state:
                segment_state = True
                op.width_state = True

                if mod.segments == 1 and op.segment_state:
                    mod.segments = preference.shape.bevel_segments if preference.shape.bevel_segments != 1 else preference.shape.bevel_segments_default

                else:
                    op.segment_state = True
                    mod.segments = 1

            elif width > 0.0011 and op.width_state:
                op.width_state = False

        # if update:
        #     op.last['thickness'] = width
        #     preference.shape[width_type] = width

        # mod.width = width
        preference.shape.inset_thickness = width

        op.last['mouse'] = op.mouse['location']
        return

    # TODO: lasso bevel support
    if (op.shape_type == 'NGON' or op.ngon_fit) and preference.shape.lasso:
        return

    ngon = op.shape_type == 'NGON' or op.ngon_fit
    boxgon = op.shape_type == 'BOX' and not op.ngon_fit and (op.ngon_point_index != -1 or op.ngon_point_bevel)

    snap = preference.snap.enable and preference.snap.incremental

    straight_edge = preference.shape.straight_edges or bc.q_back_only

    # max_dimension = max(bc.lattice.dimensions[:-1])
    max_dimension = max(dimensions()[:-1])
    clamped = False

    clamp_offset = clamp(op)

    width_input = ((op.mouse['location'].x - op.last['mouse'].x) / screen.dpi_factor(ui_scale=False, integer=True)) * max_dimension
    factor = 0.0001 if event and event.shift and op.prior_to_shift == 'NONE' else 0.001

    if op.shape_type == 'CIRCLE' and preference.shape.circle_type == 'POLYGON' and preference.shape.circle_vertices > 12:
        bc['q_bevel'] = bc.shape.data.bc.q_beveled = True
        bc.q_back_only = False
        op.geo['indices']['mid_edge'] = []

    if preference.shape.quad_bevel:
        if not straight_edge or op.shape_type == 'CIRCLE' or bc.q_back_only:
            mesh.bevel_weight(op, context, event)

        else:
            mesh.vertex_group(op, context, event)
    else:
        mesh.bevel_weight(op, context, event)

    m = None
    for mod in bc.shape.modifiers:
        if mod.type == 'BEVEL':
            m = mod
            break

    if not m:
        for mod in modifier.collect(bc.shape, types={'WELD', 'VERTEX_WEIGHT_EDIT', 'VERTEX_WEIGHT_MIX'}):
            bc.shape.modifiers.remove(mod)

        vertex_only = ngon and not op.extruded
        quad_bevel = not preference.shape.quad_bevel or (preference.shape.quad_bevel and not straight_edge)

        if vertex_only:
            mod = bc.shape.modifiers.new(name='Bevel', type='BEVEL')
            mod.show_render = False
            mod.show_expanded = False

            if bpy.app.version[:2] < (2, 90):
                mod.use_only_vertices = True

            else:
                mod.affect = 'VERTICES'

            mod.width = op.last['modifier']['bevel_width'] if not ngon and not boxgon else clamp_offset
            mod.segments = preference.shape.bevel_segments
            mod.limit_method = 'WEIGHT'
            mod.offset_type = 'OFFSET'

            if bpy.app.version[:2] < (3, 4):
                bc.shape.data.use_customdata_vertex_bevel = True

            for v in bc.shape.data.vertices:
                value = mesh.index_weight(v.index, vert=True)
                mesh.index_weight(v.index, vert=True, value=value if op.ngon_point_bevel else 1)

            mod = bc.shape.modifiers.new(name='Bevel Weld', type='WELD')
            mod.show_render = False
            mod.show_expanded = False
            # mod.merge_threshold = max(bc.lattice.dimensions) * 0.001
            mod.merge_threshold = max(dimensions()) * 0.001

            modifier.sort(bc.shape, types=['LATTICE', 'BEVEL'], first=True, typed_order=True)

        elif quad_bevel or (op.shape_type == 'CIRCLE' and preference.shape.circle_type == 'MODIFIER'):
            mod = bc.shape.modifiers.new(name='Bevel', type='BEVEL')

            mod.show_render = False
            mod.show_expanded = False

            mod.width = op.last['modifier']['bevel_width'] if not ngon and not boxgon else clamp_offset

            mod.segments = preference.shape.bevel_segments
            mod.limit_method = 'WEIGHT'
            mod.offset_type = 'OFFSET'

            # if op.mode in {'MAKE', 'JOIN'} and (op.shape_type == 'BOX' and not op.ngon_fit):
            #     mesh.mesh.recalc_normals(bc.shape, face=True, index=4, inside=True)

            mod = bc.shape.modifiers.new(name='Bevel Weld', type='WELD')
            mod.show_render = False
            mod.show_expanded = False
            # mod.merge_threshold = max(bc.lattice.dimensions) * 0.001
            mod.merge_threshold = max(dimensions()) * 0.001

            if (op.shape_type == 'NGON' or op.ngon_fit) and not preference.shape.cyclic:
                modifier.sort(bc.shape, types=['LATTICE', 'BEVEL'], first=True, typed_order=True)

        vertex_groups = bc.shape.vertex_groups if not straight_edge else reversed(bc.shape.vertex_groups)
        front_bevel = bc.bevel_front_face and (bc.q_bevel and not bc.q_back_only and op.geo['indices']['top_face']) and vertex_groups

        if not front_bevel or preference.shape.bevel_both:
            for group in vertex_groups:
                mod = bc.shape.modifiers.new(name=group.name, type='VERTEX_WEIGHT_EDIT')
                mod.vertex_group = group.name
                mod.use_remove = True
                mod.remove_threshold = 0.99

                mod = bc.shape.modifiers.new(name='Quad Bevel', type='BEVEL')
                mod.show_viewport = op.extruded
                mod.show_expanded = False

                mod.width = op.last['modifier']['quad_bevel_width']
                mod.segments = preference.shape.quad_bevel_segments
                mod.limit_method = 'VGROUP'
                mod.vertex_group = group.name
                mod.offset_type = 'OFFSET'
                mod.use_clamp_overlap = True if ngon or boxgon else False

                if mod.vertex_group == 'bottom' and not straight_edge:
                    mod.offset_type = 'WIDTH'

                if width_input > clamp(op):
                    mod.width = clamp_offset

                mod = bc.shape.modifiers.new(name='Quad Bevel Weld', type='WELD')
                mod.show_render = False
                mod.show_expanded = False
                # mod.merge_threshold = max(bc.lattice.dimensions) * 0.001
                mod.merge_threshold = max(dimensions()) * 0.001

        if front_bevel:
            mesh.mesh.recalc_normals(bc.shape, face_indices=op.geo['indices']['top_face'], inside=not op.inverted_extrude)

            mod = bc.shape.modifiers.new(name='Vgroup', type='VERTEX_WEIGHT_MIX')
            mod.vertex_group_a = 'bottom'
            mod.vertex_group_b = 'bottom'
            mod.mix_mode = 'ADD'

            mod = bc.shape.modifiers.new(name='Front Bevel', type='BEVEL')
            mod.show_viewport = op.extruded
            mod.show_expanded = False

            mod.width = op.last['modifier']['front_bevel_width']
            mod.segments = preference.shape.front_bevel_segments
            mod.limit_method = 'VGROUP'
            mod.vertex_group = 'bottom'
            mod.invert_vertex_group = True
            mod.offset_type = 'WIDTH'
            mod.angle_limit = radians(50)

            if width_input > clamp(op):
                mod.width = clamp_offset

            mod = bc.shape.modifiers.new(name='Front Bevel Weld', type='WELD')
            mod.show_render = False
            mod.show_expanded = False
            # mod.merge_threshold = max(bc.lattice.dimensions) * 0.001
            mod.merge_threshold = max(dimensions()) * 0.001

        elif not bc.q_bevel:
            mesh.mesh.recalc_normals(bc.shape, inside=op.inverted_extrude)

        modifier.sort(bc.shape, types=['LATTICE', 'MIRROR'], first=True, typed_order=True)

        if not preference.shape.cyclic:
            modifier.sort(bc.shape, types=['SOLIDIFY', 'SCREW'], last=True)

        else:
            modifier.sort(bc.shape, types=['VERTEX_WEIGHT_EDIT', 'VERTEX_WEIGHT_MIX', 'BEVEL', 'WELD'])

        return

    if ngon or boxgon:
        factor = 0.005 / max_dimension

        shape = mesh.eval_shape(bpy.context)
        for index, vindex in enumerate(op.geo['indices']['offset'] if not op.inverted_extrude else op.geo['indices']['extrusion']):
            vert = bc.shape.data.vertices[vindex]

            if op.ngon_point_index == -1:

                segment_state = False
                for mod in bc.shape.modifiers:
                    if mod.type != 'BEVEL':
                        continue

                    if not mesh.index_weight(vert.index, vert=True):
                        continue

                    weighted_width = op.last['vert_weight'][index] + width_input * factor
                    if weighted_width != 0.0 and weighted_width <= 0.0001 and not op.width_state or segment_state:
                        segment_state = True
                        op.width_state = True

                        if mod.segments == 1 and op.segment_state:
                            mod.segments = preference.shape.bevel_segments if preference.shape.bevel_segments != 1 else preference.shape.bevel_segments_default

                        else:
                            op.segment_state = True
                            mod.segments = 1

                    elif weighted_width > 0.0011 and op.width_state:
                        op.width_state = False

            if vert.index == op.ngon_point_index or op.ngon_point_index == -1:

                mesh.index_weight(index, vert=True, value=op.last['vert_weight'][index] + width_input * factor)

                # update = True
                for eindex in op.geo['indices']['top_edge']:
                    edge = bc.shape.data.edges[eindex]

                    if vert.index not in edge.vertices:
                        continue

                    vert1 = shape.vertices[edge.vertices[0]]
                    vert2 = shape.vertices[edge.vertices[1]]

                    weight = 0
                    if vert.index != vert1.index:
                        weight = mesh.index_weight(vert1.index, vert=True)

                    if vert.index != vert2.index:
                        weight = mesh.index_weight(vert2.index, vert=True)

                    length = (vert1.co - vert2.co).length

                    if op.ngon_point_index != -1:
                        length = length - (length * weight)

                    vert_weight = mesh.index_weight(vert.index, vert=True)

                    # if clamp_offset * vert_weight > length:
                    #   update = False
                    #   continue

                    if op.ngon_point_index == -1 and not vert_weight:
                        op.last['vert_weight'][index] = preference.shape.bevel_width - (clamp_offset * vert_weight)

                # if update:
                mesh.index_weight(vindex, vert=True, value=op.last['vert_weight'][index] + width_input * factor)

                for eindex in op.geo['indices']['mid_edge']:
                    edge = bc.shape.data.edges[eindex]

                    if vert.index not in edge.vertices:
                        continue

                    value = mesh.index_weight(vert.index, vert=True)
                    mesh.index_weight(eindex, value=value)
                    mesh.index_weight(edge.vertices[0], vert=True, value=value)
                    mesh.index_weight(edge.vertices[1], vert=True, value=value)

        if not preference.shape.quad_bevel and op.extruded and op.ngon_point_index == -1 and bc.q_bevel:
            if not op.last['edge_weight']:
                op.last['edge_weight'] = [mesh.index_weight(edge.index) for edge in bc.shape.data.edges]

            for index in op.geo['indices']['bot_edge']:
                edge = bc.shape.data.edges[index]

                mesh.index_weight(edge.index, value=op.last['edge_weight'][index] + width_input * factor)

        op.last['bevel_width'] = clamp_offset

        if not preference.shape.cyclic:
            edge_ids = op.geo['indices']['mid_edge']

            if  len(op.geo['indices']['mid_edge']) > 2:
                for i in (0, -1):
                    mesh.index_weight(edge_ids[i], vert=False, value=0.0)
                    edge = bc.shape.data.edges[edge_ids[i]]
                    mesh.index_weight(edge.vertices[0], vert=True, value=0.0)
                    mesh.index_weight(edge.vertices[1], vert=True, value=0.0)

        return

    segment_state = False
    update = True
    for mod in bc.shape.modifiers:
        if mod.type == 'BEVEL':
            width_type = 'bevel_width' if mod.name.startswith('Bevel') else F'{mod.name.split(" ")[0].lower()}_bevel_width'

            _input = lambda n: rounded(n + width_input * factor)
            last = op.last['modifier'][width_type]
            width = (_input(last) if last < clamp_offset else _input(clamp_offset))

            if width < 0.0004:
                width = 0.0004

            if width >= clamp_offset:
                clamped = True
                width = clamp_offset
                update = False

            if snap and event and event.ctrl:
                width = round(width, 2 if event and event.shift and op.prior_to_shift == 'NONE' else 1)

            if not clamped:
                if width < 0.001 and not op.width_state or segment_state:
                    segment_state = True
                    op.width_state = True

                    if mod.segments == 1 and op.segment_state:
                        mod.segments = preference.shape.bevel_segments if preference.shape.bevel_segments != 1 else preference.shape.bevel_segments_default

                    else:
                        op.segment_state = True
                        mod.segments = 1

                elif width > 0.0011 and op.width_state:
                    op.width_state = False

            if update:
                op.last['modifier'][width_type] = width
                preference.shape[width_type] = width

            mod.width = width

    op.last['mouse'] = op.mouse['location']


def clamp(op, q = False):
    from .. import bound_box, dimensions
    preference = addon.preference()
    bc = bpy.context.scene.bc

    offset = 0.0025 if bpy.app.version[:2] < (2, 82) else 0

    taper = preference.shape.taper

    ngon = op.shape_type == 'NGON' or op.ngon_fit
    boxgon = op.shape_type == 'BOX' and not op.ngon_fit and (op.ngon_point_index != -1 or op.ngon_point_bevel)
    if (ngon or boxgon) and not preference.shape.lasso and not q:
        dist = 0
        shape = mesh.eval_shape(bpy.context)
        indices = {i for i in range(len(shape.edges))}
        for index in op.geo['indices']['top_edge']:
            if index not in indices:
                continue

            edge = shape.edges[index]

            vert1 = shape.vertices[edge.vertices[0]]
            vert2 = shape.vertices[edge.vertices[1]]

            length = (vert1.co - vert2.co).length

            if length > dist:
                dist = length

        return dist * taper - offset

    bb = bound_box()
    vector1 = Vector(bb[0][:])
    vector2 = Vector(bb[1][:])
    vector3 = Vector(bb[5][:])
    vector4 = Vector(bb[6][:])

    distances = [vector4 - vector3, vector3 - vector2]

    if op.shape_type == 'CIRCLE' and not preference.shape.circle_type == 'STAR':
        z_height = dimensions()[2]

        if not op.flip_z and max(min(distances)) * 0.5 <= z_height:
            return max(min(distances)) * 0.7037037037037 * taper - offset

        return z_height * 1.42105263 * taper - offset

    if not offset:
        offset = -max(min(distances)) * 0.01

    if q: distances.append((vector2 - vector1) * 2.7037037037037)

    return max(min(distances)) * 0.5 * taper - offset


def clamp_and_visual_weight(op, bc, pref, clamp, set=True):
    prev = op.last['modifier']['bevel_width']

    vindices = op.geo['indices']['offset'] if not op.inverted_extrude else op.geo['indices']['extrusion']
    eindices = op.geo['indices']['mid_edge']

    for index, vindex in enumerate(vindices):
        vert = bc.shape.data.vertices[vindex]

        if op.last['modifier']['bevel_width'] > clamp:
            op.last['modifier']['bevel_width'] = clamp

        if mesh.index_weight(vert.index, vert=True) == 1.0:
            mesh.index_weight(vert.index, vert=True, value=clamp * (prev / 100) * 100)

        elif set:
            mesh.index_weight(vert.index, vert=True, value=pref.shape.bevel_width * (clamp / 100) * 100)

        # if vert.index == op.ngon_point_index:

        op.last['vert_weight'][index] = mesh.index_weight(vindex, vert=True)

        for eindex in eindices:
            edge = bc.shape.data.edges[eindex]

            if vert.index not in edge.vertices:
                continue

            mesh.index_weight(edge.index, value=mesh.index_weight(vert.index, vert=True))
