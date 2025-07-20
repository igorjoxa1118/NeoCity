import sys
from gpu.types import GPUBatch, GPUIndexBuf, GPUVertBuf, GPUShader, GPUUniformBuf


handlers = []


def load(shader):
    import os
    from ... utility.addon import path

    file = open(os.path.join(path(), 'addon', 'shader', shader), 'r')
    data = file.read()
    file.close()

    return data


def batch(shader, type, attributes={}, indices=[], vbo_length=0, vbo_length_prop_index=0):
    values = list(attributes.values())
    vbo_length = len(values[vbo_length_prop_index]) if not vbo_length and len(values) else vbo_length

    vbo = GPUVertBuf(shader.format_calc(), vbo_length)

    for prop, data in attributes.items():
        if len(data) != vbo_length:
            space = " " * 70
            raise ValueError(F'Batch shader failed; buffer/attribute length mismatch\n{space}Needed: {vbo_length}\n{space}Found: {len(data)}')

        vbo.attr_fill(prop, data)

    if len(indices):
        ibo = GPUIndexBuf(type=type, seq=indices)
        return GPUBatch(type=type, buf=vbo, elem=ibo)

    return GPUBatch(type=type, buf=vbo)


def new(*stubs, script=False):
    import bpy

    if bpy.app.version < (3, 4):
        return GPUShader(*(load(s) if script else s for s in stubs))

    import gpu
    from gpu.types import GPUStageInterfaceInfo, GPUShaderCreateInfo
    from uuid import uuid4

    from random import choice
    from string import ascii_lowercase

    interfaces = []
    constants = []

    # TODO: multi vert out?
    vert_out = GPUStageInterfaceInfo(F'{"".join(choice(ascii_lowercase) for _ in range(16))}')

    shader_info = GPUShaderCreateInfo()

    new.collect = False
    new.source = ''
    new.step = 0

    def parse(line, vertex=False, fragment=False):
        _type = 'vertex' if vertex else 'fragment'

        if ' ' not in line or line.startswith('//'):
            return

        t = line.split(' ')[1].upper()
        v = line.split(' ')[2][:-1]

        if new.collect:
            new.source += line + '\n'

        elif line.startswith('uniform'):
            if v in constants:
                return

            constants.append(v)
            shader_info.push_constant(t, v)

        elif line.startswith('in'):
            if vertex:
                getattr(shader_info, F'{_type}_in')(new.step, t, v)
                new.step += 1
                return

            return

        elif line.startswith('out'):
            if fragment:
                getattr(shader_info, F'{_type}_out')(new.step, t, v)
                new.step += 1
                return

            if any(v == i[0] for i in interfaces):
                return

            interfaces.append((v, vert_out.smooth(t, v)))
            getattr(shader_info, F'{_type}_out')(vert_out)

        elif 'void' in line:
            new.collect = True
            new.source += line + '\n'

    for i, stub in enumerate(stubs):
        stub = load(stub) if script else stub
        lines = stub.splitlines()

        new.collect = False
        new.source = ''
        new.step = 0

        for line in lines:
            if not line.strip():
                continue

            if i > 1:
                raise ValueError('Shader stubs must be vertex, fragment (WIP)')

            parse(line, vertex=not i, fragment=i)

        if script:
            new.source += '\n}'

        if not i:
            shader_info.vertex_source(new.source)
            continue

        shader_info.fragment_source(new.source)

    return gpu.shader.create_from_info(shader_info)

