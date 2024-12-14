import bpy
from pathlib import Path

def emission_glow_material(material = None, name= 'emission_glow'):
    if not material:
        material = bpy.data.materials.new (name)
    material.use_nodes = True
    material_nodes = material.node_tree.nodes
    material_nodes.clear()
    output = material_nodes.new(type="ShaderNodeOutputMaterial")

    emission_glow = material_nodes.new('ShaderNodeGroup')
    emission_glow.node_tree = emission_glow_node_group()
    material.node_tree.links.new(emission_glow.outputs[0], output.inputs[0])
    emission_glow.location = [-300, output.location[1]]
    return (material, emission_glow)

def emission_glow_node_group():
    group_name = 'HOPS.emission_glow'
    emission_glow = None
    try:
        emission_glow = bpy.data.node_groups[group_name]
        return emission_glow
    except:
        pass

    path = Path(__file__).parent.resolve() / 'materials.blend'

    with bpy.data.libraries.load(str(path)) as (data_from, data_to):
        data_to.node_groups.append(group_name)

    emission_glow = bpy.data.node_groups[group_name]

    return emission_glow
