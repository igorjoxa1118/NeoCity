import statistics

import bpy

from mathutils import Matrix
from math import radians

from bpy.types import GizmoGroup, Operator, Gizmo
from bpy.props import EnumProperty, BoolProperty

from .... utility import addon, tool, screen, modifier, operator_override


class BC_OT_transform_translate(Operator):
    bl_idname = 'bc.transform_translate'
    bl_label = 'Move'
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = ('\n Move\n'
        ' LMB - translate\n'
        ' LMB + Shift - Copy objects\n'
        ' LMB + Shift + Ctrl - reset axis')

    axis_set = (False, False, False)

    axis: EnumProperty(
        name='Axis',
        description='Axis',
        items=[
            ('X', 'x', '', '', 0),
            ('Y', 'y', '', '', 1),
            ('Z', 'z', '', '', 2),
            ('ALL', 'All', '', '', 3)],
        default='ALL')

    reset: BoolProperty(
        name='Reset axis',
        description='Reset Axis',
        default=False)


    def invoke(self, context, event):
        if self.axis == 'X':
            self.axis_set = (True, False, False)

        elif self.axis == 'Y':
            self.axis_set = (False, True, False)

        elif self.axis == 'Z':
            self.axis_set = (False, False, True)


        context.window_manager.modal_handler_add(self)

        return {'RUNNING_MODAL'}


    def boolean(self, context, obj, cutter, operation = 'DIFFERENCE'):
        mod = obj.modifiers.new(name='Boolean', type='BOOLEAN')

        if hasattr(mod, 'solver'):
            mod.solver = addon.preference().behavior.boolean_solver

        mod.show_viewport = True
        mod.show_expanded = False
        mod.object = cutter
        mod.operation = operation


    # TODO set option for user to set if he wants to copy modifiers or not when duplicating
    def modal(self, context, event):
        if event.shift:

            if event.ctrl:
                axis = 'XYZ'.index(self.axis)
                for obj in context.selected_objects:
                    obj.location[axis] = 0

                return {'FINISHED'}

            else:
                constraint = [self.axis == char for char in 'XYZ']
                #bpy.ops.object.duplicate_move('INVOKE_DEFAULT', OBJECT_OT_duplicate={"linked":False, "mode":'TRANSLATION'}, TRANSFORM_OT_translate={"constraint_axis":constraint, "release_confirm":True})

                mod_object_map = {'ARRAY' : 'offset_object'} # extend to support more modifiers
                flag = 'bc_gizmo_original'

                for obj in context.selected_objects:

                    linked_objects = [getattr(mod, mod_object_map[mod.type]) for mod in obj.modifiers if mod.type in mod_object_map]
                    linked_objects.append(obj)

                    obj[flag] = True
                    override = {'selected_objects': linked_objects, 'active_object': None, 'object': None}
                    operator_override(context, bpy.ops.object.duplicate, override, linked=False)

                    for new_obj in context.selected_objects:
                        if flag in new_obj:
                            copy = new_obj
                            obj.pop(flag)
                            new_obj.pop(flag)
                            break

                    if obj == context.active_object:
                        context.view_layer.objects.active = copy

                    if obj.bc.target is not None:
                        source_bool = None
                        for mod in reversed(obj.bc.target.modifiers):
                            if mod.type == 'BOOLEAN' and mod.object is obj:
                                source_bool = modifier.stored(mod)
                                break

                        if not source_bool:
                            continue

                        source_bool.object = copy
                        index = obj.bc.target.modifiers.find(source_bool.name) + 1

                        stored_mods = [modifier.stored(mod) for mod in obj.bc.target.modifiers]
                        stored_mods.insert(index, source_bool)
                        obj.bc.target.modifiers.clear()

                        for stored_mod in stored_mods:
                            modifier.new(obj.bc.target, mod=stored_mod)

                bpy.ops.transform.translate('INVOKE_DEFAULT', constraint_axis=constraint, release_confirm=True)

                return {'FINISHED'}

        else:
            bpy.ops.transform.translate('INVOKE_DEFAULT', constraint_axis=self.axis_set, release_confirm=True)

        return {'FINISHED'}


class BC_OT_transform_rotate(Operator):
    bl_idname = 'bc.transform_rotate'
    bl_label = 'Rotate'
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = ('\n Rotate\n'
        ' LMB - rotate\n'
        ' LMB+shift+ctrl - reset axis')

    axis_set = (False, False, False)

    axis: EnumProperty(
        name='Axis',
        description='Axis',
        items=[
            ('X', 'x', '', '', 0),
            ('Y', 'y', '', '', 1),
            ('Z', 'z', '', '', 2),
            ('ALL', 'All', '', '', 3)],
        default='ALL')

    reset: BoolProperty(
        name='Reset axis',
        description='Reset Axis',
        default=False)


    def invoke(self, context, event):
        if self.axis == 'X':
            self.axis_set = (True, False, False)

        elif self.axis == 'Y':
            self.axis_set = (False, True, False)

        elif self.axis == 'Z':
            self.axis_set = (False, False, True)

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


    def modal(self, context, event):
        if event.shift and event.ctrl:
            if self.axis == 'X':
                for obj in context.selected_objects:
                    obj.rotation_euler[0] = 0

                return {'FINISHED'}

            if self.axis == 'Y':
                for obj in context.selected_objects:
                    obj.rotation_euler[1] = 0

                return {'FINISHED'}

            if self.axis == 'Z':
                for obj in context.selected_objects:
                    obj.rotation_euler[2] = 0

                return {'FINISHED'}

        else:
            bpy.ops.transform.rotate('INVOKE_DEFAULT', constraint_axis=self.axis_set, release_confirm=True)

        return {'FINISHED'}


class BC_OT_transform_resize(Operator):
    bl_idname = 'bc.transform_resize'
    bl_label = 'Resize'
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = ('\n Scale\n'
        ' LMB - Scale\n'
        ' LMB+shift - Scale on other axis\n'
        ' LMB+shift+ctrl - Reset Scale')

    axis_set = (False, False, False)

    axis: EnumProperty(
        name='Axis',
        description='Axis',
        items=[
            ('X', 'x', '', '', 0),
            ('Y', 'y', '', '', 1),
            ('Z', 'z', '', '', 2),
            ('ALL', 'All', '', '', 3)],
        default='ALL')

    reset: BoolProperty(
        name='Reset axis',
        description='Reset Axis',
        default=False)


    def invoke(self, context, event):
        if self.axis == 'X':
            self.axis_set = (True, False, False)
        elif self.axis == 'Y':
            self.axis_set = (False, True, False)
        elif self.axis == 'Z':
            self.axis_set = (False, False, True)

        context.window_manager.modal_handler_add(self)

        return {'RUNNING_MODAL'}


    def modal(self, context, event):
        if event.shift:

            if self.axis == 'X':
                if event.ctrl:
                    for obj in context.selected_objects:
                        obj.scale[0] = 1

                    return {'FINISHED'}

                else:
                    bpy.ops.transform.resize('INVOKE_DEFAULT', constraint_axis=(False, True, True), release_confirm=True)

                    return {'FINISHED'}

            if self.axis == 'Y':
                if event.ctrl:
                    for obj in context.selected_objects:
                        obj.scale[1] = 1

                    return {'FINISHED'}

                else:
                    bpy.ops.transform.resize('INVOKE_DEFAULT', constraint_axis=(True, False, True), release_confirm=True)

                    return {'FINISHED'}

            if self.axis == 'Z':
                if event.ctrl:
                    for obj in context.selected_objects:
                        obj.scale[2] = 1

                    return {'FINISHED'}

                else:
                    bpy.ops.transform.resize('INVOKE_DEFAULT', constraint_axis=(True, True, False), release_confirm=True)

                    return {'FINISHED'}

        else:
            bpy.ops.transform.resize('INVOKE_DEFAULT', constraint_axis=self.axis_set, release_confirm=True)

        return {'FINISHED'}


class BC_OT_transform_add_gizmo(Operator):
    bl_idname = 'bc.transform_add_gizmo'
    bl_label = 'BC_transform Gizmo Display'
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = '''\n Show/Hide BC_Transform Gizmo
    shift + click drag an axis to duplicate object w/ boolean modifier
    ctrl + shift + click drag to reset axis

    Supports local and global orientations

    '''


    def execute(self, context):
        bpy.context.window_manager.gizmo_group_type_ensure(BC_WGT_transform_gizmo_group.bl_idname)
        addon.preference().transform_gizmo = True

        return {'FINISHED'}


class BC_OT_transform_remove_gizmo(Operator):
    bl_idname = 'bc.transform_remove_gizmo'
    bl_label = 'Gizmo transform Remove'
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = '\n Hide Transform Gizmo'


    def execute(self, context):
        bpy.context.window_manager.gizmo_group_type_unlink_delayed(BC_WGT_transform_gizmo_group.bl_idname)
        addon.preference().transform_gizmo = False

        return {'FINISHED'}


class BC_WGT_transform_gizmo_group(GizmoGroup):
    bl_idname = 'bc.transform_gizmo_group'
    bl_label = 'Move Gizmo'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'3D'}

    @classmethod
    def poll(cls, context):
        # if tool.active().idname == tool.name:

        #     if len(context.selected_objects) > 0:
        #         if getattr(context.active_object, 'type', '') == 'MESH':
        #             if getattr(context.active_object, 'mode', '') == 'OBJECT':
        #                 # bpy.context.window_manager.gizmo_group_type_ensure(BC_WGT_transform_gizmo_group.bl_idname)
        #                 return True

        # # bpy.context.window_manager.gizmo_group_type_unlink_delayed(BC_WGT_transform_gizmo_group.bl_idname)
        # return False
        active = tool.active()
        return active and active.idname == tool.name and context.selected_objects


    def setup(self, context):
        mpr_x = self.gizmos.new('GIZMO_GT_arrow_3d')
        opx = mpr_x.target_set_operator('bc.transform_translate')
        opx.axis = 'X'
        mpr_x.use_draw_modal = False
        mpr_x.scale_basis = 1.2
        mpr_x.color = 1, 0.2, 0.322
        mpr_x.alpha = 0.5
        mpr_x.color_highlight = 1.0, 1.0, 1.0
        mpr_x.alpha_highlight = 1.0

        scale_x = self.gizmos.new('GIZMO_GT_arrow_3d')
        spx = scale_x.target_set_operator('bc.transform_resize')
        spx.axis = 'X'
        scale_x.use_draw_modal = False
        scale_x.draw_style = 'BOX'
        scale_x.scale_basis = 0.7
        scale_x.color = 1, 0.2, 0.322
        scale_x.alpha = 0.5
        scale_x.color_highlight = 1.0, 1.0, 1.0
        scale_x.alpha_highlight = 1.0

        dial_x = self.gizmos.new(BC_GT_transform_gizmo.bl_idname)
        rpx = dial_x.target_set_operator('bc.transform_rotate')
        rpx.axis = 'X'
        dial_x.use_draw_modal = False
        dial_x.scale_basis = 1
        dial_x.color = 1, 0.2, 0.322
        dial_x.alpha = 0.5
        dial_x.color_highlight = 1.0, 1.0, 1.0
        dial_x.alpha_highlight = 1.0

        mpr_y = self.gizmos.new('GIZMO_GT_arrow_3d')
        opy = mpr_y.target_set_operator('bc.transform_translate')
        opy.axis = 'Y'
        mpr_y.use_draw_modal = False
        mpr_y.scale_basis = 1.2
        mpr_y.color = 0.545, 0.863, 0
        mpr_y.alpha = 0.5
        mpr_y.color_highlight = 1.0, 1.0, 1.0
        mpr_y.alpha_highlight = 1.0

        scale_y = self.gizmos.new('GIZMO_GT_arrow_3d')
        spy = scale_y.target_set_operator('bc.transform_resize')
        spy.axis = 'Y'
        scale_y.use_draw_modal = False
        scale_y.draw_style = 'BOX'
        scale_y.scale_basis = 0.7
        scale_y.color = 0.545, 0.863, 0
        scale_y.alpha = 0.5
        scale_y.color_highlight = 1.0, 1.0, 1.0
        scale_y.alpha_highlight = 1.0

        dial_y = self.gizmos.new(BC_GT_transform_gizmo.bl_idname)
        rpy = dial_y.target_set_operator('bc.transform_rotate')
        rpy.axis = 'Y'
        dial_y.use_draw_modal = False
        dial_y.scale_basis = 0.9
        dial_y.color = 0.545, 0.863, 0
        dial_y.alpha = 0.5
        dial_y.color_highlight = 1.0, 1.0, 1.0
        dial_y.alpha_highlight = 1.0

        mpr_z = self.gizmos.new('GIZMO_GT_arrow_3d')
        opz = mpr_z.target_set_operator('bc.transform_translate')
        opz.axis = 'Z'
        mpr_z.use_draw_modal = False
        mpr_z.scale_basis = 1.2
        mpr_z.color = 0.157, 0.565, 1
        mpr_z.alpha = 0.5
        mpr_z.color_highlight = 1.0, 1.0, 1.0
        mpr_z.alpha_highlight = 1.0

        scale_z = self.gizmos.new('GIZMO_GT_arrow_3d')
        spz = scale_z.target_set_operator('bc.transform_resize')
        spz.axis = 'Z'
        scale_z.use_draw_modal = False
        scale_z.draw_style = 'BOX'
        scale_z.scale_basis = 0.7
        scale_z.color = 0.157, 0.565, 1
        scale_z.alpha = 0.5
        scale_z.color_highlight = 1.0, 1.0, 1.0
        scale_z.alpha_highlight = 1.0

        dial_z = self.gizmos.new(BC_GT_transform_gizmo.bl_idname)
        rpz = dial_z.target_set_operator('bc.transform_rotate')
        rpz.axis = 'Z'
        dial_z.use_draw_modal = False
        dial_z.scale_basis = 1
        dial_z.color = 0.157, 0.565, 1
        dial_z.alpha = 0.5
        dial_z.color_highlight = 1.0, 1.0, 1.0
        dial_z.alpha_highlight = 1.0

        self.mpr_z = mpr_z
        self.scale_z = scale_z
        self.dial_z = dial_z
        self.mpr_x = mpr_x
        self.scale_x = scale_x
        self.dial_x = dial_x
        self.mpr_y = mpr_y
        self.scale_y = scale_y
        self.dial_y = dial_y


    def draw_prepare(self, context):
        if tool.active().idname != tool.name:
            bpy.context.window_manager.gizmo_group_type_unlink_delayed(BC_WGT_transform_gizmo_group.bl_idname)
            return

        if not hasattr(self, 'mpr_z'):
            self.setup(context)

            return

        mpr_z = self.mpr_z
        scale_z = self.scale_z
        dial_z = self.dial_z
        mpr_x = self.mpr_x
        scale_x = self.scale_x
        dial_x = self.dial_x
        mpr_y = self.mpr_y
        scale_y = self.scale_y
        dial_y = self.dial_y

        mpr_z.alpha = 0.5 if context.active_object else 0.0
        mpr_z.alpha_highlight = 1.0 if context.active_object else 0.0
        scale_z.alpha = 0.5 if context.active_object else 0.0
        scale_z.alpha_highlight = 1.0 if context.active_object else 0.0
        dial_z.alpha = 0.5 if context.active_object else 0.0
        dial_z.alpha_highlight = 1.0 if context.active_object else 0.0
        mpr_x.alpha = 0.5 if context.active_object else 0.0
        mpr_x.alpha_highlight = 1.0 if context.active_object else 0.0
        scale_x.alpha = 0.5 if context.active_object else 0.0
        scale_x.alpha_highlight = 1.0 if context.active_object else 0.0
        dial_x.alpha = 0.5 if context.active_object else 0.0
        dial_x.alpha_highlight = 1.0 if context.active_object else 0.0
        mpr_y.alpha = 0.5 if context.active_object else 0.0
        mpr_y.alpha_highlight = 1.0 if context.active_object else 0.0
        scale_y.alpha = 0.5 if context.active_object else 0.0
        scale_y.alpha_highlight = 1.0 if context.active_object else 0.0
        dial_y.alpha = 0.5 if context.active_object else 0.0
        dial_y.alpha_highlight = 1.0 if context.active_object else 0.0

        if not context.active_object:
            return

        selection = context.selected_objects
        origins_loc = [a.matrix_world.translation for a in selection]
        orig_loc = [statistics.median(col) for col in zip(*origins_loc)]
        orig_rot = context.active_object.rotation_euler

        if context.scene.transform_orientation_slots[0].type == 'LOCAL':
            x_rot_mat = orig_rot.to_matrix().to_4x4() @ Matrix.Rotation(radians(90), 4, 'Y')
            x_dial_rot_mat = orig_rot.to_matrix().to_4x4() @ Matrix.Rotation(radians(-90), 4, 'Y')
            y_rot_mat = orig_rot.to_matrix().to_4x4() @ Matrix.Rotation(radians(-90), 4, 'X')
            z_rot_mat = orig_rot.to_matrix().to_4x4() @ Matrix.Rotation(radians(90), 4, 'Z')
            x_scale_rot_mat = orig_rot.to_matrix().to_4x4() @ Matrix.Rotation(radians(-90), 4, 'Y')
            y_scale_rot_mat = orig_rot.to_matrix().to_4x4() @ Matrix.Rotation(radians(90), 4, 'X')
            z_scale_rot_mat = orig_rot.to_matrix().to_4x4() @ Matrix.Rotation(radians(-180), 4, 'X')

        else:
            x_rot_mat = Matrix.Rotation(radians(90), 4, 'Y')
            x_dial_rot_mat = Matrix.Rotation(radians(-90), 4, 'Y')
            y_rot_mat = Matrix.Rotation(radians(-90), 4, 'X')
            z_rot_mat = Matrix.Rotation(radians(90), 4, 'Z')
            x_scale_rot_mat = Matrix.Rotation(radians(-90), 4, 'Y')
            y_scale_rot_mat = Matrix.Rotation(radians(90), 4, 'X')
            z_scale_rot_mat = Matrix.Rotation(radians(-180), 4, 'X')

        orig_loc_mat = Matrix.Translation(orig_loc)
        orig_scale_mat = Matrix.Scale(1, 4, (1, 0, 0)) @ Matrix.Scale(1, 4, (0, 1, 0)) @ Matrix.Scale(1, 4, (0, 0, 1))

        z_matrix_world = orig_loc_mat @ z_rot_mat @ orig_scale_mat
        x_matrix_world = orig_loc_mat @ x_rot_mat @ orig_scale_mat
        x_dial_matrix_world = orig_loc_mat @ x_dial_rot_mat @ orig_scale_mat
        y_matrix_world = orig_loc_mat @ y_rot_mat @ orig_scale_mat

        x_scale_matrix_world = orig_loc_mat @ x_scale_rot_mat @ orig_scale_mat
        y_scale_matrix_world = orig_loc_mat @ y_scale_rot_mat @ orig_scale_mat
        z_scale_matrix_world = orig_loc_mat @ z_scale_rot_mat @ orig_scale_mat

        mpr_z.matrix_basis = z_matrix_world.normalized()
        mpr_x.matrix_basis = x_matrix_world.normalized()
        mpr_y.matrix_basis = y_matrix_world.normalized()

        dial_x.matrix_basis = x_dial_matrix_world.normalized()
        dial_y.matrix_basis = y_matrix_world.normalized()
        dial_z.matrix_basis = z_matrix_world.normalized()

        scale_z.matrix_basis = z_scale_matrix_world.normalized()
        scale_x.matrix_basis = x_scale_matrix_world.normalized()
        scale_y.matrix_basis = y_scale_matrix_world.normalized()


class BC_GT_transform_gizmo(Gizmo):
    bl_idname = 'bc.trasnform_gizmo'
    bl_target_properties = (
        {'id': 'offset', 'type': 'FLOAT', 'array_length': 1}, )

    __slots__ = (
        'custom_shape', )


    def draw(self, context):
        self.draw_custom_shape(self.custom_shape)


    def draw_select(self, context, select_id):
        self.draw_custom_shape(self.new_custom_shape('LINE_STRIP', lines), select_id=select_id)


    def setup(self):
        if not hasattr(self, 'custom_shape'):
            self.custom_shape = self.new_custom_shape('LINE_STRIP', lines)


    def exit(self, context, cancel):
        context.area.header_text_set(None)


lines = (
    (-0.876561, 0.478638, 0.0),
    (-0.908473, 0.414886, 0.0),
    (-0.935756, 0.349019, 0.0),
    (-0.958271, 0.281374, 0.0),
    (-0.975902, 0.212294, 0.0),
    (-0.98856, 0.142134, 0.0),
    (-0.996181, 0.071248, 0.0),
    (-1.0, 0, 0.0),
    (-0.996181, -0.071248, 0.0),
    (-0.98856, -0.142134, 0.0),
    (-0.975902, -0.212294, 0.0),
    (-0.958271, -0.281374, 0.0),
    (-0.935756, -0.349019, 0.0),
    (-0.908473, -0.414886, 0.0),
    (-0.876561, -0.478638, 0.0))
