from time import time
from math import radians

import bpy
import bmesh
import gpu

from bpy.types import SpaceView3D

from mathutils import Vector, Matrix
from mathutils.geometry import closest_point_on_tri

from .. modal.ray import view_matrix, surface_matrix, planar_matrix

from ..... import shader
from ..... import toolbar
from ...... utility import method_handler, addon, screen, view3d, ray, math


class display_handler:
    micro: bool = False
    local: bool = True

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

        widget.alpha = alpha * limit if bpy.context.scene.bc.snap.display or (widget.exit and widget.fade) else 0.0


    @staticmethod
    def area_tag_redraw(context, type='VIEW_3D'):
        for area in context.screen.areas:
            if area.type != type:
                continue

            area.tag_redraw()


    def __init__(self, context, mouse):
        preference = addon.preference()
        bc = context.scene.bc

        self.mouse = Vector((mouse.x, mouse.y))
        self.offset = Vector()
        self.face_index = -1

        self.fade = True

        self.grid: type = type('GridNull', tuple(), dict(display=False, update=lambda *_: None, fade=False, exit=True, remove=lambda *_, **__: None))
        self.sub_grid: type = type('GridNull', tuple(), dict(display=False, update=lambda *_: None, fade=False, exit=True, remove=lambda *_, **__: None))

        self.obj = None
        self.obj_name = ''
        self.obj_dimensions = [2, 2, 2]
        self.obj_matrix = Matrix()
        self.eval = False

        self.view_transform = context.region_data.view_rotation.to_matrix().to_4x4()

        self.normal = Vector((0, 0, -1))

        active = context.active_object and context.active_object.type == 'MESH'
        selected = context.selected_objects

        hit = False

        if active and preference.surface != 'VIEW':
            hit = self._ray_cast(context)

        if preference.surface == 'OBJECT' and hit:
            self.type = 'OBJECT'
            self._surface_matrix()

        elif preference.surface == 'VIEW' or not hit and active and selected:
            self.type = 'VIEW'

            self.location, self.normal, self.matrix = view_matrix(context, *self.mouse)

        elif preference.surface == 'CURSOR':
            self.type = 'CURSOR'
            self._cursor_matrix()

        elif preference.surface == 'WORLD' or not selected or not active:
            self.type = 'WORLD'

            matrix = planar_matrix(context)

            self.location = matrix.translation
            self.normal = matrix @ Vector((0, 0, -1))
            self.matrix = matrix

        types = {
            'GRID': preference.snap.grid,
            'VERT': preference.snap.verts,
            'EDGE': preference.snap.edges,
            'FACE': preference.snap.faces}

        types_enabled = [t for t in types if types[t]] if not preference.snap.grid and hit else ['GRID']

        fallback = Vector() if self.type != 'CURSOR' else context.scene.cursor.location
        self._offset(self.obj.location if self.obj and self.type != 'CURSOR' else fallback)

        if 'GRID' in types_enabled:
            self.grid = grid(self, context)
            self.sub_grid = grid(self, context)
            self.sub_grid.main = False

        self.points = points(self, context, types_enabled)

        bc.snap_type = self.type


    def update(self, context, mouse):
        preference = addon.preference()
        bc = context.scene.bc

        if self.obj_name not in context.scene.objects:
            self.obj = None

        elif self.obj_name:
            self.obj = context.scene.objects[self.obj_name]

        if not context.region_data:
            self.remove(force=True)

            return

        view_transform = context.region_data.view_rotation.to_matrix().to_4x4()
        cursor_location = context.scene.cursor.location

        if self.exit:
            self.remove()

        else:
            self.mouse = Vector((mouse.x, mouse.y))

            if not bc.running:
                if self.obj and ((self.eval and bc.snap.display and not self.grid.display) or (self.type not in {'VIEW', 'CURSOR', 'WORLD'} and (not self.grid.display or (preference.snap.adaptive and bc.snap.display)))):
                    if self.eval and bc.snap.display:
                        self._eval_obj(context, self.obj)
                        self.eval = False

                    if self._ray_cast(context):
                        self._surface_matrix()
                        self._offset(self.obj.location)

            if not bc.snap.display and not self.eval:
                self.eval = True

        if self.view_transform != view_transform:
            self.view_transform = view_transform

            if self.type == 'VIEW':
                self.location, self.normal, self.matrix = view_matrix(context, *self.mouse)
                self._offset(self.obj.location if self.obj else Vector())

        if self.type == 'CURSOR' and self.location != cursor_location:
            self._cursor_matrix()
            self._offset(cursor_location)

        self.grid.update(self, context)
        self.sub_grid.update(self, context)
        self.points.update(self, context)

        self.fade = self.grid.fade or self.points.fade

        bc.snap_type = self.type

        self.area_tag_redraw(context)


    def _ray_cast(self, context):
        preference = addon.preference()

        hit = False
        location = Vector()
        normal = Vector()
        face_index = -2
        obj = None
        last_object = self.obj

        if toolbar.option() and toolbar.option().active_only:
            hit, location, normal, face_index, obj, _ = ray.cast(*self.mouse, selected=True)

            if hit and self.obj != obj:
                self._eval_obj(context, obj)

        elif context.active_object and context.selected_objects:
            if self.obj != context.active_object or 'invalid' in str(self.mesh):
                self._eval_obj(context, context.active_object)

            bm = bmesh.new()
            bm.from_mesh(self.mesh)

            hit, location, normal, face_index = ray.cast(*self.mouse, bmesh_data=bm)
            obj = context.active_object

            bm.free()

        if hit and face_index != self.face_index and ((self.grid.display and preference.snap.adaptive or not self.grid.display) or obj != last_object):
            self.location = location
            self.normal = normal if round(normal.dot(self.normal), 3) != 1 else self.normal
            self.face_index = face_index

        else: hit = False

        return hit


    def _eval_obj(self, context, obj):
        bc = context.scene.bc

        self.obj = obj
        self.obj_name = obj.name
        self.obj_matrix = obj.matrix_world

        evl = obj.evaluated_get(context.evaluated_depsgraph_get())

        self.obj_dimensions = evl.dimensions[:]

        if obj.modifiers:
            self.mesh = evl.data.copy()
        else:
            self.mesh = obj.data.copy()

        self.mesh.transform(self.obj_matrix)
        self.mesh.bc.removeable = True


    def _surface_matrix(self):
        preference = addon.preference()

        matrix = self.obj_matrix.decompose()[1].to_matrix().to_4x4()

        orient_method = 'EDIT' if self.obj.mode == 'EDIT' and preference.behavior.orient_active_edge else preference.behavior.orient_method
        self.matrix = surface_matrix(self.obj, matrix, self.location, self.normal, Vector(), orient_method if preference.snap.grid else 'LOCAL', self.face_index)[1]


    def _cursor_matrix(self):
        preference = addon.preference()

        axis = {
            'X': 'Y',
            'Y': 'X',
            'Z': 'Z'}
        angle = radians(-90 if preference.axis in {'X', 'Y'} else 90)

        cursor = bpy.context.scene.cursor
        matrix = cursor.rotation_euler.to_matrix().to_4x4()

        rotation = Matrix.Rotation(angle, 4, axis[preference.axis])
        matrix @= rotation

        self.location = cursor.location.copy()
        self.normal = Vector((0, 0, -1))
        self.matrix = matrix


    def _offset(self, location):
        preference = addon.preference()

        if not self.local or not self.obj:
            return

        matrix = self.matrix.copy() if self.type != 'VIEW' else self.view_transform.copy()

        size = 1000
        triangle = [
            matrix @ Vector((-size, -size, 0.0)),
            matrix @ Vector((size, -size, 0.0)),
            matrix @ Vector((0.0, size, 0.0))]

        loc = closest_point_on_tri(location, *triangle)

        increment = preference.snap.increment

        nearest_increment = lambda n: increment * (n // increment)
        increment_offset = lambda v: Vector((a - nearest_increment(a) for a in v))

        offset = increment_offset(matrix.inverted() @ loc)
        offset.z = 0.0
        self.offset = offset.copy()

        offset = matrix @ offset

        self.view_transform.translation = offset

        if self.type != 'VIEW' and preference.snap.grid:
            self.matrix.translation = offset


    def remove(self, force=False):
        self.obj = None
        self.mesh = None

        self.eval = False

        self.grid.exit = True
        self.sub_grid.exit = True
        self.points.exit = True

        if force:
            self.grid.remove(force=True)
            self.sub_grid.remove(force=True)
            self.points.remove(force=True)


class grid:
    main: bool = True
    exit: bool = False
    display: bool = True


    def __init__(self, handler, context):
        preference = addon.preference()

        handler.init_alpha(self, preference.display.grid_fade_time_in, preference.display.grid_fade_time_out)

        self._color = Vector(preference.color.grid_wire[:])

        self._count = preference.snap.grid_units
        self._increment = preference.snap.increment

        self._size = 0.0
        self._indices = ((0, 1, 3), (0, 3, 2))
        self._uv = ((-1, -1), (1, -1), (-1, 1), (1, 1))

        self._offset = handler.offset

        self.update(handler, context)

        self._time = time()
        self._shader = shader.new('grid.vert', 'grid.frag', script=True)
        self._build_batch = True

        shader.handlers.append(self)

        self.handler = SpaceView3D.draw_handler_add(self._draw_handler, (), 'WINDOW', 'POST_VIEW')


    def update(self, handler, context):
        preference = addon.preference()

        if self.exit:
            self.remove()

        else:
            transform = handler.matrix if handler.type != 'VIEW' else handler.view_transform
            intersect = view3d.intersect_plane(*handler.mouse, handler.location, transform)

            check = ['X', 'Y', 'Z']

            while not intersect:
                if not len(check):
                    return

                axis = check.pop()
                transform = transform @ Matrix.Rotation(radians(90), 4, axis)
                intersect = view3d.intersect_plane(*handler.mouse, handler.location, transform)

            else:
                self.transform = transform
                self.intersect = intersect

                if handler.matrix != self.transform:
                    handler.matrix = self.transform

            self._count = preference.snap.grid_units if preference.snap.grid else 0
            self._increment = preference.snap.increment
            self._update_size()

            self._offset = handler.offset

        handler.update_alpha(self, self._color[-1], preference.display.grid_fade_time_out)

        self._thickness = 1 if not preference.display.thick_wire else 1.8
        self._thickness *= preference.display.wire_width


    def _update_size(self):
        preference = addon.preference()

        size = self._count * self._increment
        if self._size != size:
            self._size = size

            offset = self._size * 0.5
            offset_z = 0.0 # preference.shape.offset # TODO: intersect calc needs offset
            self._frame = tuple([tuple([offset * self._uv[i][j] if j < 2 else offset_z for j in range(3)]) for i in range(4)])

            self._build_batch = True


    def _draw_handler(self):
        method_handler(self._draw,
            identifier = 'Grid Draw',
            exit_method = self.remove,
            return_result = False)


    def _draw(self):
        preference = addon.preference()

        if not self.handler or not preference.snap.grid or not hasattr(self, '_frame'):
            return

        region_data = bpy.context.region_data

        self._shader.bind()

        self._shader.uniform_float('projection', region_data.window_matrix @ region_data.view_matrix @ self.transform)
        self._shader.uniform_float('intersect', self.intersect - self._offset)

        self._shader.uniform_float('count', self._count if self.main else self._count * 10)
        self._shader.uniform_float('size', self._size)
        self._shader.uniform_float('thickness', self._thickness)

        alpha = self.alpha if self.main else self.alpha * 0.15
        self._shader.uniform_float('color', [*self._color[:-1], alpha])

        if self._build_batch:
            self._batch = shader.batch(self._shader, 'TRIS', {'frame': self._frame}, indices=self._indices)
            self._build_batch = False

        gpu.state.blend_set('ALPHA')

        self._batch.draw(self._shader)

        gpu.state.blend_set('NONE')


    def remove(self, force=False):
        if self.handler and (not self.fade or force):
            self.fade = False
            self.handler = SpaceView3D.draw_handler_remove(self.handler, 'WINDOW')

            shader.handlers = [handler for handler in shader.handlers if handler != self]


class points:
    active = None

    exit: bool = False


    @staticmethod
    def _grid_intersect(handler, increment):
        intersect = handler.grid.intersect - handler.offset
        return Vector((*math.increment_round_2d(*intersect[:-1], increment), intersect[2]))


    @staticmethod
    def _reset_point(handler, point):
        preference = addon.preference()

        point.exit = False

        handler.init_alpha(point, preference.display.dot_fade_time_in, preference.display.dot_fade_time_out)


    def __init__(self, handler, context, types):
        preference = addon.preference()

        self._type = types
        self.handler = []

        self.fade = True
        self.face_index = handler.face_index

        if 'GRID' in self._type:
            self.handler.append(point(handler, context, 'GRID', self._grid_intersect(handler, preference.snap.increment)))
            self.active = self.handler[0]

        else:
            self._init_face_points(handler, context)

        self.update(handler, context)


    def _init_face_points(self, handler, context):
        face = handler.mesh.polygons[handler.face_index]
        locations = [point.location for point in self.handler]

        if 'VERT' in self._type:
            for index in face.vertices:
                location = handler.matrix.inverted() @ handler.mesh.vertices[index].co

                if location in locations:
                    self._reset_point(handler, self.handler[locations.index(location)])

                    continue

                self.handler.append(point(handler, context, 'VERT', location))

        if 'EDGE' in self._type:
            for index, key in enumerate(face.edge_keys):
                vert1 = handler.mesh.vertices[key[0]].co
                vert2 = handler.mesh.vertices[key[1]].co

                location = handler.matrix.inverted() @ ((vert1 + vert2) / 2)

                if location in locations:
                    self._reset_point(handler, self.handler[locations.index(location)])

                    continue

                self.handler.append(point(handler, context, 'EDGE', location))
                self.handler[-1].edge_index = index

        if 'FACE' in self._type:
            location = handler.matrix.inverted() @ face.center

            if location in locations:
                self._reset_point(handler, self.handler[locations.index(location)])

                return

            self.handler.append(point(handler, context, 'FACE', location))


    def update(self, handler, context):
        preference = addon.preference()
        bc = context.scene.bc

        self.handler = [point for point in self.handler if point.handler]
        self.fade = bool(len(self.handler))

        if self.exit:
            self.remove()

        intersect = view3d.intersect_plane(*handler.mouse, handler.location, handler.matrix)

        for point in self.handler:
            point.highlight = False
            position = view3d.location3d_to_location2d(point.transform @ point.location)
            point.distance = (position - handler.mouse).length if position else 1024

            if point.type == 'GRID' and not point.exit:
                intersect = None
                location = self._grid_intersect(handler, preference.snap.increment if not handler.micro else preference.snap.increment * 0.1)

                if point.location == location:
                    continue

                point.location = location
                point.build_batch = True

            elif self.face_index != handler.face_index:
                point.exit = True

        if not self.exit and self.face_index != handler.face_index:
            self.face_index = handler.face_index
            self._init_face_points(handler, context)

        distances = [point.distance for point in self.handler]

        if distances:
            closest = self.handler[distances.index(min(distances))]
            closest.highlight = closest.distance < preference.display.snap_dot_size * screen.dpi_factor() * preference.display.snap_dot_factor * 2 if closest.type != 'GRID' else True

            if closest.highlight and not self.exit:
                self.active = closest

                bc.snap.hit = True
                bc.snap.type = closest.type
                bc.snap.location = closest.transform @ closest.location
                bc.snap.normal = handler.normal if closest.type != 'GRID' else closest.transform @ Vector((0, 0, -1))

                rot_mat = handler.obj_matrix.decompose()[1].to_matrix().to_4x4()
                bc.snap.matrix = closest.transform if closest.type == 'GRID' or handler.obj_name not in bpy.data.objects else surface_matrix(handler.obj, rot_mat, handler.location, Vector(bc.snap.normal[:]), Vector(bc.snap.location[:]), face_index=handler.face_index)

            elif bc.snap.hit and self.active:
                bc.snap.hit = False
                bc.snap.type = ''
                bc.snap.location = Vector()
                bc.snap.normal = Vector()
                bc.snap.matrix = Matrix()

                self.active = None

        for point in self.handler:
            point.update(handler, context)

            if not intersect:
                continue

            max_dim = 2

            if handler.obj:
                max_dim = max(handler.obj_dimensions[:])

            region_fade = 1.0 - (point.location - intersect).length / max_dim

            if region_fade < 0.0:
                region_fade = 0.0

            point.alpha *= region_fade


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
    exit: bool = False

    highlight: bool = False
    distance: float = 0.0

    build_batch: bool = True


    def __init__(self, handler, context, type, location):
        preference = addon.preference()

        self.type = type

        self.location = location

        handler.init_alpha(self, preference.display.dot_fade_time_in, preference.display.dot_fade_time_out)

        self.update(handler, context)

        self._time = time()
        self._shader = shader.new('point.vert', 'point.frag', script=True)
        self._build_batch = True

        shader.handlers.append(self)

        self.handler = SpaceView3D.draw_handler_add(self._draw_handler, (), 'WINDOW', 'POST_VIEW')


    def update(self, handler, context):
        preference = addon.preference()

        if self.exit:
            self.remove()

        if not self.exit:
            self.transform = handler.matrix if self.type != 'GRID' else handler.grid.transform

        self._size = preference.display.snap_dot_size * screen.dpi_factor()
        self._size *= 1 if not self.highlight or self.type == 'GRID' else 1.5

        self._color = preference.color.snap_point[:]
        self._outline = (0.1, 0.1, 0.1) if not self.highlight else preference.color.snap_point_highlight[:-1]

        handler.update_alpha(self, self._color[-1], preference.display.dot_fade_time_out)


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
