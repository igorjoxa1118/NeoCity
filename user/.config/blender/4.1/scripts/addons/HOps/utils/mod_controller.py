import bpy
from mathutils import Vector
from . modifiers import get_mod_copy, transfer_mod_data
from .. utility import modifier
from .profile import get_bevel_profile, set_bevel_profile


class Mod_Data:
    def __init__(self, mod, created=False):
        self.mod = mod
        self.mod_copy = get_mod_copy(mod)
        self.was_created = created
        self.logically_deleted = False
        # Sort
        self.name = ''
        self.remove = False
        # Profiles
        self.profile = None

        self.__setup()


    def __setup(self):
        if not self.mod: return

        if self.mod.type == 'BEVEL':
            if hasattr(self.mod, 'use_custom_profile'):
                if self.mod.use_custom_profile:
                    self.profile = get_bevel_profile(self.mod)

            elif hasattr(self.mod, 'profile_type'):
                if self.mod.profile_type == 'CUSTOM':
                    self.profile = get_bevel_profile(self.mod)


    def revert(self):
        if not self.mod: return
        transfer_mod_data(self.mod, self.mod_copy)
        if self.mod.type == 'BEVEL':
            if self.profile:
                set_bevel_profile(self.mod, self.profile, False)


    def is_valid(self):
        if not self.mod: return False
        if self.logically_deleted: return False
        return True


class Obj_Data:
    def __init__(self, context, obj):
        self.obj = obj
        self.mod_datas = []
        self.index = 0
        self.mesh = None
        self.stroke = None
        self.dims = (0,0,0)
        self.scale = Vector((1,1,1))

        if type(obj) == bpy.types.Object:

            self.scale = obj.scale.copy()

            if type(obj.data) == bpy.types.Mesh:
                self.mesh = obj.data
                self.dims = get_obj_dims(context, obj)

            elif type(obj.data) == bpy.types.GreasePencil:
                self.stroke = obj.data
                self.dims = get_obj_dims(context, obj)


    def active_mod(self):
        '''The active mod being used'''

        if self.__ensure_index():
            return self.mod_datas[self.index].mod
        return None


    def active_mod_data(self):
        '''The active Mod Data being used'''

        if self.__ensure_index():
            return self.mod_datas[self.index]
        return None


    def all_active_mods(self):
        '''All mods that are valid / not loggicaly deleted'''

        mods = []
        for mod_data in self.mod_datas:
            if mod_data.logically_deleted == False:
                if mod_data.mod:
                    mods.append(mod_data.mod)
        return mods


    def __ensure_index(self):
        if self.index > len(self.mod_datas) - 1:
            self.index = len(self.mod_datas) - 1
        if self.index < 0:
            self.index = 0
        if len(self.mod_datas) == 0:
            return False
        return True


class Mod_Controller:
    def __init__(self, context, objs, type_map={}, create_new=False, active_obj=None):
        '''
        Type Map = KEY -> Object Type : VAL -> Mod Type
        Example = {bpy.types.Mesh : 'Array', bpy.types.GreasePencil : 'GP_ARRAY'}
        '''

        self.obj_datas = []
        self.type_map = type_map
        self.active_obj = active_obj

        # Setup
        for obj in objs:

            # Validate
            if not valid_object_type(self.type_map, obj): continue

            obj_data = Obj_Data(context, obj)

            # Mod Object
            mod_object = modifier_container(self.type_map, obj)
            if mod_object == None: continue

            # Mod Type
            valid_mod_type = mod_type_from_map(self.type_map, obj)
            if not valid_mod_type: continue

            # Capture
            for mod in mod_object:
                if mod.type == valid_mod_type:
                    mod_data = Mod_Data(mod)
                    mod.show_expanded = False

                    obj_data.mod_datas.append(mod_data)

            # Create
            if create_new or len(obj_data.mod_datas) == 0:
                mod = mod_object.new(valid_mod_type.title(), valid_mod_type)
                mod_data = Mod_Data(mod, created=True)
                mod.show_expanded = False

                obj_data.mod_datas.append(mod_data)

            # Store
            self.obj_datas.append(obj_data)

        # Index
        for obj_data in self.obj_datas:
            obj_data.index = len(obj_data.mod_datas) - 1
            if obj_data.index < 0:
                obj_data.index = 0

        # Active Validate
        valid = True
        if not self.active_obj: valid = False
        if type(self.active_obj) != bpy.types.Object: valid = False
        if type(self.active_obj.data) not in self.type_map: valid = False

        if valid == False:
            for obj_data in self.obj_datas:
                self.active_obj = obj_data.obj
                break
        else:
            # Search for active
            valid_active_obj = False
            for obj_data in self.obj_datas:
                if obj_data.obj == self.active_obj:
                    valid_active_obj = True
                    break
            # Fall back to first
            if not valid_active_obj:
                for obj_data in self.obj_datas:
                    self.active_obj = obj_data.obj
                    break


    def set_attr(self, attr='', value=0):
        '''Set attributes on all mods : contains saftey checks'''

        for obj_data in self.obj_datas:
            if not self.__validate_index(obj_data): continue
            mod = obj_data.mod_datas[obj_data.index].mod
            if not mod: continue
            if not hasattr(mod, attr): continue
            setattr(mod, attr, value)

    # --- ACTIVE --- #

    def active_modifiers(self, with_obj=False):
        '''For each Obj Data -> return the active Modifier'''

        mods = []
        for obj_data in self.obj_datas:
            if not self.__validate_index(obj_data): continue
            mod = obj_data.mod_datas[obj_data.index].mod
            if not mod: continue
            if with_obj: mods.append((obj_data.obj, mod))
            else: mods.append(mod)
        return mods


    def active_mod_datas(self):
        '''For each Obj Data -> return the active Mod Data'''

        datas = []
        for obj_data in self.obj_datas:
            if not self.__validate_index(obj_data): continue
            datas.append(obj_data.mod_datas[obj_data.index])
        return datas


    def active_object_mod(self, as_obj_data=False):
        '''Active obj -> Return the active mod'''

        obj_data = self.__active_object_data()

        if obj_data:
            if self.__validate_index(obj_data):
                if as_obj_data: return obj_data
                return obj_data.mod_datas[obj_data.index].mod

        # Return first on failure
        for obj_data in self.obj_datas:
            if not self.__validate_index(obj_data): continue
            if as_obj_data: return obj_data
            return obj_data.mod_datas[obj_data.index].mod

        return None


    def active_obj_mod_index(self):
        '''Active obj -> active mod data index'''

        obj_data = self.__active_object_data()
        if obj_data: return obj_data.index
        # Return first index
        for obj_data in self.obj_datas:
            return obj_data.index
        # Fallback
        return 0


    def active_obj_mods(self):
        '''All mods on active object / excludes logically deleted mods / invalid mods'''

        obj_data = self.__active_object_data()
        mods = []
        if not obj_data: return mods

        for mod_data in obj_data.mod_datas:
            if not mod_data.logically_deleted:
                if mod_data.mod:
                    mods.append(mod_data.mod)
        return mods

    # --- VALIDATED --- #

    def validated_obj_datas(self):
        datas = []
        for obj_data in self.obj_datas:
            if not self.__validate_index(obj_data): continue
            datas.append(obj_data)
        return datas

    # --- CREATE / DELETE --- #

    def loggically_deleted_mods(self, active_only=False):
        '''Return all the logically deleted mods (Viewport display is off / flagged for delete)'''

        mods = []
        if active_only:
            for obj_data in self.obj_datas:
                if obj_data.obj != self.active_obj: continue
                for mod_data in obj_data.mod_datas:
                    if mod_data.logically_deleted:
                        mods.append(mod_data.mod)
                return mods

        for obj_data in self.obj_datas:
            for mod_data in obj_data.mod_datas:
                if mod_data.logically_deleted:
                    mods.append(mod_data.mod)
        return mods


    def remove_active_mod(self, leave_one=True, use_logical_delete=False, remove_if_created=False):
        '''Remove mods / Handle index safety'''

        def perma_remove_mod(obj_data):
            mod_data = obj_data.mod_datas[obj_data.index]
            mod = mod_data.mod
            mod_object = modifier_container(self.type_map, obj_data.obj)
            mod_object.remove(mod)
            obj_data.mod_datas.remove(mod_data)
            self.__set_next_available_index(obj_data)


        for obj_data in self.obj_datas:
            if not self.__validate_index(obj_data): continue

            # Check if available mods is greater than 1
            if leave_one:
                count = 0
                for mod_data in obj_data.mod_datas:
                    if mod_data.logically_deleted: continue
                    count += 1
                if count <= 1: continue

            # Stop loggical delete if remove_if_created
            if remove_if_created:
                if obj_data.mod_datas[obj_data.index].was_created:
                    perma_remove_mod(obj_data)
                    continue


            if use_logical_delete:
                obj_data.mod_datas[obj_data.index].logically_deleted = True
                obj_data.mod_datas[obj_data.index].mod.show_viewport = False
                self.__set_next_available_index(obj_data)
                continue

            perma_remove_mod(obj_data)


    def create_new_mod(self, count_limit=None):
        '''Create a new mod on each object : uses type map for each object'''

        mods = []
        for obj_data in self.obj_datas:

            if type(count_limit) == int:
                count = 0
                for mod_data in obj_data.mod_datas:
                    if mod_data.logically_deleted == False:
                        count += 1
                if count > count_limit: continue

            obj = obj_data.obj

            mod_object = modifier_container(self.type_map, obj)
            if not mod_object: continue

            valid_mod_type = mod_type_from_map(self.type_map, obj)
            if not valid_mod_type: continue

            mod = mod_object.new(valid_mod_type.title(), valid_mod_type)
            mod_data = Mod_Data(mod, created=True)
            mod.show_expanded = False

            obj_data.mod_datas.append(mod_data)
            obj_data.index = len(obj_data.mod_datas) - 1
            mods.append(mod)
        return mods

    # --- MOVE : INDEX / STACK POSITION --- #

    def move_mod(self, context, up=True):
        '''Move active modifiers on the stack'''

        active_obj = context.active_object
        for obj, mod in self.active_modifiers(with_obj=True):
            context.view_layer.objects.active = obj
            if up: bpy.ops.object.modifier_move_up(modifier=mod.name)
            else: bpy.ops.object.modifier_move_down(modifier=mod.name)

        context.view_layer.objects.active = active_obj


    def clamped_next_mod_index(self, forward=True):
        '''Move the active mod index: stopping at clamped lengths'''

        for obj_data in self.obj_datas:
            if not self.__validate_index(obj_data): continue

            og_index = obj_data.index
            if forward:
                # Already maxed
                if og_index == len(obj_data.mod_datas) - 1:
                    continue
                # Try next
                for index, mod_data in enumerate(obj_data.mod_datas):
                    if index > og_index:
                        if mod_data.logically_deleted == False:
                            obj_data.index = index
                            break
            else:
                # Check for first
                if og_index == 0: continue
                # Check previous
                count = og_index
                while count:
                    count -= 1
                    # Limit
                    if count < 0:
                        obj_data.index = og_index
                        break
                    # Search back for previous available
                    if obj_data.mod_datas[count].logically_deleted == False:
                        obj_data.index = count
                        break


    def cyclic_directional_mod_index(self, forward=True):
        '''Set the next mod index but using direction.'''

        for obj_data in self.obj_datas:
            if not self.__validate_index(obj_data): continue
            og_index = obj_data.index
            valid_indexes = [i for i, mod_data in enumerate(obj_data.mod_datas) if mod_data.is_valid()]
            if not valid_indexes: continue

            new_index = None

            if forward:
                for index in valid_indexes:
                    if index > og_index:
                        new_index = index
                        break
                if new_index == None:
                    new_index = valid_indexes[0]

            else:
                for index in reversed(valid_indexes):
                    if index < og_index:
                        new_index = index
                        break
                if new_index == None:
                    new_index = valid_indexes[-1]

            if new_index == None:
                new_index = valid_indexes[-1]

            obj_data.index = new_index


    def cyclic_next_mod_index(self):
        '''Next mod index but cycling back around (Only attempts to go forward)'''

        for obj_data in self.obj_datas:
            if not self.__validate_index(obj_data): continue
            og_index = obj_data.index
            # Try to set next available mod
            set_to_first = True
            for index, mod_data in enumerate(obj_data.mod_datas):
                if index > og_index:
                    if obj_data.mod_datas[index].logically_deleted == False:
                        obj_data.index = index
                        set_to_first = False
                        break
            # Wasnt set : so use first available
            if set_to_first:
                for index, mod_data in enumerate(obj_data.mod_datas):
                    if obj_data.mod_datas[index].logically_deleted == False:
                        obj_data.index = index
                        break


    def set_active_obj_mod_index(self, mod_name=""):
        '''Set the index for the active object Mod Data by mod name -> Returns set status'''

        obj_data = self.__active_object_data()
        if not obj_data: return False

        for index, mod_data in enumerate(obj_data.mod_datas):
            mod = mod_data.mod
            if not mod: continue
            if mod.name == mod_name:
                obj_data.index = index
                return True

        return False

    # --- SORTING --- #

    def sort_mods(self, sort_types=modifier.sort_types):
        '''Sort modifiers of specified types'''

        for obj_data in self.obj_datas:
            obj = obj_data.obj

            if type(obj.data) != bpy.types.Mesh: continue

            # Orignal active mod name
            active_mod_name = None
            if self.__validate_index(obj_data):
                active_mod_name = obj_data.active_mod().name

            # Save name
            for mod_data in obj_data.mod_datas:
                if mod_data.mod:
                    mod_data.name = mod_data.mod.name
                    mod_data.mod = None

            # Sort
            modifier.sort(obj, types=sort_types, last=True)

            # Restore mod refs
            for mod_data in obj_data.mod_datas:
                if mod_data.name in obj.modifiers:
                    mod_data.mod = obj.modifiers[mod_data.name]
                else:
                    mod_data.remove = True

            # Ensure
            valid_mod_datas = [md for md in obj_data.mod_datas if not md.remove]
            obj_data.mod_datas = valid_mod_datas

            # Restore index
            for index, mod_data in enumerate(obj_data.mod_datas):
                if mod_data.mod:
                    if mod_data.mod.name == active_mod_name:
                        obj_data.index = index
                        break

    # --- MISC --- #

    def all_objs(self):
        '''All stored objects in Obj Datas list'''

        return [obj_data.obj for obj_data in self.obj_datas if obj_data.obj]


    def all_created_mods(self, with_objs=False):
        '''Every newly created modifier / does not take in to account loggically deleted mods'''

        if with_objs:
            data = {}
            for obj_data in self.obj_datas:
                for mod_data in obj_data.mod_datas:
                    if mod_data.was_created:
                        if obj_data.obj not in data:
                            data[obj_data.obj] = []
                        data[obj_data.obj].append(mod_data.mod)
            return data

        mods = []
        for obj_data in self.obj_datas:
            for mod_data in obj_data.mod_datas:
                if mod_data.was_created:
                    mods.append(mod_data.mod)
        return mods

    # --- EXITS --- #

    def cancel_exit(self):
        for obj_data in self.obj_datas:

            for mod_data in obj_data.mod_datas:
                mod_object = modifier_container(self.type_map, obj_data.obj)
                # Remove created mods
                if mod_data.was_created:
                    mod_object.remove(mod_data.mod)
                    mod_data.mod = None
                    continue
                # Remove logically deleted mods
                if mod_data.logically_deleted:
                    mod_object.remove(mod_data.mod)
                    continue
                # Revert original mods
                mod_data.revert()


    def confirm_exit(self):
        for obj_data in self.obj_datas:
            mod_object = modifier_container(self.type_map, obj_data.obj)
            for mod_data in obj_data.mod_datas:
                # Remove logically deleted mods
                if mod_data.logically_deleted:
                    if mod_data.mod:
                        mod_object.remove(mod_data.mod)
                        continue

    # --- PRIVATE --- #

    def __set_next_available_index(self, obj_data):
        '''Try to set the next index to next forward else start going backwards'''

        # Try next index
        for index, mod_data in enumerate(obj_data.mod_datas):
            if index > obj_data.index:
                if mod_data.logically_deleted == False:
                    obj_data.index = index
                    return
            else: break

        # Try previous index
        count = obj_data.index - 1

        if count < 0:
            obj_data.index = 0
            return

        while count:
            if obj_data.mod_datas[count].logically_deleted == False:
                obj_data.index = count
                return
            count -= 1
            if count < 0: break

        # Fallback
        obj_data.index = 0


    def __validate_index(self, obj_data):
        '''Attempt to ensure the Obj Data mod index -> return True if okay for use'''

        # Incorrect indexing values
        if obj_data.index > len(obj_data.mod_datas) - 1:
            obj_data.index = len(obj_data.mod_datas) - 1
        if obj_data.index < 0:
            obj_data.index = 0

        # No mod datas
        if len(obj_data.mod_datas) == 0: return False

        # Current mod is not in use : go through list and set last active
        if obj_data.mod_datas[obj_data.index].logically_deleted:
            valid = False
            for index, mod_data in enumerate(obj_data.mod_datas):
                if not mod_data.logically_deleted:
                    obj_data.index = index
                    valid = True
            if not valid: return False

        return True


    def __active_object_data(self):
        '''The active object's Obj Data'''

        if self.active_obj:
            for obj_data in self.obj_datas:
                if obj_data.obj == self.active_obj:
                    return obj_data
        return None

# --- Utils --- #

def valid_object_type(type_map, obj):
    '''Ensure a key : val mapping is present'''

    if type(obj) != bpy.types.Object: return False
    if not hasattr(obj, 'data'): return False

    if type(obj.data) in type_map: return True
    return False


def modifier_container(type_map, obj):
    '''The blender modifier struct (object.modifiers)'''

    if not valid_object_type(type_map, obj): return None

    for bpy_type in type_map:
        if type(obj.data) == bpy_type:
            if bpy_type == bpy.types.GreasePencil:
                return obj.grease_pencil_modifiers
            if bpy_type == bpy.types.Mesh:
                return obj.modifiers
            if bpy_type == bpy.types.Curve:
                return obj.modifiers
    return None


def mod_type_from_map(type_map, obj):
    '''Map the object type to the proper modifier type'''

    if not valid_object_type(type_map, obj): return None
    return type_map[type(obj.data)]


def get_obj_dims(context, obj=None):
    '''Get the object dimensions without any array mods.'''

    original_states = {}

    for mod in obj.modifiers:
        if mod.type == 'ARRAY':
            original_states[mod] = mod.show_viewport
            mod.show_viewport = False

    context.view_layer.update()

    x_scale = abs(obj.scale[0]) if abs(obj.scale[0]) > 0 else 1
    y_scale = abs(obj.scale[1]) if abs(obj.scale[1]) > 0 else 1
    z_scale = abs(obj.scale[2]) if abs(obj.scale[2]) > 0 else 1

    dims = (
        obj.dimensions[0] / x_scale,
        obj.dimensions[1] / y_scale,
        obj.dimensions[2] / z_scale)

    for key, val in original_states.items():
        key.show_viewport = val

    return dims


