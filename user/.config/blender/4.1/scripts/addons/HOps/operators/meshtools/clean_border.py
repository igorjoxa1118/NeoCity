import bpy, mathutils, math, bmesh
from math import cos, sin
from mathutils import Vector, Matrix, Quaternion, geometry
from ... utility import math as hops_math


DESC = """Clean Border
Select faces
Cleans vertices along face islands"""


class HOPS_OT_Clean_Border(bpy.types.Operator):
    bl_idname = "hops.clean_border"
    bl_label = "Clean Border"
    bl_description = DESC
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if context.active_object:
            if context.active_object.type == 'MESH':
                if context.active_object.mode == 'EDIT':
                    return True
        return False


    def execute(self, context):

        for obj in context.selected_editable_objects:
            solver(obj)

        return {'FINISHED'}


def solver(obj):
    obj.update_from_editmode()
    mesh = obj.data
    bm = bmesh.from_edit_mesh(mesh)

    bpy.ops.mesh.region_to_loop()
    verts = [v for v in bm.verts if v.select]

    dissolve_verts = []

    for vert in verts:
        
        is_boundary_vert = False
        for loop in vert.link_loops:
            if loop.edge.is_boundary:
                is_boundary_vert = True
                break
            
        if not is_boundary_vert:
            
            if len(vert.link_loops) > 2: continue
            
            if len(vert.link_edges) < 4:
                if vert not in dissolve_verts:
                    dissolve_verts.append(vert)
        
        else:
            if len(vert.link_edges) < 3:
                if vert not in dissolve_verts:
                    dissolve_verts.append(vert)

    bmesh.ops.dissolve_verts(bm, verts=dissolve_verts)
    bmesh.update_edit_mesh(mesh)