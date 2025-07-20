import bpy
from ... utility import addon
from ...ui_framework.operator_ui import Master
from ...utility.collections import all_collections_in_view_layer, hops_col_get


object_count, bool_count = 0, 0

class Container:
    def __init__(self, obj, coll, parent_mod_ref_name=""):
        self.__obj = None
        self.matrix_world = None
        self.obj = obj
        self.coll = coll
        self.parent_mod_ref_name = parent_mod_ref_name
        self.bools = []

    @property
    def obj(self):
        return self.__obj

    @obj.setter
    def obj(self, var):
        self.matrix_world = var.matrix_world.copy()
        self.__obj = var


desc = '''Uniquify Cutters

Shift - Uniquify Objects

Make boolean cutters on selected objects unique
Recursive'''

class HOPS_OT_UniquifyCutters(bpy.types.Operator):
    bl_idname = 'hops.uniquify_cutters'
    bl_label = 'Uniquify Cutters'
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = desc

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' and any(obj.type == 'MESH' for obj in context.selected_objects)


    def invoke(self, context, event):
        if event.shift:
            bpy.ops.hops.uniquify_objects('INVOKE_DEFAULT')
            return {'FINISHED'}
        return self.execute(context)


    def execute(self, context):
        containers = [Container(o, o.users_collection[0]) for o in context.selected_objects if o.type == 'MESH']
        set_bools(containers)
        copy_and_parent(containers)
        set_mirrors(containers)
        selection_setup(context, containers)
        object_and_bool_count(containers)

        draw_ui()
        self.report({'INFO'}, 'Cutters Uniquified')
        return {'FINISHED'}


def set_bools(containers):

    # Top level
    for c in containers:
        for mod in c.obj.modifiers:
            if mod.type == 'BOOLEAN':
                if mod.object:
                    bc = Container(mod.object, mod.object.users_collection[0], parent_mod_ref_name=mod.object.name)
                    c.bools.append(bc)

    # Recursive
    def child_collect(container):
        obj = container.obj

        for mod in obj.modifiers:
            if mod.type == 'BOOLEAN':
                if mod.object:
                    bc = Container(mod.object, mod.object.users_collection[0], parent_mod_ref_name=mod.object.name)
                    child_collect(bc)
                    container.bools.append(bc)

    for c in containers:
        for b in c.bools:
            child_collect(b)


def copy_and_parent(containers):

    # Recursive
    def recursive(container, last_con):

        # Get to the bottom of each branch
        for bool_con in container.bools:
            new_obj = bool_con.obj.copy()
            bool_con.coll.objects.link(new_obj)
            bool_con.obj = new_obj

            recursive(bool_con, container)

        # Skip top level calls
        if container.obj == last_con.obj: return

        # Parent
        container.obj.parent = last_con.obj

        # Insert the new obj into the mod
        if container.parent_mod_ref_name:
            for mod in last_con.obj.modifiers:
                if mod.type == 'BOOLEAN':
                    if mod.object:
                        if mod.object.name == container.parent_mod_ref_name:
                            mod.object = container.obj

        # Locate
        container.obj.matrix_parent_inverse = last_con.obj.matrix_world.inverted_safe()
        container.obj.matrix_world = container.matrix_world

    # Start recursive at each top level
    for c in containers:

        # NOTE: This will create / not create auto duplicate
        # new_obj = c.obj.copy()
        # c.coll.objects.link(new_obj)
        # c.obj = new_obj

        recursive(c, c)


def set_mirrors(containers):

    def set_mirror(container):
        if not container.bools: return
        obj = container.obj

        for b in container.bools:
            set_mirror(b)
            for mod in b.obj.modifiers:
                if mod.type == 'MIRROR':
                    if mod.mirror_object:
                        mod.mirror_object = obj

    for c in containers:
        set_mirror(c)


def selection_setup(context, containers):
    bpy.ops.object.select_all(action='DESELECT')

    scene_collections = all_collections_in_view_layer(context)
    hops_col = hops_col_get(context)

    # Recursive hide
    def hide_objects(container):
        # Get to the bottom of each branch
        for bool_con in container.bools:
            hide_objects(bool_con)

        # Created objects have one collection
        # The collection may not be part of the scene, so hide_set() throws
        col = container.obj.users_collection[0]

        # Fallback onto cutters collection
        if col not in scene_collections:
            col.objects.unlink(container.obj)
            hops_col.objects.link(container.obj)

        container.obj.hide_set(True)

    for c in containers:
        hide_objects(c)

        c.obj.hide_set(False)
        c.obj.select_set(True)
        context.view_layer.objects.active = c.obj


def object_and_bool_count(containers):

    global object_count, bool_count
    object_count, bool_count = 0, 0

    # Recursive counter
    def count_bools(container):
        global bool_count
        bool_count += 1
        # Get to the bottom of each branch
        for bool_con in container.bools:
            count_bools(bool_con)

    for c in containers:
        object_count += 1
        count_bools(c)

    bool_count -= object_count


def draw_ui():
    global object_count, bool_count
    prefs = addon.preference()
    ui = Master()
    draw_data = [
        ['Uniquify Cutters'],
        ['Root Objects', object_count],
        ['Total Cutters', bool_count]]
    ui.receive_draw_data(draw_data)
    ui.draw(prefs.ui.Hops_operator_draw_bg, prefs.ui.Hops_operator_draw_border)