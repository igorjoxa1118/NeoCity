import bpy, pathlib, sys


class NodeModifier():
    '''Base wrapper class for asset geometry nodes modifiers'''

    input_map = dict()
    modifier = None
    last_valid_group_name = ''
    default_name = ''
    id_name = ''
    _filepath = '' # used for cacheing string

    # Copy shared modifier interface
    @property
    def show_on_cage(self):
        return self.modifier.show_on_cage

    @show_on_cage.setter
    def show_oncage(self, val):
        self.modifier.show_on_cage = val

    @property
    def show_in_edit_mode(self):
        return self.modifier.show_in_edit_mode

    @show_in_edit_mode.setter
    def show_in_edit_mode(self, val):
        self.modifier.show_in_edit_mode = val

    @property
    def show_viewport(self):
        return self.modifier.show_viewport

    @show_viewport.setter
    def show_viewport(self, val):
        self.modifier.show_viewport = val

    @property
    def show_render(self):
        return self.modifier.show_render

    @show_render.setter
    def show_render(self, val):
        self.modifier.show_render = val

    @property
    def name(self):
        return self.modifier.name

    @name.setter
    def name(self, val):
        self.modifier.name = val

    # Shared implementation

    @classmethod
    def new(cls, modifier):
        '''Return new wrapper for modifer or None if modifier's node group is not valid'''

        if not cls.is_valid_modifier(modifier): return None

        return cls.__create(modifier)

    @classmethod
    def from_object (cls, object):
        '''Create new modifier on object and return wrapper'''

        modifier = object.modifiers.new(cls.default_name, 'NODES')
        modifier.node_group = cls.get_or_load_node_group()
        modifier.node_group.is_modifier = False # keep modifier dropdown clean
        modifier.node_group.asset_clear() # match ops behavior

        return cls.__create(modifier)

    @classmethod
    def get_filepath(cls):
        '''Return chached filepath to the blend file'''

        if not cls._filepath:
            cls._filepath = cls.calc_asset_path()

        return cls._filepath

    @classmethod
    def __create (cls, modifier):
        '''Crate new wrapper from modifier without checking modifier validity and create input map for the types'''

        if not cls.input_map:
            cls.input_map = {input.name : input.identifier for input in modifier.node_group.interface.items_tree if input.in_out=='INPUT'}

        new = cls()
        new.modifier = modifier

        return new

    @classmethod
    def is_valid_modifier (cls, modifier) -> bool:
        '''Check if modifier object can be wrapped'''

        if modifier.type != 'NODES': return False
        if not modifier.node_group: return False
        if not cls.is_asset_node_group(modifier.node_group): return False
        if not cls.is_valid_node_group(modifier.node_group): return False
        return True

    @classmethod
    def is_asset_node_group(cls, node_group) -> bool:
        '''Check if node group has appropriate asset id_name and filepath'''

        weak_ref = node_group.library_weak_reference
        if not weak_ref: return False
        if weak_ref.id_name != cls.id_name: return False
        if weak_ref.filepath != cls.get_filepath(): return False

        return True

    @classmethod
    def builtin_geometry_nodes_path(cls) -> pathlib.Path:
        '''Return OS-specific path to builtin geometry_nodes folder.'''
        ver = f'{bpy.app.version[0]}.{bpy.app.version[1]}'
        path = pathlib.Path(bpy.app.binary_path).parent # exec folder

        if sys.platform == 'darwin':
            path = path.parent / 'Resources'

        path = path / ver / 'datafiles' / 'assets' / 'geometry_nodes'

        return path

    # Mandatory overloads

    @classmethod
    def is_valid_node_group(cls, node_group) -> bool:
        '''Returns true if node group is compatible with wrapper e.g. I/O matches wrapper's expectation'''

        raise NotImplementedError

    @classmethod
    def get_or_load_node_group(cls):
        '''Get node group from data or load new copy if it's invalid'''

        raise NotImplementedError

    @classmethod
    def calc_asset_path(cls) -> str:
        '''Calculate absolute path to blend file the asset is stored in'''

        raise NotImplementedError

class SmoothByAngle(NodeModifier):
    default_name = 'Smooth by Angle'
    id_name = 'NTSmooth by Angle'

    # input wrappers

    @property
    def angle (self):
        return self.modifier[self.input_map['Angle']]

    @angle.setter
    def angle(self, value):
        self.modifier[self.input_map['Angle']] = float(value)
        self.modifier.node_group.interface_update(bpy.context)

    @property
    def ignore_sharpness (self):
        return self.modifier[self.input_map['Ignore Sharpness']]

    @ignore_sharpness.setter
    def ignore_sharpness(self, value):
        self.modifier[self.input_map['Ignore Sharpness']] = bool(value)
        self.modifier.node_group.interface_update(bpy.context)

    @classmethod
    def is_valid_node_group(cls, node_group) -> bool:
        if not {'Angle', 'Ignore Sharpness'}.issubset(node_group.interface.items_tree.keys()):
            return False

        return True

    @classmethod
    def calc_asset_path(cls):
        blend = 'smooth_by_angle.blend'
        return str(cls.builtin_geometry_nodes_path() / blend)

    @classmethod
    def get_or_load_node_group(cls):
        if not cls.last_valid_group_name:
            node_groups = list(filter(cls.is_asset_node_group, bpy.data.node_groups))

            if node_groups and cls.is_valid_node_group(node_groups[0]):
                return node_groups[0]

        try:
            node_group = bpy.data.node_groups[cls.last_valid_group_name]
            if cls.is_asset_node_group(node_group) and cls.is_valid_node_group(node_group):
                return node_group

        except KeyError:
            pass

        # if last loaded group isn't valid, load a new one
        path = cls.get_filepath()

        with bpy.data.libraries.load(path) as (data_from, data_to):
            data_to.node_groups.append(data_from.node_groups[0])

        node_group = data_to.node_groups[0]

        cls.last_valid_group_name = data_to.node_groups[0].name

        return data_to.node_groups[0]
