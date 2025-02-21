import bpy

from bpy.types import Panel

from . settings import hardops
from ... utility import tool, addon, screen
from . utility import preset
from .. import toolbar
from .. property.utility import names

common_separators = 5


class BC_PT_helper(Panel):
    bl_label = 'Helper'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    # bl_category = 'BoxCutter'

    _pref_string: str = F'bpy.context.preferences.addons["{addon.name}"].preferences'

    _number_string: dict = {
        1: 'Main',
        2: '2nd',
        3: '3rd',
        4: '4th',
        5: '5th',
        6: '6th',
        7: '7th',
        8: '8th',
        9: '9th'}

    _modifier_icon: dict = {
        'ARRAY': 'MOD_ARRAY',
        'BEVEL': 'MOD_BEVEL',
        'BOOLEAN': 'MOD_BOOLEAN',
        'MIRROR': 'MOD_MIRROR',
        'SCREW': 'MOD_SCREW',
        'SOLIDIFY': 'MOD_SOLIDIFY'}

    _type_dict = { # XXX: copy this explicitly per layout type, box layout should have no key entry checks (i.e. if 'disable' in props:)
        'icon': '', # remove modifier on X
        'remove': False, # remove modifier on X
        'reset': False, # resets the layout via reset operator on X
        'remove_modifier': 'bc.modifier_remove',
        'remove_object_name': '',
        'remove_modifier_name': '',
        'reset_operator': 'bc.set_enum', # operator to call on layout reset
        'reset_operator_data_path': 'bpy.context.scene.bc.start_operation', # full path to property being reset
        'reset_value': 'NONE', # value to set on reset
        'collapse_box': True, # decides if layout should perform collapse structure
        }

    _prop = { # XXX: copy this explicitly per prop, operation layout call should have no key entry checks (prototype)
        'path': F'{_pref_string}.shape', # prop path, if operator then operator prefix i.e: wm.
        'prop': '', # property/operator string name
        'text': '', # ignored if not fed, ignored in headers
        'icon': '', # prop icon value, ignored if not fed
        'icon_only': False, # prop icon value, ignored if not fed
        'header': False, # displays during header collapse state
        'header_expand': False, # displays during header expand state
        'header_only': False, # displays in header always but nowhere else (requires 'header': True)
        'header_preset': False, # uses preset in header in place of prop
        'pad': 0, # adds a separator before the prop _header only_
        'separate': 0, # adds a separator after the prop _header only_
        'small': False, # shrinks the scale_x of prop _header only_
        'scale_x': 1.0, # scale_x of prop _header only_
        'operator': False, # is a operator, i.e. {"path": 'bc', "prop": set_float} for bl_idname 'bc.set_float'
        'expand': False, # expands enum props
        'keep_path': False, # path is not overriden during modifier prop collection
        'ignore': False, # ignore prop on next call
        'reset': '', # operator used for reset
        'reset_value': 0,
        'iter_text': 'XYZ', # iterated on to create text/prop pair for each bool in vector
        'split': '', # split the row with another prop, must exist in props dict
        'preset': [], # feeds presets to prop
        'sub': [], # properties to stick on the same line, must exist in props dict
        }


    @classmethod
    def poll(cls, context):
        active = tool.active()
        return active and active.idname == tool.name


    @staticmethod
    def _expand(name, data=False, default_value=False):
        helper = addon.preference().behavior.helper

        if name not in helper.expand:
            helper.expand.add()
            helper.expand[-1].name = name
            helper.expand[-1].value = default_value

        if data:
            return helper.expand[name]

        return helper.expand[name].value


    def _label_prop(self, layout, op, prop, text='', icon='', factor=0.5, search=False, expand=False, box=False, presets=[], presets_only=False, data_path=''):
        if box:
            layout = layout.box()

        column = layout.column(align=True)

        if not presets_only:
            row = column.row(align=True)

            row.separator()

            split = row.split(align=True, factor=factor)

            if icon:
                split.label(text=text, icon=icon)

            else:
                split.label(text=F'   {text}')

            if search:
                split.prop_search(op, prop, bpy.data, data_path, text='')

            elif expand:
                split.prop(op if not data_path else eval(data_path), prop, expand=True)

            else:
                split.prop(op if not data_path else eval(data_path), prop, text='')

            for _ in range(common_separators):
                row.separator()

        if presets:
            row = column.row(align=True)

            row.separator()

            split = row.split(align=True, factor=factor)

            if presets_only:
                if icon:
                    split.label(text=text, icon=icon)
                else:
                    split.label(text=F'   {text}')
            else:
                split.separator()

            sub = split.row(align=True)

            prop_path = F'{self._pref_string}.{str(type(op)).split(".")[-2]}.{prop}' if not data_path else F'{data_path}.{prop}'

            for preset in presets:
                ot = sub.operator(F'bc.set_{type(preset).__name__}', text=str(preset))
                ot.data_path = prop_path
                ot.value = preset

            for _ in range(common_separators):
                row.separator()


    def _box_layout_handler(self, context, layout, layout_types):
        preference = addon.preference()
        bc = context.scene.bc
        op = toolbar.option()

        props = {}
        for layout_type in layout_types:
            props[layout_type] = self._type_dict.copy()

            if layout_type in {'CIRCLE', 'CIRCLE_M', 'STAR'}:
                props_circle = props[layout_type]
                props_circle['icon'] = 'MESH_CIRCLE' if preference.shape.circle_type != "STAR" else 'SOLO_OFF'

                circle_type = props_circle['circle_type'] = self._prop.copy()
                circle_type['prop'] = 'circle_type'
                circle_type['text'] = 'Type'
                circle_type['header'] = True
                circle_type['small'] = True
                circle_type['separate'] = 1
                circle_type['scale_x'] = 0.45

                if bc.running:
                    circle_diameter = props_circle['circle_diameter'] = self._prop.copy()
                    circle_diameter['prop'] = 'circle_diameter'
                    circle_diameter['text'] = 'Diameter'
                    circle_diameter['header'] = False

                circle_vertices = props_circle['circle_vertices'] = self._prop.copy()
                circle_vertices['prop'] = 'circle_vertices'
                circle_vertices['text'] = 'Vertices'
                circle_vertices['separate'] = 1
                circle_vertices['preset'] = preset.vertice
                circle_vertices['header'] = True
                circle_vertices['header_preset'] = True
                circle_vertices['scale_x'] = 0.25

                if layout_type == 'STAR':
                    circle_star_factor = props_circle['circle_star_factor'] = self._prop.copy()
                    circle_star_factor['prop'] = 'circle_star_factor'
                    circle_star_factor['text'] = 'Factor'

            if layout_type in {'NGON', 'LASSO'}:
                props_ngon = props[layout_type]
                props_ngon['icon'] = 'MOD_SIMPLIFY'

                ngon_cyclic = props_ngon['cyclic'] = self._prop.copy()
                ngon_cyclic['path'] = F'{self._pref_string}.shape'
                ngon_cyclic['prop'] = 'cyclic'
                ngon_cyclic['icon'] = F'RESTRICT_INSTANCED_O{"FF" if preference.shape.cyclic else "N"}'
                ngon_cyclic['header'] = True
                ngon_cyclic['header_only'] = True

                ngon_lasso = props_ngon['lasso'] = self._prop.copy()
                ngon_lasso['prop'] = 'lasso'
                ngon_lasso['text'] = 'Lasso'
                ngon_lasso['separate'] = 1
                ngon_lasso['icon'] = 'GP_SELECT_STROKES'
                ngon_lasso['header'] = True
                ngon_lasso['header_only'] = True

                if not preference.shape.lasso:
                    ngon_angle_lock = props_ngon['angle_lock'] = self._prop.copy()
                    ngon_angle_lock['path'] = F'{self._pref_string}.snap'
                    ngon_angle_lock['prop'] = 'angle_lock'
                    ngon_angle_lock['icon'] = 'DRIVER_ROTATIONAL_DIFFERENCE'
                    ngon_angle_lock['header'] = True
                    ngon_angle_lock['header_only'] = True

                if preference.shape.lasso:
                    ngon_lasso_adaptive = props_ngon['lasso_adaptive'] = self._prop.copy()
                    ngon_lasso_adaptive['prop'] = 'lasso_adaptive'
                    ngon_lasso_adaptive['text'] = 'Adaptive'

                    ngon_lasso_spacing = props_ngon['lasso_spacing'] = self._prop.copy()
                    ngon_lasso_spacing['prop'] = 'lasso_spacing'
                    ngon_lasso_spacing['text'] = 'Spacing'
                    ngon_lasso_spacing['separate'] = 1
                    ngon_lasso_spacing['header'] = True

                else:
                    ngon_angle = props_ngon['ngon_angle'] = self._prop.copy()
                    ngon_angle['path'] = F'{self._pref_string}.snap'
                    ngon_angle['prop'] = 'ngon_angle'
                    ngon_angle['text'] = 'Snap Angle'
                    ngon_angle['pad'] = 2
                    ngon_angle['separate'] = 1
                    ngon_angle['preset'] = preset.angle
                    ngon_angle['header'] = True
                    ngon_angle['header_preset'] = True
                    ngon_angle['scale_x'] = 1.2

                    ngon_previous_edge = props_ngon['ngon_previous_edge'] = self._prop.copy()
                    ngon_previous_edge['path'] = F'{self._pref_string}.snap'
                    ngon_previous_edge['prop'] = 'ngon_previous_edge'
                    ngon_previous_edge['text'] = 'Previous Edge'

            if layout_type == 'COLLECTION':
                props_collection = props['COLLECTION']

                collection = props_collection['collection'] = self._prop.copy()
                collection['path'] = 'bpy.context.scene.bc'
                collection['prop'] = 'collection'
                collection['text'] = 'Cutter'
                collection['sub'] = ['collection_color']

                recall_collection = props_collection['recall_collection'] = self._prop.copy()
                recall_collection['path'] = 'bpy.context.scene.bc'
                recall_collection['prop'] = 'recall_collection'
                recall_collection['text'] = 'Recall'
                recall_collection['pad'] = 9
                recall_collection['header'] = True

                collection_color = props_collection['collection_color'] = self._prop.copy()
                collection_color['path'] = F'{self._pref_string}.color'
                collection_color['prop'] = 'collection'
                collection_color['separate'] = 1
                collection_color['header'] = True
                collection_color['icon_only'] = True

                cycle_all_cutters = props_collection['cycle_all'] = self._prop.copy()
                cycle_all_cutters['prop'] = 'cycle_all'
                cycle_all_cutters['text'] = 'Cycle All Cutters'

                cycle_all_cutters = props_collection['cycle_dimensions'] = self._prop.copy()
                cycle_all_cutters['prop'] = 'cycle_dimensions'
                cycle_all_cutters['text'] = 'Recall Dimensions'

            if layout_type == 'DIMENSIONS':
                props_dimensions = props['DIMENSIONS']

                if op.shape_type == 'CIRCLE':
                    diameter = props_dimensions['circle_diameter'] = self._prop.copy()
                    diameter['prop'] = 'circle_diameter'
                    diameter['text'] = 'Diameter'
                    diameter['header'] = True

                dimension_x = props_dimensions['dimension_x'] = self._prop.copy()
                dimension_x['prop'] = 'dimension_x'
                dimension_x['text'] = 'X'
                dimension_x['header'] = True if op.shape_type != 'CIRCLE' else False

                dimension_y = props_dimensions['dimension_y'] = self._prop.copy()
                dimension_y['prop'] = 'dimension_y'
                dimension_y['text'] = 'Y'
                dimension_y['header'] = True if op.shape_type != 'CIRCLE' else False

                dimension_z = props_dimensions['dimension_z'] = self._prop.copy()
                dimension_z['prop'] = 'dimension_z'
                dimension_z['text'] = 'Z'
                dimension_z['separate'] = 1
                dimension_z['header'] = True

                origin = props_dimensions['origin'] = self._prop.copy()
                origin['path'] = 'bpy.context.scene.bc.operator'
                origin['prop'] = 'origin'
                origin['separate'] = 1
                origin['icon_only'] = True
                origin['expand'] = True
                origin['header'] = True
                origin['header_only'] = True
                origin['header_expand'] = True

            if layout_type == 'BOX_GRID':
                props_box_grid = props['BOX_GRID']
                props_box_grid['icon'] = 'MESH_GRID'
                props_box_grid['reset'] = True
                props_box_grid['reset_operator'] = 'bc.set_bool'
                props_box_grid['reset_operator_data_path'] = F'{self._pref_string}.shape.box_grid'
                props_box_grid['reset_value'] = False

                grid_divisions = props_box_grid['box_grid_divisions'] = self._prop.copy()
                grid_divisions['prop'] = 'box_grid_divisions'
                grid_divisions['text'] = 'Divisions'
                grid_divisions['iter_text'] = 'XY'
                grid_divisions['pad'] = 5
                grid_divisions['separate'] = 1
                grid_divisions['header'] = True

                grid_border = props_box_grid['box_grid_border'] = self._prop.copy()
                grid_border['prop'] = 'box_grid_border'
                grid_border['text'] = 'Border'
                grid_border['split'] = 'box_grid_auto_solidify'

                grid_solidify = props_box_grid['box_grid_auto_solidify'] = self._prop.copy()
                grid_solidify['prop'] = 'box_grid_auto_solidify'
                grid_solidify['text'] = 'Solidify'

                grid_fill_back = props_box_grid['box_grid_fill_back'] = self._prop.copy()
                grid_fill_back['prop'] = 'box_grid_fill_back'
                grid_fill_back['text'] = 'Fill Back'


            elif layout_type == 'WEDGE':
                props_wedge = props['WEDGE']
                props_wedge['icon'] = 'MESH_CONE'
                props_wedge['reset'] = True
                props_wedge['reset_operator'] = 'bc.set_bool'
                props_wedge['reset_operator_data_path'] = F'{self._pref_string}.shape.wedge'
                props_wedge['reset_value'] = False

                wedge_width = props_wedge['wedge_width'] = self._prop.copy()
                wedge_width['prop'] = 'wedge_width'
                wedge_width['text'] = 'Width'
                wedge_width['header'] = True

                wedge_factor = props_wedge['wedge_factor'] = self._prop.copy()
                wedge_factor['prop'] = 'wedge_factor'
                wedge_factor['text'] = 'Factor'
                wedge_factor['pad'] = 1
                wedge_factor['separate'] = 1
                wedge_factor['header'] = True
                wedge_factor['header_preset'] = True
                wedge_factor['preset'] = preset.factor
                wedge_factor['scale_x'] = 0.75

                wedge_width = props_wedge['wedge_lazorcut'] = self._prop.copy()
                wedge_width['prop'] = 'wedge_lazorcut'
                wedge_width['text'] = 'Wedge Lazorcut'
                wedge_width['header'] = True

            elif layout_type == 'TAPER':
                props_taper = props['TAPER']
                props_taper['icon'] = 'FULLSCREEN_EXIT'
                props_taper['reset'] = True
                props_taper['reset_operator'] = 'bc.set_float'
                props_taper['reset_operator_data_path'] = F'{self._pref_string}.shape.taper'
                props_taper['reset_value'] = 1.0

                taper = props_taper['taper'] = self._prop.copy()
                taper['prop'] = 'taper'
                taper['text'] = 'Amount'
                taper['pad'] = 10
                taper['header'] = True
                taper['header_preset'] = True
                taper['preset'] = preset.taper
                # taper['sub'] = ['persistent_taper']

                persistent_taper = props_taper['persistent_taper'] = self._prop.copy()
                persistent_taper['path'] = F'{self._pref_string}.behavior'
                persistent_taper['prop'] = 'persistent_taper'
                persistent_taper['text'] = 'Persistent'
                persistent_taper['separate'] = 2
                persistent_taper['icon'] = F'FAKE_USER_O{"N" if preference.behavior.persistent_taper else "FF"}'
                persistent_taper['icon_only'] = True
                persistent_taper['header'] = True

                keep_lattice_taper = props_taper['keep_lattice_taper'] = self._prop.copy()
                keep_lattice_taper['path'] = F'{self._pref_string}.behavior'
                keep_lattice_taper['prop'] = 'keep_lattice_taper'
                keep_lattice_taper['text'] = 'Keep Lattice'
                keep_lattice_taper['separate'] = 2
                keep_lattice_taper['icon'] = F'OUTLINER_OB_LATTICE' if preference.behavior.keep_lattice_taper else 'MOD_LATTICE'
                keep_lattice_taper['icon_only'] = True
                keep_lattice_taper['header'] = True

            elif layout_type == 'SOLIDIFY':
                props_solidify = props['SOLIDIFY']
                props_solidify['reset'] = True

                thickness = props_solidify['thickness'] = self._prop.copy()
                thickness['prop'] = 'solidify_thickness'
                thickness['text'] = 'Thickness' if not bc.bevel else 'Bevel'
                thickness['header'] = True # 'Thickness' if not bc.bevel else 'Bevel'
                thickness['pad'] = 1
                thickness['separate'] = 1
                thickness['reset'] = 'bc.set_float'
                thickness['reset_value'] = 0.02

                offset = props_solidify['offset'] = self._prop.copy()
                offset['prop'] = 'solidify_offset'
                offset['text'] = 'Offset'

            elif layout_type == 'MIRROR':
                props_mirror = props['MIRROR']
                props_mirror['reset'] = True

                if bc.running:
                    gizmo = props_mirror['gizmo'] = self._prop.copy()
                    gizmo['prop'] = 'mirror_gizmo'
                    gizmo['text'] = 'Gizmo'
                    gizmo['header'] = True
                    gizmo['header_only'] = True
                    gizmo['icon'] = 'EMPTY_AXIS'
                    gizmo['icon_only'] = True

                axis = props_mirror['axis'] = self._prop.copy()
                axis['prop'] = 'mirror_axis'
                axis['text'] = 'Axis'
                axis['header'] = True
                axis['pad'] = 1
                axis['separate'] = 1

                bisect_axis = props_mirror['bisect_axis'] = self._prop.copy()
                bisect_axis['prop'] = 'mirror_bisect_axis'
                bisect_axis['text'] = 'Bisect'

                flip_axis = props_mirror['flip_axis'] = self._prop.copy()
                flip_axis['prop'] = 'mirror_flip_axis'
                flip_axis['text'] = 'Flip'

            elif layout_type == 'ARRAY':
                props_array = props['ARRAY']
                props_array['reset'] = True

                axis = props_array['axis'] = self._prop.copy()
                axis['prop'] = 'array_axis'
                axis['text'] = 'Axis'
                axis['header'] = True
                axis['expand'] = True
                axis['scale_x'] = 0.25

                if bc.shape:
                    if bc.shape.bc.array_circle:
                        del props_array['axis']

                    array_circle = props_array['array_circle'] = self._prop.copy()
                    array_circle['path'] = 'bpy.context.scene.bc.shape.bc'
                    array_circle['prop'] = 'array_circle'
                    array_circle['icon'] = 'ANTIALIASED'
                    array_circle['keep_path'] = True
                    array_circle['header'] = True
                    array_circle['header_only'] = True
                    array_circle['separate'] = 1

                distance = props_array['distance'] = self._prop.copy()
                distance['prop'] = 'array_distance'
                distance['text'] = 'Distance'
                distance['header'] = True
                distance['reset'] = 'bc.set_float'
                distance['reset_value'] = 0.4

                count = props_array['count'] = self._prop.copy()
                count['prop'] = 'array_count'
                count['text'] = 'Count'
                count['header'] = True
                count['separate'] = 1
                count['small'] = True

            elif layout_type == 'BEVEL':
                props_bevel = props['BEVEL']
                props_bevel['reset'] = True

                q_bevel = props_bevel['q_bevel'] = self._prop.copy()
                q_bevel['path'] = 'bpy.context.scene.bc'
                q_bevel['prop'] = 'q_bevel'
                q_bevel['icon'] = 'FILE_TICK'
                q_bevel['keep_path'] = True
                q_bevel['header'] = True if op.shape_type not in {'CUSTOM'} else False
                q_bevel['header_only'] = True

                bevel_front_face = props_bevel['bevel_front_face'] = self._prop.copy()
                bevel_front_face['path'] = 'bpy.context.scene.bc'
                bevel_front_face['text'] = 'Bevel Front Face'
                bevel_front_face['prop'] = 'bevel_front_face'
                bevel_front_face['icon'] = 'EMPTY_SINGLE_ARROW'
                bevel_front_face['keep_path'] = True
                bevel_front_face['header'] = bc.q_bevel if op.shape_type != 'CUSTOM' and not bc.running else False
                bevel_front_face['separate'] = 1
                bevel_front_face['header_only'] = True

                shape_flip_z = props_bevel['shape_flip_z'] = self._prop.copy()
                shape_flip_z['path'] = 'bc'
                shape_flip_z['prop'] = 'shape_flip_z'
                shape_flip_z['icon'] = 'UV_SYNC_SELECT'
                shape_flip_z['operator'] = True
                shape_flip_z['header'] = True
                shape_flip_z['header_only'] = True
                shape_flip_z['separate'] = 1
                shape_flip_z['ignore'] = True

                width = props_bevel['width'] = self._prop.copy()
                width['prop'] = 'bevel_width'
                width['text'] = 'Width'
                width['preset'] = preset.width
                width['header'] = True

                segments = props_bevel['segments'] = self._prop.copy()
                segments['prop'] = 'bevel_segments'
                segments['text'] = 'Segments'
                segments['separate'] = 1
                segments['preset'] = preset.segment
                segments['header'] = True
                segments['small'] = True

                if not bc.running:
                    quad_bevel = props_bevel['quad_bevel'] = self._prop.copy()
                    quad_bevel['prop'] = 'quad_bevel'
                    quad_bevel['text'] = 'Quad Bevel'
                    quad_bevel['header'] = False

                bevel_both = props_bevel['bevel_both'] = self._prop.copy()
                bevel_both['prop'] = 'bevel_both'
                bevel_both['keep_path'] = True
                bevel_both['text'] = 'Bevel Both Ends'
                bevel_both['header'] = False


        modifiers = {layout_type: [mod for mod in bc.shape.modifiers if mod.type == layout_type] if bc.shape else [] for layout_type in layout_types}
        if (op.shape_type == 'CIRCLE' and preference.shape.circle_type != 'STAR' and (preference.shape.circle_type == 'MODIFIER' or preference.shape.circle_vertices > 12)) and 'BEVEL' in modifiers and len(modifiers['BEVEL']) > 1:
            modifiers['BEVEL'] = [mod for mod in modifiers['BEVEL'] if not mod.name.startswith('Bevel')]

        layout_exists = False
        for layout_type in layout_types:
            modifier_count = len(modifiers[layout_type])
            text = layout_type.title().replace('_', ' ')

            if len(text.split(' ')[-1]) == 1:
                text = F'{text[:-2]} ({text[-1]})'

            if not modifier_count or not bc.running:
                if layout_type == 'BOX_GRID' and not preference.shape.box_grid:
                    continue

                if layout_type == 'WEDGE' and not preference.shape.wedge:
                    continue

                if layout_type == 'TAPER' and preference.shape.taper == 1.0:
                    continue

                if layout_type in {'SOLIDIFY', 'MIRROR', 'ARRAY', 'BEVEL'} and bc.start_operation != layout_type and (not bc.running or layout_type != 'SOLIDIFY' or (bc.running and op.mode != 'INSET')):
                    continue

                if layout_type == 'SOLIDIFY' and bc.running and op.mode == 'INSET':
                    props[layout_type]['thickness']['prop'] = 'inset_thickness'

                if layout_type == 'BEVEL':
                    del props_bevel['shape_flip_z']

                icon = self._modifier_icon[layout_type] if layout_type in {'SOLIDIFY', 'MIRROR', 'ARRAY', 'BEVEL'} else props[layout_type]['icon']

                if layout_type == 'SOLIDIFY' and bc.bevel:
                    text = 'Bevel'
                    icon = self._modifier_icon['BEVEL']

                self._box_layout(layout, layout_type, props[layout_type], text=text, icon=icon)
                layout_exists = True

                continue

            if modifier_count == 1:
                mod = modifiers[layout_type][0]

                props[layout_type]['remove'] = True
                props[layout_type]['remove_object_name'] = bc.shape.name
                props[layout_type]['remove_modifier_name'] = mod.name

                if layout_type == 'BEVEL' and op.shape_type == 'CIRCLE' and 'BEVEL' in modifiers:
                    q_bevel['ignore'] = preference.shape.circle_type == 'MODIFIER' or (preference.shape.circle_type == 'POLYGON' and preference.shape.circle_vertices > 12)
                    shape_flip_z['ignore'] = not q_bevel['ignore']
                    if q_bevel['ignore']:
                        width['prop'] = 'quad_bevel_width'

                    use_clamp_overlap = props[mod.type]['use_clamp_overlap'] = self._prop.copy()
                    use_clamp_overlap['path'] = F'bpy.data.objects["{bc.shape.name}"].modifiers["{mod.name}"]'
                    use_clamp_overlap['prop'] = 'use_clamp_overlap'
                    use_clamp_overlap['icon'] = 'LOCKED' if mod.use_clamp_overlap else 'UNLOCKED'
                    use_clamp_overlap['separate'] = 1
                    use_clamp_overlap['header'] = True
                    use_clamp_overlap['header_only'] = True

                    segments = props_bevel['segments'] = self._prop.copy()
                    segments['path'] = F'bpy.data.objects["{bc.shape.name}"].modifiers["{mod.name}"]'
                    segments['prop'] = 'segments'
                    segments['text'] = 'Segments'
                    segments['separate'] = 1
                    segments['preset'] = preset.segment
                    segments['header'] = True
                    segments['small'] = True

                elif layout_type == 'BEVEL':
                    del props_bevel['shape_flip_z']

                self._box_layout(layout, layout_type, props[layout_type], text=text, icon=self._modifier_icon[layout_type], mod=mod)
                layout_exists = True

                continue

            for index, mod in enumerate(modifiers[layout_type]):
                if layout_type == 'BEVEL' and index:
                    q_bevel['ignore'] = True
                    bevel_front_face['ignore'] = True
                    bevel_both['ignore'] = True

                for prop in props[mod.type].keys():
                    if not isinstance(props[mod.type][prop], dict):
                        continue

                    if props[mod.type][prop]['operator'] or props[mod.type][prop]['keep_path']:
                        continue

                    props[mod.type][prop]['path'] = F'bpy.data.objects["{bc.shape.name}"].modifiers["{mod.name}"]'
                    props[mod.type][prop]['prop'] = prop #XXX: may not be a valid prop string, correct next if needed

                props[mod.type]['remove'] = True
                props[mod.type]['remove_object_name'] = bc.shape.name
                props[mod.type]['remove_modifier_name'] = mod.name

                if layout_type == 'BEVEL' and index:
                    use_clamp_overlap = props[mod.type]['use_clamp_overlap'] = self._prop.copy()
                    use_clamp_overlap['path'] = F'bpy.data.objects["{bc.shape.name}"].modifiers["{mod.name}"]'
                    use_clamp_overlap['prop'] = 'use_clamp_overlap'
                    use_clamp_overlap['icon'] = 'LOCKED' if mod.use_clamp_overlap else 'UNLOCKED'
                    use_clamp_overlap['separate'] = 1
                    use_clamp_overlap['header'] = True
                    use_clamp_overlap['header_only'] = True

                    props[mod.type]['segments']['path'] = F'bpy.data.objects["{bc.shape.name}"].modifiers["{mod.name}"]'
                    props[mod.type]['segments']['prop'] = 'segments'

                self._box_layout(layout, layout_type, props[mod.type], text=F'{self._number_string[index+1]} {mod.type.title()}', icon=self._modifier_icon[mod.type], mod=mod)
                layout_exists = True

        return layout_exists


    def _box_layout(self, layout, layout_type, props=_type_dict.copy(), text='', icon='', mod=None, default_expand=False, split_factor=0.433):
        preference = addon.preference()
        bc = bpy.context.scene.bc

        expand_pointer = mod.name.lower() if mod else layout_type.lower()
        expand = self._expand(expand_pointer, default_value=default_expand)

        column = layout.column(align=True)
        box = column.box()

        row = box.row(align=True)

        sub = row.row()
        sub.alignment = 'LEFT'

        if icon:
            sub.prop(self._expand(expand_pointer, data=True), 'value', text=text, icon=icon, toggle=True, emboss=False)
        else:
            sub.prop(self._expand(expand_pointer, data=True), 'value', text=text, toggle=True, emboss=False)

        no_header_props = True
        for p in props.keys():
            prop = props[p]

            if not isinstance(prop, dict):
                continue

            if prop['ignore']:
                if not expand:
                    prop['ignore'] = False

                continue

            if not prop['operator'] and hasattr(eval(prop['path']), prop['prop']):
                prop_type = type(eval(F'{prop["path"]}.{prop["prop"]}')).__name__

            for _ in range(prop['pad']):
                row.separator()

            operator_pointer = F'{prop["path"]}.{prop["prop"]}' # XXX: not always a valid operator prop string, identical _string format_ used for preset data path

            if prop['operator'] and prop['header'] and ((not expand or prop['header_expand']) or (prop['header_only'] and not prop['header_expand'])):
                if prop['icon']:
                    row.operator(operator_pointer, text='', icon=prop['icon'])
                else:
                    row.operator(operator_pointer, text=prop['text'])

            elif prop['header'] and ((not expand or prop['header_expand']) or (prop['header_only'] and not prop['header_expand'])):
                no_header_props = False

                sub = row
                if prop['small'] or prop['scale_x'] != 1.0:
                    sub = sub.row(align=True)
                    sub.scale_x = 0.5 if prop['scale_x'] == 1.0 else prop['scale_x']

                if prop['header_preset']:
                    for preset in prop['preset']:
                        ot = sub.operator(F'bc.set_{type(preset).__name__}', text=str(preset))
                        ot.data_path = F'{prop["path"]}.{prop["prop"]}'
                        ot.value = preset

                elif prop['expand']:
                    sub.prop(eval(prop['path']), prop['prop'], expand=True, icon_only=prop['icon_only'])

                elif prop_type == 'bpy_prop_array':
                    for i, c in enumerate(prop['iter_text']):
                        sub.prop(eval(prop['path']), prop['prop'], toggle=True, text=c, index=i)

                elif prop['icon']:
                    sub.prop(eval(prop['path']), prop['prop'], text='', icon=prop['icon'], icon_only=prop['icon_only'])

                else:
                    sub.prop(eval(prop['path']), prop['prop'], text='', icon_only=prop['icon_only'])
                    if prop['prop'] == 'inset_thickness' and prop['text'] == 'Bevel':
                        for mod in reversed(bc.bevel.modifiers):
                            if mod.type != 'BEVEL':
                                continue

                            ssub = sub.row(align=True)
                            ssub.scale_x = 0.5
                            ssub.prop(mod, 'segments', text='')

                            break

                    if prop['reset']:
                        ot = sub.operator(prop['reset'], text='', icon='TRACKING_CLEAR_BACKWARDS')
                        ot.data_path = F'{prop["path"]}.{prop["prop"]}'
                        ot.value = prop['reset_value']


            for _ in range(prop['separate']):
                row.separator()

        if no_header_props:
            row.separator()
            row.prop(self._expand(expand_pointer, data=True), 'value', text=' ', toggle=True, emboss=False)

        sub = row.row()
        sub.alignment = 'RIGHT'
        sub.emboss = 'NONE'

        sub.prop(self._expand(expand_pointer, data=True), 'value', text='', icon='DOWNARROW_HLT' if expand else 'RIGHTARROW')

        if props['remove']:
            ot = sub.operator('bc.modifier_remove', text='', icon='X')
            ot.object = props['remove_object_name']
            ot.modifier = props['remove_modifier_name']

        elif props['reset']:
            ot = sub.operator(props['reset_operator'], text='', icon='X')
            ot.data_path = props['reset_operator_data_path']
            ot.value = props['reset_value']

        if not expand:
            return

        box = column.box()

        column = box.column(align=True)
        ignore = []
        for p in props.keys():
            prop = props[p]

            if not isinstance(prop, dict):
                continue

            if prop['ignore']:
                prop['ignore'] = False
                continue

            if prop['header_only']:
                continue

            if p in ignore:
                continue

            prop_type = type(eval(F'{prop["path"]}.{prop["prop"]}')).__name__

            row = column.row(align=True)

            split = row.split(align=True, factor=(split_factor * (1.0 if not prop['reset'] else 1.08)) if not prop['split'] else 1.0)
            subsplit = split

            if prop['split']:
                subsplit = split.split(align=True)

            subsplit.label(text=F'  {prop["text"]}')

            split_row = subsplit.row(align=True)

            if prop['split']:
                split_row.alignment = 'RIGHT'

            if prop['expand']:
                split_row.prop(eval(prop['path']), prop['prop'], expand=True, icon_only=prop['icon_only'])

            # elif prop['bool_vector']:
            elif prop_type == 'bpy_prop_array':
                for i, c in enumerate(prop['iter_text']):
                    split_row.prop(eval(prop['path']), prop['prop'], toggle=True, text=c, index=i)

            elif prop['icon']:
                split_row.prop(eval(prop['path']), prop['prop'], text='', icon=prop['icon'], icon_only=prop['icon_only'])

            else:
                split_row.prop(eval(prop['path']), prop['prop'], text='', icon_only=prop['icon_only'])

            if prop['sub']:
                sub = split_row.row(align=True)
                for sp in prop['sub']:
                    ignore.append(sp)

                    if props[sp]['expand']:
                        sub.prop(eval(props[sp]['path']), props[sp]['prop'], expand=True, icon_only=prop['icon_only'])

                    # elif prop['bool_vector']:
                    elif prop_type == 'bpy_prop_array':
                        for i, c in enumerate(props[sp]['iter_text']):
                            sub.prop(eval(props[sp]['path']), props[sp]['prop'], toggle=True, text=c, index=i)

                    elif prop['icon']:
                        sub.prop(eval(props[sp]['path']), props[sp]['prop'], text='', icon=props[sp]['icon'], icon_only=props[sp]['icon_only'])

                    else:
                        sub.prop(eval(props[sp]['path']), props[sp]['prop'], text='', icon_only=props[sp]['icon_only'])

            if prop['reset']:
                ot = row.operator(prop['reset'], text='', icon='TRACKING_CLEAR_BACKWARDS')
                ot.data_path = F'{prop["path"]}.{prop["prop"]}'
                ot.value = prop['reset_value']

            if prop['split']:
                ignore.append(prop['split'])

                prop = props[prop['split']]

                split = row.split(align=True)

                split.label(text=F'  {prop["text"]}')

                split_row = split.row(align=True)
                split_row.alignment = 'RIGHT'

                if prop['expand']:
                    split_row.prop(eval(prop['path']), prop['prop'], expand=True, icon_only=prop['icon_only'])

                # elif prop['bool_vector']:
                elif prop_type == 'bpy_prop_array':
                    for i, c in enumerate(prop['iter_text']):
                        split_row.prop(eval(prop['path']), prop['prop'], toggle=True, text=c, index=i)

                elif prop['icon']:
                    split_row.prop(eval(prop['path']), prop['prop'], text='', icon=prop['icon'], icon_only=prop['icon_only'])

                else:
                    split_row.prop(eval(prop['path']), prop['prop'], text='', icon_only=prop['icon_only'])

                if prop['sub']:
                    sub = split_row.row(align=True)
                    for sp in prop['sub']:
                        ignore.append(sp)

                        if props[sp]['expand']:
                            sub.prop(eval(props[sp]['path']), props[sp]['prop'], expand=True, icon_only=prop['icon_only'])

                        # elif prop['bool_vector']:
                        elif prop_type == 'bpy_prop_array':
                            for i, c in enumerate(props[sp]['iter_text']):
                                sub.prop(eval(props[sp]['path']), props[sp]['prop'], toggle=True, text=c, index=i)

                        elif prop['icon']:
                            sub.prop(eval(props[sp]['path']), props[sp]['prop'], text='', icon=props[sp]['icon'], icon_only=props[sp]['icon_only'])

                        else:
                            sub.prop(eval(props[sp]['path']), props[sp]['prop'], text='', icon_only=props[sp]['icon_only'])


            if not prop['preset']:
                column.separator()

                continue

            row = column.row(align=True)

            split = row.split(align=True, factor=split_factor)
            split.separator()

            sub = split.row(align=True)

            for preset in prop['preset']:
                ot = sub.operator(F'bc.set_{type(preset).__name__}', text=str(preset))
                ot.data_path = F'{prop["path"]}.{prop["prop"]}'
                ot.value = preset

            column.separator()


    def _draw(self, context):
        preference = addon.preference()
        op = toolbar.option()
        bc = context.scene.bc

        self.layout.ui_units_x = 20

        layout = self.layout.column(align=True)

        row = layout.row()
        row.scale_y = 0.9
        row.label(text='Box Helper')

        layout.separator()

        split = layout.split(factor=0.09)

        button_column = split.column(align=True)

        button_column.scale_y = 1.5

        if not bc.running:
            button_column.prop(preference.behavior.helper, 'shape_type', expand=True, text='')

            button_column.separator()

            button_column.prop(preference.snap, 'enable', text='', icon=F'SNAP_O{"N" if preference.snap.enable else "FF"}')

            button_column.separator()

        if op.shape_type == 'BOX':
            button_column.prop(preference.shape, 'box_grid', text='', icon='MESH_GRID')

        button_column.prop(preference.shape, 'wedge', text='', icon='MESH_CONE')
        button_column.prop(preference.shape, 'taper_display', text='', icon='FULLSCREEN_EXIT')
        button_column.separator()

        button_column.prop(bc, 'start_operation', expand=True, text='')


        layout = split.column()

        row = layout.row(align=True)

        box = row.box()
        box.label(text=F' {op.mode.title()}')

        box = row.box()
        box.scale_x = 1.1
        shape_type = op.shape_type

        if shape_type == 'BOX' and preference.shape.box_grid:
            shape_type = 'Grid'

        prefix = 'Wedge' if preference.shape.wedge else 'Line'
        if shape_type != 'NGON' and preference.behavior.draw_line or shape_type == 'NGON' and not preference.shape.cyclic and not preference.shape.lasso:
            if shape_type == 'NGON' and prefix == 'Line':
                box.label(text=F' Ngon (Line)')

            elif prefix != 'Wedge':
                box.label(text=F' {prefix} {shape_type.title()}')

            else:
                box.label(text=F' Wedge {shape_type.title()}')

        elif shape_type == 'NGON' and preference.shape.lasso:
            box.label(text=F'{prefix if preference.shape.wedge else ""} Lasso{" (Line)" if not preference.shape.cyclic else ""}')

        elif shape_type == 'CIRCLE':
            circle_title = F'{shape_type.title() if preference.shape.circle_type != "STAR" else "Star"} ({preference.shape.circle_type[0]}) ({preference.shape.circle_vertices})'
            box.label(text=F'{prefix if preference.shape.wedge else ""} {circle_title}')

        else:
            box.label(text=F'{prefix if preference.shape.wedge else ""} {shape_type.title()}')

        sub = row.row(align=True)
        sub.scale_y = 1.5
        sub.popover(panel='BC_PT_surface', text=preference.surface.title())

        row.separator()

        sub = row.row(align=True)
        sub.alignment = 'RIGHT'
        sub.scale_x = 1.2
        sub.scale_y = 1.5
        sub.prop(op, 'live', text='', icon='PLAY' if not op.live else 'PAUSE')
        sub.popover(panel='BC_PT_settings', text='', icon='PREFERENCES')

        layout.separator()

        column = layout.column(align=True)
        row = column.row(align=True)
        row.scale_x = 2
        row.scale_y = 1.5
        row.prop(op, 'mode', text='', expand=True)

        if op.mode in {'SLICE', 'EXTRACT', 'INSET', 'JOIN', 'MAKE'} or (addon.hops() and op.mode == 'KNIFE'):
            box = column.box()

        if op.mode == 'SLICE':
            self._label_prop(box, preference.behavior, 'recut', text='Recut') # , box=True)
            self._label_prop(box, preference.behavior, 'apply_slices', text='Apply Slice')

        if op.mode == 'INSET':
            sbox = box.column()
            sbox.enabled = not preference.behavior.inset_bevel
            self._label_prop(sbox, preference.behavior, 'recut', text='Recut')
            sbox.separator()
            self._label_prop(sbox, preference.behavior, 'inset_slice', text='Slice') # , box=True)
            self._label_prop(box, preference.behavior, 'inset_bevel', text='Bevel')

        elif op.mode  == 'JOIN':
            self._label_prop(box, preference.behavior, 'join_flip_z', text='Flip Z') # , box=True)
            self._label_prop(box, preference.behavior, 'join_exact', text='Exact') # , box=True)

        elif op.mode == 'KNIFE':
            if addon.hops():
                self._label_prop(box, preference.behavior, 'hops_mark', text='HOps Mark') # , box=True)
            self._label_prop(box, preference.behavior, 'cut_through', text='Cut Through') # , box=True)

        elif op.mode  == 'EXTRACT':
            self._label_prop(box, preference.behavior, 'surface_extract', text='Surface Extract') # , box=True)

        elif op.mode  == 'MAKE':
            self._label_prop(box, preference.behavior, 'hide_make_shapes', text='Hide Gray Shape') # , box=True)

        layout.separator()

        row = layout.row(align=True)
        row.scale_x = 2
        row.scale_y = 1.5

        sub = row.row(align=True)

        if not bc.running:
            sub.enabled = op.shape_type != 'NGON'
            sub.prop(op, 'origin', expand=True, text='')

        else:
            ot = sub.operator('bc.shape_change', text='', icon='TRIA_LEFT')
            ot.index = -1

            ot = sub.operator('bc.shape_change', text='', icon='TRIA_RIGHT')
            ot.index = 1

            sub.operator('bc.shape_rotate_inside', text='', icon='CON_ROTLIMIT')

            sub.operator('bc.shape_rotate_shape', text='', icon='FILE_REFRESH')

            sub.operator('bc.shape_flip_z', text='', icon='UV_SYNC_SELECT')

        row.separator()

        if not bc.running and op.shape_type != 'NGON':
            row.separator()
            if op.shape_type == 'CUSTOM':
                row.prop(preference.shape, 'auto_proportions', text='', icon='CON_SIZELIKE')
            row.prop(preference.behavior, 'draw_line', text='', icon='DRIVER_DISTANCE')

        elif not bc.running:
            row.separator()
            row.prop(preference.shape, 'cyclic', text='', icon=F'RESTRICT_INSTANCED_O{"FF" if preference.shape.cyclic else "N"}')
            row.prop(preference.shape, 'lasso', text='', icon=F'GP_SELECT_STROKES')

        row.separator()

        sub = row.row()
        sub.alignment = 'RIGHT'
        sub.prop(preference.behavior, 'set_origin', text='', expand=True, icon_only=True)

        layout.separator()

        if not bc.running and preference.snap.enable:
            snap = True in [preference.snap.grid, preference.snap.verts, preference.snap.edges, preference.snap.faces]
            snap_grid = preference.snap.grid

            row = layout.row(align=True)
            row.scale_x = 1.5
            row.scale_y = 1.5

            sub = row.row(align=True)
            sub.active = preference.snap.enable
            sub.alert = bool(preference.snap.grid and preference.snap.increment_lock and bc.snap.operator and (bc.snap.operator.handler.grid.display if hasattr(bc.snap.operator, 'handler') else bc.snap.operator.snap.grid_active))
            sub.prop(preference.snap, 'grid', text='', icon='SNAP_GRID')

            if not preference.snap.grid:
                row.prop(preference.snap, 'verts', text='', icon='VERTEXSEL')
                row.prop(preference.snap, 'edges', text='', icon='EDGESEL')
                row.prop(preference.snap, 'faces', text='', icon='FACESEL')
            else:
                sub = row.row(align=True)
                sub.scale_x = 1.33
                sub.prop(preference.snap, 'increment', text='')

            row.popover('BC_PT_snap', text='', icon='SNAP_INCREMENT')

            snap = [preference.snap.verts, preference.snap.edges, preference.snap.faces]
            snap_sub_labels = ['Verts', 'Edges', 'Faces']
            snap_type = "" if snap.count(True) > 1 or True not in snap else snap_sub_labels[snap.index(True)]

            box = row.box()
            box.scale_y = 0.7

            if not preference.snap.enable:
                box.label(text=' Disabled')

            elif preference.snap.grid:
                box.label(text=F' {"Static " if preference.snap.static_grid else ""}Grid {snap_type}')

            elif True in snap:
                box.label(text=F' {"Static " if preference.snap.static_dot else ""}Dot{" " + snap_type[:-1] if snap_type and not preference.snap.static_dot else ""}s')

            elif preference.snap.incremental:
                box.label(text=F' Increment')

            else:
                box.label(text=F' None')

            row.prop(preference.snap, 'increment_lock', text='', icon=F'{"" if preference.snap.increment_lock else "UN"}LOCKED')

        if op.shape_type == 'CUSTOM':
            box = layout.box()
            row = box.row(align=True)
            split = row.split(align=True, factor=0.46)
            split.label(text='Shape', icon='FILE_NEW')

            sub = split.row(align=True)
            sub.prop(bc, 'shape', text='')
            ot = sub.operator('bc.custom', text='', icon='ADD')
            ot.set = True

            sub.separator()
            sub.separator()
            sub.separator()
            sub.separator()
            sub.separator()

            layout.separator()

        elif op.shape_type == 'CIRCLE':
            layout_types = (
                F'CIRCLE{"_M" if preference.shape.circle_type == "MODIFIER" else ""}' if preference.shape.circle_type != 'STAR' else 'STAR',
                )

            layout_exists = self._box_layout_handler(context, layout, layout_types)

            if layout_exists:
                layout.separator()

        elif op.shape_type == 'NGON':
            layout_types = (
                'NGON' if not preference.shape.lasso else 'LASSO',
                )

            layout_exists = self._box_layout_handler(context, layout, layout_types)

            if layout_exists:
                layout.separator()

        if not bc.running:
            layout_types = (
                'COLLECTION',
                )

            self._box_layout_handler(context, layout, layout_types)

        if bc.running:
            layout_types = (
                'DIMENSIONS',
                )

            self._box_layout_handler(context, layout, layout_types)

        self._label_prop(layout, preference.snap, 'rotate_angle', text='Rotation', box=True, presets=preset.angle, presets_only=True)

        self._label_prop(layout, preference.behavior, 'boolean_solver', text='Solver', box=True)

        if not bc.running:
            box = layout.box()
            row = box.row(align=True)

            row.separator()

            split = row.split(align=True)
            split.label(text='   AutoDepth' if preference.shape.auto_depth else '   Lazorcut')
            sub = split.row(align=True)

            if not preference.shape.auto_depth:
                sub.prop(preference.shape, 'lazorcut_depth', text='')

            else:
                sub.prop(preference.shape, 'auto_depth_large', text='', icon='FULLSCREEN_ENTER' if preference.shape.auto_depth_large else 'FULLSCREEN_EXIT')
                sub.prop(preference.shape, 'auto_depth_custom_proportions', text='', icon='FILE_NEW')
                sub.prop(preference.shape, 'auto_depth_multiplier', text='')

            sub.prop(preference.shape, 'auto_depth', text='', icon='CON_SAMEVOL')

            for _ in range(common_separators):
                row.separator()

            hops = getattr(context.window_manager, 'Hard_Ops_material_options', False)

            if hops:
                self._label_prop(layout, hops, 'active_material', text='Material', search=True, box=True, data_path='materials')

        layout.separator()

        layout_types = (
            'BOX_GRID',
            'WEDGE',
            'TAPER',
            )

        layout_exists = self._box_layout_handler(context, layout, layout_types)

        if layout_exists:
            layout.separator()

        layout_types = (
            'SOLIDIFY',
            'MIRROR',
            'ARRAY',
            'BEVEL',
            )

        self._box_layout_handler(context, layout, layout_types)


    def _simple_draw(self, context):
        wm = context.window_manager
        preference = addon.preference()
        bc = context.scene.bc
        op = toolbar.option()

        layout = self.layout

        # op = None
        # for tool in context.workspace.tools:
        #     if tool.idname == tool.name and tool.mode == tool.active().mode:
        #         op = tool.operator_properties('bc.shape_draw')

        #         break

        # if not op:
            # return

        row = layout.row(align=True)
        row.scale_x = 2
        row.scale_y = 1.5
        row.prop(op, 'mode', text='', expand=True)

        if not bc.running:
            layout.separator()

            row = layout.row()
            row.scale_x = 2
            row.scale_y = 1.25

            sub = row.row()
            sub.enabled = not bc.running
            sub.prop(op, 'shape_type', expand=True, text='')

            sub = row.row()
            sub.enabled = op.shape_type != 'NGON'
            sub.prop(op, 'origin', expand=True, text='')

            layout.separator()

            snap = layout.row(align=True)
            snap.scale_x = 1.5
            snap.scale_y = 1.5
            row = snap.row(align=True)
            row.prop(preference.snap, 'enable', text='', icon='SNAP_OFF' if not preference.snap.enable else 'SNAP_ON')

            sub = row.row(align=True)
            sub.active = preference.snap.enable
            sub.prop(preference.snap, 'incremental', text='', icon='SNAP_INCREMENT')

            # if preference.snap.enable:
            if preference.snap.incremental or preference.snap.grid:
                sub.prop(preference.snap, 'increment', text='')
                sub.prop(preference.snap, 'increment_lock', text='', icon=F'{"" if preference.snap.increment_lock else "UN"}LOCKED')
                sub = row.row(align=True)
                sub.scale_x = 1.2
                sub.popover('BC_PT_grid', text='', icon='SNAP_GRID')

                row = layout.row(align=True)
                row.alignment = 'RIGHT'
                row.scale_x = 1.22
                row.scale_y = 1.5
                row.active = preference.snap.enable

                if op.shape_type == 'NGON':
                    row.prop(preference.snap, 'angle_lock', text='', icon='DRIVER_ROTATIONAL_DIFFERENCE')

                row.prop(preference.snap, 'grid', text='', icon='SNAP_GRID')
                row.prop(preference.snap, 'verts', text='', icon='VERTEXSEL')
                row.prop(preference.snap, 'edges', text='', icon='EDGESEL')
                row.prop(preference.snap, 'faces', text='', icon='FACESEL')

            else:
                for _ in range(6):
                    sub.separator()

                if op.shape_type == 'NGON':
                    sub.prop(preference.snap, 'angle_lock', text='', icon='DRIVER_ROTATIONAL_DIFFERENCE')

                sub.prop(preference.snap, 'grid', text='', icon='SNAP_GRID')
                sub.prop(preference.snap, 'verts', text='', icon='VERTEXSEL')
                sub.prop(preference.snap, 'edges', text='', icon='EDGESEL')
                sub.prop(preference.snap, 'faces', text='', icon='FACESEL')

            if preference.snap.enable:
                row = layout.row(align=True)
                row.scale_x = 1.22
                row.scale_y = 1.5

                row.label(text='Snap Type')
                row.prop(preference.snap, 'static_grid', text='', icon='MESH_GRID')
                dot_icon = 'LIGHTPROBE_GRID' if bpy.app.version < (4, 1) else 'LIGHTPROBE_VOLUME'
                row.prop(preference.snap, 'static_dot', text='', icon=dot_icon)

                layout.separator()

        if op.mode == 'INSET':
            layout.row().label(text='\u2022 Inset')
            self.label_row(layout.row(align=True), preference.shape, 'inset_thickness', label='Thickness')
            self.label_row(layout.row(align=True), preference.behavior, 'inset_slice')

        elif op.mode == 'SLICE':
            layout.row().label(text=F'\u2022 Slice')
            self.label_row(layout.row(align=True), preference.behavior, 'recut')

        elif op.mode == 'KNIFE' and addon.hops():
            layout.row().label(text=F'\u2022 Knife')
            self.label_row(layout.row(align=True), preference.behavior, 'hops_mark')

        # if op.shape_type == 'BOX' and not bc.shape:
        #     # layout.row().label(text='\u2022 Line Box')
        #     layout.row().label(text='\u2022 Box')
        #     self.label_row(layout.row(align=True), preference.behavior, 'draw_line', label='Line Box')
        #     if preference.behavior.draw_line:
        #         self.label_row(layout.row(align=True), preference.snap, 'draw_line_angle', label='Line Angle')
        #     self.label_row(layout.row(align=True), preference.shape, 'wedge')

        if op.shape_type == 'CUSTOM':
            if not bc.collection:
                self.label_row(layout.row(align=True), bc, 'shape', label='Shape')

            else:
                row = layout.row(align=True)
                split = row.split(factor=0.5)
                split.label(text='Shape')
                split.prop_search(bc, 'shape', bc.collection, 'objects', text='')

        if op.shape_type != 'NGON':
            self.label_row(layout.row(align=True), preference.behavior, 'draw_line', label='Draw Line')
        if preference.behavior.draw_line:
            self.label_row(layout.row(align=True), preference.snap, 'draw_line_angle', label='Line Angle')

        if op.shape_type != 'NGON':
            self.label_row(layout.row(align=True), preference.shape, 'wedge', label='Wedge')
            if preference.shape.wedge:
                self.label_row(layout.row(align=True), preference.shape, 'wedge_factor', label='Factor')
                self.label_row(layout.row(align=True), preference.shape, 'wedge_width', label='Width')
        # if preference.shape.wedge:
        #     self.label_row(layout.row(align=True), preference.shape, 'wedge_side', label='Wedge Side')

        if op.shape_type == 'NGON':
            self.label_row(layout.row(align=True), preference.shape, 'cyclic', label='Cyclic (closed)' if preference.shape.cyclic else 'Cyclic (open)')
            self.label_row(layout.row(align=True), preference.shape, 'lasso', label='Lasso')
            self.label_row(layout.row(align=True), preference.snap, 'ngon_angle', label='Ngon Angle')
            self.label_row(layout.row(align=True), preference.snap, 'ngon_previous_edge')
            self.label_row(layout.row(align=True), preference.shape, 'wedge', label='Wedge')
            if preference.shape.wedge:
                self.label_row(layout.row(align=True), preference.shape, 'wedge_factor', label='Factor')
                self.label_row(layout.row(align=True), preference.shape, 'wedge_width', label='Width')

            if preference.shape.lasso:
                self.label_row(layout.row(align=True), preference.shape, 'lasso_spacing', label='Spacing')
                self.label_row(layout.row(align=True), preference.shape, 'lasso_adaptive', label='Adaptive')

        elif op.shape_type == 'CIRCLE':
            #layout.row().label(text='\u2022 Circle')
            self.label_row(layout.row(align=True), preference.shape, 'circle_vertices', label='Vertices')

        #layout.row().label(text='\u2022 Rotation')
        self.label_row(layout.row(align=True), preference.snap, 'rotate_angle', label='Snap Angle')

        # if op.shape_type != 'NGON' and not (op.shape_type == 'BOX' and preference.behavior.draw_line):
        #layout.row().label(text='\u2022 Taper')
        self.label_row(layout.row(align=True), preference.shape, 'taper', label='Taper')
        self.label_row(layout.row(align=True), preference.behavior, 'persistent_taper', label='Persistent')

        if op.shape_type == 'BOX':
            self.label_row(layout.row(align=True), preference.shape, 'box_grid', label='Grid')

            if preference.shape.box_grid:
                self.label_row(layout.row(align=True), preference.shape, 'box_grid_border', label='Border')
                self.label_row(layout.row(align=True), preference.shape, 'box_grid_auto_solidify', label='Auto Solidify')
                self.label_row(layout.row(align=True), preference.shape, 'box_grid_divisions', label='Divisions')

        if bc.shape:

            if bc.shape.bc.array:
                layout.row().label(text='\u2022 Array')
                self.label_row(layout.row(align=True), preference.shape, 'array_count', label='Count')

            if bc.shape.bc.solidify and op.mode != 'INSET':
                layout.row().label(text='\u2022 Solidify')
                self.label_row(layout.row(align=True), preference.shape, 'solidify_thickness', label='Thickness')

            if bc.shape.bc.bevel:
                layout.row().label(text='\u2022 Bevel')
                self.label_row(layout.row(align=True), preference.shape, 'bevel_width', label='Width')
                self.label_row(layout.row(align=True), preference.shape, 'bevel_segments', label='Segments')

                if op.shape_type == 'BOX' or (op.shape_type == 'CIRCLE' and preference.shape.circle_type != 'MODIFIER'):
                    self.label_row(layout.row(align=True), bc, 'bevel_front_face')
            if bc.running:
                layout.row().label(text='\u2022 Dimensions')

                if op.shape_type == 'CIRCLE':
                    self.label_row(layout.row(align=True), preference.shape, 'circle_diameter', label='Diameter')

                self.label_row(layout.row(align=True), preference.shape, 'dimension_x', label='X')
                self.label_row(layout.row(align=True), preference.shape, 'dimension_y', label='Y')
                self.label_row(layout.row(align=True), preference.shape, 'dimension_z', label='Z')

        elif bc.start_operation == 'ARRAY':
            layout.row().label(text='\u2022 Array')
            self.label_row(layout.row(align=True), preference.shape, 'array_count', label='Count')

        elif bc.start_operation == 'SOLIDIFY':
            layout.row().label(text='\u2022 Solidify')
            self.label_row(layout.row(align=True), preference.shape, 'solidify_thickness', label='Thickness')

        elif bc.start_operation == 'BEVEL':
            self.label_row(layout.row(align=True), preference.shape, 'bevel_width', label='Width')
            self.label_row(layout.row(align=True), preference.shape, 'bevel_segments', label='Segments')

        if op.mode == 'JOIN' and op.shape_type == 'CUSTOM':
            self.label_row(layout.row(align=True), preference.behavior, 'join_flip_z', label='Flip Z')

        self.layout.separator()

        self.header_row(layout.row(align=True), 'collection', label='Collection')

        if preference.expand.collection:
            self.label_row(layout.row(align=True), bc, 'collection', label='Collection')
            self.label_row(layout.row(align=True), bc, 'recall_collection', label='Recall Col.')

        hops = hasattr(wm, 'Hard_Ops_material_options')
        if hops:
            # self.layout.separator()
            # self.header_row(layout.row(align=True), 'hops', label='HardOps')
            # if preference.expand.hops:
            hardops.BC_PT_hardops_settings.draw(self, context)


    def draw(self, context):
        if addon.preference().display.simple_helper:
            self._simple_draw(context)

            return

        self._draw(context)


    def header_row(self, row, prop, label='', emboss=False):
        preference = addon.preference()
        icon = 'DISCLOSURE_TRI_RIGHT' if not getattr(preference.expand, prop) else 'DISCLOSURE_TRI_DOWN'
        row.alignment = 'LEFT'
        row.prop(preference.expand, prop, text='', emboss=emboss)

        sub = row.row(align=True)
        sub.scale_x = 0.25
        sub.prop(preference.expand, prop, text='', icon=icon, emboss=emboss)
        row.prop(preference.expand, prop, text=F'{label}', emboss=emboss)

        sub = row.row(align=True)
        sub.scale_x = 0.75
        sub.prop(preference.expand, prop, text=' ', icon='BLANK1', emboss=emboss)


    def label_row(self, row, path, prop, label=''):
        if prop in {'draw_line_angle', 'circle_vertices', 'ngon_angle', 'rotate_angle', 'array_count', 'bevel_width', 'bevel_segments', 'recut', 'taper', 'inset_slice', 'wedge_factor'}:
            column = self.layout.column(align=True)
            row = column.row(align=True)

        if prop == 'taper':
            row.label(text='Taper Amount')

        else:
            row.label(text=label if label else names[prop])

        if prop == 'box_grid_divisions':
            row.prop(path, prop, text='X', index=0)
            sub_row = self.layout.row(align=True)
            sub_row.label(text="")
            sub_row.prop(path, prop, text='Y', index=1)

        else:
            row.prop(path, prop, text='')

        values = {
            'Line Angle': preset.line_angle,
            'Rotate Angle': preset.angle,
            'Vertices': preset.vertice,
            'Count': preset.array,
            'Width': preset.width,
            'Segments': preset.segment,
            'Snap Angle': preset.angle,
            'Ngon Angle': preset.angle,
            'Taper': preset.taper,
            'Factor': preset.factor}

        if prop in {'draw_line_angle', 'circle_vertices', 'ngon_angle', 'rotate_angle', 'array_count', 'bevel_width', 'bevel_segments', 'taper', 'wedge_factor'}:
            row = column.row(align=True)
            split = row.split(factor=0.48, align=True)
            sub = split.row(align=True)
            sub = split.row(align=True)

            pointer = '.snap.' if prop in {'draw_line_angle', 'ngon_angle', 'rotate_angle'} else '.shape.'
            for value in values[label]:
                ot = sub.operator(F'wm.context_set_{"int" if prop not in {"bevel_width", "taper", "wedge_factor"} else "float"}', text=str(value))
                ot.data_path = F'preferences.addons["{__name__.partition(".")[0]}"].preferences{pointer}{prop}'
                ot.value = value

            column.separator()
