import bpy
import nodeitems_builtins
from enum import Enum
from mathutils import Vector
from ... utility import method_handler
from ... ui_framework import form_ui as form
from ... utility.base_modal_controls import Base_Modal_Controls
from ... ui_framework.master import Master
from ... ui_framework.utils.dialogue import Dialogue


def node_categories(context):

    groups = {}

    if context.area.ui_type == 'ShaderNodeTree':
        for cat in nodeitems_builtins.shader_node_categories:
            groups[cat.name] = []
            append = groups[cat.name].append
            for item in cat.items(context):
                if hasattr(item, 'nodetype'):
                    append(item.nodetype)

    elif context.area.ui_type == 'GeometryNodeTree':
        for cat in nodeitems_builtins.geometry_node_categories:
            groups[cat.name] = []
            append = groups[cat.name].append
            for item in cat.items(context):
                if hasattr(item, 'nodetype'):
                    append(item.nodetype)
    return groups


class Modes(Enum):
    RELATED = 0
    CATEGORIES = 1
    APPEND = 2
    ALL = 3


class Node_Data:

    def __init__(self, node):
        self.type = node.type
        self.bl_idname = node.bl_idname
        self.inputs = [n.type for n in node.inputs]
        self.outputs = [o.type for o in node.outputs]


class Graph:

    def __init__(self, context):
        self.tree = context.area.spaces.active.edit_tree
        self.active_node = self.tree.nodes.active
        self.location = Vector((0,0))
        self.dimensions = Vector((0, 0))

        # Insert Location
        x, y = 0, 0
        if self.active_node:
            x, y = self.active_node.location
        self.location = Vector((x, y))

        # Validate
        if self.active_node == None: return

        self.dimensions = self.active_node.dimensions.copy()

        # Node Data for scrolls
        self.node_data = {} # Key : Category, Val = [Node_Data]
        nodes = []
        category_data = node_categories(context)
        for category, types in category_data.items():
            node_datas = []
            for node_type in types:
                if not hasattr(bpy.types, node_type): continue
                node = self.tree.nodes.new(node_type)
                node_datas.append(Node_Data(node))
                nodes.append(node)
            self.node_data[category] = node_datas[:]

        for node in nodes:
            self.tree.nodes.remove(node)
        del nodes

        # Capture Node Connections
        self.output_links = {} # KEY = Socket : VAL = list ( to socket )
        self.input_links = {} # KEY = Socket : VAL = list ( to socket )

        for output in self.active_node.outputs:
            connections = []
            for link in output.links:
                connections.append(link.to_socket)
            self.output_links[output] = connections

        for n_input in self.active_node.inputs:
            connections = []
            for link in n_input.links:
                connections.append(link.from_socket)
            self.input_links[n_input] = connections


    def find_node_data(self, bl_idname):
        for category, datas in self.node_data.items():
            for node_data in datas:
                if node_data.bl_idname == bl_idname:
                    return node_data
        return None


    def hide_active(self, hide=True):
        if self.active_node == None: return
        self.active_node.hide = hide


    def restore_connections(self):
        if self.active_node == None: return

        for output in self.active_node.outputs:
            for link in output.links:
                self.tree.links.remove(link)

        for n_input in self.active_node.inputs:
            for link in n_input.links:
                self.tree.links.remove(link)

        # Connect Outputs
        for socket, connections in self.output_links.items():
            for to_scoket in connections:
                self.tree.links.new(socket, to_scoket)

        # Connect Inputs
        for socket, connections in self.input_links.items():
            for to_scoket in connections:
                self.tree.links.new(socket, to_scoket)


class Related_Nodes:

    def __init__(self, context, graph):
        self.index = 0
        self.types = []
        self.valid = True
        self.category_title = ""
        self.current_node = None

        active_node = graph.active_node
        if not active_node:
            self.valid = False
            return

        # Save nodes related nodes
        for category, datas in graph.node_data.items():
            found = False
            for node_data in datas:
                if node_data.bl_idname == active_node.bl_idname:
                    found = True
                    break
            if found:
                self.types = [n.bl_idname for n in datas]
                self.category_title = category
                break

        if not self.types:
            self.valid = False


    def scroll(self, context, scroll, graph):
        if graph.active_node == None: return
        graph.hide_active(hide=False)
        self.index += scroll
        if self.index > len(self.types) - 1:
            self.index = 0
        elif self.index < 0:
            self.index = len(self.types) - 1
        self.create(graph)


    def create(self, graph):
        self.remove(graph)
        node_type = self.types[self.index]
        self.current_node = graph.tree.nodes.new(node_type)
        location = graph.location
        dimensions = graph.dimensions
        self.current_node.location.x = location.x
        self.current_node.location.y = location.y
        self.current_node.location.y -= dimensions.y + 10


    def remove(self, graph):
        if not self.current_node: return
        graph.tree.nodes.remove(self.current_node)
        self.current_node = None


class Category_Nodes:

    def __init__(self, context, graph):
        self.categories = node_categories(context)
        self.keys = []
        self.index = 0
        self.nodes = []
        self.current_category_name = ""
        self.run_late_update = False

        if 'Layout' in self.categories:
            del self.categories['Layout']

        if 'Group' in self.categories:
            del self.categories['Group']

        self.keys = list(self.categories.keys())
        self.current_category_name = self.keys[self.index]


    def scroll(self, context, scroll, graph):
        graph.hide_active(hide=True)
        self.index += scroll
        if self.index > len(self.categories) - 1:
            self.index = 0
        elif self.index < 0:
            self.index = len(self.categories) - 1
        self.create(graph)


    def create(self, graph):

        self.remove(graph)

        category_name = self.keys[self.index]
        self.current_category_name = category_name
        node_types = self.categories[category_name]

        offset_y = 150
        shift_x = -1 * 55 * len(node_types)
        padding_x = 10

        # Place Nodes
        frame_children = []
        offset_x = 0
        for node_type in node_types:
            if not hasattr(bpy.types, node_type): continue
            node = graph.tree.nodes.new(node_type)
            node.location.x = graph.location.x + offset_x + shift_x
            node.location.y = graph.location.y - offset_y
            offset_x += node.width + padding_x
            frame_children.append(node)
            self.nodes.append(node)

        width = sum([node.width + padding_x for node in frame_children])

        # Frame
        frame = graph.tree.nodes.new('NodeFrame')
        frame.label = category_name
        frame.location.x = graph.location.x + shift_x
        frame.location.y = graph.location.y - offset_y
        frame.width = width
        frame.height = 400

        self.nodes.append(frame)

        for node in frame_children:
            node.parent = frame

        # Update parenting draw
        self.run_late_update = True


    def remove(self, graph):
        if not self.nodes: return
        for node in self.nodes:
            graph.tree.nodes.remove(node)
        self.nodes = []


    def late_update(self):
        if self.run_late_update:
            self.run_late_update = False
            bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)


class Append_Nodes:

    def __init__(self, context, graph):
        self.flip = False
        self.index = 0
        self.types = []
        self.active_socket_index = 0
        self.target_sockect_index = 0
        self.valid = False
        self.current_node = None
        self.category_index = 0

        if not graph.active_node: return
        if len(graph.active_node.outputs) < 1: return
        self.valid = True
        self.build_types(graph)

        # Default Active : Starts with output sockets
        for index, output in enumerate(graph.active_node.outputs):
            if output.enabled:
                self.active_socket_index = index
                break


    def filter_types(self, graph, string):

        active_socket = None
        if self.flip:
            active_socket = graph.active_node.inputs[self.active_socket_index].type
        else:
            active_socket = graph.active_node.outputs[self.active_socket_index].type
        if active_socket == None: return

        temp_types = []
        for category, datas in graph.node_data.items():
            for node_data in datas:
                if string.lower() in node_data.bl_idname.lower():
                    # Match Active Inputs to Target Outputs
                    if self.flip:
                        if active_socket in node_data.outputs:
                            temp_types.append(node_data.bl_idname)
                    # Match Active Outputs to Target Inputs
                    else:
                        if active_socket in node_data.inputs:
                            temp_types.append(node_data.bl_idname)

        if temp_types:
            self.index = 0
            self.types = temp_types[:]
            bpy.ops.hops.display_notification(info=F'Found : {len(self.types)} Nodes')
        else:
            bpy.ops.hops.display_notification(info='Nothing Found')


    def set_flip(self, graph):
        active = graph.active_node
        if len(active.inputs) <= 0:
            bpy.ops.hops.display_notification(info=F'Node Doesnt Support Inputs')
            return

        self.flip = not self.flip
        self.build_types(graph)


    def scroll(self, context, event, scroll, graph):
        if graph.active_node == None: return
        graph.hide_active(hide=False)

        self.__ensure_indexes(graph)

        # Output increment
        if event.shift:
            self.__scroll_outputs(context, event, scroll, graph)
        # Categories
        if event.ctrl:
            self.__scroll_categories(scroll, graph)
        # Current Node
        else:
            self.__scroll_nodes(context, event, scroll, graph)

        # Validate
        if len(self.types) == 0:
            self.build_types(graph)
        elif self.index > len(self.types) - 1:
            self.index = 0
        elif self.index < 0:
            self.index = 0
        if len(self.types) == 0:
            return

        bl_idname = self.types[self.index]
        node_data = graph.find_node_data(bl_idname)
        if not node_data: return

        if self.flip:
            in_type = graph.active_node.inputs[self.active_socket_index].type
            for index, out_type in enumerate(node_data.outputs):
                if in_type == out_type:
                    self.target_sockect_index = index
                    break
        else:
            out_type = graph.active_node.outputs[self.active_socket_index].type
            for index, in_type in enumerate(node_data.inputs):
                if out_type == in_type:
                    self.target_sockect_index = index
                    break
                if out_type in {'VECTOR', 'RGBA'}:
                    if in_type in {'VECTOR', 'RGBA'}:
                        self.target_sockect_index = index
                        break

        self.create(graph)


    def __scroll_outputs(self, context, event, scroll, graph):
        # Get next
        moved = False

        if self.flip:
            for index, n_input in enumerate(graph.active_node.inputs):
                if n_input.enabled:
                    if index > self.active_socket_index:
                        self.active_socket_index = index
                        moved = True
                        break
            # End of list : Get first
            if not moved:
                for index, n_input in enumerate(graph.active_node.inputs):
                    if n_input.enabled:
                        self.active_socket_index = index
                        break

        else:
            for index, output in enumerate(graph.active_node.outputs):
                if output.enabled:
                    if index > self.active_socket_index:
                        self.active_socket_index = index
                        moved = True
                        break
            # End of list : Get first
            if not moved:
                for index, output in enumerate(graph.active_node.outputs):
                    if output.enabled:
                        self.active_socket_index = index
                        break

        # Recalc Types
        self.build_types(graph)

        # Set back the previous type
        if self.current_node:
            bl_idname = self.current_node.bl_idname
            if bl_idname in self.types:
                self.index = self.types.index(bl_idname)


    def __scroll_categories(self, scroll, graph):

        active_socket = None
        if self.flip:
            active_socket = graph.active_node.inputs[self.active_socket_index].type
        else:
            active_socket = graph.active_node.outputs[self.active_socket_index].type
        if active_socket == None: return

        # Get all possible matching nodes
        possible = [] # -> [ (category, [nodes]), (category, [nodes]), ]
        for category, datas in graph.node_data.items():
            temp_types = []
            for node_data in datas:
                # Match Active Inputs to Target Outputs
                if self.flip:
                    if active_socket in node_data.outputs:
                        temp_types.append(node_data.bl_idname)
                # Match Active Outputs to Target Inputs
                else:
                    if active_socket in node_data.inputs:
                        temp_types.append(node_data.bl_idname)
            possible.append( (category, temp_types) )

        # Basic clamping
        self.category_index += scroll
        if self.category_index < 0:
            self.category_index = len(possible) - 1
        elif self.category_index > len(possible) - 1:
            self.category_index = 0

        category, nodes = possible[self.category_index]

        if len(nodes) > 0:
            self.index = 0
            self.types = nodes[:]
            bpy.ops.hops.display_notification(info=F'{category} : {len(self.types)} Nodes')
        else:
            bpy.ops.hops.display_notification(info=F'No Matches in : {category}')


    def __scroll_nodes(self, context, event, scroll, graph):
        self.index += scroll
        if self.index > len(self.types) - 1:
            self.index = 0
        elif self.index < 0:
            self.index = len(self.types) - 1


    def build_types(self, graph, display_count=False):
        active = graph.active_node

        self.__ensure_indexes(graph)

        if self.flip:
            ins = [i for i in active.inputs]
            if not ins: return
            active_in = ins[self.active_socket_index].type
            self.types = []
            self.index = 0
            for category, datas in graph.node_data.items():
                for node_data in datas:
                    if active_in in node_data.outputs:
                        self.types.append(node_data.bl_idname)
        else:
            outs = [o for o in active.outputs]
            if not outs: return

            active_out = outs[self.active_socket_index].type
            self.types = []
            self.index = 0
            for category, datas in graph.node_data.items():
                for node_data in datas:
                    if active_out in node_data.inputs:
                        self.types.append(node_data.bl_idname)

                    elif active_out in {'VECTOR', 'RGBA'}:
                        if 'VECTOR' in node_data.inputs or 'RGBA' in node_data.inputs:
                            self.types.append(node_data.bl_idname)

        if display_count:
            bpy.ops.hops.display_notification(info=F'Reset : {len(self.types)} Nodes')


    def __ensure_indexes(self, graph):

        if self.active_socket_index < 0:
            self.active_socket_index = 0
        if self.target_sockect_index < 0:
            self.target_sockect_index = 0

        # --- ACTIVE NODE --- #

        active = graph.active_node
        valid_sockets = []

        # Valid Input Sockets
        if self.flip:
            for index, n_input in enumerate(active.inputs):
                if n_input.enabled:
                    valid_sockets.append(index)

        # Valid Output Sockets
        else:
            for index, outputs in enumerate(active.outputs):
                if outputs.enabled:
                    valid_sockets.append(index)

        # Set to valid socket
        if self.active_socket_index not in valid_sockets:
            if valid_sockets:
                self.active_socket_index = valid_sockets[0]
            else:
                self.active_socket_index = 0

        # --- TARGET NODE --- #

        if not self.current_node: return
        valid_sockets = []

        if self.flip:
            for index, n_input in enumerate(self.current_node.inputs):
                if n_input.enabled:
                    valid_sockets.append(index)
        else:
            for index, outputs in enumerate(self.current_node.outputs):
                if outputs.enabled:
                    valid_sockets.append(index)

        # Set to valid socket
        if self.target_sockect_index not in valid_sockets:
            if valid_sockets:
                self.target_sockect_index = valid_sockets[0]
            else:
                self.target_sockect_index = 0


    def create(self, graph):
        self.remove(graph)
        if self.index > len(self.types) - 1: return
        if self.index < 0: return
        if len(self.types) == 0: return

        node_type = self.types[self.index]
        self.current_node = graph.tree.nodes.new(node_type)

        location = graph.location
        dimensions = graph.dimensions

        self.current_node.location.x = location.x
        self.current_node.location.y = location.y

        graph.restore_connections()

        if self.flip:
            # Ensure
            valid = True
            if self.target_sockect_index > len(self.current_node.outputs) - 1:
                valid = False
            if self.active_socket_index > len(graph.active_node.inputs) - 1:
                valid = False
            if not valid:
                self.__ensure_indexes(graph)
                self.remove(graph)
                return

            self.current_node.location.x -= dimensions.x + 60
            output_slot = self.current_node.outputs[self.target_sockect_index]
            input_slot = graph.active_node.inputs[self.active_socket_index]
            graph.tree.links.new(output_slot, input_slot)

        else:
            # Ensure
            valid = True
            if self.active_socket_index > len(graph.active_node.outputs) - 1:
                valid = False
            if self.target_sockect_index > len(self.current_node.inputs) - 1:
                valid = False
            if not valid:
                self.__ensure_indexes(graph)
                self.remove(graph)
                return

            self.current_node.location.x += dimensions.x + 60
            output_slot = graph.active_node.outputs[self.active_socket_index]
            input_slot = self.current_node.inputs[self.target_sockect_index]
            graph.tree.links.new(output_slot, input_slot)


    def remove(self, graph):
        if not self.current_node: return
        graph.tree.nodes.remove(self.current_node)
        self.current_node = None


class IO_Filter:

    def __init__(self):
        self.type = ''
        self.inputs = []
        self.outputs = []


class All_Nodes:

    def __init__(self, context, graph):

        self.index = 0
        self.all_types = []
        self.types = []
        self.current_node = None
        self.cat_group = {}
        # Ctrl Scroll
        self.ctrl_scroll_index = 0
        # Filters
        self.__filter_str = ""
        self.cat_key = None
        self.input_type = 'ANY'
        self.output_type = 'ANY'
        self.io_data = []
        self.all_input_types = ['ANY']
        self.all_output_types = ['ANY']

        # Node Types
        category_data = node_categories(context)
        for key, val in category_data.items():
            self.cat_group[key] = []

            for node_type in val:
                if not hasattr(bpy.types, node_type): continue
                self.all_types.append(node_type)
                self.cat_group[key].append(node_type)

        self.types = self.all_types[:]

        # IO Filter
        for node_type in self.all_types:
            node = graph.tree.nodes.new(node_type)

            io_filter = IO_Filter()
            io_filter.type = node_type
            io_filter.inputs = [i.type for i in node.inputs]
            io_filter.outputs = [o.type for o in node.outputs]
            self.io_data.append(io_filter)

            graph.tree.nodes.remove(node)

        for io_filter in self.io_data:
            for i in io_filter.inputs:
                if i not in self.all_input_types:
                    self.all_input_types.append(i)
            for o in io_filter.outputs:
                if o not in self.all_output_types:
                    self.all_output_types.append(o)

    @property
    def filter_str(self):
        return self.__filter_str

    @filter_str.setter
    def filter_str(self, val):
        self.__filter_str = val
        self.index = 0
        self.types = []
        self.cat_key = None

        for t in self.all_types:
            t_name = getattr(bpy.types, t).bl_rna.name
            if self.__filter_str.lower() in t_name.lower():
                self.types.append(t)

        # Nothing Found : RESET
        if not self.types:
            self.__filter_str = ""
            self.types = self.all_types[:]
            bpy.ops.hops.display_notification(info='Nothing Found')
        else:
            bpy.ops.hops.display_notification(info=F'Found : {len(self.types)} Nodes')


    def scroll(self, context, event, scroll, graph):
        if graph.active_node != None:
            graph.hide_active(hide=False)

        # Scroll Categories
        if event.ctrl:
            for index, key in enumerate(self.cat_group.keys()):
                if self.ctrl_scroll_index == index:
                    self.set_cat_key(key)

            self.index = 0
            self.ctrl_scroll_index += scroll
            if self.ctrl_scroll_index > len(self.cat_group) - 1:
                self.ctrl_scroll_index = 0
            elif self.ctrl_scroll_index < 0:
                self.ctrl_scroll_index = len(self.cat_group) - 1

        # Scroll Types
        else:
            self.index += scroll
            if self.index > len(self.types) - 1:
                self.index = 0
            elif self.index < 0:
                self.index = len(self.types) - 1

        self.create(graph)


    def create(self, graph):
        self.remove(graph)
        node_type = self.types[self.index]
        self.current_node = graph.tree.nodes.new(node_type)
        location = graph.location
        dimensions = graph.dimensions
        self.current_node.location.x = location.x
        self.current_node.location.y = location.y
        self.current_node.location.y -= dimensions.y + 10


    def remove(self, graph):
        if not self.current_node: return
        graph.tree.nodes.remove(self.current_node)
        self.current_node = None

    # --- FORM --- #

    def cat_highlight(self, val):
        return self.cat_key == val


    def set_cat_key(self, val):
        if val not in self.cat_group: return
        self.__filter_str = ""
        self.cat_key = val
        self.types = self.cat_group[self.cat_key][:]
        bpy.ops.hops.display_notification(info=f'Scrolling {val} : {len(self.types)}')


    def turn_off_cat_key(self):
        self.cat_key = None
        self.types = self.all_types[:]
        self.index = 0


    def key_active(self):
        return self.cat_key != None


    def set_io_filter_types(self):

        self.index = 0
        self.__filter_str = ""
        self.cat_key = None
        self.types = []

        for io_filter in self.io_data:
            # Compare Inputs
            in_valid = False
            if self.input_type != 'ANY':
                if self.input_type in io_filter.inputs:
                    in_valid = True
            else: in_valid = True

            # Compare Outputs
            out_valid = False
            if self.output_type != 'ANY':
                if self.output_type in io_filter.outputs:
                    out_valid = True
            else: out_valid = True

            if in_valid and out_valid:
                if io_filter.type not in self.types:
                    self.types.append(io_filter.type)

        if not self.types:
            self.types = self.all_types[:]
            bpy.ops.hops.display_notification(info='Nothing Found')

        else:
            bpy.ops.hops.display_notification(info=f'Found : {len(self.types)}')


    def reset_to_all(self):
        self.index = 0
        self.types = self.all_types[:]
        bpy.ops.hops.display_notification(info='Scroll All')


DESC = """Scroll Geo Nodes

Shift : Append Mode

Press H for help"""


class HOPS_OT_Cycle_Geo_Nodes(bpy.types.Operator):
    bl_idname = "hops.cycle_geo_nodes"
    bl_label = "Cycle Geo Nodes"
    bl_description = DESC
    bl_options = {"REGISTER", "UNDO", "BLOCKING"}

    @classmethod
    def poll(cls, context):
        if context.area:
            if context.area.ui_type in {'ShaderNodeTree'} or (bpy.app.version < (3, 4) and context.area.ui_type =='GeometryNodeTree'):
                return True
        return False


    def invoke(self, context, event):
        # Validate
        if not validate_context(context):
            return {'CANCELLED'}

        # Entry
        mode = Modes.RELATED
        if event.shift:
            mode = Modes.APPEND

        # Tool Shelf
        self.show_region = bpy.context.space_data.show_region_ui
        bpy.context.space_data.show_region_ui = False

        # Modes
        self.mode = mode
        self.graph = Graph(context)
        self.related_nodes = Related_Nodes(context, self.graph)
        self.category_nodes = Category_Nodes(context, self.graph)
        self.append_nodes = Append_Nodes(context, self.graph)
        self.all_nodes = All_Nodes(context, self.graph)

        if self.graph.active_node == None or self.graph.active_node.select == False:
            self.mode = Modes.ALL

        # Form
        self.form_exit = False
        self.form = None
        self.setup_form(context, event)
        self.draw_handle_2D = bpy.types.SpaceNodeEditor.draw_handler_add(self.safe_draw_2D, (context,), 'WINDOW', 'POST_PIXEL')

        # Input
        self.dialogue = Dialogue(context, self.set_dialogue, help_text="Filter Input")

        # Base Systems
        self.master = Master(context)
        self.master.only_use_fast_ui = True
        self.base_controls = Base_Modal_Controls(context, event)
        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}


    def modal(self, context, event):

        self.base_controls.update(context, event)

        if self.mode == Modes.ALL:
            self.form.update(context, event)

        skip_m_h = self.form.active()
        self.master.receive_event(event, skip_m_h)

        unblocked = True
        if self.dialogue.active or self.form.active():
            unblocked = False

        if self.base_controls.pass_through:
            if unblocked:
                return {'PASS_THROUGH'}

        elif self.base_controls.confirm:
            if unblocked:
                return self.confirm_exit(context)

        elif self.base_controls.cancel:
            if unblocked:
                return self.cancel_exit(context)

        if event.type == 'TAB' and event.value == 'PRESS':
            if not self.dialogue.active:
                if self.form.is_dot_open():
                    self.form.close_dot()
                else:
                    self.mode = Modes.ALL
                    self.alter_form_layout()
                    self.form.open_dot()
                    self.remove_all_created()
                    bpy.ops.hops.display_notification(info=F'Mode : {self.mode.name}')

        # Dialogue Menu : Update
        if self.dialogue.active:
            self.dialogue.update(event)

        # Actions
        if unblocked:
            self.actions(context, event)

        self.interface(context)
        context.area.tag_redraw()

        # Update parenting draw
        if self.mode == Modes.CATEGORIES:
            self.category_nodes.late_update()

        return {"RUNNING_MODAL"}


    def actions(self, context, event):

        # Tool Shelf
        if event.type == 'N' and event.value == 'PRESS':
            return {'PASS_THROUGH'}

        # All Mode
        elif event.type == 'E' and event.value == 'PRESS':
            self.remove_all_created()
            self.mode = Modes.ALL
            self.alter_form_layout()

        # Cycle Nodes
        elif self.base_controls.scroll:
            scroll = self.base_controls.scroll

            if self.mode == Modes.RELATED:
                self.related_nodes.scroll(context, scroll, self.graph)
            elif self.mode == Modes.CATEGORIES:
                self.category_nodes.scroll(context, scroll, self.graph)
            elif self.mode == Modes.APPEND:
                self.append_nodes.scroll(context, event, scroll, self.graph)
            elif self.mode == Modes.ALL:
                self.all_nodes.scroll(context, event, scroll, self.graph)

        # Append Modes
        elif event.type == 'A' and event.value == 'PRESS':
            if self.append_nodes.valid:
                if self.graph.active_node != None:
                    self.remove_all_created()
                    self.mode = Modes.APPEND
                    bpy.ops.hops.display_notification(info=F'Mode : {self.mode.name}')
            else:
                bpy.ops.hops.display_notification(info="Invalid Active Node")

            self.alter_form_layout()

        # Cycle Modes
        elif event.type == 'C' and event.value == 'PRESS':
            self.set_modes()
            self.alter_form_layout()

        # Dialogue Menu : Spawn
        if self.mode in {Modes.ALL, Modes.APPEND}:
            if event.type == 'S' and event.value == 'PRESS':
                self.dialogue.start()

        # Append Mode
        if self.mode == Modes.APPEND:
            # Clear Filters
            if event.type == 'R' and event.value == 'PRESS':
                self.append_nodes.build_types(self.graph, display_count=True)

            # Flip side
            if event.type == 'F' and event.value == 'PRESS':
                self.append_nodes.set_flip(self.graph)


    def interface(self, context):

        self.master.setup()
        if not self.master.should_build_fast_ui(): return

        # Main
        win_list = []
        w_append = win_list.append

        # Help
        help_items = {"GLOBAL" : [], "STANDARD" : []}

        help_items["GLOBAL"] = [
            ("H", "Toggle help"),
            ("N", "Toggle Side Panel"),
            ("~", "Toggle UI Display Type"),]

        h_append = help_items["STANDARD"].append
        h_append(('TAB' , 'Dot UI'))

        if self.related_nodes.valid:
            h_append(('C', 'Cycle Modes'))

        if self.mode == Modes.RELATED:
            w_append('Related Mode')
            if self.related_nodes.current_node:
                w_append(self.related_nodes.current_node.name)

            h_append(('Scroll', 'Cycle Relative'))

        elif self.mode == Modes.CATEGORIES:
            w_append('Category Mode')
            w_append(self.category_nodes.current_category_name)

            h_append(('Scroll', 'Cycle Categories'))

        elif self.mode == Modes.APPEND:
            w_append('Append Mode')
            if self.append_nodes.current_node:
                w_append(self.append_nodes.current_node.name)

            h_append(('Scroll', 'Cycle All Nodes'))
            h_append(('Shift', 'Cycle Ouput Socket'))
            h_append(('Ctrl', 'Cycle Categories'))
            h_append(('S', 'Filter Dialogue'))
            h_append(('R', 'Reset Filter'))

        elif self.mode == Modes.ALL:
            w_append('All Mode')
            if self.all_nodes.current_node:
                w_append(self.all_nodes.current_node.name)

            h_append(('Scroll', 'Cycle All Nodes'))
            h_append(('Ctrl Scroll', 'Category Filter'))
            h_append(('S', 'Filter Dialogue'))

        if self.mode != Modes.APPEND:
            if self.append_nodes.valid:
                h_append(('A', 'Append Mode'))

        h_append(('E' , 'Every Node'))
        h_append(('C' , 'Cycle Modes'))

        help_items["STANDARD"].reverse()

        nodes_list = []
        active_node = ""
        if not self.form.is_dot_open():
            if self.mode == Modes.ALL:
                current_node = None if self.all_nodes.current_node == None else self.all_nodes.current_node.bl_rna.name
                for t in self.all_nodes.types:
                    t_name = getattr(bpy.types, t).bl_rna.name
                    nodes_list.append([t_name, ""])
                    if current_node == t_name:
                        active_node = t_name

            elif self.mode == Modes.APPEND:
                current_node = None if self.append_nodes.current_node == None else self.append_nodes.current_node.bl_rna.name
                for t in self.append_nodes.types:
                    t_name = getattr(bpy.types, t).bl_rna.name
                    nodes_list.append([t_name, ""])
                    if current_node == t_name:
                        active_node = t_name

            elif self.mode == Modes.CATEGORIES:
                current_node = self.category_nodes.current_category_name
                for t in self.category_nodes.keys:
                    nodes_list.append([t, ""])
                    if current_node == t:
                        active_node = t

            elif self.mode == Modes.RELATED:
                current_node = None if self.related_nodes.current_node == None else self.related_nodes.current_node.bl_rna.name
                for t in self.related_nodes.types:
                    t_name = getattr(bpy.types, t).bl_rna.name
                    nodes_list.append([t_name, ""])
                    if current_node == t_name:
                        active_node = t_name

        self.master.receive_fast_ui(win_list=win_list, help_list=help_items, mods_list=nodes_list, active_mod_name=active_node, image="Array")
        self.master.finished()

    # --- FORM --- #

    def setup_form(self, context, event):
        self.form = form.Form(context, event, dot_open=False)

        def spacer(height=10, label='', active=True):
            row = self.form.row()
            row.add_element(form.Spacer(height=height))
            self.form.row_insert(row, label, active)

        # --- All --- #
        row = self.form.row()
        tips = ["Turn off Categories"]
        row.add_element(form.Button(
            scroll_enabled=False, text='X', highlight_text='✓', tips=tips,
            width=25, height=20, use_padding=False,
            callback=self.all_nodes.turn_off_cat_key,
            highlight_hook=self.all_nodes.key_active))
        tips = ["Filter Nodes"]
        row.add_element(form.Text_Input(obj=self.all_nodes, attr="filter_str", tips=tips, width=115, height=20))
        self.form.row_insert(row, label='ALL', active=self.mode == Modes.ALL)

        spacer(height=5, label='ALL', active=self.mode == Modes.ALL)

        row = self.form.row()
        group = self.categories_group(context)
        self.cat_box = form.Scroll_Box(width=140, height=60, scroll_group=group, view_scroll_enabled=True)
        row.add_element(self.cat_box)
        self.form.row_insert(row, label="ALL", active=self.mode == Modes.ALL)

        spacer(height=5, label='ALL', active=self.mode == Modes.ALL)

        row = self.form.row()
        row.add_element(form.Dropdown(
            width=100, tips=["Inputs"],
            options=self.all_nodes.all_input_types,
            obj=self.all_nodes, attr='input_type'))
        row.add_element(form.Button(
            scroll_enabled=False, text='F', tips=["Filter"],
            width=25, height=20, use_padding=False,
            callback=self.all_nodes.set_io_filter_types))
        self.form.row_insert(row, label='ALL', active=self.mode == Modes.ALL)

        row = self.form.row()
        row.add_element(form.Dropdown(
            width=100, tips=["Outputs"],
            options=self.all_nodes.all_output_types,
            obj=self.all_nodes, attr='output_type'))
        row.add_element(form.Button(
            scroll_enabled=False, text='R', tips=["Reset"],
            width=25, height=20, use_padding=False,
            callback=self.all_nodes.reset_to_all))
        self.form.row_insert(row, label='ALL', active=self.mode == Modes.ALL)

        self.form.build()


    def categories_group(self, context):

        group = form.Scroll_Group()
        index = 1
        for cat, types in self.all_nodes.cat_group.items():
            row = group.row()

            row.add_element(form.Label(text=str(index), width=25, height=20))

            tip = []
            text = form.shortened_text(cat, width=70, font_size=12)
            tip = tip if text == cat else [cat]

            row.add_element(form.Button(
                scroll_enabled=False, text=text, tips=tip,
                width=95, height=20, use_padding=False,
                callback=self.all_nodes.set_cat_key, pos_args=(cat,), neg_args=(cat,),
                highlight_hook=self.all_nodes.cat_highlight, highlight_hook_args=(cat,)))

            group.row_insert(row)
            index += 1

        return group


    def alter_form_layout(self):
        if self.mode == Modes.RELATED:
            self.form.row_activation(label='RELATED', active=True)
            self.form.row_activation(label='CATEGORIES', active=False)
            self.form.row_activation(label='APPEND', active=False)
            self.form.row_activation(label='ALL', active=False)
        elif self.mode == Modes.CATEGORIES:
            self.form.row_activation(label='RELATED', active=False)
            self.form.row_activation(label='CATEGORIES', active=True)
            self.form.row_activation(label='APPEND', active=False)
            self.form.row_activation(label='ALL', active=False)
        elif self.mode == Modes.APPEND:
            self.form.row_activation(label='RELATED', active=False)
            self.form.row_activation(label='CATEGORIES', active=False)
            self.form.row_activation(label='APPEND', active=True)
            self.form.row_activation(label='ALL', active=False)
        elif self.mode == Modes.ALL:
            self.form.row_activation(label='RELATED', active=False)
            self.form.row_activation(label='CATEGORIES', active=False)
            self.form.row_activation(label='APPEND', active=False)
            self.form.row_activation(label='ALL', active=True)
        self.form.build(preserve_top_left=True)

        if self.mode != Modes.ALL:
            if self.form.is_dot_open():
                self.form.close_dot()

    # --- UTILS --- #

    def remove_all_created(self):
        self.related_nodes.remove(self.graph)
        self.category_nodes.remove(self.graph)
        self.append_nodes.remove(self.graph)
        self.all_nodes.remove(self.graph)


    def set_modes(self):
        self.remove_all_created()

        # No Active node
        if self.graph.active_node == None:
            if self.mode == Modes.CATEGORIES:
                self.mode = Modes.ALL
            else:
                self.mode = Modes.CATEGORIES
            return

        if self.mode == Modes.RELATED:
            self.mode = Modes.CATEGORIES
        elif self.mode == Modes.CATEGORIES:
            self.mode = Modes.APPEND
        elif self.mode == Modes.APPEND:
            self.mode = Modes.ALL
        elif self.mode == Modes.ALL:
            self.mode = Modes.RELATED

        if self.mode == Modes.APPEND:
            if not self.append_nodes.valid:
                self.mode = Modes.CATEGORIES

        bpy.ops.hops.display_notification(info=F'Mode : {self.mode.name}')


    def set_dialogue(self, string):
        if self.mode == Modes.APPEND:
            self.append_nodes.filter_types(self.graph, string)
        elif self.mode == Modes.ALL:
            self.all_nodes.filter_str = string

    # --- EXITS --- #

    def common_exit(self, context):
        self.remove_shaders()
        self.form.shut_down(context)
        self.master.run_fade()
        bpy.context.space_data.show_region_ui = self.show_region
        context.area.tag_redraw()


    def confirm_exit(self, context):
        self.graph.hide_active(hide=False)
        self.common_exit(context)

        if self.mode == Modes.ALL:
            if self.all_nodes.current_node:
                bpy.ops.node.select_all(action='DESELECT')
                self.all_nodes.current_node.select = True
                self.graph.tree.nodes.active = self.all_nodes.current_node
        elif self.mode == Modes.APPEND:
            if self.append_nodes.current_node:
                bpy.ops.node.select_all(action='DESELECT')
                self.append_nodes.current_node.select = True
                self.graph.tree.nodes.active = self.append_nodes.current_node
        elif self.mode == Modes.RELATED:
            if self.related_nodes.current_node:
                bpy.ops.node.select_all(action='DESELECT')
                self.related_nodes.current_node.select = True
                self.graph.tree.nodes.active = self.related_nodes.current_node

        return {'FINISHED'}


    def cancel_exit(self, context):
        self.remove_all_created()
        self.graph.hide_active(hide=False)

        self.common_exit(context)
        return {'CANCELLED'}

    # --- SHADERS --- #

    def remove_shaders(self):
        if self.draw_handle_2D:
            self.draw_handle_2D = bpy.types.SpaceNodeEditor.draw_handler_remove(self.draw_handle_2D, "WINDOW")


    def safe_draw_2D(self, context):
        method_handler(self.draw_shader_2D,
            arguments = (context,),
            identifier = 'Modal Shader 2D',
            exit_method = self.remove_shaders)


    def draw_shader_2D(self, context):
        if self.mode == Modes.ALL:
            self.form.draw()

        if self.mode in {Modes.ALL, Modes.APPEND}:
            self.dialogue.draw()

# --- UTILS --- #

def validate_context(context):
    valid_context = False
    if hasattr(context, 'area'):
        if hasattr(context.area, 'spaces'):
            if hasattr(context.area.spaces, 'active'):
                if hasattr(context.area.spaces.active, 'edit_tree'):
                    valid_context = True
    return valid_context