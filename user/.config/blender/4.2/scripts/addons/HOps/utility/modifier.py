import bpy

from mathutils import Vector
from ctypes import Structure, c_float, c_short, c_char, cast, POINTER

### DEVIATION FROM BC/KITOPS
from . import addon
def user_sort(obj):
    # ignore_weight = addon.preference().property.sort_bevel_ignore_weight
    # ignore_vgroup = addon.preference().property.sort_bevel_ignore_vgroup
    # ignore_verts = addon.preference().property.sort_bevel_ignore_only_verts
    # sort_depth = addon.preference().property.sort_depth
    # props = {'use_only_vertices': True} if bpy.app.version < (2, 90, 0) else {'affect': 'VERTICES'}
    # bevs = bevels(obj, weight=ignore_weight, vertex_group=ignore_vgroup, props=props if ignore_verts else {})
    # sort(obj, option=addon.preference().property, ignore=bevs, sort_depth=sort_depth, ignore_flag=addon.preference().property.sort_ignore_char, stop_flag=addon.preference().property.sort_stop_char)
    sort(obj, option=addon.preference().property)


def bevel_method(obj):
    for mod in obj.modifiers:
        if mod.type == "BEVEL":
            mod.limit_method = addon.preference().property.workflow_mode
### END DEVIATION

_graph_hash = {
    'Auto Smooth': {
        '82a873746244f4af9ad0a644b5a4fedc4ea296b183f313567d8c254c33f1096986036e7a2d89d8e1cbf159fe039afeb67c382fae2f18d1aa3791677c70be558e',
        'c39943bc2ed4864755a7b17042831d2356f150a0a499ea7be361941d717879fc8f1b5be73166b473592984624729fa854a96de353f5e36a6ffd2e9412b4d36f1'
    },
}

sort_types = [
    'NODES',
    'ARRAY',
    'MIRROR',
    'SOLIDIFY',
    'BEVEL',
    'WEIGHTED_NORMAL',
    'SIMPLE_DEFORM',
    'TRIANGULATE',
    'DECIMATE',
    'REMESH',
    'SUBSURF',
    'UV_PROJECT',
]

if bpy.app.version[:2] >= (2, 82):
    sort_types.insert(4, 'WELD')

sort_flag = '*'
ignore_flag = ' '
sort_last_flag = '!'
lock_above_flag = '.'
lock_below_flag = '^'
stop_flag = '_'


def sort(obj, option=None, types=[], first=False, last=False, typed_order=False):
    ignore = []
    modifiers = []
    modifiers_last = []
    modifiers_lock_above_below = []
    sortable = obj.modifiers[:]
    sort_depth = 0 if not option else option.sort_depth
    force_last = []

    if len(sortable) < 2 : return


    def modifier_insert(use_sort, use_last, modifier, is_sort_last_flag):
        if not use_sort and not is_sort_last_flag:
            return

        if is_sort_last_flag:
            for mod in modifiers_last[:]:
                if modifier.type == mod.type:
                    if mod.name.startswith(sort_last_flag):
                        is_sort_last_flag = False
                        use_last = False
                        break

                    modifiers_last.remove(mod)

            for mod in modifiers:
                if is_sort_last_flag and modifier.type == mod.type:
                    modifiers.remove(mod)

        if modifier.type not in [mod.type for mod in modifiers_last]:
            modifiers.insert(0, modifier)

        if use_last:
            modifiers_last.append(modifier)


    def modifier_check_above_below(use_sort, use_last, modifier, is_sort_last_flag, type='above'):
        _modifiers = obj.modifiers[:]
        index = _modifiers.index(mod)
        offset_index = index + 1 if type == 'above' else index -1

        if offset_index > len(_modifiers) - 1 or offset_index < 0:
            return

        modifiers_lock_above_below.append([type, _modifiers[offset_index], modifier])


    def modifier_check(modifier):
        if not modifier.name or modifier.name.startswith(sort_last_flag*2):
            return

        prop = F'sort_{modifier.type.lower()}'
        use_sort = getattr(option, prop) if option and modifier.type in types else modifier.type in types or modifier.name.startswith(sort_flag)
        use_last = getattr(option, F'{prop}_last') if option and modifier.type in types else modifier.name.startswith(sort_last_flag)
        is_sort_last_flag = use_last and modifier.name.startswith(sort_last_flag)

        if first or last and not option:
            use_sort = modifier.type in types
            use_last = False
            is_sort_last_flag = False

        if modifier.name.startswith(lock_above_flag):
            modifier_check_above_below(use_sort, use_last, modifier, is_sort_last_flag, type='above')

        elif modifier.name.startswith(lock_below_flag):
            modifier_check_above_below(use_sort, use_last, modifier, is_sort_last_flag, type='below')

        else:
            modifier_insert(use_sort, use_last, modifier, is_sort_last_flag)

    if option and not option.sort_modifiers:
        return

    if not types:
        types = sort_types

    if sort_depth:
        length = len(sortable)

        if length > sort_depth:
            sortable = sortable[length - sort_depth - 1:]

    if option:
        ignore_weight = option.sort_bevel_ignore_weight
        ignore_vgroup = option.sort_bevel_ignore_vgroup
        ignore_verts = option.sort_bevel_ignore_only_verts
        props = {'use_only_vertices': True} if bpy.app.version[:2] < (2, 90) else {'affect': 'VERTICES'}
        for mod in bevels(obj, weight=ignore_weight, vertex_group=ignore_vgroup, props=props if ignore_verts else {}):
            ignore.append(mod)

    for mod in sortable[:]:
        if mod in ignore or mod.name.startswith(ignore_flag):
            sortable.remove(mod)
        if mod.name.startswith(sort_last_flag*2):
            force_last.append(mod)
            sortable.remove(mod)

    for index, mod in enumerate(sortable):
        if mod.name[0] == stop_flag:
            sortable = sortable[index+1:]

            break

    if typed_order:
        for type in types:
            for mod in reversed(sortable):
                if mod.type != type:
                    continue

                modifier_check(mod)
    else:
        for mod in reversed(sortable):
            modifier_check(mod)

    for mod in force_last:
        modifiers.append(mod)

    if not modifiers and not modifiers_lock_above_below:
        return

    for prop in modifiers_lock_above_below:
        if prop[1] not in modifiers:
            continue

        index = modifiers.index(prop[1])

        if prop[0] == 'above':
            modifiers.insert(index, prop[2])
            continue

        if index + 1 == len(modifiers):
            modifiers.append(prop[2])
            continue

        modifiers.insert(index + 1, prop[2])

    modifiers = [stored(mod) for mod in modifiers]
    names = {mod.name for mod in modifiers}
    for mod in obj.modifiers[:]:
        if mod.name in names:
            obj.modifiers.remove(mod)

    for index, mod in enumerate(modifiers):
        m = new(obj, mod=mod)

        if first:
            move_to_index(m, index=0)


def apply(obj, mod=None, visible=False, modifiers=[], ignore=[], types={}):
    apply = []
    keep = []

    if mod:
        apply.append(mod)

    else:
        for mod in obj.modifiers:
            if (not modifiers or mod in modifiers) and mod not in ignore and (not visible or mod.show_viewport) and (not types or mod.type in types):
                apply.append(mod)

    for mod in obj.modifiers:
        if mod not in apply:
            keep.append((mod, mod.show_viewport))

    if not apply:
        del keep

        return

    for mod in keep:
        mod[0].show_viewport = False

    shared_name = None
    if obj.data.users > 1:
        shared_name = obj.data.name
        obj.data = obj.data.copy()
    remesh_voxel_size = obj.data.remesh_voxel_size

    ob = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    obj.data = bpy.data.meshes.new_from_object(ob)
    obj.data.remesh_voxel_size = remesh_voxel_size

    for mod in apply:
        obj.modifiers.remove(mod)

    for mod in keep:
        mod[0].show_viewport = mod[1]

    for o in bpy.context.view_layer.objects:
        if o.type != 'MESH':
            continue

        if o.data.name == shared_name:
            o.data = obj.data

    if shared_name:
        obj.data.name = shared_name

    del apply
    del keep


def bevels(obj, angle=False, weight=False, vertex_group=False, props={}):
    if not hasattr(obj, 'modifiers'):
        return []

    bevel_mods = [mod for mod in obj.modifiers if mod.type == 'BEVEL']

    if not angle and not weight and not vertex_group and not props:
        return bevel_mods

    modifiers = []

    if angle:
        for mod in bevel_mods:
            if mod.limit_method == 'ANGLE':
                modifiers.append(mod)

    if weight:
        for mod in bevel_mods:
            if mod.limit_method == 'WEIGHT':
                modifiers.append(mod)

    if vertex_group:
        for mod in bevel_mods:
            if mod.limit_method == 'VGROUP':
                modifiers.append(mod)

    if props:
        for mod in bevel_mods:
            if mod in modifiers:
                continue

            for pointer in props:
                prop = hasattr(mod, pointer) and getattr(mod, pointer) == props[pointer]
                if not prop:
                    continue

                modifiers.append(mod)

    return sorted(modifiers, key=lambda mod: bevel_mods.index(mod))


def unmodified_bounds(obj, exclude={}):
    disabled = []
    for mod in obj.modifiers:
        if exclude and mod.type not in exclude and mod.show_viewport:
            disabled.append(mod)
            mod.show_viewport = False

    if disabled:
        bpy.context.view_layer.update()

    bounds = [Vector(point[:]) for point in obj.bound_box[:]]

    for mod in disabled:
        mod.show_viewport = True

    del disabled

    return bounds


def stored(mod):
    exclude = {'__doc__', '__module__', '__slots__', '_RNA_UI', 'bl_rna', 'rna_type', 'face_count', 'is_override_data', 'particle_system', 'map_curve', 'execution_time', 'persistent_uid'}
    new_type = type(mod.name, (), {})
    new_type.transfer_items = []

    projector = lambda p: type('projector', (), {'object': p.object})
    profile_point = lambda p: CurveProfilePoint(x=p.x, y=p.y, flag=p.flag, h1=p.h1, h2=p.h2, h1_loc=p.h1_loc, h2_loc=p.h2_loc)

    if mod.type == 'NODES':
        new_type.transfer_items = [i for i in mod.items()]

    else:
        del new_type.transfer_items

    for pointer in dir(mod):
        if pointer not in exclude:

            type_string = str(type(getattr(mod, pointer))).split("'")[1]
            if mod.type == 'UV_PROJECT' and pointer =='projectors':
                setattr(new_type, pointer, [projector(p) for p in mod.projectors])

            elif mod.type == 'BEVEL' and pointer == 'custom_profile':
                profile = type('custom_profile', (), {
                    'use_clip': mod.custom_profile.use_clip,
                    'use_sample_even_lengths': mod.custom_profile.use_sample_even_lengths,
                    'use_sample_straight_edges': mod.custom_profile.use_sample_straight_edges,
                    'points': [profile_point(cast(p.as_pointer(), POINTER(CurveProfilePoint)).contents) for p in mod.custom_profile.points]})

                setattr(new_type, pointer, profile)

            elif mod.type == 'HOOK' and pointer == 'matrix_inverse':
                setattr(new_type, pointer, getattr(mod, pointer).copy()) # XXX: use copy

            elif type_string not in {'bpy_prop_array', 'Vector'}:
                setattr(new_type, pointer, getattr(mod, pointer))

            else:
                setattr(new_type, pointer, list(getattr(mod, pointer)))

    if mod.type == 'NODES' and mod.node_group:
        input_nodes = (n for n in mod.node_group.nodes if isinstance(n, bpy.types.NodeGroupInput))
        mod_data = {'sockets': {}}
        for input_node in input_nodes:
            for socket in input_node.outputs[1:-1]: # Using slicing to skip the first input that is always geometry and and last that is __extend__
                socket_identifier = socket.identifier
                socket_value = mod[socket_identifier]
                mod_data['sockets'][socket_identifier] = socket_value
        setattr(new_type, 'geometry_nodes_data', mod_data)

    return new_type


def new(obj, name=str(), _type='BEVEL', mod=None, props={}):
    new = None
    if mod:
        new = obj.modifiers.new(name=mod.name, type=mod.type)

        for pointer in dir(mod):
            if '__' in pointer or pointer in {'bl_rna', 'rna_type', 'type', 'face_count', 'falloff_curve', 'vertex_indices', 'vertex_indices_set', 'is_override_data', 'particle_system', 'map_curve', 'execution_time', 'persistent_uid'}:
                continue

            elif mod.type == 'NODES':
                new.node_group = mod.node_group
                new.show_group_selector = mod.show_group_selector

                if hasattr(mod, 'transfer_items'):
                    for index, item in enumerate(mod.transfer_items):
                        new[item[0]] = item[1]

            elif mod.type == 'UV_PROJECT' and pointer =='projectors':
                new.projector_count = mod.projector_count
                for new_proj, old_proj in zip(new.projectors, mod.projectors):
                    new_proj.object = old_proj.object

            elif mod.type == 'BEVEL' and pointer == 'custom_profile':
                step = 1 / len(mod.custom_profile.points)
                for index, point in enumerate(mod.custom_profile.points[1:-1]):
                    new.custom_profile.points.add(index * step, (index + 1) * step)

                for index, point in enumerate(mod.custom_profile.points):
                    point = cast(point.as_pointer(), POINTER(CurveProfilePoint)).contents if hasattr(point,'as_pointer') else point
                    new_point = cast(new.custom_profile.points[index].as_pointer(), POINTER(CurveProfilePoint)).contents

                    new_point.x = point.x
                    new_point.y = point.y
                    new_point.flag = point.flag
                    new_point.h1 = point.h1
                    new_point.h2 = point.h2
                    new_point.h1_loc = point.h1_loc
                    new_point.h2_loc = point.h2_loc

                new.custom_profile.update()

                new.custom_profile.use_clip = mod.custom_profile.use_clip
                new.custom_profile.use_sample_even_lengths = mod.custom_profile.use_sample_even_lengths
                new.custom_profile.use_sample_straight_edges = mod.custom_profile.use_sample_straight_edges

            else:
                setattr(new, pointer, getattr(mod, pointer))

        if mod and mod.type == 'NODES':
            if bpy.app.version[:2] >= (4, 0):
                new.show_group_selector = mod.show_group_selector
            for socket_identifier, socket_value in getattr(mod, 'geometry_nodes_data', {}).get('sockets', {}).items():
                new[socket_identifier] = socket_value

        if mod.type == 'HOOK':
            new.matrix_inverse = mod.matrix_inverse # XXX: needs to be set after new.object
            new.vertex_indices_set(mod.vertex_indices)

    elif _type:
        new = obj.modifiers.new(name=name, type=_type)

        if props:
            for pointer in props:
                if hasattr(new, pointer):
                    setattr(new, pointer, props[pointer])

    return new


def exists(obj, full_match=True, types={}, **props):
    if not obj.modifiers:
        return False

    item = props.items()

    if not item:
        return bool(obj.modifiers) if not types else bool(any(mod.type in types for mod in obj.modifiers))

    checked = []
    for key, arg in item:
        checked.append(any(hasattr(mod, key) and getattr(mod, key) == arg or mod.type in types) for mod in obj.modifiers)

    return all(checked) if full_match else any(checked)


def collect(obj, full_match=False, types={}, **props):
    if not obj.modifiers:
        return []

    item = props.items()

    if not item:
        return obj.modifiers[:] if not types else [mod for mod in obj.modifiers if mod.type in types]

    check = lambda m, i: ((hasattr(m, k) and getattr(m, k) == a) for k, a in i) or m.type in types
    validated = lambda m, i: all(check(m, i)) if full_match else any(check(m, i))

    modifiers = []
    for mod in obj.modifiers:
        if not validated(mod, item):
            continue

        modifiers.append(mod)

    return modifiers


def move_to_index(mod, index=0, rebuild=False):
    from . import operator_override

    count = len(mod.id_data.modifiers)

    if index < 0:
        index = count - (abs(index) % count)

    else:
        index = index % count

    if bpy.app.version[:2] >= (2, 90) and not rebuild:
        override = {'object' : mod.id_data, 'active_object' : mod.id_data}
        operator_override(bpy.context, bpy.ops.object.modifier_move_to_index, override, modifier=mod.name, index=index)

    else:
        obj = mod.id_data
        modifiers = [stored(m) for m in obj.modifiers if m != mod]
        modifiers.insert(index, stored(mod))

        obj.modifiers.clear()

        for mod in modifiers:
            new(obj, mod=mod)


def graph_hash(mod, limit=0):
    from . import hash_iter
    return hash_iter(mod.node_group.nodes, 'type', limit=limit)


def hashed_graph(mod):
    if mod.type != 'NODES':
        return ''

    for type in _graph_hash:
        if graph_hash(mod) in _graph_hash[type]:
            return type

    return ''


class CurveProfilePoint(Structure):
    _fields_ = [
        ('x', c_float),
        ('y', c_float),
        ('flag', c_short),
        ('h1', c_char),
        ('h2', c_char),
        ('h1_loc', c_float * 2),
        ('h2_loc', c_float * 2)]
