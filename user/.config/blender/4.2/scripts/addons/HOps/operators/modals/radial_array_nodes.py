import bpy, pathlib
from mathutils import Vector
from .geometry_nodes.radial_array import radial_array_nodes, BLEND_FILE_NAME

from ... utility import addon, method_handler, operator_override, context_copy
from ...ui_framework.master import Master
from ...ui_framework.utils.mods_list import get_mods_list
from ...utility.base_modal_controls import Base_Modal_Controls

# Cursor Warp imports
from ...utils.toggle_view3d_panels import collapse_3D_view_panels
from ...utils.modal_frame_drawing import draw_modal_frame
from ...utils.cursor_warp import mouse_warp

DEF_NODEGROUP_NAME = 'HOPS_Radial_Array'
LAST_GROUP_NAME = ''


# list input types to validate group integrity
GROUP_INPUT_TYPES = [
    'GEOMETRY', # geometry
    'INT', # count
    'VECTOR', # axis
    'VALUE',  # rotation
    'VALUE', # offset
    'BOOLEAN', # apply scale
    'BOOLEAN', # center pivot
    'BOOLEAN', # full circle
    'VECTOR', # pivot offset
    'VECTOR', # rotation offset
    'OBJECT', # self
]

GROUP_INPUT_TYPES_INTERFACE = [
    'NodeSocketGeometry',  # geometry
    'NodeSocketInt', # count
    'NodeSocketVector', # axis
    'NodeSocketFloat', # rotation
    'NodeSocketFloat',  # offset
    'NodeSocketBool', # apply scale
    'NodeSocketBool', # center pivot
    'NodeSocketBool', # full circle
    'NodeSocketVector', # pivot offset
    'NodeSocketVector', # rotation offset
    'NodeSocketObject', # self
]

ROTAIONS = [
    (360.0, True),
    (180.0, False),
    (90.0, False),
    (45.0, False),
    (30.0, False),
    (15.0, False),
]

PIVOT_BASE = 0
PIVOT_OFFSET = 1
PIVOT_CENTER = 2
PIVOT_CURSOR = 3
PIVOT_OBJECT = 4

PIVOT_STATES = [
    PIVOT_BASE,
    PIVOT_OFFSET,
    PIVOT_CENTER,
    PIVOT_CURSOR,
    PIVOT_OBJECT,
]
PIVOT_NAMES = [
    'ORIGIN',
    'ORIGIN OFFSET',
    'CENTER',
    'CURSOR',
    'ACTIVE OBJECT',
]

def get_node_group():
    global LAST_GROUP_NAME
    global DEF_NODEGROUP_NAME

    def find_loaded():
        def ft (node_group):
            if not node_group.library_weak_reference: return False
            return pathlib.Path(node_group.library_weak_reference.filepath).name == BLEND_FILE_NAME

        return list(filter(ft, bpy.data.node_groups))

    group = None

    if BLEND_FILE_NAME in bpy.data.libraries:

        if LAST_GROUP_NAME:
            group = bpy.data.node_groups.get(LAST_GROUP_NAME)

            if group:
                if not is_valid(group):
                    group = None
            else:
                loaded_groups = find_loaded()

                # there can only be one
                if loaded_groups and is_valid(loaded_groups[0]):
                    group = loaded_groups[0]

    if not group:
        group = radial_array_nodes()

    LAST_GROUP_NAME = group.name
    return group


def is_valid(node_group) -> bool:
    global GROUP_INPUT_TYPES
    global LAST_GROUP_NAME

    socket_type = 'type'

    if hasattr(node_group, 'interface'):
        group_inputs = [s for s in node_group.interface.items_tree if s.in_out=='INPUT']
        socket_type = 'socket_type'
        type_table = GROUP_INPUT_TYPES_INTERFACE

    else:
        group_inputs = node_group.inputs
        type_table = GROUP_INPUT_TYPES

    if len(group_inputs) < len(GROUP_INPUT_TYPES): return False
    for type, input in zip(type_table, group_inputs):
        if type != getattr(input, socket_type): return False

    LAST_GROUP_NAME = node_group.name

    return True

def get_modifier(object):
    for mod in reversed(object.modifiers):
        if mod.type != 'NODES': continue
        if not mod.node_group: continue
        if LAST_GROUP_NAME not in mod.node_group.name: continue

        if is_valid(mod.node_group): return mod

def is_rad_array(mod):
    if mod.type != 'NODES': return False
    if not mod.node_group: return False
    if LAST_GROUP_NAME not in mod.node_group.name: return False

    if is_valid(mod.node_group): return True

    False

class RadArray():
    backup = None

    @property
    def count(self):
        return self.modifier[self.input_map[1]]

    @count.setter
    def count(self, value):
        if value < 1:
            value = 1

        self.modifier[self.input_map[1]] = value
        self.update()

    @property
    def axis(self):
        return self.modifier[self.input_map[2]]

    @axis.setter
    def axis(self, value):
        prop = self.modifier[self.input_map[2]]
        for i in range(3):
            val = value[i]
            if val > 1.0: val = 1.0
            elif val < 1.0: val = 0.0

            prop[i] = val

        self.update()

    @property
    def rotation(self):
        return self.modifier[self.input_map[3]]

    @rotation.setter
    def rotation(self, value):
        val = value
        if value < 0.0:
            val = 0.0
        elif value > 360.0:
            val = 360.0

        self.modifier[self.input_map[3]] = val
        self.update()

    @property
    def offset(self):
        return self.modifier[self.input_map[4]]

    @offset.setter
    def offset(self, value):
        self.modifier[self.input_map[4]] = value
        self.update()

    @property
    def apply_scale(self):
        return self.modifier[self.input_map[5]]

    @apply_scale.setter
    def apply_scale(self, value):
        self.modifier[self.input_map[5]] = value
        self.update()

    @property
    def center_pivot(self):
        return self.modifier[self.input_map[6]]

    @center_pivot.setter
    def center_pivot(self, value):
        self.modifier[self.input_map[6]] = value
        self.update()

    @property
    def full_circle(self):
        return self.modifier[self.input_map[7]]

    @full_circle.setter
    def full_circle(self, value):
        self.modifier[self.input_map[7]] = value
        self.update()

    @property
    def pivot_offset(self):
        return self.modifier[self.input_map[8]]

    @pivot_offset.setter
    def pivot_offset(self, value):
        input = self.modifier[self.input_map[8]]

        input[0] = value[0]
        input[1] = value[1]
        input[2] = value[2]
        self.update()

    @property
    def rotation_offset(self):
        return self.modifier[self.input_map[9]]

    @rotation_offset.setter
    def rotation_offset(self, value):
        input = self.modifier[self.input_map[9]]

        input[0] = value[0]
        input[1] = value[1]
        input[2] = value[2]
        self.update()

    @property
    def self(self):
        return self.modifier[self.input_map[10]]

    @self.setter
    def self(self, value):
        self.modifier[self.input_map[10]] = value
        self.update()

    def __init__(self, modifier) -> None:
        if bpy.app.version[0] > 3:
            self.input_map = [input.identifier for input in modifier.node_group.interface.items_tree if input.in_out=='INPUT']

        else:
            self.input_map = [input.identifier for input in modifier.node_group.inputs]

        self.modifier = modifier
        self.st_offset = self.offset
        self.index = self.start_index = modifier.id_data.modifiers.find(modifier.name)

        self.stored_pivot_offset = Vector(self.pivot_offset)
        self.stored_rotation_offset = Vector(self.rotation_offset)

        if modifier.id_data.type in {'CURVE', 'FONT'}:
            self.update = self.update_curve

        else:
            self.update = self.update_mesh

    def set_defaults(self):
        self.count = 3
        self.axis = 0.0, 0.0, 1.0
        self.rotation = 360.0
        self.offset = 0.0
        self.apply_scale = False
        self.center_pivot = False
        self.full_circle = True
        self.self = self.modifier.id_data

    def store_backup(self):
        self.backup = []

        for input in self.modifier.node_group.inputs[1:]:
            if input.type in {'RGBA', 'VECTOR'}:
                self.backup.append((input.identifier, self.modifier[input.identifier][:], True))
            else:
                self.backup.append((input.identifier, self.modifier[input.identifier], False))

    def restore_backup(self):
        for name, value, iterable in self.backup:
            if iterable:
                prop = self.modifier[name]
                for i, value in enumerate(value):
                    prop[i] = value

            else:
                self.modifier[name] = value

        self.update()

    def cycle_pivot_offset(self, val):
        if val == PIVOT_BASE:
            self.center_pivot = False
            self.pivot_offset = Vector()
            self.rotation_offset = Vector()

        elif val == PIVOT_OFFSET:
            self.center_pivot = False
            self.pivot_offset = self.stored_pivot_offset
            self.rotation_offset = self.stored_rotation_offset

        elif val == PIVOT_CENTER:
            self.center_pivot = True

        elif val == PIVOT_CURSOR:
            self.center_pivot = False
            self.update_pivot_offset(bpy.context.scene.cursor.matrix)

        elif val == PIVOT_OBJECT:
            self.center_pivot = False
            self.update_pivot_offset(bpy.context.active_object.matrix_world)

    def update_mesh(self):
        self.modifier.id_data.data.update()

    def update_curve(self):
        self.modifier.id_data.data.splines.update()
        for area in bpy.context.screen.areas:
            if area.type not in {'VIEW_3D', 'PROPERTIES'}: continue
            area.tag_redraw()

    def update_pivot_offset(self, pivot_matrix_world):
        mat = self.modifier.id_data.matrix_world.normalized().inverted() @ pivot_matrix_world

        loc, rot, _ = mat.decompose()
        self.pivot_offset = loc
        self.rotation_offset = rot.to_euler()

class ModObject():
    object = None
    modifiers: list[RadArray]
    _index: int
    mod_count: int

    @property
    def active_mod(self):
        return self.modifiers[self.index]

    @property
    def index(self):
        return self._index

    @index.setter
    def index(self, value):
        self._index = value % len(self.modifiers)

    def __init__(self, object) -> None:
        self.modifiers = [RadArray(mod) for mod in object.modifiers if is_rad_array(mod)]
        self._index = len(self.modifiers) - 1
        self.object = object
        self.mod_count = len(object.modifiers)

    def create_array(self):
        mod = self.object.modifiers.new(DEF_NODEGROUP_NAME, 'NODES')
        mod.node_group = get_node_group()
        mod.show_expanded = False
        modifier = RadArray(mod)
        modifier.set_defaults()

        self._index = len(self.modifiers)
        self.modifiers.append(modifier)
        self.mod_count += 1

    def move_mod(self, direction:int):
        override = context_copy(bpy.context)
        override['active_object'] = self.object
        override['object'] = self.object

        if direction > 0:
            if self.active_mod.index == self.mod_count - 1:
                return
            self.active_mod.index += direction

            operator_override(bpy.context, bpy.ops.object.modifier_move_down, override, modifier=self.active_mod.modifier.name)

        else:
            if self.active_mod.index == 0:
                return
            self.active_mod.index -= 1

            operator_override(bpy.context, bpy.ops.object.modifier_move_up, override, modifier=self.active_mod.modifier.name)


    @staticmethod
    def store_mod(mod) -> RadArray:
        modifier = RadArray(mod)
        modifier.store_backup()

        return modifier

class HOPS_OT_RadialArrayNodes(bpy.types.Operator):
    bl_idname = "hops.radial_array_nodes"
    bl_label = "Radial Array Nodes"
    bl_options = {'REGISTER', 'UNDO', 'BLOCKING'}
    bl_description = """Radial Array Nodes (V2) \n
LMB - Create/Adjust radial array
SHIFT + LMB - Array selection around active object
CTRL + LMB - Create new radial array
"""

    valid_objects = {'MESH', 'CURVE', 'FONT'}

    from_empty: bpy.props.BoolProperty()

    count: bpy.props.IntProperty(
        min=1,
        default=3,
    )

    @classmethod
    def poll(cls, context):
        return context.selected_objects

    def invoke(self, context, event):
        self.notify = lambda val: bpy.ops.hops.display_notification(info=val) if addon.preference().ui.Hops_extra_info else lambda val: None
        self.rotation_index = 0
        self.objects = []
        self.active_index = 0
        self.adjust_offset = True
        self.pivots = PIVOT_STATES[:]
        self.pivot_index = 0

        if (context.active_object and context.active_object.type == 'EMPTY') or event.shift:
            if not context.active_object:
                msg = 'No active objeect to array around'
                self.notify(msg)
                self.report({'INFO'}, msg)

            self.objects = [ModObject(o) for o in context.selected_objects if o != context.active_object and o.type in self.valid_objects]
            if not self.objects:
                msg = 'No valid objects in selection'
                self.notify(msg)
                self.report({'INFO'}, msg)
                return {'CANCELLED'}

            for object in self.objects:
                self.create_modifier(object)
                object.active_mod.update_pivot_offset(context.active_object.matrix_world)

            self.adjust_offset = False
            self.pivots.remove(PIVOT_OFFSET)
            self.pivot_index = len(self.pivots) - 1

        elif event.ctrl:
            self.objects = [ModObject(o) for o in context.selected_objects if o.type in self.valid_objects]

            if not self.objects:
                msg = 'No valid objects in selection'
                self.notify(msg)
                self.report({'INFO'}, msg)
                return {'CANCELLED'}

            for i, object in enumerate(self.objects):
                self.create_modifier(object)
                modifier = object.active_mod
                if object.object == context.active_object:
                    self.active_index = i

            self.pivots.remove(PIVOT_OFFSET)

            if not context.active_object:
                self.pivots.remove(PIVOT_OBJECT)

        else:
            self.objects = [ModObject(o) for o in context.selected_objects if o.type in self.valid_objects]

            if not self.objects:
                msg = 'No valid objects in selection'
                self.notify(msg)
                self.report({'INFO'}, msg)
                return {'CANCELLED'}

            created_count = 0

            for i, object in enumerate(self.objects):

                if not object.modifiers:
                    modifier = self.create_modifier(object)
                    created_count += 1

                if object.object == context.active_object:
                    self.active_index = i

            if created_count == len(self.objects):
                self.pivots.remove(PIVOT_OFFSET)

            if not context.active_object:
                self.pivots.remove(PIVOT_OBJECT)

            modifier = self.objects[self.active_index].active_mod

            if modifier.center_pivot:
                self.pivot_index = self.pivots.index(PIVOT_CENTER)

            elif Vector(modifier.pivot_offset).magnitude or Vector(modifier.rotation_offset).magnitude:
                for i, val in enumerate(self.pivots):
                    if val == PIVOT_OFFSET:
                        self.pivot_index = i
                        break

        for object in self.objects:
            for mod in object.modifiers: mod.modifier.node_group = mod.modifier.node_group # refresh node trees

        self.axis_index = 0
        axis_val = 0.0

        for i, v in enumerate(Vector(self.objects[self.active_index].active_mod.axis).normalized()):
            if v > axis_val:
                self.axis_index = i
                axis_val = v

        # Base Systems
        self.master = Master(context=context)
        self.master.only_use_fast_ui = True
        self.base_controls = Base_Modal_Controls(context, event)
        self.original_tool_shelf, self.original_n_panel = collapse_3D_view_panels()
        self.draw_handle = bpy.types.SpaceView3D.draw_handler_add(self.safe_draw_shader, (context,), 'WINDOW', 'POST_PIXEL')

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


    def modal(self, context, event):

        # Base Systems
        self.master.receive_event(event=event)
        self.base_controls.update(context, event)
        mouse_warp(context, event)

        if self.base_controls.pass_through:
            return {'PASS_THROUGH'}

        elif self.base_controls.mouse:
            for object in self.objects:
                object.active_mod.st_offset += self.base_controls.mouse
                object.active_mod.offset = object.active_mod.st_offset * self.adjust_offset

        elif self.base_controls.scroll:
            if event.ctrl:
                for object in self.objects: object.active_mod.rotation += float(self.base_controls.scroll)

                self.report({'INFO'}, str(self.objects[self.active_index].active_mod.rotation))

            elif event.shift:
                self.objects[self.active_index].move_mod(self.base_controls.scroll * -1)

            else:
                for object in self.objects: object.active_mod.count += self.base_controls.scroll
                self.count += self.base_controls.scroll

                self.report({'INFO'}, str(self.objects[self.active_index].active_mod.count))

        elif event.type == 'A' and event.value == 'PRESS':
            self.adjust_offset = not self.adjust_offset

            for object in self.objects: object.active_mod.offset = object.active_mod.st_offset * self.adjust_offset
            self.notify(f'{"En" if self.adjust_offset else "Dis"}abled Offset')


        elif event.type == 'C' and event.value == 'PRESS':
            self.pivot_index = (self.pivot_index + 1) % len(self.pivots)
            pivot_index = PIVOT_STATES[self.pivots[self.pivot_index]]

            for object in self.objects: object.active_mod.cycle_pivot_offset(pivot_index)

            self.notify(f'Pivot: {PIVOT_NAMES[pivot_index]}')

        elif event.type == 'F' and event.value == 'PRESS':
            for object in self.objects: object.active_mod.full_circle = not object.active_mod.full_circle

            self.notify('Mode: ' + ('FULL' if self.objects[self.active_index].active_mod.full_circle else 'PARTIAL'))

        elif event.type == 'Q' and event.value == 'PRESS':
            for object in self.objects:
                object.index -= 1

            self.notify(f'Target Mod: {self.objects[self.active_index].active_mod.modifier.name}')

        elif event.type == 'E' and event.value == 'PRESS':
            for object in self.objects:
                object.index += 1

            self.notify(f'Target Mod: {self.objects[self.active_index].active_mod.modifier.name}')

        elif event.type == 'R' and event.value == 'PRESS':
            self.rotation_index = (self.rotation_index + 1) % len(ROTAIONS)
            for object in self.objects:
                object.active_mod.rotation = ROTAIONS[self.rotation_index][0]
                object.active_mod.full_circle = ROTAIONS[self.rotation_index][1]

            self.notify(f'Rotation: {ROTAIONS[self.rotation_index][0]}')

        elif event.type == 'S' and event.value == 'PRESS':
            for object in self.objects:
                object.active_mod.apply_scale = not object.active_mod.apply_scale
                pivot_index = PIVOT_STATES[self.pivots[self.pivot_index]]

                object.active_mod.cycle_pivot_offset(pivot_index)

            self.notify(f'Apply Scale: {bool(self.objects[self.active_index].active_mod.apply_scale)}')

        elif event.type == 'X' and event.value == 'PRESS':
            self.axis_index = (self.axis_index + 1) % 3
            axis = Vector()
            axis[self.axis_index] = 1.0
            self.notify('Axis:' + 'XYZ'[self.axis_index])

            for object in self.objects: object.active_mod.axis = axis

        if (event.type == 'ZERO' or event.type == 'NUMPAD_0') and event.value == 'PRESS':
            for object in self.objects:
                object.active_mod.offset = 0.0
                object.active_mod.st_offset = 0.0

        elif self.base_controls.confirm:
            self.count = self.objects[self.active_index].active_mod.count

            self.remove_shader()
            collapse_3D_view_panels(self.original_tool_shelf, self.original_n_panel)
            self.master.run_fade()
            self.report({'INFO'}, "FINISHED")
            return {'FINISHED'}

        elif self.base_controls.cancel:

            # for object in self.objects:
            #     for modifier in object.modifiers:
            #         if modifier.backup:
            #             modifier.restore_backup()
            #         else:
            #             obj = modifier.modifier.id_data
            #             obj.modifiers.remove(modifier.modifier)

            self.remove_shader()
            collapse_3D_view_panels(self.original_tool_shelf, self.original_n_panel)
            self.master.run_fade()
            self.report({'INFO'}, "CANCELLED")
            bpy.ops.ed.undo_push()
            bpy.ops.ed.undo()
            return {'CANCELLED'}


        self.draw_ui(context)
        context.area.tag_redraw()
        return {'RUNNING_MODAL'}

    def create_modifier(self, object:ModObject):
        object.create_array()
        object.active_mod.count = self.count

    def draw_ui(self, context):

        self.master.setup()

        # -- Fast UI -- #
        if self.master.should_build_fast_ui():

            # Main
            win_list = []

            modifier = self.objects[self.active_index].active_mod

            axis = Vector()
            axis[self.axis_index] = 1.0
            mod_axis = Vector(modifier.axis)
            axis = 'XYZ'[self.axis_index] if axis == mod_axis else f'{mod_axis[0]:.3f}, {mod_axis[1]:.3f}, {mod_axis[2]:.3f} '
            pivot_index = PIVOT_STATES[self.pivots[self.pivot_index]]

            if addon.preference().ui.Hops_modal_fast_ui_loc_options != 1:
                win_list.append(axis)
                win_list.append(f"{modifier.count}")
                win_list.append(f"{self.objects[self.active_index].active_mod.st_offset:.2f}" if self.adjust_offset else "[A]")
                if int(modifier.rotation) != '360':
                    win_list.append(int(modifier.rotation))

            else:
                win_list.append("Radial Array (V2)")
                win_list.append(axis)
                win_list.append(f"{modifier.count}")
                win_list.append(f"{self.objects[self.active_index].active_mod.st_offset:.3f}" if self.adjust_offset else "[A] Disabled")
                win_list.append(f"[C] {PIVOT_NAMES[pivot_index]}")
                #win_list.append('FULL' if modifier.full_circle else 'PARTIAL')

                if modifier.apply_scale:
                    win_list.append( f'SCALE APPLIED')

            # Help
            help_items = {"GLOBAL" : [], "STANDARD" : []}

            help_items["GLOBAL"] = [
                ("M", "Toggle mods list"),
                ("H", "Toggle help"),
                ("~", "Toggle UI Display Type"),
                ("O", "Toggle viewport rendering")]

            help_items["STANDARD"] = [
            ]

            help_append = help_items["STANDARD"].append
            circle_mode = "Full" if modifier.full_circle else "Partial"

            help_append(["0", "Clear Offset"])
            help_append(["A", "Toggle Offset", f"{self.adjust_offset}"])
            help_append(["F", "Circle Mode " + f"({circle_mode})"])
            help_append(["S", "Apply Scale"])
            help_append(["C", f"Pivot {PIVOT_NAMES[pivot_index]}"])
            help_append(["R", "Rotation Presets"])
            help_append(["X", "Rotation Axis"])
            help_append(["Q/E", "Select next/previous Radial Array"])
            help_append(["Shift + Scroll", f"Move Modifier Up/Down"])
            help_append(["Ctrl + Scroll", f"Adjust Rotation {modifier.rotation}"])
            help_append(["Scroll", "Adjust Count"])

            # Mods
            mods_list = get_mods_list(mods=self.objects[self.active_index].object.modifiers)
            name = self.objects[self.active_index].active_mod.modifier.name

            self.master.receive_fast_ui(win_list=win_list, help_list=help_items, image="ArrayCircle", mods_list=mods_list, active_mod_name=name)

        self.master.finished()

    ####################################################
    #   CURSOR WARP
    ####################################################

    def safe_draw_shader(self, context):
        method_handler(self.draw_shader,
            arguments = (context,),
            identifier = 'UI Framework',
            exit_method = self.remove_shader)


    def remove_shader(self):
        '''Remove shader handle.'''

        if self.draw_handle:
            self.draw_handle = bpy.types.SpaceView3D.draw_handler_remove(self.draw_handle, "WINDOW")


    def draw_shader(self, context):
        '''Draw shader handle.'''

        draw_modal_frame(context)
