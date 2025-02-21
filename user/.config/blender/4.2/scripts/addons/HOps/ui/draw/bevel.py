import bpy

from ... utility import addon


def draw(column, context):

    preference = addon.preference().property
    color = addon.preference().color
    ui = addon.preference().ui

    row = column.row(align=True)
    row.label(text='Bevel:')

    box = column.box()
    row = box.row(align=True)
    split = row.split(align=True, factor=0.70)
    row.prop(preference, 'workflow_mode', expand=True)
    row.prop(preference, 'use_harden_normals', text='Harden Normals')
    row = box.row(align=True)
    row.prop(preference, 'bevel_profile', text='Profile')
    row.prop(preference, 'default_segments', text='Segments')
    row.prop(preference, 'adaptivemode', text='Adaptive')
    row = box.row(align=True)
    #row.label(text='Miter:')
    row.prop(preference, 'bevel_miter_outer', text= '')
    row.prop(preference, 'bevel_miter_inner', text= '')
    row.prop(preference, 'bevel_loop_slide', text='Loop Slide')
    column.separator()
    # column.separator()
    # row = column.row(align=True)
    # row.prop(preference, 'Hops_twist_radial_sort', text='Radial / Twist (Render Toggle)')
    # row = column.row(align=True)
    # row.prop(preference, 'to_cam_jump', text='To_Cam Jump')
    # row.prop(preference, 'to_render_jump', text='Viewport+ Set Render')
    column.separator()

    # row = column.row(align=True)
    # row.label(text='Circle:')
    # row = column.row(align=True)
    # row.prop(preference, 'circle_divisions', expand=True, text='Circle (E) Divisions')

    row = column.row(align=True)
    row.label(text='CSharp:  ')
    row = column.row(align=True)

    column.separator()

    box = column.box()
    row = box.row(align=True)
    row.prop(preference, 'auto_bweight', text='Jump to Bevel')
    row.prop(preference, 'Hops_sharp_remove_cutters', text='Remove Cutters')

    #row = column.row(align=True)
    # row.label(text='Mirror:')

    # row = column.row(align=True)
    # row.prop(preference, 'Hops_mirror_modal_scale', text='Mirror Scale')
    # row.prop(preference, 'Hops_mirror_modal_sides_scale', text='Mirror Size')

    # row = column.row(align=True)
    # row.prop(preference, 'Hops_mirror_modal_Interface_scale', text='Mirror Interface Scale')
    # row.prop(preference, 'Hops_mirror_modal_revert', text='Revert')

    # row = column.row(align=True)
    # row.prop(preference, 'Hops_gizmo_mirror_u', text='mirror u')
    # row.prop(preference, 'Hops_gizmo_mirror_v', text='mirror v')

    # column.separator()
    #
    # row = column.row(align=True)
    # row.label(text='Array:')
    # row = column.row(align=True)
    # row.prop(preference, 'force_array_reset_on_init', expand=True, text='Array Reset on Init')
    #
    # row = column.row(align=True)
    # row.prop(preference, 'force_array_apply_scale_on_init', expand=True, text='Array Scale Apply on Init')
    #
    # column.separator()
    # column.separator()
    #
    # row = column.row(align=True)
    # row.label(text='Thick:')
    # row = column.row(align=True)
    # row.prop(preference, 'force_thick_reset_solidify_init', expand=True, text='Solidify Reset on Init')
    #
    # column.separator()
    #
    # row = column.row(align=True)
    # row.label(text='Modals:')
    # row = column.row(align=True)
    #
    # column.separator()
