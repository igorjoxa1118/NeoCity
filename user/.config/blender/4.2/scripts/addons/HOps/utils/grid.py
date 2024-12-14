import bpy, mathutils, math, gpu, bmesh
from math import cos, sin, radians, degrees
from mathutils import Vector, Matrix, Quaternion, Euler, geometry
from gpu_extras.batch import batch_for_shader
from bpy_extras import view3d_utils

from .. utility import addon
from ..utility.screen import dpi_factor
from .. utility import math as hops_math
from . space_3d import get_3D_point_from_mouse, get_2d_point_from_3d_point, scene_ray_cast


class Grid_Data:
    def __init__(self, key, active, shader_type):
        self.key = key
        self.active = active

        self.shader_grid_points = []
        self.shader_border_points = []
        self.all_points = []

        self.u = 10 # Along X (2d)
        self.v = 10 # Along Y (2d)
        self.size_x = 2
        self.size_y = 2
        self.mat = Matrix()

        self.boxelize = False

        self.color = addon.preference().color.grid_system_color
        self.shader = gpu.shader.from_builtin(shader_type)
        self.grid_batch = None
        self.border_batch = None


class Grid_3D(Grid_Data):
    def __init__(self, key, active):
        built_in_shader = 'UNIFORM_COLOR' if bpy.app.version[0] >= 4 else '3D_UNIFORM_COLOR'
        super().__init__(key, active, built_in_shader)


    def locate_grid(self, context, event, method='raycast'):
    
        if method == 'raycast':
            hit, location, normal, index, object, matrix = scene_ray_cast(context, event)
            if not hit: return False
            self.mat = surface_matrix(object, matrix, location, normal, location)
            self._setup_batch()
            return True

        return False


    def alter_grid(self, u=None, v=None, loc=None, rot=None, size_x=None, size_y=None):

        if u: self.u = u if u > 2 else 2
        if v: self.v = v if v > 2 else 2

        if loc and not rot:
            rot = self.mat.decompose()[1]
            self.mat = loc_rot_mat_3d(loc, rot)

        elif not loc and rot:
            loc = self.mat.decompose()[0]
            self.mat = loc_rot_mat_3d(loc, rot)
            
        if rot and loc:
            self.mat = loc_rot_mat_3d(loc, rot)

        if size_x: self.size_x = size_x
        if size_y: self.size_y = size_y

        self._setup_batch()


    def grid_point(self, context, event):

        point = self.mat @ Vector()
        rot = self.mat.decompose()[1]
        normal = rot @ Vector((0,0,1))
        point = get_3D_point_from_mouse(mouse_pos(event), context, point, normal)
        return compare_point_to_points(point, self.all_points)


    def _update(self, context, event):
        pass


    def _setup_batch(self):

        self._set_shader_points()
        self._set_grid_points()

        # Transform Grid
        indices = [(i, i + 1) for i in range(0, len(self.shader_grid_points), 2)]
        self.grid_batch = batch_for_shader(self.shader, 'LINES', {"pos": self.shader_grid_points}, indices=indices)

        # Border
        self.shader_border_points = [
            Vector((0, 0, 0)),
            Vector((0, self.size_y, 0)),
            Vector((self.size_x, self.size_y, 0)),
            Vector((self.size_x, 0, 0))]

        for i in range(4):
            # Center
            self.shader_border_points[i] -= Vector((self.size_x * .5, self.size_y * .5, 0))
            # Transform
            self.shader_border_points[i] = self.mat @ self.shader_border_points[i]

        indices = [[i, (i + 1) % 4] for i in range(4)]
        self.border_batch = batch_for_shader(self.shader, 'LINES', {"pos": self.shader_border_points}, indices=indices)


    def _set_grid_points(self):

        square_width_x = self.size_x / self.u
        square_width_y = self.size_y / self.v

        offset = Vector((self.size_x * .5, self.size_y * .5, 0))

        self.all_points = []
        append = self.all_points.append
        for i in range(self.u + 1):
            for j in range(self.v + 1):
                append( self.mat @ (Vector(( square_width_x * i, square_width_y * j, 0)) - offset ))


    def _set_shader_points(self):

        # Generate Flat Grid
        square_width_x = self.size_x / self.u
        square_width_y = self.size_y / self.v

        self.shader_grid_points = []
        append = self.shader_grid_points.append
        for i in range(1, self.u, 1):
            append( Vector((square_width_x * i, 0          , 0)) )
            append( Vector((square_width_x * i, self.size_y, 0)) )

        for i in range(1, self.v, 1):
            if i == 0: continue
            append( Vector((0          , square_width_y * i, 0)) )
            append( Vector((self.size_x, square_width_y * i, 0)) )

        for i in range(len(self.shader_grid_points)):
            # Center
            self.shader_grid_points[i] -= Vector((self.size_x * .5, self.size_y * .5, 0))
            # Transform
            self.shader_grid_points[i] = self.mat @ self.shader_grid_points[i]


    def _draw_2d(self, context):
        pass


    def _draw_3d(self, context):
        
        if not self.grid_batch: return
        #Enable(GL_LINE_SMOOTH)
        gpu.state.blend_set('ALPHA')

        self.shader.bind()
        
        gpu.state.line_width_set(2)
        self.shader.uniform_float("color", self.color)
        self.grid_batch.draw(self.shader)
    

        gpu.state.line_width_set(4)
        self.shader.uniform_float("color", self.color)
        self.border_batch.draw(self.shader)
    
        #Disable(GL_LINE_SMOOTH)
        gpu.state.blend_set('NONE')


class Grid_2D(Grid_Data):
    def __init__(self, key, active):

        built_in_shader = 'UNIFORM_COLOR' if bpy.app.version[0] >= 4 else '2D_UNIFORM_COLOR'
        super().__init__(key, active, built_in_shader)
        self.size_x = 100
        self.size_y = 100
        self.boxelize = True

        self.debug_points = []


    def locate_grid(self, context, event, method='mouse_position', obj=None):

        if method == 'mouse_position':
            loc = mouse_pos(event).to_3d()
            self.mat = Matrix.Translation(loc)
            self._setup_batch()

        elif method == 'object_bounds' or 'selected_verts':
            if not obj: return False

            points = self.selection_bounding_points(context, obj, method)

            # Rotate
            center = self.points_center(points)
            rot = self.mat.decompose()[1]

            size = hops_math.dimensions_2d(points)
            bbp = [
                Vector((center.x - size.x * .5, center.y - size.y * .5)),
                Vector((center.x - size.x * .5, center.y + size.y * .5)),
                Vector((center.x + size.x * .5, center.y + size.y * .5)),
                Vector((center.x + size.x * .5, center.y - size.y * .5))
            ]

            rotated_points = []
            for i, p in enumerate(bbp[:]):
                p = p - center
                p = Vector((p.x, p.y, 0))
                p = rot @ p
                p = Vector((p.x, p.y))
                p = p + center
                rotated_points.append(p)

            # Size
            size = hops_math.dimensions_2d(points + rotated_points)
            self.size_x = size.x
            self.size_y = size.y

            loc = hops_math.coords_to_center_2d(points).to_3d()
            loc_mat = Matrix.Translation(loc)
            rot_mat = rot.to_matrix().to_4x4()
            self.mat = loc_mat @ rot_mat

            self._setup_batch()
            return True
    
        return False


    def selection_bounding_points(self, context, obj, method='object_bounds'):
        region = context.region
        rv3d = context.region_data

        if method == 'object_bounds':
            bb_points = object_bounds(obj)
        elif method == 'selected_verts':
            bb_points = selected_verts_bounds(obj)
        else:
            return []
        
        points = []
        append = points.append
        for bbp in bb_points:
            point = view3d_utils.location_3d_to_region_2d(region, rv3d, bbp)
            if point: append(point)

        return points


    def points_center(self, points):
        return hops_math.coords_to_center_2d(points)


    def alter_grid(self, u=None, v=None, loc=None, rot=None, size_x=None, size_y=None):

        if self.boxelize:
            if u: self.u = u if u > 2 else 2
            if v: self.v = v if v > 2 else 2
        else:
            if u: self.u = u if u > 0 else 1
            if v: self.v = v if v > 0 else 1

        if loc and not rot:
            rot = self.mat.decompose()[1]
            self.mat = loc_rot_mat_3d(loc, rot)

        elif not loc and rot:
            loc = self.mat.decompose()[0]
            self.mat = loc_rot_mat_3d(loc, rot)
            
        if rot and loc:
            self.mat = loc_rot_mat_3d(loc, rot)

        if size_x: self.size_x = size_x
        if size_y: self.size_y = size_y

        self._setup_batch()


    def grid_point(self, context, event):
        point = mouse_pos(event)
        return compare_point_to_points(point, self.all_points)


    def to_object_bounds(self, context, obj, method='object_bounds'):
        '''Returns 3D grid data for a Gird -> Object Bounds relation.'''

        # 3D border points
        casted_border = self._border_to_3d(context)

        # Get view point location
        view_loc = self._view_location(context)

        # Closest point to camera
        bounding_box = None
        if method == 'object_bounds':
            bounding_box = object_bounds(obj)
        elif method == 'selected_verts':
            bounding_box = selected_verts_bounds(obj)
        if bounding_box == None: return

        closest_bbp = compare_point_to_points(view_loc, bounding_box, closest=True)
        farthest_bbp = compare_point_to_points(view_loc, bounding_box, closest=False)

        # Distance to object
        view_normal = view_direction(context)

        # Project each border point onto closest plane
        projected_border = []
        for point in casted_border:
            end_point = point - view_normal
            loc = geometry.intersect_line_plane(point, end_point, closest_bbp, view_normal)

            round_vector(loc)
            if loc: projected_border.append(loc)
        
        # UV lines from project border
        u_lines, v_lines = self._create_uv_from_3d_border(projected_border)

        # Distance from from obj bounds to back obj bounds
        obj_bounds_view_depth = geometry.distance_point_to_plane(farthest_bbp, closest_bbp, view_normal)

        return {
            'casted_border' : casted_border,
            'u_lines' : u_lines,
            'v_lines' : v_lines,
            'clostest_point' : closest_bbp,
            'farthest_point' : farthest_bbp,
            'view_normal' : view_normal,
            'obj_bounds_view_depth' : obj_bounds_view_depth}


    def _create_uv_from_3d_border(self, border_points):
        u_lines = []
        v_lines = []

        BL = border_points[0]
        BR = border_points[3]
        TL = border_points[1]
        TR = border_points[2]

        for i in range(self.u + 1):
            factor = (1 / self.u) * i
            u_lines.append((BL.lerp(BR, factor), TL.lerp(TR, factor)))

        for i in range(self.v + 1):
            factor = (1 / self.v) * i
            v_lines.append((BL.lerp(TL, factor), BR.lerp(TR, factor)))
        
        return u_lines, v_lines


    def _view_location(self, context):
        rv3d = None
        if hasattr(context.region, 'data'):
            rv3d = context.region.data
        else:
            rv3d = context.space_data.region_3d
        if not rv3d: return

        view = rv3d.view_matrix.inverted()
        clip_end = rv3d.perspective_matrix.inverted().decompose()[2][2]
        loc = (view.decompose()[1] @ Vector((0,0,clip_end))) * -1
        loc += view.decompose()[0]
        return loc


    def _border_to_3d(self, context):
        region = context.region
        rv3d = context.region_data
        points = []

        for point in self.shader_border_points:
            loc = view3d_utils.region_2d_to_location_3d(region, rv3d, point, rv3d.view_location)
            points.append(loc)
        return points


    def _update(self, context, event):
        pass


    def _setup_batch(self):

        self._boxelize_dims()
        self._set_shader_points()
        self._set_grid_points()

        # Transform Grid
        indices = [(i, i + 1) for i in range(0, len(self.shader_grid_points), 2)]
        self.grid_batch = batch_for_shader(self.shader, 'LINES', {"pos": self.shader_grid_points}, indices=indices)

        # Border
        self.shader_border_points = [
            Vector((0, 0, 0)),
            Vector((0, self.size_y, 0)),
            Vector((self.size_x, self.size_y, 0)),
            Vector((self.size_x, 0, 0))]

        for i in range(4):
            # Center
            self.shader_border_points[i] -= Vector((self.size_x * .5, self.size_y * .5, 0))
            # Transform
            self.shader_border_points[i] = (self.mat @ self.shader_border_points[i]).to_2d()

        indices = [[i, (i + 1) % 4] for i in range(4)]
        self.border_batch = batch_for_shader(self.shader, 'LINES', {"pos": self.shader_border_points}, indices=indices)


    def _boxelize_dims(self):
        '''Uses the U for auto divisions'''

        if not self.boxelize: return

        x_gap = self.size_x / self.u

        if round(x_gap, 5) == 0: return

        y_splits = self.size_y / x_gap
        self.v = int(round(y_splits))

        self.v = 1 if self.v < 1 else self.v
        y_gap = self.size_y / self.v

        if y_gap > x_gap:
            self.size_x = y_gap * self.u
        else:
            self.size_y = x_gap * self.v


    def _set_grid_points(self):

        square_width_x = self.size_x / self.u
        square_width_y = self.size_y / self.v

        offset = Vector((self.size_x * .5, self.size_y * .5, 0))

        self.all_points = []
        append = self.all_points.append
        for i in range(self.u + 1):
            for j in range(self.v + 1):
                append( (self.mat @ (Vector(( square_width_x * i, square_width_y * j, 0)) - offset )).to_2d() )


    def _set_shader_points(self):

        # Generate Flat Grid
        square_width_x = self.size_x / self.u
        square_width_y = self.size_y / self.v

        self.shader_grid_points = []
        append = self.shader_grid_points.append
        for i in range(1, self.u, 1):
            append( Vector((square_width_x * i, 0          , 0)) )
            append( Vector((square_width_x * i, self.size_y, 0)) )

        for i in range(1, self.v, 1):
            if i == 0: continue
            append( Vector((0          , square_width_y * i, 0)) )
            append( Vector((self.size_x, square_width_y * i, 0)) )

        for i in range(len(self.shader_grid_points)):
            # Center
            self.shader_grid_points[i] -= Vector((self.size_x * .5, self.size_y * .5, 0))
            # Transform
            self.shader_grid_points[i] = (self.mat @ self.shader_grid_points[i]).to_2d()


    def _draw_2d(self, context):

        if not self.grid_batch: return
        #Enable(GL_LINE_SMOOTH)
        gpu.state.blend_set('ALPHA')

        self.shader.bind()
        
        gpu.state.line_width_set(1)
        self.shader.uniform_float("color", self.color)
        self.grid_batch.draw(self.shader)
    

        gpu.state.line_width_set(2)
        self.shader.uniform_float("color", self.color)
        self.border_batch.draw(self.shader)
    
        if self.debug_points:
            built_in_shader = 'UNIFORM_COLOR' if bpy.app.version[0] >=4 else '2D_UNIFORM_COLOR'
            shader = gpu.shader.from_builtin(built_in_shader)
            batch = batch_for_shader(shader, 'POINTS', {'pos': self.debug_points})
            shader.bind()
            shader.uniform_float('color', (1,0,0,1))
            gpu.state.point_size_set(6)
            batch.draw(shader)
            del shader
            del batch



        #Disable(GL_LINE_SMOOTH)
        gpu.state.blend_set('NONE')


    def _draw_3d(self, context):
        pass


class Grid_Controller:
    def __init__(self):
        self.grids_3d = []
        self.grids_2d = []
    

    def create_grid(self, key=0, active=True, mode_type='3D'):

        # 3D Grids
        if mode_type == '3D':
            grid = Grid_3D(key, active)
            self.grids_3d.append(grid)
            return grid

        # 2D Grids
        elif mode_type == '2D':
            grid = Grid_2D(key, active)
            self.grids_2d.append(grid)
            return grid

        return None


    def get_grid(self, key=0, mode_type='3D'):

        # 3D Grids
        if mode_type == '3D':
            for grid in self.grids_3d:
                if grid.key == key:
                    return grid

        # 2D Grids
        elif mode_type == '2D':
            for grid in self.grids_2d:
                if grid.key == key:
                    return grid

        return None


    def update(self, context, event):

        # 3D Grids
        for grid in self.grids_3d:
            if grid.active:
                grid._update(context, event)

        # 2D Grids
        for grid in self.grids_2d:
            if grid.active:
                grid._update(context, event)


    def draw_2d(self, context):

        # 3D Grids
        for grid in self.grids_3d:
            if grid.active:
                grid._draw_2d(context)
                
        # 2D Grids
        for grid in self.grids_2d:
            if grid.active:
                grid._draw_2d(context)


    def draw_3d(self, context):

        # 3D Grids
        for grid in self.grids_3d:
            if grid.active:
                grid._draw_3d(context)

        # 2D Grids
        for grid in self.grids_2d:
            if grid.active:
                grid._draw_3d(context)

# --- UTILS --- #

def surface_normal(point_a, point_b, point_c):
    u = point_b - point_a
    v = point_c - point_a
    normal = Vector((
        (u.y * v.z) - (u.z * v.y),
        (u.z * v.x) - (u.x * v.z),
        (u.x * v.y) - (u.y * v.x)))
    round_vector(normal)
    normal.normalize()
    return normal


def round_vector(vector, precision=4):
    vector.x = round(vector.x, 4)
    vector.y = round(vector.y, 4)
    vector.z = round(vector.z, 4)


def view_direction(context):
    return context.region_data.view_rotation @ Vector((0,0,1))


def object_bounds(obj):
    return hops_math.coords_to_bounds([obj.matrix_world @ v.co for v in obj.data.vertices])


def selected_verts_bounds(obj):
    if obj.mode == 'EDIT':
        bm = bmesh.from_edit_mesh(obj.data)
        return hops_math.coords_to_bounds([obj.matrix_world @ v.co for v in bm.verts if v.select])
    return hops_math.coords_to_bounds([obj.matrix_world @ v.co for v in obj.data.vertices if v.select])


def mesh_object_by_name(context, object_name=''):
    for obj in context.view_layer.objects:
        if obj.name == object_name:
            if obj.type == 'MESH':
                return obj
    return None


def compare_point_to_points(point=Vector(), points=[], closest=True):
    chosen_point = None
    compare = None
    for p in points:
        dist = (point - p).magnitude
        # Getting closest point
        if closest:
            if not chosen_point or not compare or dist < compare:
                chosen_point = p
                compare = dist
        # Getting farthest point
        else:
            if not chosen_point or not compare or dist > compare:
                chosen_point = p
                compare = dist
    return chosen_point


def loc_rot_mat_3d(loc=(0,0,0), rot=(0,0,0), quat=None):
    loc = Matrix.Translation(loc)

    if quat:
        rot = quat
    else:
        rot = Euler((radians(rot[0]), radians(rot[1]), radians(rot[2])), 'XYZ')

    return loc.to_4x4() @ rot.to_matrix().to_4x4()    


def surface_matrix(obj, matrix, location, normal, position, orient_method='LOCAL', face_index=0, edge_index=0, force_edge=False):

    track_matrix = get_track_matrix(normal, matrix=matrix)

    custom_orient = False
    tangent = Vector((0, 0, 0))
    active_edges = []

    if orient_method == 'EDIT':
        bm = bmesh.from_edit_mesh(obj.data)
        active_edges = [elem for elem in bm.select_history if isinstance(elem, bmesh.types.BMEdge)]

        if active_edges:
            custom_orient = True
            v1, v2 = active_edges[0].verts

            _, rot, _ = matrix.decompose()
            rot_matrix = rot.to_matrix().to_4x4()

            tangent = (rot_matrix @ (v2.co - v1.co)).normalized()

    if orient_method != 'LOCAL' and not active_edges:
        custom_orient = True
        object_eval = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())

        bm = bmesh.new()
        bm.from_mesh(object_eval.data)
        bm.faces.ensure_lookup_table()

        if orient_method == 'TANGENT':
            tangent = bm.faces[face_index].calc_tangent_edge()

        elif orient_method == 'NEAREST':
            bm.edges.ensure_lookup_table()

            face = bm.faces[face_index]
            distance = 0.0
            index = 0

            for i, edge in enumerate(face.edges):
                edge = [obj.matrix_world @ v.co for v in edge.verts]
                current, normalized_distance = geometry.intersect_point_line(location, *edge)

                if normalized_distance > 1:
                    current = edge[1]
                elif normalized_distance < 0:
                    current = edge[0]

                length = (current - location).length

                if length < distance or not distance:
                    distance = length
                    index = i

            tangent = (face.edges[index].verts[0].co - face.edges[index].verts[1].co).normalized()

        elif orient_method == 'EDGE' or force_edge:
            bm.edges.ensure_lookup_table()
            edge = [e for e in bm.faces[face_index].edges][edge_index]
            tangent = (edge.verts[0].co - edge.verts[1].co).normalized()

            if not force_edge:
                if len(set([str(Vector((abs(f) for f in face.normal))) for face in edge.link_faces])) == 1 and len(edge.link_faces) > 1:
                    custom_orient = False

        elif orient_method == 'FACE_FIT':
            face = bm.faces[face_index]
            face_matrix = view3d.track_matrix(normal=face.normal)
            face_matrix.translation = face.calc_center_median()

            local_verts = [(face_matrix.inverted() @ vert.co).to_2d() for vert in face.verts]
            angle = geometry.box_fit_2d(local_verts)
            tangent = face_matrix.to_3x3() @ (Matrix.Rotation(-angle, 2) @ Vector((1, 0))).to_3d()

        tangent = (obj.matrix_world.to_3x3() @ tangent).normalized()

        bm.free()

    if custom_orient:
        mat = Matrix.Identity(3)
        cross = tangent.cross(normal)

        mat.col[0] = cross
        mat.col[1] = tangent
        mat.col[2] = normal

        track_quat = mat.to_quaternion()
        track_matrix = matrix.inverted() @ track_quat.to_matrix().to_4x4()

    track_matrix = matrix @ track_matrix
    track_matrix.translation = position

    return track_matrix


def get_track_matrix(normal=Vector(), location=Vector(), matrix=Matrix(), up='Z', align='Y'):
    track_mat = (matrix.copy().to_3x3().inverted() @ normal).to_track_quat(up, align).to_matrix().to_4x4()
    track_mat.translation = location if location != Vector() else matrix.translation
    return track_mat


def mouse_pos(event):
    return Vector((event.mouse_region_x, event.mouse_region_y))









