import bpy, bmesh
from mathutils import Matrix, Vector, geometry
import math
from .... utility import addon

from .interface import alter_form_layout
from .dice_line import mouse_vector

from ....utils.grid import Grid_Controller, surface_normal


class Edit_2D:
    def __init__(self, op, context, event):
        # States
        self.dissolve_original = False
        self.clean_faces = False
        self.rotating = False
        self.keep_sharps = True
        # Data
        self.cut_planes = []
        self.obj = context.active_object
        # Grid
        self.grid_controller = Grid_Controller()
        self.grid_controller.create_grid(key=0, active=True, mode_type='2D')
        # Screen
        width = context.area.width
        height = context.area.height
        self.screen_center = Vector((width * .5, height * .5))

    @property
    def segments(self):
        grid = self.grid_controller.get_grid(key=0, mode_type='2D')
        if not grid: return 0
        return grid.u

    @segments.setter
    def segments(self, val):
        grid = self.grid_controller.get_grid(key=0, mode_type='2D')
        if not grid: return
        val = int(val)
        grid.alter_grid(u=val, v=val)

    @property
    def u(self):
        grid = self.grid_controller.get_grid(key=0, mode_type='2D')
        if not grid: return 0
        return grid.u

    @u.setter
    def u(self, val):
        grid = self.grid_controller.get_grid(key=0, mode_type='2D')
        if not grid: return
        val = int(val)
        val = val if val > 0 else 1
        grid.alter_grid(u=val)

    @property
    def v(self):
        grid = self.grid_controller.get_grid(key=0, mode_type='2D')
        if not grid: return 0
        return grid.v

    @v.setter
    def v(self, val):
        grid = self.grid_controller.get_grid(key=0, mode_type='2D')
        if not grid: return
        val = int(val)
        val = val if val > 0 else 1
        grid.alter_grid(v=val)

    @property
    def rot(self):
        grid = self.grid_controller.get_grid(key=0, mode_type='2D')
        if not grid: return 0
        rot = grid.mat.decompose()[1]
        return round(math.degrees(rot.angle), 2)

    @rot.setter
    def rot(self, val):
        grid = self.grid_controller.get_grid(key=0, mode_type='2D')
        if not grid: return
        rot = grid.mat.decompose()[1]
        if val >= 180: val = 0
        elif val < 0: val = 179
        grid.alter_grid(rot=(0,0,val))

    # --- ACTIONS --- #

    def update(self, op, context, event):

        self.grid_controller.update(context, event)
        grid = self.grid_controller.get_grid(key=0, mode_type='2D')
        if not grid: return

        mouse_pos = mouse_vector(event)

        # Rotation
        if self.rotating:
            if op.form.active():
                self.rotating = False
                return

            method = 'selected_verts' if self.obj.mode == 'EDIT' else 'object_bounds'
            points = grid.selection_bounding_points(context, obj=self.obj, method=method)
            rot_center = grid.points_center(points)

            offset = mouse_pos - rot_center
            rot = Vector((1,0)).angle_signed(offset, None)

            if event.ctrl:
                deg = math.degrees(rot)
                rot = math.radians(base_round(deg, base=5))

            if rot == None:
                self.rotating = False
                return
            
            grid.alter_grid(rot=(0,0,math.degrees(-rot)))

        # Set to Grid X = 1
        if event.type == 'X' and event.value == 'PRESS':
            grid.boxelize = False
            grid.v = 1
            alter_form_layout(op, preset_label='2D_DICE')
        
        # Set to Grid Y = 1
        elif event.type == 'Y' and event.value == 'PRESS':
            grid.boxelize = False
            grid.u = 1
            alter_form_layout(op, preset_label='2D_DICE')

        # Boxelize
        elif event.type == 'B' and event.value == 'PRESS':
            self.toggle_boxelize(op)
            if grid.boxelize:
                if grid.u == 1 and grid.v == 1:
                    grid.u = 5
                    grid.v = 5

        # Dissolve Mode
        elif event.type == 'D' and event.value == 'PRESS':
            self.set_dissolve_original(context)

        # Clean faces
        elif event.type == 'C' and event.value == "PRESS":
            if not self.dissolve_original:
                self.clean_faces = not self.clean_faces
                bpy.ops.hops.display_notification(info=F'Clean Faces : {self.clean_faces}')

        # Rotate Grid
        elif event.type == 'R' and event.value == "PRESS":
            self.rotating = not self.rotating

        # Stop Rotation on Dot
        elif event.type == 'TAB' and event.value == 'PRESS':
            self.rotating = False

        # Dissolve Sharps
        elif event.type == 'S' and event.value == 'PRESS':
            if self.dissolve_original:
                self.keep_sharps = not self.keep_sharps
                bpy.ops.hops.display_notification(info=F"Keep Sharp Edges : {'ON' if self.keep_sharps else 'OFF'}")

        # Scrolls
        if not op.form.active():
            self.actions(op, context, event, grid)

        # Grid Locate
        if self.obj.mode == 'EDIT':
            grid.locate_grid(context, event, method='selected_verts', obj=self.obj)
        else:
            grid.locate_grid(context, event, method='object_bounds', obj=self.obj)


    def actions(self, op, context, event, grid):

        # Scroll
        scroll = op.base_controls.scroll
        if scroll:
            if not grid.boxelize:
                if grid.u > 1:
                    grid.alter_grid(u=grid.u + scroll)

                if grid.v > 1:
                    grid.alter_grid(v=grid.v + scroll)
                
                if grid.v == 1 and grid.u == 1:
                    grid.alter_grid(u=grid.u + scroll, v=grid.v + scroll)

            else:
                grid.alter_grid(u=grid.u + scroll, v=grid.v + scroll)

    # --- UTILS --- #

    def knife(self, context, obj, grid_data):

        self.calc_cut_planes(grid_data)

        original_mode = context.mode
        if original_mode != 'EDIT_MESH':
            bpy.ops.object.mode_set(mode='EDIT')

        if self.clean_faces:
            bpy.ops.mesh.remove_doubles(threshold=addon.preference().property.meshclean_remove_threshold)
            bpy.ops.mesh.dissolve_limited(angle_limit=addon.preference().property.meshclean_dissolve_angle)

        mesh = obj.data
        bm = bmesh.from_edit_mesh(mesh)

        # Transform
        original_matrix = obj.matrix_world.copy()
        bmesh.ops.transform(bm, matrix=original_matrix, space=Matrix(), verts=bm.verts)

        if self.dissolve_original:
            self.dissolve_dice(bm, grid_data, original_mode)
        else:
            self.bisect(bm, original_mode)

        # Transform
        bmesh.ops.transform(bm, matrix=original_matrix.inverted(), space=Matrix(), verts=bm.verts)

        # Update and Free
        bm.normal_update()
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bmesh.update_edit_mesh(mesh)

        if original_mode != 'EDIT_MESH':
            bpy.ops.object.mode_set(mode='OBJECT')


    def dissolve_dice(self, bm, grid_data, original_mode):

        # Original Edges
        original_edges = [e for e in bm.edges if e.select]

        # Select Boundary
        faces = [f for f in bm.faces if f.select]
        bpy.ops.mesh.region_to_loop()

        # Remove boundary edges
        sel_edges = [e for e in bm.edges if e.select]
        for e in original_edges[:]:
            if e in sel_edges:
                original_edges.remove(e)

        boundary_verts = [v for v in bm.verts if v.select]

        # Select faces
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
        bpy.ops.mesh.select_all(action='DESELECT')
        for f in faces:
            f.select_set(True)

        # Dice
        self.bisect(bm, original_mode)

        faces = [f for f in bm.faces if f.select]
        bpy.ops.mesh.region_to_loop()
        boundary_edges = [e for e in bm.edges if e.select]
        bpy.ops.mesh.select_all(action='DESELECT')

        self.select_edge_loops_within_selected_faces(bm, faces, original_edges, boundary_edges)

        dissolve_edges = [e for e in bm.edges if e.select]

        tolerance = 0.0001

        # Remove edges aligned to cut planes
        for edge in dissolve_edges[:]:
            for plane_co, plane_no in self.cut_planes:
                
                c1 = edge.verts[0].co
                c2 = edge.verts[1].co
                d1 = geometry.distance_point_to_plane(c1, plane_co, plane_no)
                d2 = geometry.distance_point_to_plane(c2, plane_co, plane_no)

                if abs(d1) < tolerance:
                    if abs(d2) < tolerance:
                        if edge in dissolve_edges:
                            dissolve_edges.remove(edge)
                            edge.select_set(False)
                        continue

        # Remove Sharp edges
        if self.keep_sharps:
            for edge in dissolve_edges[:]:
                if edge.smooth == False:
                    if edge in dissolve_edges:
                        dissolve_edges.remove(edge)

        bmesh.ops.dissolve_edges(bm, edges=dissolve_edges, use_verts=False)

        # Remove verts at interseciton
        dissolve_verts = [v for v in bm.verts if v.is_valid and v.select and v not in boundary_verts]
        for vert in dissolve_verts[:]:
            skip = False
            for plane_co_1, plane_no_1 in self.cut_planes:
                if skip: break
                for plane_co_2, plane_no_2 in reversed(self.cut_planes):
                    if plane_no_1 == plane_no_2: continue

                    co = vert.co
                    d1 = geometry.distance_point_to_plane(co, plane_co_1, plane_no_1)
                    d2 = geometry.distance_point_to_plane(co, plane_co_2, plane_no_2)

                    if abs(d1) < tolerance and abs(d2) < tolerance:
                        if vert in dissolve_verts:
                            dissolve_verts.remove(vert)
                            skip = True
                            break

        # Remove Sharp verts (With more than 2 edges)
        if self.keep_sharps:
            for vert in dissolve_verts[:]:            
                for edge in vert.link_edges:
                    if edge.smooth == False:
                        if len(vert.link_edges) <= 2:
                            continue
                        if vert in dissolve_verts:
                            dissolve_verts.remove(vert)

        bmesh.ops.dissolve_verts(bm, verts=dissolve_verts)


    def select_edge_loops_within_selected_faces(self, bm, faces, edges, boundary_edges):

        for edge in edges:

            # The edge is on the boundary
            for face in edge.link_faces:
                if face not in faces: continue

            # Loops are within boundary
            for loop in edge.link_loops:
                if loop.face not in faces: continue

            visited = []

            # Select
            for loop in edge.link_loops:
                start = loop

                while True:
                    valid = False
                    if start.face in faces:
                        if start not in visited:
                            if start.edge not in boundary_edges:
                                if start.link_loop_next.edge not in boundary_edges:
                                    valid = True
                                else:
                                    start.edge.select_set(True)

                    if valid:
                        visited.append(start)
                        start.edge.select_set(True)

                        if self.radial_count(start) > 3:
                            start = start.link_loop_next.link_loop_radial_next.link_loop_next.link_loop_radial_next.link_loop_next
                        else:
                            start = start.link_loop_next.link_loop_radial_next.link_loop_next
                    else:
                        break


    def radial_count(self, loop):
        count = 0
        start_edge = loop.edge
        current = loop
        while True:
            current = current.link_loop_next.link_loop_radial_next
            if current.edge == start_edge:
                return count
            count += 1


    def calc_cut_planes(self, grid_data):

        u_lines = grid_data['u_lines']
        v_lines = grid_data['v_lines']
        view_normal = grid_data['view_normal']
        obj_bounds_view_depth = grid_data['obj_bounds_view_depth']

        if round(obj_bounds_view_depth, 4) < .0001:
            obj_bounds_view_depth = 1
        offset = view_normal * obj_bounds_view_depth

        self.cut_planes = []

        def generate_planes(lines):
            for i in range(len(lines)):
                if i == 0 or i == len(lines) - 1: continue
                p1, p2 = lines[i]
                p3 = p1 + offset
                plane_normal = surface_normal(p1, p2, p3)

                if plane_normal.magnitude == 0:
                    plane_normal = (p1).cross(view_normal)

                self.cut_planes.append((p1, plane_normal))

        generate_planes(u_lines)
        generate_planes(v_lines)


    def bisect(self, bm, original_mode):

        for i in range(len(self.cut_planes)):
            geo = None
            if original_mode == 'EDIT_MESH':
                geo = []
                geo.extend( [f for f in bm.faces if f.select] )
                geo.extend( [e for e in bm.edges if e.select] )
                geo.extend( [v for v in bm.verts if v.select] )
            else:
                geo = bm.faces[:] + bm.edges[:] + bm.verts[:]
            if not geo: return

            p1, plane_normal = self.cut_planes[i]

            ret = bmesh.ops.bisect_plane(bm,
                geom=geo,
                dist=0.0001,
                plane_co=p1,
                plane_no=plane_normal,
                use_snap_center=True,
                clear_outer=False,
                clear_inner=False)
            for elem in ret['geom']:
                elem.select_set(True)

    # --- EXITS --- #

    def confirm_exit(self, context, event):
        grid = self.grid_controller.get_grid(key=0, mode_type='2D')
        if not grid: return
        obj = context.active_object

        grid_data = None
        if obj.mode == 'EDIT':
            grid_data = grid.to_object_bounds(context, obj, method='selected_verts')
        else:
            grid_data = grid.to_object_bounds(context, obj, method='object_bounds')
        if grid_data == None: return

        # Modifiers : Turn Off
        mod_data = {}
        for mod in obj.modifiers:
            mod_data[mod.name] = mod.show_viewport
            mod.show_viewport = False

        self.knife(context, obj, grid_data)

        # Modifiers : Turn On
        for key, value in mod_data.items():
            obj.modifiers[key].show_viewport = value

        original_mode = context.mode
        bpy.ops.hops.draw_wire_mesh_launcher('INVOKE_DEFAULT', target='SELECTED')
        if original_mode == 'EDIT_MESH':
            bpy.ops.object.mode_set(mode='EDIT')


    def cancel_exit(self, context):
        pass

    # --- SHADER --- #

    def draw_2d(self, context):
        self.grid_controller.draw_2d(context)

    # --- FORM --- #

    def set_u_to_one(self):
        grid = self.grid_controller.get_grid(key=0, mode_type='2D')
        if not grid: return
        if grid.u > 1:
            grid.alter_grid(u=1)
        else:
            grid.alter_grid(u=5)


    def u_botton_hook(self):
        if self.u != 1: return True
        return False


    def set_v_to_one(self):
        grid = self.grid_controller.get_grid(key=0, mode_type='2D')
        if not grid: return
        if grid.v > 1:
            grid.alter_grid(v=1)
        else:
            grid.alter_grid(v=5)


    def v_botton_hook(self):
        if self.v != 1: return True
        return False


    def set_dissolve_original(self, context):
        if context.mode == 'EDIT_MESH':
            self.dissolve_original = not self.dissolve_original
            msg = F'Dissolve Original : {self.dissolve_original}'
            if self.clean_faces and self.dissolve_original:
                msg += ' (Clean Faces : False)'
            bpy.ops.hops.display_notification(info=msg)

        else:
            bpy.ops.hops.display_notification(info="Edit Mode Required")
        
        if self.dissolve_original:
            self.clean_faces = False


    def dissolve_original_hook(self):
        return self.dissolve_original


    def is_boxelize(self):
        grid = self.grid_controller.get_grid(key=0, mode_type='2D')
        if not grid: return False
        return grid.boxelize


    def toggle_boxelize(self, op):
        grid = self.grid_controller.get_grid(key=0, mode_type='2D')
        if not grid: return
        grid.boxelize = not grid.boxelize
        alter_form_layout(op, preset_label='2D_DICE')


def base_round(num, base=5):
    return base * round(num / base)