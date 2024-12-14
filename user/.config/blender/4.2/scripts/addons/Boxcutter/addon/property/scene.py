import bpy

from bpy.types import PropertyGroup, Object, Collection
from bpy.props import *
from mathutils import Matrix

from . import last, snap
from . utility import update
from .. import toolbar


def custom_object(option, obj):
    return obj.type in {'MESH', 'FONT', 'CURVE'}


# TODO: move scene cleanup related logic from data.clean
def cleanup(self, _):
    if self.running:
        return

    option.operator = toolbar.option()


def q_bevel(self, context):
    if not self.running:
        return

    from .. operator.shape.utility.modal import bevel
    from ... utility import addon
    preference = addon.preference()

    # bc.q_back_only = event.shift and bc.q_bevel
    self.shape.data.bc.q_beveled = self.q_bevel

    for mod in self.shape.modifiers:
        if mod.type == 'BEVEL':
            if mod.name.startswith('Bevel'):
                preference.shape['bevel_segments'] = mod.segments

            self.shape.modifiers.remove(mod)

    last = preference.shape['bevel_segments']
    preference.shape['front_bevel_segments'] = last
    preference.shape['quad_bevel_segments'] = last

    last = self.operator.last['modifier']['bevel_width']
    self.operator.last['modifier']['quad_bevel_width'] = last
    self.operator.last['modifier']['front_bevel_width'] = last

    bevel.shape(self.operator, context, False)


class option(PropertyGroup):
    operator = None
    shader = None
    extract_matrix = None

    repeat_data = {
        'lattice_deform' : [],
        'modifiers' : [],
        'array' : False,
        'array_circle': False,
        'bevel' : False,
        'solidify' : False,
        'last_depth' : 0.0,
        'ngon_fit' : False,
        'shape_type' : 'BOX',
        'wedge_points' : [],
        'taper' : 1,
        'delta_matrix' : Matrix(),
        'vertex_groups' : [],
        'inverted_extrude' :  False,
        'clamp_extrude' : True,
        'flipped_normals' : False,
        'flip_x' : False,
        'flip_y' : False,
        'flip_z' : False,
        'proportional_draw' : False,

        'geo_indices' : {
            'top_edge' : [],
            'mid_edge' : [],
            'bot_edge' : [],
            'top_face' : [],
            'bot_face' : []},
    }

    running: BoolProperty(update=cleanup)
    q_back_only: BoolProperty()
    location: FloatVectorProperty()
    mirror_axis: IntVectorProperty(default=(0, 0, 0))
    mirror_axis_flip: IntVectorProperty(default=(0, 0, 0))
    stored_collection: PointerProperty(type=Collection)
    stored_shape: PointerProperty(type=Object)
    rotated_inside: IntProperty()
    wedge_point: IntProperty()
    wedge_point_delta: IntProperty()
    wedge_slim: BoolProperty()
    flip: BoolProperty()
    snap_type: StringProperty()
    extract_name: StringProperty()

    axis: EnumProperty(
        items = [
            ('NONE', 'None', 'Use default behavior'),
            ('X', 'X', 'Modal Shortcut: X'),
            ('Y', 'Y', 'Modal Shortcut: Y'),
            ('Z', 'Z', 'Modal Shortcut: Z')],
        default = 'NONE')

    start_operation: EnumProperty(
        name = 'Start Operation',
        description = '\n',
        update = update.change_start_operation,
        items = [
            ('NONE', 'Default', '\n Modal Shortcut: TAB', 'LOCKED', 0),
            ('SOLIDIFY', 'Solidify', '\n Modal Shortcut: T\n\n'
                                     ' T - adjust thickness / Remove Modifier\n'
                                     ' 1, 2, 3, - cycles offset type on solidify modifier', 'MOD_SOLIDIFY', 1),
            ('MIRROR', 'Mirror', '\n Modal Shortcut: 1, 2, 3\n\n'
                                 ' Press 1, 2, 3 for axis X, Y, Z\n'
                                 ' Shift + 1, 2, or 3 to flip axis', 'MOD_MIRROR', 2),
            ('ARRAY', 'Array', '\n Modal Shortcut: V\n\n'
                               ' X, Y, Z, keys to change axis during array\n'
                               ' Shift + R - to reset array distance\n'
                               ' V - cycle radial array / remove array', 'MOD_ARRAY', 3),
            ('BEVEL', 'Bevel', '\n Modal Shortcut: B\n\n'
                               ' B - add bevel / remove modifier\n'
                               ' Q: Toggle back face bevel', 'MOD_BEVEL', 4)],
      default = 'NONE')

    original_active: PointerProperty(type=Object)
    lattice: PointerProperty(type=Object)
    slice: PointerProperty(type=Object)
    inset: PointerProperty(type=Object)
    bevel: PointerProperty(type=Object)
    plane: PointerProperty(type=Object)
    empty: PointerProperty(type=Object)

    snap: PointerProperty(type=snap.option)
    last: PointerProperty(type=last.option)

    collection: PointerProperty(
        name = 'Collection',
        description = '\n Collection for created objects.\n\n Default: "Cutters" \n New collection is created if set collection is not part of the scene',
        # update = update.store_collection,
        type = Collection)

    shape: PointerProperty(
        name = 'Shape',
        description = '\n Shape object',
        poll = custom_object,
        update = update.store_shape,
        type = Object)

    recall_collection: PointerProperty(
        name = 'Recall collection',
        description = '\n Collection to recall objects from',
        #update = update.store_collection,
        type = Collection)

    bevel_front_face: BoolProperty(
        name = 'Bevel Front Face',
        description = '\n Bevel the front face of the shape',
        default = False)

    q_bevel: BoolProperty(
        name = 'Bevel Back Face',
        description = '\n Bevel the back face of the shape',
        update = q_bevel,
        default = False)
