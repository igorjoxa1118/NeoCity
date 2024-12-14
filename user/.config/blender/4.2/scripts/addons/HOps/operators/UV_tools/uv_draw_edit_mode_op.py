import bpy

op_desc = '''Display the UVS
Click : Display all UVS WITH Highlight Selected
Shift : Display all UVS NO Highlight
CTRL  : Only show Selected UVS
'''

class HOPS_OT_Draw_UV_Edit_Mode(bpy.types.Operator):
    bl_idname = "hops.draw_uv_edit_mode"
    bl_label = "UV Draw Edit Mode"
    bl_description = op_desc

    def invoke(self, context, event):
        
        mode = context.mode

        if event.shift:
            bpy.ops.hops.draw_uv_launcher(use_selected_meshes=True, hops_use=True)
        elif event.ctrl:
            bpy.ops.hops.draw_uv_launcher(use_selected_meshes=True, use_selected_faces=True, show_all_and_highlight_sel=False, hops_use=True)
        else:
            bpy.ops.hops.draw_uv_launcher(use_selected_meshes=True, use_selected_faces=True, show_all_and_highlight_sel=True, hops_use=True)

        if mode == 'EDIT_MESH':
            if context.mode != 'EDIT_MESH':
                bpy.ops.object.mode_set(mode='EDIT')

        return {'FINISHED'}