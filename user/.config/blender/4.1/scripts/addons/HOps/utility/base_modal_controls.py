import bpy
from mathutils import Vector
from .. utility import addon
from .. utils.blender_ui import get_dpi_factor


keyboard_increment  = {'NUMPAD_PLUS', 'EQUAL', 'UP_ARROW'}
keyboard_decrement  = {'NUMPAD_MINUS', 'DOWN_ARROW', 'MINUS'}
confirm_events      = {'SPACE', 'LEFTMOUSE', 'RET', 'NUMPAD_ENTER'}
cancel_events       = {'ESC', 'RIGHTMOUSE'}
pass_through_events = {'MIDDLEMOUSE'}
increment_maps      = {'WHEELUPMOUSE', 'NUMPAD_PLUS', 'EQUAL', 'UP_ARROW'}
decrement_maps      = {'WHEELDOWNMOUSE', 'NUMPAD_MINUS', 'DOWN_ARROW', 'MINUS'}
numpad_types        = {'NUMPAD_0', 'NUMPAD_1', 'NUMPAD_2', 'NUMPAD_3', 'NUMPAD_4',
                        'NUMPAD_5', 'NUMPAD_6', 'NUMPAD_7', 'NUMPAD_8', 'NUMPAD_9',
                        'NUMPAD_MINUS', 'NUMPAD_PLUS'}


class Base_Modal_Controls():

    def __init__(self, context, event, popover_keys=[]):

        # States
        self.scroll       = None
        self.confirm      = None
        self.cancel       = None
        self.mouse        = None
        self.tilde        = None
        self.popover      = None
        self.pass_through = False

        # Props
        self.divisor       = 1000
        self.divisor_shift = 10
        self.mouse_region  = Vector((0,0))
        self.mouse_window  = Vector((0,0))
        self.is_industry_standard = bpy.context.preferences.keymap.active_keyconfig == 'Industry_Compatible'

        # Maps
        self.keyboard_increment  = list(keyboard_increment)
        self.keyboard_decrement  = list(keyboard_decrement)
        self.confirm_events      = list(confirm_events)
        self.cancel_events       = list(cancel_events)
        self.pass_through_events = list(pass_through_events)
        self.increment_maps      = list(increment_maps)
        self.decrement_maps      = list(decrement_maps)
        self.popover_keys        = list(popover_keys)
        self.numpad_types        = list(numpad_types)

        # Initialize
        self.__alter_keymaps()
        self.update(context, event)

    # --- STATIC --- #

    @staticmethod
    def tilde(context, event):
        tilde = context.window_manager.keyconfigs.user.keymaps['3D View'].keymap_items['hops.tilde_remap']
        return Base_Modal_Controls.keymap_item_reader(tilde, event)

    @staticmethod
    def keymap_item_reader(kmi, event):

        if event.type == kmi.type and event.value == kmi.value:
            result = [True]

            if kmi.any:
                result = [event.ctrl, event.shift, event.alt, event.oskey]
                return any(result)

            if kmi.ctrl or kmi.oskey:
                result.append(event.ctrl)
            if kmi.shift:
                result.append(event.shift)
            if kmi.alt:
                result.append(event.alt)
            if kmi.oskey:
                result.append(event.oskey)
            if kmi.key_modifier != "NONE":
                result.append(event.type == kmi.key_modifier)

            return all (result)

        return False

    # --- PUBLIC --- #

    def update(self, context, event):
        self.mouse        = self.__mouse(event, divisor=self.divisor, divisor_shift= self.divisor_shift)
        self.confirm      = self.__confirm(event)
        self.cancel       = self.__cancel(event)
        self.pass_through = self.__pass_through(event)
        self.scroll       = self.__scroll(event)
        self.popover      = self.__popover(event)
        self.tilde        = Base_Modal_Controls.tilde(context, event)

        self.mouse_region.x = event.mouse_region_x
        self.mouse_region.y = event.mouse_region_y
        self.mouse_window.x = event.mouse_x
        self.mouse_window.y = event.mouse_y

        # Toggle viewport display
        if event.type == "O" and event.value == "PRESS":
            if hasattr(context, 'space_data') and hasattr(context.space_data, 'shading'):
                types = ['WIREFRAME', 'SOLID', 'MATERIAL', 'RENDERED']
                index = types.index(context.space_data.shading.type)
                context.space_data.shading.type = types[(index + 1) % len(types)]

        # Toggle help
        if event.type == "H" and event.value == "PRESS":
            addon.preference().property.hops_modal_help = not addon.preference().property.hops_modal_help

        # Toggle overlays
        if self.tilde and event.shift == True:
            bpy.context.space_data.overlay.show_overlays = not bpy.context.space_data.overlay.show_overlays

    # --- PRIVATE --- #

    def __alter_keymaps(self):

        # Popover
        if addon.preference().keymap.spacebar_accept:
            if 'SPACE' in self.popover_keys:
                self.popover_keys.remove('SPACE')

        if not addon.preference().keymap.rmb_cancel:
            self.cancel_events.remove('RIGHTMOUSE')
            self.pass_through_events.append('RIGHTMOUSE')


    def __mouse(self, event, divisor=1000, divisor_shift=10):
        if event.type not in {'MOUSEMOVE', 'TRACKPADPAN'}:
            return 0

        modal_scale = addon.preference().ui.Hops_modal_scale
        delta = event.mouse_x - event.mouse_prev_x

        if bpy.app.version > (2, 91, 0):
            divisor = divisor / (4.5 / get_dpi_factor())

        delta = modal_scale * delta / divisor / get_dpi_factor()

        if event.shift:
            delta = modal_scale * delta / divisor_shift / get_dpi_factor()

        if addon.preference().property.modal_handedness == 'LEFT':
            return -delta

        return delta


    def __confirm(self, event):
        keys = [k for k in self.confirm_events if k not in self.popover_keys]
        return event.type in keys and event.value == 'PRESS'


    def __cancel(self, event):
        return event.type in self.cancel_events and event.value == 'PRESS'


    def __pass_through(self, event):
        if bpy.context.preferences.inputs.use_mouse_emulate_3_button and event.alt and event.type == 'LEFTMOUSE':
            return True
        if bpy.context.preferences.keymap.active_keyconfig == 'Industry_Compatible' and event.alt and event.type == 'LEFTMOUSE':
            return True
        return event.type in self.pass_through_events or 'NDOF' in event.type


    def __scroll(self, event):

        if event.type == 'TRACKPADPAN':
            delta = event.mouse_y - event.mouse_prev_y
            if abs(delta) < 5: return 0
            if delta > 0: return 1
            elif delta < 0: return -1
            else: return 0

        if event.value != 'PRESS':
            return 0
        if event.type in increment_maps:
            return 1
        if event.type in decrement_maps:
            return -1

        return 0


    def __popover(self, event):
        if event.type in self.popover_keys and event.value == 'PRESS':
            return True
        return False

