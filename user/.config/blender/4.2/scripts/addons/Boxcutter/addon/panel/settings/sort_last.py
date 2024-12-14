import bpy

from bpy.types import Panel

from .... utility import addon, tool, modifier


class BC_PT_sort_last(Panel):
    bl_label = 'Sort Last'
    bl_space_type = 'TOPBAR'
    bl_region_type = 'WINDOW'
    bl_options = {'DEFAULT_CLOSED'}


    def draw(self, context):
        preference = addon.preference()
        layout = self.layout

        row = layout.row(align=True)

        for type in modifier.sort_types:
            icon = F'MOD_{type}'
            if icon == 'MOD_WEIGHTED_NORMAL':
                icon = 'MOD_NORMALEDIT'
            elif icon == 'MOD_SIMPLE_DEFORM':
                icon = 'MOD_SIMPLEDEFORM'
            elif icon == 'MOD_DECIMATE':
                icon = 'MOD_DECIM'
            elif icon == 'MOD_WELD':
                icon = 'AUTOMERGE_OFF'
            elif icon == 'MOD_UV_PROJECT':
                icon = 'MOD_UVPROJECT'
            elif icon == 'MOD_NODES':
                icon = 'GEOMETRY_NODES'
            sub = row.row(align=True)
            sub.enabled = getattr(preference.behavior, F'sort_{type.lower()}')
            sub.prop(preference.behavior, F'sort_{type.lower()}_last', text='', icon=icon)

        if preference.behavior.sort_bevel:
            label_row(preference.behavior, 'sort_bevel_ignore_weight', layout.row(), label='Ignore Bevels using Weights')
            label_row(preference.behavior, 'sort_bevel_ignore_vgroup', layout.row(), label='Ignore Bevels with VGroups')
            label_row(preference.behavior, 'sort_bevel_ignore_only_verts', layout.row(), label='Ignore Bevels using Only Verts')

        layout.separator()

        label_row(preference.behavior, 'sort_depth', layout.row(), label='Sort Depth')
        layout.separator()
        layout.label(text='Name Prefixes:')

        for option in sorted(dir(preference.behavior)):
            if not option.endswith('_char'):
                continue

            is_space = getattr(preference.behavior, option) == ' '
            name = option              \
                .replace('sort_', '')  \
                .replace('_char', '')  \
                .replace('_', ' ')     \
                .title()               \

            if name == 'Char':
                name = 'Sort'

            elif name == 'Last':
                name = 'Sort Type Last'

            elif name == 'Lock End':
                name = 'Force Last'

            elif name == 'Lock Above':
                name = 'Anchor to Above'

            elif name == 'Lock Below':
                name = 'Anchor to Below'

            elif name == 'Stop':
                name = 'Stop Sorting'

            label_row(preference.behavior, option, layout.row(), label=F'  {name}{" (space)" if is_space else ""}', scale_x_prop=0.35)


def label_row(path, prop, row, label='', scale_x_prop=1.0):
    row.label(text=label)
    sub = row.row()
    sub.scale_x = scale_x_prop
    sub.prop(path, prop, text='')

