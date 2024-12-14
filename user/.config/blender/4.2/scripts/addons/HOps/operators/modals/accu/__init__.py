import bpy, bmesh
from enum import Enum
import gpu
from gpu_extras.batch import batch_for_shader
from mathutils import Vector, Matrix
from .... utility import math as hops_math
from .... utils.space_3d import get_3D_point_from_mouse, scene_ray_cast, get_2d_point_from_3d_point
from ....utility.screen import dpi_factor

class State(Enum):
    MAKE_PRIMITIVE = 0
    ADJUSTING = 1


ANCHORS = ['TOP', 'BOTTOM', 'LEFT', 'RIGHT', 'FRONT', 'BACK', 'NONE']


class Bounds:
    def __init__(self):
        # Bottom
        self.bot_front_left  = Vector((0,0,0))
        self.bot_front_right = Vector((0,0,0))
        self.bot_back_left   = Vector((0,0,0))
        self.bot_back_right  = Vector((0,0,0))
        # Top
        self.top_front_left  = Vector((0,0,0))
        self.top_front_right = Vector((0,0,0))
        self.top_back_left   = Vector((0,0,0))
        self.top_back_right  = Vector((0,0,0))
        # OP
        self.anchor_point = Vector((0,0,0))

    # --- Points --- #

    def all_points(self):
        return [
            self.bot_front_left,
            self.bot_front_right,
            self.bot_back_left,
            self.bot_back_right,
            self.top_front_left,
            self.top_front_right,
            self.top_back_left,
            self.top_back_right]


    def top_points(self):
        return [
        self.top_front_left,
        self.top_front_right,
        self.top_back_left,
        self.top_back_right]


    def bottom_points(self):
        return [
            self.bot_front_left,
            self.bot_front_right,
            self.bot_back_left,
            self.bot_back_right]


    def center_face_points(self):
        top   = hops_math.coords_to_center([self.top_front_left, self.top_front_right, self.top_back_right , self.top_back_left ])
        bot   = hops_math.coords_to_center([self.bot_front_left, self.bot_front_right, self.bot_back_right , self.bot_back_left ])
        left  = hops_math.coords_to_center([self.bot_back_left , self.bot_front_left , self.top_front_left , self.top_back_left ])
        right = hops_math.coords_to_center([self.bot_back_right, self.bot_front_right, self.top_front_right, self.top_back_right])
        front = hops_math.coords_to_center([self.bot_front_left, self.bot_front_right, self.top_front_right, self.top_front_left])
        back  = hops_math.coords_to_center([self.bot_back_left , self.bot_back_right,  self.top_back_right , self.top_back_left ])
        return [top, bot, left, right, front, back]


    def face_center(self, face_points):
        return hops_math.coords_to_center(face_points)


    def faces(self):
        top   = [self.top_front_left, self.top_front_right, self.top_back_right , self.top_back_left ]
        bot   = [self.bot_front_left, self.bot_front_right, self.bot_back_right , self.bot_back_left ]
        left  = [self.bot_back_left , self.bot_front_left , self.top_front_left , self.top_back_left ]
        right = [self.bot_back_right, self.bot_front_right, self.top_front_right, self.top_back_right]
        front = [self.bot_front_left, self.bot_front_right, self.top_front_right, self.top_front_left]
        back  = [self.bot_back_left , self.bot_back_right,  self.top_back_right , self.top_back_left ]
        return [top, bot, left, right, front, back]


    def get_center_point(self):
        bounds = hops_math.coords_to_bounds(self.all_points())
        center = hops_math.coords_to_center(bounds)
        return center

    # --- Mapping --- #

    def map_bounds(self, bounds):
        self.bot_front_left  = bounds[0]
        self.bot_front_right = bounds[4]
        self.bot_back_left   = bounds[3]
        self.bot_back_right  = bounds[7]
        self.top_front_left  = bounds[1]
        self.top_front_right = bounds[5]
        self.top_back_left   = bounds[2]
        self.top_back_right  = bounds[6]


    def map_other_bounds(self, other_bounds):
        self.bot_front_left  = other_bounds.bot_front_left.copy()
        self.bot_front_right = other_bounds.bot_front_right.copy()
        self.bot_back_left   = other_bounds.bot_back_left.copy()
        self.bot_back_right  = other_bounds.bot_back_right.copy()
        self.top_front_left  = other_bounds.top_front_left.copy()
        self.top_front_right = other_bounds.top_front_right.copy()
        self.top_back_left   = other_bounds.top_back_left.copy()
        self.top_back_right  = other_bounds.top_back_right.copy()

    # --- Move --- #

    def move_face(self, face='TOP', offset=0, position=None):
        if face not in ANCHORS: return
        face_index = ANCHORS.index(face)
        faces = self.faces()
        face = faces[face_index]

        axis = 0                            # Left / Right
        if face_index in {0, 1}: axis = 2   # Top / Bottom
        elif face_index in {4, 5}: axis = 1 # Front / Back

        for vert in face:
            if position:
                vert[axis] = position[axis]
            else:
                vert[axis] += offset


    def set_anchor_point(self, anchor='TOP'):
        if anchor not in ANCHORS: return

        if anchor == 'NONE':
            self.anchor_point = hops_math.coords_to_center(self.all_points())
            return

        index = ANCHORS.index(anchor)
        self.anchor_point = self.center_face_points()[index]


    def move_to_anchor_point(self, anchor='TOP'):
        if anchor not in ANCHORS: return
        index = ANCHORS.index(anchor)

        new_point = Vector((0,0,0))
        if anchor == 'NONE':
            new_point = hops_math.coords_to_center(self.all_points())
        else:
            new_point = self.center_face_points()[index]

        offset = new_point - self.anchor_point
        for vert in self.all_points():
            vert -= offset

    # --- Equalize --- #

    def adjust_length_equalized(self, val, unit_length, length, width, height):
        div = length if length != 0 else 1
        r = val / div
        w = width * r
        h = height * r
        self.adjust_width(w, unit_length)
        self.adjust_height(h, unit_length)
        self.adjust_length(val, unit_length)


    def adjust_width_equalized(self, val, unit_length, length, width, height):
        div = width if width != 0 else 1
        r = val / div
        l = length * r
        h = height * r
        self.adjust_length(l, unit_length)
        self.adjust_height(h, unit_length)
        self.adjust_width(val, unit_length)


    def adjust_height_equalized(self, val, unit_length, length, width, height):
        div = height if height != 0 else 1
        r = val / div
        l = length * r
        w = width * r
        self.adjust_length(l, unit_length)
        self.adjust_width(w, unit_length)
        self.adjust_height(val, unit_length)

    # --- Setters --- #

    def adjust_length(self, val, unit_length):
        factor = unit_scale(unit_length)
        val /= factor
        diff = (self.top_front_left - self.top_front_right).magnitude
        diff -= val
        self.move_face(face='LEFT', offset=diff)


    def adjust_width(self, val, unit_length):
        factor = unit_scale(unit_length)
        val /= factor
        diff = (self.top_front_left - self.top_back_left).magnitude
        diff -= val
        self.move_face(face='FRONT', offset=diff)


    def adjust_height(self, val, unit_length):
        factor = unit_scale(unit_length)
        val /= factor
        diff = (self.top_front_left - self.bot_front_left).magnitude
        diff -= val
        self.move_face(face='TOP', offset=-diff)

    # --- Getters --- #

    def length(self, unit_length):
        factor = unit_scale(unit_length)
        dims = hops_math.dimensions(self.all_points())
        return round(dims[0] * factor, 4)


    def width(self, unit_length):
        factor = unit_scale(unit_length)
        dims = hops_math.dimensions(self.all_points())
        return round(dims[1] * factor, 4)


    def height(self, unit_length):
        factor = unit_scale(unit_length)
        dims = hops_math.dimensions(self.all_points())
        return round(dims[2] * factor, 4)

    # --- For Drawing --- #

    def gl_bottom_lines(self):
        return [
            self.bot_front_left , self.bot_front_right,
            self.bot_front_right, self.bot_back_right,
            self.bot_back_right,  self.bot_back_left,
            self.bot_back_left,   self.bot_front_left]


    def gl_top_lines(self):
        return [
            self.top_front_left , self.top_front_right,
            self.top_front_right, self.top_back_right,
            self.top_back_right,  self.top_back_left,
            self.top_back_left,   self.top_front_left]


    def gl_side_lines(self):
        return [
            self.bot_front_left , self.top_front_left,
            self.bot_front_right, self.top_front_right,
            self.bot_back_right,  self.top_back_right,
            self.bot_back_left,   self.top_back_left]


    def gl_all_lines(self):
        return [
            self.bot_front_left , self.top_front_left,
            self.bot_front_right, self.top_front_right,
            self.bot_back_right,  self.top_back_right,
            self.bot_back_left,   self.top_back_left,

            self.bot_front_left , self.bot_front_right,
            self.bot_front_right, self.bot_back_right,
            self.bot_back_right,  self.bot_back_left,
            self.bot_back_left,   self.bot_front_left,

            self.top_front_left , self.top_front_right,
            self.top_front_right, self.top_back_right,
            self.top_back_right,  self.top_back_left,
            self.top_back_left,   self.top_front_left]

# --- Ray --- #

def ray_point(context, event, loc, normal):
    point = Vector()
    if event.shift:
        point = cast_to_verts(context, event)
    elif event.ctrl:
        point, hit = cast_to_surface(context, event)
        if not hit: point = None
    else:
        point = cast_to_plane(context, event, loc, normal)
    return point


def cast_to_plane(context, event, loc, normal):
    mouse_pos = (event.mouse_region_x, event.mouse_region_y)
    point = get_3D_point_from_mouse(mouse_pos, context, loc, normal)
    return point


def cast_to_surface(context, event):
    hit, location, normal, index, object, matrix = scene_ray_cast(context, event)
    return location, hit


def cast_to_verts(context, event):
    hit, location, normal, index, obj, matrix = scene_ray_cast(context, event)
    if hit:
        depsgraph = context.evaluated_depsgraph_get()
        object_eval = obj.evaluated_get(depsgraph)
        mesh_eval = object_eval.data

        if len(mesh_eval.polygons) - 1 < index:
            return None

        polygon = mesh_eval.polygons[index]

        compare = None
        point = None
        for vert_index in polygon.vertices:

            if len(mesh_eval.vertices) - 1 < vert_index:
                return None

            vert = mesh_eval.vertices[vert_index]
            vert_co = obj.matrix_world @ vert.co

            if compare == None:
                compare = (location - vert_co).magnitude
                point = vert_co
                continue

            mag = (location - vert_co).magnitude
            if mag < compare:
                compare = mag
                point = vert_co

        if point != None:
            return point

    return None

# --- General --- #

def unit_scale(unit_length=''):
    if unit_length == 'Kilometers':
        return 0.001
    elif unit_length == 'Meters':
        return 1
    elif unit_length == 'Centimeters':
        return 100
    elif unit_length == 'Millimeters':
        return 1000
    elif unit_length == 'Micrometers':
        return 1000000
    elif unit_length == 'Miles':
        return 0.000621371
    elif unit_length == 'Feet':
        return 3.28084
    elif unit_length == 'Inches':
        return 39.37008
    elif unit_length == 'Thousandth':
        return 39370.1

# --- Exit --- #

def confirmed_exit(op, context):

    if op.use_edit_mode:
        add_lattice_cube(op, context)
    elif op.add_cube:
        add_cube_to_bounds(op, context)
    else:
        if op.exit_with_empty:
            use_empty_to_scale(op, context)
        else:
            add_lattice_cube(op, context)


def add_cube_to_bounds(op, context):

    if context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

    bm = bmesh.new()
    bmesh.ops.create_cube(bm)
    coords = [
        op.bounds.bot_front_left,
        op.bounds.bot_front_right,
        op.bounds.bot_back_left,
        op.bounds.bot_back_right,
        op.bounds.top_front_left,
        op.bounds.top_front_right,
        op.bounds.top_back_left,
        op.bounds.top_back_right]

    bounds = hops_math.coords_to_bounds(coords)
    center = hops_math.coords_to_center(bounds)
    extents = hops_math.dimensions(bounds)

    scale_mat = hops_math.get_sca_matrix(extents)
    bmesh.ops.transform(bm, matrix=scale_mat, verts=bm.verts)

    # Finish up, write the bmesh into a new mesh
    me = bpy.data.meshes.new("Mesh")
    bm.to_mesh(me)
    bm.free()

    # Add the mesh to the scene
    obj = bpy.data.objects.new("Object", me)
    context.collection.objects.link(obj)
    obj.location = center

    # Select and make active
    context.view_layer.objects.active = obj
    obj.select_set(True)


def add_lattice_cube(op, context):

    mod_name = "Accu_Lattice"

    def get_lattice():
        lattice_data = bpy.data.lattices.new('lattice')
        lattice_data.interpolation_type_u = 'KEY_LINEAR'
        lattice_data.interpolation_type_v = 'KEY_LINEAR'
        lattice_data.interpolation_type_w = 'KEY_LINEAR'
        lattice = bpy.data.objects.new('lattice', lattice_data)
        context.collection.objects.link(lattice)
        context.view_layer.objects.active = lattice
        lattice.select_set(True)
        return lattice


    def remove_old_mods(objs):
        for obj in objs:
            for mod in obj.modifiers:
                if mod.type == 'LATTICE':
                    if mod.name[:12] == mod_name:
                        if mod.object == None:
                            obj.modifiers.remove(mod)


    def add_lattice_mods(objs, with_vg=False):
        for obj in objs:
            mod = obj.modifiers.new(name=mod_name, type="LATTICE")
            mod.object = lattice
            if with_vg:
                mod.vertex_group = obj.vertex_groups.active.name


    def apply_matrix_lattice(lattice):
        # Add shape key base
        lattice.shape_key_add(name="AccuShapeBase", from_mix=False)

        # Get coords list for accu box
        coords = op.bounds.all_points()

        # Accu box data
        bounds = hops_math.coords_to_bounds(coords)
        center = hops_math.coords_to_center(bounds)
        extents = hops_math.dimensions(bounds)

        # Accubox matrix
        accubox_matrix = Matrix.Translation(center) @ hops_math.get_sca_matrix(extents)

        try:
            # lattice.data.transform(lattice.matrix_world.inverted() @ accubox_matrix)
            # Add deform shape key
            shape_key = lattice.shape_key_add(name="AccuShapeDeform", from_mix=False)
            for val in shape_key.data.values():
                val.co = lattice.matrix_world.inverted() @ accubox_matrix @ val.co
            shape_key.value = 1

        except:
            bpy.ops.hops.display_notification(info="Nice try bud.")

    # --- Edit Mode ---#
    if op.use_edit_mode:
        objs = [obj for obj in context.selected_objects if obj.type == 'MESH' and obj.mode == 'EDIT']

        # Get vert dims
        coords = []
        for obj in objs:
            obj.update_from_editmode()
            bm = bmesh.from_edit_mesh(obj.data)
            selected = [v for v in bm.verts if v.select == True]
            for vert in selected:
                coords.append(obj.matrix_world @ vert.co)

        bounds = hops_math.coords_to_bounds(coords)
        center = hops_math.coords_to_center(bounds)
        extents = hops_math.dimensions(bounds)


        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        # Get all selected verts
        good_objs = []
        for obj in objs:
            indexes = [v.index for v in obj.data.vertices if v.select]
            if len(indexes) < 1:
                continue
            v_group = obj.vertex_groups.new(name='Accu_Lattice')
            v_group.add(index=indexes, weight=1, type='ADD')
            obj.vertex_groups.active_index = v_group.index
            good_objs.append(obj)
        objs = good_objs

        lattice = get_lattice()

        # Locate and scale the lattice to fit the object
        for i in range(3):
            if not extents[i]:
                extents[i] = 1
        scale_mat = hops_math.get_sca_matrix(extents)
        lattice.matrix_world = scale_mat # write fit transformation in lattice matrix so it's up to date
        lattice.matrix_world.translation = center

        remove_old_mods(objs)
        add_lattice_mods(objs, with_vg=True)

        # Add shape key base
        lattice.shape_key_add(name="AccuShapeBase", from_mix=False)

        # Matrix
        apply_matrix_lattice(lattice)

    # --- Object Mode ---#
    else:
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        objs = [ob for ob in context.selected_objects if ob.type in {'MESH', 'CURVE', 'FONT', 'SURFACE'}]
        bpy.ops.object.select_all(action='DESELECT')

        lattice = get_lattice()
        remove_old_mods(objs)

        # Object bounds for the lattice
        coords = []
        for obj in objs:
            eval = obj.evaluated_get(context.evaluated_depsgraph_get())
            coords.extend([obj.matrix_world @ Vector(coord) for coord in eval.bound_box])

        bounds = hops_math.coords_to_bounds(coords)
        center = hops_math.coords_to_center(bounds)
        extents = hops_math.dimensions(bounds)

        # Locate and scale the lattice to fit the object
        for i in range(3):
            if not extents[i]:
                extents[i] = 1
        scale_mat = hops_math.get_sca_matrix(extents)
        lattice.matrix_world = scale_mat # write fit transformation in lattice matrix so it's up to date
        lattice.matrix_world.translation = center

        # Add mods
        add_lattice_mods(objs)

        # Matrix
        apply_matrix_lattice(lattice)


def use_empty_to_scale(op, context):

    if context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

    selected = [ob for ob in context.selected_objects if ob.type in {'MESH', 'CURVE', 'FONT', 'SURFACE'}]
    bpy.ops.object.select_all(action='DESELECT')

    # Empty
    empty = bpy.data.objects.new("AccuEmpty", None )
    context.collection.objects.link(empty)
    empty.empty_display_type = 'SPHERE'

    # Get coords list for accu box
    coords = op.bounds.all_points()

    # Accu box data
    bounds = hops_math.coords_to_bounds(coords)
    center = hops_math.coords_to_center(bounds)
    extents = hops_math.dimensions(bounds)

    size = max(extents[0], extents[1], extents[2])
    empty.empty_display_size = size * .5

    empty.location = center

    # Parent
    for obj in selected:
        offset = obj.matrix_world.translation - op.initial_center_point
        obj.parent = empty
        obj.location = offset

    # Scale X
    if op.initial_extents[0] != 0:
        sca = extents[0] / op.initial_extents[0]
        empty.scale[0] = sca

    # Scale Y
    if op.initial_extents[1] != 0:
        sca = extents[1] / op.initial_extents[1]
        empty.scale[1] = sca

    # Scale Z
    if op.initial_extents[2] != 0:
        sca = extents[2] / op.initial_extents[2]
        empty.scale[2] = sca

# --- Face Utils --- #

def get_face_index(op, context, event):

    threshold = 75 * dpi_factor()

    centers = op.bounds.center_face_points()
    points = []
    for center in centers:
        points.append(get_2d_point_from_3d_point(context, center))

    # Get closest face center to mouse
    mouse = Vector((event.mouse_region_x, event.mouse_region_y))
    index = None
    dist = None
    for i, point in enumerate(points):
        if point == None: continue

        compare = (mouse - point).magnitude
        if compare > threshold: continue

        if index == None:
            index = i
            dist = compare
            continue
        if dist > compare:
            index = i
            dist = compare

        if index == None: return None
    return index


def build_face_batch(self):
    bounds = self.op.bounds
    faces = bounds.faces()
    quad = faces[self.face_index]
    indices = [(0,1,2), (2,3,0)]
    self.face_batch = batch_for_shader(self.shader, 'TRIS', {'pos': quad}, indices=indices)
    self.point_batch = batch_for_shader(self.shader, 'POINTS', {'pos': bounds.center_face_points()})


def draw_face_3D(self):
    if not self.face_batch: return
    if not self.point_batch: return
    self.shader.bind()
    #Enable(GL_LINE_SMOOTH)
    gpu.state.blend_set('ALPHA')

    self.shader.uniform_float('color', (0,0,1,.125))
    self.face_batch.draw(self.shader)
    self.point_batch.draw(self.shader)
