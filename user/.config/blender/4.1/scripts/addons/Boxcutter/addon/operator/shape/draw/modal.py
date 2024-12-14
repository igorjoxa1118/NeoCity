import bpy

from mathutils import Vector, Matrix

from ..... utility import addon, modifier, view3d, context_copy, math, mesh, screen
# from ... utility import st3_simple_notification
from .. import utility
from .. utility import tracked_states, shader, bound_box, dimensions
from .... import toolbar


def add_logo(op, context):
    from .... property import new

    bc = context.scene.bc
    dat = bpy.data.meshes.new(name='Cutter')

    if bc.shape:
        bpy.data.objects.remove(bc.shape)

    dat.from_pydata(new.logo_verts, new.logo_edges, new.logo_faces, shade_flat=True)
    dat.validate()

    bc.shape = bpy.data.objects.new(name='Cutter', object_data=dat)
    del dat

    bc.shape.display_type = 'WIRE' if op.mode != 'MAKE' else 'TEXTURED'
    bc.shape.bc.shape = True

    bc.collection.objects.link(bc.shape)

    if addon.preference().behavior.auto_smooth:
        if bpy.app.version < (4, 1):
            bc.shape.data.use_auto_smooth = True

        for face in bc.shape.data.polygons:
            face.use_smooth = True

    bc.shape.hide_set(True)
    bc.shape.matrix_world = bc.lattice.matrix_world

    bc.shape.data.transform(Matrix.Translation(Vector((0, 0, -0.125))))
    bc.shape.data.transform(Matrix.Diagonal((0.5, 0.5, 1, 1)))

    utility.lattice.fit(op, context)

    for point in utility.lattice.back:
        bc.lattice.data.points[point].co_deform.z = -0.125

    op.last['depth'] = -0.125

    bc.shape.matrix_world = bc.plane.matrix_world


def repeat(op, context, event):
    if op.live:
        utility.modifier.create.boolean(op, show=True)

    utility.data.repeat(op, context, collect=False)

    if addon.preference().keymap.release_lock_repeat:
        utility.modal.operation.change(op, context, event, to='NONE')
        op.extruded = True
        op.update()
        return {'RUNNING_MODAL'}

    op.repeat = True
    op.execute(context)
    op.update()
    return {'FINISHED'}


def ngon_point_bevel(context, event, op, widget):
    op.ngon_point_index = widget.index

    if not op.ngon_point_bevel:
        op.ngon_point_bevel_reset = op.last['modifier']['bevel_width']

    op.ngon_point_bevel = True

    utility.modal.operation.change(op, context, event, to='BEVEL')


def method(op, context, event):
    if event.type == 'TIMER':
       return {'PASS_THROUGH'}

    preference = addon.preference()
    # bc = context.scene.bc
    bc = context.scene.bc

    option = op.tool.operator_properties('bc.shape_draw')
    # option = toolbar.options()

    if option.mode != op.mode:
        utility.modal.mode.change(op, context, event, to=option.mode)

    if option.operation != op.operation:
        if (op.shape_type != 'BOX' or op.ngon_fit) and option.operation == 'GRID':
            option.operation = op.operation

        else:
            utility.modal.operation.change(op, context, event, to=option.operation)

    if option.behavior != op.behavior:
        utility.modal.behavior.change(op, context, to=option.behavior)

    # if option.axis != bc.axis:
    #     utility.modal.axis.change(op, context, to=option.axis)

    if option.origin != op.origin and not op.allow_menu:
        utility.modal.origin.change(op, context, event, to=option.origin)

    alt_pressed = event.alt and not op.alt
    op.alt_toggle_extrude = alt_pressed and op.operation == 'EXTRUDE'
    alt_released = op.alt and not event.alt
    if alt_released:
        op.alt_e = False

    # ctrl_pressed = event.ctrl and not op.ctrl
    # ctrl_released = op.ctrl and not event.ctrl

    shift_pressed = event.shift and not op.shift
    shift_released = op.shift and not event.shift

    op.alt = event.alt
    op.ctrl = event.ctrl
    op.shift = event.shift
    op.mmb = False

    op.mouse['location'] = Vector((event.mouse_region_x, event.mouse_region_y))

    op.show_shape = True if preference.behavior.show_shape else event.shift

    if preference.display.show_shape_wire:
        tracked_states.shader_batch = True if op.show_shape else False

    op.use_cursor_depth = event.alt

    # TODO: when operation is updated from the topbar wait for lmb press before modal update
    pass_through = False

    tool_region = [region for region in context.area.regions if region.type == 'TOOL_HEADER'][0]

    within_region_tool_header = False
    within_region_tool_header_x = event.mouse_region_x > 0 and event.mouse_region_x < tool_region.width

    region_height = context.region.height
    header_height = tool_region.height
    total_height = region_height

    if context.space_data.show_region_tool_header:
        if bpy.app.version > (2, 93, 0): #XXX: change may have happened on a micro version
            region_height -= header_height
        else:
            total_height += header_height

        if tool_region.alignment == 'TOP':
            within_region_tool_header = within_region_tool_header_x and event.mouse_region_y > region_height and event.mouse_region_y < total_height
        else:
            within_region_tool_header = within_region_tool_header_x and event.mouse_region_y > 0 - header_height and event.mouse_region_y < 0

    within_region_3d_x = event.mouse_region_x > 0 and event.mouse_region_x < context.region.width
    within_region_3d_y = event.mouse_region_y > 0 and event.mouse_region_y < region_height
    within_region_3d = within_region_3d_x and within_region_3d_y

    ngon = op.shape_type == 'NGON' or op.ngon_fit
    boxgon = op.shape_type == 'BOX' and not op.ngon_fit

    if op.allow_menu and op.operation != 'NONE':
        op.allow_menu = False

    if within_region_3d:
        bc.empty.matrix_parent_inverse = Matrix()

        # op.lazorcut = bc.lattice.dimensions[2] < preference.shape.lazorcut_limit
        op.lazorcut = dimensions()[2] < preference.shape.lazorcut_limit

        # MOUSEMOVE
        # if event.type == 'MOUSEMOVE' and event.value == 'RELEASE':
        #     op.mmb = False

        if not op.add_point and preference.shape.lasso and op.shape_type == 'NGON' and not event.shift:
            op.last['placed_mouse'] = op.mouse['location']
            op.add_point = True

        if event.type == 'MOUSEMOVE' and op.add_point and op.operation == 'DRAW':
            if preference.shape.lasso and op.shape_type == 'NGON' and (op.mouse['location'] - op.last['placed_mouse']).length > 0:
                utility.mesh.add_point(op, context, event)
                op.add_point = False

            elif (op.mouse['location'] - op.last['placed_mouse']).length > context.preferences.inputs.drag_threshold_mouse:
                utility.mesh.add_point(op, context, event)

                # if preference.behavior.draw_line:
                #     utility.mesh.add_point(op, context, event)

                op.add_point = False

            pass_through = True

        elif event.type == 'MOUSEMOVE' and preference.shape.mirror_gizmo:
            pass_through = True

        elif op.operation != 'DRAW':
            op.add_point = False

        # LEFTMOUSE
        if event.type == 'LEFTMOUSE':
            # force_repeat = True in [d < 0.000001 for d in bc.lattice.dimensions[:-2]] and op.operation != 'DRAW'
            force_repeat = True in [d < 0.000001 for d in dimensions()[:-2]] and op.operation != 'DRAW'
            repeat_threshold = (op.init_mouse - op.mouse['location']).length < preference.keymap.repeat_threshold * screen.dpi_factor()

            if preference.keymap.alt_preserve and op.alt and not op.alt_skip:
                return {'PASS_THROUGH'}

            if event.value == 'PRESS':
                op.lmb = True
                op.last['mouse_click'] = op.mouse['location']
                op.alt_skip = True

                if op.operation == 'MIRROR' and preference.shape.mirror_gizmo:
                    if op.mirror_gizmo_higlight:
                        op.skip_lmb_release = True
                        return {'PASS_THROUGH'}

                if bc.shader and bc.shader.widgets.active and bc.shader.widgets.active.type != 'SNAP' and not event.ctrl:
                    widget = bc.shader.widgets.active

                    if widget.type == 'VERT' and event.shift and (ngon or boxgon):

                        ngon_point_bevel(context, event, op, widget)
                        op.update()
                        return {'RUNNING_MODAL'}

                    if (widget.operation == 'OFFSET' or widget.operation == 'EXTRUDE' and tracked_states.thin) and event.shift and not op.move_lock:
                        op.view3d['location'] = widget.location
                        utility.modal.operation.change(op, context, event, to='MOVE')

                        op.move_lock = True

                        op.update()
                        return {'RUNNING_MODAL'}

                    if widget.operation == 'EXTRUDE' and event.shift:
                        utility.modal.operation.change(op, context, event, to='TAPER')

                        op.update()
                        return {'RUNNING_MODAL'}

                    if widget.operation == 'BEVEL' and event.shift:
                        utility.modal.operation.change(op, context, event, to='SOLIDIFY')

                        op.update()
                        return {'RUNNING_MODAL'}

                    if widget.operation == 'BEVEL':
                        op.last['mouse'] = op.mouse['location']
                        bc.shape.data.bc.q_beveled = bc.q_bevel

                        utility.modal.operation.change(op, context, event, to='BEVEL', modified=True)

                        op.update()

                        utility.modal.refresh.shape(op, context, event)

                        return {'RUNNING_MODAL'}

                    if widget.operation == 'BEVEL_INSET':
                        op.last['mouse'] = op.mouse['location']
                        utility.modal.operation.change(op, context, event, to='BEVEL_INSET', modified=True)

                        return {'RUNNING_MODAL'}

                    operation = widget.operation

                    utility.modal.operation.change(op, context, event, to=operation, dot=True)

                elif not preference.keymap.repeat_single_click:
                    if op.repeat_check and repeat_threshold or force_repeat:
                        if force_repeat and '_bc_repeat' not in bpy.data.meshes:
                            add_logo(op, context,)
                            utility.data.repeat(op, context, collect=True)

                        return repeat(op, context, event)

            if event.value == 'RELEASE':
                op.lmb = False
                op.allow_menu = False
                op.alt_skip = False

                execute_in_none = op.operation == 'NONE' and op.modified

                if op.operation == 'MIRROR' and preference.shape.mirror_gizmo:
                    return {'RUNNING_MODAL'}

                if op.operation == 'BEVEL':
                    utility.modal.operation.change(op, context, event, to='NONE')

                    op.update()
                    return {'RUNNING_MODAL'}

                if op.ngon_point_index != -1:
                    # TODO: previous state store and recall (bc undo v1)
                    if (op.last['mouse_click'] - op.mouse['location']).length < context.preferences.inputs.drag_threshold_mouse * 0.2:
                        execute_in_none = True
                        op.modified_lock = False

                    else:
                        if bc.shader:
                            bc.shader.widgets.eval_shape(context, force=True)

                        if op.ngon_fit:
                            utility.lattice.fit(op, context)

                            # op.last['lattice_corner'] = utility.lattice.center(Matrix(), 'front') * 2 - Vector(bc.lattice.bound_box[op.draw_dot_index])
                            # op.last['lattice_center'] = utility.lattice.center(Matrix(), None)

                            op.bounds = [Vector(c) for c in bound_box()]

                elif op.shape_type == 'NGON':
                    mesh.remove_doubles(bc.shape)

                if preference.keymap.repeat_single_click:
                    if op.repeat_check and repeat_threshold or force_repeat:
                        if force_repeat and '_bc_repeat' not in bpy.data.meshes:
                            add_logo(op, context,)
                            utility.data.repeat(op, context, collect=True)
                        return repeat(op, context, event)

                    op.repeat_check = False

                elif not op.repeat_check:
                    op.repeat_check = True

                if op.operation == 'DRAW' and op.draw_line and op.shape_type !='NGON':
                    op.draw_line = False
                    bc.plane.matrix_world = bc.lattice.matrix_world
                    return {'RUNNING_MODAL'}

                if preference.keymap.quick_execute:
                    quick_execute = op.operation == 'DRAW' and not op.modified and not op.shape_type == 'NGON'

                else:
                    quick_execute = False

                execute_in_extrude = op.operation in {'EXTRUDE', 'OFFSET', 'TAPER'} and not op.modified

                extrude_if_unmodified = op.operation == 'DRAW' and not op.modified and op.shape_type != 'NGON' and not op.release_lock

                # overlap = False
                extrude_if_overlap = False
                add_point = False

                if op.shape_type == 'NGON':
                    # matrix = bc.shape.matrix_world
                    # enough_verts = len(bc.shape.data.vertices) > 1
                    extrude_if_overlap = op.operation == 'DRAW' and not op.modified and op.add_point
                    add_point = op.shape_type == 'NGON' and op.operation == 'DRAW' and not op.add_point

                op.alt_lock = op.rmb
                if not op.alt_lock:
                    if (quick_execute or execute_in_none or execute_in_extrude or (op.lazorcut and execute_in_none)) and not op.modified_lock:
                        if (quick_execute and not op.release_lock) and op.mode not in {'KNIFE', 'MAKE'}:
                            utility.modifier.create.boolean(op, show=True)

                        if (op.lazorcut_performed and preference.keymap.release_lock_lazorcut) or not preference.keymap.release_lock_lazorcut or (event.ctrl and op.release_lock) or not op.lazorcut or (op.mode == 'KNIFE' and preference.surface == 'VIEW'):
                            op.execute(context)

                            op.update()
                            return {'FINISHED'}

                        elif op.lazorcut and (preference.keymap.release_lock_lazorcut or (preference.keymap.release_lock and preference.keymap.quick_execute)):
                            utility.accucut(op, context)

                            if op.mode == 'KNIFE' and preference.surface != 'VIEW':
                                # context.view_layer.update()
                                # op.lazorcut_performed = True
                                op.extruded = True
                                utility.mesh.knife(op, bpy.context, None)

                            if not preference.keymap.quick_execute:
                                utility.modal.operation.change(op, context, event, to='NONE')

                    elif op.modified and not add_point or op.release_lock and op.shape_type != 'NGON':
                        op.last['operation'] = op.operation
                        utility.modal.operation.change(op, context, event, to='NONE')

                    elif extrude_if_unmodified or extrude_if_overlap or (op.add_point_lock):# or (preference.behavior.draw_line and len(bc.shape.data.vertices) > 2)):
                        op.last['mouse'] = op.mouse['location']
                        #extrude = op.mode not in {'MAKE', 'JOIN'}
                        to = 'EXTRUDE'# if extrude else 'OFFSET'

                        if op.shape_type == 'NGON' and op.release_lock:
                            to = 'NONE'

                        utility.modal.operation.change(op, context, event, to=to, modified=to == 'NONE')
                        op.lazorcut_performed = False

                    elif add_point and not op.add_point_lock:
                        op.add_point = True
                        op.last['placed_mouse'] = op.mouse['location']

            op.update()
            return {'RUNNING_MODAL'}

        # RIGHTMOUSE | BACKSPACE
        elif event.type == 'RIGHTMOUSE' or event.type == 'BACK_SPACE':

            if preference.keymap.rmb_preserve:
                return {'PASS_THROUGH'}

            removing_points = False
            if event.type == 'RIGHTMOUSE' and event.value == 'PRESS':
                op.rmb = True

            if event.type == 'RIGHTMOUSE' and event.value == 'RELEASE':
                op.rmb = False
                op.allow_menu = False

            if event.value == 'RELEASE':
                # op.modified = True
                locked = False

                if op.add_point_lock and not op.extruded:
                    if op.ngon_fit:
                        modifier.apply(bc.shape, types=['LATTICE'])
                        op.ngon_fit = False
                        op.shape_type = 'NGON'

                    if bc.shader:
                        bc.shader.widgets.active = None

                    utility.modal.operation.change(op, context, event, to='DRAW')

                ngon_draw = op.shape_type == 'NGON' and op.operation == 'DRAW'
                rmb_cancel = preference.keymap.rmb_cancel_ngon
                # last_count = 0

                if op.alt_lock or (not rmb_cancel and event.type == 'RIGHTMOUSE' and ngon_draw and len(bc.shape.data.vertices) == 2) or (rmb_cancel and event.type == 'RIGHTMOUSE' and ngon):
                    op.cancel(context)

                    op.update()
                    return {'CANCELLED'}
                    # return {'RUNNING_MODAL'}

                elif ngon and not op.extruded:
                    if event.type != 'RIGHTMOUSE' or (event.type == 'RIGHTMOUSE' and not rmb_cancel):
                        if not op.add_point and not op.add_point_lock:
                            op.add_point_lock = True
                            op.add_point = True
                            utility.mesh.remove_point(op, context, event)
                            removing_points = True

                            utility.modal.operation.change(op, context, event, to='NONE')

                        elif op.add_point_lock:
                            op.add_point_lock = False

                        # if op.add_point:# and not preference.behavior.draw_line:
                        #     utility.mesh.remove_point(op, context, event)
                        #     removing_points = True

                    # elif event.type == 'RIGHTMOUSE':
                        # utility.modal.operation.change(op, context, event, to='NONE')

                elif op.operation != 'NONE' and op.modified:
                    utility.modal.operation.change(op, context, event, to='NONE', clear_mods=[op.last['operation']] if op.last['operation'] in {'ARRAY', 'SOLIDIFY', 'BEVEL'} else [], modified=op.modified)
                    locked = True

                op.alt_lock = True if op.lmb else False
                if op.alt_lock:
                    op.modified = True

                if not locked and not removing_points and not op.alt_lock and (op.operation == 'NONE' and not op.allow_menu or not op.modified):
                    op.cancel(context)

                    op.update()
                    return {'CANCELLED'}

            op.update()
            return {'RUNNING_MODAL'}

        # MIDDLEMOUSE
        elif event.type == 'MIDDLEMOUSE':
            if event.value == 'PRESS':
                op.mmb = True

                if op.operation == 'NONE' and bc.shader and bc.shader.widgets.active and bc.shader.widgets.active.type == 'VERT' and (ngon or boxgon):

                    ngon_point_bevel(context, event, op, bc.shader.widgets.active)
                    op.update()
                    return {'RUNNING_MODAL'}

            elif event.value == 'RELEASE':
                op.mmb = False

                if op.operation == 'BEVEL' and op.ngon_point_bevel and op.ngon_point_index != -1:
                    utility.modal.operation.change(op, context, event, to='NONE')

                    op.update()
                    return {'RUNNING_MODAL'}

            op.update()
            return {'PASS_THROUGH'}

        # NDOF
        elif 'NDOF' in event.type:
            op.update()
            return {'PASS_THROUGH'}

        # WHEELUPMOUSE, EQUAL
        elif event.type in {'WHEELUPMOUSE', 'EQUAL', 'UP_ARROW', 'RIGHT_ARROW'}:
            if event.type == 'WHEELUPMOUSE' or event.value == 'PRESS':
                if event.shift and preference.keymap.scroll_adjust_circle and op.shape_type == 'CIRCLE' and op.operation not in {'BEVEL', 'ARRAY'}:
                    preference.shape.circle_vertices += 1
                    op.report({'INFO'}, F'Circle Vertices: {preference.shape.circle_vertices}')

                elif op.operation == 'BEVEL':
                    obj = bc.shape if not bc.bevel else bc.bevel
                    for mod in obj.modifiers:
                        if mod.type == 'BEVEL':
                            mod.segments += 1

                            if bc.bevel:
                                break

                            if mod.name.startswith('Quad'):
                                preference.shape['quad_bevel_segments'] = mod.segments

                            elif mod.name.startswith('Front'):
                                preference.shape['front_bevel_segments'] = mod.segments

                            else:
                                preference.shape['bevel_segments'] = mod.segments

                                op.report({'INFO'}, F'Bevel Segments: {preference.shape.bevel_segments}')


                elif op.operation == 'ARRAY':
                    for mod in bc.shape.modifiers:
                        if mod.type == 'ARRAY':
                            mod.count += 1
                            # op.last['modifier']['count'] = mod.count
                            preference.shape.array_count = mod.count
                            op.report({'INFO'}, F'Array Count: {preference.shape.array_count}')

                            break

                elif op.operation == 'GRID':
                    if event.shift:
                        preference.shape.box_grid_divisions[0] += 1

                    elif event.ctrl:
                        preference.shape.box_grid_divisions[1] += 1

                    else:
                        preference.shape.box_grid_divisions[0] += 1
                        preference.shape.box_grid_divisions[1] += 1

                elif event.alt and preference.keymap.alt_scroll_shape_type:
                    op.ngon_fit = False
                    utility.custom.cutter(op, context)

                elif event.shift and op.operation in ('NONE', 'EXTRUDE', 'OFFSET'):
                    utility.modifier.move(op, context, False)

                else:
                    op.update()
                    return {'PASS_THROUGH'}

            else:
                op.update()
                return {'PASS_THROUGH'}

        # WHEELDOWNMOUSE, MINUS
        elif event.type in {'WHEELDOWNMOUSE', 'MINUS', 'DOWN_ARROW', 'LEFT_ARROW'}:
            if event.type == 'WHEELDOWNMOUSE' or event.value == 'PRESS':
                if event.shift and preference.keymap.scroll_adjust_circle and op.shape_type == 'CIRCLE' and op.operation not in {'BEVEL', 'ARRAY'}:
                        if preference.shape.circle_vertices > 3:
                            preference.shape.circle_vertices -= 1
                            op.report({'INFO'}, F'Circle Vertices: {preference.shape.circle_vertices}')

                elif op.operation == 'BEVEL':
                    obj = bc.shape if not bc.bevel else bc.bevel
                    for mod in obj.modifiers:
                        if mod.type == 'BEVEL':
                            mod.segments -= 1

                            if bc.bevel:
                                break

                            if mod.name.startswith('Quad'):
                                preference.shape['quad_bevel_segments'] = mod.segments

                            elif mod.name.startswith('Front'):
                                preference.shape['front_bevel_segments'] = mod.segments

                            else:
                                preference.shape['bevel_segments'] = mod.segments

                                op.report({'INFO'}, F'Bevel Segments: {preference.shape.bevel_segments}')


                elif op.operation == 'ARRAY':
                    for mod in bc.shape.modifiers:
                        if mod.type == 'ARRAY':
                            mod.count -= 1
                            preference.shape.array_count = mod.count
                            op.report({'INFO'}, F'Array Count: {preference.shape.array_count}')

                            break

                elif op.operation == 'GRID':
                    if event.shift:
                        preference.shape.box_grid_divisions[0] -= 1

                    elif event.ctrl:
                        preference.shape.box_grid_divisions[1] -= 1

                    else:
                        preference.shape.box_grid_divisions[0] -= 1
                        preference.shape.box_grid_divisions[1] -= 1

                elif event.alt and preference.keymap.alt_scroll_shape_type:
                    op.ngon_fit = False
                    utility.custom.cutter(op, context, index=-1)

                elif event.shift and op.operation in ('NONE', 'EXTRUDE', 'OFFSET'):
                    utility.modifier.move(op, context, True)

                else:
                    op.update()
                    return {'PASS_THROUGH'}
            else:
                op.update()
                return {'PASS_THROUGH'}

        # elif 'CTRL' in event.type:
        #     if event.value == 'PRESS':
        #         op.widgets.exit = True

        #     elif event.value == 'RELEASE':
        #         op.widgets = shader.widgets.setup(op)

        # ESC
        elif event.type == 'ESC':
            if event.value == 'RELEASE':
                if op.allow_menu:
                    op.allow_menu = False
                    return {'PASS_THROUGH'}

                ngon_draw = op.shape_type == 'NGON' and op.operation == 'DRAW' and not op.add_point
                if op.operation == 'NONE' and not op.allow_menu or (not op.modified and (not ngon_draw or preference.behavior.draw_line)):
                    op.cancel(context)
                    op.update()
                    return {'CANCELLED'}

                elif op.operation != 'NONE':
                    remove = [op.operation] if op.operation in {'ARRAY', 'SOLIDIFY', 'BEVEL'} else []

                    if op.operation == 'ARRAY':
                        if bc.shape.bc.array_circle:
                            bc.shape.bc['array_circle'] = False

                        remove.append('DISPLACE')

                    utility.modal.operation.change(op, context, event, to='NONE', clear_mods=remove)

        # RET
        elif event.type in {'RET', 'SPACE', 'NUMPAD_ENTER'}:
            op.execute(context)

            op.update()
            return {'FINISHED'}

        # ACCENT GRAVE / TILDE
        elif event.type == 'ACCENT_GRAVE':
            if event.value == 'RELEASE':
                op.allow_menu = op.operation == 'NONE'

                if event.shift or not preference.keymap.view_pie:
                    utility.modal.rotate.by_90(op, context, event)
                elif op.allow_menu:
                    bpy.ops.wm.call_menu_pie(name='VIEW3D_MT_view_pie')

        # SHIFT OPERATION DOWN
        elif preference.keymap.shift_operation_enable and op.shape_type != 'NGON' and not event.alt and shift_pressed and hasattr(preference.keymap.shift_in_operations, op.operation.lower()) and getattr(preference.keymap.shift_in_operations, op.operation.lower()):
            op.prior_to_shift = op.operation
            utility.modal.operation.change(op, context, event, to=preference.keymap.shift_operation, modified=op.modified)

        # SHIFT OPERATION UP
        elif preference.keymap.shift_operation_enable and op.shape_type != 'NGON' and not event.alt and shift_released and op.operation == preference.keymap.shift_operation:
            utility.modal.operation.change(op, context, event, to=op.prior_to_shift, modified=op.modified)
            op.prior_to_shift = 'NONE'

        # TAB
        elif event.type == 'TAB':
            if event.value == 'RELEASE':
                op.modified = True
                op.allow_menu = False
                utility.modal.operation.change(op, context, event, to='NONE', modified=op.modified)

        # .
        elif event.type == 'PERIOD' and op.shape_type != 'NGON':
            if event.value == 'RELEASE':
                utility.modal.origin.change(op, context, event, to='CENTER' if op.origin == 'CORNER' else 'CORNER')
                # st3_simple_notification(F'{op.origin}')

        # 1, 2, 3
        elif event.type in {'ONE', 'TWO', 'THREE'}:
            if event.value == 'RELEASE':
                axis = {
                    'ONE': 'X',
                    'NUMPAD_1': 'X',
                    'TWO': 'Y',
                    'NUMPAD_2': 'Y',
                    'THREE': 'Z',
                    'NUMPAD_3': 'Z'}

                if op.operation == 'MIRROR' and preference.shape.mirror_gizmo:
                    index = 'XYZ'.index(axis[event.type])
                    bpy.ops.bc.gizmo_click_toggle(axis_index=index, flip=event.shift)

                elif op.operation != 'SOLIDIFY':
                    if not op.mirrored:
                        for i in range(3):
                            bc.mirror_axis[i] = 0
                            bc.mirror_axis_flip[i] = 0

                        op.mirrored = True

                    utility.modal.mirror.shape(op, context, event, to=axis[event.type], flip=event.shift)

                elif not op.mode == 'INSET':
                    for mod in bc.shape.modifiers:
                        if mod.type == 'SOLIDIFY':
                            mod.offset = -1 if event.type == 'ONE' else 1
                            mod.offset = 0 if event.type == 'TWO' else mod.offset

        # A
        elif event.type == 'A':
            if event.value == 'RELEASE':
                utility.modal.mode.change(op, context, event, to='MAKE')

        # B
        elif event.type == 'B' and (op.shape_type != 'NGON' or len(bc.shape.data.vertices) > 2) and op.shape_type != 'CUSTOM':
            if event.value == 'RELEASE':

                if event.shift and op.operation == 'GRID':
                    preference.shape.box_grid_border = not preference.shape.box_grid_border
                    op.report({'INFO'}, F'Border:  {"ON" if preference.shape.box_grid_border else "OFF"}')

                else:
                    op.last['mouse'] = op.mouse['location']
                    bc.shape.data.bc.q_beveled = bc.q_bevel

                    utility.modal.operation.change(op, context, event, to='BEVEL', clear_mods=[] if op.operation != 'BEVEL' else ['BEVEL'], modified=True)

        # C
        elif event.type == 'C':
            if event.value == 'RELEASE' and (op.mode != 'INSET' or not preference.behavior.inset_bevel):
                if op.shape_type == 'NGON' and op.operation == 'DRAW':# and not preference.behavior.draw_line:
                    preference.shape.cyclic = not preference.shape.cyclic

                    if len(bc.shape.data.vertices) > 2:
                        utility.mesh.remove_point(op, context, event)
                        utility.mesh.add_point(op, context, event)

                    op.report({'INFO'}, F'{"En" if preference.shape.cyclic else "Dis"}abled Cyclic')

                elif op.shape_type != 'NGON':# or preference.behavior.draw_line:
                    if utility.custom.cutter(op, context, index=1):
                        op.ngon_fit = False

        # D
        elif event.type == 'D':
            # if event.value == 'RELEASE':
            op.allow_menu = op.operation == 'NONE'

            if op.allow_menu and not event.shift and not event.alt:
                op.update()
                return {'PASS_THROUGH'}

            elif event.alt and event.value == 'RELEASE':
                preference.display.dots = not preference.display.dots
                # widgets.exit = True

                # if preference.display.dots:
                #     widgets = shader.widgets.setup(op)

                # utility.modal.dots.collect(op)

                # if preference.display.dots:
                #     op.dots = shader.widgets.setup(op, context)
                text = F'{"En" if preference.display.dots else "Dis"}abled Dots'
                op.report({'INFO'}, text)
                # st3_simple_notification(text)

        # E
        elif event.type == 'E':
            if event.value == 'RELEASE':
                if event.alt:
                    op.alt_e = True
                    preference.behavior.boolean_solver = 'EXACT' if 'EXACT' != preference.behavior.boolean_solver else 'FAST'
                    # op.start_exact = preference.behavior.boolean_solver == 'EXACT'
                    text = F'Solver: {preference.behavior.boolean_solver.capitalize()}'
                    op.report({'INFO'}, text)
                    # st3_simple_notification(text)

                else:
                    mode = 'OFFSET' if op.operation == 'EXTRUDE' else 'EXTRUDE'
                    utility.modal.operation.change(op, context, event, to=mode)

        # F
        elif event.type == 'F':
            if event.shift and op.shape_type != 'NGON':
                if event.value == 'RELEASE':
                    op.flip_z = not op.flip_z
                    utility.modal.flip.shape(op, context, event)
                    # st3_simple_notification(F'Flip Z')

            elif event.value == 'RELEASE':
                bc.flip = not bc.flip

                if op.operation == 'EXTRUDE':
                    utility.modal.operation.change(op, context, event, to='OFFSET')

                elif op.operation == 'OFFSET':
                    utility.modal.operation.change(op, context, event, to='EXTRUDE')

        # G
        elif event.type == 'G':
            if event.value == 'RELEASE':
                # utility.modal.move.invoke(op, context, event)
                if event.shift and op.shape_type == 'BOX'and not op.ngon_fit:
                    if op.operation != 'GRID':
                        utility.modal.operation.change(op, context, event, to='GRID')

                    else:
                        utility.modal.operation.change(op, context, event, to='NONE')
                        if preference.shape.box_grid:
                            preference.shape.box_grid = False

                else:
                    utility.modal.operation.change(op, context, event, to='MOVE')

        # H
        elif event.type == 'H':
            if event.value == 'RELEASE':
                preference.display.wire_only = not preference.display.wire_only

        # I
        elif event.type == 'I':
            if event.value == 'RELEASE':
                utility.modal.mode.change(op, context, event, to='INSET')

        # O
        elif event.type == 'O':
            if event.value == 'RELEASE':
                utility.modal.operation.change(op, context, event, to='OFFSET')

        # J
        elif event.type == 'J':
            if event.value == 'RELEASE':
                utility.modal.mode.change(op, context, event, to='JOIN')

        # K
        elif event.type == 'K':
            if event.value == 'RELEASE':
                if addon.hops() and op.mode == 'KNIFE' and (event.shift or event.alt):
                    preference.behavior.hops_mark = not preference.behavior.hops_mark
                    op.report({'INFO'}, F'{"En" if preference.behavior.hops_mark else "Dis"}abled HOps Marking')
                else:
                    utility.modal.mode.change(op, context, event, to='KNIFE')

        # L
        elif event.type == 'L':
            if event.value == 'RELEASE':
                preference.behavior.show_shape = not preference.behavior.show_shape
                preference.behavior.autohide_shapes = not preference.behavior.show_shape
                op.report({'INFO'}, F'Shape is{"nt" if not preference.behavior.show_shape else ""} live')

        # M TODO: object material link type (obj.material_slots[i].link)
        elif event.type == 'M':
            if event.value == 'RELEASE' and op.mode in {'CUT', 'SLICE', 'INSET'}:
                wm = context.window_manager
                hops = wm.Hard_Ops_material_options if hasattr(wm, 'Hard_Ops_material_options') else False

                if not len(bpy.data.materials[:]):
                    hops = False

                if hops and bpy.data.materials[:]:
                    if not hops.active_material:
                        hops.active_material = bpy.data.materials[0].name

                    active_material = bpy.data.materials[hops.active_material]
                    active_index = bpy.data.materials[:].index(active_material)

                    hops.active_material = bpy.data.materials[active_index - 1].name

                    if hops.active_material != active_material.name:
                        bc.shape.data.materials.clear()

                        if op.mode not in {'SLICE', 'INSET', 'KNIFE', 'EXTRACT'}:
                            bc.shape.data.materials.append(bpy.data.materials[hops.active_material])

                            if op.mode != 'MAKE':
                                for obj in op.datablock['targets']:
                                    mats = [slot.material for slot in obj.material_slots if slot.material]

                                    obj.data.materials.clear()

                                    for index, mat in enumerate(mats):
                                        if not index or (mat != active_material or mat in op.existing[obj]['materials']):
                                            obj.data.materials.append(mat)

                                    if bpy.data.materials[hops.active_material] not in obj.data.materials[:]:
                                        obj.data.materials.append(bpy.data.materials[hops.active_material])

                        elif op.mode in {'SLICE', 'INSET'}:
                            for obj in op.datablock['targets']:
                                mats = [slot.material for slot in obj.material_slots if slot.material]

                                obj.data.materials.clear()

                                for index, mat in enumerate(mats):
                                    if not index or (mat != active_material or mat in op.existing[obj]['materials']):
                                        obj.data.materials.append(mat)

                                if op.mode == 'INSET' and bpy.data.materials[hops.active_material] not in obj.data.materials[:]:
                                    obj.data.materials.append(bpy.data.materials[hops.active_material])

                            for obj in op.datablock['slices']:
                                obj.data.materials.clear()
                                obj.data.materials.append(bpy.data.materials[hops.active_material])

                            for obj in op.datablock['insets']:
                                obj.data.materials.append(bpy.data.materials[hops.active_material])
                                mats = [slot.material for slot in obj.material_slots]
                                index = mats.index(bpy.data.materials[hops.active_material])

                                for mod in obj.modifiers:
                                    if mod.type == 'SOLIDIFY':
                                        mod.material_offset = index

                                        break
        # Q
        elif event.type == 'Q':
            if event.value == 'RELEASE' and op.operation == 'BEVEL':
                bc.q_back_only = event.shift and bc.q_bevel
                bc.q_bevel = not bc.q_bevel
                # bc.shape.data.bc.q_beveled = bc.q_bevel

                # for mod in bc.shape.modifiers:
                #     if mod.type == 'BEVEL':
                #         preference.shape.bevel_segments = mod.segments
                #         bc.shape.modifiers.remove(mod)

                # utility.modal.bevel.shape(op, context, event)

        # R
        elif event.type == 'R':
            if event.value == 'RELEASE':
                if event.shift:
                    if op.operation not in {'NONE', 'DRAW', 'EXTRUDE', 'OFFSET'}:
                        op.last['thickness'] = -0.1
                        op.last['angle'] = 0.0
                        op.last['modifier']['thickness'] = -0.01
                        op.last['modifier']['offset'] = 0.01
                        op.last['modifier']['count'] = 2
                        op.last['modifier']['segments'] = 6
                        op.last['modifier']['bevel_width'] = 0.02
                        op.last['modifier']['front_bevel_width'] = 0.02
                        op.last['modifier']['quad_bevel_width'] = 0.02

                        if ngon or boxgon:
                            for vindex in op.geo['indices']['offset']:
                                vert = bc.shape.data.vertices[vindex]

                                if op.ngon_point_index != -1 and vert.index != op.ngon_point_index:
                                    continue

                                utility.mesh.index_weight(vindex, vert=True, value=0)

                            op.last['vert_weight'] = [0 for w in op.last['vert_weight'][:]]

                            for eindex in op.geo['indices']['mid_edge']:
                                edge = bc.shape.data.edges[eindex]

                                if op.ngon_point_index != -1 and op.ngon_point_index not in edge.vertices:
                                    continue

                                utility.mesh.index_weight(eindex, value=0)

                            # op.ngon_point_bevel = False

                        op.last['mouse'] = op.mouse['location']

                        if op.operation == 'TAPER':
                            preference.shape.taper = 1.0


                    else:
                        utility.modal.rotate.by_90(op, context, event)
                        # st3_simple_notification(F'Rotate 90°')

                elif event.ctrl and op.operation == 'NONE':
                    utility.modal.rotate.by_90_shape(op, context)

                else:
                    # utility.modal.rotate.invoke(op, context, event)
                    utility.modal.operation.change(op, context, event, to='ROTATE')

        # S
        elif event.type == 'S':
            if event.value == 'RELEASE':
                # utility.modal.scale.invoke(op, context, event)
                utility.modal.operation.change(op, context, event, to='SCALE')

        # T
        elif event.type == 'T':
            if event.value == 'RELEASE':
                if event.shift:
                    if preference.keymap.shift_operation_enable and preference.keymap.shift_operation == 'TAPER':
                        if preference.shape.taper != 1.0:
                            preference.shape.taper = 1.0

                            if op.operation == 'TAPER':
                                utility.modal.operation.change(op, context, event, to=op.prior_to_shift, modified=op.modified)

                    else:
                        if op.operation == 'TAPER':
                            preference.shape.taper = 1.0
                        utility.modal.operation.change(op, context, event, to='TAPER')

                else:
                    utility.modal.operation.change(op, context, event, to='SOLIDIFY', clear_mods=[] if op.operation != 'SOLIDIFY' else ['SOLIDIFY'])

        # V
        elif event.type == 'V':
            if event.value == 'RELEASE':
                to = 'ARRAY'
                remove = [] if op.operation != 'ARRAY' else ['ARRAY']

                if bc.shape.bc.array_circle:
                    bc.shape.bc['array_circle'] = False
                    to = 'NONE'
                    remove = ('DISPLACE', 'ARRAY')

                utility.modal.operation.change(op, context, event, to=to, clear_mods=remove)

        # W
        elif event.type == 'W':
            if event.value == 'RELEASE':

                if op.wedge_check:
                    bc.wedge_slim = not bc.wedge_slim
                    preference.shape.wedge = False

                elif preference.shape.wedge:
                    op.wedge_cycle += 1
                    bc.wedge_slim = not bc.wedge_slim

                    if op.wedge_cycle > 1:
                        op.wedge_cycle = 0
                        preference.shape.wedge = False

                else:
                    preference.shape.wedge = True

                op.wedge_check = False

                utility.lattice.wedge(op, context)

                # if op.shape_type == 'NGON' and preference.behavior.draw_line:
                #     preference.shape.wedge = not preference.shape.wedge
                #     op.report({'INFO'}, F'{"En" if preference.shape.wedge else "Dis"}abled Wedge')

                # if op.shape_type != 'NGON':
                # preference.shape.wedge = not preference.shape.wedge
                # wedge_points = []
                # other_points =[]

                # for i in utility.lattice.back:
                #     if i in op.wedge_sets[preference.shape.wedge_side]:
                #         wedge_points.append(bc.lattice.data.points[i])
                #     else:
                #         other_points.append(bc.lattice.data.points[i])

                # if wedge_points:
                #     for wedge_point, other_point in zip(wedge_points, other_points):
                #         wedge_point.co_deform.z = bc.lattice.data.points[utility.lattice.front[0]].co_deform.z - 0.0001
                #         other_point.co_deform.z = op.start['extrude']

        # X, Y, Z
        elif event.type in {'X', 'Y', 'Z'}:
            if event.type == 'Z' and event.alt or event.shift:
                op.update()
                return {'PASS_THROUGH'}

            if event.value == 'RELEASE':
                if op.shape_type == 'NGON' and op.operation == 'DRAW' and event.type == 'Z' and event.ctrl:
                    utility.mesh.remove_point(op, context, event)

                elif op.operation in {'NONE', 'DRAW', 'EXTRUDE', 'OFFSET', 'BEVEL', 'SOLIDIFY'}:
                    if event.type == 'X':
                        if not event.ctrl:
                            if op.mode == 'SLICE' and event.alt:
                                preference.behavior.recut = not preference.behavior.recut
                                prefix = 'En' if preference.behavior.recut else 'Dis'
                                op.report({'INFO'}, F'{prefix}abling Recut')

                            elif op.mode == 'INSET' and event.alt and not bc.bevel:
                                preference.behavior.inset_slice = not preference.behavior.inset_slice
                                prefix = 'En' if preference.behavior.recut else 'Dis'
                                op.report({'INFO'}, F'{prefix}abling Slice')

                            elif not event.alt:
                                to = 'CUT' if op.mode != 'CUT' else 'SLICE'
                                if op.mode == 'SLICE':
                                    to = 'INTERSECT'
                                elif op.mode == 'INTERSECT':
                                    to = 'INSET'
                                elif op.mode == 'INSET':
                                    to = 'CUT'
                                utility.modal.mode.change(op, context, event, to=to)
                        elif not bc.bevel:
                            utility.modal.mode.change(op, context, event, to='KNIFE')

                    elif event.type == 'Y':
                        utility.modal.mode.change(op, context, event, to='EXTRACT')

                    elif event.type == 'Z':
                        for obj in op.datablock['targets']:
                            if obj in op.datablock['wire_targets']:
                                continue

                            obj.show_wire = not obj.show_wire
                            obj.show_all_edges = obj.show_wire

                elif op.operation in {'MOVE', 'ROTATE', 'SCALE'}:
                    utility.modal.axis.change(op, context, to=event.type)

                utility.modal.refresh.shape(op, context, event)
                op.update()
                return {'RUNNING_MODAL'}

        # ;
        elif event.type == 'SEMI_COLON':
            if event.value == 'RELEASE':
                if op.operation != 'MIRROR':
                    preference.shape.mirror_gizmo = True
                else:
                    preference.shape.mirror_gizmo = False

        elif op.operation == 'NONE' and event.type not in {'ONE', 'TWO', 'THREE', 'FOUR', 'FIVE'}:
            op.update()
            return {'PASS_THROUGH'}

        op.snap = preference.snap.enable and event.ctrl

        utility.modal.refresh.shape(op, context, event)

    elif within_region_tool_header or preference.debug:
        pass_through = True

    if pass_through:

        op.update()
        return {'PASS_THROUGH'}

    op.update()
    return {'RUNNING_MODAL'}
