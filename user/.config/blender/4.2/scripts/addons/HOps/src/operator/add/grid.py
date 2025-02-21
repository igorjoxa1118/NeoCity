import bpy
import math
import bmesh
from .... utility import addon
from mathutils import Matrix, Vector, Euler
from ....utility import math as hops_math

class Grid_common():

    axis : bpy.props.EnumProperty(
        name = 'Axis',
        description = 'Axis' ,
        items = [
            ('X', "X", "Allign along X axis"),
            ('Y', "Y", "Allign along Y axis"),
            ('Z', "Z", "Allign along Z axis"),
        ],
        default = 'Z',
    )

    selection_cutter : bpy.props.BoolProperty(
        name = 'Boolean',
        description = 'Adde boolean to the grid',
        default = True,
    )

    boolean_operation : bpy.props.EnumProperty(
        name = 'Mode',
        description = 'Mode' ,
        items = [
            ('INTERSECT', "INTERSECT", "For use with cutters"),
            ('DIFFERENCE', "DIFFERENCE", "For use with non-cutters"),
        ],
        default = 'INTERSECT',
    )

    replace : bpy.props.BoolProperty(
        name = 'Replace',
        description = 'Replace meshes of selection. Destructive.',
        default = False,
    )

    #circle

    circle_verts: bpy.props.IntProperty(
        name = 'Vert count',
        description = 'Number of vertices defining cercle',
        default = 16,
        min = 3,
    )

    circle_divisions: bpy.props.IntProperty(
        name = 'Divisions',
        description = 'How many times the grid is divided',
        default = 12,
        min = 1,
    )

    circle_radius: bpy.props.FloatProperty(
        name = 'Radius',
        description = 'Radius of the circle. Relative',
        default = 0.44,
        min = 0,
        max = 1
    )

    circle_checker : bpy.props.BoolProperty(
        name = 'Checker',
        description = 'Checker pattern',
        default = True,
    )

    def draw(self, context):

        if self.spawn_selection:
            self.layout.prop(self, 'axis')
            self.layout.prop(self, 'selection_cutter')
            if self.selection_cutter:
                self.layout.prop(self, 'boolean_operation')
        if self.__class__.__name__.endswith('circle'):
            if self.spawn_selection:
                self.layout.prop(self, 'replace')
            self.layout.prop(self, 'circle_verts')
            self.layout.prop(self, 'circle_divisions')
            self.layout.prop(self, 'circle_radius')
            self.layout.prop(self, 'circle_checker')

    def invoke(self, context, event):
        self.spawn_selection = True if event.shift else False
        self.replace = False if not self.spawn_selection else self.replace

        return self.execute(context)

    def to_selection(self, context, source_obj):


        for obj in self.selection:

            grid = source_obj.copy()
            grid.data = source_obj.data.copy()

            context.collection.objects.link(grid)

            context.view_layer.objects.active = grid

            center = hops_math.coords_to_center([ obj.matrix_world @ Vector(v) for v in obj.bound_box ])

            trans = Matrix.Translation(center)

            XYZ = 'XYZ'

            if self.axis == 'X':
                eul = Euler((0.0, math.radians(90.0), 0.0), XYZ)
            elif self.axis == 'Y':
                eul = Euler((math.radians(-90.0), 0.0, 0.0), XYZ)
            elif self.axis == 'Z':
                eul = Euler((0.0, 0.0, 0.0), XYZ)

            quat =  obj.matrix_world.to_quaternion()
            eul.rotate(quat)

            grid.matrix_world = trans @ eul.to_quaternion().to_matrix().to_4x4()

            if self.selection_cutter:
                intersect = grid.modifiers.new(type ='BOOLEAN', name ='INTERSECT')

                intersect.object = obj
                intersect.operation = self.boolean_operation

                if hasattr(intersect, 'solver'):
                    intersect.solver = 'FAST'

        bpy.data.objects.remove(source_obj)

    def replace_mesh(self, context, source_bm):

        XYZ = 'XYZ'

        if self.axis == 'X':
            eul = Euler((0.0, math.radians(90.0), 0.0), XYZ)
        elif self.axis == 'Y':
            eul = Euler((math.radians(-90.0), 0.0, 0.0), XYZ)
        elif self.axis == 'Z':
            eul = Euler((0.0, 0.0, 0.0), XYZ)

        rotation = eul.to_quaternion().to_matrix().to_4x4()

        bmesh.ops.transform(source_bm, verts = source_bm.verts, matrix =rotation)

        for obj in self.selection:

            if not obj.data or obj.type != 'MESH': continue

            source_bm.to_mesh(obj.data)
            obj.data.update()

        source_bm.free()


class HOPS_OT_ADD_grid_square(Grid_common, bpy.types.Operator):
    bl_idname = "hops.add_grid_square"
    bl_label = "Add smart grid_square"
    bl_options = {"REGISTER", "UNDO", "GRAB_CURSOR", "BLOCKING"}
    bl_description = """Create Smart grid_square
    shift - to_selection (placement and boolean)
    """


    def execute(self, context):
        self.selection = context.selected_objects[:]
        verts = [(-1, -1, 0)]
        obj = bpy.data.objects.new("Grid", bpy.data.meshes.new("Grid"))

        bpy.ops.object.select_all(action='DESELECT')
        context.collection.objects.link(obj)
        context.view_layer.objects.active = obj
        obj.select_set(True)

        bpy.ops.view3d.snap_selected_to_cursor(use_offset=False)

        if addon.preference().behavior.cursor_boolshapes:
            obj.rotation_euler = bpy.context.scene.cursor.rotation_euler

        bm = bmesh.new()
        for v in verts:
            bm.verts.new(v)
        bm.to_mesh(context.object.data)
        bm.free()

        self.add_screw_modifier(obj, 'X', 'HOPS_screw_x')
        self.add_screw_modifier(obj, 'Y', 'HOPS_screw_y', True)
        # self.add_decimate_modifier(obj, 'HOPS_decimate')
        self.add_wireframe_modifier(obj)
        if addon.preference().behavior.auto_smooth:
            bpy.context.object.data.use_auto_smooth = True
            bpy.context.object.data.auto_smooth_angle = math.radians(30)

        if self.spawn_selection:

            self.to_selection( context, obj)

        return {"FINISHED"}


    def add_wireframe_modifier(self, object):
        modifier = object.modifiers.new(name="HOPS_wireframe_c", type="WIREFRAME")
        modifier.thickness = 0.02
        modifier.use_even_offset = True
        modifier.use_relative_offset = False
        modifier.use_replace = True
        modifier.use_boundary = True


    def add_screw_modifier(self, object, axis='X', name='HOPS_screw_x', flip=False):
        screw_modifier = object.modifiers.new(name=name, type="SCREW")
        screw_modifier.angle = math.radians(0)
        screw_modifier.axis = axis
        screw_modifier.steps = 10
        screw_modifier.render_steps = 10
        screw_modifier.screw_offset = 2
        screw_modifier.iterations = 1
        screw_modifier.use_smooth_shade = True
        screw_modifier.use_merge_vertices = True
        screw_modifier.use_normal_flip = flip


    def add_displace_modifier(self, object, axis='X', name='HOPS_displace_x'):
        displace_modifier = object.modifiers.new(name=name, type="DISPLACE")
        displace_modifier.direction = axis
        displace_modifier.strength = -1.5


    def add_decimate_modifier(self, object, name='HOPS_decimate_c'):
        modifier = object.modifiers.new('Decimate', 'DECIMATE')
        modifier.angle_limit = math.radians(5)
        modifier.decimate_type = 'DISSOLVE'


class HOPS_OT_ADD_grid_diamond(Grid_common, bpy.types.Operator):
    bl_idname = "hops.add_grid_diamond"
    bl_label = "Add smart grid_diamond"
    bl_options = {"REGISTER", "UNDO", "GRAB_CURSOR", "BLOCKING"}
    bl_description = """Create Smart grid_diamond
    shift - to_selection (placement and boolean)
    """

    def execute(self, context):
        self.selection = context.selected_objects[:]

        verts = [(-1, -1, 0)]
        obj = bpy.data.objects.new("Grid", bpy.data.meshes.new("Grid"))

        bpy.ops.object.select_all(action='DESELECT')
        context.collection.objects.link(obj)
        context.view_layer.objects.active = obj
        obj.select_set(True)

        bpy.ops.view3d.snap_selected_to_cursor(use_offset=False)
        if addon.preference().behavior.cursor_boolshapes:
            obj.rotation_euler = bpy.context.scene.cursor.rotation_euler

        bm = bmesh.new()
        for v in verts:
            bm.verts.new(v)
        bm.to_mesh(context.object.data)
        bm.free()

        self.add_screw_modifier(obj, 'X', 'HOPS_screw_x')
        self.add_screw_modifier(obj, 'Y', 'HOPS_screw_y', True)
        self.add_decimate_modifier(obj, 'DISSOLVE', 'HOPS_decimate')
        self.add_subsurf_modifier(obj, 'HOPS_subsurf')
        self.add_decimate_modifier(obj, 'UNSUBDIV', 'HOPS_unsubdiv')
        self.add_wireframe_modifier(obj)
        if addon.preference().behavior.auto_smooth:
            bpy.context.object.data.use_auto_smooth = True
            bpy.context.object.data.auto_smooth_angle = math.radians(30)

        if self.spawn_selection:

            self.to_selection(context, obj)

        return {"FINISHED"}


    def add_subsurf_modifier(self, object, name='HOPS_deform_z'):
        subsurf_mod = object.modifiers.new(name=name, type="SUBSURF")
        subsurf_mod.subdivision_type = 'SIMPLE'
        subsurf_mod.levels = 4


    def add_wireframe_modifier(self, object):
        modifier = object.modifiers.new(name="HOPS_wireframe_c", type="WIREFRAME")
        modifier.thickness = 0.02
        modifier.use_even_offset = True
        modifier.use_relative_offset = False
        modifier.use_replace = True
        modifier.use_boundary = True


    def add_screw_modifier(self, object, axis='X', name='HOPS_screw_x', flip=False):
        screw_modifier = object.modifiers.new(name=name, type="SCREW")
        screw_modifier.angle = math.radians(0)
        screw_modifier.axis = axis
        screw_modifier.steps = 3
        screw_modifier.render_steps = 3
        screw_modifier.screw_offset = 2
        screw_modifier.iterations = 1
        screw_modifier.use_smooth_shade = True
        screw_modifier.use_merge_vertices = True
        screw_modifier.use_normal_flip = flip


    def add_displace_modifier(self, object, axis='X', name='HOPS_displace_x'):
        displace_modifier = object.modifiers.new(name=name, type="DISPLACE")
        displace_modifier.direction = axis
        displace_modifier.strength = -1.5


    def add_decimate_modifier(self, object, types, name='HOPS_decimate_c'):
        modifier = object.modifiers.new('Decimate', 'DECIMATE')
        modifier.angle_limit = math.radians(5)
        modifier.decimate_type = types
        modifier.iterations = 1


class HOPS_OT_ADD_grid_honey(Grid_common, bpy.types.Operator):
    bl_idname = "hops.add_grid_honey"
    bl_label = "Add smart grid_honey"
    bl_options = {"REGISTER", "UNDO", "GRAB_CURSOR", "BLOCKING"}
    bl_description = """Create Smart grid_honey
    shift - to_selection (placement and boolean)
    """

    def execute(self, context):
        self.selection = context.selected_objects[:]

        verts = [(0, 0, 0)]
        obj = bpy.data.objects.new("Grid", bpy.data.meshes.new("Grid"))

        bpy.ops.object.select_all(action='DESELECT')
        context.collection.objects.link(obj)
        context.view_layer.objects.active = obj
        obj.select_set(True)

        bpy.ops.view3d.snap_selected_to_cursor(use_offset=False)
        if addon.preference().behavior.cursor_boolshapes:
            obj.rotation_euler = bpy.context.scene.cursor.rotation_euler

        bm = bmesh.new()
        for v in verts:
            bm.verts.new(v)
        bm.to_mesh(context.object.data)
        bm.free()

        self.add_displace_modifier(obj, 'X', 'HOPS_displace_x')
        self.add_screw_modifier(obj, 0, 'X', 'HOPS_screw_x', 0.02, 2)
        self.add_screw_modifier(obj, 360, 'Z', 'HOPS_screw_y', 0, 6, True)
        self.add_decimate_modifier(obj, 'DISSOLVE', 'HOPS_decimate')
        self.add_solidify_modifier(obj, 'HOPS_solidify_z')
        self.add_array_modifier(obj, 0, 1, 2, 'HOPS_array_1')
        self.add_array_modifier(obj, 0.75, 0.25, 2, 'HOPS_array_2')
        self.add_array_modifier(obj, 0.85, 0, 4, 'HOPS_array_3')
        self.add_array_modifier(obj, 0, 0.8, 3, 'HOPS_array_4')

        if addon.preference().behavior.auto_smooth:
            bpy.context.object.data.use_auto_smooth = True
            bpy.context.object.data.auto_smooth_angle = math.radians(30)


        if self.spawn_selection:

            self.to_selection( context, obj)

        return {"FINISHED"}


    def add_array_modifier(self, object, x, y, c, name='HOPS_array_z'):
        modifier = object.modifiers.new(name, "ARRAY")
        modifier.relative_offset_displace[0] = x
        modifier.relative_offset_displace[1] = y
        modifier.relative_offset_displace[2] = 0
        modifier.count = c
        modifier.merge_threshold = 0.01


    def add_subsurf_modifier(self, object, name='HOPS_deform_z'):
        subsurf_mod = object.modifiers.new(name=name, type="SUBSURF")
        subsurf_mod.subdivision_type = 'SIMPLE'
        subsurf_mod.levels = 2


    def add_wireframe_modifier(self, object):
        modifier = object.modifiers.new(name="HOPS_wireframe_c", type="WIREFRAME")
        modifier.thickness = 0.02
        modifier.use_even_offset = True
        modifier.use_relative_offset = False
        modifier.use_replace = True
        modifier.use_boundary = True


    def add_screw_modifier(self, object, angle=0, axis='X', name='HOPS_screw_x', offset=0.02, step=6, flip=False):
        screw_modifier = object.modifiers.new(name=name, type="SCREW")
        screw_modifier.angle = math.radians(angle)
        screw_modifier.axis = axis
        screw_modifier.steps = step
        screw_modifier.render_steps = step
        screw_modifier.screw_offset = offset
        screw_modifier.iterations = 1
        screw_modifier.use_smooth_shade = True
        screw_modifier.use_merge_vertices = True
        screw_modifier.use_normal_flip = flip


    def add_displace_modifier(self, object, axis='X', name='HOPS_displace_x'):
        displace_modifier = object.modifiers.new(name=name, type="DISPLACE")
        displace_modifier.direction = axis
        displace_modifier.strength = 0.20


    def add_decimate_modifier(self, object, types, name='HOPS_decimate_c'):
        modifier = object.modifiers.new('Decimate', 'DECIMATE')
        modifier.angle_limit = math.radians(5)
        modifier.decimate_type = types
        modifier.iterations = 1


    def add_solidify_modifier(self, object, name='HOPS_solidify_z'):
        solidify_modifier = object.modifiers.new(name, "SOLIDIFY")
        solidify_modifier.thickness = 0.02
        solidify_modifier.offset = 1
        solidify_modifier.use_even_offset = True
        solidify_modifier.use_quality_normals = True
        solidify_modifier.use_rim_only = False
        solidify_modifier.show_on_cage = True

class HOPS_OT_ADD_grid_circle(Grid_common, bpy.types.Operator):
    bl_idname = "hops.add_grid_circle"
    bl_label = "Add smart grid_circle"
    bl_options = {"REGISTER", "UNDO", "GRAB_CURSOR", "BLOCKING"}
    bl_description = """Create Smart circle grid
    shift - to_selection (placement and boolean)
    F9 for options
    """

    def execute(self, context):

        self.selection = context.selected_objects[:]
        circle_verts = self.circle_verts

        grid_divs = self.circle_divisions

        radius = self.circle_radius/2

        checker = self.circle_checker and grid_divs>1

        bm = bmesh.new()

        grid_size = 0.5
        grid = bmesh.ops.create_grid(bm, size=grid_size)

        bmesh.ops.subdivide_edges(bm, edges = bm.edges, cuts=1 , use_grid_fill = False)

        square_edges = set(bm.edges)


        y_pos = Vector((0, grid_size, 0))
        x_pos = Vector((grid_size, 0, 0))

        y_pos_vert = [v for v in bm.verts if v.co == y_pos][0]
        y_neg_vert = [v for v in bm.verts if v.co == -y_pos][0]

        x_pos_vert = [v for v in bm.verts if v.co == x_pos][0]
        x_neg_vert = [v for v in bm.verts if v.co == -x_pos][0]

        circle = bmesh.ops.create_circle(bm, cap_ends = 0, segments = circle_verts, radius = radius)

        verts_y = sorted(circle['verts'], key=lambda e:e.co.y)
        verts_x = sorted(circle['verts'], key=lambda e:e.co.x)

        bm.edges.new((y_pos_vert, verts_y[-1]))
        bm.edges.new((y_neg_vert, verts_y[0]))
        bm.edges.new((x_pos_vert, verts_x[-1]))
        bm.edges.new((x_neg_vert, verts_x[0]))

        edge_net = [e for e in bm.edges if e not in square_edges]

        bmesh.utils.face_split_edgenet(bm.faces[:][0], edge_net)

        _set = set((y_pos_vert, y_neg_vert, x_pos_vert, x_neg_vert))

        bmesh.ops.delete(bm, geom =[f for f in bm.faces if all([v not in set(f.verts) for v in _set])] , context = 'FACES')

        spin_offset = 1/grid_divs
        spin_steps = grid_divs-1


        if checker:

            grid = bmesh.ops.create_grid(bm, size=grid_size, matrix = Matrix.Translation((1,0,0)), x_segments = 3, y_segments =3 )
            bmesh.ops.spin(bm, geom = bm.faces, cent = [0,0,0], axis = [0,0,1], dvec = [-1,-1,0], angle = math.pi, steps = 1, use_merge =0, use_normal_flip =0, use_duplicate = 1)
            spin_offset *=2
            spin_steps =int(spin_steps/2)

        bmesh.ops.scale(bm, verts = bm.verts , vec = Vector((1,1,0))/grid_divs )
        bmesh.ops.translate(bm, verts = bm.verts , vec = Vector((-.5,-.5,0))+ Vector((.5,.5,0))/grid_divs)

        bmesh.ops.spin(bm, geom = bm.faces, cent = [0,0,0], axis = [1,0,0], dvec = [spin_offset,0,0], angle =0, steps = spin_steps, use_merge =0, use_normal_flip =0, use_duplicate = 1)
        bmesh.ops.spin(bm, geom = bm.faces, cent = [0,0,0], axis = [0,spin_offset,0], dvec = [0,spin_offset,0], angle =0, steps = spin_steps, use_merge =0, use_normal_flip =0, use_duplicate = 1)

        if checker:

            def comparer(face):
                center = face.calc_center_median()
                return center.x > 0.5 or center.y > 0.5

            faces = [f for f in bm.faces if comparer(f)]
            bmesh.ops.delete(bm, geom = faces, context ='FACES')

        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.000001)

        bmesh.ops.scale(bm, verts = bm.verts , vec = [2,2,0] )

        if not self.replace:
            bpy.ops.object.select_all(action='DESELECT')

            grid_mesh = bpy.data.meshes.new('circle Grid')
            grid = bpy.data.objects.new('Grid', grid_mesh )

            context.collection.objects.link(grid)
            grid.select_set(True)
            context.view_layer.objects.active = grid

            bm.to_mesh(grid_mesh)
            grid_mesh.update()

            bm.free()

        if self.spawn_selection:

            if self.replace:

                self.replace_mesh( context, bm)

            else:

                self.to_selection( context, grid)



        return {'FINISHED'}
