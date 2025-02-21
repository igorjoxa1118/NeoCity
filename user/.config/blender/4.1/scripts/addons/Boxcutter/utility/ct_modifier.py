import bpy
from ctypes import Structure, cast, POINTER, addressof, c_int, c_void_p
import enum

class Link(Structure):
    pass

Link._fields_ = [
    ('next', POINTER(Link)),
    ('prev', POINTER(Link)),
]

class ListBase(Structure):
    pass

ListBase._fields_ = [
    ('first', POINTER(None)),
    ('last', POINTER(None)),
]

class ModifierData(Structure):
    pass

ModifierData._fields_ = [
    ('next', POINTER(ModifierData)),
    ('prev', POINTER(ModifierData)),
    ('type', c_int),
]


def mod_move_down(mod: bpy.types.Modifier, force=False) -> str:
    '''Move modifier down without triggering modifier update\n
    If move failed returns string describing error, otherwise None'''

    pt_mod_list = unsafe_mod_list_get(mod.id_data)
    pt_mod = cast(mod.as_pointer(), POINTER(ModifierData))

    if pt_mod.contents.next:
        if not force and get_behavior(pt_mod.contents.type)[1]:
            n_type = pt_mod.contents.next.contents.type

            if behavior.Other == get_behavior(n_type)[0]:
                return "Move Below Non Deform"

        unsafe_move_next(pt_mod, pt_mod_list)
        return

    return 'Mod is last'


def mod_move_up(mod: bpy.types.Modifier, force=False) -> str:
    '''Move modifier up without triggering modifier update\n
    If move failed returns string describing error, otherwise None
    force - specfies if move should be performed without ensuring stack validity'''

    pt_mod_list = unsafe_mod_list_get(mod.id_data)
    pt_mod = cast(mod.as_pointer(), POINTER(ModifierData))

    if pt_mod.contents.prev:
        if not force and behavior.Other == get_behavior(pt_mod.contents.type)[0]:
            p_type = pt_mod.contents.prev.contents.type

            if get_behavior(p_type)[1]:
                return "Move above Req.Original data"

        unsafe_move_prev(pt_mod, pt_mod_list)
        return

    return 'Mod is first'


def mod_move_to_index(mod: bpy.types.Modifier, index: int, force=False) -> str:
    '''Move modifier to specified index without triggering modifier update.\n
    Negative indices are not supported. Out of bounds indices are clamped.
    If move failed returns string describing error, otherwise None.
    force - specfies if move should be performed without ensuring stack validity'''

    m_index = mod.id_data.modifiers.find(mod.name)
    if m_index == index : return 'Mod is at index'


    if force:
        obj = mod.id_data
        imax = len(obj.modifiers) - 1
        index = index if index < imax else imax
        if m_index == index : return 'Mod is at index'

        pt_mod = cast(mod.as_pointer(), POINTER(Link))
        pt_mlist = unsafe_mod_list_get(obj)
        pt_dest = cast(obj.modifiers[index].as_pointer(), POINTER(Link))

        if index > m_index:
            unsafe_move_after(pt_mod, pt_dest, pt_mlist)

        else:
            unsafe_move_before(pt_mod, pt_dest, pt_mlist)

        return

    if m_index > index:
        while m_index > index:
            m_index -= 1
            res = mod_move_up(mod, force=False)
            if res:
                return  res

    else:
        while m_index < index:
            m_index += 1
            res = mod_move_down(mod, force=False)
            if res:
                return  res


def unsafe_move_next(pt_link: Link, pt_list: ListBase) -> bool:
    '''Move link to next position. Assumes link is in the list, not null and can be moved\n
    All arguments are pointer objects!'''

    link = pt_link.contents
    next = link.next.contents
    list = pt_list.contents

    if not next.next:
        list.last = addressof(link)

    else:
        next.next.contents.prev = pt_link

    if not link.prev:
        list.first = addressof(next)
    else:
        link.prev.contents.next.contents = next

    link.next = next.next
    next.prev = link.prev

    link.prev.contents = next
    next.next = pt_link


def unsafe_move_prev(pt_link: Link, pt_list: ListBase) -> bool:
    '''Move link to previous position. Assumes link is in the list, not null and can be moved\n
    All arguments are pointer objects!'''

    link = pt_link.contents
    prev = link.prev.contents
    list = pt_list.contents

    if not prev.prev:
        list.first = addressof(link)

    else:
        prev.prev.contents.next.contents = link

    if not link.next:
        list.last = addressof(prev)
    else:
        link.next.contents.prev.contents = prev

    link.prev = prev.prev
    prev.next = link.next

    link.next.contents = prev
    prev.prev = pt_link


def unsafe_swap(pt_link_a: Link, pt_link_b: Link, pt_list: ListBase) -> None:
    '''Swap two list links. Assumes both links are in the list and neither is null\n
    All arguments are pointer objects!'''

    link_a = pt_link_a.contents
    link_b = pt_link_b.contents

    if link_a.next and addressof(link_a.next.contents) == addressof(link_b):
        unsafe_move_next(pt_link_a, pt_list)
        return

    elif link_a.prev and addressof(link_a.prev.contents) == addressof(link_b):
        unsafe_move_prev(pt_link_a, pt_list)
        return

    list = pt_list.contents

    if not link_a.next:
        list.last = addressof(link_b)

    else:
        link_a.next.contents.prev.contents = link_b

    if not link_b.next:
        list.last = addressof(link_a)

    else:
        link_b.next.contents.prev.contents = link_a


    if not link_a.prev:
        list.first = addressof(link_b)


    else:
        link_a.prev.contents.next.contents = link_b

    if not link_b.prev:
        list.first = addressof(link_a)

    else:
        link_b.prev.contents.next.contents = link_a

    link_a_copy = Link(link_a.next, link_a.prev)

    link_a.prev = link_b.prev
    link_a.next = link_b.next

    link_b.prev = link_a_copy.prev
    link_b.next = link_a_copy.next


def unsafe_move_before(pt_link: Link, pt_target: Link, pt_list: ListBase) -> None:
    '''Move Link before position of the target, moving target forward\n
    Assumes both links are in the list, not null and are not the same link!\n
    All arguments are pointer objects!'''

    link = pt_link.contents
    target = pt_target.contents
    list = pt_list.contents

    if link.next:
        link.next.contents.prev = link.prev

    else:
        list.last = cast(link.prev, c_void_p)

    if link.prev:
        link.prev.contents.next = link.next

    else:
        list.first = cast(link.next, c_void_p)

    if target.prev:
        target.prev.contents.next = pt_link

    else:
        list.first = cast(pt_link, c_void_p)

    link.prev = target.prev
    link.next = pt_target
    target.prev = pt_link

def unsafe_move_after(pt_link: Link, pt_target: Link, pt_list: ListBase) -> None:
    '''Move Link after position of the target, moving target forward\n
    Assumes both links are in the list, not null and are not the same link!\n
    All arguments are pointer objects!'''

    link = pt_link.contents
    target = pt_target.contents
    list = pt_list.contents

    if link.next:
        link.next.contents.prev = link.prev

    else:
        list.last = cast(link.prev, c_void_p)

    if link.prev:
        link.prev.contents.next = link.next

    else:
        list.first = cast(link.next, c_void_p)

    if target.next:
        target.next.contents.prev = pt_link

    else:
        list.last = cast(pt_link, c_void_p)

    link.next = target.next
    link.prev = pt_target
    target.next = pt_link


MOD_OFFSET = 0
def unsafe_mod_list_get(obj: bpy.types.Object) -> ListBase:
    '''Get pointer to ListBase struct from the object. Object must have at least 1 modifier.'''

    global MOD_OFFSET
    object_ptr = obj.as_pointer()

    if MOD_OFFSET:
        return cast(object_ptr + MOD_OFFSET, POINTER(ListBase))

    # poke object memory to find byteoffset from object pointer to modifier list, which is just pointers to frst and last mod

    current_ptr = object_ptr
    fmod_ptr = obj.modifiers[0].as_pointer()
    lmod_ptr = obj.modifiers[-1].as_pointer()
    mod_list = None

    while True:
        lst = cast(current_ptr, POINTER(ListBase))

        if lst.contents.first == fmod_ptr and lst.contents.last == lmod_ptr:
            mod_list = lst
            MOD_OFFSET = current_ptr - object_ptr
            break

        current_ptr += 1

    return mod_list

class behavior(enum.Enum):
    Other = 0
    OnlyDeform = 1


def get_behavior(mod_type: int):
    if mod_type > len(MODIFIER_TYPES) - 1 or mod_type < 0:
        return (behavior.Other, False)

    return MODIFIER_TYPES[mod_type]


MODIFIER_TYPES = [
    (behavior.Other,  False)         , #ModifierType_eModifierType_None: ModifierType = 0;
    (behavior.Other,  False)         , #ModifierType_eModifierType_Subsurf: ModifierType = 1;
    (behavior.OnlyDeform,  False)         , #ModifierType_eModifierType_Lattice: ModifierType = 2;
    (behavior.OnlyDeform,  False)         , #ModifierType_eModifierType_Curve: ModifierType = 3;
    (behavior.Other,  False)         , #ModifierType_eModifierType_Build: ModifierType = 4;
    (behavior.Other,  False)         , #ModifierType_eModifierType_Mirror: ModifierType = 5;
    (behavior.Other,  False)         , #ModifierType_eModifierType_Decimate: ModifierType = 6;
    (behavior.OnlyDeform,  False)         , #ModifierType_eModifierType_Wave: ModifierType = 7;
    (behavior.OnlyDeform,  False)         , #ModifierType_eModifierType_Armature: ModifierType = 8;
    (behavior.OnlyDeform,  False)         , #ModifierType_eModifierType_Hook: ModifierType = 9;
    (behavior.OnlyDeform,  True)         , #ModifierType_eModifierType_Softbody: ModifierType = 10;
    (behavior.Other,  False)         , #ModifierType_eModifierType_Boolean: ModifierType = 11;
    (behavior.Other,  False)         , #ModifierType_eModifierType_Array: ModifierType = 12;
    (behavior.Other,  False)         , #ModifierType_eModifierType_EdgeSplit: ModifierType = 13;
    (behavior.OnlyDeform,  False)         , #ModifierType_eModifierType_Displace: ModifierType = 14;
    (behavior.Other,  False)         , #ModifierType_eModifierType_UVProject: ModifierType = 15;
    (behavior.Other,  False)         , #ModifierType_eModifierType_Smooth: ModifierType = 16;
    (behavior.OnlyDeform,  False)         , #ModifierType_eModifierType_Cast: ModifierType = 17;
    (behavior.OnlyDeform,  False)         , #ModifierType_eModifierType_MeshDeform: ModifierType = 18;
    (behavior.Other,  False)         , #ModifierType_eModifierType_ParticleSystem: ModifierType = 19;
    (behavior.OnlyDeform,  False)         , #ModifierType_eModifierType_ParticleInstance: ModifierType = 20;
    (behavior.Other,  False)         , #ModifierType_eModifierType_Explode: ModifierType = 21;
    (behavior.OnlyDeform,  False)         , #ModifierType_eModifierType_Cloth: ModifierType = 22;
    (behavior.OnlyDeform,  False)         , #ModifierType_eModifierType_Collision: ModifierType = 23;
    (behavior.Other,  False)         , #ModifierType_eModifierType_Bevel: ModifierType = 24;
    (behavior.OnlyDeform,  False)         , #ModifierType_eModifierType_Shrinkwrap: ModifierType = 25;
    (behavior.Other,  False)         , #ModifierType_eModifierType_Fluidsim: ModifierType = 26; ?there us noe .c file for it
    (behavior.Other,  False)         , #ModifierType_eModifierType_Mask: ModifierType = 27;
    (behavior.Other,  False)         , #ModifierType_eModifierType_SimpleDeform: ModifierType = 28;
    (behavior.Other,  True)          , #ModifierType_eModifierType_Multires: ModifierType = 29;
    (behavior.OnlyDeform,  False)         , #ModifierType_eModifierType_Surface: ModifierType = 30;
    (behavior.Other,  False)         , #ModifierType_eModifierType_Smoke: ModifierType = 31; DEPRECATED! for array padding only
    (behavior.OnlyDeform,  False)         , #ModifierType_eModifierType_ShapeKey: ModifierType = 32;
    (behavior.Other,  False)         , #ModifierType_eModifierType_Solidify: ModifierType = 33;
    (behavior.Other,  False)         , #ModifierType_eModifierType_Screw: ModifierType = 34;
    (behavior.OnlyDeform,  False)         , #ModifierType_eModifierType_Warp: ModifierType = 35;
    (behavior.Other,  False)         , #ModifierType_eModifierType_WeightVGEdit: ModifierType = 36;
    (behavior.Other,  False)         , #ModifierType_eModifierType_WeightVGMix: ModifierType = 37;
    (behavior.Other,  False)         , #ModifierType_eModifierType_WeightVGProximity: ModifierType = 38;
    (behavior.Other,  False)         , #ModifierType_eModifierType_Ocean: ModifierType = 39;
    (behavior.Other,  False)         , #ModifierType_eModifierType_DynamicPaint: ModifierType = 40;
    (behavior.Other,  False)         , #ModifierType_eModifierType_Remesh: ModifierType = 41;
    (behavior.Other,  False)         , #ModifierType_eModifierType_Skin: ModifierType = 42;
    (behavior.OnlyDeform,  False)         , #ModifierType_eModifierType_LaplacianSmooth: ModifierType = 43;
    (behavior.Other,  False)         , #ModifierType_eModifierType_Triangulate: ModifierType = 44;
    (behavior.Other,  False)         , #ModifierType_eModifierType_UVWarp: ModifierType = 45;
    (behavior.OnlyDeform,  False)         , #ModifierType_eModifierType_MeshCache: ModifierType = 46;
    (behavior.OnlyDeform,  False)         , #ModifierType_eModifierType_LaplacianDeform: ModifierType = 47;
    (behavior.Other,  False)         , #ModifierType_eModifierType_Wireframe: ModifierType = 48;
    (behavior.Other,  False)         , #ModifierType_eModifierType_DataTransfer: ModifierType = 49;
    (behavior.Other,  False)         , #ModifierType_eModifierType_NormalEdit: ModifierType = 50;
    (behavior.OnlyDeform,  False)         , #ModifierType_eModifierType_CorrectiveSmooth: ModifierType = 51;
    (behavior.Other,  False)         , #ModifierType_eModifierType_MeshSequenceCache: ModifierType = 52;
    (behavior.OnlyDeform,  False)         , #ModifierType_eModifierType_SurfaceDeform: ModifierType = 53;
    (behavior.Other,  False)         , #ModifierType_eModifierType_WeightedNormal: ModifierType = 54;
    (behavior.Other,  False)         , #ModifierType_eModifierType_Weld: ModifierType = 55;
    (behavior.Other,  False)         , #ModifierType_eModifierType_Fluid: ModifierType = 56;
    (behavior.Other,  False)         , #ModifierType_eModifierType_links: ModifierType = 57;
    (behavior.Other,  False)         , #ModifierType_eModifierType_MeshToVolume: ModifierType = 58;
    (behavior.Other,  False)         , #ModifierType_eModifierType_VolumeDisplace: ModifierType = 59;
    (behavior.Other,  False)         , #ModifierType_eModifierType_VolumeToMesh: ModifierType = 60;
    (behavior.Other,  False)         , #ModifierType_NUM_MODIFIER_TYPES: ModifierType = 61;
]