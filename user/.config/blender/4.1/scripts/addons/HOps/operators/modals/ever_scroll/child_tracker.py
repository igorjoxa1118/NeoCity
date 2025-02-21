import bpy
from .... utility import addon, operator_override
from .... utility.base_modal_controls import increment_maps, decrement_maps
from .... utility.collections import unhide_layers
from . import States, Auto_Scroll, update_local_view, turn_on_coll


class Child_Tracker:
    def __init__(self):
        self.children = []
        self.tracked = []
        self.index = 0
        self.last_affected = ""
        self.current_obj = None
        self.looping = False
        self.auto_scroll_sequance_begin = False

        self.help = [
        ("W",        "Show wire fade for object"),
        ("Shift V",  "Toggle all visible"),
        ("V",        "Toggle current visible"),
        ("D",        "Delete Child"),
        ("B",        "Toggle all booleans"),
        ("A",        "Add / Remove from visibility set")]


    @staticmethod
    def child_count(obj):
        return len(obj.children)


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
        if context.space_data.local_view:
            override = {'selected_objects': self.children + context.visible_objects[:]}
            bpy.ops.view3d.localview(frame_selected=False)
            operator_override(context, bpy.ops.view3d.localview, override, frame_selected=False)


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

    def event_update(self, op, context, event, obj):

        # Delete object
        if event.type == 'D' and event.value == 'PRESS':
            self.delete_obj(context, op)

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


    def delete_obj(self, context, op):
        if self.current_obj:
            name = self.current_obj.name
            self.current_obj.parent = None
            bpy.data.objects.remove(self.current_obj)

            bpy.ops.hops.display_notification(info=f"Deleted : {name}")

            self.update_data(context, op.obj)
            op.alter_form_layout(context)


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


    def exit_tracker(self, context):
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

    # --- FORM --- #

    def highlight(self, index=None):
        if index == None: return
        if index == self.index: return True
        return False


    def make_selected_active(self, index=0):
        if index < len(self.children):
            if index < 0: index = 0
            self.index = index
            self.current_obj = self.children[self.index]
            self.last_affected = self.current_obj.name
            self.current_obj.hide_set(False)
            self.current_obj.select_set(True)
            bpy.ops.hops.draw_wire_mesh_launcher(object_name=self.current_obj.name)


    def hide_toggle(self, obj):
        hide = not obj.hide_get()
        obj.hide_set(hide)


    def hide_highlight(self, obj=None):
        if not obj: return
        return obj.hide_get()


    def tracked_highlight(self, obj=None):
        if not obj: return
        return obj in self.tracked

    # --- FAS --- #

    def FAS_data(self):
        data = ['Child']
        if self.current_obj:
            data.append(self.current_obj.name)
            data.append(self.index + 1)
            data.append(len(self.children))
        return data

