import traceback
import bpy

from bl_ui.space_toolsystem_toolbar import VIEW3D_PT_tools_active as view3d_tools
from bl_ui.space_toolsystem_common import activate_by_id as activate_tool

name = __name__.partition('.')[0]


def hash_iter(iterable, *attributes, limit=0, prelen=True):
    from hashlib import sha3_512

    sample = str(len(iterable)) if prelen else ''
    for i, data in enumerate(iterable):
        if limit and i == limit:
            break

        if isinstance(data, str):
            sample += data
            continue

        for attr in attributes:
            sample += str(getattr(data, attr))

    _hash = sha3_512()
    _hash.update(sample.encode())

    return _hash.hexdigest()


def active_tool():
    active_tool = view3d_tools.tool_active_from_context(bpy.context)
    return active_tool if active_tool else type('fake_tool', (), {'idname': 'NONE', 'mode': 'OBJECT', 'operator_properties': lambda *_: None})


def activate_by_name(name):
    activate_tool(bpy.context, 'VIEW_3D', name)


def operator_override(context, op, override, *args, **kwargs):
    if not hasattr(context, 'temp_override'):
        return op({**override}, *args, **kwargs)

    with context.temp_override(**override):
        return op(*args, **kwargs)

def context_copy(context):
    '''Same as context.copy() but safe for operator redo in 4.x.x'''
    from types import BuiltinMethodType
    new_context = {}
    generic_attrs = (
        *bpy.types.bpy_struct.__dict__.keys(),
        "bl_rna", "rna_type", "copy", "property",
    )
    for attr in dir(context):
        if not (attr.startswith("_") or attr in generic_attrs):
            value = getattr(context, attr)
            if type(value) != BuiltinMethodType:
                new_context[attr] = value

    return new_context


def method_handler(method,
    arguments = tuple(),
    identifier = str(),
    exit_method = None,
    exit_arguments= tuple(),
    return_result = False,
    return_value = {'CANCELLED'}):
    '''
    method: method to call
    arguments: method arguments
    identifier: optional identifer for printout
    exit_method: optional exit method to call on exception
    exit_arguments: exit method arguments
    return_result: allows return of the method and values
    return_value: return value on exception
    '''
    identifier = identifier + ' ' if identifier else ''
    try:
        if return_result:
            return method(*arguments)
        else:
            method(*arguments)
    except Exception:
        print(F'\n{name} {identifier}Method Failed:\n')
        traceback.print_exc()

        if exit_method:
            try:
                if return_result:
                    return exit_method(*exit_arguments)
                else:
                    exit_method(*exit_arguments)
            except Exception:
                print(F'\n{name} {identifier}Exit Method Failed:\n')
                traceback.print_exc()

        if return_result:
            try: return return_value
            except Exception:
                print(F'\n{name} {identifier}Exit Return Value Failed:\n')
                traceback.print_exc()
