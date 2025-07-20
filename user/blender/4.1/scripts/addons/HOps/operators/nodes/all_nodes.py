import bpy
from mathutils import Vector
from .cycle_node import node_categories


class HOPS_OT_All_Nodes(bpy.types.Operator):
    bl_idname = "hops.all_geo_nodes"
    bl_label = "All Geo Nodes"
    bl_description = '''Place all Nodes into graph'''
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if context.area:
            if context.area.ui_type in {'ShaderNodeTree'} or (bpy.app.version < (3, 4) and context.area.ui_type =='GeometryNodeTree'):
                return True
        return False


    def execute(self, context):
        # Validate Context
        valid_context = False
        if hasattr(context, 'area'):
            if hasattr(context.area, 'spaces'):
                if hasattr(context.area.spaces, 'active'):
                    if hasattr(context.area.spaces.active, 'edit_tree'):
                        valid_context = True
        if not valid_context: return {'CANCELLED'}
        # Place
        place_nodes(context)
        return {'FINISHED'}


def place_nodes(context):

    # Current Graph
    all_nodes = node_categories(context)
    tree = context.area.spaces.active.edit_tree

    # Bounds
    min_x = 0
    max_y = 0
    if tree.nodes:
        min_x = min([node.location[0] for node in tree.nodes])
        max_y = max([node.location[1] for node in tree.nodes])
    top_left = Vector((min_x, max_y))

    # Padding
    pad_y = 500

    colors = [(.2, .2, .2), (.4, .4, .4)]
    pick = 0

    frames = []

    # Place Nodes
    offset_y = pad_y
    for cat_name, node_types in all_nodes.items():

        if cat_name == 'Layout': continue
        if cat_name == 'Group': continue

        frame_children = []

        offset_x = 0
        for node_type in node_types:
            if not hasattr(bpy.types, node_type): continue
            node = tree.nodes.new(node_type)
            node.location.x = top_left.x + offset_x
            node.location.y = top_left.y + offset_y

            frame_children.append(node)

            # Offset Across
            offset_x += node.width + 10

        # Frame
        frame = tree.nodes.new('NodeFrame')
        frame.label = cat_name
        frame.location.x = -10
        frame.location.y = offset_y + 40
        frame.width = offset_x
        frame.height = pad_y - 10
        frame.use_custom_color = True
        frame.color = colors[pick % 2]

        frames.append(frame)

        for node in frame_children:
            node.parent = frame

        # Color
        pick += 1

        # Offset Up
        offset_y += pad_y

    context.view_layer.update()
    bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=2)

    offset_y = 0

    for index, frame in enumerate(frames):
        if index == 0:
            offset_y = frame.location.y + 20
            continue

        frame.location.y = offset_y + frame.height
        offset_y = frame.location.y + 20


    bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)