import bpy
from mathutils import Vector

def chain_code(node_tree):
    if bpy.app.version >= (4, 0, 0):
        node_tree.interface.new_socket(in_out='OUTPUT', socket_type='NodeSocketGeometry', name='Geometry')
        node_tree.interface.new_socket(in_out='INPUT', socket_type='NodeSocketGeometry', name='Geometry')
        node_tree.interface.new_socket(in_out='INPUT', socket_type='NodeSocketFloat', name='Width')
        node_tree.interface.new_socket(in_out='INPUT', socket_type='NodeSocketFloat', name='Height')
        node_tree.interface.new_socket(in_out='INPUT', socket_type='NodeSocketFloat', name='Radius link')
        node_tree.interface.new_socket(in_out='INPUT', socket_type='NodeSocketFloat', name='Radius')
        node_tree.interface.new_socket(in_out='INPUT', socket_type='NodeSocketFloat', name='Scale')
        node_tree.interface.new_socket(in_out='INPUT', socket_type='NodeSocketObject', name='Object')
        node_tree.interface.new_socket(in_out='INPUT', socket_type='NodeSocketBool', name='Switch')
        node_tree.interface.new_socket(in_out='INPUT', socket_type='NodeSocketMaterial', name='Material')
    else:
        node_tree.inputs.new(type='NodeSocketGeometry', name='Geometry')
        node_tree.inputs.new(type='NodeSocketFloatDistance', name='Width')
        node_tree.inputs.new(type='NodeSocketFloatDistance', name='Height')
        node_tree.inputs.new(type='NodeSocketFloatDistance', name='Radius link')
        node_tree.inputs.new(type='NodeSocketFloatDistance', name='Radius')
        node_tree.inputs.new(type='NodeSocketFloat', name='Scale')
        node_tree.inputs.new(type='NodeSocketObject', name='Object')
        node_tree.inputs.new(type='NodeSocketBool', name='Switch')
        node_tree.inputs.new(type='NodeSocketMaterial', name='Material')
        node_tree.outputs.new(type='NodeSocketGeometry', name='Geometry')

    node = node_tree.nodes.new('NodeGroupInput')
    node.location = Vector((-640.0380249023438, 0.0))
    node.name = 'Group Input'

    try:
        node.type = 'GROUP_INPUT'
    except: pass

    node = node_tree.nodes.new('NodeGroupOutput')
    node.location = Vector((1972.8603515625, 6.881655216217041))
    node.name = 'Group Output'

    try:
        node.type = 'GROUP_OUTPUT'
    except: pass

    node = node_tree.nodes.new('GeometryNodeCurvePrimitiveQuadrilateral')
    node.location = Vector((-349.5345458984375, -57.56691360473633))
    node.name = 'Quadrilateral'

    node.mode = 'RECTANGLE'
    node.inputs[0].default_value = 2.0
    node.inputs[1].default_value = 2.0
    node.inputs[2].default_value = 4.0
    node.inputs[3].default_value = 2.0
    node.inputs[4].default_value = 1.0
    node.inputs[5].default_value = 3.0
    node.inputs[6].default_value = 1.0
    try:
        node.type = 'CURVE_PRIMITIVE_QUADRILATERAL'
    except: pass

    node = node_tree.nodes.new('GeometryNodeFilletCurve')
    node.location = Vector((-169.5445556640625, -57.56691360473633))
    node.name = 'Fillet Curve'

    node.mode = 'POLY'
    node.inputs[1].default_value = 6
    node.inputs[2].default_value = 0.25
    node.inputs[3].default_value = True
    try:
        node.type = 'FILLET_CURVE'
    except: pass

    node = node_tree.nodes.new('GeometryNodeCurveToMesh')
    node.location = Vector((13.615275382995605, -57.56691360473633))
    node.name = 'Curve to Mesh'

    node.inputs[2].default_value = False
    try:
        node.type = 'CURVE_TO_MESH'
    except: pass

    node = node_tree.nodes.new('GeometryNodeMergeByDistance')
    node.location = Vector((192.0308837890625, -57.56691360473633))
    node.name = 'Merge by Distance'

    node.mode = 'ALL'
    node.inputs[1].default_value = True
    node.inputs[2].default_value = 0.0010000000474974513
    try:
        node.type = 'MERGE_BY_DISTANCE'
    except: pass

    node = node_tree.nodes.new('GeometryNodeMeshToCurve')
    node.location = Vector((385.59912109375, -55.99961471557617))
    node.name = 'Mesh to Curve'

    node.inputs[1].default_value = True
    try:
        node.type = 'MESH_TO_CURVE'
    except: pass

    node = node_tree.nodes.new('GeometryNodeCurveToMesh')
    node.location = Vector((587.607421875, -55.99201583862305))
    node.name = 'Curve to Mesh.001'

    node.inputs[2].default_value = False
    try:
        node.type = 'CURVE_TO_MESH'
    except: pass

    node = node_tree.nodes.new('GeometryNodeCurvePrimitiveCircle')
    node.location = Vector((393.2140808105469, -228.4180450439453))
    node.name = 'Curve Circle'

    node.mode = 'RADIUS'
    node.inputs[0].default_value = 64
    node.inputs[4].default_value = 1.0
    try:
        node.type = 'CURVE_PRIMITIVE_CIRCLE'
    except: pass

    node = node_tree.nodes.new('GeometryNodeSetMaterial')
    node.location = Vector((802.4535522460938, -53.69110107421875))
    node.name = 'Set Material'

    node.inputs[1].default_value = True
    try:
        node.type = 'SET_MATERIAL'
    except: pass

    node = node_tree.nodes.new('GeometryNodeSwitch')
    node.location = Vector((1081.4599609375, -10.752914428710938))
    node.name = 'Switch'

    node.inputs[0].default_value = False
    try:
        node.type = 'SWITCH'
    except: pass

    node = node_tree.nodes.new('GeometryNodeObjectInfo')
    node.location = Vector((815.1060180664062, 247.2560577392578))
    node.name = 'Object Info'

    node.inputs[1].default_value = False
    try:
        node.type = 'OBJECT_INFO'
    except: pass

    node = node_tree.nodes.new('GeometryNodeTransform')
    node.location = Vector((1297.2239990234375, -62.3060302734375))
    node.name = 'Transform Geometry'

    try:
        node.type = 'TRANSFORM_GEOMETRY'
    except: pass

    node = node_tree.nodes.new('ShaderNodeMath')
    node.location = Vector((-344.4410095214844, 146.31057739257812))
    node.name = 'Math'

    node.operation = 'MULTIPLY'
    node.inputs[0].default_value = 0.5
    node.inputs[1].default_value = 2.0999999046325684
    node.inputs[2].default_value = 0.5
    try:
        node.type = 'MATH'
    except: pass

    node = node_tree.nodes.new('ShaderNodeMath')
    node.location = Vector((-157.49766540527344, 311.4154968261719))
    node.name = 'Math.001'

    node.operation = 'SUBTRACT'
    node.inputs[0].default_value = 0.5
    node.inputs[1].default_value = 0.5
    node.inputs[2].default_value = 0.5
    try:
        node.type = 'MATH'
    except: pass

    node = node_tree.nodes.new('GeometryNodeResampleCurve')
    node.location = Vector((70.23628997802734, 395.9522705078125))
    node.name = 'Resample Curve'

    node.mode = 'LENGTH'
    node.inputs[1].default_value = True
    node.inputs[2].default_value = 10
    node.inputs[3].default_value = 0.10000000149011612
    try:
        node.type = 'RESAMPLE_CURVE'
    except: pass

    node = node_tree.nodes.new('GeometryNodeInstanceOnPoints')
    node.location = Vector((1506.5968017578125, 49.98918533325195))
    node.name = 'Instance on Points'

    node.inputs[1].default_value = True
    node.inputs[3].default_value = False
    node.inputs[4].default_value = 0
    try:
        node.type = 'INSTANCE_ON_POINTS'
    except: pass

    node = node_tree.nodes.new('GeometryNodeRealizeInstances')
    node.location = Vector((1710.2236328125, 48.92848587036133))
    node.name = 'Realize Instances'

    try:
        node.type = 'REALIZE_INSTANCES'
    except: pass

    node = node_tree.nodes.new('FunctionNodeRotateRotation')
    node.location = Vector((1077.474609375, -320.4502258300781))
    node.name = 'Rotate Rotation'
    node.rotation_space = 'LOCAL'

    try:
        node.type = 'ROTATE_ROTATION'
    except: pass

    node = node_tree.nodes.new('FunctionNodeAlignEulerToVector')
    node.location = Vector((683.6631469726562, -365.0687561035156))
    node.name = 'Align Euler to Vector'

    node.inputs[1].default_value = 1.0
    try:
        node.type = 'ALIGN_EULER_TO_VECTOR'
    except: pass

    node = node_tree.nodes.new('GeometryNodeInputTangent')
    node.location = Vector((491.8753967285156, -477.6107177734375))
    node.name = 'Curve Tangent'

    try:
        node.type = 'INPUT_TANGENT'
    except: pass

    node = node_tree.nodes.new('GeometryNodeInputIndex')
    node.location = Vector((92.9622802734375, -597.9551391601562))
    node.name = 'Index'

    try:
        node.type = 'INDEX'
    except: pass

    node = node_tree.nodes.new('ShaderNodeMath')
    node.location = Vector((280.3388366699219, -526.56787109375))
    node.name = 'Math.002'

    node.operation = 'MULTIPLY'
    node.inputs[0].default_value = 0.5
    node.inputs[1].default_value = 1.5707999467849731
    node.inputs[2].default_value = 0.5
    try:
        node.type = 'MATH'
    except: pass

    node = node_tree.nodes.new('ShaderNodeMath')
    node.location = Vector((497.6768493652344, -580.5068359375))
    node.name = 'Math.003'

    node.operation = 'ADD'
    node.inputs[0].default_value = 0.5
    node.inputs[1].default_value = 0.5
    node.inputs[2].default_value = 0.5
    try:
        node.type = 'MATH'
    except: pass

    node = node_tree.nodes.new('FunctionNodeRandomValue')
    node.location = Vector((283.9533386230469, -703.032958984375))
    node.name = 'Random Value'

    node.inputs[2].default_value = 0.0
    node.inputs[3].default_value = 0.5
    node.inputs[4].default_value = 0
    node.inputs[5].default_value = 100
    node.inputs[6].default_value = 0.5
    node.inputs[7].default_value = 0
    node.inputs[8].default_value = 0
    try:
        node.type = 'RANDOM_VALUE'
    except: pass

    node = node_tree.nodes.new('ShaderNodeCombineXYZ')
    node.location = Vector((683.702880859375, -585.0697631835938))
    node.name = 'Combine XYZ'

    node.inputs[0].default_value = 0.0
    node.inputs[1].default_value = 0.0
    node.inputs[2].default_value = 0.0
    try:
        node.type = 'COMBXYZ'
    except: pass
    node_tree.links.new(node_tree.nodes['Group Input'].outputs['Width'], node_tree.nodes['Quadrilateral'].inputs[0])

    node_tree.links.new(node_tree.nodes['Group Input'].outputs['Height'], node_tree.nodes['Quadrilateral'].inputs[1])

    node_tree.links.new(node_tree.nodes['Group Input'].outputs['Switch'], node_tree.nodes['Switch'].inputs[0])

    node_tree.links.new(node_tree.nodes['Quadrilateral'].outputs['Curve'], node_tree.nodes['Fillet Curve'].inputs[0])

    node_tree.links.new(node_tree.nodes['Group Input'].outputs['Radius link'], node_tree.nodes['Fillet Curve'].inputs[2])

    node_tree.links.new(node_tree.nodes['Fillet Curve'].outputs['Curve'], node_tree.nodes['Curve to Mesh'].inputs[0])

    node_tree.links.new(node_tree.nodes['Curve to Mesh'].outputs['Mesh'], node_tree.nodes['Merge by Distance'].inputs[0])

    node_tree.links.new(node_tree.nodes['Merge by Distance'].outputs['Geometry'], node_tree.nodes['Mesh to Curve'].inputs[0])

    node_tree.links.new(node_tree.nodes['Mesh to Curve'].outputs['Curve'], node_tree.nodes['Curve to Mesh.001'].inputs[0])

    node_tree.links.new(node_tree.nodes['Curve Circle'].outputs['Curve'], node_tree.nodes['Curve to Mesh.001'].inputs[1])

    node_tree.links.new(node_tree.nodes['Group Input'].outputs['Radius'], node_tree.nodes['Curve Circle'].inputs[4])

    node_tree.links.new(node_tree.nodes['Curve to Mesh.001'].outputs['Mesh'], node_tree.nodes['Set Material'].inputs[0])

    node_tree.links.new(node_tree.nodes['Group Input'].outputs['Material'], node_tree.nodes['Set Material'].inputs[2])

    node_tree.links.new(node_tree.nodes['Set Material'].outputs['Geometry'], node_tree.nodes['Switch'].inputs[1])

    node_tree.links.new(node_tree.nodes['Object Info'].outputs['Geometry'], node_tree.nodes['Switch'].inputs[2])

    node_tree.links.new(node_tree.nodes['Group Input'].outputs['Object'], node_tree.nodes['Object Info'].inputs[0])

    node_tree.links.new(node_tree.nodes['Switch'].outputs['Output'], node_tree.nodes['Transform Geometry'].inputs[0])

    node_tree.links.new(node_tree.nodes['Group Input'].outputs['Scale'], node_tree.nodes['Transform Geometry'].inputs[3])

    node_tree.links.new(node_tree.nodes['Group Input'].outputs['Radius'], node_tree.nodes['Math'].inputs[0])

    node_tree.links.new(node_tree.nodes['Group Input'].outputs['Width'], node_tree.nodes['Math.001'].inputs[0])

    node_tree.links.new(node_tree.nodes['Math'].outputs['Value'], node_tree.nodes['Math.001'].inputs[1])

    node_tree.links.new(node_tree.nodes['Group Input'].outputs['Geometry'], node_tree.nodes['Resample Curve'].inputs[0])

    node_tree.links.new(node_tree.nodes['Math.001'].outputs['Value'], node_tree.nodes['Resample Curve'].inputs[3])

    node_tree.links.new(node_tree.nodes['Resample Curve'].outputs['Curve'], node_tree.nodes['Instance on Points'].inputs[0])

    node_tree.links.new(node_tree.nodes['Transform Geometry'].outputs['Geometry'], node_tree.nodes['Instance on Points'].inputs[2])

    node_tree.links.new(node_tree.nodes['Instance on Points'].outputs['Instances'], node_tree.nodes['Realize Instances'].inputs[0])

    node_tree.links.new(node_tree.nodes['Realize Instances'].outputs['Geometry'], node_tree.nodes['Group Output'].inputs[0])

    node_tree.links.new(node_tree.nodes['Rotate Rotation'].outputs['Rotation'], node_tree.nodes['Instance on Points'].inputs[5])

    node_tree.links.new(node_tree.nodes['Curve Tangent'].outputs['Tangent'], node_tree.nodes['Align Euler to Vector'].inputs[2])

    node_tree.links.new(node_tree.nodes['Align Euler to Vector'].outputs['Rotation'], node_tree.nodes['Rotate Rotation'].inputs[0])

    node_tree.links.new(node_tree.nodes['Index'].outputs['Index'], node_tree.nodes['Math.002'].inputs[0])

    node_tree.links.new(node_tree.nodes['Math.002'].outputs['Value'], node_tree.nodes['Math.003'].inputs[0])

    node_tree.links.new(node_tree.nodes['Random Value'].outputs['Value'], node_tree.nodes['Math.003'].inputs[1])

    node_tree.links.new(node_tree.nodes['Math.003'].outputs['Value'], node_tree.nodes['Combine XYZ'].inputs[0])

    node_tree.links.new(node_tree.nodes['Combine XYZ'].outputs['Vector'], node_tree.nodes['Rotate Rotation'].inputs[1])