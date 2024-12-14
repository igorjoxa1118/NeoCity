import bpy, copy, mathutils, math
from enum import Enum
from ..operator import knife as op_knife_intersect
from .... utils.objects import set_active

class Mode(Enum):
    DICE_3D = 0
    DICE_2D = 1
    DICE_LINE = 2

# --- KNIFE UTILS --- #

def knife_project(context, obj, cutter, axis):
    perspective = copy.copy(context.region_data.view_perspective)
    camera_zoom = copy.copy(context.region_data.view_camera_zoom)
    distance = copy.copy(context.region_data.view_distance)
    location = copy.copy(context.region_data.view_location)
    rotation = copy.copy(context.region_data.view_rotation)

    view = {'X': 'FRONT', 'Y': 'TOP', 'Z': 'RIGHT'}[axis]

    set_active(cutter)
    bpy.ops.view3d.view_axis(type=view, align_active=True)
    set_active(obj)
    context.region_data.view_perspective = 'ORTHO'
    context.region_data.update()

    selected = cutter.select_get()
    cutter.select_set(False)

    bpy.ops.object.mode_set(mode='EDIT')
    cutter.select_set(True)
    bpy.ops.mesh.knife_project(cut_through=True)
    bpy.ops.object.mode_set(mode='OBJECT')
    cutter.select_set(selected)

    context.region_data.view_perspective = perspective
    context.region_data.view_camera_zoom = camera_zoom
    context.region_data.view_distance = distance
    context.region_data.view_location = location
    context.region_data.view_rotation = rotation
    context.region_data.update()

    if perspective == 'ORTHO':
        axis = [int(math.degrees(a)) for a in mathutils.Quaternion(rotation).to_euler()]
        if axis   == [90,  0,  90]: bpy.ops.view3d.view_axis(type='RIGHT')
        elif axis == [90,  0,   0]: bpy.ops.view3d.view_axis(type='FRONT')
        elif axis == [0,   0,   0]: bpy.ops.view3d.view_axis(type='TOP')
        elif axis == [90,  0, -90]: bpy.ops.view3d.view_axis(type='LEFT')
        elif axis == [90,  0, 180]: bpy.ops.view3d.view_axis(type='BACK')
        elif axis == [180, 0,   0]: bpy.ops.view3d.view_axis(type='BOTTOM')


def knife_intersect(context):
    bpy.ops.object.mode_set(mode='OBJECT')
    op_knife_intersect(context, knife_project=False)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')


def prepare(obj, cutter):
    set_active(obj, select=True, only_select=True)
    bpy.ops.object.mode_set(mode='OBJECT')
    cutter.select_set(True)


def remove(obj):
    mesh = obj.data
    bpy.data.objects.remove(obj)
    bpy.data.meshes.remove(mesh)