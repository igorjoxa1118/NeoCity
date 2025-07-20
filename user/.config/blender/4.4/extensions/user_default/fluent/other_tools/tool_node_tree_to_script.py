import bpy

node_tree = bpy.data.node_groups['.f_chain']

# Génération du script
script = bpy.data.texts.new("node_tree_script")
script.write("import bpy\n\n")
# script.write("# Création du node tree\n")
# script.write(f"node_tree = bpy.data.node_groups.new('{node_tree.name}', 'ShaderNodeTree')\n\n")

# Écriture des nodes dans le script
for item in node_tree.interface.items_tree:
    if item.item_type == 'SOCKET':
        if item.in_out == 'INPUT':
            script.write(f"node_tree.interface.new_socket(in_out='INPUT', socket_type='{item.bl_socket_idname}', name='{item.name}')\n")
        elif item.in_out == 'OUTPUT':
            script.write(f"node_tree.interface.new_socket(in_out='OUTPUT', socket_type='{item.bl_socket_idname}', name='{item.name}')\n")

for node in node_tree.nodes:
    script.write(f"\n\n")
    script.write(f"node = node_tree.nodes.new('{node.bl_idname}')\n")
    script.write(f"node.location = Vector(({node.location[0]},{node.location[1]}))\n")
    script.write(f"node.name = '{node.name}'\n\n")
    try:
        script.write(f"node.operation = '{node.operation}'\n")
    except: pass
    try:
        script.write(f"node.mode = '{node.mode}'\n")
    except: pass
    try:
        for i, input in enumerate(node.inputs):
            try:
                if input.type in ['VALUE', 'INT', 'BOOLEAN']:
                    script.write(f"node.inputs['{i}'].default_value = {input.default_value}\n")
            except: pass
        try:
            if node.space:
                script.write(f"node.space = '{node.space}'\n")
        except: pass
        try:
            if node.type:
                script.write(f"try:\n")
                script.write(f"\tnode.type = '{node.type}'\n")
                script.write(f"except:pass\n")
        except: pass
    except: pass

# Écriture des connexions dans le script
already_done = []
for link in node_tree.links:
    from_node = link.from_node.name
    from_socket = link.from_socket.name
    to_node = link.to_node.name
    to_socket_name = link.to_socket.name
    to_socket_index = None

    for i, socket in enumerate(link.to_node.inputs):
        if socket.name == to_socket_name and not to_node + ' ' + str(i) in already_done:
            to_socket_index = i
            break

    if to_socket_index is not None:
        already_done.append(to_node + ' ' + str(to_socket_index))
        script.write(f"node_tree.links.new(node_tree.nodes['{from_node}'].outputs['{from_socket}'], ")
        script.write(f"node_tree.nodes['{to_node}'].inputs[{to_socket_index}])\n\n")

# Enregistrement du script dans un fichier
# script_file = bpy.path.abspath("//node_tree_script.py")
# script.save(filepath=script_file)