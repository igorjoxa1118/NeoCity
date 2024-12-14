from ... utility import addon
from ... utility import modifier

def draw(column, context):

    preference = addon.preference().property

    row = column.row(align=True)
    row.label(text = "Behavior / Boolean Solver ")

    box = column.box()
    row = box.row(align=True)
    row.prop(preference, 'workflow', expand=True)

    row = box.row(align=True)
    row.prop(preference, 'boolean_solver', expand=True)

    box = column.box()

    row = box.row(align=True)
    row.prop(preference, 'sort_modifiers', text='Sort Modifier', expand=True)

    if preference.sort_modifiers:
        row = row.row(align=True)
        row.scale_x = 1.5
        row.alignment = 'RIGHT'
        split = row.split(align=True, factor=0.85)

        row = split.row(align=True)
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
            row.prop(preference, F'sort_{type.lower()}', text='', icon=icon)

        row = split.row(align=True)
        row.scale_x = 1.5
        row.popover('HOPS_PT_sort_last', text='', icon='SORT_ASC')

    column.separator()
