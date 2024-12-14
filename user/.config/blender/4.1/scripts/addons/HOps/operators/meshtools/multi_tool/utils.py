import bpy, mathutils, math, gpu, bmesh, time
from math import cos, sin
from enum import Enum
from mathutils import Vector, Matrix
from gpu_extras.batch import batch_for_shader
from bpy.props import StringProperty
from bpy_extras import view3d_utils, mesh_utils
from bpy.app.handlers import persistent
from .... utility import addon
from .... utility.base_modal_controls import Base_Modal_Controls
from .... ui_framework.master import Master
from .... ui_framework.utils.mods_list import get_mods_list
from .... ui_framework.utils.geo import get_blf_text_dims
from .... ui_framework.graphics.draw import render_quad, render_geo, render_text, draw_border_lines, draw_2D_lines
from .... ui_framework.flow_ui.flow import Flow_Menu, Flow_Form
from .... utils.toggle_view3d_panels import collapse_3D_view_panels
from .... utils.modifiers import get_mod_copy, transfer_mod_data
from .... utils.cursor_warp import mouse_warp
from .... utils.modal_frame_drawing import draw_modal_frame
from .... utility import method_handler
from ....utility.screen import dpi_factor

# Selection utils
from .... utils.space_3d import get_3D_point_from_mouse, scene_ray_cast, ray_cast_objects


class Tool(Enum):
    SELECT = 0
    SPIN = 1
    MERGE = 2
    DISSOLVE = 3
    JOIN = 4
    KNIFE = 5


class Data:
    def __init__(self, context, event):
        # Mesh
        self.obj = None
        self.mesh = None
        self.bm = None

        # Undo system
        self.mesh_backups = [] # list of mesh names
        self.mesh_copy = None  # Current bm backup
        self.undo_index = 0    # Create a history number
        self.just_saved = False # For undo to remove working mesh and last saved

        self.__setup_mesh(context)

        # Original mesh
        self.revert_mesh_backup = self.mesh.copy()
        self.revert_mesh_backup.hops.hops_undo = True

        # Screen
        self.region = bpy.context.region
        self.rv3d = bpy.context.space_data.region_3d

        # Controls
        self.mouse_pos = (event.mouse_region_x, event.mouse_region_y)
        self.left_click_down = False
        self.mouse_accumulation = 0

        # Locked adjust state
        self.locked = False
        self.tool_mesh_backup = None


    def __setup_mesh(self, context):
        '''Construct all the tool data needed to get started.'''

        self.obj = context.active_object
        self.obj.update_from_editmode()
        self.mesh = self.obj.data
        # Create bmesh
        self.bm = bmesh.from_edit_mesh(self.mesh)
        # Create backup mesh : Save current : Store the key
        self.mesh_copy = self.mesh.copy()
        self.mesh_copy.hops.hops_undo = True
        self.mesh_backups.append(self.mesh_copy.name)

        
    def setup(self, context, event):
        # Locked adjust state
        self.locked = False
        self.tool_mesh_backup = None


    def update(self, context, event):
        
        # Mouse
        self.mouse_pos = (event.mouse_region_x, event.mouse_region_y)

        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            self.left_click_down = True
        elif event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            self.left_click_down = False

        self.__garbage_collect()


    def update_bmesh(self):
        # Update the mesh after copy was inserted
        bmesh.update_edit_mesh(self.mesh)
        self.mesh.calc_loop_triangles()

    # --- Save Utils --- #
    def undo(self):
        '''Use this to actually do an undo.'''

        # Validate mesh undo
        can_mesh_undo = False
        if len(self.mesh_backups) > 1:
            if self.mesh_backups[-1] in bpy.data.meshes.keys():
                can_mesh_undo = True
        
        # Delete all current geo
        bmesh.ops.delete(self.bm, geom=self.bm.verts, context='VERTS')

        # Get the new mesh
        if not can_mesh_undo:
            self.bm.from_mesh(self.revert_mesh_backup)
            bmesh.update_edit_mesh(self.mesh)
            return

        undo_mesh = bpy.data.meshes[self.mesh_backups[-1]]

        # Update bmesh
        self.bm.from_mesh(undo_mesh)
        bmesh.update_edit_mesh(self.mesh)

        # Remove item from backups
        bpy.data.meshes.remove(undo_mesh)
        self.mesh_backups.pop(-1)

        # Update the object data
        self.obj.update_from_editmode()

        # Get the new mesh backup (this is the one behind the poped item)
        self.mesh_copy = bpy.data.meshes[self.mesh_backups[-1]]
        self.bm = bmesh.from_edit_mesh(self.mesh)

        self.undo_index -= 1

        if self.just_saved:
            self.just_saved = False
            self.undo()


    def save(self):
        '''This will save the mesh changes.'''

        # Add increment
        self.undo_index += 1
        # Update the current mesh
        bmesh.update_edit_mesh(self.mesh)
        # Update the object data
        self.obj.update_from_editmode()
        # Get a copy of the refreshed data block
        self.mesh_copy = self.mesh.copy()
        self.mesh_copy.hops.hops_undo = True
        self.mesh_backups.append(self.mesh_copy.name)
        self.just_saved = True


    def __garbage_collect(self):
        '''Removes mesh backup objects when history is to long.'''

        error_out = 0
        while len(self.mesh_backups) > 15:
            if error_out > 50: break
            error_out += 1
            key = self.mesh_backups[0]
            if key not in bpy.data.meshes.keys(): continue
            mesh = bpy.data.meshes[key]
            bpy.data.meshes.remove(mesh)
            self.mesh_backups.remove(key)

    # --- Modal Adjust Utils --- #
    def modal_mesh_start(self):
        '''Used to save a mesh backup for the modal adjustments mode.'''

        self.locked = True
        self.mouse_accumulation = 0

        # Update the current mesh
        bmesh.update_edit_mesh(self.mesh)

        # Write data blocks
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.mode_set(mode='EDIT')

        # Capture refreshed data block
        self.bm = bmesh.from_edit_mesh(self.mesh)

        # Get a copy of the refreshed data block
        self.tool_mesh_backup = self.mesh.copy()
        self.tool_mesh_backup.hops.hops_undo = True


    def modal_mesh_cancel(self):
        '''Cancel the modal mesh and remove it / restore from starting state.'''

        self.locked = False
        bmesh.ops.delete(self.bm, geom=self.bm.verts, context='VERTS')
        # Reload bmesh based on mesh backup
        self.bm.from_mesh(self.tool_mesh_backup)
        bpy.data.meshes.remove(self.tool_mesh_backup)
        self.tool_mesh_backup = None


    def modal_mesh_confirm(self):
        '''Accept the modal mesh and resume from new state.'''

        self.locked = False
        bpy.data.meshes.remove(self.tool_mesh_backup)
        self.tool_mesh_backup = None
        bpy.ops.mesh.select_all(action='DESELECT')
        self.save()


    def modal_mesh_update(self, context, event, with_mouse_warp=False):
        '''Delete current geo and restore back to modal mesh start.'''

        if with_mouse_warp:
            mouse_warp(context, event)

        # Remove all mesh data
        bmesh.ops.delete(self.bm, geom=self.bm.verts, context='VERTS')
        # Reload bmesh based on mesh backup
        self.bm.from_mesh(self.tool_mesh_backup)


    def cancelled_exit(self):
        '''Revert the bmesh.'''

        # Delect all the current geo
        bmesh.ops.delete(self.bm, geom=self.bm.verts, context='VERTS')
        # Load the revert mesh into the bmesh
        self.bm.from_mesh(self.revert_mesh_backup)
        # Update the bmesh into the starting mesh
        bmesh.update_edit_mesh(self.mesh)
        # Remove the backup revert mesh
        bpy.data.meshes.remove(self.revert_mesh_backup)


    def confirmed_exit(self):
        '''Remove backup data.'''

        # Remove the mesh backup
        bpy.data.meshes.remove(self.revert_mesh_backup)


    def shut_down(self):
        '''Shut down modal.'''

        # Remove undo history
        for key in self.mesh_backups:
            if key in bpy.data.meshes.keys():
                mesh = bpy.data.meshes[key]
                bpy.data.meshes.remove(mesh)

        # Remove the tool mesh backup
        if self.tool_mesh_backup != None:
            bpy.data.meshes.remove(self.tool_mesh_backup)
        bmesh.update_edit_mesh(self.mesh)


def raycast_onto_object(context, event, data):
    '''Raycast into scene and only return if hit active object. Returns dictionary'''

    ray_data = {
        'result' : None,
        'location' : None,
        'normal' : None,
        'index' : None,
        'object' : None,
        'matrix' : None}

    # result, location, normal, index, object, matrix = scene_ray_cast(context, event)
    result, location, normal, index, object, matrix = ray_cast(context, event, context.active_object)

    if object == data.obj:
        ray_data['result'] = result
        ray_data['location'] = location
        ray_data['normal'] = normal
        ray_data['index'] = index
        ray_data['object'] = object
        ray_data['matrix'] = matrix

    return ray_data


def get_2d_point_from_3d(point3d, data):
    '''Get 2D Screen point from mouse.'''

    if data.rv3d is not None and data.region is not None:
        return view3d_utils.location_3d_to_region_2d(data.region, data.rv3d, point3d)


def get_vert_under_mouse(context, event, data):
    '''Get the closest vert to the mouse point.'''

    ray_data = raycast_onto_object(context, event, data)
    if ray_data['result'] == None:
        return None

    closest_vert = None
    check_distance = -1

    for index, vert in enumerate(data.bm.verts):
        distance = ray_data['location'] - (data.obj.matrix_world @ vert.co)
        distance = abs(distance.magnitude)

        if index == 0:
            closest_vert = vert
            check_distance = distance
            continue

        if distance < check_distance:
            closest_vert = vert
            check_distance = distance

    return closest_vert


def get_edge_under_mouse(context, event, data, op, as_copy=False, ret_with_ray_data=False):
    '''Gets edge under the mouse.'''

    ray_data = raycast_onto_object(context, event, data)
    if ray_data['result'] == None:
        if ret_with_ray_data == True:
            return None, None

        return None

    ray_loc = ray_data['location']
    ray_normal = ray_data['normal']

    data.bm.faces.ensure_lookup_table()
    data.bm.edges.ensure_lookup_table()
    data.bm.verts.ensure_lookup_table()
    
    # Get the closest edge
    closest_edge = None
    check_distance = -1
    edges = [e for e in data.bm.edges]
    for index, edge in enumerate(edges):

        # Take ray location and get closest point to edge
        vert_one_loc = data.obj.matrix_world @ edge.verts[0].co
        vert_two_loc = data.obj.matrix_world @ edge.verts[1].co

        # Get the closest point to the edge and a percent from the first vert to the point
        point, percent = mathutils.geometry.intersect_point_line(ray_loc, vert_one_loc, vert_two_loc)

        # Validate
        if math.isnan(percent):
            continue

        # Get distance from point and ray location
        distance = ray_loc - point
        distance = distance.magnitude

        # Save initial edge and distance
        if index == 0:
            closest_edge = edge
            check_distance = distance
            continue
        
        # Edge is not under mouse
        if percent > 1:
            continue
        elif percent < 0:
            continue

        # Check if the next edge is closer to ray poit
        if distance < check_distance:
            closest_edge = edge
            check_distance = distance

    # For drawing knife
    # TODO: GET THIS OUT
    if op.tool == Tool.KNIFE:
        op.knife.draw_points = []
        for vert in closest_edge.verts:
            op.knife.draw_points.append(data.obj.matrix_world @ vert.co)

    # Return edge
    if as_copy == False:

        # Return edge and ray data
        if ret_with_ray_data == True:
            return closest_edge, ray_data

        # Return edge only
        return closest_edge

    # Return simple data copy version
    else:
        return get_edge_copy(closest_edge, data)


def get_edge_copy(edge, data):
    '''Return a value copy of the edge and vert locations associated.'''

    class Edge:
        def __init__(self):
            self.verts = []

    copied_edge = Edge()
    for vert in edge.verts:
        pos = data.obj.matrix_world @ vert.co
        copied_edge.verts.append( pos )

    return copied_edge


def ray_cast(context, event, obj):
    vec2d = event.mouse_region_x, event.mouse_region_y
    origin = view3d_utils.region_2d_to_origin_3d(context.region, context.space_data.region_3d, vec2d)
    direction = view3d_utils.region_2d_to_vector_3d(context.region, context.space_data.region_3d, vec2d)
    return ray_cast_objects(context, origin, direction, [obj], evaluated=False)

# --- Drawing Utils --- #

def draw_gizmo_circle(data, gizmo_radius):
    width = 1
    color = (0,0,0,1)
    segments = 64
    vertices = []
    for i in range(segments):
        index = i + 1
        angle = i * 3.14159 * 2 / segments
        x = math.cos(angle) * gizmo_radius
        y = math.sin(angle) * gizmo_radius
        x += data.mouse_pos[0]
        y += data.mouse_pos[1]
        vertices.append((x, y))

    first_vert = vertices[0]
    vertices.append(first_vert)

    built_in_shader = 'UNIFORM_COLOR' if bpy.app.version[0] >=4 else '2D_UNIFORM_COLOR'
    shader = gpu.shader.from_builtin(built_in_shader)
    #Enable(GL_LINE_SMOOTH)
    gpu.state.blend_set('ALPHA')
    gpu.state.line_width_set(width)
    batch = batch_for_shader(shader, 'LINE_STRIP', {"pos": vertices})
    shader.bind()
    shader.uniform_float("color", color)
    batch.draw(shader)
    gpu.state.blend_set('NONE')

    del shader
    del batch


def draw_modal_mesh_label_2d(context, loc, offset, gizmo_radius, additional=""):
    draw_modal_frame(context)

    # Draw label
    label = "OFFSET  "
    dims = get_blf_text_dims(label, 16)[0]
    text_pos = (loc[0] + gizmo_radius, loc[1] + gizmo_radius)
    render_text(text=label, position=text_pos, size=16, color=(0,1,1,1))

    # Draw label
    cancel_pos = (loc[0] + gizmo_radius, loc[1] + gizmo_radius + (25 * dpi_factor()))
    render_text(text="Press C for cancel", position=cancel_pos, size=16, color=(0,1,1,1))

    # Draw offset
    offset_color = (0,1,0,1) if offset > 0 else (1,0,0,1)
    offset_text = f"{offset:.3f} {additional}"
    text_pos = (loc[0] + gizmo_radius + dims, loc[1] + gizmo_radius)
    render_text(text=offset_text, position=text_pos, size=18, color=offset_color)

# --- Handlers --- #

@persistent
def garbage_collection(dummy):
    for m in bpy.data.meshes:
        if m.hops.hops_undo: bpy.data.meshes.remove(m)


def register_multitool():
    bpy.app.handlers.undo_post.append(garbage_collection)


def unregister_multitool():
    if garbage_collection in bpy.app.handlers.undo_post:
        bpy.app.handlers.undo_post.remove(garbage_collection)



















