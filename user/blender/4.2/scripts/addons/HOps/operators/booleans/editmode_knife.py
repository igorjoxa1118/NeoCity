import bpy
import bmesh
from ... utility import addon
from ...ui_framework.operator_ui import Master


def edit_bool_knife(context, keep_cutters, knife_project, cut_through=True):
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

    if knife_project:
        selected = context.selected_objects
        active = context.active_object
        other = [o for o in selected if o != active]
        mesh = active.data

        for obj in selected:
            obj.select_set(False)

        if sum(mesh.count_selected_items()):
            bpy.ops.mesh.separate(type='SELECTED')
            new = context.selected_objects[0]
            new.select_set(True)

            for mod in new.modifiers:
                mod.show_viewport = mod.show_viewport and mod.show_in_editmode

            edge_split = new.modifiers.new("Edge Split", 'EDGE_SPLIT')
            edge_split.use_edge_angle = True
            edge_split.split_angle = 0.0

            bpy.ops.mesh.knife_project(cut_through=cut_through)

            if keep_cutters:
                bm = bmesh.from_edit_mesh(mesh)

                select(new.data.vertices)
                select(new.data.edges)
                select(new.data.polygons)

                bm.from_mesh(new.data)
                bmesh.update_edit_mesh(mesh)

            bpy.data.objects.remove(new, do_unlink=True)

        if other:
            # kick other objects out of edit mode as they're unselected
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.mode_set(mode='EDIT')

            for obj in other:
                obj.select_set(True)
                edge_split = obj.modifiers.new("Edge Split", 'EDGE_SPLIT')
                edge_split.use_edge_angle = True
                edge_split.split_angle = 0.0

            bpy.ops.mesh.knife_project(cut_through=cut_through)

            for obj in other:
                obj.select_set(True)
                edge_split = obj.modifiers[-1]
                obj.modifiers.remove(edge_split)

            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.mode_set(mode='EDIT')

        for obj in selected:
            obj.select_set(True)

    else:
        mesh = context.active_object.data
        bm = bmesh.from_edit_mesh(mesh)

        bpy.ops.mesh.split()

        geometry = bm.verts[:] + bm.edges[:] + bm.faces[:]
        cutter = [g for g in geometry if g.select]

        if keep_cutters:
            duplicate = bmesh.ops.duplicate(bm, geom=cutter)["geom"]
            hide(duplicate)

        if 'solver' in bpy.types.BooleanModifier.bl_rna.properties:
            bpy.ops.mesh.intersect(mode='SELECT_UNSELECT', separate_mode='CUT', threshold=1e-06, solver='FAST')
        else:
            bpy.ops.mesh.intersect(mode='SELECT_UNSELECT', separate_mode='CUT', threshold=1e-06)

        geometry = bm.verts[:] + bm.edges[:] + bm.faces[:]
        new = [g for g in geometry if g.select]

        deselect(geometry)
        select(cutter)

        bpy.ops.mesh.select_linked()

        cutter = [g for g in geometry if g.select]
        bmesh.ops.delete(bm, geom=cutter, context='VERTS')

        if keep_cutters:
            reveal(duplicate)
            select(duplicate)
        else:
            geometry = bm.verts[:] + bm.edges[:] + bm.faces[:]
            select([g for g in new if g in geometry])

        bmesh.update_edit_mesh(mesh)

    return {'FINISHED'}


class HOPS_OT_EditBoolKnife(bpy.types.Operator):
    bl_idname = "hops.edit_bool_knife"
    bl_label = "Hops Knife Boolean Edit Mode"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = """Knife Boolean in Edit Mode
LMB - Remove cutters after use (DEFAULT)
LMB + Ctrl - Keep cutters after use
LMB + Shift - Use knife project"""

    keep_cutters: bpy.props.BoolProperty(
        name="Keep Cutters",
        description="Keep cutters after use",
        default=False)

    knife_project: bpy.props.BoolProperty(
        name="Knife Project",
        description="Use knife project instead of boolean intersect",
        default=False)

    cut_through: bpy.props.BoolProperty(
        name="Cut Through",
        description="Cut through",
        default=True)

    called_ui = False

    def __init__(self):

        HOPS_OT_EditBoolKnife.called_ui = False

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.mode == 'EDIT' and obj.type == 'MESH'

    def draw(self, context):
        row = self.layout.row()
        row.prop(self, "keep_cutters")
        row.prop(self, "knife_project")

        if self.knife_project:
            row.prop(self, "cut_through")


    def invoke(self, context, event):
        self.keep_cutters = event.ctrl
        self.knife_project = event.shift
        return self.execute(context)

    def execute(self, context):

        # Operator UI
        if not HOPS_OT_EditBoolKnife.called_ui:
            HOPS_OT_EditBoolKnife.called_ui = True

            ui = Master()

            draw_data = [
                ["Knife Boolean"]]

            ui.receive_draw_data(draw_data=draw_data)
            ui.draw(draw_bg=addon.preference().ui.Hops_operator_draw_bg, draw_border=addon.preference().ui.Hops_operator_draw_border)

        return edit_bool_knife(context, self.keep_cutters, self.knife_project, cut_through=self.cut_through)
