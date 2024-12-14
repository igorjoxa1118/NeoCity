import bpy, math, bmesh, mathutils
from mathutils import Vector, Matrix, Quaternion
from bpy.props import EnumProperty, IntProperty
from ... utility import addon
from ...utility import math as hops_math


solvers = [
    ("CORNER", "Corner", "", 1),
]


class HOPS_OT_Face_Solver(bpy.types.Operator):
    bl_idname = "hops.face_solver"
    bl_label = "Face Solver"
    bl_description = """Face Solver
    Solve faces for various retopo redirects
    Press H for help
    """
    bl_options = {"REGISTER", "UNDO"}

    solver : EnumProperty(items=solvers, name='Solvers', description='Algos', default='CORNER')\

    corner : IntProperty(name='Corner', description='Offset starting corner', default=1, min=1, max=6)

    @classmethod
    def poll(cls, context):
        if context.mode == 'EDIT_MESH':
            if context.active_object and context.active_object.type == 'MESH':
                return True
        return False


    def draw(self, layout):

        layout = self.layout
        layout.use_property_split = True

        col = layout.column()

        col.prop(self, 'solver')

        col.separator_spacer()

        if self.solver == 'CORNER':
            col.prop(self, 'corner')


    def execute(self, context):

        obj = context.active_object
        obj.update_from_editmode()
        mesh = obj.data
        bm = bmesh.from_edit_mesh(mesh)

        valid = True

        if self.solver == 'CORNER':
            valid = corner_solver(bm, self.corner - 1)

        bmesh.update_edit_mesh(mesh)
        if valid:
            return {'FINISHED'}
        return {'CANCELLED'}

# --- SOLVER : CORNER --- #

def corner_solver(bm, corner=0):

    # Face        
    face = bm.faces.active
    if not face:
        bpy.ops.hops.display_notification(info="No Active Face")
        return False

    # Clear Tags
    remove_tags(face)

    # Edges
    loops = connected_loops(face.loops[0])
    if len(loops) == 4:
        if corner > 3:
            corner = 3
        quad_corner(bm, face, loops, corner)

    elif len(loops) == 6:
        hexagon_corner(bm, face, loops, corner)

    else:
        bpy.ops.hops.display_notification(info="Supported : 4 Edges / 6 Edges")
        return False

    return True


def hexagon_corner(bm, face, loops, corner=0):
    
    # Center
    points = [v.co for l in loops for v in l.edge.verts ]
    bb = hops_math.coords_to_bounds(points)
    coords = (hops_math.coords_to_center(bb),)

    cv1 = loops[corner].link_loop_next.link_loop_next.link_loop_next.vert

    v1 = loops[corner].link_loop_next.vert
    v2 = loops[corner].link_loop_prev.vert

    split_face, split_loop = bmesh.utils.face_split(face, v1, v2, coords)
    cv2 = split_loop.link_loop_next.vert

    # Join
    verts = [cv1, cv2]
    bmesh.ops.connect_verts(bm, verts=verts)

    bpy.ops.mesh.select_all(action='DESELECT')
    split_face.select = True
    cv1.select = True


def quad_corner(bm, face, loops, corner=0):

    # Center
    coords = (face.calc_center_median(),)

    # Split
    split_verts = []
    i1 = corner
    i2 = corner + 1 if corner + 1 <= len(loops) - 1 else 0
    
    if i2 == 0:
        v1 = loops[i2].link_loop_prev.link_loop_prev.vert
    else:
        v1 = loops[i2].link_loop_next.link_loop_next.vert

    for i, loop in enumerate(loops):
        if i == i1 or i == i2:
            edge, vert = bmesh.utils.edge_split(loop.edge, loop.vert, .5)
            split_verts.append(vert)

    # Create Face
    split_face, split_loop = bmesh.utils.face_split(face, split_verts[0], split_verts[1], coords)
    v2 = split_loop.link_loop_next.vert

    # Join
    verts = [v1, v2]
    bmesh.ops.connect_verts(bm, verts=verts)

    bpy.ops.mesh.select_all(action='DESELECT')

    loop = v2.link_loops[0].link_loop_radial_next if i2 == 0 else v2.link_loops[0].link_loop_next
    loop.face.select = True
    bm.faces.active = loop.face

# --- UTILS --- #

def connected_loops(loop):
    loops = []
    while True:
        if loop in loops:
            break
        else:
            loops.append(loop)
            loop = loop.link_loop_next
            if not loop: break
    return loops


def remove_tags(face):
    for e in face.edges:
        e.tag = False
    for v in face.verts:
        v.tag = False

