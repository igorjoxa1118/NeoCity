from bpy.types import PropertyGroup
from bpy.props import BoolProperty


class option(PropertyGroup):
    general: BoolProperty(name="General", description="Expand or collapse panel", default = False)
    workflow: BoolProperty(name="Workflow", description="Expand or collapse panel", default = False)
    sharp: BoolProperty(name="Sharp", description="Expand or collapse panel", default = False)
    mesh: BoolProperty(name="Mesh", description="Expand or collapse panel", default = False)
    bevel: BoolProperty(name="Bevel", description="Expand or collapse panel", default = False)
    booleans: BoolProperty(name="Boolean", description="Expand or collapse panel", default = False)
    opt_ins: BoolProperty(name="Optimize It", description="Expand or collapse panel", default = False)
