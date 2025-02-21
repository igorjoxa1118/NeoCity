import bpy, gpu
from gpu_extras.batch import batch_for_shader
from ... utility import addon

# --- SHADER --- #
DRAW_HANDLER = None


class DATA:
    running = False
    obj = None
    obj_name = ""
    points = []

    shader = None
    
    tri_shader = None
    tri_batch = None
    tri_indices = []

    quad_shader = None
    quad_batch = None
    quad_indices = []

    ngon_shader = None
    ngon_batch = None
    ngon_indices = []

    @classmethod
    def reset_data(cls):
        cls.obj = None
        cls.obj_name = ""
        cls.points = []

        built_in_shader = 'UNIFORM_COLOR' if bpy.app.version[0] >=4 else '3D_UNIFORM_COLOR'
        cls.shader = gpu.shader.from_builtin(built_in_shader)

        cls.tri_batch = None
        cls.tri_indices = []

        cls.quad_batch = None
        cls.quad_indices = []

        cls.ngon_batch = None
        cls.ngon_indices = []

    @staticmethod
    def draw():
        #Enable(GL_LINE_SMOOTH)
        gpu.state.blend_set('ALPHA')
        gpu.state.depth_test_set('LESS')
        #glDepthFunc(GL_LESS)

        alpha = addon.preference().color.poly_debug_alpha

        if DATA.tri_batch:
            DATA.shader.bind()
            color = (1,.75,0, alpha)
            DATA.shader.uniform_float('color', color)
            DATA.tri_batch.draw(DATA.shader)
        if DATA.quad_batch:
            DATA.shader.bind()
            color = (1,1,1, alpha)
            DATA.shader.uniform_float('color', color)
            DATA.quad_batch.draw(DATA.shader)
        if DATA.ngon_batch:
            DATA.shader.bind()
            color = (1,0,0, alpha)
            DATA.shader.uniform_float('color', color)
            DATA.ngon_batch.draw(DATA.shader)


def poly_draw_shader():
    DATA.draw()


def register_shader():
    global DRAW_HANDLER
    if not DRAW_HANDLER:
        DRAW_HANDLER = bpy.types.SpaceView3D.draw_handler_add(poly_draw_shader, tuple(), "WINDOW", "POST_VIEW")
    DATA.running = True


def unregister_shader():
    global DRAW_HANDLER
    if DRAW_HANDLER:
        bpy.types.SpaceView3D.draw_handler_remove(DRAW_HANDLER, "WINDOW")
        DRAW_HANDLER = None
    DATA.running = False


from bpy.app.handlers import persistent
@persistent
def remove_poly_debug_shader(dummy):
    unregister_shader()

# --- DEPSGRAPH --- #

@persistent
def poly_data_updater(scene):

    # Validate
    if DATA.obj_name not in scene.objects:
        unregister_shader()
        DATA.reset_data()
        unregister_deps()
        return

    # New ref of same object
    DATA.obj = scene.objects[DATA.obj_name]

    # Check for updates
    if DATA.obj.mode == 'EDIT':
        DATA.obj.update_from_editmode()

    insert_draw_data(DATA.obj)


def register_deps():
    bpy.app.handlers.depsgraph_update_post.append(poly_data_updater)


def unregister_deps():
    if poly_data_updater in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(poly_data_updater)

# --- OPERATOR --- #

class HOPS_OT_Poly_Display_Debug(bpy.types.Operator):
    bl_idname = "hops.poly_debug_display"
    bl_label = "Poly Debug Display"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {"REGISTER", "UNDO"}
    bl_description = """Poly Debug Display
    
    Shows topological shader coloring for derived(actual) geometry.
    Recommended for topological management

    """

    def invoke(self, context, event):

        # Validate
        if not context.active_object: return {"FINISHED"}
        if context.active_object.type != 'MESH': return {"FINISHED"}

        obj = context.active_object
        obj.hops.is_poly_debug_display = not obj.hops.is_poly_debug_display

        # Turn off drawing
        if not obj.hops.is_poly_debug_display:
            unregister_obj()
            bpy.ops.hops.display_notification(info='Disabled Poly Debug Display')
            return {"FINISHED"}

        register_obj(obj)
        bpy.ops.hops.display_notification(info='Enabled Poly Debug Display')
        return {"FINISHED"}

# --- SETUP / CLEAR --- #

def register_obj(obj):
    insert_draw_data(obj)
    register_shader()
    register_deps()


def unregister_obj():
    unregister_shader()
    unregister_deps()
    DATA.reset_data()

# --- UTILS --- #

def insert_draw_data(obj):

    mat = obj.matrix_world
    mesh = obj.data
    mesh.calc_loop_triangles()

    DATA.reset_data()
    DATA.obj_name = obj.name
    DATA.points = [mat @ (v.co + v.normal * .002) for v in mesh.vertices]

    # --- Tris --- #
    tris = [poly for poly in mesh.polygons if len(poly.vertices) == 3]
    indexes = [poly.index for poly in tris]
    DATA.tri_indices = []
    DATA.tri_batch = None

    for triangle in mesh.loop_triangles:
        if triangle.polygon_index in indexes:
            DATA.tri_indices.append([mesh.vertices[v].index for v in triangle.vertices])

    if DATA.tri_indices and DATA.points:
        DATA.tri_batch = batch_for_shader(DATA.shader, 'TRIS', {'pos': DATA.points}, indices=DATA.tri_indices)

    # --- Quads --- #
    quads = [poly for poly in mesh.polygons if len(poly.vertices) == 4]
    indexes = [poly.index for poly in quads]
    DATA.quad_indices = []
    DATA.quad_batch = None

    for triangle in mesh.loop_triangles:
        if triangle.polygon_index in indexes:
            DATA.quad_indices.append([mesh.vertices[v].index for v in triangle.vertices])

    if DATA.quad_indices and DATA.points:
        DATA.quad_batch = batch_for_shader(DATA.shader, 'TRIS', {'pos': DATA.points}, indices=DATA.quad_indices)

    # --- Ngons --- #
    ngons = [poly for poly in mesh.polygons if len(poly.vertices) > 4]
    indexes = [poly.index for poly in ngons]
    DATA.ngon_indices = []
    DATA.ngon_batch = None

    for triangle in mesh.loop_triangles:
        if triangle.polygon_index in indexes:
            DATA.ngon_indices.append([mesh.vertices[v].index for v in triangle.vertices])

    if DATA.ngon_indices and DATA.points:
        DATA.ngon_batch = batch_for_shader(DATA.shader, 'TRIS', {'pos': DATA.points}, indices=DATA.ngon_indices)