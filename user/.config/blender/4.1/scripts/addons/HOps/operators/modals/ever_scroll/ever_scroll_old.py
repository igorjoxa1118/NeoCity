import bpy, time
from enum import Enum
from gpu_extras.batch import batch_for_shader
from ... utility import addon
from ... ui_framework.master import Master
from ... ui_framework.utils.mods_list import get_mods_list
from ... ui_framework.graphics.draw import draw_text, render_quad, draw_border_lines
from ... ui_framework.utils.geo import get_blf_text_dims
from ... utility.base_modal_controls import Base_Modal_Controls, confirm_events, increment_maps, decrement_maps
from ... utils.event import Event_Clone
from ... utility.collections import unhide_layers
from ... utils.toggle_view3d_panels import collapse_3D_view_panels
from ... addon.utility import modifier as mod_utils
from ... addon.utility import method_handler
from ... addon.utility.screen import dpi_factor
from .. meshtools.applymod import apply_mod


def update_local_view(context, objs):
    if context.space_data.local_view:       
        bpy.ops.view3d.localview(frame_selected=False)
        for obj in objs:
            obj.hide_set(False)
            obj.select_set(True)
        bpy.ops.view3d.localview(frame_selected=False)
        return True
    return False


def mods_exit_options(context, event, obj):

    # Apply mods on obj
    if event.ctrl and event.type in confirm_events:
        mod_utils.apply(obj, visible=True)
        bpy.ops.hops.draw_wire_mesh_launcher('INVOKE_DEFAULT', target='SELECTED')
        bpy.ops.hops.display_notification(info="Applied visible modifiers")
        # Reveal remaining mods
        for mod in obj.modifiers:
            if mod.show_render:
                mod.show_viewport = True
        return True

    # Apply mods on copy of obj
    elif event.shift and event.type in confirm_events:
        new_obj = obj.copy()
        new_obj.data = obj.data.copy()

        for col in obj.users_collection:
            if col not in new_obj.users_collection:
                col.objects.link(new_obj)

        mod_utils.apply(new_obj, visible=True)
        new_obj.modifiers.clear()

        context.view_layer.objects.active = new_obj
        obj.select_set(False)

        for mod in obj.modifiers:
            mod.show_viewport = True

        bpy.ops.hops.draw_wire_mesh_launcher('INVOKE_DEFAULT', target='SELECTED')
        bpy.ops.hops.display_notification(info="Applied visible modifiers on duplicate")
        return True

    return False


def turn_on_coll(obj, main_coll):
    unhide_layers(obj)

    for coll in obj.users_collection:
        if coll != main_coll:
            for object in coll.objects:
                if object.display_type == 'WIRE':
                    object.hide_viewport = False
                    object.hide_set(True)


class States:
    MOD = 0
    CHILD = 1
    BOOL = 2
    COLL = 3


class Mod_Tracker:
    def __init__(self):
        self.mods = []
        self.index = 0
        self.just_reset = False
        self.last_affected = ""
        self.current_mod = None
        self.looping = False
        self.auto_scroll_sequance_begin = False

        # Mod apply from expanded
        self.apply_mod = None
        self.apply_up_to = None


    def update_data(self, context, obj):
        self.index = 0
        self.just_reset = True
        self.mods = []

        # Mod apply from expanded
        self.apply_mod = None
        self.apply_up_to = None

        for mod in obj.modifiers:
            self.mods.append(mod)

        if self.mods:
            self.current_mod = self.mods[0]
            self.last_affected = self.mods[0].name

        main_coll = obj.users_collection[0]

        # Local mode support / Turn on parent collections
        objs = []
        obj_stats = []

        for mod in self.mods:
            if hasattr(mod, 'mirror_object'):
                if mod.mirror_object:
                    objs.append(mod.mirror_object)
            elif hasattr(mod, 'object'):
                if mod.object:
                    objs.append(mod.object)

        filtered = []

        colls = [o.users_collection[0] for o in objs if len(o.users_collection) > 0]
        for obj in objs:
            if not obj.users_collection: continue
            if obj.users_collection[0] != colls:
                filtered.append(obj)

        for obj in filtered:
            turn_on_coll(obj, main_coll)

        for obj in objs:
            obj_stats.append((obj, obj.hide_get(), obj.select_get()))

        # Local mode support
        if update_local_view(context, objs):
            for obj, hide, select in obj_stats:
                obj.select_set(select)
                obj.hide_set(hide)


    def cycle_mods(self, context, step=0):
        if not self.mods_valid(): return

        self.auto_scroll_sequance_begin = False

        if self.just_reset:
            self.just_reset = False
            self.last_affected = ""
            # Looping codes for skipping on blank frame
            if self.index == len(self.mods) - 1:
                for mod in self.mods:
                    mod.show_viewport = True
                self.mods[-1].show_viewport = True
                self.index = -2
            else:
                self.index = -1
                for mod in self.mods:
                    if mod.show_render: # Protect shading
                        mod.show_viewport = False

        if addon.preference().property.modal_handedness == 'RIGHT':
            step *= -1

        show = True if step > 0 else False

        # Looping : Set first loop back to nothing showing
        if self.index == -1:
            self.index = 0
            return
        elif self.index == -2:
            self.index = len(self.mods) - 1
            return

        mod = self.mods[self.index]
        if mod.show_render: # Protect shading
            mod.show_viewport = show
        if mod.type == 'BOOLEAN':
            if mod.object:
                bpy.ops.hops.draw_wire_mesh_launcher(object_name=mod.object.name)

        self.current_mod = mod
        self.last_affected = mod.name

        self.index += step
        if self.looping:
            if self.index > len(self.mods) - 1:
                self.index = 0
                self.just_reset = True
                self.auto_scroll_sequance_begin = True
            elif self.index < 0:
                self.index = len(self.mods) - 1
                self.just_reset = True
        else:
            self.index = max(min(self.index, len(self.mods) - 1), 0)

    # --- OPERATIONS --- #

    def event_update(self, context, event, obj):

        # Expanded apply
        if self.apply_mod:
            self.apply_mods_expanded_work(obj)
            self.update_data(context, obj)

        # Validate
        if not self.mods_valid(): return

        # Visible toggle
        if event.type == 'A' and event.value == 'PRESS':
            if event.shift:
                self.reveal_mod_object()
            else:
                self.toggle_visible()
        
        # Apply mod
        elif event.type == 'F' and event.value == 'PRESS':
            if event.shift:
                self.apply_to(obj)
            else:
                self.apply_current(obj)
            return 'RESET'

        # Render
        elif event.type == 'R' and event.value == 'PRESS':
            if event.shift:
                self.toggle_render_for_all()
            else:
                self.toggle_render_for_active()

        # Loop Scroll
        elif event.type == 'L' and event.value == 'PRESS':
            self.looping = not self.looping

        # Wire display current
        elif event.type == 'W' and event.value == 'PRESS':
            self.wire_display_current()

        # Shift mods
        if event.shift and event.value == 'PRESS':
            if event.type in increment_maps:
                self.move_mod(obj, direction=1)
            elif event.type in decrement_maps:
                self.move_mod(obj, direction=-1)


    def toggle_visible(self):
        if self.current_mod:
            self.current_mod.show_viewport = not self.current_mod.show_viewport


    def reveal_mod_object(self):
        if not self.current_mod: return

        def reveal(obj):
            show = not obj.hide_get()
            obj.hide_set(show)
            if not show:
                bpy.ops.hops.draw_wire_mesh_launcher(object_name=obj.name)

        if hasattr(self.current_mod, 'mirror_object'):
            if self.current_mod.mirror_object:
                reveal(self.current_mod.mirror_object)

        elif hasattr(self.current_mod, 'object'):
            if self.current_mod.object:
                reveal(self.current_mod.object)


    def apply_to(self, obj):
        if self.current_mod:
            count = 0
            target_name = self.current_mod.name
            for mod in obj.modifiers:
                if mod.show_viewport == False:
                    continue
                count += 1
                cut_off_name = mod.name
                try:
                    bpy.ops.object.modifier_apply(modifier=mod.name)
                except:
                    obj.modifiers.remove(mod)

                if target_name == cut_off_name: break
            bpy.ops.hops.display_notification(info=f'{count} modifiers applied')

            for mod in obj.modifiers:
                mod.show_viewport = True


    def apply_current(self, obj):
        if self.current_mod:
            try:
                bpy.ops.object.modifier_apply(modifier=self.current_mod.name)
            except:
                obj.modifiers.remove(self.current_mod)


    def toggle_render_for_active(self):
        if self.current_mod:
            self.current_mod.show_render = not self.current_mod.show_render


    def toggle_render_for_all(self):
        turn_on = any([m.show_render == False for m in self.mods])
        for mod in self.mods:
            if turn_on: mod.show_render = True
            else: mod.show_render = False


    def move_mod(self, obj, direction=0):

        if not self.current_mod: return
        if direction > 0:
            bpy.ops.object.modifier_move_up(modifier=self.current_mod.name)
        elif direction < 0:
            bpy.ops.object.modifier_move_down(modifier=self.current_mod.name)

        if self.current_mod:
            self.mods = []
            for mod in obj.modifiers:
                self.mods.append(mod)
            if self.current_mod in self.mods:
                self.index = self.mods.index(self.current_mod)


    def wire_display_current(self):
        if not self.current_mod: return
        obj = None
        if hasattr(self.current_mod, 'object'):
            obj = self.current_mod.object
        elif hasattr(self.current_mod, 'mirror_object'):
            obj = self.current_mod.mirror_object
        
        if obj:
            bpy.ops.hops.draw_wire_mesh_launcher(object_name=obj.name)


    def exit_tracker(self, context, event, obj):
        mods_exit_options(context, event, obj)

    # --- UI --- #

    def expanded_interface(self):
        data = {
            'TYPE' : 'MOD',
            'ACTIVE' : self.last_affected,
            'ITEMS' : self.mods[:],
            'SETFUNC' : self.make_selected_active,
            'SHIFTFUNC' : self.reveal_mod_object,
            'APPLYFUNC' : self.apply_mods_expanded_setup}
        return data

    
    def make_selected_active(self, index=0):
        if index < len(self.mods):
            if index < 0: index = 0
            self.index = index
            self.current_mod = self.mods[self.index]
            self.last_affected = self.current_mod.name
            if self.current_mod.type == 'BOOLEAN':
                if self.current_mod.object:
                    bpy.ops.hops.draw_wire_mesh_launcher(object_name=self.current_mod.object.name)


    def apply_mods_expanded_setup(self, mod, up_to=False):
        self.apply_mod = mod
        self.apply_up_to = up_to


    def apply_mods_expanded_work(self, obj):
        if self.apply_up_to:
            count = 0
            for mod in obj.modifiers:
                if mod.show_viewport == False:
                    continue

                count += 1
                should_break = True if mod.name == self.apply_mod.name else False
                try:
                    bpy.ops.object.modifier_apply(modifier=mod.name)
                except:
                    obj.modifiers.remove(mod)
                if should_break: break
            bpy.ops.hops.display_notification(info=f'{count} modifiers applied')
            for mod in obj.modifiers:
                mod.show_viewport = True
        else:
            try:
                bpy.ops.object.modifier_apply(modifier=self.apply_mod.name)
            except:
                obj.modifiers.remove(self.apply_mod)

        self.apply_mod = None
        self.apply_up_to = None


    def fast_interface(self):
        data = []
        if self.current_mod:
            if self.index == 0:
                data.append("Unmodified Mesh")
            else:
                data.append(self.current_mod.name)
                if self.current_mod in self.mods:
                    data.append(self.mods.index(self.current_mod) + 1)
        return data

    # --- UTILS --- #

    def mods_valid(self):
        if len(self.mods) == 0:
            return False
        return True


class Child_Tracker:
    def __init__(self):
        self.children = []
        self.tracked = []
        self.index = 0
        self.last_affected = ""
        self.current_obj = None
        self.looping = False
        self.auto_scroll_sequance_begin = False


    def update_data(self, context, obj):
        self.children = []
        self.tracked = []
        self.index = 0

        for child in obj.children:
            self.children.append(child)

        if self.children:
            self.last_affected = self.children[0].name
            self.current_obj = self.children[0]

            for obj in self.children:
                unhide_layers(obj)

        else:
            self.last_affected = ""
            self.current_obj = None

        # Local mode support
        objs = []
        obj_stats = []
        for obj in self.children:
            objs.append(obj)
            obj_stats.append((obj, obj.hide_get(), obj.select_get()))

        if update_local_view(context, objs):
            for obj, hide, select in obj_stats:
                obj.select_set(select)
                obj.hide_set(hide)


    def cycle_children(self, context, step=0):
        if len(self.children) == 0: return

        self.auto_scroll_sequance_begin = False
        
        for obj in self.children:
            obj.select_set(False)
            
        if addon.preference().property.modal_handedness == 'RIGHT':
            step *= -1
    
        self.index += step
        if self.index < 0:
            self.index = 0
        elif self.index > len(self.children) - 1:
            if self.looping:
                self.index = 0
                self.auto_scroll_sequance_begin = True
            else:
                self.index = len(self.children) - 1

        obj = self.children[self.index]
        bpy.ops.hops.draw_wire_mesh_launcher(object_name=obj.name)
        obj.select_set(True)
        obj.hide_set(False)

        self.current_obj = obj
        self.last_affected = obj.name

    # --- OPERATIONS --- #
    
    def event_update(self, context, event, obj):

        # Delete object
        if event.type == 'D' and event.value == 'PRESS':
            self.delete_obj()
            return 'RESET'

        # Visible toggle
        elif event.type == 'V' and event.value == 'PRESS':
            if event.shift:
                self.toggle_all_visible()
            else:
                self.toggle_current_visible()

        # Visible booleans toggle
        elif event.type == 'B' and event.value == 'PRESS':
            self.toggle_boolean_visible(obj)

        # Add to tracked
        elif event.type == 'A' and event.value == 'PRESS':
            self.add_to_tracked()

        # Wire display current
        elif event.type == 'W' and event.value == 'PRESS':
            self.wire_display_current()


    def delete_obj(self):
        if self.current_obj:
            self.current_obj.parent = None
            bpy.data.objects.remove(self.current_obj)
            

    def toggle_current_visible(self):
        if not self.children: return
        if not self.current_obj: return
        self.current_obj.hide_set(not self.current_obj.hide_get())
        if not self.current_obj.hide_get():
            bpy.ops.hops.draw_wire_mesh_launcher(object_name=self.current_obj.name)
            self.current_obj.select_set(True)


    def toggle_all_visible(self):
        if self.children:
            show = not any([o.hide_get() for o in self.children])
            for o in self.children:
                if o not in self.tracked:
                    o.hide_set(show)
            

    def toggle_boolean_visible(self, obj):
        if not obj: return
        if not self.children: return

        bool_objs = []
        for mod in obj.modifiers:
            if mod.type == 'BOOLEAN':
                if mod.object:
                    obj = mod.object
                    if obj in self.children:
                        index = self.children.index(obj)
                        bool_objs.append(self.children[index])

        if not bool_objs: return

        show = not any([o.hide_get() for o in bool_objs])
        for o in bool_objs:
            o.hide_set(show)


    def add_to_tracked(self, obj=None):
        if not self.current_obj: return

        if obj:
            if obj in self.children:
                self.current_obj = obj
                self.index = self.children.index(obj)
                self.last_affected = obj.name

        if self.current_obj not in self.tracked:
            self.tracked.append(self.current_obj)
            bpy.ops.hops.draw_wire_mesh_launcher(object_name=self.current_obj.name)
            bpy.ops.hops.display_notification(info='Child appended to visibility')
            self.current_obj.hide_set(False)
        else:
            self.tracked.remove(self.current_obj)
            bpy.ops.hops.draw_wire_mesh_launcher(object_name=self.current_obj.name)
            bpy.ops.hops.display_notification(info='Child removed from visibility')
            self.current_obj.hide_set(True)


    def wire_display_current(self):
        if self.current_obj:
            bpy.ops.hops.draw_wire_mesh_launcher(object_name=self.current_obj.name)


    def exit_tracker(self, context, event, obj):
        if self.current_obj != None:
            bpy.ops.object.select_all(action='DESELECT')
            self.current_obj.hide_set(False)
            self.current_obj.select_set(True)
            return

        for child in self.children:
            if child.select_get():
                bpy.ops.object.select_all(action='DESELECT')
                child.hide_set(False)
                child.select_set(True)
                context.view_layer.objects.active = child
                break

    # --- UI --- #

    def expanded_interface(self):
        data = {
            'TYPE' : 'CHILD',
            'ACTIVE' : self.last_affected,
            'ITEMS' : self.children[:],
            'SETFUNC' : self.make_selected_active,
            'TRACKED' : self.tracked,
            'TRACKFUNC' : self.add_to_tracked}
        return data


    def make_selected_active(self, index=0):
        if index < len(self.children):
            if index < 0: index = 0
            self.index = index
            self.current_obj = self.children[self.index]
            self.last_affected = self.current_obj.name
            self.current_obj.hide_set(False)
            self.current_obj.select_set(True)
            bpy.ops.hops.draw_wire_mesh_launcher(object_name=self.current_obj.name)


    def fast_interface(self):
        data = []
        if self.current_obj:
            data.append(self.current_obj.name)
            data.append(self.index + 1)
            data.append(len(self.children))
        return data


class Bool_Tracker:
    def __init__(self):
        self.all_mods = []
        self.bools = []
        self.tracked_bools = [] # Appended bools to end selction
        self.ran_additive_check = False
        self.additive_protected = [] # Dont mess with start bools if prefs option is on
        self.index = 0
        self.last_affected = ""
        self.current_mod = None
        self.auto_scroll_sequance_begin = False

        # Recursive
        self.r_parent_obj = None
        self.recursive_active = False
        self.r_index = 0
        self.r_mods = []

        # For Recursive show
        self.reveal_objects = []

        # Function from expanded
        self.apply_mod = None
        self.apply_up_to = None


    def update_data(self, context, obj):
        self.all_mods = []
        self.bools = []
        self.tracked_bools = []
        self.index = 0

        # Recursive
        self.r_parent_obj = None
        self.recursive_active = False
        self.r_index = 0
        self.r_mods = []

        # For Recursive show
        self.reveal_objects = []

        # Function from expanded
        self.apply_mod = None
        self.apply_up_to = None

        main_coll = obj.users_collection[0]

        # Additive mode : Only runs once
        if self.ran_additive_check == False:
            self.ran_additive_check = True
            if addon.preference().property.bool_scroll == 'ADDITIVE':
                for mod in obj.modifiers:
                    if mod.type == 'BOOLEAN':
                        if mod.object:
                            if not mod.object.hide_get():
                                self.additive_protected.append(mod)

        objs = []
        for mod in obj.modifiers:
            if mod in self.additive_protected: continue
            self.all_mods.append(mod)
            if mod.type == 'BOOLEAN':
                self.bools.append(mod)
                if mod.object:
                    objs.append(mod.object)

        objs = list(set(objs))

        filtered = []
        colls = [o.users_collection[0] for o in objs if len(o.users_collection) > 0]
        for obj in objs:
            obj.hide_viewport = False
            if obj.name in context.view_layer.objects:
                obj.hide_set(True)

            if not obj.users_collection: continue
            if obj.users_collection[0] != colls:
                filtered.append(obj)

        for obj in filtered:
            turn_on_coll(obj, main_coll)

        if self.bools:
            self.index = len(self.bools) -1
            self.last_affected = self.bools[self.index].name
            self.current_mod = self.bools[self.index]
        else:
            self.last_affected = ""
            self.current_mod = None

        # Local mode support
        objs = []
        obj_stats = []
        for mod in self.bools:
            if mod.object:
                obj = mod.object
                objs.append(obj)
                obj_stats.append((obj, obj.hide_get(), obj.select_get()))

        if update_local_view(context, objs):
            for obj, hide, select in obj_stats:
                obj.select_set(select)
                obj.hide_set(hide)

        if self.bools:
            self.additive_prefs_save(self.bools[self.index])


    def cycle_bools(self, context, step=0):
        if len(self.bools) == 0: return

        self.auto_scroll_sequance_begin = False

        if addon.preference().property.modal_handedness == 'RIGHT':
            step *= -1

        for mod in self.bools:
            if mod.object:
                if mod.object not in self.tracked_bools:
                    mod.object.hide_set(True)
                    mod.object.select_set(False)

        # Recursive bool scroll
        if self.recursive_active:
            self.recursive_bool_cycle(step)
            return

        self.index += step
        if self.index < 0:
            self.index = len(self.bools) - 1
        elif self.index > len(self.bools) - 1:
            self.index = 0
            self.auto_scroll_sequance_begin = True

        mod = self.bools[self.index]

        self.last_affected = mod.name
        self.current_mod = mod

        if mod.object:
            obj = mod.object
            obj.hide_set(False)
            obj.select_set(True)
            bpy.ops.hops.draw_wire_mesh_launcher(object_name=obj.name)

        self.additive_prefs_save(mod)


    def additive_prefs_save(self, mod):
        if addon.preference().property.bool_scroll == 'ADDITIVE':
            if not mod.object: return
            if mod.object not in self.tracked_bools:
                self.tracked_bools.append(mod.object)


    def recursive_bool_cycle(self, step=0):
        self.r_index += step
        if self.r_index < 0:
            self.r_index = len(self.r_mods) - 1
        elif self.r_index > len(self.r_mods) - 1:
            self.r_index = 0

        self.hide_all_recursive_mods()

        mod = self.r_mods[self.r_index][0]

        self.last_affected = mod.name
        self.current_mod = mod

        self.r_parent_obj.hide_set(False)
        self.r_parent_obj.select_set(True)

        if mod.object:
            obj = mod.object
            obj.hide_set(False)
            obj.select_set(True)
            bpy.ops.hops.draw_wire_mesh_launcher(object_name=obj.name)
            

    def hide_all_recursive_mods(self):
        for items in self.r_mods:
            mod = items[0]
            if mod.object:
                if mod.object not in self.tracked_bools:
                    mod.object.hide_set(True)
                    mod.object.select_set(False)

    # --- OPERATIONS --- #

    def event_update(self, context, event, obj):

        if self.apply_mod:
            self.apply_mod_from_ui_work(context, obj)
            self.update_data(context, obj)

        # Visible toggle
        if event.type == 'V' and event.value == 'PRESS':
            if event.shift:
                self.toggle_all_visible()
            else:
                self.toggle_visible()

        # Apply current
        elif event.type == 'F' and event.value == 'PRESS':
            if event.shift:
                self.apply_to(obj)
            else:
                self.apply_current(obj)
            return 'RESET'

        # Append bool object to tracked
        elif event.type == 'A' and event.value == 'PRESS':
            self.add_current_to_tracked()

        # Wire display current
        elif event.type == 'W' and event.value == 'PRESS':
            self.wire_display_current()

        # Start recursive
        elif event.type == 'R' and event.value == 'PRESS':
            if event.shift:
                self.stop_recursive()
            else:
                self.start_recursive(obj)

        # Show Recursive Bools
        elif event.type == 'S' and event.value == 'PRESS':
            if not event.ctrl:
                self.show_recursive_objects()

        # Shift mods
        if event.shift and event.value == 'PRESS':
            if event.type in increment_maps:
                self.move_mod(obj, direction=1)
            elif event.type in decrement_maps:
                self.move_mod(obj, direction=-1)


    def toggle_visible(self):
        if self.current_mod:
            self.current_mod.show_viewport = not self.current_mod.show_viewport


    def toggle_all_visible(self):
        if self.bools:
            show = not any([m.show_viewport for m in self.bools])
            for mod in self.bools:
                mod.show_viewport = show


    def add_current_to_tracked(self, mod=None):
        if not self.current_mod: return
        if not self.current_mod.object: return

        # Called from expanded with mod option
        if mod:
            if mod.object:
                if mod.object not in self.tracked_bools:
                    self.tracked_bools.append(mod.object)
                    bpy.ops.hops.draw_wire_mesh_launcher(object_name=mod.object.name)
                    bpy.ops.hops.display_notification(info='Bool appended to visibility')    
                    mod.object.hide_set(False)              
                else:
                    self.tracked_bools.remove(mod.object)
                    bpy.ops.hops.draw_wire_mesh_launcher(object_name=mod.object.name)
                    bpy.ops.hops.display_notification(info='Bool removed from visibility')     
                    mod.object.hide_set(True)
            return

        # Regular modal option
        if self.current_mod.object not in self.tracked_bools:
            self.tracked_bools.append(self.current_mod.object)
            bpy.ops.hops.draw_wire_mesh_launcher(object_name=self.current_mod.object.name)
            bpy.ops.hops.display_notification(info='Bool appended to visibility')
            self.current_mod.object.hide_set(False)
        else:
            self.tracked_bools.remove(self.current_mod.object)
            bpy.ops.hops.draw_wire_mesh_launcher(object_name=self.current_mod.object.name)
            bpy.ops.hops.display_notification(info='Bool removed from visibility')
            self.current_mod.object.hide_set(True)


    def apply_current(self, obj):
        if self.current_mod:
            # Remove from tracked
            if self.current_mod.object:
                if self.current_mod.object in self.tracked_bools:
                    self.tracked_bools.remove(self.current_mod.object)
            try:
                bpy.ops.object.modifier_apply(modifier=self.current_mod.name)
            except:
                obj.modifiers.remove(self.current_mod)


    def apply_to(self, obj):
        if self.current_mod:
            count = 0
            target_name = self.current_mod.name
            for mod in obj.modifiers:
                count += 1
                cut_off_name = mod.name
                try:
                    bpy.ops.object.modifier_apply(modifier=mod.name)
                except:
                    obj.modifiers.remove(mod)

                if target_name == cut_off_name: break
            bpy.ops.hops.display_notification(info=f'{count} modifiers applied')


    def move_mod(self, obj, direction=0):

        if not self.current_mod: return
        if direction > 0:
            bpy.ops.object.modifier_move_up(modifier=self.current_mod.name)
        elif direction < 0:
            bpy.ops.object.modifier_move_down(modifier=self.current_mod.name)

        if self.current_mod:
            self.all_mods = []
            self.bools = []
            for mod in obj.modifiers:
                self.all_mods.append(mod)
                if mod.type == 'BOOLEAN':
                    self.bools.append(mod)
            if self.current_mod in self.bools:
                self.index = self.bools.index(self.current_mod)


    def wire_display_current(self):
        if not self.current_mod: return
        obj = None
        if hasattr(self.current_mod, 'object'):
            if self.current_mod.object:
                bpy.ops.hops.draw_wire_mesh_launcher(object_name=self.current_mod.object.name)       


    def exit_tracker(self, context, event, obj):
        if mods_exit_options(context, event, obj):
            return

        if self.current_mod:
            if self.current_mod.object:
                bpy.ops.object.select_all(action='DESELECT')
                self.current_mod.object.select_set(True)
                context.view_layer.objects.active = self.current_mod.object
                self.current_mod.object.hide_set(False)

    # Recursive Data Setup
    def start_recursive(self, obj):

        if not self.current_mod or self.current_mod.type != 'BOOLEAN':
            bpy.ops.hops.display_notification(info='Unable to begin Recursive Booleans')

        if len(self.r_mods) > 0:
            self.hide_all_recursive_mods()

        # Recursive
        self.temp_mods = []
        self.child_count = 0
        
        def bool_collect(start_mod, obj):
            if not start_mod.object: return
            for mod in start_mod.object.modifiers:
                if mod.type == 'BOOLEAN':
                    if mod.object:
                        self.child_count += 1
                        self.temp_mods.append((mod, start_mod.object))
                        bool_collect(mod, mod.object)

        bool_collect(self.current_mod, obj)

        if self.child_count > 0:
            self.r_parent_obj = self.current_mod.object
            self.recursive_active = True
            self.r_mods = self.temp_mods[:]
            self.r_index = 0

            bpy.ops.hops.display_notification(info='Started Recursive Scroll')
        else:
            bpy.ops.hops.display_notification(info='No Recursive Booleans found')


    def stop_recursive(self):
        if len(self.r_mods) > 0: self.hide_all_recursive_mods()

        # Recursive
        self.child_count = 0
        self.r_mods = []
        self.recursive_active = False
        self.r_index = 0


    def show_recursive_objects(self):

        if not self.current_mod or self.current_mod.type != 'BOOLEAN':
            bpy.ops.hops.display_notification(info='Unable to show Recursive Booleans')

        if self.reveal_objects:
            for obj in self.reveal_objects:
                if obj in self.tracked_bools: continue
                obj.hide_set(True)
                obj.select_set(False)

        self.reveal_objects = []
        def bool_collect(start_mod):
            if not start_mod.object: return
            for mod in start_mod.object.modifiers:
                if mod.type == 'BOOLEAN':
                    if mod.object:
                        self.reveal_objects.append(mod.object)
                        bool_collect(mod)

        bool_collect(self.current_mod)

        if not self.reveal_objects:
            bpy.ops.hops.display_notification(info='No recursive objects to show')
            return

        for obj in self.reveal_objects:
            obj.hide_set(False)
            obj.select_set(True)

        bpy.ops.hops.display_notification(info=f'Revealed {len(self.reveal_objects)} booleans')

    # --- UI --- #

    def expanded_interface(self):
        data = {}

        if self.recursive_active:
            data = {
                'TYPE' : 'BOOL',
                'ACTIVE' : self.r_index + 1,
                'ITEMS' : [i[0] for i in self.r_mods],
                'SETFUNC' : self.make_selected_active,
                'APPLYFUNC' : self.apply_mod_from_ui_setup,
                'ADDCLICK' : self.add_current_to_tracked,
                'TRACKED' : self.tracked_bools,
                'TRACKMOD' : self.add_current_to_tracked}
            return data

        data = {
            'TYPE' : 'BOOL',
            'ACTIVE' : self.last_affected,
            'ITEMS' : self.all_mods[:],
            'SETFUNC' : self.make_selected_active,
            'APPLYFUNC' : self.apply_mod_from_ui_setup,
            'ADDCLICK' : self.add_current_to_tracked,
            'TRACKED' : self.tracked_bools,
            'TRACKMOD' : self.add_current_to_tracked}
        return data


    def apply_mod_from_ui_setup(self, mod, up_to=False):
        self.apply_mod = mod
        self.apply_up_to = up_to

    
    def apply_mod_from_ui_work(self, context, obj):
        if self.recursive_active:
            reset_active = context.view_layer.objects.active
            for mod, obj in self.r_mods:
                if mod == self.apply_mod:
                    context.view_layer.objects.active = obj
                    try:
                        bpy.ops.object.modifier_apply(modifier=mod.name)
                    except:
                        obj.modifiers.remove(mod)
                    context.view_layer.objects.active = reset_active
                    break
            
            self.apply_mod = None
            self.apply_up_to = None
            return

        if self.apply_up_to:
            count = 0
            for mod in obj.modifiers:
                count += 1
                should_break = True if mod.name == self.apply_mod.name else False
                try:
                    bpy.ops.object.modifier_apply(modifier=mod.name)
                except:
                    obj.modifiers.remove(mod)
                if should_break: break
            bpy.ops.hops.display_notification(info=f'{count} modifiers applied')
        else:
            try:
                bpy.ops.object.modifier_apply(modifier=self.apply_mod.name)
            except:
                obj.modifiers.remove(self.apply_mod)

        self.apply_mod = None
        self.apply_up_to = None


    def make_selected_active(self, index=0):
        if self.recursive_active:
            self.hide_all_recursive_mods()
            if index < 0: index = 0
            self.r_index = index
            mod = self.r_mods[self.r_index][0]
            if mod.type == 'BOOLEAN':
                if mod.object:
                    obj = mod.object
                    obj.hide_set(False)
                    obj.select_set(True)
                    bpy.ops.hops.draw_wire_mesh_launcher(object_name=obj.name)
            return

        if index < len(self.bools):
            if index < 0: index = 0
            self.index = index
            self.current_mod = self.bools[self.index]
            self.last_affected = self.current_mod.name
            if self.current_mod.object:

                for mod in self.bools:
                    if mod.object:
                        if mod.object not in self.tracked_bools:
                            mod.object.hide_set(True)

                self.current_mod.object.hide_set(False)
                bpy.ops.hops.draw_wire_mesh_launcher(object_name=self.current_mod.object.name)


    def fast_interface(self):
        data = []

        if self.recursive_active:
            data = ['Recursive', self.r_mods[self.r_index][0].name]
            return data

        if self.current_mod:
            if self.all_mods and self.current_mod in self.all_mods:
                index = self.all_mods.index(self.current_mod) + 1
                data.append(index)
            data.append(self.current_mod.name)
            if self.current_mod.object:
                data.append(self.current_mod.object.name)

        return data


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

    def event_update(self, context, event):
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


class Tracker_Man:
    def __init__(self):
        self.mod_tracker = Mod_Tracker()
        self.child_tracker = Child_Tracker()
        self.bool_tracker = Bool_Tracker()
        self.coll_tracker = Coll_Tracker()


    def update_obj_data(self, context, obj, state):
        '''Called when setting a new object.'''

        # Global
        self.coll_tracker.set_collectons_back()

        # Trackers
        if state == States.MOD:
            return self.mod_tracker.update_data(context, obj)
        elif state == States.CHILD:
            return self.child_tracker.update_data(context, obj)
        elif state == States.BOOL:
            return self.bool_tracker.update_data(context, obj)
        elif state == States.COLL:
            return self.coll_tracker.update_data(context, obj)


    def cycle(self, context, state, step=0):
        if state == States.MOD:
            self.mod_tracker.cycle_mods(context, step)
        elif state == States.CHILD:
            self.child_tracker.cycle_children(context, step)
        elif state == States.BOOL:
            self.bool_tracker.cycle_bools(context, step)
        elif state == States.COLL:
            self.coll_tracker.cycle_coll(context, step)


    def expanded_interface(self, state):
        if state == States.MOD:
            return self.mod_tracker.expanded_interface()
        elif state == States.CHILD:
            return self.child_tracker.expanded_interface()
        elif state == States.BOOL:
            return self.bool_tracker.expanded_interface()
        elif state == States.COLL:
            return self.coll_tracker.expanded_interface()


    def fast_interface(self, state):
        if state == States.MOD:
            return self.mod_tracker.fast_interface()
        elif state == States.CHILD:
            return self.child_tracker.fast_interface()
        elif state == States.BOOL:
            return self.bool_tracker.fast_interface()
        elif state == States.COLL:
            return self.coll_tracker.fast_interface()


    def event_update(self, context, event, obj, state):
        return_code = None
        if state == States.MOD:
            return_code = self.mod_tracker.event_update(context, event, obj)
        elif state == States.CHILD:
            return_code = self.child_tracker.event_update(context, event, obj)
        elif state == States.BOOL:
            return_code = self.bool_tracker.event_update(context, event, obj)
        elif state == States.COLL:
            return_code = self.coll_tracker.event_update(context, event)
        if return_code != None:
            if return_code == 'RESET':
                self.update_obj_data(context, obj, state)


    def exit_tracker(self, context, event, obj, state):
        if state == States.MOD:
            self.mod_tracker.exit_tracker(context, event, obj)
        elif state == States.CHILD:
            self.child_tracker.exit_tracker(context, event, obj)
        elif state == States.BOOL:
            self.bool_tracker.exit_tracker(context, event, obj)
        elif state == States.COLL:
            self.coll_tracker.exit_tracker(context, event)


    def current_mod(self, state):
        if state == States.MOD:
            return self.mod_tracker.current_mod
        elif state == States.CHILD:
            return self.mod_tracker.current_mod
        elif state == States.BOOL:
            return self.bool_tracker.current_mod
        elif state == States.COLL:
            return None


class Auto_Scroll:
    '''Draws text label / Namespace for props'''
    def __init__(self, context):
        self.timer = None
        self.active = False
        self.activated_time = 0
        self.sequance_hold = False
        self.sequance_hold_time = 0

        self.x = context.area.width * .25
        self.y = context.area.height * .75
        self.font_color = addon.preference().color.Hops_UI_text_color
        self.bg_color = addon.preference().color.Hops_UI_cell_background_color
        self.br_color = addon.preference().color.Hops_UI_border_color
        self.size = 16

        dims = get_blf_text_dims("00.00", self.size)
        p = 8 * dpi_factor()
        h = dims[1] + p * 2
        w = dims[0] + p * 2
        x = self.x - p
        y = self.y + h

        # Top Left, Bottom Left, Top Right, Bottom Right
        self.verts = [
            (x, y),
            (x, y - h - p * 2),
            (x + w, y),
            (x + w, y - h - p * 2)]

    def draw(self):
        if not self.active: return

        render_quad(quad=self.verts, color=self.bg_color, bevel_corners=True)
        draw_border_lines(vertices=self.verts, width=1, color=self.br_color, bevel_corners=True)

        counter = abs(addon.preference().property.auto_scroll_time_interval - (time.time() - self.activated_time))
        text = "Start" if self.sequance_hold else f"{counter:.2f}"
        draw_text(text, self.x, self.y, size=self.size, color=self.font_color)


desc = """Ever Scroll\n
LMB - Booleans
LMB + SHIFT - Modifiers
LMB + CTRL - Child Objects
LMB + ALT - Smart Apply
"""


class HOPS_OT_Ever_Scroll(bpy.types.Operator):
    bl_idname = "hops.ever_scroll"
    bl_label = "Ever Scroll"
    bl_description = desc
    bl_options = {"REGISTER", "UNDO", "BLOCKING"}

    entry_state: bpy.props.EnumProperty(
        name="State",
        items=(
            ("NONE",  "NONE",  "NONE"),
            ("BOOL",  "BOOL",  "BOOL"),
            ("MOD",   "MOD",   "MOD"),
            ("CHILD", "CHILD", "CHILD"),
            ("COLL",  "COLL",  "COLL")),
        default="NONE")

    fas_UI: bpy.props.BoolProperty(default=True)


    def invoke(self, context, event):

        # Smart apply option
        if event.alt:
            for object in [o for o in context.selected_objects if o.type == 'MESH']:
                header = "Smart Apply"
                apply_mod(self, object, clear_last=False)
                bpy.ops.hops.display_notification(info='Smart Apply')
                bpy.ops.hops.draw_wire_mesh_launcher('INVOKE_DEFAULT', target='SELECTED')
                self.report({'INFO'}, F'Smart Applied')
                return {'FINISHED'}

        # Props
        self.tracker = Tracker_Man()
        self.state = States.BOOL
        self.sudo_event = Event_Clone(event)
        self.obj = context.active_object
        
        # Entry
        if self.entry_state == 'NONE':
            # Modifiers
            if event.shift:
                self.state = States.MOD
            # Children
            elif event.ctrl:
                self.state = States.CHILD

        elif self.entry_state == 'BOOL':
            self.state = States.BOOL
        elif self.entry_state == 'MOD':
            self.state = States.MOD
        elif self.entry_state == 'CHILD':
            self.state = States.CHILD
        elif self.entry_state == 'COLL':
            self.state = States.COLL

        # Setup
        called_setup = False
        if self.obj:
            if self.obj.type == 'MESH':
                self.tracker.update_obj_data(context, self.obj, self.state)
                called_setup = True

        if called_setup == False:
            bpy.ops.hops.display_notification(info="Select an Object")
            return {'CANCELLED'}
        else:
            self.display_state_notification()

        # Highlight and select bool obj
        if self.state == States.BOOL:
            if self.tracker.bool_tracker.current_mod:
                if self.tracker.bool_tracker.current_mod.object:
                    obj = self.tracker.bool_tracker.current_mod.object
                    bpy.ops.hops.draw_wire_mesh_launcher(object_name=obj.name)
                    obj.hide_viewport = False
                    obj.hide_set(False)

        # Auto Scroll
        self.auto_scroll = Auto_Scroll(context)
        self.draw_handle_2D = bpy.types.SpaceView3D.draw_handler_add(self.safe_draw_2D, (context,), 'WINDOW', 'POST_PIXEL')

        # # Systems
        # if addon.preference().property.bool_scroll_expanded == 'EXPANDED':
        #     self.fas_UI = False
            
        self.master = Master(context=context, custom_preset="Every_Scroll", show_fast_ui=self.fas_UI)
        self.original_tool_shelf, self.original_n_panel = collapse_3D_view_panels()
        self.base_controls = Base_Modal_Controls(context, event)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


    def modal(self, context, event):

        # System Updates
        self.master.receive_event(event=event)
        self.sudo_event.update(event)
        event = self.sudo_event
        self.base_controls.update(context, event)

        # Auto Scroll
        self.auto_scroll_update(context, event)

        # Navigation
        if self.base_controls.pass_through:
            if not self.master.is_mouse_over_ui():
                return {'PASS_THROUGH'}

        # Confirm
        shift_space = event.type == 'SPACE' and event.value == 'PRESS' and event.shift
        if self.base_controls.confirm and not shift_space:
            if not self.master.is_mouse_over_ui() or self.sudo_event.exit_from_interface:
                self.modal_exit(context)
                self.tracker.exit_tracker(context, event, self.obj, self.state)
                return {'FINISHED'}

        # Cancel
        if event.type in {'RIGHTMOUSE', 'ESC'}:
            if not self.master.is_mouse_over_ui():
                self.modal_exit(context)
                bpy.ops.ed.undo_push()
                bpy.ops.ed.undo()
                return {'CANCELLED'}

        # Change State for Expanded
        if not self.master.should_build_fast_ui():
            if event.type == 'TAB' and event.value == 'PRESS':
                self.toggle_state(context)
        # Change State for FAS (Also)
        else:
            if event.type == 'TAB' and event.value == 'PRESS' and event.shift:
                self.toggle_state(context)

        if event.type == 'Z' and event.value == 'PRESS':
            self.obj.show_wire = not self.obj.show_wire
            self.obj.show_all_edges = not self.obj.show_all_edges

        # Scrolling
        if self.base_controls.scroll and not self.auto_scroll.active:
            if not self.master.is_mouse_over_ui():
                if not event.shift and not event.ctrl:
                    step = self.base_controls.scroll
                    self.tracker.cycle(context, self.state, step)

        # Tracker modal controls
        self.tracker.event_update(context, event, self.obj, self.state)

        self.sudo_event.exit_from_interface = False
        
        self.draw_window(context)
        context.area.tag_redraw()
        return {'RUNNING_MODAL'}


    def draw_window(self, context):

        self.master.setup()

        #--- FAS ---#
        if self.master.should_build_fast_ui():

            # Active mods
            active_mod = ""
            mod = self.tracker.current_mod(self.state)
            if mod:
                active_mod = mod.name

            # Main
            win_list = []
            if self.state == States.MOD:
                win_list.append("Modifiers Scroll" if addon.preference().ui.Hops_modal_fast_ui_loc_options == 1 else "ModScroll")
            elif self.state == States.CHILD:
                win_list.append("Child Scroll" if addon.preference().ui.Hops_modal_fast_ui_loc_options == 1 else "Children")
            elif self.state == States.BOOL:
                win_list.append("Bool Scroll" if addon.preference().ui.Hops_modal_fast_ui_loc_options == 1 else "BoolScroll")
            elif self.state == States.COLL:
                win_list.append("Coll Scroll" if addon.preference().ui.Hops_modal_fast_ui_loc_options == 1 else "CollScroll")

            data = self.tracker.fast_interface(self.state)
            if data:
                for entry in data:
                    win_list.append(entry)

            # Help
            help_items = {"GLOBAL" : [], "STANDARD" : []}

            help_items["GLOBAL"] = [
                ("M", "Toggle mods list"),
                ("H", "Toggle help"),
                ("~", "Toggle UI Display Type"),
                ("O", "Toggle viewport rendering")]

            help_items["STANDARD"] = [
                ("Shift TAB", "Change Mode"),
                ("TAB",       "Open Expanded"),
                ("Ctrl S",    "Toggle Auto Scroll")]
            
            h_append = help_items["STANDARD"].append

            if self.auto_scroll.active:
                h_append(("Scroll", "Control Auto Scroll Speed"))

            if self.state == States.MOD:
                h_append(["W",            "Show wire fade for object"])
                h_append(["A",            "Toggle modifier visibility"])
                h_append(["Shift Space",  "Toggle AutoScroll"])
                h_append(["Shift A",      "Toggle modifier object"])
                h_append(["F",            "Apply modifier to mesh"])
                h_append(["Shift F",      "Apply modifiers up to current"])
                h_append(["Shift R",      "Toggle (All) Show Render"])
                h_append(["R",            "Toggle (Current) Show Render"])
                h_append(["L",            "Toggle Looping for scroll"])
                h_append(["Shift Scroll", "Move active modifier"])
                h_append(["Ctrl LMB",     "Apply visible mods"])
                h_append(["Shift LMB",    "Apply visible mods on Duplicate"])
                
            elif self.state == States.CHILD:
                h_append(["W",        "Show wire fade for object"])
                h_append(["Shift V",  "Toggle all visible"])
                h_append(["V",        "Toggle current visible"])
                h_append(["D",        "Delete Child"])
                h_append(["B",        "Toggle all booleans"])
                h_append(["A",        "Add / Remove from visibility set"])

            elif self.state == States.BOOL:
                h_append(["W",            "Show wire fade for object"])
                h_append(["A",            "Add / Remove bool to visibility set"])
                h_append(["Shift Space ", "Toggle AutoScroll"])
                h_append(["F",            "Apply modifier to mesh"])
                h_append(["R",            "Start Recursive Scroll"])
                h_append(["Shift R",      "Stop Recursive Scroll"])
                h_append(["S",            "Show Recursive Booleans"])
                #h_append(["Shift F",      "Apply modifiers up to current"])
                h_append(["V",            "Toggle modifier visibility"])
                h_append(["Shift V",      "Toggle all modifier visibility"])
                h_append(["Shift Scroll", "Move modifiers"])
                #h_append(["Ctrl LMB",     "Apply visible mods"])
                #h_append(["Shift LMB",    "Apply visible mods on Duplicated"])

            help_items["STANDARD"].reverse()

            # Mods
            mods_list = []
            if self.state == States.CHILD:
                active_mod = self.tracker.child_tracker.last_affected
                for obj in reversed(self.tracker.child_tracker.children):
                    mods_list.append([obj.name, not obj.hide_get()])
            elif self.state == States.BOOL:
                if self.tracker.bool_tracker.recursive_active:
                    mods_list = get_mods_list(mods=[i[0] for i in self.tracker.bool_tracker.r_mods])
                    active_mod = str(len(self.tracker.bool_tracker.r_mods) - self.tracker.bool_tracker.r_index - 1)
                else:
                    mods_list = get_mods_list(mods=self.obj.modifiers)
            else:
                mods_list = get_mods_list(mods=self.obj.modifiers)

            self.master.receive_fast_ui(win_list=win_list, help_list=help_items, image="Booleans", mods_list=mods_list, active_mod_name=active_mod)
        
        #--- EXPANDED ---#
        else:
            # Main
            window_name = ""
            main_window = self.tracker.expanded_interface(self.state)

            if self.state == States.MOD:
                window_name = "Modifiers"
            elif self.state == States.CHILD:
                window_name = "Children"
            elif self.state == States.BOOL:
                window_name = "Booleans"
            elif self.state == States.COLL:
                window_name = "Collections"

            play = True if self.auto_scroll.active else False
            header_tab = (self.sudo_event.alter_event, ('TAB', 'PRESS'), play, self.sudo_event.alter_event, ('SPACE', 'PRESS', [('shift', True)]))
            self.master.receive_main(win_dict=main_window, window_name=window_name, win_form=header_tab)

            # Help
            hot_keys_dict = {}

            hot_keys_dict["Shift Space"] = ["Toggle AutoScroll", self.sudo_event.alter_event, ('SPACE', 'PRESS', [('shift', True)])]
            
            if self.state == States.MOD:
                hot_keys_dict["W"] = ["Show wire fade for object", self.sudo_event.alter_event, ('W', 'PRESS')]
                hot_keys_dict["A"] = ["Toggle modifier visibility", self.sudo_event.alter_event, ('A', 'PRESS')]
                hot_keys_dict["Shift A"] = ["Toggle modifier object", self.sudo_event.alter_event, ('A', 'PRESS', [('shift', True)])]
                hot_keys_dict["F"] = ["Apply modifier to mesh", self.sudo_event.alter_event, ('F', 'PRESS')]
                hot_keys_dict["Shift F"] = ["Apply modifiers up to current", self.sudo_event.alter_event, ('F', 'PRESS', [('shift', True)])]
                hot_keys_dict["Shift R"] = ["Toggle (All) Show Render", self.sudo_event.alter_event, ('R', 'PRESS', [('shift', True)])]
                hot_keys_dict["R"] = ["Toggle (Current) Show Render", self.sudo_event.alter_event, ('R', 'PRESS')]
                hot_keys_dict["L"] = ["Toggle Looping for scroll", self.sudo_event.alter_event, ('L', 'PRESS')]
                hot_keys_dict["Shift Scroll"] = ["Move modifiers"]
                hot_keys_dict["Ctrl LMB"] = ["Apply visible mods", self.sudo_event.alter_event, ('LEFTMOUSE', 'PRESS', [('ctrl', True)], True)]
                hot_keys_dict["Shift LMB"] = ["Apply visible mods on Duplicated", self.sudo_event.alter_event, ('LEFTMOUSE', 'PRESS', [('shift', True)], True)]
                
            elif self.state == States.CHILD:
                hot_keys_dict["W"] = ["Show wire fade for object", self.sudo_event.alter_event, ('W', 'PRESS')]
                hot_keys_dict["Shift V"] = ["Toggle all visible", self.sudo_event.alter_event, ('V', 'PRESS', [('shift', True)])]
                hot_keys_dict["V"] = ["Toggle current visible", self.sudo_event.alter_event, ('V', 'PRESS')]
                hot_keys_dict["D"] = ["Delete Child", self.sudo_event.alter_event, ('D', 'PRESS')]
                hot_keys_dict["B"] = ["Toggle all booleans", self.sudo_event.alter_event, ('B', 'PRESS')]
                hot_keys_dict["A"] = ["Add / Remove from visibility set", self.sudo_event.alter_event, ('A', 'PRESS')]

            elif self.state == States.BOOL:
                hot_keys_dict["W"] = ["Show wire fade for object", self.sudo_event.alter_event, ('W', 'PRESS')]
                hot_keys_dict["A"] = ["Add / Remove bool to visibility set", self.sudo_event.alter_event, ('A', 'PRESS')]
                hot_keys_dict["F"] = ["Apply modifier to mesh", self.sudo_event.alter_event, ('F', 'PRESS')]
                hot_keys_dict["R"] = ["Start Recursive Scroll", self.sudo_event.alter_event, ('R', 'PRESS')]
                hot_keys_dict["Shift R"] = ["Stop Recursive Scroll", self.sudo_event.alter_event, ('R', 'PRESS', [('shift', True)])]
                hot_keys_dict["S"] = ["Show Recursive Booleans", self.sudo_event.alter_event, ('S', 'PRESS')]
                #hot_keys_dict["Shift F"] = ["Apply modifiers up to current", self.sudo_event.alter_event, ('F', 'PRESS', [('shift', True)])]
                hot_keys_dict["V"] = ["Toggle current modifier visibility", self.sudo_event.alter_event, ('V', 'PRESS')]
                hot_keys_dict["Shift V"] = ["Toggle all modifier visibility", self.sudo_event.alter_event, ('V', 'PRESS', [('shift', True)])]
                hot_keys_dict["Shift Scroll"] = ["Move modifiers"]
                #hot_keys_dict["Ctrl LMB"] = ["Apply visible mods", self.sudo_event.alter_event, ('LEFTMOUSE', 'PRESS', [('ctrl', True)], True)]
                #hot_keys_dict["Shift LMB"] = ["Apply visible mods on Duplicate", self.sudo_event.alter_event, ('LEFTMOUSE', 'PRESS', [('shift', True)], True)]

            elif self.state == States.COLL:
                pass

            hot_keys_dict["Z"] = ["Toggle wire display", self.sudo_event.alter_event, ('Z', 'PRESS')]
            hot_keys_dict["TAB"] = ["Switch the scroll type", self.sudo_event.alter_event, ('TAB', 'PRESS')]

            self.master.receive_help(hot_keys_dict=hot_keys_dict)
            
        self.master.finished()

    # --- UTILS --- #

    def toggle_state(self, context):
        if self.state == States.BOOL:
            self.state = States.MOD

        elif self.state == States.MOD:
            self.state = States.CHILD

        elif self.state == States.CHILD:
            self.state = States.BOOL

        # TODO: This section enables / disables Collection Scroll
        
        # if self.state == States.BOOL:
        #     self.state = States.MOD

        # elif self.state == States.MOD:
        #     self.state = States.CHILD

        # elif self.state == States.CHILD:
        #     self.state = States.COLL

        # elif self.state == States.COLL:
        #     self.state = States.BOOL

        self.tracker.update_obj_data(context, self.obj, self.state)
        self.display_state_notification()


    def display_state_notification(self):
        if self.state == States.CHILD:
            bpy.ops.hops.display_notification(info="Children")
        elif self.state == States.BOOL:
            bpy.ops.hops.display_notification(info="Booleans")
        elif self.state == States.MOD:
            bpy.ops.hops.display_notification(info="Modifiers")
        elif self.state == States.COLL:
            bpy.ops.hops.display_notification(info="Collections")


    def modal_exit(self, context):
        # Props
        self.fas_UI = True
        self.entry_state = 'NONE'
        # Auto Scroll
        if self.auto_scroll.timer: context.window_manager.event_timer_remove(self.auto_scroll.timer)
        self.remove_shaders()
        # UI
        self.master.run_fade()
        collapse_3D_view_panels(self.original_tool_shelf, self.original_n_panel)
        context.area.tag_redraw()


    def remove_shaders(self):
        if self.draw_handle_2D:
            self.draw_handle_2D = bpy.types.SpaceView3D.draw_handler_remove(self.draw_handle_2D, "WINDOW")

    # --- Auto Scroll --- #

    def auto_scroll_update(self, context, event):

        s_key = event.type == 'S' and event.value == 'PRESS' and event.ctrl and not event.shift
        space_key = event.type == 'SPACE' and event.value == 'PRESS' and event.shift

        if s_key or space_key:
            self.auto_scroll.active = not self.auto_scroll.active
            self.tracker.mod_tracker.looping = True
            self.tracker.child_tracker.looping = True

            if self.auto_scroll.active:
                self.auto_scroll.timer = context.window_manager.event_timer_add(0.1, window=context.window)
                self.auto_scroll.activated_time = time.time()
            else:
                if self.auto_scroll.timer:
                    context.window_manager.event_timer_remove(self.auto_scroll.timer)
                    self.auto_scroll.timer = None

        if not self.auto_scroll.active: return

        if self.auto_scroll.sequance_hold:
            if time.time() - self.auto_scroll.sequance_hold_time > 1:
                self.auto_scroll.activated_time = time.time()
                self.auto_scroll.sequance_hold = False
            else: return

        if time.time() - self.auto_scroll.activated_time > addon.preference().property.auto_scroll_time_interval:
            self.auto_scroll.activated_time = time.time()

            # Make both left and right scroll same direction
            step = 1
            if addon.preference().property.modal_handedness == 'RIGHT': step *= -1
            self.tracker.cycle(context, self.state, step)

        # Pause looping on sequence restart
        if self.auto_scroll.sequance_hold == False:

            if self.state == States.MOD:
                self.auto_scroll.sequance_hold = self.tracker.mod_tracker.auto_scroll_sequance_begin
                self.auto_scroll.sequance_hold_time = time.time()
                self.tracker.mod_tracker.auto_scroll_sequance_begin = False

            elif self.state == States.CHILD:
                self.auto_scroll.sequance_hold = self.tracker.child_tracker.auto_scroll_sequance_begin
                self.auto_scroll.sequance_hold_time = time.time()
                self.tracker.child_tracker.auto_scroll_sequance_begin = False

            elif self.state == States.BOOL:
                self.auto_scroll.sequance_hold = self.tracker.bool_tracker.auto_scroll_sequance_begin
                self.auto_scroll.sequance_hold_time = time.time()
                self.tracker.bool_tracker.auto_scroll_sequance_begin = False

        # Adjust speed
        if event.type in {'WHEELDOWNMOUSE', 'LEFT_BRACKET'} and event.value == 'PRESS':
            self.auto_scroll.activated_time = time.time()
            addon.preference().property.auto_scroll_time_interval -= .125
            if addon.preference().property.auto_scroll_time_interval < .1:
                addon.preference().property.auto_scroll_time_interval = .25

            bpy.ops.hops.display_notification(info=f"Interval time set: {addon.preference().property.auto_scroll_time_interval:.3f}")

        elif event.type in {'WHEELUPMOUSE', 'RIGHT_BRACKET'} and event.value == 'PRESS':
            self.auto_scroll.activated_time = time.time()
            addon.preference().property.auto_scroll_time_interval += .125
            if addon.preference().property.auto_scroll_time_interval > 60:
                addon.preference().property.auto_scroll_time_interval = 60

            bpy.ops.hops.display_notification(info=f"Interval time set: {addon.preference().property.auto_scroll_time_interval:.3f}")


    def safe_draw_2D(self, context):
        method_handler(self.draw_shader_2D,
            arguments = (context,),
            identifier = 'Modal Shader 2D',
            exit_method = self.remove_shaders)


    def draw_shader_2D(self, context):
        self.auto_scroll.draw()