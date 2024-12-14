import bpy
from bpy.props import BoolProperty
import bpy.utils.previews

# Clean Off Bevel and Sharps In Edit Mode


class HOPS_OT_UnsharpOperatorE(bpy.types.Operator):
    """
    Removes marking from edges.

    """
    bl_idname = "hops.clean1_objects"
    bl_label = "UnsharpBevelE"
    bl_options = {'REGISTER', 'UNDO'}

    clearsharps: BoolProperty(default=True)
    clearbevel: BoolProperty(default=True)
    clearcrease: BoolProperty(default=True)

    def draw(self, context):
        layout = self.layout

        box = layout.box()
        # DRAW YOUR PROPERTIES IN A BOX
        box.prop(self, 'clearsharps', text="Clear Sharps")
        box.prop(self, 'clearbevel', text="Clear Bevels")
        box.prop(self, 'clearcrease', text="Clear Crease")

    def execute(self, context):

        if self.clearsharps is True:
            bpy.ops.mesh.mark_sharp(clear=True)
        if self.clearbevel is True:
            bpy.ops.transform.edge_bevelweight(value=-1)
        if self.clearcrease is True:
            bpy.ops.transform.edge_crease(value=-1)

        return {'FINISHED'}
