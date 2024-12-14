import bpy
from ... utility import addon
from ...ui_framework.operator_ui import Master
from ...utility.collections import turn_on_parent_collections, all_collections_in_view_layer


class Container:
    def __init__(self, obj):
        self.obj = obj
        self.matrix = obj.matrix_world.copy()
        self.mod_containers = [] # <-- Container Tree
        self.mod_obj_ref = ""
        self.mod_type = ""
        self.matrix_local = obj.matrix_local.copy()
        self.matrix_parent_inverse = obj.matrix_parent_inverse.copy()
        self.matrix_basis = obj.matrix_basis.copy()
        self.parent = bool(obj.parent)


class HOPS_OT_UniquifyObjects(bpy.types.Operator):
    bl_idname = 'hops.uniquify_objects'
    bl_label = 'Uniquify Objects'
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = '''Uniquify Objects\n\nMake objects on selected objects unique \n Recursive'''

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' and any(obj.type == 'MESH' for obj in context.selected_objects)


    def execute(self, context):
        self.objs = [o for o in context.selected_objects if o.type == 'MESH']
        self.scene_collections = all_collections_in_view_layer(context)
        self.setup(context)
        self.container_counter()
        draw_ui(len(self.objs), self.count)
        self.report({'INFO'}, 'Uniquified Copy')
        return {'FINISHED'}


    def setup(self, context):


        # Duplicate selected objects / link / create containers
        self.containers = []
        def duplicate_obj(obj):
            o = obj.copy()
            if o.type == 'MESH':
                o.data = obj.data.copy()
            o.parent = None
            for c in o.children: c.parent = None
            coll = obj.users_collection[0]

            if coll not in self.scene_collections:
                coll = context.collection

            coll.objects.link(o)
            self.containers.append(Container(obj=o))

        for obj in self.objs:
            duplicate_obj(obj)

        # Setup mod containers
        def contain_mods(container):
            for mod in container.obj.modifiers:
                if mod.type not in {'ARRAY', 'MIRROR', 'BOOLEAN', 'CURVE'}: continue
                obj = None
                if   hasattr(mod,        'object'): obj = mod.object
                elif hasattr(mod, 'mirror_object'): obj = mod.mirror_object
                elif hasattr(mod, 'offset_object'): obj = mod.offset_object
                if not obj: continue
                # Create container
                cont = Container(obj)
                cont.mod_obj_ref = obj.name
                cont.mod_type = mod.type
                # <-- Recursive --> # Only for booleans
                if mod.type == 'BOOLEAN': contain_mods(cont)
                # Nest containers
                container.mod_containers.append(cont)

        # Copy mod ref objects and store in containers
        def copy_mod_objects(container):
            for cont in container.mod_containers:
                # Copy
                obj = None
                if cont.mod_type in {'BOOLEAN', 'CURVE'}:
                    obj = cont.obj.copy()
                    if cont.obj.type in {'MESH', 'CURVE'}:
                        obj.data = cont.obj.data.copy()
                else:
                    obj = bpy.data.objects.new('UniquifyObj', None)
                    obj.empty_display_size = .5
                    obj.empty_display_type = 'SPHERE'
                    try:
                        self.copy_drivers(obj, cont.obj, container.obj)
                    except: pass

                # Remove children
                for child in obj.children: child.parent = None
                # Get coll

                if cont.obj.users_collection:
                    coll = cont.obj.users_collection[0]
                    if coll not in self.scene_collections:
                        coll = context.collection

                    # Inset copy into coll
                    coll.objects.link(obj)
                # Store new obj
                cont.obj = obj
                # <-- Recursive --> # Go down a level
                copy_mod_objects(cont)
                # Assign parent
                cont.obj.parent = container.obj
                # Replace old mod ref
                for mod in container.obj.modifiers:
                    if mod.type not in {'ARRAY', 'MIRROR', 'BOOLEAN', 'CURVE'}: continue
                    obj = None
                    if   hasattr(mod,        'object'): obj = mod.object
                    elif hasattr(mod, 'mirror_object'): obj = mod.mirror_object
                    elif hasattr(mod, 'offset_object'): obj = mod.offset_object
                    if not obj: continue
                    if obj.name == cont.mod_obj_ref:
                        if mod.type == 'BOOLEAN': mod.object = cont.obj
                        if mod.type == 'MIRROR': mod.mirror_object = cont.obj
                        if mod.type == 'ARRAY': mod.offset_object = cont.obj
                        if mod.type == 'CURVE': mod.object = cont.obj

        # Set locations
        def set_matrices(container):
            for cont in container.mod_containers:
                # <-- Recursive --> # Go down a level
                set_matrices(cont)
                # Locate
                cont.obj.matrix_world = cont.matrix
                cont.obj.matrix_local = cont.matrix_local
                cont.obj.matrix_basis = cont.matrix_basis
                cont.obj.matrix_parent_inverse = cont.obj.parent.matrix_world.inverted_safe() if cont.obj.parent and not cont.parent else cont.matrix_parent_inverse

        # Do the work
        for container in self.containers:
            contain_mods(container)
            copy_mod_objects(container)
            set_matrices(container)

        # Set locations for main objects
        for container in self.containers:
            obj = container.obj
            obj.matrix_world = container.matrix

        # Select main objects / Translate
        bpy.ops.object.select_all(action='DESELECT')
        for cont in self.containers:
            obj = cont.obj
            if obj.name not in context.view_layer.objects: continue
            context.view_layer.objects.active = obj
            obj.select_set(True)
            obj.hide_set(False)
        bpy.ops.transform.translate('INVOKE_DEFAULT')


    def container_counter(self):

        self.count = 0
        def counter(container):
            for cont in container.mod_containers:
                counter(cont)
                self.count += 1

        for container in self.containers:
            counter(container)


    def copy_drivers(self, new, old, mod_obj):

        if new.animation_data == None:
            if old.animation_data:
                new.animation_data_create()
            # No drivers to copy
            else: return
        # Drivers already exsist
        else: return

        for d in old.animation_data.drivers:
            array_index = d.array_index
            data_path = d.data_path
            driver = d.driver

            new_driver = new.driver_add(data_path, array_index).driver
            new_driver.type = driver.type

            for v in d.driver.variables:
                var = new_driver.variables.new()
                var.name = v.name

                for index, t in enumerate(v.targets):
                    var.targets[index].id = mod_obj
                    var.targets[index].data_path = t.data_path

            new_driver.expression = driver.expression


def draw_ui(roots=0, objs=0):
    prefs = addon.preference()
    ui = Master()
    draw_data = [
        ['Uniquify Copy'],
        ['Root Objects', roots],
        ['Total Objects', objs]]
    ui.receive_draw_data(draw_data)
    ui.draw(prefs.ui.Hops_operator_draw_bg, prefs.ui.Hops_operator_draw_border)





# --- The bellow works (1-29-2021) : just not needed --- #

# class HOPS_OT_UniquifyObjects(bpy.types.Operator):
#     bl_idname = 'hops.uniquify_objects'
#     bl_label = 'Uniquify Objects'
#     bl_options = {'REGISTER', 'UNDO'}
#     bl_description = '''Uniquify Objects\n\nMake objects on selected objects unique \n Recursive'''

#     @classmethod
#     def poll(cls, context):
#         return context.mode == 'OBJECT' and any(obj.type == 'MESH' for obj in context.selected_objects)


#     def execute(self, context):
#         self.objs = [o for o in context.selected_objects if o.type == 'MESH']
#         self.og_hide = [(o, o.hide_get()) for o in context.scene.objects]
#         roots = len(self.objs)
#         self.setup(context)
#         self.finish(context)
#         draw_ui(roots, len(self.objs))
#         self.report({'INFO'}, 'Objects Uniquified')
#         return {'FINISHED'}


#     def setup(self, context):

#         # Collections
#         self.og_collections = []
#         for child_coll in context.view_layer.layer_collection.children:
#             self.og_collections.append((child_coll, child_coll.hide_viewport))

#         def rec_childs(object):
#             for child in object.children:
#                 if child in self.objs: continue
#                 if child not in self.objs: self.objs.append(child)

#         def rec_mods(object):
#             for mod in object.modifiers:
#                 if mod.type not in {'ARRAY', 'MIRROR', 'BOOLEAN'}: continue
#                 obj = None
#                 if   hasattr(mod,        'object'): obj = mod.object
#                 elif hasattr(mod, 'mirror_object'): obj = mod.mirror_object
#                 elif hasattr(mod, 'offset_object'): obj = mod.offset_object
#                 if not obj: continue
#                 if obj.display_type == 'SOLID': continue
#                 if obj in self.objs: continue
#                 if obj not in self.objs: self.objs.append(obj)

#         # --- Capture --- #
#         previous = len(self.objs)
#         while(True):
#             # for o in self.objs[:]:
#             #     rec_childs(o)
#             for o in self.objs[:]:
#                 rec_mods(o)

#             if previous != len(self.objs):
#                 previous = len(self.objs)
#             else: break

#         # --- Turn on Collections --- #
#         for o in self.objs:
#             turn_on_parent_collections(o, context.scene.collection)
#         bpy.ops.object.hide_view_clear()
#         context.view_layer.update()

#         # --- Select Objs --- #
#         bpy.ops.object.select_all(action='DESELECT')
#         for o in self.objs:
#             if o.name not in context.view_layer.objects: continue
#             o.select_set(True)
#             o.hide_set(False)


#     def finish(self, context):
#         bpy.ops.object.duplicate('INVOKE_DEFAULT')
#         bpy.ops.hops.late_parent('INVOKE_DEFAULT')

#         # Hide States
#         for obj, state in self.og_hide:
#             obj.hide_set(state)

#         # Collections
#         for coll, state in self.og_collections:
#             coll.hide_viewport = state

#         bpy.ops.transform.translate('INVOKE_DEFAULT')


# def draw_ui(roots=0, objs=0):
#     prefs = addon.preference()
#     ui = Master()
#     draw_data = [
#         ['Uniquify Copy'],
#         ['Root Objects', roots],
#         ['Total Objects', objs]]
#     ui.receive_draw_data(draw_data)
#     ui.draw(prefs.ui.Hops_operator_draw_bg, prefs.ui.Hops_operator_draw_border)