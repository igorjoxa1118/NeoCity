import string

import bpy

from mathutils import Vector

from bpy.types import Operator

from .. shape.utility.shader import snap, snap_alt
from .... utility import method_handler, tool, addon

pass_through_key_events = set(string.ascii_uppercase + string.ascii_lowercase + string.digits + string.punctuation)


class BC_OT_shape_snap(Operator):
    bl_idname = 'bc.shape_snap'
    bl_label = 'Snap'
    bl_options = {'INTERNAL'}


    @classmethod
    def poll(cls, context):
        active_object = context.active_object

        return tool.active().idname == tool.name and addon.preference().snap.enable


    def __init__(self):
        self.invoke_method = invoke
        self.modal_method = modal
        self.exit_method = exit

        preference = addon.preference()
        if (not preference.snap.grid and preference.snap.static_dot) or (preference.snap.grid and preference.snap.static_grid):
            self.invoke_method = snap_alt.invoke
            self.modal_method = snap_alt.modal
            self.exit_method = snap_alt.exit


    def invoke(self, context, event):
        return method_handler(self.invoke_method,
            arguments = (self, context, event),
            identifier = 'Invoke',
            exit_method = self.exit,
            exit_arguments = (context, ))


    def modal(self, context, event):
        return method_handler(self.modal_method,
            arguments = (self, context, event),
            identifier = 'Modal',
            exit_method = self.exit,
            exit_arguments = (context, ))


    def exit(self, context):
        return method_handler(self.exit_method,
            arguments = (self, context),
            identifier = 'Exit')


def invoke(op, context, event):
    preference = addon.preference()
    bc = context.scene.bc

    if bc.running or (bc.snap.operator and (hasattr(bc.snap.operator, 'handler') and not bc.snap.operator.handler.exit)):
        return {'CANCELLED'}

    bc.snap.__class__.operator = op

    if preference.keymap.enable_toolsettings:
        context.space_data.show_region_tool_header = True
        context.space_data.show_region_header = True

    op._update = True
    op._timer = None

    op._ignore_escape = False

    op._adaptive = preference.snap.adaptive

    op.handler = None
    op.handler = snap.display_handler(context, Vector((event.mouse_region_x, event.mouse_region_y)))

    preference.snap.adaptive = op._adaptive if not preference.snap.increment_lock else False

    op._timer = context.window_manager.event_timer_add(1 / preference.display.update_fps, window=context.window)
    context.window_manager.modal_handler_add(op)

    return {'RUNNING_MODAL'}


def modal(op, context, event):
    preference = addon.preference()
    bc = context.scene.bc

    op.handler.micro = event.shift

    preference.snap.adaptive = True if event.ctrl and preference.snap.increment_lock else op._adaptive

    valid_operation = not bc.running or (bc.operator.operation in {'DRAW', 'MOVE', 'ROTATE', 'SCALE'} and op.handler.grid.display)
    increment_lock = preference.snap.increment_lock and preference.snap.grid # TODO: increment_lock -> lock
    display = (event.ctrl and not preference.snap.grid and valid_operation) or (event.ctrl and not increment_lock and valid_operation) or (increment_lock and (not bc.running or (not event.ctrl and valid_operation)))

    if not bc.running and (not event.ctrl and (not preference.snap.grid or not preference.snap.increment_lock)):
        op.handler.exit = True
        op.handler.fade = op.handler.fade and bc.snap.display

    if op._update:
        bc.snap.display = display and (not preference.keymap.alt_preserve or (not event.alt or event.type != 'LEFTMOUSE'))

    if event.type in {'D', 'V'}:
        op._ignore_escape = True

    if not bc.running and ((event.type not in {'C', 'D', 'V', 'Z'} and event.type in pass_through_key_events or event.type in {'ZERO', 'ONE', 'TWO', 'THREE', 'FOUR', 'FIVE'}) or (event.type == 'ESC' and not op._ignore_escape)) or (event.type == 'SPACE' and event.ctrl):
        bc.snap.display = False

        op._update = False

        op.handler.remove(force=True)
        op.handler.area_tag_redraw(context)

        op.handler.exit = True
        op.handler.fade = False

        return {'PASS_THROUGH'}

    if event.type == 'ESC' and op._ignore_escape:
        op._ignore_escape = False

    if op.handler.grid.display and 'WHEEL' in event.type and event.ctrl:
        increment = preference.snap.increment
        direction = event.type[5:-5]

        if round(preference.snap.increment, 2) == 0.25:
            if direction == 'UP':
                preference.snap.increment = 0.2

            else:
                preference.snap.increment = 0.3

            increment = preference.snap.increment

        if increment < 1:
            if increment >= 0.1:
                if direction == 'UP':
                    preference.snap.increment = 0.1 * (increment / 0.1) + 0.1

                elif 0.1 * (increment / 0.1) - 0.1 >= 0.1:
                    preference.snap.increment = 0.1 * (increment / 0.1) - 0.1

                else:
                    preference.snap.increment = 0.09

            else:
                if direction == 'UP':
                    preference.snap.increment = 0.01 * (increment / 0.01) + 0.01

                elif 0.01 * (increment / 0.01) - 0.01 >= 0.01:
                    preference.snap.increment = 0.01 * (increment / 0.01) - 0.01

                else:
                    preference.snap.increment = 0.01

        else:
            if direction == 'UP':
                preference.snap.increment = (increment / 1) + 1

                if preference.snap.increment > 10:
                    preference.snap.increment = 10

            else:
                if (increment / 1) - 1 >= 1:
                    preference.snap.increment = (increment / 1) - 1

                else:
                    preference.snap.increment = 0.9

        if round(preference.snap.increment, 2) == 0.11:
            preference.snap.increment = 0.2

        text = F'Grid Size: {preference.snap.increment:.2f}'
        op.report({'INFO'}, text)

        return {'RUNNING_MODAL'}

    if event.type == 'TIMER' and op._update:
        op.handler.update(context, Vector((event.mouse_region_x, event.mouse_region_y)))

    elif op._timer and not op._update:
        bpy.context.window_manager.event_timer_remove(op._timer)

        op._timer = None

        op.handler.exit = True
        op.handler.fade = False

    if op.handler.exit and not op.handler.fade:
        return op.exit(context)

    return {'PASS_THROUGH'}


def exit(op, context):
    preference = addon.preference()
    bc = context.scene.bc

    bc.snap_type = ''

    op._update = False

    if op.handler:
        op.handler.remove(force=True)
        op.handler.area_tag_redraw(context)

    if bc.snap.operator and bc.snap.operator != op:
        bc.snap.operator.exit(context)

    from .... utility import handled_error
    if bc.snap.operator == op or handled_error:
        bc.snap.__class__.operator = None
        bc.snap.hit = False
        bc.snap.display = False
        bc.snap.type = ''
        bc.snap.location = Vector()

    if op._timer:
        bpy.context.window_manager.event_timer_remove(op._timer)
        op._timer = None

    preference.snap.adaptive = op._adaptive

    return {'FINISHED'}
