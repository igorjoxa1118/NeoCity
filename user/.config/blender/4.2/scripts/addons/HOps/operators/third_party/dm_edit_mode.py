import bpy, os, bmesh
from pathlib import Path
from bpy_extras.image_utils import load_image
from ... utility import addon
from ...ui_framework.master import Master
from ...utils.addons import addon_exists
from ... icons import icons_directory


class HOPS_OT_DM2_Window(bpy.types.Operator):

    """DM2 Window"""
    bl_idname = "hops.dm2_window"
    bl_label = "DM2 Window"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = """DECALmachine 2 Window
    
    Displays decal machine decal list for edit mode usage. 
    Supports DecalMachine2 only.

    Ctrl + click decal to add blank material + decal
        
    """


    def invoke(self, context, event):

        # Validate
        if context.active_object == None:
            return {'CANCELLED'}
        if context.active_object.type != 'MESH':
            return {'CANCELLED'}
        if context.mode != 'EDIT_MESH':
            return {'CANCELLED'}
        if addon_exists("DECALmachine") == False:
            return {'CANCELLED'}

        from DECALmachine.utils.registration import get_prefs
        from DECALmachine import bl_info

        # Validate Version
        if bl_info['version'][0] < 2:
            return {'CANCELLED'}

        decallibsCOL = get_prefs().decallibsCOL
        self.trimlibs = [lib for lib in decallibsCOL if lib.isvisible and lib.istrimsheet]
        self.dm_prefs = get_prefs()
        self.dm_assets_path = self.dm_prefs.assetspath
        self.collections = {}
        self.active_pack = ""
        self.build_collection = True
        self.exit = False
        self.window_name = f'DECALmachine {bl_info["version"][0]}.{bl_info["version"][1]}.{bl_info["version"][2]}'
        self.obj = context.active_object

        # Run modal
        self.master = Master(context=context, custom_preset="preset_kit_ops", show_fast_ui=False)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


    def modal(self, context, event):

        # UI Update
        self.master.receive_event(event=event)

        # Navigation
        if event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'} and event.ctrl != True:
            if not self.master.is_mouse_over_ui():
                return {'PASS_THROUGH'}

        # Confirm
        elif event.type == 'LEFTMOUSE':
            if not self.master.is_mouse_over_ui():
                self.master.run_fade()
                self.remove_images()
                return {'FINISHED'}

        # Cancel
        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            if not self.master.is_mouse_over_ui():
                self.master.run_fade()
                self.remove_images()
                return {'CANCELLED'}

        self.draw_window(context, event)

        # Decal was loaded now exit
        if self.exit == True:
            if event.value == 'RELEASE':
                self.master.run_fade()
                self.remove_images()
                context.area.tag_redraw()
                bpy.ops.machin3.trim_unwrap('INVOKE_DEFAULT', library_name=self.library_name, trim_name=self.decal_name, rotate=0)
                return {'FINISHED'}

        context.area.tag_redraw()
        return {'RUNNING_MODAL'}


    def draw_window(self, context, event):

        self.master.setup()
        prefs = addon.preference()
        main_window = {
            "folders" : [],
            "files"   : [],
            "images"  : []}

        # Build collections data
        if self.build_collection:
            self.build_collection = False

            for col in self.trimlibs:

                paths = self.dm_get_image_data(self.dm_assets_path, col.name)

                if paths != None:
                    self.collections[col.name] = paths
                    for item in reversed(self.collections[col.name]):
                        main_window["files"].append( [item[1]] )

        # Add collection
        for col_name, paths in self.collections.items():

            # Set initial pack
            if self.active_pack == "":
                self.active_pack = col_name

            # Highlight the active pack
            highlight = False
            if col_name == self.active_pack:
                highlight = True

            main_window["folders"].append([col_name, self.dm_set_active_pack, (col_name,), highlight])

            if col_name == self.active_pack:
                for items in reversed(paths):
                    image = items[1]
                    if image != None:

                        path = Path(image.filepath)
                        decal_dir = path.parts[-2]

                        if event.ctrl == True:
                            main_window["images"].append([image, self.dm_call_decal_insert, (col_name, decal_dir, True)])
                        else:
                            main_window["images"].append([image, self.dm_call_decal_insert, (col_name, decal_dir)])
                        main_window["files"].append( [decal_dir] )

            main_window["folders"].sort()
            main_window["folders"].reverse()

        self.master.receive_main(win_dict=main_window, window_name=self.window_name)
        self.master.finished()

    ##################################
    #   DECAL MACHINE
    ##################################

    def dm_get_image_data(self, assets_path="", col_name=""):

        trim_folder = os.path.join(assets_path, "Trims")
        directory = os.path.join(trim_folder, col_name)
        paths = []
        
        if os.path.exists(directory) == False:
            return None

        with os.scandir(directory) as it:
            for entry in it:
                if not entry.name.startswith('.'):

                    image_folder =  os.path.join(directory, entry.name)
                    image = self.dm_get_image(image_folder, image_name="decal")
                    if image == None:
                        continue

                    image_directory = os.path.join(directory, entry.name, "decal")
                    paths.append((image_directory, image))

        return paths


    def dm_get_image(self, image_folder, image_name):

        image = load_image_file(filename=image_name, directory=image_folder)

        if image != None:

            if bpy.app.version < (2, 83, 0):
                image.colorspace_settings.name = 'Linear'
            else:
                image.colorspace_settings.name = 'sRGB'

        if image == None:
            return None

        return image


    def dm_set_active_pack(self, pack):

        if pack in self.collections:
            self.active_pack = pack


    def dm_call_decal_insert(self, library_name, decal_name, with_mats=False):

        if with_mats == True:
            self.add_blank_materials()

        self.library_name = library_name
        self.decal_name = decal_name
        self.exit = True

    ##################################
    #   UTILS
    ##################################

    def add_blank_materials(self):
        '''Add blank materials to object so that DM trim sheets looks more controlled.'''

        mesh = self.obj.data
        bm = bmesh.from_edit_mesh(mesh)
        bm.faces.ensure_lookup_table()

        sel_faces = [f for f in bm.faces if f.select == True]


        # Add material to entire obect
        bpy.ops.mesh.select_all(action='DESELECT')

        if len(self.obj.material_slots) > 0:
            for face in bm.faces:
                slot = self.obj.material_slots[face.material_index]
                mat = slot.material
                if mat == None:
                    face.select = True
        else:
            bpy.ops.mesh.select_all(action='SELECT')

        bpy.ops.material.hops_new('INVOKE_DEFAULT')
        bpy.ops.mesh.select_all(action='DESELECT')

        # Add material to selected faces
        for f in sel_faces:
            f.select = True
        bpy.ops.material.hops_new('INVOKE_DEFAULT')

        bm.free()
        bmesh.update_edit_mesh(mesh)

        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
        bpy.ops.object.mode_set(mode='EDIT', toggle=False)


    def remove_images(self):

        # Unload images : DM
        if self.collections != {}:
            for key, val in self.collections.items():
                for items in val:
                    image = items[1]
                    if image != None:
                        try:
                            bpy.data.images.remove(image)
                        except:
                            pass


def load_image_file(filename="", directory=""):
    '''Return the loaded image.'''

    return load_image(filename + ".png", dirname=directory)
