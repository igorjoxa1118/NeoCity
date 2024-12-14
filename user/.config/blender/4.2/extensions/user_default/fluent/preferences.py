from os.path import dirname, realpath

import bpy
from bpy.types import Operator, AddonPreferences
from bpy.props import StringProperty
import rna_keymap_ui
from .Tools.independant_helper import get_addon_preferences
from .Tools.translation import translate
from .Tools.helper import load_icons
from .UI.menus import FLUENT_PT_Basic_Panel
try:
    from .power_trip import power_trip_panel
except:pass
from .primitives import primitive_add
import os

class FluentAddonPreferences(AddonPreferences):
    def bevel_compatibility(self, context):
        if get_addon_preferences().bevel_system == 'MULTIPLE' and not get_addon_preferences().auto_beveled_cut:
            get_addon_preferences().auto_beveled_cut = True

    def panel_toggle(self, context):
        if get_addon_preferences().show_panel:
            from bpy.utils import register_class
            register_class(FLUENT_PT_Basic_Panel)
            try:
                register_class(power_trip_panel.classes)
            except:pass
        else:
            from bpy.utils import unregister_class
            unregister_class(FLUENT_PT_Basic_Panel)
            try:
                unregister_class(power_trip_panel.classes)
            except:pass

    def toggle_primitive(self, context):
        if get_addon_preferences().fluent_primitive:
            bpy.types.VIEW3D_MT_mesh_add.prepend(primitive_add)
        else:
            bpy.types.VIEW3D_MT_mesh_add.remove(primitive_add)

    def instant_mesh_path_check(self, context):
        file_path = get_addon_preferences().instant_mesh_file
        if '.app' in file_path and not 'Contents' in file_path:
            norm_path = os.path.normpath('Contents/MacOS/Instant Meshes')
            get_addon_preferences().instant_mesh_file = os.path.join(file_path,norm_path)

    bl_idname = __package__

    menu_type: bpy.props.EnumProperty(
        description='Type of menu',
        name='Menu type',
        items=(('CIRCULAR', 'Circular', 'Circular'),
               ('VERTICAL', 'Vertical', 'Vertical'),
               ),
        default='CIRCULAR'
    )

    font_size: bpy.props.IntProperty(
        description='UI font size',
        name='Font size',
        default=22
    )

    icon_size: bpy.props.EnumProperty(
        description='Size of icons',
        name='Icon size',
        items=(('24', '24', '24'),
                ('32', '32', '32'),
               ('48', '48', '48'),
               ),
        default='32'
    )

    corner_preference: bpy.props.FloatProperty(
        description="Default Bevel Width",
        name="Default Bevel Width",
        default=0,
        min=0,
        max=10,
        step=0.01,
        precision=3
    )

    model_resolution: bpy.props.IntProperty(
        description='Resolution of bevels, cylinders and spheres (segments/m)',
        name='Model resolution',
        default=16,
        min=1,
        max=256
    )
    min_auto_bevel_segments: bpy.props.IntProperty(
        description='Minimum resolution of bevels (segments/m)',
        name='Minimum of segments for auto-bevel',
        default=4,
        min=0,
        max=64
    )
    min_auto_cylinder_segments: bpy.props.IntProperty(
        description='Minimum resolution of cylinders and spheres (segments/m)',
        name='Minimum of segments for auto-resolution',
        default=16,
        min=3,
        max=64
    )

    latest_bevel_width_preference: bpy.props.FloatProperty(
        description="Latest Bevel Width",
        name="Latest Bevel Width",
        default=0.01,
        min=0,
        step=0.001,
        precision=3
    )

    fluent_menu_hold: bpy.props.BoolProperty(
        description="Hold left click to keep menu visible then release hover a button to use it.",
        name="Hold click to display menu (uncheck to use single click)",
        default=False
    )

    fluent_menu_shortcut_key: bpy.props.EnumProperty(
        items=(("A", "A", "A"),
               ("B", "B", "B"),
               ("C", "C", "C"),
               ("D", "D", "D"),
               ("E", "E", "E"),
               ("F", "F", "F"),
               ("G", "G", "G"),
               ("H", "H", "H"),
               ("I", "I", "I"),
               ("J", "J", "J"),
               ("K", "K", "K"),
               ("L", "L", "L"),
               ("M", "M", "M"),
               ("N", "N", "N"),
               ("O", "O", "O"),
               ("P", "P", "P"),
               ("Q", "Q", "Q"),
               ("R", "R", "R"),
               ("S", "S", "S"),
               ("T", "T", "T"),
               ("U", "U", "U"),
               ("V", "V", "V"),
               ("W", "W", "W"),
               ("X", "X", "X"),
               ("Y", "Y", "Y"),
               ("Z", "Z", "Z"),
               ),
        default='F'
    )

    fluent_menu_shortcut_alt: bpy.props.BoolProperty(
        description="Use alt to call Fluent",
        name="Use alt to call Fluent",
        default=False
    )

    fluent_menu_shortcut_ctrl: bpy.props.BoolProperty(
        description="Use ctrl to call Fluent",
        name="Use ctrl to call Fluent",
        default=False
    )

    fluent_menu_shortcut_shift: bpy.props.BoolProperty(
        description="Use shift to call Fluent",
        name="Use shift to call Fluent",
        default=False
    )

    fluent_cut_shortcut_key: bpy.props.EnumProperty(
        items=(("A", "A", "A"),
               ("B", "B", "B"),
               ("C", "C", "C"),
               ("D", "D", "D"),
               ("E", "E", "E"),
               ("F", "F", "F"),
               ("G", "G", "G"),
               ("H", "H", "H"),
               ("I", "I", "I"),
               ("J", "J", "J"),
               ("K", "K", "K"),
               ("L", "L", "L"),
               ("M", "M", "M"),
               ("N", "N", "N"),
               ("O", "O", "O"),
               ("P", "P", "P"),
               ("Q", "Q", "Q"),
               ("R", "R", "R"),
               ("S", "S", "S"),
               ("T", "T", "T"),
               ("U", "U", "U"),
               ("V", "V", "V"),
               ("W", "W", "W"),
               ("X", "X", "X"),
               ("Y", "Y", "Y"),
               ("Z", "Z", "Z"),
               ),
        default='F'
    )

    fluent_cut_shortcut_alt: bpy.props.BoolProperty(
        description="Use alt to call Fluent cut",
        name="fluent_cut_shortcut_alt",
        default=True
    )

    fluent_cut_shortcut_ctrl: bpy.props.BoolProperty(
        description="Use ctrl to call Fluent cut",
        name="fluent_cut_shortcut_ctrl",
        default=False
    )

    fluent_cut_shortcut_shift: bpy.props.BoolProperty(
        description="Use shift to call Fluent cut",
        name="fluent_cut_shortcut_shift",
        default=False
    )

    fluent_slice_shortcut_key: bpy.props.EnumProperty(
        items=(("A", "A", "A"),
               ("B", "B", "B"),
               ("C", "C", "C"),
               ("D", "D", "D"),
               ("E", "E", "E"),
               ("F", "F", "F"),
               ("G", "G", "G"),
               ("H", "H", "H"),
               ("I", "I", "I"),
               ("J", "J", "J"),
               ("K", "K", "K"),
               ("L", "L", "L"),
               ("M", "M", "M"),
               ("N", "N", "N"),
               ("O", "O", "O"),
               ("P", "P", "P"),
               ("Q", "Q", "Q"),
               ("R", "R", "R"),
               ("S", "S", "S"),
               ("T", "T", "T"),
               ("U", "U", "U"),
               ("V", "V", "V"),
               ("W", "W", "W"),
               ("X", "X", "X"),
               ("Y", "Y", "Y"),
               ("Z", "Z", "Z"),
               ),
        default='F'
    )

    fluent_slice_shortcut_alt: bpy.props.BoolProperty(
        description="Use alt to call Fluent slice",
        name="fluent_slice_shortcut_alt",
        default=False
    )

    fluent_slice_shortcut_ctrl: bpy.props.BoolProperty(
        description="Use ctrl to call Fluent slice",
        name="fluent_slice_shortcut_ctrl",
        default=True
    )

    fluent_slice_shortcut_shift: bpy.props.BoolProperty(
        description="Use shift to call Fluent slice",
        name="fluent_slice_shortcut_shift",
        default=False
    )

    fluent_edit_shortcut_key: bpy.props.EnumProperty(
        items=(("A", "A", "A"),
               ("B", "B", "B"),
               ("C", "C", "C"),
               ("D", "D", "D"),
               ("E", "E", "E"),
               ("F", "F", "F"),
               ("G", "G", "G"),
               ("H", "H", "H"),
               ("I", "I", "I"),
               ("J", "J", "J"),
               ("K", "K", "K"),
               ("L", "L", "L"),
               ("M", "M", "M"),
               ("N", "N", "N"),
               ("O", "O", "O"),
               ("P", "P", "P"),
               ("Q", "Q", "Q"),
               ("R", "R", "R"),
               ("S", "S", "S"),
               ("T", "T", "T"),
               ("U", "U", "U"),
               ("V", "V", "V"),
               ("W", "W", "W"),
               ("X", "X", "X"),
               ("Y", "Y", "Y"),
               ("Z", "Z", "Z"),
               ),
        default='F'
    )

    fluent_edit_shortcut_alt: bpy.props.BoolProperty(
        description="Use alt to call Fluent edit",
        name="fluent_edit_shortcut_alt",
        default=False
    )

    fluent_edit_shortcut_ctrl: bpy.props.BoolProperty(
        description="Use ctrl to call Fluent edit",
        name="fluent_edit_shortcut_ctrl",
        default=False
    )

    fluent_edit_shortcut_shift: bpy.props.BoolProperty(
        description="Use shift to call Fluent edit",
        name="fluent_edit_shortcut_shift",
        default=True
    )
    language: bpy.props.EnumProperty(
        items=(
            ("ENGLISH", "English", "ENGLISH"),
            ("CHINESE", "中国人", "CHINESE"),
            ("DEUTSCH", "Deutsch", "DEUTSCH"),
            ("SPANISH", "Español", "SPANISH"),
            ("FRANCAIS", "Français", "FRANCAIS"),
            ("JAPANESE", "日本語", "JAPANESE"),
            ("RUSSIAN", "Русский", "RUSSIAN")
        ),
        default='ENGLISH'
    )


    auto_hide_bool: bpy.props.BoolProperty(
        name="auto_hide_bool",
        default=True,
        description="Hide boolean object after creation"
    )

    auto_parent: bpy.props.BoolProperty(
        name="auto_parent",
        default=True,
        description="Auto parent between the boolean object and his target"
    )

    need_updating: bpy.props.BoolProperty(
        description="need updating",
        name="need_updating",
        default=False
    )

    last_version: bpy.props.StringProperty(
        description="last version",
        name="last_version",
        default="(1.0.6)"
    )

    bg_color: bpy.props.FloatVectorProperty(
        name="Color of background text",
        subtype='COLOR',
        size=4,
        default=(0.21, 0.21, 0.21, 1)
    )

    active_bg_color: bpy.props.FloatVectorProperty(
        name="Color of active background text",
        subtype='COLOR',
        size=4,
        default=(0, 0.6, 1, 1)
    )

    overlay_color: bpy.props.FloatVectorProperty(
        name="Color of menu overlay",
        subtype='COLOR',
        size=4,
        default=[0.1, 0.1, 0.1, 0.5]
    )

    highlight_text: bpy.props.FloatVectorProperty(name="Color of hightlight text",
        subtype='COLOR',
        size=4,
        default=(0.0, 0.6, 1, 1)
    )

    hightlight_dot: bpy.props.FloatVectorProperty(name="Color of hightlight dots",
        subtype='COLOR',
        size=4,
        default=(0, 1, 1, 1)
    )

    clamp_overlap: bpy.props.BoolProperty(
        description="Use the clamp overlap bevel option",
        name="Clamp overlap",
        default=False
    )

    snap_grid_plane_color: bpy.props.FloatVectorProperty(
        name="Color of snap grid plane",
        subtype='COLOR',
        size=4,
        default=(0, .75, 1, .25)
    )

    snap_grid_dots_color: bpy.props.FloatVectorProperty(
        name="Color of snap grid plane",
        subtype='COLOR',
        size=4,
        default=(1, 1, 1, 1)
    )

    auto_beveled_cut: bpy.props.BoolProperty(
        description="Automatically add a bevel on new and cut object",
        name="Automatic bevel addition",
        default=True,
        update=bevel_compatibility
    )

    bevel_system: bpy.props.EnumProperty(
        items=(("SIMPLE", "SIMPLE", "Only one bevel on your model."),
               ("MULTIPLE", "MULTIPLE", "Need more knowledge about the Blender modifiers.")
               ),
        default='SIMPLE',
        update=bevel_compatibility
    )

    instant_mesh_file: bpy.props.StringProperty(
        name="Instant Meshes Executable",
        subtype='FILE_PATH',
        update=instant_mesh_path_check
    )

    show_panel: bpy.props.BoolProperty(
        description="Show the Fluent panel",
        name="Fluent panel",
        default=True,
        update=panel_toggle
    )

    pie_option_pt: bpy.props.BoolProperty(
        description="Show the Power Trip tool in the pie menu",
        name="PT in the pie menu",
        default=True
    )

    pie_option_toolbox: bpy.props.BoolProperty(
        description="Show the toolbox in the pie menu",
        name="Toolbox in the pie menu",
        default=True
    )

    pie_option_other_adjustments: bpy.props.BoolProperty(
        description="Show the other adjustment button in the pie menu",
        name="Other adjustment button in the pie menu",
        default=True
    )

    fluent_primitive: bpy.props.BoolProperty(
        description="Add Fluent primitive in Shift+A menu",
        name="Show Fluent primitive menu",
        default=True,
        update=toggle_primitive
    )

    cloth_resolution: bpy.props.IntProperty(
        description="Number of face",
        name="Cloth resolution",
        default=2000,
        min=0,
        step=10
    )
    cloth_shrink: bpy.props.FloatProperty(
        description="Shrink",
        name="Cloth shrink",
        default=-0.1,
        step=0.01
    )
    cloth_pressure: bpy.props.FloatProperty(
        description="Pressure",
        name="Cloth pressure",
        default=20,
        step=0.1
    )
    cloth_freeze: bpy.props.BoolProperty(
        description="Apply the simulation",
        name="Freeze",
        default=True
    )
    cloth_remesh: bpy.props.BoolProperty(
        description="Remesh the selected faces",
        name="Remesh",
        default=True
    )
    cloth_remesh_after: bpy.props.BoolProperty(
        description="Remesh the simulation",
        name="Remesh after simulation",
        default=False
    )
    cloth_triangulation: bpy.props.BoolProperty(
        description="Use a triangulate mesh",
        name="Triangulate",
        default=False
    )
    cloth_stiffness: bpy.props.FloatProperty(
        description="How much the cloth resist to the pressure",
        name="Stiffness",
        default=5,
        min=0
    )
    cloth_end_frame: bpy.props.IntProperty(
        description="Simulation duration.",
        name="End frame",
        default=30,
        min=0
    )
    cloth_remesh_tool: bpy.props.EnumProperty(
        name='Select the remesh tool',
        items=(("INSTANT_MESH", "Instant Mesh", "Instant Mesh"),
               ("QUADREMESHER", "QuadRemesher", "QuadRemesher")
               ),
        default='INSTANT_MESH'
    )
    cloth_topology: bpy.props.EnumProperty(
        name='Select the type of topology',
        items=(
            ("QUAD", "Quad", "Quad"),
            ("TRIANGULATE", "Triangulate", "Triangulate"),
            ("POKE", "Poke", "Poke"),
            ("GARMENT", "Garment", "Garment")
        ),
        default='QUAD'
    )
    cloth_separate_face: bpy.props.BoolProperty(
        description="One panel by faces",
        name="Separate by faces",
        default=False
    )
    cloth_self_collision: bpy.props.BoolProperty(
        description="Self collision",
        name="Self collision",
        default=False
    )
    cloth_gathering: bpy.props.BoolProperty(
        description="gathering",
        name="gathering",
        default=False
    )
    cloth_pin_loop: bpy.props.IntProperty(
        description="Number of edge loop from boundary edge use as pin group",
        name="Pin loop",
        min=1,
        default=2
    )
    bool_collection: StringProperty(
        description="Name of the boolean object collection",
        name="Boolean collection name",
        default='Bool_Objects'
    )

    def draw(self, context):

        icons = load_icons()
        gumroad_ico = icons.get("gumroad")
        bm_ico = icons.get("bm")
        layout = self.layout
        wm = context.window_manager
        layout = self.layout

        box = layout.box()
        box.label(text=translate('saveAfterChanges'))
        AddonKeymaps.draw_keymap_items(wm, layout)
        box = layout.box()
        box.label(text='--- '+translate('defaultValue')+' ---')
        box.prop(self, "model_resolution", text=translate('modelResolution'))
        box.prop(self, "min_auto_bevel_segments", text=translate('minAutoBevelSegments'))
        box.prop(self, "min_auto_cylinder_segments", text=translate('minAutoCylinderSegments'))
        box.prop(self, "latest_bevel_width_preference", text=translate('latestBevelWidthPreference'))
        box.prop(self, "clamp_overlap", text=translate('clampOverlap'))
        box.prop(self, "bool_collection", text=translate('boolCollection'))

        box = layout.box()
        box.label(text='--- '+translate('display')+' ---')
        box.prop(self, "menu_type", text=translate('menuType'))
        box.prop(self, "fluent_menu_hold", text=translate('fluentMenuHold'))
        box.prop(self, "font_size", text=translate('fontSize'))
        box.prop(self, "icon_size", text=translate('iconSize'))
        box.prop(self, "show_panel", text=translate('showPanel'))
        box.prop(self, "pie_option_pt", text=translate('pieOptionPt'))
        box.prop(self, "pie_option_toolbox", text=translate('pieOptionToolbox'))
        box.prop(self, "pie_option_other_adjustments", text=translate('pieOptionOtherAdjustments'))
        box.prop(self, "fluent_primitive", text=translate('fluentPrimitive'))

        box.prop(self, "language", text=translate('language'))
        box.label(text=translate('translationInProgress'))
        box.prop(self, "highlight_text", text=translate('highlightText'))
        box.prop(self, "hightlight_dot", text=translate('hightlightDot'))
        box.prop(self, "snap_grid_plane_color", text=translate('snapGridPlaneColor'))
        box.prop(self, "snap_grid_dots_color", text=translate('snapGridDotsColor'))

        box = layout.box()
        box.label(text='--- '+translate('behavior')+' ---')
        box.prop(self, "bevel_system", text=translate('bevelSystem'))
        row = box.row()
        row.enabled = self.bevel_system == 'SIMPLE'
        row.prop(self, "auto_beveled_cut", text=translate('autoBeveledCut'))
        box.prop(self, "auto_hide_bool", text=translate('autoHideBool'))
        box.prop(self, "auto_parent", text=translate('autoParent'))
        if os.path.isdir(os.path.join(dirname(realpath(__file__)), 'power_trip')):
            box = box.box()
            box.label(text=translate('remesherTool'))
            box.prop(self, "cloth_remesh_tool", text=translate('selectRemeshTool'))
            if get_addon_preferences().cloth_remesh_tool == 'INSTANT_MESH':
                box.label(text=translate('toUseCloth'))
                box.label(text=translate('setPathExe'))
                row = box.row()
                row.prop(self, "instant_mesh_file", text=translate('instantMeshFile'))
                row.operator("fluent.instantmeshdownload", text=translate('downloadInstantMesh'))
            elif get_addon_preferences().cloth_remesh_tool == 'QUADREMESHER':
                box.label(
                    text=translate('checkQuadRemesher'))


class AddonKeymaps:
    _addon_keymaps = []
    _keymaps = {}

    @classmethod
    def new_keymap(cls, name, kmi_name, kmi_value=None, km_name='3D View',
                   space_type="VIEW_3D", region_type="WINDOW",
                   event_type=None, event_value=None, ctrl=False, shift=False,
                   alt=False, key_modifier="NONE", arg = []):
        """
        Adds a new keymap
        :param name: str, Name that will be displayed in the panel preferences
        :param kmi_name: str
                - bl_idname for the operators (exemple: 'object.cube_add')
                - 'wm.call_menu' for menu
                - 'wm.call_menu_pie' for pie menu
        :param kmi_value: str
                - class name for Menu or Pie Menu
                - None for operators
        :param km_name: str, keymap name (exemple: '3D View Generic')
        :param space_type: str, space type keymap is associated with, see:
                https://docs.blender.org/api/current/bpy.types.KeyMap.html?highlight=space_type#bpy.types.KeyMap.space_type
        :param region_type: str, region type keymap is associated with, see:
                https://docs.blender.org/api/current/bpy.types.KeyMap.html?highlight=region_type#bpy.types.KeyMap.region_type
        :param event_type: str, see:
                https://docs.blender.org/api/current/bpy.types.Event.html?highlight=event#bpy.types.Event.type
        :param event_value: str, type of the event, see:
                https://docs.blender.org/api/current/bpy.types.Event.html?highlight=event#bpy.types.Event.value
        :param ctrl: bool
        :param shift: bool
        :param alt: bool
        :param key_modifier: str, regular key pressed as a modifier
                https://docs.blender.org/api/current/bpy.types.KeyMapItem.html?highlight=modifier#bpy.types.KeyMapItem.key_modifier
        :return:
        """
        cls._keymaps.update({name: [kmi_name, kmi_value, km_name, space_type,
                                    region_type, event_type, event_value,
                                    ctrl, shift, alt, key_modifier, arg]
                             })

    @classmethod
    def add_hotkey(cls, kc, keymap_name):

        items = cls._keymaps.get(keymap_name)
        if not items:
            return

        kmi_name, kmi_value, km_name, space_type, region_type = items[:5]
        event_type, event_value, ctrl, shift, alt, key_modifier, arg = items[5:]
        km = kc.keymaps.new(name=km_name, space_type=space_type,
                            region_type=region_type)

        kmi = km.keymap_items.new(kmi_name, event_type, event_value,
                                  ctrl=ctrl,
                                  shift=shift, alt=alt,
                                  key_modifier=key_modifier
                                  )
        if kmi_value:
            kmi.properties.name = kmi_value

        kmi.active = True

        if arg:
            command = 'kmi.properties.'
            command += arg[0]
            command += '="'+arg[1]+'"'
            exec(command)

        cls._addon_keymaps.append((km, kmi))

    @staticmethod
    def register_keymaps():
        wm = bpy.context.window_manager
        kc = wm.keyconfigs.addon
        # In background mode, there's no such thing has keyconfigs.user,
        # because headless mode doesn't need key combos.
        # So, to avoid error message in background mode, we need to check if
        # keyconfigs is loaded.
        if not kc:
            return

        for keymap_name in AddonKeymaps._keymaps.keys():
            AddonKeymaps.add_hotkey(kc, keymap_name)

    @classmethod
    def unregister_keymaps(cls):
        kmi_values = [item[1] for item in cls._keymaps.values() if item]
        kmi_names = [item[0] for item in cls._keymaps.values() if
                     item not in ['wm.call_menu', 'wm.call_menu_pie']]

        for km, kmi in cls._addon_keymaps:
            # remove addon keymap for menu and pie menu
            if hasattr(kmi.properties, 'name'):
                if kmi_values:
                    if kmi.properties.name in kmi_values:
                        km.keymap_items.remove(kmi)

            # remove addon_keymap for operators
            else:
                if kmi_names:
                    if kmi.idname in kmi_names:
                        km.keymap_items.remove(kmi)

        cls._addon_keymaps.clear()

    @staticmethod
    def get_hotkey_entry_item(name, kc, km, kmi_name, kmi_value, col):

        # for menus and pie_menu
        if kmi_value:
            for km_item in km.keymap_items:
                if km_item.idname == kmi_name and km_item.properties.name == kmi_value:
                    col.context_pointer_set('keymap', km)
                    rna_keymap_ui.draw_kmi([], kc, km, km_item, col, 0)
                    return

            col.label(text=f"No hotkey entry found for {name}")
            col.operator(FLUENT_OT_restore_hotkey.bl_idname,
                         text="Restore keymap",
                         icon='ADD').km_name = km.name

        # for operators
        else:
            if km.keymap_items.get(kmi_name):
                col.context_pointer_set('keymap', km)
                rna_keymap_ui.draw_kmi([], kc, km, km.keymap_items[kmi_name],
                                       col, 0)

            else:
                col.label(text=f"No hotkey entry found for {name}")
                col.operator(FLUENT_OT_restore_hotkey.bl_idname,
                             text="Restore keymap",
                             icon='ADD').km_name = km.name

    @staticmethod
    def draw_keymap_items(wm, layout):
        kc = wm.keyconfigs.user

        box = layout.box()
        for name, items in AddonKeymaps._keymaps.items():
            kmi_name, kmi_value, km_name = items[:3]
            split = box.split()
            col = split.column()
            # col.label(text=name)
            # col.separator()
            km = kc.keymaps[km_name]
            AddonKeymaps.get_hotkey_entry_item(name, kc, km, kmi_name,
                                               kmi_value, col)


class FLUENT_OT_restore_hotkey(Operator):
    bl_idname = "template.restore_hotkey"
    bl_label = "Restore hotkeys"
    bl_options = {'REGISTER', 'INTERNAL'}

    km_name: StringProperty()

    def execute(self, context):
        context.preferences.active_section = 'KEYMAP'
        wm = context.window_manager
        kc = wm.keyconfigs.addon
        km = kc.keymaps.get(self.km_name)
        if km:
            km.restore_to_default()
            context.preferences.is_dirty = True
        context.preferences.active_section = 'ADDONS'
        return {'FINISHED'}