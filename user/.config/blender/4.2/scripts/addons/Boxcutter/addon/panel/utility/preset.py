from .... utility import addon


vertice = [3, 6, 8, 32, 64]
array = [2, 4, 6, 8, 10]
width = [0.02, 0.05, 0.1]
segment = [1, 2, 3, 4, 6]
angle = [5, 15, 30, 45, 90]
line_angle = [1, 5, 10, 15]
taper = [0.1, 0.5, 1.0]
factor = [0.0, 0.5, 1.0]


def shift_operation_draw(layout, context):
    preference = addon.preference()
    enabled = preference.keymap.shift_operation_enable

    layout.label(text='Shift Operation')

    if enabled:
        layout.prop(preference.keymap, 'shift_operation', text='')
        layout.popover('BC_PT_shift_operation', text='', icon='SETTINGS')

    if enabled:
        layout.prop(preference.keymap, 'shift_operation_enable', text='', icon='X', toggle=True)

    else:
        layout.prop(preference.keymap, 'shift_operation_enable', text='')
