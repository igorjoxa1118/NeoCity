import bpy
from bpy.types import Panel
from bpy.props import BoolProperty, FloatVectorProperty, FloatProperty, EnumProperty, IntProperty, StringProperty
from ... utility import addon


def draw(column, context):

    preference = addon.preference().property
    display = addon.preference().display
    keymap = addon.preference().keymap
    color = addon.preference().color
    ui = addon.preference().ui
    wm = bpy.context.window_manager

    row = column.row(align=True)

    column.separator()
    row = column.row(align=True)
    row.prop(ui, 'Hops_auto_hide_t_panel',  text='Auto T Panel')
    row.prop(ui, 'Hops_auto_hide_n_panel',  text='Auto N Panel')
    #column.separator()
    row = column.row(align=True)
    row.label(text='Modal Handedness')
    row.prop(preference, 'modal_handedness', text='')
    row = column.row(align=True)
    row.prop(color, 'Hops_UI_cell_background_color', text='Modal BG Color')
    row = column.row(align=True)
    row.label(text='Modal Help Scale:')
    row.prop(ui, 'Hops_modal_fast_ui_help_size', text='')
    row = column.row(align=True)
    row.prop(ui, 'Hops_warp_on', text='Modal Warp')
    if addon.preference().ui.Hops_warp_on:
        row.prop(ui, 'Hops_warp_mode_padding', text='')
    row = column.row(align=True)
    row.prop(ui, 'Hops_operator_display', text='Operator Text')
    if addon.preference().ui.Hops_operator_display:
        row.prop(ui, 'Hops_operator_display_time', text='')
    row = column.row(align=True)
    row.prop(ui, 'Hops_extra_draw', text='Wire Fade')
    row.prop(ui, 'Hops_extra_draw_time', text='')
    row = column.row(align=True)
    row.label(text='Bevel Profile:')
    #row = column.row(align=True)
    row.prop(preference, 'bevel_profile', text='')
    row = column.row(align=True)
    row.label(text='Array Type')
    row.prop(preference, 'array_v2_use_2d', text='')
    #column.separator()
    row = column.row(align=True)
    row.label(text='Scroll Type')
    #row.prop(preference, 'bool_scroll_type', text='')
    row.prop(preference, 'bool_scroll', text='')
    #if preference.bool_scroll_type == 'CLASSIC':
    # row = column.row(align=True)
    # row.label(text='Scroll Method')
    # row.prop(preference, 'bool_scroll', text='')
    row = column.row(align=True)
    row.label(text='To_Cam :')
    row.prop(preference, 'to_cam', text='')
    row = column.row(align=True)
    # row.label(text='Dice :')
    # row.prop(preference, 'dice_version', text='')
    # row = column.row(align=True)
    row.label(text='To_Shape :')
    row.prop(preference, 'to_shape_type', text='')

    if bpy.app.version >= (3, 3, 0):
        row = column.row(align=True)
        row.label(text='Radial Array')
        row.prop(preference, 'radial_array_type', text='')
    if ui.Hops_operator_display and hasattr(wm, 'bc'):
        row = column.row(align=True)
        row.prop(display, 'bc_notifications', text='Boxcutter Notifications')

        if display.bc_notifications:
            row.prop(preference, 'bc_dimensions_converter', text='')
            row.prop(display, 'bc_extra_notifications', text='')

    row = column.row(align=True)
    row.prop(ui, 'expanded_menu', text='Q Menu / Sequential')
    row = column.row(align=True)
    row.prop(preference, 'add_prefix', text='Q Menu / Prefixes')
    if bpy.app.version >= (4, 1):
        row = column.row(align=True)
        row.prop(addon.preference().behavior, 'auto_smooth', text='Auto Smooth (4.1+)')
    row = column.row(align=True)
    row.prop(addon.preference().behavior, 'mat_viewport', text='Blank Mat similar to Viewport ')
    row = column.row(align=True)
    row.prop(preference, 'Hops_twist_radial_sort', text='Radial/Twist (Render/Edit Toggle)')
    row = column.row(align=True)
    row.prop(preference, 'to_render_jump', text='Viewport+ Set Render')
    row = column.row(align=True)
    row.prop(preference, 'to_light_constraint', text='Blank Light Constraint')
    row = column.row(align=True)
    row.label(text='Spacebar Accept')
    row.prop(keymap, "spacebar_accept", text="")
    # row = column.row(align=True)
    # row.label(text='RMB Cancel')
    # row.prop(keymap, "rmb_cancel", text="")
    row = column.row(align=True)
    row.label(text='Bev/Bool Hotkey Helper Toggle :')
    row.prop(preference, 'bev_bool_helper', text='')
    row = column.row(align=True)
    row.label(text='Add Primitive (NewObject)')
    row.prop(preference, 'add_primitive_newobject', text='')
    # row.prop(preference, 'sort_modifiers', text='Sort Modifier System', expand=True)
    # row = column.row(align=True)
    #row.prop(preference, 'st3_meshtools', text='ST3 Meshtools Unlock')
