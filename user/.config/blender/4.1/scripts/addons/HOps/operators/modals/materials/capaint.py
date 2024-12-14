import bpy
from pathlib import Path

def carpaint_material(material = None, name='Carpaint'):
    if not material:
        material = bpy.data.materials.new (name)
    material.use_nodes = True
    material_nodes = material.node_tree.nodes
    material_nodes.clear()
    output = material_nodes.new(type="ShaderNodeOutputMaterial")

    paint = material_nodes.new('ShaderNodeGroup')
    paint.node_tree = carpaint_node_group()
    material.node_tree.links.new(paint.outputs[0], output.inputs[0])
    paint.location = [-300, output.location[1]]
    return (material, paint)

def carpaint_node_group():
    group_name = 'HOPS.carpaint_shader'
    carpaint_shader = None
    try:
        carpaint_shader = bpy.data.node_groups[group_name]
        return carpaint_shader
    except:
        pass

    path = Path(__file__).parent.resolve() / 'materials.blend'

    with bpy.data.libraries.load(str(path)) as (data_from, data_to):
        data_to.node_groups.append(group_name)

    carpaint_shader = bpy.data.node_groups[group_name]

    return carpaint_shader