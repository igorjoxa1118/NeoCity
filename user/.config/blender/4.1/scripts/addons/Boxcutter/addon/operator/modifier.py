import bpy


from bpy.types import Operator
from bpy.props import StringProperty, BoolProperty

from ... utility import modifier


class BC_OT_modifier_remove(Operator):
    bl_idname = 'bc.modifier_remove'
    bl_label = 'Remove Modifier'
    bl_options = {'INTERNAL'}

    object: StringProperty()
    modifier: StringProperty()


    def execute(self, context):
        bc = context.scene.bc

        obj = bpy.data.objects[self.object]

        if bc.running:
            if obj == bc.shape:
                if bc.shape.modifiers[self.modifier].type == bc.start_operation:
                    bc.start_operation = 'NONE'

        obj.modifiers.remove(obj.modifiers[self.modifier])

        if self.modifier.startswith("Quad"):
            bc.q_bevel = False

        return {'FINISHED'}


class BC_OT_smart_apply(Operator):
    bl_idname = 'bc.smart_apply'
    bl_label = 'Smart Apply'
    bl_description = ('\n Applies Boolean Modifiers.\n\n'
                      ' Shift - Loose Boolean Cleanup')
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'REGISTER', 'UNDO'}

    use_loose: BoolProperty(
        name = 'Loose Boolean Cleanup',
        description = 'Cleanup booleans that do not effect the current visual geometry',
        default = True)


    @classmethod
    def poll(cls, context):
        return context.selected_objects


    def invoke(self, context, event):
        targets = []
        modifiers = {}

        cutters = []

        bool_mods = lambda mods: [mod for mod in mods if mod.type == 'BOOLEAN' and mod.object]

        mode = context.active_object.mode

        if mode == 'EDIT':
            bpy.ops.object.mode_set(mode='OBJECT')


        self.loose = event.shift and self.use_loose

        if self.loose:
            # Remove unused cutters
            rounded = lambda d: sum((round(d.x, 6), round(d.y, 6), round(d.z, 6)))
            counted = lambda d: sum((len(d.vertices), len(d.polygons), len(d.edges)))
            for obj in context.selected_objects:
                if obj.type != 'MESH':
                    continue

                evld = obj.evaluated_get(context.evaluated_depsgraph_get())
                state = counted(evld.data) + rounded(evld.dimensions) + sum((rounded(p.center) for p in evld.data.polygons))

                for mod in obj.modifiers[:]:
                    if mod.type != 'BOOLEAN' or not mod.show_viewport:
                        continue

                    mod.show_viewport = False

                    context.view_layer.update()

                    evld = obj.evaluated_get(context.evaluated_depsgraph_get())

                    if state != counted(evld.data) + rounded(evld.dimensions) + sum((rounded(p.center) for p in evld.data.polygons)):
                        mod.show_viewport = True

                        continue

                    obj.modifiers.remove(mod)

            if mode == 'EDIT':
                bpy.ops.object.mode_set(mode='EDIT')

            return {'FINISHED'}


        def collect_target(obj, mod):
            if obj not in targets:
                targets.append(obj)

            if obj.name not in modifiers:
                modifiers[obj.name] = [mod]

            elif obj.name in modifiers and mod not in modifiers[obj.name]:
                modifiers[obj.name].append(mod)


        def collect(obj, mod):
            collect_target(obj, mod)

            if mod.object not in cutters:
                cutters.append(mod.object)


        for obj in context.visible_objects:
            for mod in bool_mods(obj.modifiers):
                if mod.object.select_get():
                    collect(obj, mod)

        if not cutters:
            for obj in context.selected_objects:
                for mod in bool_mods(obj.modifiers):
                    collect(obj, mod)

        if True in [obj.select_get() for obj in targets]:
            for obj in context.visible_objects:
                for mod in bool_mods(obj.modifiers):
                    if mod.object in cutters and not obj.select_get():
                        cutters.remove(mod.object)

                if obj in targets and not obj.select_get():
                    targets.remove(obj)

        for obj in targets:
            obj.select_set(True)
            context.view_layer.objects.active = obj
            modifier.apply(obj, modifiers=modifiers[obj.name])

        for obj in cutters:
            bpy.data.meshes.remove(obj.data)

        if mode == 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT')

        del targets
        del modifiers
        del cutters

        return {'FINISHED'}
