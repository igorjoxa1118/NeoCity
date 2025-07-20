import bpy
from bpy_extras import view3d_utils
# from .viewport_drawing import *
# from .math_functions import *
# from .drawing import *
from .UI.Helpers.ui_button import *
from .bevels import *
import bmesh
from .UI.make_button import make_button

from .UI.Helpers.ui_management import *
from .Tools.translation import translate

class modifiers_manager():
    def __init__(self, obj, bool_target = None):
        self.obj = obj
        self.draw_type = obj.get('fluent_type')
        self.bool_target = bool_target
        self.mirror = None
        self.array = None
        self.circular_array = None
        self.first_solidify = None
        self.second_solidify = None
        self.first_bevel = None
        self.second_bevel = None
        self.radius = None
        self.resolution = None
        self.curve = None
        self.path_height = None
        self.inset_solidify = None
        self.taper = None
        self.scale = None
        self.rotate = None
        self.reuse = None
        self.outer_bevel = None
        self.frame = None
        self.chamfer = None
        self.keys = {
        'shift_work':False,
        'shift_press':False,
        'shift_release':False,
        'ctrl_work':False,
        'ctrl_press':False,
        'ctrl_release':False
        }
        self.x_mouse_slider_origin = None
        self.bool_operation = 'DIFFERENCE'
        self.adjust_what = None
        self.ui_management = None

    def get_obj(self):
        return self.obj

    def set_adjust_what(self, action):
        self.adjust_what = action

    def get_adjust_what(self):
        return self.adjust_what

    def adjust(self, ui_management_parent, show_menu=True):
        callback = []
        if self.adjust_what:
            if self.adjust_what == 'FIRST_SOLIDIFY':
                if not self.first_solidify:
                    self.first_solidify = first_solidify_management(self.obj, bool_target=self.bool_target)
                callback = self.first_solidify.adjust_solidify(ui_management_parent)
                try:
                    if not self.obj.get('inib_auto_bool_switching'):
                        if 'BOOL_DIFFERENCE' in callback and self.obj.get('fluent_operation') == 'CUT':
                            self.bool_operation = change_bool_operation(self.obj, self.bool_target, 'DIFFERENCE')
                        if 'BOOL_UNION' in callback and self.obj.get('fluent_operation') == 'CUT':
                            self.bool_operation = change_bool_operation(self.obj, self.bool_target, 'UNION')
                except:pass
            elif self.adjust_what == 'FIRST_BEVEL':
                if not self.first_bevel:
                    self.first_bevel = first_bevel_management(self.obj)
                callback = self.first_bevel.adjust_bevel(ui_management_parent)
            elif self.adjust_what == 'SECOND_BEVEL':
                if not self.second_bevel:
                    self.second_bevel = second_bevel_management(self.obj)
                callback = self.second_bevel.adjust_bevel(ui_management_parent)
            elif self.adjust_what == 'SECOND_SOLIDIFY':
                if not self.second_solidify:
                    self.second_solidify = second_solidify_management(self.obj)
                callback = self.second_solidify.adjust_solidify(ui_management_parent)
            elif self.adjust_what == 'MIRROR':
                if not self.mirror:
                    self.mirror = mirror_management(self.obj, self.bool_target)
                callback = self.mirror.adjust_mirror(ui_management_parent, show_menu=show_menu)
            elif self.adjust_what == 'TAPER':
                if not self.taper:
                    self.taper = taper_management(self.obj)
                callback = self.taper.adjust_tape(ui_management_parent)
            elif self.adjust_what == 'ARRAY':
                if not self.array:
                    self.array = array_management(self.obj)
                callback = self.array.adjust_array(ui_management_parent)
            elif self.adjust_what == 'CIRCULAR_ARRAY':
                if not self.circular_array:
                    self.circular_array = circular_array_management(self.obj, self.bool_target)
                callback = self.circular_array.adjust(ui_management_parent)
            elif self.adjust_what == 'DIMENSIONS':
                if not self.scale:
                    self.scale = scale_management(self.obj)
                callback = self.scale.adjust_modifier(ui_management_parent)
            elif self.adjust_what == 'ROTATION':
                if not self.rotate:
                    self.rotate = rotation_management(self.obj)
                callback = self.rotate.adjust_modifier(ui_management_parent)
            elif self.adjust_what == 'REUSE':
                if not self.reuse:
                    self.reuse = reuse_management(self.obj)
                callback = self.reuse.adjust_modifier(ui_management_parent)
            elif self.adjust_what == 'RADIUS':
                if not self.radius:
                    self.radius = radius_management(self.obj)
                callback = self.radius.adjust_modifier(ui_management_parent)
            elif self.adjust_what == 'RESOLUTION':
                if not self.resolution:
                    self.resolution = resolution_management(self.obj)
                callback = self.resolution.adjust_modifier(ui_management_parent)
            elif self.adjust_what == 'INSET_THICKNESS':
                if not self.inset_solidify:
                    self.inset_solidify = inset_management(self.obj, inset_obj=self.obj['fluent_inset'])
                callback = self.inset_solidify.adjust(ui_management_parent)
                try:
                    if 'INSET_ADD' in callback:
                        self.bool_operation = change_bool_operation(self.obj, self.bool_target, 'INSET_ADD')
                    if 'INSET_DIFF' in callback:
                        self.bool_operation = change_bool_operation(self.obj, self.bool_target, 'INSET_DIFF')
                except:
                    pass
            elif self.adjust_what == 'PATH_HEIGHT':
                if not self.path_height:
                    self.path_height = path_height_management(self.obj, bool_target=self.bool_target)
                callback = self.path_height.adjust(ui_management_parent)
                try:
                    if 'BOOL_DIFFERENCE' in callback and self.obj.get('fluent_operation') == 'CUT':
                        self.bool_operation = change_bool_operation(self.obj, self.bool_target, 'DIFFERENCE')
                        if 'CHAMFER' in callback:
                            self.obj.modifiers[fluent_modifiers_name['path_displace']].strength = -0.01
                        else:
                            self.obj.modifiers[fluent_modifiers_name['path_displace']].strength = 0.01
                    if 'BOOL_UNION' in callback and self.obj.get('fluent_operation') == 'CUT':
                        self.bool_operation = change_bool_operation(self.obj, self.bool_target, 'UNION')
                        if 'CHAMFER' in callback:
                            self.obj.modifiers[fluent_modifiers_name['path_displace']].strength = 0.01
                        else:
                            self.obj.modifiers[fluent_modifiers_name['path_displace']].strength = -0.01
                except:pass
            elif self.adjust_what == 'PATH_THICKNESS':
                if not self.first_solidify:
                    self.first_solidify = first_solidify_management(self.obj)
                callback = self.first_solidify.adjust_solidify(ui_management_parent)
            elif self.adjust_what == 'CURVE':
                if not self.curve:
                    self.curve = curve_management(self.obj)
                callback = self.curve.adjust(ui_management_parent)
            elif self.adjust_what == 'OUTER_BEVEL':
                if not self.outer_bevel:
                    self.outer_bevel = outer_bevel_management(self.obj)
                callback = self.outer_bevel.adjust(ui_management_parent)
            elif self.adjust_what == 'FRAME':
                if not self.frame:
                    self.frame = frame_management(self.obj, ui=ui_management_parent)
                callback = self.frame.adjust_frame(ui_management_parent)
            elif self.adjust_what == 'CHAMFER':
                if not self.chamfer:
                    self.chamfer = chamfer_management(self.obj, ui=ui_management_parent)
                callback = self.chamfer.adjust_chamfer(ui_management_parent)

        if 'STOP_ADJUSTMENT' in callback:
            if self.adjust_what in WIDGET_ACTIONS:
                callback.append('CLOSE_WIDGET')
            self.adjust_what = None

        return callback

    def outer_bevel_preparation(self, cut_objects=[]):
        # cut_objects est un tableau d'objets.
        # chaque objet contient l'objet coupé (cut_object) et le modifier booléen qui le coupe (boolean_modifier).
        bevels = []
        if not len(cut_objects) and self.obj and self.obj.get('fluent_type') != 'plate':
            cut_objects = find_boolean_targets(self.obj)
        if len(cut_objects):
            for i in cut_objects:
                bevel = F_outer_bevel(i['cut_object'])
                bevel_mod = find_next_to_bool(bevel.target, i['boolean_modifier'])
                if bevel_mod:
                    bevel.bool_obj = i['boolean_modifier'].object
                    bevel.bool_modifier = i['boolean_modifier']
                    bevel.initial_mod_index = i['initial_mod_index']+1
                    bevel.current_bevel = bevel_mod
                    bevels.append(bevel)
            self.outer_bevel = outer_bevel_management(bevels)
        else:
            # cherche un bevel sur l'objet lui même
            bevel = F_outer_bevel(self.obj)
            if bevel.find_last():
                bevel.last_as_current()
                bevels.append(bevel)
                self.outer_bevel = outer_bevel_management(bevels)
            else:
                print('--- outer bevel', 'no bevel found')


class mirror_management():
    def __init__(self, obj, bool_target):
        self.obj = obj
        self.mirror = None
        self.empty = None
        self.original_value = None
        self.original_ref_obj = bool_target
        self.init = None

        # affichage
        self.action = None
        self.ui_sent = False

        self.pie_menu = FLUENT_Ui_Layout('MIRROR')
        self.pie_menu.set_layout('MIRROR')

        button = make_button('VALIDATE')
        self.pie_menu.add_item(button)

        button = FLUENT_Ui_Button()
        button.set_text('')
        button.set_shape('CIRCLE')
        button.set_action('+X')
        button.set_default_color((.9, 0, 0, 1))
        self.pie_menu.add_item(button)


        button = FLUENT_Ui_Button()
        button.set_text('')
        button.set_shape('CIRCLE')
        button.set_action('-X')
        button.set_default_color((.9, 0, 0, 1))
        self.pie_menu.add_item(button)

        button = FLUENT_Ui_Button()
        button.set_text('')
        button.set_shape('CIRCLE')
        button.set_action('+Y')
        button.set_default_color((0, .9, 0, 1))
        self.pie_menu.add_item(button)

        button = FLUENT_Ui_Button()
        button.set_text('')
        button.set_shape('CIRCLE')
        button.set_action('-Y')
        button.set_default_color((0, .9, 0, 1))
        self.pie_menu.add_item(button)

        button = FLUENT_Ui_Button()
        button.set_text('')
        button.set_shape('CIRCLE')
        button.set_action('+Z')
        button.set_default_color((0, 0, .9, 1))
        self.pie_menu.add_item(button)

        button = FLUENT_Ui_Button()
        button.set_text('')
        button.set_shape('CIRCLE')
        button.set_action('-Z')
        button.set_default_color((0, 0, .9, 1))
        self.pie_menu.add_item(button)

    def set_ui(self, ui):
        ui.hide_menu()
        ui.add_items(self.pie_menu)
        ui.hide_menu()
        self.ui_sent = True

    def add_mirror(self, ref):
        self.initiation()
        if not self.mirror:
            obj = self.obj
            self.mirror = obj.modifiers.new(name=fluent_modifiers_name['mirror'], type='MIRROR')
            self.mirror.mirror_object = ref
            self.mirror.show_viewport = False
            self.mirror.show_render = False
            self.mirror.use_axis[0] = False
            self.mirror.use_axis[1] = False
            self.mirror.use_axis[2] = False
            self.mirror.use_bisect_axis[0] = True
            self.mirror.use_bisect_axis[1] = True
            self.mirror.use_bisect_axis[2] = True
            self.mirror.show_expanded = False

            if bpy.context.scene.fluentProp.auto_mirror_x :
                self.mirror.use_axis[0] = True
                self.mirror.show_viewport = True
                self.mirror.show_render = True
            if bpy.context.scene.fluentProp.auto_mirror_y :
                self.mirror.use_axis[1] = True
                self.mirror.show_viewport = True
                self.mirror.show_render = True
            if bpy.context.scene.fluentProp.auto_mirror_z :
                self.mirror.use_axis[2] = True
                self.mirror.show_viewport = True
                self.mirror.show_render = True

            place_in_stack(self.obj, self.mirror)

    def get_modifier(self):
        return self.mirror

    def initiation(self):
        for m in self.obj.modifiers:
            if m.name == fluent_modifiers_name['mirror'] and m.type == 'MIRROR':
                self.mirror = m
                self.original_ref_obj = m.mirror_object
                break
        if not self.original_ref_obj:
            self.original_ref_obj = self.obj
        return self.mirror

    def save(self):
        self.original_value = get_modifier_values(self.mirror)

    def backup(self):
        set_modifier_value(self.mirror, self.original_value)

    def end_of_adjustment(self):
        self.original_value = None
        self.init = False
        self.ui_sent = False
        if not self.mirror.use_axis[0] and not self.mirror.use_axis[1] and not self.mirror.use_axis[2]:
            self.mirror.show_viewport = False
            self.mirror.show_render = False
        else:
            self.mirror.show_viewport = True
            self.mirror.show_render = True

    def adjust_mirror(self, ui: FLUENT_ui_management, show_menu=True):
        callback = []
        screen_text = []

        keys = ui.event_dico_get()
        self.action = ui.get_button_action()[0]
        if show_menu and not self.ui_sent:
            self.set_ui(ui)

        if not self.init:
            self.add_mirror(self.original_ref_obj)
            self.save()
            self.pie_menu.set_obj(self.obj)
            self.mirror.show_viewport = True
            self.mirror.show_render = True
            self.init = True

        if keys['value'] == 'PRESS' and keys['type'] == 'C':
            target = click_on(keys['mouse_x'], keys['mouse_y'])
            if target and not keys['shift_work']:
                if target != self.obj:
                    self.mirror.mirror_object = target
                    self.original_ref_obj = self.mirror.mirror_object
                else:
                    self.mirror.mirror_object = None
            if target and keys['shift_work']:
                if self.empty:
                    bpy.data.objects.remove(self.empty, do_unlink=True)
                copy = duplicate(target)
                active_object('SET', copy)
                bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_VOLUME')
                bpy.ops.object.add(type='EMPTY')
                self.empty = bpy.context.active_object
                for c in bpy.data.collections:
                    for o in c.objects:
                        if o == self.empty:
                            c.objects.unlink(self.empty)
                try:
                    bpy.context.scene.collection.objects.unlink(self.empty)
                except:pass
                if not bpy.data.collections.get('F_Empty'):
                    coll = bpy.data.collections.new("F_Empty")
                    bpy.context.scene.collection.children.link(coll)
                bpy.data.collections['F_Empty'].objects.link(self.empty)
                self.empty.location = copy.location
                bpy.data.objects.remove(copy, do_unlink=True)
                self.mirror.mirror_object = self.empty
                self.empty.hide_viewport = True
                self.original_ref_obj = self.mirror.mirror_object

        try:
            bool_position = self.obj.matrix_world.to_translation()
            ref_position = self.original_ref_obj.matrix_world.to_translation()
            ref_rotation = self.original_ref_obj.matrix_world.to_quaternion()

            reset_obj_position = bool_position - ref_position
            reset_obj_position.rotate(ref_rotation.to_matrix().to_4x4().inverted())
            if 'X' in self.action:
                if self.mirror.use_axis[0] :
                    self.mirror.use_axis[0] = False
                else:
                    self.mirror.use_axis[0] = True

                    if '+' in self.action:
                        self.mirror.use_bisect_flip_axis[0] = True
                    else:
                        self.mirror.use_bisect_flip_axis[0] = False
            elif 'Y' in self.action:
                if self.mirror.use_axis[1] :
                    self.mirror.use_axis[1] = False
                else:
                    self.mirror.use_axis[1] = True

                    if '+' in self.action:
                        self.mirror.use_bisect_flip_axis[1] = True
                    else:
                        self.mirror.use_bisect_flip_axis[1] = False
            elif 'Z' in self.action:
                if self.mirror.use_axis[2] :
                    self.mirror.use_axis[2] = False
                else:
                    self.mirror.use_axis[2] = True

                    if '+' in self.action:
                        self.mirror.use_bisect_flip_axis[2] = True
                    else:
                        self.mirror.use_bisect_flip_axis[2] = False
        except:pass

        if keys['value'] == 'PRESS' and keys['type'] == 'ESC':
            self.backup()
            self.end_of_adjustment()
            callback.append('DO_NOT_QUIT_FLUENT')
            callback.append('STOP_ADJUSTMENT')

        if self.action == 'VALIDATE':
            self.end_of_adjustment()
            screen_text = []
            callback.append('STOP_ADJUSTMENT')
        callback.append(self.action)

        screen_text.append([translate('objectRef'), 'C'])
        screen_text.append([translate('geoCenter'), translate('shiftC')])
        ui.refresh_side_infos(screen_text)

        return callback


class array_management():
    def __init__(self, obj):
        self.obj = obj
        self.obj_dim = {}
        self.array_axis = ''
        self.slider_origin = None
        self.previous_value = {
            'x':{'count':None, 'offset':None},
            'y':{'count':None, 'offset':None},
            'z':{'count':None, 'offset':None}
        }
        self.other_adjustment = None
        self.enter_value = 'None'
        self.original_value = {
            'x':{'count':None, 'offset':None},
            'y':{'count':None, 'offset':None},
            'z':{'count':None, 'offset':None},
            'xc':None,
            'yc':None,
            'zc':None
        }
        self.backup = {}
        self.array = {
            'x':None,
            'y':None,
            'z':None,
            'xc':None,
            'yc':None,
            'zc':None
        }
        self.init = False

        # affichage
        self.pie_menu = None
        self.action = None
        self.ui_sent = False

        self.pie_menu = FLUENT_Ui_Layout('ARRAY')
        self.pie_menu.set_layout('TAPER')
        self.pie_menu.set_obj(self.obj)

        button = make_button('VALIDATE')
        self.pie_menu.add_item(button)

        button = FLUENT_Ui_Button()
        button.set_text('')
        button.set_shape('CIRCLE')
        button.set_action('+X')
        button.set_default_color((.9, 0, 0, 1))
        self.pie_menu.add_item(button)

        button = FLUENT_Ui_Button()
        button.set_text('')
        button.set_shape('CIRCLE')
        button.set_action('+Y')
        button.set_default_color((0, .9, 0, 1))
        self.pie_menu.add_item(button)

        button = FLUENT_Ui_Button()
        button.set_text('')
        button.set_shape('CIRCLE')
        button.set_action('+Z')
        button.set_default_color((0, 0, .9, 1))
        self.pie_menu.add_item(button)

    def get_pie_menu(self):
        return self.pie_menu

    def initiation(self):
        for m in self.obj.modifiers:
            if m.name == fluent_modifiers_name['array_x'] and m.type == 'ARRAY':
                self.array['x'] = m
            if m.name == fluent_modifiers_name['array_y'] and m.type == 'ARRAY':
                self.array['y'] = m
            if m.name == fluent_modifiers_name['array_z'] and m.type == 'ARRAY':
                self.array['z'] = m
            if m.name == fluent_modifiers_name['center_array_x'] and m.type == 'DISPLACE':
                self.array['xc'] = m
            if m.name == fluent_modifiers_name['center_array_y'] and m.type == 'DISPLACE':
                self.array['yc'] = m
            if m.name == fluent_modifiers_name['center_array_z'] and m.type == 'DISPLACE':
                self.array['zc'] = m
        return self.array

    def add_array(self, x=False, y=False, z=False):
        self.initiation()
        if not (self.array['x'] and self.array['y'] and self.array['z'] and self.array['xc'] and self.array['yc'] and self.array['zc']):
            obj = self.obj
            if x:
                self.array['x'] = obj.modifiers.new(name=fluent_modifiers_name['array_x'], type='ARRAY')
                self.array['x'].relative_offset_displace[0] = 1.5
                self.array['x'].relative_offset_displace[1] = 0
                self.array['x'].relative_offset_displace[2] = 0
                self.array['x'].count = 2
                self.array['x'].show_render = False
                self.array['x'].show_viewport = False
                self.array['x'].show_expanded = False
                self.array['x'].show_in_editmode = True
                place_in_stack(self.obj, self.array['x'])
            if y:
                self.array['y'] = obj.modifiers.new(name=fluent_modifiers_name['array_y'], type='ARRAY')
                self.array['y'].relative_offset_displace[0] = 0
                self.array['y'].relative_offset_displace[1] = 1.5
                self.array['y'].relative_offset_displace[2] = 0
                self.array['y'].count = 2
                self.array['y'].show_render = False
                self.array['y'].show_viewport = False
                self.array['y'].show_expanded = False
                self.array['y'].show_in_editmode = True
                place_in_stack(self.obj, self.array['y'])
            if z:
                self.array['z'] = obj.modifiers.new(name=fluent_modifiers_name['array_z'], type='ARRAY')
                self.array['z'].relative_offset_displace[0] = 0
                self.array['z'].relative_offset_displace[1] = 0
                self.array['z'].relative_offset_displace[2] = 1.5
                self.array['z'].count = 2
                self.array['z'].show_render = False
                self.array['z'].show_viewport = False
                self.array['z'].show_expanded = False
                self.array['z'].show_in_editmode = True
                place_in_stack(self.obj, self.array['z'])
            if x:
                self.array['xc'] = obj.modifiers.new(name=fluent_modifiers_name['center_array_x'], type='DISPLACE')
                self.array['xc'].direction = 'X'
                self.array['xc'].strength = 0
                self.array['xc'].show_render = False
                self.array['xc'].show_viewport = False
                self.array['xc'].show_expanded = False
                self.array['xc'].show_in_editmode = True
                place_in_stack(self.obj, self.array['xc'])
            if y:
                self.array['yc'] = obj.modifiers.new(name=fluent_modifiers_name['center_array_y'], type='DISPLACE')
                self.array['yc'].direction = 'Y'
                self.array['yc'].strength = 0
                self.array['yc'].show_render = False
                self.array['yc'].show_viewport = False
                self.array['yc'].show_expanded = False
                self.array['yc'].show_in_editmode = True
                place_in_stack(self.obj, self.array['yc'])
            if z:
                self.array['zc'] = obj.modifiers.new(name=fluent_modifiers_name['center_array_z'], type='DISPLACE')
                self.array['zc'].direction = 'Z'
                self.array['zc'].strength = 0
                self.array['zc'].show_render = False
                self.array['zc'].show_viewport = False
                self.array['zc'].show_expanded = False
                self.array['zc'].show_in_editmode = True
                place_in_stack(self.obj, self.array['zc'])

    def get_modifier(self, axis):
        if axis == 'X':
            return self.array['x']
        elif axis == 'Y':
            return self.array['y']
        elif axis == 'Z':
            return self.array['z']

    def set_slider_origin(self, value):
        self.x_mouse_slider_origin = value

    def set_previous_value(self):
        self.previous_value['x']['count'] = self.array['x'].count
        self.previous_value['x']['offset'] = self.array['x'].relative_offset_displace[0]
        self.previous_value['y']['count'] = self.array['y'].count
        self.previous_value['y']['offset'] = self.array['y'].relative_offset_displace[1]
        self.previous_value['z']['count'] = self.array['z'].count
        self.previous_value['z']['offset'] = self.array['z'].relative_offset_displace[2]

    def end_of_adjustment(self):
        self.obj_dim = {}
        self.array_axis = ''
        self.slider_origin = None
        self.previous_value = {
            'x':{'count':None, 'offset':None},
            'y':{'count':None, 'offset':None},
            'z':{'count':None, 'offset':None}
        }
        self.other_adjustment = None
        self.enter_value = 'None'
        self.original_value = {
            'x':{'count':None, 'offset':None},
            'y':{'count':None, 'offset':None},
            'z':{'count':None, 'offset':None},
            'xc':None,
            'yc':None,
            'zc':None
        }
        self.init = False
        self.ui_sent = False

    def save_values(self):
        self.original_value['x']['count'] = self.array['x'].count
        self.original_value['x']['offset'] = self.array['x'].relative_offset_displace[0]
        self.original_value['y']['count'] = self.array['y'].count
        self.original_value['y']['offset'] = self.array['y'].relative_offset_displace[1]
        self.original_value['z']['count'] = self.array['z'].count
        self.original_value['z']['offset'] = self.array['z'].relative_offset_displace[2]

    def make_backup(self):
        self.backup['x'] = get_modifier_values(self.array['x'])
        self.backup['y'] = get_modifier_values(self.array['y'])
        self.backup['z'] = get_modifier_values(self.array['z'])
        self.backup['xc'] = get_modifier_values(self.array['xc'])
        self.backup['yc'] = get_modifier_values(self.array['yc'])
        self.backup['zc'] = get_modifier_values(self.array['zc'])

    def restore_backup(self):
        set_modifier_value(self.array['x'], self.backup['x'])
        set_modifier_value(self.array['y'], self.backup['y'])
        set_modifier_value(self.array['z'], self.backup['z'])
        set_modifier_value(self.array['xc'], self.backup['xc'])
        set_modifier_value(self.array['yc'], self.backup['yc'])
        set_modifier_value(self.array['zc'], self.backup['zc'])

    def set_ui(self, ui):
        ui.hide_menu()
        ui.add_items(self.pie_menu)
        ui.hide_menu()
        self.ui_sent = True

    def restore_value(self):
        self.array['x'].count = self.original_value['x']['count']
        self.array['x'].relative_offset_displace[0] = self.original_value['x']['offset']
        self.array['y'].count = self.original_value['y']['count']
        self.array['y'].relative_offset_displace[1] = self.original_value['y']['offset']
        self.array['z'].count = self.original_value['z']['count']
        self.array['z'].relative_offset_displace[2] = self.original_value['z']['offset']

        if self.array['x'].relative_offset_displace[0]:
            self.array['x'].show_viewport = self.array['xc'].show_render = True
        else:
            self.array['x'].show_viewport = self.array['xc'].show_render = False
        recalculate_array_center(self.obj, self.array['xc'], self.array['x'], 'x')

        if self.array['y'].relative_offset_displace[1]:
            self.array['y'].show_viewport = self.array['yc'].show_render = True
        else:
            self.array['y'].show_viewport = self.array['yc'].show_render = False
        recalculate_array_center(self.obj, self.array['yc'], self.array['y'], 'y')

        if self.array['z'].relative_offset_displace[2]:
            self.array['z'].show_viewport = self.array['zc'].show_render = True
        else:
            self.array['z'].show_viewport = self.array['zc'].show_render = False
        recalculate_array_center(self.obj, self.array['zc'], self.array['z'], 'z')

    def adjust_array(self, ui: FLUENT_ui_management):
        keys = ui.event_dico_get()
        self.action = ui.get_button_action()[0]

        if not self.ui_sent:
            self.set_ui(ui)

        self.enter_value = enter_value(self.enter_value, keys)
        callback = []

        if not self.init:
            self.add_array(True, True, True)
            self.slider_origin = keys['mouse_x']
            self.set_previous_value()
            self.save_values()
            self.make_backup()
            has_mirror = False
            has_array_x = False
            has_array_y = False
            has_array_z = False
            try:
                if self.obj.modifiers[fluent_modifiers_name['mirror']].show_viewport:
                    self.obj.modifiers[fluent_modifiers_name['mirror']].show_viewport = False
                    has_mirror = True
            except:pass
            if self.array['x'].show_viewport:
                self.array['x'].show_viewport = False
                has_array_x = True
            if self.array['y'].show_viewport:
                self.array['y'].show_viewport = False
                has_array_y = True
            if self.array['z'].show_viewport:
                self.array['z'].show_viewport = False
                has_array_z = True
            depsgraph = bpy.context.evaluated_depsgraph_get()
            depsgraph.id_type_updated('OBJECT')
            self.obj_dim['x'] = self.obj.dimensions[0]
            self.obj_dim['y'] = self.obj.dimensions[1]
            self.obj_dim['z'] = self.obj.dimensions[2]
            if has_array_x:
                self.array['x'].show_viewport = True
            if has_array_y:
                self.array['y'].show_viewport = True
            if has_array_z:
                self.array['z'].show_viewport = True
            if has_mirror:
                self.obj.modifiers[fluent_modifiers_name['mirror']].show_viewport = True
            self.init = True

        if self.array_axis and keys['value'] == 'PRESS' and keys['type'] == 'LEFTMOUSE':
            self.array_axis = ''

        if type(self.action) == str and 'X' in self.action:
            self.slider_origin = keys['mouse_x']
            self.previous_value['x']['offset'] = self.array['x'].relative_offset_displace[0]
            self.save_values()
            self.other_adjustment = 'OFFSET'
            self.array_axis = 'X'
            self.array['x'].show_viewport = True
            self.array['x'].show_render = True

        if type(self.action) == str and 'Y' in self.action:
            self.slider_origin = keys['mouse_x']
            self.previous_value['y']['offset'] = self.array['y'].relative_offset_displace[1]
            self.save_values()
            self.other_adjustment = 'OFFSET'
            self.array_axis = 'Y'
            self.array['y'].show_viewport = True
            self.array['y'].show_render = True

        if type(self.action) == str and 'Z' in self.action:
            self.slider_origin = keys['mouse_x']
            self.previous_value['z']['offset'] = self.array['z'].relative_offset_displace[2]
            self.save_values()
            self.other_adjustment = 'OFFSET'
            self.array_axis = 'Z'
            self.array['z'].show_viewport = True
            self.array['z'].show_render = True

        if keys['value'] == 'PRESS' and keys['type'] == 'C':
            if self.other_adjustment == 'COUNT':
                self.other_adjustment = 'OFFSET'
                self.slider_origin = keys['mouse_x']
                if self.array_axis == 'X':
                    self.previous_value['x']['offset'] = self.array['x'].relative_offset_displace[0]
                if self.array_axis == 'Y':
                    self.previous_value['y']['offset'] = self.array['y'].relative_offset_displace[1]
                if self.array_axis == 'Z':
                    self.previous_value['z']['offset'] = self.array['z'].relative_offset_displace[2]
            else:
                self.other_adjustment = 'COUNT'
                self.slider_origin = keys['mouse_x']
                if self.array_axis == 'X':
                    self.previous_value['x']['count'] = self.array['x'].count
                if self.array_axis == 'Y':
                    self.previous_value['y']['count'] = self.array['y'].count
                if self.array_axis == 'Z':
                    self.previous_value['z']['count'] = self.array['z'].count

        if keys['value'] == 'PRESS' and keys['type'] == 'V':
            bpy.context.scene.fluentProp.centered_array = not bpy.context.scene.fluentProp.centered_array
            if bpy.context.scene.fluentProp.centered_array:
                self.array['xc'].show_render = self.array['xc'].show_viewport = True
                self.array['yc'].show_render = self.array['yc'].show_viewport = True
                self.array['zc'].show_render = self.array['zc'].show_viewport = True
            else:
                self.array['xc'].show_render = self.array['xc'].show_viewport = False
                self.array['yc'].show_render = self.array['yc'].show_viewport = False
                self.array['zc'].show_render = self.array['zc'].show_viewport = False

        if keys['value'] == 'PRESS' and keys['type'] in {'DEL', 'BACK_SPACE'}:
            if self.array_axis == 'Z':
                self.array['z'].show_viewport = False
                self.array['z'].show_render = False
                self.array['z'].count = 2
                self.array['z'].relative_offset_displace[2] = 0
                try:
                    self.array['zc'].show_viewport = self.array['zc'].show_render = False
                except:pass
                self.array_axis = ''
            elif  self.array_axis == 'Y':
                self.array_axis = ''
                self.array['y'].show_viewport = False
                self.array['y'].show_render = False
                self.array['y'].count = 2
                self.array['y'].relative_offset_displace[1] = 0
                try:
                    self.array['yc'].show_viewport = self.array['yc'].show_render = False
                except:pass
            elif  self.array_axis == 'X':
                self.array_axis = ''
                self.array['x'].show_viewport = False
                self.array['x'].show_render = False
                self.array['x'].count = 2
                self.array['x'].relative_offset_displace[0] = 0
                try:
                    self.array['xc'].show_viewport = self.array['xc'].show_render = False
                except:pass

        if keys['shift_work']:
            increment = 1000*get_addon_preferences().interface_factor
        elif keys['ctrl_work']:
            increment = 10*get_addon_preferences().interface_factor
        else:
            increment = 100*get_addon_preferences().interface_factor

        if keys['shift_press'] or keys['shift_release'] or keys['ctrl_press'] or keys['ctrl_release']:
            self.slider_origin = keys['mouse_x']
            self.set_previous_value()

        if self.array_axis != '':
            try:
                if self.array_axis == 'X':
                    if self.other_adjustment == 'OFFSET':
                        if keys['type'] == 'MOUSEMOVE':
                            self.array['x'].relative_offset_displace[0] = self.previous_value['x']['offset'] + ((keys['mouse_x'] - self.slider_origin)/increment)
                        if enter_value_validation(self.enter_value, keys)[0]:
                            self.array['x'].relative_offset_displace[0] = self.previous_value['x']['offset'] = enter_value_validation(self.enter_value, keys)[1]
                            self.enter_value = 'None'
                            self.array_axis = ''
                    else:
                        if enter_value_validation(self.enter_value, keys)[0]:
                            self.array['x'].count = self.previous_value['x']['count'] = int(enter_value_validation(self.enter_value, keys)[1])
                            self.enter_value = 'None'
                            self.array_axis = ''
                        if keys['type'] == 'MOUSEMOVE':
                            self.array['x'].count = int(self.previous_value['x']['count'] + (keys['mouse_x'] - self.slider_origin)/30)

                    if keys['value'] == 'PRESS' and keys['type'] == 'ESC':
                        try:
                            self.restore_value()
                            callback.append('DO_NOT_QUIT_FLUENT')
                            self.end_of_adjustment()
                        except:pass

                    if bpy.context.scene.fluentProp.centered_array:
                        if self.array['x'].relative_offset_displace[0]:
                            self.array['xc'].show_viewport = self.array['xc'].show_render = True
                        else:
                            self.array['xc'].show_viewport = self.array['xc'].show_render = False
                        recalculate_array_center(self.obj, self.array['xc'], self.array['x'], 'x')

                if self.array_axis == 'Y':
                    if self.other_adjustment == 'OFFSET':
                        if enter_value_validation(self.enter_value, keys)[0]:
                            self.array['y'].relative_offset_displace[1] = self.previous_value['y']['offset'] = enter_value_validation(self.enter_value, keys)[1]
                            self.enter_value = 'None'
                            self.array_axis = ''
                        if keys['type'] == 'MOUSEMOVE':
                            self.array['y'].relative_offset_displace[1] = self.previous_value['y']['offset'] + ((keys['mouse_x'] - self.slider_origin)/increment)
                    else:
                        self.array['y'].count = int(self.previous_value['y']['count'] + (keys['mouse_x'] - self.slider_origin)/30)
                        if enter_value_validation(self.enter_value, keys)[0]:
                            self.array['y'].count = self.previous_value['y']['count'] = int(enter_value_validation(self.enter_value, keys)[1])
                            self.enter_value = 'None'
                            self.array_axis = ''

                    if keys['value'] == 'PRESS' and keys['type'] == 'ESC':
                        try:
                            self.restore_value()
                            callback.append('DO_NOT_QUIT_FLUENT')
                            self.end_of_adjustment()
                        except:pass

                    if bpy.context.scene.fluentProp.centered_array:
                        if self.array['y'].relative_offset_displace[1]:
                            self.array['yc'].show_viewport = self.array['yc'].show_render = True
                        else:
                            self.array['yc'].show_viewport = self.array['yc'].show_render = False
                        recalculate_array_center(self.obj, self.array['yc'], self.array['y'], 'y')

                if self.array_axis == 'Z':
                    if self.other_adjustment == 'OFFSET':
                        if keys['type'] == 'MOUSEMOVE':
                            self.array['z'].relative_offset_displace[2] = self.previous_value['z']['offset'] + ((keys['mouse_x'] - self.slider_origin)/increment)
                        if enter_value_validation(self.enter_value, keys)[0]:
                            self.array['z'].relative_offset_displace[2] = self.previous_value['z']['offset'] = enter_value_validation(self.enter_value, keys)[1]
                            self.enter_value = 'None'
                            self.array_axis = ''
                    else:
                        if enter_value_validation(self.enter_value, keys)[0]:
                            self.array['z'].count = self.previous_value['z']['count'] = int(enter_value_validation(self.enter_value, keys)[1])
                            self.enter_value = 'None'
                            self.array_axis = ''
                        if keys['type'] == 'MOUSEMOVE':
                            self.array['z'].count = int(self.previous_value['z']['count'] + (keys['mouse_x'] - self.slider_origin)/30)

                    if keys['value'] == 'PRESS' and keys['type'] == 'ESC':
                        try:
                            self.restore_value()
                            callback.append('DO_NOT_QUIT_FLUENT')
                            self.end_of_adjustment()
                        except:pass

                    if bpy.context.scene.fluentProp.centered_array:
                        if self.array['z'].relative_offset_displace[2]:
                            self.array['zc'].show_viewport = self.array['zc'].show_render = True
                        else:
                            self.array['zc'].show_viewport = self.array['zc'].show_render = False
                        recalculate_array_center(self.obj, self.array['zc'], self.array['z'], 'z')
            except:pass

        if keys['value'] == 'PRESS' and keys['type'] == 'ESC':
            try:
                self.restore_backup()
            except:pass
            self.end_of_adjustment()
            callback.append('DO_NOT_QUIT_FLUENT')
            callback.append('STOP_ADJUSTMENT')

        # TEXT
        screen_text = []
        if self.array_axis == 'X':
            if self.other_adjustment == 'OFFSET':
                screen_text.append([translate('offset'), adjustment_value(self.array['x'].relative_offset_displace[0], self.enter_value) + ' / ' + modifier_value_converter(self.array['y'].relative_offset_displace[1]) + ' / ' + modifier_value_converter(self.array['z'].relative_offset_displace[2])])
                screen_text.append([translate('count'), modifier_value_converter(self.array['x'].count) + ' / ' + modifier_value_converter(self.array['y'].count) + ' / ' + modifier_value_converter(self.array['z'].count)])
            else:
                screen_text.append([translate('offset'), modifier_value_converter(self.array['x'].relative_offset_displace[0]) + ' / ' + modifier_value_converter(self.array['y'].relative_offset_displace[1]) + ' / ' + modifier_value_converter(self.array['z'].relative_offset_displace[2])])
                screen_text.append([translate('count'), adjustment_value(self.array['x'].count, self.enter_value) + ' / ' + modifier_value_converter(self.array['y'].count) + ' / ' + modifier_value_converter(self.array['z'].count)])
        elif self.array_axis == 'Y':
            if self.other_adjustment == 'OFFSET':
                screen_text.append([translate('offset'), modifier_value_converter(self.array['x'].relative_offset_displace[0]) + ' / ' + adjustment_value(self.array['y'].relative_offset_displace[1], self.enter_value) + ' / ' + modifier_value_converter(self.array['z'].relative_offset_displace[2])])
                screen_text.append([translate('count'),modifier_value_converter(self.array['x'].count) + ' / ' + modifier_value_converter(self.array['y'].count) + ' / ' + modifier_value_converter(self.array['z'].count)])
            else:
                screen_text.append([translate('offset'), modifier_value_converter(self.array['x'].relative_offset_displace[0]) + ' / ' + modifier_value_converter(self.array['y'].relative_offset_displace[1]) + ' / ' + modifier_value_converter(self.array['z'].relative_offset_displace[2])])
                screen_text.append([translate('count'), modifier_value_converter(self.array['x'].count) + ' / ' + adjustment_value(self.array['y'].count,self.enter_value) + ' / ' + modifier_value_converter(self.array['z'].count)])
        elif self.array_axis == 'Z':
            if self.other_adjustment == 'OFFSET':
                screen_text.append([translate('offset'), modifier_value_converter(self.array['x'].relative_offset_displace[0]) + ' / ' + modifier_value_converter(self.array['y'].relative_offset_displace[1]) + ' / ' + adjustment_value(self.array['z'].relative_offset_displace[2], self.enter_value)])
                screen_text.append([translate('count'),modifier_value_converter(self.array['x'].count) + ' / ' + modifier_value_converter(self.array['y'].count) + ' / ' + modifier_value_converter(self.array['z'].count)])
            else:
                screen_text.append([translate('offset'), modifier_value_converter(self.array['x'].relative_offset_displace[0]) + ' / ' + modifier_value_converter(self.array['y'].relative_offset_displace[1]) + ' / ' + modifier_value_converter(self.array['z'].relative_offset_displace[2])])
                screen_text.append([translate('count'), modifier_value_converter(self.array['x'].count) + ' / ' + modifier_value_converter(self.array['y'].count) + ' / ' + adjustment_value(self.array['z'].count,self.enter_value)])
        else:
            screen_text.append([translate('offset'), modifier_value_converter(self.array['x'].relative_offset_displace[0]) + ' / ' + modifier_value_converter(self.array['y'].relative_offset_displace[1]) + ' / ' + modifier_value_converter(self.array['z'].relative_offset_displace[2])])
            screen_text.append([translate('count'),modifier_value_converter(self.array['x'].count) + ' / ' + modifier_value_converter(self.array['y'].count) + ' / ' + modifier_value_converter(self.array['z'].count)])

        screen_text.append([translate('validateAxis'), translate('leftClick')])
        screen_text.append([translate('toggleAdjustment'), 'C'])
        screen_text.append([translate('centerArray'), 'V'])
        screen_text.append([translate('slowerFaster'), translate('shiftControl')])

        self.action = ui.get_button_action()[0]
        if self.action == 'VALIDATE':
            self.end_of_adjustment()
            screen_text = []
            callback.append('STOP_ADJUSTMENT')
        elif self.action is not None:
            self.slider_origin = keys['mouse_x']

        ui.refresh_side_infos(screen_text)

        return callback


class first_solidify_management():
    def __init__(self, obj, bool_target = None, default_thickness=None, default_offset=None):
        self.obj = obj
        self.bool_target = bool_target
        self.draw_type = obj.get('fluent_type')
        self.reverse = False

        self.slider_origin = None
        self.previous_value = None
        self.other_adjustment = 'THICKNESS'
        self.enter_value = 'None'
        self.original_value = None
        self.init = False

        self.ui_sent = False

        self.solidify = None
        for m in self.obj.modifiers:
            if m.name == fluent_modifiers_name['first_solidify'] and m.type == 'SOLIDIFY':
                self.solidify = m
                break
        if not self.solidify:
            self.add_solidify(default_thickness=default_thickness, default_offset=default_offset)

        # menu
        self.action = None
        self.pie_menu = FLUENT_Ui_Layout('FIRST_SOLIDIFY')
        self.pie_menu.set_layout('PIE')

        button = make_button('VALIDATE')
        self.pie_menu.add_item(button)

        if self.obj is None or self.obj and self.draw_type != 'path':
            button = FLUENT_Ui_Button()
            button.set_text(translate('offsetShortCut'))
            button.set_shape('RECTANGLE')
            button.set_action('OFFSET')
            self.pie_menu.add_item(button)

            button = FLUENT_Ui_Button()
            button.set_text(translate('thicknessShortCut'))
            button.set_shape('RECTANGLE')
            button.set_action('THICKNESS')
            self.pie_menu.add_item(button)

        if self.obj and self.obj.get('fluent_operation') and self.draw_type != 'path':
            button = FLUENT_Ui_Button()
            button.set_text(translate('crossShortCut'))
            button.set_shape('RECTANGLE')
            button.set_action('CROSS')
            self.pie_menu.add_item(button)

    def get_modifier(self):
        return self.solidify

    def set_ui(self, ui):
        ui.hide_menu()
        ui.add_items(self.pie_menu)
        ui.hide_menu()
        self.ui_sent = True

    def get_pie_menu(self):
        return self.pie_menu

    def add_solidify(self, default_thickness=None, default_offset=None):
        self.solidify = self.obj.modifiers.new(name=fluent_modifiers_name['first_solidify'], type='SOLIDIFY')
        self.solidify.show_in_editmode = True
        self.solidify.show_expanded = False
        self.solidify.use_even_offset = True

        if bpy.context.scene.fluentProp.depth:
            self.solidify.thickness = bpy.context.scene.fluentProp.depth
        else:
            self.solidify.thickness = default_thickness if default_thickness is not None else 0
        if self.draw_type == 'sphere':
            self.solidify.thickness = default_thickness if default_thickness is not None else 0
            self.solidify.offset = default_offset if default_offset is not None else -1
            self.solidify.show_render = self.solidify.show_viewport = False
        elif self.draw_type in ['box', 'poly', 'prism']:
            self.solidify.offset = default_offset if default_offset is not None else -.95
        elif self.draw_type == 'path':
            self.solidify.solidify_mode = 'NON_MANIFOLD'
            self.solidify.nonmanifold_thickness_mode = 'EVEN'
            self.solidify.offset = default_offset if default_offset is not None else 0
            self.solidify.thickness = default_thickness if default_thickness is not None else .025
            self.solidify.use_even_offset = True
        place_in_stack(self.obj, self.solidify)

        return self.solidify

    def end_of_adjustment(self):
        self.slider_origin = None
        self.previous_value = None
        self.other_adjustment = 'THICKNESS'
        self.enter_value = 'None'
        self.original_value = None
        self.init = False
        self.ui_sent = False
        if self.solidify.thickness == 0:
            self.solidify.show_render = False
            self.solidify.show_viewport = False

    def adjust_solidify(self, ui: FLUENT_ui_management):
        if not self.ui_sent:
            self.set_ui(ui)
        keys = ui.event_dico_get()
        self.enter_value = enter_value(self.enter_value, keys)

        callback = []

        if not self.init:
            self.slider_origin = keys['mouse_x']
            self.previous_value = self.solidify.thickness
            self.original_value = get_modifier_values(self.solidify)
            self.solidify.show_render = self.solidify.show_viewport = True
            # utilisation du chamfrin ?
            self.reverse = False
            if self.bool_target:
                for m in self.bool_target.modifiers:
                    if m.name == fluent_modifiers_name['pre_chamfer'] and m.show_viewport:
                        self.reverse = True
                        break
            self.init = True

        if keys['shift_work']:
            increment = 3000*get_addon_preferences().interface_factor
        elif keys['ctrl_work']:
            increment = 30*get_addon_preferences().interface_factor
        else:
            increment = 300*get_addon_preferences().interface_factor

        if keys['shift_press'] or keys['shift_release'] or keys['ctrl_press'] or keys['ctrl_release']:
            self.slider_origin = keys['mouse_x']
            if self.other_adjustment == 'THICKNESS':
                self.previous_value = self.solidify.thickness
            elif self.other_adjustment == 'OFFSET':
                self.previous_value = self.solidify.offset

        if self.other_adjustment == 'THICKNESS':
            if keys['type'] == 'MOUSEMOVE' and not keys['show_menu']:
                if self.reverse:
                    self.solidify.thickness = self.previous_value - ((keys['mouse_x'] - self.slider_origin)/increment)
                else:
                    self.solidify.thickness = self.previous_value + ((keys['mouse_x'] - self.slider_origin) / increment)
            if enter_value_validation(self.enter_value, keys)[0]:
                self.solidify.thickness = enter_value_validation(self.enter_value, keys)[1]
                self.end_of_adjustment()
                callback.append('STOP_ADJUSTMENT')
        elif self.other_adjustment == 'OFFSET':
            if keys['type'] == 'MOUSEMOVE' and not keys['show_menu']:
                self.solidify.offset = self.previous_value + ((keys['mouse_x'] - self.slider_origin)/increment)
            if enter_value_validation(self.enter_value, keys)[0]:
                self.solidify.offset = enter_value_validation(self.enter_value, keys)[1]
                self.end_of_adjustment()
                callback.append('STOP_ADJUSTMENT')

        if keys['value'] == 'PRESS' and keys['type'] == 'ESC':
            try:
                set_modifier_value(self.solidify, self.original_value)
            except:pass
            self.end_of_adjustment()
            callback.append('DO_NOT_QUIT_FLUENT')
            callback.append('STOP_ADJUSTMENT')

        if self.solidify.thickness > 0 and self.draw_type != 'path':
            if self.reverse:
                callback.append('BOOL_DIFFERENCE')
            else:
                callback.append('BOOL_UNION')
        elif  self.solidify.thickness < 0 and self.draw_type != 'path':
            if self.reverse:
                callback.append('BOOL_UNION')
            else:
                callback.append('BOOL_DIFFERENCE')

        if self.solidify.offset < -1 :
            self.solidify.offset = -1

        if self.solidify.offset > 1 :
            self.solidify.offset = 1

        # TEXT
        screen_text = []
        if self.other_adjustment == 'THICKNESS':
            screen_text.append([translate('thickness'), adjustment_value(self.solidify.thickness, self.enter_value)])
        else:
            screen_text.append([translate('thickness'), modifier_value_converter(self.solidify.thickness)])
        if self.draw_type != 'path':
            if self.other_adjustment == 'OFFSET':
                screen_text.append([translate('offset'), adjustment_value(self.solidify.offset, self.enter_value)])
            else:
                screen_text.append([translate('offset'), modifier_value_converter(self.solidify.offset)])
            if self.other_adjustment == 'THICKNESS':
                screen_text.append([translate('offset'), 'C'])
            elif self.other_adjustment == 'OFFSET':
                screen_text.append([translate('thickness'), 'C'])
        screen_text.append([translate('slowerFaster'), translate('shiftControl')])

        ui.refresh_side_infos(screen_text)

        self.action = ui.get_button_action()[0]

        if self.action == 'VALIDATE':
            self.end_of_adjustment()
            callback.append('STOP_ADJUSTMENT')
        if self.draw_type in {'box', 'poly', 'prism', 'inset', 'sphere', 'plate'}:
            if (self.other_adjustment == 'OFFSET' and keys['value'] == 'PRESS' and keys['type'] == 'C') or self.action == 'THICKNESS':
                self.other_adjustment = 'THICKNESS'
                self.previous_value = self.solidify.thickness
                self.slider_origin = keys['mouse_x']
            elif (self.other_adjustment == 'THICKNESS' and keys['value'] == 'PRESS' and keys['type'] == 'C') or self.action == 'OFFSET':
                self.other_adjustment = 'OFFSET'
                self.previous_value = self.solidify.offset
                self.slider_origin = keys['mouse_x']

        if ((keys['value'] == 'PRESS' and keys['type'] == 'V') or self.action == 'CROSS') and self.draw_type != 'sphere' and self.obj and self.obj.get('fluent_operation'):
            if self.draw_type in {'box', 'poly', 'prism'}:
                plus_grand_scalaire = cross_depth_research(self.obj, self.bool_target)
                self.solidify.thickness = plus_grand_scalaire * 1.01 * (2-math.fabs(self.solidify.offset)) * -1
                # self.solidify.thickness = plus_grand_scalaire * 1.01 * (2-math.fabs(self.solidify.offset))
                self.end_of_adjustment()
                callback.append('STOP_ADJUSTMENT')

        return callback


class second_bevel_management():
    # TODO faire une option avant/après le booléen
    # TODO revoir le stack order en fonction d'une création ou d'un boolean
    # TODO problem chevauchement icone dans menu circulaire
    def __init__(self, obj):
        self.obj = obj
        self.bevel = {
            'top':None,
            'bottom':None,
            'pre_top':None,
            'pre_bottom':None,
            'active_pre_bevel':None,
            'active_bevel':None
        }
        self.adjust_what = 'BOTH' #BOTH, TOP or BOTTOM
        self.inib_top = False
        if obj.get('fluent_type') == 'revolver':
            self.inib_top = True
        self.slider_origin = None
        self.previous_value = None
        self.other_adjustment = 'WIDTH'
        self.enter_value = 'None'
        self.original_value = None
        self.init = False
        self.prevent_auto_segments = False

        self.ui_sent = False

        for m in self.obj.modifiers:
            if m.name == fluent_modifiers_name['second_bevel_top'] and m.type == 'BEVEL':
                self.bevel['top'] = m
            if m.name == fluent_modifiers_name['second_bevel_bottom'] and m.type == 'BEVEL':
                self.bevel['bottom'] = m
            if m.name == fluent_modifiers_name['pre_second_bevel_bottom']:
                self.bevel['pre_bottom'] = m
            if m.name == fluent_modifiers_name['pre_second_bevel_top']:
                self.bevel['pre_top'] = m

            if self.bevel['top'] and self.bevel['bottom'] and self.bevel['pre_bottom'] and self.bevel['pre_top']:
                break

        if not self.bevel['top'] and not self.bevel['bottom']:
            self.add_second_bevel()

        # affichage
        self.pie_menu = None
        self.action = None

        self.pie_menu = FLUENT_Ui_Layout('FIRST_BEVEL')
        self.pie_menu.set_layout('PIE')

        button = make_button('VALIDATE')
        self.pie_menu.add_item(button)

        button = FLUENT_Ui_Button()
        button.set_text('')
        button.set_tool_tip(translate('widthShortCut'))
        button.set_shape('CIRCLE')
        button.set_action('WIDTH')
        button.set_icon('thickness')
        self.pie_menu.add_item(button)

        button = FLUENT_Ui_Button()
        button.set_text('')
        button.set_tool_tip(translate('segmentsShortCut'))
        button.set_shape('CIRCLE')
        button.set_action('SEGMENTS')
        button.set_icon('resolution')
        self.pie_menu.add_item(button)

        button = FLUENT_Ui_Button()
        button.set_text('')
        button.set_tool_tip(translate('angleLimit'))
        button.set_shape('CIRCLE')
        button.set_action('ANGLE_LIMIT')
        button.set_icon('angle')
        self.pie_menu.add_item(button)

        button = FLUENT_Ui_Button()
        button.set_text('')
        button.set_tool_tip(translate('straightShortCut'))
        button.set_shape('CIRCLE')
        button.set_action('STRAIGHT')
        button.set_icon('straight')
        self.pie_menu.add_item(button)

        button = FLUENT_Ui_Button()
        button.set_text('')
        button.set_tool_tip(translate('concaveShortCut'))
        button.set_shape('CIRCLE')
        button.set_action('CONCAVE')
        button.set_icon('convexe')
        self.pie_menu.add_item(button)

        button = FLUENT_Ui_Button()
        button.set_text('')
        button.set_tool_tip(translate('convexShortCut'))
        button.set_shape('CIRCLE')
        button.set_action('CONVEX')
        button.set_icon('concave')
        self.pie_menu.add_item(button)

        button = FLUENT_Ui_Button(name='BOTH')
        button.set_text('')
        button.set_tool_tip(translate('bothShortCut'))
        button.set_shape('CIRCLE')
        button.set_action('SIDE_BOTH')
        button.set_icon('both_face')
        self.pie_menu.add_item(button)

        button = FLUENT_Ui_Button(name='TOP')
        button.set_text('')
        button.set_tool_tip(translate('topShortCut'))
        button.set_shape('CIRCLE')
        button.set_action('SIDE_TOP')
        button.set_icon('top_face')
        self.pie_menu.add_item(button)

        button = FLUENT_Ui_Button(name='BOTTOM')
        button.set_text('')
        button.set_tool_tip(translate('bottomShortCut'))
        button.set_shape('CIRCLE')
        button.set_action('SIDE_BOTTOM')
        button.set_icon('bottom_face')
        self.pie_menu.add_item(button)

    def add_pre_modifier(self, orientation):
        main_dir = join(dirname(realpath(__file__)))
        blender_dir = join(main_dir, 'geometry_nodes')
        blender_file = join(blender_dir, 'second_bevel.blend')
        file_path_node_tree = join(blender_file, 'NodeTree')

        group_name = '.f_Pre_Second_Bevel'
        if not bpy.data.node_groups.get(group_name):
            bpy.ops.wm.append(filename=group_name, directory=file_path_node_tree)

        if orientation == 'BOTTOM':
            bevel_name = fluent_modifiers_name['pre_second_bevel_bottom']
        if orientation == 'TOP':
            bevel_name = fluent_modifiers_name['pre_second_bevel_top']
        pre_second_bevel = self.obj.modifiers.new(name=bevel_name, type='NODES')
        pre_second_bevel.node_group = bpy.data.node_groups[group_name]
        if orientation == 'BOTTOM':
            pre_second_bevel['Input_5'] = False
        if orientation == 'TOP':
            pre_second_bevel['Input_5'] = True
        pre_second_bevel['Input_4'] = 0.0
        pre_second_bevel['Input_8'] = False
        pre_second_bevel.show_in_editmode = True
        pre_second_bevel.show_expanded = False

        place_in_stack(self.obj, pre_second_bevel)

        return pre_second_bevel

    def initialize_a_modifier(self, target):
        target.show_expanded = False
        target.limit_method = 'WEIGHT'
        target.angle_limit = 0.523599
        target.width = 1.0
        if bpy.context.scene.fluentProp.second_bevel_straight:
            target.segments = 2
            target.profile = 0.25
        # else:
        #     target.segments = auto_bevel_segments(bevel=target)
        target.use_clamp_overlap = get_addon_preferences().clamp_overlap
        target.miter_outer = 'MITER_ARC'
        if bpy.context.scene.fluentProp.second_bevel_width:
            target.show_viewport = True
            target.show_render = True
        else:
            target.show_viewport = False
            target.show_render = False

        place_in_stack(self.obj, target)

    def add_second_bevel(self):
        for vg in self.obj.vertex_groups:
            if vg.name in ['bottom']:
                self.obj.vertex_groups.remove(vg)
        v_group_bottom = self.obj.vertex_groups.new(name='bottom_face')

        self.bevel['pre_bottom'] = self.add_pre_modifier('BOTTOM')
        self.bevel['bottom'] = self.obj.modifiers.new(name=fluent_modifiers_name['second_bevel_bottom'], type='BEVEL')
        self.initialize_a_modifier(self.bevel['bottom'])
        self.bevel['pre_top'] = self.add_pre_modifier('TOP')
        self.bevel['top'] = self.obj.modifiers.new(name=fluent_modifiers_name['second_bevel_top'], type='BEVEL')
        self.initialize_a_modifier(self.bevel['top'])

        self.adjust_what = self.swap('BOTH')

        if self.obj.get('fluent_operation'):
            hide_object(self.obj, 'VIEWPORT')

    def swap(self, to = None):
        if to == 'BOTH':
            self.bevel['pre_bottom']['Input_8'] = True
            self.bevel['active_pre_bevel'] = 'pre_bottom'
            self.bevel['active_bevel'] = 'bottom'
            self.bevel['top'].show_render = self.bevel['top'].show_viewport = False
            self.bevel['pre_top'].show_render = self.bevel['pre_top'].show_viewport = False

        if to == 'TOP':
            self.bevel['pre_bottom']['Input_8'] = False
            self.bevel['active_pre_bevel'] = 'pre_top'
            self.bevel['active_bevel'] = 'top'

        if to == 'BOTTOM':
            self.bevel['pre_bottom']['Input_8'] = False
            self.bevel['active_pre_bevel'] = 'pre_bottom'
            self.bevel['active_bevel'] = 'bottom'

        self.bevel[self.bevel['active_pre_bevel']].show_render = True
        self.bevel[self.bevel['active_pre_bevel']].show_viewport = True
        self.bevel[self.bevel['active_bevel']].show_render = True
        self.bevel[self.bevel['active_bevel']].show_viewport = True

        return to

    def set_ui(self, ui):
        ui.hide_menu()
        ui.add_items(self.pie_menu)
        ui.hide_menu()
        self.ui_sent = True

    def get_modifier(self):
        return self.bevel

    def end_of_adjustment(self):
        self.slider_origin = None
        self.previous_value = None
        self.other_adjustment = 'WIDTH'
        self.enter_value = 'None'
        self.original_value = None
        if self.bevel['top'].width == 0:
            self.bevel['top'].show_viewport = False
            self.bevel['top'].show_render = False
        if self.bevel['bottom'].width == 0:
            self.bevel['bottom'].show_viewport = False
            self.bevel['bottom'].show_render = False
        self.init = False
        self.inib_top = False
        self.ui_sent = False

    def toggle_bevel_position(self):
        bevel_index = None
        first_bool_index = None
        for i, m in enumerate(self.obj.modifiers):
            if not first_bool_index and m.type == 'BOOLEAN':
                first_bool_index = i
            if not bevel_index and m.name == fluent_modifiers_name['second_bevel_top']:
                bevel_index = i

        if first_bool_index and bevel_index:
            show_object(self.obj, 'VIEWPORT')
            active_object('SET', self.obj, True)
            if bevel_index < first_bool_index:
                bpy.ops.object.modifier_move_to_index(modifier=self.bevel.name, index=first_bool_index)
                bpy.ops.object.modifier_move_to_index(modifier=self.pre_bevel.name, index=first_bool_index - 1)
                hide_object(self.obj, 'VIEWPORT')
            if bevel_index > first_bool_index:
                place_in_stack(self.obj, self.pre_bevel)
                place_in_stack(self.obj, self.bevel)
            hide_object(self.obj, 'VIEWPORT')

    def adjust_bevel(self, ui: FLUENT_ui_management):
        if not self.ui_sent:
            self.set_ui(ui)
        keys = ui.event_dico_get()
        self.enter_value = enter_value(self.enter_value, keys)

        callback = []

        if not self.init:
            self.swap(self.adjust_what)
            self.slider_origin = keys['mouse_x']
            self.previous_value = self.bevel[self.bevel['active_pre_bevel']]['Input_4']
            self.original_value = {
                'top': get_modifier_values(self.bevel['top']),
                'bottom': get_modifier_values(self.bevel['bottom']),
                'pre_top': get_modifier_values(self.bevel['pre_top']),
                'pre_bottom': get_modifier_values(self.bevel['pre_bottom']),
            }
            for m in self.obj.modifiers:
                if m.name == fluent_modifiers_name['chamfer'] and m.show_viewport:
                    self.adjust_what = self.swap('BOTTOM')
                    self.inib_top = True
                    break
            if self.inib_top:
                self.pie_menu.remove_item('BOTH')
                self.pie_menu.remove_item('TOP')
                self.pie_menu.remove_item('BOTTOM')
            else:
                is_both = False
                is_top = False
                is_bottom = False
                for i in self.pie_menu.get_items():
                    if i.get_id() == 'BOTH':
                        is_both = True
                    if i.get_id() == 'TOP':
                        is_top = True
                    if i.get_id() == 'BOTTOM':
                        is_bottom = True
                if not is_both:
                    button = FLUENT_Ui_Button(name='BOTH')
                    button.set_text('')
                    button.set_tool_tip(translate('bothShortCut'))
                    button.set_shape('CIRCLE')
                    button.set_action('SIDE_BOTH')
                    button.set_icon('both_face')
                    self.pie_menu.add_item(button)
                if not is_top:
                    button = FLUENT_Ui_Button(name='TOP')
                    button.set_text('')
                    button.set_tool_tip(translate('topShortCut'))
                    button.set_shape('CIRCLE')
                    button.set_action('SIDE_TOP')
                    button.set_icon('top_face')
                    self.pie_menu.add_item(button)
                if not is_bottom:
                    button = FLUENT_Ui_Button(name='BOTTOM')
                    button.set_text('')
                    button.set_tool_tip(translate('bottomShortCut'))
                    button.set_shape('CIRCLE')
                    button.set_action('SIDE_BOTTOM')
                    button.set_icon('bottom_face')
                    self.pie_menu.add_item(button)
            self.init = True

        if keys['shift_work']:
            increment = 5000*get_addon_preferences().interface_factor
        elif keys['ctrl_work']:
            increment = 50*get_addon_preferences().interface_factor
        else:
            increment = 500*get_addon_preferences().interface_factor

        if keys['shift_press'] or keys['shift_release'] or keys['ctrl_press'] or keys['ctrl_release']:
            self.slider_origin = keys['mouse_x']
            if self.other_adjustment == 'WIDTH':
                self.previous_value = self.bevel[self.bevel['active_pre_bevel']]['Input_4']
            elif self.other_adjustment == 'ANGLE_LIMIT':
                self.previous_value = self.bevel[self.bevel['active_pre_bevel']]['Input_9']
            elif self.other_adjustment == 'SEGMENTS':
                self.previous_value = self.bevel[self.bevel['active_bevel']].segments

        if keys['value'] == 'PRESS' and keys['type'] == 'C':
            bevel_type = None
            if self.bevel[self.bevel['active_bevel']].segments > 2 and round(self.bevel[self.bevel['active_bevel']].profile, 2) != 0.08:
                bevel_type = 'convex'
            elif self.bevel[self.bevel['active_bevel']].segments in {1, 2}:
                bevel_type = 'straight'
            elif self.bevel[self.bevel['active_bevel']].segments != 1 and round(self.bevel[self.bevel['active_bevel']].profile, 2) == 0.08:
                bevel_type = 'concave'
            if bevel_type == 'convex':
                self.action = 'STRAIGHT'
            elif bevel_type == 'straight':
                self.action = 'CONCAVE'
            elif bevel_type == 'concave':
                self.action = 'CONVEX'

        if keys['type'] == 'V' and keys['value'] == 'PRESS':
            if self.other_adjustment == 'WIDTH':
                self.action = 'SEGMENTS'
            elif self.other_adjustment == 'SEGMENTS':
                self.action = 'WIDTH'

        if keys['value'] == 'PRESS' and keys['type'] == 'B':
            self.action = 'STRAIGHT_1'

        # if keys['value'] == 'PRESS' and keys['type'] == 'V':
        #     self.action = 'TOGGLE'

        if self.action == 'STRAIGHT_1':
            if self.bevel[self.bevel['active_bevel']].segments == 2:
                self.bevel[self.bevel['active_bevel']].segments = 1
                self.bevel[self.bevel['active_bevel']].profile = 0.25
            elif self.bevel[self.bevel['active_bevel']].segments == 1:
                self.bevel[self.bevel['active_bevel']].segments = 2
                self.bevel[self.bevel['active_bevel']].profile = 0.25
        elif self.action == 'STRAIGHT':
            self.bevel[self.bevel['active_bevel']].segments = 2
            self.bevel[self.bevel['active_bevel']].profile = 0.25
        elif self.action == 'CONCAVE':
            self.bevel[self.bevel['active_bevel']].segments = auto_bevel_segments(pre_bevel=self.bevel[self.bevel['active_pre_bevel']])
            self.bevel[self.bevel['active_bevel']].profile = 0.08
        elif self.action == 'CONVEX':
            self.bevel[self.bevel['active_bevel']].segments = auto_bevel_segments(pre_bevel=self.bevel[self.bevel['active_pre_bevel']])
            self.bevel[self.bevel['active_bevel']].profile = bpy.context.scene.fluentProp.bevel_profile
        elif self.action == 'ANGLE_LIMIT':
            self.other_adjustment = 'ANGLE_LIMIT'
            self.previous_value = self.bevel[self.bevel['active_pre_bevel']]['Input_9']
            self.slider_origin = keys['mouse_x']
        elif self.action == 'SEGMENTS':
            self.other_adjustment = 'SEGMENTS'
            self.previous_value = self.bevel[self.bevel['active_bevel']].segments
            self.slider_origin = keys['mouse_x']
        elif self.action == 'WIDTH':
            self.other_adjustment = 'WIDTH'
            self.previous_value = self.bevel[self.bevel['active_pre_bevel']]['Input_4']
            self.slider_origin = keys['mouse_x']
        # elif self.action == 'TOGGLE':
        #     self.toggle_bevel_position()


        if keys['type'] == 'MOUSEMOVE':
            if self.other_adjustment == 'WIDTH' and not keys['show_menu']:
                value = self.previous_value + ((keys['mouse_x'] - self.slider_origin)/increment)
                if value < 0: value = 0
                self.bevel[self.bevel['active_pre_bevel']]['Input_4'] = value
            elif self.other_adjustment == 'ANGLE_LIMIT' and not keys['show_menu']:
                value = self.previous_value + ((keys['mouse_x'] - self.slider_origin)/increment)
                if value < 0 : value = 0
                self.bevel[self.bevel['active_pre_bevel']]['Input_9'] = value
            elif self.other_adjustment == 'SEGMENTS' and not keys['show_menu']:
                self.bevel[self.bevel['active_bevel']].segments = int(self.previous_value + ((keys['mouse_x'] - self.slider_origin)/(increment/5)))
                self.prevent_auto_segments = True
        if enter_value_validation(self.enter_value, keys)[0]:
            if self.other_adjustment == 'WIDTH':
                self.bevel[self.bevel['active_pre_bevel']]['Input_4'] = enter_value_validation(self.enter_value, keys)[1]
            elif self.other_adjustment == 'ANGLE_LIMIT':
                self.bevel[self.bevel['active_bevel']].angle_limit = math.radians(enter_value_validation(self.enter_value, keys)[1])
            if self.other_adjustment == 'SEGMENTS':
                self.bevel[self.bevel['active_bevel']].segments = int(enter_value_validation(self.enter_value, keys)[1])
            callback.append('STOP_ADJUSTMENT')
            self.end_of_adjustment()

        if self.bevel[self.bevel['active_bevel']].profile != 0.25:
            if not self.prevent_auto_segments:
                self.bevel[self.bevel['active_bevel']].segments = auto_bevel_segments(pre_bevel=self.bevel[self.bevel['active_pre_bevel']])

        if self.bevel[self.bevel['active_pre_bevel']]['Input_4'] == 0:
            self.bevel[self.bevel['active_pre_bevel']].show_viewport = False
            self.bevel[self.bevel['active_pre_bevel']].show_render = False
            self.bevel[self.bevel['active_bevel']].show_viewport = False
            self.bevel[self.bevel['active_bevel']].show_render = False
        else:
            self.bevel[self.bevel['active_pre_bevel']].show_viewport = True
            self.bevel[self.bevel['active_pre_bevel']].show_render = True
            self.bevel[self.bevel['active_bevel']].show_viewport = True
            self.bevel[self.bevel['active_bevel']].show_render = True

        if not self.inib_top and keys['value'] == 'PRESS' and keys['type'] == 'X':
            if self.adjust_what == 'BOTH':
                self.adjust_what = self.swap('TOP')
            elif self.adjust_what == 'TOP':
                self.adjust_what = self.swap('BOTTOM')
            elif self.adjust_what == 'BOTTOM':
                self.adjust_what = self.swap('BOTH')
            self.previous_value = self.bevel[self.bevel['active_pre_bevel']]['Input_4']
            self.slider_origin = keys['mouse_x']

        if keys['value'] == 'PRESS' and keys['type'] == 'ESC':
            try:
                set_modifier_value(self.bevel['top'], self.original_value['top'])
                set_modifier_value(self.bevel['bottom'], self.original_value['bottom'])
            except:pass
            self.end_of_adjustment()
            callback.append('DO_NOT_QUIT_FLUENT')
            callback.append('STOP_ADJUSTMENT')

        # TEXT
        screen_text = []
        if self.inib_top:
            screen_text.append([translate('side'), self.adjust_what])
        else:
            screen_text.append([translate('side') + ' (X)', self.adjust_what])
        if self.other_adjustment == 'WIDTH':
            screen_text.append([translate('width'), adjustment_value(self.bevel[self.bevel['active_pre_bevel']]['Input_4'], self.enter_value)])
        else:
            screen_text.append([translate('width'), modifier_value_converter(self.bevel[self.bevel['active_pre_bevel']]['Input_4'])])
        if self.other_adjustment == 'SEGMENTS':
            screen_text.append([translate('segments'), adjustment_value(self.bevel[self.bevel['active_bevel']].segments, self.enter_value)])
        else:
            screen_text.append([translate('segments'), modifier_value_converter(self.bevel[self.bevel['active_bevel']].segments)])
        if self.other_adjustment == 'ANGLE_LIMIT':
            screen_text.append([translate('angleLimit'), adjustment_value(self.bevel[self.bevel['active_pre_bevel']]['Input_9'], self.enter_value)])
        else:
            screen_text.append([translate('angleLimit'), modifier_value_converter(self.bevel[self.bevel['active_pre_bevel']]['Input_9'])])
        screen_text.append([translate('oneSegment'), 'B'])
        # screen_text.append(['Toggle stack order', 'V'])
        screen_text.append([translate('slowerFaster'), translate('shiftControl')])
        screen_text.append([translate('remove'), translate('delBackSpace')])

        ui.refresh_side_infos(screen_text)
        self.action = ui.get_button_action()[0]

        if self.action == 'VALIDATE':
            self.end_of_adjustment()
            callback.append('STOP_ADJUSTMENT')
        if self.action in ['STRAIGHT', 'CONCAVE', 'CONVEX']:
            self.slider_origin = keys['mouse_x']
            self.previous_value = self.bevel[self.bevel['active_pre_bevel']]['Input_4']
        if self.action in ['SIDE_BOTH', 'SIDE_TOP', 'SIDE_BOTTOM']:
            self.adjust_what = self.swap(self.action.split('_')[1])
            self.slider_origin = keys['mouse_x']
            self.previous_value = self.bevel[self.bevel['active_pre_bevel']]['Input_4']

        if keys['value'] == 'PRESS' and keys['type'] in {'DEL', 'BACK_SPACE'}:
            self.bevel['top'].show_viewport = self.bevel['top'].show_render = False
            self.bevel['bottom'].show_viewport = self.bevel['bottom'].show_render = False
            self.bevel['pre_top'].show_viewport = self.bevel['pre_top'].show_render = False
            self.bevel['pre_bottom'].show_viewport = self.bevel['pre_bottom'].show_render = False
            self.action = 'VALIDATE'
            self.end_of_adjustment()
            screen_text = []
            callback.append('STOP_ADJUSTMENT')

        return callback


class second_solidify_management():
    def __init__(self, obj):
        self.obj = obj
        self.draw_type = None
        self.solidify = None
        self.slider_origin = None
        self.previous_value = None
        self.other_adjustment = None
        self.enter_value = 'None'
        self.original_value = None
        self.init = False

        # affichage
        self.pie_menu = None
        self.action = None
        self.ui_sent = False

        self.pie_menu = FLUENT_Ui_Layout('SECOND_SOLIDIFY')
        self.pie_menu.set_layout('PIE')

        button = make_button('VALIDATE')
        self.pie_menu.add_item(button)

        button = FLUENT_Ui_Button()
        button.set_text(translate('fakeSlice'))
        button.set_shape('RECTANGLE')
        button.set_action('FAKE_SLICE')
        self.pie_menu.add_item(button)

    def get_pie_menu(self):
        return self.pie_menu

    def set_ui(self, ui):
        ui.hide_menu()
        ui.add_items(self.pie_menu)
        ui.hide_menu()
        self.ui_sent = True

    def get_modifier(self):
        return self.solidify

    def initiation(self):
        for m in self.obj.modifiers:
            if m.name == fluent_modifiers_name['second_solidify'] and m.type == 'SOLIDIFY':
                self.solidify = m
                break
        return self.solidify

    def add_solidify(self, default_thickness=-0.01, default_offset=0, show=False):
        self.initiation()
        if not self.solidify:
            self.solidify = self.obj.modifiers.new(name=fluent_modifiers_name['second_solidify'], type='SOLIDIFY')
            self.solidify.offset = default_offset
            self.solidify.thickness = default_thickness
            self.solidify.use_even_offset = True
            self.solidify.show_viewport = show
            self.solidify.show_render = show
            self.solidify.show_expanded = False
            place_in_stack(self.obj, self.solidify)

    def end_of_adjustment(self):
        self.slider_origin = None
        self.previous_value = None
        self.other_adjustment = None
        self.enter_value = 'None'
        self.original_value = None
        self.init = False
        self.ui_sent = False

    def adjust_solidify(self, ui: FLUENT_ui_management):
        if not self.ui_sent:
            self.set_ui(ui)

        keys = ui.event_dico_get()

        self.enter_value = enter_value(self.enter_value, keys)

        callback = []
        if not self.init:
            self.add_solidify()
            self.slider_origin = keys['mouse_x']
            self.previous_value = self.solidify.thickness
            self.original_value = get_modifier_values(self.solidify)
            self.init = True

        if keys['shift_work']:
            increment = 10000*get_addon_preferences().interface_factor
        elif keys['ctrl_work']:
            increment = 100*get_addon_preferences().interface_factor
        else:
            increment = 1000*get_addon_preferences().interface_factor
        if keys['shift_press'] or keys['shift_release'] or keys['ctrl_press'] or keys['ctrl_release']:
            self.slider_origin = keys['mouse_x']
            self.previous_value = self.solidify.thickness
        if keys['type'] == 'MOUSEMOVE' and not keys['show_menu']:
            self.solidify.thickness = self.previous_value - ((keys['mouse_x'] - self.slider_origin)/increment)
        if enter_value_validation(self.enter_value, keys)[0]:
            self.solidify.thickness = enter_value_validation(self.enter_value, keys)[1]
            callback.append('STOP_ADJUSTMENT')
            self.end_of_adjustment()

        if self.solidify.thickness != 0:
            self.solidify.show_viewport = True
            self.solidify.show_render = True

        if keys['value'] == 'PRESS' and keys['type'] == 'ESC':
            try:
                set_modifier_value(self.solidify, self.original_value)
            except:pass
            self.end_of_adjustment()
            callback.append('DO_NOT_QUIT_FLUENT')
            callback.append('STOP_ADJUSTMENT')

        # TEXT
        screen_text = []
        screen_text.append([translate('thickness'), adjustment_value(self.solidify.thickness, self.enter_value)])
        screen_text.append([translate('remove'), 'Del'])
        screen_text.append([translate('slowerFaster'), translate('shiftControl')])

        self.action = ui.get_button_action()[0]

        if self.action == 'VALIDATE':
            self.end_of_adjustment()
            screen_text = []
            callback.append('STOP_ADJUSTMENT')
        else:
            self.slider_origin = keys['mouse_x']
            self.previous_value = self.solidify.thickness

        if self.action == 'FAKE_SLICE':
            self.solidify.thickness = .001
            callback.append('STOP_ADJUSTMENT')
            self.end_of_adjustment()

        if keys['value'] == 'PRESS' and keys['type'] in {'DEL', 'BACK_SPACE'}:
            self.solidify.show_viewport = False
            self.solidify.show_render = False
            self.action = 'VALIDATE'
            self.end_of_adjustment()
            screen_text = []
            callback.append('STOP_ADJUSTMENT')

        ui.refresh_side_infos(screen_text)
        recalculate_array_center(self.obj)

        return callback


class first_bevel_management():
    def __init__(self, obj, with_dots=True):
        self.obj = obj
        self.with_dots = with_dots
        if self.with_dots:
            self.obj_transformed = self.prepare_transformed_obj(obj)
        self.bevels = []
        self.slider_origin = None
        self.previous_value = None
        self.enter_value = 'None'
        self.original_value = []
        self.bevel_vertex_list = [] #rempli avec des tableaux : [vertex index, n° du vertex group]
        self.init = False
        self.prevent_auto_segments = False
        self.other_adjustment = 'WIDTH'

        # affichage
        self.pie_menu = None
        self.action = None
        self.ui_sent = False

        self.pie_menu = FLUENT_Ui_Layout('FIRST_BEVEL')
        self.pie_menu.set_layout('PIE')

        button = make_button('VALIDATE')
        self.pie_menu.add_item(button)

        button = FLUENT_Ui_Button()
        button.set_text(translate('widthShortCut'))
        button.set_shape('RECTANGLE')
        button.set_action('WIDTH')
        self.pie_menu.add_item(button)

        button = FLUENT_Ui_Button()
        button.set_text(translate('segmentsShortCut'))
        button.set_shape('RECTANGLE')
        button.set_action('SEGMENT')
        self.pie_menu.add_item(button)

        button = FLUENT_Ui_Button()
        button.set_text(translate('straightShortCut'))
        button.set_shape('RECTANGLE')
        button.set_action('STRAIGHT')
        self.pie_menu.add_item(button)

        button = FLUENT_Ui_Button()
        button.set_text(translate('concaveShortCut'))
        button.set_shape('RECTANGLE')
        button.set_action('CONCAVE')
        self.pie_menu.add_item(button)

        button = FLUENT_Ui_Button()
        button.set_text(translate('convexShortCut'))
        button.set_shape('RECTANGLE')
        button.set_action('CONVEX')
        self.pie_menu.add_item(button)

    def prepare_transformed_obj(self, obj):
        show_object(obj, 'DISABLE')
        transformed_obj = duplicate(obj)
        for m in transformed_obj.modifiers:
            if m.name not in [fluent_modifiers_name['scale'], fluent_modifiers_name['rotate']]:
                transformed_obj.modifiers.remove(m)
        show_object(transformed_obj, 'VIEWPORT')
        active_object('SET', transformed_obj, True)
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.convert(target="MESH")
        hide_object(transformed_obj, 'VIEWPORT')

        return transformed_obj

    def get_pie_menu(self):
        return self.pie_menu

    def set_ui(self, ui):
        ui.hide_menu()
        ui.add_items(self.pie_menu)
        ui.add_dots_items()
        ui.hide_menu()
        self.ui_sent = True

    def get_modifier(self):
        return self.bevels

    def initiation(self):
        for m in self.obj.modifiers:
            if fluent_modifiers_name['first_bevel'] in m.name and m.type == 'BEVEL':
                self.bevels.append(m)
        return self.bevels

    def get_vertex_list(self):
        return self.bevel_vertex_list

    def refresh_dots(self, ui: FLUENT_ui_management):
        dots = ui.get_dots()
        dots.clear_dots('3D')
        matrix = self.obj_transformed.matrix_world
        for i, v in enumerate(self.obj_transformed.data.vertices):
            co_3d = matrix @ v.co
            color = (0, 0, 0, 1)
            for b in self.bevel_vertex_list:
                if b[0] == v.index:
                    color = (1, 1, 1, 1)
            dots.add_3d_dot(co_3d, 5 * get_addon_preferences().interface_factor, color)

    def end_of_adjustment(self, ui: FLUENT_ui_management):
        self.slider_origin = None
        self.previous_value = None
        self.enter_value = 'None'
        self.original_value = []
        self.bevel_vertex_list = []
        self.init = False
        self.ui_sent = False
        self.other_adjustment = 'WIDTH'
        ui.clear_dots()
        if self.with_dots:
            bpy.data.objects.remove(self.obj_transformed, do_unlink=True)
        self.obj_transformed = None
        dots = ui.get_dots()
        dots.clear_dots('3D')

    def add_bevel(self, default_width = 0, default_profile = None):
        self.initiation()
        if len(self.bevels): return
        try:
            # supprime les vertex goup first bevel si déjà présent
            for vg in self.obj.vertex_groups:
                if 'first_bevel' in vg.name:
                    self.obj.vertex_groups.remove(vg)
        except:pass
        if len(self.bevels) == 0:
            active_object('SET', self.obj, True)
            bm = bmesh.new()
            bm.from_mesh(self.obj.data)
            bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(5), use_dissolve_boundaries=False, verts=bm.verts, edges=bm.edges)
            bm.to_mesh(self.obj.data)
            self.obj.data.update()
            bm.clear()
            bm.free()

            beveled_vertices = []
            i = 0
            for v in self.obj.data.vertices:
                # un vertex recevant un bevel ne peut pas appartenir à plus de 2 edges
                v_in_e_count = 0
                for e in self.obj.data.edges:
                    if e.vertices[0] == v.index or e.vertices[1] == v.index:
                        v_in_e_count += 1
                if v_in_e_count == 2:
                    beveled_vertices.append(v)

                    v_group = self.obj.vertex_groups.new(name='first_bevel.' + str(i))
                    v_group.add([v.index], 1, 'ADD')

                    modif = self.obj.modifiers.new(name=fluent_modifiers_name['first_bevel'] + str(i), type='BEVEL')
                    modif.show_in_editmode = False
                    modif.show_expanded = False
                    modif.limit_method = 'VGROUP'
                    modif.vertex_group = v_group.name
                    modif.affect = 'VERTICES'
                    modif.width = default_width
                    modif.use_clamp_overlap = get_addon_preferences().clamp_overlap
                    modif.loop_slide = False

                    if default_profile == 0.25:
                        modif.segments = 2
                        modif.profile = 0.25
                    elif default_profile == 0.08:
                        modif.segments = auto_bevel_segments(modif)
                        modif.profile = 0.08
                    elif default_profile == None or default_profile == bpy.context.scene.fluentProp.bevel_profile:
                        modif.segments = auto_bevel_segments(modif)
                        modif.profile = bpy.context.scene.fluentProp.bevel_profile

                    self.bevels.append(modif)

                    if modif.width == 0:
                        modif.show_viewport = False
                        modif.show_render = False
                    else:
                        modif.show_viewport = True
                        modif.show_render = True
                    place_in_stack(self.obj, modif)
                    i += 1

    def adjust_bevel(self, ui: FLUENT_ui_management):
        if not self.ui_sent:
            self.set_ui(ui)

        keys = ui.event_dico_get()
        self.enter_value = enter_value(self.enter_value, keys)
        callback = []
        end_after_order = False

        if not self.slider_origin:
            self.slider_origin = keys['mouse_x']

        if not self.init:
            self.add_bevel()
            if not self.obj_transformed and self.with_dots:
                self.obj_transformed = self.prepare_transformed_obj(self.obj)
            if self.obj.get('fluent_operation'):
                hide_object(self.obj, 'VIEWPORT')
            diff = False
            b_value = []
            vg_count = 0
            for v in self.obj.vertex_groups:
                if 'first_bevel' in v.name:
                    vg_count+=1
            for i in range(vg_count):
                b_value.append(self.obj.modifiers[fluent_modifiers_name['first_bevel']+str(i)].width)
            i=0
            for w in b_value:
                try:
                    if b_value[i] != b_value[i+1]:
                        diff = True
                except:pass
                i+=1
            i=0
            if not diff:
                for v in self.obj.data.vertices:
                    for v_group in self.obj.vertex_groups:
                        try:
                            if v_group.weight(v.index):
                                self.bevel_vertex_list.append([v.index, i])
                                i+=1
                                break
                        except:pass

            try:
                self.previous_value = self.obj.modifiers[fluent_modifiers_name['first_bevel']+str(self.bevel_vertex_list[0][1])].width
            except:pass

            self.original_value = []
            for b in self.bevels:
                self.original_value.append(get_modifier_values(b))

            if self.with_dots:
                self.refresh_dots(ui)
            self.init = True
        # FIN Initialisation

        # ui.refresh_dots(self.obj_transformed, self.bevel_vertex_list)

        if self.action == 'WIDTH':
            self.other_adjustment = 'WIDTH'
            self.slider_origin = keys['mouse_x']
            try:
                for m in self.obj.modifiers:
                    if fluent_modifiers_name['first_bevel'] in m.name and m.show_viewport:
                        self.previous_value = m.width
                        break
            except:
                pass
        elif self.action == 'SEGMENT':
            self.other_adjustment = 'SEGMENT'
            self.slider_origin = keys['mouse_x']
            try:
                for m in self.obj.modifiers:
                    if fluent_modifiers_name['first_bevel'] in m.name and m.show_viewport:
                        self.previous_value = m.segments
                        break
            except:
                pass

        if keys['value'] == 'PRESS' and keys['type'] == 'X' and self.with_dots:
            self.slider_origin = keys['mouse_x']
            region = bpy.context.region
            rv3d = bpy.context.region_data
            matrix = self.obj_transformed.matrix_world.copy()
            nearby = 10000
            candidate = None
            # try:
            # recherche du vertex le plus proche de la souris
            for v in self.obj_transformed.data.vertices:
                co_3d = matrix @ v.co
                co_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, co_3d)
                d = distance(x=co_2d.x, y=co_2d.y, xx=keys['mouse_x'], yy=keys['mouse_y'])
                if d < nearby:
                    nearby = d
                    candidate = v
            # si le vertex le plus proche est à moins de 32px de la souris
            if nearby <= 32:
                # vérifie si déjà dans la liste active
                j_y_suis = False
                for i, v in enumerate(self.bevel_vertex_list):
                    if v[1] == candidate.index:
                        # si oui on l'enlève
                        del self.bevel_vertex_list[i]
                        j_y_suis = True
                        break
                if not j_y_suis:
                    # sinon on l'ajoute
                    for i, v_group in enumerate(self.obj.vertex_groups):
                        try:
                            if v_group.weight(candidate.index):
                                n = v_group.name.split('.')[1]
                                self.bevel_vertex_list.append([candidate.index, n])
                                break
                        except:pass
                if self.bevel_vertex_list:
                    self.previous_value = self.obj.modifiers[fluent_modifiers_name['first_bevel']+str(self.bevel_vertex_list[0][1])].width
            else:
                # bascule entre tout séléctionner et rien
                if self.bevel_vertex_list:
                    self.bevel_vertex_list = []
                else:
                    for v in self.obj.data.vertices:
                        for i, v_group in enumerate(self.obj.vertex_groups):
                            try:
                                if v_group.weight(v.index):
                                    self.bevel_vertex_list.append([v.index, i])
                                    break
                            except:pass
                    self.previous_value = self.obj.modifiers[fluent_modifiers_name['first_bevel']+str(self.bevel_vertex_list[0][1])].width
            if self.with_dots:
                self.refresh_dots(ui)
            # except:pass

        if keys['shift_work']:
            increment = 5000*get_addon_preferences().interface_factor
        elif keys['ctrl_work']:
            increment = 50*get_addon_preferences().interface_factor
        else:
            increment = 500*get_addon_preferences().interface_factor
        if keys['shift_press'] or keys['shift_release'] or keys['ctrl_press'] or keys['ctrl_release']:
            self.slider_origin = keys['mouse_x']
            try:
                for m in self.obj.modifiers:
                    if fluent_modifiers_name['first_bevel'] in m.name and m.show_viewport:
                        if self.other_adjustment == 'WIDTH':
                            self.previous_value = m.width
                        elif self.other_adjustment == 'SEGMENT':
                            self.previous_value = m.segments
                        break
            except:pass
        # try:
        for v in self.bevel_vertex_list:
            modifier_name = fluent_modifiers_name['first_bevel']+str(v[1])
            modif = self.obj.modifiers[modifier_name]
            if keys['type'] == 'MOUSEMOVE' and not keys['show_menu']:
                if self.other_adjustment == 'WIDTH':
                    modif.width = self.previous_value + ((keys['mouse_x'] - self.slider_origin)/increment)
                elif self.other_adjustment == 'SEGMENT':
                    modif.segments = int(self.previous_value + ((keys['mouse_x'] - self.slider_origin) / (increment/5)))
                    self.prevent_auto_segments = True
                if modif.width == 0:
                    modif.show_viewport = False
                    modif.show_render = False
                else:
                    modif.show_viewport = True
                    modif.show_render = True

            if modif.profile != 0.25:
                if not self.prevent_auto_segments:
                    modif.segments = auto_bevel_segments(modif)

            if keys['value'] == 'PRESS' and keys['type'] == 'C':
                bevel_type = None
                if modif.segments > 2 and round(modif.profile, 2) != 0.08:
                    bevel_type = 'convex'
                elif modif.segments in {1, 2}:
                    bevel_type = 'straight'
                elif modif.segments != 1 and round(modif.profile, 2) == 0.08:
                    bevel_type = 'concave'
                if bevel_type == 'convex':
                    self.action = 'STRAIGHT'
                elif bevel_type == 'straight':
                    self.action = 'CONCAVE'
                elif bevel_type == 'concave':
                    self.action = 'CONVEX'

            if keys['value'] == 'PRESS' and keys['type'] == 'B':
                self.action = 'STRAIGHT_01'

            if self.action == 'STRAIGHT':
                modif.segments = 2
                modif.profile = 0.25
            elif self.action == 'CONCAVE':
                modif.segments = auto_bevel_segments(modif)
                modif.profile = 0.08
            elif self.action == 'CONVEX':
                modif.segments = auto_bevel_segments(modif)
                modif.profile = bpy.context.scene.fluentProp.bevel_profile
            elif self.action == 'STRAIGHT_01':
                if modif.segments == 2:
                    modif.segments = 1
                    modif.profile = 0.25
                elif modif.segments == 1:
                    modif.segments = 2
                    modif.profile = 0.25

        if enter_value_validation(self.enter_value, keys)[0]:
            end_after_order = True
            for v in self.bevel_vertex_list:
                modifier_name = fluent_modifiers_name['first_bevel'] + str(v[1])
                modif = self.obj.modifiers[modifier_name]
                if self.other_adjustment == 'WIDTH':
                    modif.width = enter_value_validation(self.enter_value, keys)[1]
                elif self.other_adjustment == 'SEGMENT':
                    modif.segments = int(enter_value_validation(self.enter_value, keys)[1])

        # trie les bevels du plus petit en haut au plus large en bas
        for i, m in enumerate(self.obj.modifiers):
            is_bevel_01 = fluent_modifiers_name['first_bevel'] in m.name
            if is_bevel_01:
                move_count = 0
                for x, b in enumerate(self.bevels):
                    try:
                        next_is_bevel = fluent_modifiers_name['first_bevel'] in self.obj.modifiers[i+x].name
                    except:
                        next_is_bevel = False
                    is_greater = False
                    if next_is_bevel:
                        is_greater = self.obj.modifiers[i].width > self.obj.modifiers[i+x].width
                        if is_greater:
                            move_count = x
                for c in range(move_count):
                    bpy.ops.object.modifier_move_down(modifier=m.name)

        if end_after_order:
            self.end_of_adjustment(ui)
            callback.append('STOP_ADJUSTMENT')

        if keys['value'] == 'PRESS' and keys['type'] == 'ESC':
            for i, b in enumerate(self.bevels):
                set_modifier_value(b, self.original_value[i])
            callback.append('DO_NOT_QUIT_FLUENT')
            callback.append('STOP_ADJUSTMENT')
            self.end_of_adjustment(ui)

        # TEXT
        screen_text = []
        if len(self.bevel_vertex_list):
            modifier_name = fluent_modifiers_name['first_bevel']+str(self.bevel_vertex_list[0][1])
            modif = self.obj.modifiers[modifier_name]
            if self.other_adjustment == 'WIDTH':
                screen_text.append([translate('width'), adjustment_value(modif.width, self.enter_value)])
            else:
                screen_text.append([translate('width'), modifier_value_converter(modif.width)])
            if self.other_adjustment == 'SEGMENT':
                screen_text.append([translate('segments'), adjustment_value(modif.segments, self.enter_value)])
            else:
                screen_text.append([translate('segments'), modifier_value_converter(modif.segments)])
        screen_text.append([translate('vertexSelection'), 'X'])
        screen_text.append([translate('oneSegment'), 'B'])
        screen_text.append([translate('slowerFaster'), translate('shiftControl')])

        self.action = ui.get_button_action()[0]

        if self.action == 'VALIDATE':
            self.end_of_adjustment(ui)
            screen_text = []
            callback.append('STOP_ADJUSTMENT')
        elif self.action is not None:
            self.slider_origin = keys['mouse_x']
            try:
                for m in self.obj.modifiers:
                    if fluent_modifiers_name['first_bevel'] in m.name and m.show_viewport:
                        if self.other_adjustment == 'WIDTH':
                            self.previous_value = m.width
                        elif self.other_adjustment == 'SEGMENT':
                            self.previous_value = m.segments
                        break
            except:pass

        if keys['type'] == 'V' and keys['value'] == 'PRESS':
            if self.other_adjustment == 'WIDTH':
                self.action = 'SEGMENT'
            elif self.other_adjustment == 'SEGMENT':
                self.action = 'WIDTH'

        ui.refresh_side_infos(screen_text)

        return callback


class taper_management():
    def __init__(self, obj):
        self.obj = obj
        self.taper = {'x':None, 'y':None, 'z':None}
        self.array_axis = None
        self.previous_value = None
        self.enter_value = 'None'
        self.original_value = None
        self.backup = {}
        self.init = False

        # affichage
        self.pie_menu = None
        self.action = None
        self.ui_sent = False

        self.pie_menu = FLUENT_Ui_Layout('TAPER')
        self.pie_menu.set_layout('TAPER')
        self.pie_menu.set_obj(self.obj)

        button = make_button('VALIDATE')
        self.pie_menu.add_item(button)

        button = FLUENT_Ui_Button()
        button.set_text('')
        button.set_shape('CIRCLE')
        button.set_action('+X')
        button.set_default_color((.9, 0, 0, 1))
        self.pie_menu.add_item(button)

        button = FLUENT_Ui_Button()
        button.set_text('')
        button.set_shape('CIRCLE')
        button.set_action('+Y')
        button.set_default_color((0, .9, 0, 1))
        self.pie_menu.add_item(button)

        button = FLUENT_Ui_Button()
        button.set_text('')
        button.set_shape('CIRCLE')
        button.set_action('+Z')
        button.set_default_color((0, 0, .9, 1))
        self.pie_menu.add_item(button)

    def set_ui(self, ui):
        ui.hide_menu()
        ui.add_items(self.pie_menu)
        ui.hide_menu()
        self.ui_sent = True

    def get_pie_menu(self):
        return self.pie_menu

    def initiation(self):
        for m in self.obj.modifiers:
            if m.name == fluent_modifiers_name['taper_x'] and m.type == 'SIMPLE_DEFORM':
                self.taper['x'] = m
            elif m.name == fluent_modifiers_name['taper_y'] and m.type == 'SIMPLE_DEFORM':
                self.taper['y'] = m
            elif m.name == fluent_modifiers_name['taper_z'] and m.type == 'SIMPLE_DEFORM':
                self.taper['z'] = m
        return self.taper

    def get_modifier(self):
        return self.taper

    def end_of_adjustment(self):
        self.slider_origin = None
        self.previous_value = None
        self.enter_value = 'None'
        self.original_value = {'axis':None, 'factor':None, 'lock_x':None, 'lock_y':None, 'lock_z':None}
        self.init = False
        self.array_axis = ''
        self.ui_sent = False

    def restore_value(self):
        self.taper['x'].factor = self.original_value['x']['factor']
        self.taper['x'].lock_y = self.original_value['x']['lock_y']
        self.taper['x'].lock_z = self.original_value['x']['lock_z']
        self.taper['y'].factor = self.original_value['y']['factor']
        self.taper['y'].lock_x = self.original_value['y']['lock_x']
        self.taper['y'].lock_z = self.original_value['y']['lock_z']
        self.taper['z'].factor = self.original_value['z']['factor']
        self.taper['z'].lock_x = self.original_value['z']['lock_x']
        self.taper['z'].lock_y = self.original_value['z']['lock_y']

    def add_taper(self):
        self.initiation()
        if not (self.taper['x'] and self.taper['y'] and self.taper['z']):
            self.taper['z'] = self.obj.modifiers.new(name=fluent_modifiers_name['taper_z'], type='SIMPLE_DEFORM')
            self.taper['z'].deform_method = 'TAPER'
            self.taper['z'].deform_axis = 'Z'
            self.taper['z'].factor = 0
            self.taper['z'].show_render = self.taper['z'].show_viewport = False
            self.taper['z'].show_expanded = False

            self.taper['x'] = self.obj.modifiers.new(name=fluent_modifiers_name['taper_x'], type='SIMPLE_DEFORM')
            self.taper['x'].deform_method = 'TAPER'
            self.taper['x'].deform_axis = 'X'
            self.taper['x'].factor = 0
            self.taper['x'].show_render = self.taper['x'].show_viewport = False
            self.taper['x'].show_expanded = False

            self.taper['y'] = self.obj.modifiers.new(name=fluent_modifiers_name['taper_y'], type='SIMPLE_DEFORM')
            self.taper['y'].deform_method = 'TAPER'
            self.taper['y'].deform_axis = 'Y'
            self.taper['y'].factor = 0
            self.taper['y'].show_render = self.taper['y'].show_viewport = False
            self.taper['y'].show_expanded = False

            place_in_stack(self.obj, self.taper['x'])
            place_in_stack(self.obj, self.taper['y'])
            place_in_stack(self.obj, self.taper['z'])

    def adjust_tape(self, ui: FLUENT_ui_management):
        callback = []
        screen_text = []

        keys = ui.event_dico_get()
        self.action = ui.get_button_action()[0]
        if not self.ui_sent:
            self.set_ui(ui)
        self.enter_value = enter_value(self.enter_value, keys)

        if not self.init:
            self.add_taper()
            self.taper['x'].show_viewport = self.taper['x'].show_render = True
            self.taper['y'].show_viewport = self.taper['y'].show_render = True
            self.taper['z'].show_viewport = self.taper['z'].show_render = True
            self.original_value = {
                'x':{
                    'factor':self.taper['x'].factor,
                    'lock_y':self.taper['x'].lock_y,
                    'lock_z':self.taper['x'].lock_z
                    },
                'y':{
                    'factor':self.taper['y'].factor,
                    'lock_x':self.taper['y'].lock_x,
                    'lock_z':self.taper['y'].lock_z
                },
                'z':{
                    'factor':self.taper['z'].factor,
                    'lock_x':self.taper['z'].lock_x,
                    'lock_y':self.taper['z'].lock_y
                }
            }
            self.previous_value = {
                'x':self.taper['x'].factor,
                'y':self.taper['y'].factor,
                'z':self.taper['z'].factor
            }
            self.backup['x'] = get_modifier_values(self.taper['x'])
            self.backup['y'] = get_modifier_values(self.taper['y'])
            self.backup['z'] = get_modifier_values(self.taper['z'])
            self.init = True

        if keys['shift_work']:
            increment = 3000*get_addon_preferences().interface_factor
        elif keys['ctrl_work']:
            increment = 30*get_addon_preferences().interface_factor
        else:
            increment = 500*get_addon_preferences().interface_factor

        if self.array_axis and keys['value'] == 'PRESS' and keys['type'] == 'LEFTMOUSE':
            self.array_axis = None

        if type(self.action) == str and 'X' in self.action:
            self.slider_origin = keys['mouse_x']
            self.previous_value['x'] = self.taper['x'].factor
            self.array_axis = 'X'
            self.taper['x'].show_viewport = True
            self.taper['x'].show_render = True
        elif type(self.action) == str and 'Y' in self.action:
            self.slider_origin = keys['mouse_x']
            self.previous_value['y'] = self.taper['y'].factor
            self.array_axis = 'Y'
            self.taper['y'].show_viewport = True
            self.taper['y'].show_render = True
        elif type(self.action) == str and 'Z' in self.action:
            self.slider_origin = keys['mouse_x']
            self.previous_value['z'] = self.taper['z'].factor
            self.array_axis = 'Z'
            self.taper['z'].show_viewport = True
            self.taper['z'].show_render = True

        if self.array_axis != None:
            if keys['shift_press'] or keys['shift_release'] or keys['ctrl_press'] or keys['ctrl_release']:
                self.slider_origin = keys['mouse_x']
                self.previous_value = {
                    'x':self.taper['x'].factor,
                    'y':self.taper['y'].factor,
                    'z':self.taper['z'].factor
                }

            if self.array_axis == 'X':
                if enter_value_validation(self.enter_value, keys)[0]:
                    self.taper['x'].factor = self.previous_value['x'] = enter_value_validation(self.enter_value, keys)[1]
                    self.enter_value = 'None'
                    self.array_axis = None
                if keys['type'] == 'MOUSEMOVE' and not keys['show_menu']:
                    self.taper['x'].factor = self.previous_value['x'] + (keys['mouse_x'] - self.slider_origin)/increment

                if keys['value'] == 'PRESS' and keys['type'] == 'ESC':
                    self.restore_value()
                    callback.append('DO_NOT_QUIT_FLUENT')
                    self.end_of_adjustment()

                if keys['value'] == 'PRESS' and keys['type'] == 'DEL':
                    self.taper['x'].factor = 0
                    self.taper['x'].show_viewport = self.taper['x'].show_render = False
                    self.array_axis = ''

                if keys['value'] == 'PRESS' and keys['type'] == 'C':
                    if not self.taper['x'].lock_y and not self.taper['x'].lock_z:
                        self.taper['x'].lock_y = True
                        self.taper['x'].lock_z = False
                    elif self.taper['x'].lock_y:
                        self.taper['x'].lock_y = False
                        self.taper['x'].lock_z = True
                    elif self.taper['x'].lock_z:
                        self.taper['x'].lock_y = False
                        self.taper['x'].lock_z = False

            if self.array_axis == 'Y':
                if enter_value_validation(self.enter_value, keys)[0]:
                    self.taper['y'].factor = self.previous_value['y'] = enter_value_validation(self.enter_value, keys)[1]
                    self.enter_value = 'None'
                    self.array_axis = None
                if keys['type'] == 'MOUSEMOVE':
                    self.taper['y'].factor = self.previous_value['y'] + (keys['mouse_x'] - self.slider_origin)/increment

                if keys['value'] == 'PRESS' and keys['type'] == 'ESC':
                    self.restore_value()
                    callback.append('DO_NOT_QUIT_FLUENT')
                    self.end_of_adjustment()

                if keys['value'] == 'PRESS' and keys['type'] == 'DEL':
                    self.taper['y'].factor = 0
                    self.taper['y'].show_viewport = self.taper['y'].show_render = False
                    self.array_axis = ''

                if keys['value'] == 'PRESS' and keys['type'] == 'C':
                    if not self.taper['y'].lock_x and not self.taper['y'].lock_z:
                        self.taper['y'].lock_x = True
                        self.taper['y'].lock_z = False
                    elif self.taper['y'].lock_x:
                        self.taper['y'].lock_x = False
                        self.taper['y'].lock_z = True
                    elif self.taper['y'].lock_z:
                        self.taper['y'].lock_x = False
                        self.taper['y'].lock_z = False

            if self.array_axis == 'Z':
                if enter_value_validation(self.enter_value, keys)[0]:
                    self.taper['z'].factor = self.previous_value['z'] = enter_value_validation(self.enter_value, keys)[1]
                    self.enter_value = 'None'
                    self.array_axis = None
                if keys['type'] == 'MOUSEMOVE':
                    self.taper['z'].factor = self.previous_value['z'] + (keys['mouse_x'] - self.slider_origin)/increment

                if keys['value'] == 'PRESS' and keys['type'] == 'ESC':
                    self.restore_value()
                    callback.append('DO_NOT_QUIT_FLUENT')
                    self.end_of_adjustment()

                if keys['value'] == 'PRESS' and keys['type'] == 'DEL':
                    self.taper['z'].factor = 0
                    self.taper['z'].show_viewport = self.taper['z'].show_render = False
                    self.array_axis = ''

                if keys['value'] == 'PRESS' and keys['type'] == 'C':
                    if not self.taper['z'].lock_x and not self.taper['z'].lock_y:
                        self.taper['z'].lock_x = True
                        self.taper['z'].lock_y = False
                    elif self.taper['z'].lock_x:
                        self.taper['z'].lock_x = False
                        self.taper['z'].lock_y = True
                    elif self.taper['z'].lock_y:
                        self.taper['z'].lock_x = False
                        self.taper['z'].lock_y = False

        if keys['value'] == 'PRESS' and keys['type'] == 'ESC':
            try:
                set_modifier_value(self.taper['x'], self.backup['x'])
                set_modifier_value(self.taper['y'], self.backup['y'])
                set_modifier_value(self.taper['z'], self.backup['z'])
            except:pass
            self.end_of_adjustment()
            callback.append('DO_NOT_QUIT_FLUENT')
            callback.append('STOP_ADJUSTMENT')

        # TEXT
        if self.array_axis == 'X':
            screen_text.append(['X '+translate('factor'), adjustment_value(self.taper['x'].factor, self.enter_value)])
        else:
            screen_text.append(['X '+translate('factor'), modifier_value_converter(self.taper['x'].factor)])
        if self.array_axis == 'Y':
            screen_text.append(['Y '+translate('factor'), adjustment_value(self.taper['y'].factor, self.enter_value)])
        else:
            screen_text.append(['Y '+translate('factor'), modifier_value_converter(self.taper['y'].factor)])
        if self.array_axis == 'Z':
            screen_text.append(['Z '+translate('factor'), adjustment_value(self.taper['z'].factor, self.enter_value)])
        else:
            screen_text.append(['Z '+translate('factor'), modifier_value_converter(self.taper['z'].factor)])
        if self.array_axis != None:
            screen_text.append([translate('lockAxis'), 'C'])
            screen_text.append([translate('remove'), translate('delete')])
            screen_text.append([translate('slowerFaster'), translate('shiftControl')])

        self.action = ui.get_button_action()[0]

        if self.action == 'VALIDATE':
            self.end_of_adjustment()
            screen_text = []
            callback.append('STOP_ADJUSTMENT')
        elif self.action is not None:
            self.slider_origin = keys['mouse_x']

        ui.refresh_side_infos(screen_text)

        return callback


class circular_array_management():
    def __init__(self, obj, target=None):
        self.obj = obj
        self.draw_type = self.obj['fluent_type']
        self.bool_target = target
        self.modifier = None
        self.slider_origin = None
        self.previous_value = None
        self.enter_value = 'None'
        self.original_value = {
            'radius':None,
            'count':None,
            'end':None,
            'angle':None,
            'z':None
        }
        self.init = False
        self.empty = None
        self.empty_matrix_save = None
        self.other_adjustment = 'RADIUS'

        # menu
        self.action = None
        self.ui_sent = False
        self.pie_menu = FLUENT_Ui_Layout('CIRCULAR_ARRAY')
        self.pie_menu.set_layout('PIE')

        button = make_button('VALIDATE')
        self.pie_menu.add_item(button)

        button = FLUENT_Ui_Button()
        button.set_text(translate('count'))
        button.set_shape('RECTANGLE')
        button.set_action('COUNT')
        self.pie_menu.add_item(button)

        button = FLUENT_Ui_Button()
        button.set_text(translate('radius'))
        button.set_shape('RECTANGLE')
        button.set_action('ARRAY_RADIUS')
        self.pie_menu.add_item(button)

        button = FLUENT_Ui_Button()
        button.set_text(translate('angle'))
        button.set_shape('RECTANGLE')
        button.set_action('ANGLE')
        self.pie_menu.add_item(button)

        button = FLUENT_Ui_Button()
        button.set_text(translate('arrayRotation'))
        button.set_shape('RECTANGLE')
        button.set_action('ARRAY_ROT')
        self.pie_menu.add_item(button)

    def set_ui(self, ui):
        ui.hide_menu()
        ui.add_items(self.pie_menu)
        ui.hide_menu()
        self.ui_sent = True

    def get_pie_menu(self):
        return self.pie_menu

    def get_modifier(self):
        return self.modifier

    def initiation(self):
        for m in self.obj.modifiers:
            if m.name == fluent_modifiers_name['circular_array'] and m.type == 'NODES':
                self.modifier = m
        return self.modifier

    def end_of_adjustment(self):
        self.slider_origin = None
        self.previous_value = None
        self.enter_value = 'None'
        self.original_value = {}
        self.init = False
        self.other_adjustment = 'RADIUS'
        self.ui_sent = False

    def restore(self):
        array_radius = self.modifier.node_group.nodes[fluent_modifiers_name['circular_array']].inputs['Radius']
        array_count = self.modifier.node_group.nodes[fluent_modifiers_name['circular_array']].inputs['Count']
        array_end = self.modifier.node_group.nodes[fluent_modifiers_name['circular_array']].inputs['End']
        array_angle = self.modifier.node_group.nodes[fluent_modifiers_name['circular_array']].inputs['Angle']
        array_z = self.modifier.node_group.nodes[fluent_modifiers_name['circular_array']].inputs['Z']
        support_object = self.modifier.node_group.nodes[fluent_modifiers_name['circular_array']].inputs['Support']
        array_radius.default_value = self.original_value['radius']
        array_count.default_value = self.original_value['count']
        array_end.default_value = self.original_value['end']
        array_angle.default_value = self.original_value['angle']
        array_z.default_value = self.original_value['z']
        support_object.default_value = self.original_value['support']

    def add_circular_array(self):
        self.initiation()
        if not self.modifier:
            main_dir = join(dirname(realpath(__file__)))
            blender_dir = join(main_dir,'geometry_nodes')
            blender_file = join(blender_dir,'array.blend')
            file_path_node_tree = join(blender_file,'NodeTree')

            group_name = fluent_modifiers_name['circular_array']
            if not bpy.data.node_groups.get(group_name):
                bpy.ops.wm.append(filename=group_name, directory=file_path_node_tree)

            self.modifier = self.obj.modifiers.new(name=fluent_modifiers_name['circular_array'], type='NODES')
            node_group = bpy.data.node_groups.new(name='Circular_Array', type='GeometryNodeTree')
            node_group.nodes.new(type='NodeGroupInput')
            node_group.nodes.new(type='NodeGroupOutput')
            if bpy.app.version >= (4, 0, 0):
                node_group.interface.new_socket(name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
                node_group.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
            else:
                node_group.inputs.new(type='NodeSocketGeometry', name='Geometry')
                node_group.outputs.new(type='NodeSocketGeometry', name='Geometry')
            self.modifier.node_group = node_group
            tree = self.modifier.node_group
            nodes = tree.nodes
            link = tree.links.new
            node_c_array = nodes.new(type='GeometryNodeGroup')
            node_c_array.name = group_name
            node_c_array.node_tree = bpy.data.node_groups.get(group_name)
            for n in nodes:
                if n.type == 'GROUP_INPUT':
                    group_in = n
                if n.type == 'GROUP_OUTPUT':
                    group_out = n
            link(group_in.outputs[0], node_c_array.inputs[0])
            link(node_c_array.outputs[0], group_out.inputs[0])
            # group_in.outputs.new(type = 'FLOAT', name='Radius')
            # link(group_in.outputs[1], node_c_array.inputs[1])
            # group_in.outputs.new(type = 'INTEGER', name='Count')
            # link(group_in.outputs[2], node_c_array.inputs[2])
            # group_in.outputs.new(type = 'FLOAT', name='Angle')
            # link(group_in.outputs[3], node_c_array.inputs[3])
            # group_in.outputs.new(type = 'FLOAT', name='Individual Rotation')
            # link(group_in.outputs[4], node_c_array.inputs[4])
            # group_in.outputs.new(type = 'FLOAT', name='Global rotation')
            # link(group_in.outputs[5], node_c_array.inputs[5])
            self.modifier.show_render = False
            self.modifier.show_viewport = False
            self.modifier.show_expanded = False
            self.modifier.node_group.nodes[fluent_modifiers_name['circular_array']].inputs['Current'].default_value = self.obj
            place_in_stack(self.obj, self.modifier)
        return self.modifier

    def adjust(self, ui: FLUENT_ui_management, draw_type=None):
        callback = []
        screen_text = []

        keys = ui.event_dico_get()
        self.action = ui.get_button_action()[0]

        if not self.ui_sent:
            self.set_ui(ui)

        self.enter_value = enter_value(self.enter_value, keys)

        if not self.modifier:
            self.add_circular_array()

        array_radius = self.modifier.node_group.nodes[fluent_modifiers_name['circular_array']].inputs['Radius']
        array_count = self.modifier.node_group.nodes[fluent_modifiers_name['circular_array']].inputs['Count']
        array_end = self.modifier.node_group.nodes[fluent_modifiers_name['circular_array']].inputs['End']
        array_angle = self.modifier.node_group.nodes[fluent_modifiers_name['circular_array']].inputs['Angle']
        array_z = self.modifier.node_group.nodes[fluent_modifiers_name['circular_array']].inputs['Z']
        support_object = self.modifier.node_group.nodes[fluent_modifiers_name['circular_array']].inputs['Support']

        if not self.init:
            self.slider_origin = keys['mouse_x']
            self.previous_value = array_radius.default_value
            self.original_value['radius'] = array_radius.default_value
            self.original_value['count'] = array_count.default_value
            self.original_value['end'] = array_end.default_value
            self.original_value['angle'] = array_angle.default_value
            self.original_value['z'] = array_z.default_value
            self.original_value['support'] = support_object.default_value
            self.init = True
            self.modifier.show_render = self.modifier.show_viewport = True

        if self.action:
            self.empty_matrix_save = self.obj.matrix_world.copy()
            if self.action == 'ANGLE':
                self.other_adjustment = 'ANGLE'
                self.previous_value = array_end.default_value
                self.slider_origin = keys['mouse_x']
            elif self.action == 'COUNT':
                self.other_adjustment = 'COUNT'
                self.previous_value = array_count.default_value
                self.slider_origin = keys['mouse_x']
            elif self.action == 'ARRAY_RADIUS':
                self.other_adjustment = 'RADIUS'
                self.previous_value = array_radius.default_value
                self.slider_origin = keys['mouse_x']
            elif self.action == 'ARRAY_ROT':
                self.other_adjustment = 'ARRAY_ROT'
                self.previous_value = array_z.default_value
                self.slider_origin = keys['mouse_x']

        if keys['shift_press'] or keys['shift_release'] or keys['ctrl_press'] or keys['ctrl_release']:
            self.slider_origin = keys['mouse_x']
            if self.other_adjustment == 'COUNT':
                self.previous_value = array_count.default_value
            elif self.other_adjustment == 'RADIUS':
                self.previous_value = array_radius.default_value
            elif self.other_adjustment == 'ANGLE':
                self.previous_value = array_end.default_value
            elif self.other_adjustment == 'ARRAY_ROT':
                self.previous_value = array_z.default_value

        if not keys['show_menu'] and (keys['type'] == 'MOUSEMOVE' or enter_value_validation(self.enter_value, keys)[0]):
            if self.other_adjustment == 'RADIUS':
                if keys['shift_work']:
                    increment = 2000*get_addon_preferences().interface_factor
                elif keys['ctrl_work']:
                    increment = 20*get_addon_preferences().interface_factor
                else:
                    increment = 200*get_addon_preferences().interface_factor

                array_radius.default_value = self.previous_value + ((keys['mouse_x'] - self.slider_origin)/increment)
                if enter_value_validation(self.enter_value, keys)[0]:
                    array_radius.default_value = enter_value_validation(self.enter_value, keys)[1]
                    self.enter_value = 'None'
                    self.other_adjustment = None
            elif self.other_adjustment == 'COUNT':
                if keys['shift_work']:
                    increment = 300*get_addon_preferences().interface_factor
                elif keys['ctrl_work']:
                    increment = 30*get_addon_preferences().interface_factor
                else:
                    increment = 60*get_addon_preferences().interface_factor
                a = array_count.default_value
                array_count.default_value = int(self.previous_value + ((keys['mouse_x'] - self.slider_origin)/increment))
                if enter_value_validation(self.enter_value, keys)[0]:
                    array_count.default_value = int(enter_value_validation(self.enter_value, keys)[1])
                    self.enter_value = 'None'
                    self.other_adjustment = None
            elif self.other_adjustment == 'ANGLE':
                if keys['shift_work']:
                    increment = 50*get_addon_preferences().interface_factor
                elif keys['ctrl_work']:
                    increment = 1*get_addon_preferences().interface_factor
                else:
                    increment = 5*get_addon_preferences().interface_factor
                array_end.default_value = int(self.previous_value + ((keys['mouse_x'] - self.slider_origin)/increment))
                if keys['ctrl_work']:
                    array_end.default_value = int(math.ceil(array_end.default_value / 45)) * 45
                if enter_value_validation(self.enter_value, keys)[0]:
                    array_end.default_value = int(enter_value_validation(self.enter_value, keys)[1])
                    self.enter_value = 'None'
                    self.other_adjustment = None
                if array_end.default_value > 360:
                    array_end.default_value = 360
                elif array_end.default_value < 0:
                    array_end.default_value = 0
            elif self.other_adjustment == 'ARRAY_ROT':
                if keys['shift_work']:
                    increment = 500*get_addon_preferences().interface_factor
                elif keys['ctrl_work']:
                    increment = 5*get_addon_preferences().interface_factor
                else:
                    increment = 50*get_addon_preferences().interface_factor
                array_z.default_value = self.previous_value + ((keys['mouse_x'] - self.slider_origin)/increment)

        if keys['value'] == 'PRESS' and keys['type'] == 'C':
            try:
                self.obj.modifiers[fluent_modifiers_name['rotate']].node_group.nodes['Transform'].inputs[2].default_value[2] += math.radians(45)
            except:
                f_rotation = rotation_management(self.obj)
                f_rotation.add_modifier()
                self.obj.modifiers[fluent_modifiers_name['rotate']].node_group.nodes['Transform'].inputs[2].default_value[2] += math.radians(45)

        if keys['value'] == 'PRESS' and keys['type'] == 'V':
            try:
                self.obj.modifiers[fluent_modifiers_name['rotate']].node_group.nodes['Transform'].inputs[2].default_value[0] += math.radians(45)
            except:
                f_rotation = rotation_management(self.obj)
                f_rotation.add_modifier()
                self.obj.modifiers[fluent_modifiers_name['rotate']].node_group.nodes['Transform'].inputs[2].default_value[0] += math.radians(45)

        if keys['value'] == 'PRESS' and keys['type'] == 'B' and self.bool_target:
            inputs = self.modifier.node_group.nodes[fluent_modifiers_name['circular_array']].inputs
            if inputs['Use Support'].default_value == 0:
                if bpy.app.version >= (4, 0, 0):
                    previous_active = bpy.context.active_object
                    bpy.ops.object.empty_add(type='PLAIN_AXES', align='WORLD', location=self.bool_target.location)
                    empty = bpy.context.active_object
                    empty.rotation_euler = self.bool_target.rotation_euler
                    empty.hide_viewport = True
                    empty.hide_render = True
                    support_object.default_value = empty
                    active_object('SET', previous_active)
                    self.obj['f_circular_empty'] = empty
                else:
                    support_object.default_value = self.bool_target
                inputs['Axis'].default_value = Vector((0, 1, 0))
                inputs['Use Support'].default_value = 1
            else:
                if bpy.app.version >= (4, 0, 0):
                    bpy.data.objects.remove(self.obj['f_circular_empty'], do_unlink=True)
                    del self.obj['f_circular_empty']
                inputs['Use Support'].default_value = 0
                inputs['Axis'].default_value = Vector((0, 0, 1))

        # TEXT
        if self.other_adjustment == 'COUNT':
            screen_text.append([translate('count'), adjustment_value(array_count.default_value, self.enter_value)])
            screen_text.append([translate('radius'), modifier_value_converter(array_radius.default_value)])
            screen_text.append([translate('angle'), modifier_value_converter(array_end.default_value)])
        elif self.other_adjustment == 'RADIUS':
            screen_text.append([translate('count'), modifier_value_converter(array_count.default_value)])
            screen_text.append([translate('radius'), adjustment_value(array_radius.default_value, self.enter_value)])
            screen_text.append([translate('angle'), modifier_value_converter(array_end.default_value)])
        elif self.other_adjustment == 'ANGLE':
            screen_text.append([translate('count'), modifier_value_converter(array_count.default_value)])
            screen_text.append([translate('radius'), modifier_value_converter(array_radius.default_value)])
            screen_text.append([translate('angle'), adjustment_value(array_end.default_value, self.enter_value)])
        else:
            screen_text.append([translate('count'), modifier_value_converter(array_count.default_value)])
            screen_text.append([translate('radius'), modifier_value_converter(array_radius.default_value)])
            screen_text.append([translate('angle'), modifier_value_converter(array_end.default_value)])
        screen_text.append([translate('objectZRotation'), 'C'])
        screen_text.append([translate('objectXRotation'), 'V'])
        screen_text.append([translate('objectAsAxis'), 'B'])
        screen_text.append([translate('slowerFaster'), translate('shiftControl')])
        screen_text.append([translate('remove'), translate('delBackSpace')])

        if self.action == 'VALIDATE':
            self.end_of_adjustment()
            screen_text = []
            callback.append('STOP_ADJUSTMENT')
        elif self.action is not None:
            self.slider_origin = keys['mouse_x']

        if keys['value'] == 'PRESS' and keys['type'] in {'DEL', 'BACK_SPACE'}:
            self.modifier.show_viewport = False
            self.modifier.show_render = False
            self.action = 'VALIDATE'
            self.end_of_adjustment()
            screen_text = []
            callback.append('STOP_ADJUSTMENT')

        if keys['value'] == 'PRESS' and keys['type'] == 'ESC':
            try:
                self.restore()
            except:pass
            self.end_of_adjustment()
            callback.append('DO_NOT_QUIT_FLUENT')
            callback.append('STOP_ADJUSTMENT')

        ui.refresh_side_infos(screen_text)

        return callback


class radius_management():
    def __init__(self, obj):
        self.obj = obj
        self.radius = None
        self.inner_radius = None
        self.slider_origin = None
        self.previous_value = None
        self.inner_previous_value = None
        self.enter_value = 'None'
        self.original_value = None
        self.inner_original_value = None
        self.init = False
        self.is_adjusting_inner_radius = False

        # menu
        self.action = None
        self.ui_sent = False
        self.pie_menu = FLUENT_Ui_Layout('FIRST_SOLIDIFY')
        self.pie_menu.set_layout('PIE')

        button = make_button('VALIDATE')
        self.pie_menu.add_item(button)

    def set_ui(self, ui):
        ui.hide_menu()
        ui.add_items(self.pie_menu)
        ui.hide_menu()
        self.ui_sent = True

    def get_pie_menu(self):
        return self.pie_menu

    def get_modifier(self):
        return self.radius

    def initiation(self):
        for m in self.obj.modifiers:
            if m.name == fluent_modifiers_name['radius'] and m.type == 'DISPLACE':
                self.radius = m
            if m.name == fluent_modifiers_name['inner_radius'] and m.type == 'DISPLACE':
                self.inner_radius = m
        return self.radius

    def end_of_adjustment(self):
        self.slider_origin = None
        self.previous_value = None
        self.inner_previous_value = None
        self.enter_value = 'None'
        self.original_value = None
        self.inner_original_value = None
        self.init = False
        self.ui_sent = False
        self.is_adjusting_inner_radius = False

    def add_radius(self):
        self.initiation()
        if not self.radius:
            found = False
            for m in self.obj.modifiers:
                if m.name == fluent_modifiers_name['radius']:
                    found = True
                    self.radius = m
                if m.name == fluent_modifiers_name['inner_radius']:
                    found = True
                    self.inner_radius = m

            if not found:
                self.radius = self.obj.modifiers.new(name=fluent_modifiers_name['radius'], type='DISPLACE')
                self.radius.show_in_editmode = True
                self.radius.show_on_cage = True
                self.radius.direction = 'X'
                self.radius.vertex_group = 'radius'
                self.radius.strength = 0
                self.radius.mid_level = 0
                self.radius.show_expanded = False
                place_in_stack(self.obj, self.radius)

                self.inner_radius = self.obj.modifiers.new(name=fluent_modifiers_name['inner_radius'], type='DISPLACE')
                self.inner_radius.show_in_editmode = True
                self.inner_radius.show_on_cage = True
                self.inner_radius.direction = 'X'
                self.inner_radius.vertex_group = 'inner_radius'
                self.inner_radius.strength = 0
                self.inner_radius.mid_level = 0
                self.inner_radius.show_expanded = False
                place_in_stack(self.obj, self.inner_radius)

    def adjust_modifier(self, ui: FLUENT_ui_management):
        callback = []
        screen_text = []

        keys = ui.event_dico_get()
        self.action = ui.get_button_action()[0]

        if not self.ui_sent:
            self.set_ui(ui)

        self.enter_value = enter_value(self.enter_value, keys)

        if not self.init:
            self.add_radius()
            self.previous_value = self.radius.strength
            self.original_value = self.radius.strength
            if self.inner_radius is not None:
                self.inner_previous_value = self.inner_radius.strength
                self.inner_original_value = self.inner_radius.strength
            self.slider_origin = keys['mouse_x']
            self.init = True

        if keys['shift_work']:
            increment = 3000*get_addon_preferences().interface_factor
        elif keys['ctrl_work']:
            increment = 30*get_addon_preferences().interface_factor
        else:
            increment = 500*get_addon_preferences().interface_factor

        if keys['shift_press'] or keys['shift_release'] or keys['ctrl_press'] or keys['ctrl_release']:
            self.slider_origin = keys['mouse_x']
            self.previous_value = self.radius.strength
            self.inner_previous_value = self.inner_radius.strength

        if keys['type'] == 'MOUSEMOVE' and not keys['show_menu']:
            if not self.is_adjusting_inner_radius:
                self.radius.strength = self.previous_value + ((keys['mouse_x'] - self.slider_origin)/increment)

            if self.inner_radius is not None and (self.inner_radius.strength != 0 or self.is_adjusting_inner_radius):
                new_value = self.inner_previous_value + ((keys['mouse_x'] - self.slider_origin)/increment)
                if new_value < 0:
                    new_value = 0

                if new_value < self.radius.strength:
                    self.inner_radius.strength = new_value

            if self.obj['fluent_type'] != 'sphere' and (self.obj.get('fluent_auto_res') == 'ENABLE' or not self.obj.get('fluent_auto_res')):
                screw = self.obj.modifiers[fluent_modifiers_name['screw']]
                screw.steps = screw.render_steps = auto_bevel_segments(displace=self.radius)
            elif self.obj['fluent_type'] == 'sphere' and (self.obj.get('fluent_auto_res') == 'ENABLE' or not self.obj.get('fluent_auto_res')):
                screw_2 = self.obj.modifiers[fluent_modifiers_name['screw_2']]
                screw_2.steps = screw_2.render_steps = int(auto_bevel_segments(displace=self.obj.modifiers[fluent_modifiers_name['radius']]) / 2)
                screw = self.obj.modifiers[fluent_modifiers_name['screw']]
                screw.steps = screw.render_steps = int(screw_2.steps / 3)

        if enter_value_validation(self.enter_value, keys)[0]:
            radius_gap = self.radius.strength - self.inner_radius.strength

            if self.is_adjusting_inner_radius:
                new_value = enter_value_validation(self.enter_value, keys)[1]
                if new_value < 0:
                    new_value = 0.0001
                if new_value > self.radius.strength:
                    new_value = self.radius.strength

                self.inner_radius.strength = self.radius.strength - new_value
            else:
                self.radius.strength = enter_value_validation(self.enter_value, keys)[1]

            if self.inner_radius.strength != 0 and not self.is_adjusting_inner_radius:
                new_value = enter_value_validation(self.enter_value, keys)[1] - radius_gap
                if new_value < 0:
                    new_value = 0

                self.inner_radius.strength = new_value

            if self.obj['fluent_type'] != 'sphere' and (self.obj.get('fluent_auto_res') == 'ENABLE' or not self.obj.get('fluent_auto_res')):
                screw = self.obj.modifiers[fluent_modifiers_name['screw']]
                screw.steps = screw.render_steps = int(auto_bevel_segments(displace=self.radius))
            elif self.obj['fluent_type'] == 'sphere' and (self.obj.get('fluent_auto_res') == 'ENABLE' or not self.obj.get('fluent_auto_res')):
                screw_2 = self.obj.modifiers[fluent_modifiers_name['screw_2']]
                screw_2.steps = screw_2.render_steps = int(auto_bevel_segments(displace=self.obj.modifiers[fluent_modifiers_name['radius']]) / 2)
                screw = self.obj.modifiers[fluent_modifiers_name['screw']]
                screw.steps = screw.render_steps = int(screw_2.steps / 3)
            self.end_of_adjustment()
            callback.append('STOP_ADJUSTMENT')

        if keys['value'] == 'PRESS' and keys['type'] == 'ESC':
            self.radius.strength = self.original_value
            self.end_of_adjustment()
            callback.append('STOP_ADJUSTMENT')
            callback.append('DO_NOT_QUIT_FLUENT')

        if keys['value'] == 'PRESS' and keys['type'] == 'C':
            self.is_adjusting_inner_radius = not self.is_adjusting_inner_radius
            self.slider_origin = keys['mouse_x']
            self.previous_value = self.radius.strength
            self.inner_previous_value = self.inner_radius.strength

        # TEXT
        adjustment_text = [translate('radius'), adjustment_value(self.radius.strength, self.enter_value)]
        if self.is_adjusting_inner_radius:
            radius_gap = self.radius.strength - self.inner_radius.strength
            adjustment_text = [translate('innerRadius'), adjustment_value(radius_gap, self.enter_value)]
        screen_text.append(adjustment_text)
        screen_text.append([translate('slowerFaster'), translate('shiftControl')])
        screen_text.append([translate('radiusToggle'), 'C'])

        if self.action == 'VALIDATE':
            inner_original_value = self.inner_original_value
            inner_radius = self.inner_radius
            self.end_of_adjustment()
            screen_text = []
            callback.append('STOP_ADJUSTMENT')

            if inner_radius is not None and inner_original_value == 0 and inner_radius.strength != 0:
                callback.append('INNER_RADIUS_ON')
            if inner_radius is not None and inner_original_value != 0 and inner_radius.strength == 0:
                callback.append('INNER_RADIUS_OFF')
        elif self.action is not None:
            self.slider_origin = keys['mouse_x']

        ui.refresh_side_infos(screen_text)
        return callback


class resolution_management():
    def __init__(self, obj):
        self.obj = obj
        self.resolution = None
        self.slider_origin = None
        self.previous_value = None
        self.enter_value = 'None'
        self.original_value = None
        self.init = False

        # menu
        self.ui_sent = False
        self.pie_menu = FLUENT_Ui_Layout('RESOLUTION')
        self.pie_menu.set_layout('PIE')

        button = make_button('VALIDATE')
        self.pie_menu.add_item(button)

    def initiation(self):
        for m in self.obj.modifiers:
            if m.name == fluent_modifiers_name['screw'] and m.type == 'SCREW':
                self.resolution = m
                break
        return self.resolution

    def set_ui(self, ui):
        ui.hide_menu()
        ui.add_items(self.pie_menu)
        ui.hide_menu()
        self.ui_sent = True

    def get_pie_menu(self):
        return self.pie_menu

    def get_modifier(self):
        return self.resolution

    def end_of_adjustment(self):
        self.slider_origin = None
        self.previous_value = None
        self.enter_value = 'None'
        self.original_value = None
        self.init = False
        self.ui_sent = False

    def add_resolution(self):
        self.initiation()
        if not self.resolution:
            found = False
            for m in self.obj.modifiers:
                if m.name == fluent_modifiers_name['screw']:
                    found = True
                    self.resolution = m
                    break
            if not found:
                self.resolution = self.obj.modifiers.new(name=fluent_modifiers_name['screw'], type='SCREW')
                self.resolution.merge_threshold = 0.0001
                self.resolution.use_merge_vertices = True
                self.resolution.use_smooth_shade = True
                self.resolution.steps = self.resolution.render_steps = auto_bevel_segments(revolver_obj=self.obj)
                self.resolution.use_normal_calculate = True
                self.resolution.show_expanded = False
                if self.obj.get('fluent_type') == 'revolver':
                    self.resolution.axis = 'Y'
                place_in_stack(self.obj, self.resolution)

    def adjust_modifier(self, ui: FLUENT_ui_management):
        callback = []
        screen_text = []

        keys = ui.event_dico_get()
        self.action = ui.get_button_action()[0]

        if not self.ui_sent:
            self.set_ui(ui)

        self.enter_value = enter_value(self.enter_value, keys)

        if not self.init:
            self.add_resolution()
            self.previous_value = self.resolution.steps
            self.original_value = self.resolution.steps
            self.slider_origin = keys['mouse_x']
            self.init = True

        if keys['shift_work']:
            increment = 300*get_addon_preferences().interface_factor
        elif keys['ctrl_work']:
            increment = 3*get_addon_preferences().interface_factor
        else:
            increment = 30*get_addon_preferences().interface_factor

        if keys['shift_press'] or keys['shift_release'] or keys['ctrl_press'] or keys['ctrl_release']:
            self.slider_origin = keys['mouse_x']
            self.previous_value = self.resolution.steps

        if keys['type'] == 'MOUSEMOVE' and not keys['show_menu']:
            self.resolution.steps = self.resolution.render_steps = int(self.previous_value + ((keys['mouse_x'] - self.slider_origin)/increment))

            if self.obj['fluent_type'] == 'sphere':
                screw_2 = self.obj.modifiers[fluent_modifiers_name['screw_2']]
                screw_2.steps = screw_2.render_steps = self.resolution.steps * 3

        if enter_value_validation(self.enter_value, keys)[0]:
            self.resolution.steps = self.resolution.render_steps = self.resolution.render_steps = int(enter_value_validation(self.enter_value, keys)[1])
            # synchro
            again = self.obj.modifiers.get(fluent_modifiers_name['screw']+'.again')
            if again:
                again.steps = again.render_steps = self.resolution.steps * 2
            callback.append('STOP_ADJUSTMENT')
            self.end_of_adjustment()

        if keys['type'] == 'C' and keys['value'] == 'PRESS':
            self.resolution.steps = self.resolution.render_steps = auto_bevel_segments(revolver_obj=self.obj)
            self.end_of_adjustment()

        if keys['type'] == 'V' and keys['value'] == 'PRESS':
            if self.obj.get('fluent_auto_res') == 'ENABLE' or not self.obj.get('fluent_auto_res'):
                self.obj['fluent_auto_res'] = 'PREVENT'
            else:
                self.obj['fluent_auto_res'] = 'ENABLE'

        if keys['value'] == 'PRESS' and keys['type'] == 'ESC':
            self.resolution.steps = self.resolution.render_steps = self.original_value
            self.end_of_adjustment()
            callback.append('STOP_ADJUSTMENT')
            callback.append('DO_NOT_QUIT_FLUENT')

        screen_text.append([translate('resolution'), adjustment_value(self.resolution.steps, self.enter_value)])
        screen_text.append([translate('defaultResolution'), 'C'])
        if self.obj.get('fluent_auto_res') == 'ENABLE' or not self.obj.get('fluent_auto_res'):
            screen_text.append([translate('preventAutoRes'), 'V'])
        else:
            screen_text.append([translate('enableAutoRes'), 'V'])
        screen_text.append([translate('slowerFaster'), translate('shiftControl')])

        if self.action == 'VALIDATE':
            self.end_of_adjustment()
            screen_text = []
            callback.append('STOP_ADJUSTMENT')
        elif self.action is not None:
            self.slider_origin = keys['mouse_x']

        ui.refresh_side_infos(screen_text)

        return callback

    def flip(self):
        callback = []
        self.resolution.use_normal_flip = not self.resolution.use_normal_flip
        callback.append('STOP_ADJUSTMENT')
        return callback


class curve_management():
    def __init__(self, obj):
        self.obj = obj
        # curve est un modifier Subdiv
        self.curve = None
        self.slider_origin = None
        self.previous_value = None
        self.enter_value = 'None'
        self.original_value = None
        self.init = False

        # menu
        self.ui_sent = False
        self.action = None
        self.pie_menu = FLUENT_Ui_Layout('CURVE')
        self.pie_menu.set_layout('PIE')

        button = make_button('VALIDATE')
        self.pie_menu.add_item(button)

    def set_ui(self, ui):
        ui.hide_menu()
        ui.add_items(self.pie_menu)
        ui.hide_menu()
        self.ui_sent = True

    def get_pie_menu(self):
        return self.pie_menu

    def get_modifier(self):
        return self.curve

    def initiation(self):
        for m in self.obj.modifiers:
            if m.name == fluent_modifiers_name['curve_subdivision'] and m.type == 'SUBSURF':
                self.curve = m
                break
        return self.curve

    def end_of_adjustment(self):
        self.slider_origin = None
        self.previous_value = None
        self.enter_value = 'None'
        self.original_value = None
        self.init = False
        self.ui_sent = False

    def add_curve(self):
        self.initiation()
        if not self.curve:
            modif = self.obj.modifiers.new(name=fluent_modifiers_name['curve_triangulate'], type='TRIANGULATE')
            modif.min_vertices = 4
            modif.ngon_method = 'BEAUTY'
            modif.quad_method = 'SHORTEST_DIAGONAL'
            modif.show_expanded = modif.show_render = modif.show_viewport = False
            move_modifier(obj=self.obj, mod_name=fluent_modifiers_name['curve_triangulate'], where='BEFORE', mod_target_name=fluent_modifiers_name['first_bevel'])
            modif = self.curve = self.obj.modifiers.new(name=fluent_modifiers_name['curve_subdivision'], type='SUBSURF')
            modif.quality = 6
            modif.levels = 3
            modif.render_levels = 3
            modif.show_expanded = modif.show_render = modif.show_viewport = False
            move_modifier(obj=self.obj, mod_name=fluent_modifiers_name['curve_subdivision'], where='AFTER', mod_target_name=fluent_modifiers_name['curve_triangulate'])
            modif = self.obj.modifiers.new(name=fluent_modifiers_name['curve_decimate'], type='DECIMATE')
            modif.decimate_type = 'DISSOLVE'
            modif.angle_limit = 0.00174533
            modif.show_expanded = modif.show_render = modif.show_viewport = False
            move_modifier(obj=self.obj, mod_name=fluent_modifiers_name['curve_decimate'], where='AFTER', mod_target_name=fluent_modifiers_name['curve_subdivision'])

    def adjust(self, ui: FLUENT_ui_management):
        callback = []
        screen_text = []

        keys = ui.event_dico_get()
        self.action = ui.get_button_action()[0]

        if not self.ui_sent:
            self.set_ui(ui)

        self.enter_value = enter_value(self.enter_value, keys)

        if not self.init:
            self.add_curve()
            self.previous_value = self.curve.levels
            self.original_value = self.curve.levels
            self.slider_origin = keys['mouse_x']
            self.init = True
            self.curve.show_render = self.curve.show_viewport = True
            self.obj.modifiers[fluent_modifiers_name['curve_triangulate']].show_render = self.obj.modifiers[fluent_modifiers_name['curve_triangulate']].show_viewport = True
            self.obj.modifiers[fluent_modifiers_name['curve_decimate']].show_render = self.obj.modifiers[fluent_modifiers_name['curve_decimate']].show_viewport = True

        if keys['shift_work']:
            increment = 600*get_addon_preferences().interface_factor
        elif keys['ctrl_work']:
            increment = 6*get_addon_preferences().interface_factor
        else:
            increment = 50*get_addon_preferences().interface_factor

        if keys['shift_press'] or keys['shift_release'] or keys['ctrl_press'] or keys['ctrl_release']:
            self.slider_origin = keys['mouse_x']
            self.previous_value = self.curve.levels

        if keys['type'] == 'MOUSEMOVE':
            level = round(self.previous_value + ((keys['mouse_x'] - self.slider_origin)/increment))
            if level > 6:
                level = 6
            elif level < 0:
                level = 0
            self.curve.render_levels = self.curve.levels = level
            if self.curve.levels != 0:
                self.curve.show_render = self.curve.show_viewport = True
                self.obj.modifiers[fluent_modifiers_name['curve_triangulate']].show_render = self.obj.modifiers[fluent_modifiers_name['curve_triangulate']].show_viewport = True
                self.obj.modifiers[fluent_modifiers_name['curve_decimate']].show_render = self.obj.modifiers[fluent_modifiers_name['curve_decimate']].show_viewport = True
            else:
                self.curve.show_render = self.curve.show_viewport = False
                self.obj.modifiers[fluent_modifiers_name['curve_triangulate']].show_render = self.obj.modifiers[fluent_modifiers_name['curve_triangulate']].show_viewport = False
                self.obj.modifiers[fluent_modifiers_name['curve_decimate']].show_render = self.obj.modifiers[fluent_modifiers_name['curve_decimate']].show_viewport = False

        if enter_value_validation(self.enter_value, keys)[0]:
            self.curve.render_levels = self.curve.levels = enter_value_validation(self.enter_value, keys)[1]
            self.end_of_adjustment()
            callback.append('STOP_ADJUSTMENT')

        if keys['value'] == 'PRESS' and keys['type'] == 'LEFTMOUSE':
            self.end_of_adjustment()
            callback.append('STOP_ADJUSTMENT')

        if (keys['value'] == 'PRESS' and keys['type'] in {'DEL', 'BACK_SPACE'}):
            hideModifier(self.curve)
            hideModifier(self.obj.modifiers[fluent_modifiers_name['curve_triangulate']])
            hideModifier(self.obj.modifiers[fluent_modifiers_name['curve_decimate']])
            self.end_of_adjustment()
            callback.append('STOP_ADJUSTMENT')


        # TEXT
        screen_text.append([translate('curve'), ''])
        screen_text.append([translate('subdivisions'), adjustment_value(self.curve.levels, self.enter_value)])
        screen_text.append([translate('slowerFaster'), translate('shiftControl')])
        screen_text.append([translate('remove'), translate('delete')])

        ui.refresh_side_infos(screen_text)

        return callback


class path_height_management():
    def __init__(self, obj, bool_target = None):
        self.obj = obj
        self.screw = None
        self.slider_origin = None
        self.previous_value = None
        self.enter_value = 'None'
        self.original_value = None
        self.bool_obj_location = [0, 0, 0]
        self.backup = None
        self.init = False
        self.reverse = False
        self.bool_target = bool_target

        # menu
        self.action = None
        self.ui_sent = False
        self.pie_menu = FLUENT_Ui_Layout('PATH_HEIGHT')
        self.pie_menu.set_layout('PIE')

        button = make_button('VALIDATE')
        self.pie_menu.add_item(button)

    def set_ui(self, ui):
        ui.hide_menu()
        ui.add_items(self.pie_menu)
        ui.hide_menu()
        self.ui_sent = True

    def get_pie_menu(self):
        return self.pie_menu

    def get_modifier(self):
        return self.screw

    def initiation(self):
        ok = 0
        for m in self.obj.modifiers:
            if m.name == fluent_modifiers_name['path_height'] and m.type == 'SCREW':
                self.screw = m
                ok+=1
            if m.name == fluent_modifiers_name['path_displace'] and m.type == 'DISPLACE':
                ok+=1
            if ok == 2:
                break
        if ok==2:
            return True
        else:
            return False

    def make_backup(self):
        self.backup = get_modifier_values(self.screw)

    def restore(self):
        set_modifier_value(self.screw, self.backup)

    def end_of_adjustment(self):
        self.slider_origin = None
        self.previous_value = None
        self.enter_value = 'None'
        self.original_value = None
        self.bool_obj_location = [0, 0, 0]
        self.init = False
        self.ui_sent = False

    def add_screw(self):
        self.initiation()
        if not self.screw:
            displace = self.obj.modifiers.new(name=fluent_modifiers_name['path_displace'], type='DISPLACE')
            displace.direction = 'Z'
            displace.strength = 0.01
            displace.show_in_editmode = True
            modif = self.screw = self.obj.modifiers.new(name=fluent_modifiers_name['path_height'], type='SCREW')
            modif.merge_threshold = 0.0001
            modif.angle = 0
            modif.axis = 'Z'
            modif.steps = 1
            modif.use_normal_calculate = True
            modif.render_steps = 1
            modif.show_expanded = False
            modif.show_in_editmode = True
            # decimate = self.obj.modifiers.new(name=fluent_modifiers_name['path_decimate'], type='DECIMATE')
            # decimate.decimate_type = 'DISSOLVE'
            place_in_stack(self.obj, displace)
            place_in_stack(self.obj, modif)
            # place_in_stack(self.obj, decimate)

    def adjust(self, ui: FLUENT_ui_management):
        callback = []
        screen_text = []

        keys = ui.event_dico_get()
        self.action = ui.get_button_action()[0]
        if not self.ui_sent:
            self.set_ui(ui)

        self.enter_value = enter_value(self.enter_value, keys)

        if not self.init:
            self.add_screw()
            self.previous_value = self.screw.screw_offset
            self.original_value = self.screw.screw_offset
            self.slider_origin = keys['mouse_x']
            self.bool_obj_location[0] = self.obj.location.x
            self.bool_obj_location[1] = self.obj.location.y
            self.bool_obj_location[2] = self.obj.location.z
            self.make_backup()
            # utilisation du chamfrin ?
            self.reverse = False
            if self.bool_target:
                for m in self.bool_target.modifiers:
                    if m.name == fluent_modifiers_name['pre_chamfer'] and m.show_viewport:
                        self.reverse = True
                        break
            self.init = True

        if self.reverse:
            callback.append('CHAMFER')

        if keys['shift_work']:
            increment = 3000*get_addon_preferences().interface_factor
        elif keys['ctrl_work']:
            increment = 30*get_addon_preferences().interface_factor
        else:
            increment = 300*get_addon_preferences().interface_factor

        if keys['shift_press'] or keys['shift_release'] or keys['ctrl_press'] or keys['ctrl_release']:
            self.slider_origin = keys['mouse_x']
            self.previous_value = self.screw.screw_offset

        if keys['type'] == 'MOUSEMOVE' and not keys['show_menu']:
            self.screw.screw_offset = self.previous_value + ((keys['mouse_x'] - self.slider_origin)/increment)

        if enter_value_validation(self.enter_value, keys)[0]:
            self.screw.screw_offset = enter_value_validation(self.enter_value, keys)[1]
            callback.append('STOP_ADJUSTMENT')
            self.end_of_adjustment()

        if keys['value'] == 'PRESS' and keys['type'] == 'V':
            self.screw.screw_offset = max(self.obj.dimensions[0] * 1.414, self.obj.dimensions[1] * 1.414, self.obj.dimensions[2] * 1.414) * (-1)

        if self.screw.screw_offset > 0:
            if self.reverse:
                callback.append('BOOL_DIFFERENCE')
            else:
                callback.append('BOOL_UNION')
        elif self.screw.screw_offset < 0:
            if self.reverse :
                callback.append('BOOL_UNION')
            else:
                callback.append('BOOL_DIFFERENCE')

        if keys['value'] == 'PRESS' and keys['type'] == 'ESC':
            self.restore()
            self.end_of_adjustment()
            callback.append('STOP_ADJUSTMENT')
            callback.append('DO_NOT_QUIT_FLUENT')

        # TEXT
        screen_text.append([translate('depthHeight'), adjustment_value(self.screw.screw_offset, self.enter_value)])
        screen_text.append([translate('slowerFaster'), translate('shiftControl')])

        if self.action == 'VALIDATE':
            self.end_of_adjustment()
            screen_text = []
            callback.append('STOP_ADJUSTMENT')

        ui.refresh_side_infos(screen_text)

        return callback


class inset_management():
    def __init__(self, obj, inset_obj):
        self.obj = obj
        self.inset_obj = inset_obj
        self.solidify = None
        self.slider_origin = None
        self.previous_value = None
        self.enter_value = 'None'
        self.original_value = None
        self.init = False

        # menu
        self.action = None
        self.ui_sent = False

        self.pie_menu = FLUENT_Ui_Layout('FIRST_SOLIDIFY')
        self.pie_menu.set_layout('PIE')

        button = make_button('VALIDATE')
        self.pie_menu.add_item(button)

    def set_ui(self, ui):
        ui.hide_menu()
        ui.add_items(self.pie_menu)
        ui.hide_menu()
        self.ui_sent = True

    def get_pie_menu(self):
        return self.pie_menu

    def get_modifier(self):
        return self.solidify

    def initiation(self):
        for m in self.inset_obj.modifiers:
            if m.name == fluent_modifiers_name['inset_solidify'] and m.type == 'SOLIDIFY':
                self.solidify = m
        return self.solidify

    def end_of_adjustment(self):
        self.slider_origin = None
        self.previous_value = None
        self.enter_value = 'None'
        self.original_value = None
        self.init = False
        self.ui_sent = False

    def add_inset(self):
        self.initiation()
        if not self.solidify:
            self.solidify = self.inset_obj.modifiers.new(name=fluent_modifiers_name['inset_solidify'], type='SOLIDIFY')
            self.solidify.show_expanded = False

    def adjust(self, ui: FLUENT_ui_management):
        callback = []
        screen_text = []

        keys = ui.event_dico_get()
        self.action = ui.get_button_action()[0]

        if not self.ui_sent:
            self.set_ui(ui)

        self.enter_value = enter_value(self.enter_value, keys)

        if not self.init:
            self.add_inset()
            self.previous_value = self.solidify.thickness
            self.original_value = self.solidify.thickness
            self.slider_origin = keys['mouse_x']
            self.init = True

        if keys['shift_work']:
            increment = 3000*get_addon_preferences().interface_factor
        elif keys['ctrl_work']:
            increment = 30*get_addon_preferences().interface_factor
        else:
            increment = 500*get_addon_preferences().interface_factor

        if keys['shift_press'] or keys['shift_release'] or keys['ctrl_press'] or keys['ctrl_release']:
            self.slider_origin = keys['mouse_x']
            self.previous_value = self.solidify.thickness

        if keys['type'] == 'MOUSEMOVE' and not keys['show_menu']:
            self.solidify.thickness = self.previous_value - ((keys['mouse_x'] - self.slider_origin)/increment)
            if self.solidify.thickness < 0:
                callback.append('INSET_ADD')
            else:
                callback.append('INSET_DIFF')

        if enter_value_validation(self.enter_value, keys)[0]:
            self.solidify.thickness = enter_value_validation(self.enter_value, keys)[1]
            self.end_of_adjustment()
            callback.append('STOP_ADJUSTMENT')

        if keys['value'] == 'PRESS' and keys['type'] == 'ESC':
            self.solidify.thickness = self.original_value
            self.end_of_adjustment()
            callback.append('STOP_ADJUSTMENT')
            callback.append('DO_NOT_QUIT_FLUENT')

        # TEXT
        screen_text.append([translate('thickness'), adjustment_value(self.solidify.thickness, self.enter_value)])
        screen_text.append([translate('slowerFaster'), translate('shiftControl')])

        if self.action == 'VALIDATE':
            self.end_of_adjustment()
            screen_text = []
            callback.append('STOP_ADJUSTMENT')
        elif self.action is not None:
            self.slider_origin = keys['mouse_x']

        ui.refresh_side_infos(screen_text)

        return callback


class scale_management():
    def __init__(self, obj):
        self.obj = obj
        self.slider_origin = None
        self.previous_value = None
        self.enter_value = 'None'
        self.original_value = None
        self.scale = None
        self.init = False
        self.array_axis = ''
        if bpy.app.version >= (4, 0, 0):
            self.inputs_name = {
                '1':'Socket_1',
                '2':'Socket_2'
            }
        else:
            self.inputs_name = {
                '1': 'Input_1',
                '2': 'Input_2'
            }

        # affichage
        self.action = None
        self.ui_sent = False

        self.pie_menu = FLUENT_Ui_Layout('SCALE')
        self.pie_menu.set_layout('TAPER')

        button = make_button('VALIDATE')
        self.pie_menu.add_item(button)

        button = FLUENT_Ui_Button()
        button.set_text('')
        button.set_shape('CIRCLE')
        button.set_action('+X')
        button.set_default_color((.9, 0, 0, 1))
        self.pie_menu.add_item(button)

        button = FLUENT_Ui_Button()
        button.set_text('')
        button.set_shape('CIRCLE')
        button.set_action('+Y')
        button.set_default_color((0, .9, 0, 1))
        self.pie_menu.add_item(button)

    def set_ui(self, ui):
        ui.hide_menu()
        ui.add_items(self.pie_menu)
        ui.hide_menu()
        self.ui_sent = True

    def get_pie_menu(self):
        return self.pie_menu

    def initiation(self):
        self.scale = None
        for m in self.obj.modifiers:
            if m.name == fluent_modifiers_name['scale'] and m.type == 'NODES':
                self.scale = m
        return self.scale

    def get_modifier(self):
        return self.scale

    def end_of_adjustment(self):
        self.slider_origin = None
        self.previous_value = None
        self.enter_value = 'None'
        self.original_value = {
            'x':None,
            'y':None,
            'x':None,
            'y':None
        }
        self.init = False
        self.ui_sent = False
        self.array_axis = ''

    def restore_value(self):
        self.scale.node_group.nodes['Transform'].inputs[3].default_value[0] = self.original_value['x']
        self.scale.node_group.nodes['Transform'].inputs[3].default_value[1] = self.original_value['y']
        recalculate_array_center(self.obj)

    def build_node_tree(self, node_tree):
        if bpy.app.version >= (4, 0, 0):
            node_tree.interface.new_socket(name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
            node_tree.interface.new_socket(name="X size", in_out='INPUT', socket_type='NodeSocketFloat')
            node_tree.interface.new_socket(name="Y size", in_out='INPUT', socket_type='NodeSocketFloat')
            node_tree.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
        else:
            node_tree.inputs.new(type='NodeSocketGeometry', name='Geometry')
            node_tree.inputs.new(type='NodeSocketFloat', name='X size')
            node_tree.inputs.new(type='NodeSocketFloat', name='Y size')
            node_tree.outputs.new(type='NodeSocketGeometry', name='Geometry')
        node = node_tree.nodes.new('ShaderNodeSeparateXYZ')
        node.location = Vector((-19.683433532714844, -405.4295959472656))
        node.name = 'Separate XYZ'

        node = node_tree.nodes.new('ShaderNodeVectorMath')
        node.location = Vector((-176.68878173828125, -405.4295959472656))
        node.name = 'Vector Math'

        node.operation = 'SUBTRACT'

        node = node_tree.nodes.new('GeometryNodeBoundBox')
        node.location = Vector((-342.2919921875, -405.4295959472656))
        node.name = 'Bounding Box'

        node = node_tree.nodes.new('ShaderNodeMath')
        node.location = Vector((173.89697265625, -435.3860168457031))
        node.name = 'Math.001'

        node.operation = 'DIVIDE'

        node = node_tree.nodes.new('ShaderNodeCombineXYZ')
        node.location = Vector((351.2616271972656, -282.0840759277344))
        node.name = 'Combine XYZ'
        node.inputs[2].default_value = 1

        node = node_tree.nodes.new('ShaderNodeMath')
        node.location = Vector((173.89697265625, -282.0840759277344))
        node.name = 'Math'

        node.operation = 'DIVIDE'

        node = node_tree.nodes.new('NodeGroupOutput')
        node.location = Vector((758.154296875, -82.7459716796875))
        node.name = 'Group Output'

        node = node_tree.nodes.new('GeometryNodeTransform')
        node.location = Vector((552.4358520507812, -82.7459716796875))
        node.name = 'Transform'

        node = node_tree.nodes.new('NodeGroupInput')
        node.location = Vector((-607.5216674804688, -91.2480239868164))
        node.name = 'Group Input'

        node_tree.links.new(node_tree.nodes['Group Input'].outputs['Geometry'], node_tree.nodes['Transform'].inputs[0])

        node_tree.links.new(node_tree.nodes['Transform'].outputs['Geometry'], node_tree.nodes['Group Output'].inputs[0])

        node_tree.links.new(node_tree.nodes['Group Input'].outputs['Geometry'], node_tree.nodes['Bounding Box'].inputs[0])

        node_tree.links.new(node_tree.nodes['Vector Math'].outputs['Vector'], node_tree.nodes['Separate XYZ'].inputs[0])

        node_tree.links.new(node_tree.nodes['Group Input'].outputs['X size'], node_tree.nodes['Math'].inputs[0])

        node_tree.links.new(node_tree.nodes['Math'].outputs['Value'], node_tree.nodes['Combine XYZ'].inputs[0])

        node_tree.links.new(node_tree.nodes['Math.001'].outputs['Value'], node_tree.nodes['Combine XYZ'].inputs[1])

        node_tree.links.new(node_tree.nodes['Combine XYZ'].outputs['Vector'], node_tree.nodes['Transform'].inputs[3])

        node_tree.links.new(node_tree.nodes['Bounding Box'].outputs['Max'], node_tree.nodes['Vector Math'].inputs[0])

        node_tree.links.new(node_tree.nodes['Bounding Box'].outputs['Min'], node_tree.nodes['Vector Math'].inputs[1])

        node_tree.links.new(node_tree.nodes['Separate XYZ'].outputs['X'], node_tree.nodes['Math'].inputs[1])

        node_tree.links.new(node_tree.nodes['Group Input'].outputs['Y size'], node_tree.nodes['Math.001'].inputs[0])

        node_tree.links.new(node_tree.nodes['Separate XYZ'].outputs['Y'], node_tree.nodes['Math.001'].inputs[1])

    def add_modifier(self):
        self.initiation()
        if not self.scale:
            self.scale = self.obj.modifiers.new(name=fluent_modifiers_name['scale'], type='NODES')
            node_group = bpy.data.node_groups.new(name='Scale', type='GeometryNodeTree')
            self.scale.node_group = node_group
            self.build_node_tree(node_group)

            dim = get_raw_object_dim(self.obj, False)
            self.scale[self.inputs_name['1']] = dim[0]
            self.scale[self.inputs_name['2']] = dim[1]

            recalculate_array_center(self.obj)
            place_in_stack(self.obj, self.scale)
        return self.scale

    def adjust_modifier(self, ui: FLUENT_ui_management):
        callback = []
        screen_text = []

        keys = ui.event_dico_get()
        self.action = ui.get_button_action()[0]

        if not self.ui_sent:
            self.set_ui(ui)

        self.enter_value = enter_value(self.enter_value, keys)

        if not self.init:
            self.add_modifier()
            self.pie_menu.set_obj(self.obj)
            self.original_value = {
                'x':self.scale[self.inputs_name['1']],
                'y':self.scale[self.inputs_name['2']]
            }
            self.previous_value = {
                'x':self.scale[self.inputs_name['1']],
                'y':self.scale[self.inputs_name['2']]
            }
            self.init = True

        if keys['shift_work']:
            increment = 3000*get_addon_preferences().interface_factor
        elif keys['ctrl_work']:
            increment = 30*get_addon_preferences().interface_factor
        else:
            increment = 500*get_addon_preferences().interface_factor

        if self.array_axis and keys['value'] == 'PRESS' and keys['type'] == 'LEFTMOUSE':
            self.array_axis = None

        if type(self.action) == str and 'X' in self.action:
            self.slider_origin = keys['mouse_x']
            self.previous_value['x'] = self.scale[self.inputs_name['1']]
            self.array_axis = 'X'
        elif type(self.action) == str and 'Y' in self.action:
            self.slider_origin = keys['mouse_x']
            self.previous_value['y'] = self.scale[self.inputs_name['2']]
            self.array_axis = 'Y'

        if self.array_axis != None:
            if keys['shift_press'] or keys['shift_release'] or keys['ctrl_press'] or keys['ctrl_release']:
                self.slider_origin = keys['mouse_x']
                self.previous_value = {
                    'x':self.scale[self.inputs_name['1']],
                    'y':self.scale[self.inputs_name['2']],
                }

            if self.array_axis == 'X':
                if enter_value_validation(self.enter_value, keys)[0]:
                    self.scale[self.inputs_name['1']] = self.previous_value['x'] = enter_value_validation(self.enter_value, keys)[1]
                    self.enter_value = 'None'
                    self.array_axis = None
                elif keys['type'] == 'MOUSEMOVE' and not keys['show_menu']:
                    self.scale[self.inputs_name['1']] = self.previous_value['x'] + (keys['mouse_x'] - self.slider_origin)/increment
                elif keys['value'] == 'PRESS' and keys['type'] == 'ESC':
                    self.restore_value()
                    callback.append('DO_NOT_QUIT_FLUENT')
                    self.end_of_adjustment()

            if self.array_axis == 'Y':
                if enter_value_validation(self.enter_value, keys)[0]:
                    self.scale[self.inputs_name['2']] = self.previous_value['y'] = enter_value_validation(self.enter_value, keys)[1]
                    self.enter_value = 'None'
                    self.array_axis = None
                elif keys['type'] == 'MOUSEMOVE':
                    self.scale[self.inputs_name['2']] = self.previous_value['y'] + (keys['mouse_x'] - self.slider_origin)/increment

                elif keys['value'] == 'PRESS' and keys['type'] == 'ESC':
                    self.restore_value()
                    callback.append('DO_NOT_QUIT_FLUENT')
                    self.end_of_adjustment()

        if keys['value'] == 'PRESS' and keys['type'] == 'ESC':
            try:
                self.restore_value()
            except:pass
            self.end_of_adjustment()
            callback.append('DO_NOT_QUIT_FLUENT')
            callback.append('STOP_ADJUSTMENT')

        # rafraichir le viewport (merci geometry nodes)
        self.scale.show_viewport = False
        self.scale.show_viewport = True

        # TEXT
        if self.array_axis == 'X':
            screen_text.append(['X '+ translate('size'), adjustment_value(self.scale[self.inputs_name['1']], self.enter_value)])
        else:
            screen_text.append(['X '+ translate('size'), modifier_value_converter(self.scale[self.inputs_name['1']])])
        if self.array_axis == 'Y':
            screen_text.append(['Y '+ translate('size'), adjustment_value(self.scale[self.inputs_name['2']], self.enter_value)])
        else:
            screen_text.append(['Y '+ translate('size'), modifier_value_converter(self.scale[self.inputs_name['2']])])
        screen_text.append([translate('slowerFaster'), translate('shiftControl')])

        if self.action == 'VALIDATE':
            self.end_of_adjustment()
            screen_text = []
            callback.append('STOP_ADJUSTMENT')
        elif self.action is not None:
            self.slider_origin = keys['mouse_x']

        ui.refresh_side_infos(screen_text)
        recalculate_array_center(self.obj)

        return callback


class rotation_management():
    def __init__(self, obj):
        self.obj = obj
        self.slider_origin = None
        self.previous_value = None
        self.enter_value = 'None'
        self.original_value = None
        self.rotate = None
        self.init = False
        self.array_axis = ''

        # affichage
        self.action = None
        self.ui_sent = False

        self.pie_menu = FLUENT_Ui_Layout('SCALE')
        self.pie_menu.set_layout('TAPER')
        self.pie_menu.set_obj(self.obj)

        button = make_button('VALIDATE')
        self.pie_menu.add_item(button)

        button = FLUENT_Ui_Button()
        button.set_text('')
        button.set_shape('CIRCLE')
        button.set_action('+X')
        button.set_default_color((.9, 0, 0, 1))
        self.pie_menu.add_item(button)

        button = FLUENT_Ui_Button()
        button.set_text('')
        button.set_shape('CIRCLE')
        button.set_action('+Y')
        button.set_default_color((0, .9, 0, 1))
        self.pie_menu.add_item(button)

        button = FLUENT_Ui_Button()
        button.set_text('')
        button.set_shape('CIRCLE')
        button.set_action('+Z')
        button.set_default_color((0, 0, .9, 1))
        self.pie_menu.add_item(button)

    def set_ui(self, ui):
        ui.hide_menu()
        ui.add_items(self.pie_menu)
        ui.hide_menu()
        self.ui_sent = True

    def get_pie_menu(self):
        return self.pie_menu

    def initiation(self):
        for m in self.obj.modifiers:
            if m.name == fluent_modifiers_name['rotate'] and m.type == 'NODES':
                self.rotate = m
        return self.rotate

    def get_modifier(self):
        return self.rotate

    def end_of_adjustment(self):
        self.slider_origin = None
        self.previous_value = None
        self.enter_value = 'None'
        self.original_value = {'axis':None, 'factor':None, 'lock_x':None, 'lock_y':None, 'lock_z':None}
        self.init = False
        self.array_axis = ''
        self.ui_sent = False

    def restore_value(self):
        self.rotate.node_group.nodes['Transform'].inputs[2].default_value[0] = self.original_value['r_x']
        self.rotate.node_group.nodes['Transform'].inputs[2].default_value[1] = self.original_value['r_y']
        self.rotate.node_group.nodes['Transform'].inputs[2].default_value[2] = self.original_value['r_z']

    def add_modifier(self):
        self.initiation()
        if not self.rotate:
            self.rotate = self.obj.modifiers.new(name=fluent_modifiers_name['rotate'], type='NODES')
            node_group = bpy.data.node_groups.new(name='Rotation', type='GeometryNodeTree')
            node_group.nodes.new(type='NodeGroupInput')
            node_group.nodes.new(type='NodeGroupOutput')
            if bpy.app.version >= (4, 0, 0):
                node_group.interface.new_socket(name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
                node_group.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
            else:
                node_group.inputs.new(type='NodeSocketGeometry', name='Geometry')
                node_group.outputs.new(type='NodeSocketGeometry', name='Geometry')
            self.rotate.node_group = node_group
            tree = self.rotate.node_group
            nodes = tree.nodes
            link = tree.links.new
            node_transform = nodes.new(type='GeometryNodeTransform')
            node_transform.name = 'Transform'
            for n in nodes:
                if n.type == 'GROUP_INPUT':
                    group_in = n
                if n.type == 'GROUP_OUTPUT':
                    group_out = n
            link(group_in.outputs[0], node_transform.inputs[0])
            link(node_transform.outputs[0], group_out.inputs[0])
            place_in_stack(self.obj, self.rotate)
        return self.rotate

    def adjust_modifier(self, ui: FLUENT_ui_management):
        callback = []
        screen_text = []

        keys = ui.event_dico_get()
        self.action = ui.get_button_action()[0]
        if not self.ui_sent:
            self.set_ui(ui)

        self.enter_value = enter_value(self.enter_value, keys)

        if not self.init:
            self.add_modifier()
            self.original_value = {
                'r_x':self.rotate.node_group.nodes['Transform'].inputs[2].default_value[0],
                'r_y':self.rotate.node_group.nodes['Transform'].inputs[2].default_value[1],
                'r_z':self.rotate.node_group.nodes['Transform'].inputs[2].default_value[2]
            }
            self.previous_value = {
                'r_x':self.rotate.node_group.nodes['Transform'].inputs[2].default_value[0],
                'r_y':self.rotate.node_group.nodes['Transform'].inputs[2].default_value[1],
                'r_z':self.rotate.node_group.nodes['Transform'].inputs[2].default_value[2]
            }
            self.init = True

        if keys['shift_work']:
            increment = 3000*get_addon_preferences().interface_factor
        elif keys['ctrl_work']:
            increment = 30*get_addon_preferences().interface_factor
        else:
            increment = 300*get_addon_preferences().interface_factor

        if self.array_axis and keys['value'] == 'PRESS' and keys['type'] == 'LEFTMOUSE':
            self.array_axis = None

        if type(self.action) == str and 'X' in self.action:
            self.slider_origin = keys['mouse_x']
            self.previous_value['x'] = self.rotate.node_group.nodes['Transform'].inputs[2].default_value[0]
            self.array_axis = 'X'
        elif type(self.action) == str and 'Y' in self.action:
            self.slider_origin = keys['mouse_x']
            self.previous_value['y'] = self.rotate.node_group.nodes['Transform'].inputs[2].default_value[1]
            self.array_axis = 'Y'
        elif type(self.action) == str and 'Z' in self.action:
            self.slider_origin = keys['mouse_x']
            self.previous_value['r_z'] = self.rotate.node_group.nodes['Transform'].inputs[2].default_value[2]
            self.array_axis = 'Z'

        if self.array_axis != None:
            if keys['ctrl_work']:
                snap = math.radians(45)
            else:
                snap = math.radians(5)

            if keys['shift_press'] or keys['shift_release'] or keys['ctrl_press'] or keys['ctrl_release']:
                self.slider_origin = keys['mouse_x']
                self.previous_value = {
                    'r_x':self.rotate.node_group.nodes['Transform'].inputs[2].default_value[0],
                    'r_y':self.rotate.node_group.nodes['Transform'].inputs[2].default_value[1],
                    'r_z':self.rotate.node_group.nodes['Transform'].inputs[2].default_value[2]
                }

            if self.array_axis == 'X':
                if enter_value_validation(self.enter_value, keys)[0]:
                    self.rotate.node_group.nodes['Transform'].inputs[2].default_value[0] = self.previous_value['x'] = enter_value_validation(self.enter_value, keys)[1]
                    self.enter_value = 'None'
                if keys['type'] == 'MOUSEMOVE' and not keys['show_menu']:
                    self.rotate.node_group.nodes['Transform'].inputs[2].default_value[0] = snap_slider_value(self.previous_value['r_x'], snap) + snap_slider_value((keys['mouse_x'] - self.slider_origin)/increment, snap)

            elif self.array_axis == 'Y':
                if enter_value_validation(self.enter_value, keys)[0]:
                    self.rotate.node_group.nodes['Transform'].inputs[2].default_value[1] = self.previous_value['y'] = enter_value_validation(self.enter_value, keys)[1]
                    self.enter_value = 'None'
                if keys['type'] == 'MOUSEMOVE' and not keys['show_menu']:
                    self.rotate.node_group.nodes['Transform'].inputs[2].default_value[1] = snap_slider_value(self.previous_value['r_y'], snap) + snap_slider_value((keys['mouse_x'] - self.slider_origin)/increment, snap)
            elif self.array_axis == 'Z':
                if enter_value_validation(self.enter_value, keys)[0]:
                    self.rotate.node_group.nodes['Transform'].inputs[2].default_value[2] = self.previous_value['r_z'] = enter_value_validation(self.enter_value, keys)[1]
                    self.enter_value = 'None'
                if keys['type'] == 'MOUSEMOVE' and not keys['show_menu']:
                    self.rotate.node_group.nodes['Transform'].inputs[2].default_value[2] = snap_slider_value(self.previous_value['r_z'], snap) + snap_slider_value((keys['mouse_x'] - self.slider_origin)/increment, snap)

            if keys['value'] == 'PRESS' and keys['type'] == 'ESC':
                self.restore_value()
                callback.append('DO_NOT_QUIT_FLUENT')

        if keys['value'] == 'PRESS' and keys['type'] == 'ESC':
            self.restore_value()
            callback.append('STOP_ADJUSTMENT')
            callback.append('DO_NOT_QUIT_FLUENT')
            self.end_of_adjustment()

        recalculate_array_center(self.obj)
        # TEXT
        screen_text.append([translate('angle'), adjustment_value(
            math.degrees(self.rotate.node_group.nodes['Transform'].inputs[2].default_value[0]),
            self.enter_value) + ' / ' + adjustment_value(
            math.degrees(self.rotate.node_group.nodes['Transform'].inputs[2].default_value[1]),
            self.enter_value) + ' / ' + adjustment_value(
            math.degrees(self.rotate.node_group.nodes['Transform'].inputs[2].default_value[2]),
            self.enter_value)])
        screen_text.append([translate('45Snap'), translate('holdControl')])
        if self.array_axis != None:
            screen_text.append([translate('validate'), translate('leftClick')])
        screen_text.append([translate('slowerFaster'), translate('shiftControl')])

        if self.action == 'VALIDATE':
            self.end_of_adjustment()
            screen_text = []
            callback.append('STOP_ADJUSTMENT')
        elif self.action is not None:
            self.slider_origin = keys['mouse_x']

        ui.refresh_side_infos(screen_text)

        return callback


def reuse_cutter(obj, bool_source: Object):
    global fluent_modifiers_to_exclude_per_type
    draw_type = obj.get('fluent_type')
    excluded_modifiers_for_shape = fluent_modifiers_to_exclude_per_type[draw_type]

    radius = None
    for mod in obj.modifiers:
        if fluent_modifiers_name['radius'] in mod.name:
            radius = mod.strength
        if any(x in mod.name for x in fluent_modifiers_to_ignore_for_reuse):
            continue

        if draw_type == 'path' and bool_source.get('fluent_type') != 'path' and any(x in mod.name for x in [fluent_modifiers_name['path_decimate'], fluent_modifiers_name['path_height'],fluent_modifiers_name['path_displace']]):
            continue

        if bool_source.get('fluent_type') in ['sphere', 'revolver'] and fluent_modifiers_name['first_solidify'] in mod.name:
            continue

        obj.modifiers.remove(mod)
    first_bevel_added = False
    source_radius = None
    source_inner_radius = None
    for mod in bool_source.modifiers:
        if fluent_modifiers_name['radius'] in mod.name:
            source_radius = mod.strength
        if fluent_modifiers_name['inner_radius'] in mod.name:
            source_inner_radius = mod.strength

    for mod in bool_source.modifiers:
        if not mod.show_viewport:
            continue

        if any(x in mod.name for x in fluent_modifiers_to_ignore_for_reuse):
            continue

        if any(x in mod.name for x in excluded_modifiers_for_shape):
            continue

        if fluent_modifiers_name['first_solidify'] in mod.name:
            first_solidify_management(obj, default_thickness=mod.thickness, default_offset=mod.offset)
            continue

        if fluent_modifiers_name['first_bevel'] in mod.name and not first_bevel_added:
            first_bevel_man = first_bevel_management(obj, with_dots=False)
            first_bevel_man.add_bevel(default_width=mod.width, default_profile=mod.profile)
            first_bevel_added = True
            continue

        if fluent_modifiers_name['second_solidify'] in mod.name:
            second_solidify_man = second_solidify_management(obj)
            second_solidify_man.add_solidify(default_thickness=mod.thickness, default_offset=mod.offset, show=True)
            continue

        if fluent_modifiers_name['chamfer'] in mod.name:
            chamfer_management(obj, segments=mod.segments, profile=mod.profile, width=mod.width)
            continue

        if fluent_modifiers_name['inner_radius'] in mod.name:
            new_mod = copy_modifiers_stack(bool_source, obj, mod.name, do_place_in_stack=True)
            source_gap = source_radius - source_inner_radius
            new_mod.strength = radius - source_gap
            continue

        # All the modifiers where a simple copy is working
        if any(x in mod.name for x in fluent_modifiers_simple_copy):
            copy_modifiers_stack(bool_source, obj, mod.name, do_place_in_stack=True)

    if obj.get('fluent_operation') == 'INSET' and bool_source.get('fluent_operation') == 'INSET':
        solidify_source = None
        for mod in bool_source.get('fluent_inset').modifiers:
            if fluent_modifiers_name['inset_solidify'] not in mod.name:
                continue

            solidify_source = mod
            break

        if solidify_source is not None:
            for mod in obj.get('fluent_inset').modifiers:
                if fluent_modifiers_name['inset_solidify'] not in mod.name:
                    continue

                mod.thickness = solidify_source.thickness
                mod.offset = solidify_source.offset
                break


class reuse_management():
    def __init__(self, obj):
        self.obj = obj
        self.init = False
        self.reuse_step = 1

    def initiation(self):
        for m in self.obj.modifiers:
            if m.name == fluent_modifiers_name['rotate'] and m.type == 'NODES':
                self.rotate = m
        return self.rotate

    def get_modifier(self):
        return self.rotate

    def end_of_adjustment(self, ui):
        bpy.context.window.cursor_set("DEFAULT")
        ui.pause_toggle = False
        self.reuse_step = 1

    def adjust_modifier(self, ui: FLUENT_ui_management):
        callback = []
        keys = ui.event_dico_get()

        bpy.context.window.cursor_set("DEFAULT")
        if self.reuse_step == 1:
            ui.refresh_side_infos([
                [translate('reuse'), translate('selectToReuse')],
                [translate('validate'), translate('enter')]
            ])
            affichage_booleen()

            self.reuse_step = 2
            ui.toggle_menu_displaying()
            ui.pause_toggle = True

        if self.reuse_step != 1:
            bpy.context.window.cursor_set("EYEDROPPER")

        if self.reuse_step == 2 and keys['type'] not in {'RET', 'NUMPAD_ENTER', 'RIGHTMOUSE', 'TAB'}:
            if keys['value'] == 'PRESS' and keys['type'] == 'ESC':
                affichage_booleen()
                self.end_of_adjustment(ui)
                callback.append('STOP_ADJUSTMENT')

                return callback

            return 'PASS_THROUGH'

        if self.reuse_step == 2 and keys['type'] in {'RET', 'NUMPAD_ENTER'}:
            ui.cursor_infos.reset_text()
            bool_source = bpy.context.active_object
            if len(bpy.context.selected_objects) != 1:
                ui.cursor_infos.set_text([translate('selectObject'), translate('thenEnter')])

                return 'PASS_THROUGH'

            targets = find_boolean_targets(bool_source)
            if len(targets) == 0:
                ui.cursor_infos.set_text([translate('selectCutter'), translate('thenEnter')])

                return 'PASS_THROUGH'


            try:
                bool_source['fluent_operation']
            except:
                ui.cursor_infos.set_text([translate('selectBoolean'), translate('thenEnter')])
                return 'PASS_THROUGH'

            affichage_booleen()
            reuse_cutter(self.obj, bool_source)

            self.end_of_adjustment(ui)
            callback.append('STOP_ADJUSTMENT')

        return callback


class outer_bevel_management():
    def __init__(self, bevel):
        self.slider_origin = None
        self.previous_value = None
        self.other_adjustment = 'WIDTH'
        self.enter_value = 'None'
        self.original_value = None
        self.init = False
        self.bevels = bevel # tableau contenant toutes les class outer bevel
        self.copy_bevel_step = 0
        self.simple_copy_mode = False

        # menu
        self.ui_sent = False
        self.action = None
        self.pie_menu = FLUENT_Ui_Layout('OUTER_BEVEL')
        self.pie_menu.set_layout('PIE')

        button = make_button('VALIDATE')
        self.pie_menu.add_item(button)

        button = FLUENT_Ui_Button()
        button.set_text(translate('width'))
        button.set_shape('RECTANGLE')
        button.set_action('WIDTH')
        self.pie_menu.add_item(button)

        button = FLUENT_Ui_Button()
        button.set_text(translate('angleLimit'))
        button.set_shape('RECTANGLE')
        button.set_action('ANGLE_LIMIT')
        self.pie_menu.add_item(button)

        button = FLUENT_Ui_Button()
        button.set_text(translate('copyBevel'))
        button.set_shape('RECTANGLE')
        button.set_action('COPY_BEVEL')
        self.pie_menu.add_item(button)

    def set_ui(self, ui):
        ui.hide_menu()
        ui.add_items(self.pie_menu)
        ui.hide_menu()
        self.ui_sent = True

    def get_pie_menu(self):
        return self.pie_menu

    def end_of_adjustment(self):
        self.slider_origin = None
        self.previous_value = None
        self.other_adjustment = 'WIDTH'
        self.enter_value = 'None'
        self.original_value = None
        self.init = False
        self.ui_sent = False

    def end_copy_boolean(self, ui: FLUENT_ui_management):
        self.copy_bevel_step = 0
        bpy.context.window.cursor_set("DEFAULT")
        active_object('SET', self.bevels[0].bool_obj, True)
        if self.simple_copy_mode:
            affichage_booleen()
        else:
            for bevel in self.bevels:
                display_object_booleans(bevel.target, hide=True)
        ui.pause_toggle = False

    def adjust(self, ui: FLUENT_ui_management):
        keys = ui.event_dico_get()
        self.action = ui.get_button_action()[0]
        if not self.ui_sent:
            self.set_ui(ui)

        self.enter_value = enter_value(self.enter_value, keys)

        callback = []

        if not self.init:
            self.slider_origin = keys['mouse_x']
            self.previous_value = self.bevels[0].get_width()
            self.original_value = self.bevels[0].get_width()
            self.init = True

        if self.action == 'WIDTH':
            self.other_adjustment = 'WIDTH'
            self.previous_value = self.bevels[0].get_width()
        elif self.action == 'ANGLE_LIMIT':
            self.other_adjustment = 'ANGLE_LIMIT'
            self.previous_value = self.bevels[0].get_angle_limit()
        elif self.action == 'COPY_BEVEL':
            self.other_adjustment = 'COPY_BEVEL'
            self.previous_value = self.bevels[0].get_width()
            self.copy_bevel_step = 1

            if keys['shift_work']:
                self.simple_copy_mode = True

        if keys['shift_work']:
            increment = 5000*get_addon_preferences().interface_factor
        elif keys['ctrl_work']:
            increment = 50*get_addon_preferences().interface_factor
        else:
            increment = 500*get_addon_preferences().interface_factor

        bpy.context.window.cursor_set("DEFAULT")
        if self.other_adjustment == 'COPY_BEVEL':
            if self.copy_bevel_step == 1:
                ui.refresh_side_infos([
                    [translate('outerBevel'), translate('selectBooleanCopy')],
                    [translate('validate'), translate('enter')]
                ])
                if self.simple_copy_mode:
                    affichage_booleen()
                else:
                    for bevel in self.bevels:
                        display_object_booleans(bevel.target, hide=False)

                self.copy_bevel_step = 2
                ui.toggle_menu_displaying()
                ui.pause_toggle = True

            if self.copy_bevel_step != 0:
                bpy.context.window.cursor_set("EYEDROPPER")

            if self.copy_bevel_step == 2 and keys['type'] not in {'RET', 'NUMPAD_ENTER', 'RIGHTMOUSE', 'TAB'}:
                if keys['value'] == 'PRESS' and keys['type'] == 'ESC':
                    self.end_copy_boolean(ui)

                return 'PASS_THROUGH'

            if self.copy_bevel_step == 2 and keys['type'] in {'RET', 'NUMPAD_ENTER'}:
                ui.cursor_infos.reset_text()
                bool_source = bpy.context.active_object
                if len(bpy.context.selected_objects) != 1:
                    ui.cursor_infos.set_text([translate('selectObject'), translate('thenEnter')])

                    return 'PASS_THROUGH'

                if self.simple_copy_mode:
                    targets = find_boolean_targets(bool_source)

                    if len(targets) == 0:
                        ui.cursor_infos.set_text([translate('selectCutter'), translate('thenEnter')])

                        return 'PASS_THROUGH'

                    outer_bever_copy = find_next_to_bool(targets[0]['cut_object'], targets[0]['boolean_modifier'])
                    if outer_bever_copy is None:
                        ui.cursor_infos.set_text([translate('selectBooleanCutterOB'), translate('thenEnter')])

                        return 'PASS_THROUGH'

                try:
                    bool_source['fluent_operation']
                except:
                    ui.cursor_infos.set_text([translate('selectBoolean'), translate('thenEnter')])
                    return 'PASS_THROUGH'

                if self.simple_copy_mode:
                    affichage_booleen()
                    self.simple_copy_bevel(bool_source, outer_bever_copy)
                else:
                    for bevel in self.bevels:
                        display_object_booleans(bevel.target, hide=False)
                    self.copy_bevel(bool_source)

                self.end_copy_boolean(ui)

        if keys['shift_press'] or keys['shift_release'] or keys['ctrl_press'] or keys['ctrl_release']:
            self.slider_origin = keys['mouse_x']
            if self.other_adjustment == 'WIDTH':
                self.previous_value = self.bevels[0].get_width()
            if self.other_adjustment == 'ANGLE_LIMIT':
                self.previous_value = self.bevels[0].get_angle_limit()

        if keys['type'] == 'MOUSEMOVE':
            if self.other_adjustment == 'WIDTH' and not keys['show_menu']:
                for b in self.bevels:
                    b.set_width(self.previous_value + ((keys['mouse_x'] - self.slider_origin) / increment))
                    b.refresh_hide_show_bevel_modifiers()
            if self.other_adjustment == 'ANGLE_LIMIT' and not keys['show_menu']:
                for b in self.bevels:
                    b.set_angle_limit(self.previous_value + ((keys['mouse_x'] - self.slider_origin) / increment))
        if self.other_adjustment != 'COPY_BEVEL' and enter_value_validation(self.enter_value, keys)[0]:
            if self.other_adjustment == 'WIDTH':
                for b in self.bevels:
                    b.set_width(enter_value_validation(self.enter_value, keys)[1])
                    b.refresh_hide_show_bevel_modifiers()
            if self.other_adjustment == 'ANGLE_LIMIT':
                for b in self.bevels:
                    b.set_angle_limit(enter_value_validation(self.enter_value, keys)[1])
            callback.append('STOP_ADJUSTMENT')
            self.end_of_adjustment()

        if keys['value'] == 'PRESS' and keys['type'] == 'ESC':
            try:
                for b in self.bevels:
                    b.set_width(self.original_value)
                    b.restore_initial_index()
                    b.refresh_hide_show_bevel_modifiers()
            except:
                pass
            self.end_of_adjustment()
            self.end_copy_boolean(ui)
            callback.append('DO_NOT_QUIT_FLUENT')
            callback.append('STOP_ADJUSTMENT')

        if keys['value'] == 'PRESS' and keys['type'] == 'DEL':
            try:
                for b in self.bevels:
                    b.restore_initial_index()
                    previous_bevel = b.find_previous_bevel()
                    b.set_width(previous_bevel.width)
                    b.refresh_hide_show_bevel_modifiers()
            except:
                pass
            self.end_of_adjustment()
            self.end_copy_boolean(ui)
            callback.append('DO_NOT_QUIT_FLUENT')
            callback.append('STOP_ADJUSTMENT')

        # TEXT
        screen_text = []
        screen_text.append([translate('width'), adjustment_value(self.bevels[0].get_width(), self.enter_value)])
        screen_text.append([translate('angleLimit'), adjustment_value(math.degrees(self.bevels[0].get_angle_limit()), self.enter_value)])
        screen_text.append([translate('remove'), translate('delete')])

        if self.action == 'VALIDATE':
            try:
                for b in self.bevels:
                    b.refresh_hide_show_bevel_modifiers()
            except:
                pass

            screen_text = []
            self.end_of_adjustment()
            self.end_copy_boolean(ui)
            callback.append('STOP_ADJUSTMENT')
        elif self.action is not None:
            self.slider_origin = keys['mouse_x']

        ui.refresh_side_infos(screen_text)

        return callback

    def simple_copy_bevel(self, bool_source: Object, outer_bever_copy: Modifier):
        for b in self.bevels:
            b.current_bevel.width = outer_bever_copy.width
            b.refresh_hide_show_bevel_modifiers()

    def copy_bevel(self, bool_source: Object):
        source_width = None
        for b in self.bevels:
            bool_source_mod = find_boolean_modifier(bool_source, b.target)
            if not bool_source_mod:
                continue

            bevel_source_mod = find_next_to_bool(b.target,bool_source_mod)
            source_width = bevel_source_mod.width

        if source_width is None:
            raise Exception('No Default Width found in any object to copy bevel')

        for b in self.bevels:
            bool_source_mod = find_boolean_modifier(bool_source, b.target)
            if not bool_source_mod:
                b.current_bevel.width = source_width
                b.refresh_hide_show_bevel_modifiers()
                continue

            bool_mod = find_boolean_modifier(b.bool_obj, b.target)
            bevel_source_mod = find_next_to_bool(b.target, bool_source_mod)

            move_modifier(obj=b.target, mod_name=b.current_bevel.name, where='ON', mod_target_name=bool_source_mod.name)
            move_modifier(obj=b.target, mod_name=bool_mod.name, where='ON', mod_target_name=b.current_bevel.name)
            b.current_bevel.width = bevel_source_mod.width
            b.refresh_hide_show_bevel_modifiers()


class frame_management():
    def __init__(self, obj, ui=None):
        self.obj = obj
        self.draw_type = obj.get('fluent_type')

        self.slider_origin = None
        self.previous_value = None
        self.adjust = 'DEPTH'
        self.inputs = {
            'WIDTH': 'Input_2',
            'DEPTH': 'Input_3',
            'OFFSET': 'Input_4',
            'Z': 'Input_5'
        }
        self.enter_value = 'None'
        self.original_value = None
        self.init = False

        self.ui_sent = False

        self.frame = None
        for m in self.obj.modifiers:
            if m.name == fluent_modifiers_name['frame'] and m.type == 'NODES':
                self.frame = m
                break
        if not self.frame:
            self.add_frame()

        # menu
        self.action = None
        self.pie_menu = FLUENT_Ui_Layout('FRAME')
        self.pie_menu.set_layout('PIE')

        button = make_button('VALIDATE')
        self.pie_menu.add_item(button)

        button = FLUENT_Ui_Button()
        button.set_text(translate('widthShortCutC'))
        button.set_shape('RECTANGLE')
        button.set_action('WIDTH')
        self.pie_menu.add_item(button)

        button = FLUENT_Ui_Button()
        button.set_text(translate('depthShortCut'))
        button.set_shape('RECTANGLE')
        button.set_action('DEPTH')
        self.pie_menu.add_item(button)

        button = FLUENT_Ui_Button()
        button.set_text(translate('offsetShortCutV'))
        button.set_shape('RECTANGLE')
        button.set_action('OFFSET')
        self.pie_menu.add_item(button)

        button = FLUENT_Ui_Button()
        button.set_text(translate('zPosition'))
        button.set_shape('RECTANGLE')
        button.set_action('Z')
        self.pie_menu.add_item(button)

    def get_modifier(self):
        return self.frame

    def set_ui(self, ui):
        ui.hide_menu()
        ui.add_items(self.pie_menu)
        ui.hide_menu()
        self.ui_sent = True

    def get_pie_menu(self):
        return self.pie_menu

    def add_frame(self):
        main_dir = join(dirname(realpath(__file__)))
        blender_dir = join(main_dir, 'geometry_nodes')
        blender_file = join(blender_dir, 'frame.blend')
        file_path_node_tree = join(blender_file, 'NodeTree')

        group_name = fluent_modifiers_name['frame']
        if not bpy.data.node_groups.get(group_name):
            bpy.ops.wm.append(filename=group_name, directory=file_path_node_tree)

        self.frame = self.obj.modifiers.new(name=fluent_modifiers_name['frame'], type='NODES')
        self.frame.node_group = bpy.data.node_groups[group_name]
        self.frame.show_in_editmode = True
        self.frame.show_expanded = False

        place_in_stack(self.obj, self.frame)
        return self.frame

    def end_of_adjustment(self):
        self.slider_origin = None
        self.previous_value = None
        self.adjust = 'WIDTH'
        self.enter_value = 'None'
        self.original_value = None
        self.init = False
        self.ui_sent = False
        if self.frame[self.inputs['WIDTH']] <= 0 or self.frame[self.inputs['DEPTH']] <= 0:
            self.frame.show_viewport = self.frame.show_render = False

    def adjust_frame(self, ui: FLUENT_ui_management):
        if not self.ui_sent:
            self.set_ui(ui)
        keys = ui.event_dico_get()
        self.enter_value = enter_value(self.enter_value, keys)

        callback = []

        if not self.init:
            self.slider_origin = keys['mouse_x']
            self.previous_value = self.frame[self.inputs[self.adjust]]
            self.original_value = get_modifier_values(self.frame)
            self.frame.show_render = self.frame.show_viewport = True
            self.init = True

        if keys['shift_work']:
            increment = 3000*get_addon_preferences().interface_factor
        elif keys['ctrl_work']:
            increment = 30*get_addon_preferences().interface_factor
        else:
            increment = 300*get_addon_preferences().interface_factor

        if keys['shift_press'] or keys['shift_release'] or keys['ctrl_press'] or keys['ctrl_release']:
            self.slider_origin = keys['mouse_x']
            self.previous_value = self.frame[self.inputs[self.adjust]]

        if keys['type'] == 'MOUSEMOVE' and not keys['show_menu']:
            self.frame[self.inputs[self.adjust]] = self.previous_value + ((keys['mouse_x'] - self.slider_origin) / increment)
            if self.adjust in ['DEPTH', 'WIDTH'] and self.frame[self.inputs[self.adjust]] < 0:
                self.frame[self.inputs[self.adjust]] = 0.0
        if enter_value_validation(self.enter_value, keys)[0]:
            self.frame[self.inputs[self.adjust]] = enter_value_validation(self.enter_value, keys)[1]
            self.end_of_adjustment()
            callback.append('STOP_ADJUSTMENT')

        if keys['value'] == 'PRESS' and keys['type'] == 'ESC':
            try:
                set_modifier_value(self.frame, self.original_value)
            except:pass
            self.end_of_adjustment()
            callback.append('DO_NOT_QUIT_FLUENT')
            callback.append('STOP_ADJUSTMENT')

        # rafraichir le viewport (merci geometry nodes)
        self.frame.show_viewport = False
        self.frame.show_viewport = True

        # TEXT
        screen_text = []
        if self.adjust == 'DEPTH':
            screen_text.append([translate('depth'), adjustment_value(self.frame[self.inputs[self.adjust]], self.enter_value)])
        else:
            screen_text.append([translate('depth'), modifier_value_converter(self.frame[self.inputs['DEPTH']])])

        if self.adjust == 'WIDTH':
            screen_text.append([translate('width'), adjustment_value(self.frame[self.inputs[self.adjust]], self.enter_value)])
        else:
            screen_text.append([translate('width'), modifier_value_converter(self.frame[self.inputs['WIDTH']])])

        if self.adjust == 'OFFSET':
            screen_text.append([translate('offset'), adjustment_value(self.frame[self.inputs[self.adjust]], self.enter_value)])
        else:
            screen_text.append([translate('offset'), modifier_value_converter(self.frame[self.inputs['OFFSET']])])

        if self.adjust == 'Z':
            screen_text.append(['Z', adjustment_value(self.frame[self.inputs[self.adjust]], self.enter_value)])
        else:
            screen_text.append(['Z', modifier_value_converter(self.frame[self.inputs['Z']])])
        screen_text.append([translate('slowerFaster'), translate('shiftControl')])

        ui.refresh_side_infos(screen_text)
        recalculate_array_center(self.obj)

        self.action = ui.get_button_action()[0]

        if self.action == 'VALIDATE':
            self.end_of_adjustment()
            callback.append('STOP_ADJUSTMENT')
        if (self.adjust == 'DEPTH' and keys['value'] == 'PRESS' and keys['type'] == 'C') or self.action == 'WIDTH':
            self.adjust = 'WIDTH'
            self.previous_value = self.frame[self.inputs[self.adjust]]
            self.slider_origin = keys['mouse_x']
        elif (self.adjust == 'WIDTH' and keys['value'] == 'PRESS' and keys['type'] == 'C') or self.action == 'DEPTH':
            self.adjust = 'DEPTH'
            self.previous_value = self.frame[self.inputs[self.adjust]]
            self.slider_origin = keys['mouse_x']
        if (self.adjust == 'Z' and keys['value'] == 'PRESS' and keys['type'] == 'V') or self.action == 'OFFSET':
            self.adjust = 'OFFSET'
            self.previous_value = self.frame[self.inputs[self.adjust]]
            self.slider_origin = keys['mouse_x']
        elif (self.adjust == 'OFFSET' and keys['value'] == 'PRESS' and keys['type'] == 'V') or self.action == 'Z':
            self.adjust = 'Z'
            self.previous_value = self.frame[self.inputs[self.adjust]]
            self.slider_origin = keys['mouse_x']

        return callback


class chamfer_management():
    def __init__(self, obj, ui=None, segments=1, profile=0.25, width=0):
        self.obj = obj
        self.draw_type = obj.get('fluent_type')

        self.slider_origin = None
        self.previous_value = None
        self.prevent_auto_segments = False
        self.adjust = 'WIDTH'
        self.enter_value = 'None'
        self.original_value = None
        self.init = False

        self.ui_sent = False

        self.chamfer = None
        self.pre_chamfer = None
        for m in self.obj.modifiers:
            if m.name == fluent_modifiers_name['chamfer']:
                self.chamfer = m
            if m.name == fluent_modifiers_name['pre_chamfer']:
                self.pre_chamfer = m
            if self.chamfer and self.pre_chamfer:
                break
        if not self.chamfer:
            self.add_chamfer(segments, profile, width)

        # menu
        self.action = None
        self.pie_menu = FLUENT_Ui_Layout('FRAME')
        self.pie_menu.set_layout('PIE')

        button = make_button('VALIDATE')
        self.pie_menu.add_item(button)

        button = FLUENT_Ui_Button()
        button.set_text(translate('width'))
        button.set_shape('RECTANGLE')
        button.set_action('WIDTH')
        self.pie_menu.add_item(button)

        button = FLUENT_Ui_Button()
        button.set_text(translate('straightShortCut'))
        button.set_shape('RECTANGLE')
        button.set_action('STRAIGHT')
        self.pie_menu.add_item(button)

        button = FLUENT_Ui_Button()
        button.set_text(translate('concaveShortCut'))
        button.set_shape('RECTANGLE')
        button.set_action('CONCAVE')
        self.pie_menu.add_item(button)

        button = FLUENT_Ui_Button()
        button.set_text(translate('convexShortCut'))
        button.set_shape('RECTANGLE')
        button.set_action('CONVEX')
        self.pie_menu.add_item(button)

        button = FLUENT_Ui_Button()
        button.set_text(translate('segmentsShortCut'))
        button.set_shape('RECTANGLE')
        button.set_action('SEGMENTS')
        self.pie_menu.add_item(button)

    def get_modifier(self):
        return self.chamfer

    def set_ui(self, ui):
        ui.hide_menu()
        ui.add_items(self.pie_menu)
        ui.hide_menu()
        self.ui_sent = True

    def get_pie_menu(self):
        return self.pie_menu

    def add_chamfer(self, segments=1, profile=0.25, width=0):
        for vg in self.obj.vertex_groups:
            if vg.name in ['top', 'bottom']:
                self.obj.vertex_groups.remove(vg)
        v_group = self.obj.vertex_groups.new(name='top_face')
        # v_group_bottom = self.obj.vertex_groups.new(name='bottom_face')

        main_dir = join(dirname(realpath(__file__)))
        blender_dir = join(main_dir, 'geometry_nodes')
        blender_file = join(blender_dir, 'chamfer.blend')
        file_path_node_tree = join(blender_file, 'NodeTree')

        group_name = fluent_modifiers_name['pre_chamfer']
        if not bpy.data.node_groups.get(group_name):
            bpy.ops.wm.append(filename=group_name, directory=file_path_node_tree)

        self.pre_chamfer = self.obj.modifiers.new(name=fluent_modifiers_name['pre_chamfer'], type='NODES')
        self.pre_chamfer.node_group = bpy.data.node_groups[group_name]
        self.pre_chamfer.show_in_editmode = True
        self.pre_chamfer.show_expanded = False
        self.pre_chamfer["Output_2_attribute_name"] = 'top_face'
        self.pre_chamfer["Output_3_attribute_name"] = 'bottom_face'

        place_in_stack(self.obj, self.pre_chamfer)

        self.chamfer = self.obj.modifiers.new(name=fluent_modifiers_name['chamfer'], type='BEVEL')
        self.chamfer.affect = 'EDGES'
        self.chamfer.offset_type = 'OFFSET'
        self.chamfer.segments = segments
        self.chamfer.profile = profile
        self.chamfer.limit_method = 'VGROUP'
        self.chamfer.vertex_group = 'top_face'
        self.chamfer.use_clamp_overlap = False
        self.chamfer.width = width
        self.chamfer.show_expanded = False

        place_in_stack(self.obj, self.chamfer)

        return self.chamfer

    def remove(self):
        self.obj.modifiers.remove(self.chamfer)
        self.obj.modifiers.remove(self.pre_chamfer)
        self.pre_chamfer = None
        self.chamfer = None

    def end_of_adjustment(self):
        self.slider_origin = None
        self.previous_value = None
        self.adjust = 'WIDTH'
        self.enter_value = 'None'
        self.original_value = None
        self.init = False
        self.ui_sent = False
        if self.chamfer and self.chamfer.width <= 0:
            self.chamfer.show_viewport = self.chamfer.show_render = False
            self.pre_chamfer.show_viewport = self.pre_chamfer.show_render = False

    def adjust_chamfer(self, ui: FLUENT_ui_management):
        if not self.ui_sent:
            self.set_ui(ui)
        keys = ui.event_dico_get()
        self.enter_value = enter_value(self.enter_value, keys)

        callback = []

        if not self.init:
            self.slider_origin = keys['mouse_x']
            self.previous_value = self.chamfer.width
            self.original_value = get_modifier_values(self.chamfer)
            self.chamfer.show_render = self.chamfer.show_viewport = True
            self.pre_chamfer.show_render = self.pre_chamfer.show_viewport = True
            for m in self.obj.modifiers:
                if m.name == fluent_modifiers_name['pre_second_bevel_bottom']:
                    m['Input_8'] = False
                if m.name == fluent_modifiers_name['second_bevel_top']:
                    m.show_viewport = m.show_render = False
                if m.name == fluent_modifiers_name['pre_second_bevel_top'] :
                    m.show_viewport = m.show_render = False
            self.init = True

        if keys['value'] == 'PRESS' and keys['type'] == 'C':
            bevel_type = None
            if self.chamfer.segments > 2 and round(self.chamfer.profile, 2) != 0.08:
                bevel_type = 'convex'
            elif self.chamfer.segments in {1, 2}:
                bevel_type = 'straight'
            elif self.chamfer.segments != 1 and round(self.chamfer.profile, 2) == 0.08:
                bevel_type = 'concave'
            if bevel_type == 'convex':
                self.action = 'STRAIGHT'
            elif bevel_type == 'straight':
                self.action = 'CONCAVE'
            elif bevel_type == 'concave':
                self.action = 'CONVEX'

        if keys['value'] == 'PRESS' and keys['type'] == 'B':
            self.action = 'STRAIGHT_1'

        if self.action == 'STRAIGHT_1':
            if self.chamfer.segments == 2:
                self.chamfer.segments = 1
                self.chamfer.profile = 0.25
            elif self.chamfer.segments == 1:
                self.chamfer.segments = 2
                self.chamfer.profile = 0.25
        elif self.action == 'STRAIGHT':
            self.chamfer.segments = 1
            self.chamfer.profile = 0.25
        elif self.action == 'CONCAVE':
            self.chamfer.segments = auto_bevel_segments(self.chamfer)
            self.chamfer.profile = 0.08
        elif self.action == 'CONVEX':
            self.chamfer.segments = auto_bevel_segments(self.chamfer)
            self.chamfer.profile = bpy.context.scene.fluentProp.bevel_profile

        if keys['shift_work']:
            increment = 3000*get_addon_preferences().interface_factor
        elif keys['ctrl_work']:
            increment = 30*get_addon_preferences().interface_factor
        else:
            increment = 300*get_addon_preferences().interface_factor

        if keys['shift_press'] or keys['shift_release'] or keys['ctrl_press'] or keys['ctrl_release']:
            self.slider_origin = keys['mouse_x']
            if self.adjust == 'WIDTH':
                self.previous_value = self.chamfer.width

        if self.adjust == 'WIDTH':
            if keys['type'] == 'MOUSEMOVE' and not keys['show_menu']:
                self.chamfer.width = self.previous_value + ((keys['mouse_x'] - self.slider_origin) / increment)
                if self.chamfer.width < 0:
                    self.chamfer.width = 0
            if enter_value_validation(self.enter_value, keys)[0]:
                self.chamfer.width = enter_value_validation(self.enter_value, keys)[1]
                self.adjust = None
                self.end_of_adjustment()
                callback.append('STOP_ADJUSTMENT')
        if self.adjust == 'SEGMENTS':
            if keys['type'] == 'MOUSEMOVE' and not keys['show_menu']:
                self.prevent_auto_segments = True
                self.chamfer.segments = int(self.previous_value + ((keys['mouse_x'] - self.slider_origin) / increment))
            if enter_value_validation(self.enter_value, keys)[0]:
                self.prevent_auto_segments = True
                self.chamfer.segments = int(enter_value_validation(self.enter_value, keys)[1])
                self.adjust = None
                self.end_of_adjustment()
                callback.append('STOP_ADJUSTMENT')

        if self.chamfer.profile != 0.25 and self.adjust != 'SEGMENTS' and not self.prevent_auto_segments:
            self.chamfer.segments = auto_bevel_segments(bevel=self.chamfer)

        if keys['value'] == 'PRESS' and keys['type'] == 'ESC':
            try:
                set_modifier_value(self.chamfer, self.original_value)
            except:pass
            self.end_of_adjustment()
            callback.append('DO_NOT_QUIT_FLUENT')
            callback.append('STOP_ADJUSTMENT')

        # rafraichir le viewport (merci geometry nodes)
        self.chamfer.show_viewport = False
        self.chamfer.show_viewport = True

        # TEXT
        screen_text = []

        if self.adjust == 'WIDTH':
            screen_text.append([translate('width'), adjustment_value(self.chamfer.width, self.enter_value)])
        else:
            screen_text.append([translate('width'), modifier_value_converter(self.chamfer.width)])
        if self.adjust == 'SEGMENTS':
            screen_text.append([translate('segments'), adjustment_value(self.chamfer.segments, self.enter_value)])
        else:
            screen_text.append([translate('segments'), modifier_value_converter(self.chamfer.segments)])


        screen_text.append([translate('oneSegment'), 'B'])
        screen_text.append([translate('slowerFaster'), translate('shiftControl')])

        ui.refresh_side_infos(screen_text)
        recalculate_array_center(self.obj)

        self.action = ui.get_button_action()[0]

        if keys['value'] == 'PRESS' and keys['type'] == 'V':
            if self.adjust == 'WIDTH':
                self.action = 'SEGMENTS'
            elif self.adjust == 'SEGMENTS':
                self.action = 'WIDTH'

        if self.action:
            self.slider_origin = keys['mouse_x']
        if self.action == 'VALIDATE':
            self.end_of_adjustment()
            callback.append('STOP_ADJUSTMENT')
        if self.action == 'SEGMENTS':
            self.adjust = 'SEGMENTS'
            self.previous_value = self.chamfer.segments
            self.slider_origin = keys['mouse_x']
        if self.action == 'WIDTH':
            self.adjust = 'WIDTH'
            self.previous_value = self.chamfer.width
            self.slider_origin = keys['mouse_x']


        return callback