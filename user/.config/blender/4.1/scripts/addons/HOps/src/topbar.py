from bpy.utils import register_tool, unregister_tool

from . tools.hopstool import Hops, HopsEdit
from . tools.mirror import HopsMirror


def register():

    # register_tool(Hops, after='builtin.measure', separator=True)
    register_tool(Hops, after=None, separator=True)
    # register_tool(HopsEdit, after='builtin.measure', separator=True)
    register_tool(HopsEdit, after=None, separator=True)


def unregister():

    # unregister_tool(HopsMirror)
    unregister_tool(HopsEdit)
    unregister_tool(Hops)
