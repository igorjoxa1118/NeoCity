import bpy, gpu, math, time, mathutils, random
from mathutils import Vector
from gpu_extras.batch import batch_for_shader
from bpy.props import StringProperty, BoolProperty
from ...ui_framework.graphics.draw import render_geo, draw_border_lines, render_quad, render_text
from ...ui_framework.utils.geo import get_blf_text_dims

from ... utility import addon
from ...utility import method_handler
from ...utils.blender_ui import get_dpi, get_dpi_factor


##############################################################################
# Global Data
##############################################################################

HANDLE = None     # The draw handle for shader
HOLD_DURATION = 2 # How long to show the uvs before fading
FADE_DURATION = 4 # How long to fade out for

class Data:
    '''Global communications from operator to ui modal.'''

    containers = []
    currently_drawing = False
    reset = False # Tell the modal to reset itself
    
    @staticmethod
    def reset_data():
        Data.containers = []


class Container:
    '''The drawing data container.'''

    def __init__(self):
        # Edges
        self.uv_loop_verts = []
        # Faces
        self.loop_tris = [] # Indices
        self.uv_points = [] # Points
        # Color
        self.color = addon.preference().color.Hops_UI_uv_color
        # Map Name
        self.name = ""

##############################################################################
# Launch Operator
##############################################################################

class HOPS_OT_Draw_UV_Launcher(bpy.types.Operator):
    bl_idname = "hops.draw_uv_launcher"
    bl_label = "UV Draw Launcher"
    bl_options = {"INTERNAL"}

    target_obj: StringProperty(
        name = 'Target UV Obj',
        description = 'The target object to draw uvs for',
        default = '')

    use_selected_meshes: BoolProperty(
        name = "Use selected mesh",
        default = False)

    use_selected_faces: BoolProperty(
        name = "Use the selected faces",
        default = False)
    
    use_tagged_faces: BoolProperty(
        name = "Use the tagged faces",
        default = False)

    show_all_and_highlight_sel: BoolProperty(
        name = "Show all and highlight selected uvs",
        default = False)

    hops_use: BoolProperty(
        name = "Use hops routes",
        default = False)

    def execute(self, context):
        
        # Not called properly
        if self.target_obj == '':
            if self.use_selected_meshes == False:
                return {'FINISHED'}
        
        # Draw all selected meshes
        # if self.use_selected_meshes == True:
        #     set_uv_draw_data_multi(context, self.use_selected_faces)
            
        # Valeriy sketch - Draw all selected meshes ----
        if self.use_selected_meshes == True:
            set_uv_draw_data_multi(context, self.use_selected_faces, self.use_tagged_faces, self.show_all_and_highlight_sel, hops_use=self.hops_use)
        # -----------------------------------
        
        # Single draw data
        else:
            if self.target_obj in bpy.data.objects.keys():
                obj = bpy.data.objects[self.target_obj]
                set_uv_draw_data_single(obj, self.use_selected_faces, self.use_tagged_faces, self.show_all_and_highlight_sel, hops_use=self.hops_use)

        if len(Data.containers) < 1:
            bpy.ops.hops.display_notification(info="No UV Maps Found")
            return {'FINISHED'}

        # Trigger modal to reset its timers and start fade over again
        if Data.currently_drawing == True:
            Data.reset = True
        # Call a fresh operator if none is currently running
        if Data.reset == False:
            bpy.ops.hops.draw_uvs('INVOKE_DEFAULT')

        return {'FINISHED'}

##############################################################################
# Utils for Launcher
##############################################################################

def set_uv_draw_data_single(obj, use_selected_faces=False, use_tagged_faces=False, show_all_and_highlight_sel=False, hops_use=False):
    '''Get a list of list vector 2 that represents the uv edges.  [[Vec2, Vec2, Vec2], ... ]'''

    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
    Data.reset_data()

    mesh = obj.data

    # Override to show all uvs and highlight selected
    use_selected_faces = not show_all_and_highlight_sel if show_all_and_highlight_sel else use_selected_faces 

    container = build_and_append_draw_data(mesh, use_selected_faces)
    Data.containers.append(container)

    # Layer on a selection layer
    if show_all_and_highlight_sel:
        for mesh in meshes:
            container = highlight_layer(mesh, hops_use=hops_use)
            if container != None:
                Data.containers.append(container)
                container.color = (random.uniform(.75, .875), random.uniform(.75, .875), random.uniform(.75, .875), 1)
                container.name = ""


def set_uv_draw_data_multi(context, use_selected_faces=False, use_tagged_faces=False, show_all_and_highlight_sel=False, hops_use=False):
    '''Get a list of list vector 2 that represents the uv edges.  [[Vec2, Vec2, Vec2], ... ]'''

    selected = context.selected_objects[:]
    in_mode = context.objects_in_mode[:]
    objects = set(selected + in_mode)

    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
    Data.reset_data()

    meshes = [obj.data for obj in objects if obj.type == 'MESH']
    for mesh in meshes:

        # Override to show all uvs and highlight selected
        use_selected_faces = not show_all_and_highlight_sel if show_all_and_highlight_sel else use_selected_faces

        container = build_and_append_draw_data(mesh, use_selected_faces, use_tagged_faces)
        if container != None:
            Data.containers.append(container)

    if len(Data.containers) > 1:
        for container in Data.containers:
            container.color = (random.uniform(.5, .25), random.uniform(.5, .25), random.uniform(.5, .25), 1)

    # Layer on a selection layer
    if show_all_and_highlight_sel:
        for mesh in meshes:
            container = highlight_layer(mesh, hops_use=hops_use)
            if container != None:
                Data.containers.append(container)
                container.color = (random.uniform(.75, .875), random.uniform(.75, .875), random.uniform(.75, .875), 1)
                container.name = ""


def build_and_append_draw_data(mesh, use_selected_faces=False, use_tagged_faces=False):
    '''Take the mesh and build the draw data. Returns the new draw data instance.'''

    # Validate
    if len(mesh.uv_layers) < 1:
        return None

    offset = addon.preference().ui.Hops_uv_padding * get_dpi_factor()
    scale = addon.preference().ui.Hops_uv_scale * get_dpi_factor()

    container = Container() # Create a new container
    mesh.update()
    mesh.calc_loop_triangles()

    # For drawing faces
    for tri in mesh.loop_triangles:
        # If only use selected faces
        if use_selected_faces:
            polygon = mesh.polygons[tri.polygon_index]
            if not polygon.select:
                continue

        container.loop_tris.append(tri.loops[:])

    uv_data = mesh.uv_layers.active.data 
    for ud in uv_data:
        point = ud.uv * scale
        point[0] += offset
        point[1] += offset
        container.uv_points.append(point)

    # For drawing edges
    uv_layer = mesh.uv_layers.active
    container.name = uv_layer.name # Get name
    
    uvs = [uv_loop.uv for uv_loop in uv_layer.data]
    for polygon in mesh.polygons:

        # If only use selected faces
        if use_selected_faces and not polygon.select:
            continue
            
        # Valeriy sketch ---- # If use tagged faces
        if use_tagged_faces and display_facemap and display_facemap.data[polygon.index].value == 0:
            continue
        # ---------------------------------

        points = [uvs[index] for index in polygon.loop_indices]
        for i in range(len(points)):
            point = [points[i][0] * scale + offset, points[i][1] * scale + offset]
            container.uv_loop_verts.append(point)
            if i < len(points) - 1:
                point = [points[i + 1][0] * scale + offset, points[i + 1][1] * scale + offset]
                container.uv_loop_verts.append(point)
            else:
                point = [points[-1][0] * scale + offset, points[-1][1] * scale + offset]
                point = [points[0][0] * scale + offset, points[0][1] * scale + offset]
                container.uv_loop_verts.append(point)

    return container


def highlight_layer(mesh, hops_use=False):

    # Validate
    if len(mesh.uv_layers) < 1:
        return None

    offset = addon.preference().ui.Hops_uv_padding * get_dpi_factor()
    scale = addon.preference().ui.Hops_uv_scale * get_dpi_factor()

    container = Container() # Create a new container

    # For drawing faces
    for tri in mesh.loop_triangles:
        polygon = mesh.polygons[tri.polygon_index]
        # Valeriy sketch: ------------------
        # It highlight selected faces
        if hops_use:
            if not polygon.select:
                continue

        container.loop_tris.append(tri.loops[:])

    uv_data = mesh.uv_layers.active.data
    for ud in uv_data:
        point = ud.uv * scale
        point[0] += offset
        point[1] += offset
        container.uv_points.append(point)

    # For drawing edges
    uv_layer = mesh.uv_layers.active
    container.name = uv_layer.name # Get name
    
    uvs = [uv_loop.uv for uv_loop in uv_layer.data]
    for polygon in mesh.polygons:

        if not polygon.select:
            continue

        points = [uvs[index] for index in polygon.loop_indices]
        for i in range(len(points)):
            point = [points[i][0] * scale + offset, points[i][1] * scale + offset]
            container.uv_loop_verts.append(point)
            if i < len(points) - 1:
                point = [points[i + 1][0] * scale + offset, points[i + 1][1] * scale + offset]
                container.uv_loop_verts.append(point)
            else:
                point = [points[-1][0] * scale + offset, points[-1][1] * scale + offset]
                point = [points[0][0] * scale + offset, points[0][1] * scale + offset]
                container.uv_loop_verts.append(point)

    return container

##############################################################################
# Drawing Modal
##############################################################################

class HOPS_OT_Draw_UV(bpy.types.Operator):
    '''UI Modal'''

    bl_idname = "hops.draw_uvs"
    bl_label = "Drawing for uvs"
    bl_options = {"INTERNAL"}

    def invoke(self, context, event):

        # Global
        Data.currently_drawing = True
        Data.reset = False

        # Props
        self.prefs = addon.preference()

        # Registers
        self.shader = Shader(context)
        self.timer = context.window_manager.event_timer_add(0.075, window=context.window)

        # Time
        self.start_time = time.time()
        self.time_diff = 0

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


    def modal(self, context, event):

        # Resest every thing if new drawing is initialized
        self.__check_for_reset()

        # Capture the difference in start time and now
        self.time_diff = time.time() - self.start_time

        # Tigger fade
        if self.time_diff >= HOLD_DURATION:
            self.shader.start_fade = True

        # Hold + Fade : completed
        if self.time_diff >= HOLD_DURATION + FADE_DURATION:
            self.__finished(context)
            return {'FINISHED'}

        # Redraw the viewport
        if context.area != None:
            context.area.tag_redraw()

        return {'PASS_THROUGH'}

    
    def __check_for_reset(self):
        '''Check if the draw should start over due to another op call.'''

        if Data.reset == True:
            Data.reset = False
            Data.currently_drawing = True
            self.start_time = time.time()
            self.time_diff = 0
            self.shader.reset()


    def __finished(self, context):
        '''Remove the timer, shader, and reset Data'''

        # Global
        Data.currently_drawing = False
        Data.reset = False
        Data.reset_data()

        # Unregister
        if self.timer != None:
            context.window_manager.event_timer_remove(self.timer)
        if self.shader != None:
            self.shader.destroy()
        if context.area != None:
            context.area.tag_redraw()

##############################################################################
# Draw Shader
##############################################################################

class Shader():

    def __init__(self, context):

        self.context = context
        self.prefs = addon.preference()
        self.start_fade = False
        self.__captured_start_fade_time = False
        self.__start_fade_time = 0
        color = self.prefs.color.Hops_UI_uv_color
        self.__og_alpha = color[3]
        self.__alpha = color[3]
        self.__setup_handle()

        # BG props
        self.bg_color = self.prefs.color.Hops_UI_cell_background_color
        self.br_color = self.prefs.color.Hops_UI_border_color

        offset = self.prefs.ui.Hops_uv_padding * get_dpi_factor()
        scale = self.prefs.ui.Hops_uv_scale * get_dpi_factor()
        self.padding = 15 * get_dpi_factor()
        far_left = offset - self.padding
        far_right = offset + scale + self.padding
        bottom = offset - self.padding
        top = offset + scale + self.padding

        self.top_left =  (far_left,  top)
        self.bot_left =  (far_left,  bottom)
        self.top_right = (far_right, top)
        self.bot_right = (far_right, bottom)

        # Text
        self.font_color = self.prefs.color.Hops_UI_text_color
        self.font_size = 14
        self.__full_alpha = 1

 
    def __setup_handle(self):
        '''Setup the draw handle for the UI'''

        global HANDLE
        if HANDLE == None:
            HANDLE = bpy.types.SpaceView3D.draw_handler_add(self.safe_draw, (self.context, ), "WINDOW", "POST_PIXEL")


    def safe_draw(self, context):
        method_handler(self.draw,
            arguments = (context,),
            identifier = 'UV Draw Shader',
            exit_method = self.destroy)


    def draw(self, context):
        '''Draw the UVs.'''

        self.__fade_alpha()

        # Validate
        if Data.containers == []:
            return

        self.__draw_bg()
        self.__draw_label()
        self.__draw_uvs()


    def __fade_alpha(self):

        if self.start_fade == True:
            # Capture fade start fade time
            if self.__captured_start_fade_time == False:
                self.__captured_start_fade_time = True
                self.__start_fade_time = time.time()

            # Fade alpha
            duration = FADE_DURATION
            diff = time.time() - self.__start_fade_time
            ratio = diff / duration
            self.__alpha = self.__og_alpha - (self.__og_alpha * ratio)
            
            self.__full_alpha = 1 - (1 * ratio) # Used with text to start at 1


    def __draw_bg(self):
        '''Draw the background behind the UVs.'''

        bg_color = (self.bg_color[0], self.bg_color[1], self.bg_color[2], self.__alpha)
        br_color = (self.br_color[0], self.br_color[1], self.br_color[2], self.__alpha)

        render_quad(
            quad=(self.top_left, self.bot_left, self.top_right, self.bot_right),
            color=bg_color)

        draw_border_lines(
            vertices=[self.top_left, self.bot_left, self.top_right, self.bot_right],
            width=2,
            color=br_color,
            format_lines=True)


    def __draw_label(self):
        '''Draw the text over the uvs box.'''

        color = (self.font_color[0], self.font_color[1], self.font_color[2], self.__full_alpha)
        label = "UV Display"
        label_x = get_blf_text_dims(label, self.font_size)[0]
        render_text(
            text=label,
            position=(self.top_left[0], self.top_left[1] + self.padding),
            size=self.font_size,
            color=color)

        # Draw the uv maps on the right hand side
        if len(Data.containers) > 1:
            y_offset = 0
            for container in Data.containers:
                if container.name == "": continue
                height = get_blf_text_dims(container.name, self.font_size)[1]
                color = (container.color[0] + .25, container.color[1] + .25, container.color[2] + .25, self.__full_alpha)
                render_text(
                    text=container.name,
                    position=(self.bot_right[0] + self.padding, self.bot_right[1] + y_offset),
                    size=self.font_size,
                    color=color)
                y_offset += height + self.padding
        elif len(Data.containers) == 1:
            container = Data.containers[0]
            if container.name == "": return
            color = (container.color[0] + .25, container.color[1] + .25, container.color[2] + .25, self.__full_alpha)
            render_text(
                text=container.name,
                position=(self.top_left[0] + self.padding + label_x, self.top_left[1] + self.padding),
                size=self.font_size,
                color=color)


    def __draw_uvs(self):
        '''Draw the mesh uvs.'''

        # Draw faces
        for container in Data.containers:
            color = (container.color[0], container.color[1], container.color[2], self.__alpha)
            render_geo(verts=container.uv_points, indices=container.loop_tris, color=color)

        # Draw edges
        for container in Data.containers:
            built_in_shader = 'UNIFORM_COLOR' if bpy.app.version[0] >=4 else '2D_UNIFORM_COLOR'
            shader = gpu.shader.from_builtin(built_in_shader)
            #Enable(GL_LINE_SMOOTH)
            gpu.state.blend_set('ALPHA')
            gpu.state.line_width_set(1)
            batch = batch_for_shader(shader, 'LINES', {"pos": container.uv_loop_verts})
            shader.bind()
            shader.uniform_float("color", (0, 0, 0,self.__alpha))
            batch.draw(shader)
            gpu.state.blend_set('NONE')
            del shader
            del batch


    def reset(self):
        '''Reset the shader for new drawing before being deleted.'''

        self.start_fade = False
        color = self.prefs.color.Hops_UI_uv_color
        self.__alpha = color[3]
        self.__full_alpha = 1
        self.__start_fade_time = 0
        self.__captured_start_fade_time = False


    def destroy(self):
        '''Remove the shader.'''

        global HANDLE
        if HANDLE != None:
            bpy.types.SpaceView3D.draw_handler_remove(HANDLE, "WINDOW")
            HANDLE = None
            Data.reset_data() # Extra clean up call

##############################################################################
# Remove On App Reload
##############################################################################

from bpy.app.handlers import persistent
@persistent
def remove_uv_draw_shader(dummy):
    global HANDLE
    if HANDLE != None:
        bpy.types.SpaceView3D.draw_handler_remove(HANDLE, "WINDOW")
        HANDLE = None

    # Reset draw data
    Data.reset_data()
    Data.currently_drawing = False
    Data.reset = False