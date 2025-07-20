import bpy
from bpy.types import PropertyGroup
from bpy.props import EnumProperty, PointerProperty, IntProperty, BoolProperty, FloatProperty
from ..utility import addon
from ..utility.collections import turn_on_parent_collections

status_items = [
    ("UNDEFINED", "Undefined", "", "NONE", 0),
    ("CSHARP", "CSharp", "", "NONE", 1),
    ("CSTEP", "CStep", "", "NONE", 2),
    ("BOOLSHAPE", "BoolShape", "", "NONE", 3),
    ("BOOLSHAPE2", "BoolShape2", "", "NONE", 4)]

# Array V2
axis_items = [
    ("X", "x", "", "NONE", 0),
    ("Y", "y", "", "NONE", 1),
    ("Z", "z", "", "NONE", 2)]


def get_modifier_with_type(object, modifier_type):
    for modifier in object.modifiers:
        if modifier.type == modifier_type:
            return modifier
    return None


def active_mod_index(self, context):
    try: # for obsolete blender versions
        obj = self.id_data
        mod = obj.modifiers[self.active_modifier_index]
        obj.modifiers.active = mod
    except:
        pass


def update_bevel_helper_hide(self, context):
    obj = self.id_data  # self refers to HOPSProperties, id_data gives the object it's attached to
    if self.is_user_triggered:
        turn_on_parent_collections(obj, context.scene.collection)
        obj.hide_set(self.bevel_helper_hide)

        if not self.bevel_helper_hide:
            bpy.ops.hops.draw_wire_mesh_launcher('INVOKE_DEFAULT', target='NONE', object_name=obj.name)
    else:
        self.bevel_helper_hide = obj.hide_get()
    self.is_user_triggered = True


class HOpsObjectProperties(PropertyGroup):

    status: EnumProperty(name="Status", default="UNDEFINED", items=status_items)
    adaptivesegments: IntProperty("Adaptive Segments", default=3, min=-10, max=25)

    def pending_boolean(self):
        return get_modifier_with_type(self.id_data, "BOOLEAN") is not None

    is_pending_boolean: BoolProperty(name="Is Pending Boolean", get=pending_boolean)
    is_global: BoolProperty(name="Is Global", description="Auto smooth angle will be overwritten by Csharp/Ssharp operators", default=True)

    array_x: FloatProperty(name="Array gizmo x", description="Array gizmo x", default=0)
    array_y: FloatProperty(name="Array gizmo y", description="Array gizmo y", default=0)
    array_z: FloatProperty(name="Array gizmo z", description="Array gizmo z", default=0)

    last_array_axis: EnumProperty(name="array_axis", default="X", items=axis_items)

    is_poly_debug_display: BoolProperty(name="Poly Debug Display", default=False)
    active_modifier_index: IntProperty(update=active_mod_index)

    bevel_helper_hide: BoolProperty(
        name="Bevel Helper Hide",
        description="Hide/Show Bevel Helper",
        default=False,
        update=update_bevel_helper_hide
    )
    is_user_triggered: BoolProperty(default=True) 


class HOpsMeshProperties(PropertyGroup):
    hops_undo: BoolProperty(name="Hops Undo System", default=False)


class HOpsNodeProperties(PropertyGroup):
    maps_system: BoolProperty(name="Maps System Group", default=False)
    just_created: BoolProperty(name="Maps System Just Created", default=False)
    roughness_mix: BoolProperty(name="Maps Roughness", default=False)
    color_mix: BoolProperty(name="Maps Roughness", default=False)
    metal_mix: BoolProperty(name="Maps Roughness", default=False)
    viewer: BoolProperty(name="Maps Viewer Node", default=False)


class HOpsImgProperties(PropertyGroup):
    maps_system: BoolProperty(name="Maps System Group", default=False)
    just_created: BoolProperty(name="Maps System Just Created ", default=False)
