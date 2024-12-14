import bpy, bmesh
from bpy.types import GizmoGroup, Gizmo
from mathutils import Vector, Matrix
from math import copysign, pi

from .... utility import addon
from ..shape.utility import modal

gizmo_scale = 1.8
color_inactive = 0.4, 0.4, 0.4


class GizmoProp:
    gizmo_index: int
    axis_index: int
    matrix: Matrix
    operator: str

    _enable_axis: True
    _enabled: True

    @property
    def enable_axis(self):
        return self._enable_axis

    @enable_axis.setter
    def enable_axis(self, val):
        self._enable_axis = val

        gz = GIZMOS[self.gizmo_index]
        if val:
            gz.color = COLORS[self.axis_index]
        else:
            gz.color = color_inactive

    @property
    def enabled(self):
        return self._enabled

    @enabled.setter
    def enabled(self, val):
        self._enabled = val

        gz = GIZMOS[self.gizmo_index]

        if val:
            op = gz.target_set_operator(self.operator)
            op.gizmo_index = self.gizmo_index

        else:
            gz.target_set_operator(BC_OT_Mirror_Gizmo_Disabled.bl_idname)

    def __init__(self, gizmo_index, axis_index, flip, matrix, operator):
        self.gizmo_index = gizmo_index
        self.axis_index = axis_index
        self.flip = flip
        self.matrix = matrix
        self.operator = operator

class DiscountMirror:
    def __init__(self, context):
        self.use_axis = False, False, False
        self.use_bisect_flip_axis = False, False, False
        self.bisect_threshold = 0.001
        self.id_data = context.scene.bc.shape
        self.mirror_object = context.active_object

COLORS = [
    Vector((1, 0.2, 0.322)),
    Vector((0.545, 0.863, 0)),
    Vector((0.157, 0.565, 1)),
]

class BC_GGT_Mirror_GizmoGroup(GizmoGroup):
    bl_idname = "BC_GGT_mirror"
    bl_label = ""
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'3D', 'EXCLUDE_MODAL'}

    @classmethod
    def poll(cls, context):
        bc = context.scene.bc

        if bc.running and addon.preference().shape.mirror_gizmo:
            return True

        global GIZMOS
        GIZMOS = []

        context.window_manager.gizmo_group_type_unlink_delayed(BC_GGT_Mirror_GizmoGroup.bl_idname)

    def setup(self, context):
        bc = context.scene.bc

        for i in range (6):
            gz = self.gizmos.new('GIZMO_GT_arrow_3d')
            self.color_gizmo(gz, i)
            gz.draw_style = 'BOX'

            op = gz.target_set_operator(GIZMO_PROP[i].operator)
            op.gizmo_index = i

        global GIZMOS
        GIZMOS = self.gizmos[:]
        mod = None

        for m in bc.shape.modifiers:
            if m.type == 'MIRROR':
                mod = m
                break

        if not mod:
            mod = DiscountMirror(context)

        for i in range(3):
            gizmo = GIZMO_PROP[i]
            o_gizmo = GIZMO_PROP[i + 3]
            use = mod.use_axis[i]

            if not use:
                gizmo.enable_axis = True
                o_gizmo.enable_axis = True

            elif mod.use_bisect_flip_axis[i]:
                gizmo.enable_axis = True
                o_gizmo.enable_axis = False

            else:
                gizmo.enable_axis = False
                o_gizmo.enable_axis = True

            pos, neg = self.validate_axis(mod, i)

            gizmo.enabled = pos
            o_gizmo.enabled = neg

    @staticmethod
    def color_gizmo(gz, index: int):
        gz.color = COLORS[GIZMO_PROP[index].axis_index]
        gz.alpha = 1

        gz.color_highlight = gz.color * 1.6
        gz.alpha_highlight = 0.7

        gz.scale_basis = gizmo_scale

    def refresh(self, context):
        bc = context.scene.bc
        operator = bc.__class__.operator
        operator.mirror_gizmo_higlight = False
        preference = addon.preference()

        object = context.active_object if context.active_object else bc.shape
        matrix = object.matrix_world.normalized()

        if preference.display.mirror_gizmo_loc == 'CENTER':
            matrix.translation = sum([bc.shape.matrix_world @ v for v in bc.operator.bounds], Vector()) / 8

        for i, gz in enumerate(self.gizmos):
            gz.matrix_basis = matrix
            gz.matrix_offset = GIZMO_PROP[i].matrix

            if gz.is_highlight:
                bc.__class__.operator.mirror_gizmo_higlight = True

    @staticmethod
    def validate_axis(mod, axis_index):
        positive = False
        negative = False

        object = mod.id_data
        matrix = object.matrix_world.copy()
        normal = Vector()
        normal[axis_index] = 1.0
        if mod.mirror_object: matrix = mod.mirror_object.matrix_world.normalized()

        co_world = matrix.translation
        normal_world = matrix @ normal

        local_space = object.matrix_world.inverted()

        co = local_space @ co_world
        normal = local_space @ normal_world
        normal = normal - co
        normal.normalize()

        eval = object.evaluated_get(bpy.context.evaluated_depsgraph_get())

        bm = bmesh.new()
        bm.from_mesh(eval.data)
        geom = bm.verts[:] + bm.edges[:] + bm.faces[:]

        result = bmesh.ops.bisect_plane(bm, geom=geom, dist=mod.bisect_threshold, plane_co=co, plane_no=normal, clear_outer=False, clear_inner=True)
        if bool (result['geom_cut']):
            return True, True

        if mod.use_axis[axis_index]:
            if mod.use_bisect_flip_axis[axis_index]:
                return False, True

            return True, False

        if result['geom']:
            positive = True
        else:
            negative = True

        return positive, negative

class BC_OT_Mirror_Gizmo(bpy.types.Operator):
    """Mirror"""
    bl_idname = "bc.gizmo_click_op"
    bl_label = ""
    gizmo_index: bpy.props.IntProperty()
    exit_mirror: bpy.props.BoolProperty()

    def invoke (self, context, event):
        self.exit_mirror = not event.shift

        return self.execute(context)

    def execute(self, context):
        bc = context.scene.bc
        preference = addon.preference()

        mod = self.get_mirror(context)
        gizmo = GIZMO_PROP[self.gizmo_index]
        o_gizmo = GIZMO_PROP[(self.gizmo_index + 3) % 6]
        mod.use_bisect_axis[gizmo.axis_index] = True

        if not gizmo.enabled: return {'FINISHED'}

        if mod.use_axis[gizmo.axis_index] and gizmo.flip == mod.use_bisect_flip_axis[gizmo.axis_index]:
            mod.use_axis[gizmo.axis_index] = False
            mod.use_bisect_flip_axis[gizmo.axis_index] = False
            gizmo.enable_axis = True
            o_gizmo.enable_axis = True
            bc.shape.data.update()

        else:
            mod.use_axis[gizmo.axis_index] = True
            mod.use_bisect_flip_axis[gizmo.axis_index] = gizmo.flip
            gizmo.enable_axis = False
            o_gizmo.enable_axis = True
            bc.shape.data.update()

        self.validate_group(mod)

        preference.shape['mirror_axis'] =  mod.use_axis
        preference.shape['mirror_bisect_axis'] = mod.use_bisect_axis
        preference.shape['mirror_flip_axis'] = mod.use_bisect_flip_axis

        if self.exit_mirror:
            preference.shape.mirror_gizmo = False

        return {'FINISHED'}

    @staticmethod
    def get_mirror(context):
        bc = context.scene.bc

        mirror = None
        for mod in bc.shape.modifiers:
            if mod.type == 'MIRROR': return mod

        mirror = bc.shape.modifiers.new(name='Mirror', type='MIRROR')
        mirror.use_axis = False, False, False
        mirror.use_bisect_axis = False, False, False
        mirror.use_bisect_flip_axis = False, False, False

        if context.active_object:
            mirror.mirror_object = context.active_object

        bc.mirror_axis = mirror.use_axis
        bc.mirror_axis_flip = mirror.use_bisect_flip_axis

        return mirror

    @staticmethod
    def validate_group(mod):
        for i in range(3):
            pos_gizmo = GIZMO_PROP[i]
            neg_gizmo = GIZMO_PROP[i + 3]
            pos, neg = BC_GGT_Mirror_GizmoGroup.validate_axis(mod, i)

            p_active = mod.use_axis[i] and mod.use_bisect_flip_axis[i] == pos_gizmo.flip
            n_active = mod.use_axis[i] and mod.use_bisect_flip_axis[i] == neg_gizmo.flip

            pos_gizmo.enabled = pos or p_active
            neg_gizmo.enabled = neg or n_active

class BC_OT_Mirror_Gizmo_Xp(BC_OT_Mirror_Gizmo):
    """Mirror on X+ axis"""
    bl_idname = "bc.gizmo_click_op_xp"

class BC_OT_Mirror_Gizmo_Yp(BC_OT_Mirror_Gizmo):
    """Mirror on Y+ axis"""
    bl_idname = "bc.gizmo_click_op_yp"

class BC_OT_Mirror_Gizmo_Zp(BC_OT_Mirror_Gizmo):
    """Mirror on Z+ axis"""
    bl_idname = "bc.gizmo_click_op_zp"

class BC_OT_Mirror_Gizmo_Xn(BC_OT_Mirror_Gizmo):
    """Mirror on X- axis"""
    bl_idname = "bc.gizmo_click_op_xn"

class BC_OT_Mirror_Gizmo_Yn(BC_OT_Mirror_Gizmo):
    """Mirror on Y- axis"""
    bl_idname = "bc.gizmo_click_op_yn"

class BC_OT_Mirror_Gizmo_Zn(BC_OT_Mirror_Gizmo):
    """Mirror on Z- axis"""
    bl_idname = "bc.gizmo_click_op_zn"


class BC_OT_Mirror_Gizmo_Toggle(bpy.types.Operator):
    bl_idname = "bc.gizmo_click_toggle"
    bl_label = ''
    axis_index: bpy.props.IntProperty()
    flip: bpy.props.BoolProperty()

    @classmethod
    def poll(_, context):
        return GIZMOS

    def execute(self, context):
        mod = BC_OT_Mirror_Gizmo.get_mirror(context)
        mod.use_bisect_axis[self.axis_index] = True

        p_gizmo = GIZMO_PROP[self.axis_index]
        n_gizmo = GIZMO_PROP[(self.axis_index + 3) % 6]

        self.flip = self.flip and mod.use_axis[self.axis_index]

        if not self.flip:
            if mod.use_axis[self.axis_index]:
                mod.use_axis[self.axis_index] = False
                p_gizmo.enable_axis = n_gizmo.enable_axis = True
                BC_OT_Mirror_Gizmo.validate_group(mod)
                return {'FINISHED'}

            if p_gizmo.enabled:
                mod.use_bisect_flip_axis[self.axis_index] = False
                p_gizmo.enable_axis = False
                n_gizmo.enable_axis = True

            else:
                mod.use_bisect_flip_axis[self.axis_index] = True
                p_gizmo.enable_axis = True
                n_gizmo.enable_axis = False

            BC_OT_Mirror_Gizmo.validate_group(mod)
            mod.use_axis[self.axis_index] = True

            return {'FINISHED'}

        if mod.use_bisect_flip_axis[self.axis_index]:
            if not p_gizmo.enabled: return {'FINISHED'}

            p_gizmo.enable_axis = True
            n_gizmo.enable_axis = False
            mod.use_bisect_flip_axis[self.axis_index] = False

        else:
            if not n_gizmo.enabled: return {'FINISHED'}

            p_gizmo.enable_axis = True
            n_gizmo.enable_axis = False
            mod.use_bisect_flip_axis[self.axis_index] = True

        BC_OT_Mirror_Gizmo.validate_group(mod)
        mod.use_axis[self.axis_index] = True
        return {'FINISHED'}

class BC_OT_Mirror_Gizmo_Disabled(bpy.types.Operator):
    """Disabled"""
    bl_idname = "bc.gizmo_click_op_disabled"
    bl_label = ''

    def execute(self, context):
        return {'FINISHED'}


GIZMO_PROP = [
    GizmoProp(0, 0, False ,Matrix.Rotation(pi/2, 4, 'Y'), BC_OT_Mirror_Gizmo_Xp.bl_idname),
    GizmoProp(1, 1, False ,Matrix.Rotation(-pi/2, 4, 'X'), BC_OT_Mirror_Gizmo_Yp.bl_idname),
    GizmoProp(2, 2, False ,Matrix.Rotation(0, 4, 'X'), BC_OT_Mirror_Gizmo_Zp.bl_idname),
    GizmoProp(3, 0, True ,Matrix.Rotation(-pi/2, 4, 'Y'), BC_OT_Mirror_Gizmo_Xn.bl_idname),
    GizmoProp(4, 1, True ,Matrix.Rotation(pi/2, 4, 'X'), BC_OT_Mirror_Gizmo_Yn.bl_idname),
    GizmoProp(5, 2, True ,Matrix.Rotation(pi, 4, 'X'), BC_OT_Mirror_Gizmo_Zn.bl_idname),
]

GIZMOS = []
