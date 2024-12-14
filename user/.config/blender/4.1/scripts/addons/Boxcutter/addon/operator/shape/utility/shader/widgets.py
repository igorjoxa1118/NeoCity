from time import time
from math import cos, sin

import bpy
import gpu

from bpy.types import SpaceView3D

from mathutils import Vector, geometry

# from ... utility import dimensions
from .. import bound_box as _bound_box
from ..... import shader
from ...... utility import method_handler, addon, screen, view3d, math


class display_handler:
    display: bool = False
    operation: str = 'NONE'

    exit: bool = False
    force_exit: bool = False


    @staticmethod
    def init_alpha(widget, time_in, time_out):
        widget.fade = bool(time_in) or bool(time_out)
        widget.fade_time_start = time()
        widget.fade_time = time_in * 0.001
        widget.fade_type = 'IN' if bool(time_in) else 'NONE'


    @staticmethod
    def update_alpha(widget, limit, time_out):
        alpha = 1.0

        if widget.fade_time and widget.fade_type != 'NONE':
            alpha = (time() - widget.fade_time_start) / widget.fade_time

        if widget.fade_type == 'IN':
            alpha = alpha if alpha < 1.0 else 1.0

            if alpha == 1.0:
                widget.fade_type = 'NONE'

        elif widget.fade_type == 'OUT':
            alpha = 1.0 - alpha if alpha < 1.0 else 0.0

            if alpha == 0.0:
                widget.fade_type = 'NONE'
                widget.fade = False

        elif widget.fade_type == 'NONE' and widget.exit:
            widget.fade_time_start = time()
            widget.fade_time = time_out * 0.001

            widget.fade_type = 'OUT'
            alpha = widget.alpha

        widget.alpha = alpha * limit if not widget.exit or (widget.exit and widget.fade) else 0.0


    @staticmethod
    def area_tag_redraw(context, type='VIEW_3D'):
        for area in context.screen.areas:
            if area.type != type:
                continue

            area.tag_redraw()


    def __init__(self, context, mouse):
        self.active = None
        self.mouse = Vector((mouse.x, mouse.y))
        self.fade = True
        self.shape = None
        self.widgets = widgets(self, context)

        self._eval_block = False


    def eval_shape(self, context, force=False):
        bc = context.scene.bc

        if bc.running and bc.operator.shape_type not in {'BOX', 'NGON'} and not bc.operator.ngon_fit:
            return

        if not hasattr(bc.shape, 'modifiers'):
            self.shape = type('shape', (), {'vertices': []})

            return

        if not hasattr(self, 'shape') or bc.operator.operation == 'NONE' and not self._eval_block or self.widgets.handler or force:
            self._eval_block = bc.operator.operation == 'NONE'

            for mod in bc.shape.modifiers[:]:
                if mod.type in {'BEVEL', 'ARRAY', 'SOLIDIFY', 'SCREW', 'MIRROR', 'WELD'}:
                    mod.show_viewport = False

            new_vert = lambda v: type('vertex', (), {'co': v.co.xyz, 'index': v.index})
            evl = bc.shape.evaluated_get(context.evaluated_depsgraph_get())
            self.shape = type('shape', (), {
                'vertices': [new_vert(v) for v in evl.data.vertices],
                'dimensions': Vector(evl.dimensions[:]),
                'bound_box': [Vector(b) for b in evl.bound_box],
                })

            for mod in bc.shape.modifiers:
                mod.show_viewport = True


    def update(self, context, mouse):
        if not context.region_data:
            self.remove(force=True)

            return

        if self.exit:
            self.remove()

        else:
            self.mouse = Vector((mouse.x, mouse.y))

        self.widgets.update(self, context)
        self.active = self.widgets.active

        self.fade = self.widgets.fade

        self.area_tag_redraw(context)


    def remove(self, force=False):
        self.obj = None
        self.mesh = None

        self.widgets.exit = True

        if force:
            self.widgets.remove(force=True)


class widgets:
    active = None
    operation: str = 'NONE'

    exit: bool = False

    @staticmethod
    def _widget_location(handler, type, index=-1):
        preference = addon.preference()
        bc = bpy.context.scene.bc
        op =  bc.operator

        if not bc.running or not hasattr(op, 'draw_dot_index'):
            return None

        matrix = bc.shape.matrix_world
        draw_index = op.draw_dot_index

        bound_box = [Vector(v) for v in _bound_box(lattice=True)]

        displace = [m for m in bc.shape.modifiers if m.type == 'DISPLACE']

        if displace:
            mod = displace[0]
            i = 'XYZ'.index(mod.direction) # should always be an axis

            for v in bound_box:
                v[i] += mod.strength

        vert_locations = [Vector((round(w.location.x, 1), round(w.location.y, 1), round(w.location.z, 1))) for w in handler.widgets.handler if w.type == 'VERT']
        draw_point = bound_box[draw_index]
        # max_dimension = max(bc.lattice.dimensions[:-1])
        max_dimension = max((preference.shape.dimension_x, preference.shape.dimension_y))

        if type == 'DRAW':
            if Vector((round(draw_point.x, 1), round(draw_point.y, 1), round(draw_point.z, 1))) in vert_locations:
                offset = 0.05 * max_dimension

                draw_point.x -= -offset if draw_index in {5, 6} else offset
                draw_point.y -= -offset if draw_index in {2, 6} else offset

            return draw_point

        elif type in {'OFFSET', 'EXTRUDE'}:
            side = [(1, 2, 5, 6), (0, 3, 4, 7)][::-1 if type != 'OFFSET' else 1]
            return 0.25 * math.vector_sum([bound_box[i] for i in side[op.inverted_extrude]])

        elif type == 'DISPLACE':
            indices = (4, 5, 6, 7) if draw_index in {5, 6} else (0, 1, 2, 3)
            return 0.25 * math.vector_sum([bound_box[i] for i in indices])

        elif type == 'BEVEL':
            index_keys = {1: 7, 2: 4, 5: 3, 6: 0}
            offset = 0.05 * max_dimension

            location = bound_box[index_keys[draw_index if draw_index in index_keys.keys() else 1]]
            location.x -= offset if draw_index in {5, 6} else -offset
            location.y -= offset if draw_index in {2, 6} else -offset

            # if bc.lattice.dimensions[2] > preference.shape.offset:
            if preference.shape.dimension_z > preference.shape.offset:
                location.z -= offset

            return location

        elif type == 'BEVEL_INSET':
            index_keys = {1: 7, 2: 4, 5: 3, 6: 0}
            offset = 0.15 * max_dimension

            location = bound_box[index_keys[draw_index if draw_index in index_keys.keys() else 1]]
            location.x -= offset if draw_index in {5, 6} else -offset
            location.y -= offset if draw_index in {2, 6} else -offset

            # if bc.lattice.dimensions[2] > preference.shape.offset:
            if handler.shape and handler.shape.dimensions[2] > preference.shape.offset:
                location.z -= offset

            return location

        elif type == 'VERT':
            if index == -1:
                snap = preference.snap
                snap = snap.enable and snap.grid and snap.increment

                indices = op.geo['indices']['extrusion'] if op.extruded or (op.shape_type == 'BOX' and not op.ngon_fit) else []

                valid = lambda v: v.index in indices if op.inverted_extrude and not snap else not v.index in indices

                return [vert for vert in handler.shape.vertices if valid(vert)]

            elif not handler.exit and index < len(handler.shape.vertices):
                return handler.shape.vertices[index].co

        elif type == 'SNAP':
            ngon_last_enabled = len(bc.shape.data.vertices) > 1 and not preference.shape.lasso and ((op.ctrl and not preference.snap.angle_lock) or (not op.ctrl and preference.snap.angle_lock))

            if not ngon_last_enabled or len(bc.shape.data.vertices) < 3 or (op.ngon_point_index == -1 and op.shape_type == 'BOX' and not op.ngon_fit):
                return None

            ngon_angle = 0.017453292519943295 * preference.snap.ngon_angle
            angle45 = 0.017453292519943295 * (45 if op.shape_type == 'NGON' and not op.ngon_fit else 15)

            if op.ngon_point_index > len(bc.shape.data.vertices):
                op.ngon_point_index = 0

            index = op.ngon_point_index

            n = index + 1 if index + 1 < len(bc.shape.data.vertices) else 0
            anchor = bc.shape.data.vertices[n].co.xy

            current = bc.shape.data.vertices[index].co.xy
            previous = bc.shape.data.vertices[index-1].co.xy

            previous_edge_angle = 0.0

            if preference.snap.ngon_previous_edge:
                previous_edge_angle = (previous - bc.shape.data.vertices[index-2].co.xy).angle_signed(Vector((1, 0)), 0.0)

            if op.shape_type == 'BOX' and not op.ngon_fit:
                previous_edge_angle = 0.0
                for i in op.geo['indices']['offset']:
                    if i == index:
                        continue

                    for key in bc.shape.data.edge_keys:
                        if i not in key:
                            continue

                        if index in key:
                            anchor = bc.shape.data.vertices[i].co.xy
                            anchor_index = i
                            break

                for i in op.geo['indices']['offset']:
                    if i == index:
                        continue

                    for key in bc.shape.data.edge_keys:
                        if i not in key:
                            continue

                        if index in key and anchor_index not in key:
                            previous = bc.shape.data.vertices[i].co.xy
                            break

            delta = current - previous
            angle = round((delta.angle_signed(Vector((1, 0)), 0.0) - previous_edge_angle) / ngon_angle) * ngon_angle + previous_edge_angle

            direction = Vector((cos(angle), sin(angle)))
            projection = previous + delta.project(direction)

            location = Vector((projection.x, projection.y, bc.shape.data.vertices[index].co.z))

            delta = location.xy - anchor
            angle = round((delta.angle_signed(Vector((1, 0)), 0.0) - previous_edge_angle) / angle45) * angle45 + previous_edge_angle

            direction45 = Vector((cos(angle), sin(angle)))

            factor = 1000
            intersect = geometry.intersect_line_line_2d(
                anchor + delta.project(direction45) * factor,
                anchor - delta.project(direction45) * factor,
                previous - delta.project(direction) * factor,
                previous + delta.project(direction) * factor)

            if intersect:
                intersect_location = matrix @ Vector((intersect.x, intersect.y, location.z))
                position = view3d.location3d_to_location2d(intersect_location)

                point = matrix @ Vector((projection.x, projection.y, location.z))
                point_position = view3d.location3d_to_location2d(point)

                if (point_position - position).length < preference.keymap.ngon_last_line_threshold * screen.dpi_factor() * 6:
                    return Vector((intersect.x, intersect.y, location.z))

            snap_widget = [w for w in handler.widgets.handler if w.type == 'SNAP']
            if snap_widget and snap_widget[-1].distance < preference.keymap.ngon_last_line_threshold * screen.dpi_factor() * 6:
                return snap_widget[-1].location

        return None


    def _enabled_types(self, bc):
        preference = addon.preference()

        enabled_types = []
        op = bc.operator

        if not bc.running:
            return enabled_types

        if op.operation == 'NONE' and not op.ctrl:
            enabled_types = ['DRAW', 'EXTRUDE']

            if not bc.shader or not bc.shader.thin:
                enabled_types.append('OFFSET')

            if bc.shape and bc.shape.modifiers:
                types = [mod.type for mod in bc.shape.modifiers]

                if 'DISPLACE' in types:
                    enabled_types.append('DISPLACE')

            if (op.shape_type in {'BOX', 'NGON'} or op.ngon_fit) and not preference.shape.lasso and not preference.shape.box_grid:
                enabled_types.append('VERT')

            if not preference.shape.lasso and not preference.shape.box_grid:
                enabled_types.append('BEVEL')

            if not preference.shape.lasso and op.mode == 'INSET':
                enabled_types.append('BEVEL_INSET')

        if op.operation == 'DRAW' and (op.shape_type in {'BOX', 'NGON'} or op.ngon_fit) and (op.ngon_point_index != -1 or op.shape_type == 'NGON'):
            enabled_types.append('SNAP')

        return enabled_types


    def _validate_widgets(self, context, handler, types):
        preference = addon.preference()
        bc = context.scene.bc

        if not preference.display.dots:
            types = []

        available = [w.type for w in self.handler if not w.exit]
        for type in types:
            if type not in available:
                location = self._widget_location(handler, type)

                if not location:
                    continue

                if type == 'BEVEL_INSET':
                    self.handler.append(point(handler, context, type, location, preference.color.dot_bevel, use_shader='inset_bevel'))
                    self.handler[-1].operation = 'BEVEL_INSET'
                    self.handler[-1].size = 1.25

                    continue

                elif isinstance(location, list):
                    for vert in location:
                        self.handler.append(point(handler, context, type, vert.co, preference.color.dot_vert, use_shader='vert'))
                        self.handler[-1].operation = 'DRAW'
                        self.handler[-1].index = vert.index

                    continue

                if type == 'BEVEL' and bc.bevel:
                    continue

                self.handler.append(point(handler, context, type, location if location else Vector(), preference.color.dot if type != 'BEVEL' else preference.color.dot_bevel if type != 'SNAP' else preference.color.snap_point))
                self.handler[-1].operation = type

                if self.handler[-1].type == 'SNAP':
                    self.handler[-1].size = 0.5

                elif self.handler[-1].type == 'BEVEL':
                    self.handler[-1].size = 1.25

        for widget in self.handler:
            if widget.type not in types or not bc.running:
                widget.exit = True


    def __init__(self, handler, context):
        self.handler = []

        self.fade = True

        self._types = []

        self.update(handler, context)


    def update(self, handler, context):
        preference = addon.preference()
        bc = context.scene.bc
        op = bc.operator

        self.active = None
        self.operation = 'NONE'

        self.handler = [w for w in self.handler if w.handler] # flushes
        self.fade = bool(len(self.handler))

        if self.exit:
            self.remove()

        if not hasattr(handler, 'widgets'):
            return

        handler.eval_shape(context)
        self._validate_widgets(context, handler, self._enabled_types(bc))

        for widget in self.handler:
            widget.highlight = False

            location = self._widget_location(handler, widget.type, index=widget.index)
            position = view3d.location3d_to_location2d(widget.transform @ widget.location)
            widget.distance = (position - handler.mouse).length if position else 1024

            if widget.location == location:
                continue

            if not location:
                widget.exit = True

                continue

            widget.location = location
            widget.transform = bc.shape.matrix_world
            widget.build_batch = True

        valid = [widget for widget in self.handler if not widget.exit]
        distances = [widget.distance for widget in valid]

        if distances:
            closest = valid[distances.index(min(distances))]
            closest.highlight = closest.distance < preference.display.dot_size * screen.dpi_factor() * preference.display.dot_factor * (2 if closest.type != 'SNAP' else 0.5) and not closest.exit

            if closest.highlight and not self.exit:
                self.active = closest
                self.operation = closest.operation

        for widget in self.handler:
            widget.update(handler, context)


    def remove(self, force=False):
        remove = []
        for index, handler in enumerate(self.handler):
            handler.exit = True

            if force:
                remove.append(index)

        for index in remove:
            if self.handler[index].handler:
                self.handler[index].remove(force=True)


class point:
    size: float = 1.0

    operation: str = 'NONE'
    index: int = -1

    highlight: bool = False
    distance: float = 0.0

    build_batch: bool = True

    exit: bool = False


    def __init__(self, handler, context, type, location, color, use_shader='point'):
        preference = addon.preference()

        self.type = type

        self.location = location
        self._dot_color = color

        handler.init_alpha(self, preference.display.dot_fade_time_in, preference.display.dot_fade_time_out)

        self.update(handler, context)

        self._time = time()
        self._shader = shader.new(F'{use_shader}.vert', F'{use_shader}.frag', script=True)
        self._build_batch = True

        shader.handlers.append(self)

        self.handler = SpaceView3D.draw_handler_add(self._draw_handler, (), 'WINDOW', 'POST_VIEW')


    def update(self, handler, context):
        preference = addon.preference()
        bc = context.scene.bc

        if self.exit:
            self.remove()

        if not self.exit and bc.running:
            self.transform = bc.shape.matrix_world.copy()

        self._size = preference.display.dot_size * screen.dpi_factor()
        self._size *= self.size * 1 if not self.highlight else self.size * 1.5

        if self.type == 'SNAP':
            self._color = preference.color.snap_point if not self.highlight else preference.color.snap_point_highlight
            self._outline = preference.color.snap_point[:-1] if not self.highlight else preference.color.snap_point_highlight[:-1]

        else:
            self._color = self._dot_color if not self.highlight else preference.color.dot_highlight[:]
            self._outline = [0.0, 0.0, 0.0] if not self.highlight else self._color[:-1]

        handler.update_alpha(self, (self._color[-1] / (1 if not self.highlight else 2)) if self.type == 'VERT' else self._color[-1], preference.display.dot_fade_time_out)


    def _draw_handler(self):
        method_handler(self._draw,
            identifier = 'Point Draw',
            exit_method = self.remove,
            return_result = False)


    def _draw(self):
        if not self.handler:
            return

        region_data = bpy.context.region_data

        self._shader.bind()

        self._shader.uniform_float('projection', region_data.window_matrix @ region_data.view_matrix @ self.transform)

        self._shader.uniform_float('color', [*self._color[:-1], self.alpha])
        self._shader.uniform_float('outline', self._outline)

        if self.build_batch:
            self._batch = shader.batch(self._shader, 'POINTS', {'vert': [self.location]})
            self.build_batch = False

        gpu.state.blend_set('ALPHA')
        gpu.state.point_size_set(self._size)

        self._batch.draw(self._shader)

        gpu.state.point_size_set(1)
        gpu.state.blend_set('NONE')


    def remove(self, force=False):
        if self.handler and (not self.fade or force):
            self.fade = False
            self.handler = SpaceView3D.draw_handler_remove(self.handler, 'WINDOW')

            shader.handlers = [handler for handler in shader.handlers if handler != self]
