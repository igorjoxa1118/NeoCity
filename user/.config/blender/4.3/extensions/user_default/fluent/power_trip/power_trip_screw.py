import bpy
from bpy.props import StringProperty
from bpy.types import Operator

from ..Tools.translation import translate
from ..UI.Helpers.viewport_drawing import *
from ..UI.Helpers.ui_button import *
import time
import os
from os.path import join, dirname, realpath, normpath
from ..UI.make_button import make_button
from ..UI.Helpers.ui_management import FLUENT_ui_management
from ..Tools.independant_helper import *
from ..modifiers import mirror_management


def tool_type_list_ui():
    # menu box
    pie_menu = FLUENT_Ui_Layout('TOOL_LIST', title=translate('driveType'), subtitle=translate('driveType'))
    pie_menu.set_layout('PIE')

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_tool_tip(translate('tool')+' 0')
    button.set_shape('CIRCLE')
    button.set_icon('screw_head_tool_00')
    button.set_action('00_HEAD_MENU')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_tool_tip(translate('tool')+' 1')
    button.set_shape('CIRCLE')
    button.set_icon('screw_head_tool_01')
    button.set_action('01_HEAD_MENU')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_tool_tip(translate('tool')+' 2')
    button.set_shape('CIRCLE')
    button.set_icon('screw_head_tool_02')
    button.set_action('02_HEAD_MENU')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_tool_tip(translate('tool')+' 3')
    button.set_shape('CIRCLE')
    button.set_icon('screw_head_tool_03')
    button.set_action('03_HEAD_MENU')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_tool_tip(translate('tool')+' 4')
    button.set_shape('CIRCLE')
    button.set_icon('screw_head_tool_04')
    button.set_action('04_HEAD_MENU')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_tool_tip(translate('tool')+' 5')
    button.set_shape('CIRCLE')
    button.set_icon('screw_head_tool_05')
    button.set_action('05_HEAD_MENU')
    pie_menu.add_item(button)

    button = make_button('BACK')
    pie_menu.add_item(button)

    return pie_menu


def head_type_list_ui():
    # menu box
    pie_menu = FLUENT_Ui_Layout('HEAD_LIST', title=translate('headType'), subtitle=translate('holdShift'))
    pie_menu.set_layout('PIE')

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_tool_tip(translate('head')+' 00')
    button.set_shape('CIRCLE')
    button.set_icon('screw_head_style_00')
    button.set_action('CHANGE_HEAD_00')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_tool_tip(translate('head')+' 01')
    button.set_shape('CIRCLE')
    button.set_icon('screw_head_style_01')
    button.set_action('CHANGE_HEAD_01')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_tool_tip(translate('head')+' 02')
    button.set_shape('CIRCLE')
    button.set_icon('screw_head_style_02')
    button.set_action('CHANGE_HEAD_02')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_tool_tip(translate('head')+' 03')
    button.set_shape('CIRCLE')
    button.set_icon('screw_head_style_03')
    button.set_action('CHANGE_HEAD_03')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_tool_tip(translate('head')+' 04')
    button.set_shape('CIRCLE')
    button.set_icon('screw_head_style_04')
    button.set_action('CHANGE_HEAD_04')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_tool_tip(translate('head')+' 05')
    button.set_shape('CIRCLE')
    button.set_icon('screw_head_style_05')
    button.set_action('CHANGE_HEAD_05')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_tool_tip(translate('head')+' 06')
    button.set_shape('CIRCLE')
    button.set_icon('screw_head_style_06')
    button.set_action('CHANGE_HEAD_06')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_tool_tip(translate('head')+' 07')
    button.set_shape('CIRCLE')
    button.set_icon('screw_head_style_07')
    button.set_action('CHANGE_HEAD_07')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_tool_tip(translate('head')+' 08')
    button.set_shape('CIRCLE')
    button.set_icon('screw_head_style_08')
    button.set_action('CHANGE_HEAD_08')
    pie_menu.add_item(button)

    button = make_button('BACK')
    pie_menu.add_item(button)

    return pie_menu


def screw_adjust_ui():
    pie_menu = FLUENT_Ui_Layout('ADJUSTMENTS', title='Screw menu', subtitle=translate('holdShift'))
    pie_menu.set_layout('PIE')

    button = make_button('QUIT')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_tool_tip(translate('change'))
    button.set_shape('CIRCLE')
    button.set_icon('change')
    button.set_action('TOOL_TYPE_MENU')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_tool_tip(translate('mergeDistance'))
    button.set_shape('CIRCLE')
    button.set_icon('merge')
    button.set_action('MERGE')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_tool_tip(translate('scale'))
    button.set_shape('CIRCLE')
    button.set_icon('scale')
    button.set_action('SCALE')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_tool_tip(translate('position'))
    button.set_shape('CIRCLE')
    button.set_icon('move')
    button.set_action('OFFSET')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_tool_tip(translate('gap'))
    button.set_shape('CIRCLE')
    button.set_icon('thickness')
    button.set_action('GAP')
    pie_menu.add_item(button)

    button = make_button('MIRROR')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text(translate('io'))
    button.set_tool_tip(translate('insideOutside'))
    button.set_shape('RECTANGLE')
    button.set_action('INSIDE')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text(translate('1pF'))
    button.set_tool_tip(translate('onePerFace'))
    button.set_shape('RECTANGLE')
    button.set_action('ONE_PER_FACE')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text(translate('loop'))
    button.set_tool_tip('')
    button.set_shape('RECTANGLE')
    button.set_action('CORNERS')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_tool_tip(translate('reuse'))
    button.set_shape('CIRCLE')
    button.set_icon('reuse')
    button.set_action('REUSE')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_tool_tip(translate('debugView'))
    button.set_shape('CIRCLE')
    button.set_icon('show_bool')
    button.set_action('DEBUG')
    pie_menu.add_item(button)

    return pie_menu


def scale_ui():
    pie_menu = FLUENT_Ui_Layout('SCALE')
    pie_menu.set_layout('PIE')

    button = make_button('VALIDATE')
    pie_menu.add_item(button)

    return pie_menu


def offset_ui():
    pie_menu = FLUENT_Ui_Layout('OFFSET')
    pie_menu.set_layout('PIE')

    button = make_button('VALIDATE')
    pie_menu.add_item(button)

    return pie_menu


class FLUENT_OT_Screw(Operator):
    """Place screw heads on face
Select an object before."""
    bl_idname = "fluent.screw"
    bl_label="Screw heads"
    bl_options={'REGISTER','UNDO'}

    operation: StringProperty(
        default=''
    )

    ui_management = None

    @classmethod
    def poll(cls, context):
        if context.object and context.object.mode == 'OBJECT':
            return True
        else:
            return False

    def adjustment(self):
        what = self.status.split('#')[1]
        screen_text = []
        callback = []
        events = self.ui_management.event_dico_get()
        self.enter_value = enter_value(self.enter_value, events)

        if 'SCALE' in what:
            if events['shift_work']:
                increment = 12000
            elif events['ctrl_work']:
                increment = 120
            else:
                increment = 1200

            if events['shift_press'] or events['shift_release'] or events['ctrl_press'] or events['ctrl_release']:
                self.slider_origin_x = events['mouse_x']
                self.previous_value = self.modifier['Input_6']

            self.modifier['Input_6'] = self.previous_value + (events['mouse_x'] - self.slider_origin_x) / increment

            if enter_value_validation(self.enter_value, events)[0]:
                self.modifier['Input_6'] = enter_value_validation(self.enter_value, events)[1]
                callback.append('STOP_ADJUSTMENT')
                self.enter_value = 'None'

            if events['type'] == 'ESC' and events['value'] == 'PRESS':
                self.modifier['Input_6'] = self.original_value
                self.status = 'SCREW_ADDED'
                self.ui_management.remove_last_menu()

            if self.modifier['Input_6'] < 0:
                self.modifier['Input_6'] = 0
            bpy.context.scene.fluentProp.screw_scale = self.modifier['Input_6']

            # TEXT
            screen_text.append(['Width', adjustment_value(self.modifier['Input_6'], self.enter_value)])

        if 'OFFSET' in what:
            if events['shift_work']:
                increment = 8000
            elif events['ctrl_work']:
                increment = 80
            else:
                increment = 800

            if events['shift_press'] or events['shift_release'] or events['ctrl_press'] or events['ctrl_release']:
                self.slider_origin_x = events['mouse_x']
                self.previous_value = self.modifier['Input_5']

            self.modifier['Input_5'] = self.previous_value + (events['mouse_x'] - self.slider_origin_x) / increment

            if enter_value_validation(self.enter_value, events)[0]:
                self.modifier['Input_5'] = enter_value_validation(self.enter_value, events)[1]
                callback.append('STOP_ADJUSTMENT')
                self.enter_value = 'None'

            if events['type'] == 'ESC' and events['value'] == 'PRESS':
                self.modifier['Input_5'] = self.original_value
                self.status = 'SCREW_ADDED'
                self.ui_management.remove_last_menu()

            if self.modifier['Input_5'] < 0:
                self.modifier['Input_5'] = 0
            bpy.context.scene.fluentProp.screw_offset = self.modifier['Input_5']

            # TEXT
            screen_text.append(['Offset', adjustment_value(self.modifier['Input_5'], self.enter_value)])

        if 'MERGE' in what:
            if events['shift_work']:
                increment = 8000
            elif events['ctrl_work']:
                increment = 80
            else:
                increment = 800

            if events['shift_press'] or events['shift_release'] or events['ctrl_press'] or events['ctrl_release']:
                self.slider_origin_x = events['mouse_x']
                self.previous_value = self.modifier['Input_4']

            self.modifier['Input_4'] = self.previous_value + (events['mouse_x'] - self.slider_origin_x) / increment
            bpy.context.scene.fluentProp.screw_offset = self.modifier['Input_4']

        if 'GAP' in what:
            if events['shift_work']:
                increment = 8000
            elif events['ctrl_work']:
                increment = 80
            else:
                increment = 800

            if events['shift_press'] or events['shift_release'] or events['ctrl_press'] or events['ctrl_release']:
                self.slider_origin_x = events['mouse_x']
                self.previous_value = self.modifier['Input_16']

            self.modifier['Input_16'] = self.previous_value + (events['mouse_x'] - self.slider_origin_x) / increment

            if events['type'] == 'ESC' and events['value'] == 'PRESS':
                self.modifier['Input_16'] = self.original_value
                self.status = 'SCREW_ADDED'
                self.ui_management.remove_last_menu()

            bpy.context.scene.fluentProp.screw_offset = self.modifier['Input_16']

        self.modifier.show_viewport = False
        self.modifier.show_viewport = True

        return callback, screen_text

    def change_screw(self):
        file_path = join(os.path.dirname(realpath(__file__)),normpath('screws/head_screw.blend/Object/'))
        screw_name = 'Retopo_Head_Screw_' + str(self.choice[1]) + '_' + str(self.choice[0])
        if not bpy.data.objects.get(screw_name):
            bpy.ops.wm.append(filename=screw_name, directory=file_path, do_reuse_local_id=True)
            bpy.data.objects[screw_name].hide_render = True
            bpy.data.objects[screw_name].hide_set(True)
        self.modifier['Input_7'] = bpy.data.objects[screw_name]
        self.modifier.show_viewport = False
        self.modifier.show_viewport = True
        self.ui_management.remove_last_menu()
        active_object('SET', self.screw_support, True)
        # place dans une collection dédiée
        if not bpy.data.collections.get('F_Screw_Objects'):
            coll = bpy.data.collections.new("F_Screw_Objects")
            bpy.context.scene.collection.children.link(coll)
        try:
            bpy.data.collections['F_Screw_Objects'].objects.link(bpy.data.objects[screw_name])
        except:
            pass
        try:
            bpy.context.scene.collection.objects.unlink(bpy.data.objects[screw_name])
        except:
            pass

    def end(self):
        bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')

    def copy_mirror(self, source, target):
        try:
            mirror_source = source.modifiers[fluent_modifiers_name['mirror']]
            mirror_data = get_modifier_values(mirror_source)
            mirror_mod = None
            try:
                mirror_mod = target.modifiers[fluent_modifiers_name['mirror']]
            except:
                pass

            if mirror_mod is None:
                mirror = mirror_management(target, None)
                mirror.add_mirror(None)
            set_modifier_value(target.modifiers[fluent_modifiers_name['mirror']], mirror_data)
        except: pass

    def modal(self, context, event):
        self.ui_management.refresh_ui_items_list()

        context.area.tag_redraw()
        events = self.ui_management.event_dico_refresh(event)

        if self.status == 'WAIT_SELECTION' and event.type not in ['RET', 'NUMPAD_ENTER', 'ESC'] and bpy.context.active_object and bpy.context.active_object.mode == 'EDIT':
            return {'PASS_THROUGH'}

        if self.status == 'SCREW_ADDED' and (pass_through(event) or event.type == 'TAB' or (bpy.context.active_object and bpy.context.active_object.mode == 'EDIT')):
            return {'PASS_THROUGH'}

        if event.type == 'ESC' and event.value == 'PRESS' and self.status == 'WAIT_REUSE':
            self.status = 'SCREW_ADDED'

        if event.type == 'RIGHTMOUSE' and event.value == 'PRESS' and self.status == 'SCREW_ADDED':
            self.end()
            return {'FINISHED'}

        # action via les bouttons
        action = self.ui_management.get_button_action()[0]
        refresh_pos = True
        callback = []

        if event.type == 'M' and event.value == 'PRESS':
            action = 'MIRROR'

        if action == 'MIRROR' or self.statut == 'AJUSTEMENT_EN_COURS':
            self.statut = 'AJUSTEMENT_EN_COURS'
            if not self.mirror:
                self.mirror = mirror_management(self.screw_support, None)
            callback = self.mirror.adjust_mirror(self.ui_management)
            self.ui_management.pause_toggle = True

        if 'callback' in locals() and 'PASS_THROUGH' in callback:
            return {'PASS_THROUGH'}

        if 'callback' in locals() and 'STOP_ADJUSTMENT' in callback:
            self.copy_mirror(self.screw_support, self.screw_bool)

            self.screw_bool.hide_set(True)
            callback.append('CLOSE_WIDGET')
            self.ui_management.clean_side_infos()
            self.ui_management.pause_toggle = False
            self.ui_management.refresh_ui_items_list(close_widget=True)

            self.statut = None

        if action:
            if action == 'FINISHED':
                self.end()
                return {'FINISHED'}
            elif action == 'CANCELLED':
                self.end(cancel=True)
                return {'FINISHED'}
            elif 'CHANGE_' in action:
                self.choice[1] = action.split('_')[2]
                self.change_screw()
                self.ui_management.remove_last_menu()
            elif 'TOOL_TYPE_MENU' in action and not event.shift:
                self.ui_management.position_menu_under_previous(self.pie_menu_tool_list)
                self.ui_management.add_items(self.pie_menu_tool_list, is_submenu=True)
                refresh_pos = False
            elif 'HEAD_MENU' in action and not event.shift:
                self.choice[0] = action.split('_')[0]
                self.ui_management.position_menu_under_previous(self.pie_menu_head_list)
                self.ui_management.add_items(self.pie_menu_head_list, is_submenu=True)
                refresh_pos = False
            elif action == 'BACK_MENU' and not event.shift:
                self.ui_management.remove_last_menu(is_submenu=True)
            elif action == 'SCALE':
                self.ui_management.hide_menu()
                self.ui_management.add_items(self.pie_menu_scale)
                self.ui_management.hide_menu()
                self.status = 'ADJUST#SCALE'
                self.slider_origin_x = events['mouse_x']
                self.previous_value = self.original_value = self.modifier['Input_6']
            elif action == 'OFFSET':
                self.ui_management.hide_menu()
                self.ui_management.add_items(self.pie_menu_offset)
                self.ui_management.hide_menu()
                self.status = 'ADJUST#OFFSET'
                self.slider_origin_x = events['mouse_x']
                self.previous_value = self.original_value = self.modifier['Input_5']
            elif action == 'MERGE':
                self.ui_management.hide_menu()
                self.ui_management.add_items(self.pie_menu_offset)
                self.ui_management.hide_menu()
                self.status = 'ADJUST#MERGE'
                self.slider_origin_x = events['mouse_x']
                self.previous_value = self.modifier['Input_4']
            elif action == 'GAP':
                self.ui_management.hide_menu()
                self.ui_management.add_items(self.pie_menu_offset)
                self.ui_management.hide_menu()
                self.status = 'ADJUST#GAP'
                self.slider_origin_x = events['mouse_x']
                self.previous_value  = self.original_value = self.modifier['Input_16']
            elif action == 'INSIDE':
                # supprime le vertex group du bool
                for vg in self.screw_bool.vertex_groups:
                    self.screw_bool.vertex_groups.remove(vg)
                v_group = self.screw_bool.vertex_groups.new(name='screws')

                # copie les données du vertex group du screw dans bool
                vg_source = self.screw_support.vertex_groups['screws']
                vg_target = self.screw_bool.vertex_groups['screws']
                for i, vt in enumerate(self.screw_bool.data.vertices):
                    try:
                        vg_target.add([vt.index], vg_source.weight(i), 'ADD')
                    except:pass


                self.modifier['Input_14'] = not self.modifier['Input_14']
                self.modifier.show_viewport = False
                self.modifier.show_viewport = True
                # vérifie si un booléen existe déjà avec le screw_bool
                boolean_modifier = None
                for m in self.obj.modifiers:
                    if m.type == 'BOOLEAN' and m.object == self.screw_bool:
                        boolean_modifier = m
                        break
                if not boolean_modifier:
                    active_object('SET', self.obj, True)
                    self.screw_bool.hide_set(False)
                    self.screw_bool.select_set(True)
                    bpy.ops.fluent.booleanoperator('INVOKE_DEFAULT')
                    active_object('SET', self.screw_support, True)
                else:
                    self.obj.modifiers.remove(boolean_modifier)
                    double_outer_bevel_cleaner([self.obj])
            elif action == 'CORNERS':
                self.modifier['Input_15'] = not self.modifier['Input_15']
                self.modifier.show_viewport = False
                self.modifier.show_viewport = True
            elif action == 'ONE_PER_FACE':
                self.modifier['Input_22'] = not self.modifier['Input_22']
                self.modifier.show_viewport = False
                self.modifier.show_viewport = True
            elif action == 'VALIDATE':
                if 'callback' in locals() and 'CLOSE_WIDGET' in callback:
                    self.ui_management.refresh_ui_items_list(close_widget=True)
                else:
                    self.ui_management.remove_last_menu()
                if 'ADJUST' in self.status:
                    self.status = 'SCREW_ADDED'
            elif action == 'REUSE':
                self.status = 'WAIT_REUSE'
                self.ui_management.refresh_side_infos([
                    [translate('pick'), translate('leftClick')],
                    [translate('cancel'), translate('escape')]
                ])
            elif action == 'DEBUG':
                node_tree = bpy.data.node_groups['Rivets']
                nodes = node_tree.nodes
                # nodes = node_tree.nodes
                for n in nodes:
                    if n.name == 'DEBUG':
                        node_inset = n
                    if n.name == 'LAST_NODE':
                        last_node = n
                    if n.type == 'GROUP_OUTPUT':
                        node_output = n
                link = node_tree.links.new
                if last_node.outputs[0].links:
                    link(node_inset.outputs[0], node_output.inputs[0])
                else:
                    link(last_node.outputs[0], node_output.inputs[0])
                bpy.ops.fluent.wireframedisplay('INVOKE_DEFAULT')

        if 'ADJUST' in self.status and not events['show_menu']:
            callback = self.adjustment()

        if 'callback' in locals() and 'STOP_ADJUSTMENT' in callback:
            self.ui_management.clean_side_infos()
            if 'callback' in locals() and 'CLOSE_WIDGET' in callback:
                self.ui_management.refresh_ui_items_list(close_widget=True)
            else:
                self.ui_management.remove_last_menu()
            self.status = 'SCREW_ADDED'
            return {'RUNNING_MODAL'}

        if self.status == 'WAIT_REUSE' and event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            obj = None
            obj = click_on(event.mouse_region_x, event.mouse_region_y)
            if obj and obj.get('fluent_type') == 'head_screw':
                self.modifier['Input_7'] = obj.modifiers[fluent_modifiers_name['head_screw']]['Input_7']
                self.modifier['Input_6'] = obj.modifiers[fluent_modifiers_name['head_screw']]['Input_6']
                self.modifier['Input_5'] = obj.modifiers[fluent_modifiers_name['head_screw']]['Input_5']
                self.status = 'SCREW_ADDED'
                self.ui_management.clean_side_infos()
                self.modifier.show_viewport = False
                self.modifier.show_viewport = True

                self.copy_mirror(obj, self.screw_support)


        # gestion affichage du pie menu
        self.ui_management.toggle_menu_displaying(refresh_pos)

        if self.status == 'WAIT_SELECTION' and event.type == 'ESC' and event.value == 'PRESS':
            bpy.data.objects.remove(self.copy, do_unlink=True)
            self.obj.hide_set(False)
            self.end()
            return {'FINISHED'}

        if self.status == 'WAIT_SELECTION' and event.type in ['RET', 'NUMPAD_ENTER'] and event.value == 'PRESS':
            print('--- press enter')
            # vérifie qu'au moins une face est sélectionnée
            face_selected = False
            bpy.ops.object.mode_set(mode='OBJECT')
            for p in self.copy.data.polygons:
                if p.select:
                    face_selected = True
                    break
            if face_selected == False:
                self.report({'ERROR'}, "At least, you have to select one face.")
                bpy.data.objects.remove(self.copy, do_unlink=True)
                self.obj.hide_set(False)
                self.end()
                return {'FINISHED'}
            print ('--- at least one side is selected')
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.duplicate()
            bpy.ops.mesh.separate(type='SELECTED')
            bpy.ops.object.mode_set(mode='OBJECT')
            self.screw_support = bpy.context.selected_objects[1]
            self.screw_support.name = '.f_screw'
            self.obj.hide_set(False)
            bpy.data.objects.remove(self.copy, do_unlink=True)
            print('--- import geo node')
            # import geometry node tree
            script_dir = join(dirname(realpath(__file__)))
            screws_dir = join(script_dir, 'screws')
            print('--- --- path :', screws_dir)
            blender_file = join(screws_dir, 'Rivets.blend')
            file_path_node_tree = join(blender_file, 'NodeTree')
            bpy.ops.wm.append(filename='Rivets', directory=file_path_node_tree, do_reuse_local_id=True)
            bpy.ops.wm.append(filename='Rivets.Holes', directory=file_path_node_tree, do_reuse_local_id=True)

            # création du vertex group qui gère où afficher les rivets
            print('--- create vertex group')
            for vg in self.screw_support.vertex_groups:
                self.screw_support.vertex_groups.remove(vg)
            v_group = self.screw_support.vertex_groups.new(name='screws' )
            for v in self.screw_support.data.vertices:
                v_group.add([v.index], 1, 'ADD')
            print('--- add modifier')
            # ajoute et paramètre le modifier
            self.modifier = self.screw_support.modifiers.new(name=fluent_modifiers_name['head_screw'], type='NODES')
            self.modifier.node_group = bpy.data.node_groups['Rivets']
            self.modifier['Input_6'] = bpy.context.scene.fluentProp.screw_scale
            self.modifier['Input_5'] = bpy.context.scene.fluentProp.screw_offset
            self.modifier.show_viewport = False
            print('--- data update')
            self.screw_support['fluent_type'] = 'head_screw'
            self.screw_support['fluent_screw_from'] = self.obj

            self.status = 'SCREW_ADDED'
            self.ui_management.hide_menu()
            self.ui_management.add_items(self.pie_menu_adjust)
            self.ui_management.hide_menu()
            print('--- duplicate')
            # duplique les têtes de visses et change le geometry node tree
            self.screw_bool = duplicate(self.screw_support, self.screw_support.name + '_bool')
            print('--- add in bool collection')
            del self.screw_bool['fluent_type']
            add_in_bool_collection(self.screw_bool)
            print('--- set viewport property')
            self.screw_bool.display_type = 'WIRE'
            self.screw_bool.hide_render = True
            print('--- add modifier for boolean')
            modif = self.screw_bool.modifiers[fluent_modifiers_name['head_screw']]
            modif.show_viewport = True
            print('--- set node group')
            modif.node_group = bpy.data.node_groups['Rivets.Holes']
            print('--- set input 12')
            modif['Input_12'] = self.screw_support
            print('--- hide')
            self.screw_bool.hide_set(True)
            print('--- refresh ui')
            self.ui_management.clean_side_infos()
            # print('--- active object', self.screw_support)
            # active_object('SET', self.screw_support, True)
            print('--- end of import function')

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        # autres variables
        self.status = 'WAIT_SELECTION'
        self.ui_management = FLUENT_ui_management(event)
        self.pie_menu_tool_list = tool_type_list_ui()
        self.pie_menu_head_list = head_type_list_ui()
        self.pie_menu_adjust = screw_adjust_ui()
        self.pie_menu_scale = scale_ui()
        self.pie_menu_offset = offset_ui()
        self.slider_origin_x = 0
        self.previous_value = 0
        self.original_value = 0
        self.modifier = None
        self.choice = [00, 00]
        self.screw_support = None
        self.screw_bool = None
        self.enter_value = 'None'
        self.mirror = None
        self.statut = None

        if self.operation == 'ADD':
            # vérifications
            if active_object('GET'):
                bpy.ops.object.mode_set(mode='OBJECT')
            self.obj = active_object()
            if not self.obj or not self.obj.type == 'MESH':
                make_oops([translate('selectAtLeastOneObject')], translate('howToUse'), 'ERROR')

            # création d'une copie de l'objet avec application des modifiers
            self.copy = duplicate(self.obj)
            apply_modifiers(self.copy)
            self.obj.hide_set(True)

            # bascule en edit mode
            active_object('SET', self.copy, True)
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
            bpy.ops.mesh.select_all(action='DESELECT')

            self.ui_management.refresh_side_infos([
                [translate('selectFaces'), ''],
                [translate('validate'), translate('enter')],
                [translate('cancel'), translate('escape')]
            ])
        elif self.operation == 'EDIT':
            self.screw_support = active_object('GET')
            self.modifier = self.screw_support.modifiers[fluent_modifiers_name['head_screw']]
            self.ui_management.hide_menu()
            self.ui_management.add_items(self.pie_menu_adjust)
            self.ui_management.hide_menu()
            # recherche du screw_bool
            for obj in bpy.data.objects:
                if obj.type == 'MESH':
                    for m in obj.modifiers:
                        if m.type == 'NODES' and m.node_group == bpy.data.node_groups['Rivets.Holes'] and m['Input_12'] == self.screw_support:
                            self.screw_bool = obj
                            break
            # objet d'origine
            self.obj = self.screw_support.get('fluent_screw_from')

            self.status = 'SCREW_ADDED'

        args = (self, context)
        self._handle = bpy.types.SpaceView3D.draw_handler_add(draw_callback_px, args, 'WINDOW', 'POST_PIXEL')
        context.window_manager.modal_handler_add(self)

        return {'RUNNING_MODAL'}


classes = FLUENT_OT_Screw