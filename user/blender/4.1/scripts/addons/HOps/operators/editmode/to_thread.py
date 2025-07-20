from math import copysign, cos, degrees, radians, sin, tau

import bmesh
import bpy
from bmesh.types import BMEdge, BMFace, BMVert
from mathutils import Euler, Matrix, Vector

from ...ui_framework.master import Master
from ...ui_framework.utils.mods_list import get_mods_list
from ...utility import addon, method_handler
from ...utility.base_modal_controls import Base_Modal_Controls
from ...utils.cursor_warp import mouse_warp
from ...utils.modal_frame_drawing import draw_modal_frame
from ...utils.toggle_view3d_panels import collapse_3D_view_panels
from .geometry_nodes.to_thread import NODE_GROUP_NAME, REQUIRED_SOCKETS, socket_table, to_thread_nodes


class HOPS_OT_ToThread(bpy.types.Operator):
    bl_idname = 'hops.to_thread'
    bl_label = 'To Thread'
    bl_options = {'REGISTER', 'UNDO', 'BLOCKING'}
    bl_description = 'Convert selected cylinder to thread'


    @classmethod
    def poll(cls, context: bpy.types.Context):
        return context.mode == 'EDIT_MESH'


    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):

        # Selection
        object = context.active_object
        object.update_from_editmode()
        self.scale, self.positions = self.apply_scale(object)
        parameters = self.to_cylinder(object)
        if not parameters:
            self.report({'WARNING'}, 'Selection must be a cylinder')
            return {'CANCELLED'}

        # Modifier
        self.modifier, self.table = self.get_modifier(object)
        if self.modifier:
            self.backup = self.backup_modifier(self.modifier, self.table)
        else:
            self.modifier, self.table = self.new_modifier(object)
            self.backup = None
        for key, value in parameters.items():
            self.modifier[self.table[key]] = value

        # States
        self.mouse_mode = 'DEPTH'
        self.snap_break = 0.05
        self.snap_buffer = 0.0

        # Base systems
        self.master = Master(context)
        self.master.only_use_fast_ui = True
        self.base_controls = Base_Modal_Controls(context, event)
        self.original_tool_shelf, self.original_n_panel = collapse_3D_view_panels(force=True)
        self.draw_handle = bpy.types.SpaceView3D.draw_handler_add(self.safe_draw_shader, (context,), 'WINDOW', 'POST_PIXEL')

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


    def modal(self, context: bpy.types.Context, event: bpy.types.Event):

        # Base systems
        self.master.receive_event(event=event)
        self.base_controls.update(context, event)
        mouse_warp(context, event)

        # Pass
        if self.base_controls.pass_through:
            return {'PASS_THROUGH'}

        # Cancel
        if self.base_controls.cancel:
            return self.cancel_exit(context)

        # Confirm
        if self.base_controls.confirm:
            if event.type in ('RET', 'NUMPAD_ENTER') and event.shift:
                mod_name = self.modifier.name[:]
                self.apply_modifier(context.active_object, self.modifier)

                bpy.ops.hops.draw_wire_mesh_launcher('INVOKE_DEFAULT', target='SELECTED')
                if addon.preference().ui.Hops_extra_info:
                    bpy.ops.hops.display_notification(info=f'{mod_name} : Applied' )

            context.space_data.overlay.show_overlays = True
            context.active_object.show_wire = False
            return self.confirm_exit(context)

        # Inputs
        self.actions(context, event)

        # UI
        self.draw_ui(context)

        context.area.tag_redraw()
        return {'RUNNING_MODAL'}

    # --- ACTIONS --- #

    def actions(self, context: bpy.types.Context, event: bpy.types.Event):

        # Scroll
        if self.base_controls.scroll:
            self.scroll_adjust(context, event)

        # Mouse move
        elif event.type == 'MOUSEMOVE':
            self.mouse_adjust(context, event)

        # Mouse mode
        elif event.type == 'D' and event.value == 'PRESS':
            self.mouse_mode = 'DEPTH'
        elif event.type == 'R' and event.value == 'PRESS':
            self.mouse_mode = 'ROOT'
        elif event.type == 'C' and event.value == 'PRESS':
            self.mouse_mode = 'CREST'
        elif event.type == 'T' and event.value == 'PRESS':
            self.mouse_mode = 'TAPER'

        # Wire display
        elif event.type == 'Z' and event.value == 'PRESS':
            context.space_data.overlay.show_overlays = True
            context.active_object.show_wire = not context.active_object.show_wire
            context.active_object.show_all_edges = context.active_object.show_wire


    def scroll_adjust(self, context: bpy.types.Context, event: bpy.types.Event):

        # Direction
        if event.shift:
            self.modifier[self.table['Direction']] += self.base_controls.scroll * tau / self.modifier[self.table['Resolution']]
            self.refresh_modifier(self.modifier)

        # Turns
        else:
            self.modifier[self.table['Turns']] = clamp(self.modifier[self.table['Turns']] + self.base_controls.scroll, 1, 100)
            self.refresh_modifier(self.modifier)


    def mouse_adjust(self, context: bpy.types.Context, event: bpy.types.Event):

        # Depth
        if self.mouse_mode == 'DEPTH':
            if event.ctrl:
                self.snap_buffer += self.base_controls.mouse

                if abs(self.snap_buffer) > self.snap_break:
                    increment = 0.01 if event.shift else 0.05
                    value = snap(self.modifier[self.table['Depth']] + copysign(increment, self.snap_buffer), increment)
                    self.modifier[self.table['Depth']] = clamp(value, -100.0, 100.0)
                    self.snap_buffer = 0.0

            else:
                value = self.modifier[self.table['Depth']] + self.base_controls.mouse
                self.modifier[self.table['Depth']] = clamp(value, -100.0, 100.0)

            self.refresh_modifier(self.modifier)

        # Root
        elif self.mouse_mode == 'ROOT':
            if event.ctrl:
                self.snap_buffer += self.base_controls.mouse

                if abs(self.snap_buffer) > self.snap_break:
                    increment = 0.01 if event.shift else 0.05
                    value = snap(self.modifier[self.table['Root']] + copysign(increment, self.snap_buffer), increment)
                    self.modifier[self.table['Root']] = clamp(value, 0.0, 1.0)
                    self.snap_buffer = 0.0

            else:
                value = self.modifier[self.table['Root']] + self.base_controls.mouse
                self.modifier[self.table['Root']] = clamp(value, 0.0, 1.0)

            self.refresh_modifier(self.modifier)

        # Crest
        elif self.mouse_mode == 'CREST':
            if event.ctrl:
                self.snap_buffer += self.base_controls.mouse

                if abs(self.snap_buffer) > self.snap_break:
                    increment = 0.01 if event.shift else 0.05
                    value = snap(self.modifier[self.table['Crest']] + copysign(increment, self.snap_buffer), increment)
                    self.modifier[self.table['Crest']] = clamp(value, 0.0, 1.0)
                    self.snap_buffer = 0.0

            else:
                value = self.modifier[self.table['Crest']] + self.base_controls.mouse
                self.modifier[self.table['Crest']] = clamp(value, 0.0, 1.0)

            self.refresh_modifier(self.modifier)

        # Taper
        elif self.mouse_mode == 'TAPER':
            if event.ctrl:
                self.snap_buffer += self.base_controls.mouse

                if abs(self.snap_buffer) > self.snap_break:
                    increment = radians(1.0) if event.shift else radians(5.0)
                    value = snap(self.modifier[self.table['Taper']] + copysign(increment, self.snap_buffer), increment)
                    self.modifier[self.table['Taper']] = clamp(value, radians(15.0), radians(180.0))
                    self.snap_buffer = 0.0

            else:
                value = self.modifier[self.table['Taper']] + self.base_controls.mouse
                self.modifier[self.table['Taper']] = clamp(value, radians(15.0), radians(180.0))

            self.refresh_modifier(self.modifier)

    # --- UI --- #

    def draw_ui(self, context: bpy.types.Context):
        self.master.setup()
        if not self.master.should_build_fast_ui(): return

        # Main
        win_list = []
        if addon.preference().ui.Hops_modal_fast_ui_loc_options != 1:
            win_list.append(f'{self.modifier[self.table["Turns"]]}')
            win_list.append(f'{self.modifier[self.table["Depth"]]:.3f}')
            win_list.append(f'{self.modifier[self.table["Root"]]:.3f}')
            win_list.append(f'{self.modifier[self.table["Crest"]]:.3f}')
            win_list.append(f'{degrees(self.modifier[self.table["Taper"]]):.1f}°')
            win_list.append(f'{degrees(self.modifier[self.table["Direction"]]):.1f}°')
        else:
            win_list.append(self.modifier.name)
            win_list.append(f'Turns: {self.modifier[self.table["Turns"]]}')
            win_list.append(f'Depth: {self.modifier[self.table["Depth"]]:.3f}')
            win_list.append(f'Root: {self.modifier[self.table["Root"]]:.3f}')
            win_list.append(f'Crest: {self.modifier[self.table["Crest"]]:.3f}')
            win_list.append(f'Taper: {degrees(self.modifier[self.table["Taper"]]):.1f}°')
            win_list.append(f'Direction: {degrees(self.modifier[self.table["Direction"]]):.1f}°')

        # Help
        help_items = {}
        help_items['GLOBAL'] = [
            ('M', 'Toggle mods list'),
            ('H', 'Toggle help'),
            ('~', 'Toggle UI display type'),
            ('O', 'Toggle viewport rendering'),
        ]
        help_items['STANDARD'] = [
            ('Shift + Enter',   'Apply modifier'),
            ('Z',               'Toggle wireframe'),
            ('T',               'Taper mode'),
            ('C',               'Crest mode'),
            ('R',               'Root mode'),
            ('D',               'Depth mode'),
            ('Shift + Scroll',  'Adjust direction'),
            ('Scroll',          'Adjust turns'),
        ]

        if self.mouse_mode == 'DEPTH':
            help_items['STANDARD'].append(['Move', 'Adjust depth'])
        elif self.mouse_mode == 'ROOT':
            help_items['STANDARD'].append(['Move', 'Adjust root'])
        elif self.mouse_mode == 'CREST':
            help_items['STANDARD'].append(['Move', 'Adjust crest'])
        elif self.mouse_mode == 'TAPER':
            help_items['STANDARD'].append(['Move', 'Adjust taper'])

        # Mods
        mods_list = get_mods_list(context.active_object.modifiers)

        self.master.receive_fast_ui(win_list=win_list, help_list=help_items, image='ToThread', mods_list=mods_list, active_mod_name=self.modifier.name)
        self.master.finished()

    # --- UTILS --- #

    def apply_scale(self, object: bpy.types.Object) -> tuple[Vector, list[Vector]]:
        mesh: bpy.types.Mesh = object.data
        bm = bmesh.from_edit_mesh(mesh)

        scale = object.scale.copy()
        positions = [vert.co.copy() for vert in bm.verts]

        if scale.x != scale.y or scale.y != scale.z:
            bpy.ops.hops.display_notification(info='Applied non-uniform scale' )

            object.scale = Vector((1.0, 1.0, 1.0))
            bm.transform(Matrix.Diagonal(scale).to_4x4())
            object.update_from_editmode()

        return scale, positions


    def unapply_scale(self, object: bpy.types.Object, scale: Vector, positions: list[Vector]):
        mesh: bpy.types.Mesh = object.data
        bm = bmesh.from_edit_mesh(mesh)

        object.scale = scale
        for vert, position in zip(bm.verts, positions):
            vert.co = position


    def to_cylinder(self, object: bpy.types.Object) -> dict:
        mesh: bpy.types.Mesh = object.data
        bm = bmesh.from_edit_mesh(mesh)

        # Selected geometry
        faces = [face for face in bm.faces if face.select]
        if len(faces) < 8 or any(len(face.edges) != 4 for face in faces):
            return {}

        vertical_edges = self.get_vertical_edges(faces)
        if len(vertical_edges) != len(faces):
            return {}

        top_verts, bottom_verts = self.get_top_and_bottom_verts(vertical_edges)
        if len(top_verts) != len(faces) or len(bottom_verts) != len(faces):
            return {}

        # Calculate parameters
        resolution = len(faces)

        top_center: Vector = sum((vert.co for vert in top_verts), Vector()) / resolution
        bottom_center: Vector = sum((vert.co for vert in bottom_verts), Vector()) / resolution
        center: Vector = (top_center + bottom_center) * 0.5

        edge: BMEdge = vertical_edges[0]
        middle: Vector = (edge.verts[0].co + edge.verts[1].co) * 0.5
        offset: Vector = (middle - center)

        axis_z = Vector(top_center - bottom_center).normalized()
        axis_y = Vector(offset - offset.project(axis_z)).normalized()
        axis_x = axis_y.cross(axis_z)

        rotation_from = Matrix((axis_x, axis_y, axis_z))
        rotation_to: Matrix = rotation_from.inverted()
        angles: Euler = rotation_to.to_euler()

        def calc_radius(edge: BMEdge) -> float:
            middle = Vector(edge.verts[0].co + edge.verts[1].co) * 0.5
            offset = Vector(middle - center)
            return Vector(offset - offset.project(axis_z)).length

        radius = sum(map(calc_radius, vertical_edges)) / resolution
        height = Vector(top_center - bottom_center).length

        # Move geometry
        edge: BMEdge = vertical_edges[1]
        middle: Vector = (edge.verts[0].co + edge.verts[1].co) * 0.5
        offset: Vector = (middle - center)

        unprojected = Vector(offset - offset.project(axis_z)).normalized()
        unrotated: Vector = rotation_from @ unprojected
        sign = copysign(1.0, unrotated.to_2d().angle_signed((0.0, 1.0)))

        for circle, z in zip((top_verts, bottom_verts), (height * 0.5, height * -0.5)):
            for index, vert in enumerate(circle):
                angle = sign * index / resolution * tau

                x = radius * -sin(angle)
                y = radius * cos(angle)
                vert.co = center + rotation_to @ Vector((x, y ,z))

        parameters = {
            'Translation': center,
            'Rotation': angles,
            'Resolution': resolution,
            'Radius': radius,
            'Height': height,
        }

        return parameters


    def get_vertical_edges(self, faces: list[BMFace]) -> list[BMEdge]:
        edges: list[BMEdge] = []

        face_curr: BMFace = faces[0]
        edge_prev: BMEdge = None

        for _ in faces:
            for edge_curr in face_curr.edges:
                if edge_curr is edge_prev:
                    continue
                if edge_curr.is_boundary:
                    continue
                if all(face.select for face in edge_curr.link_faces):
                    break

            for face in edge_curr.link_faces:
                if face is not face_curr:
                    face_curr = face
                    break

            edges.append(edge_curr)
            edge_prev = edge_curr

        return edges


    def get_top_and_bottom_verts(self, edges: list[BMEdge]) -> tuple[list[BMVert], list[BMVert]]:
        top_verts: list[BMVert] = []
        bottom_verts: list[BMVert] = []

        up = Vector(edges[0].verts[1].co - edges[0].verts[0].co)

        for edge in edges:
            direction = Vector(edge.verts[1].co - edge.verts[0].co)

            if direction.dot(up) > 0.0:
                top_verts.append(edge.verts[1])
                bottom_verts.append(edge.verts[0])
            else:
                top_verts.append(edge.verts[0])
                bottom_verts.append(edge.verts[1])

        return top_verts, bottom_verts


    def generate_unique_name(self, object: bpy.types.Object) -> str:
        mesh: bpy.types.Mesh = object.data

        modifier_names = [modifier.name for modifier in object.modifiers]
        vertex_group_names = [group.name for group in object.vertex_groups]
        attribute_names = [attribute.name for attribute in mesh.attributes]
        all_names = set(modifier_names + vertex_group_names + attribute_names)

        if (name := NODE_GROUP_NAME) not in all_names:
            return name

        for number in range(1, 1000):
            if (name := f'{NODE_GROUP_NAME}.{number:03}') not in all_names:
                return name

        raise Exception('Consider this an easter egg')


    def get_modifier(self, object: bpy.types.Object) -> tuple[bpy.types.NodesModifier, dict]:
        mesh: bpy.types.Mesh = object.data
        groups_per_vertex = [[g.group for g in v.groups] for v in mesh.vertices if v.select]

        bm = bmesh.from_edit_mesh(mesh)
        verts = [vert for vert in bm.verts if vert.select]

        for modifier in object.modifiers:
            modifier: bpy.types.NodesModifier

            # Node group
            if modifier.type != 'NODES' or not modifier.node_group:
                continue
            if not modifier.node_group.name.startswith(NODE_GROUP_NAME):
                continue

            # Sockets
            table = socket_table(modifier.node_group)
            if any(socket not in table for socket in REQUIRED_SOCKETS):
                continue

            # Vertex group
            group = object.vertex_groups.find(modifier[table['Selection']])
            if all(group in groups for groups in groups_per_vertex):
                return modifier, table

            # Attribute
            layer = bm.verts.layers.float.get(modifier[table['Selection']])
            if layer and all(vert[layer] for vert in verts):
                return modifier, table

        return None, None


    def new_modifier(self, object: bpy.types.Object) -> tuple[bpy.types.NodesModifier, dict]:

        # Vertex group
        bpy.ops.object.vertex_group_assign_new()
        group = object.vertex_groups[-1]
        group.name = self.generate_unique_name(object)

        # Modifier
        modifier: bpy.types.NodesModifier = object.modifiers.new(group.name, 'NODES')
        object.modifiers.move(len(object.modifiers) - 1, 0)
        modifier.node_group, table = to_thread_nodes()
        modifier[table['Selection']] = group.name

        try:
            modifier.panels[0].is_open = False
        except:
            pass

        return modifier, table


    def backup_modifier(self, modifier: bpy.types.NodesModifier, table: dict) -> dict:
        backup = {}

        for key in REQUIRED_SOCKETS:
            value = modifier[table[key]]

            # Copy vector properties
            if hasattr(value, 'to_list'):
                backup[key] = value.to_list()
            else:
                backup[key] = value

        return backup


    def restore_modifier(self, modifier: bpy.types.NodesModifier, table: dict, backup: dict):
        for key, value in backup.items():
            modifier[table[key]] = value

        self.refresh_modifier(modifier)


    def apply_modifier(self, object: bpy.types.Object, modifier: bpy.types.NodesModifier):
        mesh: bpy.types.Mesh = object.data
        groups = {group.name for group in object.vertex_groups}

        slots_before = len(object.material_slots)
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.modifier_apply(modifier=modifier.name)
        slots_after = len(object.material_slots)

        # Iterating over attributes directly does not work properly.
        for index in reversed(list(range(len(mesh.attributes)))):
            if mesh.attributes[index].name in groups:
                mesh.attributes.active_index = index
                bpy.ops.geometry.attribute_convert(mode='VERTEX_GROUP')

        for count in range(slots_after, slots_before, -1):
            object.active_material_index = count - 1
            bpy.ops.object.material_slot_remove()


    def remove_modifier(self, object: bpy.types.Object, modifier: bpy.types.NodesModifier):
        object.modifiers.remove(modifier)
        object.vertex_groups.remove(object.vertex_groups[-1])


    def refresh_modifier(self, modifier: bpy.types.NodesModifier):
        for _ in range(2):
            modifier.show_viewport = not modifier.show_viewport

    # --- EXIT --- #

    def confirm_exit(self, context: bpy.types.Context) -> set:
        self.common_exit(context)
        return {'FINISHED'}


    def cancel_exit(self, context: bpy.types.Context) -> set:
        self.common_exit(context)
        self.unapply_scale(context.active_object, self.scale, self.positions)

        if self.backup:
            self.restore_modifier(self.modifier, self.table, self.backup)
        else:
            self.remove_modifier(context.active_object, self.modifier)

        return {'CANCELLED'}


    def common_exit(self, context: bpy.types.Context):
        collapse_3D_view_panels(self.original_tool_shelf, self.original_n_panel)

        self.remove_shader()
        self.master.run_fade()

    # --- SHADER --- #

    def safe_draw_shader(self, context: bpy.types.Context):
        method_handler(self.draw_shader, arguments = (context,), identifier = 'ToThread Shader', exit_method = self.remove_shader)


    def remove_shader(self):
        if self.draw_handle:
            self.draw_handle = bpy.types.SpaceView3D.draw_handler_remove(self.draw_handle, 'WINDOW')


    def draw_shader(self, context: bpy.types.Context):
        draw_modal_frame(context)

# --- UTILS --- #

def snap(value: float, increment: float) -> float:
    return float(round(value / increment)) * increment


def clamp(value: float, min_: float, max_: float) -> float:
    return min(max(value, min_), max_)
