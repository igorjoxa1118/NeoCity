import bpy

from bpy.types import Panel, Operator

from .... utility import addon, tool
from ... sound import time_code
from ... property.utility import names


class BC_PT_display_settings(Panel):
    bl_label = 'Display'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'BoxCutter'
    bl_parent_id = 'BC_PT_settings'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        active = tool.active()
        return active and active.idname == tool.name and context.region.type == 'UI'


    def draw(self, context):
        preference = addon.preference()
        layout = self.layout

        # self.label_row(layout.row(), preference.snap, 'fade_distance', label='Fade Distance')
        self.label_row(layout.row(), preference.display, 'dots', 'Display Dots')

        self.label_row(layout.row(), preference.display, 'simple_pie', label='Simple Pie')
        self.label_row(layout.row(), preference.display, 'simple_topbar')
        self.label_row(layout.row(), preference.display, 'simple_helper', label='Simple Helper')
        self.label_row(layout.row(), preference.display, 'grid_mode')

        self.label_row(layout.row(), preference.display, 'wire_only')

        self.label_row(layout.row(), preference.display, 'show_shape_wire')
        if preference.display.wire_only:
            self.label_row(layout.row(), preference.display, 'thick_wire')
            self.label_row(layout.row(), preference.display, 'wire_size_factor', 'Wire Multiplier')

        layout.row().label(text='Fade')
        self.label_row(layout.row(), preference.display, 'shape_fade_time_in', '  In')

        if preference.display.shape_fade_time_out not in time_code:
            self.label_row(layout.row(), preference.display, 'shape_fade_time_out', '  Out')

        else:
            row = layout.row(align=True)
            row.label(text='Out')
            row.operator('bc.display_fade_prev', icon='REW', text='')
            row.prop(preference.display, 'shape_fade_time_out', text='')
            row.operator('bc.display_fade_next', icon='FF', text='')

        self.label_row(layout.row(), preference.display, 'shape_fade_time_out_extract', '  Extract Out')

        if preference.display.shape_fade_time_out in time_code.keys():
            self.label_row(layout.row(), preference.display, 'sound_volume', 'Volume')
            self.label_row(layout.row(), bpy.context.preferences.system, 'audio_device', 'Audio Device')

    def label_row(self, row, path, prop, label=''):
        row.label(text=label if label else names[prop])
        row.prop(path, prop, text='')


class BC_OT_display_fade_next(Operator):
    bl_idname = 'bc.display_fade_next'
    bl_label = 'Next'
    bl_category = 'BoxCutter'
    bl_description = 'Next sound'
    bl_options = {'INTERNAL'}


    def execute(self, context):
        func = lambda a, b: a + b
        fade_scroll(func)

        return{'FINISHED'}


class BC_OT_display_fade_prev(Operator):
    bl_idname = 'bc.display_fade_prev'
    bl_label = 'Prev'
    bl_category = 'BoxCutter'
    bl_description = 'Previous sound'
    bl_options = {'INTERNAL'}


    def execute(self, context):
        func = lambda a, b: a - b
        fade_scroll(func)

        return{'FINISHED'}


def fade_scroll(func):
    preference = addon.preference()
    _list = sorted(time_code.keys())
    index = func(_list.index(preference.display.shape_fade_time_out), 1) % len(_list)
    preference.display.shape_fade_time_out = _list[index]
