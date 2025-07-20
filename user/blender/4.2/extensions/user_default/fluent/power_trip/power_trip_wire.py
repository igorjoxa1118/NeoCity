import bpy
from bpy.types import Operator

from ..Tools.translation import translate
from ..UI.Helpers.viewport_drawing import *
from ..UI.Helpers.ui_button import *
import time
import math
from bpy.props import StringProperty
from mathutils import Vector
from ..UI.make_button import make_button
from ..UI.Helpers.ui_management import FLUENT_ui_management
from .chain import chain_code
from ..modifiers import mirror_management


def wire_ui():
    pie_menu = FLUENT_Ui_Layout('WIRE', title=translate('wireMenu'), subtitle=translate('holdShift'))
    pie_menu.set_layout('PIE')

    button = make_button('QUIT')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_tool_tip(translate('radius'))
    button.set_text('')
    button.set_shape('CIRCLE')
    button.set_icon('radius')
    button.set_action('RADIUS')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_tool_tip(translate('rootStrength'))
    button.set_shape('CIRCLE')
    button.set_icon('stiffness')
    button.set_action('STIFFNESS')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_icon('t1')
    button.set_tool_tip(translate('twist')+' 01')
    button.set_shape('CIRCLE')
    button.set_action('TILT_01')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_icon('t2')
    button.set_tool_tip(translate('twist')+' 02')
    button.set_shape('CIRCLE')
    button.set_action('TILT_02')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_tool_tip(translate('array'))
    button.set_icon('array')
    button.set_shape('CIRCLE')
    button.set_action('ARRAY_MENU')
    pie_menu.add_item(button)

    button = make_button('MIRROR')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_tool_tip(translate('extra'))
    button.set_icon('extra')
    button.set_shape('CIRCLE')
    button.set_action('EXTRA_MENU')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_tool_tip(translate('utilities'))
    button.set_icon('tool')
    button.set_shape('CIRCLE')
    button.set_action('UTILITIES_MENU')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_tool_tip(translate('simulation'))
    button.set_shape('CIRCLE')
    button.set_icon('simulation')
    button.set_action('SIMULATION')
    pie_menu.add_item(button)

    return pie_menu


def wire_ring_ui():
    pie_menu = FLUENT_Ui_Layout('WIRE_RING_MENU',title='Ring menu', subtitle=translate('holdShift'))
    pie_menu.set_layout('PIE')

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_tool_tip(translate('add'))
    button.set_icon('creation')
    button.set_shape('CIRCLE')
    button.set_action('ADD_RING')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_tool_tip(translate('pick'))
    button.set_icon('pick')
    button.set_shape('CIRCLE')
    button.set_action('RING_PICK')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_tool_tip(translate('radius'))
    button.set_icon('radius')
    button.set_shape('CIRCLE')
    button.set_action('RING_RADIUS')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_tool_tip(translate('move'))
    button.set_icon('move')
    button.set_shape('CIRCLE')
    button.set_action('RING_MOVE')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_tool_tip(translate('length'))
    button.set_icon('thickness')
    button.set_shape('CIRCLE')
    button.set_action('RING_LENGTH')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_tool_tip(translate('scale'))
    button.set_icon('scale')
    button.set_shape('CIRCLE')
    button.set_action('RING_SCALE')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_tool_tip(translate('thickness'))
    button.set_icon('first_solidify')
    button.set_shape('CIRCLE')
    button.set_action('RING_THICKNESS')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_tool_tip(translate('bevel'))
    button.set_icon('first_bevel')
    button.set_shape('CIRCLE')
    button.set_action('RING_BEVEL')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_tool_tip(translate('array'))
    button.set_icon('array')
    button.set_shape('CIRCLE')
    button.set_action('RING_ARRAY_COUNT')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text('LR')
    button.set_tool_tip(translate('lengthResolution'))
    button.set_shape('CIRCLE')
    button.set_action('RING_L_RESOLUTION')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_icon('resolution')
    button.set_tool_tip(translate('circleResolution'))
    button.set_shape('CIRCLE')
    button.set_action('RING_C_RESOLUTION')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_tool_tip(translate('remove'))
    button.set_icon('remove')
    button.set_shape('CIRCLE')
    button.set_action('RING_REMOVE')
    pie_menu.add_item(button)

    button = make_button('BACK')
    pie_menu.add_item(button)

    pie_menu.set_decalage(1)

    return pie_menu


def wire_array_ui():
    pie_menu = FLUENT_Ui_Layout('ARRAY_MENU', title=translate('arrayMenu'), subtitle=translate('holdShift'))
    pie_menu.set_layout('PIE')

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_tool_tip(translate('radius'))
    button.set_icon('radius')
    button.set_shape('CIRCLE')
    button.set_action('RADIUS')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text(translate('count'))
    button.set_shape('RECTANGLE')
    button.set_action('ARRAY_COUNT')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text(translate('gap'))
    button.set_shape('RECTANGLE')
    button.set_action('ARRAY_GAP')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_tool_tip(translate('linear'))
    button.set_icon('array')
    button.set_shape('CIRCLE')
    button.set_action('ARRAY_LINEAR')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_tool_tip(translate('circular'))
    button.set_icon('circular_array')
    button.set_shape('CIRCLE')
    button.set_action('ARRAY_CIRCULAR')
    pie_menu.add_item(button)

    button = make_button('BACK')
    pie_menu.add_item(button)

    pie_menu.set_decalage(1)

    return pie_menu


def wire_extra_ui():
    pie_menu = FLUENT_Ui_Layout('EXTRA_MENU',title=translate('extraMenu'), subtitle=translate('holdShift'))
    pie_menu.set_layout('PIE')

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_tool_tip(translate('coil'))
    button.set_shape('CIRCLE')
    button.set_icon('coil')
    button.set_action('COIL_MENU')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_tool_tip(translate('protection'))
    button.set_shape('CIRCLE')
    button.set_icon('protection')
    button.set_action('PROTECTION_MENU')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_tool_tip(translate('duct'))
    button.set_icon('duct')
    button.set_shape('CIRCLE')
    button.set_action('DUCT_MENU')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_tool_tip(translate('chain'))
    button.set_icon('chain')
    button.set_shape('CIRCLE')
    button.set_action('CHAIN_MENU')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_tool_tip(translate('ring'))
    button.set_shape('CIRCLE')
    button.set_icon('ring')
    button.set_action('WIRE_RING_MENU')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_icon('connector')
    button.set_tool_tip(translate('connector'))
    button.set_shape('CIRCLE')
    button.set_action('CONNECTOR_MENU')
    pie_menu.add_item(button)

    button = make_button('BACK')
    pie_menu.add_item(button)

    pie_menu.set_decalage(1)

    return pie_menu


def wire_coil_ui():
    pie_menu = FLUENT_Ui_Layout('COIL_MENU',title=translate('coilMenu'), subtitle=translate('holdShift'))
    pie_menu.set_layout('PIE')

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_tool_tip(translate('addRemove'))
    button.set_icon('on_off')
    button.set_shape('CIRCLE')
    button.set_action('COIL_ADD')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_tool_tip(translate('radius'))
    button.set_icon('radius')
    button.set_shape('CIRCLE')
    button.set_action('COIL_RADIUS')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_tool_tip(translate('resolution'))
    button.set_icon('resolution')
    button.set_shape('CIRCLE')
    button.set_action('COIL_SPIRAL_RESOLUTION')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text('ROT')
    button.set_tool_tip(translate('rotationCount'))
    button.set_shape('CIRCLE')
    button.set_action('COIL_ROTATIONS')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_tool_tip(translate('rootStrength'))
    button.set_shape('CIRCLE')
    button.set_icon('stiffness')
    button.set_action('STIFFNESS')
    pie_menu.add_item(button)

    button = make_button('BACK')
    pie_menu.add_item(button)

    pie_menu.set_decalage(1)

    return pie_menu


def wire_protection_ui():
    pie_menu = FLUENT_Ui_Layout('PROTECTION_MENU', title=translate('protectionMenu'), subtitle=translate('holdShift'))
    pie_menu.set_layout('PIE')

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_tool_tip(translate('addRemove'))
    button.set_icon('on_off')
    button.set_shape('CIRCLE')
    button.set_action('PROTECTION_ADD')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_tool_tip(translate('spiralRadius'))
    button.set_icon('radius')
    button.set_shape('CIRCLE')
    button.set_action('PROTECTION_SPIRAL_RADIUS')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_tool_tip(translate('height'))
    button.set_icon('height')
    button.set_shape('CIRCLE')
    button.set_action('PROTECTION_HEIGHT')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text('ROT')
    button.set_tool_tip(translate('rotationCount'))
    button.set_shape('CIRCLE')
    button.set_action('PROTECTION_ROTATIONS')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_tool_tip(translate('thickness'))
    button.set_icon('first_solidify')
    button.set_shape('CIRCLE')
    button.set_action('PROTECTION_THICKNESS')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_tool_tip(translate('resolution'))
    button.set_icon('resolution')
    button.set_shape('CIRCLE')
    button.set_action('PROTECTION_RESOLUTION')
    pie_menu.add_item(button)

    button = make_button('BACK')
    pie_menu.add_item(button)

    pie_menu.set_decalage(1)

    return pie_menu


def wire_duct_ui():
    pie_menu = FLUENT_Ui_Layout('DUCT_MENU', title=translate('ductMenu'), subtitle=translate('holdShift'))
    pie_menu.set_layout('PIE')

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_tool_tip(translate('addRemove'))
    button.set_icon('on_off')
    button.set_shape('CIRCLE')
    button.set_action('DUCT_ADD')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_tool_tip(translate('radius'))
    button.set_icon('radius')
    button.set_shape('CIRCLE')
    button.set_action('DUCT_RADIUS')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text('RAT')
    button.set_tool_tip(translate('ratio'))
    button.set_shape('CIRCLE')
    button.set_action('DUCT_RATIO')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_tool_tip(translate('length'))
    button.set_icon('thickness')
    button.set_shape('CIRCLE')
    button.set_action('DUCT_LENGTH')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_tool_tip(translate('bevel'))
    button.set_icon('first_bevel')
    button.set_shape('CIRCLE')
    button.set_action('DUCT_BEVEL')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_tool_tip(translate('rootStrength'))
    button.set_shape('CIRCLE')
    button.set_icon('stiffness')
    button.set_action('STIFFNESS')
    pie_menu.add_item(button)

    button = make_button('BACK')
    pie_menu.add_item(button)

    pie_menu.set_decalage(1)

    return pie_menu


def wire_chain_ui():
    pie_menu = FLUENT_Ui_Layout('CHAIN_MENU', title=translate('chainMenu'), subtitle=translate('holdShift'))
    pie_menu.set_layout('PIE')

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_tool_tip(translate('add'))
    button.set_icon('creation')
    button.set_shape('CIRCLE')
    button.set_action('CHAIN_ADD')
    pie_menu.add_item(button)

    # button = FLUENT_Ui_Button()
    # button.set_text('OFF')
    # button.set_tool_tip('Offset')
    # button.set_shape('CIRCLE')
    # # button.set_icon('stiffness')
    # button.set_action('CHAIN_OFFSET')
    # pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text('SIZ')
    button.set_tool_tip(translate('size'))
    button.set_shape('CIRCLE')
    # button.set_icon('stiffness')
    button.set_action('CHAIN_SIZE')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_tool_tip(translate('radius'))
    button.set_shape('CIRCLE')
    button.set_icon('radius')
    button.set_action('CHAIN_THICKNESS')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_tool_tip(translate('bevel'))
    button.set_shape('CIRCLE')
    button.set_icon('first_bevel')
    button.set_action('CHAIN_BEVEL')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_tool_tip(translate('scale'))
    button.set_shape('CIRCLE')
    button.set_icon('scale')
    button.set_action('CHAIN_SCALE')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_tool_tip(translate('pickLink'))
    button.set_shape('CIRCLE')
    button.set_icon('pick')
    button.set_action('CHAIN_PICK')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_tool_tip(translate('rootStrength'))
    button.set_shape('CIRCLE')
    button.set_icon('stiffness')
    button.set_action('STIFFNESS')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_tool_tip(translate('reuse'))
    button.set_icon('reuse')
    button.set_shape('CIRCLE')
    button.set_action('REUSE')
    pie_menu.add_item(button)

    button = make_button('BACK')
    pie_menu.add_item(button)

    pie_menu.set_decalage(1)

    return pie_menu


def wire_utilities_ui():
    pie_menu = FLUENT_Ui_Layout('UTILITIES_MENU',title='Utilities menu', subtitle=translate('holdShift'))
    pie_menu.set_layout('PIE')

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_tool_tip(translate('circleResolution'))
    button.set_shape('CIRCLE')
    button.set_icon('resolution')
    button.set_action('CIRCLE_RESOLUTION')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_tool_tip(translate('curveResolution'))
    button.set_shape('CIRCLE')
    button.set_icon('curve_resolution')
    button.set_action('CURVE_RESOLUTION')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_tool_tip(translate('reuse'))
    button.set_icon('reuse')
    button.set_shape('CIRCLE')
    button.set_action('REUSE')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_tool_tip(translate('reset'))
    button.set_icon('reset')
    button.set_shape('CIRCLE')
    button.set_action('RESET')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_icon('offset')
    button.set_tool_tip(translate('upDown'))
    button.set_shape('CIRCLE')
    button.set_action('CURVE_OFFSET')
    pie_menu.add_item(button)

    button = make_button('BACK')
    pie_menu.add_item(button)
    pie_menu.set_decalage(1)

    return pie_menu


def wire_connector_ui():
    pie_menu = FLUENT_Ui_Layout('CONNECTOR_MENU', title=translate('connectorMenu'), subtitle=translate('holdShift'))
    pie_menu.set_layout('PIE')

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_icon('pick')
    button.set_tool_tip(translate('pick'))
    button.set_shape('CIRCLE')
    button.set_action('CONNECTOR_PICK')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_icon('remove')
    button.set_tool_tip(translate('remove'))
    button.set_shape('CIRCLE')
    button.set_action('CONNECTOR_REMOVE')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_icon('scale')
    button.set_tool_tip(translate('scale'))
    button.set_shape('CIRCLE')
    button.set_action('CONNECTOR_SCALE')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_icon('offset')
    button.set_tool_tip(translate('upDown'))
    button.set_shape('CIRCLE')
    button.set_action('CURVE_OFFSET')
    pie_menu.add_item(button)

    button = make_button('BACK')
    pie_menu.add_item(button)

    pie_menu.set_decalage(1)

    return pie_menu


def only_validate_menu():
    pie_menu = FLUENT_Ui_Layout('WIRE_RING')
    pie_menu.set_layout('PIE')

    button = make_button('VALIDATE')
    pie_menu.add_item(button)

    return pie_menu


class FLUENT_OT_Wire(Operator):
    """Put a cable"""
    bl_idname = "fluent.wire"
    bl_label = "Fluent wire"
    bl_options = {'REGISTER', 'UNDO'}

    operation: StringProperty(
        default='ADD'
    )

    ui_management = None

    def number_adjustment(self, the_modifier, input, increment, event, type, min = None, max = None):
        events = self.ui_management.event_dico_get()
        if self.previous_value is None:
            self.previous_value = the_modifier[input]
            self.slider_origin = event.mouse_region_x
            self.ui_management.hide_menu()
            self.ui_management.add_items(only_validate_menu())
            self.ui_management.hide_menu()
        self.enter_value = enter_value(self.enter_value, events)
        if events['shift_work']:
            increment = increment*10
        elif events['ctrl_work']:
            increment = increment/10
        else:
            increment = increment
        if events['shift_press'] or events['shift_release'] or events['ctrl_press'] or events[
            'ctrl_release']:
            self.slider_origin = event.mouse_region_x
            self.previous_value = the_modifier[input]

        value = self.previous_value + ((event.mouse_region_x - self.slider_origin) / increment)

        enter_value_validation_result = enter_value_validation(self.enter_value, events)
        if enter_value_validation_result[0]:
            value = enter_value_validation_result[1]
            self.end_of_adjustment()

        if min != None and value < min:
            value = min
        if max != None and value > max:
            value = max

        if type == 'FLOAT':
            the_modifier[input] = value
        elif type == 'INT':
            the_modifier[input] = int(value)

        the_modifier.show_viewport = False
        the_modifier.show_viewport = True

    def load_geometry_node(self):
        # charge la node
        if not bpy.data.node_groups.get('fluent_wire'):
            file_path_node_tree = os.path.dirname(realpath(__file__)) + "/wire/wire.blend/NodeTree"
            bpy.ops.wm.append(filename='fluent_wire', directory=file_path_node_tree)
        # ajoute geometry nodes
        geo_nodes = self.fluent_curve['curve_obj'].modifiers.new(name='.f_geometry_nodes', type='NODES')
        geo_nodes.node_group = bpy.data.node_groups['fluent_wire'].copy()

        # ajoute le bevel
        bevel_modif = self.fluent_curve['curve_obj'].modifiers.new(name=fluent_modifiers_name['outer_bevel'], type='BEVEL')
        bevel_modif.limit_method = 'ANGLE'
        bevel_modif.angle_limit = math.radians(40)
        bevel_modif.width = .001
        bevel_modif.segments = auto_bevel_segments(bevel_modif)
        bevel_modif.miter_outer = 'MITER_ARC'
        bevel_modif.use_clamp_overlap = False
        bevel_modif.harden_normals = True
        bevel_modif.show_expanded = False

    def make_wire(self, curve_name='Fluent_Wire'):
        bpy.ops.curve.primitive_bezier_curve_add()
        active_object('GET').name = curve_name
        self.fluent_curve['curve_obj'] = active_object('GET')
        self.fluent_curve['curve_obj']['fluent_type'] = 'wire'

        self.fluent_curve['curve_obj'].rotation_euler[0] = 0
        self.fluent_curve['curve_obj'].rotation_euler[1] = 0
        self.fluent_curve['curve_obj'].rotation_euler[2] = 0

        self.fluent_curve['curve_obj'].location = Vector((0, 0, 0))

        spline = active_object('GET').data.splines[0]

        a = spline.bezier_points[0]
        b = spline.bezier_points[1]

        a.co = self.fluent_curve['first_point']['hit']
        b.co = self.fluent_curve['second_point']['hit']

        a.handle_left = a.co - (self.fluent_curve['stiffness'] * self.fluent_curve['first_point']['normal'])
        a.handle_right = a.co + (self.fluent_curve['stiffness'] * self.fluent_curve['first_point']['normal'])

        b.handle_left = b.co + (self.fluent_curve['stiffness'] * self.fluent_curve['second_point']['normal'])
        b.handle_right = b.co - (self.fluent_curve['stiffness'] * self.fluent_curve['second_point']['normal'])

        self.fluent_curve['curve_obj'].data.bevel_depth = 0
        self.fluent_curve['curve_obj'].data.bevel_resolution = 16
        self.fluent_curve['curve_obj'].data.resolution_u = 64
        self.fluent_curve['curve_obj'].data.twist_mode = 'MINIMUM'
        self.fluent_curve['curve_obj'].data.twist_smooth = 8

        self.load_geometry_node()

    def add_your_chain_link(self, obj):
        if bpy.app.version >= (4, 0, 0):
            self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes']['Socket_7'] = obj
            self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes']['Socket_8'] = True
        else:
            self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes']['Input_6'] = obj
            self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes']['Input_7'] = True
        self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes'].show_viewport = False
        self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes'].show_viewport = True

    def add_ring(self, picked_ring=None):
        if not picked_ring:
            folder = '/wire'
            file_path_wire = os.path.dirname(realpath(__file__)) + folder + "/wire.blend/Object/"
            self.fluent_curve['curve_obj'].select_set(False)
            bpy.ops.wm.append(filename='f_ring_01', directory=file_path_wire)
            ring = bpy.context.selected_objects[0]
            ring['fluent_type'] = 'wire_ring'
            ring.name = self.fluent_curve['curve_obj'].name + '.Ring'
        else:
            ring = picked_ring

        # mise à jour de geometry nodes
        the_modifier = self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes']
        tree = the_modifier.node_group
        nodes = tree.nodes
        link = tree.links.new
        node_ring = nodes.new(type='GeometryNodeGroup')
        node_ring.node_tree = bpy.data.node_groups.get('f_add_ring')
        node_join = None
        node_reroute = None
        for n in nodes:
            if n.name == 'Join rings':
                node_join = n
            if n.name == 'curve_for_extra':
                node_reroute = n
            if node_join and node_reroute:
                break
        link(node_ring.outputs[0], node_join.inputs[0])
        link(node_reroute.outputs[0], node_ring.inputs[0])
        node_ring.inputs[1].default_value = ring

        if not picked_ring:
            the_input = ring.modifiers['Radius']
            radius = self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes']['Input_6']
            the_input.strength = radius * 2
            curve_length = self.fluent_curve['curve_obj'].data.splines[0].calc_length()
            node_ring.inputs['X Offset'].default_value = curve_length / 2
            if self.current_ring_node and self.current_ring_node.inputs['Object'].default_value.get('fluent_type') == 'wire_ring':
                for i in range(len(ring.modifiers)):
                    ring.modifiers.remove(ring.modifiers[0])
                copy_modifiers_stack(self.current_ring_node.inputs['Object'].default_value, ring, name='')
            ring.hide_set(True)
            ring.hide_render = True

        self.current_ring_node = node_ring
        self.fluent_curve['ring_nodes'].append(node_ring)

    def add_duct(self):
        folder = '/wire'
        file_path_wire = os.path.dirname(realpath(__file__)) + folder + "/wire.blend/Object/"
        self.fluent_curve['curve_obj'].select_set(False)
        bpy.ops.wm.append(filename='f_duct', directory=file_path_wire)
        duct = bpy.context.selected_objects[0]
        duct.hide_set(True)
        duct.hide_render = True
        duct.name = self.fluent_curve['curve_obj'].name + '.Duct'

        # mise à jour de geometry nodes
        the_modifier = self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes']
        the_modifier['Input_25'] = duct
        the_modifier['Radius'] = 0

        # ajoute un weld modifier juste après geometry node
        weld = self.fluent_curve['curve_obj'].modifiers.new(type='WELD', name=fluent_modifiers_name['weld'])
        weld.merge_threshold = 0.0001
        active_object('SET', self.fluent_curve['curve_obj'], True)
        bpy.ops.object.modifier_move_to_index(modifier=weld.name, index=1)

        bevel = self.fluent_curve['curve_obj'].modifiers[fluent_modifiers_name['outer_bevel']]
        bevel.width = 0.0001
        # masque le bevel
        # try:
        #     bevel = self.fluent_curve['curve_obj'].modifiers[fluent_modifiers_name['outer_bevel']]
        #     bevel.show_render = bevel.show_viewport = False
        # except:pass

    def add_chain(self):
        if not bpy.data.node_groups.get('.f_chain'):
            # créer un nouveau node tree
            node_tree = bpy.data.node_groups.new(name='.f_chain', type='GeometryNodeTree')
            chain_code(node_tree)
        else:
            node_tree = bpy.data.node_groups.get('.f_chain')

        self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes'].node_group = node_tree
        if bpy.app.version >= (4, 0, 0):
            self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes']['Socket_2'] = 0.1
            self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes']['Socket_3'] = 0.05
            self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes']['Socket_4'] = 0.05
            self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes']['Socket_5'] = .01
            self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes']['Socket_6'] = 1.0
        else:
            self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes']['Input_1'] = 0.1
            self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes']['Input_2'] = 0.05
            self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes']['Input_3'] = 0.05
            self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes']['Input_4'] = 0.01
            self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes']['Input_5'] = 1.0

        self.fluent_curve['chain'] = True

    def smooth_tilt(self):
        active_object('SET', self.fluent_curve['curve_obj'], True)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.curve.select_all(action='SELECT')
        bpy.ops.curve.smooth_tilt()
        bpy.ops.object.mode_set(mode='OBJECT')
        self.fluent_curve['curve_obj'].select_set(False)

    def end_of_adjustment(self):
        self.smooth_tilt()
        try:
            modifier_name = self.action.split('#')[1]
            if modifier_name in {'F_Ring_Array'}:
                bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        except:pass
        self.action = 'NOTHING'
        self.build_step = self.other_adjustment = None
        self.enter_value = 'None'
        self.previous_value = None

    def put_curve(self, reset = False):
        events = self.ui_management.event_dico_get()

        if not self.fluent_curve['added'] and self.fluent_curve['first_point'] and self.fluent_curve['second_point']:
            self.snap_face_center = False
            self.make_wire()

            self.fluent_curve['added'] = True
            self.ui_management.clear_dots()
            self.ui_management.hide_menu()
            self.ui_management.add_items(self.wire_menu)
            self.ui_management.hide_menu()

        # place le second point
        if events['value'] == 'PRESS' and events['type'] == 'LEFTMOUSE' and not self.fluent_curve['second_point'] and self.fluent_curve['first_point']:
            obj = click_on(events['mouse_x'], events['mouse_y'])
            if obj:
                copy = duplicate(obj, '.f_temp')
                apply_modifiers(copy)
                cast = obj_ray_cast(copy, events['mouse_x'], events['mouse_y'])
                if events['ctrl_work']:
                    cast['hit'] = copy.data.polygons[cast['face_index']].center
                local_cast = cast_local2global(cast)
                del local_cast['obj']
                bpy.data.objects.remove(copy, do_unlink=True)
                self.fluent_curve['second_point'] = local_cast.copy()
                dots = self.ui_management.get_dots()
                dots.clear_dots()

        # place le premier point
        if events['value'] == 'PRESS' and events['type'] == 'LEFTMOUSE' and not self.fluent_curve['first_point']:
            obj = click_on(events['mouse_x'], events['mouse_y'])
            if obj:
                copy = duplicate(obj, '.f_temp')
                apply_modifiers(copy)
                cast = obj_ray_cast(copy, events['mouse_x'], events['mouse_y'])
                if events['ctrl_work']:
                    cast['hit'] = copy.data.polygons[cast['face_index']].center
                global_cast = cast_local2global(cast)
                del global_cast['obj']
                bpy.data.objects.remove(copy, do_unlink=True)
                self.fluent_curve['first_point'] = global_cast.copy()
                dots = self.ui_management.get_dots()
                dots.add_3d_dot(global_cast['hit'], 5, (1, 1, 1, 1))

        if not reset:
            return [
                [translate('wireTool'),''],
                [translate('wireEnds'), translate('leftClick')],
                [translate('snapToFace'), translate('holdControl')]
            ]

    def modal(self, context, event):
        events = self.ui_management.event_dico_refresh(event)
        context.area.tag_redraw()
        screen_text = []
        refresh_pos = True

        self.ui_management.refresh_ui_items_list()

        if pass_through(event) or event.type == 'TAB':
            return {'PASS_THROUGH'}

        try:
            if bpy.context.active_object.mode == 'EDIT' and (not self.action or self.action in ['NOTHING', '###']):
                return {'PASS_THROUGH'}
        except:pass

        # animation
        if event.type == 'TIMER' and self.value_animation['step'] == 'PROCESS':
            delta = 10*(time.time()-self.value_animation['t0'])
            self.value_animation['input'].default_value = self.value_animation['v0'] + math.sin(delta)*self.value_animation['strength']
            if round(delta, 2) >= round(math.pi*2, 2):
                self.value_animation['input'].default_value = self.value_animation['v0']
                self.value_animation['step'] = 'WAIT'

        # action des bouttons
        action = self.ui_management.get_button_action()[0]
        callback = []

        # action du clavier
        if event.type == 'R' and event.value == 'PRESS':
            action = 'SELECT_RING'
        if event.type == 'ESC' and event.value == 'PRESS' and not self.action:
            action = 'CANCELLED'
        if event.type == 'ESC' and event.value == 'PRESS' and self.action:
            self.action = None
        if event.type == 'M' and event.value == 'PRESS':
            action = 'MIRROR'

        if action == 'MIRROR' or self.statut == 'AJUSTEMENT_EN_COURS':
            self.statut = 'AJUSTEMENT_EN_COURS'
            if not self.mirror:
                self.mirror = mirror_management(self.fluent_curve['curve_obj'], None)
            callback = self.mirror.adjust_mirror(self.ui_management)
            self.ui_management.pause_toggle = True

        if 'callback' in locals() and 'PASS_THROUGH' in callback:
            return {'PASS_THROUGH'}

        if 'callback' in locals() and 'STOP_ADJUSTMENT' in callback:
            callback.append('CLOSE_WIDGET')
            self.ui_management.clean_side_infos()
            self.ui_management.pause_toggle = False
            self.ui_management.refresh_ui_items_list(close_widget=True)

            self.statut = None

        if action:
            if action == 'VALIDATE':
                if 'callback' in locals() and 'CLOSE_WIDGET' in callback:
                    self.ui_management.refresh_ui_items_list(close_widget=True)
                else:
                    self.ui_management.remove_last_menu()
                self.end_of_adjustment()
                action = 'NOTHING'
            elif action == 'WIRE_RING_MENU' and not event.shift and not self.fluent_curve['chain']:
                self.ui_management.position_menu_under_previous(self.wire_ring_menu)
                self.ui_management.add_items(self.wire_ring_menu, is_submenu=True)
                refresh_pos = False
            elif action == 'ARRAY_MENU' and not event.shift and not self.fluent_curve['chain']:
                self.ui_management.position_menu_under_previous(self.array_menu)
                self.ui_management.add_items(self.array_menu, is_submenu=True)
                refresh_pos = False
            elif action == 'EXTRA_MENU' and not event.shift:
                self.ui_management.position_menu_under_previous(self.extra_menu)
                self.ui_management.add_items(self.extra_menu, is_submenu=True)
                refresh_pos = False
            elif action == 'COIL_MENU' and not event.shift and not self.fluent_curve['chain']:
                self.ui_management.position_menu_under_previous(self.coil_menu)
                self.ui_management.add_items(self.coil_menu, is_submenu=True)
                refresh_pos = False
            elif action == 'PROTECTION_MENU' and not event.shift and not self.fluent_curve['chain']:
                self.ui_management.position_menu_under_previous(self.protection_menu)
                self.ui_management.add_items(self.protection_menu, is_submenu=True)
                refresh_pos = False
            elif action == 'UTILITIES_MENU' and not event.shift:
                self.ui_management.position_menu_under_previous(self.utilities_menu)
                self.ui_management.add_items(self.utilities_menu, is_submenu=True)
                refresh_pos = False
            elif action == 'DUCT_MENU' and not event.shift and not self.fluent_curve['chain']:
                self.ui_management.position_menu_under_previous(self.duct_menu)
                self.ui_management.add_items(self.duct_menu, is_submenu=True)
                refresh_pos = False
            elif action == 'CONNECTOR_MENU' and not event.shift and not self.fluent_curve['chain']:
                self.ui_management.position_menu_under_previous(self.connector_menu)
                self.ui_management.add_items(self.connector_menu, is_submenu=True)
                refresh_pos = False
            elif action == 'CHAIN_MENU' and not event.shift:
                self.ui_management.position_menu_under_previous(self.chain_menu)
                self.ui_management.add_items(self.chain_menu, is_submenu=True)
                refresh_pos = False
            elif action == 'BACK_MENU' and not event.shift:
                self.ui_management.remove_last_menu(is_submenu=True)
            self.action = action

        # creation de la courbe
        if not self.fluent_curve['added']:
            screen_text = self.put_curve()

        if not events['show_menu'] and self.value_animation['step'] == 'WAIT':
            # basic settings ###############################
            if self.action == 'RADIUS' and not self.fluent_curve['chain']:
                the_modifier = self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes']
                input = 'Input_6'
                if self.enter_value != 'None':
                    screen_text.append([translate('radius'), str(self.enter_value)])
                else:
                    screen_text.append([translate('radius'), str(round(the_modifier[input], 5))])
                screen_text.append([translate('gap'), 'V'])
                screen_text.append([translate('count'), 'B'])

                self.number_adjustment(the_modifier, input, 400, event, 'FLOAT')

                if event.type == 'C' and event.value == 'PRESS':
                    self.ui_management.remove_last_menu()
                    self.ui_management.hide_menu()
                    self.end_of_adjustment()
                    self.action = 'RADIUS'
                    return {'RUNNING_MODAL'}
                if event.type == 'V' and event.value == 'PRESS':
                    self.ui_management.remove_last_menu()
                    self.ui_management.hide_menu()
                    self.end_of_adjustment()
                    self.action = 'ARRAY_GAP'
                    return {'RUNNING_MODAL'}
                if event.type == 'B' and event.value == 'PRESS':
                    self.ui_management.remove_last_menu()
                    self.ui_management.hide_menu()
                    self.end_of_adjustment()
                    self.action = 'ARRAY_COUNT'
                    return {'RUNNING_MODAL'}

            if self.action == 'TILT_01':
                if self.previous_value is None:
                    self.previous_value = self.fluent_curve['curve_obj'].data.splines[0].bezier_points[0].tilt
                    self.slider_origin = event.mouse_region_x
                    self.ui_management.add_items(only_validate_menu())
                    self.ui_management.hide_menu()
                if events['shift_work']:
                    increment = 3000
                elif events['ctrl_work']:
                    increment = 30
                else:
                    increment = 300
                if events['shift_press'] or events['shift_release'] or events['ctrl_press'] or events['ctrl_release']:
                    self.slider_origin = event.mouse_region_x
                    self.previous_value = self.fluent_curve['curve_obj'].data.splines[0].bezier_points[0].tilt

                self.fluent_curve['curve_obj'].data.splines[0].bezier_points[0].tilt = self.previous_value - ((event.mouse_region_x - self.slider_origin)/increment)

            if self.action == 'TILT_02':
                spline = self.fluent_curve['curve_obj'].data.splines[0]
                if self.previous_value is None:
                    self.previous_value = self.fluent_curve['curve_obj'].data.splines[0].bezier_points[-1].tilt
                    self.slider_origin = event.mouse_region_x
                    self.ui_management.add_items(only_validate_menu())
                    self.ui_management.hide_menu()
                if events['shift_work']:
                    increment = 3000
                elif events['ctrl_work']:
                    increment = 30
                else:
                    increment = 300
                if events['shift_press'] or events['shift_release'] or events['ctrl_press'] or events['ctrl_release']:
                    self.slider_origin = event.mouse_region_x
                    self.previous_value = self.fluent_curve['curve_obj'].data.splines[0].bezier_points[len(spline.bezier_points)-1].tilt

                self.fluent_curve['curve_obj'].data.splines[0].bezier_points[-1].tilt = self.previous_value - ((event.mouse_region_x - self.slider_origin)/increment)

            if self.action == 'STIFFNESS':
                if self.previous_value is None:
                    self.previous_value = self.fluent_curve['stiffness']
                    self.slider_origin = event.mouse_region_x
                    self.ui_management.add_items(only_validate_menu())
                    self.ui_management.hide_menu()
                if events['shift_work']:
                    increment = 3000
                elif events['ctrl_work']:
                    increment = 30
                else:
                    increment = 300
                if events['shift_press'] or events['shift_release'] or events['ctrl_press'] or events['ctrl_release']:
                    self.slider_origin = event.mouse_region_x
                    self.previous_value = self.fluent_curve['stiffness']

                self.fluent_curve['stiffness'] = self.previous_value + ((event.mouse_region_x - self.slider_origin)/increment)

                if self.fluent_curve['stiffness'] <= 0:
                    self.fluent_curve['stiffness'] = 0.001

                spline = self.fluent_curve['curve_obj'].data.splines[0]

                a = spline.bezier_points[0]
                b = spline.bezier_points[len(spline.bezier_points)-1]

                # first_vec = Vector((self.fluent_curve['first_point']['normal'][0], self.fluent_curve['first_point']['normal'][1], self.fluent_curve['first_point']['normal'][2]))
                # second_vec = Vector((self.fluent_curve['second_point']['normal'][0], self.fluent_curve['second_point']['normal'][1], self.fluent_curve['second_point']['normal'][2]))
                first_vec = (a.handle_right - a.handle_left).normalized()
                second_vec = (b.handle_left - b.handle_right).normalized()


                a.handle_left = a.co - (self.fluent_curve['stiffness'] * first_vec)
                a.handle_right = a.co + (self.fluent_curve['stiffness'] * first_vec)

                b.handle_left = b.co + (self.fluent_curve['stiffness'] * second_vec)
                b.handle_right = b.co - (self.fluent_curve['stiffness'] * second_vec)

            if self.action == 'CIRCLE_RESOLUTION' and not self.fluent_curve['chain']:
                the_modifier = self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes']
                input = 'Input_27'
                if self.enter_value != 'None':
                    screen_text.append([translate('resolution'), str(self.enter_value)])
                else:
                    screen_text.append([translate('resolution'), str(round(the_modifier[input], 5))])

                self.number_adjustment(the_modifier, input, 10, event, 'INT')

            if self.action == 'CURVE_RESOLUTION':
                if self.previous_value is None:
                    self.previous_value = self.fluent_curve['curve_obj'].data.resolution_u
                    self.slider_origin = event.mouse_region_x
                    self.ui_management.add_items(only_validate_menu())
                    self.ui_management.hide_menu()
                if self.enter_value != 'None':
                    screen_text.append([translate('resolution', upperCase=True), str(self.enter_value)])
                else:
                    screen_text.append([translate('resolution', upperCase=True), str(self.fluent_curve['curve_obj'].data.resolution_u)])
                self.enter_value = enter_value(self.enter_value, events)
                if events['shift_work']:
                    increment = 300
                elif events['ctrl_work']:
                    increment = 3
                else:
                    increment = 30
                if events['shift_press'] or events['shift_release'] or events['ctrl_press'] or events['ctrl_release']:
                    self.slider_origin = event.mouse_region_x
                    self.previous_value = self.fluent_curve['curve_obj'].data.bevel_resolution

                self.fluent_curve['curve_obj'].data.resolution_u = int(self.previous_value + ((event.mouse_region_x - self.slider_origin)/increment))
                if enter_value_validation(self.enter_value, event)[0]:
                    self.do_not = 'QUIT_FLUENT'
                    self.fluent_curve['curve_obj'].data.resolution_u = int(enter_value_validation(self.enter_value, event)[1])
                    self.end_of_adjustment()

            if self.action == 'CURVE_OFFSET':
                the_modifier = self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes']
                the_input = 'Input_7'
                if self.enter_value != 'None':
                    screen_text.append([translate('resolution'), str(self.enter_value)])
                else:
                    screen_text.append([translate('resolution'), str(round(the_modifier[the_input], 5))])

                self.number_adjustment(the_modifier, the_input, 80, event, 'FLOAT')
            # array ######################################
            if self.action == 'ARRAY_COUNT':
                the_modifier = self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes']
                the_input = 'Input_4'
                if self.enter_value != 'None':
                    screen_text.append([translate('count'), str(self.enter_value)])
                else:
                    screen_text.append([translate('count'), str(round(the_modifier[the_input], 5))])
                screen_text.append([translate('radius'), 'C'])
                screen_text.append([translate('gap'), 'V'])

                self.number_adjustment(the_modifier, the_input, 50, event, 'INT')

                if event.type == 'C' and event.value == 'PRESS':
                    self.ui_management.remove_last_menu()
                    self.ui_management.hide_menu()
                    self.end_of_adjustment()
                    self.action = 'RADIUS'
                    return {'RUNNING_MODAL'}
                if event.type == 'V' and event.value == 'PRESS':
                    self.ui_management.remove_last_menu()
                    self.ui_management.hide_menu()
                    self.end_of_adjustment()
                    self.action = 'ARRAY_GAP'
                    return {'RUNNING_MODAL'}
                if event.type == 'B' and event.value == 'PRESS':
                    self.ui_management.remove_last_menu()
                    self.ui_management.hide_menu()
                    self.end_of_adjustment()
                    self.action = 'ARRAY_COUNT'
                    return {'RUNNING_MODAL'}

            if self.action == 'ARRAY_GAP':
                the_modifier = self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes']
                the_input = 'Input_3'
                if self.enter_value != 'None':
                    screen_text.append([translate('gap'), str(self.enter_value)])
                else:
                    screen_text.append([translate('gap'), str(round(the_modifier[the_input], 5))])
                screen_text.append([translate('radius'), 'C'])
                screen_text.append([translate('count'), 'B'])

                self.number_adjustment(the_modifier, the_input, 200, event, 'FLOAT')

                if event.type == 'C' and event.value == 'PRESS':
                    self.ui_management.remove_last_menu()
                    self.ui_management.hide_menu()
                    self.end_of_adjustment()
                    self.action = 'RADIUS'
                    return {'RUNNING_MODAL'}
                if event.type == 'V' and event.value == 'PRESS':
                    self.ui_management.remove_last_menu()
                    self.ui_management.hide_menu()
                    self.end_of_adjustment()
                    self.action = 'ARRAY_GAP'
                    return {'RUNNING_MODAL'}
                if event.type == 'B' and event.value == 'PRESS':
                    self.ui_management.remove_last_menu()
                    self.ui_management.hide_menu()
                    self.end_of_adjustment()
                    self.action = 'ARRAY_COUNT'
                    return {'RUNNING_MODAL'}

            if self.action == 'ARRAY_LINEAR':
                the_modifier = self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes']
                the_input = 'Input_5'
                the_modifier[the_input] = False
                the_modifier.show_viewport = False
                the_modifier.show_viewport = True
                self.action = None

            if self.action == 'ARRAY_CIRCULAR':
                the_modifier = self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes']
                the_input = 'Input_5'
                the_modifier[the_input] = True
                the_modifier.show_viewport = False
                the_modifier.show_viewport = True
                self.action = None

            # coil #######################################
            if self.action == 'COIL_ADD':
                the_modifier = self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes']
                the_input = 'Input_9'
                the_modifier[the_input] = not the_modifier[the_input]
                the_modifier.show_viewport = False
                the_modifier.show_viewport = True
                self.action = None

            if self.action == 'COIL_RADIUS':
                the_modifier = self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes']
                the_input = 'Input_28'
                if self.enter_value != 'None':
                    screen_text.append([translate('radius'), str(self.enter_value)])
                else:
                    screen_text.append([translate('radius'), str(round(the_modifier[the_input], 5))])
                screen_text.append([translate('toggleSpiral'), 'C'])

                self.number_adjustment(the_modifier, the_input, 500, event, 'FLOAT')

                if event.type == 'C' and event.value == 'PRESS':
                    self.ui_management.remove_last_menu()
                    self.ui_management.hide_menu()
                    self.end_of_adjustment()
                    self.action = 'COIL_SPIRAL_RADIUS'
                    return {'RUNNING_MODAL'}

            if self.action == 'COIL_ROTATIONS':
                the_modifier = self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes']
                the_input = 'Input_13'
                if self.enter_value != 'None':
                    screen_text.append([translate('count'), str(self.enter_value)])
                else:
                    screen_text.append([translate('count'), str(round(the_modifier[the_input], 5))])

                self.number_adjustment(the_modifier, the_input, 100, event, 'FLOAT')

            if self.action == 'COIL_SPIRAL_RADIUS':
                the_modifier = self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes']
                the_input = 'Input_14'
                if self.enter_value != 'None':
                    screen_text.append([translate('radius'), str(self.enter_value)])
                else:
                    screen_text.append([translate('radius'), str(round(the_modifier[the_input], 5))])
                screen_text.append([translate('toggleSpiral'), 'C'])

                self.number_adjustment(the_modifier, the_input, 100, event, 'FLOAT')

                if event.type == 'C' and event.value == 'PRESS':
                    self.ui_management.remove_last_menu()
                    self.ui_management.hide_menu()
                    self.end_of_adjustment()
                    self.action = 'COIL_RADIUS'
                    return {'RUNNING_MODAL'}

            if self.action == 'COIL_SPIRAL_RESOLUTION':
                the_modifier = self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes']
                the_input = 'Input_12'
                if self.enter_value != 'None':
                    screen_text.append([translate('resolution'), str(self.enter_value)])
                else:
                    screen_text.append([translate('resolution'), str(round(the_modifier[the_input], 5))])
                self.number_adjustment(the_modifier, the_input, 100, event, 'INT')

            # protection #################################
            if self.action == 'PROTECTION_ADD':
                the_modifier = self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes']
                the_input = 'Input_17'
                the_modifier[the_input] = not the_modifier[the_input]
                the_modifier.show_viewport = False
                the_modifier.show_viewport = True
                self.action = None

            if self.action == 'PROTECTION_SPIRAL_RADIUS':
                the_modifier = self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes']
                the_input = 'Input_18'
                self.number_adjustment(the_modifier, the_input, 300, event, 'FLOAT')
                if self.enter_value != 'None':
                    screen_text.append([translate('radius'), str(self.enter_value)])
                else:
                    screen_text.append([translate('radius'), str(round(the_modifier[the_input], 5))])
                screen_text.append([translate('thickness'), 'C'])

                if event.type == 'C' and event.value == 'PRESS':
                    self.ui_management.remove_last_menu()
                    self.ui_management.hide_menu()
                    self.end_of_adjustment()
                    self.action = 'PROTECTION_THICKNESS'
                    return {'RUNNING_MODAL'}

            if self.action == 'PROTECTION_HEIGHT':
                the_modifier = self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes']
                the_input = 'Input_19'
                self.number_adjustment(the_modifier, the_input, 300, event, 'FLOAT')
                if self.enter_value != 'None':
                    screen_text.append([translate('height'), str(self.enter_value)])
                else:
                    screen_text.append([translate('height'), str(round(the_modifier[the_input], 5))])
                screen_text.append([translate('rotation'), 'C'])

                if event.type == 'C' and event.value == 'PRESS':
                    self.ui_management.remove_last_menu()
                    self.ui_management.hide_menu()
                    self.end_of_adjustment()
                    self.action = 'PROTECTION_ROTATIONS'
                    return {'RUNNING_MODAL'}

            if self.action == 'PROTECTION_ROTATIONS':
                the_modifier = self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes']
                the_input = 'Input_20'
                self.number_adjustment(the_modifier, the_input, 100, event, 'FLOAT')
                if self.enter_value != 'None':
                    screen_text.append([translate('count'), str(self.enter_value)])
                else:
                    screen_text.append([translate('count'), str(round(the_modifier[the_input], 5))])
                screen_text.append([translate('height'), 'C'])

                if event.type == 'C' and event.value == 'PRESS':
                    self.ui_management.remove_last_menu()
                    self.ui_management.hide_menu()
                    self.end_of_adjustment()
                    self.action = 'PROTECTION_HEIGHT'
                    return {'RUNNING_MODAL'}

            if self.action == 'PROTECTION_THICKNESS':
                the_modifier = self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes']
                the_input = 'Input_21'
                self.number_adjustment(the_modifier, the_input, 500, event, 'FLOAT')
                if self.enter_value != 'None':
                    screen_text.append([translate('thickness'), str(self.enter_value)])
                else:
                    screen_text.append([translate('thickness'), str(round(the_modifier[the_input], 5))])
                screen_text.append([translate('radius'), 'C'])

                if event.type == 'C' and event.value == 'PRESS':
                    self.ui_management.remove_last_menu()
                    self.ui_management.hide_menu()
                    self.end_of_adjustment()
                    self.action = 'PROTECTION_SPIRAL_RADIUS'
                    return {'RUNNING_MODAL'}

            if self.action == 'PROTECTION_RESOLUTION':
                the_modifier = self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes']
                the_input = 'Input_22'
                self.number_adjustment(the_modifier, the_input, 10, event, 'INT')
                if self.enter_value != 'None':
                    screen_text.append([translate('resolution'), str(self.enter_value)])
                else:
                    screen_text.append([translate('resolution'), str(round(the_modifier[the_input], 5))])

            # rings ######################################
            if self.action == 'SELECT_RING':
                for i, n in enumerate(self.fluent_curve['ring_nodes']):
                    if n == self.current_ring_node:
                        try:
                            self.current_ring_node = self.fluent_curve['ring_nodes'][i + 1]
                        except:
                            self.current_ring_node = self.fluent_curve['ring_nodes'][0]
                        self.value_animation['input'] = self.current_ring_node.inputs['X Offset']
                        self.value_animation['v0'] = self.current_ring_node.inputs['X Offset'].default_value
                        self.value_animation['t0'] = time.time()
                        self.value_animation['strength'] = 0.02
                        self.value_animation['step'] = 'PROCESS'
                        break
                self.action = None

            if self.action == 'ADD_RING':
                self.add_ring()
                self.action = None

            if self.action == 'RING_MOVE' and self.current_ring_node:
                node = self.current_ring_node
                the_input = node.inputs['X Offset']
                if self.previous_value is None:
                    self.previous_value = the_input.default_value
                    self.slider_origin = event.mouse_region_x
                    self.ui_management.add_items(only_validate_menu())
                    self.ui_management.hide_menu()
                if self.enter_value != 'None':
                    screen_text.append([translate('offset'), str(self.enter_value)])
                else:
                    screen_text.append([translate('offset'), str(round(the_input.default_value, 5))])
                self.enter_value = enter_value(self.enter_value, events)
                if events['shift_work']:
                    increment = 3000
                elif events['ctrl_work']:
                    increment = 30
                else:
                    increment = 300
                if events['shift_press'] or events['shift_release'] or events['ctrl_press'] or events[
                    'ctrl_release']:
                    self.slider_origin = event.mouse_region_x
                    self.previous_value = the_input.default_value

                the_input.default_value = self.previous_value + ((event.mouse_region_x - self.slider_origin) / increment)
                if enter_value_validation(self.enter_value, event)[0]:
                    the_input.default_value = enter_value_validation(self.enter_value, event)[1]
                    self.end_of_adjustment()

            if self.action == 'RING_SCALE' and self.current_ring_node and self.current_ring_node.inputs['Object'].default_value.get('fluent_type') != 'wire_ring':
                node = self.current_ring_node
                the_input = node.inputs['Scale']
                if self.previous_value is None:
                    self.previous_value = the_input.default_value
                    self.slider_origin = event.mouse_region_x
                    self.ui_management.add_items(only_validate_menu())
                    self.ui_management.hide_menu()
                if self.enter_value != 'None':
                    screen_text.append([translate('scale'), str(self.enter_value)])
                else:
                    screen_text.append([translate('scale'), str(round(the_input.default_value, 5))])
                self.enter_value = enter_value(self.enter_value, events)
                if events['shift_work']:
                    increment = 3000
                elif events['ctrl_work']:
                    increment = 30
                else:
                    increment = 300
                if events['shift_press'] or events['shift_release'] or events['ctrl_press'] or events[
                    'ctrl_release']:
                    self.slider_origin = event.mouse_region_x
                    self.previous_value = the_input.default_value

                the_input.default_value = self.previous_value + ((event.mouse_region_x - self.slider_origin) / increment)
                if enter_value_validation(self.enter_value, event)[0]:
                    the_input.default_value = enter_value_validation(self.enter_value, event)[1]
                    self.end_of_adjustment()

            if self.action == 'RING_ARRAY_COUNT' and self.current_ring_node:
                node = self.current_ring_node
                the_input = node.inputs['Count']
                if self.previous_value is None:
                    self.previous_value = the_input.default_value
                    self.slider_origin = event.mouse_region_x
                    self.ui_management.add_items(only_validate_menu())
                    self.ui_management.hide_menu()
                if self.enter_value != 'None':
                    screen_text.append([translate('count'), str(self.enter_value)])
                else:
                    screen_text.append([translate('count'), str(round(the_input.default_value, 5))])
                self.enter_value = enter_value(self.enter_value, events)
                screen_text.append([translate('gap'), 'C'])
                if events['shift_work']:
                    increment = 1000
                elif events['ctrl_work']:
                    increment = 10
                else:
                    increment = 100
                if events['shift_press'] or events['shift_release'] or events['ctrl_press'] or events[
                    'ctrl_release']:
                    self.slider_origin = event.mouse_region_x
                    self.previous_value = the_input.default_value

                the_input.default_value = int(self.previous_value + ((event.mouse_region_x - self.slider_origin) / increment))
                if enter_value_validation(self.enter_value, event)[0]:
                    the_input.default_value = int(enter_value_validation(self.enter_value, event)[1])
                    self.end_of_adjustment()

                if event.type == 'C' and event.value == 'PRESS':
                    self.ui_management.remove_last_menu()
                    self.ui_management.hide_menu()
                    self.end_of_adjustment()
                    self.action = 'RING_ARRAY_GAP'
                    return {'RUNNING_MODAL'}

            if self.action == 'RING_ARRAY_GAP' and self.current_ring_node:
                node = self.current_ring_node
                the_input = node.inputs['Gap']
                if self.previous_value is None:
                    self.previous_value = the_input.default_value
                    self.slider_origin = event.mouse_region_x
                    self.ui_management.add_items(only_validate_menu())
                    self.ui_management.hide_menu()
                if self.enter_value != 'None':
                    screen_text.append([translate('gap'), str(self.enter_value)])
                else:
                    screen_text.append([translate('gap'), str(round(the_input.default_value, 5))])
                self.enter_value = enter_value(self.enter_value, events)
                screen_text.append([translate('count'), 'C'])
                if events['shift_work']:
                    increment = 1000
                elif events['ctrl_work']:
                    increment = 10
                else:
                    increment = 100
                if events['shift_press'] or events['shift_release'] or events['ctrl_press'] or events[
                    'ctrl_release']:
                    self.slider_origin = event.mouse_region_x
                    self.previous_value = the_input.default_value

                the_input.default_value = self.previous_value + ((event.mouse_region_x - self.slider_origin) / increment)
                if enter_value_validation(self.enter_value, event)[0]:
                    the_input.default_value = enter_value_validation(self.enter_value, event)[1]
                    self.end_of_adjustment()

                if event.type == 'C' and event.value == 'PRESS':
                    self.ui_management.remove_last_menu()
                    self.ui_management.hide_menu()
                    self.end_of_adjustment()
                    self.action = 'RING_ARRAY_COUNT'
                    return {'RUNNING_MODAL'}

            if self.action == 'RING_LENGTH' and self.current_ring_node and self.current_ring_node.inputs['Object'].default_value.get('fluent_type') == 'wire_ring':
                node = self.current_ring_node
                ring_obj = node.inputs['Object'].default_value
                the_input = ring_obj.modifiers['Length']
                if self.previous_value is None:
                    self.previous_value = the_input.screw_offset
                    self.slider_origin = event.mouse_region_x
                    self.ui_management.add_items(only_validate_menu())
                    self.ui_management.hide_menu()
                if self.enter_value != 'None':
                    screen_text.append([translate('length'), str(self.enter_value)])
                else:
                    screen_text.append([translate('length'), str(round(the_input.screw_offset, 5))])
                self.enter_value = enter_value(self.enter_value, events)
                if events['shift_work']:
                    increment = 3000
                elif events['ctrl_work']:
                    increment = 30
                else:
                    increment = 300
                if events['shift_press'] or events['shift_release'] or events['ctrl_press'] or events[
                    'ctrl_release']:
                    self.slider_origin = event.mouse_region_x
                    self.previous_value = the_input.screw_offset

                the_input.screw_offset = self.previous_value + ((event.mouse_region_x - self.slider_origin) / increment)
                if enter_value_validation(self.enter_value, event)[0]:
                    the_input.screw_offset = enter_value_validation(self.enter_value, event)[1]
                    self.end_of_adjustment()

            if self.action == 'RING_L_RESOLUTION' and self.current_ring_node and self.current_ring_node.inputs['Object'].default_value.get('fluent_type') == 'wire_ring':
                node = self.current_ring_node
                ring_obj = node.inputs['Object'].default_value
                the_input = ring_obj.modifiers['Length']
                if self.previous_value is None:
                    self.previous_value = the_input.steps
                    self.slider_origin = event.mouse_region_x
                    self.ui_management.add_items(only_validate_menu())
                    self.ui_management.hide_menu()
                if self.enter_value != 'None':
                    screen_text.append([translate('length'), str(self.enter_value)])
                else:
                    screen_text.append([translate('length'), str(round(the_input.steps, 5))])
                self.enter_value = enter_value(self.enter_value, events)
                if events['shift_work']:
                    increment = 500
                elif events['ctrl_work']:
                    increment = 5
                else:
                    increment = 50
                if events['shift_press'] or events['shift_release'] or events['ctrl_press'] or events[
                    'ctrl_release']:
                    self.slider_origin = event.mouse_region_x
                    self.previous_value = the_input.steps

                the_input.steps = the_input.render_steps = int(self.previous_value + ((event.mouse_region_x - self.slider_origin) / increment))
                if enter_value_validation(self.enter_value, event)[0]:
                    the_input.steps = the_input.render_steps = int(enter_value_validation(self.enter_value, event)[1])
                    self.end_of_adjustment()

            if self.action == 'RING_RADIUS' and self.current_ring_node and self.current_ring_node.inputs['Object'].default_value.get('fluent_type') == 'wire_ring':
                node = self.current_ring_node
                ring_obj = node.inputs['Object'].default_value
                the_input = ring_obj.modifiers['Radius']
                if self.previous_value is None:
                    self.previous_value = the_input.strength
                    self.slider_origin = event.mouse_region_x
                    self.ui_management.add_items(only_validate_menu())
                    self.ui_management.hide_menu()
                if self.enter_value != 'None':
                    screen_text.append([translate('length'), str(self.enter_value)])
                else:
                    screen_text.append([translate('length'), str(round(the_input.strength, 5))])
                screen_text.append([translate('sameAsWire'), 'C'])
                self.enter_value = enter_value(self.enter_value, events)
                if events['shift_work']:
                    increment = 500
                elif events['ctrl_work']:
                    increment = 5
                else:
                    increment = 50
                if events['shift_press'] or events['shift_release'] or events['ctrl_press'] or events[
                    'ctrl_release']:
                    self.slider_origin = event.mouse_region_x
                    self.previous_value = the_input.strength

                the_input.strength = self.previous_value + ((event.mouse_region_x - self.slider_origin) / increment)
                if enter_value_validation(self.enter_value, event)[0]:
                    the_input.strength = enter_value_validation(self.enter_value, event)[1]
                    self.end_of_adjustment()
                if events['type'] == 'C' and events['value'] == 'PRESS':
                    radius = self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes']['Input_6']
                    the_input.strength = radius * 2

                    self.end_of_adjustment()

            if self.action == 'RING_THICKNESS' and self.current_ring_node and self.current_ring_node.inputs['Object'].default_value.get('fluent_type') == 'wire_ring':
                node = self.current_ring_node
                ring_obj = node.inputs['Object'].default_value
                the_input = ring_obj.modifiers['Thickness']
                if self.previous_value is None:
                    self.previous_value = the_input.thickness
                    self.slider_origin = event.mouse_region_x
                    self.ui_management.add_items(only_validate_menu())
                    self.ui_management.hide_menu()
                if self.enter_value != 'None':
                    screen_text.append([translate('length'), str(self.enter_value)])
                else:
                    screen_text.append([translate('length'), str(round(the_input.thickness, 5))])
                screen_text.append([translate('sameAsWire'), 'C'])
                self.enter_value = enter_value(self.enter_value, events)
                if events['shift_work']:
                    increment = 5000
                elif events['ctrl_work']:
                    increment = 50
                else:
                    increment = 500
                if events['shift_press'] or events['shift_release'] or events['ctrl_press'] or events[
                    'ctrl_release']:
                    self.slider_origin = event.mouse_region_x
                    self.previous_value = the_input.thickness

                the_input.thickness = self.previous_value + ((event.mouse_region_x - self.slider_origin) / increment)
                if enter_value_validation(self.enter_value, event)[0]:
                    the_input.thickness = enter_value_validation(self.enter_value, event)[1]
                    self.end_of_adjustment()

            if self.action == 'RING_BEVEL' and self.current_ring_node and self.current_ring_node.inputs['Object'].default_value.get('fluent_type') == 'wire_ring':
                node = self.current_ring_node
                ring_obj = node.inputs['Object'].default_value
                the_input = ring_obj.modifiers['Bevel']
                if self.previous_value is None:
                    self.previous_value = the_input.width
                    self.slider_origin = event.mouse_region_x
                    self.ui_management.add_items(only_validate_menu())
                    self.ui_management.hide_menu()
                if self.enter_value != 'None':
                    screen_text.append([translate('length'), str(self.enter_value)])
                else:
                    screen_text.append([translate('length'), str(round(the_input.width, 5))])
                screen_text.append([translate('convexStraight'), 'C'])
                self.enter_value = enter_value(self.enter_value, events)
                if events['shift_work']:
                    increment = 8000
                elif events['ctrl_work']:
                    increment = 80
                else:
                    increment = 800
                if events['shift_press'] or events['shift_release'] or events['ctrl_press'] or events[
                    'ctrl_release']:
                    self.slider_origin = event.mouse_region_x
                    self.previous_value = the_input.width

                if event.type == 'C' and event.value == 'PRESS':
                    if the_input.segments == 1:
                        the_input.segments = auto_bevel_segments(the_input)
                    else:
                        the_input.segments = 1
                the_input.width = self.previous_value + ((event.mouse_region_x - self.slider_origin) / increment)
                if enter_value_validation(self.enter_value, event)[0]:
                    the_input.width = enter_value_validation(self.enter_value, event)[1]
                    self.end_of_adjustment()

            if self.action == 'RING_C_RESOLUTION' and self.current_ring_node and self.current_ring_node.inputs['Object'].default_value.get('fluent_type') == 'wire_ring':
                node = self.current_ring_node
                ring_obj = node.inputs['Object'].default_value
                the_input = ring_obj.modifiers['Screw']
                if self.previous_value is None:
                    self.previous_value = the_input.steps
                    self.slider_origin = event.mouse_region_x
                    self.ui_management.add_items(only_validate_menu())
                    self.ui_management.hide_menu()
                if self.enter_value != 'None':
                    screen_text.append([translate('length'), str(self.enter_value)])
                else:
                    screen_text.append([translate('length'), str(round(the_input.steps, 5))])
                self.enter_value = enter_value(self.enter_value, events)
                if events['shift_work']:
                    increment = 500
                elif events['ctrl_work']:
                    increment = 5
                else:
                    increment = 50
                if events['shift_press'] or events['shift_release'] or events['ctrl_press'] or events[
                    'ctrl_release']:
                    self.slider_origin = event.mouse_region_x
                    self.previous_value = the_input.steps

                the_input.steps = the_input.render_steps = int(self.previous_value + ((event.mouse_region_x - self.slider_origin) / increment))
                if enter_value_validation(self.enter_value, event)[0]:
                    the_input.steps = the_input.render_steps = int(enter_value_validation(self.enter_value, event)[1])
                    self.end_of_adjustment()

            if self.action == 'RING_REMOVE' and self.current_ring_node:
                geo_node = self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes'].node_group
                if self.current_ring_node.inputs['Object'].default_value.get('fluent_type') == 'wire_ring':
                    bpy.data.objects.remove(self.current_ring_node.inputs['Object'].default_value, do_unlink=True)
                else:
                    original_name = self.current_ring_node.inputs['Object'].default_value.name
                    save = duplicate(self.current_ring_node.inputs['Object'].default_value)
                    bpy.data.objects.remove(self.current_ring_node.inputs['Object'].default_value, do_unlink=True)
                    save.name = original_name
                geo_node.nodes.remove(self.current_ring_node)
                self.current_ring_node = None
                self.fluent_curve['ring_nodes'] = []
                for n in geo_node.nodes:
                    if n.type == 'GROUP' and n.node_tree.name == 'f_add_ring' and n.inputs['Object'].default_value:
                        self.fluent_curve['ring_nodes'].append(n)
                if len(self.fluent_curve['ring_nodes']):
                    self.current_ring_node = self.fluent_curve['ring_nodes'][-1]
                self.action = None

            # duct ##########################################################
            if self.action == 'DUCT_ADD':
                the_modifier = self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes']
                the_input = 'Input_25'
                if the_modifier[the_input]:
                    the_modifier[the_input] = None
                    the_modifier['Input_6'] = 0.05
                    self.fluent_curve['curve_obj'].modifiers.remove(self.fluent_curve['curve_obj'].modifiers[fluent_modifiers_name['weld']])
                    # réaffiche le bevel
                    # try:
                    #     bevel = self.fluent_curve['curve_obj'].modifiers[fluent_modifiers_name['outer_bevel']]
                    #     bevel.show_render = bevel.show_viewport = True
                    # except: pass
                else:
                    self.add_duct()
                    the_modifier['Input_6'] = 0.0
                    the_modifier.show_viewport = False
                    the_modifier.show_viewport = True
                self.action = None

            if self.action == 'DUCT_RATIO':
                duct_obj = self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes']['Input_25']
                if duct_obj:
                    gn_modifier = duct_obj.modifiers['duct']
                    if self.previous_value is None:
                        self.previous_value = gn_modifier['Input_1']
                        self.slider_origin = event.mouse_region_x
                        self.ui_management.hide_menu()
                        self.ui_management.add_items(only_validate_menu())
                        self.ui_management.hide_menu()
                    if self.enter_value != 'None':
                        screen_text.append([translate('ratio'), str(self.enter_value)])
                    else:
                        screen_text.append([translate('ratio'), str(round(gn_modifier['Input_1'], 5))])
                    self.enter_value = enter_value(self.enter_value, events)
                    screen_text.append([translate('radius'), 'C'])
                    if events['shift_work']:
                        increment = 3000
                    elif events['ctrl_work']:
                        increment = 30
                    else:
                        increment = 300
                    if events['shift_press'] or events['shift_release'] or events['ctrl_press'] or \
                            events['ctrl_release']:
                        self.slider_origin = event.mouse_region_x
                        self.previous_value = gn_modifier['Input_1']

                    gn_modifier['Input_1'] = self.previous_value + ((event.mouse_region_x - self.slider_origin) / increment)
                    if enter_value_validation(self.enter_value, event)[0]:
                        gn_modifier['Input_1'] = enter_value_validation(self.enter_value, event)[1]
                        self.end_of_adjustment()

                    if event.type == 'C' and event.value == 'PRESS':
                        self.ui_management.remove_last_menu()
                        self.ui_management.hide_menu()
                        self.end_of_adjustment()
                        self.action = 'DUCT_RADIUS'
                        return {'RUNNING_MODAL'}

                    if gn_modifier['Input_1'] < 0:
                        gn_modifier['Input_1'] = 0.0
                    if gn_modifier['Input_1'] > 1:
                        gn_modifier['Input_1'] = 1.0

                    gn_modifier.show_viewport = False
                    gn_modifier.show_viewport = True

            if self.action == 'DUCT_LENGTH':
                duct_obj = self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes']['Input_25']
                if duct_obj:
                    gn_modifier = duct_obj.modifiers['duct']
                    if self.previous_value is None:
                        self.previous_value = gn_modifier['Input_0']
                        self.slider_origin = event.mouse_region_x
                        self.ui_management.hide_menu()
                        self.ui_management.add_items(only_validate_menu())
                        self.ui_management.hide_menu()
                    if self.enter_value != 'None':
                        screen_text.append([translate('length'), str(self.enter_value)])
                    else:
                        screen_text.append([translate('length'), str(round(gn_modifier['Input_0'], 5))])
                    self.enter_value = enter_value(self.enter_value, events)
                    if events['shift_work']:
                        increment = 3000
                    elif events['ctrl_work']:
                        increment = 30
                    else:
                        increment = 300
                    if events['shift_press'] or events['shift_release'] or events['ctrl_press'] or \
                            events['ctrl_release']:
                        self.slider_origin = event.mouse_region_x
                        self.previous_value = gn_modifier['Input_0']

                    gn_modifier['Input_0'] = self.previous_value + ((event.mouse_region_x - self.slider_origin) / increment)
                    if enter_value_validation(self.enter_value, event)[0]:
                        gn_modifier['Input_0'] = enter_value_validation(self.enter_value, event)[1]
                        self.end_of_adjustment()

                    gn_modifier.show_viewport = False
                    gn_modifier.show_viewport = True

            if self.action == 'DUCT_RADIUS':
                duct_obj = self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes']['Input_25']
                if duct_obj:
                    gn_modifier = duct_obj.modifiers['duct']
                    radius_1 = 'Input_4'
                    radius_2 = 'Input_3'
                    if self.previous_value is None:
                        self.adjust_me = radius_1
                        self.previous_value = gn_modifier[self.adjust_me]
                        self.slider_origin = event.mouse_region_x
                        self.ui_management.hide_menu()
                        self.ui_management.add_items(only_validate_menu())
                        self.ui_management.hide_menu()
                    if self.enter_value != 'None':
                        screen_text.append([translate('radius'), str(self.enter_value)])
                    else:
                        screen_text.append([translate('radius'), str(round(gn_modifier[self.adjust_me], 5))])
                    screen_text.append([translate('otherRadius'), 'C'])
                    self.enter_value = enter_value(self.enter_value, events)
                    screen_text.append([translate('ratio'), 'V'])
                    if events['shift_work']:
                        increment = 3000
                    elif events['ctrl_work']:
                        increment = 30
                    else:
                        increment = 300
                    if events['shift_press'] or events['shift_release'] or events['ctrl_press'] or \
                            events['ctrl_release']:
                        self.slider_origin = event.mouse_region_x
                        self.previous_value = gn_modifier[self.adjust_me]

                    if events['type'] == 'C' and events['value'] == 'PRESS':
                        if self.adjust_me == radius_1:
                            self.adjust_me = radius_2
                        elif self.adjust_me == radius_2:
                            self.adjust_me = radius_1
                        self.previous_value = gn_modifier[self.adjust_me]
                        self.slider_origin = event.mouse_region_x

                    gn_modifier[self.adjust_me] = self.previous_value + ((event.mouse_region_x - self.slider_origin) / increment)
                    if enter_value_validation(self.enter_value, event)[0]:
                        gn_modifier[self.adjust_me] = enter_value_validation(self.enter_value, event)[1]
                        self.end_of_adjustment()

                    gn_modifier.show_viewport = False
                    gn_modifier.show_viewport = True

                    if event.type == 'V' and event.value == 'PRESS':
                        self.ui_management.remove_last_menu()
                        self.ui_management.hide_menu()
                        self.end_of_adjustment()
                        self.action = 'DUCT_RATIO'
                        return {'RUNNING_MODAL'}

            if self.action == 'DUCT_BEVEL':
                duct_obj = self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes']['Input_25']
                if duct_obj:
                    gn_modifier = duct_obj.modifiers['duct']
                    if self.previous_value is None:
                        self.previous_value = gn_modifier['Input_6']
                        self.slider_origin = event.mouse_region_x
                        self.ui_management.hide_menu()
                        self.ui_management.add_items(only_validate_menu())
                        self.ui_management.hide_menu()
                    if self.enter_value != 'None':
                        screen_text.append([translate('length'), str(self.enter_value)])
                    else:
                        screen_text.append([translate('length'), str(round(gn_modifier['Input_6'], 5))])
                    self.enter_value = enter_value(self.enter_value, events)
                    if events['shift_work']:
                        increment = 3000
                    elif events['ctrl_work']:
                        increment = 30
                    else:
                        increment = 300
                    if events['shift_press'] or events['shift_release'] or events['ctrl_press'] or \
                            events['ctrl_release']:
                        self.slider_origin = event.mouse_region_x
                        self.previous_value = gn_modifier['Input_6']

                    gn_modifier['Input_6'] = self.previous_value + ((event.mouse_region_x - self.slider_origin) / increment)
                    if enter_value_validation(self.enter_value, event)[0]:
                        gn_modifier['Input_6'] = enter_value_validation(self.enter_value, event)[1]
                        self.end_of_adjustment()

                    gn_modifier.show_viewport = False
                    gn_modifier.show_viewport = True
            # chain #########################################################
            if self.action == 'CHAIN_ADD':
                self.add_chain()
                self.action = None

            # if self.action == 'CHAIN_OFFSET' and self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes'].node_group.name == '.f_chain':
            #     the_modifier = self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes']
            #     input = 'Input_5'
            #     if self.enter_value != 'None':
            #         screen_text.append([translate('offset'), str(self.enter_value)])
            #     else:
            #         screen_text.append([translate('offset'), str(round(the_modifier[input], 5))])
            #
            #     self.number_adjustment(the_modifier, input, 100, event, 'FLOAT')

            if self.action == 'CHAIN_SIZE' and self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes'].node_group.name == '.f_chain':
                the_modifier = self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes']
                if bpy.app.version >= (4, 0, 0):
                    input = 'Socket_2'
                else:
                    input = 'Input_5'
                if self.enter_value != 'None':
                    screen_text.append([translate('length'), str(self.enter_value)])
                else:
                    screen_text.append([translate('length'), str(round(the_modifier[input], 5))])

                if bpy.app.version >= (4, 0, 0):
                    screen_text.append([translate('width'), str(round(the_modifier['Socket_3'], 5))])
                else:
                    screen_text.append([translate('width'), str(round(the_modifier['Input_2'], 5))])

                screen_text.append([translate('toggleLengthWidth'), 'C'])

                self.number_adjustment(the_modifier, input, 800, event, 'FLOAT', min = 0.02)

                if event.type == 'C' and event.value == 'PRESS':
                    if bpy.app.version >= (4, 0, 0):
                        self.previous_value = the_modifier['Socket_3']
                    else:
                        self.previous_value = the_modifier['Input_2']
                    self.slider_origin = event.mouse_region_x
                    self.action = 'CHAIN_SIZE_Y'
                    return {'RUNNING_MODAL'}

            if self.action == 'CHAIN_SIZE_Y' and self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes'].node_group.name == '.f_chain':
                the_modifier = self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes']
                if bpy.app.version >= (4, 0, 0):
                    input = 'Socket_3'
                else:
                    input = 'Input_2'
                if bpy.app.version >= (4, 0, 0):
                    screen_text.append([translate('length'), str(round(the_modifier['Socket_2'], 5))])
                else:
                    screen_text.append([translate('length'), str(round(the_modifier['Input_1'], 5))])
                if self.enter_value != 'None':
                    screen_text.append([translate('width'), str(self.enter_value)])
                else:
                    screen_text.append([translate('width'), str(round(the_modifier[input], 5))])

                screen_text.append([translate('toggleLengthWidth'), 'C'])

                self.number_adjustment(the_modifier, input, 800, event, 'FLOAT', 0.02)

                if event.type == 'C' and event.value == 'PRESS':
                    self.previous_value = the_modifier['Socket_2']
                    self.slider_origin = event.mouse_region_x
                    self.action = 'CHAIN_SIZE'
                    return{'RUNNING_MODAL'}

            if self.action == 'CHAIN_THICKNESS' and self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes'].node_group.name == '.f_chain':
                the_modifier = self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes']
                if bpy.app.version >= (4, 0, 0):
                    input = 'Socket_5'
                else:
                    input = 'Input_4'
                if self.enter_value != 'None':
                    screen_text.append([translate('thickness'), str(self.enter_value)])
                else:
                    screen_text.append([translate('thickness'), str(round(the_modifier[input], 5))])

                if bpy.app.version >= (4, 0, 0):
                    self.number_adjustment(the_modifier, input, 3000, event, 'FLOAT', min=0.001, max=the_modifier['Socket_2']/2)
                else:
                    self.number_adjustment(the_modifier, input, 3000, event, 'FLOAT', min=0.001, max=the_modifier['Input_2'] / 2)


            if self.action == 'CHAIN_SCALE' and self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes'].node_group.name == '.f_chain':
                the_modifier = self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes']
                if bpy.app.version >= (4, 0, 0):
                    input = 'Socket_6'
                else:
                    input = 'Input_5'
                if self.enter_value != 'None':
                    screen_text.append([translate('scale'), str(self.enter_value)])
                else:
                    screen_text.append([translate('scale'), str(round(the_modifier[input], 5))])

                self.number_adjustment(the_modifier, input, 800, event, 'FLOAT')

            if self.action == 'CHAIN_BEVEL' and self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes'].node_group.name == '.f_chain':
                the_modifier = self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes']
                if bpy.app.version >= (4, 0, 0):
                    input = 'Socket_4'
                else:
                    input = 'Input_3'
                if self.enter_value != 'None':
                    screen_text.append([translate('radius'), str(self.enter_value)])
                else:
                    screen_text.append([translate('radius'), str(round(the_modifier[input], 5))])

                self.number_adjustment(the_modifier, input, 1000, event, 'FLOAT')

        # chain ########################################
        if self.action == 'CHAIN_PICK_WAITING' and event.type == 'ESC' and event.value == 'PRESS':
            self.action = None

        if self.action == 'CHAIN_PICK_WAITING' and event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            obj = None
            obj = click_on(event.mouse_region_x, event.mouse_region_y)
            if obj:
                self.add_your_chain_link(obj)
                self.action = None

        if self.action == 'CHAIN_PICK_WAITING':
            screen_text.append([translate('pick'), translate('leftClick')])
            screen_text.append([translate('cancel'), translate('escape')])

        if self.action == 'CHAIN_PICK':
            screen_text.append([translate('pick'), translate('leftClick')])
            screen_text.append([translate('cancel'), translate('escape')])
            self.action = 'CHAIN_PICK_WAITING'
        # ring #########################################
        if self.action == 'RING_PICK':
            screen_text.append([translate('pick'), translate('leftClick')])
            screen_text.append([translate('cancel'), translate('escape')])
            if event.type == 'ESC' and event.value == 'PRESS':
                self.action = None

        if self.action == 'RING_PICK_WAITING' and event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            obj = None
            obj = click_on(event.mouse_region_x, event.mouse_region_y)
            if obj:
                self.add_ring(obj)
                self.action = None

        if self.action == 'RING_PICK':
            self.action = 'RING_PICK_WAITING'
        # connector ##################################
        if self.action == 'CONNECTOR_PICK':
            screen_text.append([translate('pick'), translate('leftClick')])
            screen_text.append([translate('cancel'), translate('escape')])
            if event.type == 'ESC' and event.value == 'PRESS':
                self.action = None

        if self.action == 'CONNECTOR_REMOVE':
            the_modifier = self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes']
            the_modifier['Input_1'] = None
            the_modifier.show_viewport = False
            the_modifier.show_viewport = True
            self.action = None

        if self.action == 'CONNECTOR_SCALE' and not events['show_menu']:
            the_modifier = self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes']
            the_input = 'Input_33'
            if self.enter_value != 'None':
                screen_text.append([translate('scale'), str(self.enter_value)])
            else:
                screen_text.append([translate('scale'), str(round(the_modifier[the_input], 5))])

            self.number_adjustment(the_modifier, the_input, 400, event, 'FLOAT')

        if self.action == 'CONNECTOR_PICK_WAITING' and event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            obj = None
            obj = click_on(event.mouse_region_x, event.mouse_region_y)
            if obj:
                geo_node = self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes']
                geo_node['Input_1'] = obj
                if len(obj.material_slots):
                    geo_node['Input_46'] = obj.material_slots[0].material
                self.action = None
                geo_node.show_viewport = False
                geo_node.show_viewport = True

        if self.action == 'CONNECTOR_PICK':
            self.action = 'CONNECTOR_PICK_WAITING'
        # utilities ####################################

        if self.action == 'REUSE_WAITNG' and event.value == 'PRESS' and event.type == 'LEFTMOUSE':
            obj_source = click_on(event.mouse_region_x, event.mouse_region_y, search='CURVE')
            if obj_source and obj_source.get('fluent_type') == 'wire':
                self.action = None
                the_modifier_source = obj_source.modifiers['.f_geometry_nodes']
                if the_modifier_source:
                    the_modifier = self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes']
                    if the_modifier_source.node_group.name == '.f_chain':
                        self.add_chain()
                        copy_gn_mod_inputs(the_modifier, obj_source)
                    else:
                        copy_gn_mod_inputs(the_modifier, obj_source)

                    the_modifier.show_viewport = False
                    the_modifier.show_viewport = True
                try:
                    mirror_source = obj_source.modifiers[fluent_modifiers_name['mirror']]
                    mirror_data = get_modifier_values(mirror_source)
                    mirror_mod = None
                    try:
                        mirror_mod = self.fluent_curve['curve_obj'].modifiers[fluent_modifiers_name['mirror']]
                    except: pass

                    if mirror_mod is None:
                        mirror = mirror_management(self.fluent_curve['curve_obj'], None)
                        mirror.add_mirror(None)
                    set_modifier_value(self.fluent_curve['curve_obj'].modifiers[fluent_modifiers_name['mirror']], mirror_data)
                except:pass

        if self.action == 'REUSE':
            self.action = 'REUSE_WAITNG'

        if self.action == 'REUSE_WAITNG':
            screen_text.append([translate('pickWire'), translate('leftClick')])
            screen_text.append([translate('cancel'), translate('escape')])

        if self.action == 'RESET':
            bpy.data.objects.remove(self.fluent_curve['curve_obj'], do_unlink=True)
            self.fluent_curve['added'] = False
            self.put_curve(True)
            self.action = None

        if event.value == 'PRESS' and event.type == 'W' and self.fluent_curve['curve_obj']:
            if self.fluent_curve['curve_obj'].show_wire:
                self.fluent_curve['curve_obj'].show_wire = False
                try:
                    self.fluent_curve['wire_obj'].show_wire = False
                except:pass
            else:
                self.fluent_curve['curve_obj'].show_wire = True
                try:
                    self.fluent_curve['wire_obj'].show_wire = True
                except:pass

        # simulation #######################################
        if self.action == 'SIMULATION':
            copy = duplicate(self.fluent_curve['curve_obj'])
            self.fluent_curve['curve_obj'].hide_set(True)
            copy.data.bevel_depth = 0
            copy.data.resolution_u = int(256 * copy.data.splines[0].calc_length())
            edge_length = copy.data.splines[0].calc_length() / copy.data.resolution_u
            cable_radius = .05
            if self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes'].node_group.name != '.f_chain':
                cable_radius = self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes']['Input_6']
                if self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes']['Input_25']:
                    object_design = self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes']['Input_25']
                    if object_design and 'f_duct' and object_design.data.name:
                        cable_radius = object_design.modifiers['duct']['Input_4'] / 100
                # conserve le décalage du à d'éventuels connecteurs
                node_tree = self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes'].node_group
                nodes = node_tree.nodes
                for n in nodes:
                    if n.name == 'connector_offset':
                        node_offset = n
                    if n.type == 'GROUP_OUTPUT':
                        node_output = n
                link = node_tree.links.new
                link(node_offset.outputs[0], node_output.inputs[0])
            active_object('SET', copy, True)
            for i in range(len(copy.modifiers)-1):
                copy.modifiers.remove(copy.modifiers[0])
            bpy.ops.object.convert(target='MESH')

            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.mesh.select_mode(type='VERT')
            bpy.ops.object.mode_set(mode='OBJECT')

            copy.data.vertices[0].select = True
            copy.data.vertices[len(copy.data.vertices) - 1].select = True

            if not cable_radius:
                cable_radius = 0.05
            gradient = int(cable_radius * 2 / edge_length * 2) +1
            if gradient < 20:
                gradient = 20


            bpy.ops.object.mode_set(mode='EDIT')
            if cable_radius:
                for i in range(gradient - 1):
                    bpy.ops.mesh.select_more()

            self.action = 'SET_GRADIENT'

        if self.action == 'SET_GRADIENT':
            screen_text.append([translate('pinGroup'), ''])
            screen_text.append([translate('extendReducePin'), 'C/V'])
            screen_text.append([translate('startSimulation'), translate('enter')])
            if bpy.context.active_object.mode == 'EDIT' and (event.value == 'PRESS' and event.type in {'RET', 'NUMPAD_ENTER'}):
                self.action = 'START_SIMULATION'
            if bpy.context.active_object.mode == 'EDIT' and (event.type in ['C', 'V'] and event.value == 'PRESS'):
                if event.type == 'C' and event.value == 'PRESS':
                    bpy.ops.mesh.select_more()
                elif event.type == 'V' and event.value == 'PRESS':
                    bpy.ops.mesh.select_less()

        if self.action == 'START_SIMULATION':
            obj = active_object('GET')
            bpy.ops.object.mode_set(mode='OBJECT')
            obj.vertex_groups.new(name='pin')
            pin_vertices = [v.index for v in obj.data.vertices if v.select]
            gradient = int(len(pin_vertices) / 2)

            for i in range(gradient):
                x = (i) / (gradient - 1)
                d = 3.88
                a = 0.39
                b = 0.05
                c = 0.224
                weight = d * math.pow(x-a, 3) + b*x+c
                pin_vertices = [v.index for v in obj.data.vertices if v.select]
                obj.vertex_groups['pin'].add(pin_vertices, weight, 'REPLACE')

                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_less()
                bpy.ops.object.mode_set(mode='OBJECT')

            pin_vertices = [v.index for v in obj.data.vertices if v.select]
            obj.vertex_groups['pin'].add(pin_vertices, 1, 'REPLACE')

            cloth_mod = obj.modifiers.new(type='CLOTH', name='Cloth')
            cloth_mod.settings.vertex_group_mass = "pin"
            cloth_mod.settings.time_scale = 4
            cloth_mod.settings.pin_stiffness = 1

            if bpy.context.scene.frame_end < 100:
                bpy.context.scene.frame_end = 100

            bpy.context.scene.frame_set(0)
            bpy.ops.screen.animation_play()

            self.action = 'SIM_IN_PROGRESS'

        if self.action == 'SIM_IN_PROGRESS':
            if bpy.context.scene.frame_current >= 100:
                bpy.ops.screen.animation_cancel(restore_frame=False)
                bpy.ops.object.convert(target='CURVE')
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.curve.spline_type_set(type='BEZIER')
                bpy.ops.curve.handle_type_set(type='AUTOMATIC')
                bpy.ops.curve.decimate(ratio=0.025)
                bpy.ops.object.mode_set(mode='OBJECT')

                original_wire = self.fluent_curve['curve_obj']
                self.fluent_curve['curve_obj'] = active_object('GET')
                self.load_geometry_node()
                node_wire = self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes']

                if original_wire.modifiers['.f_geometry_nodes'].node_group.name != '.f_chain':
                    # reconnecte la sortie
                    node_tree = node_wire.node_group
                    nodes = node_tree.nodes
                    for n in nodes:
                        if n.name == 'last':
                            node_last = n
                        if n.type == 'GROUP_OUTPUT':
                            node_output = n
                    link = node_tree.links.new
                    link(node_last.outputs[0], node_output.inputs[0])

                    the_modifier_original = original_wire.modifiers['.f_geometry_nodes']
                    the_modifier = self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes']
                    copy_gn_mod_inputs(the_modifier, original_wire)

                    node_wire['Input_31'] = 1 - original_wire.modifiers['.f_geometry_nodes']['Input_7']
                    node_wire['Input_7'] = 0.000001
                else:
                    self.add_chain()
                    the_modifier = self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes']
                    copy_gn_mod_inputs(the_modifier, original_wire)

                self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes'].show_viewport = False
                self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes'].show_viewport = True

                bpy.data.objects.remove(original_wire, do_unlink=True)
                self.fluent_curve['curve_obj'].data.bevel_depth = 0
                bpy.ops.object.shade_smooth()

                self.action = None

        # sortie ##############################################
        if self.action == 'CANCELLED':
            if self.operation == 'ADD':
                try:
                    bpy.data.objects.remove(self.fluent_curve['curve_obj'], do_unlink=True)
                except:
                    pass
            context.window_manager.event_timer_remove(self.timer)
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            return {'FINISHED'}

        if self.fluent_curve['added'] and (event.value == 'PRESS' and event.type == 'RIGHTMOUSE' and bpy.context.active_object.mode == 'OBJECT') or action == 'FINISHED':
            self.fluent_curve['ring_nodes'] = []
            self.fluent_curve['curve_obj']['fluent_wire_data'] = self.fluent_curve
            self.fluent_curve['curve_obj']['fluent_type'] = 'wire'
            try:
                bpy.data.collections['Wire_Objects'].objects.link(self.fluent_curve['curve_obj'])
                bpy.context.scene.collection.objects.unlink(self.fluent_curve['curve_obj'])
            except:pass
            context.window_manager.event_timer_remove(self.timer)
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            return {'FINISHED'}

        self.ui_management.refresh_side_infos(screen_text)

        # gestion affichage du pie menu
        self.ui_management.toggle_menu_displaying(refresh_pos)

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        self.fluent_curve = {
            'added': False,
            'curve_obj': None,
            'stiffness': 0.5,
            'ring_nodes': [],
            'first_point': None,
            'second_point': None,
            'chain': False
        }
        self.adjustment = None

        self.build_step = None

        self.wire_style = None

        self.mirror = None
        self.statut = None

        self.simulation_data = {
        'bevel_depth':0,
        'bevel_resolution':0
        }

        self.current_ring_node = None

        # affichage
        self.ui_management = FLUENT_ui_management(event)
        self.ui_management.add_dots_items()

        self.value_animation = {
            'input':None,
            'v0':None,
            't0': None,
            'strength':0.1,
            'step':'WAIT' # WAIT ou RUNNING
        }

        self.display_menu = None
        self.action = None
        self.previous_value = None
        self.adjust_me = None
        self.slider_origin = None
        self.other_adjustment = None
        self.enter_value = 'None'

        self.previous_radius = None

        self.cast = None
        self.snap_face_center = True

        self.wire_menu = wire_ui()
        self.wire_ring_menu = wire_ring_ui()
        self.array_menu = wire_array_ui()
        self.extra_menu = wire_extra_ui()
        self.coil_menu = wire_coil_ui()
        self.protection_menu = wire_protection_ui()
        self.utilities_menu = wire_utilities_ui()
        self.duct_menu = wire_duct_ui()
        self.connector_menu = wire_connector_ui()
        self.chain_menu = wire_chain_ui()

        button = make_button('CANCEL')
        self.ui_management.add_items(button)

        if self.operation == 'EDIT':
            obj = active_object('GET')
            self.fluent_curve['ring_nodes'] = []
            self.fluent_curve = {
                'added': True,
                'curve_obj': obj,
                'ring_nodes': [],
                'stiffness': obj['fluent_wire_data']['stiffness'],
                'first_point': {
                    'hit': Vector((obj['fluent_wire_data']['first_point']['hit'][0], obj['fluent_wire_data']['first_point']['hit'][1], obj['fluent_wire_data']['first_point']['hit'][2])),
                    'normal': Vector((obj['fluent_wire_data']['first_point']['normal'][0], obj['fluent_wire_data']['first_point']['normal'][1], obj['fluent_wire_data']['first_point']['normal'][2]))
                },
                'second_point': {
                    'hit': Vector((obj['fluent_wire_data']['second_point']['hit'][0], obj['fluent_wire_data']['second_point']['hit'][1], obj['fluent_wire_data']['second_point']['hit'][2])),
                    'normal': Vector((obj['fluent_wire_data']['second_point']['normal'][0], obj['fluent_wire_data']['second_point']['normal'][1], obj['fluent_wire_data']['second_point']['normal'][2]))
                },
                'chain':obj['fluent_wire_data']['chain']
            }
            the_modifier = self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes']
            for n in the_modifier.node_group.nodes:
                if n.type == 'GROUP' and n.node_tree.name == 'f_add_ring' and n.inputs['Object'].default_value:
                    self.fluent_curve['ring_nodes'].append(n)
            if len(self.fluent_curve['ring_nodes']):
                self.current_ring_node = self.fluent_curve['ring_nodes'][-1]
            self.ui_management.add_items(self.wire_menu)

        if self.operation == 'BECOME_FLUENT':
            obj = active_object('GET')
            bezier_points = obj.data.splines[0].bezier_points
            self.fluent_curve['added'] = True
            self.fluent_curve['curve_obj'] = obj
            self.fluent_curve['stiffness'] = 1
            self.fluent_curve['ring_nodes'] = []
            self.fluent_curve['first_point'] = {
                'hit': obj.matrix_world @ bezier_points[0].co,
                'normal': obj.matrix_world @ (bezier_points[0].handle_right - bezier_points[0].co)
            }
            self.fluent_curve['second_point'] = {
                'hit': obj.matrix_world @ bezier_points[-1].co,
                'normal': obj.matrix_world @ (bezier_points[-1].handle_right - bezier_points[-1].co)
            }
            self.load_geometry_node()
            self.ui_management.add_items(self.wire_menu)


        if not bpy.data.collections.get('Wire_Objects'):
            coll = bpy.data.collections.new("Wire_Objects")
            bpy.context.scene.collection.children.link(coll)

        active_object(self.fluent_curve['curve_obj'], 'SET', True)

        args = (self, context)
        self.timer = context.window_manager.event_timer_add(0.04, window=context.window)
        self._handle = bpy.types.SpaceView3D.draw_handler_add(draw_callback_px, args, 'WINDOW', 'POST_PIXEL')
        context.window_manager.modal_handler_add(self)

        return {'RUNNING_MODAL'}


class FLUENT_OT_ChainToMesh(Operator):
    """Convert chain to mesh"""
    bl_idname = "fluent.chaintomesh"
    bl_label = "Chain 2 mesh"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # vérification
        obj = active_object(action='GET')
        if obj:
            bpy.ops.object.duplicates_make_real()
            obj.select_set(False)
            active_object(action='SET', obj=context.selected_objects[0])

            bpy.ops.object.convert(target='MESH')
            bpy.ops.object.join()
            bpy.data.objects.remove(obj, do_unlink=True)
        return {'FINISHED'}


classes = [FLUENT_OT_Wire, FLUENT_OT_ChainToMesh]