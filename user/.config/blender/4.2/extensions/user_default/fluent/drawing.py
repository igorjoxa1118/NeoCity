import bpy
from bpy_extras import view3d_utils
import mathutils
from mathutils import Vector

from .Tools.translation import translate
from .UI.Helpers.shapes import *
from .Tools.helper import *


class FLUENT_Drawing():

    def __init__(self):
        self.cast_for_init = None
        self.equation_du_plan = []

        self.drawing_plane = None
        self.drawing_data = [[],[]]

        # grid variables
        self.resolution = 8
        self.x_gap = 0
        self.y_gap = 0
        self.align_to = 'FACE' #FACE or VIEW
        self.dot_size = 2
        self.dot_color = get_addon_preferences().snap_grid_dots_color
        self.hightlight_dot_color = get_addon_preferences().hightlight_dot
        self.plane_color = get_addon_preferences().snap_grid_plane_color
        self.snap_distance = 16
        self.display_grid = False
        self.display_dots = False
        self.snaped_coords = []
        self.plane_size = 1000

        self.grid_dots_coords = [] # en coordonnées locales du plan
        self.extended = True
        self.align_to_view = False
        self.align_diagonal = False

        self.align_data = {
            'point_01' : None,
            'point_02' : None
        }

        self.statut = None

        self.the_draw = {
            'type' : 'RECTANGLE',
            'coords_premier_clique' : [],
            'obj' : None,
            'shape_click_counter' : 0
        }

        self.cursor_infos = FLUENT_Cursor_Infos()

        self.side_infos = FLUENT_Panel_Infos()

        self.rectangle_info = [
            [translate('drawFromCenter'), 'SHIFT'],
            [translate('drawASquare'), 'CTRL'],
            [translate('validate'), translate('leftClick', upperCase=True)],
            [translate('validatePath'), translate('space')],
            [translate('cancel'), translate('escape')]
        ]
        self.prism_info = [
            [translate('forceTriangle'), translate('holdControl')],
            [translate('forceHexagon'), translate('holdAlt')],
            [translate('validate'), translate('leftClick', upperCase=True)],
            [translate('validateShape'), translate('shiftLeftClick', upperCase=True)],
            [translate('cancel'), translate('escape')]
        ]
        self.shape_info = [
            [translate('snapDirection'), translate('holdControl')],
            [translate('remove'), translate('backspace', upperCase=True)],
            [translate('validateShape'), translate('shiftLeftClick', upperCase=True)],
            [translate('validatePath'), translate('space')],
            [translate('validateClosedPath'), translate('shiftSpace', upperCase=True)],
            [translate('cancel'), translate('escape')]
        ]
        self.revolver_info = [
            [translate('remove'), translate('backspace', upperCase=True)],
            [translate('validatePath'), translate('space')],
            [translate('cancel'), translate('escape')]
        ]

        self.snaped_dots = FLUENT_Draw_Dots()
        self.snaped_dots.set_dots([[], []])

        self.sommets_dans_le_plan = []

        self.snaped_angle = FLUENT_Draw_Lines()

        self.align_lines = FLUENT_Draw_Lines()

        self.help_dots = FLUENT_Draw_Dots()

        self.temp = None

    def set_extended(self, a):
        self.extended = a

    def get_extended(self):
        return self.extended

    def set_align_to_view(self, a):
        self.align_to_view = a

    def get_align_to_view(self):
        return self.align_to_view

    def get_snaped_coords(self):
        return self.snaped_coords

    def reset(self):
        if not self.drawing_plane:
            if get_view_orientation_from_matrix() != 'UNDEFINED':
                self.set_align_to_view(True)
        try:
            bpy.data.objects.remove(self.drawing_plane, do_unlink=True)
        except:pass
        try:
            bpy.data.objects.remove(self.the_draw['obj'], do_unlink=True)
        except:pass
        self.cast_for_init = None
        self.equation_du_plan = []

        self.drawing_plane = None
        self.drawing_data = [[],[]]
        self.statut = None
        self.the_draw['coords_premier_clique']:[]
        self.the_draw['obj']:None
        self.the_draw['shape_click_counter']:0
        self.display_grid = False
        self.grid_dots_coords = []

    def grid_init(self, obj_original, events):
        if obj_original and not self.align_to_view:
            copy = duplicate(obj_original, '.f_temp')
            # suppression de tous les outer bevels pour avoir des arrêtes nettes
            remove_me = []
            for m in copy.modifiers:
                if m.type == 'BEVEL' and fluent_modifiers_name['outer_bevel'] in m.name:
                    remove_me.append(m)
                elif m.type == 'WEIGHTED_NORMAL':
                    remove_me.append(m)
            for m in remove_me:
                copy.modifiers.remove(m)
            copy.data.shade_flat()
            apply_modifiers(copy)

            depsgraph = bpy.context.evaluated_depsgraph_get()
            depsgraph.id_type_updated('OBJECT')

            cast = self.cast_for_init = obj_ray_cast(copy, events['mouse_x'], events['mouse_y'])
            if not cast['success']:
                bpy.data.objects.remove(copy, do_unlink=True)
                return False

            original_rotation = copy.rotation_euler.copy()
            copy.rotation_euler = Vector((0, 0, 0))

            original_position = copy.location.copy()
            copy.location = Vector((0, 0, 0))

            # applique le scale
            mb = copy.matrix_basis
            if hasattr(copy.data, "transform"):
                copy.data.transform(mb)
            for c in copy.children:
                c.matrix_local = mb @ c.matrix_local
            copy.matrix_basis.identity()

            depsgraph = bpy.context.evaluated_depsgraph_get()
            depsgraph.id_type_updated('OBJECT')

            obj = copy

            matrix = obj.matrix_world.copy()
            normal_in_world = matrix @ cast['normal']
            face_center_in_world = matrix @ obj.data.polygons[cast['face_index']].center
            self.equation_du_plan = plan_equation(n=normal_in_world, v=face_center_in_world, do='CALCUL')
            self.sommets_dans_le_plan = []
            if self.extended:
                for v in obj.data.vertices:
                    if plan_equation(normal_in_world, v.co, 'CHECK', self.equation_du_plan):
                        self.sommets_dans_le_plan.append(v.co)
            else:
                for v_index in obj.data.polygons[cast['face_index']].vertices:
                    self.sommets_dans_le_plan.append(obj.data.vertices[v_index].co)

            if not len(self.sommets_dans_le_plan):
                make_oops([translate('noVertices'), translate('faceNotFlat'), translate('impossibleToDisplayGrid')], translate('error'), 'ERROR')
                bpy.data.objects.remove(copy, do_unlink=True)
                return False

        try:
            bpy.data.objects.remove(self.drawing_plane, do_unlink=True)
        except:pass

        # creation du plan
        drawing_plan_verts = []
        plane_size = self.plane_size
        drawing_plan_verts.append((-plane_size, plane_size, 0))
        drawing_plan_verts.append((plane_size, plane_size, 0))
        drawing_plan_verts.append((plane_size, -plane_size, 0))
        drawing_plan_verts.append((-plane_size, -plane_size, 0))
        edges = [(0, 1), (1, 2), (2, 3), (3, 0)]
        faces = [(0, 1, 2, 3)]
        mesh_data = bpy.data.meshes.new("f_drawing_plane")
        mesh_data.from_pydata(drawing_plan_verts, edges, faces)
        mesh_data.update()
        drawing_tool_plan_obj = bpy.data.objects.new("f_drawing_plane", mesh_data)
        drawing_tool_plan_obj.hide_render = True
        self.drawing_plane = drawing_tool_plan_obj
        bpy.context.scene.collection.objects.link(drawing_tool_plan_obj)

        if obj_original and not self.align_to_view:

            # coordonnées moyennes des points du plan
            x_moy = 0
            y_moy = 0
            z_moy = 0
            for i, j in enumerate(self.sommets_dans_le_plan):
                x_moy += j.x
                y_moy += j.y
                z_moy += j.z
            x_moy = x_moy/(i+1)
            y_moy = y_moy/(i+1)
            z_moy = z_moy/(i+1)

            # x_max = y_max = z_max = -1000
            # x_min = y_min = z_min = 1000
            # for i in self.sommets_dans_le_plan:
            #     if i.x > x_max:
            #         x_max = i.x
            #     if i.x < x_min:
            #         x_min = i.x
            #     if i.y > y_max:
            #         y_max = i.y
            #     if i.y < y_min:
            #         y_min = i.y
            #     if i.z > z_max:
            #         z_max = i.z
            #     if i.z < z_min:
            #         z_min = i.z

            # définit le centre
            # print('--- z', z_min, z_max)
            grid_center = Vector((x_moy, y_moy, z_moy))
            # grid_center = Vector(((x_max+x_min)/2, (y_max+y_min)/2, (z_max+z_min)/2))
            self.drawing_plane.location = grid_center

            # rotation du plan
            vector_up = Vector((0, 0, 1))
            rot = vector_up.rotation_difference(obj.matrix_world @ self.cast_for_init['normal'])
            self.drawing_plane.rotation_euler = rot.to_euler('XYZ')
            _rot = self.drawing_plane.rotation_euler.copy()
            precision = 2
            test_x = False
            if math.fabs(round(self.drawing_plane.rotation_euler.x,precision)) == round(0, precision):
                test_x = True
            else:
                if math.fabs(round(self.drawing_plane.rotation_euler.x, precision)) == round(math.pi, precision):
                    test_x = True
            test_y = False
            if math.fabs(round(self.drawing_plane.rotation_euler.y, precision)) == round(0, precision):
                test_y = True
            else:
                if math.fabs(round(self.drawing_plane.rotation_euler.y, precision)) == round(math.pi, precision):
                    test_y = True

            if (test_x and test_y):
                self.drawing_plane.rotation_euler.z = 0
            else:
                total = 0
                threshold = math.radians(1)
                while not (-2*threshold<self.drawing_plane.rotation_euler.x<2*threshold or -2*threshold<self.drawing_plane.rotation_euler.y<2*threshold):
                    self.drawing_plane.rotation_euler.rotate_axis("Z", threshold)
                    total+=threshold
                threshold = math.radians(0.1)
                while not (-2*threshold<self.drawing_plane.rotation_euler.x<2*threshold or -2*threshold<self.drawing_plane.rotation_euler.y<2*threshold):
                    self.drawing_plane.rotation_euler.rotate_axis("Z", threshold)
                    total+=threshold
                threshold = math.radians(0.01)
                while not (-2*threshold<self.drawing_plane.rotation_euler.x<2*threshold or -2*threshold<self.drawing_plane.rotation_euler.y<2*threshold):
                    self.drawing_plane.rotation_euler.rotate_axis("Z", threshold)
                    total+=threshold
                threshold = math.radians(0.0005)
                while not (-2*threshold<self.drawing_plane.rotation_euler.x<2*threshold or -2*threshold<self.drawing_plane.rotation_euler.y<2*threshold):
                    self.drawing_plane.rotation_euler.rotate_axis("Z", threshold)
                    total+=threshold

            # Taille du plan
            # on ramène tous les vertices de la face dans un plan XY
            vertices_temp = []
            flat_rot_eul = mathutils.Euler((0, 0, 0), 'XYZ')
            flat_rot_quat = flat_rot_eul.to_quaternion()
            rot_quat = self.drawing_plane.rotation_euler.to_quaternion()
            diff_rot_quat = rot_quat.rotation_difference(flat_rot_quat)
            for v in self.sommets_dans_le_plan:
                a = v - self.drawing_plane.location
                a.rotate(diff_rot_quat)
                vertices_temp.append(a)

            self.temp = vertices_temp
            # trouve les coordonnees extremes
            x_max = -1000
            x_min = 1000
            y_max = -1000
            y_min = 1000
            for v in vertices_temp:
                if v.x > x_max:
                    x_max = v.x
                if v.x < x_min:
                    x_min = v.x
                if v.y > y_max:
                    y_max = v.y
                if v.y < y_min:
                    y_min = v.y

            x_total = math.fabs(x_max-x_min)
            y_total = math.fabs(y_max-y_min)
            self.x_gap = x_total/self.resolution
            self.y_gap = y_total/self.resolution
            x_min -= self.x_gap
            y_min -= self.y_gap
            self.grid_dots_coords = []
            for x in range(self.resolution + 3):
                for y in range(self.resolution + 3):
                    self.grid_dots_coords.append(
                        Vector((x_min + x * self.x_gap, y_min + y * self.y_gap, 0))
                    )
        else:
            x_max = 2
            x_min = -2
            y_max = 2
            y_min = -2
            x_total = math.fabs(x_max-x_min)
            y_total = math.fabs(y_max-y_min)
            x_gap = x_total/self.resolution
            y_gap = y_total/self.resolution
            self.grid_dots_coords = []
            for x in range(self.resolution + 1):
                for y in range(self.resolution + 1):
                    self.grid_dots_coords.append(
                        Vector((x_min + x * x_gap, y_min + y * y_gap, 0))
                    )


        # replace tout le monde à la position et rotation d'origine
        if obj_original and not self.align_to_view:
            # previous_active_obj = active_object('GET')
            active_object('SET', self.drawing_plane, True)
            active_object('SET', copy)
            bpy.ops.object.parent_set(type='OBJECT', keep_transform=True)
            copy.location = original_position
            copy.rotation_euler = original_rotation
            active_object('SET', self.drawing_plane, True)
            bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
            bpy.data.objects.remove(copy, do_unlink=True)

            temp = []
            for v in self.sommets_dans_le_plan:
                co_3d = obj_original.matrix_world @ v
                temp.append(co_3d)
            self.sommets_dans_le_plan = temp

        if self.align_to_view or (not obj_original and get_view_orientation_from_matrix() != 'UNDEFINED'):
            align_to_view(self.drawing_plane)
            if obj_original:
                self.drawing_plane.location = obj_original.location

                depsgraph = bpy.context.evaluated_depsgraph_get()
                depsgraph.update()

                nearest_vertex = None
                plus_grand_scalaire = 10000

                obj_original_eval = obj_original.evaluated_get(depsgraph)
                view_rotation = bpy.context.region_data.view_rotation.to_euler()
                vector_view = Vector((0, 0, 1))
                vector_view.rotate(view_rotation)
                viewer_position = obj_original.location + (vector_view * (100))
                for v in obj_original_eval.data.vertices:
                    v_global = obj_original.matrix_world @ v.co
                    vec = v_global - viewer_position
                    dist = vector_3d_length(vec)
                    if dist < plus_grand_scalaire:
                        plus_grand_scalaire = dist
                        nearest_vertex = v_global

                plane_direction = self.drawing_plane.matrix_world @ self.drawing_plane.data.polygons[0].normal
                vec_01 = nearest_vertex - self.drawing_plane.location
                move = vec_01.project(vector_view)
                plane_direction.normalize()
                move_local_axis(self.drawing_plane, 'Z', move.length)

        depsgraph = bpy.context.evaluated_depsgraph_get()
        depsgraph.id_type_updated('OBJECT')

        # cache dans le viewport
        self.drawing_plane.hide_set(True)

        self.statut = 'GRILLE_OK'

        return True

    def grid_to_square(self):
        lx = (self.grid_dots_coords[0].x + self.grid_dots_coords[-1].x) / 2
        ly = (self.grid_dots_coords[0].y + self.grid_dots_coords[-1].y) / 2
        delta = Vector((lx, ly, 0))
        move_local_axis(self.drawing_plane, 'X', delta.x)
        move_local_axis(self.drawing_plane, 'Y', delta.y)
        for i, d in enumerate(self.grid_dots_coords):
            d -= delta
        # la longueur du coté du carré sera le coté le plus long du rectangle
        x_min = self.grid_dots_coords[0].x
        y_min = self.grid_dots_coords[0].y
        x_max = self.grid_dots_coords[len(self.grid_dots_coords)-1].x
        y_max = self.grid_dots_coords[len(self.grid_dots_coords)-1].y
        x_total = math.fabs(x_max-x_min)
        y_total = math.fabs(y_max-y_min)

        if x_total > y_total:
            y_max = x_max
            y_min = x_min
        elif y_total > x_total:
            x_max = y_max
            x_min = y_min
        
        x_total = math.fabs(x_max-x_min)
        y_total = math.fabs(y_max-y_min)
        x_gap = x_total/(self.resolution + 2)
        y_gap = y_total/(self.resolution + 2)
        self.grid_dots_coords = []
        for x in range(self.resolution + 3):
            for y in range(self.resolution + 3):
                self.grid_dots_coords.append(
                    Vector((x_min + x * x_gap, y_min + y * y_gap, 0))
                )

    def set_display_dots(self, a):
        self.display_dots = a

    def get_display_dots(self):
        return self.display_dots

    def set_equation_du_plan(self):
        self.equation_du_plan = plan_equation(n = 0, v = 0, do = 'CALCUL', eq = [0, 0, 0, 0])

    def set_display_grid(self, a):
        self.display_grid = a

    def set_statut(self, statut):
        self.statut = statut

    def get_statut(self):
        return self.statut

    def get_drawing_plane(self):
        return self.drawing_plane

    def plane_rotation(self, axis, angle):
        r = snap_slider_value(angle, 5)
        self.drawing_plane.rotation_euler.rotate_axis(axis, math.radians(r))
        if self.the_draw['obj']:
            self.the_draw['obj'].rotation_euler = self.drawing_plane.rotation_euler.copy()
        return r

    def plane_move(self, axis, delta):
        move_local_axis(self.drawing_plane, axis, delta)
        if self.the_draw['obj']:
            self.the_draw['obj'].location = self.drawing_plane.location

    def plane_scale(self, axis, delta):
        if self.drawing_plane:
            x_min = self.grid_dots_coords[0].x
            y_min = self.grid_dots_coords[0].y
            x_max = self.grid_dots_coords[len(self.grid_dots_coords)-1].x
            y_max = self.grid_dots_coords[len(self.grid_dots_coords)-1].y
            
            if axis == 'X':
                x_min -= delta/2
                x_max += delta/2
            elif axis == 'Y':
                y_min -= delta/2
                y_max += delta/2
            elif axis == 'XY':
                x_min -= delta/2
                x_max += delta/2
                y_min -= delta/2
                y_max += delta/2

            if x_min < x_max:
                x_total = math.fabs(x_max-x_min)
                y_total = math.fabs(y_max-y_min)
                x_gap = x_total/self.resolution
                y_gap = y_total/self.resolution
                self.grid_dots_coords = []
                for x in range(self.resolution + 1):
                    for y in range(self.resolution + 1):
                        self.grid_dots_coords.append(
                            Vector((x_min + x * x_gap, y_min + y * y_gap, 0))
                        )

    def set_the_draw_type(self, a):
        self.the_draw['type'] = a
        if self.the_draw['obj']:
            try:
                bpy.data.objects.remove(self.the_draw['obj'], do_unlink=True)
            except:pass
            self.the_draw['obj'] = None
        if self.statut == 'EN_ATTENTE':
            self.statut = 'GRILLE_OK'
        elif self.statut in ['EN_COURS', 'TERMINE']:
            self.statut = 'GRILLE_OK'
        elif self.statut == 'EN_ATTENTE_REVOLVER':
            self.statut = None
            self.display_grid = False
        if self.the_draw['type'] == 'RECTANGLE':
            self.side_infos.add_line(translate('rectangle', upperCase=True), '', reset = True)
            self.side_infos.add_line(translate('drawRectangle'), translate('leftClick'), reset = False)
            self.side_infos.add_line(translate('drawFromOutside'), translate('shiftLeftClickFace'), reset = False)
        elif self.the_draw['type'] == 'PRISM':
            self.side_infos.add_line(translate('circle', upperCase=True), '', reset = True)
            self.side_infos.add_line(translate('drawCircle'), translate('leftClick'), reset = False)
            self.side_infos.add_line(translate('drawFromOutside'), translate('shiftLeftClickFace'), reset = False)
        elif self.the_draw['type'] == 'SHAPE':
            self.side_infos.add_line(translate('shape', upperCase=True), '', reset = True)
            self.side_infos.add_line(translate('drawShape'), translate('leftClick'), reset = False)
            self.side_infos.add_line(translate('drawFromOutside'), translate('shiftLeftClickFace'), reset = False)
        elif self.the_draw['type'] == 'REVOLVER':
            self.side_infos.add_line(translate('solidOfRevolution', upperCase=True), '', reset = True)
            self.side_infos.add_line(translate('displayGrid'), translate('rightClick'), reset = False)
            self.side_infos.add_line(translate('setPivot'), translate('rightClickAgain'), reset = False)

    def get_the_draw_type(self):
        return self.the_draw['type']

    def get_the_draw(self):
        return self.the_draw

    def set_resolution(self, a):
        on_face = False
        x_min = self.grid_dots_coords[0].x
        y_min = self.grid_dots_coords[0].y
        x_max = self.grid_dots_coords[-1].x
        y_max = self.grid_dots_coords[-1].y
        if int((self.resolution + 3)*(self.resolution + 3)) == len(self.grid_dots_coords):
            on_face = True
        if on_face:
            x_min += self.x_gap
            y_min += self.y_gap
            x_max -= self.x_gap
            y_max -= self.y_gap
            w = 3
        else:
            w = 1

        self.resolution = a
        if a > 32:
            a = 32
        elif a < 1:
            a = 1
        self.resolution = a

        x_total = math.fabs(x_max-x_min)
        y_total = math.fabs(y_max-y_min)
        self.x_gap = x_total/self.resolution
        self.y_gap = y_total/self.resolution
        if on_face:
            x_min -= self.x_gap
            y_min -= self.y_gap
        self.grid_dots_coords = []
        for x in range(self.resolution + w):
            for y in range(self.resolution + w):
                self.grid_dots_coords.append(
                    Vector((x_min + x * self.x_gap, y_min + y * self.y_gap, 0))
                )

    def get_resolution(self):
        return self.resolution

    def grid_align(self, events):
        if self.snaped_coords:
            mouse_x = self.snaped_coords[0]
            mouse_y = self.snaped_coords[1]
        else:
            mouse_x = events['mouse_x']
            mouse_y = events['mouse_y']
        cast = obj_ray_cast(self.drawing_plane, mouse_x, mouse_y)
        if not self.align_data['point_01']:
            self.align_data['point_01'] = cast['hit']
            return 'STEP_01'
        elif not self.align_data['point_02']:
            self.align_data['point_02'] = cast['hit']
        if self.align_data['point_01'] and self.align_data['point_02']:
            edge_length = distance(self.align_data['point_01'].x, self.align_data['point_01'].y, 0, self.align_data['point_02'].x, self.align_data['point_02'].y, 0)
            co_milieu = (self.align_data['point_01'] + self.align_data['point_02'])/2
            if (self.align_data['point_01'].x - self.align_data['point_02'].x) != 0:
                coef = (self.align_data['point_01'].y - self.align_data['point_02'].y)/(self.align_data['point_01'].x - self.align_data['point_02'].x)
                angle = math.atan(coef)
                if round(angle) < 0: angle += math.pi
            else:
                angle = math.pi / 2
            if self.align_diagonal:
                angle = 0
            move_local_axis(self.drawing_plane, 'X', co_milieu.x)
            move_local_axis(self.drawing_plane, 'Y', co_milieu.y)
            self.drawing_plane.rotation_euler.rotate_axis('Z', angle)

            x_min = y_min = -edge_length/2
            x_max = y_max = edge_length/2

            if self.align_diagonal:
                width = math.fabs(self.align_data['point_01'].x - self.align_data['point_02'].x)
                height = math.fabs(self.align_data['point_01'].y - self.align_data['point_02'].y)
                x_min = -width/2
                x_max = -x_min
                y_min = -height/2
                y_max = -y_min

            x_total = math.fabs(x_max-x_min)
            y_total = math.fabs(y_max-y_min)
            x_gap = x_total/self.resolution
            y_gap = y_total/self.resolution
            self.grid_dots_coords = []
            for x in range(self.resolution + 1):
                for y in range(self.resolution + 1):
                    self.grid_dots_coords.append(
                        Vector((x_min + x * x_gap, y_min + y * y_gap, 0))
                    )
            if self.the_draw['obj']:
                self.the_draw['obj'].location = self.drawing_plane.location
                self.the_draw['obj'].rotation_euler = self.drawing_plane.rotation_euler.copy()
            self.align_data = {
                'point_01' : None,
                'point_02' : None
            }
            return 'FINISHED'

    def process(self, events):
        if self.snaped_coords:
            mouse_x = self.snaped_coords[0]
            mouse_y = self.snaped_coords[1]
        else:
            mouse_x = events['mouse_x']
            mouse_y = events['mouse_y']
        self.snaped_angle.set_lines([])
        if self.statut == 'GRILLE_OK':
            # Initialisation de l'objet à dessiner
            try:
                bpy.data.objects.remove(self.the_draw['obj'], do_unlink=True)
            except:pass
            if self.the_draw['type'] == 'RECTANGLE':
                self.the_draw['obj'] = make_plane()
                self.the_draw['obj']['fluent_type'] = 'box'
                self.the_draw['obj'].location = self.drawing_plane.location
            elif self.the_draw['type'] == 'PRISM':
                self.the_draw['obj'] = make_prism()
                self.the_draw['obj']['fluent_type'] = 'prism'
            elif self.the_draw['type'] == 'SPHERE':
                self.the_draw['obj'] = make_sphere()
                self.the_draw['obj']['fluent_type'] = 'sphere'
            elif self.the_draw['type'] == 'SHAPE':
                self.the_draw['obj'] = make_shape()
                self.the_draw['obj']['fluent_type'] = 'poly'
                self.the_draw['obj'].location = self.drawing_plane.location
            elif self.the_draw['type'] == 'REVOLVER':
                self.the_draw['obj'] = make_shape()
                self.the_draw['obj']['fluent_type'] = 'revolver'
            self.the_draw['obj'].rotation_euler = self.drawing_plane.rotation_euler
            self.the_draw['obj'].hide_set(True)
            self.the_draw['obj'].hide_render = True
            self.statut = 'EN_ATTENTE'
            if events['type'] == 'LEFTMOUSE' and events['value'] == 'PRESS' and not events['shift_work']:
                cast = obj_ray_cast(self.drawing_plane, mouse_x, mouse_y)
                if cast['success']:
                    self.the_draw['coords_premier_clique'] = cast['hit']
                    if self.the_draw['type'] == 'SHAPE':
                        for v in self.the_draw['obj'].data.vertices:
                            v.co = cast['hit']
                        self.the_draw['shape_click_counter'] += 1
                    self.statut = 'EN_COURS'
        elif self.statut in ['EN_ATTENTE', 'EN_ATTENTE_REVOLVER']:
            if events['type'] == 'LEFTMOUSE' and events['value'] == 'PRESS':
                cast = obj_ray_cast(self.drawing_plane, mouse_x, mouse_y)
                if cast['success']:
                    self.the_draw['coords_premier_clique'] = cast['hit']
                    if self.the_draw['type'] in ['SHAPE', 'REVOLVER']:
                        for v in self.the_draw['obj'].data.vertices:
                            v.co = cast['hit']
                        self.the_draw['shape_click_counter'] += 1

                    self.statut = 'EN_COURS'
            elif events['type'] == 'RIGHTMOUSE' and events['value'] == 'PRESS' and self.the_draw['type'] == 'REVOLVER':
                cast = obj_ray_cast(self.drawing_plane, mouse_x, mouse_y)
                if cast['success']:
                    # inv = self.drawing_plane.matrix_world.copy()
                    # inv.invert()
                    # self.drawing_plane.location += (cast['hit'] - self.drawing_plane.location) @ inv
                    lx = (self.grid_dots_coords[0].x + self.grid_dots_coords[-1].x) / 2
                    ly = (self.grid_dots_coords[0].y + self.grid_dots_coords[-1].y) / 2
                    delta = cast['hit'] - Vector((lx, ly, 0))
                    move_local_axis(self.drawing_plane, 'X', delta.x)
                    move_local_axis(self.drawing_plane, 'Y', delta.y)
                    self.grid_to_square()
                    self.drawing_plane.rotation_euler.rotate_axis('X', math.radians(90))

                    self.the_draw['obj'].location = self.drawing_plane.location
                    self.the_draw['obj'].rotation_euler = self.drawing_plane.rotation_euler

                    self.statut = 'EN_ATTENTE_REVOLVER'
        elif self.statut == 'EN_COURS':
            if self.the_draw['type'] == 'RECTANGLE':
                self.side_infos.reset()
                for i, j in enumerate(self.rectangle_info):
                    self.side_infos.add_line(self.rectangle_info[i][0], self.rectangle_info[i][1])
            elif self.the_draw['type'] == 'PRISM':
                self.side_infos.reset()
                for i, j in enumerate(self.prism_info):
                    self.side_infos.add_line(self.prism_info[i][0], self.prism_info[i][1])
            elif self.the_draw['type'] in ['SHAPE', 'REVOLVER']:
                self.side_infos.reset()
                if self.the_draw['type'] == 'SHAPE':
                    for i, j in enumerate(self.shape_info):
                        self.side_infos.add_line(self.shape_info[i][0], self.shape_info[i][1])
                elif self.the_draw['type'] == 'REVOLVER':
                    for i, j in enumerate(self.revolver_info):
                        self.side_infos.add_line(self.revolver_info[i][0], self.revolver_info[i][1])
                self.snaped_dots.set_dots([[], []])
                if events['type'] == 'BACK_SPACE' and events['value'] == 'PRESS':
                    if self.the_draw['shape_click_counter']-1 > 0:
                        self.the_draw['obj'].data.vertices[self.the_draw['shape_click_counter']-1].co = self.the_draw['obj'].data.vertices[0].co
                        self.the_draw['obj'].data.vertices[self.the_draw['shape_click_counter']].co = self.the_draw['obj'].data.vertices[0].co
                        self.the_draw['shape_click_counter'] -= 1
                    else:
                        self.the_draw['obj'].data.vertices[0].co = Vector((0, 0, 0))
                        if self.the_draw['type'] == 'SHAPE':
                            self.statut = 'EN_ATTENTE'
                        if self.the_draw['type'] == 'REVOLVER':
                            self.statut = 'EN_ATTENTE_REVOLVER'

            if events['type'] == 'MOUSEMOVE':
                cast = obj_ray_cast(self.drawing_plane, mouse_x, mouse_y)
                if cast['success']:
                    hit = cast['hit']
                    if self.the_draw['type'] == 'RECTANGLE':
                        vertices = self.the_draw['obj'].data.vertices
                        if not events['shift_work']:
                            if not events['ctrl_work']:
                                vertices[0].co.x = self.the_draw['coords_premier_clique'].x
                                vertices[0].co.y = self.the_draw['coords_premier_clique'].y
                                vertices[2].co.x = hit.x
                                vertices[2].co.y = hit.y
                                vertices[1].co.x = hit.x
                                vertices[1].co.y = vertices[0].co.y
                                vertices[3].co.x = vertices[0].co.x
                                vertices[3].co.y = hit.y
                            else:
                                snap_result = snap(vertices[0].co.x, vertices[0].co.y, hit.x, hit.y, only = '45')
                                vertices[0].co.x = self.the_draw['coords_premier_clique'].x
                                vertices[0].co.y = self.the_draw['coords_premier_clique'].y
                                vertices[2].co.x = snap_result[0]
                                vertices[2].co.y = snap_result[1]
                                vertices[1].co.x = snap_result[0]
                                vertices[1].co.y = vertices[0].co.y
                                vertices[3].co.x = vertices[0].co.x
                                vertices[3].co.y = snap_result[1]
                        else:
                            if not events['ctrl_work']:
                                vertices[0].co.x = self.the_draw['coords_premier_clique'].x  - (hit.x - self.the_draw['coords_premier_clique'].x)
                                vertices[0].co.y = self.the_draw['coords_premier_clique'].y  - (hit.y - self.the_draw['coords_premier_clique'].y)
                                vertices[2].co.x = hit.x
                                vertices[2].co.y = hit.y
                                vertices[1].co.x = hit.x
                                vertices[1].co.y = vertices[0].co.y
                                vertices[3].co.x = vertices[0].co.x
                                vertices[3].co.y = hit.y
                            else:
                                snap_result = snap(self.the_draw['coords_premier_clique'].x, self.the_draw['coords_premier_clique'].y, hit.x, hit.y, only = '45')
                                diff_x = self.the_draw['coords_premier_clique'].x - snap_result[0]
                                diff_y = self.the_draw['coords_premier_clique'].y - snap_result[1]
                                center_x = self.the_draw['coords_premier_clique'].x
                                center_y = self.the_draw['coords_premier_clique'].y
                                vertices[0].co.x = center_x + diff_x
                                vertices[0].co.y = center_y + diff_y
                                vertices[2].co.x = center_x - diff_x
                                vertices[2].co.y = center_y - diff_y
                                vertices[1].co.x = center_x - diff_x
                                vertices[1].co.y = center_y + diff_y
                                vertices[3].co.x = center_x + diff_x
                                vertices[3].co.y = center_y - diff_y
                    elif self.the_draw['type'] in ['PRISM', 'SPHERE']:
                        self.the_draw['obj'].location = self.drawing_plane.matrix_world @ Vector((self.the_draw['coords_premier_clique'][0], self.the_draw['coords_premier_clique'][1], 0))
                        a = hit.x - self.the_draw['coords_premier_clique'][0]
                        b = hit.y - self.the_draw['coords_premier_clique'][1]
                        try:
                            if self.the_draw['type'] == 'PRISM':
                                self.the_draw['obj'].modifiers[fluent_modifiers_name['radius']].strength = math.sqrt(a * a + b * b)
                                if events['ctrl_work']:
                                    screw = self.the_draw['obj'].modifiers[fluent_modifiers_name['screw']]
                                    screw.steps = screw.render_steps = 3
                                elif events['alt_work']:
                                    screw = self.the_draw['obj'].modifiers[fluent_modifiers_name['screw']]
                                    screw.steps = screw.render_steps = 6
                                else:
                                    screw = self.the_draw['obj'].modifiers[fluent_modifiers_name['screw']]
                                    screw.steps = screw.render_steps = auto_bevel_segments(displace=self.the_draw['obj'].modifiers[fluent_modifiers_name['radius']])
                            elif self.the_draw['type'] == 'SPHERE':
                                self.the_draw['obj'].modifiers[fluent_modifiers_name['radius']].strength = math.sqrt(a * a + b * b) * 2
                                screw_2 = self.the_draw['obj'].modifiers[fluent_modifiers_name['screw_2']]
                                screw_2.steps = screw_2.render_steps = auto_bevel_segments(displace=self.the_draw['obj'].modifiers[fluent_modifiers_name['radius']]) / 2
                                screw = self.the_draw['obj'].modifiers[fluent_modifiers_name['screw']]
                                screw.steps = screw.render_steps = screw_2.steps / 3
                        except:
                            pass
                    elif self.the_draw['type'] in ['SHAPE', 'REVOLVER']:
                        if events['ctrl_work'] and not self.display_dots:
                            snap_range = 16
                            region = bpy.context.region
                            rv3d = bpy.context.region_data
                            distance_x_max = 10000
                            distance_y_max = 10000
                            is_snaped = {
                            'x':False,
                            'y':False,
                            '45':False
                            }
                            matrix = self.the_draw['obj'].matrix_world
                            hit_co_3d = self.drawing_plane.matrix_world @ hit
                            hit_co_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, hit_co_3d)
                            # snap sur les autres vertices
                            verts_snaped_coords = [None,None]

                            for i in range(self.the_draw['shape_click_counter']):
                                v = self.the_draw['obj'].data.vertices[i]
                                v_co_3d = matrix @ v.co
                                v_co_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, v_co_3d)

                                vector_hit_vertex = hit - v.co

                                if math.fabs(vector_hit_vertex.x) < math.fabs(vector_hit_vertex.y) and math.fabs(vector_hit_vertex.x) < distance_x_max:
                                    candidate_01 = Vector((v.co.x, hit.y, 0))
                                    candidate_02 = None
                                    distance_x_max = math.fabs(vector_hit_vertex.x)
                                elif math.fabs(vector_hit_vertex.y) < math.fabs(vector_hit_vertex.x) and math.fabs(vector_hit_vertex.y) < distance_y_max:
                                    candidate_02 = Vector((hit.x, v.co.y, 0))
                                    candidate_01 = None
                                    distance_y_max = math.fabs(vector_hit_vertex.y)
                                else:
                                    candidate_01 = None
                                    candidate_02 = None

                                if candidate_01:
                                    c1_co_3d = matrix @ candidate_01
                                    c1_co_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, c1_co_3d)
                                    d_x = distance(hit_co_2d.x, hit_co_2d.y, 0, c1_co_2d.x, c1_co_2d.y, 0)
                                    if d_x <= snap_range:
                                        verts_snaped_coords[0] = v.co.x
                                        is_snaped['x'] = True
                                        dots = self.snaped_dots.get_dots()
                                        if not dots[0]:
                                            self.snaped_dots.set_dots([[v_co_2d.x, v_co_2d.y, 4, (1, 0, 0, 1)], dots[1]])
                                        else:
                                            self.snaped_dots.set_dots([dots[0], [v_co_2d.x, v_co_2d.y, 4, (1, 0, 0, 1)]])

                                if candidate_02:
                                    c2_co_3d = matrix @ candidate_02
                                    c2_co_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, c2_co_3d)
                                    d_y = distance(hit_co_2d.x, hit_co_2d.y, 0, c2_co_2d.x, c2_co_2d.y, 0)
                                    if d_y <= snap_range:
                                        verts_snaped_coords[1] = v.co.y
                                        is_snaped['y'] = True
                                        dots = self.snaped_dots.get_dots()
                                        if not dots[0]:
                                            self.snaped_dots.set_dots([[v_co_2d.x, v_co_2d.y, 4, (1, 0, 0, 1)], dots[1]])
                                        else:
                                            self.snaped_dots.set_dots([dots[0], [v_co_2d.x, v_co_2d.y, 4, (1, 0, 0, 1)]])

                            # snap les angles à 45°
                            angle_snaped_coords = []
                            snap_angle_avec_le_dernier = False
                            try:
                                v = self.the_draw['obj'].data.vertices[self.the_draw['shape_click_counter']-1]
                                snap_result = snap_455(v.co.x, v.co.y, hit.x, hit.y)
                                co_3d_local = Vector((snap_result[0], snap_result[1], 0))
                                co_3d = matrix @ co_3d_local
                                co_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, co_3d)
                                d = distance(co_2d.x, co_2d.y, 0, hit_co_2d.x, hit_co_2d.y, 0)
                                if d <= snap_range:
                                    angle_snaped_coords = snap_result
                                    v2 = self.the_draw['obj'].data.vertices[self.the_draw['shape_click_counter']-2]
                                    v2_co_3d = matrix @ v2.co
                                    v1_co_3d = matrix @ v.co
                                    v0 = self.the_draw['obj'].data.vertices[self.the_draw['shape_click_counter']-0]
                                    v0_co_3d = matrix @ v0.co
                                    self.snaped_angle.set_lines([
                                        [
                                            [(v2_co_3d.x, v2_co_3d.y, v2_co_3d.z),(v1_co_3d.x, v1_co_3d.y, v1_co_3d.z),(v1_co_3d.x, v1_co_3d.y, v1_co_3d.z),(v0_co_3d.x, v0_co_3d.y, v0_co_3d.z)],
                                            2,
                                            (1, 0, 0, 1),
                                            False
                                        ]
                                    ])
                                else:
                                    # test l'angle avec le premier vertex de la forme
                                    v2 = self.the_draw['obj'].data.vertices[0]
                                    snap_result = snap_455(v2.co.x, v2.co.y, hit.x, hit.y)
                                    co_3d = matrix @ Vector((snap_result[0], snap_result[1], 0))
                                    co_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, co_3d)
                                    d = distance(x=co_2d.x, y=co_2d.y, xx=hit_co_2d.x, yy=hit_co_2d.y)
                                    if d < snap_range:
                                        snap_angle_avec_le_dernier = True
                                        v0 = self.the_draw['obj'].data.vertices[self.the_draw['shape_click_counter']-1]
                                        v0_co_3d = matrix @ v0.co
                                        v1 = self.the_draw['obj'].data.vertices[self.the_draw['shape_click_counter']-0]
                                        v1_co_3d = matrix @ v1.co
                                        v2_co_3d = matrix @ v2.co
                                        self.snaped_angle.set_lines([
                                            [
                                                [(v0_co_3d.x, v0_co_3d.y, v0_co_3d.z),(v1_co_3d.x, v1_co_3d.y, v1_co_3d.z),(v1_co_3d.x, v1_co_3d.y, v1_co_3d.z),(v2_co_3d.x, v2_co_3d.y, v2_co_3d.z)],
                                                2,
                                                (1, 0, 0, 1),
                                                False
                                            ]
                                        ])
                            except:
                                pass

                            # combinaison des résultats
                            snaped_coords = [hit.x, hit.y]
                            if not angle_snaped_coords and not snap_angle_avec_le_dernier:
                                if verts_snaped_coords[0] and verts_snaped_coords[1]:
                                    snaped_coords = verts_snaped_coords
                                elif verts_snaped_coords[0]:
                                    snaped_coords[0] = verts_snaped_coords[0]
                                elif verts_snaped_coords[1]:
                                    snaped_coords[1] = verts_snaped_coords[1]
                            elif angle_snaped_coords and not snap_angle_avec_le_dernier:
                                if not verts_snaped_coords[0] and not verts_snaped_coords[1]:
                                    snaped_coords = angle_snaped_coords
                                else:
                                    if verts_snaped_coords[0]:
                                        # coordonées du vertex précedent
                                        v1 = self.the_draw['obj'].data.vertices[self.the_draw['shape_click_counter']-1]
                                        f = snap_455(v1.co.x, v1.co.y, hit.x, hit.y, True)
                                        if f:
                                            snaped_coords[0] = verts_snaped_coords[0]
                                            snaped_coords[1] = f['a']*verts_snaped_coords[0]+f['b']
                                    elif verts_snaped_coords[1]:
                                        # coordonées du vertex précedent
                                        v1 = self.the_draw['obj'].data.vertices[self.the_draw['shape_click_counter']-1]
                                        f = snap_455(v1.co.x, v1.co.y, hit.x, hit.y, True)
                                        if f:
                                            snaped_coords[1] = verts_snaped_coords[1]
                                            snaped_coords[0] = (verts_snaped_coords[1]-f['b'])/f['a']
                            elif not angle_snaped_coords and snap_angle_avec_le_dernier:
                                if verts_snaped_coords[0]:
                                    v2 = self.the_draw['obj'].data.vertices[0]
                                    f = snap_455(v2.co.x, v2.co.y, hit.x, hit.y, True)
                                    if f:
                                        snaped_coords[0] = verts_snaped_coords[0]
                                        snaped_coords[1] = f['a']*verts_snaped_coords[0]+f['b']
                                elif verts_snaped_coords[1]:
                                    v2 = self.the_draw['obj'].data.vertices[0]
                                    f = snap_455(v2.co.x, v2.co.y, hit.x, hit.y, True)
                                    if f:
                                        snaped_coords[1] = verts_snaped_coords[1]
                                        snaped_coords[0] = (verts_snaped_coords[1]-f['b'])/f['a']
                                else:
                                    v2 = self.the_draw['obj'].data.vertices[0]
                                    snaped_coords = snap_455(v2.co.x, v2.co.y, hit.x, hit.y)

                            try:
                                self.the_draw['obj'].data.vertices[self.the_draw['shape_click_counter']].co.x = snaped_coords[0]
                                self.the_draw['obj'].data.vertices[self.the_draw['shape_click_counter']].co.y = snaped_coords[1]
                            except:
                                print('Shape snap error')
                        else:
                            self.the_draw['obj'].data.vertices[self.the_draw['shape_click_counter']].co = hit

            if events['type'] == 'LEFTMOUSE' and events['value'] == 'PRESS' and self.the_draw['type'] in ['SHAPE', 'REVOLVER'] and not events['shift_work']:
                self.the_draw['shape_click_counter'] += 1

            # Valide le chemin
            if self.the_draw['type'] in ['SHAPE', 'REVOLVER', 'RECTANGLE'] and events['type'] == 'SPACE' and events['value'] == 'PRESS':
                self.statut = 'TERMINE'
                if self.the_draw['type'] in ['SHAPE', 'RECTANGLE']:
                    self.the_draw['obj']['fluent_type'] = 'path'

                active_object(action = 'SET', obj = self.the_draw['obj'], solo = True)

                if self.the_draw['type'] in ['SHAPE', 'REVOLVER']:
                    self.the_draw['obj'].data.vertices[self.the_draw['shape_click_counter']].co = self.the_draw['obj'].data.vertices[self.the_draw['shape_click_counter']-1].co

                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.delete(type='ONLY_FACE')
                bpy.ops.mesh.select_all(action='DESELECT')
                bpy.ops.object.mode_set(mode='OBJECT')

                if self.the_draw['type'] == 'SHAPE' and not events['shift_work']:
                    self.the_draw['obj'].data.vertices[self.the_draw['shape_click_counter']].select = True
                    bpy.ops.object.mode_set(mode='EDIT')
                    bpy.ops.mesh.delete(type='VERT')

                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.mesh.remove_doubles()
                bpy.ops.mesh.delete(type='ONLY_FACE')
                bpy.ops.mesh.select_all(action='DESELECT')
                bpy.ops.object.mode_set(mode='OBJECT')

                # supprime l'edge sur l'axe de rotation
                if self.the_draw['type'] in ['REVOLVER']:
                    v1 = None
                    v2 = None
                    for v in self.the_draw['obj'].data.vertices:
                        if math.fabs(round(v.co.x, 3)) == 0:
                            if not v1:
                                v1 = v
                                v.co.x = 0
                            elif not v2:
                                v2 = v
                                v.co.x = 0
                    if v1 and v2:
                        v1.select = v2.select = True
                        bpy.ops.object.mode_set(mode='EDIT')
                        bpy.context.scene.tool_settings.mesh_select_mode = [True, False, False]
                        bpy.ops.mesh.delete(type='EDGE')
                        bpy.ops.object.mode_set(mode='OBJECT')
            # convertie un prism en poly et valide
            elif self.the_draw['type'] in ['PRISM'] and events['type'] == 'LEFTMOUSE' and events['value'] == 'PRESS' and events['shift_work']:
                self.statut = 'TERMINE'
                self.the_draw['obj']['fluent_type'] = 'poly'
                apply_modifiers(self.the_draw['obj'])
            # valide en tant que path
            elif self.the_draw['type'] in ['PRISM'] and events['type'] == 'SPACE':
                self.statut = 'TERMINE'
                radius_mod = None
                for mod in self.the_draw['obj'].modifiers:
                    if fluent_modifiers_name['radius'] in mod.name:
                        radius_mod = mod
                        break

                for mod in self.the_draw['obj'].modifiers:
                    if fluent_modifiers_name['inner_radius'] in mod.name:
                        mod.strength = radius_mod.strength * 0.9
                        break

            # Valide dessin
            elif events['type'] == 'LEFTMOUSE' and events['value'] == 'PRESS':
                if self.the_draw['type'] in ['RECTANGLE', 'PRISM', 'SPHERE']:
                    self.statut = 'TERMINE'
                if self.the_draw['type'] in ['SHAPE'] and events['shift_work']:
                    self.statut = 'TERMINE'
                    self.the_draw['obj'].data.vertices[self.the_draw['shape_click_counter']].co = \
                    self.the_draw['obj'].data.vertices[self.the_draw['shape_click_counter'] - 1].co
                    active_object(action='SET', obj=self.the_draw['obj'], solo=True)
                    bpy.ops.object.mode_set(mode='EDIT')
                    bpy.ops.mesh.select_all(action='SELECT')
                    bpy.ops.mesh.remove_doubles()
                    bpy.ops.object.mode_set(mode='OBJECT')

        elif self.statut == 'TERMINE':
            try:
                depsgraph = bpy.context.evaluated_depsgraph_get()
                bool_obj_eveluated = self.the_draw['obj'].evaluated_get(depsgraph)
                az = round(bool_obj_eveluated.data.polygons[0].normal.z, 3)
                bz = round(self.drawing_plane.data.polygons[0].normal.z, 3)
                if az!=bz:
                    for p in self.the_draw['obj'].data.polygons:
                        p.flip()
            except:pass
            self.end()
        elif self.statut == None:
            if self.the_draw['type'] == 'RECTANGLE':
                self.side_infos.add_line(translate('rectangle', upperCase=True), '', reset = True)
                self.side_infos.add_line(translate('drawRectangle'), translate('leftClick'), reset = False)
                self.side_infos.add_line(translate('drawFromOutside'), translate('shiftLeftClickFace'), reset = False)
            elif self.the_draw['type'] == 'PRISM':
                self.side_infos.add_line(translate('circle', upperCase=True), '', reset = True)
                self.side_infos.add_line(translate('drawCircle'), translate('leftClick'), reset = False)
                self.side_infos.add_line(translate('drawFromOutside'), translate('shiftLeftClickFace'), reset = False)
            elif self.the_draw['type'] == 'SHAPE':
                self.side_infos.add_line(translate('shape', upperCase=True), '', reset = True)
                self.side_infos.add_line(translate('drawShape'), translate('leftClick'), reset = False)
                self.side_infos.add_line(translate('drawFromOutside'), translate('shiftLeftClickFace'), reset = False)
            elif self.the_draw['type'] == 'REVOLVER':
                self.side_infos.add_line(translate('solidOfRevolution', upperCase=True), '', reset = True)
                self.side_infos.add_line(translate('displayGrid'), translate('rightClick'), reset = False)
                self.side_infos.add_line(translate('setPivot'), translate('rightClickAgain'), reset = False)

    def draw(self, events):
        region = bpy.context.region
        rv3d = bpy.context.region_data
        self.drawing_data[0] = []
        close_list = []

        if self.display_grid:
            try:
                # dessine le plan
                corner_3d = [
                    self.grid_dots_coords[0],
                    self.grid_dots_coords[round(math.sqrt(len(self.grid_dots_coords)))-1],
                    self.grid_dots_coords[len(self.grid_dots_coords)-round(math.sqrt(len(self.grid_dots_coords)))],
                    self.grid_dots_coords[-1],
                ]
                corner_2d = []
                for c in corner_3d:
                    co_3d = self.drawing_plane.matrix_world @ c
                    co_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, co_3d)
                    corner_2d.append(co_2d)
                indices = [(0, 1, 2), (1, 2, 3)]
                drawing_tris(corner_2d, indices, self.plane_color)
            except:
                print('--- error plane drawing')
                pass

            if self.display_dots:
                try:
                    #dessine les lignes centrales
                    lx = (self.grid_dots_coords[0].x + self.grid_dots_coords[-1].x)/2
                    ly = (self.grid_dots_coords[0].y + self.grid_dots_coords[-1].y)/2
                    local_coords = [
                        Vector((self.grid_dots_coords[0].x, ly, 0)),
                        Vector((self.grid_dots_coords[-1].x, ly, 0)),
                        Vector((lx, self.grid_dots_coords[0].y, 0)),
                        Vector((lx, self.grid_dots_coords[-1].y, 0))
                    ]
                    global_coords = []
                    for i in local_coords:
                        co_3d = self.drawing_plane.matrix_world @ i
                        global_coords.append(co_3d)
                    draw_line(coords=global_coords, thickness=2, color=(0, .75, 1, 1), transform_2d=True)
                except:pass

                try:
                    # dessine les points de la grille
                    grid_dots = []
                    for v in self.grid_dots_coords:
                            co_3d = self.drawing_plane.matrix_world @ v
                            co_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, co_3d)
                            dist = distance(x=co_2d.x, y=co_2d.y, xx=events['mouse_x'], yy=events['mouse_y'])
                            if dist < self.snap_distance:
                                close_list.append({'coord':co_2d, 'dist':dist})
                            grid_dots.append([co_2d.x, co_2d.y])
                    draw_all_circle_full(grid_dots, self.dot_size, self.dot_color, 8)
                except:pass
                try:
                    # dessin les points sur les sommets
                    vertices_dots = []
                    for co_3d in self.sommets_dans_le_plan:
                        co_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, co_3d)
                        self.drawing_data[0].append(co_2d)
                        dist = distance(x=co_2d.x, y=co_2d.y, xx=events['mouse_x'], yy=events['mouse_y'])
                        if dist < self.snap_distance:
                            close_list.append({'coord':co_2d, 'dist':dist})
                        vertices_dots.append([co_2d.x, co_2d.y])
                    draw_all_circle_full(vertices_dots, self.dot_size*2, self.hightlight_dot_color, 8)
                except:pass
            
            # dessine le point le plus proche de la souris en plus gros
            if self.display_dots and len(close_list):
                min = self.snap_distance
                snaped = None
                for c in close_list:
                    if c['dist'] < min:
                        min = c['dist']
                        snaped = c
                draw_circle_full(snaped['coord'].x, snaped['coord'].y, self.dot_size*3, self.dot_color, segments = 8)
                self.snaped_coords = [snaped['coord'].x, snaped['coord'].y]
            else:
                self.snaped_coords = [events['mouse_x'], events['mouse_y']]

        if self.statut == 'EN_COURS':
            a = prepare_draw_shape(self.the_draw['obj'])
            drawing_tris(a[0], a[1], (1, 1, 1, .5))
            draw_edges(self.the_draw['obj'], 2, (1, 1, 1, 1), transform_2d=True)

        if self.align_data['point_01']:
            co_3d = self.drawing_plane.matrix_world @ self.align_data['point_01']
            cast = obj_ray_cast(self.drawing_plane, self.snaped_coords[0], self.snaped_coords[1])
            mouse_co_3d = self.drawing_plane.matrix_world @ cast['hit']
            self.align_lines.set_lines([[
                [co_3d, mouse_co_3d],
                2,
                (1, 1, 1, 1),
                False
            ]])
            self.align_lines.draw(events)

        self.cursor_infos.draw(events)

        self.side_infos.draw(events)

        try:
            self.snaped_dots.draw(events)
        except:
            pass
        # try:
        self.snaped_angle.draw(events)
        # except:pass

        self.help_dots.draw(events)

    def end(self):
        bpy.data.objects.remove(self.drawing_plane, do_unlink=True)
        self.cast_for_init = None
        self.equation_du_plan = []

        self.drawing_plane = None
        self.drawing_plane = None
        self.drawing_data = [[],[]]

        # self.statut = None
