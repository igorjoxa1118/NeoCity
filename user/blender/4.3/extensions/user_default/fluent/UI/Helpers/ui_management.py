import bpy
from bpy_extras import view3d_utils

import time

from .shapes import FLUENT_Cursor_Infos, FLUENT_Panel_Infos, FLUENT_Draw_Dots
from .ui_button import FLUENT_Ui_Layout, FLUENT_Ui_Button
from ...Tools.helper import get_addon_preferences


class FLUENT_ui_management():

    def __init__(self, event):
        self.pie_menu_history = []
        self.ui_items_list = []
        self.events = self.event_dico_builder()
        self.cursor_infos = FLUENT_Cursor_Infos()
        self.ui_items_list.append(self.cursor_infos)
        self.side_infos = FLUENT_Panel_Infos()
        self.ui_items_list.append(self.side_infos)
        self.dots = FLUENT_Draw_Dots()
        # self.dots_vertex_list = None
        # self.dots_obj = None

        self.button_is_hover = False
        self.action = None
        self.delay = None
        self.button_action_hover = None
        self.pause_toggle = False

    def event_dico_builder(self):
        dico = {'mouse_left_click': False, 'mouse_x': 0, 'mouse_y': 0, 'value': None,
                'type': None, 'shift_press': False, 'shift_work': False, 'shift_release': False, 'ctrl_press': False,
                'ctrl_work': False, 'ctrl_release': False, 'alt_press': False, 'alt_work': False, 'alt_release': False,
                'show_menu': False}
        return dico

    def event_dico_refresh(self, event):
        self.events['mouse_x'] = event.mouse_region_x
        self.events['mouse_y'] = event.mouse_region_y

        self.events['value'] = event.value
        self.events['type'] = event.type

        if event.shift and not self.events['shift_press'] and not self.events['shift_work']:
            self.events['shift_press'] = True
        elif event.shift and self.events['shift_press']:
            self.events['shift_press'] = False
            self.events['shift_work'] = True
        elif not event.shift and self.events['shift_work']:
            self.events['shift_release'] = True
            self.events['shift_work'] = False
        elif not event.shift and self.events['shift_release']:
            self.events['shift_release'] = False
        else:
            self.events['shift_press'] = False

        # gestion des événements du ctrl
        if event.ctrl and not self.events['ctrl_press'] and not self.events['ctrl_work']:
            self.events['ctrl_press'] = True
        elif event.ctrl and self.events['ctrl_press']:
            self.events['ctrl_press'] = False
            self.events['ctrl_work'] = True
        elif not event.ctrl and self.events['ctrl_work']:
            self.events['ctrl_release'] = True
            self.events['ctrl_work'] = False
        elif not event.ctrl and self.events['ctrl_release']:
            self.events['ctrl_release'] = False
        else:
            self.events['ctrl_press'] = False

        # gestion des événements du alt
        if event.alt and not self.events['alt_press'] and not self.events['alt_work']:
            self.events['alt_press'] = True
        elif event.alt and self.events['alt_press']:
            self.events['alt_press'] = False
            self.events['alt_work'] = True
        elif not event.alt and self.events['alt_work']:
            self.events['alt_release'] = True
            self.events['alt_work'] = False
        elif not event.alt and self.events['alt_release']:
            self.events['alt_release'] = False
        else:
            self.events['alt_press'] = False

        if event.value == 'PRESS' and event.type == 'LEFTMOUSE':
            self.events['mouse_left_click'] = True

        if event.value == 'RELEASE' and event.type == 'LEFTMOUSE':
            self.events['mouse_left_click'] = False

        return self.events

    def event_dico_set(self, dico):
        self.events = dico

    def event_dico_get(self):
        return self.events

    def add_items(self, item, is_submenu = False):
        if type(item) is FLUENT_Ui_Layout and item.get_layout() in ['PIE', 'COLUMN']:
            if is_submenu and get_addon_preferences().fluent_menu_hold:
                if self.delay is None:
                    self.delay = time.time()
                else:
                    if time.time() - self.delay > 1:
                        self.delay = None
                        try:
                            self.hide_menu()
                            self.pie_menu_history.extend(item)
                            self.show_menu()
                        except:
                            self.hide_menu()
                            self.pie_menu_history.append(item)
                            self.show_menu()
            else:
                try:
                    self.pie_menu_history.extend(item)
                except:
                    self.pie_menu_history.append(item)
        else:
            try:
                self.ui_items_list.extend(item)
            except:
                self.ui_items_list.append(item)

    def add_dots_items(self):
        self.add_items(self.dots)

    def remove_items(self, names):
        items_to_remove = []
        for index, menu in enumerate(self.ui_items_list):
            if not isinstance(menu, FLUENT_Ui_Layout) or menu.get_id() not in names:
                continue

            items_to_remove.append(index)

        for item in items_to_remove:
            del self.ui_items_list[item]

    def get_items(self):
        return self.ui_items_list, self.pie_menu_history

    def get_dots(self):
        return self.dots

    def get_current_item(self):
        if len(self.ui_items_list) == 0:
            return None

        return self.ui_items_list[-1]

    def get_button_action(self):
        action = None
        pressed_button = None
        action_hover = None
        self.button_is_hover = False
        self.action = None
        for b in self.ui_items_list:
            if type(b) is FLUENT_Ui_Layout and b.get_layout() in ['PIE', 'COLUMN']:
                layout_items_list = b.get_items()
                for i in layout_items_list:
                    i.is_hover(self.events)
                    if i.get_state() in [1, 2]:
                        self.button_is_hover = True
                        action_hover = i.get_action()
                    if i.get_state() == 2:
                        action = i.get_action()
                        i.set_state(0)
                        pressed_button = i
                        break
                    else:
                        action = None
                if action:
                    break
        if not action :
            for b in self.ui_items_list:
                if type(b) is FLUENT_Ui_Button:
                    b.is_hover(self.events)
                    if b.get_state() in [1, 2]:
                        self.button_is_hover = True
                        action_hover = b.get_action()
                    if b.get_state() == 2:
                        action = b.get_action()
                        b.set_state(0)
                        pressed_button = b
                        break
                    else:
                        action = None
                elif type(b) is FLUENT_Ui_Layout:
                    layout_items_list = b.get_items()
                    for i in layout_items_list:
                        i.is_hover(self.events)
                        if i.get_state() in [1, 2]:
                            self.button_is_hover = True
                            action_hover = i.get_action()
                        if i.get_state() == 2:
                            action = i.get_action()
                            i.set_state(0)
                            pressed_button = i
                            break
                        else:
                            action = None
                    if action:
                        break
        self.action = action
        if self.button_action_hover != action_hover:
            self.delay = None
            self.button_action_hover = action_hover

        if not self.action and self.button_is_hover:
            action = '###'

        return action, pressed_button

    def toggle_menu_displaying(self, refresh_pos=True):
        if self.pause_toggle:
            return

        if get_addon_preferences().fluent_menu_hold:
            if not self.events['show_menu'] and self.events['mouse_left_click'] and not self.button_is_hover:
                if refresh_pos:
                    self.position_menu_under_mouse()
                self.show_menu()
            elif self.events['show_menu'] and not self.events['mouse_left_click']:
                self.hide_menu()
        else:
            if self.events['value'] == 'PRESS' and self.events['type'] == 'LEFTMOUSE':
                if self.events['show_menu'] and not (self.action and '_MENU' in self.action):
                    self.hide_menu()
                else:
                    if not self.button_is_hover:
                        if refresh_pos:
                            self.position_menu_under_mouse()
                        self.show_menu()
                    else:
                        if self.action and '_MENU' in self.action:
                            self.show_menu()
        return

    def show_menu(self):
        self.events['show_menu'] = True
        self.delay = None
        if len(self.pie_menu_history):
            for b in self.pie_menu_history[-1].get_items():
                try:
                    b.set_show(True)
                except:
                    print('--- ERROR Impossible to show button')

    def hide_menu(self):
        self.events['show_menu'] = False
        self.delay = None
        if len(self.pie_menu_history) and not self.events['show_menu']:
            for b in self.pie_menu_history[-1].get_items():
                try:
                    b.set_show(False)
                except:
                    print('--- ERROR Impossible to hide button')

    def position_menu_under_mouse(self):
        if len(self.pie_menu_history) < 1:
            return
        if self.pie_menu_history[-1].get_layout() not in ['MIRROR', 'TAPER']:
            self.pie_menu_history[-1].spread(self.events['mouse_x'], self.events['mouse_y'])

    def position_menu_under_previous(self, menu):
        if len(self.pie_menu_history) < 1:
            return

        if self.pie_menu_history[-1].get_layout() not in ['MIRROR', 'TAPER']:
            current_menu = self.pie_menu_history[-1]
            menu.spread(current_menu.get_pie_center()[0], current_menu.get_pie_center()[1])

    def get_current_menu(self):
        if len(self.pie_menu_history) == 0:
            return None

        return self.pie_menu_history[-1]

    def remove_last_menu(self, is_submenu = False):
        ok = False
        if is_submenu and get_addon_preferences().fluent_menu_hold:
            if self.delay is None:
                self.delay = time.time()
            else:
                if time.time() - self.delay > 1:
                    self.delay = None
                    ok = True
        else:
            ok = True
        if ok:
            # supprime le dernier menu et positionne le "nouveau dernier" menu à la même position
            previous_position = self.pie_menu_history[-1].get_pie_center()
            del self.pie_menu_history[-1]
            self.pie_menu_history[-1].spread(previous_position[0], previous_position[1])
            self.show_menu()

    def refresh_side_infos(self, text):
        self.side_infos.reset()
        for i, j in enumerate(text):
            self.side_infos.add_line(text[i][0], text[i][1])

    def clean_side_infos(self):
        self.side_infos.reset()

    def refresh_ui_items_list(self, close_widget=False):
        layouts = ['PIE', 'COLUMN']
        if close_widget:
            layouts.append('MIRROR')
            layouts.append('TAPER')
        self.ui_items_list = [i for i in self.ui_items_list if not (type(i) is FLUENT_Ui_Layout and i.get_layout() in layouts)]

        if len(self.pie_menu_history) < 1:
            return

        self.ui_items_list.append(self.pie_menu_history[-1])

    def global_ui_drawing(self):
        for item in self.ui_items_list:
            item.draw(self.events)

    def clear_dots(self):
        self.dots.clear_dots()

    def add_a_dot(self, dot):
        self.dots.add_2d_dot(dot)

    def set_button_active(self, action):
        for b in self.get_items()[0]:
            if type(b) == FLUENT_Ui_Button:
                if b.get_action() != action:
                    b.set_active(False)
                else:
                    b.set_active(True)
            elif type(b) == FLUENT_Ui_Layout:
                layout_items_list = b.get_items()
                for bb in layout_items_list:
                    if bb.get_action() != action:
                        bb.set_active(False)
                    else:
                        bb.set_active(True)