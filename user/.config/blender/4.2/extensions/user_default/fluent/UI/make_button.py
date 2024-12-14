import bpy

from ..Tools.translation import translate
from .Helpers.ui_button import FLUENT_Ui_Button

def make_button(what):
    if what == ('FIRST_SOLIDIFY'):
        button = FLUENT_Ui_Button('FIRST_SOLIDIFY')
        button.set_text('')
        button.set_tool_tip(translate('firstSolidify'))
        button.set_shape('CIRCLE')
        button.set_icon('first_solidify')
        button.set_action(what)
        button.set_order(0)
    elif what == ('FIRST_BEVEL'):
        button = FLUENT_Ui_Button('FIRST_BEVEL')
        button.set_text('')
        button.set_tool_tip(translate('firstBevel'))
        button.set_shape('CIRCLE')
        button.set_icon('first_bevel')
        button.set_action(what)
        button.set_order(1)
    elif what == ('SECOND_BEVEL'):
        button = FLUENT_Ui_Button('SECOND_BEVEL')
        button.set_text('')
        button.set_tool_tip(translate('secondBevel'))
        button.set_shape('CIRCLE')
        button.set_icon('second_bevel')
        button.set_action(what)
        button.set_order(2)
    elif what == ('TAPER'):
        button = FLUENT_Ui_Button('TAPER')
        button.set_text('')
        button.set_tool_tip(translate('taper'))
        button.set_shape('CIRCLE')
        button.set_icon('taper')
        button.set_action(what)
        button.set_order(3)
    elif what == ('SECOND_SOLIDIFY'):
        button = FLUENT_Ui_Button('SECOND_SOLIDIFY')
        button.set_text('')
        button.set_tool_tip(translate('secondSolidify'))
        button.set_shape('CIRCLE')
        button.set_icon('second_solidify')
        button.set_action(what)
        button.set_order(4)
    elif what == ('DIMENSIONS'):
        button = FLUENT_Ui_Button('DIMENSIONS')
        button.set_text('')
        button.set_tool_tip(translate('dimensions'))
        button.set_shape('CIRCLE')
        button.set_icon('dimensions')
        button.set_action(what)
    elif what == ('ROTATION'):
        button = FLUENT_Ui_Button('ROTATION')
        button.set_text('')
        button.set_tool_tip(translate('rotation'))
        button.set_shape('CIRCLE')
        button.set_icon('rotation')
        button.set_action(what)
    elif what == ('REUSE'):
        button = FLUENT_Ui_Button('REUSE')
        button.set_text('')
        button.set_tool_tip(translate('reuse'))
        button.set_shape('CIRCLE')
        button.set_icon('pick')
        button.set_action(what)
    elif what == ('MIRROR'):
        button = FLUENT_Ui_Button('MIRROR')
        button.set_text('')
        button.set_tool_tip(translate('mirror'))
        button.set_shape('CIRCLE')
        button.set_icon('mirror')
        button.set_action(what)
        button.set_order(5)
    elif what == ('ARRAY'):
        button = FLUENT_Ui_Button('ARRAY')
        button.set_text('')
        button.set_tool_tip(translate('arrayShortCut'))
        button.set_shape('CIRCLE')
        button.set_icon('array')
        button.set_action(what)
        button.set_order(6)
    elif what == ('CIRCULAR_ARRAY'):
        button = FLUENT_Ui_Button('CIRCULAR_ARRAY')
        button.set_text('')
        button.set_tool_tip(translate('circularArray'))
        button.set_shape('CIRCLE')
        button.set_icon('circular_array')
        button.set_action(what)
        button.set_order(7)
    elif what == ('FRAME'):
        button = FLUENT_Ui_Button('FRAME')
        button.set_text('')
        button.set_tool_tip(translate('frame'))
        button.set_shape('CIRCLE')
        button.set_icon('frame')
        button.set_action(what)
        button.set_order(8)
    elif what == ('CHAMFER'):
        button = FLUENT_Ui_Button('CHAMFER')
        button.set_text('')
        button.set_tool_tip(translate('chamfer'))
        button.set_shape('CIRCLE')
        button.set_icon('chamfer')
        button.set_action(what)
        button.set_order(3)
    elif what == ('RESOLUTION'):
        button = FLUENT_Ui_Button('RESOLUTION')
        button.set_text('')
        button.set_tool_tip(translate('resolution'))
        button.set_shape('CIRCLE')
        button.set_icon('resolution')
        button.set_action(what)
    elif what == ('INSET'):
        button = FLUENT_Ui_Button('INSET')
        button.set_text('')
        button.set_tool_tip(translate('insetThickness'))
        button.set_shape('CIRCLE')
        button.set_icon('first_solidify')
        button.set_action('INSET_THICKNESS')
    elif what == ('RADIUS'):
        button = FLUENT_Ui_Button('RADIUS')
        button.set_text('')
        button.set_tool_tip(translate('radius'))
        button.set_shape('CIRCLE')
        button.set_icon('radius')
        button.set_action(what)
    elif what == ('CURVE'):
        button = FLUENT_Ui_Button('CURVE')
        button.set_text('')
        button.set_tool_tip(translate('curve'))
        button.set_shape('CIRCLE')
        button.set_icon('curve')
        button.set_action(what)
        button.set_order(9)
    elif what == ('OUTER_BEVEL'):
        button = FLUENT_Ui_Button('OUTER_BEVEL')
        button.set_text('OB')
        button.set_tool_tip(translate('outerBevel'))
        button.set_shape('CIRCLE')
        # button.set_icon('curve')
        button.set_action(what)
        button.set_order(10)
    elif what == ('CANCEL'):
        button = FLUENT_Ui_Button('CANCEL')
        button.set_text('')
        button.set_tool_tip(translate('cancelShortCut'))
        button.set_shape('CIRCLE')
        button.set_icon('cancel')
        button.set_action('CANCELLED')
        # overlap = bpy.context.preferences.system.use_region_overlap
        t_panel_width = 0
        n_panel_width = 0
        # if overlap:
        for region in bpy.context.area.regions:
            if region.type == 'TOOLS':
                t_panel_width = region.width
            if region.type == 'UI':
                n_panel_width = region.width
        button_dimensions = button.get_dimensions()[0]
        button.set_position((bpy.context.area.width - n_panel_width - t_panel_width - button_dimensions, button_dimensions))
    elif what == ('VALIDATE'):
        button = FLUENT_Ui_Button('VALIDATE')
        button.set_text('')
        button.set_tool_tip(translate('validate'))
        button.set_shape('CIRCLE')
        button.set_action('VALIDATE')
        button.set_icon('validate')
        button.set_order(99)
    elif what == ('QUIT'):
        button = FLUENT_Ui_Button('QUIT')
        button.set_text('')
        button.set_tool_tip(translate('validAndQuit'))
        button.set_shape('CIRCLE')
        button.set_action('FINISHED')
        button.set_icon('quit')
        button.set_order(99)
    elif what == ('BACK'):
        button = FLUENT_Ui_Button('BACK')
        button.set_text('')
        button.set_tool_tip(translate('back'))
        button.set_shape('CIRCLE')
        button.set_action('BACK_MENU')
        button.set_icon('back')
    elif what == ('MORE'):
        button = FLUENT_Ui_Button()
        button.set_text('')
        button.set_tool_tip(translate('more'))
        button.set_icon('more')
        button.set_shape('CIRCLE')
        button.set_action('EXTRA_MENU')
        button.set_order(9)
    return button