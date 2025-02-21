import bpy
from math import radians
from mathutils import Vector, Matrix
from ... utility import addon


class Object():
    def __init__(self, obj:bpy.types.Object) -> None:
        self.name = obj.name

        loc, rot, sca = obj.matrix_world.decompose()

        eval = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())

        self.matrix_scaless = Matrix.Translation(loc) @ rot.to_matrix().to_4x4()
        scale = Matrix.Diagonal((*sca, 1))
        self.bounds = [scale @ Vector(v) for v in eval.bound_box]
        self.min_corner, self.max_corner = coordinates_to_diagonal(self.bounds)
        self.center = (self.min_corner + self.max_corner) /2


class Curve():
    _name = 'HOPS Curve'
    _axis_map = {
        'POS_X' : 0, # X+ direction
        'POS_Y' : 90, # Y+ direction
        'POS_Z' : 180, # Z+ direction
        'NEG_X' : -90, #  X- direction
        'NEG_Y' : 180, # Y- direction
        'NEG_Z' : -90, # -90 tilt Z- direction
    }

    def __init__(self, context, deform_axis='POS_Z', stretch=True) -> None:
        self.modifiers = []
        self.deform_axis = deform_axis
        self.type = 'NURBS'

        self.data = bpy.data.curves.new(self._name, 'CURVE')
        self.data.use_path = False
        self.data.use_stretch = stretch
        self.data.use_deform_bounds = True
        self.data.dimensions = '3D'

        self.object = bpy.data.objects.new(self._name, self.data)
        self.object.show_in_front = True

        context.collection.objects.link(self.object)

    def remove(self) -> None:
        bpy.data.objects.remove(self.object)
        bpy.data.curves.remove(self.data)

        for mod in self.modifies:
            mod.id_data.modifiers.remove(self.modifier)

        self.modifies.clear()

    def add_modifier(self, object):
        modifier = object.modifiers.new(type='CURVE', name=self._name)
        modifier.name = self._name
        modifier.object = self.object
        modifier.deform_axis = self.deform_axis

        self.modifiers.append(modifier)

    def create_spline(self, points: list, type='NURBS', resolution_u=36, order_u=3):
        self.type = type

        self.data.splines.clear()
        spline = self.data.splines.new(type)
        spline.use_endpoint_u = True
        count = len(points)
        tilt = radians(self._axis_map[self.deform_axis])
        spline.resolution_u = resolution_u

        if type == 'BEZIER':
            spline.bezier_points.add(count - 1)
            handle_offset = ((points[-1] - points[0]) / count) * 0.5

            for point, vec in zip(spline.bezier_points, points):
                point.co = vec
                point.radius = 1
                point.tilt = tilt

                point.handle_left_type = 'ALIGNED'
                point.handle_right_type = 'ALIGNED'
                point.handle_right = vec + handle_offset
                point.handle_left = vec - handle_offset

        else:
            spline.points.add(count - 1)
            spline.order_u = order_u

            for point, vec in zip(spline.points, points):
                point.co[0] = vec[0]
                point.co[1] = vec[1]
                point.co[2] = vec[2]
                point.co[3] = 1
                point.radius = 1
                point.tilt = tilt


DESC = '''Adds a curve + curve mod to shape

F9 for adjustment

'''

class HOPS_OT_MOD_Curve(bpy.types.Operator):
    bl_idname = 'hops.mod_curve'
    bl_label = 'Add a Curve modifier with Curve object'
    bl_options = {'REGISTER', 'UNDO', 'BLOCKING'}
    bl_description = DESC

    deform_axis: bpy.props.EnumProperty(
        name='Axis',
        description='Deform Axis',
        items=[
            ('POS_X', '+X', 'Deform +X axis'),
            ('POS_Y', '+Y', 'Deform +Y axis'),
            ('POS_Z', '+Z', 'Deform +Z axis'),
            ('NEG_X', '-X', 'Deform -X axis'),
            ('NEG_Y', '-Y', 'Deform -Y axis'),
            ('NEG_Z', '-Z', 'Deform -Z axis'),
            ],
        default='POS_Z')

    subdivisions: bpy.props.IntProperty(
        name='Subdivisions',
        description='Number of times the curve is subdivided',
        min=0,
        default=1
    )

    type: bpy.props.EnumProperty(
        name='Type',
        description='Spline type',
        items=[
            ('BEZIER', 'BEZIER', 'BEZIER'),
            ('NURBS', 'NURBS', 'NURBS'),
            ],
        default='BEZIER'
    )

    resolution: bpy.props.IntProperty(
        name='Resolution U',
        description='Curve subdivision per segment',
        min=1,
        default=36,
    )

    order: bpy.props.IntProperty(
        name='Order U',
        description='Order for NURBS curve in U direction. Higher number = smoother curve',
        min=2,
        max=6,
        default=3,
    )

    stretch: bpy.props.BoolProperty(
        name='Stretch',
        description='Stretch Object(s) to fit curve',
        default=True,
    )

    combined: bpy.props.BoolProperty(
        name='Combined',
        description='Create single curve to deform selection',
        default=False
    )

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def invoke(self, context, event):
        self.notify = lambda val, sub='': bpy.ops.hops.display_notification(info=val, subtext=sub) if addon.preference().ui.Hops_extra_info else lambda val, sub=None: None
        self.selection = [Object(o) for o in context.selected_objects if o.type == 'MESH']

        if not self.selection:
            msg = 'CANCELLED'
            sub = 'No selected Meshes'
            self.notify(val=msg, sub=sub)

            return {'CANCELLED'}
        return self.execute(context)

    def execute(self, context):
        if self.combined:
            bounds = [o.matrix_scaless @ v for o in self.selection for v in o.bounds]
            _min, _max = coordinates_to_diagonal(bounds)
            center = (_min + _max) / 2

            _min -= center
            _max -= center

            curve = Curve(context, stretch=self.stretch, deform_axis=self.deform_axis)
            axis = self.deform_axis[-1]
            index = 'XYZ'.index(axis)
            points = [_min, _max] if self.deform_axis.startswith('POS') else [_max, _min]

            for vec in points:
                for i in range (3):
                    if i != index:
                        vec[i] = 0

            curve.create_spline(subdivide_line(*points, times=self.subdivisions), type=self.type, resolution_u=self.resolution, order_u=self.order)
            curve.object.matrix_world.translation = center

            for Obj in self.selection:
                obj = bpy.data.objects[Obj.name]

                curve.add_modifier(obj)
        else:
            for Obj in self.selection:
                obj = bpy.data.objects[Obj.name]
                center = Obj.center
                _min = Obj.min_corner - Obj.center
                _max = Obj.max_corner - Obj.center

                curve = Curve(context, stretch=self.stretch, deform_axis=self.deform_axis)
                axis = self.deform_axis[-1]
                index = 'XYZ'.index(axis)
                points = [_min, _max] if self.deform_axis.startswith('POS') else [_max, _min]

                for vec in points:
                    for i in range (3):
                        if i != index:
                            vec[i] = 0.0

                curve.create_spline(subdivide_line(*points, times=self.subdivisions), type=self.type, resolution_u=self.resolution, order_u=self.order)
                curve.add_modifier(obj)
                matrix = Obj.matrix_scaless.copy()
                matrix.translation = Obj.matrix_scaless @ center

                curve.object.matrix_world = matrix

                curve.object.select_set(True)
                context.view_layer.objects.active = curve.object
                obj.select_set(False)

        msg = F'Curve Modifier {self.deform_axis[-1]}'
        subtext = f'{self.type.capitalize()} Divisions: {self.subdivisions} / Resolution: {self.resolution} / Stretch: {self.stretch}'#. Combined: {self.combined}.'
        if self.type == 'NURBS':
            subtext = f'Order: {self.order}. {subtext}'

        self.notify(val=msg, sub=subtext)

        return {'FINISHED'}

    def draw(self, context):
        self.layout.prop(self, 'type')
        self.layout.prop(self, 'deform_axis')
        self.layout.prop(self, 'subdivisions')
        self.layout.prop(self, 'resolution')
        if self.type == 'NURBS':
            self.layout.prop(self, 'order')
        self.layout.prop(self, 'stretch')
        self.layout.prop(self, 'combined')



def coordinates_to_diagonal(coords) -> Vector:
    mins = []
    maxs = []
    length = len(coords[0])

    for i in range (length):
        var = [vec[i] for vec in coords]
        mins.append(min(var))
        maxs.append(max(var))

    return Vector(mins), Vector(maxs)

def subdivide_line(p1: Vector, p2: Vector, times=0) -> list:
    direction = p2 - p1

    divisor = 1 + times
    increment = direction * (1 / divisor)

    result = []

    for i in range(divisor + 1):
        vec = p1 + (increment * i)
        result.append(vec)

    return result
