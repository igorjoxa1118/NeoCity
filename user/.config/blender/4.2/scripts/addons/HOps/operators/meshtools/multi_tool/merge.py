from .utils import *


class Merge:
    def __init__(self, context):
        # Prefs
        self.prefs_vert_size = None
        if len(context.preferences.themes) > 0:
            self.prefs_vert_size = bpy.context.preferences.themes[0].view_3d.vertex_size


    def shut_down(self, context):
        # Prefs
        if self.prefs_vert_size:
            if len(context.preferences.themes) > 0:
                bpy.context.preferences.themes[0].view_3d.vertex_size = self.prefs_vert_size


    def setup(self):
        # Merge
        self.merge_locked = False
        self.vert_one = None
        self.vert_two = None

        # Gravitate
        self.grav_locked = False
        self.grav_point = None
        self.grav_tolerance = 0
        self.grav_gl_points = []

        # Join
        self.join_locked = False

        # Slide
        self.slide_locked = False

        # Mouse Controls
        self.pressed = False
        self.drag_distance = 0


    def update(self, context, event, data, op):

        # Vertex size
        if event.type in {'PLUS', 'EQUAL'} and event.value == 'PRESS':
            if len(context.preferences.themes) > 0:
                context.preferences.themes[0].view_3d.vertex_size += 1
        elif event.type == 'MINUS' and event.value == 'PRESS':
            if len(context.preferences.themes) > 0:
                context.preferences.themes[0].view_3d.vertex_size -= 1

        if self.grav_locked:
            self.__gravitate(context, event, data, op)
            return

        elif self.merge_locked:
            self.__vert_merge(context, event, data, op)
            return

        elif self.slide_locked:
            self.setup()
            data.save()
            return

        elif self.join_locked:
            op.join.update(context, event, data, op)
            if op.join.start == False:
                self.setup()
            return

        data.locked = False

        # Join setup
        if event.type == 'LEFTMOUSE' and event.value == 'PRESS' and event.shift:
            vert = get_vert_under_mouse(context, event, data)
            if vert:
                self.join_locked = True
                # Setup join module
                op.join.start = True
                op.join.first_vert = vert
                op.join.override_release_confirm = True
                return
            else:
                bpy.ops.hops.display_notification(info="Click vert")
            return

        # Slide setup
        if event.type == 'LEFTMOUSE' and event.value == 'PRESS' and event.ctrl:
            vert = get_vert_under_mouse(context, event, data)
            if vert:
                self.slide_locked = True
                bpy.ops.mesh.select_all(action='DESELECT')
                vert.select = True
                bpy.ops.transform.vert_slide('INVOKE_DEFAULT')
                return
            else:
                bpy.ops.hops.display_notification(info="Click vert")
            return

        # Mouse gesture setup
        if self.pressed:
            # Merge
            if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
                data.locked = True
                self.merge_locked = True
                self.pressed = False
            # Gravitate
            else:
                self.drag_distance += abs(event.mouse_x - event.mouse_prev_x)
                if self.drag_distance > 10:
                    data.locked = True
                    data.modal_mesh_start()
                    self.grav_locked = True

        # Detection start
        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            vert = get_vert_under_mouse(context, event, data)
            if vert:
                self.setup()
                self.pressed = True

                self.vert_one = vert
                self.grav_point = vert.co.copy()
                return
            else:
                bpy.ops.hops.display_notification(info="Click / Click Drag on point.")


    def __vert_merge(self, context, event, data, op):

        # Cancel
        if event.type == 'C' and event.value == "PRESS":
            self.setup()

        if event.type == "MOUSEMOVE":
            vert = get_vert_under_mouse(context, event, data)
            if vert:
                if vert == self.vert_one: return
                self.vert_two = vert

        # (3) Second click : Join the (first vert, second vert) and start over
        if self.vert_one and self.vert_two:
            if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
                verts = [self.vert_one, self.vert_two]
                bmesh.ops.pointmerge(data.bm, verts=verts, merge_co=self.vert_two.co)
                data.save()
                self.setup()


    def __gravitate(self, context, event, data, op):
        '''Merge verts into point using modal mesh mode.'''

        # Cancel
        if event.type == 'C' and event.value == "PRESS":
            self.setup()
            data.modal_mesh_cancel()
            return

        # Unlock / Remove backup
        elif event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            self.setup()
            data.modal_mesh_confirm()
            return

        data.mouse_accumulation -= op.base_controls.mouse
        self.grav_tolerance = abs(data.mouse_accumulation)
        data.modal_mesh_update(context, event, with_mouse_warp=True)

        # --- BMESH --- #
        merge_vert = None
        for v in data.bm.verts:
            if v.co == self.grav_point:
                merge_vert = v
                break
        if merge_vert == None:
            self.setup()
            bpy.ops.hops.display_notification(info="Lost reference to vertex")
            return

        verts = []
        self.grav_gl_points = []
        for v in data.bm.verts:
            if v == merge_vert: continue
            if (v.co - merge_vert.co).magnitude <= self.grav_tolerance:
                verts.append(v)
                self.grav_gl_points.append(data.obj.matrix_world @ v.co)
        if not verts:
            return

        merge_loc = merge_vert.co.copy()
        bmesh.ops.pointmerge(data.bm, verts=verts, merge_co=merge_loc)
        verts = [v for v in data.bm.verts if (v.co - merge_loc).magnitude < .001]
        bmesh.ops.remove_doubles(data.bm, verts=verts, dist=.125)


    def help(self):
        return [
            ("C",          "Cancel operation"),
            ("Click",      "Click 2 verts to merge at last"),
            ("Click Drag", "Click and drag a point for Gravitate"),
            ("Ctrl Click", "Vert slide tool (Release mouse to confirm)"),
            ("Shift Drag", "Knife vert to vert"),
            ("+ / -",      "Vertex Size"),
            ("", "________MERGE________")]


    def draw_2d(self, context, data, op):
        if self.grav_locked and self.grav_point:
            draw_modal_mesh_label_2d(
                context,
                (context.area.width * .5, context.area.height * .5),
                self.grav_tolerance,
                120 * dpi_factor(),
                additional=f'  {len(self.grav_gl_points)}')
            return


    def draw_3d(self, context, data, op):

        if self.join_locked:
            op.join.draw_3d(context, data, op)
            return

        if self.grav_locked:
            if self.grav_point:
                built_in_shader = 'UNIFORM_COLOR' if bpy.app.version[0] >=4 else '3D_UNIFORM_COLOR'
                shader = gpu.shader.from_builtin(built_in_shader)
                batch = batch_for_shader(shader, 'POINTS', {'pos': [data.obj.matrix_world @ self.grav_point]})
                shader.bind()
                shader.uniform_float('color', (1,0,0,1))
                gpu.state.blend_set('ALPHA')
                gpu.state.point_size_set(6)
                batch.draw(shader)
                del shader
                del batch

            if self.grav_gl_points:
                built_in_shader = 'UNIFORM_COLOR' if bpy.app.version[0] >=4 else '3D_UNIFORM_COLOR'
                shader = gpu.shader.from_builtin(built_in_shader)
                batch = batch_for_shader(shader, 'POINTS', {'pos': self.grav_gl_points})
                shader.bind()
                shader.uniform_float('color', (0,1,0,1))
                gpu.state.blend_set('ALPHA')
                gpu.state.point_size_set(3)
                batch.draw(shader)
                del shader
                del batch

            return

        if self.vert_one != None:
            built_in_shader = 'UNIFORM_COLOR' if bpy.app.version[0] >=4 else '3D_UNIFORM_COLOR'
            shader = gpu.shader.from_builtin(built_in_shader)
            batch = batch_for_shader(shader, 'POINTS', {'pos': [data.obj.matrix_world @ self.vert_one.co]})
            shader.bind()
            shader.uniform_float('color', (1,0,0,1))
            gpu.state.blend_set('ALPHA')
            gpu.state.point_size_set(6)
            batch.draw(shader)
            del shader
            del batch

        if self.vert_two != None:
            built_in_shader = 'UNIFORM_COLOR' if bpy.app.version[0] >=4 else '3D_UNIFORM_COLOR'
            shader = gpu.shader.from_builtin(built_in_shader)
            batch = batch_for_shader(shader, 'POINTS', {'pos': [data.obj.matrix_world @ self.vert_two.co]})
            shader.bind()
            shader.uniform_float('color', (1,0,0,1))
            gpu.state.blend_set('ALPHA')
            gpu.state.point_size_set(6)
            batch.draw(shader)
            del shader
            del batch

            first_pos = data.obj.matrix_world @ self.vert_one.co
            second_pos = data.obj.matrix_world @ self.vert_two.co

            verts = [first_pos, second_pos]
            indices = [(0,1)]

            built_in_shader = 'UNIFORM_COLOR' if bpy.app.version[0] >=4 else '3D_UNIFORM_COLOR'
            shader = gpu.shader.from_builtin(built_in_shader)
            batch = batch_for_shader(shader, 'LINES', {'pos': verts}, indices=indices)
            shader.bind()
            shader.uniform_float('color', (0,0,0,1))
            #Enable(GL_LINE_SMOOTH)
            gpu.state.blend_set('ALPHA')
            gpu.state.line_width_set(3)
            batch.draw(shader)
            del shader
            del batch