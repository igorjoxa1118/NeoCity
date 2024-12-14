import bpy

from bpy.utils import register_class, unregister_class

from ..... utility import addon, modifier
from .... utility import adjust_shapez_to_solver
from .... import toolbar
from .... operator.property import operation
from .... operator.shape.utility.modal.mode import change

recent_sort_char = {}

sort_options = (
    'sort_modifiers',
    'sort_nodes',
    'sort_bevel',
    'sort_array',
    'sort_mirror',
    'sort_solidify',
    'sort_weighted_normal',
    'sort_simple_deform',
    'sort_triangulate',
    'sort_decimate',
    'sort_remesh',
    'sort_subsurf',
    'sort_bevel_last',
    'sort_array_last',
    'sort_mirror_last',
    'sort_nodes_last',
    'sort_solidify_last',
    'sort_weighted_normal_last',
    'sort_simple_deform_last',
    'sort_triangulate_last',
    'sort_decimate_last',
    'sort_remesh_last',
    'sort_subsurf_last')


def sync_sort(behavior, context):
    for option in sort_options:
        if addon.hops() and hasattr(addon.hops().property, option):
            addon.hops().property[option] = getattr(behavior, option)
        # else:
        #     print(F'Unable to sync sorting options with Hard Ops; Box Cutter {option}\nUpdate Hard Ops!')

        if addon.kitops() and hasattr(addon.kitops(), option):
            addon.kitops()[option] = getattr(behavior, option)
        else:
            # print(F'Unable to sync sorting options with KIT OPS; Box Cutter {option}\nUpdate KIT OPS!')
            pass


def validate_char(behavior, context, option):
    for other in dir(behavior):
        if not other.endswith('_char'):
            continue

        if option == other:
            if not getattr(behavior, option):
                value = behavior.__annotations__[option].keywords['default']
                recent_sort_char[option] = value
                setattr(behavior, option, value)

                return

            continue

        if getattr(behavior, option) == getattr(behavior, other):
            setattr(behavior, other, recent_sort_char[option])
            recent_sort_char[option] = getattr(behavior, option)

            return

    recent_sort_char[option] = getattr(behavior, option)


def sort_depth(behavior, context):
    sync_sort(behavior, context)

    # modifier.sort_depth = behavior.sort_depth


def sort_char(behavior, context):
    validate_char(behavior, context, 'sort_char')
    sync_sort(behavior, context)

    modifier.sort_flag = behavior.sort_char


def sort_ignore_char(behavior, context):
    validate_char(behavior, context, 'sort_ignore_char')
    sync_sort(behavior, context)

    modifier.ignore_flag = behavior.sort_ignore_char


def sort_last_char(behavior, context):
    validate_char(behavior, context, 'sort_last_char')
    sync_sort(behavior, context)

    modifier.sort_last_flag = behavior.sort_last_char


def sort_lock_above_char(behavior, context):
    validate_char(behavior, context, 'sort_lock_above_char')
    sync_sort(behavior, context)

    modifier.lock_below_flag = behavior.sort_lock_above_char


def sort_lock_below_char(behavior, context):
    validate_char(behavior, context, 'sort_lock_below_char')
    sync_sort(behavior, context)

    modifier.lock_above_flag = behavior.sort_lock_below_char


def sort_stop_char(behavior, context):
    validate_char(behavior, context, 'sort_stop_char')
    sync_sort(behavior, context)

    modifier.stop_flag = behavior.sort_stop_char


def simple_topbar(display, context):
    toggle = not display.simple_topbar
    display.topbar_pad = toggle
    display.pad_menus = toggle


def release_lock(keymap, context):
    bpy.ops.bc.release_lock('INVOKE_DEFAULT')


def tab(display, context):
    from .... panel import classes as panels

    for panel in panels:
        if hasattr(panel, 'bl_category') and panel.bl_category and panel.bl_category != 'Tool':
            unregister_class(panel)
            panel.bl_category = display.tab
            register_class(panel)


def shape_type(behavior, context):
    op = toolbar.option()

    # if op.shape_type != 'BOX' and behavior.draw_line:
    #     op.shape_type = 'BOX'


def shift_operation_preset(shift_operation, context):
    preference = addon.preference()
    preference.keymap['shift_operation_preset'] = shift_operation.name


def shift_operation_presets(keymap, context):
    preset = keymap.shift_operation_preset

    if preset:
        keymap.shift_operation_presets[preset].operation = keymap.shift_operation


def shift_in_operation(_, context):
    preference = addon.preference()

    if not preference.keymap.shift_operation_preset:
        return

    preset = preference.keymap.shift_operation_presets[preference.keymap.shift_operation_preset]

    for shift_operation in operation.shift_operations:
        preset[shift_operation.lower()] = getattr(preference.keymap.shift_in_operations, shift_operation.lower())


def shift_operation(keymap, context):
    preset_name = keymap.shift_operation_preset

    preset = None

    if preset_name:
        preset = keymap.shift_operation_presets[preset_name]

        if keymap.shift_operation != preset.operation:
            keymap.shift_operation = preset.operation

        for shift_operation in operation.shift_operations:
            keymap.shift_in_operations[shift_operation.lower()] = getattr(preset, shift_operation.lower())


def inset_bevel(behavior, context):
    bc = context.scene.bc

    if not bc.running:
        return

    preference = addon.preference()

    if preference.behavior.recut:
        preference.behavior.recut = False

    if preference.behavior.inset_slice:
        preference.behavior.inset_slice = False

    if not preference.behavior.inset_bevel:
        if not bc.bevel:
            return

        for tgt in bc.operator.datablock['targets']:
            for i, m in enumerate(tgt.modifiers):
                if m.type == 'BOOLEAN' and m.object == bc.bevel:
                    m.object = bc.inset
                    tgt.modifiers.remove(tgt.modifiers[i + 1])
                    break

        for obj in bc.operator.datablock['bevels']:
            bpy.data.objects.remove(obj)

        bc.operator.datablock['bevels'].clear()

        bc.bevel = None

        for m in reversed(bc.inset.modifiers):
            if m.type == 'DISPLACE':
                bc.inset.modifiers.remove(m)
                break

        solidify = None
        for m in reversed(bc.inset.modifiers):
            if m.type == 'SOLIDIFY':
                solidify = m
                break

        solidify.show_viewport = True

        return

    if bc.operator.mode != 'INSET':
        return

    bc.bevel = bc.inset.copy()
    bc.bevel.data.bc.inset_bevel = True

    index = 0
    for i, m in enumerate(reversed(bc.bevel.modifiers)):
        if m.type == 'BOOLEAN' and m.object != bc.shape:
            index = len(bc.bevel.modifiers) - i

    for m in bc.bevel.modifiers:
        if m.type == 'BOOLEAN' and not m.show_viewport:
            m.show_viewport = True

        if m.type != 'BOOLEAN' or m.object == bc.shape:
            continue

        if not m.object:
            continue

        if m.object.data.bc.inset_bevel:
            m.show_viewport = False

    bc.collection.objects.link(bc.bevel)
    bc.bevel.bc.bevel = True
    bc.bevel.name = 'Bevel'
    bc.bevel.data.name = 'Bevel'

    bc.bevel.hide_set(True)

    solidify = None
    for m in bc.inset.modifiers:
        if m.type == 'SOLIDIFY':
            solidify = m
            break

    solidify.show_viewport = False

    displace = bc.inset.modifiers.new(name='Displace', type='DISPLACE')
    displace.strength = preference.shape.offset
    displace.mid_level = 0

    for mod in bc.bevel.modifiers[:]:
        if mod.type == 'WEIGHTED_NORMAL':
            bc.bevel.modifiers.remove(mod)

        if mod.type == 'BEVEL':
            bc.bevel.modifiers.remove(mod)

    solidify = None
    for mod in bc.bevel.modifiers:
        if mod.type == 'SOLIDIFY':
            solidify = mod
            break

    solidify.show_expanded = False
    solidify.thickness = bpy.context.space_data.clip_end
    solidify.offset = 1.000001

    bevel = bc.bevel.modifiers.new(name='_Bevel', type='BEVEL')
    bevel.show_expanded = False
    bevel.width = abs(bc.operator.last['thickness'])

    modifier.move_to_index(bevel, index)
    bc.operator.datablock['bevels'].append(bc.bevel)

    for o in bc.operator.datablock['targets']:
        for m in o.modifiers:
            if m.type == 'BOOLEAN' and m.object == bc.inset:
                m.object = bc.bevel

    for m in reversed(bc.bevel.modifiers):
        if m.type == 'BOOLEAN':
            m.name = F'_{m.name}'
            break

    weld = None
    for tgt in bc.operator.datablock['targets']:
        for index, mod in enumerate(tgt.modifiers):
            if mod.type != 'BOOLEAN' or not mod.object:
                continue

            if not mod.object.data.bc.inset_bevel:
                continue

            if index + 1 >= len(tgt.modifiers):
                continue

            if tgt.modifiers[index + 1].type != 'WELD':
                continue

            weld = tgt.modifiers[index + 1]

    for tgt in bc.operator.datablock['targets']:
        for index, mod in enumerate(tgt.modifiers):
            if mod.type != 'BOOLEAN' or mod.object != bc.bevel:
                continue

            if not weld:
                weld = tgt.modifiers.new(name='Inset Weld', type='WELD')
                weld.show_expanded = False
                modifier.move_to_index(weld, index + 1)
                break

            modifier.move_to_index(weld, index)
            break


def rebool(_, context):
    bc = context.scene.bc

    if not bc.running:
        return

    operator = bc.operator

    event = type('fake_event', (), {'ctrl' : False, 'shift' : False, 'alt' : False})
    change(operator, context, event, to=operator.mode, force=True)


def boolean_solver(behavior, context):
    bc = context.scene.bc

    if not bc.running or not bpy.app.version[:2] >= (2, 91):
        return

    operator = bc.operator

    if operator.mode == 'INSET':
        for target, inset in zip(operator.datablock['targets'], operator.datablock['insets']):
            for mod in reversed(target.modifiers):
                if mod.type == 'BOOLEAN' and mod.object is inset:
                    mod.solver = behavior.boolean_solver
                    break

            for mod in reversed(inset.modifiers):
                if mod.type == 'BOOLEAN' and mod.object is bc.shape:
                    mod.solver = behavior.boolean_solver
                    break

        for slice, inset in zip(operator.datablock['slices'], operator.datablock['insets']):
            for mod in reversed(slice.modifiers):
                if mod.type == 'BOOLEAN' and mod.object is inset:
                    mod.solver = behavior.boolean_solver
                    break

        #<< elif operator.mode == 'JOIN':
        #<<     for obj in operator.datablock['targets'] + operator.datablock['slices']:
        #<<         for mod in reversed(obj.modifiers):
        #<<             if mod.type == 'BOOLEAN' and mod.object is bc.shape:
        #<<                 # mod.solver = 'EXACT' if addon.preference().behavior.join_exact else behavior.boolean_solver
        #<<                 mod.solver = behavior.boolean_solver
        #<<                 break

    else:
        for obj in operator.datablock['targets'] + operator.datablock['slices']:
            for mod in reversed(obj.modifiers):
                if mod.type == 'BOOLEAN' and mod.object is bc.shape:
                    mod.solver = behavior.boolean_solver
                    break


    bc = context.scene.bc
    op = bc.operator

    if not op.extruded:
        adjust_shapez_to_solver(behavior, bc, op)


def hide_make_shapes(behavior, context):
    bc = context.scene.bc

    if not bc.running:
        return

    # operator = bc.operator

    if behavior.hide_make_shapes and not bc.shape.hide_get():
        bc.shape.hide_set(True)

    elif not behavior.hide_make_shapes and bc.shape.hide_get():
        bc.shape.hide_set(False)

        bc.shape.display_type = 'TEXTURED'

        bc.shape.data.use_auto_smooth = True
        for face in bc.shape.data.polygons:
            face.use_smooth = True
