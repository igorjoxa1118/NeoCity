from .utils import *


class Dissolve:
    def setup(self):
        self.vert = None
        self.edge = None
        self.vert_draw = None
        self.edge_draw = None


    def update(self, context, event, data, op):
        # Vert mode
        if event.type == 'ONE' and event.value == "PRESS":
            bpy.ops.mesh.select_mode(use_extend=False, type="VERT")

        # Edge mode
        elif event.type == 'TWO' and event.value == "PRESS":
            bpy.ops.mesh.select_mode(use_extend=False, type="EDGE")

        # Get vert / edge
        if event.type == "MOUSEMOVE":
            if 'VERT' in data.bm.select_mode:
                self.vert = get_vert_under_mouse(context, event, data)
                if self.vert != None:
                    self.vert_draw = data.obj.matrix_world @ self.vert.co
            else:
               self.vert = None
               self.vert_draw = None

            if 'EDGE' in data.bm.select_mode:
                self.edge = get_edge_under_mouse(context, event, data, op)
                if self.edge != None:
                    self.edge_draw = get_edge_copy(self.edge, data)
            else:
                self.edge = None
                self.edge_draw = None

        # Close the deal
        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            save = False
            if self.edge != None:
                if self.edge in data.bm.edges:
                    bmesh.ops.dissolve_edges(data.bm, edges=[self.edge])
                    save = True

            if self.vert != None:
                if self.vert in data.bm.verts:
                    bmesh.ops.dissolve_verts(data.bm, verts=[self.vert], use_face_split=False, use_boundary_tear=False)
                    save = True

            if save:
                self.setup()
                data.save()


    def help(self):
        return [
            ("2",     "Select Edges"),
            ("1",     "Select Verts"),
            ("Click", "Dissolve selection"),
            ("", "________DISSOLVE________")]


    def draw_2d(self, context, data, op):
        pass


    def draw_3d(self, context, data, op):
        if self.vert_draw != None:

            built_in_shader = 'UNIFORM_COLOR' if bpy.app.version[0] >=4 else '3D_UNIFORM_COLOR'
            shader = gpu.shader.from_builtin(built_in_shader)
            batch = batch_for_shader(shader, 'POINTS', {'pos': [self.vert_draw]})
            shader.bind()
            shader.uniform_float('color', (1,0,0,1))
            gpu.state.blend_set('ALPHA')
            gpu.state.point_size_set(6)
            batch.draw(shader)
            del shader
            del batch

        if self.edge_draw != None:

            verts = []
            indices = []
            push = 0
            for index, vert in enumerate(self.edge_draw.verts):
                verts.append( (vert[0], vert[1], vert[2]) )
                indices.append( (index + push, index + push + 1) )
                push += 1
            built_in_shader = 'UNIFORM_COLOR' if bpy.app.version[0] >=4 else '3D_UNIFORM_COLOR'
            shader = gpu.shader.from_builtin(built_in_shader)
            batch = batch_for_shader(shader, 'LINES', {'pos': verts}, indices=indices)
            shader.bind()
            shader.uniform_float('color', (1,0,0,1))
            #Enable(GL_LINE_SMOOTH)
            gpu.state.blend_set('ALPHA')
            gpu.state.line_width_set(3)
            batch.draw(shader)
            del shader
            del batch