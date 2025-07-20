import bpy, bmesh, enum, gpu, sys
from mathutils import Vector, Matrix, geometry
from bpy_extras.view3d_utils import region_2d_to_origin_3d, region_2d_to_vector_3d, location_3d_to_region_2d
from gpu_extras.batch import batch_for_shader

from ... utility import addon
from ... ui_framework.master import Master
from ... ui_framework.utils.mods_list import get_mods_list
from ... utility.base_modal_controls import Base_Modal_Controls
from ... utils.space_3d import ray_cast_objects
from ... utility.shader import dot_handler
from ... utils.blender_ui import get_dpi_factor
from ... utility.object import set_origin
from ... utility.math import coords_to_center, dimensions
from ... utils.toggle_view3d_panels import collapse_3D_view_panels
from ... ui_framework import form_ui as form
from ... utility import method_handler


class states(enum.Enum):
    origin = 0
    cursor = 1
    empty = 2


class modes(enum.Enum):
    none = enum.auto()
    set = enum.auto()
    gizmo = enum.auto()


class gizmo_modes(enum.Enum):
    rot = 0
    loc = 1
    locrot = 2


class object_modes(enum.Enum):
    VISIBLE = 0
    SELECTION = 1
    DESELECTED = 2


DESC = """Set Origin
Set origin of selected object(s) to a point or line on mesh surface \n
Shift - Copy origin's location and rotation from active object to selection
Ctrl + Shift - Copy origin's location from active object to selection
"""


class HOPS_OT_SET_ORIGIN(bpy.types.Operator):
    bl_idname = "hops.set_origin"
    bl_label = "Set Origin"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = DESC

    _state = states.origin
    _median_loc = False

    axis_gizmo = [
        Vector(),
        Vector((1, 0, 0)),
        Vector(),
        Vector((0, 1, 0)),
        Vector(),
        Vector((0, 0, 1)),
    ]

    axis_gizmo_colors = [
        [1, 0, 0, 1],
        [1, 0, 0, 1],
        [0, 1, 0, 1],
        [0, 1, 0, 1],
        [0, 0, 1, 1],
        [0, 0, 1, 1],
    ]

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, val):
        if val == self._state: return

        if val == states.origin:
            self.color = self.color_origin
            self.color_high = self.color_origin_high
            self.set_dot_colors()
        elif val == states.cursor:
            self.color = self.color_cursor
            self.color_high = self.color_cursor_high
            self.set_dot_colors()

        else:
            self.color = self.color_empty
            self.color_high = self.color_empty_high
            self.set_dot_colors()

        self._state = val

    @property
    def median_loc(self):
        return self._median_loc

    @median_loc.setter
    def median_loc(self, val):
        if self._median_loc == val: return

        self._median_loc = val

        if self.final_matrix is None: return
        if self.gizmo_mode != gizmo_modes.rot:
            if val:
                self.final_matrix.translation = (self.anchor_matrix.translation + self.pointer_vec) /2

            else:
                self.final_matrix.translation = self.anchor_matrix.translation

        if self.origin_dot: self.origin_dot.location = self.final_matrix.translation

    @classmethod
    def poll(cls, context):
        # for obj in context.selected_objects:
        #     if obj.type and obj.type == 'EMPTY':
        #         return False
        return context.selected_objects

    def invoke(self, context, event):
        self.notify = lambda val: bpy.ops.hops.display_notification(info=val) if addon.preference().ui.Hops_extra_info else lambda val: None
        self.object_name = ''
        self.face_index = -1
        preference = addon.preference()
        self.init_cursor_matrix = context.scene.cursor.matrix.copy()
        self.shift = event.shift
        self.state = states.origin
        self.mode = modes.none
        self.gizmo_handler = None
        self.intersect = Vector()
        self.selected_meshes = [o for o in context.selected_objects if o.type == 'MESH']
        self.visible_meshes = [o for o in context.visible_objects if o.type == 'MESH']
        self.unselected = [o for o in self.visible_meshes if not o.select_get()]
        self.object_mode = object_modes.SELECTION
        self.objects = self.selected_meshes
        self.gizmo_mode = gizmo_modes.locrot
        self.median_loc_base = False
        self.median_loc = False
        self.empty = None
        self.empties = []
        self.object_lock = False
        self.parent_to_empty = True
        self.bounds_only = False
        self.bounds_obj = None
        self.bounds_obj_index = -1

        if event.shift:
            if not context.active_object:
                msg ='No active object to copy origin from!'
                self.notify(msg)
                self.report({'INFO'}, msg)
                return {'CANCELLED'}

            active = context.active_object
            selected = [o for o in context.selected_objects if o is not active]

            if not selected:
                msg ='No selected objects to set origin to!'
                self.notify(msg)
                self.report({'INFO'}, msg)
                return {'CANCELLED'}

            if event.ctrl:
                origin = active.matrix_world.translation
                msg = "Copied origin's location"

            else:
                origin = active.matrix_world
                msg = "Copied origin's location and orientation"

            for obj in selected:
                set_origin(obj, origin)

            self.report({'INFO'}, msg)
            self.notify(msg)
            return{'FINISHED'}

        if not self.visible_meshes:
            msg = 'There are no Mesh objects to work with'
            self.notify(msg)

            self.report({'INFO'}, msg)
            return {"CANCELLED"}

        #draw data
        self.size = 15 * get_dpi_factor()
        self.size_high = 1.5 * self.size
        self.outline_color = [0, 0, 0, 0]
        self.outline_color_high = [0, 0, 0 ,0]
        self.outline_width = 0
        self.outline_width_high = 0

        self.color_origin = preference.color.dot
        self.color_origin_high = preference.color.dot_highlight

        self.color_cursor = (1, 0, 0, 0.8)
        self.color_cursor_high = (1, 1, 0, 0.8)

        self.color_empty = (0, 1, 0, 0.8)
        self.color_empty_high = (0, 1, 1, 0.8)

        self.color = self.color_origin
        self.color_high = self.color_origin_high

        self.gizmo_origin = Vector()
        self.gizmo_pointer = Vector()

        self.edges = []
        self.final_matrix = None

        self.gizmo_handler = bpy.types.SpaceView3D.draw_handler_add(self.draw_rot_gizmo, (context,), 'WINDOW', 'POST_VIEW')
        self.dot_handler = dot_handler(context, handle_draw=True)
        self.dot_handler.snap_radius = self.size / 2
        self.anchor_matrix = Matrix()
        self.pointer_vec = Vector()
        self.active_dot = None
        self.origin_dot = None

        # Dot UI
        self.form_obj = None
        if context.active_object != None:
            if context.active_object.type == 'MESH':
                obj = context.active_object
                if obj in self.selected_meshes:
                    if obj in self.visible_meshes:
                        self.form_obj = context.active_object
        self.form = None
        if self.form_obj and addon.preference().property.in_tool_popup_style == 'DEFAULT':
            if len(self.form_obj.modifiers) > 0:
                self.setup_form(context, event)

        self.form_obj_mod_mapping = {}
        if self.form_obj != None:
            for mod in self.form_obj.modifiers:
                self.form_obj_mod_mapping[mod.name] = mod.show_viewport

        # Base Systems
        self.master = Master(context=context)
        self.master.only_use_fast_ui = True
        self.base_controls = Base_Modal_Controls(context, event)
        self.original_tool_shelf, self.original_n_panel = collapse_3D_view_panels()
        self.draw_handle = bpy.types.SpaceView3D.draw_handler_add(self.safe_draw_shader, (context,), 'WINDOW', 'POST_PIXEL')

        self.update_dots(context, event)
        redraw_areas(context)

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


    def modal(self, context, event):

        # Base Systems
        self.master.receive_event(event)
        self.base_controls.update(context, event)
        if self.form:
            self.form.update(context, event)

        if self.base_controls.pass_through or event.type.count('WHEEL'):
            return {'PASS_THROUGH'}

        self.median_loc = self.median_loc_base - event.alt #XOR in python

        if event.type == 'MOUSEMOVE':
            mouse = Vector((event.mouse_region_x, event.mouse_region_y))

            if self.mode == modes.none:
                self.update_dots(context, event)
                self.active_dot = self.dot_handler.active_dot

            elif self.mode == modes.set:
                vec2d = location_3d_to_region_2d(context.region, context.space_data.region_3d, self.anchor_matrix.translation, default=mouse)
                if (mouse - vec2d).length > self.dot_handler.snap_radius:
                    self.mode = modes.gizmo
                    self.setup_gizmo()

            elif self.mode == modes.gizmo:
                matrix = self.anchor_matrix.copy()
                pointer_vec = self.intersect_tri(context, matrix, mouse)

                self.update_dots(context, event)

                if self.dot_handler.active_dot and self.dot_handler.active_dot is self.active_dot:
                    self.dot_handler.active_dot.highlit = False

                else:
                    self.active_dot = self.dot_handler.active_dot

                active_vec = self.active_dot.location if self.active_dot else None

                if not active_vec and self.gizmo_mode != gizmo_modes.loc:
                    distance = 0.0
                    nearest = None
                    for edge in self.edges:
                        current, normalized_distance = geometry.intersect_point_line(pointer_vec, *edge)

                        if normalized_distance > 1:
                            current = edge[1]

                        elif normalized_distance < 0:
                            current = edge[0]

                        length = (current - pointer_vec).length

                        if length < distance or not distance:
                            distance = length
                            nearest = edge

                    active_vec, _ = geometry.intersect_point_line(self.anchor_matrix.translation, *nearest)

                active_vec = active_vec if active_vec else matrix.translation
                self.pointer_vec = active_vec

                track_vec = matrix.inverted() @ active_vec
                delta_angle = track_vec.to_2d().angle_signed(Vector((0, 1)), 0)
                correction_matrix = Matrix.Rotation(delta_angle, 4, 'Z')
                matrix @= correction_matrix

                if self.median_loc:
                    matrix.translation = (self.anchor_matrix.translation + self.pointer_vec) / 2

                if self.gizmo_mode == gizmo_modes.loc:
                    self.final_matrix.translation = matrix.translation

                elif self.gizmo_mode == gizmo_modes.rot:
                    matrix.translation = self.final_matrix.translation
                    self.final_matrix = matrix

                else:
                    self.final_matrix = matrix

                self.create_origin_dot()
                self.origin_dot.location = self.final_matrix.translation

                for i in range(3):
                    self.gizmo_pointer[i] = active_vec[i]

        elif event.type == 'A' and event.value == 'PRESS':
            i = self.state.value
            i = (i + 1) % len(states.__members__)
            self.state = states(i)

            if self.origin_dot:
                color = [1 - c for c in self.color]
                color[3] = 1
                self.origin_dot.color = self.origin_dot.color_high = color
            self.notify(f'{self.state.name.capitalize()} Mode')

        elif event.type == 'B' and event.value == 'PRESS':
            self.bounds_only = not self.bounds_only
            self.object_name = ''
            if self.bounds_obj is not None: self.bounds_obj.hide_set(not self.bounds_only)
            self.update_dots(context, event)

            msg = 'Bounds' if self.bounds_only else 'Mesh'
            self.notify(msg)

        elif event.type == 'C' and event.value == 'PRESS' and self.object_name:
            self.object_lock = not self.object_lock

            self.notify(f'Objects: {self.object_name if self.object_lock else self.object_mode.name.capitalize()}')

        elif event.type == 'E' and event.value == 'PRESS' and self.state == states.empty:
            self.parent_to_empty = not self.parent_to_empty

            self.notify(f'Parent to empty: {self.parent_to_empty}')

        elif event.type == 'S' and event.value == 'PRESS' and self.mode == modes.none and not self.object_lock:
            i = self.object_mode.value
            i = (i + 1) % len(object_modes.__members__)
            self.object_mode = object_modes(i)

            if self.object_mode == object_modes.VISIBLE:
                self.objects = self.visible_meshes

            elif self.object_mode == object_modes.SELECTION:
                self.objects = self.selected_meshes
                if self.object_name and not bpy.data.objects[self.object_name].select_get():
                    self.dot_handler.clear_dots()
                    self.object_name = ''

            else:
                self.objects = self.unselected
                if self.object_name and bpy.data.objects[self.object_name].select_get():
                    self.dot_handler.clear_dots()
                    self.object_name = ''

            self.update_dots(context, event)
            self.notify(f'Objects: {self.object_mode.name.capitalize()}')

        elif event.type == 'R' and event.value == 'PRESS':
            i = self.gizmo_mode.value
            i = (i + 1) % len(modes.__members__)
            self.gizmo_mode = gizmo_modes(i)

            if self.gizmo_mode == gizmo_modes.loc:
                msg = 'Location'
            elif self.gizmo_mode == gizmo_modes.rot:
                msg = 'Rotation'
            else:
                msg = 'Loc & Rot'

            self.notify(f'Gizmo mode: {msg}')

        elif event.type == 'F' and event.value == 'PRESS':
            self.median_loc_base = not self.median_loc_base
            self.median_loc = not self.median_loc

            if self.median_loc:
                msg = 'Location: Median'
            else:
                msg = 'Location: First'

            self.notify(msg)

        elif event.type == 'LEFTMOUSE' and event.value == 'PRESS' and self.active_dot:
            self.mode = modes.set
            self.anchor_matrix = self.active_dot.matrix.copy()
            matrix = self.anchor_matrix.copy()

            if self.gizmo_mode == gizmo_modes.loc:
                self.final_matrix.translation = matrix.translation

            elif self.gizmo_mode == gizmo_modes.rot:
                matrix.translation = self.final_matrix.translation
                self.final_matrix = matrix

            else:
                self.final_matrix = matrix

        elif event.type == 'LEFTMOUSE' and event.value == 'RELEASE' and self.mode != modes.none:
            if self.state == states.cursor:
                if self.mode == modes.set:
                    matrix = Matrix.Translation(self.final_matrix.translation)
                    context.scene.cursor.matrix = matrix

                elif self.mode == modes.gizmo:
                    matrix = self.final_matrix.copy()

                    if self.gizmo_mode == gizmo_modes.loc:
                        matrix = Matrix.Translation(self.final_matrix.translation)

                    elif self.gizmo_mode == gizmo_modes.rot:
                        matrix.translation = context.scene.cursor.matrix.translation

                    context.scene.cursor.matrix = matrix

            elif self.state == states.origin:
                if self.mode == modes.set:
                    for obj in context.selected_objects:
                        for obj in context.selected_objects:
                            set_origin(obj, self.final_matrix.translation)

                else:
                    for obj in context.selected_objects:
                        if self.gizmo_mode == gizmo_modes.loc:
                            set_origin(obj, self.final_matrix.translation)

                        elif self.gizmo_mode == gizmo_modes.rot:
                            matrix = self.final_matrix.copy()
                            matrix.translation = obj.matrix_world.translation
                            set_origin(obj, matrix)

                        else:
                            set_origin(obj, self.final_matrix)

            elif self.state == states.empty:
                self.empty = bpy.data.objects.new('Origin', None)
                self.empties.append(self.empty)
                self.empty.empty_display_type = 'SPHERE'
                context.collection.objects.link(self.empty)
                self.empty.matrix_world = self.final_matrix

            if self.mode == modes.set or self.gizmo_mode == gizmo_modes.loc:
                msg = 'Location'

            elif self.gizmo_mode == gizmo_modes.rot:
                msg = 'Rotation'
            else:
                msg = 'Location and Rotation'

            self.notify(f'{self.state.name.capitalize()} set: {msg}')

            if event.shift:
                if self.mode == modes.set: self.create_origin_dot()
                self.origin_dot.location = self.final_matrix.translation
                self.origin_dot.matrices = [self.final_matrix.copy()]
                self.mode = modes.none

            else:
                if self.state == states.empty:
                    if self.parent_to_empty:
                        inv_mat = self.empty.matrix_world.inverted()
                        for obj in context.selected_objects:
                            mat = obj.matrix_world.copy()

                            obj.parent = self.empty
                            obj.matrix_parent_inverse = inv_mat
                            obj.matrix_world = mat

                self.exit(context)
                self.select_empties(context)
                self.report({'INFO'}, "FINISHED")
                return {'FINISHED'}

        elif self.base_controls.cancel:
            #context.scene.cursor.matrix = self.init_cursor_matrix
            self.exit(context)
            self.report({'INFO'}, "CANCELLED")
            bpy.ops.ed.undo_push()
            bpy.ops.ed.undo()
            return {'CANCELLED'}

        elif event.type == 'SPACE':
            self.exit(context)
            self.select_empties(context)
            self.report({'INFO'}, "FINISHED")
            self.notify('FINISHED')
            return {'FINISHED'}

        elif event.type == 'TAB' and event.value == 'PRESS' and addon.preference().property.in_tool_popup_style == 'BLENDER':
            bpy.ops.hops.modlist_popover(allow_removal=False)

        self.draw_ui(context)
        redraw_areas(context)
        return {'RUNNING_MODAL'}


    def exit(self, context):
        if self.bounds_obj is not None:
            me = self.bounds_obj.data
            bpy.data.objects.remove(self.bounds_obj)
            bpy.data.meshes.remove(me)

        self.dot_handler.purge()
        self.purge_gizmo()

        collapse_3D_view_panels(self.original_tool_shelf, self.original_n_panel)
        self.master.run_fade()
        redraw_areas(context)

        # Form
        self.remove_shader()
        if self.form:
            self.form.shut_down(context)
        if self.form_obj != None:
            for mod_name, show in self.form_obj_mod_mapping.items():
                if mod_name in self.form_obj.modifiers:
                    self.form_obj.modifiers[mod_name].show_viewport = show


    def update_dots(self, context, event):
        vec2d = event.mouse_region_x, event.mouse_region_y
        origin = region_2d_to_origin_3d(context.region, context.space_data.region_3d, vec2d)
        direction = region_2d_to_vector_3d(context.region, context.space_data.region_3d, vec2d)
        objects = self.objects
        rebuild = 0

        if self.object_lock and self.object_name:
            objects = [bpy.data.objects[self.object_name]]

        hit, _, _, index, object, matrix = ray_cast_objects(context, origin, direction, objects, evaluated=True)

        if hit and object.type == 'MESH':
            if object.name != self.object_name:
                rebuild += 1
                self.object_name = object.name
                self.create_bounds(object)

            if index != self.face_index:
                rebuild += 1
                self.face_index = index

        if self.bounds_only and self.bounds_obj:
            rebuild = 0
            self.face_index = -1
            hit, _, _, index, object, matrix  = self.bounds_cast(origin, direction)
            #hit, _, _, index, object, matrix  = ray_cast_objects(context, origin, direction, [self.bounds_obj], evaluated=False)
            if hit and (index != self.bounds_obj_index):
                rebuild = 1
                object = self.bounds_obj
                self.bounds_obj_index = index

        if rebuild:
            self.dot_handler.clear_dots()
            self.origin_dot = None

            if self.mode == modes.none:
                self.edges.clear()

            eval_mesh = object.evaluated_get(context.evaluated_depsgraph_get()).data
            face = eval_mesh.polygons[index]

            loc, rot, sca = matrix.decompose()
            trans_mat = Matrix.Translation(loc)
            rot_mat = rot.to_matrix().to_4x4()
            scale_mat = Matrix.Diagonal((*sca, 1))

            normal = (scale_mat.inverted().transposed() @ face.normal)
            surface_matrix = normal.to_track_quat('Z', 'Y').to_matrix().to_4x4()
            surface_matrix.translation = face.center
            surface_matrix = trans_mat @ rot_mat @ surface_matrix

            for vert in face.vertices:
                vec = matrix @ eval_mesh.vertices[vert].co
                dot = self.dot_handler.dot_create(vec, type='VERT', size=self.size, size_high=self.size_high, color=self.color, color_high=self.color_high, outline_color=self.outline_color, outline_color_high=self.outline_color_high, outline_width=self.outline_width, outline_width_high=self.outline_width_high)

                mat = surface_matrix.copy()
                mat.translation = vec
                dot.matrices = [mat]

            for vert1, vert2 in face.edge_keys:
                v1 = matrix @ eval_mesh.vertices[vert1].co
                v2 = matrix @ eval_mesh.vertices[vert2].co
                vec = (v1 + v2) /2

                if self.mode == modes.none:
                    self.edges.append((v1, v2))

                dot = self.dot_handler.dot_create(vec, type='EDGE', size=self.size, size_high=self.size_high, color=self.color, color_high=self.color_high, outline_color=self.outline_color, outline_color_high=self.outline_color_high, outline_width=self.outline_width, outline_width_high=self.outline_width_high)
                mat = surface_matrix.copy()
                mat.translation = vec
                dot.matrices = [mat]

            vec = matrix @ face.center
            dot = self.dot_handler.dot_create(vec, type='FACE', size=self.size, size_high=self.size_high, color=self.color, color_high=self.color_high, outline_color=self.outline_color, outline_color_high=self.outline_color_high, outline_width=self.outline_width, outline_width_high=self.outline_width_high)
            mat = surface_matrix.copy()
            mat.translation = vec
            dot.matrices = [mat]

            if self.mode == modes.none:
                self.final_matrix = matrix.normalized()
                self.final_matrix.translation = matrix.translation

            self.create_origin_dot()

        self.dot_handler.update(context, event)


    def set_dot_colors(self,):
        for dot in self.dot_handler.dots:
            dot.color = self.color
            dot.color_high = self.color_high


    def draw_rot_gizmo(self, context):
        if self.mode != modes.gizmo: return
        #Enable(bgl.GL_LINE_SMOOTH)
        gpu.state.line_width_set(3)
        line = [self.gizmo_origin, self.gizmo_pointer]
        built_in_shader = 'UNIFORM_COLOR' if bpy.app.version[0] >=4 else '3D_UNIFORM_COLOR'
        shader = gpu.shader.from_builtin(built_in_shader)
        batch = batch_for_shader(shader, 'LINES', {"pos": line})
        shader.bind()
        shader.uniform_float('color', self.color_high)
        batch.draw(shader)


        persp_matrix = context.region_data.view_matrix.copy()
        persp_matrix.translation.z = context.region_data.view_distance
        depth_factor = (persp_matrix @ self.origin_dot.location).z * 0.1
        s = (0.5 if context.region_data.view_perspective == 'ORTHO' else 0.3 ) * abs(depth_factor)
        sca = Matrix.Scale(s, 4)

        matrix = self.final_matrix @ sca
        matrix.translation = self.origin_dot.location
        axes = [matrix @ v for v in self.axis_gizmo]

        built_in_shader = 'FLAT_COLOR' if bpy.app.version[0] >=4 else '3D_FLAT_COLOR'
        axes_shader = gpu.shader.from_builtin(built_in_shader)
        axes_batch = batch_for_shader(axes_shader, 'LINES', {"pos": axes, 'color': self.axis_gizmo_colors})
        axes_shader.bind()
        axes_batch.draw(axes_shader)

        #Disable(bgl.GL_LINE_SMOOTH)
        gpu.state.line_width_set(1)


    def setup_gizmo(self):
        location = self.dot_handler.active_dot.location
        for i in range(3):
            self.gizmo_origin[i] = location[i]


    def purge_gizmo(self):
        if self.gizmo_handler:
            bpy.types.SpaceView3D.draw_handler_remove(self.gizmo_handler, 'WINDOW')
            self.gizmo_handler = None


    def intersect_tri(self, context, matrix, vec2d):
        v1 = matrix @ Vector(( 0, 1, 0))
        v2 = matrix @ Vector(( 1,-1, 0))
        v3 = matrix @ Vector((-1,-1, 0))

        origin = region_2d_to_origin_3d(context.region, context.space_data.region_3d, vec2d)
        direction = region_2d_to_vector_3d(context.region, context.space_data.region_3d, vec2d)

        intersect = geometry.intersect_ray_tri(v1, v2, v3, direction, origin, False)
        if not intersect:
            intersect = geometry.intersect_ray_tri(v1, v2, v3, -direction, origin, False)

        if not intersect:
            intersect = self.intersect

        self.intersect = intersect

        return intersect

    def bounds_cast(self, origin_world, direction_world):
        mesh = self.bounds_obj.data
        matrix = self.bounds_obj.matrix_world
        inverted = matrix.inverted()

        origin = inverted @ origin_world
        direction = inverted @ (direction_world + origin_world) - origin

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

        return hit, vec, normal, index, self.bounds_obj, matrix

    def create_origin_dot(self):
        if self.origin_dot is None:

            color = [1 - c for c in self.color]
            color[3] = 1
            self.origin_dot = self.dot_handler.dot_create(self.final_matrix.translation, type='ORIGIN', size=self.size*0.8, size_high=self.size_high, color=color, color_high=color, outline_color=self.outline_color, outline_color_high=self.outline_color_high, outline_width=self.outline_width, outline_width_high=self.outline_width_high)

            self.origin_dot.matrices = [Matrix.Translation(self.final_matrix.translation)]


    def select_empties(self, context):
        if not self.empties: return

        bpy.ops.object.select_all(action='DESELECT')
        for obj in self.empties:
            obj.select_set(True)
            context.view_layer.objects.active = obj


    def create_bounds(self, obj):
        if self.bounds_obj is None:
            me = bpy.data.meshes.new('SO_Proxy')
            self.bounds_obj = bpy.data.objects.new('SO_Proxy', me)
            bpy.context.collection.objects.link(self.bounds_obj)
            self.bounds_obj.display_type = 'BOUNDS'
            self.bounds_obj.hide_set(not self.bounds_only)

        center = coords_to_center(obj.bound_box)
        scale = dimensions(obj.bound_box)
        bm = bmesh.new()
        matrix = Matrix.Diagonal((*scale, 1))
        matrix.translation = center
        bmesh.ops.create_cube(bm, matrix=matrix)
        bm.to_mesh(self.bounds_obj.data)
        self.bounds_obj.data.update()
        self.bounds_obj.matrix_world = obj.matrix_world
        self.bounds_obj_index = -1


    def draw_ui(self, context):

        self.master.setup()
        if not self.master.should_build_fast_ui(): return

        # Main
        win_list = []

        if self.gizmo_mode == gizmo_modes.loc:
            gmode = '[R] Location'
            gmode_s = '[R] L'

        elif self.gizmo_mode == gizmo_modes.rot:
            gmode = '[R] Rotation'
            gmode_s = '[R] R'

        else:
            gmode = '[R] Loc & Rot'
            gmode_s = '[R] L&R'

        if addon.preference().ui.Hops_modal_fast_ui_loc_options != 1:
            win_list.append(self.state.name.capitalize()[0])
            win_list.append(f"[S] {self.object_mode.name[0]}" if not self.object_lock else "L")
            win_list.append(gmode_s)
            win_list.append('F' if not self.median_loc else 'M')

            if self.state == states.empty:
                win_list.append(f'[E] {self.parent_to_empty}')

        else:
            win_list.append(self.state.name.capitalize())
            win_list.append(f"[S] {self.object_mode.name.capitalize()}" if not self.object_lock else self.object_name)
            win_list.append(gmode)
            win_list.append('[F] First' if not self.median_loc else '[F] Median')
            win_list.append('[B] Mesh' if self.bounds_only else '[B] Bounds')

            if self.state == states.empty:
                win_list.append(f'[E] Parent: {self.parent_to_empty}')

        # Help
        help_items = {"GLOBAL" : [], "STANDARD" : []}

        help_items["GLOBAL"] = [
            ("M", "Toggle mods list"),
            ("H", "Toggle help"),
            ("~", "Toggle UI Display Type"),
            ("O", "Toggle viewport rendering")]

        help_items["STANDARD"] = [
            ("TAB", f"Modifier list") if addon.preference().property.in_tool_popup_style == 'BLENDER' else ('', ''),
            ("B", f"Toggle {'Bounds' if not self.bounds_only else 'Mesh'} mode"),
            ("C", f"Object lock: {self.object_lock}"),
            ("F", f"Location : {'First' if not self.median_loc else 'Median'} [Alt]"),
            ("R", f"Gizmo Mode : {gmode}"),
            ("S", f"Objects: {self.object_mode.name.capitalize()}"),
            ("A", f"Change Mode {self.state.name.capitalize()}"),
            ("Shift+LMB", "Confirm without exit"),
            ("LMB  ", f"Set {self.state.name.capitalize()}; Hold to rotate"),
            ("RMB  ", "Cancel"),
            ("SPACE", "Confirm"),]

        if self.state == states.empty:
            help_items["STANDARD"] = [("E", f"Parent to empty: {self.parent_to_empty}")] + help_items["STANDARD"]

        # Mods
        mods_list = get_mods_list(mods=bpy.context.active_object.modifiers)

        self.master.receive_fast_ui(win_list=win_list, help_list=help_items, image="", mods_list=mods_list)
        self.master.finished()

    # --- FORM FUNCS --- #

    def setup_form(self, context, event):
        # MAX WIDTH = 165
        self.form = form.Form(context, event, dot_open=False)

        # Mod Scroll Box
        group = form.Scroll_Group()
        for index, mod in enumerate(self.form_obj.modifiers):
            row = group.row()
            # Count
            row.add_element(form.Label(text=str(index + 1), width=25, height=20))
            # Mod name
            text = form.shortened_text(mod.name, width=95, font_size=12)
            row.add_element(form.Label(text=text, width=100, height=20))
            # Visible
            row.add_element(form.Button(
                scroll_enabled=False, text="X", highlight_text="O", tips=["Toggle visibility"],
                width=20, height=20, use_padding=False,
                callback=self.rebuild_from_form, pos_args=(mod, context),
                highlight_hook_obj=mod, highlight_hook_attr='show_viewport'))
            group.row_insert(row)
        row = self.form.row()

        box_height = 160

        if len(self.form_obj.modifiers) < 8:
            box_height = 20 * len(self.form_obj.modifiers)

        mod_box = form.Scroll_Box(width=165, height=box_height, scroll_group=group, view_scroll_enabled=True)
        row.add_element(mod_box)
        self.form.row_insert(row, active=True)

        self.form.build()


    def rebuild_from_form(self, mod, context):
        mod.show_viewport = not mod.show_viewport

    # --- SHADERS --- #

    def safe_draw_shader(self, context):
        method_handler(self.draw_shader,
            arguments = (context,),
            identifier = 'Set Origin 2D Shader',
            exit_method = self.remove_shader)


    def remove_shader(self):
        if self.draw_handle:
            self.draw_handle = bpy.types.SpaceView3D.draw_handler_remove(self.draw_handle, "WINDOW")


    def draw_shader(self, context):
        if self.form:
            self.form.draw()


def redraw_areas(context):
    for area in context.screen.areas:
        if area.type != 'VIEW_3D': continue
        area.tag_redraw()

