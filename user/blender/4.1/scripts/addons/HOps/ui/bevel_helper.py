import bpy
from .. icons import get_icon_id, icons
from math import radians, degrees
from .. utility import addon
from .. utils.blender_ui import get_dpi_factor
from .. utility.collections import turn_on_parent_collections
from bpy.props import BoolProperty, StringProperty

presets = {
    "Width": [0.01, 0.02, 0.1],
    "Segments": [1, 3, 4, 6, 12],
    "Profile": [0.3, 0.5, 0.7],
    "Angle": [30, 45, 60]}


class HOPS_OT_bevel_helper(bpy.types.Operator):
    bl_idname = 'hops.bevel_helper'
    bl_description = 'Display HOps Bevel Helper'
    bl_label = 'HOps Bevel Helper'

    label: bool = False

    @classmethod
    def poll(cls, context):
        return any(o.type in {'MESH'} for o in context.selected_objects)

    def check(self, context):
        return True

    def invoke(self, context, event):
        preference = addon.preference().ui

        for obj in context.selected_objects:
            for mod in obj.modifiers:
                if mod.type in {'BEVEL', 'BOOLEAN'}:
                    mod.show_expanded = False
                    if mod.type == 'BOOLEAN':
                        if mod.object:
                            current_view = mod.object.hide_viewport
                            mod.object.hops.is_user_triggered = False
                            mod.object.hops.bevel_helper_hide = current_view
                            if context.space_data.local_view:  # Check if we are in local view
                                mod.object.local_view_set(context.space_data, True)

        if preference.use_bevel_helper_popup:
            self.label = True
            return context.window_manager.invoke_popup(self, width=int(240 * get_dpi_factor(force=False)))
        else:
            return context.window_manager.invoke_props_dialog(self, width=int(240 * get_dpi_factor(force=False)))

    def execute(self, context):
        return {'FINISHED'}

    def draw(self, context):
        preference = addon.preference().ui
        layout = self.layout

        if self.label:
            layout.label(text='HOps Bevel Helper')

        row = layout.row(align=True)
        row.prop(preference, "show_bevel_in_bevel_helper", toggle=True, icon='MOD_BEVEL')
        row.prop(preference, "show_boolean_in_bevel_helper", toggle=True, icon='MOD_BOOLEAN')

        for obj in context.selected_objects:
            if obj.type == 'MESH':
                bevelmods = [modifier for modifier in obj.modifiers if modifier.type == "BEVEL"]
                booleanmods = [modifier for modifier in obj.modifiers if modifier.type == "BOOLEAN"]

                if bevelmods or booleanmods:
                    layout.label(text=obj.name, icon='OBJECT_DATA')

                if preference.show_bevel_in_bevel_helper:
                    if bevelmods:
                        for mod in bevelmods:
                            self.draw_bevel(context, obj, mod)

                if preference.show_boolean_in_bevel_helper:
                    if booleanmods:
                        layout.separator()
                        # Draw toggle all buttons
                        split = layout.split(factor=0.5)
                        row = split.row(align=True)

                        row.operator('hops.bevel_helper_hide_all_bools', text='Show All', icon='HIDE_OFF').obj_name = obj.name
                        if bpy.app.version > (2, 90, 0):
                            split = split.split(factor=0.3)
                            row = split.row(align=True)
                            # row.alignment = 'LEFT'
                            fast = row.operator('hops.bevel_helper_boolean_solver', text='F')
                            fast.obj_name = obj.name
                            fast.solver = 'FAST'
                            exact = row.operator('hops.bevel_helper_boolean_solver', text='E')
                            exact.obj_name = obj.name
                            exact.solver = 'EXACT'

                        row = split.row(align=True)
                        # row.alignment = 'RIGHT'
                        row.operator('hops.bevel_helper_unhide_all_bools', text='Hide All', icon='HIDE_ON').obj_name = obj.name

                        for mod in booleanmods:
                            self.draw_boolean(context, obj, mod)

                        layout.separator()

    def draw_boolean(self, context, obj, mod):
        layout = self.layout
        split = layout.split(factor=0.5)

        row = split.row()
        row.alignment = 'LEFT'

        # row.prop(mod, 'show_expanded', text='', emboss=False)
        row.alert = True
        if mod.object:
            name = mod.object.name
            row.alert = False

        row.separator()
        icon = get_icon_id("orange") if mod.operation == 'INTERSECT' else get_icon_id("green") if mod.operation == 'UNION' else get_icon_id("red")

        swapoperator = row.operator('hops.bevel_helper_bool_swap', text='', icon_value=icon, emboss=False)
        swapoperator.obj_name = obj.name
        swapoperator.mod_name = mod.name
        row.prop(mod, 'name', text='', emboss=False)
        row.separator()
        row.prop(mod, 'show_viewport', text='', emboss=False)

        if bpy.app.version > (2, 90, 0):
            split = split.row(align=True).split(factor=0.3)
            row = split.row(align=True)
            row.alignment = 'LEFT'
            row.prop(mod, 'solver', text='', emboss=True)

        row = split.row(align=True)
        row.alignment = 'RIGHT'


        if mod.object:
            row.label(text=name)
            row.separator()
            icon = 'HIDE_ON' if mod.object.hops.bevel_helper_hide else 'HIDE_OFF'
            row.prop(mod.object.hops, 'bevel_helper_hide', text='', icon=icon, emboss=False)
            row.separator()
            if mod.object.hops.bevel_helper_hide:
                row.label(text='')
            else:
                icon = 'RESTRICT_SELECT_OFF' if mod.object.select_get() else 'RESTRICT_SELECT_ON'
                selectoperator = row.operator('hops.bevel_helper_bool_select', text='', icon=icon, emboss=False)
                selectoperator.obj_name = obj.name
                selectoperator.mod_name = mod.name
    

        # column.separator()

    def draw_bevel(self, context, obj, mod):
        preference = addon.preference().property
        layout = self.layout

        split = layout.split(factor=0.5)

        row = split.row()
        row.alignment = 'LEFT'
        row.prop(mod, 'show_expanded', text='', emboss=False)
        row.prop(mod, 'name', text='', icon='MOD_BEVEL', emboss=False)

        row = split.row(align=True)
        row.alignment = 'RIGHT'
        # if index == 0:
        row.prop(preference, 'show_presets', text='', icon=F'RESTRICT_SELECT_O{"FF" if preference.show_presets else "N"}', emboss=False)
        row.prop(mod, 'show_viewport', text='', emboss=False)

        split = layout.split(factor=0.1)
        column = split.column()
        column.separator()

        column = split.column(align=True)

        if mod.show_expanded:
            self.expanded(context, column, obj, mod)

        else:
            self.label_row(context, column, obj, mod, 'width', label='Width')
            self.label_row(context, column, obj, mod, 'segments', label='Segments')


        if bpy.app.version < (2, 90, 0):
            column.row().prop(mod, "use_custom_profile")
            row = column.row()
            row.enabled = mod.use_custom_profile
            if mod.use_custom_profile:
                column.template_curveprofile(mod, "custom_profile")
                row2 = column.row(align=True)
                op = row2.operator('hops.save_bevel_profile', text='Save Profile')
                op.obj, op.mod = context.object.name, mod.name
                op = row2.operator('hops.load_bevel_profile', text='Load Profile')
                op.obj, op.mod = context.object.name, mod.name

        else:
            column.row().prop(mod, "profile_type", expand=True)
            if mod.profile_type == 'CUSTOM':
                column.template_curveprofile(mod, "custom_profile")
                col = column.row(align=True)
                op = col.operator('hops.save_bevel_profile', text='Save Profile')
                op.obj, op.mod = context.object.name, mod.name
                op = col.operator('hops.load_bevel_profile', text='Load Profile')
                op.obj, op.mod = context.object.name, mod.name

    def expanded(self, context, layout, obj, mod):
        self.label_row(context, layout, obj, mod, 'width', label='Width')
        self.label_row(context, layout, obj, mod, 'segments', label='Segments')

        self.label_row(context, layout, obj, mod, 'profile', label='Profile')

        layout.separator()

        self.label_row(context, layout, obj, mod, 'limit_method', label='Method')

        if mod.limit_method == 'ANGLE':
            self.label_row(context, layout, obj, mod, 'angle_limit', label='Angle')
            layout.separator()

        elif mod.limit_method == 'VGROUP':
            self.label_row(context, layout, obj, mod, 'vertex_group', label='Vertex Group')
            layout.separator()

        self.label_row(context, layout, obj, mod, 'offset_type', label='Width Method')

        layout.separator()

        self.label_row(context, layout, obj, mod, 'miter_outer', label='Outer')
        self.label_row(context, layout, obj, mod, 'miter_inner', label='Inner')
        self.label_row(context, layout, obj, mod, 'spread', label='Spread')

        layout.separator()

        self.label_row(context, layout, obj, mod, 'use_clamp_overlap', label='Clamp Overlap')
        self.label_row(context, layout, obj, mod, 'harden_normals', label='Harden Normals')

        layout.separator()

    def label_row(self, context, layout, obj, path, prop, label='Label'):
        preference = addon.preference().property
        column = layout.column(align=True)
        split = column.split(factor=0.5, align=True)

        split.label(text=label)

        row = split.row(align=True)
        if label == 'Width':
            width = obj.modifiers[path.name].width

            sub = row.row(align=True)
            sub.scale_x = 0.3

            ot = sub.operator('wm.context_set_float', text='/')
            ot.data_path = F'active_object.modifiers["{path.name}"].width'
            ot.value = width / 2

            row.prop(path, prop, text='')

            sub = row.row(align=True)
            sub.scale_x = 0.3
            ot = sub.operator('wm.context_set_float', text='*')
            ot.data_path = F'active_object.modifiers["{path.name}"].width'
            ot.value = width * 2
        else:
            row.prop(path, prop, text='')


        if label in {'Width', 'Segments', 'Profile', 'Angle'} and preference.show_presets:
            split = column.split(factor=0.5, align=True)
            split.separator()
            row = split.row(align=True)

            for preset in presets[label]:
                ot = row.operator(
                    F'wm.context_set_{"int" if label not in {"Width", "Profile", "Angle"} else "float"}', text=str(preset))
                ot.data_path = F'active_object.modifiers["{path.name}"].{prop}'
                ot.value = preset if label != 'Angle' else radians(preset)

            if label not in {'Profile', 'Angle'}:
                column.separator()


class HOPS_OT_bevel_helper_hide_false(bpy.types.Operator):
    bl_idname = 'hops.bevel_helper_hide_false'
    bl_description = 'Hide for  bevel helper'
    bl_label = 'HOps Bevel Helper'

    obj_name: StringProperty(name="obj name")

    def execute(self, context):
        obj = bpy.data.objects[self.obj_name]
        turn_on_parent_collections(obj, context.scene.collection)
        obj.hide_set(False)
        bpy.ops.hops.draw_wire_mesh_launcher('INVOKE_DEFAULT', target='NONE', object_name=obj.name)
        return {'FINISHED'}


class HOPS_OT_bevel_helper_hide_true(bpy.types.Operator):
    bl_idname = 'hops.bevel_helper_hide_true'
    bl_description = 'Hide for bevel helper'
    bl_label = 'HOps Bevel Helper'

    obj_name: StringProperty(name="obj name")

    def execute(self, context):
        obj = bpy.data.objects[self.obj_name]
        turn_on_parent_collections(obj, context.scene.collection)
        obj.hide_set(True)
        return {'FINISHED'}


class HOPS_OT_bevel_helper_hide_all_bools(bpy.types.Operator):
    bl_idname = 'hops.bevel_helper_hide_all_bools'
    bl_description = 'Hide all boolean objects'
    bl_label = 'HOps Bevel Helper'

    obj_name: StringProperty(name="obj name")

    def execute(self, context):
        obj = bpy.data.objects[self.obj_name]
        toggle_all_bools(context, obj, on=True)
        return {'FINISHED'}


class HOPS_OT_bevel_helper_unhide_all_bools(bpy.types.Operator):
    bl_idname = 'hops.bevel_helper_unhide_all_bools'
    bl_description = 'Unhide all boolean objects'
    bl_label = 'HOps Bevel Helper'

    obj_name: StringProperty(name="obj name")

    def execute(self, context):
        obj = bpy.data.objects[self.obj_name]
        toggle_all_bools(context, obj, on=False)
        return {'FINISHED'}


class HOPS_OT_bevel_helper_boolean_solver(bpy.types.Operator):
    bl_idname = 'hops.bevel_helper_boolean_solver'
    bl_description = 'Set solver for booleans'
    bl_label = 'HOps Bevel Helper'

    obj_name: StringProperty(name="obj name")
    solver: StringProperty(name="FAST")

    def execute(self, context):
        obj = bpy.data.objects[self.obj_name]

        if hasattr(obj, 'modifiers'):
            for mod in obj.modifiers:
                if mod.type == 'BOOLEAN':
                    if self.solver == 'FAST':
                        mod.solver = 'FAST'
                    else:
                        mod.solver = 'EXACT'

        return {'FINISHED'}


def toggle_all_bools(context, obj, on=True):
    '''Hide / Unhide all objects referenced by the mods of the object.'''

    if hasattr(obj, 'modifiers'):
        bools = set()

        for mod in obj.modifiers:
            if mod.type == 'BOOLEAN':
                if mod.object is not None:
                    bools.add(mod.object)

            elif mod.type == 'NODES':
                for node in mod.node_group.nodes:
                    if (node.type == 'OBJECT_INFO') and (node.inputs['Object'].default_value is not None):
                        bools.add(node.inputs['Object'].default_value)

        for obj in bools:
            if isinstance(obj, bpy.types.Object):
                turn_on_parent_collections(obj, context.scene.collection)
                obj.hide_set(not on)
                obj.hops.bevel_helper_hide = not on


class HOPS_OT_bevel_helper_bool_swap(bpy.types.Operator):
    bl_idname = 'hops.bevel_helper_bool_swap'
    bl_description = 'Swap boolean'
    bl_label = 'HOps Bevel Helper'

    obj_name: StringProperty(name="obj name")
    mod_name: StringProperty(name="mod name")

    def execute(self, context):
        mod = bpy.data.objects[self.obj_name].modifiers[self.mod_name]

        if mod.operation == 'DIFFERENCE':
            mod.operation = 'INTERSECT'
        elif mod.operation == 'INTERSECT':
            mod.operation = 'UNION'
        else:
            mod.operation = 'DIFFERENCE'

        return {'FINISHED'}


class HOPS_OT_bevel_helper_bool_select(bpy.types.Operator):
    bl_idname = 'hops.bevel_helper_bool_select'
    bl_description = 'Select boolean'
    bl_label = 'HOps Bevel Helper'

    obj_name: StringProperty(name="obj name")
    mod_name: StringProperty(name="mod name")

    def execute(self, context):
        mod = bpy.data.objects[self.obj_name].modifiers[self.mod_name]
        if mod.object:
            if mod.object.select_get():
                mod.object.select_set(False)
            else:
                mod.object.select_set(True)

        return {'FINISHED'}