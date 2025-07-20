import math, sys
import bpy, bmesh
from mathutils import Vector, Matrix, geometry
from bpy_extras.view3d_utils import region_2d_to_origin_3d, region_2d_to_vector_3d, location_3d_to_region_2d
import numpy

import gpu
from gpu_extras.batch import batch_for_shader

from ...... utility import addon, tool, screen
from ...... utility.math import coordinates_dimension, coordinates_center
from .. modal import ray

class grid_handler():
    grid_draw_offset = 0.0
    surface_offset_vector = Vector((0, 0, 0.002))

    grid_color = [0, 0, 0, 1]
    plane_color = [0.6, 0, 0, 0.3]
    border_color = grid_color
    border_f_color = grid_color.copy()

    plane_verts = []
    plane_verts_base = [
        Vector((-0.5,-0.5, grid_draw_offset)),
        Vector(( 0.5,-0.5, grid_draw_offset)),
        Vector((-0.5, 0.5, grid_draw_offset)),
        Vector(( 0.5, 0.5, grid_draw_offset))]

    plane_uvs = [
        Vector((0, 0)),
        Vector((1, 0)),
        Vector((0, 1)),
        Vector((1, 1))]

    plane_indices = [(1, 3, 2), (0, 1, 2)]
    border_idices = [(0, 1), (0, 2), (2, 3), (1, 3)]

    grid_thickness = 1.2

    center_vert = Vector((0,0,0))

    nearest_dot = None

    dot_wire_id = None
    dot_wire_co = None

    dot_size = 10
    dot_size_high = 2
    dot_snap_radius = dot_size * 0.5

    dot_colors = {
    'VERT': (1, 1, 1, 1), 'VERT_HIGH': (1, 0, 0, 1),
    'EDGE': (1, 1, 1, 1), 'EDGE_HIGH': (1, 0, 0, 1),
    'FACE': (1, 1, 1, 1), 'FACE_HIGH': (1, 0, 0, 1),
    }

    grid_vert_count = -1
    grid_verts = []
    grid_ids = []

    alignment_matrix = Matrix()
    init_alignment_matrix = Matrix()
    scale_matrix = Matrix()
    snap_world = Vector((0, 0, 0))
    frozen = False
    rotation_snap = 15
    rotation_axis = 'Z'
    rotation_keep_normal = True

    snapable_types = {'MESH', 'CURVE', 'SURFACE', 'FONT', 'META'}
    selection_only = True
    alignment = 'NEAREST'
    fit_precision = 0.01

    draw = True
    draw_dots = True
    draw_dots_wire = True
    dot_alignment = {'VERT', 'EDGE', 'FACE'}
    dot_alignment_ignore_flat = True
    dot_preview = True
    dot_preview_size = 0.05
    dot_preview_scale = 1
    enabled_dots = frozenset(('VERT', 'EDGE', 'FACE'))

    cast_override = None
    active_mesh_edge = False

    front_draw = False

    _unit = Vector((0.5, 0.5))
    unit_face_fit = _unit.copy()
    _divisions = 1
    _dot_divisions = 1

    _count = Vector((1, 1))

    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, val):
        if val == self._mode:
            return

        if val == 'MOVE' and self.snap_type != 'DOTS' and not self.frozen:
            self.mouse_warp(bpy.context)

        self.sync_matrices()
        self._mode = val

        if val == 'ROTATE':
            self.origin_ref = self.origin.copy()
            self.direction_ref = self.direction.copy()

    @property
    def divisions(self):
        return self._divisions

    @divisions.setter
    def divisions(self, val):
        val = int(val)
        val = val if val > 0 else 1
        if val == self.divisions : return

        self._divisions = int(val)
        self.grid_data_update()

    @property
    def dot_divisions(self):
        return self._dot_divisions

    @dot_divisions.setter
    def dot_divisions(self, val):
        val = int(val)
        val = val if val >= 0 else 0
        if val == self._dot_divisions : return

        self._dot_divisions = val
        self.nearest_dot = None
        self.create_dots()

    @property
    def unit(self):
        return self._unit

    @unit.setter
    def unit(self, val):
        self._unit.x = abs(val[0])
        self._unit.y = abs(val[1])

        self.grid_data_update()


    @property
    def count(self):
        return self._count

    @count.setter
    def count(self, val):
        self._count.x = abs(int(val[0]))
        self._count.y = abs(int(val[1]))

        if self._count.x < 1:
            self._count.x = 1

        if self._count.y < 1:
            self._count.y = 1

        self.grid_data_update()

    @property
    def snap_type(self):
        return self._snap_type

    @snap_type.setter
    def snap_type(self, val):
        types = {'GRID', 'DOTS', 'BOTH'}
        if val not in types:
           raise ValueError(F'Type must be in {types}')

        self._snap_type = val


    @classmethod
    def snap_vec_xy(self, vec, val=(1, 1)):
        x = val[0]
        y = val[1]

        vec.x = round(vec.x / x) * x if x else vec.x
        vec.y = round(vec.y / y) * y if y else vec.y
        vec.z = 0

        return vec


    def __init__(self, context, event, snap_type='BOTH', snapable_types={}, selection_only=True, alignment='NEAREST', override_matrix=Matrix(), divisions=2, grid_units=[0.5, 0.5], cell_count=[1, 1], surface_offset=0.005, cast_override=None, enabled_dots={'VERT', 'EDGE', 'FACE'}, dot_alignment={'VERT', 'EDGE', 'FACE'}, dot_alignment_ignore_flat=True, active_mesh_edge=False, dot_divisions = 0, dot_colors=None, draw_dots_wire=True):
        self._mode = 'MOVE' if snap_type != 'DOTS' else 'NONE'

        divisions = int(divisions)
        dot_divisions = int(dot_divisions)
        self._divisions = divisions if divisions > 0 else 1
        self._dot_divisions = dot_divisions if dot_divisions >= 0 else 0

        self._unit = Vector(grid_units)
        self._count = Vector(cell_count)

        self.snap_type = snap_type
        self.alignment = alignment
        self.draw_dots_wire = draw_dots_wire

        self.selection_only = selection_only
        self.dot_alignment = dot_alignment
        self.surface_offset_vector = Vector((0,0, surface_offset))
        self.enabled_dots = enabled_dots
        self.cast_override = cast_override
        self.dot_alignment_ignore_flat = dot_alignment_ignore_flat
        self.active_mesh_edge = active_mesh_edge
        self.dot_handler = None

        self.wire_shader = uniform_shader.compile()
        self.grid_shader = Grid_shader.compile()
        self.cursor_dot_shader = flat_point_outline.compile()

        if dot_colors is not None:
            self.dot_colors = dot_colors

        self.initialized = False
        self.running = False

        if snapable_types:
            self.snapable_types = snapable_types

        self.region = context.region
        self.region_3d = context.space_data.region_3d

        self.mouse = Vector((event.mouse_region_x, event.mouse_region_y))
        self.intersect = Vector((0, 0, 0))

        self.mouse_input()

        if alignment == 'OVERRIDE':
            loc, rot, sca = override_matrix.decompose()
            self.alignment_matrix = Matrix.Translation(loc) @ rot.to_matrix().to_4x4()
            self.init_alignment_matrix = override_matrix.copy()
            self.scale_matrix = Matrix.Diagonal((*sca, 1))

            self.snap_type = 'GRID'

        elif alignment.startswith('WORLD'):
            #self.align_face(context)
            self.initialized = True
            char = alignment[-1]

            if char == 'Z':
                matrix = Matrix()

            elif char == 'X':
                matrix = Matrix.Rotation(math.radians(90), 4, 'Y')

            elif char == 'Y':
                matrix = Matrix.Rotation(math.radians(90), 4, 'X')

            matrix.translation = matrix @ self.surface_offset_vector
            self.init_alignment_matrix = matrix
            self.alignment_matrix = matrix

            self.snap_type = 'GRID'

        else:
            self.initialized = self.align_face(context)
            if not self.initialized:

                return

        self.initialized = True
        self.snap_matrix = self.alignment_matrix @ self.scale_matrix

        self.draw_handler_3d = bpy.types.SpaceView3D.draw_handler_add(draw_callback_3d, (self, context), 'WINDOW', 'POST_VIEW')

    def start(self, context, event):
        self.running = True
        self.create_dots()
        self.update(context, event)

    def purge(self):
        handler_3d = getattr(self, 'draw_handler_3d', False)

        if handler_3d:
            bpy.types.SpaceView3D.draw_handler_remove(self.draw_handler_3d, 'WINDOW')

            self.draw_handler_3d = None

        if self.dot_handler:
            self.dot_handler.purge()


    def update(self, context, event):
        self.mouse = Vector((event.mouse_region_x, event.mouse_region_y))

        areas = [area for area in context.screen.areas if area.type == 'VIEW_3D']

        for area in areas:
            area_mouse_x = event.mouse_x - area.x
            area_mouse_y = event.mouse_y - area.y

            if 0 < area_mouse_x < area.width and 0 < area_mouse_y < area.height:
                space_data = area.spaces.active
                self.region_3d = space_data.region_3d

                for region in area.regions:
                    region_mouse_x = event.mouse_x - region.x
                    region_mouse_y = event.mouse_y - region.y
                    if region.type == 'WINDOW' and 0 < region_mouse_x < region.width and 0 < region_mouse_y < region.height:
                        self.mouse.x = region_mouse_x
                        self.mouse.y = region_mouse_y
                        self.region = region

                        break

                if space_data.region_quadviews:
                    if area_mouse_x < area.width / 2:
                        i = 1 if area_mouse_y > area.height / 2 else 0

                    else:
                        i = 3 if area_mouse_y > area.height / 2 else 2

                    self.region_3d = space_data.region_quadviews[i]
                break

        self.mouse_input()
        self.nearest_dot = None

        if self.snap_type in {'BOTH', 'DOTS'}:
            if self.draw and self.draw_dots:

                self.dot_handler.update(context, event)

                self.nearest_dot = self.dot_handler.active_dot

                if self.snap_type == 'DOTS':
                    self.snap_world = self.intersect_tri(self.snap_matrix)

                    if self.nearest_dot:
                        self.snap_matrix = self.nearest_dot.matrix @ self.scale_matrix

                        if self.draw and self.draw_dots:
                            self.snap_world = self.snap_matrix.translation

                    return

            else:
                self.snap_matrix = self.alignment_matrix.copy()
                self.snap_matrix.translation = self.snap_world = self.intersect_tri(self.alignment_matrix)

                if self.snap_type == 'DOTS':
                    return


        if self.mode == 'NONE':
            vec = self.snap_matrix.inverted() @ self.intersect_tri(self.snap_matrix)
            self.snap_world = self.snap_matrix @ self.snap_vec_xy(vec, self.unit / self.divisions) if self.draw else self.snap_matrix @ vec


        elif self.mode == 'MOVE' :
            matrix = self.alignment_matrix @ self.scale_matrix

            vec = matrix.inverted() @ self.intersect_tri(self.alignment_matrix)
            if not event.shift:
                self.snap_vec_xy(vec, self.unit / self.divisions)

            else:
                vec.z = 0

            self.snap_matrix = matrix @ Matrix.Translation(vec)
            self.snap_world = self.snap_matrix.translation

            if self.nearest_dot:
                self.snap_matrix = self.nearest_dot.matrix @ self.scale_matrix

        elif self.mode == 'ROTATE':
            matrix = self.init_alignment_matrix.copy()
            matrix.translation = self.alignment_matrix.translation

            input_matrix = matrix
            ref_vec = Vector((1,0))

            if self.rotation_axis == 'X':
                input_matrix = matrix @ Matrix.Rotation(math.radians(90), 4, 'Y')
                ref_vec = Vector((0, 1))

            elif self.rotation_axis == 'Y':
                input_matrix = matrix @ Matrix.Rotation(math.radians(90), 4, 'X')
                ref_vec = Vector((1, 0))

            input_matrix_inv = input_matrix.inverted()
            vec = input_matrix_inv @ self.intersect_tri(input_matrix)

            vec_ref = input_matrix_inv @ self.intersect_tri(input_matrix, origin=self.origin_ref, direction=self.direction_ref)
            angle = vec.to_2d().angle_signed(ref_vec, 0) - vec_ref.to_2d().angle_signed(ref_vec, 0)

            if event.ctrl:
                incr = math.radians(self.rotation_snap)
                angle = round(angle / incr) * incr

            delta_rot = Matrix.Rotation(angle, 4, 'Z')

            self.snap_matrix = input_matrix @ delta_rot @ input_matrix.inverted() @ matrix

            if self.rotation_keep_normal:
                z_vec = Vector((0,0,1))
                normal_current = self.init_alignment_matrix.to_3x3() @ z_vec
                normal_final = self.snap_matrix.to_3x3() @ z_vec

                if normal_current.dot(normal_final) < 0:
                    self.snap_matrix = self.snap_matrix @ Matrix.Rotation(math.radians(180), 4, self.rotation_axis)

            self.snap_matrix = self.snap_matrix @ self.scale_matrix

        elif self.mode == 'SCALE':
            vec = self.alignment_matrix.inverted() @ self.intersect_tri(self.alignment_matrix)

            x = vec.x / (self.unit.x * self.count.x)
            y = vec.y / (self.unit.y * self.count.y)

            x = abs(x)
            y = abs(y)

            if not event.shift:
                y = x = max((x,y))

            self.snap_matrix = self.alignment_matrix @ Matrix.Diagonal((x, y, 1, 1))

        elif self.mode == 'EXTEND':
            vec = self.snap_matrix.inverted() @ self.intersect_tri(self.alignment_matrix)
            vec = self.snap_vec_xy(vec, self.unit)

            x = abs((vec.x / self.unit.x))
            y = abs((vec.y / self.unit.y))

            if not event.shift:
                y = x = max((y,x))

            if x != self.count.x or y != self.count.y:
                self.count = (x, y)

                return

        self.grid_data_update()


    def grid_data_update(self):
        plane_matrix = self.snap_matrix @ Matrix.Diagonal((self.unit.x * self.count.x * 2, self.unit.y * self.count.y * 2, 1, 1))
        self.plane_verts = [plane_matrix @ v for v in self.plane_verts_base]

        draw_offset = self.alignment_matrix.to_3x3() @ Vector((0, 0, self.grid_draw_offset))
        self.center_vert = self.snap_matrix.translation + draw_offset

        if self.frozen or self.mode == 'NONE':
            self.center_vert = self.snap_world + draw_offset


    def mouse_input(self, coord2d=tuple()):
        if not coord2d:
            coord2d = self.mouse

        self.origin = region_2d_to_origin_3d(self.region, self.region_3d, coord2d)
        self.direction = region_2d_to_vector_3d(self.region, self.region_3d, coord2d)


    def mouse_warp(self, context):
        coord = location_3d_to_region_2d(context.region, context.space_data.region_3d, self.snap_matrix.translation, default=self.mouse)
        x = int(coord.x + self.region.x)
        y = int(coord.y + self.region.y)

        context.window.cursor_warp(x, y)


    def align_face(self, context):
        cast = raycast_obj(context, self.origin, self.direction, object_types=self.snapable_types) if not self.cast_override or self.initialized else self.cast_override
        hit, location, normal, bm_container, obj, obj_matrix_scaless = cast

        if not hit:
            return False

        self.bm_container = bm_container
        self.obj_surface_matrix = obj_matrix_scaless

        face = bm_container.faces[:][0]
        face_matrix = face.normal.to_track_quat('Z', 'Y').to_matrix().to_4x4()
        face_matrix.translation = self.obj_surface_matrix.inverted() @ location
        face_matrix_inv = face_matrix.inverted()

        track_vec = Vector((0, 0, 0))
        anchor = location

        if self.active_mesh_edge:
            pass

        if self.alignment == 'NEAREST':

            distance = 0.0
            nearest_edge = None
            for edge in face.edges:
                vecs = edge.verts[0].co, edge.verts[1].co

                current, normalized_distance = geometry.intersect_point_line(face_matrix.translation, *vecs)

                if normalized_distance > 1:
                    current = vecs[1]

                elif normalized_distance < 0:
                    current = vecs[0]

                length = (current - face_matrix.translation).length

                if length < distance or not distance:
                    distance = length
                    nearest_edge = vecs

            track_vec = (face_matrix_inv @ nearest_edge[0]) - (face_matrix_inv @ nearest_edge[1])
            anchor = self.obj_surface_matrix @ min(nearest_edge, key=lambda vec: (face_matrix_inv @ vec).length)

        elif self.alignment == 'TANGENT':
            tangent_edge = max(face.edges, key=lambda edge: (edge.verts[0].co - edge.verts[1].co).length)
            track_vec = (face_matrix_inv @ tangent_edge.verts[0].co) - (face_matrix_inv @ tangent_edge.verts[1].co)
            verts_co = tangent_edge.verts[0].co, tangent_edge.verts[1].co
            anchor = self.obj_surface_matrix @ min(verts_co, key=lambda vec: (face_matrix_inv @ vec).length)

        elif self.alignment == 'FACE_FIT':
            local_verts = [(face_matrix_inv @ vert.co).to_2d() for vert in face.verts]
            convex_verts = [local_verts[i] for i in geometry.convex_hull_2d(local_verts)]

            angle = geometry.box_fit_2d(convex_verts)
            delta_rotation = Matrix.Rotation(angle, 2)
            aligned_hull = [delta_rotation @ vert for vert in convex_verts]
            _min, _max = coordinates_to_diagonal(aligned_hull)
            diagonal = _max - _min

            center = delta_rotation.inverted() @ ((_min + _max) / 2)
            edge_vec = delta_rotation.inverted() @ Vector((1, 0))

            if diagonal.x < diagonal.y:
                unit = diagonal.x / 2
                self.unit.x = unit
                self.unit.y = unit

                self.count.x = 1

                fraction, whole = math.modf(diagonal.y / diagonal.x)
                self.count.y = int(whole) if fraction < self.fit_precision else int(whole) + 1

            else:
                unit = diagonal.y / 2
                self.unit.x = unit
                self.unit.y = unit

                fraction, whole = math.modf(diagonal.x / diagonal.y)
                self.count.x = int(whole) if fraction < self.fit_precision else int(whole) + 1
                self.count.y = 1

            track_vec = edge_vec
            anchor = self.obj_surface_matrix @ face_matrix @ center.to_3d()
            self.unit_face_fit = self.unit.copy()

        elif self.alignment == 'LOCAL':
            plane_matrix = self.obj_surface_matrix @ face_matrix
            plane_matrix.translation = location
            normal = plane_matrix.to_3x3() @ Vector((0, 0, 1))

            self.origin = obj.matrix_world.translation
            self.direction = normal

            anchor = self.intersect_tri(plane_matrix)

        delta_angle = track_vec.to_2d().angle_signed(Vector((1,0)), 0)
        correction_matrix = Matrix.Rotation(delta_angle, 4, 'Z')

        self.alignment_matrix = self.obj_surface_matrix.to_quaternion().to_matrix().to_4x4() @ face_matrix @ correction_matrix

        surface_offset = self.alignment_matrix.to_quaternion() @ self.surface_offset_vector

        self.alignment_matrix.translation = anchor + surface_offset
        self.init_alignment_matrix = self.alignment_matrix

        return True


    def create_dots(self):
        if self.snap_type not in {'BOTH', 'DOTS'}: return
        if not {'VERT', 'EDGE', 'FACE'}.intersection(self.enabled_dots): return

        if not self.dot_handler:
            self.dot_handler = dot_handler(bpy.context, handle_draw=False)
            self.dot_handler.dot_preview_size = self.dot_preview_size * self.dot_preview_scale

        self.dot_handler.clear_dots()
        self.dot_handler.snap_radius = self.dot_snap_radius
        self.dot_handler.dot_preview = self.dot_preview
        self.dot_handler.preview_color = self.plane_color
        self.dot_handler.preview_width = self.grid_thickness * 1.5

        size = self.dot_size
        size_high = self.dot_size * self.dot_size_high
        width = 0
        width_high = size_high * 0.1

        bm_container = self.bm_container.copy()
        face = bm_container.faces[:][0]
        face_matrix = face.normal.to_track_quat('Z', 'Y').to_matrix().to_4x4()
        face_matrix.translation = self.obj_surface_matrix.inverted() @ face.calc_center_median()
        face_matrix_inv = face_matrix.inverted()

        surface_offset_matrix = Matrix.Translation(self.surface_offset_vector)

        result = bmesh.ops.subdivide_edges(bm_container, edges=bm_container.edges, cuts=self.dot_divisions, use_grid_fill=len(bm_container.verts) > 3)
        created_verts = [elem for elem in result['geom_inner'] if isinstance(elem, bmesh.types.BMVert)]

        if 'VERT' in self.enabled_dots:
            color = self.dot_colors['VERT']
            color_high = self.dot_colors['VERT_HIGH']

            container = bm_container
            original_verts = [v for v in container.verts if v not in set(created_verts)]
            custom_normal = container.verts.layers.string.get('custom_normal')
            inner_verts = [v for v in created_verts if not v.is_boundary]
            outer_verts = [v for v in created_verts if v.is_boundary]
            e_normal = container.edges.layers.string.get('normal')

            def create_vert_dot(vert, mat_index, normal=None, boundary=False):
                vec_world = (self.obj_surface_matrix @ vert.co)

                matrices = []

                if normal is not None:
                    matrix = normal.to_track_quat('Z', 'Y').to_matrix().to_4x4()
                    t_vec = matrix.inverted() @ vert.co - matrix.inverted() @ vert.link_edges[0].other_vert(vert).co
                    matrix = self.obj_surface_matrix @ matrix @ Matrix.Rotation(t_vec.to_2d().angle_signed(Vector((1,0)), 0), 4, 'Z')
                    matrix.translation = vec_world
                    matrix = matrix @ surface_offset_matrix
                    matrices.append(matrix)

                shared_matrix = self.alignment_matrix.copy()
                shared_matrix.translation = vec_world
                shared_matrix = shared_matrix @ surface_offset_matrix
                matrices.append(shared_matrix)

                if boundary:
                    boundary_edges = [e for e in vert.link_edges if e.is_boundary]
                    normal = str(boundary_edges[0][e_normal], 'ascii')

                    if normal:
                        x, y, z = normal.split(',')
                        normal = Vector((float(x), float(y), float(z)))
                        normal_matrix = normal.to_track_quat('Z', 'Y').to_matrix().to_4x4()
                        normal_matrix_inv = normal_matrix.inverted()
                        edge = boundary_edges[0]
                        t_vec = normal_matrix_inv @ edge.verts[0].co - normal_matrix_inv @ edge.verts[1].co
                        normal_matrix = normal_matrix @ Matrix.Rotation(t_vec.to_2d().angle_signed(Vector((1,0)), 0), 4, 'Z')

                        normal_matrix = self.obj_surface_matrix @ normal_matrix
                        normal_matrix.translation = vec_world
                        normal_matrix = normal_matrix @ surface_offset_matrix
                        matrices.insert(0, normal_matrix)

                    inner_edge = [e for e in vert.link_edges if not e.is_boundary]
                    edges = (boundary_edges[0], inner_edge[0]) if inner_edge else [boundary_edges[0]]

                    for edge in edges:
                        edge_matrix = vert.normal.to_track_quat('Z', 'Y').to_matrix().to_4x4()
                        edge_matrix_inv = edge_matrix.inverted()
                        t_vec = edge_matrix_inv @ edge.verts[0].co - edge_matrix_inv @ edge.verts[1].co
                        edge_matrix = edge_matrix @ Matrix.Rotation(t_vec.to_2d().angle_signed(Vector((1,0)), 0), 4, 'Z')

                        edge_matrix = self.obj_surface_matrix @ edge_matrix
                        edge_matrix.translation = vec_world
                        edge_matrix = edge_matrix @ surface_offset_matrix
                        matrices.append(edge_matrix)

                vert_matrix = vert.normal.to_track_quat('Z', 'Y').to_matrix().to_4x4()
                vert_matrix.translation = vert.co
                vert_matrix_inv = vert_matrix.inverted()

                diagonal_filter = dict()
                ref = vert.normal.orthogonal()
                linkd_faces = vert.link_faces if len(vert.link_faces) != 4 else vert.link_faces[:1]
                for face in linkd_faces:
                    linked_edges = [edge for edge in vert.link_edges if edge in set(face.edges)]
                    vecs = [(vert_matrix_inv @ e.other_vert(vert).co).normalized() for e in linked_edges]
                    diagonal = sum(vecs, Vector()) / 2
                    diagonal.normalize()

                    if not round(diagonal.length, 3): continue

                    key = round(abs(ref.dot(diagonal)), 3)
                    diagonal_filter[key] = diagonal

                for diagonal in diagonal_filter.values():
                    t_vec = diagonal
                    diagonal_matrix = self.obj_surface_matrix @ vert_matrix @ Matrix.Rotation(t_vec.to_2d().angle_signed(Vector((1,0)), 0), 4, 'Z')
                    diagonal_matrix.translation = vec_world
                    diagonal_matrix = diagonal_matrix @ surface_offset_matrix
                    matrices.append(diagonal_matrix)

                dot = self.dot_handler.dot_create(location=vec_world, type='VERT', size=size, size_high=size_high, color=color, color_high=color, outline_color_high=color_high, outline_width=width, outline_width_high=width_high)
                dot.matrices = matrices
                dot.mat_index = mat_index


            mat_index = 0 if 'VERT' in self.dot_alignment else 1
            for vert in original_verts:
                normal = vert[custom_normal]
                x, y, z = str(vert[custom_normal], 'ascii').split(',')
                normal = Vector((float(x), float(y), float(z)))

                create_vert_dot(vert, mat_index , normal=normal)

            for vert in inner_verts:
                create_vert_dot(vert, 0, normal=None)

            for vert in outer_verts:
                create_vert_dot(vert, mat_index=mat_index, normal=None, boundary=True)

        if 'EDGE' in self.enabled_dots:
            color = self.dot_colors['EDGE']
            color_high = self.dot_colors['EDGE_HIGH']

            container = bm_container
            e_normal = container.edges.layers.string.get('normal')
            e_flat = container.edges.layers.int.get('flat')

            for edge in container.edges:
                vec_world = self.obj_surface_matrix @ ((edge.verts[0].co + edge.verts[1].co) / 2)

                t_vec = face_matrix_inv @ edge.verts[0].co - face_matrix_inv @ edge.verts[1].co
                matrix = self.obj_surface_matrix @ face_matrix @ Matrix.Rotation(t_vec.to_2d().angle_signed(Vector((1,0)), 0), 4, 'Z')
                matrix.translation = vec_world

                shared_matrix = self.alignment_matrix.copy()
                shared_matrix.translation = vec_world

                matrices = [matrix, shared_matrix]

                normal = str(edge[e_normal], 'ascii')
                if normal:
                    x, y, z = str(edge[e_normal], 'ascii').split(',')
                    normal = Vector((float(x), float(y), float(z)))

                    normal_matrix = normal.to_track_quat('Z', 'Y').to_matrix().to_4x4()
                    normal_matrix_inv = normal_matrix.inverted()
                    t_vec = normal_matrix_inv @ edge.verts[0].co - normal_matrix_inv @ edge.verts[1].co
                    normal_matrix = normal_matrix @ Matrix.Rotation(t_vec.to_2d().angle_signed(Vector((1,0)), 0), 4, 'Z')

                    normal_matrix = self.obj_surface_matrix @ normal_matrix
                    normal_matrix.translation = vec_world
                    matrices.append(normal_matrix)

                d_type = 'EDGE'
                mat_index = 0 if d_type in self.dot_alignment and (not self.dot_alignment_ignore_flat or not (edge[e_flat] or not edge.is_boundary)) else 1

                for mat in matrices:
                    mat.translation = mat @ self.surface_offset_vector

                dot = self.dot_handler.dot_create(location=vec_world, type='EDGE', size=size, size_high=size_high, color=color, color_high=color, outline_color_high=color_high, outline_width=width, outline_width_high=width_high)
                dot.matrices = matrices
                dot.mat_index = mat_index

        if 'FACE' in self.enabled_dots:
            color = self.dot_colors['FACE']
            color_high = self.dot_colors['FACE_HIGH']

            container = bm_container
            face = bm_container.faces[:][0]
            vec_world = self.obj_surface_matrix @ face.calc_center_median()

            matrix = self.obj_surface_matrix @ face_matrix
            matrix.translation = vec_world
            matrix = matrix @ surface_offset_matrix

            shared_matrix = self.alignment_matrix.copy()
            shared_matrix.translation = vec_world
            shared_matrix = shared_matrix @ surface_offset_matrix
            matrices = matrix, shared_matrix

            d_type = 'FACE'
            mat_index = 0 if d_type in self.dot_alignment else 1

            for face in container.faces:
                matrices = [mat.copy() for mat in matrices]
                vec = face.calc_center_median()
                for mat in matrices:
                    mat.translation = self.obj_surface_matrix @ vec
                    mat.translation = mat @ self.surface_offset_vector

                vec_world = self.obj_surface_matrix @ vec

                dot = self.dot_handler.dot_create(location=vec_world, type='FACE', size=size, size_high=size_high, color=color, color_high=color, outline_color_high=color_high, outline_width=width, outline_width_high=width_high)
                dot.matrices = matrices
                dot.mat_index = mat_index


        self.dot_wire_co = self.dot_wire_id = None

        if self.draw_dots_wire and len(bm_container.faces) > 1:
            me = bpy.data.meshes.new('temp')

            bm_container.to_mesh(me)

            length = len(me.vertices)
            self.dot_wire_co = numpy.ones([length, 3], dtype='f', order='C')
            me.vertices.foreach_get('co', numpy.reshape(self.dot_wire_co, length * 3))

            length = len(me.edges)
            self.dot_wire_id = numpy.empty([len(me.edges), 2], dtype='i', order='C' )
            me.edges.foreach_get('vertices', numpy.reshape(self.dot_wire_id, length * 2))

            bpy.data.meshes.remove(me)


    def realign(self, context, event):
        # self.mouse = Vector((event.mouse_region_x, event.mouse_region_y))
        # self.mouse_input()

        if self.align_face(context):
            _sca = self.snap_matrix.to_scale()

            sca = Matrix.Diagonal(_sca).to_4x4()
            self.snap_matrix = self.init_alignment_matrix

            self.snap_matrix = self.snap_matrix @ sca

            vec = self.init_alignment_matrix.inverted() @ self.intersect_tri(self.init_alignment_matrix)
            self.snap_world = self.init_alignment_matrix @ self.snap_vec_xy(vec, self.unit / self.divisions)
            self.snap_matrix.translation = self.snap_world

            self._mode = 'MOVE' if not self.frozen else 'NONE'

            self.sync_matrices()
            self.grid_data_update()
            self.create_dots()


    def intersect_tri(self, matrix, origin=None, direction=None):
        v1 = matrix @ Vector(( 0, 1, 0))
        v2 = matrix @ Vector(( 1,-1, 0))
        v3 = matrix @ Vector((-1,-1, 0))

        origin = origin if origin else self.origin
        direction = direction if direction else self.direction

        intersect = geometry.intersect_ray_tri(v1, v2, v3, direction, origin, False)
        if not intersect:
            intersect = geometry.intersect_ray_tri(v1, v2, v3, -direction, origin, False)

        if not intersect:
            intersect = self.intersect

        self.intersect = intersect

        return intersect

    def build_grid_mesh(self, edges_only=False):
        unit = self.unit / self.divisions

        count_x = int(self.count.x * self.divisions)
        count_y = int(self.count.y * self.divisions)

        bm = bmesh.new()
        half_unit = unit / 2
        matrix = Matrix.Translation((*half_unit, 0)) @ Matrix.Diagonal((*unit , 1, 1))
        bmesh.ops.create_grid(bm, size=0.5, matrix=matrix)

        if edges_only:
            bmesh.ops.delete(bm, geom=bm.faces, context='FACES_ONLY')

        bmesh.ops.spin(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], cent=[0, 0, 0], axis=[1, 0, 0], dvec=[unit.x, 0, 0], angle=0, steps=count_x -1, use_merge=0, use_normal_flip=0, use_duplicate=1)
        bmesh.ops.spin(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], cent=[0, 0, 0], axis=[0, 1, 0], dvec=[0, unit.y, 0], angle=0, steps=count_y -1, use_merge=0, use_normal_flip=0, use_duplicate=1)

        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=min(unit) / 2)

        bmesh.ops.mirror(bm, geom= bm.verts[:] + bm.edges[:] + bm.faces[:], axis='X', merge_dist=unit.x / 2)
        bmesh.ops.mirror(bm, geom= bm.verts[:] + bm.edges[:] + bm.faces[:], axis='Y', merge_dist=unit.y / 2)

        if bm.faces:
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

            if bm.faces[:][0].normal.z < 0:
                bmesh.ops.reverse_faces(bm, faces=bm.faces)

        me = bpy.data.meshes.new('snapping_mesh')
        bm.to_mesh(me)
        bm.free()

        return me


    def sync_matrices(self):
        _loc, _rot, _sca = self.snap_matrix.decompose()

        loc = Matrix.Translation(_loc)
        rot = _rot.to_matrix().to_4x4()
        sca = Matrix.Diagonal(_sca).to_4x4()

        self.alignment_matrix = loc @ rot
        self.scale_matrix = sca

        if self.mode == 'ROTATE':
            self.init_alignment_matrix = self.alignment_matrix.copy()


    def cancel_transform(self):
        if self.mode in {'SCALE'}:
            self.snap_matrix = self.alignment_matrix @ self.scale_matrix

        elif self.mode == 'ROTATE':
            loc = self.alignment_matrix.translation
            self.alignment_matrix = self.snap_matrix = self.init_alignment_matrix @ self.scale_matrix
            self.alignment_matrix.translation = self.snap_matrix.translation = loc

        elif self.mode =='MOVE' and self.frozen:
            self.snap_matrix = self.alignment_matrix @ self.scale_matrix

        self.mode = 'NONE' if self.frozen else 'MOVE'

        self.grid_data_update()

class dot():
    _highlight = False
    _index = 0
    _size = 20
    _size_high = 40
    _outline_width = 1
    _outline_width_high = 2
    _mat_index = -1

    _location = None
    _color = None
    _color_high = None
    _outline_color = None
    _outline_color_high = None

    @property
    def matrix(self):
        return self.matrices[self.mat_index]

    @property
    def mat_index(self):
        return self._mat_index

    @mat_index.setter
    def mat_index(self, val):
        if not self.matrices: return
        self._mat_index = val % len(self.matrices)

    @property
    def highlight(self):
        return self._highlight

    @highlight.setter
    def highlight(self, val):
        self._highlight = val

        if val:
            self.handler.colors[self._index] = self.color_high
            self.handler.outline_colors[self._index] = self.outline_color_high
            self.handler.sizes[self._index] = self.size_high
            self.handler.outline_widths[self._index] = self.outline_width_high

        else:
            self.handler.colors[self._index] = self.color
            self.handler.outline_colors[self._index] = self.outline_color
            self.handler.sizes[self._index] = self.size
            self.handler.outline_widths[self._index] = self.outline_width

    location = property(fget=lambda self: self._location, fset=lambda self, val: self._set_iter(self._location, val))
    color = property(fget=lambda self: self._color, fset=lambda self, val: self._set_iter(self._color, val))
    color_high = property(fget=lambda self: self._color_high, fset=lambda self, val: self._set_iter(self._color_high, val))
    outline_color = property(fget=lambda self: self._outline_color, fset=lambda self, val: self._set_iter(self._outline_color, val))
    outline_color_high = property(fget=lambda self: self._outline_color_high, fset=lambda self, val: self._set_iter(self._outline_color_high, val))

    size = property(fget=lambda self: self._size, fset=lambda self, val: self._set_val('_size', 'sizes', val, False))
    size_high = property(fget=lambda self: self._size_high, fset=lambda self, val: self._set_val('_size_high', 'sizes', val, True))
    outline_width = property(fget=lambda self: self._outline_width, fset=lambda self, val: self._set_val('_outline_width', 'outline_widths', val, False))
    outline_width_high = property(fget=lambda self: self._outline_width_high, fset=lambda self, val: self._set_val('_outline_width_high', 'outline_widths', val, True))

    def __init__(self, handler):
        self.handler = handler
        self.type = ''
        self.matrices = []

    def _set_iter(self, attr, val):
        for i in range(len(attr)):
            attr[i] = val[i]

    def _set_val(self, attr_name, col_name, val, high):
        setattr(self, attr_name, val)

        if self.highlight == high:
            col = getattr(self.handler, col_name)
            col[self._index] = val

class dot_handler():

    dots = []
    locations = []

    active_dot = None
    draw_handler = None
    dot_shader = None
    draw = True
    dot_preview = False
    dot_preview_size = 0.05

    colors = None
    sizes = None
    outline_colors = None
    outline_widths = None

    snap_radius = 10

    preview_verts = [Vector((-0.5,-0.5, 0)), Vector(( 0.5,-0.5, 0)), Vector((-0.5, 0.5, 0)), Vector(( 0.5, 0.5, 0))]
    preview_indices = [(1, 3, 2), (0, 1, 2)]
    preview_border_indices = [(0, 1), (0, 2), (2, 3), (1, 3)]
    preview_color = [0.5, 0.5, 0.5, 0.3]
    preview_width = 1

    def __init__(self, context, handle_draw=True):
        self.region = context.region
        self.region_3d = context.space_data

        self.colors = []
        self.sizes = []
        self.outline_colors = []
        self.outline_widths = []
        self.dot_shader = flat_point_outline.compile()

        if handle_draw:
            self.draw_handler = bpy.types.SpaceView3D.draw_handler_add(self.draw_callback, (context,), 'WINDOW', 'POST_VIEW')

    def update(self, context, event):
        self.mouse = Vector((event.mouse_region_x, event.mouse_region_y))

        areas = [area for area in context.screen.areas if area.type == 'VIEW_3D']

        for area in areas:
            area_mouse_x = event.mouse_x - area.x
            area_mouse_y = event.mouse_y - area.y

            if 0 < area_mouse_x < area.width and 0 < area_mouse_y < area.height:
                space_data = area.spaces.active
                self.region_3d = space_data.region_3d

                for region in area.regions:
                    region_mouse_x = event.mouse_x - region.x
                    region_mouse_y = event.mouse_y - region.y
                    if region.type == 'WINDOW' and 0 < region_mouse_x < region.width and 0 < region_mouse_y < region.height:
                        self.mouse.x = region_mouse_x
                        self.mouse.y = region_mouse_y
                        self.region = region

                        break

                if space_data.region_quadviews:
                    if area_mouse_x < area.width / 2:
                        i = 1 if area_mouse_y > area.height / 2 else 0

                    else:
                        i = 3 if area_mouse_y > area.height / 2 else 2

                    self.region_3d = space_data.region_quadviews[i]
                break

        if self.active_dot:
            self.active_dot.highlight = False

        self.active_dot = None
        distance = 0
        for dot in self.dots:
            vec2d = location_3d_to_region_2d(self.region, self.region_3d, dot.location, default=Vector((0,0)))

            dist = (self.mouse - vec2d).length

            if dist > self.snap_radius:
                continue

            if dist < distance or not self.active_dot:
                self.active_dot = dot
                distance = dist

        if self.active_dot:
            self.active_dot.highlight = True

    def dot_create(self, location, type='VERT', size=5, size_high=10, color=(1, 1, 1, 0.8), color_high=(1, 0, 0, 1), outline_color=(0, 0, 0, 1), outline_color_high=(1, 0, 0, 1), outline_width=1, outline_width_high=2):
        _dot = dot(self)
        index = len(self.dots)
        self.dots.append(_dot)

        _dot._index = index
        _dot.type = type
        _dot._location = Vector(location)
        _dot._size = size
        _dot._size_high = size_high
        _dot._color = list(color)
        _dot._color_high = list(color_high)
        _dot._outline_color = list(outline_color)
        _dot._outline_color_high = list(outline_color_high)
        _dot._outline_width = outline_width
        _dot._outline_width_high = outline_width_high
        _dot._highlight = False

        self.locations.append(_dot.location)
        self.sizes.append(_dot.size)
        self.colors.append(_dot.color)
        self.outline_colors.append(_dot.outline_color)
        self.outline_widths.append(_dot._outline_width)

        return _dot

    def dot_remove(self, dot, update_indices=True):
        index = dot._index
        if self.active_dot is dot:
            self.active_dot = None

        del self.dots[index]
        del self.locations[index]
        del self.sizes[index]
        del self.colors[index]
        del self.outline_colors[index]
        del self.outline_widths[index]

        if update_indices:
            for i in range(index, len(self.dots)):
                self.dots[i]._index = i

    def update_indices(self):
        for dot, i in enumerate(self.dots):
            dot._index = i

    def foreach_set(self, name, val):
        for dot in self.dots:
            setattr(dot, name, val)

    def clear_dots(self):
        self.active_dot = None
        self.dots.clear()
        self.locations.clear()
        self.sizes.clear()
        self.colors.clear()
        self.outline_colors.clear()
        self.outline_widths.clear()

    def purge(self):
        self.clear_dots()

        if self.draw_handler:
            bpy.types.SpaceView3D.draw_handler_remove(self.draw_handler, 'WINDOW')
            self.draw_handler = None

    def draw_callback(self, context):
        if not self.draw: return
        if not self.locations: return
        gpu.state.blend_set('ALPHA')
        # bgl.glEnable(bgl.GL_LINE_SMOOTH)

        self.alignment_preview(context)

        dot_shader = self.dot_shader

        dot_shader.bind()
        dot_shader.uniform_float('ViewProjectionMatrix', context.region_data.perspective_matrix)

        gpu.state.program_point_size_set(True)

        batch = batch_for_shader(dot_shader, 'POINTS', {'pos': self.locations, 'color_fill': self.colors, 'size': self.sizes, 'outlineWidth': self.outline_widths, 'color_outline': self.outline_colors
        })
        batch.draw(dot_shader)

        gpu.state.program_point_size_set(False)
        gpu.state.blend_set('NONE')
        # bgl.glDisable(bgl.GL_LINE_SMOOTH)

    def alignment_preview(self, context):
        if not self.active_dot: return

        if self.dot_preview and self.active_dot.matrices:
            size = self.sizes[self.active_dot._index]
            self.sizes[self.active_dot._index] = 0

            dot_matrix = self.active_dot.matrix
            persp_matrix = context.region_data.view_matrix.copy()
            persp_matrix.translation.z = -context.region_data.view_distance

            depth_factor = ((persp_matrix @ dot_matrix.translation) - dot_matrix.translation).length * 0.1
            size = self.dot_preview_size * (1 + depth_factor)
            scale = Matrix.Scale(size, 4)
            matrix = dot_matrix @ scale
            positions = [matrix @ vec for vec in self.preview_verts]

            uniform_color = 'UNIFORM_COLOR' if bpy.app.version[0] >= 4 else '3D_UNIFORM_COLOR'
            preview_shader = gpu.shader.from_builtin(uniform_color)
            preview_shader.bind()
            preview_shader.uniform_float('color', self.preview_color)

            preview_batch = batch_for_shader(preview_shader, 'TRIS', {'pos': positions}, indices=self.preview_indices)
            preview_batch.draw(preview_shader)

            gpu.state.line_width_set(self.preview_width)

            border_shader = gpu.shader.from_builtin(uniform_color)
            border_shader.bind()
            border_shader.uniform_float('color', self.active_dot.outline_color_high)

            border_batch = batch_for_shader(border_shader, 'LINES', {'pos': positions}, indices=self.preview_border_indices)
            border_batch.draw(border_shader)

            gpu.state.line_width_set(1)

            self.sizes[self.active_dot._index] = size


def raycast_obj(context, origin_world, direction_world, selected_only=True, object_types={}, evaluated=True):
    object_types = {'MESH', 'CURVE'}
    depsgraph = context.evaluated_depsgraph_get()
    objects = [o for o in context.selected_objects if o.type in object_types] if selected_only else [o for o in context.visible_objects if o.type in object_types]

    if  evaluated and {'MESH'}.issuperset(object_types) and context.mode == 'OBJECT':
        hit, location, normal, index, obj, matrix = context.scene.ray_cast(context.view_layer if bpy.app.version[:2] < (2, 91) else depsgraph, origin_world, direction_world)

        if not hit:
            return False, Vector((0, 0, 0)), Vector((0, 0,-1)), -1, None, Matrix()

        if not selected_only or obj in set(objects):
            cast = (hit, location, normal, index, obj.matrix_world)
            eval_obj = obj.evaluated_get(depsgraph)
            temp_mesh = eval_obj.to_mesh()
            processed_cast = cast_processor(obj, temp_mesh, cast)

            eval_obj.to_mesh_clear()

            return processed_cast

    cast = None
    hit_object = None
    hit_mesh = None
    distance = None
    to_clear = []
    removeable_objects = []
    removeable_meshes = []

    cast_mesh = bpy.data.meshes.new('tmp')
    cast_obj = bpy.data.objects.new('tmp', cast_mesh)
    bpy.context.collection.objects.link(cast_obj)
    removeable_meshes.append(cast_mesh)
    removeable_objects.append(cast_obj)

    bm = bmesh.new()
    bmesh.ops.create_cube(bm)
    bm.to_mesh(cast_mesh)
    bm.free()
    verts_co = [v.co.copy() for v in cast_mesh.vertices]

    def quad_cast(mesh, origin, direction):
        distance = sys.float_info.max
        hit = False
        vec = Vector()
        normal = Vector((0, 0, -1))
        index = -1
        for p in mesh.polygons:

            v1 = mesh.vertices[p.vertices[0]].co
            v2 = mesh.vertices[p.vertices[1]].co
            v3 = mesh.vertices[p.vertices[2]].co

            point = geometry.intersect_ray_tri(v1, v2, v3, direction, origin, True)
            if point is not None:
                dist = (point - origin).magnitude
                if dist < distance:
                    hit = True
                    vec = point
                    normal = p.normal
                    index = p.index
                    distance = dist

            else:
                v1 = mesh.vertices[p.vertices[2]].co
                v2 = mesh.vertices[p.vertices[3]].co
                v3 = mesh.vertices[p.vertices[0]].co

                point = geometry.intersect_ray_tri(v1, v2, v3, direction, origin, True)

                if point is not None:
                    dist = (point - origin).magnitude
                    if dist < distance:
                        hit = True
                        vec = point
                        normal = p.normal
                        index = p.index
                        distance = dist

        return hit, vec, normal, index

    def has_screw(obj):
        for mod in obj.modifiers:
            if mod.type == 'SCREW' and mod.show_viewport: return True

    for obj in objects:
        inverted = obj.matrix_world.inverted()
        orig = inverted @ origin_world
        direction = inverted @ (direction_world + origin_world) - orig
        use_evaluated = evaluated

        if obj.mode == 'EDIT':
            obj.update_from_editmode()

        if not use_evaluated:
            tmp = bpy.data.objects.new('tmp', obj.data)
            context.collection.objects.link(tmp)
            bounds = [Vector(v) for v in tmp.bound_box]
            bpy.data.objects.remove(tmp)

        else:
            eval = obj.evaluated_get(context.evaluated_depsgraph_get())
            bounds = eval.bound_box

        center = coordinates_center(bounds)
        sca = coordinates_dimension(bounds)
        matrix = Matrix.Translation(center) @ Matrix.Diagonal((*sca, 1))

        for v, co in zip(cast_mesh.vertices, verts_co):
            v.co = matrix @ co

        hit, *_ = quad_cast(cast_mesh, orig, direction)

        if not hit:
            continue

        if obj.mode == 'EDIT' and obj.type == 'MESH':
            obj.update_from_editmode()
            cast_obj.data = obj.data

            hit, location, normal, index = cast_obj.ray_cast(orig, direction)

            if hit:
                location = obj.matrix_world @ location
                dist = location - origin_world

                if dist < distance or not distance:
                    distance = dist
                    cast = (hit, location, normal, index, obj.matrix_world)
                    hit_object = obj
                    hit_mesh = obj.data

        elif obj.mode == 'OBJECT' and obj.type == 'MESH':
            if use_evaluated:
                if has_screw(obj):
                    eval_obj = obj.evaluated_get(depsgraph)
                    temp_mesh = bpy.data.meshes.new_from_object(eval_obj)
                    cast_obj.data = temp_mesh

                    hit, location, normal, index  = cast_obj.ray_cast(orig, direction)

                else:
                    eval_obj = obj.evaluated_get(depsgraph)
                    hit, location, normal, index = eval_obj.ray_cast(orig, direction)

            else:
                eval_obj = obj
                hit, location, normal, index = eval_obj.ray_cast(orig, direction)

            if hit:
                location = obj.matrix_world @ location
                dist = location - origin_world

                if dist < distance or not distance:
                    distance = dist
                    cast = (hit, location, normal, index, obj.matrix_world)
                    hit_object = obj
                    hit_mesh = eval_obj.data

        else:
            eval_obj = obj.evaluated_get(depsgraph) if use_evaluated else obj
            temp_mesh = bpy.data.meshes.new_from_object(eval_obj)
            cast_obj.data = temp_mesh

            hit, location, normal, index  = cast_obj.ray_cast(orig, direction)

            removeable_meshes.append(temp_mesh)

            if hit:
                location = obj.matrix_world @ location
                dist = location - origin_world

                if dist < distance or not distance:
                    distance = dist
                    cast = (hit, location, normal, index, obj.matrix_world)
                    hit_object = obj
                    hit_mesh = temp_mesh

    if not cast:
        processed_cast = (False, Vector((0,0,0)), Vector((0,0,-1)), -1, None, Matrix())

    elif cast[0] and cast[3] < 0: # invalid index from screw modifier
        hit, location, normal, index, matrix = cast
        inverted = matrix.inverted()
        orig = inverted @ origin_world
        direction = inverted @ (direction_world + origin_world) - orig

        mesh = bpy.data.meshes.new_from_object(hit_object.evaluated_get(depsgraph))
        removeable_meshes.append(mesh)
        cast_obj.data = mesh
        _, _, _, index = cast_obj.ray_cast(orig, direction)

        cast = hit, location, normal, index, matrix
        processed_cast = cast_processor(hit_object, hit_mesh, cast)

    else:
        processed_cast = cast_processor(hit_object, hit_mesh, cast)

    for obj in removeable_objects: bpy.data.objects.remove(obj)
    for mesh in  removeable_meshes: bpy.data.meshes.remove(mesh)

    for obj in to_clear:
        obj.to_mesh_clear()

    return processed_cast


def edit_mesh_cast(obj, origin_world, direction_world):
    obj.update_from_editmode()
    temp_obj = bpy.data.objects.new('tmp', obj.data)
    bpy.context.collection.objects.link(temp_obj)

    inverted = obj.matrix_world.inverted()
    orig = inverted @ origin_world
    direction = inverted @ (direction_world + origin_world) - orig

    hit, location, normal, index, _ = temp_obj.ray_cast(orig, direction)
    bpy.data.objects.remove(temp_obj)

    if hit:
        cast = (True, obj.matrix_world @ location, normal, index, obj.matrix_world)

        return cast_processor(obj, obj.data, cast)

    else:
        return False, Vector((0,0,0)), Vector((0,0,-1)), -1, None, Matrix()


def cast_processor(obj, mesh, cast):
    hit, location, normal, face_index, matrix = cast

    loc, rot, sca = matrix.decompose()

    trans_mat = Matrix.Translation(loc)
    rot_mat = rot.to_matrix().to_4x4()
    scale_mat = Matrix.Diagonal((*sca, 1))
    scale_mat_inv_trans = scale_mat.inverted().transposed()

    face_hit = mesh.polygons[face_index]
    bm_container = bmesh.new()
    # float_vector layer doesn't exist pre 2.91
    custom_normal = bm_container.verts.layers.string.new('custom_normal')

    if mesh.is_editmode:
        bm = bmesh.from_edit_mesh(mesh)

    else:
        bm = bmesh.new(use_operators=False)
        bm.from_mesh(mesh)

    bm.faces.ensure_lookup_table()
    bm_face_hit = bm.faces[face_index]

    for vert in bm_face_hit.verts:
        vec = scale_mat @ vert.co
        normal = sum([(scale_mat_inv_trans @ f.normal).normalized() for f in vert.link_faces], Vector()) / len(vert.link_faces)
        normal.normalize()

        v = bm_container.verts.new(vec)
        v[custom_normal] = bytes(f'{normal.x},{normal.y},{normal.z}', 'ascii')

    i_map = {index : i for i, index in enumerate(face_hit.vertices)}

    edge_keys = [tuple(i_map[i] for i in edge) for edge in face_hit.edge_keys]

    active_element = bm.select_history.active
    active_edge = active_element if isinstance(active_element, bmesh.types.BMEdge) else None

    bm_container.verts.ensure_lookup_table()
    bm_container.select_history.clear()
    e_normal = bm_container.edges.layers.string.new('normal')
    e_flat = bm_container.edges.layers.int.new('flat')

    flat = math.radians(1)
    for edge, key in zip(bm_face_hit.edges, edge_keys):
        e = bm_container.edges.new((bm_container.verts[key[0]], bm_container.verts[key[1]]))

        flag = edge.calc_face_angle(0) < flat
        e[e_flat] = flag

        length = len(edge.link_faces)
        if length > 1:
            normal = sum([face.normal for face in edge.link_faces], Vector()) / length
            normal = (scale_mat_inv_trans @ normal).normalized()
            e[e_normal] = bytes(f'{normal.x},{normal.y},{normal.z}', 'ascii')

        if edge is active_edge:
            bm_container.select_history.add(e)

    face = bm_container.faces.new(bm_container.verts)
    face.normal_update()

    sca_normal = scale_mat_inv_trans @ bm_face_hit.normal
    sca_normal.normalize()

    if face.normal.dot(sca_normal) < 0:
        face.normal_flip()

    cast = (hit, location, face.normal.copy(), bm_container, obj, trans_mat @ rot_mat)

    return cast


def coordinates_to_diagonal(coords):
    mins = []
    maxs = []
    length = len(coords[0])

    for i in range (length):
        var = [vec[i] for vec in coords]
        mins.append(min(var))
        maxs.append(max(var))

    return Vector(mins), Vector(maxs)


def grid_shader (self, context):
    if not self.front_draw and (self.grid_draw_offset + self.surface_offset_vector.z):
        gpu.state.depth_test_set('LESS')
        gpu.state.depth_mask_set(False)

    uniform_color = 'UNIFORM_COLOR' if bpy.app.version[0] >= 4 else '3D_UNIFORM_COLOR'
    polygon_shader = gpu.shader.from_builtin(uniform_color)
    polygon_shader.bind()
    polygon_shader.uniform_float('color', self.plane_color)


    polygon_batch = batch_for_shader(polygon_shader, 'TRIS', {'pos': self.plane_verts}, indices=self.plane_indices)
    polygon_batch.draw(polygon_shader)

    gpu.state.line_width_set(self.grid_thickness)


    sca = self.snap_matrix.to_scale()

    self.grid_shader.bind()
    self.grid_shader.uniform_float('color', (self.grid_color))
    self.grid_shader.uniform_float('divisions', self.count * self.divisions * 2)
    self.grid_shader.uniform_float('thickness', self.grid_thickness)
    self.grid_shader.uniform_float('ViewProjectionMatrix', context.region_data.perspective_matrix)

    self.grid_batch = batch_for_shader(self.grid_shader, 'TRIS', {'pos' : self.plane_verts, 'UV' : self.plane_uvs}, indices=self.plane_indices)
    self.grid_batch.draw(self.grid_shader)

    gpu.state.line_width_set(self.grid_thickness * 1.5)

    border_shader = gpu.shader.from_builtin(uniform_color)
    border_shader.bind()
    border_shader.uniform_float('color', self.border_color if not self.frozen else self.border_f_color)

    border_batch = batch_for_shader(border_shader, 'LINES', {'pos': self.plane_verts}, indices=self.border_idices)
    border_batch.draw(border_shader)

    gpu.state.depth_mask_set(True)
    gpu.state.depth_test_set('NONE')
    gpu.state.line_width_set(1)


def draw_callback_3d(self, context):
    if not self.draw:
        return

    gpu.state.blend_set('ALPHA')
    # bgl.glEnable(bgl.GL_LINE_SMOOTH)

    if self.snap_type in {'BOTH', 'GRID'}:
        grid_shader(self, context)
        cursor_dot(self, context)

    face_dots(self, context)

    gpu.state.blend_set('NONE')
    # bgl.glDisable(bgl.GL_LINE_SMOOTH)


def cursor_dot(self, context):
    if not self.nearest_dot:
        gpu.state.point_size_set(self.dot_size)

        cursor_dot_shader = self.cursor_dot_shader
        cursor_dot_shader.bind()
        cursor_dot_shader.uniform_float('ViewProjectionMatrix', context.region_data.perspective_matrix)
        color = self.dot_colors['VERT']

        batch3 = batch_for_shader(cursor_dot_shader, 'POINTS', {'pos': [self.center_vert], 'color_fill': [color], 'size': [self.dot_size], 'outlineWidth': [0], 'color_outline': [[0,0,0,0]]})
        batch3.draw(cursor_dot_shader)

        gpu.state.point_size_set(1)


def face_dots(self, context):
    if self.snap_type == 'GRID' or not self.draw_dots or not self.dot_handler or not self.dot_handler.dots:
        return

    if self.dot_wire_co is not None:
        gpu.state.line_width_set(self.grid_thickness)
        wire_shader =  self.wire_shader
        wire_batch = batch_for_shader(wire_shader,'LINES', {'pos' : self.dot_wire_co}, indices = self.dot_wire_id)
        wire_shader.bind()
        wire_shader.uniform_float('ViewProjectionMatrix', context.region_data.perspective_matrix @ self.obj_surface_matrix)
        wire_shader.uniform_float('color', self.border_f_color)
        wire_batch.draw(wire_shader)
        gpu.state.line_width_set(1)

    self.dot_handler.draw_callback(context)


def redraw_areas(context):
    for area in context.screen.areas:
        if area.type != 'VIEW_3D': continue
        area.tag_redraw()


class uniform_shader():

    vertex_attr = '''
        uniform mat4 ViewProjectionMatrix;
        in vec3 pos;

    '''
    vertex = '''
        void main()
        {

          gl_Position = ViewProjectionMatrix * vec4(pos, 1.0);
        }
    '''

    fragment_attr = '''
        uniform vec4 color;
        out vec4 FragColor;
    '''

    fragment = '''
        void main()
        {
            FragColor = color;
        }
    '''

    @classmethod
    def compile(cls):

        if bpy.app.version[:2] < (3, 3):
            vertex = cls.vertex_attr + cls.vertex
            fragment = cls.fragment_attr + cls.fragment

            shader = gpu.types.GPUShader(vertex, fragment)

        else:
            shader_info = gpu.types.GPUShaderCreateInfo()

            shader_info.push_constant('MAT4', 'ViewProjectionMatrix')
            shader_info.push_constant('VEC4', 'color')
            shader_info.vertex_in(0, 'VEC3', 'pos')

            shader_info.fragment_out(0, 'VEC4', 'FragColor')

            shader_info.vertex_source(cls.vertex)
            shader_info.fragment_source(cls.fragment)

            shader = gpu.shader.create_from_info(shader_info)
        return shader

class flat_point_outline():

    vertex_attr = '''
        uniform mat4 ViewProjectionMatrix;

        in float size;
        in float outlineWidth;

        in vec4 color_fill;
        in vec4 color_outline;

        in vec3 pos;

        out vec4 radii;
        out vec4 fillColor;
        out vec4 outlineColor;
    '''

    vertex = '''
        void main()
        {
            vec4 pos_4d = vec4(pos, 1.0);
            gl_Position = ViewProjectionMatrix * pos_4d;
            gl_PointSize = size;

            /* calculate concentric radii in pixels */
            float radius = 0.5 * size;

            /* start at the outside and progress toward the center */
            radii[0] = radius;
            radii[1] = radius - 1.0;
            radii[2] = radius - outlineWidth;
            radii[3] = radius - outlineWidth - 1.0;

            /* convert to PointCoord units */
            radii /= size;

            fillColor = color_fill;
            outlineColor = color_outline;
        }

    '''

    fragment_attr = '''
        in vec4 radii;
        in vec4 fillColor;
        in vec4 outlineColor;

        out vec4 fragColor;
    '''

    fragment = '''
        void main()
        {
        float dist = length(gl_PointCoord - vec2(0.5));

        /* transparent outside of point
        * --- 0 ---
        * smooth transition
        * --- 1 ---
        * pure outline color
        * --- 2 ---
        * smooth transition
        * --- 3 ---
        * pure fill color
        * ...
        * dist = 0 at center of point */

        float midStroke = 0.5 * (radii[1] + radii[2]);

        if (dist > midStroke) {
            fragColor.rgb = outlineColor.rgb;
            fragColor.a = mix(outlineColor.a, 0.0, smoothstep(radii[1], radii[0], dist));
        }
        else {
            fragColor = mix(fillColor, outlineColor, smoothstep(radii[3], radii[2], dist));
        }

        fragColor = fragColor;
        }

    '''

    @classmethod
    def compile(cls):

        if bpy.app.version[:2] < (3, 3):
            vertex = cls.vertex_attr + cls.vertex
            fragment = cls.fragment_attr + cls.fragment

            shader = gpu.types.GPUShader(vertex, fragment)

        else:
            shader_info = gpu.types.GPUShaderCreateInfo()
            vertex_out = gpu.types.GPUStageInterfaceInfo('v_out')
            vertex_out.smooth('VEC4', 'radii')
            vertex_out.smooth('VEC4', 'fillColor')
            vertex_out.smooth('VEC4', 'outlineColor')

            shader_info.push_constant('MAT4', 'ViewProjectionMatrix')
            shader_info.vertex_in(0, 'FLOAT', 'size')
            shader_info.vertex_in(1, 'FLOAT', 'outlineWidth')
            shader_info.vertex_in(2, 'VEC4', 'color_fill')
            shader_info.vertex_in(3, 'VEC4', 'color_outline')
            shader_info.vertex_in(4, 'VEC3', 'pos')
            shader_info.vertex_out(vertex_out)

            shader_info.fragment_out(0, 'VEC4', 'fragColor')

            shader_info.vertex_source(cls.vertex)
            shader_info.fragment_source(cls.fragment)

            shader = gpu.shader.create_from_info(shader_info)
        return shader

class Grid_shader():
    vertex_attr = '''
        uniform mat4 ViewProjectionMatrix;
        in vec3 pos;
        in vec2 UV;

        out vec2 uv;
    '''

    vertex = '''
        void main()
        {
          gl_Position = ViewProjectionMatrix * vec4(pos, 1.0);
          uv = UV;
        }
    '''

    fragment_attr = '''
        uniform vec4 color;
        uniform vec2 divisions;
        uniform float thickness;
        in vec2 uv;

        out vec4 FragColor;
    '''

    fragment = '''
        void main() {
            vec2 increment = vec2(1) / divisions;
            vec2 pixel = thickness * divisions * fwidth(uv) * 0.8;
            vec2 alpha;

            vec2 fraction = fract(uv / increment);
            vec2 whole = round(uv / increment) * increment;
            if (whole.x == 0.0 || whole.x == 1)
            {
                alpha.x = 0.0;
            }

            else if (1 - fraction.x < pixel.x || fraction.x < pixel.x )
            {
                alpha.x = 1.0;
            }

            else
            {
                alpha.x = 0.0;
            }


            if (whole.y == 0.0 || whole.y == 1 )
            {
                alpha.y = 0.0;
            }

            else if (1 - fraction.y < pixel.y || fraction.y < pixel.y )
            {
                alpha.y = 1.0;
            }
            else
            {
                alpha.y = 0.0;
            }

            FragColor = vec4(color.xyz, color.w * max(alpha.x, alpha.y));

        }


    '''

    @classmethod
    def compile(cls):

        if bpy.app.version[:2] < (3, 3):
            vertex = cls.vertex_attr + cls.vertex
            fragment = cls.fragment_attr + cls.fragment

            shader = gpu.types.GPUShader(vertex, fragment)

        else:
            shader_info = gpu.types.GPUShaderCreateInfo()
            vertex_out = gpu.types.GPUStageInterfaceInfo('v_out')
            vertex_out.smooth('VEC2', 'uv')

            shader_info.push_constant('MAT4', 'ViewProjectionMatrix')
            shader_info.push_constant('VEC4', 'color')
            shader_info.push_constant('VEC2', 'divisions')
            shader_info.push_constant('FLOAT', 'thickness')
            shader_info.vertex_in(0, 'VEC3', 'pos')
            shader_info.vertex_in(1, 'VEC2', 'UV')
            shader_info.vertex_out(vertex_out)

            shader_info.fragment_out(0, 'VEC4', 'FragColor')

            shader_info.vertex_source(cls.vertex)
            shader_info.fragment_source(cls.fragment)

            shader = gpu.shader.create_from_info(shader_info)
        return shader


def modal(self, context, event):
    preference = addon.preference()
    bc = context.scene.bc

    plane_color = self.plane_color.copy()
    grid_color = self.grid_color.copy()

    if bc.running:
        self.grid_handler.draw_dots = preference.snap.dot_dot_snap

        if preference.snap.auto_transparency:
            plane_color[3] *= 0.25
            grid_color[3] *= 0.25

        if bc.operator.operation not in  {'DRAW', 'MOVE', 'ROTATE', 'SCALE'}:
            self.grid_handler.draw = False

    else:
        self.grid_handler.frozen = self.frozen
        self.grid_handler.draw = True
        self.grid_handler.draw_dots = True

        if not self.grid_handler.frozen and self.grid_handler.mode == 'NONE':
            self.grid_handler.mode = 'MOVE'

        if (not self.frozen and not event.ctrl) or not self.should_run:
            if not (preference.snap.increment_lock and preference.snap.increment_lock):
                self.exit(context)

                return{'FINISHED'}

    self.grid_handler.plane_color = plane_color
    self.grid_handler.grid_color = grid_color

    redraw_areas(context)

    if event.type == 'MOUSEMOVE':
        self.grid_handler.update(context, event)

        self.snap.matrix = self.grid_handler.snap_matrix.normalized()
        self.snap.matrix.translation = self.grid_handler.snap_matrix.translation
        self.snap.snap_world = self.grid_handler.snap_world.copy()
        bc.snap.location = self.grid_handler.snap_matrix.translation

        if self.grid_handler.nearest_dot:
            self.snap.point = type('point', (), {'type': self.grid_handler.nearest_dot.type})

        else:
            self.snap.point = None

        if self.grid_handler.frozen:
            self.snap.matrix.translation = self.snap.snap_world
            bc.snap.location = self.snap.snap_world

        bc.snap.hit = True if self.grid_handler.snap_type != 'DOTS' else bool(self.grid_handler.nearest_dot)

        return {'PASS_THROUGH'}

    elif event.type == 'RIGHTMOUSE':
        if self.grid_handler.snap_type == 'DOTS':
            return {'PASS_THROUGH'}

        if event.value == 'PRESS' and (self.grid_handler.mode in {'ROTATE', 'SCALE'} or (self.grid_handler.mode == 'MOVE' and self.grid_handler.frozen)):
            self.grid_handler.cancel_transform()

        elif event.value == 'PRESS' and event.ctrl:
            self.grid_handler.mode = 'EXTEND'
            self.frozen = True
            self.grid_handler.frozen = True

        elif event.value == 'RELEASE':
            self.grid_handler.mode = 'MOVE' if not self.grid_handler.frozen else 'NONE'

        else:
            return {'PASS_THROUGH'}


    elif event.type == 'R' and event.value == 'PRESS':
        if self.grid_handler.snap_type == 'DOTS':
            return {'PASS_THROUGH'}

        if self.grid_handler.mode == 'ROTATE':
            self.grid_handler.mode = 'MOVE' if not self.grid_handler.frozen else 'NONE'

        else:
            self.grid_handler.mode = 'ROTATE'

    elif event.type == 'S' and event.value == 'PRESS':
        if self.grid_handler.snap_type == 'DOTS':
            return {'PASS_THROUGH'}

        if self.grid_handler.mode == 'SCALE':
            self.grid_handler.mode = 'MOVE' if not self.grid_handler.frozen else 'NONE'

        else:
            self.grid_handler.mode = 'SCALE'

    elif event.type == 'G' and event.value == 'PRESS':
        if self.grid_handler.snap_type == 'DOTS':
            if self.grid_handler.nearest_dot:
                self.grid_handler.snap_type = 'GRID'

                matrix = self.grid_handler.nearest_dot.matrix
                self.grid_handler.alignment_matrix = matrix.copy()
                self.grid_handler.init_alignment_matrix = matrix.copy()
                self.grid_handler.grid_data_update()
                self.grid_handler.mode = 'NONE'
                self.grid_handler.frozen = True
                self.frozen = True
                self.snap.grid_active = True
                self.grid_handler.nearest_dot = None

                if preference.snap.toggle_ortho_grid:
                    context.space_data.overlay.show_ortho_grid = False

                if preference.snap.toggle_floor:
                    context.space_data.overlay.show_floor = False

                return {'RUNNING_MODAL'}

            else:
                return {'PASS_THROUGH'}

        if self.grid_handler.snap_type == 'GRID':
            if event.shift:
                me = self.grid_handler.build_grid_mesh()
                obj = bpy.data.objects.new('snapping_grid', me)
                obj.matrix_world = self.grid_handler.snap_matrix

                context.collection.objects.link(obj)
                obj.show_wire = True

                self.exit(context)

                return{'FINISHED'}


            if self.grid_handler.mode != 'MOVE':
                self.grid_handler.mode = 'MOVE'

            elif self.grid_handler.frozen:
                self.grid_handler.mode = 'NONE'

    elif event.type == 'E' and event.value == 'PRESS':
        if self.grid_handler.snap_type == 'DOTS':
            return {'PASS_THROUGH'}

        if self.grid_handler.mode == 'EXTEND':
            self.grid_handler.mode = 'MOVE' if not self.grid_handler.frozen else 'NONE'

        else:
            self.grid_handler.mode = 'EXTEND'
            self.frozen = True
            self.grid_handler.frozen = True

    elif event.type == 'A' and event.value == 'PRESS' and not any((event.ctrl, event.shift, event.alt, event.oskey)):
        if self.grid_handler.alignment not in {'WORLD', 'OVERRIDE'}:
            self.grid_handler.realign(context, event)

    elif event.type in 'XYZ' and event.value == 'PRESS' and self.grid_handler.mode == 'ROTATE':
        if self.grid_handler.snap_type == 'DOTS':
            return {'PASS_THROUGH'}

        self.grid_handler.rotation_axis = event.type
        self.grid_handler.update(context, event)

    elif(event.type.count('WHEEL') or event.type.count('ARROW')) and event.value == 'PRESS' and (event.ctrl or event.shift):
        direction = 1 if 'UP' in event.type else -1

        if self.grid_handler.snap_type =='DOTS':

            if self.grid_handler.nearest_dot and event.ctrl and not event.shift and not event.alt:
                self.grid_handler.dot_preview = self.grid_handler.dot_handler.dot_preview = True

                dot = self.grid_handler.nearest_dot
                dot.mat_index += direction
                matrix = dot.matrix

                self.snap.matrix = matrix
                self.snap.location = self.grid_handler.snap_world = matrix.translation.copy()
                self.grid_handler.update(context, event)

                return {'RUNNING_MODAL'}

            elif event.shift and not event.alt:
                self.grid_handler.dot_divisions += direction
                self.frozen = self.grid_handler.frozen = True
                self.grid_handler.mode = 'NONE'
                self.grid_handler.update(context, event)
                return {'RUNNING_MODAL'}


        if self.grid_handler.snap_type == 'DOTS':
            return {'PASS_THROUGH'}

        if event.shift:
            self.grid_handler.divisions += direction

        else:
            unit = self.grid_handler.unit
            val = min(unit)

            if val > 1:
                val = round(val + direction, 0)

                if val < 1: val = 1

            elif val == 1:
                val = 0.9 if direction < 0 else 2

            else:
                if val > 0.1:
                    val = round(val + (direction * 0.1), 1)
                    if val < 0.1: val = 0.09

                else:
                    val = round(val + (direction * 0.01), 2)
                    if val < 0.01 : val = 0.01

            preference.snap.increment = val

            self.report({'INFO'}, F'Grid Unit Size: {preference.snap.increment:.2f}')
            self.grid_handler.unit = Vector((val, val)) # trigger setter

    elif event.type == 'LEFTMOUSE' and event.value == 'PRESS':
        if self.grid_handler.snap_type == 'DOTS':
            return {'PASS_THROUGH'}

        if self.grid_handler.mode != 'NONE' and self.grid_handler.frozen:
            self.grid_handler.mode = 'NONE'

        elif self.grid_handler.mode != 'MOVE' and not self.grid_handler.frozen:
            self.grid_handler.mode = 'MOVE'

        else:
            return {'PASS_THROUGH'}

    elif event.type in {'SPACE', 'TAB'}: #munch both values
        if event.value == 'PRESS':
            self.grid_handler.update(context, event) #update before freezing
            self.grid_handler.frozen = not self.grid_handler.frozen
            self.frozen = not self.frozen
            self.grid_handler.mode = 'NONE' if self.grid_handler.frozen else 'MOVE'

    # elif event.type == 'Q' and event.value == 'PRESS':
    #     if self.grid_handler.nearest_dot:
    #         self.grid_handler.dot_handler.dot_remove(self.grid_handler.nearest_dot)
    #     self.grid_handler.update(context, event)
    #     return{'RUNNING_MODAL'}

    elif event.type == 'ESC':
        self.exit(context)

        return {'CANCELLED'}

    elif event.type == 'K' and event.value == 'PRESS':
        if self.grid_handler.snap_type == 'DOTS':
            return {'PASS_THROUGH'}
        if not context.active_object or context.active_object.type != 'MESH' and not event.shift: return {'PASS_THROUGH'}

        active = context.active_object
        selection = context.selected_objects[:]
        mode = active.mode
        me = self.grid_handler.build_grid_mesh(edges_only=True)
        grid_obj = bpy.data.objects.new('grid_object', me)
        grid_obj.matrix_world = self.grid_handler.snap_matrix
        context.collection.objects.link(grid_obj)

        view_mat = context.region_data.view_matrix.copy()
        perspective = context.region_data.view_perspective
        context.region_data.view_perspective = 'ORTHO'
        context.region_data.view_matrix = self.grid_handler.snap_matrix.normalized().inverted()
        context.region_data.update()

        for obj in selection: obj.select_set(False)
        active.select_set(True)

        if context.mode != 'EDIT_MESH':
            bpy.ops.object.mode_set(mode='EDIT')

            grid_obj.select_set(True)
            bpy.ops.mesh.knife_project(cut_through=True)

        else:
            bm = bmesh.from_edit_mesh(context.active_object.data)
            selected = [f for f in bm.faces if f.select]
            visible = []

            if selected:
                visible = [f for f in bm.faces if not f.hide]
                for f in visible:
                    f.hide = not f.select

            grid_obj.select_set(True)
            bpy.ops.mesh.knife_project(cut_through=True)

            for f in visible:
                f.hide = False

            bmesh.update_edit_mesh(context.active_object.data)

        context.region_data.view_matrix = view_mat
        context.region_data.view_perspective = perspective
        context.region_data.update()
        bpy.data.objects.remove(grid_obj)
        bpy.data.meshes.remove(me)

        if active.mode != mode:
            bpy.ops.object.mode_set(mode=mode)

        for obj in selection: obj.select_set(True)

        self.exit(context)
        return {'FINISHED'}

    else:
        return {'PASS_THROUGH'}

    return {'RUNNING_MODAL'}


def invoke(self, context, event):
    self.frozen = False
    self.should_run = True

    bc = context.scene.bc
    preference = addon.preference()

    if bc.snap.operator or bc.running:
        return {'CANCELLED'}

    preference = addon.preference()

    self.tool = tool.active().operator_properties('bc.shape_draw')

    surface = preference.surface if [o for o in context.selected_objects if o.type == 'MESH'] else 'WORLD'
    orientation = preference.behavior.orient_method
    alignment = orientation
    override_matrix = Matrix()
    view_world_dots = False
    self.surface_offset = 0

    if self.tool.mode == 'MAKE' or preference.behavior.boolean_solver == 'EXACT':
        self.surface_offset = 0

    elif self.tool.mode == 'JOIN' and preference.behavior.join_exact:
        self.surface_offset = 0

    else:
        self.surface_offset = preference.shape.offset


    if not preference.snap.grid and not any((preference.snap.verts, preference.snap.edges, preference.snap.faces)):
        return {'PASS_THROUGH'}

    # if surface in {'VIEW', 'WORLD'} and not preference.snap.grid:
    #     return {'PASS_THROUGH'}

    #convert bc's alignment types and subtype into single alignment argument
    if surface == 'VIEW':
        alignment = 'OVERRIDE'
        _, _, override_matrix = ray.view_matrix(context, event.mouse_region_x, event.mouse_region_y)
        override_matrix.translation += override_matrix.to_quaternion() @ Vector((0, 0, self.surface_offset))
        view_world_dots = True

    elif surface == 'CURSOR':
        alignment = 'OVERRIDE'
        loc, rot, _ = context.scene.cursor.matrix.decompose()
        override_matrix = Matrix.Translation(loc) @ rot.to_matrix().to_4x4()
        axis = {'X': 'Y','Y': 'X', 'Z': 'Z'} [preference.axis]
        override_matrix = override_matrix @ Matrix.Rotation(math.radians(-90 if axis in {'X', 'Y'} else 90), 4, axis)
        override_matrix.translation += override_matrix.to_quaternion() @ Vector((0, 0, self.surface_offset))

    elif surface == 'WORLD':
        vec = context.region_data.view_rotation @ Vector((0, 0, 1))
        char = preference.axis
        colinear = lambda v1, v2: round(abs(v1.dot(v2)), 3) == 1

        if colinear(vec, Vector((1, 0, 0))):
            char = 'X'

        elif colinear(vec, Vector((0, 1, 0))):
            char = 'Y'

        elif colinear(vec, Vector((0, 0, 1))):
            char = 'Z'

        alignment = 'WORLD' + char
        view_world_dots =True

    units = Vector.Fill(2, preference.snap.increment)
    cell_count = math.ceil(preference.snap.grid_units / 2)
    cell_count = Vector.Fill(2, abs(cell_count))
    snapable = {'MESH'}
    enabled_dots = {'VERT' if preference.snap.verts else '', 'EDGE' if preference.snap.edges else '', 'FACE' if preference.snap.faces else ''}
    cast_override = None
    dot_alignment = {'EDGE'} if alignment in {'LOCAL', 'NEAREST'} else {}
    ignore_flat = alignment == 'LOCAL'

    if surface == 'OBJECT':
        coord2d = Vector((event.mouse_region_x, event.mouse_region_y))
        origin = region_2d_to_origin_3d(context.region, context.space_data.region_3d, coord2d)
        direction = region_2d_to_vector_3d(context.region, context.space_data.region_3d, coord2d)
        cast = raycast_obj(context, origin, direction, object_types=snapable)

        if cast[0]:
            cast_override = cast

        else:
            surface = 'VIEW'
            alignment = 'OVERRIDE'
            _, _, override_matrix = ray.view_matrix(context, event.mouse_region_x, event.mouse_region_y)
            override_matrix.translation += override_matrix.to_quaternion() @ Vector((0, 0, self.surface_offset))
            view_world_dots = True

    if view_world_dots and not preference.snap.grid:
        from ...snap import invoke, modal, exit
        self.invoke_method = invoke
        self.modal_method = modal
        self.exit_method = exit

        return self.invoke(context, event)

    dot_color = Vector(preference.color.snap_point)
    dot_color_high = Vector(preference.color.snap_point_highlight)

    dot_colors = {
    'VERT': dot_color, 'VERT_HIGH': dot_color_high,
    'EDGE': dot_color, 'EDGE_HIGH': dot_color_high,
    'FACE': dot_color, 'FACE_HIGH': dot_color_high,
    }

    draw_dots_wire = preference.snap.dot_show_subdivision

    self.grid_handler = grid_handler(context, event, snap_type='GRID' if preference.snap.grid else 'DOTS', snapable_types=snapable, selection_only=True, alignment=alignment, override_matrix=override_matrix, divisions=1, grid_units=units, cell_count=cell_count, dot_alignment=dot_alignment, dot_alignment_ignore_flat=ignore_flat, enabled_dots=enabled_dots, cast_override=cast_override, surface_offset=self.surface_offset, dot_divisions=0, dot_colors=dot_colors, draw_dots_wire=draw_dots_wire)

    if not self.grid_handler.initialized:
        return {'PASS_THROUGH'}

    bc.snap.__class__.operator = self
    self.grid_color = Vector(preference.color.grid_wire)
    self.grid_color[3] *= 0.25
    self.grid_handler.grid_color = self.grid_color
    self.plane_color = Vector(getattr(preference.color, self.tool.mode.lower())) if preference.display.grid_mode else Vector(preference.color.grid)
    self.grid_handler.plane_color = self.plane_color
    self.border_color = Vector(preference.color.grid_wire)
    self.grid_handler.border_color = self.border_color
    self.grid_handler.border_f_color = Vector((1,1,1,1)) - self.border_color
    self.grid_handler.border_f_color[3] = 1

    self.grid_handler.rotation_snap = preference.snap.rotate_angle
    self.grid_handler.dot_preview = preference.snap.dot_preview

    dpi_factor = screen.dpi_factor()

    self.grid_handler.dot_size = preference.display.snap_dot_size * dpi_factor
    self.grid_handler.dot_snap_radius = self.grid_handler.dot_size * preference.display.snap_dot_factor
    self.grid_handler.dot_preview_scale = preference.snap.dot_preview_scale
    self.grid_handler.grid_thickness =  preference.display.wire_width * dpi_factor

    self.init_overlays = {
        'show_ortho_grid' : context.space_data.overlay.show_ortho_grid,
        'show_floor' : context.space_data.overlay.show_floor
    }

    if preference.snap.grid:
        if preference.snap.toggle_ortho_grid:
            context.space_data.overlay.show_ortho_grid = False

        if preference.snap.toggle_floor:
            context.space_data.overlay.show_floor = False

    self.grid_handler.front_draw = preference.snap.front_draw if surface not in {'VIEW', 'WORLD'} else True

    self.snap = type('snap', (), {})
    self.snap.running = True
    self.snap.grid_active = preference.snap.grid
    self.snap.edge_index = -1
    self.snap.face_index = -1
    self.snap.point = None
    self.snap.matrix = self.grid_handler.snap_matrix.normalized()
    self.snap.matrix.translation = self.grid_handler.snap_matrix.translation
    self.snap.snap_world = self.grid_handler.snap_world.copy()
    self.snap.object = context.active_object

    bc.snap.location = self.grid_handler.snap_matrix.translation
    bc.snap.hit = False

    bpy.app.handlers.load_pre.append(file_load_handler)
    bpy.app.handlers.load_factory_startup_post.append(file_load_handler)

    context.window_manager.modal_handler_add(self)

    self.grid_handler.start(context, event)

    redraw_areas(context)

    return {'RUNNING_MODAL'}


def exit(self, context):
    bc = context.scene.bc
    preference = addon.preference()

    grid_handler = getattr(self, 'grid_handler', False)

    if grid_handler and grid_handler.snap_type != 'DOTS':
        for key, val in self.init_overlays.items():
            setattr(context.space_data.overlay, key, val)

    if grid_handler:
        self.grid_handler.purge()

    bc.snap.operator = None
    bc.snap.__class__.operator = None

    bc.snap.hit = False

    redraw_areas(context)

    return {'FINISHED'}


def file_load_handler(var):
    bc = bpy.context.scene.bc

    if bc.snap.operator:
        bc.snap.operator.exit(bpy.context)

