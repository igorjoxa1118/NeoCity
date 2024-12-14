import bpy

from math import radians

# from .... utility import modifier
from .. import modifier
from ...... utility import addon, screen


def shape(op, context, event):
    bc = context.scene.bc
    preference = addon.preference()

    displace = None

    for mod in bc.shape.modifiers:
        if mod.type == 'DISPLACE':
            displace = mod

            break

    if not displace:
        displace = bc.shape.modifiers.new('Displace', 'DISPLACE')
        displace.direction = 'X'
        displace.strength = preference.shape.displace
        displace.mid_level = 0

    location = op.view3d['location'].x + op.start['displace']

    displace.strength = location

    #XXX: updating tracked states array distance using this intersect_distance
    from .. import tracked_states
    tracked_states.array_distance = abs(location)

    op.last['modifier']['displace'] = displace.strength

    preference.shape['array_distance'] = displace.strength
    preference.shape['displace'] = displace.strength
