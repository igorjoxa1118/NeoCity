import bpy
from pathlib import Path


BLEND_FILE_NAME = 'HOPS_ToThread.blend'
NODE_GROUP_NAME = 'HOPS_ToThread'

REQUIRED_SOCKETS = [
    'Selection',
    'Translation',
    'Rotation',
    'Resolution',
    'Radius',
    'Height',
    'Turns',
    'Depth',
    'Root',
    'Crest',
    'Taper',
]


def to_thread_nodes(reuse_existing=True, keep_asset=False) -> tuple[bpy.types.NodeGroup, dict]:
    if reuse_existing:
        for node_group in bpy.data.node_groups:
            if not node_group.name.startswith(NODE_GROUP_NAME):
                continue

            table = socket_table(node_group)

            if any(socket not in table for socket in REQUIRED_SOCKETS):
                continue

            return node_group, table

    path = Path(__file__).parent.resolve() / BLEND_FILE_NAME

    with bpy.data.libraries.load(str(path)) as (data_from, data_to):
        data_to.node_groups.append(NODE_GROUP_NAME)

    to_thread = data_to.node_groups[0]

    if not keep_asset:
        to_thread.asset_clear()

    return to_thread, socket_table(to_thread)


def socket_table(node_group: bpy.types.NodeGroup) -> dict:
    table = {}

    for item in node_group.interface.items_tree:
        if item.item_type == 'SOCKET':
            table[item.name] = item.identifier

    return table
