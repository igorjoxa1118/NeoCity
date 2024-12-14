import math

import bpy
from bpy.types import Operator
from bpy.props import StringProperty

from .UI.Helpers.viewport_drawing import *
from .drawing import *
from .modifiers import *
from .bevels import *
from .Tools.independant_helper import *

# TODO pourvoir faire des presets

class FLUENT_OT_Cutter(Operator):
    bl_idname = "fluent.cutter"
    bl_label = "Fluent cutter"
    bl_options = {'REGISTER', 'UNDO'}

    operation: StringProperty(
        default='CUT'
    )
    ui_management = None
    drawing = None

    def init_variables(self, event):
        self.ui_management = FLUENT_ui_management(event)

        depsgraph = bpy.context.evaluated_depsgraph_get()

        if active_object('GET') and active_object('GET').select_get():
            self.cut_object = active_object('GET')
            remove_empty_bool_modifier(self.cut_object)
            use_auto_smooth(self.cut_object.data)
            self.cut_object_eval = self.cut_object.evaluated_get(depsgraph)
        else:
            self.cut_object = None

        self.bool_obj = None
        self.fluent_adjustments = None

        self.drawing = FLUENT_Drawing()
        self.ui_management.add_items(self.drawing)

        self.statut = 'EN_ATTENTE_DU_DESSIN'

        self.slider_origin = None

        self.drawing_plane_saved_matrix = None
        self.drawing_plane_saved_vertices_position = []

        button = make_button('CANCEL')
        self.ui_management.add_items(button)

        rectangle_drawing_button = FLUENT_Ui_Button()
        rectangle_drawing_button.set_text('')
        rectangle_drawing_button.set_tool_tip(translate('rectangleShortCut'))
        rectangle_drawing_button.set_shape('CIRCLE')
        rectangle_drawing_button.set_action('RECTANGLE')
        rectangle_drawing_button.set_icon('rectangle')
        rectangle_drawing_button.set_active(True)

        circle_drawing_button = FLUENT_Ui_Button()
        circle_drawing_button.set_text('')
        circle_drawing_button.set_tool_tip(translate('circleShortCut'))
        circle_drawing_button.set_shape('CIRCLE')
        circle_drawing_button.set_action('PRISM')
        circle_drawing_button.set_icon('prism')

        sphere_drawing_button = FLUENT_Ui_Button()
        sphere_drawing_button.set_text('')
        sphere_drawing_button.set_tool_tip(translate('sphere'))
        sphere_drawing_button.set_shape('CIRCLE')
        sphere_drawing_button.set_action('SPHERE')
        sphere_drawing_button.set_icon('sphere')

        shape_drawing_button = FLUENT_Ui_Button()
        shape_drawing_button.set_text('')
        shape_drawing_button.set_tool_tip(translate('shapeShortCut'))
        shape_drawing_button.set_shape('CIRCLE')
        shape_drawing_button.set_action('SHAPE')
        shape_drawing_button.set_icon('shape')

        revolver_drawing_button = FLUENT_Ui_Button()
        revolver_drawing_button.set_text('')
        revolver_drawing_button.set_tool_tip(translate('revolver'))
        revolver_drawing_button.set_shape('CIRCLE')
        revolver_drawing_button.set_action('REVOLVER')
        revolver_drawing_button.set_icon('revolver')

        inset_2_button = FLUENT_Ui_Button()
        inset_2_button.set_text('')
        inset_2_button.set_tool_tip(translate('faceInset'))
        inset_2_button.set_shape('CIRCLE')
        inset_2_button.set_action('INSET_2')
        inset_2_button.set_icon('inset_2')

        creation_button = FLUENT_Ui_Button()
        creation_button.set_text('')
        creation_button.set_tool_tip(translate('creation'))
        creation_button.set_shape('CIRCLE')
        creation_button.set_action('CREATION')
        creation_button.set_icon('creation')
        if self.operation == 'CREATION':
            creation_button.set_active(True)

        cut_button = FLUENT_Ui_Button()
        cut_button.set_text('')
        cut_button.set_tool_tip(translate('cutAdd'))
        cut_button.set_shape('CIRCLE')
        cut_button.set_action('CUT')
        cut_button.set_icon('cut')
        if self.operation == 'CUT':
            cut_button.set_active(True)

        slice_button = FLUENT_Ui_Button()
        slice_button.set_text('')
        slice_button.set_tool_tip(translate('slice'))
        slice_button.set_shape('CIRCLE')
        slice_button.set_action('SLICE')
        slice_button.set_icon('slice')
        if self.operation == 'SLICE':
            slice_button.set_active(True)

        inset_button = FLUENT_Ui_Button()
        inset_button.set_text('')
        inset_button.set_tool_tip(translate('inset'))
        inset_button.set_shape('CIRCLE')
        inset_button.set_action('INSET')
        inset_button.set_icon('inset')
        if self.operation == 'INSET':
            inset_button.set_active(True)

        row = FLUENT_Ui_Layout('DESSIN')
        row.add_item(creation_button)
        row.add_item(cut_button)
        row.add_item(slice_button)
        row.add_item(inset_button)
        row.add_item(rectangle_drawing_button)
        row.add_item(circle_drawing_button)
        row.add_item(sphere_drawing_button)
        row.add_item(shape_drawing_button)
        row.add_item(revolver_drawing_button)
        row.add_item(inset_2_button)
        row.spread()
        self.ui_management.add_items(row)
        #############################################################################
        widget_rotation = FLUENT_Ui_Layout('GRID_ROTATION')
        widget_rotation.set_obj(self.drawing.get_drawing_plane())

        button = make_button('VALIDATE')
        button.set_action('VALIDATE_ROTATION')
        widget_rotation.add_item(button)

        button = FLUENT_Ui_Button()
        button.set_text('')
        button.set_shape('CIRCLE')
        button.set_action('+X_ROT')
        button.set_default_color((.9, 0, 0, 1))
        widget_rotation.add_item(button)

        button = FLUENT_Ui_Button()
        button.set_text('')
        button.set_shape('CIRCLE')
        button.set_action('+Y_ROT')
        button.set_default_color((0, .9, 0, 1))
        widget_rotation.add_item(button)

        button = FLUENT_Ui_Button()
        button.set_text('')
        button.set_shape('CIRCLE')
        button.set_action('+Z_ROT')
        button.set_default_color((0, 0, .9, 1))
        widget_rotation.add_item(button)

        widget_rotation.set_layout('TAPER')
        self.rot_grid_widget = widget_rotation
        ######################################################################
        #############################################################################
        widget_move = FLUENT_Ui_Layout('GRID_MOVE')
        widget_move.set_obj(self.drawing.get_drawing_plane())

        button = make_button('VALIDATE')
        button.set_action('VALIDATE_MOVE')
        widget_move.add_item(button)

        button = FLUENT_Ui_Button()
        button.set_text('')
        button.set_shape('CIRCLE')
        button.set_action('+X_MOVE')
        button.set_default_color((.9, 0, 0, 1))
        widget_move.add_item(button)

        button = FLUENT_Ui_Button()
        button.set_text('')
        button.set_shape('CIRCLE')
        button.set_action('+Y_MOVE')
        button.set_default_color((0, .9, 0, 1))
        widget_move.add_item(button)

        widget_move.set_layout('TAPER')
        self.move_grid_widget = widget_move
        ######################################################################
        #############################################################################
        widget_scale = FLUENT_Ui_Layout('GRID_SCALE')
        widget_scale.set_obj(self.drawing.get_drawing_plane())

        button = make_button('VALIDATE')
        button.set_action('VALIDATE_SCALE')
        widget_scale.add_item(button)

        button = FLUENT_Ui_Button()
        button.set_text('')
        button.set_shape('CIRCLE')
        button.set_action('+X_SCALE')
        button.set_default_color((.9, 0, 0, 1))
        widget_scale.add_item(button)

        button = FLUENT_Ui_Button()
        button.set_text('')
        button.set_shape('CIRCLE')
        button.set_action('+Y_SCALE')
        button.set_default_color((0, .9, 0, 1))
        widget_scale.add_item(button)

        button = FLUENT_Ui_Button()
        button.set_text('')
        button.set_shape('CIRCLE')
        button.set_action('+Z_SCALE')
        button.set_default_color((0, 0, .9, 1))
        widget_scale.add_item(button)

        widget_scale.set_layout('TAPER')
        self.scale_grid_widget = widget_scale
        ######################################################################
        column = FLUENT_Ui_Layout('GRID_MANIPULATION')

        button = FLUENT_Ui_Button()
        button.set_text('')
        button.set_tool_tip(translate('rotation'))
        button.set_shape('CIRCLE')
        button.set_action('GRID_ROTATION')
        button.set_icon('rotation')
        column.add_item(button)

        button = FLUENT_Ui_Button()
        button.set_text('')
        button.set_tool_tip(translate('move'))
        button.set_shape('CIRCLE')
        button.set_action('GRID_MOVE')
        button.set_icon('move')
        column.add_item(button)

        button = FLUENT_Ui_Button()
        button.set_text('')
        button.set_tool_tip(translate('scale'))
        button.set_shape('CIRCLE')
        button.set_action('GRID_SCALE')
        button.set_icon('scale')
        column.add_item(button)

        button = FLUENT_Ui_Button()
        button.set_text('')
        button.set_tool_tip(translate('alignShortCut'))
        button.set_shape('CIRCLE')
        button.set_action('GRID_ALIGN')
        button.set_icon('align')
        column.add_item(button)

        button = FLUENT_Ui_Button()
        button.set_text('')
        button.set_tool_tip('resolutionShortCut')
        button.set_shape('CIRCLE')
        button.set_action('GRID_RESOLUTION')
        button.set_icon('grid_resolution')
        column.add_item(button)

        button = FLUENT_Ui_Button()
        button.set_text('')
        button.set_tool_tip(translate('square'))
        button.set_shape('CIRCLE')
        button.set_action('GRID_SQUARE')
        button.set_icon('to_square')
        column.add_item(button)

        button = FLUENT_Ui_Button()
        button.set_text('')
        button.set_tool_tip(translate('alignToView'))
        button.set_shape('CIRCLE')
        button.set_action('GRID_VIEW')
        button.set_icon('align_view')
        column.add_item(button)

        button = FLUENT_Ui_Button()
        button.set_text('')
        button.set_tool_tip(translate('extendShortCut'))
        button.set_shape('CIRCLE')
        button.set_action('GRID_EXTENDED')
        button.set_icon('extend')
        button.set_active(True)
        column.add_item(button)

        column.set_layout('COLUMN_LEFT')
        column.spread()

        self.grid_manipulation = column

        self.cursor_infos = FLUENT_Cursor_Infos()
        self.ui_management.add_items(self.cursor_infos)

    def change_de_dessin(self, a):
        self.drawing.set_the_draw_type(a)

    def end(self, option='FINISHED'):
        if self.drawing.get_the_draw()['obj']:
            try:
                bpy.data.objects.remove(self.drawing.get_the_draw()['obj'], do_unlink=True)
            except:
                pass
        if self.drawing.get_drawing_plane():
            try:
                bpy.data.objects.remove(self.drawing.get_drawing_plane(), do_unlink=True)
            except:
                pass

        bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')


        try:
            active_object('SET', self.cut_object, True)
        except:pass

    def modal(self, context, event):
        self.ui_management.refresh_ui_items_list()
        events = self.ui_management.event_dico_refresh(event)

        context.area.tag_redraw()

        if pass_through(event):
            return {'PASS_THROUGH'}
        if bpy.context.active_object and bpy.context.active_object.mode == 'EDIT':
            return {'PASS_THROUGH'}

        # action via les bouttons
        action = self.ui_management.get_button_action()[0]

        # action via les raccourcis clavier
        if not events['shift_work']:# Toutes actions sans shift
            if event.type == 'S' and    event.value == 'PRESS':
                action = 'SHAPE'
            elif event.type == 'C' and event.value == 'PRESS' and 'ALIGN' not in self.statut:
                action = 'PRISM'
            elif event.type == 'R' and event.value == 'PRESS':
                action = 'RECTANGLE'
            elif event.type == 'Q' and event.value == 'PRESS':
                action = 'FINISHED'
            elif event.type == 'X' and event.value == 'PRESS':
                action = 'GRID_EXTENDED'
            elif event.type == 'ESC' and event.value == 'PRESS':
                action = 'FINISHED'
            elif event.type == 'W' and event.value == 'PRESS':
                try:
                    if self.cut_object.show_wire:
                        self.cut_object.show_wire = False
                    else:
                        self.cut_object.show_wire = True
                except:pass

        if events['shift_work']:
            if event.type == 'R' and event.value == 'PRESS':
                action = 'GRID_X_ROT_45'

        if action:
            events['type'] = events['value'] = ''
            if action in ['FINISHED', 'CANCELLED']:
                self.end()
                return {'FINISHED'}
            elif action in ['RECTANGLE', 'PRISM', 'SHAPE', 'REVOLVER', 'SPHERE']:
                self.change_de_dessin(action)
                # desactive les autres
                self.ui_management.set_button_active(action)
            elif action == 'INSET_2':
                self.end()
                active_object('SET', self.cut_object, True)
                bpy.ops.fluent.faceextraction('INVOKE_DEFAULT', call_by='CUT')
                return {'FINISHED'}
            elif action in ['CUT', 'SLICE', 'INSET', 'CREATION']:
                self.operation = action
                # desactive les autres
                self.ui_management.set_button_active(action)
            elif action == 'GRID_ROTATION':
                self.ui_management.remove_items(['GRID_MOVE', 'GRID_SCALE', 'GRID_ROTATION'])
                self.drawing.grid_to_square()
                self.rot_grid_widget.set_obj(self.drawing.get_drawing_plane())
                self.ui_management.add_items(self.rot_grid_widget)
            elif action == 'GRID_MOVE':
                self.ui_management.remove_items(['GRID_ROTATION', 'GRID_SCALE', 'GRID_MOVE'])
                self.drawing.grid_to_square()
                self.move_grid_widget.set_obj(self.drawing.get_drawing_plane())
                self.ui_management.add_items(self.move_grid_widget)
            elif action == 'GRID_SCALE':
                self.ui_management.remove_items(['GRID_MOVE', 'GRID_ROTATION', 'GRID_SCALE'])
                self.drawing.grid_to_square()
                self.scale_grid_widget.set_obj(self.drawing.get_drawing_plane())
                self.ui_management.add_items(self.scale_grid_widget)
            elif action == 'GRID_ALIGN':
                self.statut = 'GRID_ADJUSTMENT_ALIGN'
            elif action == 'VALIDATE_ROTATION':
                self.ui_management.remove_items(['GRID_ROTATION'])
            elif action == 'VALIDATE_MOVE':
                self.ui_management.remove_items(['GRID_MOVE'])
            elif action == 'VALIDATE_SCALE':
                self.ui_management.remove_items(['GRID_SCALE'])
            elif action in ['+Z_ROT', '+X_ROT', '+Y_ROT']:
                self.statut = 'GRID_ADJUSTMENT' + '_ROTATION_' + action
                self.slider_origin = events['mouse_x']
                self.drawing_plane_saved_matrix = self.drawing.get_drawing_plane().matrix_world.copy()
            elif action == 'GRID_X_ROT_45':
                angle = 45
                drawing_plane = self.drawing.get_drawing_plane()
                if drawing_plane:
                    if not drawing_plane.get('original_normal'):
                        normal_avant = drawing_plane.data.polygons[0].normal
                        normal_avant = local_to_global_co(drawing_plane, normal_avant) - drawing_plane.location
                        drawing_plane['original_normal'] = normal_avant
                    normal_avant = Vector((drawing_plane['original_normal'][0], drawing_plane['original_normal'][1], drawing_plane['original_normal'][2]))
                    self.drawing.plane_rotation('X', angle)
                    depsgraph = bpy.context.evaluated_depsgraph_get()
                    depsgraph.update()
                    normal_apres = drawing_plane.data.polygons[0].normal
                    normal_apres = local_to_global_co(drawing_plane, normal_apres) - drawing_plane.location
                    if produit_scalaire(normal_avant, normal_apres)<0:
                        self.drawing.plane_rotation('X', 180)
            elif action in ['+Z_MOVE', '+X_MOVE', '+Y_MOVE']:
                self.statut = 'GRID_ADJUSTMENT' + '_MOVE_' + action
                self.slider_origin = events['mouse_x']
                self.drawing_plane_saved_matrix = self.drawing.get_drawing_plane().matrix_world.copy()
            elif action in ['+Z_SCALE', '+X_SCALE', '+Y_SCALE']:
                self.statut = 'GRID_ADJUSTMENT' + '_SCALE_' + action
                self.slider_origin = events['mouse_x']
                self.drawing_plane_saved_vertices_position = [v.co.copy() for v in
                                                              self.drawing.get_drawing_plane().data.vertices]
            elif action == 'GRID_RESOLUTION':
                self.statut = 'GRID_ADJUSTMENT_RESOLUTION'
                self.slider_origin = events['mouse_x']
            elif action == 'GRID_MOVE':
                self.statut = 'GRID_ADJUSTMENT_MOVE'
                self.slider_origin = events['mouse_x']
            elif action == 'GRID_SQUARE':
                self.drawing.grid_to_square()
            elif action == 'GRID_EXTENDED':
                self.drawing.set_extended(not self.drawing.get_extended())
                buttons = self.grid_manipulation.get_items()
                extended_button = [b for b in buttons if b.get_action() == 'GRID_EXTENDED'][0]
                if self.drawing.get_extended():
                    extended_button.set_active(True)
                else:
                    extended_button.set_active(False)
            elif action == 'GRID_VIEW':
                self.drawing.set_align_to_view(not self.drawing.get_align_to_view())
                self.drawing.grid_init(self.cut_object, events)
        else:
            if self.statut == 'EN_ATTENTE_DU_DESSIN':
                if self.drawing.get_statut() == 'TERMINE':
                    self.statut = 'DESSIN_TERMINE'
                    self.bool_obj = self.drawing.get_the_draw()['obj']

                # clique droit sur une face affiche la grille clique gauche lance le dessin
                # si aucun widget n'est affiché
                current_item = self.ui_management.get_current_item()
                if not (type(current_item) is FLUENT_Ui_Layout and current_item.get_id() in ['GRID_ROTATION', 'GRID_SCALE', 'GRID_MOVE']):
                    self.drawing.process(events)
                    if (self.drawing.get_statut() == None and events['value'] == 'PRESS' and events['type'] in ['RIGHTMOUSE', 'LEFTMOUSE']):
                        self.drawing.reset()
                        success = self.drawing.grid_init(self.cut_object, events)
                        if success:
                            if event.value == 'PRESS' and event.type == 'RIGHTMOUSE':
                                self.drawing.set_display_grid(True)
                                self.rot_grid_widget.set_obj(self.drawing.get_drawing_plane())
                                self.ui_management.add_items(self.grid_manipulation)
                                if event.shift:
                                    self.drawing.set_display_dots(False)
                                else:
                                    self.drawing.set_display_dots(True)
                            self.drawing.process(events)
                    elif (self.drawing.get_statut() in ['EN_ATTENTE', 'GRILLE_OK'] and events['value'] == 'PRESS' and events['type'] in ['RIGHTMOUSE']):
                        self.drawing.reset()
                        success = self.drawing.grid_init(self.cut_object, events)
                        if success:
                            self.drawing.set_display_grid(True)
                            self.ui_management.add_items(self.grid_manipulation)
                            if event.shift:
                                self.drawing.set_display_dots(False)
                            else:
                                self.drawing.set_display_dots(True)
                            self.drawing.process(events)
                    elif events['value'] == 'PRESS' and events['type'] == 'ESC':
                        self.drawing.reset()
            elif self.statut == 'DESSIN_TERMINE':
                bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
                active_object(action='SET', obj=self.bool_obj, solo=True)
                if self.bool_obj['fluent_type'] != 'revolver':
                    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
                if self.cut_object and len(self.cut_object.data.polygons) and self.cut_object.data.polygons[0].use_smooth:
                    for p in self.bool_obj.data.polygons:
                        p.use_smooth = True
                use_auto_smooth(self.bool_obj.data)

                if self.operation != 'CREATION' and self.cut_object:
                    if get_addon_preferences().auto_parent:
                        parent_relationship(self.cut_object, self.bool_obj)
                    add_in_bool_collection(self.bool_obj)
                    boolean_visibility_setup(self.bool_obj)
                    bpy.ops.fluent.editor('INVOKE_DEFAULT', bool_obj_name=self.bool_obj.name,
                                          cut_obj_name=self.cut_object.name, operation=self.operation)
                else:
                    self.bool_obj.hide_render = False
                    bpy.ops.fluent.editor('INVOKE_DEFAULT', bool_obj_name=self.bool_obj.name, cut_obj_name='',
                                          operation='CREATION')
                return {'FINISHED'}
            elif 'GRID_ADJUSTMENT' in self.statut:
                if 'ROTATION' in self.statut:
                    if events['type'] == 'MOUSEMOVE':
                        self.drawing.get_drawing_plane().matrix_world = self.drawing_plane_saved_matrix
                        delta = (events['mouse_x'] - self.slider_origin) / 4
                        if 'Z' in self.statut:
                            t = self.drawing.plane_rotation('Z', delta)
                        if 'X' in self.statut:
                            t = self.drawing.plane_rotation('X', delta)
                        if 'Y' in self.statut:
                            t = self.drawing.plane_rotation('Y', delta)
                        self.cursor_infos.set_text([str(t) + '°'])
                elif 'MOVE' in self.statut:
                    if events['shift_press'] or events['shift_release'] or events['ctrl_press'] or events['ctrl_release']:
                        self.slider_origin = events['mouse_x']
                        self.drawing_plane_saved_matrix = self.drawing.get_drawing_plane().matrix_world.copy()
                    if events['type'] == 'MOUSEMOVE':
                        if events['shift_work']:
                            increment = 1000
                        elif events['ctrl_work']:
                            increment = 10
                        else:
                            increment = 100
                        self.drawing.get_drawing_plane().matrix_world = self.drawing_plane_saved_matrix
                        delta = (events['mouse_x'] - self.slider_origin) / increment
                        if 'X' in self.statut:
                            self.drawing.plane_move('X', delta)
                        if 'Y' in self.statut:
                            self.drawing.plane_move('Y', delta)
                elif 'SCALE' in self.statut:
                    if events['shift_press'] or events['shift_release'] or events['ctrl_press'] or events['ctrl_release']:
                        self.slider_origin = events['mouse_x']
                        self.drawing_plane_saved_matrix = self.drawing.get_drawing_plane().matrix_world.copy()
                    if events['type'] == 'MOUSEMOVE':
                        if events['shift_work']:
                            increment = 1000
                        elif events['ctrl_work']:
                            increment = 10
                        else:
                            increment = 100
                        for i, v in enumerate(self.drawing.get_drawing_plane().data.vertices):
                            v.co = self.drawing_plane_saved_vertices_position[i]
                        delta = (events['mouse_x'] - self.slider_origin) / increment
                        self.slider_origin = events['mouse_x']
                        if 'X' in self.statut:
                            self.drawing.plane_scale('X', delta)
                        elif 'Y' in self.statut:
                            self.drawing.plane_scale('Y', delta)
                        elif 'Z' in self.statut:
                            self.drawing.plane_scale('XY', delta)
                elif 'RESOLUTION' in self.statut:
                    self.cursor_infos.set_text([translate('resolution'), str(self.drawing.get_resolution())])
                    if events['mouse_x'] - self.slider_origin > 50:
                        self.drawing.set_resolution(self.drawing.get_resolution() + 1)
                        self.slider_origin = events['mouse_x']
                    elif events['mouse_x'] - self.slider_origin < -50:
                        self.drawing.set_resolution(self.drawing.get_resolution() - 1)
                        self.slider_origin = events['mouse_x']
                elif 'ALIGN' in self.statut:
                    mode_text = translate('linearMode')
                    if self.drawing.align_diagonal:
                        mode_text = translate('diagonalMode')

                    self.cursor_infos.set_text([
                        translate('alignToGrid'),
                        translate('clickTwoVertices'),
                        mode_text
                    ])
                    step = None
                    if event.value == 'PRESS' and event.type == 'C':
                        self.drawing.align_diagonal = not self.drawing.align_diagonal

                    if event.value == 'PRESS' and event.type == 'LEFTMOUSE':
                        step = self.drawing.grid_align(events)
                    if step == 'FINISHED':
                        self.drawing.align_diagonal = False
                        self.statut = 'EN_ATTENTE_DU_DESSIN'
                        self.cursor_infos.set_text([])
                if event.value == 'PRESS' and event.type == 'LEFTMOUSE' \
                    and not 'ALIGN' in self.statut:
                    self.statut = 'EN_ATTENTE_DU_DESSIN'
                    self.cursor_infos.set_text([])

        if events['type'] == 'V' and events['value'] == 'PRESS' and self.statut != 'GRID_ADJUSTMENT_RESOLUTION':
            self.statut = 'GRID_ADJUSTMENT_RESOLUTION'
            self.slider_origin = events['mouse_x']
        elif (events['type'] == 'V' and events['value'] == 'RELEASE' or events['type'] == 'LEFTMOUSE' and events['value'] == 'RELEASE') and self.statut == 'GRID_ADJUSTMENT_RESOLUTION':
            self.statut = 'EN_ATTENTE_DU_DESSIN'
            self.cursor_infos.set_text([])
        elif events['type'] == 'A' and events['value'] == 'PRESS' and self.statut == 'EN_ATTENTE_DU_DESSIN':
            self.statut = 'GRID_ADJUSTMENT_ALIGN'

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        # VERIFICATIONS
        try:
            bpy.ops.object.mode_set(mode='OBJECT')
        except:
            pass

        # test si uniquement des objets sont sélectionnés
        for o in bpy.context.selected_objects:
            if o.type not in ['MESH']:
                make_oops([translate('nonObjectThing')], title=translate('howToUse'), icon='ERROR')
                return {'FINISHED'}

        # test si dans le preview
        if not context.area.type == 'VIEW_3D':
            make_oops([translate('previewNotFound')], title=translate('howToUse'), icon='ERROR')
            return {'FINISHED'}

        self.init_variables(event)

        args = (self, context)

        # self.timer = context.window_manager.event_timer_add(1/25, window=context.window)
        self._handle = bpy.types.SpaceView3D.draw_handler_add(draw_callback_px, args, 'WINDOW', 'POST_PIXEL')
        context.window_manager.modal_handler_add(self)

        return {'RUNNING_MODAL'}


class FLUENT_OT_CutStarter(Operator):
    """Cut/Add"""
    bl_idname = "fluent.cutstarter"
    bl_label = "Cut"

    def invoke(self, context, event):
        bpy.ops.fluent.cutter('INVOKE_DEFAULT', operation='CUT')
        return {'FINISHED'}


class FLUENT_OT_SliceStarter(Operator):
    """Slice"""
    bl_idname = "fluent.slicestarter"
    bl_label = "Slice"

    def invoke(self, context, event):
        bpy.ops.fluent.cutter('INVOKE_DEFAULT', operation='SLICE')
        return {'FINISHED'}


class FLUENT_OT_InsetStarter(Operator):
    """Inset"""
    bl_idname = "fluent.insetstarter"
    bl_label = "Inset"

    def invoke(self, context, event):
        bpy.ops.fluent.cutter('INVOKE_DEFAULT', operation='INSET')
        return {'FINISHED'}


class FLUENT_OT_CreateStarter(Operator):
    """Creation"""
    bl_idname = "fluent.createstarter"
    bl_label = "Creation"

    def invoke(self, context, event):
        bpy.ops.fluent.cutter('INVOKE_DEFAULT', operation='CREATION')
        return {'FINISHED'}


class FLUENT_OT_BooleanOperator(Operator):
    """Boolean operation between 2 objects"""
    bl_idname = "fluent.booleanoperator"
    bl_label = "Boolean"
    bl_options = {'REGISTER', 'UNDO'}

    def verification(self):
        callback = []

        try:
            bpy.ops.object.mode_set(mode='OBJECT')
        except:
            pass

        # test si uniquement des objets sont sélectionnés
        for i, o in enumerate(bpy.context.selected_objects):
            if o.type != 'MESH':
                make_oops([translate('nonObjectThing')], title=translate('howToUse'), icon='ERROR')
                callback.append('FINISHED')

        # test si seulement 2 objets sont sélectionnés
        if i != 1:
            make_oops([translate('selectTwoObjects')], title=translate('howToUse'), icon='ERROR')
            callback.append('FINISHED')

        # test si dans le preview
        if not bpy.context.area.type == 'VIEW_3D':
            make_oops([translate('previewNotFound')], title=translate('howToUse'), icon='ERROR')
            callback.append('FINISHED')

        return callback

    def invoke(self, context, event):
        callback = self.verification()
        if 'FINISHED' in callback:
            return {'FINISHED'}

        self.cut_object = active_object(action='GET')
        for o in bpy.context.selected_objects:
            if o != self.cut_object:
                self.bool_obj = o

        self.operation = '*CUT'

        # test si le type n'est pas déjà définit
        try:
            self.bool_obj['fluent_type']
        except:
            self.bool_obj['fluent_type'] = 'unknow'

        add_in_bool_collection(self.bool_obj)
        self.bool_obj.display_type = 'WIRE'
        self.bool_obj.hide_set(True)
        self.bool_obj.hide_render = True
        if self.bool_obj.parent is None:
            parent_relationship(self.cut_object, self.bool_obj)
        bpy.ops.fluent.editor('INVOKE_DEFAULT', bool_obj_name=self.bool_obj.name, cut_obj_name=self.cut_object.name,
                              operation=self.operation)
        return {'FINISHED'}


class FLUENT_OT_BooleanDisplay(Operator):
    """Show/Hide boolean objects"""
    bl_idname = "fluent.booleandisplay"
    bl_label = "Boolean visibility"
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):
        affichage_booleen()

        return {'FINISHED'}


class FLUENT_OT_AddLatestBevel(Operator):
    """Add a bevel
Hold Shift - Remove all bevels"""
    bl_idname = "fluent.addlatestbevel"
    bl_label = "Add the latest bevel"
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):
        if active_object('GET'):
            if bpy.context.active_object.mode == 'EDIT':
                make_oops([translate('onlyInObjectMode')], title=translate('info'), icon='ERROR')
                return {'CANCELLED'}
            for obj in bpy.context.selected_objects:
                if not obj.type == 'MESH':
                    continue
                bevel = F_outer_bevel()
                bevel.set_target(obj)
                bevel.first_as_current()
                if event.shift:
                    bevel.remove('ALL')
                else:
                    if not bevel.get_first_bevel():
                        bevel.add()
                        bevel.set_width(bpy.context.scene.fluentProp.width)
                    else:
                        bevel.set_width(bpy.context.scene.fluentProp.width)
        return {'FINISHED'}


class FLUENT_OT_TechnicalDisplay(Operator):
    """Show/Hide wireframe + boolean objects"""
    bl_idname = "fluent.technicaldisplay"
    bl_label = "Technical display"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.fluent.wireframedisplay('INVOKE_DEFAULT')
        bpy.ops.fluent.booleandisplay('INVOKE_DEFAULT')
        return {'FINISHED'}


class FLUENT_OT_WireframeDisplay(Operator):
    """Show/Hide wireframe"""
    bl_idname = "fluent.wireframedisplay"
    bl_label = "Wireframe display"
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):
        if active_object(action='GET'):
            if bpy.context.object.show_wire == True:
                for o in bpy.context.selected_objects:
                    o.show_wire = False
                    o.show_all_edges = False
            else:
                for o in bpy.context.selected_objects:
                    o.show_wire = True
                    o.show_all_edges = True
        return {'FINISHED'}


class FLUENT_OT_AutoCompleteOne(Operator):
    """Completes your model.
Copy the object and apply every modifier.

Hold Ctrl - to apply without duplication.
Hold Alt - to keep the outer bevel as modifier.
Hold Shift - to remove the outer bevels.
Hold Ctrl+Shift - to revert to non-destructive."""
    bl_idname = "fluent.autocompleteone"
    bl_label = "Autocomplete"
    bl_options = {'REGISTER', 'UNDO'}

    from_normal_repair: bpy.props.BoolProperty(
        description="from_normal_repair",
        name="from_normal_repair",
        default=False
    )

    def macro(self):
        # mark sharp, seams, unwrap
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type='EDGE')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.edges_select_sharp(sharpness=0.610865)
        if not self.from_normal_repair:
            bpy.ops.mesh.mark_sharp()
        bpy.ops.mesh.mark_seam(clear=False)
        bpy.ops.mesh.select_mode(type='FACE')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.unwrap(method='CONFORMAL', fill_holes=True, correct_aspect=False, margin=0.003)
        bpy.ops.object.mode_set(mode='OBJECT')

    def mark_seam_in_cylinder(self, obj):
        # mark seam sur rayon avant solidify
        active_object(obj, 'SET', True)
        for mm in obj.modifiers:
            if mm.name != 'First_Solidify':
                if mm.type != 'BOOLEAN':
                    if mm.show_render:
                        try:
                            bpy.ops.object.modifier_apply(modifier=mm.name)
                        except:
                            obj.modifiers.remove(mm)
                    else:
                        obj.modifiers.remove(mm)
            else:
                # trouve un rayon et mark seam
                length = 0
                i = 0
                for e in obj.data.edges:
                    vertices = obj.data.vertices
                    v1 = vertices[e.vertices[0]]
                    v2 = vertices[e.vertices[1]]
                    next_length = length_between(
                        v1.co.x, v1.co.y, v2.co.x, v2.co.y)
                    if next_length > length:
                        length = next_length
                        if i >= 1:
                            first_seam = e
                            # mark seam et applique le solidify
                            e.use_seam = True
                            try:
                                bpy.ops.object.modifier_apply(modifier=mm.name)
                            except:
                                obj.modifiers.remove(mm)
                            break
                    i += 1
                # mark l'edge entre les 2 rayons
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_mode(type='EDGE')
                bpy.ops.mesh.select_all(action='DESELECT')
                bpy.ops.object.mode_set(mode='OBJECT')
                for e in obj.data.edges:
                    if e.use_seam:
                        e.select = True
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.loop_multi_select(ring=False)
                bpy.ops.mesh.mark_seam(clear=False)
                bpy.ops.object.mode_set(mode='OBJECT')

    def cylinder(self, obj):
        # ajout de seams sur les coupes cylindriques
        # si boolean → regarde l'objet → si cylindre → duplique l'objet et l'utilise à la place → routine d'ajout de seam
        copy_list = []
        bool_list = []
        for m in obj.modifiers:
            if m.type == 'BOOLEAN' and m.object:
                bool = m.object
                bool_visibility = bool.hide_viewport
                bool_list.append([bool, bool_visibility])
                # if bool.get('fluent_type') == 'prism':
                #     bool.hide_viewport = False
                #     # active_object(bool, 'SET', True)
                #     # bpy.ops.object.duplicate()
                #     # copy = active_object(action='GET')
                #     copy = duplicate(bool)
                #     copy_list.append(copy)
                #     m.object = copy
                #     active_object(copy, 'SET', True)
                #     self.mark_seam_in_cylinder(copy)

        return copy_list, bool_list

    def autocomplete(self, obj, alt=False, shift=False, ctrl=False):
        # ctrl → pas de duplication
        # alt → garde le dernier bevel
        # shift → retire le dernier bevel

        # TODO pouvoir marker les seems dans les cylindres.
        # if obj.get('fluent_type') in {'prism'}:
        #     self.mark_seam_in_cylinder(obj)

        if ctrl or self.from_normal_repair:
            obj_completed = obj
            if not self.from_normal_repair:
                obj_completed.name += '.frozen'
        else:
            active_object('SET', obj, True)
            bpy.ops.object.duplicate()
            obj_completed = active_object('GET')
            obj_completed.name = obj.name + '.frozen'
            obj.hide_render = True
            obj.hide_set(True)
            obj_completed.hide_render = False
            obj_completed.hide_set(False)

        bevel = None
        weighted_normal = None
        if alt:
            modifiers_count = len(obj_completed.modifiers)
            if modifiers_count >= 2 and fluent_modifiers_name['outer_bevel'] in obj_completed.modifiers[
                modifiers_count - 2].name and obj_completed.modifiers[modifiers_count - 1].type == 'WEIGHTED_NORMAL':
                bevel = get_modifier_values(obj.modifiers[modifiers_count - 2])
                weighted_normal = get_modifier_values(obj_completed.modifiers[modifiers_count - 1])
                obj_completed.modifiers.remove(obj_completed.modifiers[len(obj_completed.modifiers) - 1])
                obj_completed.modifiers.remove(obj_completed.modifiers[len(obj_completed.modifiers) - 1])
        if shift:
            modifiers_count = len(obj_completed.modifiers)
            if modifiers_count >= 2 and fluent_modifiers_name['outer_bevel'] in obj_completed.modifiers[
                modifiers_count - 2].name and obj_completed.modifiers[modifiers_count - 1].type == 'WEIGHTED_NORMAL':
                obj_completed.modifiers.remove(obj_completed.modifiers[len(obj_completed.modifiers) - 1])
                obj_completed.modifiers.remove(obj_completed.modifiers[len(obj_completed.modifiers) - 1])

        active_object(action='SET', obj=obj_completed, solo=True)
        bpy.ops.object.convert(target='MESH')
        try:
            self.macro()
        except:
            bpy.ops.object.mode_set(mode='OBJECT')

        if bevel:
            bpy.ops.fluent.addlatestbevel('INVOKE_DEFAULT')
            set_modifier_value(obj_completed.modifiers[fluent_modifiers_name['outer_bevel']], bevel)
            set_modifier_value(obj_completed.modifiers[fluent_modifiers_name['weighted_normal']], weighted_normal)

        if obj_completed.get('fluent_obj'):
            obj_completed['fluent_obj'] = 0
        if obj_completed.get('fluent_type'):
            obj_completed['fluent_type'] = 'unknow'

        return obj_completed

    def invoke(self, context, event):
        latest_bevel_obj_list = []
        fluent_object_list = []
        object_completed_list = []

        if len(bpy.context.selected_objects):
            if event.ctrl and event.shift:  # suppression du frozen et réaffichage du non destructif
                for obj in bpy.context.selected_objects:
                    try:
                        original_name = obj.name.split('.frozen')[0]
                        bpy.data.objects.get(original_name).hide_viewport = False
                        bpy.data.objects.get(original_name).hide_render = False
                        bpy.data.objects.get(original_name).hide_set(False)
                        bpy.data.objects.remove(obj, do_unlink=True)
                    except:
                        pass
                return {'FINISHED'}
            if get_addon_preferences().bevel_system == 'MULTIPLE' and event.alt:
                make_oops([translate('altOptionMultiBevel')], title=translate('howToUse'), icon='ERROR')
                return {'CANCELLED'}
            else:
                # liste tous les objets fluent parmi la selection
                for obj in bpy.context.selected_objects:
                    if obj.type in {'MESH'}:
                        fluent_object_list.append(obj)
                for obj in bpy.context.selected_objects:
                    if obj.type in {'CURVE'}:
                        fluent_object_list.append(obj)

                # sélectionne les objets fluent et applique tous les modifiers
                for obj in fluent_object_list:
                    object_completed_list.append(
                        self.autocomplete(obj, ctrl=event.ctrl, alt=event.alt, shift=event.shift))

                # place les objets dans une collection dédiée et les rends visibles au rendu
                if not bpy.data.collections.get('Completed'):
                    coll = bpy.data.collections.new("Completed")
                    bpy.context.scene.collection.children.link(coll)

                for o in object_completed_list:
                    o.hide_render = o.hide_viewport = False
                    try:
                        bpy.context.scene.collection.objects.unlink(o)
                    except:
                        pass
                    try:
                        for c in bpy.data.collections:
                            for oo in c.objects:
                                if oo == o:
                                    c.objects.unlink(o)
                        bpy.data.collections['Completed'].objects.link(o)
                    except:
                        pass

                active_object(object_completed_list[0], 'SET', True)
                return {'FINISHED'}
        else:
            make_oops([translate('selectAtLeastOneObject')], title=translate('howToUse'), icon='ERROR')

            return {'CANCELLED'}


class FLUENT_OT_NormalRepair(Operator):
    """Repair shading artifact
Be careful every modifier will be applied but the original object is kept.

Hold Shift - to remove a repaired object and revert to the live version"""
    bl_idname = "fluent.normalrepair"
    bl_label = "Normal Repair"
    bl_options = {'REGISTER', 'UNDO'}
    ui_management = None

    def make_source(self, obj):
        # réalise une copie sans booléen de l'objet
        self.normal_source_obj = duplicate(obj, name='_normalSource')
        self.normal_source_obj.hide_viewport = False
        if self.root_name:
            bpy.data.objects.get(self.root_name).hide_set(True)
        for m in self.normal_source_obj.modifiers:
            if m.type == 'BOOLEAN':
                self.normal_source_obj.modifiers.remove(m)
        active_object('SET', self.normal_source_obj, True)
        bpy.ops.object.convert(target='MESH')
        self.normal_source_obj.hide_render = True
        self.normal_source_obj.hide_set(True)
        bpy.ops.object.select_all(action='DESELECT')

    def prepare_data_transfer(self, already_fixed=False):
        active_object('SET', self.normal_fixed_obj, True)
        if not already_fixed:
            self.normal_fixed_obj.select_set(True)
            bpy.ops.fluent.autocompleteone('INVOKE_DEFAULT', from_normal_repair=True)
        self.normal_fixed_obj.hide_set(False)
        self.normal_fixed_obj.hide_render = False
        # self.normal_fixed_obj = active_object('GET')
        active_object('SET', self.normal_fixed_obj, solo=True)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type="FACE")
        bpy.ops.mesh.select_all(action="DESELECT")
        bpy.ops.object.mode_set(mode='OBJECT')

        # supprime les vertex groups si déjà présent
        for vg in self.normal_fixed_obj.vertex_groups:
            self.normal_fixed_obj.vertex_groups.remove(vg)
        # création du vertex group
        self.vertex_group = self.normal_fixed_obj.vertex_groups.new(name='NormalRepair')

        modif = self.normal_fixed_obj.modifiers.new(name=fluent_modifiers_name['data_transfer'], type='DATA_TRANSFER')
        modif.object = self.normal_source_obj
        modif.vertex_group = 'NormalRepair'
        modif.use_loop_data = True
        modif.data_types_loops = {'CUSTOM_NORMAL'}
        modif.loop_mapping = 'POLYINTERP_LNORPROJ'
        modif.show_in_editmode = True
        self.vertex_group.remove(
            [v.index for v in self.normal_fixed_obj.data.vertices])
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type="FACE")
        bpy.ops.object.mode_set(mode='OBJECT')

    def modal(self, context, event):
        self.ui_management.refresh_ui_items_list()

        context.area.tag_redraw()
        try:
            self.update_display()
        except:
            pass

        if not event.type in {'RET', 'NUMPAD_ENTER', 'RIGHTMOUSE', 'TAB'} and self.build_step == 2:
            return {'PASS_THROUGH'}
        elif pass_through(event):
            return {'PASS_THROUGH'}

        if self.build_step == 0:  # ajuste le weld
            self.original_obj.modifiers['.f_weld_normal_repair'].merge_threshold = (event.mouse_region_x - self.x_mouse_slider_origin) / 4000
            if event.value == 'PRESS' and event.type == 'LEFTMOUSE':
                self.build_step = 0.5
                bpy.context.object.show_wire = False
                self.ui_management.refresh_side_infos([[translate('step', upperCase=True)+' 2/3', translate('selectNormalSource')]])
                return {'RUNNING_MODAL'}
        elif self.build_step == 0.5:  # affiche les booleans pour sélection de la source
            bpy.ops.fluent.booleandisplay('INVOKE_DEFAULT')
            bpy.ops.object.select_all(action='DESELECT')
            context.view_layer.objects.active = None
            if '_normalFixed' in self.original_obj.name:
                bpy.data.objects.get(self.original_name).hide_set(False)
                self.original_obj.hide_set(True)
                # root_name = self.original_obj.name.split('_normalFixed')[0]
                # bpy.data.objects.get(root_name).hide_set(False)
            self.build_step = 1
            return {'RUNNING_MODAL'}
        elif self.build_step == 1 and event.value == 'PRESS' and event.type == 'LEFTMOUSE':  # selection de la source
            obj = click_on(event.mouse_region_x, event.mouse_region_y, ignore=False, search=['MESH'], ignore_display=[['BOUNDS']])
            if obj:
                try:
                    bpy.data.objects.get(self.original_name).hide_set(True)
                    self.original_obj.hide_set(True)
                except:pass
                self.make_source(obj)
                self.normal_fixed_obj = duplicate(self.original_obj)
                active_object('SET', self.normal_fixed_obj, True)
                for m in self.normal_fixed_obj.modifiers:
                    if m.type == 'WEIGHTED_NORMAL':
                        self.normal_fixed_obj.modifiers.remove(modifier=m)
                bpy.ops.object.convert(target='MESH')
                if self.normal_fixed_obj.get('fluent_obj'):
                    self.normal_fixed_obj['fluent_obj'] = 0
                if self.normal_fixed_obj.get('fluent_type'):
                    self.normal_fixed_obj['fluent_type'] = 'unknow'
                self.normal_fixed_obj.name = self.original_obj.name + '_normalFixed'
                self.original_obj.hide_set(True)
                self.original_obj.hide_render = True
                try:
                    self.original_obj.modifiers.remove(modifier=self.original_obj.modifiers['.f_weld_normal_repair'])
                except:
                    pass
                self.prepare_data_transfer()
                self.build_step = 2

                self.ui_management.refresh_side_infos([
                    [translate('step', upperCase=True)+' 3/3', translate('selectFacesThenPressEnter')],
                    [translate('quit'), translate('rightClick')]
                ])

                bpy.ops.fluent.booleandisplay('INVOKE_DEFAULT')
                active_object('SET', self.normal_fixed_obj, True)
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.context.space_data.shading.type = 'SOLID'
                bpy.context.space_data.shading.light = 'MATCAP'
                bpy.context.space_data.shading.studio_light = 'metal_carpaint.exr'

                return {'RUNNING_MODAL'}
        elif self.build_step == 2 and event.value == 'PRESS' and event.type in {'RET', 'NUMPAD_ENTER'}:  # ajoute la selection au vertex group utilisé par le data transfer
            bpy.ops.object.mode_set(mode='OBJECT')
            selected_verts = [
                v.index for v in self.normal_fixed_obj.data.vertices if v.select]
            self.vertex_group.add(selected_verts, 1, "ADD")
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action="DESELECT")

        # sortie du modal
        if event.value == 'PRESS' and event.type in {'RIGHTMOUSE', 'TAB'} and self.build_step == 2:
            bpy.context.space_data.shading.type = self.previous_viewport_settings['type']
            bpy.context.space_data.shading.light = self.previous_viewport_settings['light']
            bpy.context.space_data.shading.studio_light = self.previous_viewport_settings['studio_light']
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.modifier_apply(modifier=fluent_modifiers_name['data_transfer'])
            self.normal_fixed_obj.vertex_groups.clear()
            bpy.data.objects.remove(self.normal_source_obj, do_unlink=True)
            bpy.types.SpaceView3D.draw_handler_remove(self._handle_two, 'WINDOW')
            return {'FINISHED'}

        if event.value == 'PRESS' and event.type == 'ESC':
            try:
                self.original_obj.show_wire = False
            except:
                pass
            bpy.types.SpaceView3D.draw_handler_remove(
                self._handle_two, 'WINDOW')
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        # étape 0 : weld modifier, étape 1 : selectionne la source, étape 2 : selectionne les faces
        self.original_obj = active_object('GET')
        # vérifications
        if len(bpy.context.selected_objects) != 1:
            make_oops([translate('selectOneObject')], title=translate('howToUse'), icon='ERROR')
            return {'FINISHED'}

        # initialisation
        self.adjustment = None
        self.previous_viewport_settings = {
            'type': bpy.context.space_data.shading.type,
            'studio_light': bpy.context.space_data.shading.studio_light,
            'light': bpy.context.space_data.shading.light
        }
        self.original_obj = active_object(action='GET')
        self.build_step = 0
        self.root_name = None
        self.x_mouse_slider_origin = event.mouse_region_x

        self.ui_management = FLUENT_ui_management(event)

        # recherche de bevel
        has_bevel = [False, None]
        if len(self.original_obj.modifiers) >= 1 and self.original_obj.modifiers[-1].type == 'BEVEL':
            has_bevel = [True, -1]
        if len(self.original_obj.modifiers) >= 2 and self.original_obj.modifiers[-2].type == 'BEVEL':
            has_bevel = [True, -2]

        if not '_normalFixed' in self.original_obj.name:
            if not has_bevel[0]:
                make_oops([translate('noBevel'), translate('addThenTry')], title=translate('howToUse'),
                          icon='ERROR')
                return {'FINISHED'}
            try:
                # ajoute le weld modifier pour corriger l'overlapping
                self.weld_modifier = self.original_obj.modifiers.new(name='.f_weld_normal_repair', type='WELD')
                if has_bevel[1] == -1:
                    bpy.ops.object.modifier_move_up(modifier='.f_weld_normal_repair')
                elif has_bevel[1] == -2:
                    bpy.ops.object.modifier_move_up(modifier='.f_weld_normal_repair')
                    bpy.ops.object.modifier_move_up(modifier='.f_weld_normal_repair')
                bpy.context.object.show_wire = True
                self.ui_management.refresh_side_infos([[translate('step', upperCase=True)+' 1/3', translate('mergeCloseVertices')]])
            except:
                self.build_step = 0.5
        else:
            if event.shift:
                # supprime l'objet et sa normal source et réaffiche le suivant
                root_name = self.original_obj.name.split('_normalFixed')[0]
                live_object = bpy.data.objects.get(root_name)
                bpy.data.objects.remove(self.original_obj, do_unlink=True)
                show_object(live_object, 'VIEWPORT')
                show_object(live_object, 'RENDER')
                return {'FINISHED'}
            else:
                # édition
                self.original_name = self.original_obj.name.split('_normalFixed')[0]

                try:
                    # ajoute le weld modifier pour corriger l'overlapping
                    self.weld_modifier = self.original_obj.modifiers.new(name='.f_weld_normal_repair', type='WELD')
                    if has_bevel[1] == -1:
                        bpy.ops.object.modifier_move_up(modifier='.f_weld_normal_repair')
                    elif has_bevel[1] == -2:
                        bpy.ops.object.modifier_move_up(modifier='.f_weld_normal_repair')
                        bpy.ops.object.modifier_move_up(modifier='.f_weld_normal_repair')
                    bpy.context.object.show_wire = True
                    self.ui_management.refresh_side_infos([[translate('step', upperCase=True)+' 1/3', translate('mergeCloseVertices')]])
                except:
                    self.build_step = 0.5

                # bpy.data.objects.get(self.original_name).hide_set(False)
                # self.original_obj.hide_set(True)
                # bpy.ops.fluent.booleandisplay('INVOKE_DEFAULT')
                # bpy.ops.object.select_all(action='DESELECT')
                # context.view_layer.objects.active = None
                # self.build_step = 1
                self.build_step = 0

        self._handle_two = bpy.types.SpaceView3D.draw_handler_add(draw_callback_px, (self, context), 'WINDOW', 'POST_PIXEL')
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


class FLUENT_OT_BooleanDuplicate(Operator):
    """Duplicate/Extract a boolean object
Select a boolean object to duplicate it.
Hold Shift - Extract the selected boolean object
"""
    bl_idname = "fluent.booleanduplicate"
    bl_label = "Boolean Instance"
    bl_options = {'REGISTER', 'UNDO'}
    ui_management = None

    def duplicate(self):
        self.copy = duplicate(self.first, linked=True)

        self.copy['fluent_id'] = self.fluent_id
        add_in_bool_collection(self.copy)

        # Cut the cutter, les sous booléens doivent suivre
        for child in self.first.children:
            duplicate_and_add_boolean(child=child, obj_with_modifiers=self.copy)

        self.duplicate_slice()
        try:
            self.copy.rotation_euler = self.drawing.get_drawing_plane().rotation_euler.copy()
        except:
            pass
        if self.copy.get('fluent_type') == 'revolver':
            self.copy.rotation_euler.rotate_axis('X', math.radians(90))

        self.copy.display_type = 'WIRE'
        self.bool_drawing = FLUENT_Draw_Object(self.copy, (1, 1, 1, 0.05))

    def duplicate_slice(self):
        if not self.is_slice_mode:
            return

        try:
            self.first['fluent_slice']
        except:
            make_oops(
                [translate('sliceObjectNotFound')],
                translate('fluentDataError'),
                'ERROR'
            )
            return

        self.slice_cutters = []
        for mod in self.first['fluent_slice'].modifiers:
            if mod.type != 'BOOLEAN' or mod.object is None:
                continue

            targets = find_boolean_targets(mod.object)
            if len(targets) != 1:
                continue

            obj_copy = duplicate_and_add_boolean(child=mod.object, parent_obj=self.copy)
            self.slice_cutters.append({'obj': obj_copy, 'operation': mod.operation})

    def modal(self, context, event):
        context.area.tag_redraw()

        events = self.ui_management.event_dico_refresh(event)

        # action des boutons
        action = self.ui_management.get_button_action()[0]

        # raccourcis clavier
        if event.value == 'PRESS' and event.type == 'R':
            self.copy.rotation_euler.rotate_axis('Z', math.radians(45))

        if event.type == 'MOUSEMOVE':
            self.previous_cast = self.cast.copy()
            if self.duplicate_on:
                self.cast = obj_ray_cast(self.duplicate_on, events['mouse_x'], events['mouse_y'])
            if not self.cast['success']:
                self.duplicate_on = click_on(events['mouse_x'], events['mouse_y'], ignore=self.copy,
                                             search=['MESH'])
            if (self.cast['success'] and self.cast['normal'] != self.previous_cast['normal']) or (
                    not self.drawing.get_extended() and self.cast['face_index'] != self.previous_cast['face_index']):
                self.duplicate_on = click_on(events['mouse_x'], events['mouse_y'], ignore=self.copy,
                                             search=['MESH'])
                if self.duplicate_on:
                    is_display = self.drawing.get_display_dots()
                    self.drawing.reset()
                    self.drawing.grid_init(self.duplicate_on, events)
                    self.drawing.set_display_grid(True)
                    self.drawing.set_display_dots(is_display)
                    try:
                        self.copy.rotation_euler = self.drawing.get_drawing_plane().rotation_euler.copy()
                        if self.copy.get('fluent_type') == 'revolver':
                            self.copy.rotation_euler.rotate_axis('X', math.radians(90))
                    except:
                        pass
            try:
                self.copy.location = self.duplicate_on.matrix_world @ \
                                     obj_ray_cast(self.duplicate_on, self.drawing.get_snaped_coords()[0],
                                                  self.drawing.get_snaped_coords()[1])['hit']
            except:
                pass

        # place la copie
        if event.value == 'PRESS' and event.type == 'LEFTMOUSE' and self.duplicate_on:
            if get_addon_preferences().auto_parent:
                parent_relationship(self.duplicate_on, self.copy)

            new_mod = self.duplicate_on.modifiers.new(name=fluent_modifiers_name['boolean'], type="BOOLEAN")
            new_mod.solver = 'FAST'
            new_mod.object = self.copy
            new_mod.show_expanded = False
            new_mod.show_viewport = False
            new_mod.operation = self.operation
            self.bool_list.append(new_mod)
            bevels = F_outer_bevel(self.duplicate_on)
            bevels.management()

            if self.is_slice_mode:
                change_bool_operation(self.copy, self.duplicate_on, 'SLICE')
                slice_obj = self.copy['fluent_slice']
                for mod in slice_obj.modifiers:
                    if mod.type != 'BOOLEAN' or mod.object != self.copy:
                        continue

                    self.bool_list.append(mod)
                    break

                for cutter in self.slice_cutters:
                    new_mod = slice_obj.modifiers.new(name=fluent_modifiers_name['boolean'], type="BOOLEAN")
                    new_mod.solver = 'FAST'
                    new_mod.object = cutter.get('obj')
                    new_mod.show_expanded = False
                    new_mod.show_viewport = False
                    new_mod.operation = cutter.get('operation')
                    self.bool_list.append(new_mod)
                    bevels = F_outer_bevel(slice_obj)
                    bevels.management()

            self.duplicate()

        # controle de la grille
        if event.value == 'PRESS' and event.type == 'C':
            self.drawing.set_display_dots(not self.drawing.get_display_dots())
        if event.value == 'PRESS' and event.type == 'V':
            self.drawing.set_resolution(self.drawing.get_resolution() + 1)
            bpy.context.scene.fluentProp.grid_resolution = self.drawing.get_resolution()
        if event.value == 'PRESS' and event.type == 'B':
            self.drawing.set_resolution(self.drawing.get_resolution() - 1)
            bpy.context.scene.fluentProp.grid_resolution = self.drawing.get_resolution()
        if event.value == 'PRESS' and event.type == 'X':
            self.drawing.set_extended(not self.drawing.get_extended())

        if pass_through(event):
            return {'PASS_THROUGH'}

        # Quit
        if event.type == 'RIGHTMOUSE' and event.value == 'PRESS':
            for child in self.copy.children:
                bpy.data.objects.remove(child, do_unlink=True)

            bpy.data.objects.remove(self.copy, do_unlink=True)
            bpy.data.objects.remove(self.drawing.get_drawing_plane(), do_unlink=True)
            for b in self.bool_list:
                b.show_expanded = True
                b.show_viewport = True
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            bpy.types.SpaceView3D.draw_handler_remove(self._handle_obj_draw, 'WINDOW')
            return{'FINISHED'}

        self.mouse_x = event.mouse_region_x
        self.mouse_y = event.mouse_region_y
        return {'RUNNING_MODAL'}

    def invoke(self, context, event):

        obj = active_object('GET')
        self.first = obj

        if not obj:
            make_oops([translate('selectAtLeastOneObject')], title=translate('howToUse'), icon='ERROR')
            return {'FINISHED'}
        else:
            if not obj.get('fluent_operation'):
                make_oops([translate('selectBoolean')], title=translate('howToUse'), icon='ERROR')
                return {'FINISHED'}

        if event.shift:  # extraction
            boolean_extraction()
            return {'FINISHED'}

        # duplicate
        self.previous_cast = None
        self.bool_list = []
        self.copy = None
        self.is_slice_mode = False
        self.slice_cutters = []

        self.operation = 'DIFFERENCE'
        try:
            if obj.get('fluent_type') in ['box', 'prism', 'poly'] and obj.modifiers[fluent_modifiers_name['first_solidify']].thickness > 0:
                self.operation = 'UNION'

            if obj.get('fluent_type') in ['revolver']:
                co_y_moyen = 0
                for v in obj.data.vertices:
                    co_y_moyen = co_y_moyen + v.co.y
                co_y_moyen = co_y_moyen / len(obj.data.vertices)
                if co_y_moyen > 0:
                    self.operation = 'UNION'

            if obj.get('fluent_operation') == 'SLICE':
                self.is_slice_mode = True

            if obj.get('fluent_type') in ['path'] and obj.modifiers[fluent_modifiers_name['path_height']].screw_offset > 0:
                self.operation = 'UNION'
        except:
            pass
        self.ui_management = FLUENT_ui_management(event)
        self.drawing = FLUENT_Drawing()
        self.ui_management.add_items(self.drawing)
        events = self.ui_management.event_dico_refresh(event)

        self.ui_management.refresh_side_infos([
            [translate('put'), translate('leftClick')],
            [translate('rotate'), 'R'],
            [translate('gridResolution'), 'V / B'],
            [translate('gridDisplaying'), 'C'],
            [translate('gridExtended'), 'X'],
            [translate('quit'), translate('rightClick')],
        ])

        self.duplicate_on = click_on(events['mouse_x'], events['mouse_y'], ignore=obj, search=['MESH'])
        if self.duplicate_on:
            self.drawing.grid_init(self.duplicate_on, events)
            self.drawing.set_display_grid(True)
            self.drawing.set_display_dots(True)
            self.cast = obj_ray_cast(self.duplicate_on, events['mouse_x'], events['mouse_y'])
        else:
            self.cast = {'success': False, 'normal': None}

        if obj.get('fluent_id'):
            self.fluent_id = obj.get('fluent_id')
        else:
            self.fluent_id = search_last_fluent_id() + 1
            obj['fluent_id'] = self.fluent_id

        self.duplicate()

        args = (self, context)
        self._handle = bpy.types.SpaceView3D.draw_handler_add(draw_callback_px, args, 'WINDOW', 'POST_PIXEL')
        self._handle_obj_draw = bpy.types.SpaceView3D.draw_handler_add(self.bool_drawing.draw, (), 'WINDOW', 'POST_VIEW')
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


class FLUENT_OT_BooleanSynchronization(Operator):
    """Synchronize boolean objects duplicated by Fluent duplicate function"""
    bl_idname = "fluent.booleansynchronization"
    bl_label = "Boolean Synchronization"
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):
        obj = bpy.context.active_object
        modifiers_values = []
        if obj and obj.get('fluent_id'):
            fluent_id = obj.get('fluent_id')
            for o in bpy.data.objects:
                if o.get('fluent_id') and o.get('fluent_id') == fluent_id and o != obj:
                    reuse_cutter(o, obj)

        else:
            make_oops([translate('selectDuplicated')], title=translate('info'), icon='ERROR')
            return {'FINISHED'}
        return {'RUNNING_MODAL'}


class FLUENT_OT_VGCleaner(Operator):
    """Remove selected vertices from each vertex groups"""
    bl_idname = "fluent.vgcleaner"
    bl_label = "VG Cleaner"

    def execute(self, context):
        obj = active_object('GET')
        bpy.ops.object.mode_set(mode='EDIT')
        displayed_bevels = []
        for m in obj.modifiers:
            if m.type == 'BEVEL' and 'First_Bevel' in m.name:
                m.show_viewport = False
                displayed_bevels.append(m)
        bpy.ops.object.mode_set(mode='OBJECT')
        selected_verts = [v.index for v in obj.data.vertices if v.select]
        for vg in obj.vertex_groups:
            vg.remove(selected_verts)
        for b in displayed_bevels:
            b.show_viewport = True
        return {'FINISHED'}


class FLUENT_OT_ToggleLoopSlide(Operator):
    """Toggle the bevel's loop slide option"""
    bl_idname = "fluent.toggleloopslide"
    bl_label = "Toggle Loop Slide"

    def execute(self, context):
        for o in bpy.context.selected_objects:
            for m in o.modifiers:
                if fluent_modifiers_name['outer_bevel'] in m.name and m.type == 'BEVEL':
                    m.loop_slide = not m.loop_slide
        return {'FINISHED'}


class FLUENT_OT_BecomeFluent(Operator):
    """Transform a plane to a Fluent object
Hold Alt - Extract a face from an object"""
    bl_idname = "fluent.becomefluent"
    bl_label = "Become Fluent"
    bl_options = {'REGISTER', 'UNDO'}

    call_from: bpy.props.StringProperty(
        name='call_from',
        default=''
    )

    def convert(self):
        bpy.ops.object.mode_set(mode='OBJECT')
        obj = active_object()
        active_object('SET', obj, True)
        if obj.type == 'MESH':
            try:
                for m in obj.modifiers:
                    obj.modifiers.remove(m)
            except:
                pass
            bpy.ops.object.convert(target='MESH')
            if len(obj.data.polygons):
                decimate = obj.modifiers.new(type='DECIMATE', name='Decimate')
                decimate.decimate_type = 'DISSOLVE'
                bpy.ops.object.convert(target='MESH')
                bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS', center='MEDIAN')
                error = False
                for i, p in enumerate(obj.data.polygons):
                    try:
                        if round(math.fabs(obj.data.polygons[i].normal.x), 5) != round(
                                math.fabs(obj.data.polygons[i - 1].normal.x), 5) or round(
                                math.fabs(obj.data.polygons[i].normal.y), 5) != round(
                                math.fabs(obj.data.polygons[i - 1].normal.y), 5) or round(
                                math.fabs(obj.data.polygons[i].normal.z), 5) != round(
                                math.fabs(obj.data.polygons[i - 1].normal.z), 5):
                            error = True
                    except:
                        pass
                if not error:
                    bpy.ops.object.shade_smooth()
                    use_auto_smooth(bpy.context.object.data)
                    active_object('SET', obj, True)
                    if self.call_from == 'PRIMITIVE':
                        obj['fluent_type'] = 'box'
                        bpy.ops.fluent.editor('INVOKE_DEFAULT', bool_obj_name=obj.name, cut_obj_name='',
                                              operation='CREATION')
                    else:
                        obj['fluent_type'] = 'poly'
                        active_object('SET', obj, True)
                        bpy.ops.fluent.editor('INVOKE_DEFAULT', operation='EDIT', call_from='become_fluent')
                    return {'FINISHED'}
                else:
                    make_oops([translate('objectNotPlane')], title=translate('problem'), icon='ERROR')
                    return {'CANCELLED'}
            else:
                make_oops([translate('objectNotPlane')], title=translate('problem'), icon='ERROR')
                return {'CANCELLED'}
        elif obj.type == 'CURVE':
            if len(obj.data.splines) == 1 and len(obj.data.splines[0].bezier_points):
                bpy.ops.fluent.wire('INVOKE_DEFAULT', operation='BECOME_FLUENT')
            else:
                if len(obj.data.splines) != 1:
                    make_oops([translate('singleCurveExpected')], title=translate('howToUse'), icon='ERROR')
                elif not len(obj.data.splines[0].bezier_points):
                    make_oops([translate('bezierCurveExpected')], title=translate('howToUse'), icon='ERROR')
            return {'FINISHED'}

    def invoke(self, context, event):
        # vérifications
        if not active_object('GET'):
            make_oops([translate('selectAtLeastOneObject')], title=translate('howToUse'), icon='ERROR')
            return {'FINISHED'}
        if not event.alt:
            self.convert()
            return {'FINISHED'}
        else:
            bpy.ops.fluent.faceextraction('INVOKE_DEFAULT')
            return {'FINISHED'}


class FLUENT_OT_FaceExtraction(Operator):
    """Face extraction
    Extract a face from an object then turn it into a Fluent object"""
    bl_idname = "fluent.faceextraction"
    bl_label = "Face extraction"
    bl_options = {'REGISTER', 'UNDO'}

    obj = None
    extracted = None
    ui_management = None
    call_by: StringProperty(
        default=''
    )

    def modal(self, context, event):
        self.ui_management.refresh_ui_items_list()
        context.area.tag_redraw()

        if event.type not in ['RET', 'NUMPAD_ENTER', 'ESC']:
            return {'PASS_THROUGH'}
        if event.type in ['RET', 'NUMPAD_ENTER'] and event.value == 'PRESS':
            save_view_mat = bpy.context.region_data.view_matrix.copy()
            bpy.ops.mesh.separate(type='SELECTED')
            bpy.ops.object.mode_set(mode='OBJECT')
            self.extracted = bpy.context.selected_objects[1]
            bpy.data.objects.remove(self.copy, do_unlink=True)
            self.obj.hide_viewport = False
            active_object('SET', self.extracted, True)

            # remettre à plat
            if self.call_by != 'plate':
                for area in bpy.context.screen.areas:
                    if area.type == 'VIEW_3D':
                        for space in area.spaces:
                            if space.type == 'VIEW_3D':
                                if space.region_3d.is_perspective:
                                    init_persp_ortho = 'PERSP'
                                else:
                                    init_persp_ortho = 'ORTHO'

                context.region_data.view_perspective = 'ORTHO'
                bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.view3d.snap_cursor_to_selected()
                bpy.ops.view3d.view_axis(type='TOP', align_active=True, relative=False)
                bpy.ops.object.mode_set(mode='OBJECT')
                bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='BOUNDS')
                bpy.ops.object.empty_add(align='VIEW')
                temp_empty = bpy.context.active_object
                temp_empty.rotation_mode = 'XYZ'

                restoreRot_X = temp_empty.rotation_euler[0]
                restoreRot_Y = temp_empty.rotation_euler[1]
                restoreRot_Z = temp_empty.rotation_euler[2]

                bpy.ops.object.select_all(action='DESELECT')
                self.extracted.select_set(True)
                temp_empty.select_set(True)
                bpy.context.view_layer.objects.active = temp_empty
                bpy.ops.object.parent_set()

                bpy.ops.object.select_all(action='DESELECT')
                temp_empty.select_set(True)
                bpy.ops.object.rotation_clear()

                bpy.ops.object.select_all(action='DESELECT')
                self.extracted.select_set(True)
                bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')

                bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)

                self.extracted.rotation_mode = 'XYZ'
                self.extracted.rotation_euler[0] = restoreRot_X
                self.extracted.rotation_euler[1] = restoreRot_Y
                self.extracted.rotation_euler[2] = restoreRot_Z

                bpy.ops.object.select_all(action='DESELECT')
                temp_empty.select_set(True)
                bpy.ops.object.delete()

                active_object(self.extracted, 'SET', True)

                context.region_data.view_perspective = init_persp_ortho
                bpy.context.region_data.view_matrix = save_view_mat

            if self.call_by == 'CUT':
                self.extracted['fluent_type'] = 'poly'
                self.extracted.display_type == 'WIRE'
                boolean_visibility_setup(self.extracted)
                add_in_bool_collection(self.extracted)
                parent_relationship(self.obj, self.extracted)
                self.obj.hide_set(False)
                for p in self.extracted.data.polygons:
                    p.flip()
                bpy.ops.fluent.editor('INVOKE_DEFAULT', bool_obj_name=self.extracted.name,
                                      cut_obj_name=self.obj.name, operation='CUT')
            elif self.call_by == 'plate':
                bpy.context.scene.collection.objects.link
                self.extracted['fluent_type'] = 'plate'
                use_auto_smooth(self.extracted.data)
                self.obj.hide_set(False)

                for p in self.extracted.data.polygons:
                    p.flip()

                active_object('SET', self.extracted, True)
                mirror = self.extracted.modifiers.new(name=fluent_modifiers_name['mirror'], type='MIRROR')
                mirror.mirror_object = self.obj
                mirror.show_viewport = False
                mirror.show_render = False
                mirror.use_axis[0] = False
                mirror.use_axis[1] = False
                mirror.use_axis[2] = False
                mirror.use_bisect_axis[0] = True
                mirror.use_bisect_axis[1] = True
                mirror.use_bisect_axis[2] = True
                mirror.show_expanded = False
                bpy.ops.fluent.editor('INVOKE_DEFAULT', bool_obj_name=self.extracted.name, operation='PLATE')

                # if self.obj.modifiers.get(fluent_modifiers_name['outer_bevel']):
                #     copy_modifiers_stack(self.obj, self.extracted, name=fluent_modifiers_name['outer_bevel'])
                #     copy_modifiers_stack(self.obj, self.extracted, name=fluent_modifiers_name['weighted_normal'])

            else:
                for p in self.extracted.data.polygons:
                    p.flip()
                self.obj.hide_set(False)
                active_object('SET', self.extracted, True)
                bpy.ops.fluent.becomefluent('INVOKE_DEFAULT')

            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            return {'FINISHED'}
        if event.type == 'ESC' and event.value == 'PRESS':
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.data.objects.remove(self.copy)
            self.obj.hide_set(False)
            active_object('SET', self.obj, True)
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            return {'FINISHED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        if not self.obj and not active_object():
            make_oops([translate('selectAtLeastOneObject')], title=translate('howToUse'), icon='ERROR')
            return {'FINISHED'}

        self.ui_management = FLUENT_ui_management(event)
        if self.obj: active_object('SET', self.obj, True)
        if not self.obj: self.obj = active_object()

        if self.call_by == 'plate':
            self.copy = duplicate(self.obj, '.Plate')
            for m in self.copy.modifiers:
                if fluent_modifiers_name['outer_bevel'] in m.name:
                    self.copy.modifiers.remove(m)
                    continue
                if fluent_modifiers_name['weighted_normal'] in m.name:
                    self.copy.modifiers.remove(m)
            self.copy.data.shade_flat()
        else:
            self.copy = duplicate(self.obj)
        apply_modifiers(self.copy)

        self.obj.hide_set(True)
        active_object('SET', self.copy, True)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
        bpy.ops.mesh.select_all(action='DESELECT')

        self.ui_management.refresh_side_infos([
            [translate('selectFaces'), ''],
            [translate('validate'), translate('enter')]
        ])

        args = (self, context)
        self._handle = bpy.types.SpaceView3D.draw_handler_add(draw_callback_px, args, 'WINDOW', 'POST_PIXEL')
        context.window_manager.modal_handler_add(self)

        return {'RUNNING_MODAL'}


class FLUENT_OT_OtherAdjustments(Operator):
    """Options"""
    bl_idname = "fluent.otheradjustments"
    bl_label = "Other adjustments"
    bl_options = {'REGISTER', 'UNDO'}

    centered_array: bpy.props.BoolProperty(
        description="Draw array from the center",
        name="Centered array",
        default=True
    )
    auto_mirror_x: bpy.props.BoolProperty(
        description="Auto Mirror X",
        name="Auto Mirror X",
        default=False
    )
    auto_mirror_y: bpy.props.BoolProperty(
        description="Auto Mirror Y",
        name="Auto Mirror Y",
        default=False
    )
    auto_mirror_z: bpy.props.BoolProperty(
        description="Auto Mirror Z",
        name="Auto Mirror Z",
        default=False
    )
    loop_slide: bpy.props.BoolProperty(
        description="Use the loop slide option",
        name="Loop Slide",
        default=True
    )
    outer_bevel_segments: bpy.props.IntProperty(
        description="0 = automatic",
        name="Outer bevel segments",
        default=0,
        min=0,
        step=1
    )
    bevel_profile: bpy.props.FloatProperty(
        description="Bevel profile",
        name="Bevel profile",
        default=0.50,
        min=0,
        max=1,
        step=0.01
    )
    model_resolution: bpy.props.IntProperty(
        description='Resolution of bevels, cylinders and spheres (segments/m)',
        name='Model resolution',
        default=32,
        min=1,
        max=256
    )
    bevel_factor: bpy.props.FloatProperty(
        description="Increase/decrease the bevel size of selected object",
        name="Bevel factor",
        default=1,
        min=0.001,
        step=0.01
    )
    min_auto_bevel_segments: bpy.props.IntProperty(
        description="Minimum resolution of bevels (segments/m). 0 = automatic",
        name="Min. of segments for auto-bevel",
        default=1,
        min=0,
        step=1
    )
    min_auto_cylinder_segments: bpy.props.IntProperty(
        description="Minimum resolution of cylinders and spheres (segments/m). 0 = automatic",
        name="Min. of segments for auto-cylinder",
        default=1,
        min=0,
        step=1
    )

    def execute(self, context):

        if self.bevel_factor != 1:
            for o in bpy.context.selected_objects:
                for m in o.modifiers:
                    if m.type == 'BEVEL':
                        m.width *= self.bevel_factor

        if bpy.context.scene.fluentProp.bevel_profile != self.bevel_profile:
            bpy.context.scene.fluentProp.bevel_profile = self.bevel_profile

        if bpy.context.scene.fluentProp.auto_mirror_x != self.auto_mirror_x:
            bpy.context.scene.fluentProp.auto_mirror_x = self.auto_mirror_x

        if bpy.context.scene.fluentProp.auto_mirror_y != self.auto_mirror_y:
            bpy.context.scene.fluentProp.auto_mirror_y = self.auto_mirror_y

        if bpy.context.scene.fluentProp.auto_mirror_z != self.auto_mirror_z:
            bpy.context.scene.fluentProp.auto_mirror_z = self.auto_mirror_z

        if bpy.context.scene.fluentProp.centered_array != self.centered_array:
            bpy.context.scene.fluentProp.centered_array = self.centered_array

        if bpy.context.scene.fluentProp.loop_slide != self.loop_slide:
            bpy.context.scene.fluentProp.loop_slide = self.loop_slide

        if bpy.context.scene.fluentProp.outer_bevel_segments != self.outer_bevel_segments:
            bpy.context.scene.fluentProp.outer_bevel_segments = self.outer_bevel_segments

        if bpy.context.scene.fluentProp.model_resolution != self.model_resolution:
            bpy.context.scene.fluentProp.model_resolution = self.model_resolution
            # update_resolution()

        if bpy.context.scene.fluentProp.min_auto_bevel_segments != self.min_auto_bevel_segments:
            bpy.context.scene.fluentProp.min_auto_bevel_segments = self.min_auto_bevel_segments

        if bpy.context.scene.fluentProp.min_auto_cylinder_segments != self.min_auto_cylinder_segments:
            bpy.context.scene.fluentProp.min_auto_cylinder_segments = self.min_auto_cylinder_segments

        return {'FINISHED'}

    def invoke(self, context, event):
        self.bevel_factor = 1
        self.bevel_profile = bpy.context.scene.fluentProp.bevel_profile
        self.auto_mirror_x = bpy.context.scene.fluentProp.auto_mirror_x
        self.auto_mirror_y = bpy.context.scene.fluentProp.auto_mirror_y
        self.auto_mirror_z = bpy.context.scene.fluentProp.auto_mirror_z
        self.centered_array = bpy.context.scene.fluentProp.centered_array
        self.loop_slide = bpy.context.scene.fluentProp.loop_slide
        self.outer_bevel_segments = bpy.context.scene.fluentProp.outer_bevel_segments
        self.model_resolution = bpy.context.scene.fluentProp.model_resolution
        self.min_auto_bevel_segments = bpy.context.scene.fluentProp.min_auto_bevel_segments
        self.min_auto_cylinder_segments = bpy.context.scene.fluentProp.min_auto_cylinder_segments
        return context.window_manager.invoke_props_dialog(self)


class FLUENT_OT_BuildingAnimation(Operator):
    """See your object growing !"""
    bl_idname = "fluent.buildinganimation"
    bl_label = "Animation builder"
    bl_options = {'REGISTER', 'UNDO'}

    obj = None
    speed = None
    slice_data = [] #[ [modifier, [objects] ] ]
    already_animated = []

    def recursive_search(self, data, target):
        found = False
        if type(data) is list:
            for i in data:
                if type(i) is list:
                    found = self.recursive_search(i, target)
                    if found:
                        return found
                else:
                    if i == target:
                        found = True
                        return found
        return found

    def anim_second_solidify(self, obj, frame, visible_modifiers):
        anim_length = int(12/self.speed)
        second_solidify = obj.modifiers.get(fluent_modifiers_name['second_solidify'])
        if second_solidify and second_solidify in visible_modifiers:
            second_solidify.show_viewport = second_solidify.show_render = True
            second_solidify.keyframe_insert('show_viewport')
            second_solidify.keyframe_insert('show_render')
            frame += anim_length
            bpy.context.scene.frame_set(frame)
            second_solidify.keyframe_insert('thickness')
            frame -= anim_length
            bpy.context.scene.frame_set(frame)
            second_solidify.thickness = 0
            second_solidify.keyframe_insert('thickness')
            frame += anim_length
            bpy.context.scene.frame_set(frame)
        return frame

    def anim_first_solidify(self, obj, frame, visible_modifiers):
        anim_length = int(12/self.speed)
        first_solidify = obj.modifiers.get(fluent_modifiers_name['first_solidify'])
        if first_solidify and first_solidify in visible_modifiers:
            first_solidify.show_viewport = first_solidify.show_render = True
            first_solidify.keyframe_insert('show_viewport')
            first_solidify.keyframe_insert('show_render')
            frame += anim_length
            bpy.context.scene.frame_set(frame)
            first_solidify.keyframe_insert('thickness')
            frame -= anim_length
            bpy.context.scene.frame_set(frame)
            first_solidify.thickness = 0
            first_solidify.keyframe_insert('thickness')
            frame += anim_length
            bpy.context.scene.frame_set(frame)
        return frame

    def anim_first_bevel(self, obj, frame, visible_modifiers):
        anim_length = int(12/self.speed)
        first_bevels = [m for m in obj.modifiers if fluent_modifiers_name['first_bevel'] in m.name]
        if len(first_bevels):
            for first_bevel in first_bevels:
                if first_bevel and first_bevel in visible_modifiers:
                    first_bevel.show_viewport = first_bevel.show_render = True
                    first_bevel.keyframe_insert('show_viewport')
                    first_bevel.keyframe_insert('show_render')
                    frame += anim_length
                    bpy.context.scene.frame_set(frame)
                    first_bevel.keyframe_insert('width')
                    frame -= anim_length
                    bpy.context.scene.frame_set(frame)
                    first_bevel.width = 0
                    first_bevel.keyframe_insert('width')
            frame += anim_length
            bpy.context.scene.frame_set(frame)
        return frame

    def anim_second_bevel(self, obj, frame, visible_modifiers):
        anim_length = int(12/self.speed)
        second_bevel_top = obj.modifiers.get(fluent_modifiers_name['second_bevel_top'])
        second_bevel_bottom = obj.modifiers.get(fluent_modifiers_name['second_bevel_bottom'])
        is_top =  second_bevel_top and second_bevel_top in visible_modifiers
        is_bottom = second_bevel_bottom and second_bevel_bottom in visible_modifiers
        if is_top:
            second_bevel_top.show_viewport = second_bevel_top.show_render = True
            second_bevel_top.keyframe_insert('show_viewport')
            second_bevel_top.keyframe_insert('show_render')
        if is_bottom:
            second_bevel_bottom.show_viewport = second_bevel_bottom.show_render = True
            second_bevel_bottom.keyframe_insert('show_viewport')
            second_bevel_bottom.keyframe_insert('show_render')
        frame += anim_length
        bpy.context.scene.frame_set(frame)
        if is_top:
            second_bevel_top.keyframe_insert('width')
        if is_bottom:
            second_bevel_bottom.keyframe_insert('width')
        frame -= anim_length
        bpy.context.scene.frame_set(frame)
        if is_top:
            second_bevel_top.width = 0
            second_bevel_top.keyframe_insert('width')
        if is_bottom:
            second_bevel_bottom.width = 0
            second_bevel_bottom.keyframe_insert('width')
        frame += anim_length
        bpy.context.scene.frame_set(frame)
        return frame

    def anim_chamfer(self, obj, frame, visible_modifiers):
        anim_length = int(12/self.speed)
        chamfer = obj.modifiers.get(fluent_modifiers_name['chamfer'])
        # pre_chamfer = obj.modifiers.get(fluent_modifiers_name['pre_chamfer'])
        if chamfer and chamfer in visible_modifiers:
            chamfer.show_viewport = chamfer.show_render = True
            # pre_chamfer.show_viewport = pre_chamfer.show_render = True
            chamfer.keyframe_insert('show_viewport')
            chamfer.keyframe_insert('show_render')
            # pre_chamfer.keyframe_insert('show_viewport')
            frame += anim_length
            bpy.context.scene.frame_set(frame)
            chamfer.keyframe_insert('width')
            frame -= anim_length
            bpy.context.scene.frame_set(frame)
            chamfer.width = 0
            chamfer.keyframe_insert('width')
            frame += anim_length
            bpy.context.scene.frame_set(frame)
        return frame
    
    def anim_mirror(self, obj, frame, visible_modifiers):
        mirror = obj.modifiers.get(fluent_modifiers_name['mirror'])
        if mirror in visible_modifiers:
            mirror.show_viewport = mirror.show_render = True
            mirror.keyframe_insert('show_viewport')
            mirror.keyframe_insert('show_render')
        return frame

    def anim_array(self, obj, frame, visible_modifiers):
        anim_length = int(24/self.speed)
        found = False
        for vm in visible_modifiers:
            if vm.type == 'ARRAY':
                found = True
                vm.show_viewport = vm.show_render = True
                vm.keyframe_insert('show_viewport')
                vm.keyframe_insert('show_render')
                frame += anim_length
                bpy.context.scene.frame_set(frame)
                vm.keyframe_insert(data_path="count")
                frame -= anim_length
                bpy.context.scene.frame_set(frame)
                vm.count = 0
                vm.keyframe_insert(data_path="count")
        if found:
            frame += anim_length
            bpy.context.scene.frame_set(frame)
        return frame

    def anim_taper(self, obj, frame, visible_modifiers):
        anim_length = int(12/self.speed)
        tapers = [m for m in obj.modifiers if m.name in [fluent_modifiers_name['taper_x'], fluent_modifiers_name['taper_y'], fluent_modifiers_name['taper_z']]]
        found = False
        for taper in tapers:
            if taper in visible_modifiers:
                found = True
                taper.show_viewport = taper.show_render = True
                taper.keyframe_insert('show_viewport')
                taper.keyframe_insert('show_render')
                frame += anim_length
                bpy.context.scene.frame_set(frame)
                taper.keyframe_insert('factor')
                frame -= anim_length
                bpy.context.scene.frame_set(frame)
                taper.factor = 0
                taper.keyframe_insert('factor')
        if found:
            frame += anim_length
            bpy.context.scene.frame_set(frame)
        return frame

    def anim_circular_array(self, obj, frame, visible_modifiers):
        anim_length = int(24/self.speed)
        circular_array = obj.modifiers.get(fluent_modifiers_name['circular_array'])
        if circular_array and circular_array in visible_modifiers:
            circular_array.show_viewport = circular_array.show_render = True
            array_end = circular_array.node_group.nodes[fluent_modifiers_name['circular_array']].inputs['Count']
            circular_array.keyframe_insert('show_viewport')
            circular_array.keyframe_insert('show_render')
            frame += anim_length
            bpy.context.scene.frame_set(frame)
            array_end.keyframe_insert('default_value')
            frame -= anim_length
            bpy.context.scene.frame_set(frame)
            array_end.default_value = 0
            array_end.keyframe_insert('default_value')
            frame += anim_length
            bpy.context.scene.frame_set(frame)
        return frame

    def anim_frame(self, obj, frame, visible_modifiers):
        anim_length = int(12/self.speed)
        frame_modifier = obj.modifiers.get(fluent_modifiers_name['frame'])
        if frame_modifier and frame_modifier in visible_modifiers:
            frame_modifier.show_viewport = frame_modifier.show_render = True
            frame_modifier.keyframe_insert('show_viewport')
            frame_modifier.keyframe_insert('show_render')
            frame += anim_length
            bpy.context.scene.frame_set(frame)
            frame_modifier.keyframe_insert('["Input_3"]')
            frame -= anim_length
            bpy.context.scene.frame_set(frame)
            frame_modifier['Input_3'] = 0.0
            frame_modifier.keyframe_insert('["Input_3"]')
            frame += anim_length
            bpy.context.scene.frame_set(frame)
        return frame

    def anim_screw(self, obj, frame, visible_modifiers):
        anim_length = int(12 / self.speed)
        screw = obj.modifiers.get(fluent_modifiers_name['screw'])
        if screw and screw in visible_modifiers:
            screw.show_viewport = screw.show_render = True
            screw.keyframe_insert('show_viewport')
            screw.keyframe_insert('show_render')
            frame += anim_length
            bpy.context.scene.frame_set(frame)
            screw.keyframe_insert('steps')
            screw.keyframe_insert('render_steps')
            frame -= anim_length
            bpy.context.scene.frame_set(frame)
            screw.steps = 0
            screw.render_steps = 0
            screw.keyframe_insert('steps')
            screw.keyframe_insert('render_steps')
            frame += anim_length
            bpy.context.scene.frame_set(frame)
        return frame

    def anim_head_screw_bool(self, obj, frame):
        anim_length = int(12 / self.speed)
        screw_modifier = obj.modifiers.get(fluent_modifiers_name['head_screw'])
        frame += anim_length
        bpy.context.scene.frame_set(frame)
        screw_modifier.keyframe_insert('["Input_6"]')
        frame -= anim_length
        bpy.context.scene.frame_set(frame)
        screw_modifier['Input_6'] = 0.0
        screw_modifier.keyframe_insert('["Input_6"]')
        frame += anim_length
        bpy.context.scene.frame_set(frame)
        return frame

    def anim_boolean(self, frame, visible_modifiers, slice_boolean_modifiers, sliced_part):
        for vm in visible_modifiers:
            if vm.type == 'BOOLEAN':
                vm.show_viewport = vm.show_render = True
                vm.keyframe_insert('show_viewport')
                vm.keyframe_insert('show_render')
                bool_obj = vm.object
                # recherche si il s'agit de tête de visse
                is_screw = False
                for m in bool_obj.modifiers:
                    if m.type == 'NODES' and m.node_group.name == 'Rivets.Holes':
                        screw = m['Input_12']
                        frame = self.anim_head_screw_bool(screw, frame)
                        is_screw = True
                        break
                if is_screw:
                    continue
                # recherche si le modifier actuel produit un slice
                if bool_obj and bool_obj.get('fluent_operation') == 'SLICE' and vm.operation == 'DIFFERENCE':
                    slice_info = []
                    # recherche et affiche les objets produits par le slice
                    for obj in bpy.data.objects:
                        if obj.type == 'MESH':
                            bool_count = 0
                            for i, m in enumerate(obj.modifiers):
                                if m.type == 'BOOLEAN':
                                    bool_count += 1
                                if m.type == 'BOOLEAN' and m.operation == 'INTERSECT' and m.object == bool_obj:
                                    slice_info.append([obj, m, bool_count])
                    # réordonne la liste
                    slice_info = sorted(slice_info, key=lambda x: x[-1])
                    # affiche uniquement l'objet dont le modifier bool slicer est le plus haut dans la liste des modifiers
                    slice_info[0][0].hide_viewport = False
                    slice_info[0][0].keyframe_insert('hide_viewport')
                    frame = self.anim_object(bool_obj, frame)
                    for s in slice_info:
                        frame = self.anim_object(s[0], frame, s[1])
                else:
                    frame = self.anim_object(bool_obj, frame)
        return frame

    def anim_object(self, obj, frame, start_modifier = None):

        if not obj:
            make_oops([translate('cleanBlender')], translate('error'), 'ERROR')
            return {'FINISHED'}

        if obj in self.already_animated:
            return frame

        if 'inset' in obj.name:
            found = False
            for m in obj.modifiers:
                if found and m.type == 'BOOLEAN' and m.operation == 'INTERSECT':
                    frame = self.anim_object(m.object, frame)
                if m.name == fluent_modifiers_name['inset_solidify']:
                    found = True
            return frame

        self.already_animated.append(obj)

        # masque tous les modifiers
        visible_modifiers = []
        sliced_part = []
        slice_boolean_modifiers = []
        ignore = [
            fluent_modifiers_name['pre_chamfer'],
            fluent_modifiers_name['rotate'],
            fluent_modifiers_name['screw'],
            fluent_modifiers_name['radius'],
            fluent_modifiers_name['decimate'],
            fluent_modifiers_name['center_array_x'],
            fluent_modifiers_name['center_array_y'],
            fluent_modifiers_name['center_array_z'],
            fluent_modifiers_name['path_height'],
            fluent_modifiers_name['path_displace'],
            fluent_modifiers_name['scale'],
            fluent_modifiers_name['weighted_normal'],
            fluent_modifiers_name['outer_bevel'],
            fluent_modifiers_name['second_solidify'],
            fluent_modifiers_name['pre_second_bevel_bottom'],
            fluent_modifiers_name['pre_second_bevel_top'],
        ]
        keep_visible = [
            fluent_modifiers_name['circular_array']
        ]
        start = True
        if start_modifier:
            start = False

        for m in obj.modifiers:

            if m == start_modifier:
                start = True
                continue
            if not start:
                continue

            if m.show_viewport and (m.name not in ignore or m.name == fluent_modifiers_name['screw'] and obj.get('fluent_type') == 'revolver'):
                visible_modifiers.append(m)
                if not m.name in keep_visible:
                    m.show_viewport = m.show_render = False
                    m.keyframe_insert('show_viewport')
                    m.keyframe_insert('show_render')
                    # le modifier actuel est il un booléen produisant un slice
                    if m.type == 'BOOLEAN' and m.object and m.object.get('fluent_operation') == 'SLICE':
                        self.slice_data.append([m,[]])
                        # recherche des objets produits par le slice et les cache
                        for o in bpy.data.objects:
                            if o.type == 'MESH' and o != obj:
                                for mm in o.modifiers:
                                    if mm.type == 'BOOLEAN' and mm.operation == 'INTERSECT' and mm.object == m.object and 'inset' not in o.name:
                                        self.slice_data[-1][1].append(o)
                                        o.hide_viewport = True
                                        o.keyframe_insert('hide_viewport')

        if obj.display_type == 'TEXTURED':
            bpy.context.scene.frame_set(0)
            obj.hide_viewport = True
            obj.keyframe_insert('hide_viewport')
            obj.hide_render = True
            obj.keyframe_insert('hide_render')
            bpy.context.scene.frame_set(frame)
            obj.hide_viewport = False
            obj.keyframe_insert('hide_viewport')
            obj.hide_render = False
            obj.keyframe_insert('hide_render')

        frame = self.anim_mirror(obj, frame, visible_modifiers)

        frame = self.anim_screw(obj, frame, visible_modifiers)

        frame = self.anim_first_solidify(obj, frame, visible_modifiers)

        # frame = self.anim_second_solidify(obj, frame, visible_modifiers)

        frame = self.anim_array(obj, frame, visible_modifiers)

        frame = self.anim_circular_array(obj, frame, visible_modifiers)

        frame = self.anim_first_bevel(obj, frame, visible_modifiers)

        frame = self.anim_second_bevel(obj, frame, visible_modifiers)

        frame = self.anim_taper(obj, frame, visible_modifiers)

        frame = self.anim_boolean(frame, visible_modifiers, slice_boolean_modifiers, sliced_part)

        frame = self.anim_chamfer(obj, frame, visible_modifiers)

        frame = self.anim_frame(obj, frame, visible_modifiers)

        return frame

    def execute(self, context):
        self.obj = active_object('GET')
        self.speed = context.scene.fluentProp.anim_speed
        self.already_animated = []
        if not self.obj:
            return {'CANCELLED'}

        # ce positionne en début de timeline
        frame = bpy.context.scene.frame_current
        # bpy.context.scene.frame_set(frame)
        # self.slice_data.append(self.obj)
        self.anim_object(self.obj, frame)



        return{'FINISHED'}


class FLUENT_OT_ClothAnimation(Operator):
    """See your object growing !"""
    bl_idname = "fluent.clothanimation"
    bl_label = "Animate cloth"
    bl_options = {'REGISTER', 'UNDO'}

    speed = None

    def anim_cloth_panel(self, cloth_panel):
        anim_length = int(12/self.speed)
        obj = cloth_panel[0]
        cloth_modifier = cloth_panel[1]
        # Création du shape key
        active_object('SET', obj, True)
        bpy.ops.object.modifier_apply_as_shapekey(keep_modifier=True, modifier="Cloth")
        cloth_modifier.show_viewport = cloth_modifier.show_render = False
        # Anime la visibilité
        frame = bpy.context.scene.frame_current
        frame -= 1
        bpy.context.scene.frame_set(frame)
        obj.hide_viewport = True
        obj.hide_render = True
        obj.keyframe_insert('hide_viewport')
        obj.keyframe_insert('hide_render')
        frame += 1
        bpy.context.scene.frame_set(frame)
        obj.hide_viewport = False
        obj.hide_render = False
        obj.keyframe_insert('hide_viewport')
        obj.keyframe_insert('hide_render')
        # Anime le shape key
        shape_key = obj.data.shape_keys.key_blocks['Cloth']
        shape_key.value = 0
        shape_key.keyframe_insert('value')
        frame += anim_length
        bpy.context.scene.frame_set(frame)
        shape_key.value = 1
        shape_key.keyframe_insert('value')
        frame -= anim_length
        bpy.context.scene.frame_set(frame)


    def execute(self, context):
        cloth_panels = []
        self.speed = context.scene.fluentProp.anim_speed
        for obj in context.selected_objects:
            for m in obj.modifiers:
                if m.type == 'CLOTH' and m.name == 'Cloth':
                    cloth_panels.append([obj, m])
        if not cloth_panels:
            make_oops([translate('noObjectWithCloth')], translate('info'), 'ERROR')
            return{'CANCELLED'}
        for cloth_panel in cloth_panels:
            self.anim_cloth_panel(cloth_panel)
        return{'FINISHED'}


class FLUENT_OT_SliceCleaner(Operator):
    """Remove invisible faces in slice cuts"""
    bl_idname = 'fluent.slicecleaner'
    bl_label = 'Slice cleaner'

    def execute(self, context):
        obj = bpy.context.active_object
        mesh = obj.data
        bm = bmesh.new()
        bm.from_mesh(mesh)

        faces_to_delete = []

        # Parcourir toutes les faces et vérifiez si leurs normales sont opposées, coplanaires et que les vertices sont confondus
        for face1 in bm.faces:
            equation_plan = plan_equation(v=face1.calc_center_median(), n=face1.normal)
            for face2 in bm.faces:
                if face1 != face2:
                    dot_product = face1.normal.dot(face2.normal)
                    if dot_product < -0.99:  # les faces sont opposés
                        if plan_equation(do='CHECK', eq=equation_plan, v=face2.calc_center_median()): # les plans sont coplanaires
                            epsilon = 0.001
                            exit = False
                            for vertex1 in face2.verts:
                                for vertex2 in face1.verts:
                                    distance = vertex1.co - vertex2.co
                                    if distance.length < epsilon:
                                        faces_to_delete.extend([face1.index, face2.index])
                                        exit = True
                                        break
                                if exit:
                                    break


        # Supprimer les faces par leurs indices
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        for face_index in faces_to_delete:
            mesh.polygons[face_index].select = True

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.delete(type='FACE')
        bpy.ops.object.mode_set(mode='OBJECT')

        # Libérer la ressource BMESH
        bm.free()

        return {'FINISHED'}