import bpy, bmesh, mathutils, math, gpu, time, numpy
from gpu_extras.batch import batch_for_shader
from mathutils import Vector, Matrix
from bpy.props import EnumProperty, StringProperty, BoolProperty
from ... utility import method_handler
from ... utility import addon

##############################################################################
# Draw Data
##############################################################################

HANDLE_3D = None
EXTRA_CHECK = 0

class Data:
    # States
    mesh_modal_running = False
    restart_modal = False
    # Draw Data
    lines = []
    indices = []
    # Shader
    shader = None
    batch = None

    @staticmethod
    def reset_data():
        Data.lines = []
        Data.indices = []
        Data.shader = None
        Data.batch = None

    @staticmethod
    def reset_states():
        Data.mesh_modal_running = False

    @staticmethod
    def set_batch():
        if not len(Data.lines): return
        built_in_shader = 'UNIFORM_COLOR' if bpy.app.version[0] >=4 else '3D_UNIFORM_COLOR'
        Data.shader = gpu.shader.from_builtin(built_in_shader)
        Data.batch = batch_for_shader(Data.shader, 'LINES', {"pos": Data.lines}, indices = Data.indices if len(Data.indices) else None)

##############################################################################
# Launch Operator
##############################################################################

class HOPS_OT_Draw_Wire_Mesh_Launcher(bpy.types.Operator):
    bl_idname = "hops.draw_wire_mesh_launcher"
    bl_label = "UV Draw Launcher"
    bl_options = {"INTERNAL"}

    target: EnumProperty(
        name="Mesh Target",
        description="What meshes to target",
        items=[
            ('ACTIVE'  , "Active"  , "Use the active object"),
            ('SELECTED', "Selected", "Use all the selected objects"),
            ('NONE'    , "None"    , "Void the options")],
        default='NONE')

    object_name: StringProperty(
        name='Object Name',
        description='The object to use as the fade target',
        default="")

    omit_subd: BoolProperty(
        name="Omit Subd Wire",
        default=False)

    def execute(self, context):

        # Extra Check : If draw modal has not saved a time than just reset every thing manual
        if time.time() - EXTRA_CHECK > addon.preference().ui.Hops_extra_draw_time:
            Data.reset_data()
            Data.reset_states()
            Data.restart_modal = False

        if addon.preference().ui.Hops_extra_draw == False:
            return {'FINISHED'}

        if self.target == 'ACTIVE':
            capture_active_mesh_data(context, self.omit_subd)

        elif self.target == 'SELECTED':
            capture_selected_mesh_data(context, self.omit_subd)

        elif self.target == 'NONE':
            capture_obj_mesh_data(context, self.object_name, self.omit_subd)

        # Trigger modal to reset its timers and start fade over again
        if Data.mesh_modal_running == True:
            Data.restart_modal = True
        # Call a fresh operator if none is currently running
        else:
            bpy.ops.hops.draw_wire_mesh('INVOKE_DEFAULT')

        return {'FINISHED'}


def capture_active_mesh_data(context, omit_subd):
    Data.reset_data()

    obj = context.active_object
    
    subd_mod_map = {}
    if omit_subd:
        for mod in obj.modifiers:
            if mod.type == 'SUBSURF':
                subd_mod_map[mod] = mod.show_viewport
                mod.show_viewport = False

    depsgraph = context.evaluated_depsgraph_get()
    if type(obj) == bpy.types.Object:
        if obj.type == 'MESH':
            object_eval = obj.evaluated_get(depsgraph)
            mesh_eval = object_eval.data
            Data.lines, Data.indices = get_draw_data(mesh_eval, obj.matrix_world)

    if omit_subd:
        for mod, show in subd_mod_map.items():
            mod.show_viewport = show

    Data.set_batch()


def capture_selected_mesh_data(context, omit_subd):
    Data.reset_data()

    set_to_edit = False
    if context.mode == 'EDIT_MESH':
        set_to_edit = True
        bpy.ops.object.mode_set(mode='OBJECT')

    objs = [o for o in context.selected_objects if o.type == 'MESH']
    depsgraph = context.evaluated_depsgraph_get()

    if objs:
        coords = []
        index_list = []
        for obj in objs:

            subd_mod_map = {}
            if omit_subd:
                for mod in obj.modifiers:
                    if mod.type == 'SUBSURF':
                        subd_mod_map[mod] = mod.show_viewport
                        mod.show_viewport = False

            object_eval = obj.evaluated_get(depsgraph)
            mesh_eval = object_eval.data
            lines, indices = get_draw_data(mesh_eval, obj.matrix_world)
            coords.append(lines)
            index_list.append(indices)

            if omit_subd:
                for mod, show in subd_mod_map.items():
                    mod.show_viewport = show

        Data.lines = numpy.concatenate(coords, axis=0).tolist()

        #remap indices
        add_index = 0
        for i in range(1, len(index_list)):
            index_array = index_list[i]
            add_index += len(coords[i-1])
            index_array += add_index

        Data.indices = numpy.concatenate(index_list, axis=0).tolist()

    Data.set_batch()

    if set_to_edit:
        bpy.ops.object.mode_set(mode='OBJECT')


def capture_obj_mesh_data(context, obj_name, omit_subd):
    Data.reset_data()

    obj = None
    if obj_name in context.scene.objects.keys():
        temp = context.scene.objects[obj_name]
        if type(temp) == bpy.types.Object:
            if temp.type == 'MESH':
                obj = temp

    if not obj: return

    if context.mode == 'EDIT_MESH':
        obj.update_from_editmode()

    subd_mod_map = {}
    if omit_subd:
        for mod in obj.modifiers:
            if mod.type == 'SUBSURF':
                subd_mod_map[mod] = mod.show_viewport
                mod.show_viewport = False

    depsgraph = context.evaluated_depsgraph_get()
    object_eval = obj.evaluated_get(depsgraph)
    mesh_eval = object_eval.data
    Data.lines, Data.indices = get_draw_data(mesh_eval, obj.matrix_world)

    if omit_subd:
        for mod, show in subd_mod_map.items():
            mod.show_viewport = show

    Data.set_batch()


#numpy is too wordy for copying this all over
def get_draw_data(mesh, matrix):
    #vert coords
    length = len(mesh.vertices)
    coords = numpy.empty([length, 3], dtype = 'f')
    mesh.vertices.foreach_get('co', numpy.reshape(coords, length * 3))

    #add normal offset
    normals = numpy.empty([length, 3], dtype = 'f')
    mesh.vertices.foreach_get('normal', numpy.reshape(normals, length * 3))
    coords += normals * 0.002

    coords = numpy.append(coords, numpy.ones([length, 1], dtype='f'), axis=1)
    coords = coords @ numpy.array(matrix.transposed(), dtype='f')
    coords = numpy.delete(coords, [3], 1)
    coords = numpy.array(coords, dtype ='f', copy=False, order='C') # restore 'C' order so vbuffer is happy

    #indices
    length = len(mesh.edges)
    indices = numpy.empty([len(mesh.edges), 2], dtype='i', order='C' )
    mesh.edges.foreach_get('vertices', numpy.reshape(indices, length * 2))

    return coords, indices

##############################################################################
# Drawing Modal
##############################################################################

class HOPS_OT_Draw_Wire_Mesh(bpy.types.Operator):
    bl_idname = "hops.draw_wire_mesh"
    bl_label = "Drawing for mesh wire fade"
    bl_options = {"INTERNAL"}

    def invoke(self, context, event):
        # Internal check
        self.last_called = time.time()

        # Registers
        self.shader = Shader(context)
        self.timer = context.window_manager.event_timer_add(0.075, window=context.window)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


    def modal(self, context, event):

        Data.mesh_modal_running = True
        global EXTRA_CHECK
        EXTRA_CHECK = time.time()

        # Resest every thing if new drawing is initialized
        if Data.restart_modal:
            Data.restart_modal = False
            self.last_called = time.time()
            self.shader.reset(context)

        time_out = False
        if time.time() - self.last_called > addon.preference().ui.Hops_extra_draw_time:
            time_out = True

        # Reset everything
        if self.shader.fade_complete or time_out:
            self.__finished(context)
            return {'FINISHED'}

        # Redraw the viewport
        if context.area != None:
            context.area.tag_redraw()

        return {'PASS_THROUGH'}


    def __finished(self, context):
        '''Remove the timer, shader, and reset Data'''

        # Global
        Data.reset_data()
        Data.reset_states()

        # Unregister
        if self.timer != None:
            context.window_manager.event_timer_remove(self.timer)
        if self.shader != None:
            self.shader.destroy()
        if context.area != None:
            context.area.tag_redraw()


class Shader():

    def __init__(self, context):
        self.duration = addon.preference().ui.Hops_extra_draw_time
        self.reset(context)
        self.__setup_handle(context)


    def reset(self, context):
        '''Restart the shader.'''

        self.fade_complete = False
        self.start_time = time.time()
        color = addon.preference().color.Hops_wire_mesh
        self.alpha = color[3]
        self.og_alpha = color[3]
        self.color = (color[0], color[1], color[2], self.alpha)

        self.__setup_handle(context)


    def destroy(self):
        '''Remove the shader.'''

        global HANDLE_3D
        if HANDLE_3D != None:
            bpy.types.SpaceView3D.draw_handler_remove(HANDLE_3D, "WINDOW")
            HANDLE_3D = None

        Data.reset_data()
        Data.reset_states()


    def __setup_handle(self, context):
        '''Setup the draw handle for the UI'''

        global HANDLE_3D
        if HANDLE_3D == None:
            HANDLE_3D = bpy.types.SpaceView3D.draw_handler_add(self.__safe_draw_3d, (context, ), "WINDOW", "POST_VIEW")


    def __safe_draw_3d(self, context):
        method_handler(self.__draw_3d,
            arguments = (context,),
            identifier = 'Dice Fade Draw Shader 3D',
            exit_method = self.destroy)


    def __draw_3d(self, context):
        '''Draw the UVs.'''

        # Validate
        if not len(Data.lines) or not Data.shader or not Data.batch:
            self.fade_complete = True
            return

        # Lower alpha during fade
        self.__handle_fade()

        #Enable(GL_LINE_SMOOTH)
        gpu.state.blend_set('ALPHA')
        gpu.state.depth_test_set('LESS')
        #glDepthFunc(GL_LESS)
        gpu.state.line_width_set(3)

        # Draw wires
        Data.shader.bind()
        Data.shader.uniform_float("color", (self.color[0], self.color[1], self.color[2], self.alpha))
        Data.batch.draw(Data.shader)

        gpu.state.blend_set('NONE')
        gpu.state.depth_test_set('NONE')
        gpu.state.face_culling_set('NONE')
        gpu.state.depth_test_set('NONE')

        # Trigger exit
        if self.alpha <= 0:
            self.fade_complete = True


    def __handle_fade(self):
        '''Fade the alpha based on current time and Global DURATION variable'''

        diff = time.time() - self.start_time
        ratio = diff / self.duration
        self.alpha = self.og_alpha - (self.og_alpha * ratio)


##############################################################################
# Remove On App Reload
##############################################################################

from bpy.app.handlers import persistent
@persistent
def remove_mesh_draw_shader(dummy):
    global HANDLE_3D
    if HANDLE_3D != None:
        bpy.types.SpaceView3D.draw_handler_remove(HANDLE_3D, "WINDOW")
        HANDLE_3D = None

    Data.reset_data()
    Data.reset_states()
