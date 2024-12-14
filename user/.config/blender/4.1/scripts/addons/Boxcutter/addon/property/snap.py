import bpy

from bpy.types import PropertyGroup, Object, Mesh
from bpy.props import *

def hit_get(option):
    if not option.operator:
        option.hit = False

    return option['hit']

def hit_set(option, value):
    option['hit'] = value

class option(PropertyGroup):
    operator = None

    hit: BoolProperty(get=hit_get, set=hit_set)
    type: StringProperty()
    ngon_last: BoolProperty()

    display: BoolProperty()
    location: FloatVectorProperty()
    normal: FloatVectorProperty()
