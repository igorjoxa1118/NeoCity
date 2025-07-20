from typing import List

import bpy
from bpy.types import Object, Modifier
from bpy_extras import view3d_utils
from mathutils import Matrix, Vector, Euler
import gpu
import math
import os
from os.path import join, dirname, realpath
from .constants import *

from .independant_helper import get_addon_preferences
from .math_functions import *
from ..bevels import *
from .independant_helper import *

from ..t3dn_bip import previews

import time

init_pref = False

def time_tracker(pre=None, text=None, init=False):
    if init:
        return time.time()
    t = time.time()
    return t

image_size = (32, 32)
# Chargement des icones blender
fluent_icons_collection = {}
fluent_icons_loaded = False
fluent_bpy_utils_previews = None
icons_dir = join(dirname(realpath(__file__)))

def load_icons(load_texture=True):
    global fluent_icons_collection
    global fluent_icons_loaded
    global fluent_bpy_utils_previews

    def read_loop(icons_dir, load_texture) :
        global fluent_icons_collection
        count = 0
        for f in os.listdir(icons_dir):
            count += 1
            f_name = f.split('.')[0]
            f_extension = f.split('.')[1]
            if f_extension == 'png':
                if load_texture:
                    img = bpy.data.images.load(join(icons_dir, f))
                    fluent_icons_collection[f_name]['texture'] = gpu.texture.from_image(img)
                    bpy.data.images.remove(img)
                else:
                    img_preview = fluent_bpy_utils_previews.load_safe(f_name, join(icons_dir, f), 'IMAGE')
                    fluent_icons_collection[f_name] = {'previews': img_preview, 'texture': None}

    if fluent_icons_loaded:
        return fluent_icons_collection

    parent_dir = os.path.join(dirname(realpath(__file__)), os.pardir)
    icons_dir = join(os.path.abspath(parent_dir), 'UI')
    icons_dir = join(icons_dir, 'icons')

    if fluent_bpy_utils_previews is None:
        fluent_bpy_utils_previews = previews.new(max_size=(256, 256))

    read_loop(icons_dir, load_texture)

    try:
        #charge les icones des grilles
        parent_dir = os.path.join(dirname(realpath(__file__)), os.pardir)
        power_trip_dir = join(os.path.abspath(parent_dir), 'power_trip')
        power_trip_grid_dir = join(power_trip_dir, 'grids')
        power_trip_grid_icons_dir = join(power_trip_grid_dir, 'icons')
        read_loop(power_trip_grid_icons_dir, load_texture)
    except:pass

    try:
        #charge les icones des visses
        parent_dir = os.path.join(dirname(realpath(__file__)), os.pardir)
        power_trip_dir = join(os.path.abspath(parent_dir), 'power_trip')
        power_trip_screw_dir = join(power_trip_dir, 'screws')
        power_trip_screw_icons_dir = join(power_trip_screw_dir, 'icons')
        read_loop(power_trip_screw_icons_dir, load_texture)
    except:pass

    fluent_icons_loaded = load_texture

    return fluent_icons_collection


def clear_icons():
    # global fluent_icons_loaded
    # global fluent_icons_collection
    # global fluent_bpy_utils_previews
    # bpy.utils.previews.remove(fluent_bpy_utils_previews)
    # fluent_icons_collection.clear()
    # fluent_icons_loaded = False
    global fluent_icons_collection
    global fluent_icons_loaded
    global fluent_bpy_utils_previews
    previews.remove(fluent_bpy_utils_previews)
    fluent_icons_collection.clear()
    fluent_icons_loaded = False


def make_oops(msg, title, icon):
    def oops(self, context):
        for m in msg:
            self.layout.label(text=m)

    bpy.context.window_manager.popup_menu(oops, title=title, icon=icon)


def obj_ray_cast(obj, mouse_x, mouse_y):
    # get the context arguments
    scene = bpy.context.scene
    region = bpy.context.region
    rv3d = bpy.context.region_data
    coord = (mouse_x, mouse_y)

    # get the ray from the viewport and mouse
    view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
    ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)

    ray_target = ray_origin + view_vector

    matrix = obj.matrix_world.copy()
    # get the ray relative to the object
    matrix_inv = matrix.inverted()
    ray_origin_obj = matrix_inv @ ray_origin
    ray_target_obj = matrix_inv @ ray_target
    ray_direction_obj = ray_target_obj - ray_origin_obj

    # cast the ray
    success, location, normal, face_index = obj.ray_cast(ray_origin_obj, ray_direction_obj)

    return {
        'success': success,
        'hit': location,
        'normal': normal,
        'face_index': face_index,
        'ray_origin': ray_origin,
        'obj': obj
    }


def cast_local2global(dico):
    if dico['success']:
        obj = dico['obj']
        matrix = obj.matrix_world
        converted = {
            'success': dico['success'],
            'hit': matrix @ dico['hit'],
            'normal': matrix.to_3x3() @ dico['normal'],
            'face_index': dico['face_index'],
            'ray_origin': dico['ray_origin'],
            'obj': dico['obj']
        }
        return converted
    else:
        print('Cast fail, impossible to convert.')


def click_on(mouse_x, mouse_y, ignore=False, search=['MESH'], ignore_display=['BOUNDS', 'WIRE']):
    best_length_squared = -1.0
    best_obj = None

    visible_list = bpy.context.visible_objects
    depsgraph = bpy.context.evaluated_depsgraph_get()

    for obj in visible_list:
        if obj.type in search and not obj.hide_get() and obj.display_type not in ignore_display and obj != ignore:
            try:
                eval_obj = obj.evaluated_get(depsgraph)
                result = obj_ray_cast(eval_obj, mouse_x, mouse_y)
            except:
                result = {'success': False}

            if result['success']:
                length_squared = (obj.matrix_world @ result['hit'] - result.get('ray_origin')).length_squared
                if best_obj is None or length_squared < best_length_squared:
                    best_length_squared = length_squared
                    best_obj = obj

    return best_obj


def local_to_global_co(obj, co_local):
    co_global = obj.matrix_world.copy() @ co_local
    return co_global


def co3d_to_co2d(co_3d):
    region = bpy.context.region
    rv3d = bpy.context.region_data
    co_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, co_3d)
    return co_2d


def make_plane():
    vertices = []
    for i in range(4):
        vertices.append((0, 0, 0))
    edges = [(0, 1), (1, 2), (2, 3), (3, 0)]
    faces = [(0, 1, 2, 3)]
    mesh_data = bpy.data.meshes.new("bool_cube_data")
    mesh_data.from_pydata(vertices, edges, faces)
    mesh_data.update()
    bool_obj = bpy.data.objects.new("bool_cube", mesh_data)
    bpy.context.scene.collection.objects.link(bool_obj)
    return bool_obj


def make_prism():
    verts = [(0, 0, 0), (0, 0, 0)]
    edges = [(0, 1)]
    mesh_data = bpy.data.meshes.new("bool_obj_data")
    mesh_data.from_pydata(verts, edges, [])
    mesh_data.update()
    bool_obj = bpy.data.objects.new("bool_obj", mesh_data)
    bpy.context.scene.collection.objects.link(bool_obj)
    bpy.context.view_layer.objects.active = bool_obj

    v_group_radius = bool_obj.vertex_groups.new()
    v_group_radius.name = 'radius'
    v_group_radius.add([1], 1, 'ADD')
    v_group_inner_radius = bool_obj.vertex_groups.new()
    v_group_inner_radius.name = 'inner_radius'
    v_group_inner_radius.add([0], 1, 'ADD')

    # creation des modifiers
    bpy.ops.object.mode_set(mode='OBJECT')
    radius = bool_obj.modifiers.new(name=fluent_modifiers_name['radius'], type='DISPLACE')
    radius.show_in_editmode = True
    radius.show_on_cage = True
    radius.direction = 'X'
    radius.vertex_group = 'radius'
    radius.strength = 0
    radius.mid_level = 0
    radius.show_expanded = False

    inner_radius = bool_obj.modifiers.new(name=fluent_modifiers_name['inner_radius'], type='DISPLACE')
    inner_radius.show_in_editmode = True
    inner_radius.show_on_cage = True
    inner_radius.direction = 'X'
    inner_radius.vertex_group = 'inner_radius'
    inner_radius.strength = 0
    inner_radius.mid_level = 0
    inner_radius.show_expanded = False

    resolution = bool_obj.modifiers.new(name=fluent_modifiers_name['screw'], type='SCREW')
    resolution.merge_threshold = 0.0001
    resolution.use_merge_vertices = True
    resolution.use_smooth_shade = True
    resolution.steps = 16
    resolution.render_steps = 16
    resolution.use_normal_calculate = True
    resolution.use_normal_flip = True
    resolution.show_expanded = False

    decimate = bool_obj.modifiers.new(name=fluent_modifiers_name['decimate'], type='DECIMATE')
    decimate.decimate_type = 'DISSOLVE'
    decimate.angle_limit = 0.00174533

    return bool_obj


def make_shape(max=500):
    vertices = []
    edges = []
    faces = []
    for i in range(max):
        vertices.append((0, 0, 0))
    for i in range(max - 1):
        edges.append((i, i + 1))
    face = [i for i in range(max)]
    faces.append(face)
    mesh_data = bpy.data.meshes.new("bool_cube_data")
    mesh_data.from_pydata(vertices, edges, faces)
    mesh_data.update()
    bool_obj = bpy.data.objects.new("bool_cube", mesh_data)
    bpy.context.scene.collection.objects.link(bool_obj)
    return bool_obj


def make_sphere():
    verts = [(0, 0, 0)]
    mesh_data = bpy.data.meshes.new("bool_obj_data")
    mesh_data.from_pydata(verts, [], [])
    mesh_data.update()
    bool_obj = bpy.data.objects.new("bool_obj", mesh_data)
    bpy.context.scene.collection.objects.link(bool_obj)
    bpy.context.view_layer.objects.active = bool_obj

    v_group_radius = bool_obj.vertex_groups.new()
    v_group_radius.name = 'radius'
    v_group_radius.add([1], 1, 'ADD')
    v_group_inner_radius = bool_obj.vertex_groups.new()
    v_group_inner_radius.name = 'inner_radius'
    v_group_inner_radius.add([0], 1, 'ADD')

    # creation des modifiers
    radius_mod = bool_obj.modifiers.new(type='DISPLACE', name=fluent_modifiers_name['radius'])
    radius_mod.direction = 'Z'
    radius_mod.strength = 0

    resolution_mod = bool_obj.modifiers.new(type='SCREW', name=fluent_modifiers_name['screw'])
    resolution_mod.axis = 'Y'
    resolution_mod.angle = math.radians(180)
    resolution_mod.use_merge_vertices = True
    resolution_mod.steps = resolution_mod.render_steps = auto_bevel_segments(displace=radius_mod)

    screw_mod = bool_obj.modifiers.new(type='SCREW', name=fluent_modifiers_name['screw_2'])
    screw_mod.angle = math.radians(360)
    screw_mod.use_smooth_shade = True
    screw_mod.use_normal_calculate = True
    screw_mod.use_merge_vertices = True
    screw_mod.merge_threshold = 0.0001
    screw_mod.steps = screw_mod.render_steps = resolution_mod.steps * 2

    return bool_obj

def enter_value(valeur, event):
    # saisie des valeurs
    common_events = {'NUMPAD_MINUS': '-', 'MINUS': '-', 'NUMPAD_PERIOD': '.', 'PERIOD': '.', 'COMMA': '.',
                     'BACK_SPACE': "BACK_SPACE"}
    numpad_events = {'NUMPAD_0': '0', 'NUMPAD_1': '1', 'NUMPAD_2': '2', 'NUMPAD_3': '3', 'NUMPAD_4': '4',
                     'NUMPAD_5': '5', 'NUMPAD_6': '6', 'NUMPAD_7': '7', 'NUMPAD_8': '8', 'NUMPAD_9': '9'}
    normal_events = {'ZERO': '0', 'ONE': '1', 'TWO': '2', 'THREE': '3', 'FOUR': '4', 'FIVE': '5', 'SIX': '6',
                     'SEVEN': '7', 'EIGHT': '8', 'NINE': '9'}
    if bpy.context.preferences.inputs.use_emulate_numpad:
        # That way we do not override the camera switching hotkeys
        # BUG: For some reason, pressing 4 and 6 don't orbit...
        all_events = {**common_events, **numpad_events}
    else:
        all_events = {**common_events, **normal_events, **numpad_events}
    if event['value'] == 'PRESS' and event['type'] in all_events.keys():
        if valeur == 'None':
            valeur = ''
        valeur_to_append = all_events.get(event['type'], '')
        if valeur_to_append == 'BACK_SPACE':
            valeur = valeur[:-1]
        elif valeur_to_append == '-':
            # NOTE: It would be great to be able to negate the value without having to manually input everything
            #       Valeur is 'None' unfortunately, we need a new parameter or pass the real value
            #       Passing the real value is the best thing to do, we can clear it over here anyway!
            if len(valeur) > 0 and valeur[0] == '-':
                valeur = valeur[1:]
            else:
                valeur = '-' + valeur
        else:
            valeur += all_events.get(event['type'], '')
    return valeur


def enter_value_validation(value, event):
    try:
        if event['value'] == 'PRESS' and event['type'] in {'NUMPAD_ENTER', 'RET'}:
            return [True, float(value)]
        else:
            return [False]
    except:
        return [False]


def get_modifier_values(mod):
    properties = [p.identifier for p in mod.bl_rna.properties if not p.is_readonly]
    properties_values = [getattr(mod, p) for p in properties]
    return {'properties': properties, 'properties_values': properties_values, 'show_render': mod.show_render,
            'show_viewport': mod.show_viewport, 'name': mod.name}


def set_modifier_value(mod, properties_dico, avoid=[]):
    i = 0
    for prop in properties_dico['properties']:
        if prop not in avoid:
            setattr(mod, prop, properties_dico['properties_values'][i])
        i += 1
    mod.show_render = properties_dico['show_render']
    mod.show_viewport = properties_dico['show_viewport']


def adjustment_value(modifier, enter_value):
    if enter_value == 'None':
        return str(round(modifier, 3))
    else:
        return enter_value


def snap_slider_value(val, gap):
    return val // gap * gap


def snap_horizontal_vertical(x, y, xx, yy):
    delta_x = math.fabs(x - xx)
    delta_y = math.fabs(y - yy)

    if delta_y != 0:
        snap = delta_x / delta_y
    else:
        snap = 2

    if snap < 0.5:
        return [x, yy]
    else:
        return [xx, y]


def snap_45(x, y, xx, yy):
    a = xx - x + y
    b = -(xx - x) + y
    if math.fabs(a - yy) < math.fabs(b - yy):
        y_snaped = a
    else:
        y_snaped = b

    return [xx, y_snaped]


def snap_455(x1, y1, x2, y2, get_equation=False):
    if x2 != x1:
        angle = math.degrees(math.atan((y2 - y1) / (x2 - x1)))
        if 0 < angle < 90:
            f1 = {'a': 1, 'b': y1 - 1 * x1}
            if not get_equation:
                return [x2, f1['a'] * x2 + f1['b']]
            else:
                return f1
        elif -90 < angle < 0:
            f2 = {'a': -1, 'b': y1 - (-1) * x1}
            if not get_equation:
                return [x2, f2['a'] * x2 + f2['b']]
            else:
                return f2
    return False


def snap_other_vertices(obj, x, y):
    distance_max = 1000
    snaped_coords = False
    for v in obj.data.vertices:
        d_x = math.fabs(v.co.x - x)
        d_y = math.fabs(v.co.y - y)
        if (d_x < distance_max or d_y < distance_max) and (d_x > 0.05 or d_y > 0.05):
            if d_x < d_y:
                snaped_coords = [v.co.x, y]
            else:
                snaped_coords = [x, v.co.y]
            distance_max = min([d_x, d_y])
    if snaped_coords:
        return snaped_coords
    else:
        return [x, y]


def snap(ox, oy, x, y, only=None):
    if not only:
        s_hv = snap_horizontal_vertical(ox, oy, x, y)
        diff_02 = distance(x, y, 0, s_hv[0], s_hv[1], 0)
        s_45 = snap_45(ox, oy, x, y)
        diff_03 = distance(x, y, 0, s_45[0], s_45[1], 0)
        closest = min([diff_02, diff_03])
        if closest == diff_02:
            return s_hv
        elif closest == diff_03:
            return s_45
    elif only == '45':
        return snap_45(ox, oy, x, y)


def draw_linear_function(f, obj, lines, color):
    matrix = obj.matrix_world
    x1 = -2
    x2 = 2
    p1 = Vector((x1, f['a'] * x1 + f['b'], 0))
    p2 = Vector((x2, f['a'] * x2 + f['b'], 0))
    p1_co = matrix @ p1
    p2_co = matrix @ p2
    lines.append_a_line([
        [(p1_co.x, p1_co.y, p1_co.z), (p2_co.x, p2_co.y, p2_co.z)],
        6,
        color,
        False
    ])


def find_next_to_bool(obj: Object, bool):
    for i, m in enumerate(obj.modifiers):
        try:
            if m == bool and obj.modifiers[i+1].type == 'BEVEL':
                return obj.modifiers[i+1]
        except:
            return None


def find_boolean_modifier(bool_obj, cut_obj):
    # retour le modifier sinon False
    for m in cut_obj.modifiers:
        if m.type == 'BOOLEAN' and m.object == bool_obj:
            return m
            break
    return False


def find_boolean_operation(bool_obj, bool_target):
    # recherche le modifier booléen
    for m in bool_target.modifiers:
        if m.type == 'BOOLEAN' and m.object == bool_obj:
            bool_modifier = m
            bool_operation = m.operation
            break
    if not bool_modifier:
        return False

    # détermine l'opération actuelle
    current_operation = None
    # test si c'est un slice
    if bool_modifier.operation == 'DIFFERENCE':
        for o in bpy.data.objects:
            for m in o.modifiers:
                if m.type == 'BOOLEAN' and m.object == bool_obj and m.operation == 'INTERSECT':
                    current_operation = 'SLICE'
                    break
            if current_operation:
                break
    # si ni slice ni inset sont trouvé, par défaut, on prend l'opération du modifier
    if not current_operation:
        current_operation = bool_modifier.operation

    return current_operation


def find_boolean_targets(bool_obj):
    boolean_targets = []
    if bool_obj.get('fluent_inset'):
        bool_obj = bool_obj.get('fluent_inset')
    for o in bpy.context.visible_objects:
        if o.type == 'MESH':
            for i, m in enumerate(o.modifiers):
                if m.type == 'BOOLEAN' and m.object == bool_obj:
                    boolean_targets.append({
                        'cut_object': o,
                        'boolean_modifier': m,
                        'initial_mod_index': i
                    })
    return boolean_targets


def change_bool_operation(bool_obj, bool_target, operation):
    # recherche le modifier booléen
    if bool_obj.get('fluent_inset'):
        bool_modifier = find_boolean_modifier(bool_obj.get('fluent_inset'), bool_target)
    else:
        bool_modifier = find_boolean_modifier(bool_obj, bool_target)
    if not bool_modifier:
        print('no bool modifier')
        return False

    current_operation = bool_obj['fluent_operation']

    if operation in ['CUT', 'UNION', 'DIFFERENCE', 'INTERSECT']:
        if current_operation in ['CUT', 'UNION', 'DIFFERENCE', 'INTERSECT']:
            if bool_modifier.operation != operation:
                if operation == 'CUT':
                    operation = 'DIFFERENCE'
                else:
                    bool_modifier.operation = operation
                bool_obj['fluent_operation'] = 'CUT'
        elif current_operation == 'SLICE':
            slice_obj = bool_obj['fluent_slice']
            bpy.data.objects.remove(slice_obj, do_unlink=True)
            if operation == 'CUT': operation = 'DIFFERENCE'
            bool_modifier.operation = operation
            bool_obj['fluent_operation'] = 'CUT'
            bool_obj.pop('fluent_slice', None)
        elif current_operation == 'INSET':
            inset_obj = bool_obj['fluent_inset']
            bpy.data.objects.remove(inset_obj, do_unlink=True)
            if operation == 'CUT': operation = 'DIFFERENCE'
            bool_modifier.operation = operation
            bool_obj['fluent_operation'] = 'CUT'
            bool_obj.pop('fluent_inset', None)
            bool_modifier.object = bool_obj
        # if bool_obj.get('fluent_type') in ['revolver']:
        #     co_y_moyen = 0
        #     for v in bool_obj.data.vertices:
        #         co_y_moyen = co_y_moyen + v.co.y
        #     co_y_moyen = co_y_moyen / len(bool_obj.data.vertices)
        #     if co_y_moyen > 0:
        #         bool_modifier.operation = 'UNION'
        #     else:
        #         bool_modifier.operation = 'DIFFERENCE'
    elif operation == 'SLICE':
        if current_operation == 'INSET':
            inset_obj = bool_obj['fluent_inset']
            bpy.data.objects.remove(inset_obj, do_unlink=True)
            bool_obj['fluent_operation'] = 'CUT'
            bool_obj.pop('fluent_inset', None)
            bool_modifier.object = bool_obj
        bool_modifier.operation = 'DIFFERENCE'
        slice_obj = duplicate(obj=bool_target, name='.slice')
        # slice_obj.location = bool_target.location
        # slice_obj.rotation_euler = bool_target.rotation_euler.copy()
        if get_addon_preferences().auto_parent:
            parent_relationship(bool_target, slice_obj)
        m = find_boolean_modifier(bool_obj, slice_obj)
        m.operation = 'INTERSECT'
        # si le bool est un obj fluent je vérifie que le solidify soit dans le bon sens
        if bool_obj.get('fluent_type') in ['box', 'prism', 'poly']:
            slice_obj['fluent_type'] = bool_target.get('fluent_type')
            for m in bool_obj.modifiers:
                if m.type == 'SOLIDIFY' and m.name == fluent_modifiers_name['first_solidify']:
                    m.thickness = math.fabs(m.thickness) * -1
        bool_obj['fluent_operation'] = 'SLICE'
        bool_obj['fluent_slice'] = slice_obj
        slice_bevel = F_outer_bevel()
        slice_bevel.set_target(slice_obj)
        slice_bevel.management()
        bevel = F_outer_bevel()
        bevel.set_target(bool_target)
        bevel.management()
    elif operation == 'INSET':
        if current_operation == 'SLICE':
            slice_obj = bool_obj['fluent_slice']
            bpy.data.objects.remove(slice_obj, do_unlink=True)
            bool_obj['fluent_operation'] = 'CUT'
            bool_obj.pop('fluent_slice', None)
        inset_obj = duplicate(obj=bool_target, name='.inset')
        if get_addon_preferences().auto_parent:
            parent_relationship(bool_target, inset_obj)
        inset_obj.display_type = 'WIRE'
        m = find_boolean_modifier(bool_obj, inset_obj)
        inset_obj.modifiers.remove(modifier=m)
        solidify = inset_obj.modifiers.new(name=fluent_modifiers_name['inset_solidify'], type="SOLIDIFY")
        solidify.offset = 0
        solidify.use_even_offset = True
        solidify.solidify_mode = 'NON_MANIFOLD'
        solidify.thickness = 0.05
        # if get_addon_preferences().bevel_system != 'MULTIPLE':
        inset_bevel = F_outer_bevel()
        inset_bevel.set_target(inset_obj)
        inset_bevel.find_last()
        inset_bevel.remove('ALL')
        # inset_bevel.remove('LAST')
        bool = inset_obj.modifiers.new(name=fluent_modifiers_name['boolean'], type="BOOLEAN")
        bool.solver = 'FAST'
        bool.operation = 'INTERSECT'
        bool.object = bool_obj
        bool.show_expanded = False
        bool_modifier.object = inset_obj
        bool_modifier.operation = 'DIFFERENCE'
        bool_obj['fluent_operation'] = 'INSET'
        bool_obj['fluent_inset'] = inset_obj
        add_in_bool_collection(inset_obj)
        inset_obj.hide_set(True)
        inset_obj.hide_render = True
        inset_obj['fluent_operation'] = 'INSET'
    elif operation == 'INSET_ADD':
        bool_modifier.operation = 'UNION'
    elif operation == 'INSET_DIFF':
        bool_modifier.operation = 'DIFFERENCE'

    active_object('SET', bool_obj, True)
    bool_obj.hide_set(True)
    return operation


def get_modifier_values(mod):
    properties = [p.identifier for p in mod.bl_rna.properties if not p.is_readonly]
    properties_values = [getattr(mod, p) for p in properties]
    return {'properties': properties, 'properties_values': properties_values, 'show_render': mod.show_render,
            'show_viewport': mod.show_viewport, 'name': mod.name}


def set_modifier_value(mod, properties_dico, avoid=[]):
    i = 0
    for prop in properties_dico['properties']:
        if prop not in avoid:
            setattr(mod, prop, properties_dico['properties_values'][i])
        i += 1
    mod.show_render = properties_dico['show_render']
    mod.show_viewport = properties_dico['show_viewport']


def original_name(name):
    return name.split('.')[0]


def copy_gn_mod_inputs(original_mod, source_obj):
    for mod in source_obj.modifiers:
        if mod.name != original_mod.name:
            continue
        if bpy.app.version >= (4, 0, 0):
            for node_input in original_mod.node_group.interface.items_tree:
                if node_input.name == 'Geometry':
                    continue

                for i in mod.node_group.interface.items_tree:
                    if i == node_input.identifier:
                        new_value = mod[node_input.identifier]
                        original_mod[node_input.identifier] = new_value
                        break
        else:
            for node_input in original_mod.node_group.inputs:
                if node_input.name == 'Geometry':
                    continue

                new_value = mod[node_input.identifier]
                original_mod[node_input.identifier] = new_value

        for key in mod.keys():
            new_value = mod[key]
            original_mod[key] = new_value
        break


def save_modifers_stack(obj):
    modifiers_stack = []
    for m in obj.modifiers:
        modifier = {}
        modifier['name'] = m.name
        modifier['type'] = m.type
        modifier['value'] = get_modifier_values(m)
        modifiers_stack.append(modifier)
    return modifiers_stack


def remake_modifiers_stack(obj, stack):
    # supprimes les modifiers actuels
    for i,m in enumerate(obj.modifiers):
        obj.modifiers.remove(modifier=m)
    # recréer la liste les modifiers
    for i, m in enumerate(stack):
        new_mod = obj.modifiers.new(name=m['name'], type=m['type'])
        set_modifier_value(new_mod, m['value'])


def copy_modifiers_stack(source, target, name='', do_place_in_stack=False):
    single_mod_added = None
    for m in source.modifiers:
        if name != '' and m.name != name:
            continue
        new = target.modifiers.new(type=m.type, name=m.name)
        properties_dico = get_modifier_values(m)
        set_modifier_value(new, properties_dico)
        if m.type == 'NODES':
            copy_gn_mod_inputs(new, source)
        if do_place_in_stack:
            place_in_stack(target, new)

        single_mod_added = new

    return single_mod_added

def duplicate(obj, name='.copy', linked=False):
    if linked:
        copy = bpy.data.objects.new(obj.name + name, obj.data)
    else:
        copy = bpy.data.objects.new(obj.name + name, obj.data.copy())
    bpy.context.collection.objects.link(copy)
    copy_modifiers_stack(obj, copy)
    copy.location = obj.matrix_world.to_translation()
    copy.rotation_euler = obj.matrix_world.to_euler()
    copy.scale = obj.matrix_world.to_scale()
    copy.hide_render = obj.hide_render
    copy.hide_viewport = obj.hide_viewport
    copy.hide_set(obj.hide_get())
    # Récupère la collection de l'objet d'origine et place la copie dans la même collection
    if obj.users_collection:
        obj_collection = obj.users_collection[0]
    if copy.users_collection:
        copy_collection = copy.users_collection[0]
    if obj_collection != copy_collection:
        copy_collection.objects.unlink(copy)
        obj_collection.objects.link(copy)
    if obj.get('fluent_type'):
        copy['fluent_type'] = obj.get('fluent_type')
    if obj.get('fluent_operation'):
        copy['fluent_operation'] = obj.get('fluent_operation')
    return copy


def duplicate_and_add_boolean(child: Object, obj_with_modifiers: Object | None = None, parent_obj: Object | None = None) -> Object:
    if parent_obj is None:
        parent_obj = obj_with_modifiers

    child_copy = duplicate(obj=child, linked=True)

    if child.get('fluent_id'):
        child_copy['fluent_id'] = child.get('fluent_id')
    else:
        child['fluent_id'] = child_copy['fluent_id'] = search_last_fluent_id() + 1

    if child_copy.get('fluent_operation'):
        child_copy.display_type = 'WIRE'
        add_in_bool_collection(child_copy)
    if get_addon_preferences().auto_parent and parent_obj is not None:
        child_copy.hide_viewport = False
        child_copy.hide_set(False)
        active_object(action='SET', obj=parent_obj, solo=True)
        child_copy.select_set(True)
        bpy.ops.object.parent_set(type='OBJECT', keep_transform=False)
        bpy.ops.object.select_all(action='DESELECT')

    # Relance de la fonction pour les cuts de cuts
    for c in child.children:
        duplicate_and_add_boolean(child=c, obj_with_modifiers=child_copy)

    if obj_with_modifiers is None:
        return child_copy

    for m in obj_with_modifiers.modifiers:
        if m.type == 'BOOLEAN' and m.object == child:
            m.object = child_copy
            break

    for m in child_copy.modifiers:
        if m.type == 'MIRROR':
            m.mirror_object = obj_with_modifiers

    return child_copy

def apply_modifiers(obj, ignore=[]):
    previous_active_object = active_object('GET')
    active_object('SET', obj, True)
    if ignore:
        apply_me = []
        for m in obj.modifiers:
            if m not in ignore:
                apply_me.append(m)
        for m in apply_me:
            bpy.ops.object.modifier_apply(modifier=m.name)

    if not ignore:
        bpy.ops.object.convert(target="MESH")
    active_object('SET', previous_active_object, True)


def affichage_booleen(bool_collection = None, operation = None):
    if not bool_collection:
        try:
            bool_collection = bpy.data.collections[get_addon_preferences().bool_collection]
        except:
            return
    if len(bool_collection.objects) and bool_collection.objects[0].hide_get() or operation == False:
        operation = False
        for o in bool_collection.objects:
            if o.get('fluent_type') != 'grid':
                o.hide_set(False)
    elif len(bool_collection.objects) and not bool_collection.objects[0].hide_get() or operation == True:
        operation = True
        for o in bool_collection.objects:
            if o.get('fluent_type') != 'grid':
                o.hide_set(True)
    for child_collection in bool_collection.children:
        affichage_booleen(child_collection, operation)


def display_object_booleans(obj: Object, hide=False):
    for m in obj.modifiers:
        if m.type != 'BOOLEAN':
            continue

        if m.object is None:
            continue

        m.object.hide_set(hide)


def add_in_bool_collection(obj):
    the_scene = bpy.context.scene

    if not bpy.data.collections.get(get_addon_preferences().bool_collection):
        bpy.data.collections.new(get_addon_preferences().bool_collection)
    coll = bpy.data.collections.get(get_addon_preferences().bool_collection)

    if not the_scene.collection.children.get(get_addon_preferences().bool_collection):
        the_scene.collection.children.link(coll)
    try:
        bpy.data.collections[get_addon_preferences().bool_collection].objects.link(obj)
    except:
        pass
    try:
        bpy.context.scene.collection.objects.unlink(obj)
    except:
        pass


def cross_depth_research(obj, target):
    helper = make_plane()
    helper.data.vertices[0].co = Vector((-1, -1, 0))
    helper.data.vertices[1].co = Vector((-1, 1, 0))
    helper.data.vertices[2].co = Vector((1, 1, 0))
    helper.data.vertices[3].co = Vector((1, -1, 0))

    helper.location = obj.location
    helper.rotation_euler = obj.rotation_euler

    depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.id_type_updated('OBJECT')

    direction_du_trou = helper.matrix_world.to_3x3() @ helper.data.polygons[0].normal
    direction_du_trou.normalize()

    target_eval = target.evaluated_get(depsgraph)
    target_matrix = target_eval.matrix_world

    plus_grand_p_scalaire_trouve = 0
    for v in target_eval.data.vertices:
        v_co_3d = target_matrix @ v.co
        vector_test = Vector(
            (v_co_3d.x - helper.location.x, v_co_3d.y - helper.location.y, v_co_3d.z - helper.location.z))
        # direction_du_trou et vector_test on la même origine
        p_scalaire = produit_scalaire(direction_du_trou, vector_test)
        if math.fabs(p_scalaire) > plus_grand_p_scalaire_trouve:
            plus_grand_p_scalaire_trouve = p_scalaire
    bpy.data.objects.remove(helper, do_unlink=True)
    return plus_grand_p_scalaire_trouve


def move_local_axis(obj, axis, distance):
    if axis == 'X':
        vec = Vector((1, 0, 0))
    elif axis == 'Y':
        vec = Vector((0, 1, 0))
    elif axis == 'Z':
        vec = Vector((0, 0, 1))
    inv = obj.matrix_world.copy()
    inv.invert()
    vec_rot = vec @ inv
    obj.location = obj.location + vec_rot * distance


def move_modifier(obj=None, mod_name=None, where='AFTER', mod_target_name=None):
    active_obj = active_object()
    if mod_name and mod_target_name and obj:
        active_object('SET', obj)
        current_index = 0
        target_index = 0
        # trouve les index courrants
        for i, m in enumerate(obj.modifiers):
            if m.name == mod_name:
                current_index = i
            if m.name == mod_target_name:
                target_index = i
        if current_index > target_index and where == 'AFTER':
            bpy.ops.object.modifier_move_to_index(modifier=mod_name, index=target_index+1)
        elif current_index > target_index and where == 'BEFORE':
            bpy.ops.object.modifier_move_to_index(modifier=mod_name, index=target_index - 1)
        elif where == 'ON' and target_index - current_index != 1: # and gére le cas du "ON" où il est déjà bien placé
            bpy.ops.object.modifier_move_to_index(modifier=mod_name, index=target_index)
    if where == 'LAST_BOOL' and obj and mod_name:
        active_obj('SET', obj)
        current_index = 0
        for i, m in enumerate(obj.modifiers):
            if m.name == mod_name:
                current_index = i
        while obj.modifiers[current_index + 1].type == 'BOOLEAN':
            bpy.ops.object.modifier_move_down({'object': obj}, modifier=mod_name)
            current_index += 1
            pass
    active_object('SET', active_obj, 'True')


def shade_smooth(obj, a=True):
    mesh = obj.data
    if a == True:
        for p in mesh.polygons:
            if p.use_smooth:
                break
            p.use_smooth = True
    else:
        for p in mesh.polygons:
            if not p.use_smooth:
                break
            p.use_smooth = False


def remove_empty_bool_modifier(obj):
    delete_them = []
    for i, m in enumerate(obj.modifiers):
        if m.type == 'BOOLEAN':
            if not m.object:
                delete_them.append(m)
                if m.operation == 'INTERSECT':
                    bpy.data.objects.remove(obj, do_unlink=True)
                else:
                    # pour le multiple bevel, il faut aussi enlever le bevel suivant
                    try:
                        if fluent_modifiers_name['outer_bevel'] in obj.modifiers[
                            i + 1].name and get_addon_preferences().bevel_system == 'MULTIPLE':
                            delete_them.append(obj.modifiers[i + 1])
                    except:
                        pass
    for d in delete_them:
        try:
            obj.modifiers.remove(d)
        except:
            pass
    if get_addon_preferences().bevel_system == 'MULTIPLE':
        last_outerbevel = None
        for m in obj.modifiers:
            if fluent_modifiers_name['outer_bevel'] in m.name:
                last_outerbevel = m
        if last_outerbevel:
            last_outerbevel.show_viewport = last_outerbevel.show_render = True


def parent_relationship(parent_obj, children_obj):
    children_obj.parent = parent_obj
    children_obj.matrix_parent_inverse = parent_obj.matrix_world.inverted()


def vector_to_tuple(vec):
    return (vec.x, vec.y, vec.z)


def cycles_visibility(stat):
    try:
        bpy.context.object.cycles_visibility.camera = stat
        bpy.context.object.cycles_visibility.glossy = stat
        bpy.context.object.cycles_visibility.scatter = stat
        bpy.context.object.cycles_visibility.shadow = stat
        bpy.context.object.cycles_visibility.transmission = stat
        bpy.context.object.cycles_visibility.diffuse = stat
    except:
        pass


def boolean_cleaner(objs):
    for obj in objs:
        # suppression des modifiers booléens non utilisés
        delete_them = []
        for i, m in enumerate(obj.modifiers):
            if m.type == 'BOOLEAN':
                if not m.object:
                    delete_them.append(m)
        for d in delete_them:
            obj.modifiers.remove(d)

        # recherche deux outer bevel successif et supprime le premier
        delete_them = []
        for i, m in enumerate(obj.modifiers):
            if len(obj.modifiers)-1 >= i + 1:
                if fluent_modifiers_name['outer_bevel'] in m.name and fluent_modifiers_name['outer_bevel'] in obj.modifiers[i + 1].name:
                    delete_them.append(m)
        for m in delete_them:
            obj.modifiers.remove(m)


def double_outer_bevel_cleaner(objs):
    for obj in objs:
        remove_us = []
        for i, m in enumerate(obj.modifiers):
            try:
                if fluent_modifiers_name['outer_bevel'] in m.name and fluent_modifiers_name['outer_bevel'] in obj.modifiers[i+1]:
                    remove_us.append(obj.modifiers[i+1])
            except:pass
        for m in remove_us:
            obj.modifiers.remove(m)


def search_last_fluent_id():
    greatest = 0
    for obj in bpy.data.objects:
        if obj.get('fluent_id') and obj.get('fluent_id') > greatest:
            greatest = obj.get('fluent_id')
    return greatest


def event_dico_builder():
    dico = {'mouse_left_click': False, 'mouse_x': 0, 'mouse_y': 0, 'value': None,
            'type': None, 'shift_press': False, 'shift_work': False, 'shift_release': False, 'ctrl_press': False,
            'ctrl_work': False, 'ctrl_release': False, 'alt_press': False, 'alt_work': False, 'alt_release':False, 'show_menu':False}
    return dico


def event_dico_refresh(dico, event):
    dico['mouse_x'] = event.mouse_region_x
    dico['mouse_y'] = event.mouse_region_y

    dico['value'] = event.value
    dico['type'] = event.type

    if event.shift and not dico['shift_press'] and not dico['shift_work']:
        dico['shift_press'] = True
    elif event.shift and dico['shift_press']:
        dico['shift_press'] = False
        dico['shift_work'] = True
    elif not event.shift and dico['shift_work']:
        dico['shift_release'] = True
        dico['shift_work'] = False
    elif not event.shift and dico['shift_release']:
        dico['shift_release'] = False
    else:
        dico['shift_press'] = False

    # gestion des événements du ctrl
    if event.ctrl and not dico['ctrl_press'] and not dico['ctrl_work']:
        dico['ctrl_press'] = True
    elif event.ctrl and dico['ctrl_press']:
        dico['ctrl_press'] = False
        dico['ctrl_work'] = True
    elif not event.ctrl and dico['ctrl_work']:
        dico['ctrl_release'] = True
        dico['ctrl_work'] = False
    elif not event.ctrl and dico['ctrl_release']:
        dico['ctrl_release'] = False
    else:
        dico['ctrl_press'] = False

    # gestion des événements du alt
    if event.alt and not dico['alt_press'] and not dico['alt_work']:
        dico['alt_press'] = True
    elif event.alt and dico['alt_press']:
        dico['alt_press'] = False
        dico['alt_work'] = True
    elif not event.alt and dico['alt_work']:
        dico['alt_release'] = True
        dico['alt_work'] = False
    elif not event.alt and dico['alt_release']:
        dico['alt_release'] = False
    else:
        dico['alt_press'] = False

    if event.value == 'PRESS' and event.type == 'LEFTMOUSE':
        dico['mouse_left_click'] = True

    if event.value == 'RELEASE' and event.type == 'LEFTMOUSE':
        dico['mouse_left_click'] = False

    return dico


def boolean_extraction():
    selection = bpy.context.selected_objects
    for obj in selection:
        if obj.get('fluent_type') in ['box', 'prism', 'poly', 'revolver', 'path']:
            copy = duplicate(obj, name='.extracted')
            try:
                del copy['fluent_operation']
            except:
                pass
            copy['fluent_type'] = obj['fluent_type']
            active_object(copy, 'SET', True)
            copy.color = (1, 1, 1, 1)
            copy.display_type = 'TEXTURED'
            copy.hide_render = False
            copy.data.shade_flat()
            try:
                bpy.data.collections[get_addon_preferences().bool_collection].objects.unlink(copy)
                bpy.context.scene.collection.objects.link(copy)
            except:
                pass
            cycles_visibility(True)


def align_to_view(obj):
    rv3d = bpy.context.region_data
    obj.rotation_euler = rv3d.view_rotation.to_euler()


def get_evaluated_object(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    return obj.evaluated_get(depsgraph)


def boolean_visibility_setup(obj, action=True):
    include_view_layers(bpy.data.collections.get(get_addon_preferences().bool_collection))
    obj.display_type = 'WIRE'
    obj.hide_render = True
    obj.visible_camera = False
    obj.visible_shadow = False
    obj.hide_set(True)


def update_resolution():
    # mise à jour de tous les bevels, les cylindres et spheres
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.get('fluent_type'):
            for m in o.modifiers:
                if fluent_modifiers_name['outer_bevel'] in m.name and bpy.context.scene.fluentProp.outer_bevel_segments == 0:
                    m.segments = auto_bevel_segments(bevel=m)
                if fluent_modifiers_name['first_bevel'] in m.name:
                    m.segments = auto_bevel_segments(bevel=m)
                if fluent_modifiers_name['second_bevel_top'] in m.name or fluent_modifiers_name['second_bevel_bottom'] in m.name:
                    m.segments = auto_bevel_segments(bevel=m)
                if o.get('fluent_type') == 'prism':
                    if fluent_modifiers_name['screw'] in m.name:
                        m.steps = m.render_steps = auto_bevel_segments(displace=o.modifiers[fluent_modifiers_name['radius']])
                if o.get('fluent_type') == 'revolver':
                    if fluent_modifiers_name['screw'] in m.name:
                        m.steps = m.render_steps = auto_bevel_segments(revolver_obj=o)


def place_in_stack(obj, mod):
    global fluent_stack_order
    draw_type = obj.get('fluent_type')
    order = fluent_stack_order[draw_type]
    index_theorique = 0
    for i, j in enumerate(order):
        if fluent_modifiers_name[j] in mod.name:
            index_theorique = i
            break
    liste_des_modifiers_suivants = fluent_stack_order[draw_type][index_theorique+1:len(fluent_stack_order[draw_type])]
    liste_des_modifiers_suivants = [fluent_modifiers_name[i].split('.')[1] for i in liste_des_modifiers_suivants]
    previous_modifier_index = len(obj.modifiers)
    last_index = len(obj.modifiers) - 1
    if last_index < 0: last_index = 0
    for i, m in enumerate(reversed(obj.modifiers)):
        index = last_index-i

        name_index_check = m.name.split('.')[1] in liste_des_modifiers_suivants and index < previous_modifier_index
        second_bevel_check = m.name.split('.')[1] == fluent_modifiers_name['outer_bevel'].split('.')[1] and 'Second_Bevel' in mod.name
        if name_index_check or second_bevel_check:
            previous_modifier_index = index

    active_object('SET', obj, True)
    if len(obj.modifiers) > previous_modifier_index >= 0:
        obj.modifiers.move(obj.modifiers.find(mod.name), previous_modifier_index)

    if not obj.get('fluent_operation') and draw_type not in ['pipe', 'wire', 'head_screw']:
        bevels = F_outer_bevel(obj)
        bevels.management()


def get_view_orientation_from_matrix():
    view_matrix = bpy.context.space_data.region_3d.view_matrix
    r = lambda x: round(x, 2)
    view_rot = view_matrix.to_euler()

    if bpy.context.region_data.view_perspective == 'ORTHO':
        orientation_dict = {(0.0, 0.0, 0.0): 'TOP',
                            (r(math.pi), 0.0, 0.0): 'BOTTOM',
                            (r(-math.pi / 2), 0.0, 0.0): 'FRONT',
                            (r(math.pi / 2), 0.0, r(-math.pi)): 'BACK',
                            (r(-math.pi / 2), r(math.pi / 2), 0.0): 'LEFT',
                            (r(-math.pi / 2), r(-math.pi / 2), 0.0): 'RIGHT'}
        return orientation_dict.get(tuple(map(r, view_rot)), 'UNDEFINED')
    else:
        return 'UNDEFINED'


def shortcut_test(km, event):
    if km.value == event.value and km.type == event.type and km.ctrl == event.ctrl and km.alt == event.alt and km.shift == event.shift:
        return True
    else:
        return False


def pass_through(event):
    return (event.type in viewport_navigation_events) \
           or (event.type in viewport_navigation_keys and not event.shift) \
           or (event.alt and event.type == 'LEFTMOUSE') \
           or (event.alt and event.type == 'RIGHTMOUSE')


def hideModifier(modifier):
    modifier.show_render = False
    modifier.show_viewport = False


def modifier_value_converter(value):
    return str(round(value, 3))


def include_view_layers(collection, scenes="all", hide=False):

    def recur_all_layer_collection(layer_collection, all_vl, ):
        if (len(layer_collection.children) != 0):
            all_vl += layer_collection.children
            for ch in layer_collection.children:
                recur_all_layer_collection(ch, all_vl)
        return all_vl

    if (scenes == "all"):
        scenes = bpy.data.scenes[:]

    for s in scenes:
        for v in s.view_layers:
            for lc in recur_all_layer_collection(v.layer_collection, []):

                if (lc.collection == collection):

                    if (lc.exclude != hide):
                        lc.exclude = hide


def hide_object(obj, a):
    if a == 'VIEWPORT':
        obj.hide_set(True)
    if a == 'DISABLE':
        obj.hide_viewport = True
    if a == 'RENDER':
        obj.hide_render = True


def show_object(obj, a):
    if a == 'VIEWPORT':
        obj.hide_set(False)
    if a == 'DISABLE':
        obj.hide_viewport = False
    if a == 'RENDER':
        obj.hide_render = False


def get_raw_object_dim(obj: Object, with_scale: bool = True) -> list[float] | Vector:
    was_shown_modifiers = []
    for mod in obj.modifiers:
        if with_scale and any(x in mod.name for x in fluent_dimension_mods):
            continue

        if obj.get('fluent_type', None) in ['prism', 'sphere'] and mod.name in [fluent_modifiers_name['radius'], fluent_modifiers_name['screw'], fluent_modifiers_name['screw_2']]:
            continue

        if mod.show_viewport:
            was_shown_modifiers.append(mod)
        mod.show_viewport = False

    depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.id_type_updated('OBJECT')
    dim = obj.dimensions.copy()
    for mod in was_shown_modifiers:
        mod.show_viewport = True

    depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.id_type_updated('OBJECT')

    return dim


def recalculate_array_center(obj: Object, mod_center: Modifier|None=None, mod_array: Modifier|None=None, axis=None):
    if not bpy.context.scene.fluentProp.centered_array:
        return

    index = None
    if axis == 'x':
        index = 0
    if axis == 'y':
        index = 1
    if axis == 'z':
        index = 2

    if axis is not None:
        if mod_center is None and mod_array is None:
            for mod in obj.modifiers:
                if mod.name == fluent_modifiers_name['array_'+axis] and mod.type == 'ARRAY':
                    mod_array = mod
                if mod.name == fluent_modifiers_name['center_array_'+axis] and mod.type == 'DISPLACE':
                    mod_center = mod

            if mod_center is None and mod_array is None:
                return

        dim = get_raw_object_dim(obj)
        mod_center.strength = (mod_array.count - 1) * mod_array.relative_offset_displace[index] * dim[index] * (-1)

        return

    recalculate_array_center(obj, axis='x')
    recalculate_array_center(obj, axis='y')
    recalculate_array_center(obj, axis='z')


def initialize_properties_from_preferences():
    global init_pref
    if not init_pref:
        prefs = get_addon_preferences()
        scene_props = bpy.context.scene.fluentProp
        scene_props.model_resolution = prefs.model_resolution
        scene_props.width = prefs.latest_bevel_width_preference
        scene_props.min_auto_bevel_segments = prefs.min_auto_bevel_segments
        scene_props.min_auto_cylinder_segments = prefs.min_auto_cylinder_segments
        init_pref = True


def find_screw_bool_modifier(obj):
    bool_modifiers = []
    for m in obj.modifiers:
        if m.type == 'BOOLEAN' and m.object.get('fluent_secondary_type') == 'screw_bool':
            bool_modifiers.append(m)
    return bool_modifiers