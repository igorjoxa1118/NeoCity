import bpy, bmesh, mathutils, math, gpu
from mathutils import Matrix, Vector
from gpu_extras.batch import batch_for_shader
from bpy_extras import view3d_utils
from math import sin, cos
from ....utility.screen import dpi_factor
from .... utility import addon
from ....utils.grid import surface_normal
from ....utils.space_3d import ray_cast_objects, get_3D_point_from_mouse


class Edit_Line:
    def __init__(self, op, context, event):
        # Mesh
        self.obj = context.active_object
        self.mesh = self.obj.data
        self.backup = self.mesh.copy()
        # Cut Line
        self.cut_plane_co = Vector()
        self.snap_plane_no = None # Special case override
        self.__angle = 0
        # Drawing
        self.circle_center = mouse_vector(event)
        self.snap_point = None
        self.radius = 10 * dpi_factor(min=.5)
        built_in_shader = 'UNIFORM_COLOR' if bpy.app.version[0] >=4 else '2D_UNIFORM_COLOR'
        self.shader = gpu.shader.from_builtin(built_in_shader)
        self.circle_batch = None
        self.snap_batch = None
        self.cut_line_batch = None
        # Screen
        width = context.area.width
        height = context.area.height
        screen = Vector((width, height))
        self.screen_scale = screen.magnitude
        self.screen_center = Vector((width * .5, height * .5))

    @property
    def angle(self):
        return round(math.degrees(self.__angle), 0)

    @angle.setter
    def angle(self, val):
        self.__angle = math.radians(val)
        if abs(math.degrees(self.__angle)) > 360:
            self.__angle = 0
        self.setup_batch()

    # --- ACTIONS --- #

    def update(self, op, context, event):

        if op.form.active():
            return

        bm = self.open_bmesh(context)
        if not bm: return

        # Reset Overrides
        self.snap_plane_no = None

        # Reset Rotation
        if event.type == 'R' and event.value == 'PRESS':
            self.__angle = 0

        # Rotate / Possible Cut
        if event.alt:
            self.rotate(context, event, bm)
            self.circle_center = self.point_3d_to_2d(context, self.cut_plane_co)
            self.setup_batch()
            # Cut
            if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
                self.knife(context, bm)

            self.close_bmesh(context, bm)
            return

        # Snap
        if event.ctrl:
            coord_3d = self.snapped_vert_coord(context, event, bm)
            if coord_3d:
                self.cut_plane_co = coord_3d
            else:
                self.cut_plane_co = self.point_2d_to_3d(context, mouse_vector(event))
        # Mouse
        else:
            self.cut_plane_co = self.point_2d_to_3d(context, mouse_vector(event))

        self.circle_center = self.point_3d_to_2d(context, self.cut_plane_co)
        self.setup_batch()

        # Cut
        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            self.knife(context, bm)

        self.close_bmesh(context, bm)

        # Wire Fade
        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            if context.mode != 'EDIT_MESH':
                bpy.ops.hops.draw_wire_mesh_launcher('INVOKE_DEFAULT', target='SELECTED')

    # --- UTILS --- #

    def open_bmesh(self, context):
        bm = None
        if context.mode == 'EDIT_MESH':
            bm = bmesh.from_edit_mesh(self.mesh)
        else:
            bm = bmesh.new()
            bm.from_mesh(self.mesh)
        return bm
    

    def close_bmesh(self, context, bm):
        if context.mode == 'EDIT_MESH':
            bmesh.update_edit_mesh(self.mesh)
        else:
            bm.to_mesh(self.mesh)
            bm.free()


    def knife(self, context, bm):
        # Cut Geo
        geo = None
        if context.mode == 'EDIT_MESH':
            geo = []
            geo.extend( [f for f in bm.faces if f.select] )
            geo.extend( [e for e in bm.edges if e.select] )
            geo.extend( [v for v in bm.verts if v.select] )
        else:
            geo = bm.faces[:] + bm.edges[:] + bm.verts[:]
        if not geo: return

        # Transform
        bmesh.ops.transform(bm, matrix=self.obj.matrix_world, space=Matrix(), verts=bm.verts)

        plane_no = Vector()

        # Vert snap override
        if self.snap_plane_no != None:
            plane_no = self.snap_plane_no

        # Regular angle
        else:
            # Cut point to screen
            casted = self.point_3d_to_2d(context, self.cut_plane_co)
            rotated = Vector((cos(self.__angle), sin(self.__angle)))
            rotated.normalized()

            # Screen point along cut line
            point_2d = casted + rotated * (self.screen_scale * .5)
            p3 = self.point_2d_to_3d(context, point_2d)

            vn = view_normal(context)

            p1 = self.cut_plane_co
            p2 = p1 + vn

            plane_no = surface_normal(p1, p2, p3)

        # Mem Faces
        sel_faces = [f for f in bm.faces if f.select]

        # Cut
        ret = bmesh.ops.bisect_plane(bm,
            geom=geo,
            dist=0.0001,
            plane_co=self.cut_plane_co,
            plane_no=plane_no,
            use_snap_center=True,
            clear_outer=False,
            clear_inner=False)

        # Select
        for elem in ret['geom_cut']:
            if isinstance(elem, bmesh.types.BMEdge):
                for face in elem.link_faces:
                    face.select_set(True)
        # Transform
        bmesh.ops.transform(bm, matrix=self.obj.matrix_world.inverted(), space=Matrix(), verts=bm.verts)


    def rotate(self, context, event, bm):

        # Vert Align Rotation
        if event.ctrl:
            target = self.snapped_vert_coord(context, event, bm)
            if target:
                if target == self.cut_plane_co: return
                plane_co = self.point_3d_to_2d(context, self.cut_plane_co)
                target_co = self.point_3d_to_2d(context, target)
                
                diff_vec = plane_co - target_co
                self.__angle = diff_vec.angle_signed(Vector((1,0)), 0)

                # Override
                vn = view_normal(context)
                p1 = self.cut_plane_co
                p2 = target
                p3 = target + vn
                self.snap_plane_no = surface_normal(p1, p2, p3).normalized()

                # Drawing
                self.snap_point = target_co
                return

        # Mouse Rotation
        mouse = mouse_vector(event) - self.circle_center
        self.__angle = mouse.angle_signed(Vector((1,0)), 0)


    def snapped_vert_coord(self, context, event, bm):
        # Raycast
        mouse = mouse_vector(event)
        origin = view3d_utils.region_2d_to_origin_3d(context.region, context.space_data.region_3d, mouse)
        direction = view3d_utils.region_2d_to_vector_3d(context.region, context.space_data.region_3d, mouse)
        result, location, normal, index, object, matrix = ray_cast_objects(context, origin, direction, [self.obj], evaluated=False)

        if not result:
            return None

        # Closest Point
        coords = [self.obj.matrix_world @ v.co for v in bm.verts]
        coord_3d = None
        compare = None
        for coord in coords:
            magnitude = (location - coord).magnitude
            if coord_3d == None or magnitude < compare:
                coord_3d = coord
                compare = magnitude

        return coord_3d


    def point_2d_to_3d(self, context, point):
        rv3d = context.region_data
        return get_3D_point_from_mouse(point, context, rv3d.view_location, view_normal(context))


    def point_3d_to_2d(self, context, point_3d):
        region = context.region
        rv3d = context.region_data
        return view3d_utils.location_3d_to_region_2d(region, rv3d, point_3d, default=self.screen_center)


    def setup_batch(self):

        # Center Circle
        points = []
        for i in range(32):
            angle = i * 3.14159 * 2 / 32
            x = self.circle_center.x + (math.cos(angle) * self.radius)
            y = self.circle_center.y + (math.sin(angle) * self.radius)
            points.append((x, y))
        points.append(points[0])
        self.circle_batch = batch_for_shader(self.shader, 'LINE_STRIP', {"pos": points})

        # Snap Circle
        self.snap_batch = None
        if self.snap_plane_no != None:
            points = []
            for i in range(32):
                angle = i * 3.14159 * 2 / 32
                x = self.snap_point.x + (math.cos(angle) * self.radius)
                y = self.snap_point.y + (math.sin(angle) * self.radius)
                points.append((x, y))
            points.append(points[0])
            self.snap_batch = batch_for_shader(self.shader, 'LINE_STRIP', {"pos": points})

        # Line
        rotated = Vector((cos(self.__angle), sin(self.__angle)))
        rotated.normalized()
        points = [
            self.circle_center + rotated * self.screen_scale,
            self.circle_center - rotated * self.screen_scale]
        self.cut_line_batch = batch_for_shader(self.shader, 'LINES', {"pos": points})

    # --- EXITS --- #

    def __common_exit(self, context):
        if self.backup.name in bpy.data.meshes:
            bpy.data.meshes.remove(self.backup)


    def confirm_exit(self, context):
        self.__common_exit(context)


    def cancel_exit(self, context):

        if context.mode == 'EDIT_MESH':
            bm = bmesh.from_edit_mesh(self.mesh)
            bmesh.ops.delete(bm, geom=bm.verts, context='VERTS')
            bmesh.update_edit_mesh(self.mesh)
            bm.from_mesh(self.backup)
            bmesh.update_edit_mesh(self.mesh)
            self.obj.update_from_editmode()
            self.__common_exit(context)
            return

        bm = bmesh.new()
        bm.from_mesh(self.mesh)
        bmesh.ops.delete(bm, geom=bm.verts, context='VERTS')
        bm.from_mesh(self.backup)
        bm.to_mesh(self.mesh)
        bm.free()
        self.__common_exit(context)

    # --- SHADER --- #

    def draw_2d(self, context):

        if not self.circle_batch: return

        #Enable(GL_LINE_SMOOTH)
        gpu.state.blend_set('ALPHA')
        gpu.state.line_width_set(2)

        self.shader.bind()
        self.shader.uniform_float("color", (0,0,0,1))
        self.circle_batch.draw(self.shader)
        self.cut_line_batch.draw(self.shader)

        if self.snap_batch:
            self.shader.uniform_float("color", (0,1,0,1))
            self.snap_batch.draw(self.shader)
        
        gpu.state.blend_set('NONE')

# --- UTILS --- #

def view_normal(context):
    view_quat = context.region_data.view_rotation
    view_normal = view_quat @ Vector((0,0,1))
    view_normal.normalized()
    return view_normal


def vec_angle(vec_a, vec_b):
    vec_a_norm = vec_a.normalized()
    vec_b_norm = vec_b.normalized()
    dot = vec_a_norm.dot(vec_b_norm)
    return math.degrees(math.acos(dot))


def mouse_vector(event):
    return Vector((event.mouse_region_x, event.mouse_region_y))