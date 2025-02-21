import bpy
import bmesh
from ... utility import addon
from ...ui_framework.operator_ui import Master


def edit_bool_inset(context, keep_cutters, outset, thickness, use_swap, use_self, threshold, solver):
    def select( geom):
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

    mesh = context.active_object.data
    bm = bmesh.from_edit_mesh(mesh)

    geometry = bm.verts[:] + bm.edges[:] + bm.faces[:]
    visible = [g for g in geometry if not g.hide]

    target = [g for g in visible if not g.select]
    cutter = [g for g in visible if g.select]

    if keep_cutters:
        duplicate = bmesh.ops.duplicate(bm, geom=cutter)["geom"]
        hide(duplicate)

    inset = bmesh.ops.duplicate(bm, geom=target)["geom"]
    faces = [g for g in inset if type(g) == bmesh.types.BMFace]

    if outset:
        bmesh.ops.reverse_faces(bm, faces=faces)

    bmesh.ops.solidify(bm, geom=inset, thickness=float(thickness))
    bmesh.ops.inset_region(bm, faces=faces, thickness=0.00, depth=0.01, use_even_offset=True)

    hide(target)
    bmesh.update_edit_mesh(mesh)
    if bpy.app.version > (2, 83, 0):
        bpy.ops.mesh.intersect_boolean(operation='INTERSECT', use_swap=use_swap, use_self=use_self, threshold=threshold, solver=solver)
    else:
        bpy.ops.mesh.intersect_boolean(operation='INTERSECT', use_swap=use_swap, threshold=threshold)

    geometry = bm.verts[:] + bm.edges[:] + bm.faces[:]
    result = [g for g in geometry if not g.hide]

    reveal(target)
    select(result)
    operation = 'UNION' if outset else 'DIFFERENCE'
    if bpy.app.version > (2, 83, 0):
        bpy.ops.mesh.intersect_boolean(operation=operation, use_swap=use_swap, use_self=use_self, threshold=threshold, solver=solver)
    else:
        bpy.ops.mesh.intersect_boolean(operation=operation, use_swap=use_swap, threshold=threshold)

    if keep_cutters:
        geometry = bm.verts[:] + bm.edges[:] + bm.faces[:]
        deselect(geometry)
        reveal(duplicate)
        select(duplicate)

    bmesh.update_edit_mesh(mesh)
    return {'FINISHED'}


class HOPS_OT_EditBoolInset(bpy.types.Operator):
    bl_idname = "hops.edit_bool_inset"
    bl_label = "Hops Inset Boolean Edit Mode"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = """Inset Boolean in Edit Mode
LMB - Inset and remove cutters after use (DEFAULT)
LMB + Ctrl - Keep cutters after use
LMB + Shift - Outset"""

    keep_cutters: bpy.props.BoolProperty(
        name="Keep Cutters",
        description="Keep cutters after use",
        default=False)

    outset: bpy.props.BoolProperty(
        name="Outset",
        description="Use union instead of difference",
        default=False)

    thickness: bpy.props.FloatProperty(
        name="Thickness",
        description="How deep the inset should cut",
        default=0.10,
        min=0.00,
        soft_max=10.0,
        step=1,
        precision=3,)

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

        HOPS_OT_EditBoolInset.called_ui = False

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.mode == 'EDIT' and obj.type == 'MESH'

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        row = layout.row()
        row.prop(self, "keep_cutters")
        row.prop(self, "outset")
        layout.prop(self, "thickness")
        layout.separator()

        if bpy.app.version > (2, 83, 0):
            row = self.layout.row()
            row.prop(addon.preference().property, "boolean_solver", text='Solver', expand=True)
        layout.separator()
        layout.prop(self, 'use_swap')
        if bpy.app.version > (2, 83, 0):
            layout.prop(self, 'use_self')
        layout.prop(self, "keep_cutters")
        layout.prop(self, 'threshold')

    def invoke(self, context, event):
        self.keep_cutters = event.ctrl
        self.outset = event.shift
        return self.execute(context)

    def execute(self, context):

        # Operator UI
        if not HOPS_OT_EditBoolInset.called_ui:
            HOPS_OT_EditBoolInset.called_ui = True

            ui = Master()

            draw_data = [
                ["Inset Boolean"]]

            ui.receive_draw_data(draw_data=draw_data)
            ui.draw(draw_bg=addon.preference().ui.Hops_operator_draw_bg, draw_border=addon.preference().ui.Hops_operator_draw_border)

        return edit_bool_inset(context, self.keep_cutters, self.outset, self.thickness, self.use_swap, self.use_self, self.threshold, addon.preference().property.boolean_solver)
