import bpy
import bmesh
import enum
from math import radians, copysign, sqrt
from ... utility import addon, collections, object, math , modifier, operator_override, method_handler, context_copy
# from ... utils.blender_ui import get_dpi_factor
# from ... utils.context import ExecutionContext
from bpy.props import EnumProperty, FloatProperty, BoolProperty
from mathutils import Vector, Matrix, Euler

from ... ui_framework.master import Master
from ... ui_framework.utils.mods_list import get_mods_list
from ... utility.base_modal_controls import Base_Modal_Controls

# Cursor Warp imports
from ... utils.toggle_view3d_panels import collapse_3D_view_panels
from ... utils.modal_frame_drawing import draw_modal_frame
from ... utils.cursor_warp import mouse_warp

class Mouse_states(enum.Enum):
    none = enum.auto()
    scale = enum.auto()
    decap_adjsut = enum.auto()
    decap_solidify = enum.auto()
    hull_dissolve = enum.auto()
    shape_offset = enum.auto()
    cyl_diameter = enum.auto()
    alignment = enum.auto()

class Scroll_states(enum.Enum):
    none = enum.auto()
    cyl_segments = enum.auto()
    sphere_adjust = enum.auto()
    quad_sphere_adjust = enum.auto()

def selector_update(self, context):
    operator = HOPS_OT_Conv_To_Shape_1_5.operator
    if not operator: return

    operator.mouse_state = operator.mouse_def_states[operator.primitive_type]
    operator.scroll_state = operator.scroll_def_states[operator.primitive_type]
    operator.create_shape(context)


DESC = """To_Shape 1.5 \n
Convert selection to a myriad of shapes including empties.
Interactive version of the classic operator
"""


class HOPS_OT_Conv_To_Shape_1_5(bpy.types.Operator):
    bl_idname = "hops.to_shape_1_5"
    bl_label = "To_Shape 1.5"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = DESC

    operator = None
    individual: bpy.props.BoolProperty(
        name="Individual",
        description="Create shape per object using its local space",
        default = False)

    equalize_mode_items=[
        ('OFF', "OFF", "OFF"),
        ('ALL', "ALL", "ALL"),
        ('RADIUS', "RADIUS", "RADIUS"),
    ]

    equalize_mode: bpy.props.EnumProperty(
        name="Equalize mode",
        description="How shape is equalzied",
        items=equalize_mode_items,
        default='OFF')

    modified: bpy.props.BoolProperty(
        name="Modified",
        description="Take the bounding box dimensions from the modified object",
        default=True)

    alignment_items=[
        # ('AUTO_OBJECT', "AUTO_OBJECT", "Allign along longest object dimension"),
        # ('AUTO_MESH', "AUTO_MESH", "Allign along longest mesh dimension"),
        ('X', "X", "Allign along X axis"),
        ('Y', "Y", "Allign along Y axis"),
        ('Z', "Z", "Allign along Z axis"),
    ]

    alignment: bpy.props.EnumProperty(
        name="Alignment",
        description="What axis to allign along",
        items=alignment_items,
        default='Z')

    scale: bpy.props.FloatProperty(
        name="Scale",
        description="Scale",
        default=1,
        min = 0,
        precision = 3)

    copy_1st_bvl_items =[
        ('OFF', "OFF", "OFF"),
        ('ON', "ON", "OB"),
        ('ANGLE', "ANGLE", "ANGLE"),
    ]

    copy_1st_bvl: bpy.props.EnumProperty(
        name="Copy 1st bevel",
        description="Copy bevel",
        items=copy_1st_bvl_items,
        default='OFF')

    parent_mode_items=[
        ('OFF', "OFF", "No parenting"),
        ('ON', "ON", "Parent shape to source"),
        ('INVERSE', "INVERSE", "Parent soure to shape"),
    ]

    parent_mode: bpy.props.EnumProperty(
        name="Parent mode",
        description="Parenting",
        items=parent_mode_items,
        default='OFF')

    shape_offset_axis_items=[
        ('CENTER', "CENTER", "No offset"),
        ('+X', "+X", "Offset into +X direction"),
        ('+Y', "+Y", "Offset into +Y direction"),
        ('+Z', "+Z", "Offset into +Z direction"),
        ('-X', "-X", "Offset into -X direction"),
        ('-Y', "-Y", "Offset into -Y direction"),
        ('-Z', "-Z", "Offset into -Z direction"),
        ('ORIGIN', "ORIGIN", "Offset to origin")
    ]

    shape_offset_axis: bpy.props.EnumProperty(
        name="Shape offset",
        description="Relative unit offset",
        items=shape_offset_axis_items,
        default='CENTER')

    shape_offset: bpy.props.FloatProperty(
        name="Offset",
        description="Offset plane from selection",
        default=0)

    shade_wire: bpy.props.BoolProperty(
        name = 'Shade Wire',
        description = 'Shade Wirefame and disable in render',
        default = False)

    active_only: bpy.props.BoolProperty(
        name = 'Active Only',
        description = 'Only use active object',
        default = False)

    ##cylinder
    cyl_segments_default = 32
    cyl_segments: bpy.props.IntProperty(
        name="Segments",
        description="Number of segments",
        default=cyl_segments_default,
        min=3)

    cyl_diameter1_default = 1
    cyl_diameter1: bpy.props.FloatProperty(
        name="Diameter 1",
        description="Diameter 1",
        default=cyl_diameter1_default)

    cyl_diameter2_default = 1
    cyl_diameter2: bpy.props.FloatProperty(
        name="Diameter 2",
        description="Diameter 2",
        default=cyl_diameter2_default)

    ##sphere
    sphere_segments_default = 32
    sphere_segments: bpy.props.IntProperty(
        name="Segments",
        description="Nmber of segments",
        default=sphere_segments_default,
        min=3)

    sphere_rings_default = 16
    sphere_rings: bpy.props.IntProperty(
        name="Rings",
        description="Number of rings",
        default=sphere_rings_default,
        min=3)

    sphere_diameter_default = 1
    sphere_diameter: bpy.props.FloatProperty(
        name="Diameter",
        description="Diameter",
        default=sphere_diameter_default)

    ##quad sphere
    quad_sphere_divisions_default = 5
    quad_sphere_divisions: bpy.props.IntProperty(
        name="Divisions",
        description="Nmber of divisions",
        default=quad_sphere_divisions_default,
        min=1)

    ##plane

    plane_alignment_items=[
        ('X', "X", "Aaling on X axis"),
        ('Y', "Y", "Aaling on Y axis"),
        ('Z', "Z", "Aaling on Z axis")
    ]

    plane_alignment: bpy.props.EnumProperty(
        name="Plane axis",
        description="What side to create planeo on",
        items=plane_alignment_items,
        default='Z')

    # empty

    empty_display_items=[
        ('PLAIN_AXES', 'PLAIN_AXES', 'PLAIN_AXES'),
        ('SINGLE_ARROW', 'SINGLE_ARROW', 'SINGLE_ARROW'),
        ('CIRCLE', 'CIRCLE', 'CIRCLE'),
        ('CUBE', 'CUBE', 'CUBE'),
        ('SPHERE', 'SPHERE', 'SPHERE'),
        ('ARROWS', 'ARROWS', 'ARROWS'),
        ('CONE', 'CONE', 'CONE')
    ]

    empty_display: bpy.props.EnumProperty(
        name="Display type",
        description="Empty display type",
        items=empty_display_items,
        default='PLAIN_AXES')

    # Convex_Hull
    dissolve_angle_default = 5
    dissolve_angle: bpy.props.FloatProperty(
        name = "Dissolve Angles",
        description = "Dissolve faces below this angle",
        default = dissolve_angle_default,
        min = 0,
        max = 180,
        precision = 1
    )

    # Decap
    decap_thickness_default = 0.9
    decap_thickness: bpy.props.FloatProperty(
        name = "Thickness",
        description = "Relative thickness of remaining piece",
        default = decap_thickness_default,
        min = 0,
        max = 1
    )

    decap_center_default = 0.5
    decap_center: bpy.props.FloatProperty(
        name = "Center",
        description = "Relative center of remaining piece",
        default = decap_center_default,
        min = 0,
        max = 1
    )

    decap_fill_mode_items=[
        ('NO', "NO", "NO"),
        ('POS', "POS", "POS"),
        ('NEG', "NEG", "NEG"),
        ('BOTH', "BOTH", "BOTH"),
    ]

    decap_fill_mode: bpy.props.EnumProperty(
        name="Fill mode",
        description="Fill mode",
        items=decap_fill_mode_items,
        default='NO')

    decap_axis_items=[
        ('X', "X", "X"),
        ('Y', "Y", "Y"),
        ('Z', "Z", "Z"),
    ]

    decap_axis: bpy.props.EnumProperty(
        name="Axis",
        description="Slicing axis",
        items=decap_axis_items,
        default='Z')


    display_original : bpy.props.BoolProperty(
        name = "Display original",
        description = "Dispaly original object",
        default = True,
    )

    decap_cap_type_items=[
        ('NO', "NO", "No Caps"),
        ('ARRAY', "ARRAY", "Array-compatible"),
        ('DEFAULT', "DEFAULT", "Default"),
    ]

    decap_cap_type : bpy.props.EnumProperty(
        name="Cap types",
        description="Cap type",
        items=decap_cap_type_items,
        default='NO')

    decap_keep_caps_array : bpy.props.BoolProperty(
        name = "Array-compatible",
        description = "Adjust caps to work as array caps",
        default = False,
    )

    decap_solidify_default = False
    decap_solidify : bpy.props.BoolProperty(
        name = 'Solidify',
        description = 'Solidify 0 thickness slice to match original',
        default = decap_solidify_default
    )

    decap_solidify_multi_default = 1
    decap_solidify_multi : bpy.props.FloatProperty(
        name = 'Solidify multiplier',
        description = 'Solidify multiplier',
        default = decap_solidify_multi_default

    )

    #Curve

    curve_type_items=[
        ('BEZIER', 'BEZIER', 'BEZIER'),
        ('NURBS', 'NURBS', 'NURBS'),
    ]

    curve_type: bpy.props.EnumProperty(
        name='Type',
        description='Spline type',
        items=curve_type_items,
        default='BEZIER',
    )

    curve_axis_items=[
        ('X', "X", "X"),
        ('Y', "Y", "Y"),
        ('Z', "Z", "Z"),
    ]
    curve_axis: bpy.props.EnumProperty(
        name='Axis',
        description='Axis',
        items=curve_axis_items,
        default='Z'
    )


    #selector

    primitive_type_items=[
        ('Cube', "Cube", "Cube"),
        ('Plane', "Plane", "Plane"),
        ('Cylinder', "Cylinder", "Cylinder"),
        ('Sphere', "Sphere", "Sphere"),
        ('Quad_Sphere', "Quad Sphere", "Quad Sphere"),
        # ('Monkey', "Monkey", "Monkey"),
        ('Empty', 'Empty', 'Empty'),
        ('Convex_Hull', 'Convex Hull', 'Convex Hull'),
        ('Decap', 'Decap', 'Create visual copy and decaps it'),
        ('Curve', "Curve", "Curve"),
        ]

    primitive_type: bpy.props.EnumProperty(
        name="Primitive",
        description="Primitive type",
        items=primitive_type_items,
        default='Cube',
        update = selector_update)


    @classmethod
    def poll(cls, context):
        return context.active_object or context.selected_objects


    def draw(self, context):
        self.layout.prop(self, 'primitive_type')
        self.layout.prop(self, 'individual')

        if self.primitive_type not in {'Convex_Hull','Decap'}:
            self.layout.prop(self, 'equalize_mode')

        self.layout.prop(self, 'modified')
        self.layout.prop(self, 'scale')
        self.layout.prop(self, 'parent_mode')
        self.layout.prop(self, 'shape_offset_axis')
        self.layout.prop(self, 'shape_offset')
        self.layout.prop(self, 'active_only')
        self.layout.prop(self, 'shade_wire')

        if context.mode == 'OBJECT':
            self.layout.prop(self, 'display_original')

        if self.primitive_type not in self.no_bevel_club :
            self.layout.prop(self, 'copy_1st_bvl')

        if self.primitive_type == 'Cylinder':
            self.layout.prop(self, 'cyl_segments')
            self.layout.prop(self, 'cyl_diameter1')
            self.layout.prop(self, 'cyl_diameter2')
            self.layout.prop(self, 'alignment')

        elif self.primitive_type == 'Plane':
            self.layout.prop(self, "plane_alignment")

        elif self.primitive_type == 'Sphere':
            self.layout.prop(self, "sphere_segments")
            self.layout.prop(self, "sphere_rings")
            self.layout.prop(self, "sphere_diameter")
            self.layout.prop(self, 'alignment')

        elif self.primitive_type == 'Quad_Sphere':
            self.layout.prop(self, "quad_sphere_divisions")

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
            self.layout.prop(self, "decap_fill_mode")
            self.layout.prop(self, 'decap_cap_type')

        elif self.primitive_type == 'Curve':
            self.layout.prop(self, 'curve_type')
            self.layout.prop(self, 'curve_axis')

    def invoke (self, context, event):
        # if event.shift:
        #     self.individual = True
        # else:
        #     self.individual = False

        # if event.ctrl:
        #     self.primitive_type = 'Empty'
        #     self.individual = True
        #     self.parent_shape = True
        #     self.parent_shape_inverse = True
        #     self.empty_display = 'CUBE'

        if bmesh.ops.create_cone.__doc__.count("radius"):
            def create_cylinder(bm):
                bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=self.cyl_segments, radius1=self.cyl_diameter1/2, radius2=self.cyl_diameter2/2, depth=1)
        else:
            def create_cylinder(bm):
                bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=self.cyl_segments, diameter1=self.cyl_diameter1/2, diameter2=self.cyl_diameter2/2, depth=1)

        if bmesh.ops.create_uvsphere.__doc__.count("radius"):
            def create_uvsphere(bm):
                bmesh.ops.create_uvsphere (bm, u_segments = self.sphere_segments, v_segments = self.sphere_rings, radius = self.sphere_diameter/2 )
        else:
            def create_uvsphere(bm):
                bmesh.ops.create_uvsphere (bm, u_segments = self.sphere_segments, v_segments = self.sphere_rings, diameter = self.sphere_diameter/2 )

        self.create_cylinder = create_cylinder
        self.create_uvsphere = create_uvsphere

        self.mouse_def_states = {
            'Cube' : Mouse_states.none,
            'Plane' : Mouse_states.alignment,
            'Cylinder' : Mouse_states.alignment,
            'Sphere' : Mouse_states.alignment,
            'Quad_Sphere' : Mouse_states.none,
            'Empty' : Mouse_states.none,
            'Convex_Hull' : Mouse_states.none,
            'Decap' : Mouse_states.decap_adjsut,
            'Curve' : Mouse_states.alignment
        }

        self.scroll_def_states = {
            'Cube' : Scroll_states.none,
            'Plane' : Scroll_states.none,
            'Cylinder' : Scroll_states.none,
            'Sphere' : Scroll_states.none,
            'Quad_Sphere' : Scroll_states.none,
            'Empty' : Scroll_states.none,
            'Convex_Hull' : Scroll_states.none,
            'Decap' : Scroll_states.none,
            'Curve' : Scroll_states.none,
        }

        self.offset_map = {
            'CENTER' : Vector((0, 0, 0)),
            '+X'     : Vector((1, 0, 0)),
            '+Y'     : Vector((0, 1, 0)),
            '+Z'     : Vector((0, 0, 1)),
            '-X'     : Vector((-1, 0, 0)),
            '-Y'     : Vector((0, -1, 0)),
            '-Z'     : Vector((0, 0, -1)),
            'ORIGIN' : Vector((0, 0, 0)),
        }

        self.segment_presets = {
            "ONE" : 8,
            "TWO" : 12,
            "THREE" : 24,
            "FOUR" : 32,
            "FIVE" : 64,
            "SIX" : 128,
        }

        for val, i in enumerate(list(self.segment_presets.values()), 1):
            self.segment_presets[F'NUMPAD_{i}'] = val

        self.no_bevel_club = {'Plane', 'Empty', 'Convex_Hull', 'Decap', 'Curve'}
        self.mouse_state = self.mouse_def_states[self.primitive_type]
        self.scroll_state = self.scroll_def_states[self.primitive_type]
        self.last_decap_thick = self.decap_thickness
        self.mouse_buffer = 0
        self.mouse_threshold = 0.15
        self.active_only = False
        self.flair = False
        self.running = False

        self.notify = lambda val: bpy.ops.hops.display_notification(info=val) if addon.preference().ui.Hops_extra_info else lambda val: None
        self.elem_multi = lambda vect1, vect2 : Vector([a*b for a,b in zip(vect1, vect2)])

        bpy.context.view_layer.update()
        self.active_obj_name = context.active_object.name if context.active_object else ''

        # XXX : ST3
        self.selected = set(context.selected_objects)
        # self.selected = set([obj for obj in context.selected_objects if obj.name in context.view_layer.objects])

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

        self.object_params_select = []
        self.object_params_active = []

        for obj in self.selected:
            self.mesh_update(obj)
            obj_data = Obj_data()
            obj_data.object_name = obj.name
            obj_data.object_matrix = obj.matrix_world.copy()
            obj_data.parent_name = obj.parent.name if obj.parent else ''
            obj_data.matrix_parent_inverse = obj.matrix_parent_inverse.copy()
            obj_data.hide = obj.hide_get()

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

            obj_data.convex_valid = True
            if obj.type == 'MESH':
                if obj.mode == 'EDIT':
                    bm = bmesh.from_edit_mesh(obj.data)
                    obj_data.convex_valid = len([isinstance(elem, bmesh.types.BMVert) for elem in bm.select_history]) > 2

                else:
                    obj_data.convex_valid = len(obj.data.vertices) > 2

            obj_data.center_base = math.coords_to_center(obj_data.bounds_base)
            obj_data.center_final = math.coords_to_center(obj_data.bounds_final)
            obj_data.center_decap_base = math.coords_to_center(obj_data.bounds_decap_base)
            obj_data.center_decap_final = math.coords_to_center(obj_data.bounds_decap_final)

            self.object_params_select.append(obj_data)

            if obj == context.active_object:
                self.object_params_active.append(obj_data)

            if not self.display_original and context.mode == 'OBJECT':
                obj.hide_set(True)

        if not self.object_params_select:
            return {'CANCELLED'}

        self.created_shapes = set()
        self.deletable = set()
        self.hide_shapes = set()
        self.enable_mods = set()
        self.create_shape(context)
        self.notify(F'Shape: {self.primitive_type}')

        # Base Systems
        self.master = Master(context)
        self.master.only_use_fast_ui = True
        self.base_controls = Base_Modal_Controls(context, event, popover_keys=['TAB', 'SPACE'])
        self.original_tool_shelf, self.original_n_panel = collapse_3D_view_panels()
        self.draw_handle = bpy.types.SpaceView3D.draw_handler_add(self.safe_draw_shader, (context,), 'WINDOW', 'POST_PIXEL')

        self.__class__.operator = self
        context.window_manager.modal_handler_add(self)
        self.running = True

        return {'RUNNING_MODAL'}

    def modal(self, context, event):

        # Base Systems
        self.master.receive_event(event=event)
        self.base_controls.update(context, event)
        mouse_warp(context, event)

        if self.base_controls.pass_through:
            return {'PASS_THROUGH'}

        elif self.base_controls.popover:
            context.window_manager.popover(popup_draw)

        elif self.base_controls.mouse:
            if self.mouse_state == Mouse_states.scale:
                self.scale += self.base_controls.mouse

            elif self.mouse_state == Mouse_states.decap_adjsut:
                if event.ctrl:
                    self.decap_center += self.base_controls.mouse
                else:
                    self.decap_thickness += self.base_controls.mouse

            elif self.mouse_state == Mouse_states.decap_solidify:
                if event.ctrl:
                    self.decap_center += self.base_controls.mouse
                else:
                    self.decap_solidify_multi += self.base_controls.mouse

            elif self.mouse_state == Mouse_states.hull_dissolve:
                self.dissolve_angle += self.base_controls.mouse*10

            elif self.mouse_state == Mouse_states.shape_offset:
                self.shape_offset += self.base_controls.mouse

            elif self.mouse_state == Mouse_states.cyl_diameter:

                if event.ctrl and not event.alt:
                    self.cyl_diameter1 += self.base_controls.mouse

                elif event.alt and not event.ctrl:
                    self.cyl_diameter2 += self.base_controls.mouse

                else:
                    self.cyl_diameter1 += self.base_controls.mouse
                    self.cyl_diameter2 = self.cyl_diameter1

            elif self.mouse_state == Mouse_states.alignment:
                self.mouse_buffer += self.base_controls.mouse

                if abs(self.mouse_buffer) >= self.mouse_threshold:

                    if self.primitive_type == 'Plane':
                        prop_name = 'plane_alignment'

                    elif self.primitive_type in {'Cylinder', 'Sphere'}:
                        prop_name = 'alignment'

                    elif self.primitive_type  == 'Curve':
                        prop_name = 'curve_axis'

                    setattr(self, prop_name, self.enum_scroll(prop_name, value= int(copysign(1, self.mouse_buffer)) ) )

                    self.mouse_buffer = 0
                    self.create_shape(context)

            if self.mouse_state not in {Mouse_states.none, Mouse_states.alignment}:
                self.create_shape(context, flair=False)

        elif self.base_controls.scroll:
            if self.scroll_state == Scroll_states.none:
                if event.shift:
                    prop_name = ''
                    message = ''

                    if self.primitive_type == 'Plane':
                        prop_name = 'plane_alignment'
                        message = 'Axis:'

                    elif self.primitive_type in {'Cylinder', 'Sphere'}:
                        prop_name = 'alignment'
                        message = 'Alignment:'

                    elif self.primitive_type == 'Empty':
                        prop_name = 'empty_display'
                        message = 'Display:'

                    elif self.primitive_type == 'Decap':
                        prop_name = 'decap_axis'
                        message = 'Axis:'

                    if prop_name:
                        setattr(self, prop_name, self.enum_scroll(prop_name, value=self.base_controls.scroll))
                        self.create_shape(context)
                        self.notify(F'{message} {getattr(self, prop_name)}')

                elif event.ctrl:

                    self.shape_offset_axis  = self.enum_scroll('shape_offset_axis', value=self.base_controls.scroll)
                    self.create_shape(context, flair=False)
                    self.notify(F'Shape offset: {self.shape_offset_axis}')

                else:

                    self.primitive_type = self.enum_scroll('primitive_type', value=self.base_controls.scroll)

                    self.notify(F'Shape: {self.primitive_type}')

            elif self.scroll_state == Scroll_states.cyl_segments:
                self.cyl_segments += self.base_controls.scroll
                self.create_shape(context, flair=False)

            elif self.scroll_state == Scroll_states.sphere_adjust:

                if event.shift:
                    self.sphere_rings += self.base_controls.scroll
                else:
                    self.sphere_segments += self.base_controls.scroll

                self.create_shape(context, flair= False)

            elif self.scroll_state == Scroll_states.quad_sphere_adjust:
                self.quad_sphere_divisions += self.base_controls.scroll
                self.create_shape(context, flair= False)

        elif self.base_controls.confirm:
            self.running = False
            self.flair = True
            self.remove_shader()
            collapse_3D_view_panels(self.original_tool_shelf, self.original_n_panel)
            self.master.run_fade()

            self.__class__.operator = None

            for obj in  self.hide_shapes:
                obj.hide_set(True)

            for mod in self.enable_mods:
                mod.show_viewport =  True

            override = context_copy(context)
            override['edit_object'] = None
            override['selected_objects'] = list(self.created_shapes)
            override['mode'] = 'OBJECT'

            operator_override(context, bpy.ops.hops.draw_wire_mesh_launcher, override, 'INVOKE_DEFAULT', target='SELECTED')

            self.remove_deletables()

            self.created_shapes.clear()
            self.hide_shapes.clear()
            self.enable_mods.clear()
            self.deletable.clear()

            return {'FINISHED'}

        elif self.base_controls.cancel:
            self.running = False
            self.remove_shader()
            collapse_3D_view_panels(self.original_tool_shelf, self.original_n_panel)
            self.master.run_fade()

            self.__class__.operator = None

            self.purge_shapes()
            self.remove_deletables()

            if self.active_obj_name:
                context.view_layer.objects.active = bpy.data.objects[self.active_obj_name]

            for obj_data in self.object_params_select:
                obj = bpy.data.objects[obj_data.object_name]
                obj.parent = bpy.data.objects[obj_data.parent_name] if obj_data.parent_name else None
                obj.matrix_parent_inverse = obj_data.matrix_parent_inverse
                obj.matrix_world = obj_data.object_matrix
                obj.hide_set(obj_data.hide)
                obj.select_set(True)

            if self.active_obj_name:
                context.view_layer.objects.active = bpy.data.objects[self.active_obj_name]

            self.object_params_select.clear()
            self.object_params_active.clear()
            self.created_shapes.clear()
            self.hide_shapes.clear()
            self.enable_mods.clear()
            self.deletable.clear()

            return {'CANCELLED'}

        elif event.type == 'A' and event.value == 'PRESS':

            current_mouse_state = self.mouse_state
            current_scroll_state = self.scroll_state
            message = ''

            if self.primitive_type == 'Cylinder':
                if self.mouse_state == Mouse_states.cyl_diameter:

                    self.mouse_state = self.mouse_def_states[self.primitive_type]
                    self.scroll_state = self.scroll_def_states[self.primitive_type]
                else:
                    self.scroll_state = Scroll_states.cyl_segments
                    self.mouse_state = Mouse_states.cyl_diameter
                    message = 'Adjusting Cylinder'

            elif self.primitive_type == 'Sphere':
                self.scroll_state = Scroll_states.sphere_adjust if self.scroll_state != Scroll_states.sphere_adjust else Scroll_states.none
                message = 'Adjusting Sphere'

            elif self.primitive_type == 'Quad_Sphere':
                self.scroll_state = Scroll_states.quad_sphere_adjust if self.scroll_state != Scroll_states.quad_sphere_adjust else Scroll_states.none
                message = 'Adjusting Quad Sphere'

            elif self.primitive_type == 'Convex_Hull':
                self.mouse_state = Mouse_states.hull_dissolve if self.mouse_state != Mouse_states.hull_dissolve else Mouse_states.none
                message ='Adjusting Dissolve Angle'

            # elif self.primitive_type == 'Plane':
            #     self.mouse_state = Mouse_states.plane_offset if self.mouse_state != Mouse_states.plane_offset else Mouse_states.none
            #     message = 'Adjusting Offset'

            if self.mouse_state == self.mouse_def_states[self.primitive_type] and self.scroll_state == self.scroll_def_states[self.primitive_type]:
                message = 'Adjusment: OFF'

            if self.mouse_state == current_mouse_state and self.scroll_state == current_scroll_state:
                message = ''

            if message:
                self.notify(message)

        elif event.type == 'B' and event.value == 'PRESS':
            if self.primitive_type not in self.no_bevel_club:
                self.copy_1st_bvl = self.enum_scroll('copy_1st_bvl')
                self.create_shape(context)

                self.notify(F'Copy 1st bevel: {self.copy_1st_bvl}')

        elif event.type == 'C' and event.value == 'PRESS':
            if self.primitive_type == 'Decap':
                self.decap_cap_type = self.enum_scroll('decap_cap_type')
                self.create_shape(context)

                self.notify(F'Cap Type: {self.decap_cap_type}')

            elif self.primitive_type == 'Curve':
                self.curve_type = self.enum_scroll('curve_type')
                self.create_shape(context)

                self.notify(f'Curve Type: {self.curve_type}')

        elif event.type == 'D' and event.value == 'PRESS':
            if context.mode == 'OBJECT':
                self.display_original = not self.display_original

                for obj_data in self.object_params_select:
                    bpy.data.objects[obj_data.object_name].hide_set(not self.display_original)

                self.notify(F'Display Original: {self.display_original}')

        elif event.type == 'E' and event.value == 'PRESS':
            if self.primitive_type not in {'Convex_Hull','Decap'}:
                self.equalize_mode = self.enum_scroll('equalize_mode')
                self.create_shape(context)
                self.notify(F'Equalize: {self.equalize_mode}')

        elif event.type == 'F' and event.value == 'PRESS':
            if self.primitive_type == 'Decap':
                self.decap_fill_mode = self.enum_scroll('decap_fill_mode')
                self.create_shape(context)

                self.notify(F'Fill mode: {self.decap_fill_mode}')

        elif event.type == 'G' and event.value == 'PRESS':
            if event.ctrl:
                self.mouse_state = self.mouse_def_states[self.primitive_type]
                self.shape_offset = 0
                self.create_shape(context)
                self.notify('Offset reset')

            else:

                if self.mouse_state != Mouse_states.shape_offset:
                    self.mouse_state = Mouse_states.shape_offset
                    self.notify('Offset Adjust: ON')
                else:
                    self.mouse_state = self.mouse_def_states[self.primitive_type]
                    self.notify('Offset Adjust: OFF')

                    if self.primitive_type == 'Cylinder' and self.scroll_state == Scroll_states.cyl_segments:
                        self.mouse_state = Mouse_states.cyl_diameter

        elif event.type == 'I' and event.value == 'PRESS':
            self.individual = not self.individual
            self.create_shape(context)
            self.notify(F'Mode: {"Individual" if self.individual else "Combined"} ')

        elif event.type == 'P' and event.value == 'PRESS':
            self.parent_mode = self.enum_scroll('parent_mode')

            for obj_data in self.object_params_select:
                obj = bpy.data.objects[obj_data.object_name]
                obj.parent = bpy.data.objects[obj_data.parent_name] if obj_data.parent_name else None
                obj.matrix_parent_inverse = obj_data.matrix_parent_inverse
                obj.matrix_world = obj_data.object_matrix

            self.create_shape(context, flair = False)

            self.notify(F'Parenting: {self.parent_mode}')

        elif event.type == 'R' and event.value == 'PRESS':
            # if self.primitive_type == 'Plane':
            #     self.plane_offset = annotations['plane_offset'][1]['default']

            if self.primitive_type == 'Cylinder':
                self.cyl_segments = self.cyl_segments_default
                self.cyl_diameter1 = self.cyl_diameter1_default
                self.cyl_diameter2 = self.cyl_diameter2_default

            elif self.primitive_type == 'Sphere':
                self.sphere_segments = self.sphere_segments_default
                self.sphere_rings = self.sphere_rings_default

            elif self.primitive_type == 'Quad_Sphere':
                self.quad_sphere_divisions = self.quad_sphere_divisions_default

            elif self.primitive_type == 'Convex_Hull':
                self.dissolve_angle = self.dissolve_angle_default

            elif self.primitive_type == 'Decap':
                self.decap_thickness = self.decap_thickness_default
                self.decap_center = self.decap_center_default
                self.decap_solidify = self.decap_solidify_default
                self.decap_solidify_multi = self.decap_solidify_multi_default

            self.mouse_state = self.mouse_def_states[self.primitive_type]
            self.scroll_state = self.scroll_def_states[self.primitive_type]

            self.create_shape(context)

            self.notify(F'Reset {self.primitive_type} adjustments')


        elif event.type == 'S' and event.value == 'PRESS':

            if event.ctrl:
                self.mouse_state = self.mouse_def_states[self.primitive_type]
                self.scale = 1
                self.create_shape(context)
                self.notify('Scale reset')

            else:

                if self.mouse_state != Mouse_states.scale:
                    self.mouse_state = Mouse_states.scale
                    self.notify('Scale Adjust: ON')
                else:
                    self.mouse_state = self.mouse_def_states[self.primitive_type]
                    self.notify('Scale Adjust: OFF')

                    if self.primitive_type == 'Cylinder' and self.scroll_state == Scroll_states.cyl_segments:
                        self.mouse_state = Mouse_states.cyl_diameter

        elif event.type == 'T' and event.value == 'PRESS':
            if self.primitive_type == 'Decap':
                if self.decap_solidify:
                    self.decap_solidify = False
                    self.mouse_state = self.mouse_def_states[self.primitive_type]
                    self.decap_thickness = self.last_decap_thick

                    self.notify('ZERO Thickness: OFF')
                else:
                    self.decap_solidify = True
                    self.last_decap_thick = self.decap_thickness
                    self.decap_thickness = 0
                    self.decap_cap_type = 'NO'
                    self.decap_fill_mode = 'POS'
                    self.mouse_state = Mouse_states.decap_solidify

                    self.notify('ZERO Thickness: ON')

                self.create_shape(context)


        elif event.type == 'W' and event.value == 'PRESS':
            if event.shift:
                self.shade_wire = not self.shade_wire
                self.create_shape(context)
                self.notify(f'Shade {"Wire" if self.shade_wire else "Solid" }')

            else:
                self.modified = not self.modified
                self.create_shape(context)
                self.notify(F'Modified: {self.modified}')

        elif event.type == 'X' and event.value == 'PRESS':
            prop_name = ''
            message = ''

            if self.primitive_type == 'Plane':
                prop_name = 'plane_alignment'
                message = 'Axis:'

            elif self.primitive_type in {'Cylinder', 'Sphere'}:
                prop_name = 'alignment'
                message = 'Alignment:'

            elif self.primitive_type == 'Empty':
                prop_name = 'empty_display'
                message = 'Display:'

            elif self.primitive_type == 'Decap':
                prop_name = 'decap_axis'
                message = 'Axis:'

            if prop_name:
                setattr(self, prop_name, self.enum_scroll(prop_name))
                self.create_shape(context)
                self.notify(F'{message} {getattr(self, prop_name)}')

        elif event.type == 'Y' and event.value == 'PRESS':
            if self.object_params_active:
                self.active_only = not self.active_only

            self.notify (F'Active Only: {self.active_only}')
            self.create_shape(context)

        elif  event.type in self.segment_presets and event.value == 'PRESS':
            if self.primitive_type == 'Cylinder':
                preset = self.segment_presets[event.type]
                self.cyl_segments = preset
                self.notify(f'Segments: {self.cyl_segments}')
                self.create_shape(context)

            elif self.primitive_type == 'Sphere':
                preset = self.segment_presets[ event.type ]
                self.sphere_segments = preset
                self.sphere_rings = int(preset/2)
                self.notify(F'Segments: {self.sphere_segments}. Rings: {self.sphere_rings}')
                self.create_shape(context)

        self.draw_ui(context)
        context.area.tag_redraw()

        return {'RUNNING_MODAL'}

    def create_shape(self, context, flair=True):
        self.flair = flair

        self.purge_shapes()
        self.execute(context)

    def execute (self, context):
        self.created_shapes.clear()
        self.hide_shapes.clear()
        self.enable_mods.clear()

        object_params = self.object_params_active if self.active_only else self.object_params_select

        if self.individual:

            for obj_data in object_params:
                obj = bpy.data.objects[obj_data.object_name]

                if self.modified:

                    mesh_location = obj_data.center_final
                    dimensions = obj_data.dimensions_final

                else:

                    mesh_location = obj_data.center_base
                    dimensions = obj_data.dimensions_base

                obj_scale = obj.matrix_world.to_scale()
                dimensions_world = self.elem_multi(dimensions, obj_scale)

                if self.primitive_type == 'Decap':
                    if not obj.data : continue

                    if self.modified:

                        mesh_location = obj_data.center_decap_final
                        dimensions = obj_data.dimensions_decap_final

                    else:

                        mesh_location = obj_data.center_decap_base
                        dimensions = obj_data.dimensions_decap_base

                    primitives = self.decap(context, center = mesh_location , objects = [obj], dimensions=dimensions, scale_object = obj_scale ,  world=False )

                    primitive = primitives[0]

                    offset_vectors = [Vector((0,0,0,)), Vector((0,0,0,)), Vector((0,0,0,)),]

                    if self.decap_cap_type == 'ARRAY':

                        axis_vect = [self.decap_axis == a for a in 'XYZ']

                        array_offset = self.elem_multi(primitive.dimensions, axis_vect)

                        offset_vectors = [
                            Vector((0,0,0,)),
                            +array_offset,
                            -array_offset
                        ]

                        mod = primitive.modifiers.new(name='Array', type ='ARRAY')
                        mod.count = 1
                        mod.use_merge_vertices = True
                        mod.use_relative_offset = True
                        mod.use_constant_offset = False
                        mod.use_object_offset = False
                        mod.relative_offset_displace = axis_vect
                        mod.end_cap = primitives[1]
                        mod.start_cap = primitives[2]
                        mod.show_viewport = False

                        self.hide_shapes.add(primitives[1])
                        self.hide_shapes.add(primitives[2])
                        self.enable_mods.add(mod)

                    matrix = matrix_transfrom (obj.matrix_world, scale= Vector ((1,1,1)) )
                    quat = matrix.to_quaternion()
                    origin = obj.matrix_world @ mesh_location
                    origin_offset = quat @ self.elem_multi(primitive.dimensions/2, -self.offset_map[self.shape_offset_axis])

                    for prim, cap_offset in zip (primitives, offset_vectors):
                        prim.matrix_world = matrix.copy()
                        self.set_origin(prim, origin + quat @ cap_offset + origin_offset)

                        prim.matrix_world.translation += quat @ self.elem_multi(dimensions_world/2, self.offset_map[self.shape_offset_axis]) - origin_offset
                        prim.matrix_world.translation += quat @ self.offset_map[self.shape_offset_axis] * self.shape_offset

                        if not len(prim.data.vertices) and prim is not primitive:
                            me = prim.data
                            bpy.data.objects.remove(prim)
                            bpy.data.meshes.remove(me)
                            self.hide_shapes.discard(prim)
                            continue

                        self.created_shapes.add(prim)

                    if self.shape_offset_axis == 'ORIGIN':
                        primitive.matrix_world.translation += obj_data.object_matrix.translation - primitive.matrix_world.translation

                elif self.primitive_type == 'Empty':
                    location = obj.matrix_world @ mesh_location
                    primitive = self.add_empty(context, obj,  dimensions)
                    primitive.empty_display_size *= max (obj_scale)
                    primitive.empty_display_size *= self.scale
                    primitive.matrix_world = matrix_transfrom (obj.matrix_world, location=location, scale= Vector ((1,1,1)) )

                    quat = primitive.matrix_world.to_quaternion()

                    primitive.matrix_world.translation += quat @ self.elem_multi(dimensions_world/2, self.offset_map[self.shape_offset_axis])
                    primitive.matrix_world.translation += quat @ self.offset_map[self.shape_offset_axis] * self.shape_offset

                else:
                    if self.primitive_type == 'Convex_Hull':
                        if not obj_data.has_data or not obj_data.convex_valid: continue

                        primitive = self.convex_hull(context, center = mesh_location , objects = [obj], scale_object = obj_scale)
                        primitive_dimensions = primitive.dimensions

                    elif self.primitive_type == 'Curve':
                        primitive, primitive_dimensions = self.add_curve(context, obj, mesh_location, dimensions, obj_scale)

                    else:
                        primitive = self.pirmitive_add(context, obj, mesh_location, dimensions, scale_object= obj_scale)
                        primitive_dimensions = primitive.dimensions

                    primitive.matrix_world = matrix_transfrom(obj.matrix_world, scale=Vector ((1,1,1)) )

                    quat = primitive.matrix_world.to_quaternion()
                    origin = obj.matrix_world @ mesh_location
                    origin_offset = quat @ self.elem_multi(primitive_dimensions/2, -self.offset_map[self.shape_offset_axis])

                    if self.primitive_type == 'Plane' and self.plane_alignment == self.shape_offset_axis[1]:
                        origin_offset = Vector((0,0,0))

                    self.set_origin(primitive, origin + origin_offset)

                    primitive.matrix_world.translation += quat @ self.elem_multi(dimensions_world/2, self.offset_map[self.shape_offset_axis]) - origin_offset
                    primitive.matrix_world.translation += quat @ self.offset_map[self.shape_offset_axis] * self.shape_offset

                self.deselect(obj)
                self.set_active(primitive)

                self.created_shapes.add(primitive)

                if self.shape_offset_axis == 'ORIGIN' and self.primitive_type != 'Decap':
                    primitive.matrix_world.translation = obj_data.object_matrix.translation


                if self.shade_wire:
                    primitive.display_type = 'WIRE'
                    primitive.hide_render = True

                if self.parent_mode == 'ON':
                    set_parent (primitive, obj)

                elif self.parent_mode == 'INVERSE':
                    if self.active_only:
                        for obj_data in self.object_params_select:
                            set_parent(bpy.data.objects[obj_data.object_name], primitive)
                    else:
                        set_parent(obj, primitive)

        else:

            bbox_array=[]
            bounds_attr = 'bounds'

            if self.primitive_type == 'Decap':
                bounds_attr += '_decap'

            if self.modified:
                bounds_attr += '_final'

            else:
                bounds_attr += '_base'

            for obj_data in object_params:
                obj = bpy.data.objects[obj_data.object_name]
                bounds = getattr(obj_data, bounds_attr)

                bbox_array.extend([obj_data.object_matrix @ vec for vec in bounds])
                self.deselect(obj)

            if len (bbox_array) <2:
                return {'FINISHED'}

            bounds = math.coords_to_bounds(bbox_array)
            mesh_location = math.coords_to_center(bounds)
            dimensions = math.dimensions(bbox_array)

            if self.primitive_type == 'Decap':
                valid_objects = [bpy.data.objects[obj_data.object_name] for obj_data in object_params if obj_data.has_data]

                if not valid_objects:
                    return {'FINISHED'}

                primitives = self.decap(context, dimensions=dimensions, center = mesh_location , objects = valid_objects, world=True)

                primitive = primitives[0]

                offset_vectors = [Vector((0,0,0,)), Vector((0,0,0,)), Vector((0,0,0,)),]

                if self.decap_cap_type == 'ARRAY':

                    axis_vect = [self.decap_axis == a for a in 'XYZ']

                    array_offset = self.elem_multi(primitive.dimensions, axis_vect)

                    offset_vectors = [
                        Vector((0,0,0,)),
                        +array_offset,
                        -array_offset
                    ]

                    mod = primitive.modifiers.new(name='Array', type ='ARRAY')
                    mod.count = 1
                    mod.use_merge_vertices = True
                    mod.use_relative_offset = True
                    mod.use_constant_offset = False
                    mod.use_object_offset = False
                    mod.relative_offset_displace = axis_vect
                    mod.end_cap = primitives[1]
                    mod.start_cap = primitives[2]
                    mod.show_viewport = False

                    self.hide_shapes.add(primitives[1])
                    self.hide_shapes.add(primitives[2])
                    self.enable_mods.add(mod)

                origin_offset = self.elem_multi(primitive.dimensions/2, -self.offset_map[self.shape_offset_axis])

                for prim, cap_offset in zip (primitives, offset_vectors):
                    prim.matrix_world = Matrix()

                    self.set_origin(prim, mesh_location + cap_offset + origin_offset)

                    prim.matrix_world.translation += self.elem_multi(dimensions/2, self.offset_map[self.shape_offset_axis]) - origin_offset

                    prim.matrix_world.translation += self.offset_map[self.shape_offset_axis] * self.shape_offset

                    if not len(prim.data.vertices) and prim is not primitive:
                        me = prim.data
                        bpy.data.objects.remove(prim)
                        bpy.data.meshes.remove(me)
                        self.hide_shapes.discard(prim)
                        continue

                    self.created_shapes.add(prim)

                if self.shape_offset_axis == 'ORIGIN':
                    loc = sum([obj_data.object_matrix.translation for obj_data in object_params], Vector()) / len(object_params)
                    for p in primitives: p.matrix_world.translation += loc - p.matrix_world.translation

            elif self.primitive_type == 'Empty':
                primitive = self.add_empty(context, obj, dimensions)
                primitive.empty_display_size *= self.scale
                primitive.matrix_world = matrix_transfrom (Matrix(), location=mesh_location, scale= Vector ((1,1,1)) )

                primitive.matrix_world.translation += self.elem_multi(dimensions/2, self.offset_map[self.shape_offset_axis])
                primitive.matrix_world.translation += self.offset_map[self.shape_offset_axis] * self.shape_offset

            else:

                if self.primitive_type == 'Convex_Hull':
                    valid_objects = [bpy.data.objects[obj_data.object_name] for obj_data in object_params if obj_data.has_data and obj_data.convex_valid]

                    if not valid_objects:
                        return {'FINISHED'}

                    primitive = self.convex_hull(context, center = mesh_location , objects = valid_objects, world=True)
                    primitive_dimensions = primitive.dimensions

                elif self.primitive_type == 'Curve':
                    primitive, primitive_dimensions = self.add_curve(context, obj, mesh_location, dimensions)

                else:
                    primitive = self.pirmitive_add(context, obj,  mesh_location, dimensions)
                    primitive_dimensions = primitive.dimensions

                origin_offset = self.elem_multi(primitive_dimensions/2, -self.offset_map[self.shape_offset_axis])

                if self.primitive_type == 'Plane' and self.plane_alignment == self.shape_offset_axis[1]:
                    origin_offset = Vector((0,0,0))

                self.set_origin(primitive, mesh_location + origin_offset)

                primitive.matrix_world.translation += self.elem_multi(dimensions/2, self.offset_map[self.shape_offset_axis]) - origin_offset
                primitive.matrix_world.translation += self.offset_map[self.shape_offset_axis] * self.shape_offset

            self.created_shapes.add(primitive)

            if self.shape_offset_axis == 'ORIGIN' and self.primitive_type != 'Decap':
                loc = sum([obj_data.object_matrix.translation for obj_data in object_params], Vector()) / len(object_params)
                primitive.matrix_world.translation = loc


            if self.parent_mode == 'ON':
                if self.active_obj_name:
                    set_parent (primitive, bpy.data.objects[self.active_obj_name])

            elif self.parent_mode == 'INVERSE':

                if self.active_only:
                    for obj_data in self.object_params_select:
                        set_parent(bpy.data.objects[obj_data.object_name], primitive)
                else:
                    for obj_data in object_params:
                        obj = bpy.data.objects[obj_data.object_name]
                        set_parent(obj, primitive)

            self.set_active(primitive)

            if self.shade_wire:
                primitive.display_type = 'WIRE'
                primitive.hide_render = True

        if self.flair:
            override = context_copy(context)
            override['edit_object'] = None
            override['selected_objects'] = list(self.created_shapes)
            override['mode'] = 'OBJECT'

            operator_override(context, bpy.ops.hops.draw_wire_mesh_launcher, override,'INVOKE_DEFAULT', target='SELECTED')

        if not self.running:
            if context.mode == 'OBJECT':
                for obj_data in self.object_params_select:
                    bpy.data.objects[obj_data.object_name].hide_set(not self.display_original)

        return {'FINISHED'}


    def pirmitive_add (self, context, object, vector, dimensions, scale_object = Vector((1,1,1))) :
        primitive = self.primitive_type
        primitive_mesh = bpy.data.meshes.new(primitive)
        primitive_obj = bpy.data.objects.new(primitive, primitive_mesh)
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
            self.create_cylinder(bm)

        elif primitive == 'Monkey':
            bmesh.ops.create_monkey(bm, matrix = math.get_sca_matrix([0.5, 0.5 ,0.5]))

        elif primitive == 'Plane':
           bm = self.plane_mesh ()
           bm.faces.ensure_lookup_table()
           scale_center = bm.faces[0].calc_center_median()

        elif primitive == 'Sphere':
            self.create_uvsphere(bm)

        elif primitive == 'Quad_Sphere':
            bmesh.ops.create_cube(bm, size=2.0)
            bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=self.quad_sphere_divisions, use_grid_fill=True)

            for v in bm.verts:
                x = v.co.x * sqrt(1 - (v.co.y * v.co.y / 2 ) - ( v.co.z * v.co.z / 2 ) + ( (v.co.y * v.co.y * v.co.z * v.co.z ) / 3 ) ) * 0.5
                y = v.co.y * sqrt(1 - (v.co.z * v.co.z / 2 ) - ( v.co.x * v.co.x / 2 ) + ( (v.co.z * v.co.z * v.co.x * v.co.x ) / 3 ) ) * 0.5
                z = v.co.z * sqrt(1 - (v.co.x * v.co.x / 2 ) - ( v.co.y * v.co.y / 2 ) + ( (v.co.x * v.co.x * v.co.y * v.co.y ) / 3 ) ) * 0.5

                v.co.x = x
                v.co.y = y
                v.co.z = z


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

        if self.equalize_mode != 'OFF':

            if self.equalize_mode == 'RADIUS':

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

        if self.copy_1st_bvl != 'OFF' and primitive not in self.no_bevel_club:
            if self.individual:
                source = object
            else:
                source = bpy.data.objects[self.active_obj_name] if self.active_obj_name else None

            if source:
                bevels = [mod for mod in source.modifiers if mod.type =='BEVEL']
                if bevels:
                    source_bvl = bevels[0]

                    if self.copy_1st_bvl == 'ANGLE':
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
                        primitive_mesh.use_auto_smooth = True
                        primitive_mesh.auto_smooth_angle = getattr(object.data, 'auto_smooth_angle', radians(30))
                        for face in bm.faces:
                            face.smooth = True

        bm.to_mesh(primitive_mesh)
        bm. free()

        col = collections.find_collection(context, object, must_be_in_view_layer=True)
        col.objects.link(primitive_obj)
        return primitive_obj

    def convex_hull(self, context, center = Vector((0, 0, 0)) , objects = [], scale_object = Vector((1,1,1)), world = False):
        primitive = self.primitive_type
        primitive_mesh = bpy.data.meshes.new(primitive)
        primitive_obj = bpy.data.objects.new(primitive, primitive_mesh)
        bm = bmesh.new()

        if self.modified:
            for obj in objects:
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

        col = collections.find_collection(context, objects[0], must_be_in_view_layer=True)
        col.objects.link(primitive_obj)
        return primitive_obj

    def decap(self, context, objects = [], dimensions= Vector((1, 1, 1)) ,  center = Vector((0, 0, 0)), scale_object = Vector((1,1,1)), world = False):

        source = bmesh.new()

        smooth = False
        smooth_angle = radians(30)

        if self.modified:
            for obj in objects:
                #self.mesh_update(obj)

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
                #obj.hide_set(self.decap_hide_orig and context.mode == 'OBJECT')

        else:

            for obj in objects:
                #self.mesh_update(obj)

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

                #obj.hide_set(self.decap_hide_orig and context.mode == 'OBJECT')

        bms = []


        bm_main = source.copy()
        bms.append ( (bm_main, '') )

        decap_fill_neg = self.decap_fill_mode in {'NEG', 'BOTH'}
        decap_fill_pos = self.decap_fill_mode in {'POS', 'BOTH'}

        slicer(bm_main, dimensions=dimensions, center=center , axis = self.decap_axis,
                slice_thick=self.decap_thickness, cut_offset=self.decap_center,
                fill_neg=decap_fill_neg, fill_pos=decap_fill_pos)

        if self.decap_cap_type != 'NO':

            neg_thick = (self.decap_center - self.decap_thickness/2)*2
            pos_thick = (1 - (self.decap_center + self.decap_thickness/2))*2

            bm_pos = source.copy()

            slicer(bm_pos, dimensions=dimensions, center=center , axis = self.decap_axis,
                    slice_thick=pos_thick, cut_offset= 1,
                    fill_neg=decap_fill_pos, fill_pos=False)

            if bm_pos.verts:
                bms.append( (bm_pos, '_pos') )
            else:
                bm_pos.free()
                bms.append( (bmesh.new(), '_pos') )

            bm_neg = source.copy()

            slicer(bm_neg, dimensions=dimensions, center=center , axis = self.decap_axis,
                    slice_thick=neg_thick, cut_offset= 0,
                    fill_neg=False, fill_pos=decap_fill_neg)

            if bm_neg.verts:
                bms.append( (bm_neg, '_neg') )
            else:
                bm_neg.free()
                bms.append((bmesh.new(), '_neg' ))


        scale = Vector((self.scale, self.scale, self.scale))
        fit_matrix = math.get_sca_matrix(scale_object)

        if self.decap_solidify and not self.decap_thickness and bms[0][0].faces:
            bm = bms[0][0]
            index = 'XYZ'.index(self.decap_axis)
            axis_vector = Vector([self.decap_axis == v for v in 'XYZ'])

            offset = self.elem_multi(dimensions, axis_vector) * self.decap_center * self.decap_solidify_multi

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

            primitive_mesh.use_auto_smooth = smooth
            primitive_mesh.auto_smooth_angle = smooth_angle

            bm.to_mesh(primitive_mesh)
            bm.free()

            col = collections.find_collection(context, objects[0], must_be_in_view_layer=True)
            col.objects.link(primitive_obj)
            primitive_obj.select_set(True)

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
        # bmesh.ops.create_cube(bm)
        # if self.plane_alignment == '+X':
        #     verts = [v for v in bm.verts if v.co[0]==-0.5]
        # elif self.plane_alignment == '+Y':
        #     verts = [v for v in bm.verts if v.co[1]==-0.5]
        # elif self.plane_alignment == '+Z':
        #     verts = [v for v in bm.verts if v.co[2]==-0.5]
        # elif self.plane_alignment == '-X':
        #     verts = [v for v in bm.verts if v.co[0]==0.5]
        # elif self.plane_alignment == '-Y':
        #     verts = [v for v in bm.verts if v.co[1]==0.5]
        # elif self.plane_alignment == '-Z':
        #     verts = [v for v in bm.verts if v.co[2]==0.5]

        # bmesh.ops.delete(bm, geom = verts, context = 'VERTS')

        # offset = self.plane_offset
        # if self.plane_alignment in {'-X', '-Y', '-Z'}:
        #     offset*= -1
        # if self.plane_alignment in {'+X', '-X'}:
        #     bmesh.ops.transform(bm, matrix = Matrix.Translation(Vector((offset,0,0))), verts = bm.verts)
        # elif self.plane_alignment in {'+Y', '-Y'}:
        #     bmesh.ops.transform(bm, matrix = Matrix.Translation(Vector((0,offset,0))), verts = bm.verts)
        # elif self.plane_alignment in {'+Z', '-Z'}:
        #     bmesh.ops.transform(bm, matrix = Matrix.Translation(Vector((0,0,offset))), verts = bm.verts)

        alignment = self.plane_alignment
        XYZ = 'XYZ'
        if alignment == 'X':
            eul = Euler((0.0, radians(90.0), 0.0), XYZ)
        elif alignment == 'Y':
            eul = Euler((radians(-90.0), 0.0, 0.0), XYZ)
        elif alignment == 'Z':
            eul = Euler((0.0, 0.0, 0.0), XYZ)

        bmesh.ops.create_grid(bm, x_segments =1, y_segments = 1, matrix = eul.to_matrix().to_4x4(), size = 0.5)

        return bm

    def add_empty(self, context, object, dimensions):
        primitive = self.primitive_type
        primitive_obj = bpy.data.objects.new(primitive, None)
        col = collections.find_collection(context, object, must_be_in_view_layer=True)
        col.objects.link(primitive_obj)
        primitive_obj.empty_display_type = self.empty_display
        primitive_obj.empty_display_size = max (dimensions)*0.6

        return primitive_obj

    def add_curve(self, context, object, center, dimensions, scale = Vector((1, 1, 1))):
        primitive = self.primitive_type
        primitive_data = bpy.data.curves.new(primitive, 'CURVE')
        primitive_obj = bpy.data.objects.new(primitive, primitive_data)
        primitive_obj.show_in_front = True
        col = collections.find_collection(context, object, must_be_in_view_layer=True)
        col.objects.link(primitive_obj)
        primitive_data.dimensions = '3D'

        center  = self.elem_multi(scale, center)
        dimensions = self.elem_multi(dimensions, scale) * self.scale
        index = 'XYZ'.index(self.curve_axis)

        for i in range(3):
            if i == index: continue
            dimensions[i] = 0

        _max = dimensions / 2
        points = (-_max, _max)
        count = 2

        primitive_data.splines.clear()
        spline = primitive_data.splines.new(self.curve_type)
        spline.use_endpoint_u = True

        if self.curve_type == 'BEZIER':
            spline.bezier_points.add(count - 1)
            handle_offset = ((points[-1] - points[0]) / count) * 0.5

            for point, vec in zip(spline.bezier_points, points):
                vec += center
                point.co = vec
                point.radius = 1

                point.handle_left_type = 'ALIGNED'
                point.handle_right_type = 'ALIGNED'
                point.handle_right = vec + handle_offset
                point.handle_left = vec - handle_offset

        else:
            spline.points.add(count - 1)
            #spline.order_u = order_u

            for point, vec in zip(spline.points, points):
                vec += center
                point.co[0] = vec[0]
                point.co[1] = vec[1]
                point.co[2] = vec[2]
                point.co[3] = 1
                point.radius = 1

        return primitive_obj, dimensions

    def purge_shapes(self):
        self.remove_deletables()
        self.deletable.update(self.created_shapes)

        for obj in self.created_shapes:
            obj.name += '_'
            if obj.data:
                obj.data.name += '_'

            for col in obj.users_collection[:]:
                col.objects.unlink(obj)

        self.created_shapes.clear()
        self.hide_shapes.clear()
        self.enable_mods.clear()

    def remove_deletables(self):
        for obj in self.deletable:
            data = obj.data
            type = obj.type

            bpy.data.objects.remove(obj)

            if data:
                if type == 'MESH':
                    bpy.data.meshes.remove(data)

                else:
                    bpy.data.curves.remove(data)

        self.deletable.clear()

    def enum_scroll(self, prop, value = 1):
        attribute = getattr(self, prop + '_items')
        items = [item[0] for item in attribute]
        return items[ (items.index(getattr(self, prop)) + value ) % len(items) ]


    def draw_ui(self, context):

        self.master.setup()

        # -- Fast UI -- #
        if not self.master.should_build_fast_ui(): return

        # Main
        win_list = []
        if addon.preference().ui.Hops_modal_fast_ui_loc_options != 1:
            win_list.append(self.primitive_type)
            win_list.append(self.shape_offset_axis)
            if self.shape_offset > 0:
                win_list.append(F'{self.shape_offset:.3f}')
            if self.individual:
                win_list.append('I' if self.individual else 'C')
            if not self.modified:
                win_list.append(F"M: {self.modified}")
            if self.equalize_mode != "OFF":
                if self.primitive_type not in {'Empty', 'Decap', 'Convex_Hull' }:
                    win_list.append(self.equalize_mode)
            if self.scale != 1:
                win_list.append(F"{self.scale:.3f}")
            if self.parent_mode != "OFF":
                win_list.append(self.parent_mode)

            if self.primitive_type == 'Plane':
                win_list.append(self.plane_alignment)
                #win_list.append(F'{self.plane_offset:.3f}')

            elif self.primitive_type == 'Cylinder':
                #win_list.append(self.alignment)
                win_list.append(self.cyl_segments)

            elif self.primitive_type == 'Sphere':
                #win_list.append(self.alignment)
                win_list.append(self.sphere_segments)
                win_list.append(self.sphere_rings)

            elif self.primitive_type == 'Quad_Sphere':
                #win_list.append(self.alignment)
                win_list.append(self.quad_sphere_divisions)

            # elif self.primitive_type == 'Empty':
            #     win_list.append(self.empty_display)

            elif self.primitive_type == 'Decap':
                win_list.append(self.decap_axis)
                if self.decap_fill_mode != 'NO':
                    win_list.append(self.decap_fill_mode)
                if self.decap_cap_type != 'NO':
                    win_list.append(self.decap_cap_type)
                win_list.append(f'{self.decap_thickness:.3f}' if not self.decap_solidify else 'Z')
                win_list.append(f'{self.decap_center:.3f}')

            elif self.primitive_type == 'Convex_Hull':
                win_list.append(f'{self.dissolve_angle:.1f}')

            elif self.primitive_type == 'Curve':
                win_list.append(self.curve_type[0])
                win_list.append(self.curve_axis)


            # if self.primitive_type not in self.no_bevel_club:
            #     win_list.append(self.copy_1st_bvl)

        else:
            win_list.append(self.primitive_type)
            win_list.append(self.shape_offset_axis)
            win_list.append(F'Offset[G]: {self.shape_offset:.3f}')
            #win_list.append(F"Mode[I]: {'Individual' if self.individual else 'Combined'}")
            #win_list.append(F"Modified: {self.modified}")
            # if self.primitive_type not in {'Empty', 'Decap', 'Convex_Hull' }:
            #     win_list.append(F"Equalize: {self.equalize_mode}")
            win_list.append(F"Scale[S]: {self.scale:.3f}")
            #win_list.append(f"Parenting: {self.parent_mode}")
            #win_list.append(f"Show Original: {self.display_original}")

            if self.primitive_type == 'Plane':
                win_list.append(F'Axis: {self.plane_alignment}')
                #win_list.append(F'Offset: {self.plane_offset:.3f}')

            elif self.primitive_type == 'Cylinder':
                win_list.append(F'Alignment: {self.alignment}')
                win_list.append(F'Segments: {self.cyl_segments}')

            elif self.primitive_type == 'Sphere':
                win_list.append(F'Alignment: {self.alignment}')
                win_list.append(F'Segments: {self.sphere_segments}')
                win_list.append(F'Rings: {self.sphere_rings}')

            elif self.primitive_type == 'Quad_Sphere':
                win_list.append(F'Divisions: {self.quad_sphere_divisions}')

            elif self.primitive_type == 'Empty':
                win_list.append(F'Display: {self.empty_display}')

            elif self.primitive_type == 'Decap':
                win_list.append(F'Axis: {self.decap_axis}')
                #win_list.append(F"Fill: {self.decap_fill_mode}")
                #win_list.append(F"Caps: {self.decap_cap_type}")
                win_list.append(F'Thickness: {self.decap_thickness:.3f}' if not self.decap_solidify else 'ZERO')
                win_list.append(F'Center: {self.decap_center:.3f}')

            elif self.primitive_type == 'Convex_Hull':
                win_list.append(F'Dissolve:{self.dissolve_angle:.1f}')

            elif self.primitive_type == 'Curve':
                win_list.append(F'Type[C]: {self.curve_type}')
                win_list.append(F'Axis: {self.curve_axis}')

            # if self.primitive_type not in self.no_bevel_club:
            #     win_list.append(F'Copy 1st BVL: {self.copy_1st_bvl}')

        # Help
        help_items = {"GLOBAL" : [], "STANDARD" : []}

        help_items["GLOBAL"] = [
            ("M", "Toggle mods list"),
            ("H", "Toggle help"),
            ("~", "Toggle UI Display Type"),
            ("O", "Toggle viewport rendering")]

        help_append = help_items["STANDARD"].append

        if self.primitive_type == 'Decap':
            help_append(["C", f"Caps mode - {self.decap_cap_type}"])
            help_append(["F", f"Fill Mode - {self.decap_fill_mode}"])
            help_append(["T", "Toggle ZERO thickness mode"])

        elif self.primitive_type == 'Curve':
            help_append(["C", f"Type - {self.curve_type}"])

        if self.primitive_type not in self.no_bevel_club:
            help_append(["B", f"1st bevel - {self.copy_1st_bvl}"])

        if self.primitive_type in {'Plane', 'Sphere', 'Cylinder', 'Decap'}:
            help_append(["X  ", 'Adjust alignment'])

        help_append(["Y",  F"Active Only: {self.active_only}"])
        help_append(["Ctrl+S", "Reset Scale"])
        help_append(["Ctrl+G", "Reset Offset"])
        help_append(["G", "Toggle Offset adjust"])
        help_append(["S", "Toggle Scale adjust"])
        help_append(["P", f"Parenting Mode {self.parent_mode}"])
        help_append(["I", f"Toggle {'Individual' if self.individual else 'Combined'}"])
        help_append(["R", "Reset shape Adjustment"])
        help_append(["A", "Toggle Adjustment mode"])
        help_append(["D", F"Display original: {self.display_original}"])
        help_append(["E", f"Equalize mode - {self.equalize_mode}"])
        help_append(["Shift+W", f"Shade {'Solid' if self.shade_wire else 'Wire'}"])
        help_append(["W", f"Toggle Modified {self.modified}"])
        help_append(["LMB", "Apply"])
        help_append(["RMB", "Cancel"])

        # scroll
        if self.scroll_state == Scroll_states.none:
            if self.primitive_type in {'Plane', 'Sphere', 'Cylinder', 'Decap'}:
                help_append(["Shift+Scroll  ", 'Adjust alignment'])

            elif self.primitive_type == 'Empty':
                help_append(["Shift+Scroll ", 'Adjust Display type'])

            help_append(["Ctrl+Scroll  ", "Adjust offset direction"])
            help_append(["Scroll", "Cycle Shape"])

        elif self.scroll_state == Scroll_states.cyl_segments:
            help_append(["Scroll ", 'Adjust Segments'])

        elif self.scroll_state == Scroll_states.sphere_adjust:
            help_append(["Shift+Scroll ", 'Adjust Rings'])
            help_append(["Scroll", 'Adjust Segmnets'])

        elif self.scroll_state == Scroll_states.sphere_adjust:
            help_append(["Scroll", 'Adjust Division'])

        # mouse
        if self.mouse_state == Mouse_states.hull_dissolve:
            help_append(["Mouse", "Adjust Dissolve angle"])

        elif self.mouse_state == Mouse_states.shape_offset:
            help_append(["Mouse", "Adjust Offset"])

        elif self.mouse_state == Mouse_states.decap_adjsut:
            help_append(["Ctrl+Mouse ", "Adjust Center"])
            help_append(["Mouse", "Adjust Thickness"])

        elif self.mouse_state == Mouse_states.decap_solidify:
            help_append(["Ctrl+Mouse ", "Adjust Center"])
            help_append(["Mouse", "Adjust Solidify"])

        elif self.mouse_state == Mouse_states.scale:
            help_append(["Mouse", "Adjust Scale"])

        elif self.mouse_state == Mouse_states.cyl_diameter:
            help_append(["Alt+Mouse ", "Adjust Diameter 2"])
            help_append(["Ctrl+Mouse ", "Adjust Diameter 1"])
            help_append(["Mouse", "Adjust Diameter"])

        if 'SPACE' in self.base_controls.popover_keys:
            help_items["STANDARD"].append(('Space', 'Open Select Menu'))
        elif 'TAB' in self.base_controls.popover_keys:
            help_items["STANDARD"].append(('TAB', 'Open Select Menu'))

        # Mods
        mods_list = get_mods_list(mods=bpy.context.active_object.modifiers) if context.active_object else []

        self.master.receive_fast_ui(win_list=win_list, help_list=help_items, image="Tthick", mods_list=mods_list)

        self.master.finished()

    ####################################################
    #   CURSOR WARP
    ####################################################

    def safe_draw_shader(self, context):
        method_handler(self.draw_shader,
            arguments = (context,),
            identifier = 'UI Framework',
            exit_method = self.remove_shader)


    def remove_shader(self):
        '''Remove shader handle.'''

        if self.draw_handle:
            self.draw_handle = bpy.types.SpaceView3D.draw_handler_remove(self.draw_handle, "WINDOW")


    def draw_shader(self, context):
        '''Draw shader handle.'''

        draw_modal_frame(context)

def set_parent (child, parent):
    buffer = child.matrix_world.copy()
    child.parent = parent
    child.matrix_parent_inverse = parent.matrix_world.inverted()
    child.matrix_world = buffer

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
        self.center_base = None

        self.dimensions_final = None
        self.bounds_final = None
        self.center_final = None

        self.parent_name = None
        self.matrix_parent_inverse = None

        self.hide = None

def popup_draw(self, context):
    layout = self.layout

    data = HOPS_OT_Conv_To_Shape_1_5.operator
    if not data: return {'CANCELLED'}

    layout.label(text= 'Selector')
    vals = (item[0] for item in data.primitive_type_items)

    for val in vals:
        row = layout.row()
        row.scale_y = 2
        row.prop_enum(data, 'primitive_type', val)
