import bpy
import bmesh
import bpy.utils.previews
from math import radians
from ... utility import addon, collections, object, math , modifier, operator_override, context_copy
from ... utils.blender_ui import get_dpi_factor
from ... utils.context import ExecutionContext
from bpy.props import EnumProperty, FloatProperty, BoolProperty
from mathutils import Vector, Matrix, Euler

class HOPS_OT_Conv_To_Shape(bpy.types.Operator):
    bl_idname = "hops.to_shape"
    bl_label = "To_Shape"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = """To_Shape
Convert selection to a myriad of shapes including empties

LMB - Converts selection to single primitive
LMB+SHIFT - Creates primitive per object
LMB+CTRL - Parent selection to empties

"""
#general
    individual: bpy.props.BoolProperty(
    name="Individual", description="Create shape per object using its local space", default = False)

    equalize: bpy.props.BoolProperty(
    name="Equalize", description="Make all dimensions equal", default = False)

    equalize_radius: bpy.props.BoolProperty(
    name="Radius only", description="Make all but longest dimension equal", default = False)

    modified: bpy.props.BoolProperty(
        name="Modified",
        description="Take the bounding box dimensions from the modified object",
        default=True)

    alignment: bpy.props.EnumProperty(
        name="Alignment",
        description="What axis to allign along",
        items=[
            ('AUTO_OBJECT', "AUTO_OBJECT", "Allign along longest object dimension"),
            ('AUTO_MESH', "AUTO_MESH", "Allign along longest mesh dimension"),
            ('X', "X", "Allign along X axis"),
            ('Y', "Y", "Allign along Y axis"),
            ('Z', "Z", "Allign along Z axis"),
            ],
        default='AUTO_OBJECT')
    scale: bpy.props.FloatProperty(
        name="Scale",
        description="Scale",
        default=1)

    copy_1st_bvl: bpy.props.BoolProperty(
        name="Copy 1st bevel",
        description="Copy 1st bevel of targe object",
        default=False)
    copy_1st_bvl_angle_only: bpy.props.BoolProperty(
        name="Angle only",
        description="Only consider Angle limit mode Bevels",
        default=False)

    parent_shape: bpy.props.BoolProperty(
        name="Parent shape to selection",
        description="Parent shape to selectio",
        default=False)
    parent_shape_inverse: bpy.props.BoolProperty(
        name="Inverse",
        description="Invert parenting",
        default=False)

##cylinder
    cyl_segments: bpy.props.IntProperty(
        name="Segments",
        description="Number of segments",
        default=32,
        min=3)
    cyl_diameter1: bpy.props.FloatProperty(
        name="Diameter 1",
        description="Diameter 1",
        default=1)

    cyl_diameter2: bpy.props.FloatProperty(
        name="Diameter 2",
        description="Diameter 2",
        default=1)

##sphere
    sphere_segments: bpy.props.IntProperty(
        name="Segments",
        description="Nmber of segments",
        default=32,
        min=3)
    sphere_rings: bpy.props.IntProperty(
        name="Rings",
        description="Number of rings",
        default=16,
        min=3)

    sphere_diameter: bpy.props.FloatProperty(
        name="Diameter",
        description="Diameter",
        default=1)

##plane
    plane_alignment: bpy.props.EnumProperty(
        name="Plane axis",
        description="What side to create planeo on",
        items=[
            ('+X', "+X", "Create a plane on the +X axis"),
            ('+Y', "+Y", "Create a plane on the +Y axis"),
            ('+Z', "+Z", "Create a plane on the +Z axis"),
            ('-X', "-X", "Create a plane on the -X axis"),
            ('-Y', "-Y", "Create a plane on the -Y axis"),
            ('-Z', "-Z", "Create a plane on the -Z axis")],
        default='+X')

    plane_offset: bpy.props.FloatProperty(
        name="Offset",
        description="Offset plane from selection",
        default=0)
# empty
    empty_display: bpy.props.EnumProperty(
        name="Display type",
        description="Empty display type",
        items=[
        ('PLAIN_AXES', 'PLAIN_AXES', 'PLAIN_AXES'),
        ('SINGLE_ARROW', 'SINGLE_ARROW', 'SINGLE_ARROW'),
        ('CIRCLE', 'CIRCLE', 'CIRCLE'),
        ('CUBE', 'CUBE', 'CUBE'),
        ('SPHERE', 'SPHERE', 'SPHERE'),
        ('ARROWS', 'ARROWS', 'ARROWS'),
        ('CONE', 'CONE', 'CONE') ],
        default='PLAIN_AXES')

# Convex_Hull
    dissolve_angle: bpy.props.FloatProperty(
        name = "Dissolve Angles",
        description = "Dissolve faces below this angle",
        default = 5,
        min = 0,
        max = 180
    )

# Decap
    decap_thickness: bpy.props.FloatProperty(
        name = "Thickness",
        description = "Relative thickness of remaining piece",
        default = 0.9,
        min = 0,
        max = 1
    )

    decap_center: bpy.props.FloatProperty(
        name = "Center",
        description = "Relative center of remaining piece",
        default = 0.5,
        min = 0,
        max = 1
    )

    decap_fill_pos : bpy.props.BoolProperty(
        name = "Fill+",
        description = "Fill with N-gon on positive side",
        default = True,
    )

    decap_fill_neg : bpy.props.BoolProperty(
        name = "Fill-",
        description = "Fill with N-gon on negative side",
        default = True,
    )

    decap_axis: bpy.props.EnumProperty(
        name="Axis",
        description="Slicing axis",
        items=[
            ('X', "X", "X"),
            ('Y', "Y", "Y"),
            ('Z', "Z", "Z"),
            ],

        default='Z')

    decap_hide_orig : bpy.props.BoolProperty(
        name = "Hide original",
        description = "Hide original out of the way",
        default = False,
    )

    decap_keep_caps : bpy.props.BoolProperty(
        name = "Keep caps",
        description = "Keep caps as sepearate objects",
        default = False,
    )

    decap_keep_caps_array : bpy.props.BoolProperty(
        name = "Array-compatible",
        description = "Adjust caps to work as array caps",
        default = False,
    )

    decap_solidify : bpy.props.BoolProperty(
        name = 'Solidify',
        description = 'Solidify 0 thickness slice to match original',
        default = False

    )

    decap_solidify_multi : bpy.props.FloatProperty(
        name = 'Solidify multiplier',
        description = 'Solidify multiplier',
        default = 1

    )


#selector
    primitive_type: bpy.props.EnumProperty(
        name="Primitive",
        description="Primitive type",
        items=[
            ('Cube', "Cube", "Cube"),
            ('Plane', "Plane", "Plane"),
            ('Cylinder', "Cylinder", "Cylinder"),
            ('Sphere', "Sphere", "Sphere"),
           # ('Monkey', "Monkey", "Monkey"),
            ('Empty', 'Empty', 'Empty'),
            ('Convex_Hull', 'Convex Hull', 'Convex Hull'),
            ('Decap', 'Decap', 'Create visual copy and decaps it'),
            ],

        default='Cube')

    def draw(self, context):
        self.layout.prop(self, 'primitive_type')
        self.layout.prop(self, 'individual')

        if self.primitive_type not in {'Convex_Hull','Decap'}:
            self.layout.prop(self, 'equalize')
            if self.equalize:
                self.layout.prop(self, 'equalize_radius')

        self.layout.prop(self, 'modified')
        self.layout.prop(self, 'scale')
        self.layout.prop(self, 'parent_shape')
        if self.parent_shape:
            self.layout.prop(self, 'parent_shape_inverse')

        if self.primitive_type not in self.no_bevel_club :
            self.layout.prop(self, 'copy_1st_bvl')

            if self.copy_1st_bvl:
                self.layout.prop(self, 'copy_1st_bvl_angle_only')

        if self.primitive_type == 'Cylinder':
            self.layout.prop(self, 'cyl_segments')
            self.layout.prop(self, 'cyl_diameter1')
            self.layout.prop(self, 'cyl_diameter2')
            self.layout.prop(self, 'alignment')

        elif self.primitive_type == 'Plane':
            self.layout.prop(self, "plane_alignment")
            self.layout.prop(self, "plane_offset")

        elif self.primitive_type == 'Sphere':
            self.layout.prop(self, "sphere_segments")
            self.layout.prop(self, "sphere_rings")
            self.layout.prop(self, "sphere_diameter")
            self.layout.prop(self, 'alignment')

        elif self.primitive_type == 'Empty':
            self.layout.prop(self, "empty_display")

        elif self.primitive_type == 'Convex_Hull':
            self.layout.prop(self, "dissolve_angle")

        elif self.primitive_type == 'Decap':
            self.layout.prop(self, "decap_axis")
            self.layout.prop(self, "decap_thickness")
            if not self.decap_thickness:
                self.layout.prop(self, 'decap_solidify')
                self.layout.prop(self, 'decap_solidify_multi')

            self.layout.prop(self, "decap_center")
            self.layout.prop(self, "decap_fill_pos")
            self.layout.prop(self, "decap_fill_neg")
            self.layout.prop(self, 'decap_hide_orig')
            self.layout.prop(self, 'decap_keep_caps')
            if self.decap_keep_caps:
                self.layout.prop(self, 'decap_keep_caps_array')




    @classmethod
    def poll(cls, context):
        return context.active_object or context.selected_objects

    def invoke (self, context, event):
        if event.shift:
            self.individual = True
        else:
            self.individual = False

        if event.ctrl:
            self.primitive_type = 'Empty'
            self.individual = True
            self.parent_shape = True
            self.parent_shape_inverse = True
            self.empty_display = 'CUBE'

        self.no_bevel_club = {'Plane', 'Empty', 'Convex_Hull', 'Decap'}

        bpy.context.view_layer.update()
        self.active_obj_name = context.active_object.name if context.active_object else ''
        self.selected = set(context.selected_objects)
        if context.active_object and context.mode =='EDIT_MESH':
            self.selected.add(context.active_object)

        if context.mode == 'EDIT_MESH':
            self.get_coords = self.get_coords_edit
            self.deselect = lambda obj: None
            self.set_active = lambda primitive : None
            self.mesh_update = lambda obj: obj.update_from_editmode()

        else:
            self.get_coords = self.get_coords_obj
            self.deselect = lambda obj: obj.select_set(False)
            self.set_active = lambda primitive :set_active(primitive)
            self.mesh_update = lambda obj: None

        self.object_params = []

        for obj in self.selected:
            self.mesh_update(obj)
            obj_data = Obj_data()
            obj_data.object_name = obj.name
            obj_data.object_matrix = obj.matrix_world.copy()

            obj_data.bounds_base = self.get_coords(context, obj)
            obj_data.bounds_final = self.get_coords(context, obj, modified=True)

            obj_data.bounds_decap_base = self.get_coords_obj(context, obj)
            obj_data.bounds_decap_final = self.get_coords_obj(context, obj, modified=True)


            if len (obj_data.bounds_base)<2 or len(obj_data.bounds_final)<2 :
                continue

            if obj.type == 'EMPTY':
                obj_data.dimensions_base = Vector((1,1,1))
                obj_data.dimensions_final = Vector((1,1,1))
            else:
                obj_data.dimensions_base =  math.dimensions(obj_data.bounds_base)
                obj_data.dimensions_final =  math.dimensions(obj_data.bounds_final)
                obj_data.dimensions_decap_base =  math.dimensions(obj_data.bounds_decap_base)
                obj_data.dimensions_decap_final =  math.dimensions(obj_data.bounds_decap_final)

            obj_data.has_data = obj.type in {'MESH', 'CURVE', 'FONT', 'SURFACE', 'META'}

            obj_data.center_base = math.coords_to_center(obj_data.bounds_base)
            obj_data.center_final = math.coords_to_center(obj_data.bounds_final)
            obj_data.center_decap_base = math.coords_to_center(obj_data.bounds_decap_base)
            obj_data.center_decap_final = math.coords_to_center(obj_data.bounds_decap_final)

            self.object_params.append(obj_data)

        if not self.object_params:
            return {'CANCELLED'}

        self.created_shapes = set()

        return self.execute(context)

    def execute(self, context):
        self.created_shapes.clear()

        if self.individual:

            for obj_data in self.object_params:
                obj = bpy.data.objects[obj_data.object_name]

                if self.modified:

                    mesh_location = obj_data.center_final
                    dimensions = obj_data.dimensions_final

                else:

                    mesh_location = obj_data.center_base
                    dimensions = obj_data.dimensions_base

                if self.primitive_type == 'Convex_Hull':
                    if not obj.data : continue

                    primitive = self.convex_hull(context, center = mesh_location , objects = [obj], scale_object = obj.matrix_world.to_scale())
                    primitive.matrix_world = matrix_transfrom (obj.matrix_world, scale= Vector ((1,1,1)) )

                    self.set_origin(primitive, obj.matrix_world @ mesh_location)

                elif self.primitive_type == 'Decap':
                    if not obj.data : continue

                    primitives = self.decap(context, center = mesh_location , objects = [obj], dimensions=dimensions, scale_object = obj.matrix_world.to_scale() ,  world=False )

                    primitive = primitives[0]

                    offset_vectors = [Vector((0,0,0,)), Vector((0,0,0,)), Vector((0,0,0,)),]

                    if self.decap_keep_caps and self.decap_keep_caps_array:

                        axis_vect = [self.decap_axis == a for a in 'XYZ']
                        elem_mult = lambda vect1, vect2 : Vector(a*b for a,b in zip(vect1, vect2))

                        array_offset = elem_mult(primitive.dimensions, axis_vect)

                        offset_vectors = [
                            Vector((0,0,0,)),
                            +array_offset,
                            -array_offset
                        ]

                    matrix = matrix_transfrom (obj.matrix_world, scale= Vector ((1,1,1)) )
                    loc = obj.matrix_world @ mesh_location
                    for prim, offset in zip (primitives, offset_vectors):
                        prim.matrix_world = matrix.copy()
                        prim.matrix_world.translation = loc + (matrix.to_quaternion() @ offset)
                        prim.data.transform(Matrix.Translation(-(matrix.inverted() @ loc)- offset) )

                        if not len(prim.data.vertices) and prim is not primitive:
                            me = prim.data
                            bpy.data.objects.remove(prim)
                            bpy.data.meshes.remove(me)
                            continue

                        self.created_shapes.add(prim)


                elif self.primitive_type == 'Empty':
                    location = obj.matrix_world @ mesh_location
                    primitive = self.add_empty(context, obj,  dimensions)
                    primitive.empty_display_size *= max (obj.matrix_world.to_scale())
                    primitive.empty_display_size *= self.scale
                    primitive.matrix_world = matrix_transfrom (obj.matrix_world, location=location, scale= Vector ((1,1,1)) )

                else:
                    primitive = self.pirmitive_add(context, obj, mesh_location, dimensions, scale_object= obj.matrix_world.to_scale())
                    primitive.matrix_world = matrix_transfrom (obj.matrix_world, scale= Vector ((1,1,1)) )
                    self.center_origin(primitive,)

                self.deselect(obj)
                self.set_active(primitive)

                self.created_shapes.add(primitive)

                if self.parent_shape:
                    if self.parent_shape_inverse:
                        set_parent(obj, primitive)
                    else:
                        set_parent (primitive, obj)

        else:

            bbox_array=[]
            bounds_attr = 'bounds'

            if self.primitive_type == 'Decap':
                bounds_attr += '_decap'

            if self.modified:
                bounds_attr += '_final'

            else:
                bounds_attr += '_base'

            for obj_data in self.object_params:
                obj = bpy.data.objects[obj_data.object_name]
                bounds = getattr(obj_data, bounds_attr)

                bbox_array.extend([obj_data.object_matrix @ vec for vec in bounds])
                self.deselect(obj)

            if len (bbox_array) <2:
                return {'CANCELLED'}

            bounds = math.coords_to_bounds(bbox_array)
            mesh_location = math.coords_to_center(bounds)
            dimensions = math.dimensions(bbox_array)

            if self.primitive_type == 'Convex_Hull':
                valid_objects = [bpy.data.objects[obj_data.object_name] for obj_data in self.object_params if obj_data.has_data ]
                if not valid_objects: return {'FINISHED'}

                primitive = self.convex_hull(context, center = mesh_location , objects = valid_objects, world=True)
                self.set_origin(primitive, mesh_location)

            elif self.primitive_type == 'Decap':
                valid_objects = [bpy.data.objects[obj_data.object_name] for obj_data in self.object_params if obj_data.has_data ]
                if not valid_objects: return {'FINISHED'}

                primitives = self.decap(context, dimensions=dimensions, center = mesh_location , objects = valid_objects, world=True)

                primitive = primitives[0]


                offset_vectors = [Vector((0,0,0,)), Vector((0,0,0,)), Vector((0,0,0,)),]

                if self.decap_keep_caps and self.decap_keep_caps_array:

                    axis_vect = [self.decap_axis == a for a in 'XYZ']
                    elem_mult = lambda vect1, vect2 : Vector(a*b for a,b in zip(vect1, vect2))

                    array_offset = elem_mult(primitive.dimensions, axis_vect)

                    offset_vectors = [
                        Vector((0,0,0,)),
                        +array_offset,
                        -array_offset
                    ]

                for prim, offset in zip (primitives, offset_vectors):
                    prim.matrix_world = Matrix()
                    prim.matrix_world.translation = mesh_location + offset
                    prim.data.transform(Matrix.Translation(- mesh_location - offset) )

                    if not len(prim.data.vertices) and prim is not primitive:
                        me = prim.data
                        bpy.data.objects.remove(prim)
                        bpy.data.meshes.remove(me)
                        continue

                    self.created_shapes.add(prim)

            elif self.primitive_type == 'Empty':
                primitive = self.add_empty(context, obj, dimensions)
                primitive.empty_display_size *= self.scale
                primitive.matrix_world = matrix_transfrom ( Matrix(), location=mesh_location, scale= Vector ((1,1,1)) )

            else:
                primitive = self.pirmitive_add(context, obj,  mesh_location, dimensions)
                self.center_origin(primitive)

            if self.parent_shape:
                if self.parent_shape_inverse:
                    for obj_data in self.object_params:
                        obj = bpy.data.objects[obj_data.object_name]
                        set_parent(obj, primitive)
                elif self.active_obj_name:
                    set_parent (primitive, bpy.data.objects[self.active_obj_name])

            self.set_active(primitive)
            self.created_shapes.add(primitive)

        override = context_copy(context)
        override['edit_object'] = None
        override['selected_objects'] = list(self.created_shapes)
        override['mode'] = 'OBJECT'
        operator_override(context, bpy.ops.hops.draw_wire_mesh_launcher, override, 'INVOKE_DEFAULT', target='SELECTED')

        return {'FINISHED'}



    def pirmitive_add (self, context, object, vector, dimensions, scale_object = Vector((1,1,1)),  ) :
        primitive = self.primitive_type
        primitive_mesh = bpy.data.meshes.new(primitive)
        primitive_obj = bpy.data.objects.new(primitive, primitive_mesh)
        col = collections.find_collection(context, object)
        col.objects.link(primitive_obj)
        bm = bmesh.new()

        fit_matrix  = math.get_sca_matrix(scale_object) @ Matrix.Translation(vector) @ math.get_sca_matrix(dimensions)

        scale_center = Vector((0,0,0))

        max_vec = fit_matrix @ Vector((0.5,0.5,0.5))
        min_vec = fit_matrix @ Vector((-0.5,-0.5,-0.5))

        final_dimesnions = math.dimensions(  (min_vec, max_vec) )
        final_dim_max = axle = max(final_dimesnions)

        if primitive == 'Cube':
            bmesh.ops.create_cube(bm)

        elif primitive == 'Cylinder':
            bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=self.cyl_segments, radius1=self.cyl_diameter1/2, radius2=self.cyl_diameter2/2, depth =1)

        elif primitive == 'Monkey':
            bmesh.ops.create_monkey(bm, matrix = math.get_sca_matrix([0.5, 0.5 ,0.5]))

        elif primitive == 'Plane':
           bm = self.plane_mesh ()
           bm.faces.ensure_lookup_table()
           scale_center = bm.faces[0].calc_center_median()


        elif primitive == 'Sphere':
            bmesh.ops.create_uvsphere (bm, u_segments = self.sphere_segments, v_segments = self.sphere_rings, radius = self.sphere_diameter/2 )


        if primitive in {'Cylinder', 'Sphere'}:
            XYZ = 'XYZ'

            if self.alignment == 'AUTO_OBJECT':

                index = list(final_dimesnions).index(axle)

                alignment = XYZ[index]

            elif self.alignment == 'AUTO_MESH':

                index = list(dimensions).index(max(dimensions))

                alignment = XYZ[index]

            else:
                alignment = self.alignment
                index = XYZ.index(self.alignment)

            if alignment == 'X':
                eul = Euler((0.0, radians(90.0), 0.0), XYZ)
            elif alignment == 'Y':
                eul = Euler((radians(-90.0), 0.0, 0.0), XYZ)
            elif alignment == 'Z':
                eul = Euler((0.0, 0.0, 0.0), XYZ)

            axle = final_dimesnions[index]

            bmesh.ops.transform(bm, matrix = math.get_rot_matrix(eul.to_quaternion()), verts = bm.verts)

        bmesh.ops.transform(bm, matrix = fit_matrix , verts = bm.verts)

        scale_vector = Vector((1,1,1))

        if self.equalize:

            if self.equalize_radius:

                dims = list(final_dimesnions)
                dims.remove(axle)
                max_dim = max(dims)

            else:

                axle = max_dim = final_dim_max

            for i in range(3):
                if final_dimesnions[i] == axle:
                    continue
                scale_vector[i] = max_dim/final_dimesnions[i] if final_dimesnions[i] else final_dimesnions[i]

        scale_vector*=self.scale

        bmesh.ops.scale(bm, vec = scale_vector, verts = bm.verts, space = Matrix.Translation(-(fit_matrix @ scale_center)) )

        if self.copy_1st_bvl and primitive not in self.no_bevel_club:
            if self.individual:
                source = object
            else:
                source = bpy.data.objects[self.active_obj_name] if self.active_obj_name else None

            if source:
                bevels = [mod for mod in source.modifiers if mod.type =='BEVEL']
                if bevels:
                    source_bvl = bevels[0]

                    if self.copy_1st_bvl_angle_only:
                        angles = [bvl for bvl in bevels if bvl.limit_method =='ANGLE']
                        if angles:
                            source_bvl = angles[0]
                        else:
                            source_bvl = None

                    if source_bvl:

                        stored_source = modifier.stored(source_bvl)

                        modifier.new(primitive_obj, name=source_bvl.name, mod = stored_source)

                        del stored_source

                        dest_bvl = primitive_obj.modifiers[0]

                        if dest_bvl.limit_method not in {'NONE', 'ANGLE'}:
                            dest_bvl.limit_method = 'ANGLE'
                            dest_bvl.angle_limit = radians(30)
                        if addon.preference().behavior.auto_smooth:
                            primitive_mesh.use_auto_smooth = True
                            primitive_mesh.auto_smooth_angle = getattr(object.data, 'auto_smooth_angle', radians(30))
                        for face in bm.faces:
                            face.smooth = True

        bm.to_mesh(primitive_mesh)
        bm. free()
        return primitive_obj

    def convex_hull(self, context, center = Vector((0, 0, 0)) , objects = [], scale_object = Vector((1,1,1)), world = False):
        primitive = self.primitive_type
        primitive_mesh = bpy.data.meshes.new(primitive)
        primitive_obj = bpy.data.objects.new(primitive, primitive_mesh)
        col = collections.find_collection(context, objects[0])
        col.objects.link(primitive_obj)
        bm = bmesh.new()

        if self.modified:
            for obj in objects:
                self.mesh_update(obj)

                smooth_store =  getattr(obj.data, 'use_auto_smooth', False)

                if smooth_store : obj.data.use_auto_smooth = False

                depsgraph = context.evaluated_depsgraph_get()
                eval_obj = obj.evaluated_get(depsgraph)

                temp_mesh = eval_obj.to_mesh()

                if smooth_store : obj.data.use_auto_smooth = smooth_store
                primitive_mesh.use_auto_smooth = smooth_store
                primitive_mesh.auto_smooth_angle = temp_mesh.auto_smooth_angle

                matrix = obj.matrix_world if world else Matrix()
                temp_mesh.transform(matrix)

                bm.from_mesh(temp_mesh)
                obj.to_mesh_clear()

        else:
            for obj in objects:
                self.mesh_update(obj)

                smooth_store =  getattr(obj.data, 'use_auto_smooth', False)
                if smooth_store : obj.data.use_auto_smooth = False

                temp_mesh = obj.to_mesh()

                if smooth_store : obj.data.use_auto_smooth = smooth_store
                primitive_mesh.use_auto_smooth = smooth_store
                primitive_mesh.auto_smooth_angle = temp_mesh.auto_smooth_angle

                matrix = obj.matrix_world if world else Matrix()
                temp_mesh.transform(matrix)

                bm.from_mesh(temp_mesh)
                obj.to_mesh_clear()


        if context.mode != 'OBJECT':
            verts = [v for v in bm.verts if not v.select]
            bmesh.ops.delete(bm, geom = verts, context = 'VERTS')

        ret= bmesh.ops.convex_hull(bm, input =bm.verts, use_existing_faces = True)

        filter = set(ret['geom'])

        del_verts = [v for v in bm.verts if v not in filter]

        bmesh.ops.delete(bm, geom = del_verts, context = 'VERTS')

        bmesh.ops.dissolve_limit(bm, angle_limit =radians(self.dissolve_angle) , use_dissolve_boundaries = False, verts = bm.verts , edges = bm.edges)

        fit_matrix = math.get_sca_matrix(scale_object)

        bmesh.ops.transform(bm, matrix = fit_matrix, verts = bm.verts)

        scale = Vector((self.scale,self.scale,self.scale))
        bmesh.ops.scale(bm, vec = scale , verts = bm.verts, space = Matrix.Translation(-(fit_matrix @ center)) )

        bm.to_mesh(primitive_mesh)
        bm.free()
        return primitive_obj

    def decap(self, context, objects = [], dimensions= Vector((1, 1, 1)) ,  center = Vector((0, 0, 0)), scale_object = Vector((1,1,1)), world = False):

        source = bmesh.new()

        smooth = False
        smooth_angle = radians(30)

        if self.modified:
            for obj in objects:
                self.mesh_update(obj)

                smooth_store =  getattr(obj.data, 'use_auto_smooth', False)
                if smooth_store : obj.data.use_auto_smooth = False

                depsgraph = context.evaluated_depsgraph_get()
                eval_obj = obj.evaluated_get(depsgraph)
                temp_mesh = eval_obj.to_mesh()

                if smooth_store : obj.data.use_auto_smooth = smooth_store
                smooth = smooth_store
                smooth_angle = temp_mesh.auto_smooth_angle

                matrix = obj.matrix_world if world else Matrix()
                temp_mesh.transform(matrix)

                source.from_mesh(temp_mesh)
                obj.to_mesh_clear()
                obj.hide_set(self.decap_hide_orig and context.mode == 'OBJECT')

        else:

            for obj in objects:
                self.mesh_update(obj)

                smooth_store =  getattr(obj.data, 'use_auto_smooth', False)
                if smooth_store : obj.data.use_auto_smooth = False

                temp_mesh = obj.to_mesh()

                if smooth_store : obj.data.use_auto_smooth = smooth_store
                smooth = smooth_store
                smooth_angle = temp_mesh.auto_smooth_angle

                matrix = obj.matrix_world if world else Matrix()
                temp_mesh.transform(matrix)

                source.from_mesh(temp_mesh)
                obj.to_mesh_clear()

                obj.hide_set(self.decap_hide_orig and context.mode == 'OBJECT')

        bms = []


        bm_main = source.copy()
        bms.append ( (bm_main, '') )
        slicer(bm_main, dimensions=dimensions, center=center , axis = self.decap_axis,
                slice_thick=self.decap_thickness, cut_offset=self.decap_center,
                fill_neg=self.decap_fill_neg, fill_pos=self.decap_fill_pos)

        if self.decap_keep_caps:

            neg_thick = (self.decap_center - self.decap_thickness/2)*2
            pos_thick = (1 - (self.decap_center + self.decap_thickness/2))*2

            bm_pos = source.copy()

            slicer(bm_pos, dimensions=dimensions, center=center , axis = self.decap_axis,
                    slice_thick=pos_thick, cut_offset= 1,
                    fill_neg=self.decap_fill_pos, fill_pos=False)

            if bm_pos.verts:
                bms.append( (bm_pos, '_pos') )
            else:
                bm_pos.free()
                bms.append( (bmesh.new(), '_pos') )

            bm_neg = source.copy()

            slicer(bm_neg, dimensions=dimensions, center=center , axis = self.decap_axis,
                    slice_thick=neg_thick, cut_offset= 0,
                    fill_neg=False, fill_pos=self.decap_fill_neg)

            if bm_neg.verts:
                bms.append( (bm_neg, '_neg') )
            else:
                bm_neg.free()
                bms.append((bmesh.new(), '_neg' ))


        scale = Vector((self.scale,self.scale,self.scale))
        fit_matrix = math.get_sca_matrix(scale_object)

        if self.decap_solidify and not self.decap_thickness and bms[0][0].faces:
            bm = bms[0][0]
            index = 'XYZ'.index(self.decap_axis)
            axis_vector = Vector([self.decap_axis == v for v in 'XYZ'])

            elem_multi = lambda vect1, vect2 : Vector([a*b for a,b in zip(vect1, vect2)])

            offset = elem_multi(dimensions, axis_vector) * self.decap_center * self.decap_solidify_multi

            bmesh.ops.transform(bm, verts = bm.verts  ,matrix = matrix.Translation(-offset))

            for face in bm.faces:
                face.normal = axis_vector

            bmesh.ops.solidify(bm, geom = bm.faces, thickness= -dimensions[index]* self.decap_solidify_multi )


        for bm, _ in bms:

            bmesh.ops.transform(bm, matrix = fit_matrix, verts = bm.verts)
            bmesh.ops.scale(bm, vec = scale , verts = bm.verts, space = Matrix.Translation(-(fit_matrix @ center)) )


        primitives = []
        for bm, suffix in bms:
            primitive = self.primitive_type + suffix
            primitive_mesh = bpy.data.meshes.new(primitive)
            primitive_obj = bpy.data.objects.new(primitive, primitive_mesh)
            col = collections.find_collection(context, objects[0])
            col.objects.link(primitive_obj)
            primitive_obj.select_set(True)

            primitive_mesh.use_auto_smooth = smooth
            primitive_mesh.auto_smooth_angle = smooth_angle

            bm.to_mesh(primitive_mesh)
            bm.free()

            primitives.append(primitive_obj)

        source.free()

        return primitives


    def get_coords_obj(self, context, obj, matrix = Matrix(), modified = False):
        if modified:
            bb = [matrix @ Vector(v) for v in obj.bound_box]

        else:

            tmp = bpy.data.objects.new("Bounding Box", obj.data)
            bb = [matrix @ Vector (v) for v in tmp.bound_box]
            bpy.data.objects.remove(tmp)

        return bb

    def get_coords_edit (self, context, obj, matrix = Matrix(), modified = False ):

        coords = []
        if modified:
            depsgraph = context.evaluated_depsgraph_get()
            obj_eval = obj.evaluated_get(depsgraph)
            data_eval = obj_eval.to_mesh()
            coords = [matrix @ v.co for v in data_eval.vertices if v.select]
            obj_eval.to_mesh_clear()
        if not coords :
            bm = bmesh.from_edit_mesh(obj.data)
            coords = [matrix @ v.co for v in bm.verts if v.select]

        return coords


    def set_origin (self, obj, center):
        obj.data.transform(Matrix.Translation( -(obj.matrix_world.inverted() @ center)))
        obj.matrix_world = matrix_transfrom (obj.matrix_world, location= center)

    def center_origin(self, obj, center = None) :

        center = object.center(obj) if not center else center
        obj.data.transform(Matrix.Translation(-center))
        obj.matrix_world = matrix_transfrom (obj.matrix_world, location=obj.matrix_world @ center)


    def plane_mesh (self):
        bm = bmesh.new()
        bmesh.ops.create_cube(bm)
        if self.plane_alignment == '+X':
            verts = [v for v in bm.verts if v.co[0]==-0.5]
        elif self.plane_alignment == '+Y':
            verts = [v for v in bm.verts if v.co[1]==-0.5]
        elif self.plane_alignment == '+Z':
            verts = [v for v in bm.verts if v.co[2]==-0.5]
        elif self.plane_alignment == '-X':
            verts = [v for v in bm.verts if v.co[0]==0.5]
        elif self.plane_alignment == '-Y':
            verts = [v for v in bm.verts if v.co[1]==0.5]
        elif self.plane_alignment == '-Z':
            verts = [v for v in bm.verts if v.co[2]==0.5]

        bmesh.ops.delete(bm, geom = verts, context = 'VERTS')

        offset = self.plane_offset
        if self.plane_alignment in {'-X', '-Y', '-Z'}:
            offset*= -1
        if self.plane_alignment in {'+X', '-X'}:
            bmesh.ops.transform(bm, matrix = Matrix.Translation(Vector((offset,0,0))), verts = bm.verts)
        elif self.plane_alignment in {'+Y', '-Y'}:
            bmesh.ops.transform(bm, matrix = Matrix.Translation(Vector((0,offset,0))), verts = bm.verts)
        elif self.plane_alignment in {'+Z', '-Z'}:
            bmesh.ops.transform(bm, matrix = Matrix.Translation(Vector((0,0,offset))), verts = bm.verts)

        return bm

    def add_empty(self, context, object, dimensions):
        primitive = self.primitive_type
        primitive_obj = bpy.data.objects.new(primitive, None)
        col = collections.find_collection(context, object)
        col.objects.link(primitive_obj)
        primitive_obj.empty_display_type = self.empty_display
        primitive_obj.empty_display_size = max (dimensions)*0.6


        return primitive_obj

def set_parent (chlid, parent):
    buffer = chlid.matrix_world.copy()
    chlid.parent = parent
    chlid.matrix_parent_inverse = parent.matrix_world.inverted()
    chlid.matrix_world = buffer

def matrix_transfrom (matrix, location = None, rotation = None, scale = None):
    loc, rot, sca = matrix.decompose()
    loc = location if location else loc
    rot = rotation if rotation else rot
    sca = scale if scale else sca

    mat_loc = Matrix.Translation(loc)
    mat_rot = rot.to_matrix().to_4x4()
    mat_sca = math.get_sca_matrix (sca)

    return mat_loc @ mat_rot @  mat_sca

def apply_scale_matrix(obj):
    obj.data.transform(math.get_sca_matrix(obj.scale))
    obj.matrix_world = matrix_transfrom(obj.matrix_world, scale= Vector((1,1,1,)) )

def set_active(obj):
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def slicer(bm, dimensions = Vector((1,1,1,)), center = Vector((0,0,0,)) ,  axis = 'Z', slice_thick = 0.1, cut_offset = 0.5, fill_neg = True, fill_pos = True ):
    slice_thick /=2

    index = 'XYZ'.index(axis)

    dimension = dimensions[index]

    normal = Vector( [axis == s for s in 'XYZ'] )

    offset_unit = normal*dimension

    bottom = center -(offset_unit/2)

    positive_slice = bottom + (offset_unit * slice_thick) + (offset_unit * cut_offset)

    negative_slice = bottom - (offset_unit * slice_thick) + (offset_unit * cut_offset)

    if slice_thick:

        positive_cut = bmesh.ops.bisect_plane(bm, geom = bm.verts[:]+ bm.edges[:] + bm.faces[:] ,
            dist = 0, plane_co =positive_slice , plane_no = normal,
            use_snap_center= False, clear_outer = True, clear_inner= False)

        if fill_pos:
            positive_edges = [e for e in positive_cut['geom_cut'] if isinstance(e, bmesh.types.BMEdge)]
            ret =  bmesh.ops.holes_fill(bm, edges = positive_edges)


        negative_cut = bmesh.ops.bisect_plane(bm, geom = bm.verts[:]+ bm.edges[:] + bm.faces[:] ,
            dist = 0, plane_co =negative_slice , plane_no = normal,
            use_snap_center= False, clear_outer = False, clear_inner= True)

        if fill_neg:
            negative_edges = [e for e in negative_cut['geom_cut'] if isinstance(e, bmesh.types.BMEdge)]
            bmesh.ops.holes_fill(bm, edges = negative_edges)

    else:
        plane_co = (positive_slice + negative_slice)/2

        normal_signed = normal *-1 if plane_co[index]>0.5 else normal

        center_cut = bmesh.ops.bisect_plane(bm, geom = bm.verts[:]+ bm.edges[:] + bm.faces[:] ,
            dist = 0, plane_co = plane_co, plane_no = normal_signed,
            use_snap_center= False, clear_outer = True, clear_inner= True)
        bmesh.ops.remove_doubles(bm, verts = bm.verts, dist = 0.0001)

        if fill_neg or fill_pos:
            bmesh.ops.holes_fill(bm, edges = bm.edges)

class Obj_data():
    def __init__(self):
        self.object_name = None
        self.object_matrix = None
        self.has_data = False
        self.dimensions_base = None
        self.bounds_base = None
        self.dimensions_final = None
        self.bounds_final = None
        self.center_base = None
        self.center_final = None
