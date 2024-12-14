import bpy
from bpy.props import FloatProperty, BoolProperty
from ... utility import addon
from .. sculpt.sculpt_tools import exit_sculpt

class HOPS_OT_VoxelizerOperator(bpy.types.Operator):
    bl_idname = "view3d.voxelizer"
    bl_label = "Object Mode Voxelization"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = '''Voxelizes Objects From Object Mode

    Ctrl - Set voxel size
    
    '''
    # voxsize: FloatProperty(name="Vox Size", description="Size Of Voxelization", default=0.1, min=0.01, max=10)

    @classmethod
    def poll(cls, context):
        return getattr(context.active_object, "type", "") == "MESH"

    def draw(self, context):
        layout = self.layout

        data = context.active_object.data
        layout.prop(data, 'remesh_voxel_size', text='')

        # box = layout.box()

        # box.prop(self, 'voxsize', text="Voxelization Size")

    def invoke(self, context, event):
        if bpy.context.active_object.mode == 'SCULPT':
            if context.sculpt_object.use_dynamic_topology_sculpting:
                bpy.ops.sculpt.dynamic_topology_toggle('INVOKE_DEFAULT')
                in_sculpt = True
            else:
                in_sculpt = False
        else:
            in_sculpt = False

        data = context.active_object.data
        if event.ctrl:
            bpy.ops.object.voxel_size_edit('INVOKE_DEFAULT')
            if in_sculpt:
                bpy.ops.sculpt.dynamic_topology_toggle('INVOKE_DEFAULT')
        else:
            try:
                voxelize(context.active_object, data.remesh_voxel_size)
                bpy.ops.hops.draw_wire_mesh_launcher('INVOKE_DEFAULT', target='SELECTED')
                bpy.ops.hops.display_notification(info=f"Voxelized: {data.remesh_voxel_size:.3f}")
                if in_sculpt:
                    bpy.ops.sculpt.dynamic_topology_toggle('INVOKE_DEFAULT')
            except:
                bpy.ops.hops.display_notification(info=f"Nice Try")
        return {"FINISHED"}

def voxelize(object, voxsize):
    if bpy.context.active_object.mode == 'SCULPT':
        in_sculpt = True
        exit_sculpt()
    else:
        in_sculpt = False
    bpy.ops.object.convert(target='MESH')
    bpy.context.object.data.remesh_voxel_size = voxsize
    bpy.ops.object.voxel_remesh()
    if in_sculpt:
        bpy.ops.object.mode_set(mode='SCULPT') 
