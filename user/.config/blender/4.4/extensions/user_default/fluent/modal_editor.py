import bpy

from bpy.types import Operator
from bpy.props import StringProperty

from .UI.Helpers.viewport_drawing import *
from .modifiers import *
from .bevels import *
from .Tools.independant_helper import *
from .UI.Helpers.ui_management import *
from .UI.make_button import make_button
from .Tools.translation import translate

def box_ui():
    # menu box
    pie_menu = FLUENT_Ui_Layout('BOX')
    pie_menu.set_layout('PIE')

    button = make_button('QUIT')
    pie_menu.add_item(button)

    pie_menu.add_separator()

    button = make_button('CHAMFER')
    pie_menu.add_item(button)

    button = make_button('SECOND_BEVEL')
    pie_menu.add_item(button)

    button = make_button('FIRST_BEVEL')
    pie_menu.add_item(button)

    button = make_button('FIRST_SOLIDIFY')
    pie_menu.add_item(button)

    pie_menu.add_separator()

    button = make_button('MIRROR')
    pie_menu.add_item(button)

    button = make_button('ARRAY')
    pie_menu.add_item(button)

    button = make_button('CIRCULAR_ARRAY')
    pie_menu.add_item(button)

    button = make_button('MORE')
    pie_menu.add_item(button)

    pie_menu.add_separator()

    for b in pie_menu.get_items():
        try:
            b.set_show(False)
        except:
            pass

    ### EXTRA
    pie_menu_extra = FLUENT_Ui_Layout('EXTRA_MENU', title=translate('extraMenu'), subtitle=translate('holdShift'))
    pie_menu_extra.set_layout('PIE')

    button = make_button('TAPER')
    pie_menu_extra.add_item(button)

    button = make_button('FRAME')
    pie_menu_extra.add_item(button)

    button = make_button('SECOND_SOLIDIFY')
    pie_menu_extra.add_item(button)

    button = make_button('BACK')
    pie_menu_extra.add_item(button)

    pie_menu_extra.set_decalage(1)

    return pie_menu, pie_menu_extra


def shape_ui():
    # menu shape
    pie_menu = FLUENT_Ui_Layout('POLY')
    pie_menu.set_layout('PIE')

    button = make_button('QUIT')
    pie_menu.add_item(button)

    pie_menu.add_separator()

    button = make_button('CHAMFER')
    pie_menu.add_item(button)

    button = make_button('SECOND_BEVEL')
    pie_menu.add_item(button)

    button = make_button('FIRST_BEVEL')
    pie_menu.add_item(button)

    button = make_button('FIRST_SOLIDIFY')
    pie_menu.add_item(button)

    pie_menu.add_separator()

    button = make_button('MIRROR')
    pie_menu.add_item(button)

    button = make_button('ARRAY')
    pie_menu.add_item(button)

    button = make_button('CIRCULAR_ARRAY')
    pie_menu.add_item(button)

    button = make_button('MORE')
    pie_menu.add_item(button)

    pie_menu.add_separator()

    for b in pie_menu.get_items():
        try:
            b.set_show(False)
        except:
            pass

    ### EXTRA
    pie_menu_extra = FLUENT_Ui_Layout('EXTRA_MENU', title=translate('extraMenu'), subtitle=translate('holdShift'))
    pie_menu_extra.set_layout('PIE')

    button = make_button('TAPER')
    pie_menu_extra.add_item(button)

    button = make_button('FRAME')
    pie_menu_extra.add_item(button)

    button = make_button('SECOND_SOLIDIFY')
    pie_menu_extra.add_item(button)

    button = make_button('CURVE')
    pie_menu_extra.add_item(button)

    button = make_button('BACK')
    pie_menu_extra.add_item(button)

    pie_menu_extra.set_decalage(1)

    return pie_menu, pie_menu_extra


def path_ui():
    # menu path
    pie_menu = FLUENT_Ui_Layout('PATH')
    pie_menu.set_layout('PIE')

    button = make_button('QUIT')
    pie_menu.add_item(button)

    pie_menu.add_separator()

    button = make_button('SECOND_SOLIDIFY')
    pie_menu.add_item(button)

    button = make_button('TAPER')
    pie_menu.add_item(button)

    button = make_button('SECOND_BEVEL')
    pie_menu.add_item(button)

    button = make_button('FIRST_BEVEL')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_tool_tip(translate('thickness'))
    button.set_shape('CIRCLE')
    button.set_icon('thickness')
    button.set_action('PATH_THICKNESS')
    pie_menu.add_item(button)

    button = FLUENT_Ui_Button()
    button.set_text('')
    button.set_tool_tip(translate('height'))
    button.set_shape('CIRCLE')
    button.set_icon('first_solidify')
    button.set_action('PATH_HEIGHT')
    pie_menu.add_item(button)

    pie_menu.add_separator()

    button = make_button('MIRROR')
    pie_menu.add_item(button)

    button = make_button('ARRAY')
    pie_menu.add_item(button)

    button = make_button('CIRCULAR_ARRAY')
    pie_menu.add_item(button)

    pie_menu.add_separator()

    for b in pie_menu.get_items():
        try:
            b.set_show(False)
        except:
            pass
    return pie_menu


def prism_ui():
    # menu prism
    pie_menu = FLUENT_Ui_Layout('PRISM')
    pie_menu.set_layout('PIE')

    button = make_button('QUIT')
    pie_menu.add_item(button)

    pie_menu.add_separator()

    button = make_button('CHAMFER')
    pie_menu.add_item(button)

    button = make_button('SECOND_BEVEL')
    pie_menu.add_item(button)

    button = make_button('FIRST_SOLIDIFY')
    pie_menu.add_item(button)

    pie_menu.add_separator()

    button = make_button('RESOLUTION')
    pie_menu.add_item(button)

    button = make_button('RADIUS')
    pie_menu.add_item(button)

    pie_menu.add_separator()

    button = make_button('MIRROR')
    pie_menu.add_item(button)

    button = make_button('ARRAY')
    pie_menu.add_item(button)

    button = make_button('CIRCULAR_ARRAY')
    pie_menu.add_item(button)

    button = make_button('MORE')
    pie_menu.add_item(button)

    pie_menu.add_separator()

    for b in pie_menu.get_items():
        try:
            b.set_show(False)
        except:
            pass

    ### EXTRA
    pie_menu_extra = FLUENT_Ui_Layout('EXTRA_MENU', title=translate('extraMenu'), subtitle=translate('holdShift'))
    pie_menu_extra.set_layout('PIE')

    button = make_button('TAPER')
    pie_menu_extra.add_item(button)

    button = make_button('FRAME')
    pie_menu_extra.add_item(button)

    button = make_button('SECOND_SOLIDIFY')
    pie_menu_extra.add_item(button)

    button = make_button('BACK')
    pie_menu_extra.add_item(button)

    pie_menu_extra.set_decalage(1)

    return pie_menu, pie_menu_extra


def sphere_ui():
    # menu prism
    pie_menu = FLUENT_Ui_Layout('SPHERE')
    pie_menu.set_layout('PIE')

    button = make_button('QUIT')
    pie_menu.add_item(button)

    pie_menu.add_separator()

    button = make_button('SECOND_SOLIDIFY')
    pie_menu.add_item(button)

    button = make_button('TAPER')
    pie_menu.add_item(button)

    button = make_button('RESOLUTION')
    pie_menu.add_item(button)

    button = make_button('RADIUS')
    pie_menu.add_item(button)

    pie_menu.add_separator()

    button = make_button('MIRROR')
    pie_menu.add_item(button)

    button = make_button('ARRAY')
    pie_menu.add_item(button)

    button = make_button('CIRCULAR_ARRAY')
    pie_menu.add_item(button)

    pie_menu.add_separator()

    for b in pie_menu.get_items():
        try:
            b.set_show(False)
        except:
            pass
    return pie_menu


def revolver_ui():
    # menu revolver
    pie_menu = FLUENT_Ui_Layout('PRISM')
    pie_menu.set_layout('PIE')

    button = make_button('QUIT')
    pie_menu.add_item(button)

    pie_menu.add_separator()

    button = FLUENT_Ui_Button()
    button.set_text(translate('flip'))
    button.set_shape('CIRCLE')
    button.set_action('FLIP_SCREW')
    pie_menu.add_item(button)

    button = make_button('SECOND_SOLIDIFY')
    pie_menu.add_item(button)

    button = make_button('TAPER')
    pie_menu.add_item(button)

    button = make_button('SECOND_BEVEL')
    pie_menu.add_item(button)

    button = make_button('FIRST_BEVEL')
    pie_menu.add_item(button)

    button = make_button('RESOLUTION')
    pie_menu.add_item(button)

    pie_menu.add_separator()

    button = make_button('MIRROR')
    pie_menu.add_item(button)

    button = make_button('ARRAY')
    pie_menu.add_item(button)

    button = make_button('CIRCULAR_ARRAY')
    pie_menu.add_item(button)

    pie_menu.add_separator()

    for b in pie_menu.get_items():
        try:
            b.set_show(False)
        except:
            pass
    return pie_menu


def unknow_ui():
    pie_menu = FLUENT_Ui_Layout('UNKNOW')
    pie_menu.set_layout('PIE')

    button = make_button('QUIT')
    pie_menu.add_item(button)

    for b in pie_menu.get_items():
        try:
            b.set_show(False)
        except:
            pass
    return pie_menu


def plate_ui():
    # menu box
    pie_menu = FLUENT_Ui_Layout('BOX')
    pie_menu.set_layout('PIE')

    button = make_button('QUIT')
    pie_menu.add_item(button)

    button = make_button('FIRST_SOLIDIFY')
    pie_menu.add_item(button)

    pie_menu.add_separator()

    button = make_button('MIRROR')
    pie_menu.add_item(button)

    pie_menu.add_separator()

    # pie_menu.set_decalage(-2)

    for b in pie_menu.get_items():
        try:
            b.set_show(False)
        except:
            pass
    return pie_menu


class FLUENT_OT_Editor(Operator):
    """Edit a Fluent object"""
    bl_idname = "fluent.editor"
    bl_label = "Fluent editor"
    bl_options = {'REGISTER', 'UNDO'}

    bool_obj_name: StringProperty(
        default=''
    )
    cut_obj_name: StringProperty(
        default=''
    )
    operation: StringProperty(
        default=''
    )
    call_from: StringProperty(
        default=''
    )

    def init_variables(self, event):
        self.ui_management = FLUENT_ui_management(event)
        self.bool_drawing = None
        self.blender_operator_running = False
        self.action = None

        if self.operation != 'EDIT':
            if bpy.data.objects.get(self.cut_obj_name):
                self.cut_object = bpy.data.objects.get(self.cut_obj_name)
                depsgraph = bpy.context.evaluated_depsgraph_get()
                self.cut_object_eval = self.cut_object.evaluated_get(depsgraph)
            else:
                self.cut_object = None
                self.cut_object_eval = None

            self.bool_obj = bpy.data.objects.get(self.bool_obj_name)
            self.fluent_adjustments = None
        else:
            self.cut_object = None
            self.bool_obj = None
            self.fluent_adjustments = None

        self.bevel = F_outer_bevel()

        self.ui_management.event_dico_builder()

        # if event.value == 'PRESS' and event.type == 'LEFTMOUSE':
        #     self.events['mouse_left_click'] = True
        # if event.value == 'RELEASE' and event.type == 'LEFTMOUSE':
        #     self.events['mouse_left_click'] = False

        self.statut = 'EN_ATTENTE'

        button = make_button('CANCEL')
        self.ui_management.add_items(button)

        row = FLUENT_Ui_Layout('CUT OPERATIONS')

        if self.operation not in ['EDIT', 'CREATION', 'PLATE']:
            button = FLUENT_Ui_Button()
            button.set_text('')
            button.set_tool_tip(translate('cutAdd'))
            button.set_shape('CIRCLE')
            button.set_action('CUT')
            button.set_icon('cut')
            row.add_item(button)

            button = FLUENT_Ui_Button()
            button.set_text('')
            button.set_tool_tip(translate('slice'))
            button.set_shape('CIRCLE')
            button.set_action('SLICE')
            button.set_icon('slice')
            row.add_item(button)

            button = FLUENT_Ui_Button()
            button.set_text('')
            button.set_tool_tip(translate('inset'))
            button.set_shape('CIRCLE')
            button.set_action('INSET')
            button.set_icon('inset')
            row.add_item(button)

        if self.operation not in ['CREATION', 'PLATE']:
            button = FLUENT_Ui_Button()
            button.set_text('')
            button.set_tool_tip(translate('newDrawing'))
            button.set_action('NEW_DRAWING')
            button.set_shape('CIRCLE')
            button.set_icon('draw')
            row.add_item(button)

        button = FLUENT_Ui_Button()
        button.set_text('')
        button.set_tool_tip(translate('showHideBoolean'))
        button.set_action('SHOW_BOOLEAN')
        button.set_shape('CIRCLE')
        button.set_icon('show_bool')
        row.add_item(button)

        row.spread()

        self.ui_management.add_items(row)

    def initialisation(self):
        if self.operation in ['CUT', 'SLICE', 'INSET', '*CUT']:
            # en cas de sortie de dessin le booléen est à rajouter
            if self.cut_object and self.bool_obj:
                bool = find_boolean_modifier(self.bool_obj, self.cut_object)

                if not bool:
                    bool = self.cut_object.modifiers.new(type='BOOLEAN', name=fluent_modifiers_name['boolean'])
                    bool.object = self.bool_obj
                    bool.solver = 'FAST'
                    bool.show_expanded = False
                    bool.show_in_editmode = True
                    self.bool_obj['fluent_operation'] = 'CUT'
                    if self.bool_obj.get('fluent_type') in ['revolver']:
                        co_y_moyen = 0
                        for v in self.bool_obj.data.vertices:
                            co_y_moyen = co_y_moyen + v.co.y
                        co_y_moyen = co_y_moyen / len(self.bool_obj.data.vertices)
                        if co_y_moyen > 0:
                            bool.operation = 'UNION'

                # cut the cutter
                if self.cut_object.get('fluent_type') in ['box', 'prism', 'poly', 'path', 'revolver']:
                    place_in_stack(self.cut_object, bool)
        elif self.operation == 'EDIT':
            if len(bpy.context.selected_objects) != 1:
                make_oops([translate('selectOneObject')], title=translate('howToUse'), icon='ERROR')
                return 'FINISHED'

            obj = active_object(action='GET')
            if obj.get('fluent_type') in ['box', 'prism', 'sphere', 'poly', 'path', 'revolver', 'unknow', 'plate', 'head_screw']:
                self.bool_obj = obj
                self.modifiers_stack_save = save_modifers_stack(obj)
                cut_objects = find_boolean_targets(self.bool_obj)
                try:
                    self.cut_object = cut_objects[0]['cut_object']
                    bool = cut_objects[0]['boolean_modifier']
                except:pass
            else:
                make_oops([translate('selectFluentObject')], title=translate('howToUse'), icon='ERROR')
                return 'FINISHED'

        # on vérifie la présence de modifiers de base si rien, c'est que l'on sort de dessin et il faut les rajouter
        # et lancer l'ajustement du solidify
        if self.bool_obj:
            self.fluent_adjustments = modifiers_manager(obj=self.bool_obj, bool_target=self.cut_object)
            # if self.operation == 'EDIT' and self.bool_obj.get('fluent_type') not in ['box', 'poly', 'path', 'prism', 'sphere', 'revolver', 'plate', 'head_screw'] and (not get_addon_preferences().bevel_system == 'MULTIPLE' and self.bool_obj.get('fluent_type') == 'unknow'):
            #     make_oops(
            #         [translate('cantBeEdited'), translate('selectFluentObject')],
            #         title=translate('problem'), icon='ERROR')
            #     return 'FINISHED'

            if self.bool_obj['fluent_type'] == 'box':
                self.pie_menu_root, self.extra_menu = box_ui()
                layout = FLUENT_Ui_Layout('TRANSFORM')
                layout.set_layout('COLUMN_LEFT')
                button = make_button('DIMENSIONS')
                layout.add_item(button)
                button = make_button('ROTATION')
                layout.add_item(button)
                button = make_button('REUSE')
                layout.add_item(button)
                layout.spread()
                self.ui_management.add_items(layout)

                if self.operation not in ['CUT', 'EDIT', 'CREATION']:
                    self.operation = change_bool_operation(self.bool_obj, self.cut_object, self.operation)

            elif self.bool_obj['fluent_type'] == 'poly':
                self.pie_menu_root, self.extra_menu = shape_ui()

                layout = FLUENT_Ui_Layout('TRANSFORM')
                layout.set_layout('COLUMN_LEFT')
                button = make_button('DIMENSIONS')
                layout.add_item(button)
                button = make_button('ROTATION')
                layout.add_item(button)
                button = make_button('REUSE')
                layout.add_item(button)
                layout.spread()
                self.ui_management.add_items(layout)

                if self.operation not in ['CUT', 'EDIT', 'CREATION']:
                    self.operation = change_bool_operation(self.bool_obj, self.cut_object, self.operation)

            elif self.bool_obj['fluent_type'] == 'path':
                self.pie_menu_root = path_ui()

                layout = FLUENT_Ui_Layout('TRANSFORM')
                layout.set_layout('COLUMN_LEFT')
                button = make_button('DIMENSIONS')
                layout.add_item(button)
                button = make_button('ROTATION')
                layout.add_item(button)
                button = make_button('REUSE')
                layout.add_item(button)
                layout.spread()
                self.ui_management.add_items(layout)

                if self.operation not in ['CUT', 'EDIT', 'CREATION']:
                    self.operation = change_bool_operation(self.bool_obj, self.cut_object, self.operation)

            elif self.bool_obj['fluent_type'] == 'prism':
                self.pie_menu_root, self.extra_menu = prism_ui()

                for mod in self.bool_obj.modifiers:
                    if fluent_modifiers_name['inner_radius'] in mod.name:
                        if mod.strength != 0:
                            self.pie_menu_root.remove_item('CHAMFER')
                            break

                layout = FLUENT_Ui_Layout('TRANSFORM')
                layout.set_layout('COLUMN_LEFT')
                button = make_button('DIMENSIONS')
                layout.add_item(button)
                button = make_button('ROTATION')
                layout.add_item(button)
                button = make_button('REUSE')
                layout.add_item(button)
                layout.spread()
                self.ui_management.add_items(layout)

                if self.operation not in ['CUT', 'EDIT', 'CREATION']:
                    self.operation = change_bool_operation(self.bool_obj, self.cut_object, self.operation)

            elif self.bool_obj['fluent_type'] == 'sphere':
                self.pie_menu_root = sphere_ui()

                layout = FLUENT_Ui_Layout('TRANSFORM')
                layout.set_layout('COLUMN_LEFT')
                button = make_button('DIMENSIONS')
                layout.add_item(button)
                button = make_button('ROTATION')
                layout.add_item(button)
                button = make_button('REUSE')
                layout.add_item(button)
                layout.spread()
                self.ui_management.add_items(layout)

                if self.operation not in ['CUT', 'EDIT', 'CREATION']:
                    self.operation = change_bool_operation(self.bool_obj, self.cut_object, self.operation)

            elif self.bool_obj['fluent_type'] == 'revolver':
                self.pie_menu_root = revolver_ui()

                layout = FLUENT_Ui_Layout('TRANSFORM')
                layout.set_layout('COLUMN_LEFT')
                button = make_button('DIMENSIONS')
                layout.add_item(button)
                button = make_button('ROTATION')
                layout.add_item(button)
                button = make_button('REUSE')
                layout.add_item(button)
                layout.spread()
                self.ui_management.add_items(layout)

                if self.operation not in ['CUT', 'EDIT', 'CREATION']:
                    self.operation = change_bool_operation(self.bool_obj, self.cut_object, self.operation)

            elif self.bool_obj['fluent_type'] == 'unknow':
                self.pie_menu_root = unknow_ui()

                if self.operation not in ['CUT', 'EDIT', 'CREATION']:
                    self.operation = change_bool_operation(self.bool_obj, self.cut_object, self.operation)
                boolean_visibility_setup(self.bool_obj)

            elif self.bool_obj['fluent_type'] == 'plate':
                self.pie_menu_root = plate_ui()

            self.bool_drawing = FLUENT_Draw_Object(self.bool_obj, (1, 1, 1, .05))

            if self.bool_obj.display_type == 'WIRE':
                self.bool_obj.hide_set(True)
            else:
                self.bool_obj.hide_set(False)

            if self.operation == 'INSET' or (self.operation == 'EDIT' and self.bool_obj.get('fluent_inset')):
                button = make_button('INSET')
                self.pie_menu_root.add_item(button)

            if self.operation != '*CUT':
                if self.operation != 'EDIT' and self.bool_obj.get('fluent_type') in ['box', 'poly', 'prism']:
                    if self.operation == 'CREATION':
                        try:
                            self.bool_obj.modifiers[fluent_modifiers_name['first_solidify']].offset = 0
                        except:
                            first_solidify_management(self.bool_obj)
                            self.bool_obj.modifiers[fluent_modifiers_name['first_solidify']].offset = 0
                    self.fluent_adjustments.set_adjust_what('FIRST_SOLIDIFY')
                    self.statut = 'AJUSTEMENT_EN_COURS'
                elif self.operation != 'EDIT' and self.bool_obj.get('fluent_type') in ['path']:
                    self.fluent_adjustments.set_adjust_what('PATH_HEIGHT')
                    self.statut = 'AJUSTEMENT_EN_COURS'
                elif self.operation != 'EDIT' and self.bool_obj.get('fluent_type') in ['revolver']:
                    decimate = self.bool_obj.modifiers.new(name=fluent_modifiers_name['decimate'], type='DECIMATE')
                    decimate.decimate_type = 'DISSOLVE'
                    decimate.angle_limit = 0.00872665
                    decimate.delimit = {'NORMAL'}
                    self.fluent_adjustments.set_adjust_what('RESOLUTION')
                    self.statut = 'AJUSTEMENT_EN_COURS'
                elif self.operation != 'EDIT' and self.bool_obj.get('fluent_type') in ['plate']:
                    try:
                        self.bool_obj.modifiers[fluent_modifiers_name['first_solidify']].thickness = bpy.context.scene.fluentProp.plate_solidify_thickness
                    except:
                        first_solidify_management(self.bool_obj)
                        self.bool_obj.modifiers[fluent_modifiers_name['first_solidify']].thickness = bpy.context.scene.fluentProp.plate_solidify_thickness
                    if bpy.context.scene.fluentProp.plate_solidify_thickness == 0:
                        self.statut = 'AJUSTEMENT_EN_COURS'
                        self.fluent_adjustments.set_adjust_what('FIRST_SOLIDIFY')
                    # if get_addon_preferences().bevel_system == 'MULTIPLE':
                    #     if self.operation == 'CREATE':
                    #         self.bevel.set_target(self.bool_obj)
                    #         self.bevel.management()
                    #         self.fluent_adjustments.outer_bevel_preparation()
                    #     button = make_button('OUTER_BEVEL')
                    #     self.pie_menu_root.add_item(button)
                    # else:
                    #     self.bevel.set_target(self.bool_obj)
                    #     self.bevel.management()

        if self.cut_object and not self.cut_object.get('fluent_operation'):
            if get_addon_preferences().bevel_system == 'MULTIPLE':
                if self.operation != 'EDIT':
                    self.bevel.set_target(self.cut_object)
                    self.bevel.management()
                try:
                    self.fluent_adjustments.outer_bevel_preparation(cut_objects)
                except:
                    cut_objects = find_boolean_targets(self.bool_obj)
                    self.fluent_adjustments.outer_bevel_preparation(cut_objects)
                outer_bevel_button = [b.get_id() for b in self.pie_menu_root.get_items() if b.get_id() == 'OUTER_BEVEL']
                if not outer_bevel_button:
                    button = make_button('OUTER_BEVEL')
                    self.pie_menu_root.add_item(button)
            else:
                self.bevel.set_target(self.cut_object)
                self.bevel.management()
        # elif self.operation == 'EDIT' and self.bool_obj.get('fluent_type') == 'plate':
        #     if get_addon_preferences().bevel_system == 'MULTIPLE':
        #         self.bevel.set_target(self.bool_obj)
        #         self.fluent_adjustments.outer_bevel_preparation()
        #         button = make_button('OUTER_BEVEL')
        #         self.pie_menu_root.add_item(button)
        #     else:
        #         self.bevel.set_target(self.bool_obj)
        #         self.bevel.management()

        # Si on édite un booléen → on cache les autres
        if self.bool_obj.get('fluent_operation'):
            for o in bpy.data.collections[get_addon_preferences().bool_collection].objects:
                if o != self.bool_obj:
                    o.hide_set(True)

        self.ui_management.add_items(self.pie_menu_root)

    def end(self, option='FINISHED'):
        bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
        bpy.types.SpaceView3D.draw_handler_remove(self._handle_obj_draw, 'WINDOW')
        if option == 'FINISHED':
            self.bool_obj.hide_viewport = False
            if self.cut_object and self.operation not in ['CREATION', 'PLATE'] or self.operation == 'EDIT' and self.bool_obj.display_type != 'TEXTURED':
                self.bool_obj.hide_set(get_addon_preferences().auto_hide_bool)

            if self.bool_obj.get('fluent_type') == 'plate':
                bpy.context.scene.fluentProp.plate_solidify_thickness = self.bool_obj.modifiers[fluent_modifiers_name['first_solidify']].thickness
            if self.events['shift_work']:
                active_object('SET', self.bool_obj, True)
                bpy.ops.object.convert(target='MESH')
                try:
                    del self.bool_obj['fluent_type']
                except:pass
        elif option == 'CANCELLED':
            if self.operation != 'EDIT':
                try:
                    bpy.data.objects.remove(self.bool_obj['fluent_slice'], do_unlink=True)
                except:pass
                try:
                    bpy.data.objects.remove(self.bool_obj['fluent_inset'], do_unlink=True)
                except:pass
                try:
                    bpy.data.objects.remove(self.bool_obj, do_unlink=True)
                except:pass
                try:
                    boolean_cleaner([self.cut_object])
                except:pass
            else:
                remake_modifiers_stack(self.bool_obj, self.modifiers_stack_save)

        try:
            active_object('SET', self.cut_object, True)
        except:pass

    def shortcut(self, event, action):
        if event.type == 'H' and event.value == 'PRESS':
            action = 'SHOW_BOOLEAN'
        if event.type == 'W' and event.value == 'PRESS':
            try:
                if self.cut_object.show_wire:
                    self.cut_object.show_wire = False
                else:
                    self.cut_object.show_wire = True
            except:pass
        if event.type in ['RIGHTMOUSE'] and event.value == 'PRESS':
            action = 'FINISHED'
        if event.type in ['ESC'] and event.value == 'PRESS':
            action = 'CANCELLED'

        # boolean shortcut
        if self.operation not in ['EDIT', 'CREATION']:
            if event.type == 'I' and event.value == 'PRESS':
                action = 'INTERSECT'
                self.bool_obj['inib_auto_bool_switching'] = True
            if event.type == 'U' and event.value == 'PRESS':
                action = 'UNION'
                self.bool_obj['inib_auto_bool_switching'] = True
            if event.type == 'D' and event.value == 'PRESS':
                action = 'DIFFERENCE'
                self.bool_obj['inib_auto_bool_switching'] = True

        # adjustment shortcut
        if event.type == 'S' and event.value == 'PRESS' and self.statut != 'AJUSTEMENT_EN_COURS':
            action = 'FIRST_SOLIDIFY'
        elif event.type == 'B' and event.value == 'PRESS' and self.statut != 'AJUSTEMENT_EN_COURS':
            action = 'FIRST_BEVEL'
        elif event.type == 'M' and event.value == 'PRESS' and self.statut != 'AJUSTEMENT_EN_COURS':
            action = 'MIRROR'
        elif event.type == 'A' and event.value == 'PRESS' and self.statut != 'AJUSTEMENT_EN_COURS':
            action = 'ARRAY'

        return action

    def modal(self, context, event):
        if pass_through(event) or event.type == 'TAB' or event.type in ['G', 'R']:
            try:
                if event.type == 'TAB' and event.value == 'PRESS':
                    active_object('SET', self.bool_obj, True)
                    if bpy.context.active_object:
                        if self.bool_obj.get('fluent_operation'):
                            if bpy.context.active_object.mode == 'OBJECT':
                                self.bool_obj.hide_set(False)
                            else:
                                self.bool_obj.hide_set(True)
                    else:
                        if self.bool_obj.get('fluent_operation'):
                            self.bool_obj.hide_set(False)
                        # active_object('SET', self.bool_obj, True)

                if event.type in ['G', 'R'] and event.value == 'PRESS':
                    active_object('SET', self.bool_obj, True)
                    if self.bool_obj.get('fluent_operation'):
                        self.bool_obj.hide_set(False)
                    # active_object('SET', self.bool_obj, True)
                    self.blender_operator_running = 'MOVE'

                return {'PASS_THROUGH'}
            except:pass

        try:
            if bpy.context.active_object.mode == 'EDIT' or self.blender_operator_running:
                if self.blender_operator_running == 'MOVE' and event.type in ['LEFTMOUSE', 'RIGHTMOUSE', 'ESC'] and event.value == 'PRESS':
                    self.blender_operator_running = False
                    if self.bool_obj.get('fluent_operation'):
                        self.bool_obj.hide_set(True)
                return {'PASS_THROUGH'}
        except:pass

        self.ui_management.refresh_ui_items_list()
        self.events = self.ui_management.event_dico_refresh(event)
        context.area.tag_redraw()

        # Ajustement
        if self.statut == 'AJUSTEMENT_EN_COURS':
            callback = self.fluent_adjustments.adjust(self.ui_management)
            if self.fluent_adjustments.get_adjust_what() in WIDGET_ACTIONS:
                self.ui_management.pause_toggle = True

        if 'callback' in locals() and 'PASS_THROUGH' in callback:
            return {'PASS_THROUGH'}

        if 'callback' in locals() and 'STOP_ADJUSTMENT' in callback:
            self.ui_management.clean_side_infos()
            self.ui_management.pause_toggle = False
            if 'CLOSE_WIDGET' in callback:
                self.ui_management.refresh_ui_items_list(close_widget=True)
            else:
                self.ui_management.remove_last_menu()

            if 'INNER_RADIUS_ON' in callback:
                self.pie_menu_root.remove_item('CHAMFER')
            if 'INNER_RADIUS_OFF' in callback:
                button = make_button('CHAMFER')
                self.pie_menu_root.add_item(button, 2)
            self.ui_management.hide_menu()
            self.statut = 'EN_ATTENTE'
            return {'RUNNING_MODAL'}
        # Fin ajustement

        # récupère l'action
        action = self.ui_management.get_button_action()[0]
        action = self.shortcut(event, action)

        if action:
            if action == 'FINISHED':
                self.end()
                return {'FINISHED'}
            if action == 'CANCELLED':
                self.end('CANCELLED')
                return {'FINISHED'}
            elif action in ['VALIDATE', 'CROSS', 'FAKE_SLICE', 'REMOVE']:
                if 'callback' in locals() and 'CLOSE_WIDGET' in callback:
                    self.ui_management.refresh_ui_items_list(close_widget=True)
                else:
                    self.ui_management.remove_last_menu()
                self.statut = 'EN_ATTENTE'
            elif action in ['FIRST_SOLIDIFY', 'FIRST_BEVEL', 'SECOND_BEVEL', 'SECOND_SOLIDIFY', 'MIRROR', 'TAPER',
                            'ARRAY', 'CIRCULAR_ARRAY', 'DIMENSIONS', 'ROTATION', 'REUSE', 'RADIUS', 'RESOLUTION',
                            'INSET_THICKNESS', 'PATH_THICKNESS', 'PATH_HEIGHT', 'CURVE', 'OUTER_BEVEL', 'FRAME', 'CHAMFER']:
                self.fluent_adjustments.set_adjust_what(action)
                self.statut = 'AJUSTEMENT_EN_COURS'

                if action in WIDGET_ACTIONS:
                    self.ui_management.pause_toggle = True
            elif action == 'FLIP_SCREW':
                self.bool_obj.modifiers[fluent_modifiers_name['screw']].use_normal_flip = not self.bool_obj.modifiers[
                    fluent_modifiers_name['screw']].use_normal_flip
            elif action == 'NEW_DRAWING':
                if self.operation != 'CREATION':
                    if self.operation != 'EDIT':
                        if event.shift:
                            if self.operation != 'CREATION': self.bool_obj.hide_set(False)
                            active_object(action='SET', obj=self.bool_obj, solo=True)
                        else:
                            if self.operation != 'CREATION':
                                if get_addon_preferences().auto_hide_bool:
                                    self.bool_obj.hide_set(True)
                            active_object(action='SET', obj=self.cut_object, solo=True)
                    else:
                        self.bool_obj.hide_set(False)
                        active_object(action='SET', obj=self.bool_obj, solo=True)
                    bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
                    bpy.types.SpaceView3D.draw_handler_remove(self._handle_obj_draw, 'WINDOW')
                    bpy.ops.fluent.cutter('INVOKE_DEFAULT')
                    return {'FINISHED'}
            elif action in ['CUT', 'SLICE', 'INSET', 'INTERSECT', 'UNION', 'DIFFERENCE']:
                if action != self.operation:
                    previous_operation = self.operation
                    self.operation = change_bool_operation(self.bool_obj, self.cut_object, action)
                    if self.operation == 'INSET' and previous_operation != 'INSET':
                        for p in self.ui_management.get_items()[1]:
                            if p.get_id() in ['BOX', 'POLY', 'PRISM', 'UNKNOW', 'PATH']:
                                button = make_button('INSET')
                                p.add_item(button)
                    elif previous_operation == 'INSET' and self.operation != 'INSET':
                        for p in self.ui_management.get_items()[1]:
                            if p.get_id() in ['BOX', 'POLY', 'PRISM']:
                                p.remove_item('INSET')
                    cut_objects = find_boolean_targets(self.bool_obj)
                    self.fluent_adjustments.outer_bevel_preparation(cut_objects)
            elif action == 'SHOW_BOOLEAN':
                if self.events['shift_work']:
                    affichage_booleen()
                else:
                    if self.bool_obj['fluent_type'] not in ['plate']:
                        self.bool_obj.hide_viewport = not self.bool_obj.hide_viewport
            elif action == 'EXTRA_MENU' and not event.shift:
                self.ui_management.position_menu_under_previous(self.extra_menu)
                self.ui_management.add_items(self.extra_menu, is_submenu=True)
                refresh_pos = False
            elif action == 'BACK_MENU' and not event.shift:
                self.ui_management.remove_last_menu(is_submenu=True)

        # gestion affichage du pie menu
        self.ui_management.toggle_menu_displaying()

        if self.bool_obj.get('fluent_type') == 'unknow' and self.operation not in ['EDIT', 'CREATION'] and self.statut != 'AJUSTEMENT_EN_COURS':
            self.ui_management.side_infos.add_line(translate('difference'), 'D', True)
            self.ui_management.side_infos.add_line(translate('union'), 'U')
            self.ui_management.side_infos.add_line(translate('intersect'), 'I')

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        # VERIFICATIONS
        try:
            bpy.ops.object.mode_set(mode='OBJECT')
        except:
            pass

        # test si uniquement des objets sont sélectionnés
        for o in bpy.context.selected_objects:
            if o.type not in ['MESH', 'CURVE']:
                make_oops([translate('nonObjectThing')], title=translate('howToUse'), icon='ERROR')
                return {'FINISHED'}

        # test si l'objet actif est un objet fluent
        if self.operation == 'EDIT':
            obj = active_object('GET')
            if obj:
                fluent_type = obj.get('fluent_type')
                if fluent_type:
                    test = False
                    if fluent_type in ['box', 'poly', 'prism', 'plate']:
                        if self.call_from == 'become_fluent':
                            test = True
                        else:
                            for m in obj.modifiers:
                                if m.name == fluent_modifiers_name['first_solidify']:
                                    test = True
                    if fluent_type == 'sphere':
                        for m in obj.modifiers:
                            if m.name == fluent_modifiers_name['screw_2']:
                                test = True
                    if fluent_type == 'path':
                        for m in obj.modifiers:
                            if m.name == fluent_modifiers_name['path_height']:
                                test = True
                    if fluent_type == 'revolver':
                        for m in obj.modifiers:
                            if m.name == fluent_modifiers_name['screw']:
                                test = True
                    if fluent_type == 'unknow' and get_addon_preferences().bevel_system == 'MULTIPLE' or obj.get('fluent_inset'):
                        test = True
                    if fluent_type == 'grid':
                        for m in obj.modifiers:
                            if m.name == 'ArrayX_from_bool':
                                test = True
                                bpy.ops.fluent.grids('INVOKE_DEFAULT', operation='EDIT')
                                return {'FINISHED'}
                    if fluent_type == 'wire' and obj.type == 'CURVE':
                        for m in obj.modifiers:
                            if m.name == '.f_geometry_nodes':
                                test = True
                                bpy.ops.fluent.wire('INVOKE_DEFAULT', operation='EDIT')
                                return {'FINISHED'}
                    if fluent_type == 'pipe':
                        for m in obj.modifiers:
                            if m.name == '.f_geometry_nodes':
                                test = True
                                bpy.ops.fluent.pipe('INVOKE_DEFAULT', operation='EDIT')
                                return {'FINISHED'}
                    if fluent_type == 'head_screw':
                        for m in obj.modifiers:
                            if m.name == '.f_Head_Screw':
                                test = True
                                bpy.ops.fluent.screw('INVOKE_DEFAULT', operation='EDIT')
                                return {'FINISHED'}
                    if not test:
                        make_oops([translate('editOnFluentObj'), translate('notFluentCreation')], title=translate('howToUse'), icon='ERROR')
                        return{'FINISHED'}
                else:
                    make_oops([translate('editOnFluentObj'), translate('notFluentCreation')], title=translate('howToUse'), icon='ERROR')
                    return {'FINISHED'}
            else:
                make_oops([translate('selectFluentObject')], title=translate('howToUse'), icon='ERROR')
                return {'FINISHED'}

        # test si dans le preview
        if not context.area.type == 'VIEW_3D':
            make_oops([translate('previewNotFound')], title=translate('howToUse'), icon='ERROR')
            return {'FINISHED'}

        self.init_variables(event)

        callback = self.initialisation()

        if self.bool_obj.modifiers.get(fluent_modifiers_name['head_screw']):
            return {'FINISHED'}

        if callback == 'FINISHED':
            return {'FINISHED'}

        args = (self, context)

        # self.timer = context.window_manager.event_timer_add(1/25, window=context.window)
        self._handle = bpy.types.SpaceView3D.draw_handler_add(draw_callback_px, args, 'WINDOW', 'POST_PIXEL')
        self._handle_obj_draw = bpy.types.SpaceView3D.draw_handler_add(self.bool_drawing.draw, (), 'WINDOW', 'POST_VIEW')
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
