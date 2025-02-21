import bpy
import bmesh
from ... utility import addon
from ...ui_framework.operator_ui import Master


def edit_bool_difference(context, keep_cutters, use_swap, use_self, threshold, solver):
    def select(geom):
        for g in geom:
            g.select = True

    def deselect(geom):
        for g in geom:
            g.select = False

    def reveal(geom):
        for g in geom:
            g.hide = False

    def hide(geom):
        for g in geom:
            g.hide = True

    if keep_cutters:
        mesh = context.active_object.data
        bm = bmesh.from_edit_mesh(mesh)
        geometry = bm.verts[:] + bm.edges[:] + bm.faces[:]
        cutter = [g for g in geometry if g.select]
        duplicate = bmesh.ops.duplicate(bm, geom=cutter)["geom"]
        hide(duplicate)
        bmesh.update_edit_mesh(mesh)

    if bpy.app.version > (2, 83, 0):
        bpy.ops.mesh.intersect_boolean(operation='DIFFERENCE', use_swap=use_swap, use_self=use_self, threshold=threshold, solver=solver)
    else:
        bpy.ops.mesh.intersect_boolean(operation='DIFFERENCE', use_swap=use_swap, threshold=threshold)

    if keep_cutters:
        geometry = bm.verts[:] + bm.edges[:] + bm.faces[:]
        deselect(geometry)
        reveal(duplicate)
        select(duplicate)
        bmesh.update_edit_mesh(mesh)

    return {'FINISHED'}


class HOPS_OT_EditBoolDifference(bpy.types.Operator):
    bl_idname = "hops.edit_bool_difference"
    bl_label = "Hops Difference Boolean Edit Mode"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = """Difference Boolean in Edit Mode
LMB - Remove cutters after use (DEFAULT)
LMB + Ctrl - Keep cutters after use"""

    keep_cutters: bpy.props.BoolProperty(
        name="Keep Cutters",
        description="Keep cutters after use",
        default=False)

    use_swap: bpy.props.BoolProperty(
        name="Swap",
        description="Swaps selection after boolean",
        default=False)

    use_self: bpy.props.BoolProperty(
        name="Self",
        description="Use on self",
        default=False)

    threshold: bpy.props.FloatProperty(
        name="Threshold",
        description="Threshold",
        default=0.001)

    called_ui = False

    def __init__(self):

        HOPS_OT_EditBoolDifference.called_ui = False


    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.mode == 'EDIT' and obj.type == 'MESH'

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        if bpy.app.version > (2, 83, 0):
            row = self.layout.row()
            row.prop(addon.preference().property, "boolean_solver", text='Solver', expand=True)
        layout.separator()
        layout.prop(self, 'use_swap')
        if bpy.app.version > (2, 83, 0):
            layout.prop(self, 'use_self')
        layout.prop(self, "keep_cutters")
        layout.prop(self, 'threshold')

    def execute(self, context):

        # Operator UI
        if not HOPS_OT_EditBoolDifference.called_ui:
            HOPS_OT_EditBoolDifference.called_ui = True

            ui = Master()

            draw_data = [
                ["Difference Boolean"]]

            ui.receive_draw_data(draw_data=draw_data)
            ui.draw(draw_bg=addon.preference().ui.Hops_operator_draw_bg, draw_border=addon.preference().ui.Hops_operator_draw_border)

        return edit_bool_difference(context, self.keep_cutters, self.use_swap, self.use_self, self.threshold, addon.preference().property.boolean_solver)
