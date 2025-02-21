import bpy
from .... utility import addon
from .... ui_framework.utils.mods_list import get_mods_list
from .... ui_framework import form_ui as form
from . import Mode
from . struct import get_boxelize_ref

# --- FAS --- #

def draw_FAS(op, context):
    op.master.setup()
    if not op.master.should_build_fast_ui(): return

    # Main
    win_list = ["Dice"]

    # Help
    help_items = {"GLOBAL" : [], "STANDARD" : []}
    help_items["GLOBAL"] = [
        ("M", "Toggle mods list"),
        ("H", "Toggle help"),
        ("~", "Toggle UI Display Type"),
        ("O", "Toggle viewport rendering")]
    help_items["STANDARD"] = [
        ("TAB", f"Dot : {'CLOSE' if op.form.is_dot_open() else 'OPEN'}"),
        ("V", op.edit_mode.name),
        ("W", "Toggle Wireframe")]

    # Mods
    mods_list = get_mods_list(mods=bpy.context.active_object.modifiers)

    w_append = win_list.append
    h_append = help_items["STANDARD"].append

    # --- Extend --- #
    if op.edit_mode == Mode.DICE_3D:
        dice_3d_FAS(op, context, w_append, h_append)
    elif op.edit_mode == Mode.DICE_2D:
        dice_2d_FAS(op, context, w_append, h_append)
    elif op.edit_mode == Mode.DICE_LINE:
        dice_line_FAS(op, context, w_append, h_append)

    # Draw
    help_items['STANDARD'].reverse()
    op.master.receive_fast_ui(win_list=win_list, help_list=help_items, image="Dice", mods_list=mods_list)
    op.master.finished()


def dice_3d_FAS(op, context, w_append, h_append):
    D3D = op.dice_3d
    boxelize = get_boxelize_ref()
    prefs = addon.preference()

    # Main
    w_append("3d Mode[V]") 
    if boxelize.active:
        w_append(f"Segments : {boxelize.segments}")
    else:
        if D3D.x_dice.active:
            w_append(f"X : {D3D.x_dice.segments}")
        if D3D.y_dice.active:
            w_append(f"Y : {D3D.y_dice.segments}")
        if D3D.z_dice.active:
            w_append(f"Z : {D3D.z_dice.segments}")

    w_append(f'{D3D.knife_method}[Q]')

    if D3D.exit_to_twist:
        w_append("To_Twist")

    # Help
    h_append(("Q",            f"Method : {D3D.knife_method}"))
    h_append(("X",            f"Turn X Axis : {'OFF' if D3D.x_dice.active else 'ON'}"))
    h_append(("Y",            f"Turn Y Axis : {'OFF' if D3D.y_dice.active else 'ON'}"))
    h_append(("Z",            f"Turn Z Axis : {'OFF' if D3D.z_dice.active else 'ON'}"))
    h_append(("S",            "Smart Apply"))
    h_append(("T",            f"Exit To_Twist : {'ON' if D3D.exit_to_twist else 'OFF'}"))
    h_append(("J",            f"Join Objects"))
    h_append(("B",            f"Boxelize : {'ON' if boxelize.active else 'OFF'}"))
    h_append(("N",            f"Shader : {prefs.property.dice_wire_type}"))
    h_append(("Shift Scroll", "Scroll Presets"))


def dice_2d_FAS(op, context, w_append, h_append):
    D2D = op.dice_2d
    prefs = addon.preference()

    # Main
    w_append("2d Mode[V]")
    w_append(f"X : {D2D.u}")
    w_append(f"Y : {D2D.v}")

    # Help
    h_append(("Scroll", "Adjust Segments"))
    h_append(("Numpad", "Navigation"))
    h_append(("D", f"Dissolve Original {D2D.dissolve_original}"))
    h_append(("C", f"Clean Faces {D2D.clean_faces}"))
    h_append(("X", "Set X Dice to 1"))
    h_append(("Y", "Set Y Dice to 1"))
    h_append(("B", "Toggle Boxelize"))
    h_append(("R", "Toggle Rotation"))
    if D2D.dissolve_original:
        h_append(("S", f"Keep Sharps {D2D.keep_sharps}"))
    if D2D.rotating:
        h_append(("CTRL", "Angle Snap"))


def dice_line_FAS(op, context, w_append, h_append):
    DL = op.dice_line
    prefs = addon.preference()

    # Main
    w_append("Line Mode[V]")
    w_append(f"Angle {DL.angle}")

    # Help
    h_append(("Scroll",    "Navigation"))
    h_append(("Numpad",    "Navigation"))
    h_append(("Alt",       "Adjust Rotation"))
    h_append(("Ctrl",     "Vert Snap"))
    h_append(("Alt Shift", "Vert to Vert"))
    h_append(("LeftMouse", "Cut"))
    h_append(("R",         "Reset Angle"))
    
# --- FORM --- #

def spacer(op, height=10, label='', active=True):
    row = op.form.row()
    row.add_element(form.Spacer(height=height))
    op.form.row_insert(row, label=label, active=active)


def setup_form(op, context, event):
    
    op.form = form.Form(context, event, dot_open=False)
    
    row = op.form.row()
    row.add_element(form.Label(text="Dice"))
    row.add_element(form.Spacer(width=10))
    opts = ["3D", "2D", "LINE"]
    tips = ["The cut projection method"]
    row.add_element(form.Dropdown(options=opts, tips=tips, callback=op.switch_edit_modes, update_hook=op.edit_modes_hook))
    tips = ["Execute and Exit", "Shift Click : Execute and Twist"]
    row.add_element(form.Button(text="✓", tips=tips, callback=op.exit_button, pos_args=(False,), neg_args=(True,), shift_img="ATwist360"))
    op.form.row_insert(row)

    spacer(op)

    # Dice 3D
    dice_3d_form(op, context, event)
    
    # Dice 2D
    dice_2d_form(op, context, event)

    # Dice Line
    dice_line_form(op, context, event)

    op.form.build()


def dice_3d_form(op, context, event):
    D3D = op.dice_3d
    boxelize = get_boxelize_ref()

    row = op.form.row()
    opts = ["Knife", "Intersect"]
    tips = ["Knife Project", "Mesh Intersect"]
    row.add_element(form.Dropdown(options=opts, tips=tips, callback=D3D.set_knife_method, update_hook=D3D.knife_method_hook))
    op.form.row_insert(row, label='3D_DICE', active=True)

    row = op.form.row()
    row.add_element(form.Button(text="B", width=20, tips=["Boxelize"], callback=D3D.toggle_boxelize, pos_args=(op,)))
    row.add_element(form.Input(obj=D3D, attr="boxelize_segments", width=50, increment=1))
    row.add_element(form.Button(text="Smart Apply", callback=D3D.smart_apply, pos_args=(context,)))
    op.form.row_insert(row, label='BOXELIZE', active=boxelize.active)

    spacer(op, label='BOXELIZE', active=boxelize.active)

    row = op.form.row()
    row.add_element(form.Button(text="B", width=20, tips=["Boxelize"], callback=D3D.toggle_boxelize, pos_args=(op,)))
    row.add_element(form.Button(text="Smart Apply", callback=D3D.smart_apply, pos_args=(context,)))
    op.form.row_insert(row, label='AXIAL', active=not boxelize.active)

    spacer(op, label='AXIAL', active=not boxelize.active)

    row = op.form.row()
    row.add_element(form.Button(text="X", width=20, tips=["Toggle Axis"], callback=D3D.x_dice.toggle_active, highlight_hook=D3D.x_dice.active_hook))
    row.add_element(form.Spacer(width=5))
    row.add_element(form.Input(obj=D3D.x_dice, attr="segments", width=50, increment=1, on_active_callback=D3D.x_dice.activate))
    op.form.row_insert(row, label='AXIAL', active=not boxelize.active)

    row = op.form.row()
    row.add_element(form.Button(text="Y", width=20, tips=["Toggle Axis"], callback=D3D.y_dice.toggle_active, highlight_hook=D3D.y_dice.active_hook))
    row.add_element(form.Spacer(width=5))
    row.add_element(form.Input(obj=D3D.y_dice, attr="segments", width=50, increment=1, on_active_callback=D3D.y_dice.activate))
    op.form.row_insert(row, label='AXIAL', active=not boxelize.active)

    row = op.form.row()
    row.add_element(form.Button(text="Z", width=20, tips=["Toggle Axis"], callback=D3D.z_dice.toggle_active, highlight_hook=D3D.z_dice.active_hook))
    row.add_element(form.Spacer(width=5))
    row.add_element(form.Input(obj=D3D.z_dice, attr="segments", width=50, increment=1, on_active_callback=D3D.z_dice.activate))
    op.form.row_insert(row, label='AXIAL', active=not boxelize.active)

    spacer(op, label='AXIAL', active=not boxelize.active)

    row = op.form.row()
    opts = ["DOTS", "LINES", "TICKS"]
    tips = ["Graphics type"]
    row.add_element(form.Dropdown(width=60, options=opts, tips=tips, callback=D3D.set_shader_type, update_hook=D3D.shader_type_hook))
    row.add_element(form.Button(img='eyecon_open', width=20, tips=["Toggle see through"], callback=D3D.toggle_see_through, highlight_hook=D3D.see_through_hook))
    op.form.row_insert(row, label='3D_DICE', active=True)


def dice_2d_form(op, context, evet):
    D2D = op.dice_2d

    row = op.form.row()
    row.add_element(form.Label(text="Rot"))
    row.add_element(form.Input(obj=D2D, attr="rot", width=50, increment=1))
    op.form.row_insert(row, label='2D_DICE', active=False)

    spacer(op, height=5, label='2D_DICE', active=False)

    row = op.form.row()
    row.add_element(form.Button(text="Dissolve", callback=D2D.set_dissolve_original, pos_args=(context,), highlight_hook=D2D.dissolve_original_hook))
    op.form.row_insert(row, label='2D_DICE', active=False)

    spacer(op, height=5, label='2D_DICE', active=False)

    row = op.form.row()
    row.add_element(form.Button(text="Boxelize", callback=D2D.toggle_boxelize, pos_args=(op,), highlight_hook=D2D.is_boxelize))
    op.form.row_insert(row, label='2D_DICE', active=False)

    spacer(op, height=5, label='2D_DICE', active=False)

    row = op.form.row()
    row.add_element(form.Input(obj=D2D, attr="segments", width=50, increment=1))
    op.form.row_insert(row, label='2D_DICE_BOXELIZE', active=False)

    row = op.form.row()
    row.add_element(form.Button(text="X", callback=D2D.set_u_to_one, highlight_hook=D2D.u_botton_hook))
    row.add_element(form.Spacer(width=5))
    row.add_element(form.Input(obj=D2D, attr="u", width=50, increment=1))
    op.form.row_insert(row, label='2D_DICE_BOXELIZE_UV', active=False)

    row = op.form.row()
    row.add_element(form.Button(text="Y", callback=D2D.set_v_to_one, highlight_hook=D2D.v_botton_hook))
    row.add_element(form.Spacer(width=5))
    row.add_element(form.Input(obj=D2D, attr="v", width=50, increment=1))
    op.form.row_insert(row, label='2D_DICE_BOXELIZE_UV', active=False)


def dice_line_form(op, context, evet):
    DL = op.dice_line

    row = op.form.row()
    row.add_element(form.Input(obj=DL, attr="angle", width=50, increment=15))
    op.form.row_insert(row, label='LINE_DICE', active=False)

    spacer(op, label='LINE_DICE', active=False)


def alter_form_layout(op, preset_label=''):
    
    if preset_label == 'BOXELIZE':
        # 3D
        op.form.row_activation(label='BOXELIZE', active=True)
        op.form.row_activation(label='AXIAL', active=False)
        op.form.row_activation(label='3D_DICE', active=True)
        # 2D
        op.form.row_activation(label='2D_DICE', active=False)
        op.form.row_activation(label='2D_DICE_BOXELIZE', active=False)
        op.form.row_activation(label='2D_DICE_BOXELIZE_UV', active=False)
        # LINE
        op.form.row_activation(label='LINE_DICE', active=False)

    elif preset_label == 'AXIAL':
        # 3D
        op.form.row_activation(label='BOXELIZE', active=False)
        op.form.row_activation(label='AXIAL', active=True)
        op.form.row_activation(label='3D_DICE', active=True)
        # 2D
        op.form.row_activation(label='2D_DICE', active=False)
        op.form.row_activation(label='2D_DICE_BOXELIZE', active=False)
        op.form.row_activation(label='2D_DICE_BOXELIZE_UV', active=False)
        # LINE
        op.form.row_activation(label='LINE_DICE', active=False)

    elif preset_label == '3D_DICE':
        # 3D
        boxelize = get_boxelize_ref()
        op.form.row_activation(label='BOXELIZE', active=boxelize.active)
        op.form.row_activation(label='AXIAL', active=not boxelize.active)
        op.form.row_activation(label='3D_DICE', active=True)
        # 2D
        op.form.row_activation(label='2D_DICE', active=False)
        op.form.row_activation(label='2D_DICE_BOXELIZE', active=False)
        op.form.row_activation(label='2D_DICE_BOXELIZE_UV', active=False)
        # LINE
        op.form.row_activation(label='LINE_DICE', active=False)

    elif preset_label == '2D_DICE':
        # 3D
        op.form.row_activation(label='BOXELIZE', active=False)
        op.form.row_activation(label='AXIAL', active=False)
        op.form.row_activation(label='3D_DICE', active=False)
        # 2D
        boxelize = op.dice_2d.is_boxelize()
        op.form.row_activation(label='2D_DICE', active=True)
        op.form.row_activation(label='2D_DICE_BOXELIZE', active=boxelize)
        op.form.row_activation(label='2D_DICE_BOXELIZE_UV', active=not boxelize)
        # LINE
        op.form.row_activation(label='LINE_DICE', active=False)
    
    elif preset_label == 'LINE_DICE':
        # 3D
        op.form.row_activation(label='BOXELIZE', active=False)
        op.form.row_activation(label='AXIAL', active=False)
        op.form.row_activation(label='3D_DICE', active=False)
        # 2D
        op.form.row_activation(label='2D_DICE', active=False)
        op.form.row_activation(label='2D_DICE_BOXELIZE', active=False)
        op.form.row_activation(label='2D_DICE_BOXELIZE_UV', active=False)
        # LINE
        op.form.row_activation(label='LINE_DICE', active=True)

    op.form.build(preserve_top_left=True)

