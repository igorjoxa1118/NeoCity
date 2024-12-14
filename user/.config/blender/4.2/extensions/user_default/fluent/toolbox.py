import bpy
from bpy.types import Operator
from bpy_extras import view3d_utils

from .UI.Helpers.viewport_drawing import *
from .modifiers import *
from .bevels import *
from .Tools.independant_helper import *
from .Tools.translation import translate
from .UI.Helpers.ui_management import FLUENT_ui_management


class FLUENT_OT_AlignView(Operator):
    "Align view to vertex"
    bl_idname = "fluent.alignview"
    bl_label = "Align view"
    bl_options = {'REGISTER', 'UNDO'}

    ui_management = None

    def modal(self, context, event):
        context.area.tag_redraw()

        if pass_through(event):
            return {'PASS_THROUGH'}

        region = context.region
        rv3d = context.region_data

        self.ui_management.clear_dots()
        snaped_vertex = [1000, None, None]  # distance, vertex, co2_d
        obj = click_on(event.mouse_region_x, event.mouse_region_y)

        if obj:
            eval_obj = get_evaluated_object(obj)
            matrix = eval_obj.matrix_world
            for v in eval_obj.data.vertices:
                co_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, matrix @ v.co)
                d = distance(co_2d.x, co_2d.y, 0, event.mouse_region_x, event.mouse_region_y, 0)
                if d <= 32 and d < snaped_vertex[0]:
                    snaped_vertex[0] = d
                    snaped_vertex[1] = v
                    snaped_vertex[2] = co_2d
            if snaped_vertex[1]:
                self.ui_management.add_a_dot([snaped_vertex[2].x, snaped_vertex[2].y, 6, (1, 1, 1, 1)])

        if event.value == 'PRESS' and event.type == 'LEFTMOUSE' and snaped_vertex[1]:
            v_normal = matrix @ snaped_vertex[1].normal - obj.location
            v_up = Vector((0, 0, 1))
            q_rot = v_normal.rotation_difference(v_up)
            rv3d.view_rotation = q_rot.inverted()
            context.region_data.view_perspective = 'ORTHO'
            active_object('SET', obj, True)
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            return {'FINISHED'}

        if event.value == 'PRESS' and event.type == 'ESC':
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            return {'FINISHED'}
        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        self.ui_management = FLUENT_ui_management(event)
        self.ui_management.add_dots_items()
        self.the_vertex = None
        self.previous_object = None
        self._handle = bpy.types.SpaceView3D.draw_handler_add(draw_callback_px, (self, context), 'WINDOW', 'POST_PIXEL')
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


class FLUENT_OT_CleanBooleanObjects(Operator):
    """Remove unused boolean objects"""
    bl_idname = "fluent.cleanbooleanobjects"
    bl_label = "Fluent - Remove unused boolean objects"

    def invoke(self, context, event):
        for o in bpy.data.collections[get_addon_preferences().bool_collection].objects:
            modifier_found = False
            for oo in bpy.data.objects:
                for m in oo.modifiers:
                    if m.type == 'BOOLEAN' and m.object == o:
                        modifier_found = True
                        break
            if not modifier_found:
                bpy.data.objects.remove(o, do_unlink=True)
        return {'FINISHED'}


class FLUENT_OT_ApplyToBoolean(Operator):
    """Apply all modifiers from the first to the first boolean.
Especially useful to prepare the model to the boolean support tool.

/!\ Your object will be impossible to edit with Fluent./!\ """
    bl_idname = "fluent.applytoboolean"
    bl_label = "Apply to boolean"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = active_object('GET')
        if obj:
            for m in obj.modifiers:
                if m.type != 'BOOLEAN' or fluent_modifiers_name['outer_bevel'] in m.name:
                    if m.show_render:
                        try:
                            bpy.ops.object.modifier_apply(modifier=m.name)
                        except:
                            obj.modifiers.remove(m)
                    else:
                        obj.modifiers.remove(m)
                else:
                    break
            if obj.get('fluent_obj'):
                obj['fluent_obj'] = 0
            if obj.get('fluent_type'):
                obj['fluent_type'] = 'unknow'
        return {'FINISHED'}


class FLUENT_OT_AutoSupport(Operator):
    """Automatic edge supports making.
Select the boolean object first and the main object after

Hold Shift - supports for each loose parts"""
    bl_idname = "fluent.autosupport"
    bl_label = "Boolean support creation"
    bl_options = {'REGISTER', 'UNDO'}

    def cutterObj(self):
        height = .01
        vertices = [(-1, -1, -height), (-1, 1, -height), (1, 1, -height), (1, -1, -height),
                    (-1, -1, height), (-1, 1, height), (1, 1, height), (1, -1, height),
                    (-1, 0, -height), (1, 0, -height),
                    (-1, 0, height), (1, 0, height),
                    (0, -1, -height), (0, 1, -height),
                    (0, -1, height), (0, 1, height),
                    (0, 0, -height), (0, 0, height)]

        faces = [(0, 4, 10, 8), (8, 10, 5, 1), (1, 5, 15, 13), (13, 15, 6, 2), (2, 6, 11, 9), (9, 11, 7, 3),
                 (3, 7, 14, 12), (12, 14, 4, 0),
                 (4, 10, 17, 14), (10, 5, 15, 17), (17, 15, 6, 11), (14, 17, 11, 7), (0, 8, 16, 12), (8, 1, 13, 16),
                 (16, 13, 2, 9), (12, 16, 9, 3),
                 (8, 10, 17, 16), (16, 17, 11, 9), (12, 14, 17, 16), (16, 17, 15, 13)]

        mesh_data = bpy.data.meshes.new("cutter")
        mesh_data.from_pydata(vertices, [], faces)
        mesh_data.update()
        cutter_obj = bpy.data.objects.new("cutter", mesh_data)
        bpy.context.scene.collection.objects.link(cutter_obj)
        active_object('SET', cutter_obj, True)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.object.vertex_group_add()
        bpy.ops.object.vertex_group_assign()
        v_groups = bpy.context.active_object.vertex_groups
        v_groups[0].name = 'intersect'
        bpy.ops.object.mode_set(mode='OBJECT')

        return cutter_obj

    def execute(self, context):
        bool_list = []
        cutter_list = []
        obj = active_object('GET')
        obj.select_set(False)
        for v in obj.data.vertices:
            v.select = False
        margin = 0.01

        if not obj:
            make_oops([translate('firstSelectBoolean'), translate('secondSelectObject')],
                      title=translate('info'), icon='ERROR')

            return {'CANCELLED'}

        # récupère la largeur du dernier bevel angle
        hidden_modifiers = []
        for m in obj.modifiers:
            if m.type == 'BEVEL' and m.limit_method == 'ANGLE':
                margin = m.width * 2 + margin
                hidden_modifiers.append(m)
                m.show_viewport = False
        for o in bpy.context.selected_objects:
            bool_list.append(o)
            o.select_set(False)
        for b in bool_list:
            multiparts = False
            active_object('SET', b, True)
            bpy.ops.object.duplicate()
            copy = active_object('GET')
            active_object('SET', copy, True)

            for m in copy.modifiers:
                if m.show_render and m.type in {'MIRROR', 'ARRAY'}:
                    multiparts = True

            bpy.ops.object.convert(target='MESH')
            bpy.ops.object.transform_apply(location=True, rotation=False, scale=True)

            if multiparts and self.event.shift:
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.mesh.separate(type='LOOSE')
                bpy.ops.object.mode_set(mode='OBJECT')
                bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
                subparts = bpy.context.selected_objects

                for s in subparts:
                    cutter = self.cutterObj()
                    cutter.select_set(True)
                    context.view_layer.objects.active = cutter
                    bpy.ops.object.mode_set(mode='EDIT')
                    bpy.ops.mesh.select_all(action='SELECT')
                    bpy.ops.object.mode_set(mode='OBJECT')
                    cutter.dimensions = s.dimensions
                    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
                    cutter.dimensions.x = cutter.dimensions.x + margin
                    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
                    cutter.dimensions.y = cutter.dimensions.y + margin
                    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
                    cutter.location = s.location
                    cutter.rotation_euler = s.rotation_euler
                    cutter_list.append(cutter)
                    cutter.select_set(False)
                    bpy.data.objects.remove(s, do_unlink=True)

            else:
                bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
                b.select_set(False)
                cutter = self.cutterObj()
                cutter.select_set(True)
                context.view_layer.objects.active = cutter
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.object.mode_set(mode='OBJECT')
                cutter.dimensions = copy.dimensions
                bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
                cutter.dimensions.x = cutter.dimensions.x + margin
                bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
                cutter.dimensions.y = cutter.dimensions.y + margin
                bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
                cutter.location = copy.location
                cutter.rotation_euler = b.rotation_euler
                cutter_list.append(cutter)
                cutter.select_set(False)
                bpy.data.objects.remove(copy, do_unlink=True)
        for o in cutter_list:
            o.select_set(True)
        active_object('SET', obj)
        bpy.ops.object.join()
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type="VERT")
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.normals_make_consistent(inside=False)
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_set_active(group='intersect')
        bpy.ops.object.vertex_group_select()
        bpy.ops.mesh.intersect()
        bpy.ops.mesh.remove_doubles()
        v_no_group = []
        bpy.ops.object.mode_set(mode='OBJECT')
        for v in obj.data.vertices:
            if v.select:
                v_no_group.append(v.index)
        bpy.ops.object.mode_set(mode='OBJECT')
        obj.vertex_groups['intersect'].remove(v_no_group)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_set_active(group='intersect')
        bpy.ops.object.vertex_group_select()
        bpy.ops.mesh.delete(type='VERT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.object.vertex_group_remove()
        bpy.ops.object.mode_set(mode='OBJECT')

        obj.select_set(False)

        context.view_layer.objects.active = bool_list[0]

        for m in hidden_modifiers:
            m.show_viewport = True

        return {'FINISHED'}

    def invoke(self, context, event):
        if len(bpy.context.selected_objects) != 2:
            make_oops([translate('selectTwoObjects'), translate('selectBooleanThenObject')], title=translate('howToUse'),
                      icon='ERROR')

            return {'CANCELLED'}
        else:
            obj = active_object()
            for m in obj.modifiers:
                if m.type == 'SOLIDIFY':
                    make_oops([translate('useSolidifyModifier'),
                               translate('impossibleAddEdge'),
                               translate('resultNotAsExpected'), translate('useApplyToBoolean')],
                              title=translate('problem'), icon='ERROR')
            self.event = event
            self.execute(context)
            return {'FINISHED'}


class FLUENT_OT_AllCutterMirror(Operator):
    "Apply a mirror for each cut"
    bl_idname = "fluent.allcuttermirror"
    bl_label = "Mirror all cutters"
    bl_options = {'REGISTER', 'UNDO'}

    ui_management = None

    def modal(self, context, event):
        self.ui_management.refresh_ui_items_list()

        self.events = self.ui_management.event_dico_refresh(event)

        context.area.tag_redraw()

        if pass_through(event):
            return {'PASS_THROUGH'}

        # action des boutons
        action = self.ui_management.get_button_action()[0]
        self.all_fluent_adjustments[0].adjust(self.ui_management)
        for i, fa in enumerate(self.all_fluent_adjustments):
            if i != 0:
                fa.adjust(self.ui_management, show_menu=False)

        if event.type == 'ESC' and event.value == 'PRESS':
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            return {'FINISHED'}

        if (event.type == 'Q' and event.value == 'PRESS') or action == 'FINISHED' or action == 'VALIDATE':
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            return {'FINISHED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        # vérifications
        if not active_object():
            make_oops([translate('selectAtLeastOneObject')], title=translate('howToUse'), icon='ERROR')

            return {'FINISHED'}

        # VARIABLES
        self.obj = active_object()
        self.all_fluent_adjustments = []

        self.ui_management = FLUENT_ui_management(event)

        button = make_button('CANCEL')
        self.ui_management.add_items(button)

        for m in self.obj.modifiers:
            if m.type == 'BOOLEAN':
                cutter = m.object
                if cutter.get('fluent_type'):
                    self.all_fluent_adjustments.append(modifiers_manager(obj=cutter, bool_target=self.obj))
        if self.all_fluent_adjustments:
            for fa in self.all_fluent_adjustments:
                fa.set_adjust_what('MIRROR')

            self._handle = bpy.types.SpaceView3D.draw_handler_add(draw_callback_px, (self, context), 'WINDOW',
                                                                  'POST_PIXEL')
            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        else:
            make_oops([translate('noFluentBooleanFound')], title=translate('info'), icon='ERROR')

            return {'CANCELLED'}
