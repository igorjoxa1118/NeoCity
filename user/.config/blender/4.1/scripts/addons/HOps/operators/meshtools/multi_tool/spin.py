from .utils import *


class Spin:
    def setup(self):
        self.edge_draw = None


    def update(self, context, event, data, op):
        if event.type == "MOUSEMOVE":
            self.edge_draw = get_edge_under_mouse(context, event, data, op, as_copy=True)

        elif event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            edge = get_edge_under_mouse(context, event, data, op)
            if edge != None:
                use_ccw = True if event.shift else False
                bmesh.ops.rotate_edges(data.bm, edges=[edge], use_ccw=use_ccw)
                data.save()


    def help(self):
        return [
            ("Shift Click", "Spin the edge (Counter Clock Wise)"),
            ("Click",       "Spin the edge (Clock Wise)"),
            ("", "________SPIN________")]


    def draw_2d(self, context, data, op):
        pass


    def draw_3d(self, context, data, op):
        if self.edge_draw == None:
            return

        verts = []
        indices = []
        push = 0
        for index, vert in enumerate(self.edge_draw.verts):
            verts.append( (vert[0], vert[1], vert[2]) )
            indices.append( (index + push, index + push + 1) )
            push += 1

        shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'LINES', {'pos': verts}, indices=indices)
        shader.bind()
        shader.uniform_float('color', (1,0,0,1))
        #Enable(GL_LINE_SMOOTH)
        gpu.state.blend_set('ALPHA')
        gpu.state.line_width_set(3)
        batch.draw(shader)
        del shader
        del batch