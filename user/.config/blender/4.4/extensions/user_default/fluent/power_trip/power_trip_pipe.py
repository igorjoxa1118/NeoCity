from bpy.types import Operator

from ..Tools.translation import translate
from ..UI.Helpers.viewport_drawing import *
from ..UI.Helpers.ui_button import *
import time
from mathutils import Vector
from bpy.props import StringProperty
from ..UI.make_button import make_button
from ..UI.Helpers.ui_management import FLUENT_ui_management
from ..Tools.independant_helper import *
from ..modifiers import mirror_management


def pipe_ui():
    pie_menu = FLUENT_Ui_Layout('WIRE',title=translate('pipeMenu'), subtitle=translate('holdShift'))
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
    button.set_tool_tip(translate('bevel'))
    button.set_text('')
    button.set_shape('CIRCLE')
    button.set_icon('first_bevel')
    button.set_action('PIPE_BEVEL')
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
    button.set_tool_tip(translate('path'))
    button.set_shape('CIRCLE')
    button.set_icon('path')
    button.set_action('PATH')
    pie_menu.add_item(button)

    return pie_menu


def pipe_ring_ui():
    pie_menu = FLUENT_Ui_Layout('WIRE_RING_MENU',title=translate('ringMenu'), subtitle=translate('holdShift'))
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
    button.set_tool_tip(translate('lengthResolution'))
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


def pipe_array_ui():
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


def pipe_extra_ui():
    pie_menu = FLUENT_Ui_Layout('EXTRA_MENU', title=translate('extraMenu'), subtitle=translate('holdShift'))
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


def pipe_coil_ui():
    pie_menu = FLUENT_Ui_Layout('COIL_MENU', title=translate('coilMenu'), subtitle=translate('holdShift'))
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


def pipe_protection_ui():
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


def pipe_duct_ui():
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
    button.set_tool_tip(translate('rootStrength'))
    button.set_shape('CIRCLE')
    button.set_icon('stiffness')
    button.set_action('STIFFNESS')
    pie_menu.add_item(button)

    button = make_button('BACK')
    pie_menu.add_item(button)

    pie_menu.set_decalage(1)

    return pie_menu


def pipe_utilities_ui():
    pie_menu = FLUENT_Ui_Layout('UTILITIES_MENU',title=translate('utilities'), subtitle=translate('holdShift'))
    pie_menu.set_layout('PIE')

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_tool_tip(translate('circleResolution'))
    button.set_shape('CIRCLE')
    button.set_icon('resolution')
    button.set_action('CIRCLE_RESOLUTION')
    pie_menu.add_item(button)

    # button = FLUENT_Ui_Button()
    # button.set_text('')
    # button.set_tool_tip('Curve resolution')
    # button.set_shape('CIRCLE')
    # button.set_icon('curve_resolution')
    # button.set_action('CURVE_RESOLUTION')
    # pie_menu.add_item(button)

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

    button = make_button('BACK')
    pie_menu.add_item(button)
    pie_menu.set_decalage(1)

    return pie_menu


def pipe_connector_ui():
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


class FLUENT_OT_Pipe(Operator):
    """Put a pipe"""
    bl_idname = "fluent.pipe"
    bl_label = "Fluent pipe"
    bl_options = {'REGISTER', 'UNDO'}

    operation: StringProperty(
        default='ADD'
    )

    ui_management = None

    def number_adjustment(self, the_modifier, input, increment, event, type):
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
        increment *= get_addon_preferences().interface_factor
        if events['shift_press'] or events['shift_release'] or events['ctrl_press'] or events[
            'ctrl_release']:
            self.slider_origin = event.mouse_region_x
            self.previous_value = the_modifier[input]

        value = self.previous_value + ((event.mouse_region_x - self.slider_origin) / increment)

        if enter_value_validation(self.enter_value, event)[0]:
            value = enter_value_validation(self.enter_value, event)[1]
            self.end_of_adjustment()
        if type == 'FLOAT':
            the_modifier[input] = value
        elif type == 'INT':
            the_modifier[input] = int(value)


        the_modifier.show_viewport = False
        the_modifier.show_viewport = True

    def load_geometry_node(self):
        # charge la node
        if not bpy.data.node_groups.get('fluent_pipe'):
            file_path_node_tree = os.path.dirname(realpath(__file__)) + "/wire/wire.blend/NodeTree"
            bpy.ops.wm.append(filename='fluent_pipe', directory=file_path_node_tree)
        # ajoute geometry nodes
        geo_nodes = self.fluent_curve['curve_obj'].modifiers.new(name='.f_geometry_nodes', type='NODES')
        geo_nodes.node_group = bpy.data.node_groups['fluent_pipe'].copy()

    def make_pipe(self):

        try:
            x_i = self.fluent_curve['first_point']['hit'].x
            y_i = self.fluent_curve['first_point']['hit'].y
            z_i = self.fluent_curve['first_point']['hit'].z
        except:
            x_i = self.fluent_curve['first_point']['hit'][0]
            y_i = self.fluent_curve['first_point']['hit'][1]
            z_i = self.fluent_curve['first_point']['hit'][2]
        start = Vector((x_i, y_i, z_i))

        try:
            x_f = self.fluent_curve['second_point']['hit'].x
            y_f = self.fluent_curve['second_point']['hit'].y
            z_f = self.fluent_curve['second_point']['hit'].z
        except:
            x_f = self.fluent_curve['second_point']['hit'][0]
            y_f = self.fluent_curve['second_point']['hit'][1]
            z_f = self.fluent_curve['second_point']['hit'][2]
        end = Vector((x_f, y_f, z_f))

        root_length = self.fluent_curve['root_length']
        first_corner = start + (root_length * self.fluent_curve['first_point']['normal'])
        last_corner = end + (root_length * self.fluent_curve['second_point']['normal'])
        if self.fluent_curve['combinaison'] == 1:
            self.fluent_curve['path'] = [
                start,
                first_corner,
                (last_corner.x, first_corner.y, first_corner.z),
                (last_corner.x, last_corner.y, first_corner.z),
                last_corner,
                end
            ]
        elif self.fluent_curve['combinaison'] == 2:
            self.fluent_curve['path'] = [
                start,
                first_corner,
                (last_corner.x, first_corner.y, first_corner.z),
                (last_corner.x, first_corner.y, last_corner.z),
                last_corner,
                end
            ]
        elif self.fluent_curve['combinaison'] == 3:
            self.fluent_curve['path'] = [
                start,
                first_corner,
                (first_corner.x, last_corner.y, first_corner.z),
                (last_corner.x, last_corner.y, first_corner.z),
                last_corner,
                end
            ]
        elif self.fluent_curve['combinaison'] == 4:
            self.fluent_curve['path'] = [
                start,
                first_corner,
                (first_corner.x, last_corner.y, first_corner.z),
                (first_corner.x, last_corner.y, last_corner.z),
                last_corner,
                end
            ]
        elif self.fluent_curve['combinaison'] == 5:
            self.fluent_curve['path'] = [
                start,
                first_corner,
                (first_corner.x, first_corner.y, last_corner.z),
                (last_corner.x, first_corner.y, last_corner.z),
                last_corner,
                end
            ]
        elif self.fluent_curve['combinaison'] == 6:
            self.fluent_curve['path'] = [
                start,
                first_corner,
                (first_corner.x, first_corner.y, last_corner.z),
                (first_corner.x, last_corner.y, last_corner.z),
                last_corner,
                end
            ]

        pipe_verts = []
        for i in self.fluent_curve['path']:
            pipe_verts.append((0, 0, 0))
        edges = []
        for i in range(len(self.fluent_curve['path']) - 1):
            edges.append((i, i + 1))
        faces = []
        mesh_data = bpy.data.meshes.new("pipe_data")
        mesh_data.from_pydata(pipe_verts, edges, faces)
        mesh_data.update()
        pipe = bpy.data.objects.new("pipe", mesh_data)
        self.bool_obj = pipe
        bpy.context.scene.collection.objects.link(pipe)
        active_object('SET', pipe)
        bpy.ops.object.mode_set(mode='OBJECT')

        i = 0
        for v in pipe.data.vertices:
            v.co = self.fluent_curve['path'][i]
            i += 1

        pipe.modifiers.new(name=fluent_modifiers_name['weld'], type='WELD')

        # bpy.ops.object.mode_set(mode='EDIT')
        # bpy.ops.mesh.select_all(action="SELECT")
        # bpy.ops.mesh.dissolve_limited(angle_limit=0.0174533)
        # bpy.ops.mesh.remove_doubles()
        bpy.ops.object.mode_set(mode='OBJECT')
        modif = pipe.modifiers.new(name=fluent_modifiers_name['bevel'], type='BEVEL')
        modif.affect = 'VERTICES'
        modif.width = 0.1
        modif.segments = auto_bevel_segments(modif)
        modif.show_expanded = False

        self.fluent_curve['curve_obj'] = pipe
        use_auto_smooth(pipe.data)

        pipe['fluent_pipe_data'] = self.fluent_curve
        pipe['fluent_type'] = 'pipe'

        self.load_geometry_node()

    def align_ending_point(self, axis):
        if axis == 'X' and self.fluent_curve['path'][5].x != self.fluent_curve['path'][0].x:
            self.fluent_curve['path'][5].x = self.fluent_curve['path'][0].x
        elif axis == 'X' and self.fluent_curve['path'][5].x == self.fluent_curve['path'][0].x:
            self.fluent_curve['path'][5].x = self.fluent_curve['second_point']['hit'].x

        if axis == 'Y' and self.fluent_curve['path'][5].y != self.fluent_curve['path'][0].y:
            self.fluent_curve['path'][5].y = self.fluent_curve['path'][0].y
        elif axis == 'Y' and self.fluent_curve['path'][5].y == self.fluent_curve['path'][0].y:
            self.fluent_curve['path'][5].y = self.fluent_curve['second_point']['hit'].y

        if axis == 'Z' and self.fluent_curve['path'][5].z != self.fluent_curve['path'][0].z:
            self.fluent_curve['path'][5].z = self.fluent_curve['path'][0].z
        elif axis == 'Z' and self.fluent_curve['path'][5].z == self.fluent_curve['path'][0].z:
            self.fluent_curve['path'][5].z = self.fluent_curve['second_point']['hit'].z

        self.update_path()

    def update_path(self):
        start = self.fluent_curve['path'][0]
        end = self.fluent_curve['path'][5]

        root_length = self.fluent_curve['root_length']
        first_corner = start + (root_length * self.fluent_curve['first_point']['normal'])
        last_corner = end + (root_length * self.fluent_curve['second_point']['normal'])

        if self.fluent_curve['combinaison'] == 1:
            self.fluent_curve['path'] = [
                start,
                first_corner,
                (last_corner.x, first_corner.y, first_corner.z),
                (last_corner.x, last_corner.y, first_corner.z),
                last_corner,
                end
            ]
        elif self.fluent_curve['combinaison'] == 2:
            self.fluent_curve['path'] = [
                start,
                first_corner,
                (last_corner.x, first_corner.y, first_corner.z),
                (last_corner.x, first_corner.y, last_corner.z),
                last_corner,
                end
            ]
        elif self.fluent_curve['combinaison'] == 3:
            self.fluent_curve['path'] = [
                start,
                first_corner,
                (first_corner.x, last_corner.y, first_corner.z),
                (last_corner.x, last_corner.y, first_corner.z),
                last_corner,
                end
            ]
        elif self.fluent_curve['combinaison'] == 4:
            self.fluent_curve['path'] = [
                start,
                first_corner,
                (first_corner.x, last_corner.y, first_corner.z),
                (first_corner.x, last_corner.y, last_corner.z),
                last_corner,
                end
            ]
        elif self.fluent_curve['combinaison'] == 5:
            self.fluent_curve['path'] = [
                start,
                first_corner,
                (first_corner.x, first_corner.y, last_corner.z),
                (last_corner.x, first_corner.y, last_corner.z),
                last_corner,
                end
            ]
        elif self.fluent_curve['combinaison'] == 6:
            self.fluent_curve['path'] = [
                start,
                first_corner,
                (first_corner.x, first_corner.y, last_corner.z),
                (first_corner.x, last_corner.y, last_corner.z),
                last_corner,
                end
            ]

        for i, v in enumerate(self.fluent_curve['curve_obj'].data.vertices):
            v.co = self.fluent_curve['path'][i]

    def add_ring(self, picked_ring=None):
        if not picked_ring:
            folder = '/wire'
            file_path_wire = os.path.dirname(realpath(__file__)) + folder + "/wire.blend/Object/"
            self.fluent_curve['curve_obj'].select_set(False)
            bpy.ops.wm.append(filename='f_ring_01', directory=file_path_wire)
            ring = bpy.context.selected_objects[0]
            ring['fluent_type'] = 'pipe_ring'
            ring.name = self.fluent_curve['curve_obj'].name + '.Ring'
        else:
            ring = picked_ring

        # mise à jour de geometry nodes
        the_modifier = self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes']
        tree = the_modifier.node_group
        nodes = tree.nodes
        link = tree.links.new
        node_ring = nodes.new(type='GeometryNodeGroup')
        node_ring.node_tree = bpy.data.node_groups.get('f_add_pipe_ring')
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
            node_ring.inputs['X Offset'].default_value = 0
            if self.current_ring_node:
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
        node_group = self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes'].node_group.nodes['fluent_pipe']
        node_group.inputs['Design'].default_value = duct
        node_group.inputs['Radius'].default_value = 0

        # ajoute un weld modifier juste après geometry node
        weld = self.fluent_curve['curve_obj'].modifiers.new(type='WELD', name=fluent_modifiers_name['weld'])
        active_object('SET', self.fluent_curve['curve_obj'], True)
        bpy.ops.object.modifier_move_to_index(modifier=weld.name, index=1)

    def end_of_adjustment(self):
        if self.action in {'TILT_01', 'TILT_02'} :
            active_object(self.fluent_curve['curve_obj'], 'SET')
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.curve.select_all(action = 'SELECT')
            bpy.ops.curve.smooth_tilt()
            bpy.ops.object.mode_set(mode='OBJECT')
            self.fluent_curve['curve_obj'].select_set(False)

        try:
            modifier_name = self.action.split('#')[1]
            if modifier_name in {'F_Ring_Array'}:
                bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        except:pass
        self.action = 'NOTHING'
        self.build_step = self.other_adjustment = None
        self.enter_value = 'None'
        self.previous_value = None

    def put_curve(self):
        events = self.ui_management.event_dico_get()
        if not self.fluent_curve['added'] and self.fluent_curve['first_point'] and self.fluent_curve['second_point']:
            self.snap_face_center = False
            self.make_pipe()

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

        bpy.ops.object.select_all(action="DESELECT")

        return [
            [translate('pipeTool'), ''],
            [translate('pipeEnds'), translate('leftClick')],
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
            if bpy.context.active_object.mode == 'EDIT' and not self.action:
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
        if self.fluent_curve['added']:
            if event.type == 'R' and event.value == 'PRESS':
                action = 'SELECT_RING'
            if event.type == 'X' and event.value == 'PRESS':
                action = 'ALIGN_X'
            if event.type == 'Y' and event.value == 'PRESS':
                action = 'ALIGN_Y'
            if event.type == 'Z' and event.value == 'PRESS':
                action = 'ALIGN_Z'
            if event.type == 'M' and event.value == 'PRESS':
                action = 'MIRROR'
        if event.type == 'ESC' and event.value == 'PRESS' and not self.action:
            action = 'CANCELLED'
        if event.type == 'ESC' and event.value == 'PRESS' and self.action:
            self.action = None

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
            elif action == 'WIRE_RING_MENU' and not event.shift:
                self.ui_management.position_menu_under_previous(self.wire_ring_menu)
                self.ui_management.add_items(self.wire_ring_menu, is_submenu=True)
                refresh_pos = False
            elif action == 'ARRAY_MENU' and not event.shift:
                self.ui_management.position_menu_under_previous(self.array_menu)
                self.ui_management.add_items(self.array_menu, is_submenu=True)
                refresh_pos = False
            elif action == 'EXTRA_MENU' and not event.shift:
                self.ui_management.position_menu_under_previous(self.extra_menu)
                self.ui_management.add_items(self.extra_menu, is_submenu=True)
                refresh_pos = False
            elif action == 'COIL_MENU' and not event.shift:
                self.ui_management.position_menu_under_previous(self.coil_menu)
                self.ui_management.add_items(self.coil_menu, is_submenu=True)
                refresh_pos = False
            elif action == 'PROTECTION_MENU' and not event.shift:
                self.ui_management.position_menu_under_previous(self.protection_menu)
                self.ui_management.add_items(self.protection_menu, is_submenu=True)
                refresh_pos = False
            elif action == 'UTILITIES_MENU' and not event.shift:
                self.ui_management.position_menu_under_previous(self.utilities_menu)
                self.ui_management.add_items(self.utilities_menu, is_submenu=True)
                refresh_pos = False
            elif action == 'DUCT_MENU' and not event.shift:
                self.ui_management.position_menu_under_previous(self.duct_menu)
                self.ui_management.add_items(self.duct_menu, is_submenu=True)
                refresh_pos = False
            elif action == 'CONNECTOR_MENU' and not event.shift:
                self.ui_management.position_menu_under_previous(self.connector_menu)
                self.ui_management.add_items(self.connector_menu, is_submenu=True)
                refresh_pos = False
            elif action == 'BACK_MENU' and not event.shift:
                self.ui_management.remove_last_menu(is_submenu=True)
            self.action = action

        # gestion affichage du pie menu
        self.ui_management.toggle_menu_displaying(refresh_pos)

        if action in ['ALIGN_X', 'ALIGN_Y', 'ALIGN_Z']:
            if 'X' in action:
                self.align_ending_point('X')
            elif 'Y' in action:
                self.align_ending_point('Y')
            elif 'Z' in action:
                self.align_ending_point('Z')

        if not events['show_menu'] and self.value_animation['step'] == 'WAIT':
            # basic settings ###############################
            if self.action == 'RADIUS':
                the_modifier = self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes']
                the_input = 'Input_6'
                self.number_adjustment(the_modifier, the_input, 400, event, 'FLOAT')
                if self.enter_value != 'None':
                    screen_text.append([translate('radius'), str(self.enter_value)])
                else:
                    screen_text.append([translate('radius'), str(round(the_modifier[the_input], 5))])
                screen_text.append([translate('gap'), 'V'])
                screen_text.append([translate('count'), 'B'])

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

            if self.action == 'PIPE_BEVEL':
                the_input = self.fluent_curve['curve_obj'].modifiers[fluent_modifiers_name['bevel']]
                if self.previous_value is None:
                    self.previous_value = the_input.width
                    self.slider_origin = event.mouse_region_x
                    self.ui_management.hide_menu()
                    self.ui_management.add_items(only_validate_menu())
                    self.ui_management.hide_menu()
                if self.enter_value != 'None':
                    screen_text.append([translate('width'), str(self.enter_value)])
                else:
                    screen_text.append([translate('width'), str(round(the_input.width, 5))])
                self.enter_value = enter_value(self.enter_value, events)
                screen_text.append([translate('segments'), 'C'])
                screen_text.append([translate('wireframe'), 'W'])
                if events['shift_work']:
                    increment = 4000
                elif events['ctrl_work']:
                    increment = 40
                else:
                    increment = 400
                if events['shift_press'] or events['shift_release'] or events['ctrl_press'] or events['ctrl_release']:
                    self.slider_origin = event.mouse_region_x
                    self.previous_value = the_input.width

                the_input.width = self.previous_value + ((event.mouse_region_x - self.slider_origin)/increment)
                if enter_value_validation(self.enter_value, event)[0]:
                    the_input.width = enter_value_validation(self.enter_value, event)[1]
                    self.end_of_adjustment()

                if event.type == 'C' and event.value == 'PRESS':
                    self.ui_management.remove_last_menu()
                    self.ui_management.hide_menu()
                    self.end_of_adjustment()
                    self.action = 'PIPE_SEGMENTS'
                    return {'RUNNING_MODAL'}

            if self.action == 'PIPE_SEGMENTS':
                the_input = self.fluent_curve['curve_obj'].modifiers[fluent_modifiers_name['bevel']]
                if self.previous_value is None:
                    self.previous_value = the_input.segments
                    self.slider_origin = event.mouse_region_x
                    self.ui_management.hide_menu()
                    self.ui_management.add_items(only_validate_menu())
                    self.ui_management.hide_menu()
                if self.enter_value != 'None':
                    screen_text.append([translate('segments'), str(self.enter_value)])
                else:
                    screen_text.append([translate('segments'), str(round(the_input.segments, 5))])
                self.enter_value = enter_value(self.enter_value, events)
                screen_text.append([translate('width'), 'C'])
                screen_text.append([translate('wireframe'), 'W'])
                if events['shift_work']:
                    increment = 1000
                elif events['ctrl_work']:
                    increment = 10
                else:
                    increment = 100
                if events['shift_press'] or events['shift_release'] or events['ctrl_press'] or events['ctrl_release']:
                    self.slider_origin = event.mouse_region_x
                    self.previous_value = the_input.segments

                the_input.segments = int(self.previous_value + ((event.mouse_region_x - self.slider_origin)/increment))
                if enter_value_validation(self.enter_value, event)[0]:
                    the_input.segments = int(enter_value_validation(self.enter_value, event)[1])
                    self.end_of_adjustment()

                if event.type == 'C' and event.value == 'PRESS':
                    self.ui_management.remove_last_menu()
                    self.ui_management.hide_menu()
                    self.end_of_adjustment()
                    self.action = 'PIPE_BEVEL'
                    return {'RUNNING_MODAL'}

            if self.action == 'TILT_01':
                if self.previous_value is None:
                    self.previous_value = self.fluent_curve['curve_obj'].data.splines[0].bezier_points[0].tilt
                    self.slider_origin = event.mouse_region_x
                    self.ui_management.hide_menu()
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
                    self.ui_management.hide_menu()
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
                    self.previous_value = self.fluent_curve['root_length']
                    self.slider_origin = event.mouse_region_x
                    self.ui_management.hide_menu()
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
                    self.previous_value = self.fluent_curve['root_length']

                if event.type =='MOUSEMOVE':
                    self.fluent_curve['root_length'] = self.previous_value + ((event.mouse_region_x - self.slider_origin)/increment)
                    if self.fluent_curve['root_length'] < 0:
                        self.fluent_curve['root_length'] = 0
                    self.update_path()

            if self.action == 'CIRCLE_RESOLUTION':
                the_modifier = self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes']
                the_input = 'Input_27'
                self.number_adjustment(the_modifier, the_input, 10, event, 'INT')
                if self.enter_value != 'None':
                    screen_text.append([translate('resolution'), str(self.enter_value)])
                else:
                    screen_text.append([translate('resolution'), str(round(the_modifier[the_input], 5))])

            if self.action == 'CURVE_RESOLUTION':
                if self.previous_value is None:
                    self.previous_value = self.fluent_curve['curve_obj'].data.resolution_u
                    self.slider_origin = event.mouse_region_x
                    self.ui_management.hide_menu()
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

                self.fluent_curve['curve_obj'].data.resolution_u = self.previous_value + ((event.mouse_region_x - self.slider_origin)/increment)
                if enter_value_validation(self.enter_value, event)[0]:
                    self.do_not = 'QUIT_FLUENT'
                    self.fluent_curve['curve_obj'].data.resolution_u = enter_value_validation(self.enter_value, event)[1]
                    self.end_of_adjustment()

            if self.action == 'CURVE_OFFSET':
                the_modifier = self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes']
                the_input = 'Input_7'
                self.number_adjustment(the_modifier, the_input, 80, event, 'FLOAT')
                if self.enter_value != 'None':
                    screen_text.append([translate('resolution'), str(self.enter_value)])
                else:
                    screen_text.append([translate('resolution'), str(round(the_modifier[the_input], 5))])
                self.enter_value = enter_value(self.enter_value, events)

            if self.action == 'PATH':
                if self.previous_value is None:
                    self.previous_value = 0
                    self.slider_origin = event.mouse_region_x
                    self.ui_management.hide_menu()
                    self.ui_management.add_items(only_validate_menu())
                    self.ui_management.hide_menu()

                increment = 1

                value = self.previous_value + ((event.mouse_region_x - self.slider_origin)/increment)
                value = snap_slider_value(value, 20)

                if round(value) != 0:
                    self.previous_value = 0
                    self.slider_origin = event.mouse_region_x
                    if round(value) > 0:
                        self.fluent_curve['combinaison'] += 1
                        if self.fluent_curve['combinaison'] > 6:
                            self.fluent_curve['combinaison'] = 0
                    else:
                        self.fluent_curve['combinaison'] -= 1
                        if self.fluent_curve['combinaison'] < 0:
                            self.fluent_curve['combinaison'] = 6
                    self.update_path()

                screen_text.append([translate('path'), str(self.fluent_curve['combinaison'])])

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
                screen_text.append([translate('rotate'), 'C'])

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
                    self.ui_management.hide_menu()
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
                if events['shift_press'] or events['shift_release'] or events['ctrl_press'] or \
                        events[
                            'ctrl_release']:
                    self.slider_origin = event.mouse_region_x
                    self.previous_value = the_input.default_value

                the_input.default_value = self.previous_value + (
                            (event.mouse_region_x - self.slider_origin) / increment)
                if enter_value_validation(self.enter_value, event)[0]:
                    the_input.default_value = enter_value_validation(self.enter_value, event)[1]
                    self.end_of_adjustment()

            if self.action == 'RING_SCALE' and self.current_ring_node and self.current_ring_node.inputs[
                'Object'].default_value.get('fluent_type') != 'pipe_ring':
                node = self.current_ring_node
                the_input = node.inputs['Scale']
                if self.previous_value is None:
                    self.previous_value = the_input.default_value
                    self.slider_origin = event.mouse_region_x
                    self.ui_management.hide_menu()
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
                if events['shift_press'] or events['shift_release'] or events['ctrl_press'] or \
                        events[
                            'ctrl_release']:
                    self.slider_origin = event.mouse_region_x
                    self.previous_value = the_input.default_value

                the_input.default_value = self.previous_value + (
                            (event.mouse_region_x - self.slider_origin) / increment)
                if enter_value_validation(self.enter_value, event)[0]:
                    the_input.default_value = enter_value_validation(self.enter_value, event)[1]
                    self.end_of_adjustment()

            if self.action == 'RING_ARRAY_COUNT' and self.current_ring_node:
                node = self.current_ring_node
                the_input = node.inputs['Count']
                if self.previous_value is None:
                    self.previous_value = the_input.default_value
                    self.slider_origin = event.mouse_region_x
                    self.ui_management.hide_menu()
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
                if events['shift_press'] or events['shift_release'] or events['ctrl_press'] or \
                        events[
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
                    self.ui_management.hide_menu()
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
                if events['shift_press'] or events['shift_release'] or events['ctrl_press'] or \
                        events[
                            'ctrl_release']:
                    self.slider_origin = event.mouse_region_x
                    self.previous_value = the_input.default_value

                the_input.default_value = self.previous_value + (
                            (event.mouse_region_x - self.slider_origin) / increment)
                if enter_value_validation(self.enter_value, event)[0]:
                    the_input.default_value = enter_value_validation(self.enter_value, event)[1]
                    self.end_of_adjustment()

                if event.type == 'C' and event.value == 'PRESS':
                    self.ui_management.remove_last_menu()
                    self.ui_management.hide_menu()
                    self.end_of_adjustment()
                    self.action = 'RING_ARRAY_COUNT'
                    return {'RUNNING_MODAL'}

            if self.action == 'RING_LENGTH' and self.current_ring_node and self.current_ring_node.inputs[
                'Object'].default_value.get('fluent_type') == 'pipe_ring':
                node = self.current_ring_node
                ring_obj = node.inputs['Object'].default_value
                the_input = ring_obj.modifiers[translate('length')]
                if self.previous_value is None:
                    self.previous_value = the_input.screw_offset
                    self.slider_origin = event.mouse_region_x
                    self.ui_management.hide_menu()
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
                if events['shift_press'] or events['shift_release'] or events['ctrl_press'] or \
                        events[
                            'ctrl_release']:
                    self.slider_origin = event.mouse_region_x
                    self.previous_value = the_input.screw_offset

                the_input.screw_offset = self.previous_value + ((event.mouse_region_x - self.slider_origin) / increment)
                if enter_value_validation(self.enter_value, event)[0]:
                    the_input.screw_offset = enter_value_validation(self.enter_value, event)[1]
                    self.end_of_adjustment()

            if self.action == 'RING_L_RESOLUTION' and self.current_ring_node and self.current_ring_node.inputs[
                'Object'].default_value.get('fluent_type') == 'pipe_ring':
                node = self.current_ring_node
                ring_obj = node.inputs['Object'].default_value
                the_input = ring_obj.modifiers[translate('length')]
                if self.previous_value is None:
                    self.previous_value = the_input.steps
                    self.slider_origin = event.mouse_region_x
                    self.ui_management.hide_menu()
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
                if events['shift_press'] or events['shift_release'] or events['ctrl_press'] or \
                        events[
                            'ctrl_release']:
                    self.slider_origin = event.mouse_region_x
                    self.previous_value = the_input.steps

                the_input.steps = the_input.render_steps = int(self.previous_value + ((event.mouse_region_x - self.slider_origin) / increment))
                if enter_value_validation(self.enter_value, event)[0]:
                    the_input.steps = the_input.render_steps = int(enter_value_validation(self.enter_value, event)[1])
                    self.end_of_adjustment()

            if self.action == 'RING_RADIUS' and self.current_ring_node and self.current_ring_node.inputs['Object'].default_value.get('fluent_type') == 'pipe_ring':
                node = self.current_ring_node
                ring_obj = node.inputs['Object'].default_value
                the_input = ring_obj.modifiers[translate('radius')]
                if self.previous_value is None:
                    self.previous_value = the_input.strength
                    self.slider_origin = event.mouse_region_x
                    self.ui_management.hide_menu()
                    self.ui_management.add_items(only_validate_menu())
                    self.ui_management.hide_menu()
                if self.enter_value != 'None':
                    screen_text.append([translate('length'), str(self.enter_value)])
                else:
                    screen_text.append([translate('length'), str(round(the_input.strength, 5))])
                screen_text.append([translate('sameAsPipe'), 'C'])
                self.enter_value = enter_value(self.enter_value, events)
                if events['shift_work']:
                    increment = 500
                elif events['ctrl_work']:
                    increment = 5
                else:
                    increment = 50
                if events['shift_press'] or events['shift_release'] or events['ctrl_press'] or events['ctrl_release']:
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

            if self.action == 'RING_THICKNESS' and self.current_ring_node and self.current_ring_node.inputs['Object'].default_value.get('fluent_type') == 'pipe_ring':
                node = self.current_ring_node
                ring_obj = node.inputs['Object'].default_value
                the_input = ring_obj.modifiers['Thickness']
                if self.previous_value is None:
                    self.previous_value = the_input.thickness
                    self.slider_origin = event.mouse_region_x
                    self.ui_management.hide_menu()
                    self.ui_management.add_items(only_validate_menu())
                    self.ui_management.hide_menu()
                if self.enter_value != 'None':
                    screen_text.append([translate('length'), str(self.enter_value)])
                else:
                    screen_text.append([translate('length'), str(round(the_input.thickness, 5))])
                screen_text.append([translate('sameAsPipe'), 'C'])
                self.enter_value = enter_value(self.enter_value, events)
                if events['shift_work']:
                    increment = 5000
                elif events['ctrl_work']:
                    increment = 50
                else:
                    increment = 500
                if events['shift_press'] or events['shift_release'] or events['ctrl_press'] or \
                        events[
                            'ctrl_release']:
                    self.slider_origin = event.mouse_region_x
                    self.previous_value = the_input.thickness

                the_input.thickness = self.previous_value + ((event.mouse_region_x - self.slider_origin) / increment)
                if enter_value_validation(self.enter_value, event)[0]:
                    the_input.thickness = enter_value_validation(self.enter_value, event)[1]
                    self.end_of_adjustment()

            if self.action == 'RING_BEVEL' and self.current_ring_node and self.current_ring_node.inputs[
                'Object'].default_value.get('fluent_type') == 'pipe_ring':
                node = self.current_ring_node
                ring_obj = node.inputs['Object'].default_value
                the_input = ring_obj.modifiers['Bevel']
                if self.previous_value is None:
                    self.previous_value = the_input.width
                    self.slider_origin = event.mouse_region_x
                    self.ui_management.hide_menu()
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
                if events['shift_press'] or events['shift_release'] or events['ctrl_press'] or \
                        events[
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

            if self.action == 'RING_C_RESOLUTION' and self.current_ring_node and self.current_ring_node.inputs[
                'Object'].default_value.get('fluent_type') == 'pipe_ring':
                node = self.current_ring_node
                ring_obj = node.inputs['Object'].default_value
                the_input = ring_obj.modifiers['Screw']
                if self.previous_value is None:
                    self.previous_value = the_input.steps
                    self.slider_origin = event.mouse_region_x
                    self.ui_management.hide_menu()
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
                if events['shift_press'] or events['shift_release'] or events['ctrl_press'] or \
                        events[
                            'ctrl_release']:
                    self.slider_origin = event.mouse_region_x
                    self.previous_value = the_input.steps

                the_input.steps = the_input.render_steps = int(self.previous_value + ((event.mouse_region_x - self.slider_origin) / increment))
                if enter_value_validation(self.enter_value, event)[0]:
                    the_input.steps = the_input.render_steps = int(enter_value_validation(self.enter_value, event)[1])
                    self.end_of_adjustment()

            if self.action == 'RING_REMOVE' and self.current_ring_node:
                the_modifier = self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes']
                if self.current_ring_node.inputs['Object'].default_value.get('fluent_type') == 'pipe_ring':
                    bpy.data.objects.remove(self.current_ring_node.inputs['Object'].default_value, do_unlink=True)
                else:
                    original_name = self.current_ring_node.inputs['Object'].default_value.name
                    save = duplicate(self.current_ring_node.inputs['Object'].default_value)
                    bpy.data.objects.remove(self.current_ring_node.inputs['Object'].default_value, do_unlink=True)
                    save.name = original_name
                the_modifier.node_group.nodes.remove(self.current_ring_node)
                self.current_ring_node = None
                self.fluent_curve['ring_nodes'] = []
                for n in the_modifier.node_group.nodes:
                    if n.type == 'GROUP' and n.node_tree.name == 'f_add_pipe_ring' and n.inputs['Object'].default_value:
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
                    self.fluent_curve['curve_obj'].modifiers.remove(
                        self.fluent_curve['curve_obj'].modifiers[fluent_modifiers_name['weld']])
                else:
                    self.add_duct()
                self.action = None

            if self.action == 'DUCT_RATIO':
                duct_obj = self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes']['Input_25']
                if duct_obj:
                    ratio_modifier = duct_obj.modifiers['ratio']
                    if self.previous_value is None:
                        self.previous_value = ratio_modifier.strength
                        self.slider_origin = event.mouse_region_x
                        self.ui_management.hide_menu()
                        self.ui_management.add_items(only_validate_menu())
                        self.ui_management.hide_menu()
                    if self.enter_value != 'None':
                        screen_text.append([translate('ratio'), str(self.enter_value)])
                    else:
                        screen_text.append([translate('ratio'), str(round(ratio_modifier.strength, 5))])
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
                        self.previous_value = ratio_modifier.strength

                    ratio_modifier.strength = self.previous_value + (
                                (event.mouse_region_x - self.slider_origin) / increment)
                    if enter_value_validation(self.enter_value, event)[0]:
                        ratio_modifier.strength = enter_value_validation(self.enter_value, event)[1]
                        self.end_of_adjustment()

                    if event.type == 'C' and event.value == 'PRESS':
                        self.ui_management.remove_last_menu()
                        self.ui_management.hide_menu()
                        self.end_of_adjustment()
                        self.action = 'DUCT_RADIUS'
                        return {'RUNNING_MODAL'}

            if self.action == 'DUCT_RADIUS':
                duct_obj = self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes']['Input_25']
                if duct_obj:
                    radius_01_modifier = duct_obj.modifiers['radius_01']
                    radius_02_modifier = duct_obj.modifiers['radius_02']
                    if self.previous_value is None:
                        self.adjust_me = radius_01_modifier
                        self.previous_value = self.adjust_me.strength
                        self.slider_origin = event.mouse_region_x
                        self.ui_management.hide_menu()
                        self.ui_management.add_items(only_validate_menu())
                        self.ui_management.hide_menu()
                    if self.enter_value != 'None':
                        screen_text.append([translate('radius'), str(self.enter_value)])
                    else:
                        screen_text.append([translate('radius'), str(round(self.adjust_me.strength, 5))])
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
                        self.previous_value = self.adjust_me.strength

                    if events['type'] == 'C' and events['value'] == 'PRESS':
                        if self.adjust_me == radius_01_modifier:
                            self.adjust_me = radius_02_modifier
                        elif self.adjust_me == radius_02_modifier:
                            self.adjust_me = radius_01_modifier
                        self.previous_value = self.adjust_me.strength
                        self.slider_origin = event.mouse_region_x

                    self.adjust_me.strength = self.previous_value + (
                            (event.mouse_region_x - self.slider_origin) / increment)
                    if enter_value_validation(self.enter_value, event)[0]:
                        self.adjust_me.strength = enter_value_validation(self.enter_value, event)[1]
                        self.end_of_adjustment()

                    if event.type == 'V' and event.value == 'PRESS':
                        self.ui_management.remove_last_menu()
                        self.ui_management.hide_menu()
                        self.end_of_adjustment()
                        self.action = 'DUCT_RATIO'
                        return {'RUNNING_MODAL'}

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
                self.action = None
                geo_node.show_viewport = False
                geo_node.show_viewport = True

        if self.action == 'CONNECTOR_PICK':
            self.action = 'CONNECTOR_PICK_WAITING'

        # utilities ####################################
        if self.action == 'REUSE':
            screen_text.append([translate('pickAnotherPipe'), translate('leftClick')])
            screen_text.append([translate('cancel'), translate('escape')])
        if self.action == 'REUSE' and event.value == 'PRESS' and event.type == 'LEFTMOUSE':
            obj_source = click_on(event.mouse_region_x, event.mouse_region_y)
            if obj_source and obj_source.get('fluent_type') == 'pipe':
                self.action = None
                the_modifier_source = obj_source.modifiers['.f_geometry_nodes']
                if the_modifier_source:
                    the_modifier = self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes']
                    copy_gn_mod_inputs(the_modifier, obj_source)
                    the_modifier.show_viewport = False
                    the_modifier.show_viewport = True
                # recopie les paramètre du bevel
                bevel_source = obj_source.modifiers[fluent_modifiers_name['bevel']]
                bevel_data = get_modifier_values(bevel_source)
                set_modifier_value(self.fluent_curve['curve_obj'].modifiers[fluent_modifiers_name['bevel']], bevel_data)

                try:
                    mirror_source = obj_source.modifiers[fluent_modifiers_name['mirror']]
                    mirror_data = get_modifier_values(mirror_source)
                    mirror_mod = None
                    try:
                        mirror_mod = self.fluent_curve['curve_obj'].modifiers[fluent_modifiers_name['mirror']]
                    except:
                        pass

                    if mirror_mod is None:
                        mirror = mirror_management(self.fluent_curve['curve_obj'], None)
                        mirror.add_mirror(None)
                    set_modifier_value(self.fluent_curve['curve_obj'].modifiers[fluent_modifiers_name['mirror']], mirror_data)
                except:pass

        if self.action == 'RESET':
            bpy.data.objects.remove(self.fluent_curve['curve_obj'], do_unlink=True)
            self.fluent_curve['added'] = False
            self.put_curve()
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

        if event.value == 'PRESS' and event.type == 'RIGHTMOUSE' or self.action == 'FINISHED':
            try:
                self.fluent_curve['ring_nodes'] = []
            except:pass
            try:
                bpy.data.collections['Wire_Objects'].objects.link(self.fluent_curve['curve_obj'])
                bpy.context.scene.collection.objects.unlink(self.fluent_curve['curve_obj'])
            except:pass
            context.window_manager.event_timer_remove(self.timer)
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            return {'FINISHED'}

        # creation de la courbe
        if not self.fluent_curve['added']:
            screen_text = self.put_curve()
        else:
            screen_text.append([translate('alignEnds'), translate('xyz')])

        self.ui_management.refresh_side_infos(screen_text)

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        self.fluent_curve = {
            'added': False,
            'curve_obj': None,
            'ring_nodes': [],
            'first_point': None,
            'second_point': None,
            'root_length': 0.2,
            'path': [],
            'combinaison': 2,
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

        self.wire_menu = pipe_ui()
        self.wire_ring_menu = pipe_ring_ui()
        self.array_menu = pipe_array_ui()
        self.extra_menu = pipe_extra_ui()
        self.coil_menu = pipe_coil_ui()
        self.utilities_menu = pipe_utilities_ui()
        self.duct_menu = pipe_duct_ui()
        self.connector_menu = pipe_connector_ui()

        button = make_button('CANCEL')
        self.ui_management.add_items(button)

        if self.operation == 'EDIT':
            obj = active_object('GET')
            self.fluent_curve['ring_nodes'] = []
            self.fluent_curve = {
                'added': True,
                'curve_obj': obj,
                'ring_nodes': [],
                'root_length': obj['fluent_pipe_data']['root_length'],
                'path': [
                    Vector((obj['fluent_pipe_data']['path'][0][0], obj['fluent_pipe_data']['path'][0][1], obj['fluent_pipe_data']['path'][0][2])),
                    Vector((obj['fluent_pipe_data']['path'][1][0], obj['fluent_pipe_data']['path'][1][1], obj['fluent_pipe_data']['path'][1][2])),
                    Vector((obj['fluent_pipe_data']['path'][2][0], obj['fluent_pipe_data']['path'][2][1], obj['fluent_pipe_data']['path'][2][2])),
                    Vector((obj['fluent_pipe_data']['path'][3][0], obj['fluent_pipe_data']['path'][3][1], obj['fluent_pipe_data']['path'][3][2])),
                    Vector((obj['fluent_pipe_data']['path'][4][0], obj['fluent_pipe_data']['path'][4][1], obj['fluent_pipe_data']['path'][4][2])),
                    Vector((obj['fluent_pipe_data']['path'][5][0], obj['fluent_pipe_data']['path'][5][1], obj['fluent_pipe_data']['path'][5][2])),
                ],
                'combinaison': obj['fluent_pipe_data']['combinaison'],
                'first_point': {
                    'hit': Vector((obj['fluent_pipe_data']['first_point']['hit'][0], obj['fluent_pipe_data']['first_point']['hit'][1], obj['fluent_pipe_data']['first_point']['hit'][2])),
                    'normal': Vector((obj['fluent_pipe_data']['first_point']['normal'][0], obj['fluent_pipe_data']['first_point']['normal'][1], obj['fluent_pipe_data']['first_point']['normal'][2]))
                },
                'second_point': {
                    'hit': Vector((obj['fluent_pipe_data']['second_point']['hit'][0], obj['fluent_pipe_data']['second_point']['hit'][1], obj['fluent_pipe_data']['second_point']['hit'][2])),
                    'normal': Vector((obj['fluent_pipe_data']['second_point']['normal'][0], obj['fluent_pipe_data']['second_point']['normal'][1], obj['fluent_pipe_data']['second_point']['normal'][2]))
                }
            }
            geo_node = self.fluent_curve['curve_obj'].modifiers['.f_geometry_nodes'].node_group
            for n in geo_node.nodes:
                if n.type == 'GROUP' and n.node_tree.name == 'f_add_pipe_ring' and n.inputs['Object'].default_value:
                    self.fluent_curve['ring_nodes'].append(n)
            if len(self.fluent_curve['ring_nodes']):
                self.current_ring_node = self.fluent_curve['ring_nodes'][-1]
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


classes = [FLUENT_OT_Pipe]