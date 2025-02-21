import bpy
from .... utility import addon
from .... utility.base_modal_controls import increment_maps, decrement_maps

from . import States, Auto_Scroll, update_local_view, mods_exit_options, turn_on_coll


class Coll_Tracker:
    def __init__(self):
        self.current_coll = None
        self.original_collection_states = {}
        self.collection_list = []


    def update_data(self, context, obj):
        self.current_coll = context.scene.collection

        # Unhide view layer collections
        def enable_coll(start_coll):
            for child in start_coll.children:
                child.hide_viewport = False
                enable_coll(child)
        enable_coll(context.view_layer.layer_collection)

        # Capture original
        if not self.original_collection_states:
            for c in bpy.data.collections:
                self.original_collection_states[c.name] = [c.hide_viewport]

        # Disabble
        for c in bpy.data.collections:
            c.hide_viewport = True

        # Capture the collections
        if not self.collection_list:
            self.collection_list.append(context.scene.collection)
            def walk(start_coll):
                for child in start_coll.children:
                    if type(child) == bpy.types.Collection:
                        self.collection_list.append(child)
                        walk(child)
            walk(context.scene.collection)


    def set_collectons_back(self):
        
        if not self.original_collection_states: return

        for c in bpy.data.collections:
            if c.name in self.original_collection_states:
                c.hide_viewport = self.original_collection_states[c.name][0]

    # --- OPERATIONS --- #

    def event_update(self, op, context, event):
        pass


    def cycle_coll(self, context, step):

        index = self.collection_list.index(self.current_coll)
        self.current_coll = self.collection_list[(index + step) % len(self.collection_list)]

        self.disable_others(context)


    def exit_tracker(self, context, event):
        pass

    # --- UI --- #

    def expanded_interface(self):
        data = {
            'TYPE' : 'COLL',
            'ACTIVE' : self.current_coll,
            'ITEMS' : self.collection_list,
            'SETFUNC' : self.set_selected,
            'OBJTOGGLE' : self.toggle_objs}
        return data


    def set_selected(self, coll):
        if not coll: return

        self.current_coll = coll
        self.disable_others(bpy.context)


    def toggle_objs(self, coll):
        if not coll: return

        self.current_coll = coll
        self.disable_others(bpy.context)

        bpy.ops.object.hide_view_clear()
        for obj in coll.objects:
            obj.hide_viewport = False


    def fast_interface(self):
        data = []
        if self.current_coll:
            data.append(self.current_coll.name)
        return data

    # --- UTILS --- #

    def disable_others(self, context):
        if not self.collection_list: return
        if not self.current_coll: return

        # Hide all
        for coll in self.collection_list:
            coll.hide_viewport = True

        # Show current
        self.current_coll.hide_viewport = False

        # Top level parent collections
        top_level = [c for c in context.collection.children if type(c) == bpy.types.Collection]
        top_level.append(context.scene.collection)
        if self.current_coll in top_level: return

        # Parent chain for current
        self.parents = []

        def enable_parents(start_coll):

            if self.current_coll == start_coll:
                return True

            for child in start_coll.children:
                if type(child) == bpy.types.Collection:

                    # Skip empty neighbor collections
                    if len(child.children) == 0 and child != self.current_coll:
                        continue

                    if enable_parents(child):
                        self.parents.append(start_coll)
                        return True
            
            return False

        for coll in top_level:
            self.parents = []
            if enable_parents(coll): break

        for coll in self.parents:
            coll.hide_viewport = False
