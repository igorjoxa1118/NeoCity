import bpy
from .... utility import addon
from .... utility.base_modal_controls import increment_maps, decrement_maps

from . import States, Auto_Scroll, update_local_view, mods_exit_options, turn_on_coll, get_mod_object, get_node_graph_objects
from .... utility.collections import unhide_layers

class Mod_Tracker:
    def __init__(self):
        self.mods = []
        self.index = 0
        self.just_reset = False
        self.last_affected = ""
        self.current_mod = None
        self.looping = False
        self.auto_scroll_sequance_begin = False
        self.mods_exclude = set()
        self.active_obj = None

        self.help = [
        ("W",            "Show wire fade for object"),
        ("A",            "Toggle modifier visibility"),
        ("Shift A",      "Toggle modifier object"),
        ("F",            "Apply modifier to mesh"),
        ("Shift F",      "Apply modifiers up to current"),
        ("Shift R",      "Toggle (All) Show Render"),
        ("R",            "Toggle (Current) Show Render"),
        ("L",            "Toggle Looping for scroll"),
        ("Shift Scroll", "Move active modifier"),
        ("Ctrl LMB",     "Apply visible mods"),
        ("Shift LMB",    "Apply visible mods on Duplicate")]


    def update_data(self, context, obj):
        self.index = 0
        self.just_reset = True
        self.mods = []

        if obj is not self.active_obj:
            self.mods_exclude = set()

            for mod in obj.modifiers:
                # exclude initially unrendered mods form cycling
                if mod.show_render:
                    self.mods.append(mod)
                else:
                    self.mods_exclude.add(mod.name)
        else:
            for mod in obj.modifiers:
                if mod.name not in self.mods_exclude:
                    self.mods.append(mod)

        self.active_obj = obj

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

            if mod.type == 'NODES':
                objs.extend(get_node_graph_objects(mod))

        filtered = []

        colls = [o.users_collection[0] for o in objs if len(o.users_collection) > 0]
        for obj in objs:
            if not obj.users_collection: continue
            if obj.users_collection[0] != colls:
                filtered.append(obj)

        cache = set()
        for obj in filtered:
            unhide_layers(obj)

            for coll in obj.users_collection:
                if coll != main_coll:
                    if coll in cache: continue
                    cache.add(coll)

                for object in coll.objects:
                    if object.display_type == 'WIRE':
                        if object.hide_viewport:
                            object.hide_viewport = False
                        if not object.hide_get():
                            object.hide_set(True)

        for mod in self.mods:
            mod.show_viewport = False


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

    def event_update(self, op, context, event, obj):

        # Validate
        if not self.mods_valid(): return

        # Visible toggle
        if event.type == 'A' and event.value == 'PRESS':
            if event.shift:
                self.reveal_mod_object(context)
            else:
                self.toggle_visible()

        # Apply mod
        elif event.type == 'F' and event.value == 'PRESS':
            if event.shift:
                self.apply_to(obj)
            else:
                self.apply_current(obj)

            self.update_data(context, obj)

            if not self.mods: self.current_mod = None

            op.alter_form_layout(context)

        # Render
        elif event.type == 'R' and event.value == 'PRESS':
            if event.shift:
                self.toggle_render_for_all()
            else:
                self.toggle_render_for_active()

        # Loop Scroll
        elif event.type == 'L' and event.value == 'PRESS':
            self.toggle_looping()

        # Wire display current
        elif event.type == 'W' and event.value == 'PRESS':
            self.wire_display_current()

        # Shift mods
        if event.shift and event.value == 'PRESS':
            if event.type in increment_maps:
                self.move_mod(obj, direction=1)
                op.alter_form_layout(context)
            elif event.type in decrement_maps:
                self.move_mod(obj, direction=-1)
                op.alter_form_layout(context)


    def toggle_looping(self):
        self.looping = not self.looping
        msg = "Looping : On" if self.looping else "Looping : Off"
        bpy.ops.hops.display_notification(info=msg)


    def toggle_visible(self):
        if self.current_mod:
            self.current_mod.show_viewport = not self.current_mod.show_viewport


    def reveal_mod_object(self, context):
        if not self.current_mod: return

        def reveal(obj):

            if context.space_data.local_view:

                objs = []

                if obj.hide_get() == True:
                    objs.append(obj)
                elif obj.visible_get() == False:
                    objs.append(obj)
                else:
                    obj.hide_set(True)

                for o in context.visible_objects:
                    if o not in objs:
                        objs.append(o)

                # Come out of Local view
                bpy.ops.view3d.localview(frame_selected=False)
                for o in objs:
                    o.hide_set(False)
                    o.select_set(True)
                # Go back into local view
                bpy.ops.view3d.localview(frame_selected=False)

                bpy.ops.hops.draw_wire_mesh_launcher(object_name=obj.name, omit_subd=True)

            else:
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

        elif hasattr(self.current_mod, 'offset_object'):
            if self.current_mod.offset_object:
                reveal(self.current_mod.offset_object)

        elif self.current_mod.type == 'NODES':
            objs = get_node_graph_objects(self.current_mod)
            if not objs: return

            # Local
            if context.space_data.local_view:

                # Toggle Logic
                test_obj = objs[0]
                show = False
                if test_obj.hide_get() == True:
                    show = True
                elif test_obj.visible_get() == False:
                    show = True

                reveal_objs = []
                for o in context.visible_objects:
                    if show == False and o in objs:
                        continue
                    reveal_objs.append(o)

                if show:
                    for o in objs:
                        if o not in reveal_objs:
                            reveal_objs.append(o)
                else:
                    for o in objs:
                        o.hide_set(True)
                        o.select_set(False)
                        if o in reveal_objs:
                            reveal_objs.remove(o)

                bpy.ops.view3d.localview(frame_selected=False)
                for o in reveal_objs:
                    o.hide_set(False)
                    o.select_set(True)
                bpy.ops.view3d.localview(frame_selected=False)

            # Standard
            else:
                for obj in objs:
                    if obj.hide_get():
                        obj.hide_set(False)
                    else:
                        obj.hide_set(True)


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
            if turn_on:mod.show_render = True
            else: mod.show_render = False

        msg = "On" if turn_on else "Off"
        bpy.ops.hops.display_notification(info=f"Render : {msg}")


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


    def exit_tracker(self, context, event, obj, force_ctrl=False, force_shift=False):
        mods_exit_options(context, event, obj, force_ctrl=force_ctrl, force_shift=force_shift)

    # --- FORM --- #

    def make_selected_active(self, context, index=0, reveal_object=False):
        if index > len(self.mods) - 1:
            index = len(self.mods) - 1
        if index < 0:
            index = 0

        self.index = index
        self.current_mod = self.mods[self.index]
        self.last_affected = self.current_mod.name
        if self.current_mod.type == 'BOOLEAN':
            if self.current_mod.object:
                bpy.ops.hops.draw_wire_mesh_launcher(object_name=self.current_mod.object.name)

        if reveal_object:
            self.reveal_mod_object(context)


    def highlight(self, index=None):
        if index == None: return
        if index == self.index: return True
        return False


    def mod_toggle_view(self, obj, mod_name=''):
        if mod_name not in obj.modifiers: return
        mod = obj.modifiers[mod_name]
        mod.show_viewport = not mod.show_viewport


    def mod_show_view_highlight(self, obj, mod_name=''):
        if mod_name not in obj.modifiers: return False
        mod = obj.modifiers[mod_name]
        if mod.show_viewport: return False
        return True


    def mod_toggle_render(self, obj, mod_name=''):
        if mod_name not in obj.modifiers: return
        mod = obj.modifiers[mod_name]
        mod.show_render = not mod.show_render


    def mod_show_render_highlight(self, obj, mod_name=''):
        if mod_name not in obj.modifiers: return False
        mod = obj.modifiers[mod_name]
        if mod.show_render: return False
        return True


    def apply_mods_form(self, context, op, mod_name='', up_to=False):

        obj = op.obj
        if mod_name not in obj.modifiers: return
        mod = obj.modifiers[mod_name]
        apply_mod = mod

        if up_to:
            count = 0
            for mod in obj.modifiers:
                count += 1
                should_break = True if mod.name == apply_mod.name else False
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
                name = apply_mod.name
                bpy.ops.object.modifier_apply(modifier=apply_mod.name)
                bpy.ops.hops.display_notification(info=f'Applied : {name}')
            except:
                obj.modifiers.remove(apply_mod)

        self.update_data(context, obj)
        op.alter_form_layout(context)


    def isolate_mod(self, mod):
        self.current_mod = mod

        # Determine if it should enable visibility up to current
        enable_up_to = True
        for mod in self.mods:
            if mod == self.current_mod:
                break
            if mod.show_viewport:
                enable_up_to = False
        # Enable visibilty up to current
        if enable_up_to:
            for mod in self.mods:
                if mod == self.current_mod:
                    break
                mod.show_viewport = True
        # Only isolate the current mod
        else:
            for mod in self.mods:
                mod.show_viewport = False
        # Enable the current
        self.current_mod.show_viewport = True
        # Set the current index
        if self.current_mod in self.mods:
            self.index = self.mods.index(self.current_mod)
        else:
            self.index = 0

    # --- FAS --- #

    def FAS_data(self):
        data = ['Modifier']
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