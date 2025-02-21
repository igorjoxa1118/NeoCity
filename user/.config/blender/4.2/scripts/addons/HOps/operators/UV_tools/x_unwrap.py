import bpy, bmesh
from bpy.props import FloatProperty, BoolProperty, EnumProperty
from ... utils.bmesh import selectSmoothEdges
from ... utility import addon
from ...ui_framework.operator_ui import Master
from math import radians, degrees, pi

class HOPS_OT_XUnwrapF(bpy.types.Operator):
    bl_idname = "hops.xunwrap"
    bl_label = "XUnwrap"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = """Unwrap mesh using automated unwrapping and draw UVs in the 3d view
    CTRL - Only display UVs (No Unwrap)"""

    angle_limit:      FloatProperty(name="Angle limit", default=45, min=0.0, max=90)
    rmargin:          FloatProperty(name="Margin", default=0.0002, min=0.0, max=1)
    user_area_weight: FloatProperty(name="User area weight", default=0.03, min=0.0, max=1)
    bweight_as_seams: BoolProperty(default=False, )
    crease_as_seams:  BoolProperty(default=False, description='Convert crease to seeams')
    sharp_as_seams:   BoolProperty(default=True, description="Use marked sharp edges")
    called_ui = False
    rmethod:          EnumProperty(
        name='Method',
        items = [
            ('SMART', 'Smart', 'Smart UV project'),
            ('NORMAL', 'Normal', 'Setup mesh for normal map compatibility'),
        ],
    )


    def __init__(self):
        HOPS_OT_XUnwrapF.called_ui = False

    @classmethod
    def poll(cls, context):
        selected = context.selected_objects
        object = context.active_object
        if object is None: return False
        if object.mode == "OBJECT" and any(obj.type == "MESH" for obj in selected):
            return True


    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.prop(self, 'rmethod')
        box.prop(self, "angle_limit")
        box.prop(self, "rmargin")

        if self.rmethod == 'SMART':
            box.prop(self, "user_area_weight")

        elif self.rmethod == 'NORMAL':
            box.prop(self, 'sharp_as_seams', text="Use sharp edges")
            box.prop(self, 'crease_as_seams', text="Convert crease to seams")
            box.prop(self, 'bweight_as_seams', text="Convert bevel weight to seams")


    def invoke(self, context, event):

        # Call UV Draw op only
        if event.ctrl == True:
            bpy.ops.hops.draw_uv_launcher(use_selected_meshes=True, hops_use=True)
            return {"FINISHED"}

        self.execute(context)
        #hops_draw_uv()
        self.report({'INFO'}, F'UVed at Angle Of : {self.angle_limit}')
        return {"FINISHED"}


    def parameter_getter(self):
        return self.rmargin


    def execute(self, context):

        self.og_active = context.active_object
        self.og_selection = context.selected_objects

        self.lazy_selection(context)

        bpy.ops.object.mode_set(mode='EDIT')

        if self.rmethod == 'NORMAL':
            for obj in bpy.context.selected_objects:
                bpy.context.view_layer.objects.active = obj
                me = obj.data
                if addon.preference().behavior.auto_smooth:
                    me.use_auto_smooth = True
                    me.auto_smooth_angle = pi

                bm = bmesh.from_edit_mesh(me)

                if bpy.app.version[0] >= 4:
                    crease = bm.edges.layers.float.get('crease_edge')
                    if crease is None:
                        crease = bm.edges.layers.float.new('crease_edge')
                else:
                    crease = bm.edges.layers.crease.verify()

                if bpy.app.version[0] >= 4:
                    bevel = bm.edges.layers.float.get('bevel_weight_edge')
                    if bevel is None:
                        bevel = bm.edges.layers.float.new('bevel_weight_edge')
                else:
                    bevel = bm.edges.layers.bevel_weight.verify()

                for e in bm.edges:
                    angle = degrees(e.calc_face_angle(0.0))
                    e.seam = bool((angle > self.angle_limit) + (e[crease] * self.crease_as_seams) + (e[crease] * self.crease_as_seams) + (e[bevel] * self.bweight_as_seams) + ((not e.smooth) * self.sharp_as_seams))
                    e.smooth = not e.seam

                bpy.ops.mesh.select_all(action='SELECT')

            bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=self.rmargin)

        elif self.rmethod == 'SMART':
            if bpy.app.version <= (2, 90, 0):
                bpy.ops.uv.smart_project(angle_limit=radians(self.angle_limit), island_margin=self.rmargin, user_area_weight=self.user_area_weight)

            elif bpy.app.version > (2, 90, 0):
                bpy.ops.uv.smart_project(angle_limit=radians(self.angle_limit), island_margin=self.rmargin, area_weight=self.user_area_weight, correct_aspect=False, scale_to_bounds=False)

        bpy.ops.object.mode_set(mode='OBJECT')

        # Operator UI
        if HOPS_OT_XUnwrapF.called_ui == False:
            HOPS_OT_XUnwrapF.called_ui = True

            objs_unwrapped = len([obj for obj in context.selected_objects if obj.type == 'MESH'])

            ui = Master()
            ui.receive_draw_data(
                draw_data=[
                    ["Auto Unwrap"],
                    ["Unwrapped", objs_unwrapped],
                    ["Angle", self.angle_limit],
                    ["Weight", self.user_area_weight],
                    ["Margin", self.rmargin]])
            ui.draw(draw_bg=addon.preference().ui.Hops_operator_draw_bg, draw_border=addon.preference().ui.Hops_operator_draw_border)

        # Call UV Draw op
        bpy.ops.hops.draw_uv_launcher(use_selected_meshes=True, hops_use=True)

        self.set_selection_back(context)
        return {"FINISHED"}


    def lazy_selection(self, context):
        '''Make sure context selections are good.'''

        active = context.active_object
        mesh_objs = [obj for obj in context.selected_objects if obj.type == 'MESH']

        bpy.ops.object.select_all(action='DESELECT')

        for obj in mesh_objs:
            obj.select_set(True)

        context.view_layer.objects.active = active if active in mesh_objs else mesh_objs[0]


    def set_selection_back(self, context):
        '''Set the selection back to the original'''

        bpy.ops.object.select_all(action='DESELECT')
        context.view_layer.objects.active = self.og_active
        for obj in self.og_selection:
            obj.select_set(True)
