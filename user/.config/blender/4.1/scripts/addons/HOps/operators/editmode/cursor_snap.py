import bpy
import bmesh

from bpy.props import BoolProperty
from mathutils import Matrix, Vector, Euler


class HOPS_OT_CursorSnap(bpy.types.Operator):
    bl_idname = "hops.cursor_snap"
    bl_label = "Hops Cursor Snap"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Snap and rotate 3D coursor along selected item(s)"

    swap_face: BoolProperty(name="Swap Face normal", description="Use other face for normal orientation", default=False)

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'MESH' and context.mode == 'EDIT_MESH'

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "swap_face")

    def execute(self, context):

        obj = bpy.context.object
        me = obj.data
        bm = bmesh.from_edit_mesh(me)

        save_mode = bpy.context.scene.cursor.rotation_mode
        loc, rot, scl = obj.matrix_world.decompose()
        rot_matrix = rot.to_matrix().to_4x4()

        selected_edges = [e for e in bm.edges if e.select]
        if selected_edges:

            if len(selected_edges) == 1:
                selected_edge = selected_edges[0]
                v1, v2 = selected_edge.verts

                if self.swap_face:
                    if len(selected_edge.link_faces) == 2:
                        normal = rot_matrix @ selected_edge.link_faces[1].normal
                    else:
                        normal = rot_matrix @ selected_edge.link_faces[0].normal
                else:
                    normal = rot_matrix @ selected_edge.link_faces[0].normal

            else:
                bpy.ops.view3d.snap_cursor_to_selected()
                return {'CANCELLED'}
        else:
            selected_verts = [v for v in bm.verts if v.select]

            if len(selected_verts) == 2:
                v1, v2 = selected_verts
                linked_face = [x for x in v1.link_faces if x in v2.link_faces]
                if linked_face:
                    normal = rot_matrix @ linked_face[0].normal
                else:
                    bpy.ops.view3d.snap_cursor_to_selected()
                    return {'CANCELLED'}

            else:
                bpy.ops.view3d.snap_cursor_to_selected()
                return {'CANCELLED'}

        tangent = (rot_matrix @ v2.co - rot_matrix @ v1.co).normalized()
        cross = tangent.cross(normal)

        matrix = Matrix.Identity(3)
        matrix.col[0] = cross
        matrix.col[1] = tangent
        matrix.col[2] = normal

        quat = matrix.to_quaternion()
        selected = [obj.matrix_world @ v.co for v in bm.verts if v.select]
        loc = sum(selected, Vector()) / len(selected)
        bpy.context.scene.cursor.location = loc

        bpy.context.scene.cursor.rotation_mode = "QUATERNION"
        bpy.context.scene.cursor.rotation_quaternion = quat

        bpy.context.scene.cursor.rotation_mode = save_mode

        return {'FINISHED'}