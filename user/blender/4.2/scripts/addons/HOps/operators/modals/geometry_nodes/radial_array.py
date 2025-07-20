import bpy
from pathlib import Path

BLEND_FILE_NAME = 'HOPS_Radial_Array.blend'

'''Load node group from blendfile'''
def radial_array_nodes(keep_asset=False):

    path = Path(__file__).parent.resolve() / BLEND_FILE_NAME

    with bpy.data.libraries.load(str(path)) as (data_from, data_to):
        data_to.node_groups.append(data_from.node_groups[0])

    radial_array = data_to.node_groups[0]

    if not keep_asset:
        radial_array.asset_clear()

    return radial_array
