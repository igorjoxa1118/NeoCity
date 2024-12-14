import math
from .... ui_framework import form_ui as form

available_mods = {
    # Modify
    'WEIGHTED_NORMAL',
    # Generate
    'ARRAY',
    'BEVEL',
    'BOOLEAN',
    'DECIMATE',
    'EDGE_SPLIT',
    'MIRROR',
    'SCREW',
    'SOLIDIFY',
    'SUBSURF',
    'WELD',
    'WIREFRAME',
    # Deform
    'CAST',
    'DISPLACE',
    'LATTICE',
    'SIMPLE_DEFORM',
    }

def popup_generator(op, mod, index, bool_tracker_mode=False):
    if mod.type not in available_mods: return "", None
    msg = "Ctrl Click : Popup menu"
    popup = form.Popup()

    header(op, popup, mod, index, bool_tracker_mode)
    spacer(popup)

    # --- Modify --- #

    if mod.type == 'WEIGHTED_NORMAL':
        row = popup.row()
        row.add_element(form.Label(text="Mode"))
        opts = ['FACE_AREA', 'CORNER_ANGLE', 'FACE_AREA_WITH_ANGLE']
        row.add_element(form.Dropdown(
            options=opts, callback=set_wn_mode, additional_args=(mod,),
            update_hook=get_wn_mode, hook_args=(mod,), index=opts.index(mod.mode)))
        popup.row_insert(row)

        spacer(popup)

        row = popup.row()
        row.add_element(form.Label(text="Weight", width=75))
        row.add_element(form.Input(obj=mod, attr='weight', increment=1, width=50, decimal_draw_precision=0, use_mod_keys=False))
        popup.row_insert(row)

        row = popup.row()
        row.add_element(form.Label(text="Threshold", width=75))
        row.add_element(form.Input(obj=mod, attr='thresh', increment=.1, width=50, decimal_draw_precision=2))
        popup.row_insert(row)

        spacer(popup)

        row = popup.row()
        row.add_element(form.Button(text="Keep Sharp", obj=mod, attr="keep_sharp"))
        row.add_element(form.Spacer(width=5))
        row.add_element(form.Button(text="Face Influence", obj=mod, attr="use_face_influence"))
        popup.row_insert(row)

        spacer(popup)
        return msg, popup

    # --- Generate --- #

    if mod.type == 'ARRAY':
        row = popup.row()
        row.add_element(form.Button(text="Object", obj=mod, attr="use_object_offset"))
        row.add_element(form.Spacer(width=5))
        row.add_element(form.Button(text="Merge", obj=mod, attr="use_merge_vertices"))
        popup.row_insert(row)

        spacer(popup)

        row = popup.row()
        row.add_element(form.Label(text="Count", width=50))
        row.add_element(form.Input(obj=mod, attr='count', increment=1, decimal_draw_precision=0))
        popup.row_insert(row)

        spacer(popup)

        row = popup.row()
        row.add_element(form.Button(text="Constant", obj=mod, attr="use_constant_offset"))
        popup.row_insert(row)

        spacer(popup, height=5)

        row = popup.row()
        row.add_element(form.Input(obj=mod, attr='constant_offset_displace', increment=1, width=50, decimal_draw_precision=3, attr_index=0))
        row.add_element(form.Spacer(width=5))
        row.add_element(form.Input(obj=mod, attr='constant_offset_displace', increment=1, width=50, decimal_draw_precision=3, attr_index=1))
        row.add_element(form.Spacer(width=5))
        row.add_element(form.Input(obj=mod, attr='constant_offset_displace', increment=1, width=50, decimal_draw_precision=3, attr_index=2))
        popup.row_insert(row)

        spacer(popup)

        row = popup.row()
        row.add_element(form.Button(text="Relative", obj=mod, attr="use_relative_offset"))
        popup.row_insert(row)

        spacer(popup, height=5)

        row = popup.row()
        row.add_element(form.Input(obj=mod, attr='relative_offset_displace', increment=1, width=50, decimal_draw_precision=3, attr_index=0))
        row.add_element(form.Spacer(width=5))
        row.add_element(form.Input(obj=mod, attr='relative_offset_displace', increment=1, width=50, decimal_draw_precision=3, attr_index=1))
        row.add_element(form.Spacer(width=5))
        row.add_element(form.Input(obj=mod, attr='relative_offset_displace', increment=1, width=50, decimal_draw_precision=3, attr_index=2))
        popup.row_insert(row)

        spacer(popup)
        return msg, popup

    if mod.type == 'BEVEL':
        row = popup.row()
        row.add_element(form.Button(text="Harden", obj=mod, attr="harden_normals"))
        row.add_element(form.Spacer(width=5))
        row.add_element(form.Button(text="Clamp", obj=mod, attr="use_clamp_overlap"))
        popup.row_insert(row)

        spacer(popup)

        row = popup.row()
        row.add_element(form.Label(text="Amount", width=75))
        row.add_element(form.Input(obj=mod, attr='width', increment=.1, width=75, decimal_draw_precision=5))
        popup.row_insert(row)

        row = popup.row()
        row.add_element(form.Label(text="Segments", width=75))
        row.add_element(form.Input(obj=mod, attr='segments', increment=1, width=75, decimal_draw_precision=5))
        popup.row_insert(row)

        row = popup.row()
        row.add_element(form.Label(text="Angle", width=75))
        row.add_element(form.Input(obj=mod, attr='angle_limit', increment=math.radians(1), width=75, decimal_draw_precision=0, handle_radians=True, use_mod_keys=False))
        popup.row_insert(row)

        spacer(popup)

        row = popup.row()
        row.add_element(form.Label(text="Outer", width=50))
        opts = ['MITER_SHARP', 'MITER_PATCH', 'MITER_ARC']
        row.add_element(form.Dropdown(
            options=opts, callback=set_bevel_outer, additional_args=(mod,),
            update_hook=get_bevel_outer, hook_args=(mod,), index=opts.index(mod.miter_outer)))
        popup.row_insert(row)

        row = popup.row()
        row.add_element(form.Label(text="Inner", width=50))
        opts = ['MITER_SHARP', 'MITER_ARC']
        row.add_element(form.Dropdown(
            options=opts, callback=set_bevel_inner, additional_args=(mod,),
            update_hook=get_bevel_inner, hook_args=(mod,), index=opts.index(mod.miter_inner)))
        popup.row_insert(row)

        spacer(popup)
        return msg, popup

    if mod.type == 'BOOLEAN':
        row = popup.row()
        opts = ['INTERSECT', 'UNION', 'DIFFERENCE']
        row.add_element(form.Dropdown(
            options=opts, callback=set_boolean_operation, additional_args=(mod,),
            update_hook=get_boolean_operation, hook_args=(mod,), index=opts.index(mod.operation)))
        
        if hasattr(mod, 'solver'):
            row.add_element(form.Spacer(width=10))
            opts = ['EXACT', 'FAST']
            row.add_element(form.Dropdown(
                options=opts, callback=set_boolean_solver, additional_args=(mod,),
                update_hook=get_boolean_solver, hook_args=(mod,), index=opts.index(mod.solver)))
        popup.row_insert(row)

        spacer(popup)
        return msg, popup

    if mod.type == 'DECIMATE':

        popup.update_func = decimate_popup_alter
        popup.update_args = (popup, mod)

        modes = ['COLLAPSE', 'UNSUBDIV', 'DISSOLVE']

        row = popup.row()
        row.add_element(form.Dropdown(
            options=modes, callback=set_decimate_type, additional_args=(mod,),
            update_hook=get_decimate_type, hook_args=(mod,), index=modes.index(mod.decimate_type)))
        popup.row_insert(row)

        spacer(popup)

        # COLLAPSE
        row = popup.row()
        row.add_element(form.Label(text="Ratio", width=75))
        row.add_element(form.Input(obj=mod, attr='ratio', increment=.05, width=75, decimal_draw_precision=3))
        popup.row_insert(row, label='COLLAPSE', active=True if mod.decimate_type == 'COLLAPSE' else False)

        # UNSUBDIV
        row = popup.row()
        row.add_element(form.Label(text="Iterations", width=75))
        row.add_element(form.Input(obj=mod, attr='iterations', increment=1, width=75, decimal_draw_precision=0, use_mod_keys=False))
        popup.row_insert(row, label='UNSUBDIV', active=True if mod.decimate_type == 'UNSUBDIV' else False)

        # DISSOLVE
        row = popup.row()
        row.add_element(form.Label(text="Angle Limit", width=75))
        row.add_element(form.Input(obj=mod, attr='angle_limit', increment=math.radians(1), width=75, decimal_draw_precision=0, handle_radians=True, use_mod_keys=False))
        popup.row_insert(row, label='DISSOLVE', active=True if mod.decimate_type == 'DISSOLVE' else False)

        spacer(popup)
        return msg, popup

    if mod.type == 'EDGE_SPLIT':
        row = popup.row()
        row.add_element(form.Button(text="Angle", obj=mod, attr="use_edge_angle"))
        row.add_element(form.Spacer(width=5))
        row.add_element(form.Button(text="Sharp", obj=mod, attr="use_edge_sharp"))
        popup.row_insert(row)

        spacer(popup)

        row = popup.row()
        row.add_element(form.Label(text="Angle"))
        row.add_element(form.Input(obj=mod, attr='split_angle', increment=math.radians(1), width=75, decimal_draw_precision=0, handle_radians=True, use_mod_keys=False))
        popup.row_insert(row)

        spacer(popup)
        return msg, popup

    if mod.type == 'MIRROR':
        row = popup.row()
        row.add_element(form.Label(text='Axis', width=40))
        row.add_element(form.Spacer(width=5))
        row.add_element(form.Button(text="X", obj=mod, attr="use_axis", attr_index=0))
        row.add_element(form.Spacer(width=5))
        row.add_element(form.Button(text="Y", obj=mod, attr="use_axis", attr_index=1))
        row.add_element(form.Spacer(width=5))
        row.add_element(form.Button(text="Z", obj=mod, attr="use_axis", attr_index=2))
        popup.row_insert(row)

        spacer(popup)

        row = popup.row()
        row.add_element(form.Label(text='Bisect', width=40))
        row.add_element(form.Spacer(width=5))
        row.add_element(form.Button(text="X", obj=mod, attr="use_bisect_axis", attr_index=0))
        row.add_element(form.Spacer(width=5))
        row.add_element(form.Button(text="Y", obj=mod, attr="use_bisect_axis", attr_index=1))
        row.add_element(form.Spacer(width=5))
        row.add_element(form.Button(text="Z", obj=mod, attr="use_bisect_axis", attr_index=2))
        popup.row_insert(row)

        spacer(popup)

        row = popup.row()
        row.add_element(form.Label(text='Flip', width=40))
        row.add_element(form.Spacer(width=5))
        row.add_element(form.Button(text="X", obj=mod, attr="use_bisect_flip_axis", attr_index=0))
        row.add_element(form.Spacer(width=5))
        row.add_element(form.Button(text="Y", obj=mod, attr="use_bisect_flip_axis", attr_index=1))
        row.add_element(form.Spacer(width=5))
        row.add_element(form.Button(text="Z", obj=mod, attr="use_bisect_flip_axis", attr_index=2))
        popup.row_insert(row)

        spacer(popup)
        return msg, popup

    if mod.type == 'SCREW':
        row = popup.row()
        opts = ['X', 'Y', 'Z']
        row.add_element(form.Dropdown(
            options=opts, callback=set_screw_axis, additional_args=(mod,),
            update_hook=get_screw_axis, hook_args=(mod,), index=opts.index(mod.axis)))
        row.add_element(form.Spacer(width=5))
        row.add_element(form.Button(text="Merge", obj=mod, attr="use_merge_vertices"))
        row.add_element(form.Spacer(width=5))
        row.add_element(form.Button(text="Flip", obj=mod, attr="use_normal_flip"))
        popup.row_insert(row)

        spacer(popup)

        row = popup.row()
        row.add_element(form.Label(text="Angle", width=50))
        row.add_element(form.Input(obj=mod, attr='angle', increment=math.radians(1), width=75, decimal_draw_precision=2, handle_radians=True, use_mod_keys=False))
        popup.row_insert(row)

        row = popup.row()
        row.add_element(form.Label(text="Screw", width=50))
        row.add_element(form.Input(obj=mod, attr='screw_offset', increment=.5, width=75, decimal_draw_precision=2))
        popup.row_insert(row)

        row = popup.row()
        row.add_element(form.Label(text="Screw", width=50))
        row.add_element(form.Input(obj=mod, attr='iterations', increment=1, width=75, decimal_draw_precision=0, use_mod_keys=False))
        popup.row_insert(row)

        spacer(popup)
        return msg, popup

    if mod.type == 'SOLIDIFY':
        row = popup.row()
        row.add_element(form.Button(text="Even", obj=mod, attr="use_even_offset"))
        row.add_element(form.Spacer(width=5))
        row.add_element(form.Button(text="Fill", obj=mod, attr="use_rim"))
        row.add_element(form.Spacer(width=5))
        row.add_element(form.Button(text="Rim", obj=mod, attr="use_rim_only"))
        row.add_element(form.Spacer(width=5))
        row.add_element(form.Button(text="Flip", obj=mod, attr="use_flip_normals"))
        popup.row_insert(row)

        spacer(popup)

        row = popup.row()
        row.add_element(form.Label(text="Thickness", width=75))
        row.add_element(form.Input(obj=mod, attr='thickness', increment=.1, width=75, decimal_draw_precision=5))
        popup.row_insert(row)

        row = popup.row()
        row.add_element(form.Label(text="Offset", width=75))
        row.add_element(form.Input(obj=mod, attr='offset', increment=.1, width=75, decimal_draw_precision=5))
        popup.row_insert(row)

        spacer(popup)
        return msg, popup

    if mod.type == 'SUBSURF':
        row = popup.row()
        opts = ['CATMULL_CLARK', 'SIMPLE']
        row.add_element(form.Dropdown(
            options=opts, callback=set_subd_subdivision_type, additional_args=(mod,),
            update_hook=get_subd_subdivision_type, hook_args=(mod,), index=opts.index(mod.subdivision_type)))
        popup.row_insert(row)

        spacer(popup)

        row = popup.row()
        row.add_element(form.Label(text="Viewport", width=75))
        row.add_element(form.Input(obj=mod, attr='levels', increment=1, width=50, decimal_draw_precision=0, use_mod_keys=False))
        popup.row_insert(row)

        row = popup.row()
        row.add_element(form.Label(text="Render", width=75))
        row.add_element(form.Input(obj=mod, attr='render_levels', increment=1, width=50, decimal_draw_precision=0, use_mod_keys=False))
        popup.row_insert(row)

        spacer(popup)

        row = popup.row()
        row.add_element(form.Button(text="Optimal Display", obj=mod, attr="show_only_control_edges"))
        popup.row_insert(row)

        spacer(popup)

        row = popup.row()
        row.add_element(form.Button(text="Crease", obj=mod, attr="use_creases"))
        popup.row_insert(row)

        spacer(popup)

        row = popup.row()
        opts = ['PRESERVE_CORNERS', 'ALL']
        row.add_element(form.Dropdown(
            options=opts, callback=set_subd_boundary_smooth, additional_args=(mod,),
            update_hook=get_subd_boundary_smooth, hook_args=(mod,), index=opts.index(mod.boundary_smooth)))
        popup.row_insert(row)

        spacer(popup)
        return msg, popup

    if mod.type == 'WELD':

        if hasattr(mod, 'mode'):
            row = popup.row()
            opts = ['ALL', 'CONNECTED']
            row.add_element(form.Dropdown(
                options=opts, callback=set_weld_mode, additional_args=(mod,),
                update_hook=get_weld_mode, hook_args=(mod,), index=opts.index(mod.mode)))
            popup.row_insert(row)

            spacer(popup)

        row = popup.row()
        row.add_element(form.Label(text="Distance"))
        row.add_element(form.Input(obj=mod, attr='merge_threshold', increment=.001, width=75, decimal_draw_precision=5))
        popup.row_insert(row)

        spacer(popup)
        return msg, popup

    if mod.type == 'WIREFRAME':
        row = popup.row()
        row.add_element(form.Button(text="Even", obj=mod, attr="use_even_offset"))
        row.add_element(form.Spacer(width=5))
        row.add_element(form.Button(text="Boundary", obj=mod, attr="use_boundary"))
        row.add_element(form.Spacer(width=5))
        row.add_element(form.Button(text="Relative", obj=mod, attr="use_relative_offset"))
        popup.row_insert(row)

        spacer(popup)

        row = popup.row()
        row.add_element(form.Label(text="Thickness", width=75))
        row.add_element(form.Input(obj=mod, attr='thickness', increment=.1, width=75, decimal_draw_precision=3))
        popup.row_insert(row)

        row = popup.row()
        row.add_element(form.Label(text="Offset", width=75))
        row.add_element(form.Input(obj=mod, attr='offset', increment=.1, width=75, decimal_draw_precision=3))
        popup.row_insert(row)

        spacer(popup)
        return msg, popup

    # --- Deform --- #

    if mod.type == 'CAST':
        row = popup.row()
        opts = ['SPHERE', 'CYLINDER', 'CUBOID']
        row.add_element(form.Dropdown(
            options=opts, callback=set_cast_shape, additional_args=(mod,),
            update_hook=get_cast_shape, hook_args=(mod,), index=opts.index(mod.cast_type)))
        row.add_element(form.Spacer(width=5))
        row.add_element(form.Button(text="X", obj=mod, attr="use_x"))
        row.add_element(form.Spacer(width=5))
        row.add_element(form.Button(text="Y", obj=mod, attr="use_y"))
        row.add_element(form.Spacer(width=5))
        row.add_element(form.Button(text="Z", obj=mod, attr="use_z"))
        popup.row_insert(row)

        spacer(popup)

        row = popup.row()
        row.add_element(form.Label(text="Factor", width=50))
        row.add_element(form.Input(obj=mod, attr='factor', increment=.1, width=75, decimal_draw_precision=2))
        popup.row_insert(row)

        row = popup.row()
        row.add_element(form.Label(text="Radius", width=50))
        row.add_element(form.Input(obj=mod, attr='radius', increment=.1, width=75, decimal_draw_precision=2))
        popup.row_insert(row)

        row = popup.row()
        row.add_element(form.Label(text="Size", width=50))
        row.add_element(form.Input(obj=mod, attr='size', increment=.1, width=75, decimal_draw_precision=2))
        popup.row_insert(row)

        spacer(popup)
        return msg, popup

    if mod.type == 'DISPLACE':
        row = popup.row()
        opts = ['X', 'Y', 'Z', 'NORMAL', 'CUSTOM_NORMAL', 'RGB_TO_XYZ']
        row.add_element(form.Dropdown(
            options=opts, callback=set_displace_direction, additional_args=(mod,),
            update_hook=get_displace_direction, hook_args=(mod,), index=opts.index(mod.direction)))
        popup.row_insert(row)

        spacer(popup)

        row = popup.row()
        row.add_element(form.Label(text="Strength", width=75))
        row.add_element(form.Input(obj=mod, attr='strength', increment=.1, width=75, decimal_draw_precision=2))
        popup.row_insert(row)

        row = popup.row()
        row.add_element(form.Label(text="Mid Level", width=75))
        row.add_element(form.Input(obj=mod, attr='mid_level', increment=.1, width=75, decimal_draw_precision=2))
        popup.row_insert(row)

        spacer(popup)
        return msg, popup

    if mod.type == 'LATTICE':
        row = popup.row()
        row.add_element(form.Label(text="Strength"))
        row.add_element(form.Input(obj=mod, attr='strength', increment=.1, width=75, decimal_draw_precision=2))
        popup.row_insert(row)

        spacer(popup)
        return msg, popup

    if mod.type == 'SIMPLE_DEFORM':

        popup.update_func = simp_def_popup_alter
        popup.update_args = (popup, mod)


        row = popup.row()
        opts = ['TWIST' ,'BEND' ,'TAPER' ,'STRETCH']
        row.add_element(form.Dropdown(
            options=opts, callback=set_simp_def_method, additional_args=(mod,),
            update_hook=get_simp_def_method, hook_args=(mod,), index=opts.index(mod.deform_method)))
        row.add_element(form.Spacer(width=10))
        opts = ['X', 'Y', 'Z']
        row.add_element(form.Dropdown(
            options=opts, callback=set_simp_def_axis, additional_args=(mod,),
            update_hook=get_simp_def_axis, hook_args=(mod,), index=opts.index(mod.deform_axis)))
        popup.row_insert(row)

        spacer(popup)

        float_active = True if mod.deform_method in {'TAPER' ,'STRETCH'} else False

        row = popup.row()
        row.add_element(form.Label(text="Factor"))
        row.add_element(form.Input(obj=mod, attr='factor', increment=.1, width=75, decimal_draw_precision=2))
        popup.row_insert(row, label='FLOAT', active=float_active)

        row = popup.row()
        row.add_element(form.Label(text="Factor"))
        row.add_element(form.Input(obj=mod, attr='factor', increment=math.radians(1), width=75, decimal_draw_precision=2, handle_radians=True, use_mod_keys=False))
        popup.row_insert(row, label='DEGREES', active=not float_active)

        spacer(popup)
        return msg, popup

# --- UTILS --- #

def spacer(popup, height=10):
    row = popup.row()
    row.add_element(form.Spacer(height=height))
    popup.row_insert(row)

def header(op, popup, mod, index, bool_tracker_mode=False):
    row = popup.row()

    type_text = mod.type

    # Shorten long ones
    if mod.type == 'WEIGHTED_NORMAL':
        type_text = 'WN'
    elif mod.type == 'EDGE_SPLIT':
        type_text = 'SPLIT'

    row.add_element(form.Label(text=f'{index} : {type_text} : {mod.name}'))

    if bool_tracker_mode:
        row.add_element(form.Button(
            glob_img_key='eyecon_closed', tips=["Isolate modifier / Enable up to"],
            callback=op.bool_tracker.isolate_mod, pos_args=(mod,), neg_args=(mod,)))
    else:
        row.add_element(form.Button(
            glob_img_key='eyecon_closed', tips=["Isolate modifier / Enable up to"],
            callback=op.mod_tracker.isolate_mod, pos_args=(mod,), neg_args=(mod,)))
    row.add_element(form.Spacer(width=10))
    row.add_element(form.Button(
        glob_img_key="eyecon_open", tips=["Toggle visibility"], obj=mod, attr="show_viewport"))
    popup.row_insert(row)

# --- WEIGHTED NORMAL --- #

def set_wn_mode(opt, mod):
    mod.mode = opt

def get_wn_mode(mod):
    return mod.mode

# --- BOOLEAN --- #

def set_boolean_operation(opt, mod):
    mod.operation = opt

def get_boolean_operation(mod):
    return mod.operation

def set_boolean_solver(opt, mod):
    mod.solver = opt

def get_boolean_solver(mod):
    return mod.solver

# --- DECIMATE --- #

def decimate_popup_alter(popup, mod):
    if mod.decimate_type == 'COLLAPSE':
        if popup.get_row_status(label='COLLAPSE'): return
        popup.row_activation(label='COLLAPSE', active=True)
        popup.row_activation(label='UNSUBDIV', active=False)
        popup.row_activation(label='DISSOLVE', active=False)
        popup.trigger_rebuild()
    elif mod.decimate_type == 'UNSUBDIV':
        if popup.get_row_status(label='UNSUBDIV'): return
        popup.row_activation(label='COLLAPSE', active=False)
        popup.row_activation(label='UNSUBDIV', active=True)
        popup.row_activation(label='DISSOLVE', active=False)
        popup.trigger_rebuild()
    elif mod.decimate_type == 'DISSOLVE':
        if popup.get_row_status(label='DISSOLVE'): return
        popup.row_activation(label='COLLAPSE', active=False)
        popup.row_activation(label='UNSUBDIV', active=False)
        popup.row_activation(label='DISSOLVE', active=True)
        popup.trigger_rebuild()

def set_decimate_type(opt, mod):
    mod.decimate_type = opt

def get_decimate_type(mod):
    return mod.decimate_type

# --- BEVEL --- #

def set_bevel_outer(opt, mod):
    mod.miter_outer = opt

def get_bevel_outer(mod):
    return mod.miter_outer

def set_bevel_inner(opt, mod):
    mod.miter_inner = opt

def get_bevel_inner(mod):
    return mod.miter_inner

# --- SCREW --- #

def set_screw_axis(opt, mod):
    mod.axis = opt

def get_screw_axis(mod):
    return mod.axis

# --- SUB-D --- #

def set_subd_subdivision_type(opt, mod):
    mod.subdivision_type = opt

def get_subd_subdivision_type(mod):
    return mod.subdivision_type

def set_subd_boundary_smooth(opt, mod):
    mod.boundary_smooth = opt

def get_subd_boundary_smooth(mod):
    return mod.boundary_smooth

# --- WELD --- #

def set_weld_mode(opt, mod):
    mod.mode = opt

def get_weld_mode(mod):
    return mod.mode

# --- CAST --- #

def set_cast_shape(opt, mod):
    mod.cast_type = opt

def get_cast_shape(mod):
    return mod.cast_type

# --- DISPLACE --- #

def set_displace_direction(opt, mod):
    mod.direction = opt

def get_displace_direction(mod):
    return mod.direction

# --- SIMPLE DEFORM --- #

def simp_def_popup_alter(popup, mod):
    if mod.deform_method in {'TAPER' ,'STRETCH'}:
        if popup.get_row_status(label='FLOAT'): return

        popup.row_activation(label='FLOAT', active=True)
        popup.row_activation(label='DEGREES', active=False)
        popup.trigger_rebuild()
    else:
        if popup.get_row_status(label='DEGREES'): return

        popup.row_activation(label='FLOAT', active=False)
        popup.row_activation(label='DEGREES', active=True)
        popup.trigger_rebuild()

def set_simp_def_method(opt, mod):
    mod.deform_method = opt

def get_simp_def_method(mod):
    return mod.deform_method

def set_simp_def_axis(opt, mod):
    mod.deform_axis = opt

def get_simp_def_axis(mod):
    return mod.deform_axis


