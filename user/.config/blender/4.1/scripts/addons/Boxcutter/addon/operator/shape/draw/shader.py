import bpy

from mathutils import Vector

from bpy.types import Operator, SpaceView3D
from bpy.props import BoolProperty

from .. utility import shader, statusbar
from .. utility import tracked_events, tracked_states
from ..... utility import addon, method_handler


class BC_OT_shader(Operator):
    bl_idname = 'bc.shader'
    bl_label = 'Shader'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'INTERNAL'}


    def _invoke(self, context, event):
        bc = context.scene.bc

        bc.__class__.shader = self

        self.timer = None
        self.exit = False

        self.shape = None
        self.widgets = None

        self.update_states()

        self.shape = shader.shape.setup(self)
        self.widgets = shader.widgets.display_handler(context, Vector((event.mouse_region_x, event.mouse_region_y)))

        # tracked_states.widgets = self.widgets

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


    def invoke(self, context, event):
        return method_handler(self._invoke,
                 arguments = (context, event),
                 identifier = 'SHADER INVOKE',
                 exit_method = self.remove,
                 exit_arguments = (True, ))


    def _modal(self, context, event):
        preference = addon.preference()
        bc = context.scene.bc

        if not self.timer:
            self.timer = context.window_manager.event_timer_add(1 / preference.display.update_fps, window=context.window)

        if not bc.running or self.exit or self.cancelled:
            bc.__class__.shader = None

            if self.cancelled or not (self.shape.fade or self.widgets.fade):
                self.remove(force=True)

                return {'CANCELLED'}

            self.shape.exit = True
            self.widgets.exit = True

            self.update(context, event)

            if not self.exit:
                clear_states()
                self.exit = True

        elif event.type == 'TIMER':
            self.update(context, event)

        return {'PASS_THROUGH'}


    def modal(self, context, event):
        return method_handler(self._modal,
                 arguments = (context, event),
                 identifier = 'SHADER MODAL',
                 exit_method = self.remove,
                 exit_arguments = (True, ))


    def update(self, context, event):
        if not self.exit:
            self.update_states()

        self.shape.update(self, context)
        self.widgets.update(context, Vector((event.mouse_region_x, event.mouse_region_y)))

        # if context.area:
        #     context.area.tag_redraw()


    def update_states(self):
        self.mouse = tracked_events.mouse

        self.mode = tracked_states.mode
        self.operation = tracked_states.operation
        self.shape_type = tracked_states.shape_type
        self.origin = tracked_states.origin
        self.rotated = tracked_states.rotated
        self.scaled = tracked_states.scaled
        self.cancelled = tracked_states.cancelled

        self.rmb_lock = tracked_states.rmb_lock
        self.modified = tracked_states.modified
        self.bounds = tracked_states.bounds
        self.thin = tracked_states.thin
        self.draw_dot_index = tracked_states.draw_dot_index
        self.lazorcut = tracked_states.lazorcut


    def remove(self, force=False):
        bc = bpy.context.scene.bc

        bc.__class__.shader = None

        if self.shape and self.shape.handler:
            self.shape.remove()

        if self.widgets:
            self.widgets.remove(force=force)

        if self.timer:
            bpy.context.window_manager.event_timer_remove(self.timer)

        return {'CANCELLED'}


def clear_states():
    tracked_states.widgets = None

    tracked_states.mode = 'CUT'
    tracked_states.operation = 'NONE'
    tracked_states.shape_type = 'BOX'
    tracked_states.rotated = False
    tracked_states.scaled = False
    tracked_states.cancelled = False

    tracked_states.rmb_lock = False
    tracked_states.modified = False
    tracked_states.bounds = []
    tracked_states.thin = False
    tracked_states.draw_dot_index = 0
    tracked_states.lazorcut = False
    tracked_states.extruded = False
