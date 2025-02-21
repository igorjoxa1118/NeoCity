from .utils import *


class Knife_Data:

    def __init__(self):
        self.reset()


    def reset(self):
        self.edge_to_vert_thresh = .1
        self.edge_snap_percent = .25
        self.ray_data = None
        self.gl_point_loc = None

        # Edge snap data
        self.bm_edge = None
        self.start_vert = None
        self.distance_percent = None


    def get_and_gen_bm_vert(self, dont_perform_cut=False):
        '''Generate the and return the bm vert from ray loc.'''
        
        if self.validate_state() == False:
            return None

        if dont_perform_cut == True:
            return self.start_vert

        if self.distance_percent == 0:
            return self.start_vert
        elif self.distance_percent == 1:
            for vert in self.bm_edge.verts:
                if vert != self.start_vert:
                    return vert

        edge, vert = bmesh.utils.edge_split(self.bm_edge, self.start_vert, self.distance_percent)
        self.bm_edge = edge
        self.start_vert = vert
        return vert


    def set_bm_edge(self, bm, edge, obj, ray_data, snaps=''):
        '''Set bm edge data for drawing and for edge split loc.'''

        # Assign incoming
        self.bm_edge = edge
        self.ray_data = ray_data

        # Ensure new data
        if self.validate_state() == False:
            self.reset()

        # Ray data
        ray_loc = ray_data['location']
        ray_norm = ray_data['normal']

        # Object world matrix
        world_mat = obj.matrix_world

        # Validate
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()

        # Edge length
        edge_length = self.bm_edge.calc_length()

        # Verts on edge
        vert_one = edge.verts[0]
        vert_two = edge.verts[1]

        # Vert locations
        vert_one_loc = world_mat @ vert_one.co
        vert_two_loc = world_mat @ vert_two.co

        # Vert distances from ray loc
        vert_one_dist = (ray_loc - vert_one_loc).magnitude
        vert_two_dist = (ray_loc - vert_two_loc).magnitude
        
        # Get closest vert
        shortest_distance = 0
        closest_vert = None
        if vert_one_dist < vert_two_dist:
            shortest_distance = vert_one_dist
            closest_vert = vert_one
            self.gl_point_loc = vert_one_loc
        else:
            shortest_distance = vert_two_dist
            closest_vert = vert_two
            self.gl_point_loc = vert_two_loc

        # Check if we should just use the vert because its inside the thresh
        finished = False
        thresh_length = edge_length * self.edge_to_vert_thresh
        if shortest_distance <= thresh_length:
            self.start_vert = closest_vert
            self.distance_percent = 0
            finished = True
        else:
            self.gl_point_loc = None
        if finished:
            return True

        # Get the closest point to the edge and a percent from the first vert to the point
        point, distance = mathutils.geometry.intersect_point_line(ray_loc, vert_one_loc, vert_two_loc)
        self.start_vert = vert_one

        if math.isnan(distance):
            return False

        # Snap to the nearest rounded position
        if snaps == 'CTRL':            
            self.distance_percent = round(distance * 4) / 4.0
            position = self.start_vert.co.lerp(vert_two.co, self.distance_percent)
            self.gl_point_loc = world_mat @ position

        elif snaps == 'SHIFT':
            if distance > .5: self.distance_percent = 1
            else: self.distance_percent = 0
            position = self.start_vert.co.lerp(vert_two.co, self.distance_percent)
            self.gl_point_loc = world_mat @ position

        # Get a point along the line closest to the ray location
        else:
            self.distance_percent = distance
            self.gl_point_loc = point


        return True


    def validate_state(self):
        '''Make sure data is valid.'''

        if self.bm_edge == None:
            return False

        if type(self.ray_data) != dict:
            return False

        ray_data_keys = {'result', 'location', 'normal', 'index', 'object', 'matrix'}
        for key, val in self.ray_data.items():
            if key not in ray_data_keys:
                return False
        
        if isinstance(self.bm_edge, bmesh.types.BMEdge):
            return True
        else:
            return False


    def transfer_data_knife(self, other):
        '''Transfer data over from other knife to make swap chain.'''

        self.ray_data = other.ray_data
        self.gl_point_loc = other.gl_point_loc

        # Edge snap data
        self.bm_edge = other.bm_edge
        self.start_vert = other.start_vert
        self.distance_percent = other.distance_percent


class Knife:
    def setup(self):
        self.start = False
        self.chain_running = False
        self.first = Knife_Data()
        self.second = Knife_Data()
        self.draw_points = []


    def update(self, context, event, data, op):
        # Cancel
        if event.type in {'C', 'E'} and event.value == "PRESS":
            self.setup()
        
        snap = "CTRL" if event.ctrl else ""
        snap = "SHIFT" if event.shift else snap

        # (1) Scan for first edge under mouse
        if self.start == False:
            if event.type == 'MOUSEMOVE':
                edge, ray_data = get_edge_under_mouse(context, event, data, op, ret_with_ray_data=True)
                if edge != None:
                    if self.first.set_bm_edge(data.bm, edge, data.obj, ray_data, snaps=snap) == False:
                        self.start = False
                        self.first.reset()
                        self.second.reset()

        # (2) Confirm first edge edge
        if self.start == False:
            if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
                if self.first.validate_state():
                    self.start = True

        # (3) Scan for second edge under mouse
        if self.start == True:
            if event.type == "MOUSEMOVE":
                edge, ray_data = get_edge_under_mouse(context, event, data, op, ret_with_ray_data=True)
                if edge != None:
                    # Make sure its not the first edge
                    if edge != self.first.bm_edge:
                        if self.second.set_bm_edge(data.bm, edge, data.obj, ray_data, snaps=snap) == False:
                            self.start = False
                            self.first.reset()
                            self.second.reset()

        # (4) Confirm operation
        if self.start == True:
            if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
                
                if self.first.validate_state():
                    if self.second.validate_state():

                        first_vert = self.first.get_and_gen_bm_vert(dont_perform_cut=self.chain_running)
                        second_vert = self.second.get_and_gen_bm_vert()

                        # Something failed
                        if first_vert == None or second_vert == None:
                            self.start = False
                            self.first.reset()
                            self.second.reset()
                            return

                        if first_vert != second_vert:
                            verts = [first_vert, second_vert]
                            bmesh.ops.connect_vert_pair(data.bm, verts=verts)
                            data.save()                      
                        else:
                            self.second.reset()
                            return
                        
                        self.start = True
                        self.chain_running = True
                        self.first.transfer_data_knife(self.second)
                        self.second.reset()


    def help(self):
        return [
            ("C / E", "Cancel cut chain"),
            ("SHIFT", "Vert Snap"),
            ("Ctrl",  "Edge Snap 25% increments"),
            ("Click", "Click 2 verts / edges to knife at last"),
            ("", "________KNIFE________")]


    def draw_2d(self, context, data, op):
        factor = dpi_factor()
        up = 40 * factor
        right = 40 * factor
        font_size = 12

        if self.first.gl_point_loc != None:
            point = get_2d_point_from_3d(self.first.gl_point_loc, data)
            if point != None:
                text_loc = (point[0] + up, point[1] + right)
                text = f'{int(self.first.distance_percent * 100)} %'
                render_text(text=text, position=text_loc, size=font_size, color=(0,1,1,1))

                verts = (point, text_loc)
                draw_2D_lines(vertices=verts, width=.5, color=(0,1,1,.25))

        if self.second.gl_point_loc != None:
            point = get_2d_point_from_3d(self.second.gl_point_loc, data)
            if point != None:
                text_loc = (point[0] + up, point[1] + right)
                text = f'{int(self.second.distance_percent * 100)} %'
                render_text(text=text, position=text_loc, size=font_size, color=(0,1,1,1))

                verts = (point, text_loc)
                draw_2D_lines(vertices=verts, width=.5, color=(0,1,1,.25))


    def draw_3d(self, context, data, op):
        if self.draw_points != []:

            verts = [self.draw_points[0], self.draw_points[1]]
            indices = [(0,1)]

            built_in_shader = 'UNIFORM_COLOR' if bpy.app.version[0] >=4 else '3D_UNIFORM_COLOR'
            shader = gpu.shader.from_builtin(built_in_shader)
            batch = batch_for_shader(shader, 'LINES', {'pos': verts}, indices=indices)
            shader.bind()
            shader.uniform_float('color', (1,1,0,1))
            #Enable(GL_LINE_SMOOTH)
            gpu.state.blend_set('ALPHA')
            gpu.state.line_width_set(3)
            batch.draw(shader)
            del shader
            del batch

        if self.first.gl_point_loc != None:

            built_in_shader = 'UNIFORM_COLOR' if bpy.app.version[0] >=4 else '3D_UNIFORM_COLOR'
            shader = gpu.shader.from_builtin(built_in_shader)
            batch = batch_for_shader(shader, 'POINTS', {'pos': [self.first.gl_point_loc]})
            shader.bind()
            shader.uniform_float('color', (1,0,0,1))
            gpu.state.blend_set('ALPHA')
            gpu.state.point_size_set(6)
            batch.draw(shader)
            del shader
            del batch

        if self.second.gl_point_loc != None:

            built_in_shader = 'UNIFORM_COLOR' if bpy.app.version[0] >=4 else '3D_UNIFORM_COLOR'
            shader = gpu.shader.from_builtin(built_in_shader)
            batch = batch_for_shader(shader, 'POINTS', {'pos': [self.second.gl_point_loc]})
            shader.bind()
            shader.uniform_float('color', (1,0,0,1))
            gpu.state.blend_set('ALPHA')
            gpu.state.point_size_set(6)
            batch.draw(shader)
            del shader
            del batch

        if self.second.gl_point_loc != None and self.first.gl_point_loc != None:

            verts = [self.first.gl_point_loc, self.second.gl_point_loc]
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