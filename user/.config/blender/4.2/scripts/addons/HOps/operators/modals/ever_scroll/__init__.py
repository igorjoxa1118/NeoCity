import bpy, time, gpu
from enum import Enum
from .... utility import addon
from .... ui_framework.graphics.draw import draw_text, render_quad, draw_border_lines
from .... ui_framework.utils.geo import get_blf_text_dims
from .... utility.base_modal_controls import confirm_events
from .... utility.collections import unhide_layers
from .... utility import modifier as mod_utils
from ....utility.screen import dpi_factor


class States(Enum):
    MOD = 0
    CHILD = 1
    BOOL = 2
    COLL = 3


class Auto_Scroll:
    '''Draws text label / Namespace for props'''
    def __init__(self, context):
        self.timer = None
        self.active = False
        self.activated_time = 0
        self.sequance_hold = False
        self.sequance_hold_time = 0

        self.x = context.area.width * .25
        self.y = context.area.height * .75
        self.font_color = addon.preference().color.Hops_UI_text_color
        self.bg_color = addon.preference().color.Hops_UI_cell_background_color
        self.br_color = addon.preference().color.Hops_UI_border_color
        self.size = 16

        dims = get_blf_text_dims("00.00", self.size)
        p = 8 * dpi_factor()
        h = dims[1] + p * 2
        w = dims[0] + p * 2
        x = self.x - p
        y = self.y + h

        # Top Left, Bottom Left, Top Right, Bottom Right
        self.verts = [
            (x, y),
            (x, y - h - p * 2),
            (x + w, y),
            (x + w, y - h - p * 2)]


    def display_msg(self):
        counter = abs(addon.preference().property.auto_scroll_time_interval - (time.time() - self.activated_time))
        text = "Start" if self.sequance_hold else f"{counter:.2f}"
        return text


    def draw(self):
        if not self.active: return

        render_quad(quad=self.verts, color=self.bg_color, bevel_corners=True)
        draw_border_lines(vertices=self.verts, width=1, color=self.br_color, bevel_corners=True)

        draw_text(self.display_msg(), self.x, self.y, size=self.size, color=self.font_color)


def update_local_view(context, objs):
    if context.space_data.local_view:
        # Come out of Local view
        bpy.ops.view3d.localview(frame_selected=False)
        for obj in objs:
            obj.hide_set(False)
            obj.select_set(True)
        # Go back into local view
        bpy.ops.view3d.localview(frame_selected=False)
        return True
    return False


def mods_exit_options(context, event, obj, force_ctrl=False, force_shift=False):

    # Apply mods on obj
    if (event.ctrl and event.type in confirm_events) or force_ctrl:
        mod_utils.apply(obj, visible=True)
        bpy.ops.hops.draw_wire_mesh_launcher('INVOKE_DEFAULT', target='SELECTED')
        bpy.ops.hops.display_notification(info="Applied visible modifiers")
        # Reveal remaining mods
        for mod in obj.modifiers:
            if mod.show_render:
                mod.show_viewport = True
        return True

    # Apply mods on copy of obj
    elif (event.shift and event.type in confirm_events) or force_shift:
        new_obj = obj.copy()
        new_obj.data = obj.data.copy()

        for col in obj.users_collection:
            if col not in new_obj.users_collection:
                col.objects.link(new_obj)

        mod_utils.apply(new_obj, visible=True)
        new_obj.modifiers.clear()

        context.view_layer.objects.active = new_obj
        obj.select_set(False)

        for mod in obj.modifiers:
            mod.show_viewport = True

        bpy.ops.hops.draw_wire_mesh_launcher('INVOKE_DEFAULT', target='SELECTED')
        bpy.ops.hops.display_notification(info="Applied visible modifiers on duplicate")
        return True

    return False


def turn_on_coll(obj, main_coll):
    unhide_layers(obj)

    for coll in obj.users_collection:
        if coll != main_coll:
            for object in coll.objects:
                if object.display_type == 'WIRE':
                    if object.hide_viewport:
                        object.hide_viewport = False
                    if not object.hide_get():
                        object.hide_set(True)


def get_mod_object(mod):
    obj = None
    if   hasattr(mod,        'object'): obj = mod.object
    elif hasattr(mod, 'mirror_object'): obj = mod.mirror_object
    elif hasattr(mod, 'offset_object'): obj = mod.offset_object
    if obj: return obj

    if mod.type != 'ARRAY': return None

    obj = bpy.context.active_object

    if not obj.animation_data: return

    f_curves = obj.animation_data.drivers

    for f_cruve in f_curves:

        path = f_cruve.data_path
        s = path.index('[') + 2
        e = path.index(']') - 1

        if mod.name != path[s:e]: continue

        driver = f_cruve.driver
        for var in driver.variables:
            for tar in var.targets:
                if not tar.id: continue
                if tar.id.name[:15] == 'HOPSArrayTarget':
                    return tar.id
    return None


def get_node_graph_objects(mod):
    if mod.type != 'NODES': return []
    if mod.node_group == None: return []
    objects = []
    for node in mod.node_group.nodes:
        if node.type == 'OBJECT_INFO':
            obj_input = node.inputs['Object']
            if obj_input.is_linked:
                link = obj_input.links[0]
                if link.from_node.type != 'GROUP_INPUT' or link.from_socket.type != 'OBJECT': continue

                val = mod[link.from_socket.identifier]
                if val and val.type == 'MESH':
                    objects.append(val)

            else:
                val = obj_input.default_value
                if val and val.type == 'MESH':
                    objects.append(val)
    return objects
