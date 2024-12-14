import bpy, os, random, time
from pathlib import Path
from mathutils import Vector
from bpy_extras.image_utils import load_image
from enum import Enum

from ... utility import addon

from ... ui_framework.master import Master
from ... ui_framework import form_ui as form

from ... utility import method_handler
from ... utility.base_modal_controls import Base_Modal_Controls
from ... utils.toggle_view3d_panels import collapse_3D_view_panels
from ... utils.modal_frame_drawing import draw_modal_frame
from ... utils.cursor_warp import mouse_warp

from . material_scroll import random_principled


class Tweaks(Enum):
    SCROLL = 0
    MOVE = 1
    SCALE = 2
    ROTATE = 3


OBJ_TYPES = {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT'}
IMG_TYPES = ['PNG', 'JPG', 'BMP', 'TIFF', 'PNG-JPG', 'ALL']
BLEND_MODES = ['MIX', 'MULTIPLY', 'SCREEN', 'DIVIDE', 'LIGHTEN', 'ADD', 'SUBTRACT']
DESC = """Map Scroll V1
Scroll Texture Maps

Make sure a path is specified in prefs prior to use.

Press H for help
"""

class Data:
    def __init__(self):
        self.objs = []
        self.active_obj = None
        self.shared_material = None
        self.dirs = Dirs()
        self.imgs = Imgs()
        self.nodes = Nodes()


    def setup(self, op, context):

        # --- Objects --- #
        self.objs = []
        for obj in context.selected_objects:
            if obj and obj.type in OBJ_TYPES:
                # Ignore none principled
                mat = obj.active_material
                if mat != None:
                    tree = mat.node_tree
                    if get_node(tree, bl_idname='ShaderNodeBsdfPrincipled') == None:
                        continue
                self.objs.append(Object(obj))

        # Invalid setup
        if len(self.objs) < 1:
            bpy.ops.hops.display_notification(info="Invalid Objects / Materials : Use Principled")
            return False

        # Assign material if none
        for object in self.objs:
            if object.mat == None:
                if self.shared_material == None:
                    self.shared_material = random_principled()
                object.mat = self.shared_material
                object.use_mat_pop = True
                object.obj.active_material = self.shared_material
                # object.obj.data.materials.append(self.shared_material)
                object.obj.active_material_index = len(object.obj.data.materials) - 1

        # Set active object
        for object in self.objs:
            if context.active_object == object.obj:
                self.active_obj = object
                break
        if self.active_obj == None:
            self.active_obj = self.objs[0]

        # --- Image --- #
        mat = self.active_obj.mat
        img = self.nodes.find_img_texture(mat)
        if type(img) == bpy.types.Image:
            img.hops.maps_system = True
            img.colorspace_settings.name = 'Non-Color'
            self.imgs.cur_img = img
            self.imgs.cur_tex = os.path.split(img.filepath)[1]
        for image in bpy.data.images:
            image.hops.just_created = False

        # --- Nodes --- #
        self.nodes.setup(op)

        # --- Directory --- #
        if type(self.imgs.cur_img) == bpy.types.Image:
            img_path = self.imgs.cur_img.filepath
            if not os.path.exists(img_path):
                bpy.ops.hops.display_notification(info="Image file not found on device")
                return False
            self.dirs.current_dir = os.path.split(img_path)[0]

        return True


    def close(self, op, context, with_cancel=False):

        self.imgs.close(op, with_cancel)
        self.nodes.close(op, with_cancel)

        if not with_cancel: return

        # Remove created material
        for object in self.objs:
            if object.use_mat_pop:
                object.obj.data.materials.pop()

        if self.shared_material:
            if type(self.shared_material) == bpy.types.Material:
                bpy.data.materials.remove(self.shared_material)


class Object:
    def __init__(self, obj):
        self.obj = obj
        self.original = Original_OBJ(obj)
        self.mat = self.original.mat
        self.use_mat_pop = False


class Original_OBJ:
    def __init__(self, obj):
        self.index = obj.active_material_index
        self.mat = obj.active_material


class Dirs:
    def __init__(self):
        self.root_dir = self.prefs_folder()
        self.current_dir = self.root_dir
        self.filter = self.prefs_filter()

        # Scroll Data
        self.scroll_dirs = []
        for root, dirs, files in os.walk(self.root_dir):
            for f in files:
                self.scroll_dirs.append((f, root))
        self.filtered_dirs = []
        self.build_scroll_dirs()


    def build_scroll_dirs(self):
        self.filtered_dirs = [(f, r) for f, r in self.scroll_dirs if self.filter_file(Path(f))]


    def prefs_folder(self):
        folder = Path(addon.preference().property.maps_folder).resolve()
        if os.path.exists(folder): return folder

        try:
            folder.mkdir(parents=True, exist_ok=True)
            return folder
        except:
            print(f'Unable to create {folder}')
            return None


    def prefs_filter(self):
        prefs_map_type = addon.preference().property.map_scroll_ftype
        return prefs_map_type if prefs_map_type in IMG_TYPES else IMG_TYPES[0]


    def folders(self, adjacent=False):

        def folder_list(directory):
            return [f for f in os.listdir(directory) if os.path.isdir(os.path.join(directory, f))]

        if not adjacent:
            return folder_list(self.current_dir)

        # See if the current folder has any folders within it : if not : return adjacent folders
        if self.dir_contains_folders(self.current_dir):
            return folder_list(self.current_dir)
        else:
            directory = os.path.split(self.current_dir)[0]
            return folder_list(directory)


    def files(self, override_path=None):

        directory = override_path if override_path else self.current_dir
        files = []
        try:
            for f in os.listdir(directory):
                path = Path(os.path.join(directory, f))
                if not path.is_file: continue

                if self.filter_file(path):
                    files.append(f)
        except: pass

        return files


    def filter_file(self, path):

        suffix = path.suffix

        if self.filter == 'ALL': 
            if suffix in {'.png', '.jpg', '.jpeg', '.bmp', '.tiff'}:
                return True
        if self.filter == 'PNG-JPG':
            if suffix in {'.png', '.jpg', '.jpeg'}:
                return True
        elif self.filter == 'PNG':
            if suffix in {'.png'}:
                return True
        elif self.filter == 'JPG':
            if suffix in {'.jpg', '.jpeg'}:
                return True
        elif self.filter == 'BMP':
            if suffix in {'.bmp'}:
                return True
        elif self.filter == 'TIFF':
            if suffix in {'.tiff'}:
                return True

        return False


    def set_folder(self, op, folder_name=""):
        
        valid = False

        # Look in current directory
        folder = os.path.join(self.current_dir, folder_name)
        if os.path.isdir(folder):
            valid = True

        # Look in adjacent directory
        if not valid:
            folder = os.path.split(self.current_dir)[0]
            folder = os.path.join(folder, folder_name)
            if os.path.isdir(folder):
                valid = True

        # Try from root
        if not valid:
            self.current = self.root_dir
            folder = os.path.join(backup, folder_name)
            if os.path.isdir(folder):
                valid = True

        # Fall back to root
        if not valid:
            self.current_dir = self.root_dir

        self.current_dir = folder

        has_folders = False
        try:
            for directory in os.listdir(self.current_dir):
                if os.path.isdir(os.path.join(self.current_dir, directory)):
                    has_folders = True
                    break
        except: pass
        
        if has_folders:
            op.reload_folders()
            op.reload_files()
            op.form.build()
        else:
            op.reload_files()
            op.form.build()


    def go_back_dir(self, op):
        if self.dir_contains_folders(self.current_dir):
            path, split = os.path.split(self.current_dir)
            if os.path.isdir(path):

                root = Path(self.root_dir)
                child = Path(path)
                if root not in child.parents:
                    path = self.root_dir

                self.current_dir = path
                op.reload_folders()
                op.reload_files()
                op.form.build()
                return

        # Go back 2 directories if there was not one in current folder
        path, split = os.path.split(self.current_dir)
        path, split = os.path.split(path)
        self.current_dir = path
        op.reload_folders()
        op.reload_files()
        op.form.build()
        return


    def dir_contains_folders(self, directory):
        for path in os.listdir(directory):
            if os.path.isdir(os.path.join(directory, path)):
                return True
        return False


    def go_home(self, op):
        if os.path.isdir(self.root_dir):
            self.current_dir = self.root_dir
        
            op.reload_folders()
            op.reload_files()
            op.form.build()


    def highlight_hook(self, folder=""):
        if folder == os.path.split(self.current_dir)[1]:
            return True
        return False

    # --- Modal --- #

    def next_available(self, op, direction=0, use_random=False):

        def rebuild(op, img_file, root):
            self.current_dir = root
            op.reload_folders()
            folder_name = os.path.split(root)[1]
            self.set_folder(op, folder_name)
            op.data.imgs.load(op, img_file)

        # Get a new image file
        if op.data.imgs.cur_tex == "" or op.data.imgs.cur_img == None:
            index = 0
            if len(self.filtered_dirs) - 1 > 0:
                index = random.randint(0, len(self.filtered_dirs) - 1)
            elif len(self.filtered_dirs) - 1 < 0:
                bpy.ops.hops.display_notification(info="No Images : Change filter type (TAB)")
                return
            rebuild(op, self.filtered_dirs[index][0], self.filtered_dirs[index][1])
            return

        if use_random:
            index = 0
            if len(self.filtered_dirs) - 1 > 0:
                index = random.randint(0, len(self.filtered_dirs) - 1)
            elif len(self.filtered_dirs) - 1 < 0:
                bpy.ops.hops.display_notification(info="No Images : Change filter type (TAB)")
                return
            rebuild(op, self.filtered_dirs[index][0], self.filtered_dirs[index][1])
            return

        index = None
        img_file = op.data.imgs.cur_tex
        for i, items in enumerate(self.filtered_dirs):
            if items[0] == img_file and items[1] == self.current_dir:
                index = i
                break

        if index == None:
            rebuild(op, self.filtered_dirs[-1][0], self.filtered_dirs[-1][1])
            return

        if direction > 0:
            index += 1
            if index > len(self.filtered_dirs) - 1:
                index = 0

        elif direction < 0:
            index -= 1
            if index < 0:
                index = len(self.filtered_dirs) - 1

        rebuild(op, self.filtered_dirs[index][0], self.filtered_dirs[index][1])
  

class Imgs:
    def __init__(self):
        self.cur_img = None
        self.cur_tex = ""
        self.loaded = [] # [(File name , b3d image name)... ]
        self.cur_img_name = ""

    
    def load(self, op, texture):

        def set_image(op, img, texture):
            self.cur_img = img
            self.cur_tex = texture
            self.loaded.append((texture, img.name))
            self.cur_img_name = img.name
            op.data.nodes.set_new_texture(op)

        for file_name, b3d_img_name in self.loaded:
            if file_name == texture:
                if b3d_img_name in bpy.data.images:
                    set_image(op, bpy.data.images[b3d_img_name], texture)
                    return

        img = load_image(texture, dirname=op.data.dirs.current_dir)
        if type(img) == bpy.types.Image:

            img.hops.maps_system = True
            img.hops.just_created = True
            img.colorspace_settings.name = 'Non-Color'
            set_image(op, img, texture)


    def highlight_hook(self, texture=""):
        if texture == None: return False
        if self.cur_tex == "": return False
        if texture == self.cur_tex:
            return True
        return False


    def close(self, op, with_cancel=False):
        loaded = list(set(self.loaded))

        for file_name, b3d_img_name in loaded:
            if b3d_img_name in bpy.data.images:
                
                if b3d_img_name == self.cur_img_name:
                    if with_cancel == False:
                        continue
                    if bpy.data.images[b3d_img_name].hops.just_created == False:
                        continue

                img = bpy.data.images[b3d_img_name]
                bpy.data.images.remove(img, do_unlink=True)

        for image in bpy.data.images:
            image.hops.just_created = False


class Nodes:
    def __init__(self):
        self.original = Original_Nodes()
        self.node_groups = dict() # Key => Material, Val => [nodes]
        self.use_roughness = True
        self.use_metallic = False
        self.use_normal = False
        self.use_color = False

        self.viewer_set = False

        self.color_1 = (1,1,1,1)
        self.color_2 = (1,1,1,1)

        self.__scale = 1
        self.__location = 0
        self.__bright = 0
        self.__contrast = 0
        self.__bump_distance = 0
        self.__bump_strength = 0
        self.__roughness = .5
        self.__roughness_value = 0
        self.__metalness = .5
        self.__metalness_value = 0

        self.roughness_blend = BLEND_MODES[0]
        self.color_blend = BLEND_MODES[0]
        self.metalness_blend = BLEND_MODES[0]

    # --- Global --- #
    @property
    def scale(self):
        return round(self.__scale, 3)

    @scale.setter
    def scale(self, val):
        self.__scale = val
        self.set_params()

    @property
    def location(self):
        return round(self.__location, 3)

    @location.setter
    def location(self, val):
        self.__location = val
        self.set_params()

    @property
    def bright(self):
        return round(self.__bright, 3)

    @bright.setter
    def bright(self, val):
        self.__bright = val
        self.set_params()

    @property
    def contrast(self):
        return round(self.__contrast, 3)

    @contrast.setter
    def contrast(self, val):
        self.__contrast = val
        self.set_params()

    # --- Roughness --- #
    @property
    def roughness(self):
        return round(self.__roughness, 3)

    @roughness.setter
    def roughness(self, val):
        val = max(min(val, 1), 0)
        self.__roughness = val
        self.set_params()

    @property
    def roughness_value(self):
        return round(self.__roughness_value, 3)

    @roughness_value.setter
    def roughness_value(self, val):
        val = max(min(val, 1), 0)
        self.__roughness_value = val
        self.set_params()


    def set_roughness_channel(self, op, set_viewer=False):

        if op.form.db.increment and self.use_roughness:
            if self.viewer_set:
                self.viewer_set = False
                self.connect_principled_to_matout()
                bpy.ops.hops.display_notification(info="Viewer Off")
            else:
                self.viewer_set = True
                self.set_channel(
                    from_hops_param='roughness_mix', from_node_id='ShaderNodeMixRGB', from_node_socket='Color',
                    to_node_id='ShaderNodeEmission', to_node_socket='Color',
                    connect=True)
                self.connect_viewer_to_matout()
                bpy.ops.hops.display_notification(info="Viewing Roughness Channel")
            return

        if set_viewer:
            if not self.use_roughness:
                bpy.ops.hops.display_notification(info="Enable Channel to View")
                return

            if self.viewer_set:
                self.viewer_set = False
                self.connect_principled_to_matout()
                return

            self.viewer_set = True

            self.set_channel(
                from_hops_param='roughness_mix', from_node_id='ShaderNodeMixRGB', from_node_socket='Color',
                to_node_id='ShaderNodeEmission', to_node_socket='Color',
                connect=True)
            self.connect_viewer_to_matout()
            bpy.ops.hops.display_notification(info="Viewing Roughness Channel")
            return

        self.viewer_set = False
        self.use_roughness = not self.use_roughness
        self.set_channel(
            from_hops_param='roughness_mix', from_node_id='ShaderNodeMixRGB', from_node_socket='Color',
            to_node_id='ShaderNodeBsdfPrincipled', to_node_socket='Roughness',
            connect=self.use_roughness)
        self.connect_principled_to_matout()
        op.form.row_activation(label='ROUGHNESS', active=self.use_roughness)
        op.form.build()


    def roughness_channel_hook(self):
        return self.use_roughness

   
    def set_roughness_blend(self, opt=''):
        self.roughness_blend = opt
        self.set_params()


    def roughness_blend_hook(self):
        return self.roughness_blend

    # --- Color --- #
    def set_color_channel(self, op, set_viewer=False):

        if op.form.db.increment and self.use_color:
            if self.viewer_set:
                self.viewer_set = False
                self.connect_principled_to_matout()
                bpy.ops.hops.display_notification(info="Viewer Off")
            else:
                self.viewer_set = True
                self.set_channel(
                    from_hops_param='color_mix', from_node_id='ShaderNodeMixRGB', from_node_socket='Color',
                    to_node_id='ShaderNodeEmission', to_node_socket='Color',
                    connect=True)
                self.connect_viewer_to_matout()
                bpy.ops.hops.display_notification(info="Viewing Color Channel")
            return

        if set_viewer:
            if not self.use_color:
                bpy.ops.hops.display_notification(info="Enable Channel to View")
                return

            if self.viewer_set:
                self.viewer_set = False
                self.connect_principled_to_matout()
                return
                
            self.viewer_set = True

            self.set_channel(
                from_hops_param='color_mix', from_node_id='ShaderNodeMixRGB', from_node_socket='Color',
                to_node_id='ShaderNodeEmission', to_node_socket='Color',
                connect=True)
            self.connect_viewer_to_matout()
            bpy.ops.hops.display_notification(info="Viewing Color Channel")
            return

        self.viewer_set = False
        self.use_color = not self.use_color
        self.set_channel(
            from_hops_param='color_mix', from_node_id='ShaderNodeMixRGB', from_node_socket='Color',
            to_node_id='ShaderNodeBsdfPrincipled', to_node_socket='Base Color',
            connect=self.use_color)
        self.connect_principled_to_matout()
        op.form.row_activation(label='COLOR', active=self.use_color)
        op.form.build()


    def color_channel_hook(self):
        return self.use_color


    def set_color_blend(self, opt=''):
        self.color_blend = opt
        self.set_params()


    def color_blend_hook(self):
        return self.color_blend

    # --- Metal --- #
    @property
    def metalness(self):
        return round(self.__metalness, 3)

    @metalness.setter
    def metalness(self, val):
        val = max(min(val, 1), 0)
        self.__metalness = val
        self.set_params()

    @property
    def metalness_value(self):
        return round(self.__metalness_value, 3)

    @metalness_value.setter
    def metalness_value(self, val):
        val = max(min(val, 1), 0)
        self.__metalness_value = val
        self.set_params()


    def set_metallic_channel(self, op, set_viewer=False):

        if op.form.db.increment and self.use_metallic:
            if self.viewer_set:
                self.viewer_set = False
                self.connect_principled_to_matout()
                bpy.ops.hops.display_notification(info="Viewer Off")
            else:
                self.viewer_set = True
                self.set_channel(
                    from_hops_param='metal_mix', from_node_id='ShaderNodeMixRGB', from_node_socket='Color',
                    to_node_id='ShaderNodeEmission', to_node_socket='Color',
                    connect=True)
                self.connect_viewer_to_matout()
                bpy.ops.hops.display_notification(info="Viewing Metallic Channel")
            return

        if set_viewer:
            if not self.use_metallic:
                bpy.ops.hops.display_notification(info="Enable Channel to View")
                return

            if self.viewer_set:
                self.viewer_set = False
                self.connect_principled_to_matout()
                return

            self.viewer_set = True

            self.set_channel(
                from_hops_param='metal_mix', from_node_id='ShaderNodeMixRGB', from_node_socket='Color',
                to_node_id='ShaderNodeEmission', to_node_socket='Color',
                connect=True)
            self.connect_viewer_to_matout()
            bpy.ops.hops.display_notification(info="Viewing Metallic Channel")
            return

        self.viewer_set = False
        self.use_metallic = not self.use_metallic
        self.set_channel(
            from_hops_param='metal_mix', from_node_id='ShaderNodeMixRGB', from_node_socket='Color',
            to_node_id='ShaderNodeBsdfPrincipled', to_node_socket='Metallic',
            connect=self.use_metallic)
        self.connect_principled_to_matout()
        op.form.row_activation(label='METALNESS', active=self.use_metallic)
        op.form.build()


    def metallic_channel_hook(self):
        return self.use_metallic


    def set_metalness_blend(self, opt=''):
        self.metalness_blend = opt
        self.set_params()


    def metalness_blend_hook(self):
        return self.metalness_blend

    # --- Bump --- #
    @property
    def bump_distance(self):
        return round(self.__bump_distance, 3)

    @bump_distance.setter
    def bump_distance(self, val):
        self.__bump_distance = val
        self.set_params()

    @property
    def bump_strength(self):
        return abs(round(self.__bump_strength, 3))

    @bump_strength.setter
    def bump_strength(self, val):
        self.__bump_strength = abs(val)
        self.set_params()


    def set_normal_channel(self, op, set_viewer=False):

        if op.form.db.increment and self.use_normal:
            if self.viewer_set:
                self.viewer_set = False
                self.connect_principled_to_matout()
                bpy.ops.hops.display_notification(info="Viewer Off")
            else:
                self.viewer_set = True
                self.set_channel(
                    from_node_id='ShaderNodeBump', from_node_socket='Normal',
                    to_node_id='ShaderNodeEmission', to_node_socket='Color',
                    connect=True)
                self.connect_viewer_to_matout()
                bpy.ops.hops.display_notification(info="Viewing Normal Channel")
            return

        if set_viewer:
            if not self.use_normal:
                bpy.ops.hops.display_notification(info="Enable Channel to View")
                return

            if self.viewer_set:
                self.viewer_set = False
                self.connect_principled_to_matout()
                return

            self.viewer_set = True

            self.set_channel(
                from_node_id='ShaderNodeBump', from_node_socket='Normal',
                to_node_id='ShaderNodeEmission', to_node_socket='Color',
                connect=True)
            self.connect_viewer_to_matout()
            bpy.ops.hops.display_notification(info="Viewing Normal Channel")
            return

        self.viewer_set = False
        self.use_normal = not self.use_normal
        self.set_channel(
            from_node_id='ShaderNodeBump', from_node_socket='Normal',
            to_node_id='ShaderNodeBsdfPrincipled', to_node_socket='Normal',
            connect=self.use_normal)
        self.connect_principled_to_matout()
        op.form.row_activation(label='BUMP', active=self.use_normal)
        op.form.build()


    def normal_channel_hook(self):
        return self.use_normal

    # --- Utils --- #

    def setup(self, op):

        self.original.setup(op)
        self.assign_node_graph(op)

        mat = op.data.active_obj.mat
        tree = mat.node_tree

        shader_node = get_node(tree, bl_idname='ShaderNodeBsdfPrincipled', hops_param='maps_system')

        # --- Contrast --- #
        contrast_node = get_node(tree, bl_idname='ShaderNodeBrightContrast', hops_param='maps_system')
        self.__bright = contrast_node.inputs[1].default_value
        self.__contrast = contrast_node.inputs[2].default_value

        # --- Roughness --- #
        roughness_node = get_node(tree, bl_idname='ShaderNodeMixRGB', hops_param='roughness_mix')
        self.__roughness_value = roughness_node.inputs[2].default_value[0]
        self.__roughness = roughness_node.inputs[0].default_value
        
        if roughness_node.blend_type in BLEND_MODES:
            self.roughness_blend = roughness_node.blend_type

        # --- Metallic --- #
        metal_node = get_node(tree, bl_idname='ShaderNodeMixRGB', hops_param='metal_mix')
        for link in metal_node.outputs[0].links:
            if link.to_node == shader_node:
                if link.to_socket.name == 'Metallic':
                    self.use_metallic = True
                    break
        metal_val = shader_node.inputs[4].default_value
        metal_node.inputs[2].default_value = (metal_val, metal_val, metal_val, 1)
        self.__metalness_value = metal_val
        self.__metalness = metal_node.inputs[0].default_value

        if metal_node.blend_type in BLEND_MODES:
            self.metalness_blend = metal_node.blend_type

        # --- Bump --- #
        bump_node = get_node(tree, bl_idname='ShaderNodeBump', hops_param='maps_system')
        for link in bump_node.outputs[0].links:
            if link.to_node == shader_node:
                if link.to_socket.name == 'Normal':
                    self.use_normal = True
                    break
        if bump_node.hops.just_created:
            self.__bump_strength = .1
        else:
            self.__bump_strength = bump_node.inputs[0].default_value
        self.__bump_distance = min(bump_node.inputs[1].default_value, .1)
        
        if bump_node.invert: self.__bump_distance *= -1

        # --- Color --- #
        color_node = get_node(tree, bl_idname='ShaderNodeMixRGB', hops_param='color_mix')
        for link in color_node.outputs[0].links:
            if link.to_node == shader_node:
                if link.to_socket.name == 'Base Color':
                    self.use_color = True
                    break

        self.color_1 = color_node.inputs['Color1'].default_value[:]
        self.color_2 = color_node.inputs['Color2'].default_value[:]

        if color_node.blend_type in BLEND_MODES:
            self.color_blend = color_node.blend_type

        # --- Loc / Scale --- #
        mapping_node = get_node(tree, bl_idname='ShaderNodeMapping', hops_param='maps_system')
        self.__location = mapping_node.inputs[1].default_value[0]
        self.__scale = mapping_node.inputs[3].default_value[0]

        self.connect_principled_to_matout()
        self.set_params()


    def connect_principled_to_matout(self):
        self.set_channel(
            from_hops_param=None, from_node_id='ShaderNodeBsdfPrincipled', from_node_socket='BSDF',
            to_node_id='ShaderNodeOutputMaterial', to_node_socket='Surface', to_hops_param=None,
            connect=True)


    def connect_viewer_to_matout(self):
        self.set_channel(
            from_hops_param='viewer', from_node_id='ShaderNodeEmission', from_node_socket='Emission',
            to_node_id='ShaderNodeOutputMaterial', to_node_socket='Surface', to_hops_param=None,
            connect=True)


    def set_channel(self, from_hops_param='maps_system', from_node_id='', from_node_socket='', to_node_id='', to_node_socket='', to_hops_param='maps_system', connect=False):
        for mat_name, nodes in self.node_groups.items():
            if mat_name in bpy.data.materials:
                mat = bpy.data.materials[mat_name]
                tree = mat.node_tree

                from_node = None
                if from_hops_param == None:
                    from_node = get_node(tree, bl_idname=from_node_id)
                else:
                    from_node = get_node(tree, bl_idname=from_node_id, hops_param=from_hops_param)
                if not from_node: continue

                to_node = None
                if to_hops_param == None:
                    to_node = get_node(tree, bl_idname=to_node_id)
                else:
                    to_node = get_node(tree, bl_idname=to_node_id, hops_param=to_hops_param)
                if not to_node: continue

                # Remove and links first
                if from_node_socket in from_node.outputs:
                    if from_node.outputs[from_node_socket].is_linked:
                        for link in from_node.outputs[from_node_socket].links:
                            if link.to_node == to_node:
                                if link.to_socket.name == to_node_socket:
                                    tree.links.remove(link)
                                    break

                # Add new link
                if connect:
                    socket_connect(tree, from_node, from_node_socket, to_node, to_node_socket)
        self.set_params()


    def find_img_texture(self, mat):
        tree = mat.node_tree
        tex_img_node = get_node(tree, bl_idname='ShaderNodeTexImage', hops_param='maps_system')
        if not tex_img_node: return None
        return tex_img_node.image


    def materials(self, op):
        mats = []
        for object in op.data.objs:
            obj = object.obj
            mat = obj.active_material
            if mat not in mats:
                mats.append(mat)
        return mats


    def assign_node_graph(self, op):
        mats = self.materials(op)

        for mat in mats:
            if mat.use_nodes == False:
                mat.use_nodes = True
            tree = mat.node_tree
            shader_node = get_node(tree, 'ShaderNodeBsdfPrincipled')
            
            self.setup_nodes(op, mat, tree, shader_node)


    def setup_nodes(self, op, mat, tree, shader_node):
        x, y = shader_node.location
        x -= 300
        y -= 400
 
        # RUFF MIX -> SHADER
        rough_mix = get_node(tree, bl_idname='ShaderNodeMixRGB', hops_param='roughness_mix')
        rough_mix = rough_mix if rough_mix else create_node(tree, x, y, bl_idname='ShaderNodeMixRGB')
        rough_mix.hops.roughness_mix = True
        rough_mix.label = 'Roughness'
        rough_mix.location = (x - rough_mix.width, y)
        x, y = rough_mix.location
        x -= 20
        socket_connect(tree, rough_mix, 'Color', shader_node, 'Roughness')

        # CONTRAST -> RUFF MIX
        contrast_node = get_node(tree, bl_idname='ShaderNodeBrightContrast', hops_param='maps_system')
        contrast_node = contrast_node if contrast_node else create_node(tree, x, y, bl_idname='ShaderNodeBrightContrast')
        contrast_node.location = (x - contrast_node.width - 10, y)
        x, y = contrast_node.location
        socket_connect(tree, contrast_node, 'Color', rough_mix, 'Color1')

        # RAMP -> CONTRAST
        ramp_node = get_node(tree, bl_idname='ShaderNodeValToRGB', hops_param='maps_system')
        ramp_node = ramp_node if ramp_node else create_node(tree, x, y, bl_idname='ShaderNodeValToRGB')
        ramp_node.location = (x - ramp_node.width - 10, y)
        x, y = ramp_node.location
        socket_connect(tree, ramp_node, 'Color', contrast_node, 'Color')

        # TEX -> RAMP
        tex_img_node = get_node(tree, bl_idname='ShaderNodeTexImage', hops_param='maps_system')
        tex_img_node = tex_img_node if tex_img_node else create_node(tree, x, y, bl_idname='ShaderNodeTexImage')
        tex_img_node.location = (x - tex_img_node.width - 10, y)
        x, y = tex_img_node.location
        socket_connect(tree, tex_img_node, 'Color', ramp_node, 'Fac')

        # MAP -> TEX
        mapping_node = get_node(tree, bl_idname='ShaderNodeMapping', hops_param='maps_system')
        mapping_node = mapping_node if mapping_node else create_node(tree, x, y, bl_idname='ShaderNodeMapping')
        mapping_node.location = (x - mapping_node.width - 10, y)
        x, y = mapping_node.location
        socket_connect(tree, mapping_node, 'Vector', tex_img_node, 'Vector')

        # COORDS -> MAP
        tex_coord_node = get_node(tree, bl_idname='ShaderNodeTexCoord', hops_param='maps_system')
        tex_coord_node = tex_coord_node if tex_coord_node else create_node(tree, x, y, bl_idname='ShaderNodeTexCoord')
        tex_coord_node.location = (x - tex_coord_node.width - 10, y)
        socket_connect(tree, tex_coord_node, 'Object', mapping_node, 'Vector')

        # COLOR MIX
        color_mix_node = get_node(tree, bl_idname='ShaderNodeMixRGB', hops_param='color_mix')
        color_mix_node = color_mix_node if color_mix_node else create_node(tree, x, y, bl_idname='ShaderNodeMixRGB')
        color_mix_node.hops.color_mix = True
        color_mix_node.label = 'Color'
        color_mix_node.location = (rough_mix.location.x, y + 400)
        socket_connect(tree, contrast_node, 'Color', color_mix_node, 'Fac')

        # METAL MIX
        metal_mix_node = get_node(tree, bl_idname='ShaderNodeMixRGB', hops_param='metal_mix')
        metal_mix_node = metal_mix_node if metal_mix_node else create_node(tree, x, y, bl_idname='ShaderNodeMixRGB')
        metal_mix_node.hops.metal_mix = True
        metal_mix_node.label = 'Metal'
        metal_mix_node.location = (rough_mix.location.x, y + 200)
        socket_connect(tree, contrast_node, 'Color', metal_mix_node, 'Color1')

        # BUMP
        bump_node = get_node(tree, bl_idname='ShaderNodeBump', hops_param='maps_system')
        bump_node = bump_node if bump_node else create_node(tree, x, y, bl_idname='ShaderNodeBump')
        bump_node.location = (rough_mix.location.x, contrast_node.location.y - 200)
        socket_connect(tree, contrast_node, 'Color', bump_node, 'Height')

        # VIEWER
        view_node = get_node(tree, bl_idname='ShaderNodeEmission', hops_param='maps_system')
        view_node = view_node if view_node else create_node(tree, 0, 0, bl_idname='ShaderNodeEmission')
        view_node.hops.viewer = True
        view_node.location = (color_mix_node.location.x, color_mix_node.location.y + 200)

        # Text node props
        tex_img_node.projection = 'BOX'
        tex_img_node.projection_blend = .1
        tex_img_node.image = op.data.imgs.cur_img
        tex_img_node.interpolation = 'Cubic'

        # Hops Reference
        hops_nodes = [shader_node, rough_mix, contrast_node, ramp_node, tex_img_node, mapping_node, tex_coord_node, color_mix_node, metal_mix_node, bump_node, view_node]
        for node in hops_nodes:
            node.hops.maps_system = True
        self.node_groups[mat.name] = hops_nodes

        # Make sure there is a Material Output
        out_node = get_node(tree, bl_idname='ShaderNodeOutputMaterial')
        out_node = out_node if out_node else create_node(tree, 0, 0, bl_idname='ShaderNodeOutputMaterial')


    def set_new_texture(self, op):
        img = op.data.imgs.cur_img
        if type(img) != bpy.types.Image: return

        for node in self.stored_nodes():
            if node.bl_idname == 'ShaderNodeTexImage':
                node.image = img


    def set_params(self):
        for node in self.stored_nodes():
            if node.bl_idname == 'ShaderNodeBrightContrast':
                node.inputs[1].default_value = self.__bright
                node.inputs[2].default_value = self.__contrast
            
            elif node.bl_idname == 'ShaderNodeMapping':
                node.inputs[3].default_value = (self.__scale, self.__scale, self.__scale)
                node.inputs[1].default_value = (self.__location, self.__location, 0)
            
            elif node.bl_idname == 'ShaderNodeBump':
                if self.__bump_distance < 0: node.invert = True
                else: node.invert = False
                node.inputs[0].default_value = abs(self.__bump_strength)
                node.inputs[1].default_value = abs(self.__bump_distance)

            elif node.bl_idname == 'ShaderNodeMixRGB':
                if node.hops.roughness_mix == True:
                    node.inputs[0].default_value = self.__roughness
                    node.inputs[2].default_value = (self.__roughness_value, self.__roughness_value, self.__roughness_value, 1)
                    node.blend_type = self.roughness_blend

                elif node.hops.color_mix == True:
                    node.inputs[1].default_value = self.color_1
                    node.inputs[2].default_value = self.color_2
                    node.blend_type = self.color_blend

                elif node.hops.metal_mix == True:
                    node.inputs[0].default_value = self.__metalness
                    node.inputs[2].default_value = (self.__metalness_value, self.__metalness_value, self.__metalness_value, 1)
                    node.blend_type = self.metalness_blend


    def stored_nodes(self):
        all_nodes = []
        for mat_name, nodes in self.node_groups.items():
            all_nodes.extend(nodes)
        return all_nodes


    def close(self, op, with_cancel=False):
        if with_cancel:
            self.original.close(op)

    # --- Modal --- #

    def adjust_move(self, offset=0):
        for node in self.stored_nodes():
            if node.bl_idname == 'ShaderNodeMapping':
                current = node.inputs[1].default_value
                node.inputs[1].default_value = (current[0] + offset, current[1] + offset, current[2])
                self.__location = current[0] + offset


    def adjust_scale(self, offset=0):
        for node in self.stored_nodes():
            if node.bl_idname == 'ShaderNodeMapping':
                current = node.inputs[3].default_value
                self.__scale = current[0] + offset
                node.inputs[3].default_value = (self.__scale, self.__scale, self.__scale)


    def adjust_rotation(self, offset=0):
        for node in self.stored_nodes():
            if node.bl_idname == 'ShaderNodeMapping':
                current = node.inputs[2].default_value
                node.inputs[2].default_value = (current[0] + offset, current[1] + offset, current[2])


class Original_Nodes:
    def __init__(self):
        self.revert_nodes = []


    def setup(self, op):
        data = op.data
        mats = data.nodes.materials(op)

        for mat in mats:
            tree = mat.node_tree
            captured_principled = False
            for node in tree.nodes:
                node.hops.just_created = False

                if node.bl_idname == 'ShaderNodeBsdfPrincipled' and captured_principled == False:
                    captured_principled = True
                    self.set_revert_data(mat, node)

                if node.hops.maps_system == False: continue
                self.set_revert_data(mat, node)


    def set_revert_data(self, mat, node):
        node_data = Revert_Node_Data()
        node_data.material = mat
        node_data.node = node

        # Input
        for index, puts in enumerate(node.inputs):
            # Values
            if type(puts.default_value) == float:
                node_data.input_values[index] = puts.default_value
            else:
                node_data.input_values[index] = puts.default_value[:]
            # Links
            for link in puts.links:
                if not link.from_socket or not link.to_socket: continue
                node_data.input_links.append((link.from_socket, link.to_socket))

        # Image
        if node.bl_idname == 'ShaderNodeTexImage':
            if node.image != None:
                node_data.image_name = node.image.name

        self.revert_nodes.append(node_data)


    def close(self, op):
        mats = op.data.nodes.materials(op)

        # Revert
        for revert in self.revert_nodes:
            node = revert.node
            mat = revert.material
            tree = mat.node_tree

            # Values
            for index, value in revert.input_values.items():
                node.inputs[index].default_value = value
                
            # Input Links
            for puts in node.inputs:
                for link in puts.links:
                    tree.links.remove(link)

            for link in revert.input_links:
                if len(link) != 2: continue
                tree.links.new(link[0], link[1])

            # Image
            if node.bl_idname == 'ShaderNodeTexImage':
                if type(revert.image_name) == str:
                    if revert.image_name in bpy.data.images:
                        node.image = bpy.data.images[revert.image_name]

        # Delete
        for mat in mats:
            tree = mat.node_tree
            for node in tree.nodes:
                if node.hops.just_created:
                    tree.nodes.remove(node)


class Revert_Node_Data:
    def __init__(self):
        self.material = None
        self.node = None
        self.input_values = dict()
        self.input_links = []
        self.image_name = None


class HOPS_OT_Map_Scroll(bpy.types.Operator):
    bl_idname = "hops.map_scroll"
    bl_label = "Map Scroll"
    bl_description = DESC
    bl_options = {"REGISTER", "UNDO", "BLOCKING"}

    @classmethod
    def poll(cls, context):

        if not addon.preference().property.maps_folder: return False

        folder = Path(addon.preference().property.maps_folder).resolve()
        if not folder.exists():
            return False

        types = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff'}
        valid = False
        for root, dirs, files in os.walk(folder):
            if valid: break
            if len(files) > 0:
                for f in files:
                    path = Path(os.path.join(root, f))
                    suffix = path.suffix
                    if suffix in types:
                        valid = True
                        break

        if not valid: return False

        return any(obj.type in OBJ_TYPES for obj in context.selected_objects if obj)


    def invoke(self, context, event):

        # Mode
        self.exit_to_edit = False
        if context.mode != 'OBJECT':
            self.exit_to_edit = True
            objs = context.objects_in_mode
            active = context.active_object
            bpy.ops.object.mode_set(mode='OBJECT')
            for obj in objs:
                obj.select_set(True)
            active.select_set(True)

        # Data
        self.data = Data()

        # Dirs
        if len(self.data.dirs.scroll_dirs) < 1:
            bpy.ops.hops.display_notification(info="No files found")
            return {'CANCELLED'} 

        # Setup
        valid = self.data.setup(self, context)
        if valid == False:
            return {'CANCELLED'} 

        # Controls
        self.tweak = Tweaks.SCROLL

        # Form
        self.form_exit = False
        self.form = None
        self.setup_form(context, event)

        # VP
        self.og_vp = context.space_data.shading.type
        context.space_data.shading.type = 'MATERIAL'

        # Base Systems
        self.master = Master(context=context)
        self.master.only_use_fast_ui = True
        self.base_controls = Base_Modal_Controls(context, event)
        self.original_tool_shelf, self.original_n_panel = collapse_3D_view_panels()
        self.draw_handle_2D = bpy.types.SpaceView3D.draw_handler_add(self.safe_draw_2D, (context,), 'WINDOW', 'POST_PIXEL')

        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}


    def modal(self, context, event):

        # --- Base Systems --- #
        self.master.receive_event(event=event)
        self.base_controls.update(context, event)
        self.form.update(context, event)
        form_active = self.form.active()

        # --- Base Controls --- #
        if not self.form.is_dot_open():
            mouse_warp(context, event)

        if self.base_controls.pass_through:
            if not form_active:
                return {'PASS_THROUGH'}

        if not form_active:
            if self.form.is_dot_open():
                if event.type in {'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
                    return {'PASS_THROUGH'}

        if self.base_controls.cancel:
            if not form_active:
                return self.cancel_exit(context)

        elif self.base_controls.confirm:
            if not form_active:
                return self.confirm_exit(context)

        if self.form_exit:
            return self.confirm_exit(context)

        if event.type == 'TAB' and event.value == 'PRESS':
            if self.form.is_dot_open():
                self.form.close_dot()
            else:
                self.form.open_dot()

        # --- Actions --- #
        if not form_active:
            self.actions(context, event)

        self.interface(context=context)
        context.area.tag_redraw()
        return {"RUNNING_MODAL"}


    def interface(self, context):
        self.master.setup()

        # --- Fast UI --- #
        if self.master.should_build_fast_ui():

            # Main
            win_list = []
            win_list.append("Map-Scroll")
            
            img_name = self.data.imgs.cur_tex.split('.')[0]
            if img_name == "": win_list.append("No Image Loaded")
            else: win_list.append(img_name)
            
            if self.data.nodes.use_normal:
                win_list.append(f"Bump : {self.data.nodes.bump_distance}")

            # Help
            help_items = {"GLOBAL" : [], "STANDARD" : []}

            help_items["GLOBAL"] = [
                ("M", "Toggle mods list"),
                ("H", "Toggle help"),
                ("~", "Toggle UI Display Type"),
                ("O", "Toggle viewport rendering")]

            if not self.form.is_dot_open():
                help_items["STANDARD"] = [
                    ("G"                           , "Move"),
                    ("S"                           , "Scale"),
                    ("R"                           , "Rotate"),
                    ("E"                           , "Random Map"),
                    ("N"                           , f"Bump {'OFF' if self.data.nodes.use_normal else 'ON'}"),
                    ("Scroll / Move Shift + Ctrl"  , "Bump"),
                    ("Scroll / Move Alt"           , "Contrast"),
                    ("Scroll / Move Ctrl"          , "Scale"),
                    ("Scroll / Move Shift"         , "Brightness"),
                    ("Scroll"                      , "Maps"),
                    ("TAB"                         , "DOT UI")]

            else:
                help_items["STANDARD"] = [
                    ("TAB", "DOT UI")]

            self.master.receive_fast_ui(win_list=win_list, help_list=help_items, image="QGui")

        self.master.finished()

    # --- FORM --- #

    def setup_form(self, context, event):
        self.form = form.Form(context, event, dot_open=False)

        self.form.dot_calls(
            scroll_func=self.data.dirs.next_available,
            scroll_pos_args=(self, 0, True),
            scroll_neg_args=(self, 0, True),
            tips=["Scroll for random texture"])

        def spacer(height=10):
            row = self.form.row()
            row.add_element(form.Spacer(height=height))
            self.form.row_insert(row)

        def divide_bar(label='', active=False):
            row = self.form.row()
            row.add_element(form.Spacer(width=270, height=10, draw_bar=True))
            self.form.row_insert(row, label=label, active=active)

        # Header
        row = self.form.row()
        row.add_element(form.Label(text="Map Scroll", width=250))
        row.add_element(form.Button(text="X", width=20, tips=["Finalize and Exit"], callback=self.exit_button))
        self.form.row_insert(row)

        spacer()

        # Navigation / Maps
        row = self.form.row()
        row.add_element(form.Button(img="TriLeft", width=20, height=20, tips=["Go back directory"], callback=self.data.dirs.go_back_dir, pos_args=(self,), neg_args=(self,)))
        row.add_element(form.Spacer(width=5))
        row.add_element(form.Button(text="Home", width=50, height=20, callback=self.data.dirs.go_home, pos_args=(self,), neg_args=(self,), use_padding=False))

        row.add_element(form.Spacer(width=100))
        nodes = self.data.nodes

        row.add_element(form.Button(text="R", width=20, tips=["Toggle Roughness Channel", "Shift Click : Toggle Viewer Mode"], 
            callback=nodes.set_roughness_channel, pos_args=(self,), neg_args=(self, True), highlight_hook=nodes.roughness_channel_hook))
       
        row.add_element(form.Spacer(width=5))
     
        row.add_element(form.Button(text="M", width=20, tips=["Toggle Metallic Channel", "Shift Click : Toggle Viewer Mode"], 
            callback=nodes.set_metallic_channel, pos_args=(self,), neg_args=(self, True), highlight_hook=nodes.metallic_channel_hook))
       
        row.add_element(form.Spacer(width=5))
      
        row.add_element(form.Button(text="N", width=20, tips=["Toggle Normal Map Channel", "Shift Click : Toggle Viewer Mode"], 
            callback=nodes.set_normal_channel, pos_args=(self,), neg_args=(self, True), highlight_hook=nodes.normal_channel_hook))
        
        row.add_element(form.Spacer(width=5))
       
        row.add_element(form.Button(text="C", width=20, tips=["Toggle Color Channel", "Shift Click : Toggle Viewer Mode"], 
            callback=nodes.set_color_channel, pos_args=(self,), neg_args=(self, True), highlight_hook=nodes.color_channel_hook))
        
        self.form.row_insert(row)

        spacer()

        # Folder Box
        row = self.form.row()
        group = self.folder_group()
        self.folder_box = form.Scroll_Box(width=270, height=20 * addon.preference().property.map_scroll_folder_count, scroll_group=group, view_scroll_enabled=True)
        row.add_element(self.folder_box)
        self.form.row_insert(row)

        spacer()

        # Filter
        row = self.form.row()
        row.add_element(form.Spacer(height=25))
        row.add_element(form.Label(text="Filter", width=50))
        index = IMG_TYPES.index(self.data.dirs.filter)
        row.add_element(form.Dropdown(width=75, options=IMG_TYPES, callback=self.set_map_type, update_hook=self.get_map_type, index=index))
        self.form.row_insert(row)

        spacer()

        # File Box
        row = self.form.row()
        group = self.file_group()
        self.file_box = form.Scroll_Box(width=270, height=20 * addon.preference().property.map_scroll_file_count, scroll_group=group, view_scroll_enabled=True)
        row.add_element(self.file_box)
        self.form.row_insert(row)

        spacer()

        NODES = self.data.nodes

        # Global
        row = self.form.row()
        row.add_element(form.Label(text="Scale", width=60, height=20))
        row.add_element(form.Input(obj=NODES, attr="scale", width=60, increment=.025, font_size=12))
        row.add_element(form.Spacer(width=10))
        row.add_element(form.Label(text="Loc", width=60, height=20))
        row.add_element(form.Input(obj=NODES, attr="location", width=60, increment=.025, font_size=12))
        self.form.row_insert(row)

        divide_bar(active=True)

        row = self.form.row()
        row.add_element(form.Label(text="Contrast", width=60, height=20))
        row.add_element(form.Input(obj=NODES, attr="contrast", width=60, increment=.025, font_size=12))
        row.add_element(form.Spacer(width=10))
        row.add_element(form.Label(text="Bright", width=60, height=20))
        row.add_element(form.Input(obj=NODES, attr="bright", width=60, increment=.025, font_size=12))
        self.form.row_insert(row)

        # Roughness
        divide_bar(label='ROUGHNESS', active=NODES.use_roughness)

        row = self.form.row()
        row.add_element(form.Label(text="R Blend", width=60, height=20))
        row.add_element(form.Input(obj=NODES, attr="roughness", width=60, increment=.025, font_size=12))
        row.add_element(form.Spacer(width=5))
        row.add_element(form.Input(obj=NODES, attr="roughness_value", width=60, increment=.025, font_size=12, tips=["Roughness value"]))
        row.add_element(form.Spacer(width=5))
        row.add_element(form.Dropdown(width=80, options=BLEND_MODES, callback=NODES.set_roughness_blend, update_hook=NODES.roughness_blend_hook, index=BLEND_MODES.index(NODES.roughness_blend)))
        self.form.row_insert(row, label='ROUGHNESS', active=NODES.use_roughness)

        # Metal
        divide_bar(label='METALNESS', active=NODES.use_metallic)

        row = self.form.row()
        row.add_element(form.Label(text="M Blend", width=60, height=20))
        row.add_element(form.Input(obj=NODES, attr="metalness", width=60, increment=.025, font_size=12))
        row.add_element(form.Spacer(width=5))
        row.add_element(form.Input(obj=NODES, attr="metalness_value", width=60, increment=.025, font_size=12, tips=["Metalness value"]))
        row.add_element(form.Spacer(width=5))
        row.add_element(form.Dropdown(width=80, options=BLEND_MODES, callback=NODES.set_metalness_blend, update_hook=NODES.metalness_blend_hook, index=BLEND_MODES.index(NODES.metalness_blend)))
        self.form.row_insert(row, label='METALNESS', active=NODES.use_metallic)

        # Bump
        divide_bar(label='BUMP', active=NODES.use_normal)

        row = self.form.row()
        row.add_element(form.Label(text="Strength", width=60, height=20))
        row.add_element(form.Input(obj=NODES, attr="bump_strength", width=60, increment=.0125, font_size=12))
        row.add_element(form.Label(text="Distance", width=60, height=20))
        row.add_element(form.Input(obj=NODES, attr="bump_distance", width=60, increment=.0125, font_size=12))
        self.form.row_insert(row, label='BUMP', active=NODES.use_normal)

        # Color
        divide_bar(label='COLOR', active=NODES.use_color)

        row = self.form.row()
        row.add_element(form.Label(text="Mix 1", width=50, height=20))
        row.add_element(form.Color(obj=NODES, attr="color_1", width=40, height=8, pref_color=1, callback=NODES.set_params))
        row.add_element(form.Spacer(width=5))
        row.add_element(form.Label(text="Mix 2", width=50, height=20))
        row.add_element(form.Color(obj=NODES, attr="color_2", width=40, height=8, pref_color=2, callback=NODES.set_params))
        row.add_element(form.Spacer(width=5))
        row.add_element(form.Dropdown(width=80, options=BLEND_MODES, callback=NODES.set_color_blend, update_hook=NODES.color_blend_hook, index=0))
        self.form.row_insert(row, label='COLOR', active=NODES.use_color)

        self.form.build()


    def folder_group(self):
        folders = self.data.dirs.folders(adjacent=True)
        group = form.Scroll_Group()
        for folder in folders:
            row = group.row()

            text = form.shortened_text(folder, width=220, font_size=12)
            tip = [] if text == folder else [folder]

            row.add_element(form.Button(
                scroll_enabled=False, text=text, tips=tip,
                width=250, height=20, use_padding=False,
                callback=self.data.dirs.set_folder, pos_args=(self, folder),
                highlight_hook=self.data.dirs.highlight_hook, highlight_hook_args=(folder,)))
            group.row_insert(row)
        return group


    def file_group(self):
        files = self.data.dirs.files()
        group = form.Scroll_Group()
        for texture in files:
            row = group.row()

            text = form.shortened_text(texture, width=220, font_size=12)
            tip = [] if text == texture else [texture]

            row.add_element(form.Button(
                text=text, tips=tip, width=250, height=20, use_padding=False, scroll_enabled=False,
                callback=self.data.imgs.load, pos_args=(self, texture),
                highlight_hook=self.data.imgs.highlight_hook, highlight_hook_args=(texture,)))
            group.row_insert(row)
        return group


    def reload_folders(self):
        self.folder_box.scroll_group.clear(bpy.context)
        group = self.folder_group()
        self.folder_box.scroll_group = group


    def reload_files(self):
        self.file_box.scroll_group.clear(bpy.context)
        group = self.file_group()
        self.file_box.scroll_group = group


    def set_map_type(self, opt=''):
        self.data.dirs.filter = opt
        self.data.dirs.build_scroll_dirs()
        self.reload_files()
        self.form.build()


    def get_map_type(self):
        return self.data.dirs.filter


    def exit_button(self):
        self.form_exit = True

    # --- MODAL --- #

    def actions(self, context, event):

        # Random Map
        if event.type == 'E' and event.value == 'PRESS':
            self.data.dirs.next_available(self, use_random=True)
            return

        # Move
        elif event.type == 'G' and event.value == 'PRESS':
            if self.tweak == Tweaks.MOVE:
                self.tweak = Tweaks.SCROLL
            else:
                self.tweak = Tweaks.MOVE

        # Scale
        elif event.type == 'S' and event.value == 'PRESS':
            if self.tweak == Tweaks.SCALE:
                self.tweak = Tweaks.SCROLL
            else:
                self.tweak = Tweaks.SCALE

        # Rotation
        elif event.type == 'R' and event.value == 'PRESS':
            if self.tweak == Tweaks.ROTATE:
                self.tweak = Tweaks.SCROLL
            else:
                self.tweak = Tweaks.ROTATE

        # Bump Toggle
        elif event.type == 'N' and event.value == 'PRESS':
            self.data.nodes.set_normal_channel(self)

        # Update Tweaks
        if self.tweak == Tweaks.SCROLL:
            self.scrolls(context, event)
        elif self.tweak == Tweaks.MOVE:
            self.data.nodes.adjust_move(offset=self.base_controls.mouse)
        elif self.tweak == Tweaks.SCALE:
            self.data.nodes.adjust_scale(offset=self.base_controls.mouse)
        elif self.tweak == Tweaks.ROTATE:
            self.data.nodes.adjust_rotation(offset=self.base_controls.mouse)
 

    def scrolls(self, context, event):
        scroll = self.base_controls.scroll
        mouse = self.base_controls.mouse

        # Texture
        if scroll:
            if not event.shift and not event.ctrl and not event.alt:
                self.data.dirs.next_available(self, direction=scroll)

        if scroll == 0 and mouse == 0: return

        # Bright
        if event.shift and not event.ctrl and not event.alt:
            bright = self.data.nodes.bright
            if scroll > 0:
                bright += .05
            elif scroll < 0:
                bright -= .05
            elif mouse:
                bright += mouse
            self.data.nodes.bright = bright
        # Scale
        elif not event.shift and event.ctrl and not event.alt:
            scale = self.data.nodes.scale
            if scroll > 0:
                scale += .05
            elif scroll < 0:
                scale -= .05
            elif mouse:
                scale += mouse
            self.data.nodes.scale = scale
        # Contrast
        elif not event.shift and not event.ctrl and event.alt:
            contrast = self.data.nodes.contrast
            if scroll > 0:
                contrast += .05
            elif scroll < 0:
                contrast -= .05
            elif mouse:
                contrast += mouse
            self.data.nodes.contrast = contrast
        # Bump
        elif event.shift and event.ctrl and not event.alt:
            bump = self.data.nodes.bump_distance
            if scroll > 0:
                bump += .01
            elif scroll < 0:
                bump -= .01
            elif mouse:
                bump += mouse
            
            if not self.data.nodes.use_normal:
                self.data.nodes.set_normal_channel(self)

            self.data.nodes.bump_distance = bump

    # --- EXITS --- #

    def common_exit(self, context):
        self.form.shut_down(context)
        self.remove_shaders()
        collapse_3D_view_panels(self.original_tool_shelf, self.original_n_panel)
        self.master.run_fade()

        context.space_data.shading.type = self.og_vp

        self.data.nodes.connect_principled_to_matout()

        if self.exit_to_edit:
            bpy.ops.object.mode_set(mode='EDIT')


    def confirm_exit(self, context):
        self.data.close(self, context, with_cancel=False)
        self.common_exit(context)
        return {'FINISHED'}


    def cancel_exit(self, context):
        self.data.close(self, context, with_cancel=True)
        self.common_exit(context)
        return {'CANCELLED'}

    # --- SHADERS --- #

    def remove_shaders(self):
        if self.draw_handle_2D:
            self.draw_handle_2D = bpy.types.SpaceView3D.draw_handler_remove(self.draw_handle_2D, "WINDOW")


    def safe_draw_2D(self, context):
        method_handler(self.draw_shader_2D,
            arguments = (context,),
            identifier = 'Modal Shader 2D',
            exit_method = self.remove_shaders)


    def draw_shader_2D(self, context):
        self.form.draw()

        if not self.form.is_dot_open():
            draw_modal_frame(context)

# --- UTILS --- #

def remove_materials(obj):
    obj.data.materials.clear()


def assign_material_object(obj, mat):
    obj.data.materials.append(mat)
    index = len(obj.data.materials) - 1
    obj.active_material_index = index
    return index


def create_node(tree, x, y, bl_idname=''):
    node = tree.nodes.new(type=bl_idname)
    node.hops.just_created = True
    node.location = (x, y)
    return node


def socket_connect(tree, node_out=None, out_socket='', node_in=None, in_socket=''):
    # Validate
    if out_socket not in node_out.outputs: return
    if in_socket not in node_in.inputs: return
    # Link
    socket_out = node_out.outputs[out_socket]
    socket_in = node_in.inputs[in_socket]
    tree.links.new(socket_out, socket_in)


def get_node(tree, bl_idname='', hops_param='', index=-1):

    nodes = [n for n in tree.nodes if n.bl_idname == bl_idname]

    if hops_param != '':
        nodes = [n for n in nodes if getattr(n.hops, hops_param) == True]

    if not nodes or index > len(nodes) - 1:
        return None

    return nodes[index]


def create_principled_material():
    mat = bpy.data.materials.new('Material')
    mat.use_nodes = True
    tree = mat.node_tree
    tree.nodes.clear()

    principled = create_node(tree, x=0, y=0, bl_idname='ShaderNodeBsdfPrincipled')
    x = principled.width + 20
    output = create_node(tree, x=x, y=0, bl_idname='ShaderNodeOutputMaterial')
    socket_connect(tree, principled, 'BSDF', output, 'Surface')
    return mat


def create_principled():
    mat = bpy.data.materials.new('Maps Principled')
    mat.use_nodes = True
    return mat
