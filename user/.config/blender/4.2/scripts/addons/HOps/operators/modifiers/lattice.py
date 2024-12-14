import bpy
import bmesh
import statistics
from mathutils import Vector, Matrix
from ... utility import collections, object, math
from ... utility import addon
from ...ui_framework.operator_ui import Master
from ...utils.objects import set_active

from ... utility import modifier


class HOPS_OT_MOD_Lattice(bpy.types.Operator):
    bl_idname = "hops.mod_lattice"
    bl_label = "Add Lattice Modifier"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = """LMB - Add Lattice Modifier for selection with world-oriented Lattice
LMB + Shift - Add Lattice Modifier for each object with object-oriented lattice
CTRL - Force new lattice modifier

"""

    modified: bpy.props.BoolProperty(
    name="Modified", description="Use final geometry. Edit mode only", default = False)
    #i've set it false by default, as calculation of final geo can get quite heavy
    individual: bpy.props.BoolProperty(
    name="Individual", description="Assign individual lattice per object", default = False)

    mode: bpy.props.EnumProperty(
        name="Lattice Style",
        default='KEY_BSPLINE',
        items=(("KEY_LINEAR", "Linear", ""),
               ("KEY_BSPLINE", "Bspline", "")))


    called_ui = False


    def __init__(self):

        HOPS_OT_MOD_Lattice.called_ui = False


    def draw (self, context):
        self.layout.prop(self, 'mode')
        if self.edit_init:
            self.layout.prop(self, 'modified')
        self.layout.prop(self, 'individual')


    @classmethod
    def poll(cls, context):
        return True


    def invoke(self, context, event):
        self.selected = []
        self.edit_init= False
        if context.mode == 'EDIT_MESH':
            self.edit_init = True

        self.ctrl_event = False
        if event.ctrl:
            self.ctrl_event=True

        self.individual = False
        if event.shift:
            self.individual = True

        return self.execute(context)


    def execute (self, context):
        context.view_layer.update()
        self.selected = [ob for ob in context.selected_objects if ob.type in {'MESH', 'CURVE', 'FONT', 'SURFACE', 'GPENCIL'}]

        if self.individual:
            lattices = []
            for obj in self.selected:

                if self.ctrl_event or not self.lattice_modifiers(obj):
                    coords = self.get_vert_coords(obj,context)
                    lattice_object = self.add_lattice_obj(context, obj)
                    self.add_lattice_modifier(context, obj, lattice_object)
                    self.lattice_transform(obj, lattice_object,coords)
                    lattices.append(lattice_object)

            if lattices:
                bpy.ops.object.mode_set(mode = 'OBJECT')
                bpy.ops.object.select_all(action='DESELECT')
                for l in lattices:
                    set_active (l, select=True)
        else:
            coords_all=[]
            for obj in self.selected:
                if self.ctrl_event or not self.lattice_modifiers(obj):
                    coords= []
                    if context.mode in {'EDIT_MESH', 'EDIT_GPENCIL'}:
                        coords= self.get_vert_coords(obj, context, obj.matrix_world)
                        if coords != None:
                            coords_all.extend(coords)

                    else:
                        coords_all.extend(object.bound_coordinates(obj, obj.matrix_world))
                elif self.blank_lattice_modifiers(obj):
                    self.blank_lattice_modifiers(obj)[0].object = lattice_object = self.add_lattice_obj(context, obj)
                    coords = self.get_vert_coords(obj, context)
                    self.lattice_transform(obj, lattice_object, coords)

            if len(coords_all)>0:
                lattice_object = self.add_lattice_obj(context, context.active_object)
                self.lattice_transform(obj, lattice_object, coords_all)
                for obj in self.selected :
                    self.add_lattice_modifier(context, obj, lattice_object)
                if context.mode in {'EDIT_MESH', 'EDIT_GPENCIL'}:
                    bpy.ops.object.mode_set(mode = 'OBJECT')
                set_active(lattice_object, select=True, only_select= True)


        if obj.type == "MESH":
            modifier.sort(obj, types=['WEIGHTED_NORMAL'], last=True)

        # Operator UI
        if not HOPS_OT_MOD_Lattice.called_ui:
            HOPS_OT_MOD_Lattice.called_ui = True

            ui = Master()
            draw_data = [
                ["LATTICE"],
                ["Modified", self.modified]]
            ui.receive_draw_data(draw_data=draw_data)
            ui.draw(draw_bg=addon.preference().ui.Hops_operator_draw_bg, draw_border=addon.preference().ui.Hops_operator_draw_border)

        return {"FINISHED"}


    @staticmethod
    def lattice_modifiers(obj):
        if obj.type == 'GPENCIL':
            return [modifier for modifier in obj.grease_pencil_modifiers if modifier.type == 'GP_LATTICE']
        else:
            return [modifier for modifier in obj.modifiers if modifier.type == 'LATTICE']


    def blank_lattice_modifiers(self, obj):
        return [modifier for modifier in self.lattice_modifiers(obj) if modifier.object is None]


    def add_lattice_modifier(self, context, obj, lattice_object):
        if obj.type == 'GPENCIL':
            lattice_modifier = obj.grease_pencil_modifiers.new(name="Lattice", type='GP_LATTICE')
        else:
            lattice_modifier = obj.modifiers.new(name="Lattice", type='LATTICE')

        lattice_modifier.object = lattice_object

        if obj.type in {'MESH', 'GPENCIL'} and obj.mode in {'EDIT', 'EDIT_GPENCIL'}:
            lattice_modifier.vertex_group = obj.vertex_groups.active.name


    def add_lattice_obj(self, context, obj, ):
        lattice_data = bpy.data.lattices.new('Lattice')
        lattice_obj = bpy.data.objects.new('Lattice', lattice_data)
        collection = collections.find_collection(context, obj)
        collection.objects.link(lattice_obj)
        lattice_obj.data.use_outside = True
        lattice_obj.data.interpolation_type_u = self.mode
        lattice_obj.data.interpolation_type_v = self.mode
        lattice_obj.data.interpolation_type_w = self.mode

        return lattice_obj


    def lattice_transform (self, obj, lattice_obj, coords = None  ):
        if coords:
            box = math.coords_to_bounds(coords)
            lattice_obj.location =  math.coords_to_center(box)
            lattice_obj.dimensions = math.dimensions(box)
            if self.individual:
                lattice_obj.location =  obj.matrix_world @ math.coords_to_center(box)
                obj_scale = obj.matrix_world.to_scale()
                for i in range(3):
                     lattice_obj.scale[i] *= obj_scale[i]
                lattice_obj.rotation_euler = obj.matrix_world.to_euler()

        else:
            lattice_obj.location = obj.matrix_world @ math.coords_to_center(obj.bound_box)
            lattice_obj.dimensions = obj.dimensions
            lattice_obj.rotation_euler = obj.matrix_world.to_euler()

        lattice_obj.scale *=1.01 #increase lattice szize a bit to avoid potential with bounding verts

        # Make sure lattice works for flat objects (it stops functioning at scale 0)
        for index, name in enumerate(['points_u', 'points_v', 'points_w']):
            if -0.00001 < lattice_obj.scale[index] < 0.00001:
                lattice_obj.scale[index] = 1
                setattr(lattice_obj.data, name, 1)

    def set_vert_groups(self, obj):
        lattice_verts = obj.vertex_groups.new(name='HardOps_Lattice')
        group_idx = lattice_verts.index

        bm = bmesh.from_edit_mesh(obj.data)
        bm.verts.layers.deform.verify()

        bm_deform = bm.verts.layers.deform.active

        selected_vert = [v for v in bm.verts if v.select]

        if not selected_vert:
            return None

        for v in selected_vert:
            v[bm_deform][group_idx] = 1

        obj.update_from_editmode()


    def get_vert_coords(self, obj, context, matrix = Matrix()):
        if obj.type == 'MESH' and obj.mode == 'EDIT':
            coords = []
            self.set_vert_groups(obj)

            if self.modified :
                coords = self.mod_coord(context, obj, -1, matrix)

            else:
                group_idx = len(obj.vertex_groups) - 1
                coords = [ matrix @ v.co for v in obj.data.vertices if group_idx in [ vg.group for vg in v.groups]]

            return coords

        elif obj.type == 'GPENCIL' and obj.mode == 'EDIT_GPENCIL':
            lattice_verts = obj.vertex_groups.new(name='HardOps_Lattice')
            group_idx = lattice_verts.index

            selected_points = []

            for stroke in obj.data.layers.active.active_frame.strokes:
                selected_points.extend(p for p in stroke.points if p.select)

            if not selected_points:
                return None

            # Ideally this would be done without bpy.ops, but I couldn't figure out how to find working indices for the stroke points
            bpy.ops.gpencil.vertex_group_assign()

            # At this point in time, grease pencil modifiers are not taken into account when converting to curve, so self.modified is not supported here
            return [matrix @ p.co for p in selected_points]

        else:
            return None


    @staticmethod
    #return vertex coordinates from final vertex groups
    def mod_coord (context, obj, group_idx, matrix = Matrix()):
        depsgraph = context.evaluated_depsgraph_get()
        eval = obj.evaluated_get(depsgraph)
        me = eval.to_mesh()
        group_idx = len(obj.vertex_groups) - 1
        coords_b = [ matrix @ v.co for v in me.vertices if group_idx in [ vg.group for vg in v.groups]]
        eval.to_mesh_clear()

        return coords_b
