from typing import List

import bpy
from bpy.props import BoolProperty, CollectionProperty, EnumProperty, StringProperty
from bpy.types import BooleanModifier, Context, Event, Modifier, Object, Operator, PropertyGroup, UILayout

from ... utility import addon
from ...ui_framework.operator_ui import Master as UIMaster
from ...utility.modifier import new as modifier_new
from ...utility.modifier import stored as modifier_stored

# You can't use this operator without geometry nodes.
try:
    from bpy.types import GeometryNodeObjectInfo, NodesModifier
    try:
        from bpy.types import GeometryNodeMeshBoolean
    except ImportError:
        from bpy.types import GeometryNodeBoolean as GeometryNodeMeshBoolean
except ImportError:
    GeometryNodeMeshBoolean, GeometryNodeObjectInfo, NodesModifier = [type(None)] * 3
    SUPPORT_GEOMETRY_NODES = False
else:
    SUPPORT_GEOMETRY_NODES = True


class BoolStackItem(PropertyGroup):
    name: StringProperty(name='Name', description='Name of the first/only modifier')
    select: BoolProperty(name='Select', description='Whether to (un)stack this item')
    booleans: StringProperty(name='Booleans', description='List of booleans to stack')

    def draw(self, layout: UILayout):
        icon = 'RADIOBUT_ON' if self.select else 'RADIOBUT_OFF'
        layout.prop(self, 'select', text=self.name, icon=icon, toggle=True)


class HOPS_OT_BoolStack(Operator):
    bl_idname = 'hops.bool_stack'
    bl_label = 'Hops Stack Booleans'
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = '\n'.join((
        'Geometry Node - Stack / Unstack',
        '',
        'Convert booleans into geometry nodes or geometry nodes into booleans.',
        '',
        'LMB - Stack mode.',
        'Alt - Unstack mode.',
        'Ctrl - Include exact booleans when stacking.',
        'Shift - Stack all booleans / unstack all node groups',  # Blender adds the last period.
    ))

    mode: EnumProperty(
        name='Mode',
        items=[
            ('STACK', 'Stack', 'Convert a set of consecutive boolean modifiers into a geometry nodes modifier'),
            ('UNSTACK', 'Unstack', 'Convert a geometry nodes modifier back into individual boolean modifiers'),
        ],
        default='STACK',
        options={'SKIP_SAVE'},
    )

    # Options for stack:
    stack_exact_booleans: BoolProperty(
        name='Stack Exact Booleans',
        description='Convert boolean modifiers that use the exact solver (nodes do not support it)',
        default=False,
        options={'SKIP_SAVE'},
    )

    stack_items: CollectionProperty(
        name='Stack Items',
        description='Property groups containing information about sets of booleans',
        type=BoolStackItem,
        options={'SKIP_SAVE'},
    )

    stack_items_exact: CollectionProperty(
        name='Stack Items Exact',
        description='Property groups containing information about sets of booleans (including exact booleans)',
        type=BoolStackItem,
        options={'SKIP_SAVE'},
    )

    # Options for unstack:
    unstack_items: CollectionProperty(
        name='Unstack Items',
        description='Property groups containing information about geometry nodes modifiers',
        type=BoolStackItem,
        options={'SKIP_SAVE'},
    )

    def get_items(self) -> List[BoolStackItem]:
        if self.mode == 'STACK':
            if not self.stack_exact_booleans:
                return self.stack_items
            else:
                return self.stack_items_exact

        elif self.mode == 'UNSTACK':
            return self.unstack_items

    def draw(self, context: Context):
        layout = self.layout.column(align=True)

        row = layout.row(align=True)
        row.prop(self, 'mode', expand=True)

        if self.mode == 'STACK':
            icon = 'CHECKBOX_HLT' if self.stack_exact_booleans else 'CHECKBOX_DEHLT'
            layout.prop(self, 'stack_exact_booleans', icon=icon, toggle=True)

        layout.separator()
        items = self.get_items()

        if items:
            for item in items:
                item.draw(layout)
        else:
            layout.label(text='No eligible modifiers found')

    @classmethod
    def poll(cls, context: Context) -> bool:
        if not SUPPORT_GEOMETRY_NODES:
            return False

        object: Object = context.active_object
        return (object is not None) and (object.type == 'MESH') and (object.mode == 'OBJECT')

    def invoke(self, context: Context, event: Event) -> set:
        object: Object = context.active_object

        # Remove dead booleans so they don't split up boolean sets.
        _remove_dead_boolean_modifiers(object)

        # Set options based on modifier keys.
        self.mode = 'UNSTACK' if event.alt else 'STACK'
        self.stack_exact_booleans = event.ctrl

        # Populate stack items.
        for modifier_set in _boolean_modifier_sets(object, False):
            item: BoolStackItem = self.stack_items.add()
            item.name = f'{modifier_set[0].name} - {modifier_set[-1].name}'
            item.select = event.shift
            item.booleans = repr([modifier.name for modifier in modifier_set])

        # Select first stack item.
        if self.stack_items:
            item: BoolStackItem = self.stack_items[0]
            item.select = True

        # Populate stack items (with exact).
        for modifier_set in _boolean_modifier_sets(object, True):
            item: BoolStackItem = self.stack_items_exact.add()
            item.name = f'{modifier_set[0].name} - {modifier_set[-1].name}'
            item.select = event.shift
            item.booleans = repr([modifier.name for modifier in modifier_set])

        # Select first stack item (with exact).
        if self.stack_items_exact:
            item: BoolStackItem = self.stack_items_exact[0]
            item.select = True

        # Populate unstack items.
        for modifier in _nodes_modifiers(object):
            item: BoolStackItem = self.unstack_items.add()
            item.name = modifier.name
            item.select = event.shift

        # Select last unstack item.
        if self.unstack_items:
            item: BoolStackItem = self.unstack_items[-1]
            item.select = True

        # Get the original modifier counts for the notification.
        self.original_boolean_count = len(list(filter(_check_boolean_modifier, object.modifiers)))
        self.original_nodes_count = len(list(filter(_check_nodes_modifier, object.modifiers)))

        # Execute before the notification to get converted modifier counts.
        self.execute(context)
        self.notification(context, event)

        return {'FINISHED'}

    def notification(self, context: Context, event: Event):
        object: Object = context.active_object
        items = self.get_items()

        if self.mode == 'STACK':
            draw_title = ['Boolean Stack']
            if items:
                draw_data = [
                    ['Convert Exact Booleans', self.stack_exact_booleans],
                    ['Convert All Sets', event.shift],
                    ['Node Groups Created', self.converted_nodes_count],
                    ['Booleans Removed', f'{self.converted_boolean_count} / {self.original_boolean_count}'],
                    ['Modifiers Total', len(object.modifiers)],
                ]
            elif self.stack_items_exact:  # Using exact would have given eligible modifiers.
                draw_data = [
                    ['No eligible modifiers found'],
                    ['Try including exact booleans'],
                ]
            else:
                draw_data = [['No eligible modifiers found']]

        elif self.mode == 'UNSTACK':
            draw_title = ['Boolean Unstack']
            if items:
                draw_data = [
                    ['Convert All Stacks', event.shift],
                    ['Booleans Created', f'{self.converted_boolean_count}'],
                    ['Node Groups Removed', f'{self.converted_nodes_count} / {self.original_nodes_count}'],
                    ['Modifiers Total', len(object.modifiers)],
                ]
            else:
                draw_data = [['No eligible modifiers found']]

        # Our UI code expects all items except the title to be in reverse order.
        draw_data.append(draw_title)
        draw_data.reverse()

        ui = UIMaster()
        ui.receive_draw_data(draw_data=draw_data)
        ui.draw(draw_bg=addon.preference().ui.Hops_operator_draw_bg, draw_border=addon.preference().ui.Hops_operator_draw_border)

    def execute(self, context: Context) -> set:
        object: Object = context.active_object
        items = self.get_items()

        # Keep track of converted modifier counts for the notification.
        self.converted_boolean_count = 0
        self.converted_nodes_count = 0

        if not items:
            self.report({'INFO'}, 'No eligible modifiers found')

        elif self.mode == 'STACK':
            self.execute_stack(object, items)
            self.report({'INFO'}, f'Consolidated {self.converted_boolean_count} booleans to {self.converted_nodes_count} node groups')

        elif self.mode == 'UNSTACK':
            self.execute_unstack(object, items)
            self.report({'INFO'}, f'Dissolved {self.converted_nodes_count} node groups to {self.converted_boolean_count} booleans')

        return {'FINISHED'}

    def execute_stack(self, object: Object, items: List[BoolStackItem]):
        for item in items:
            if not item.select:
                continue

            # Get the boolean modifiers for this item.
            boolean_modifiers: List[BooleanModifier] = [object.modifiers.get(name) for name in eval(item.booleans)]

            # Backup and remove all modifiers after the last boolean.
            stored_modifiers = _backup_modifiers(object, object.modifiers.find(boolean_modifiers[-1].name) + 1)

            # Include the number of booleans in the modifier name.
            nodes_modifier: NodesModifier = object.modifiers.new(f'{len(boolean_modifiers)} Booleans', 'NODES')
            nodes_modifier.show_expanded = False  # Collapse created modifiers.

            # Name the node group after the modifier and the object.
            node_group = bpy.data.node_groups.new(f'{nodes_modifier.name} ({object.name})', 'GeometryNodeTree')
            nodes_modifier.node_group = node_group

            input_node = node_group.nodes.new("NodeGroupInput")
            input_node.location = (-200, 0)
            output_node = node_group.nodes.new("NodeGroupOutput")
            output_node.location = (len(boolean_modifiers) * 200, 0)

            # Group I/O
            if bpy.app.version < (4, 0):
                node_group.inputs.clear()
                node_group.inputs.new("NodeSocketGeometry", "Geometry")
                node_group.outputs.clear()
                node_group.outputs.new("NodeSocketGeometry", "Geometry")

            else:
                node_group.interface.clear()
                node_group.interface.new_socket(socket_type="NodeSocketGeometry", name="Geometry", in_out='INPUT')
                node_group.interface.new_socket(socket_type="NodeSocketGeometry", name="Geometry", in_out='OUTPUT')

            # Store boolean nodes so we can link them later.
            boolean_nodes: List[GeometryNodeMeshBoolean] = []

            for index, boolean_modifier in enumerate(boolean_modifiers):
                boolean_node: GeometryNodeMeshBoolean = node_group.nodes.new(GeometryNodeMeshBoolean.__name__)
                boolean_node.location = (index * 200, 0)
                boolean_node.label = 'Boolean' + (' (Exact)' if boolean_modifier.solver == 'EXACT' else '')  # Store the solver in the node label.
                boolean_node.operation = boolean_modifier.operation

                # Link the boolean node with the previous boolean node.
                if boolean_nodes:
                    socket_index = 0 if boolean_node.operation == 'DIFFERENCE' else 1
                    node_group.links.new(boolean_node.inputs[socket_index], boolean_nodes[-1].outputs[0])
                boolean_nodes.append(boolean_node)

                object_node: GeometryNodeObjectInfo = node_group.nodes.new(GeometryNodeObjectInfo.__name__)
                object_node.location = (index * 200 - 200, -200)
                object_node.transform_space = 'RELATIVE'
                object_node.inputs['Object'].default_value = boolean_modifier.object

                # Link the boolean node with the corresponding object node.
                node_group.links.new(boolean_node.inputs[1], object_node.outputs[-1])

                # Remove the original boolean modifier after conversion.
                object.modifiers.remove(boolean_modifier)

                # Increment the boolean count.
                self.converted_boolean_count += 1

            # Link the first and last boolean nodes with the input and output nodes.
            socket_index = 0 if boolean_nodes[0].operation == 'DIFFERENCE' else 1
            node_group.links.new(boolean_nodes[0].inputs[socket_index], input_node.outputs[0])
            node_group.links.new(output_node.inputs[0], boolean_nodes[-1].outputs[0])

            # I like to deselect all nodes.
            for node in node_group.nodes.values():
                node.select = False

            # Restore all modifiers that were after the last boolean.
            _restore_modifiers(object, stored_modifiers)

            # Increment the nodes count.
            self.converted_nodes_count += 1

    def execute_unstack(self, object: Object, items: List[BoolStackItem]):
        for item in items:
            if not item.select:
                continue

            # Get the geometry nodes modifier and associated node group for this item.
            nodes_modifier: NodesModifier = object.modifiers.get(item.name)
            node_group = nodes_modifier.node_group

            # Backup and remove all modifiers after the nodes modifier.
            stored_modifiers = _backup_modifiers(object, object.modifiers.find(nodes_modifier.name) + 1)

            for link in sorted(node_group.links.values(), key=lambda link: link.to_node.name):
                if isinstance(link.to_node, GeometryNodeMeshBoolean) and isinstance(link.from_node, GeometryNodeObjectInfo):
                    boolean_node: GeometryNodeMeshBoolean = link.to_node
                    object_node: GeometryNodeObjectInfo = link.from_node

                    boolean_modifier: BooleanModifier = object.modifiers.new('Boolean', 'BOOLEAN')
                    boolean_modifier.show_expanded = False  # Collapse created modifiers.
                    boolean_modifier.solver = 'EXACT' if ('EXACT' in boolean_node.label.upper()) else 'FAST'  # Restore the solver from the node label.
                    boolean_modifier.operation = boolean_node.operation
                    boolean_modifier.object = object_node.inputs['Object'].default_value

                    # Increment the boolean count.
                    self.converted_boolean_count += 1

            # Remove the nodes modifier and associated node group.
            object.modifiers.remove(nodes_modifier)
            bpy.data.node_groups.remove(node_group)

            # Restore all modifiers that were after the nodes modifier.
            _restore_modifiers(object, stored_modifiers)

            # Increment the nodes count.
            self.converted_nodes_count += 1


def _backup_modifiers(object: Object, index: int) -> List[Modifier]:
    '''Backup and remove all modifiers after the given index.'''
    stored_modifiers: List[Modifier] = []

    for modifier in object.modifiers[index:]:
        stored_modifiers.append(modifier_stored(modifier))
        object.modifiers.remove(modifier)

    return stored_modifiers


def _restore_modifiers(object: Object, modifiers: List[Modifier]):
    '''Restore backed up modifiers to the end of the stack.'''
    for modifier in modifiers:
        modifier_new(object, mod=modifier)


def _boolean_modifier_sets(object: Object, convert_exact_booleans: bool) -> List[List[BooleanModifier]]:
    '''Get sets of consecutive eligible boolean modifiers.'''
    boolean_modifiers: List[BooleanModifier] = []
    boolean_sets: List[List[BooleanModifier]] = []

    for modifier in object.modifiers:
        # Add eligible modifiers to the list.
        if _check_boolean_modifier(modifier, convert_exact_booleans):
            boolean_modifiers.append(modifier)

        # If the set is not empty, add it and clear the list.
        elif boolean_modifiers:
            boolean_sets.append(boolean_modifiers.copy())
            boolean_modifiers.clear()

    # If the last modifier was eligible, add its set too.
    if boolean_modifiers:
        boolean_sets.append(boolean_modifiers)

    return boolean_sets


def _check_boolean_modifier(modifier: BooleanModifier, convert_exact_booleans: bool = True) -> bool:
    '''Check whether this is a valid boolean modifier for our use case.'''
    if isinstance(modifier, BooleanModifier) and (modifier.operand_type == 'OBJECT') and (modifier.object is not None):
        return convert_exact_booleans or (modifier.solver != 'EXACT')

    return False


def _remove_dead_boolean_modifiers(object: Object):
    '''Remove boolean modifiers with no cutter from this object.'''
    for modifier in object.modifiers.values():
        if isinstance(modifier, BooleanModifier):
            if modifier.operand_type == 'OBJECT':
                if modifier.object is None:
                    object.modifiers.remove(modifier)

            elif modifier.operand_type == 'COLLECTION':
                if modifier.collection is None:
                    object.modifiers.remove(modifier)


def _nodes_modifiers(object: Object) -> List[NodesModifier]:
    '''Get geometry nodes modifiers from the given object.'''
    nodes_modifiers: List[NodesModifier] = []

    for modifier in object.modifiers:
        if _check_nodes_modifier(modifier):
            nodes_modifiers.append(modifier)

    return nodes_modifiers


def _check_nodes_modifier(modifier: NodesModifier) -> bool:
    '''Check whether this is a valid nodes modifier for our use case.'''
    return isinstance(modifier, NodesModifier) and (modifier.node_group is not None)
