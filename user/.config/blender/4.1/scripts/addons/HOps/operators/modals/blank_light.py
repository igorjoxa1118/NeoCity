import bpy, math, random, os, json
from datetime import datetime
from pathlib import Path
from math import cos, sin, pi, radians, degrees
from mathutils import Matrix, Vector
from ... ui_framework.master import Master
from ... ui_framework import form_ui as form
from ... utility import addon
from ... utility.base_modal_controls import Base_Modal_Controls

# Input system
from ...utility.screen import dpi_factor
from ... ui_framework.graphics.draw import render_quad, render_text, draw_border_lines
from ... ui_framework.utils.geo import get_blf_text_dims

# Cursor Warp imports
from ... utils.toggle_view3d_panels import collapse_3D_view_panels
from ... utils.modal_frame_drawing import draw_modal_frame
from ... utils.cursor_warp import mouse_warp
from ... utility import method_handler

# Save system
invalid = {'\\', '/', ':', '*', '?', '"', '<', '>', '|', '.'}
completed = {'LEFTMOUSE', 'RET', 'NUMPAD_ENTER'}
cancel = {'RIGHTMOUSE', 'ESC'}


class FLight:
    def __init__(self, light):
        self.light = light
        self.name = light.name
        self.increment_amount = .25
        if light.data.type in {'POINT', 'AREA'}:
            self.increment_amount = 100

    @property
    def energy(self):
        if not self.light: return 1
        return round(self.light.data.energy, 1)

    @energy.setter
    def energy(self, val):
        if not self.light: return
        self.light.data.energy = val
    

    def toggle_vis(self):
        self.light.hide_viewport = not self.light.hide_viewport
    

    def vis_hook(self):
        return bool(self.light.hide_viewport)


description = """Blank Light
Creates a randomized light rig
    
LMB   - Blank Light Rig Scroll
Shift - Expanded Dot UI (Tab) 
Ctrl  - Non Destructive Scroll
(keeps previous light placements and count)

Press H for help
"""

class HOPS_OT_Blank_Light(bpy.types.Operator):

    """Blank Light Rig"""
    bl_idname = "hops.blank_light"
    bl_label = "Blank Light"
    bl_options = {"REGISTER", "UNDO", "BLOCKING"}
    bl_description = description


    def invoke(self, context, event):

        # Props
        self.form_exit = False
        self.empty = None
        self.lights = []
        self.active_light = None
        self.non_destructive = True if event.ctrl else False        
        self.mouse_active = True
        self.available_light_types = {'AREA', 'SUN'}
        self.exit_to_viewport_adjust = False
        self.ran_world_setup = False

        # Fog
        if bpy.app.version[0] < 4:
            self.initial_world_setup(context)
            self.set_fog_off = self.is_fog_on()
            self.__fog_z = 0
            self.set_initial_fog_z()
            self.__fog_opacity = 0
            self.set_initial_fog_opacity()
        
        # JSON Props
        self.json_data = None                           # Current loaded json data
        self.json_current_file = None                   # Current json file path
        self.json_file_dirs = self.get_json_file_dirs() # The current list of file directories
        self.json_files = []                            # All the file names
        self.json_current_file_name = ""                # Used for UI
        self.json_file_name = None                      # Last saved file name
        self.json_getting_file_name = False             # If inputing file name
        self.setup_json_draw_elements(context)          # Setup input system

        # Setup
        self.capture_initial_state(context=context)

        self.get_light_empty(context)
        self.get_lights()
        if self.lights == []:
            self.randomize_all_lights()

        # Scene Settings
        self.use_scene_lights = context.space_data.shading.use_scene_lights
        context.space_data.shading.use_scene_lights = True

        # Form
        self.form_lights = []

        # Base Systems
        self.setup_form(context, event)
        self.master = Master(context)
        self.master.only_use_fast_ui = True
        self.base_controls = Base_Modal_Controls(context, event)
        self.original_tool_shelf, self.original_n_panel = collapse_3D_view_panels()
        self.draw_handle = bpy.types.SpaceView3D.draw_handler_add(self.safe_draw_shader, (context,), 'WINDOW', 'POST_PIXEL')
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


    def modal(self, context, event):

        # Getting JSON file name (Shift S sets this.)
        if self.json_getting_file_name == True:
            self.save_json_file_with_user_input(context, event)
            context.area.tag_redraw()
            return {'RUNNING_MODAL'}

        self.master.receive_event(event)
        self.base_controls.update(context, event)
        self.form.update(context, event)
        
        # Dot open / close
        if event.type == 'TAB' and event.value == 'PRESS':
            if self.form.is_dot_open():
                self.form.close_dot()
            else:
                self.form.open_dot()

        # Navigation
        if self.base_controls.pass_through:
            if not self.form.active():
                return {'PASS_THROUGH'}

        # Confirm
        elif self.base_controls.confirm:
            if not self.form.active():
                self.confirm_exit(context)
                return {'FINISHED'}

        # Cancel
        elif self.base_controls.cancel:
            if not self.form.active():
                self.cancel_exit(context)
                return {'CANCELLED'}

        # Form Close
        if self.form_exit:
            self.confirm_exit(context)
            return {'FINISHED'}

        # Actions
        if not self.form.is_dot_open():
            self.actions(context, event)

        # Mouse Navigation
        elif event.type in {'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            if not self.form.active():
                return {'PASS_THROUGH'}

        self.FAS_display(context=context)
        context.area.tag_redraw()
        return {'RUNNING_MODAL'}


    def actions(self, context, event):

        if self.mouse_active:
            mouse_warp(context, event)
            if not self.non_destructive:
                angle = self.base_controls.mouse * 2 
                if abs(angle) > 0:
                    self.rotate_light_rig(angle)

        # Randomize / Scale / Switch Lights
        if event.type in {'WHEELUPMOUSE', 'WHEELDOWNMOUSE', 'LEFT_ARROW', 'RIGHT_ARROW'} and event.value == 'PRESS':
            if not self.form.active():
                if self.non_destructive:
                    self.randomize_all_lights_non_additive(context)
                
                else:
                    if event.ctrl == True:
                        self.switch_light_types(context)
                    elif event.shift == False:
                        self.randomize_all_lights()
                    elif event.shift == True:
                        if event.type == 'WHEELUPMOUSE':
                            self.rig_sca += .25
                        else:
                            self.rig_sca -= .25

        # Set all colors to white
        elif event.type == 'W' and event.value == 'PRESS':
            self.set_all_colors_to_white()

        # Toggle Extra Lights
        elif event.type == 'E' and event.value == 'PRESS':
            if self.available_light_types == {'AREA'}:
                self.available_light_types = {'AREA', 'SUN'}
            elif self.available_light_types == {'AREA', 'SUN'}:
                self.available_light_types = {'AREA', 'SUN', 'POINT'}
            elif self.available_light_types == {'AREA', 'SUN', 'POINT'}:
                self.available_light_types = {'AREA'}

            types = ""
            for light_type in self.available_light_types:
                types += str(light_type) + "  "
            bpy.ops.hops.display_notification(info=f'{types}')

        # Increase light energy
        elif event.type in self.base_controls.keyboard_increment:
            if event.value == 'PRESS':
                self.adjust_light_energy(increase=True)
            
        # Decrease light energy
        elif event.type in self.base_controls.keyboard_decrement:
            if event.value == 'PRESS':
                self.adjust_light_energy(increase=False)

        # Desaturate colors
        elif event.type == 'D' and event.value == 'PRESS':
            self.desaturate_light_colors()
            
        # Saturate colors / Save
        elif event.type == 'S' and event.value == 'PRESS':
            # Save JSON
            if event.shift: self.start_save_system()
            # Adjust colors
            else: self.saturate_light_colors()

        # Randomize colors
        elif event.type == 'C' and event.value == 'PRESS':
            self.randomize_light_colors()

        # Add Eevee Bloom
        elif event.type == 'Q' and event.value == 'PRESS':
            self.toggle_bloom()

        # Exit to viewport adjust
        elif event.type == 'V' and event.value == 'PRESS':
            self.exit_to_viewport_adjust = not self.exit_to_viewport_adjust

        # Toggle Ortho / Perspective
        elif event.type in {'P', 'NUMPAD_5'} and event.value == 'PRESS':
            bpy.ops.view3d.view_persportho()

        # Toggle volumetrics
        elif event.type == 'F' and event.value == 'PRESS':
            if bpy.app.version[0] < 4:
                self.toggle_world_fog(context)
            else:
                bpy.ops.hops.display_notification(info=F'Unavailable Post 4.0', subtext = "Due to changes with Blender itself in later versions")


    def confirm_exit(self, context):
        self.common_exit(context)
        if self.exit_to_viewport_adjust == True:
            bpy.context.space_data.shading.use_scene_world = False
            bpy.ops.hops.adjust_viewport('INVOKE_DEFAULT')


    def cancel_exit(self, context):
        self.common_exit(context)
        self.restore_initial_state(context=context)


    def common_exit(self, context):
        self.master.run_fade()
        self.form.shut_down(context)
        self.remove_shader()
        collapse_3D_view_panels(self.original_tool_shelf, self.original_n_panel)
        context.space_data.shading.use_scene_lights = self.use_scene_lights

    # --- SETTERS --- #

    @property
    def rig_loc(self):
        return round(self.empty.location.z, 1)

    @rig_loc.setter
    def rig_loc(self, val):
        self.empty.location.z = val

    @property
    def rig_rot(self):
        return int(math.degrees(self.empty.rotation_euler.z))

    @rig_rot.setter
    def rig_rot(self, val):
        self.empty.rotation_euler.z = math.radians(val)
        if abs(math.degrees(self.empty.rotation_euler.z)) > 360:
            self.empty.rotation_euler.z = 0

    @property
    def rig_sca(self):
        return round(self.empty.scale[0], 1)

    @rig_sca.setter
    def rig_sca(self, val):
        self.empty.scale = Vector((val, val, val))

    @property
    def fog_z(self):
        return round(self.__fog_z, 1)

    @fog_z.setter
    def fog_z(self, val):
        val = 0 if abs(val) > 99.9 else val
        self.__fog_z = val
        self.z_location_world()

    @property
    def fog_opacity(self):
        return round(self.__fog_opacity, 2)

    @fog_opacity.setter
    def fog_opacity(self, val):
        self.__fog_opacity = val

        if self.__fog_opacity > 1: self.__fog_opacity = 1
        elif self.__fog_opacity < 0: self.__fog_opacity = 0

        self.world_opacity()

    # --- FORM FUNCS --- #

    def FAS_display(self, context):
        self.master.setup()
        if self.master.should_build_fast_ui():

            # Main
            win_list = []
            point_lights = 0
            area_lights = 0
            sun_lights = 0

            for light in self.lights:
                if light.data.type == 'POINT':
                    point_lights += 1
                elif light.data.type == 'AREA':
                    area_lights += 1
                elif light.data.type == 'SUN':
                    sun_lights += 1

            if addon.preference().ui.Hops_modal_fast_ui_loc_options != 1:
                win_list.append(f'P : {point_lights}')
                win_list.append(f'A : {area_lights}')
                win_list.append(f'S : {sun_lights}')
            else:
                win_list.append(f'Point Lights: {point_lights}')
                win_list.append(f'Area Lights: {area_lights}')
                win_list.append(f'Sun Lights: {sun_lights}')
            
            if self.exit_to_viewport_adjust:
                win_list.append(f'[V] To_Viewport {self.exit_to_viewport_adjust}')

            # Help
            help_items = {"GLOBAL" : [], "STANDARD" : []}

            help_items["GLOBAL"] = [
                ("M", "Toggle lights list"),
                ("H", "Toggle help"),
                ("~", "Toggle UI Display Type"),
                ("O", "Toggle viewport rendering")]

            help_items["STANDARD"] = [
                ('V',              f'To_Viewport - {self.exit_to_viewport_adjust}'),
                ("W",              "Set all lights to White"),
                ("+ -",            "Adjust energy"),
                ("D",              "Desaturate colors"),
                ("S",              "Saturate colors"),
                ('Q',              'Bloom'),
                ('Shift + S',      'Save Configuration'),
                ("C",              "Randomize light colors"),
                ("E",              "Toggle additional lights"),
                ("5 / P",          "Toggle Ortho"),
                #('F',              "Toggle Fog"),
                ("Scroll",         "Next Blank Rig"),
                ("Ctrl + Scroll",  "Switch light types"),
                ("Shift + Scroll", "Adjust Scale")]

            if bpy.app.version[0] < 4:
                help_items["STANDARD"].insert(-3, ['F',              "Toggle Fog"]),

            # Mods
            mods_list = []
            for light in self.lights:
                mods_list.append([light.name, ""])

            self.master.receive_fast_ui(win_list=win_list, help_list=help_items, image="ArrayCircle", mods_list=mods_list)

        self.master.finished()


    def setup_form(self, context, event):

        self.form = form.Form(context, event, dot_open=event.shift)

        def spacer(height=10):
            row = self.form.row()
            row.add_element(form.Spacer(height=height))
            self.form.row_insert(row)
        
        def gap(row, width=5):
            row.add_element(form.Spacer(width=width))

        row = self.form.row()
        row.add_element(form.Label(text="BlankLight", width=195))
        row.add_element(form.Button(text="X", width=20, tips=["Finalize and Exit"], callback=self.exit_button))
        self.form.row_insert(row)

        spacer()

        row = self.form.row()
        row.add_element(form.Button(img='small_dice', width=32, tips=["Click / Scroll", "Generate a new light setup"], callback=self.randomize_all_lights))
        gap(row)
        row.add_element(form.Button(text='E', width=22, tips=["Click / Scroll", "Adjust the energy levels"], callback=self.adjust_light_energy, pos_args=(True,), neg_args=(False,)))
        gap(row)
        row.add_element(form.Button(text='C', width=22, tips=["Click / Scroll", "Generate new colors only"], callback=self.randomize_light_colors))
        gap(row)
        row.add_element(form.Button(text='W', width=22, tips=["Click", "Remove all colors from lights"], callback=self.set_all_colors_to_white))
        gap(row)
        row.add_element(form.Button(text='B', width=22, tips=["Click", "Toggle EEVEE Bloom"], callback=self.toggle_bloom))
        self.form.row_insert(row)

        spacer()

        row = self.form.row()
        row.add_element(form.Label(text="L", width=20))
        row.add_element(form.Input(obj=self, attr="rig_loc", width=45, increment=.1, font_size=12, tips=["Location"]))
        row.add_element(form.Label(text="R", width=20))
        row.add_element(form.Input(obj=self, attr="rig_rot", width=45, increment=18, font_size=12, tips=["Rotation"]))
        row.add_element(form.Label(text="S", width=20))
        row.add_element(form.Input(obj=self, attr="rig_sca", width=45, increment=.1, font_size=12, tips=["Scale"]))
        self.form.row_insert(row)

        spacer()

        row = self.form.row()
        group = self.lights_group()
        self.lights_box = form.Scroll_Box(width=215, height=20 * 3, scroll_group=group, view_scroll_enabled=False)
        row.add_element(self.lights_box)
        self.form.row_insert(row)

        spacer()

        row = self.form.row()
        row.add_element(form.Button(text="Presets", tips=["Toggle Presets list."], callback=self.presets_toggle))
        gap(row)
        row.add_element(form.Button(text="Save", tips=["Save the current light config."], callback=self.start_save_system))
        self.form.row_insert(row)

        spacer()

        row = self.form.row()
        group = self.json_group(context)
        self.json_box = form.Scroll_Box(width=215, height=20 * 5, scroll_group=group, view_scroll_enabled=True)
        row.add_element(self.json_box)
        self.form.row_insert(row, label='PRESETS', active=False)

        spacer()

        if bpy.app.version[0] < 4:
            row = self.form.row()
            row.add_element(form.Button(text="Fog", tips=["Toggle Fog."], callback=self.toggle_world_fog, pos_args=(context,), neg_args=(context,), highlight_hook=self.fog_update_hook))
            self.form.row_insert(row, label='FOG_PARTIAL', active=not self.set_fog_off)

            row = self.form.row()
            row.add_element(form.Button(text="Fog", width=40, tips=["Toggle Fog."], callback=self.toggle_world_fog, pos_args=(context,), neg_args=(context,), highlight_hook=self.fog_update_hook))
            gap(row)
            row.add_element(form.Button(text="R", width=20, tips=["Randomize Fog"], callback=self.randomize_fog))
            gap(row)
            row.add_element(form.Button(text="C", width=20, tips=["Randomize Fog Color"], callback=self.randomize_world_color))
            gap(row)
            row.add_element(form.Input(obj=self, attr="fog_z", width=50, increment=.1, font_size=12, tips=["Fog Location"]))
            gap(row)
            row.add_element(form.Input(obj=self, attr="fog_opacity", width=45, increment=.05, font_size=12, tips=["Fog Opacity"]))
            self.form.row_insert(row, label='FOG_FULL', active=self.set_fog_off)

        self.form.build()


    def lights_group(self):
        self.form_lights = [FLight(light) for light in self.lights]
        group = form.Scroll_Group()
        for light in self.form_lights:

            row = group.row()
            text = form.shortened_text(light.name, width=105, font_size=12)
            tip = [light.name, "Click : Change light color"]

            row.add_element(
                form.Button(
                    text='O', highlight_text='X', width=20, height=20, use_padding=False, scroll_enabled=False,
                    callback=light.toggle_vis, highlight_hook=light.vis_hook))

            row.add_element(
                form.Button(
                    text=text, tips=tip, width=115, height=20, use_padding=False, scroll_enabled=False,
                    callback=self.set_random_light_color, pos_args=(light.light,)))

            row.add_element(
                form.Input(obj=light, attr="energy", width=60, height=20, increment=light.increment_amount, font_size=12, tips=["Energy"]))

            group.row_insert(row)
        return group


    def json_group(self, context):
        group = form.Scroll_Group()
        for json_file in self.get_json_file_names(with_msg=False):

            row = group.row()
            text = form.shortened_text(json_file, width=185, font_size=12)
            tip = [] if text == json_file else [json_file]

            row.add_element(
                form.Button(
                    text=text, tips=tip, width=195, height=20, use_padding=False, scroll_enabled=False,
                    callback=self.load_specified_json_file, pos_args=(context, json_file), neg_args=(context, json_file)))

            group.row_insert(row)
        return group


    def rebuild_lights_group(self):
        if not hasattr(self, 'lights_box'): return
        self.lights_box.scroll_group.clear(bpy.context)
        group = self.lights_group()
        self.lights_box.scroll_group = group
        self.form.build()


    def rebuild_json_group(self, context):
        if not hasattr(self, 'json_box'): return
        self.json_box.scroll_group.clear(context)
        group = self.json_group(context)
        self.json_box.scroll_group = group
        self.form.build()


    def fog_row_full_toggle(self, preset_label=''):

        self.form.db.clicked = False

        if self.set_fog_off:
            self.form.row_activation(label='FOG_PARTIAL', active=False)
            self.form.row_activation(label='FOG_FULL', active=True)
            self.form.build()
        else:
            self.form.row_activation(label='FOG_PARTIAL', active=True)
            self.form.row_activation(label='FOG_FULL', active=False)
            self.form.build()


    def presets_toggle(self):
        active = self.form.get_row_status(label='PRESETS')
        self.form.row_activation(label='PRESETS', active=not active)
        self.form.db.clicked = False
        self.form.build()


    def exit_button(self):
        self.form_exit = True

    # --- SHADER --- #

    def safe_draw_shader(self, context):
        method_handler(self.draw_shader,
            arguments=(context,),
            identifier='Blank Lights',
            exit_method=self.remove_shader)


    def remove_shader(self):
        if self.draw_handle:
            self.draw_handle = bpy.types.SpaceView3D.draw_handler_remove(self.draw_handle, "WINDOW")


    def draw_shader(self, context):
        self.form.draw()

        if not self.form.is_dot_open():
            draw_modal_frame(context)

    # --- WORLD FOG --- #

    def initial_world_setup(self, context):
        if bpy.context.scene.world == None:
            world = bpy.data.worlds.new('HopsWorld')
            bpy.context.scene.world = world
        
        world = bpy.context.scene.world
        world.use_nodes = True

        types = [n.type for n in world.node_tree.nodes]
        found_output = True if 'OUTPUT_WORLD' in types else False 

        if found_output == False:
            node = world.node_tree.nodes.new('ShaderNodeOutputWorld')
            node.location = (0,0)


    def set_initial_fog_z(self):
        for node in self.hops_world_nodes():
            if node.name == 'Mapping':
                self.__fog_z = node.inputs['Location'].default_value.z


    def set_initial_fog_opacity(self):
        for node in self.hops_world_nodes():
            if node.name == 'Volume Scatter':
                self.__fog_opacity = node.inputs['Color'].default_value[0]
                break


    def toggle_world_fog(self, context):
        '''Toggle the world fog values.'''

        world = bpy.context.scene.world
        node_tree = world.node_tree
        nodes = node_tree.nodes
        if 'HOPS WORLD' in nodes:
            hops_group = nodes['HOPS WORLD']
            for node in hops_group.node_tree.nodes:
                if node.name == 'Volume Scatter':
                    node.inputs['Color'].default_value[0] = 0 if self.set_fog_off else 1
                    node.inputs['Color'].default_value[1] = 0 if self.set_fog_off else 1
                    node.inputs['Color'].default_value[2] = 0 if self.set_fog_off else 1
                    break
        else:
            self.setup_world_edit_mode(context)
            self.set_fog_off = False

        self.set_fog_off = not self.set_fog_off
        self.fog_row_full_toggle()


    def is_fog_on(self):
        if bpy.context.scene.eevee.use_volumetric_lights:
            if bpy.context.scene.eevee.use_volumetric_shadows:
                
                if not bpy.context.scene.world: return False
                if not bpy.context.scene.world.use_nodes: return False

                node_tree = bpy.context.scene.world.node_tree
                nodes = node_tree.nodes
                if 'HOPS WORLD' in nodes:
                    hops_group = nodes['HOPS WORLD']
                    for node in hops_group.node_tree.nodes:
                        if node.name == 'Volume Scatter':
                            if node.inputs['Color'].default_value[0] == 1:
                                return True
        return False


    def fog_update_hook(self):
        return bool(self.set_fog_off)


    def setup_world_edit_mode(self, context: bpy.context):
        '''Creates the initial world setup.'''

        if self.ran_world_setup: return

        bpy.context.scene.eevee.use_volumetric_lights = True
        bpy.context.scene.eevee.use_volumetric_shadows = True
        bpy.context.scene.world.use_nodes = True
        bpy.context.space_data.shading.use_scene_lights = True
        bpy.context.space_data.shading.use_scene_world = True

        # Data
        group_name = "HOPS WORLD"
        world_output = None

        # Search for the node group and remove it if found
        node_tree = context.scene.world.node_tree
        nodes = node_tree.nodes
        for node in nodes:
            if node.type == 'GROUP':
                if node.name == group_name:
                    node_tree.nodes.remove(node)
                    break

        # Remove the node group from the blend data
        for tree in bpy.data.node_groups:
            if tree.name == group_name:
                bpy.data.node_groups.remove(tree)

        # Get the world output
        for node in nodes:
            if node.type == 'OUTPUT_WORLD':
                world_output = node
                break

        # If the world output was not found
        if world_output == None:
            node_tree.nodes.new('ShaderNodeOutputWorld')

        # Create the node group
        self.create_volume_node_group(group_name=group_name)

        # Insert node group into world node tree
        volume_group = node_tree.nodes.new("ShaderNodeGroup")
        volume_group.node_tree = bpy.data.node_groups[group_name]
        volume_group.location = (world_output.location[0] - 250, world_output.location[1] - 100)
        volume_group.name = group_name

        # Link : Volume -> World
        node_tree.links.new(volume_group.outputs['shader_out'], world_output.inputs['Volume'])

        self.ran_world_setup = True


    def create_volume_node_group(self, group_name=""):
        '''Creates the volume node group and insert it into the blend data'''

        # Create : Group
        node_group = bpy.data.node_groups.new(group_name, 'ShaderNodeTree')

        # Create : Group Outputs
        group_outputs = node_group.nodes.new('NodeGroupOutput')
        group_outputs.location = (700,0)
        node_group.outputs.new('NodeSocketShader','shader_out')
        
        # Create : Group Inputs
        group_inputs = node_group.nodes.new('NodeGroupInput')
        group_inputs.location = (-700,200)
        node_group.inputs.new('NodeSocketFloat','density')
        node_group.inputs.new('NodeSocketFloat','scale_one')
        node_group.inputs.new('NodeSocketFloat','scale_two')

        node_group.inputs['density'].min_value = 0
        node_group.inputs['density'].max_value = 1
        node_group.inputs['density'].default_value = 1

        node_group.inputs['scale_one'].min_value = 0
        node_group.inputs['scale_one'].max_value = 2
        node_group.inputs['scale_one'].default_value = .05

        node_group.inputs['scale_two'].min_value = 0
        node_group.inputs['scale_two'].max_value = 2
        node_group.inputs['scale_two'].default_value = .25

        # Create : Texture Coords
        text_coords_node = node_group.nodes.new('ShaderNodeTexCoord')
        text_coords_node.location = (-700,0)

        # Create : Mapping
        mapping_node = node_group.nodes.new('ShaderNodeMapping')
        mapping_node.inputs['Scale'].default_value = (.2, .2, 1)
        self.__fog_z = mapping_node.inputs['Location'].default_value.z
        mapping_node.location = (-500,0)

        # Create : Musgrave One
        musgrave_node_one = node_group.nodes.new('ShaderNodeTexMusgrave')
        musgrave_node_one.musgrave_type = 'RIDGED_MULTIFRACTAL'
        musgrave_node_one.inputs['Scale'].default_value = .05
        musgrave_node_one.inputs['Offset'].default_value = .25
        musgrave_node_one.location = (-300,-200)

        # Create : Musgrave Two
        musgrave_node_two = node_group.nodes.new('ShaderNodeTexMusgrave')
        musgrave_node_two.musgrave_type = 'RIDGED_MULTIFRACTAL'
        musgrave_node_two.inputs['Scale'].default_value = .25
        musgrave_node_two.inputs['Offset'].default_value = .3
        musgrave_node_two.location = (-300,200)

        # Create : Mix
        mix_node = node_group.nodes.new('ShaderNodeMixRGB')
        mix_node.blend_type = 'MIX'
        mix_node.inputs['Color2'].default_value = (.2,.2,.2,1)
        mix_node.location = (0,0)

        # Create : Mix Density
        mix_density = node_group.nodes.new('ShaderNodeMixRGB')
        mix_density.blend_type = 'MIX'
        mix_density.inputs['Color1'].default_value = (0,0,0,1)
        mix_density.location = (250,0)

        # Create : Volume Scatter
        volume_node = node_group.nodes.new('ShaderNodeVolumeScatter')
        volume_node.location = (450,0)

        # Links
        node_group.links.new(text_coords_node.outputs['Generated'], mapping_node.inputs['Vector'])
        node_group.links.new(mapping_node.outputs['Vector'], musgrave_node_two.inputs['Vector'])
        node_group.links.new(mapping_node.outputs['Vector'], musgrave_node_one.inputs['Vector'])
        node_group.links.new(musgrave_node_one.outputs['Fac'], mix_node.inputs['Color1'])
        node_group.links.new(musgrave_node_two.outputs['Fac'], mix_node.inputs['Fac'])
        node_group.links.new(mix_node.outputs['Color'], mix_density.inputs['Color2'])
        node_group.links.new(mix_density.outputs['Color'], volume_node.inputs['Density'])
        node_group.links.new(volume_node.outputs['Volume'], group_outputs.inputs['shader_out'])
        # Inputs
        node_group.links.new(group_inputs.outputs['density'], mix_density.inputs['Fac'])
        node_group.links.new(group_inputs.outputs['scale_one'], musgrave_node_one.inputs['Scale'])
        node_group.links.new(group_inputs.outputs['scale_two'], musgrave_node_two.inputs['Scale'])


    def randomize_fog(self):
        for node in self.hops_world_nodes():
            if node.name == 'Mapping':
                node.inputs['Scale'].default_value = (random.uniform(.25, 1), random.uniform(.25, 1), 1)
            elif node.name == "Group Input":
                node.outputs['scale_one'].default_value = random.uniform(.001, .1)
                node.outputs['scale_two'].default_value = random.uniform(.001, .3)
            elif node.name == 'Musgrave Texture':
                node.inputs['Offset'].default_value = random.uniform(.05, .35)
            elif node.name == 'Musgrave Texture.001':
                node.inputs['Offset'].default_value = random.uniform(.001, .4)
            elif node.name == 'Mix':
                col = random.uniform(.05, .5)
                node.inputs['Color2'].default_value = (col,col,col,1)
            elif node.name == 'Volume Scatter':
                col = random.uniform(.05, .5)
                node.inputs['Color'].default_value = (col,col,col,1)
                node.inputs['Anisotropy'].default_value = random.uniform(0, .8)


    def randomize_world_color(self):
        for node in self.hops_world_nodes():
            if node.name == 'Volume Scatter':
                node.inputs['Color'].default_value = (random.uniform(.5, 1), random.uniform(.5, 1), random.uniform(.5, 1) ,1)
                break


    def rotate_world(self, rot=18):
        for node in self.hops_world_nodes():
            if node.name == 'Mapping':
                node.inputs['Rotation'].default_value.z += rot
                break


    def z_location_world(self, z_loc=0):
        for node in self.hops_world_nodes():
            if node.name == 'Mapping':
                if z_loc:
                    node.inputs['Location'].default_value.z += z_loc
                    self.__fog_z = node.inputs['Location'].default_value.z
                    break
                else:
                    node.inputs['Location'].default_value.z = self.__fog_z

    
    def world_opacity(self, opacity=0):
        for node in self.hops_world_nodes():
            if node.name == 'Volume Scatter':
                if opacity:
                    node.inputs['Color'].default_value[0] += opacity
                    node.inputs['Color'].default_value[1] += opacity
                    node.inputs['Color'].default_value[2] += opacity
                    break
                else:
                    node.inputs['Color'].default_value[0] = self.__fog_opacity
                    node.inputs['Color'].default_value[1] = self.__fog_opacity
                    node.inputs['Color'].default_value[2] = self.__fog_opacity
                    break


    def hops_world_nodes(self):
        node_tree = bpy.context.scene.world.node_tree
        nodes = node_tree.nodes
        if 'HOPS WORLD' not in nodes: return []
        return nodes['HOPS WORLD'].node_tree.nodes


    def toggle_bloom(self):
        bpy.context.scene.eevee.use_bloom = not bpy.context.scene.eevee.use_bloom
        bpy.context.scene.eevee.bloom_intensity = 1.04762
        bpy.context.scene.eevee.bloom_threshold = 1.94286
        self.report({'INFO'}, F'Bloom: {bpy.context.scene.eevee.use_bloom}')

    # --- RIG / LIGHT --- #

    def get_light_empty(self, context, with_create_new=True, at_cursor=False):
        '''Get the light collection or return the exsisting one.'''

        empty_name = "HOPS Light Empty"
        new_empty = None
        collection = context.view_layer.active_layer_collection.collection

        # Check if the empty exsist
        for obj in collection.objects:
            if obj.name[:16] == empty_name:
                new_empty = obj
                break

        # Used for initial data storing
        if with_create_new == False:
            if new_empty == None:
                return None
            else:
                return new_empty

        # If no empty was in the collection make a new empty
        if new_empty == None:
            new_empty = bpy.data.objects.new(empty_name, None )
            context.collection.objects.link(new_empty)
            new_empty.empty_display_size = .5
            new_empty.empty_display_type = 'SPHERE'

        # Store it
        self.empty = new_empty

        # Locate it
        if not self.non_destructive:
            self.empty.location = context.scene.cursor.location


    def get_lights(self):
        '''Get all the light objects on parent object.'''

        new_lights = []

        for obj in self.empty.children:
            if obj.type == 'LIGHT':
                new_lights.append(obj)

        self.lights = new_lights


    def randomize_all_lights(self):
        '''Delete all the lights and rebuild everything randomly.'''

        for light in self.lights:
            bpy.data.lights.remove(light.data)

        self.lights = []

        for light_type in self.available_light_types:

            # Add random area lights
            if light_type == 'AREA':
                self.lights += self.add_random_area_lights()

            # Add random sun lights
            elif light_type == 'SUN':
                self.lights += self.add_random_sun_lights()

            # Add random point lights
            elif light_type == 'POINT':
                self.lights += self.add_random_point_lights()

        self.rebuild_lights_group()


    def randomize_all_lights_non_additive(self, context):
        '''Randomize all the lights in non additive mode.'''

        #self.switch_light_types(context, use_random=True)
        self.randomize_light_energy()
        for light in self.lights:
            self.set_random_light_color(light)


    def switch_light_types(self, context, use_random=False):
        '''Keeps the lights in place but switches there type and resets the energy.'''


        for light in self.lights:

            types = list(self.available_light_types)

            # Remove the current light from the list
            if use_random == False:
                if len(types) > 1:
                    if light.data.type in types:
                        index = types.index(light.data.type)
                        light.data.type = types[(index + 1) % len(types)]
                    else:
                        light.data.type = types[0]
            else:
                if len(types) > 1:
                    ran_index = random.randint(0, len(types) - 1)

                    # Make it harder for a sun to happen
                    if types[ran_index] == 'SUN':
                        pick = random.randint(0, 20)
                        if pick < 7:
                            light.data.type = 'SUN'
                        else:
                            light.data.type = 'AREA'

                    else:
                        light.data.type = types[ran_index]


                elif len(types) == 1:
                    light.data.type = types[0]

            if light.data.type == 'POINT':
                light.name = "HOPS_LIGHT_POINT"
                light.data.energy = random.uniform(50, 1000)
                light.data.shadow_soft_size = .25

            elif light.data.type == 'AREA':
                light.name = "HOPS_LIGHT_AREA"
                light.data.size = random.uniform(1, 10)
                light.data.energy = random.uniform(50, 7000)

            elif light.data.type == 'SUN':
                light.name = "HOPS_LIGHT_SUN"
                light.data.energy = random.uniform(1, 5)   


    def add_random_point_lights(self):
        lights = []
        light_count = random.randint(0, 6)
        radius = random.uniform(10, 30)

        # Place in circle
        for i in range(light_count):

            # Sweep angle
            angle = i * math.pi * 2 / light_count
            angle += random.uniform(-.5, .5)

            # Location
            x_loc = cos(angle) * radius
            y_loc = sin(angle) * radius
            z_loc = random.uniform(2, 6)
            location = (x_loc, y_loc, z_loc)

            # Create light
            new_light = self.add_light(location=location, light_type='POINT')

            # Color
            self.set_random_light_color(new_light)

            # Energy
            new_light.data.energy = random.uniform(50, 1000)

            # Store
            lights.append(new_light)

        return lights


    def add_random_sun_lights(self):

        lights = []
        light_count = 0
        if len(self.available_light_types) > 2:
            light_count = random.randint(0, 3)
        else:
            light_count = random.randint(0, 1)

        radius = random.uniform(15, 20)

        # Place in circle
        for i in range(light_count):

            # Sweep angle
            angle = i * math.pi * 2 / light_count
            angle += random.uniform(-.5, .5)

            # Location
            x_loc = cos(angle) * radius
            y_loc = sin(angle) * radius
            z_loc = random.uniform(.5, 30)
            location = (x_loc, y_loc, z_loc)

            # Create light
            new_light = self.add_light(location=location, light_type='SUN')

            # Color
            self.set_random_light_color(new_light)

            # Energy
            new_light.data.energy = random.uniform(1, 5)

            # Rotation
            up_vec = Vector((0, 0, 1))
            euler_rot = up_vec.rotation_difference(location).to_euler()
            new_light.rotation_euler = euler_rot

            # Store
            lights.append(new_light)

        return lights


    def add_random_area_lights(self):
        lights = []
        light_count = random.randint(1, 4)
        radius = random.uniform(15, 20)

        # Place in circle
        for i in range(light_count):

            # Sweep angle
            angle = i * math.pi * 2 / light_count
            angle += random.uniform(-.5, .5)

            # Location
            x_loc = cos(angle) * radius
            y_loc = sin(angle) * radius
            z_loc = random.uniform(.5, 30)
            location = (x_loc, y_loc, z_loc)

            # Create light
            new_light = self.add_light(location=location, light_type='AREA')

            # Color
            self.set_random_light_color(new_light)

            # Energy
            new_light.data.energy = random.uniform(50, 7000)

            # Size
            new_light.data.size = random.uniform(1, 10)

            # Rotation
            up_vec = Vector((0, 0, 1))
            euler_rot = up_vec.rotation_difference(location).to_euler()
            new_light.rotation_euler = euler_rot

            # Store
            lights.append(new_light)

        return lights


    def rotate_light_rig(self, angle=0):
        '''Rotate the light rig.'''

        if self.empty != None:
            self.empty.rotation_euler.z += angle

    # --- LOWER LEVEL FUNCTIONS --- #

    def add_light(self, location=(0,0,0), look_target=(0,0,0), light_type='POINT'):
        '''Create a new light, return light ID.'''

        light_data = bpy.data.lights.new(name='HOPS_Light_Data', type=light_type)
        light_obj = bpy.data.objects.new(f'HOPS_{light_type}', object_data=light_data)
        light_obj.location = location
        light_obj.data.use_contact_shadow = True
        bpy.context.collection.objects.link(light_obj)
        light_obj.parent = self.empty

        if addon.preference().property.to_light_constraint:
            con = light_obj.constraints.new(type='TRACK_TO')
            con.target = self.empty
            con.up_axis = 'UP_Y'
            con.track_axis = 'TRACK_NEGATIVE_Z'

        return light_obj


    def set_random_light_color(self, light):
        '''Set light color.'''

        r = random.uniform(0, 1)
        g = random.uniform(0, 1)
        b = random.uniform(0, 1)
        light.data.color = (r, g, b)


    def set_all_colors_to_white(self):
        '''Sets all the color values to white.'''

        for light in self.lights:
            light.data.color = (1, 1, 1)
            

    def adjust_light_energy(self, increase=True):
        '''Increase the energy of each light based on increase.'''

        for light in self.lights:

            if light.data.type == 'POINT':
                value = 100 if increase else -(light.data.energy / 15)
                light.data.energy += value

            elif light.data.type == 'AREA':
                value = 100 if increase else -(light.data.energy / 15)
                light.data.energy += value

            elif light.data.type == 'SUN':
                value = .25 if increase else -(light.data.energy / 15)
                light.data.energy += value

            if light.data.energy < 0:
                light.data.energy = 0


    def randomize_light_energy(self):
        '''Set random light energy.'''

        for light in self.lights:

            if light.data.type == 'POINT':
                light.data.energy =random.uniform(50, 1000)

            elif light.data.type == 'AREA':
                light.data.energy =random.uniform(50, 7000)

            elif light.data.type == 'SUN':
                light.data.energy = random.uniform(1, 5)


    def desaturate_light_colors(self):
        '''Desaturate the light colors by moving values to white.'''

        for light in self.lights:
            for index, value in enumerate(light.data.color):
                diff = 1 - value
                if diff > 0:
                    light.data.color[index] += diff / 10


    def saturate_light_colors(self):
        '''Saturate the light colors by moving values to its closer side.'''

        for light in self.lights:
            if light.data.color.s < 1:
                diff = 1 - light.data.color.s
                light.data.color.s += diff / 10


    def randomize_light_colors(self):
        '''Randomize the light colors.'''

        for light in self.lights:
            self.set_random_light_color(light)

    # --- RECOVERY FUNCTIONS --- #

    def capture_initial_state(self, context):
        '''Capture all the settings from the intitial build.'''

        self.initial_light_data = []
        self.initial_empty_data = None
        empty = self.get_light_empty(context, with_create_new=False)

        # No light empty was found : will remove every thing on cancel
        if empty == None:
            return
        else:
            class Empty_Data:
                def __init__(self):
                    self.name = None
                    self.loc = None
                    self.scale = None
                    self.rot = None

            self.initial_empty_data = Empty_Data()
            self.initial_empty_data.name = empty.name
            self.initial_empty_data.loc = (empty.location[0], empty.location[1], empty.location[2])
            self.initial_empty_data.scale = (empty.scale[0], empty.scale[1], empty.scale[2])
            self.initial_empty_data.rot = (empty.rotation_euler[1], empty.rotation_euler[1], empty.rotation_euler[2])
                
        # Copy light data from original lights
        for obj in empty.children:
            if obj.type == 'LIGHT':
                light_data = self.get_initial_light_data(obj)
                if light_data != None:
                    self.initial_light_data.append(light_data)


    def restore_initial_state(self, context):
        '''Revert back all the changes made in the modal on cancel.'''

        # Delete everything since it started with nothing
        if self.initial_empty_data == None:
            for light in self.lights:
                bpy.data.lights.remove(light.data)
            bpy.data.objects.remove(self.empty)

        # Revert back to original state
        else:
            # Make sure no errors occured
            if self.empty == None:
                return

            # Revert the empty
            self.empty.name = self.initial_empty_data.name
            self.empty.location = self.initial_empty_data.loc
            self.empty.scale = self.initial_empty_data.scale
            self.empty.rotation_euler = self.initial_empty_data.rot

            # Remove all the modified lights
            for light in self.lights:
                bpy.data.lights.remove(light.data)

            # Add back the original lights
            for light_data in self.initial_light_data:
                light = self.add_light(
                    location=light_data.loc,
                    look_target=self.empty.location,
                    light_type=light_data.type)

                light.name = light_data.name
                light.data.energy = light_data.energy
                light.data.color = light_data.color
                # create a location matrix
                mat_loc = Matrix.Translation(light_data.loc)
                # create an identitiy matrix
                mat_sca = Matrix.Scale(1, 4, light_data.scale)
                # create a rotation matrix
                mat_rot = light_data.rot.to_matrix()
                mat_rot = mat_rot.to_4x4()

                # combine transformations
                mat_out = mat_loc @ mat_rot @ mat_sca

                light.matrix_local = mat_out


    def get_initial_light_data(self, light):
        '''Create a copy of all the light data for the light.'''

        # Validate type and data members
        validated = False
        if hasattr(light, 'type'):
            if light.type == 'LIGHT':
                if hasattr(light, 'data'):
                    if hasattr(light.data, 'energy'):
                        if hasattr(light.data, 'color'):
                            validated = True

        if validated == False:
            return None

        class Light_Data:
            def __init__(self):
                self.name = None
                self.type = None
                self.energy = None
                self.color = None
                self.loc = None
                self.scale = None
                self.rot = None

        light_data = Light_Data()
        light_data.name = light.name
        light_data.type = light.data.type
        light_data.energy = light.data.energy
        light_data.color = (light.data.color[0], light.data.color[1], light.data.color[2])
        light_data.loc = (light.location[0], light.location[1], light.location[2])
        light_data.scale = (light.scale[0], light.scale[1], light.scale[2])
        light_data.rot = light.matrix_local.decompose()[1]
        return light_data

    # --- JSON FUNCTIONS --- #

    def start_save_system(self):
        self.json_file_name = None
        self.json_getting_file_name = True


    def get_next_json_configuration(self, context, forward=True):
        '''Get the next configuration from the json file.'''

        # Validate file dirs
        self.json_file_dirs = self.get_json_file_dirs()
        if len(self.json_file_dirs) < 1:
            bpy.ops.hops.display_notification(info='No Light files.')
            return

        # Set current file
        if self.json_current_file == None:
            self.json_current_file = self.json_file_dirs[0]

        # Go to next file
        else:
            # Keep moving
            if self.json_current_file in self.json_file_dirs:
                index = self.json_file_dirs.index(self.json_current_file)
                increment = 1 if forward else -1
                self.json_current_file = self.json_file_dirs[(index + increment) % len(self.json_file_dirs)]
            # File was not there restart
            else:
                self.json_current_file = self.json_file_dirs[0]

        # Set the file name
        file_with_extension = os.path.basename(self.json_current_file)
        self.json_current_file_name = file_with_extension.split('.')[0]

        # Open file for write
        self.json_data = None 
        with open(self.json_current_file, 'r') as json_file:
            self.json_data = json.load(json_file)

        # Load data
        if self.json_data != None:
            self.setup_rig_to_match_json_data(context, self.json_data)
            head, tail = file_name = os.path.split(self.json_current_file)
            if self.master.should_build_fast_ui():
                bpy.ops.hops.display_notification(info=F'{tail.split(".")[0]}')
        else:
            bpy.ops.hops.display_notification(info=F'ERROR: Bad Data @ {self.json_current_file}')


    def setup_rig_to_match_json_data(self, context, data={}):
        '''Setup the light rig to math the json data.'''

        # Clear the lights out
        for light in self.lights:
            bpy.data.lights.remove(light.data)
        self.lights = []

        for light_name, props_dict in data.items():
            if type(props_dict) != dict:
                print("Props for key are invalid")
                continue

            # Validate
            validated = False
            if "type" in props_dict:
                if "loc" in props_dict:
                    validated = True
            if validated == False:
                continue

            light = self.add_light(
                location=props_dict['loc'],
                look_target=self.empty.location,
                light_type=props_dict['type'])

            # Validate
            validated = False
            if "rot" in props_dict:
                if "scale" in props_dict:
                    if "color" in props_dict:
                        if "energy" in props_dict:
                            if "size" in props_dict:
                                validated = True
            if validated == False:
                continue

            light.rotation_euler = props_dict['rot']
            light.scale = props_dict['scale']
            light.data.color = props_dict['color']
            light.data.energy = props_dict['energy']

            if hasattr(light.data, 'size'):
                light.data.size = props_dict['size']

            self.lights.append(light)


    def save_json_file_with_user_input(self, context, event):
        '''Freeze the modal and take input.'''

        # Add draw handle
        if not hasattr(self, 'json_draw_handle'):
            self.json_draw_handle = None
            
        if self.json_draw_handle == None:
            self.json_draw_handle = bpy.types.SpaceView3D.draw_handler_add(self.safe_draw_file_name, (context,), 'WINDOW', 'POST_PIXEL')

        # Cancelled
        if event.type in cancel and event.value == 'PRESS':
            self.json_getting_file_name = False
            # Remove shader
            self.remove_file_name_shader()
            bpy.ops.hops.display_notification(info="Cancelled")
            return

        # Finished
        if event.type in completed and event.value == 'PRESS':
            if self.json_file_name == None or self.json_file_name == "":
                form = '%B %d %Y - %H %M %S %f'
                self.json_file_name = datetime.now().strftime(form)
            self.json_getting_file_name = False

        # Append
        elif event.ascii not in invalid and event.value == 'PRESS':
            if self.json_file_name == None:
                self.json_file_name = ""
            
            self.json_file_name += event.ascii

        # Backspace
        if event.type == 'BACK_SPACE' and event.value == 'PRESS':
            if self.json_file_name != None:
                self.json_file_name = self.json_file_name[:len(self.json_file_name)-1]
            else:
                self.json_file_name = ""

        # Completed Input : SAVE FILE
        if self.json_getting_file_name == False:
            # Remove shader
            self.remove_file_name_shader()
            # Save the file
            self.save_rig_to_json(context)
            bpy.ops.hops.display_notification(info="File Saved!")
            self.rebuild_json_group(context)

        # Set text to draw
        if self.json_file_name == None:
            self.json_shader_file_text = "Auto"
        else:
           self.json_shader_file_text = self.json_file_name

        # Hack for the UI
        self.master.receive_event(event)
        self.FAS_display(context)
        self.form.update(context, event)


    def setup_json_draw_elements(self, context):
        '''Setup json drawing data from invoke.'''

        factor = dpi_factor(min=.25)
        self.json_shader_file_text = ""
        self.json_shader_help_text = "Type in file name or Return for Date Time formatting."
        self.screen_width = context.area.width
        self.screen_height = context.area.height


    def safe_draw_file_name(self, context):
        method_handler(self.draw_file_name_shader,
            arguments=(context,),
            identifier='File Save',
            exit_method=self.remove_file_name_shader)


    def remove_file_name_shader(self):
        if self.json_draw_handle:
            self.json_draw_handle = bpy.types.SpaceView3D.draw_handler_remove(self.json_draw_handle, "WINDOW")


    def draw_file_name_shader(self, context):
        '''Draw shader handle.'''

        factor = dpi_factor()

        help_text_size = 18
        file_text_size = 24

        sample_y = get_blf_text_dims("XyZ`Qq", file_text_size)[1]
        help_text_dims = get_blf_text_dims(self.json_shader_help_text, help_text_size)
        file_text_dims = get_blf_text_dims(self.json_shader_file_text, file_text_size)

        center_x = self.screen_width * .5
        center_y = self.screen_height * .5

        text_padding_y = 30 * factor
        text_padding_x = 20 * factor

        total_height = text_padding_y * 3 + sample_y + sample_y
        widest_text = help_text_dims[0] if help_text_dims[0] > file_text_dims[0] else file_text_dims[0]
        total_width = text_padding_x * 2 + widest_text

        # TL, BL, TR, BR
        verts = [
            (center_x - total_width * .5, center_y + total_height * .5),
            (center_x - total_width * .5, center_y - total_height * .5),
            (center_x + total_width * .5, center_y + total_height * .5),
            (center_x + total_width * .5, center_y - total_height * .5)]

        render_quad(
            quad=verts,
            color=(0,0,0,.5))

        draw_border_lines(
            vertices=verts,
            width=2,
            color=(0,0,0,.75))

        x_loc = center_x - help_text_dims[0] * .5
        y_loc = center_y - help_text_dims[1] * .5 + file_text_size * factor
        render_text(
            text=self.json_shader_help_text, 
            position=(x_loc, y_loc), 
            size=help_text_size, 
            color=(1,1,1,1))

        x_loc = center_x - file_text_dims[0] * .5
        y_loc = center_y - file_text_dims[1] * .5 - file_text_size * factor
        render_text(
            text=self.json_shader_file_text, 
            position=(x_loc, y_loc), 
            size=file_text_size, 
            color=(1,1,1,1))


    def save_rig_to_json(self, context):
        '''Save the rig to a json file.'''

        # Get path to light folder
        folder_path = self.get_json_folder_path()
        if folder_path == None:
            return

        # Validate json file name
        if self.json_file_name == "" or self.json_file_name == None:
            return

        # Get the rig data as a dict
        rig_data = self.get_light_rig_data_for_json()
        if rig_data == None:
            return

        # Save the file
        self.save_json_file(folder_path=folder_path, rid_data=rig_data)


    def get_json_folder_path(self):
        '''Return the folder path for the JSON files.'''

        prefs = addon.preference()
        folder = Path(prefs.property.lights_folder).resolve()
        
        if os.path.exists(folder):
            return folder
        
        try:
            folder.mkdir(parents=True, exist_ok=True)
            return folder
        except:
            print(f'Unable to create {folder}')
            return None


    def ensure_json_file_name(self, folder_path=""):
        '''Makes sure no other file with the same name exsist.'''

        if folder_path == "":
            return None
        
        file_path = os.path.join(folder_path, self.json_file_name + '.json')
        if os.path.exists(file_path):
            form = ' %B %d %Y - %H %M %S %f'
            self.json_file_name += datetime.now().strftime(form)


    def get_json_file_names(self, with_msg=True):
        '''Get all the json file names.'''

        # Check for json files
        folder = self.get_json_folder_path()
        if folder == None:
            return []

        all_files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
        json_files = []

        for f in all_files:
            filename, file_extension = os.path.splitext(f)
            if file_extension == '.json':
                json_files.append(filename)

        if json_files == [] and with_msg:
            bpy.ops.hops.display_notification(info='Save a light first: Shift + S')

        return json_files


    def get_json_file_dirs(self):
        '''Set the list of file directories.'''

        # Check for json files
        folder = self.get_json_folder_path()
        if folder == None:
            return

        all_files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
        json_files = []

        for f in all_files:
            filename, file_extension = os.path.splitext(f)
            if file_extension == '.json':
                json_files.append(os.path.join(folder, f))

        return json_files


    def get_light_rig_data_for_json(self):
        '''Capture the light rig data as a json ready dictionary.'''

        # Validate
        if self.empty == None:
            return None

        config = {}
        for obj in self.empty.children:
            if obj.type == 'LIGHT':
                config[obj.name] = {
                    'loc'    : (obj.location[0], obj.location[1], obj.location[2]),
                    'rot'    : (obj.rotation_euler[0], obj.rotation_euler[1], obj.rotation_euler[2]),
                    'scale'  : (obj.scale[0], obj.scale[1], obj.scale[2]),
                    'color'  : (obj.data.color[0], obj.data.color[1], obj.data.color[2]),
                    'energy' : obj.data.energy,
                    'type'   : obj.data.type,
                    'size'   : obj.data.size if hasattr(obj.data, 'size') else 0
                }

        return config


    def save_json_file(self, folder_path="", rid_data={}):
        '''Save the rig data to the file.'''

        # Make sure the file wont write over and exsisting file
        self.ensure_json_file_name(folder_path=folder_path)

        # Create file and dump jason into it
        file_path = os.path.join(folder_path, self.json_file_name + '.json')
        with open(file_path, 'w') as json_file:
            json.dump(rid_data, json_file, indent=4)

        # Update the directories list
        self.json_file_dirs = self.get_json_file_dirs()

        # Update files
        self.json_files = self.get_json_file_names()


    def load_specified_json_file(self, context, file_name=""):
        '''Load the specified file name.'''

        # Check if the files are loaded
        if self.json_file_dirs == [] or self.json_file_dirs == None:
            bpy.ops.hops.display_notification(info="Could not load file.")
            return

        # Get file dir
        load_dir = ""
        for f_name in self.json_file_dirs:
            if file_name in f_name:
                load_dir = f_name
                break
        if load_dir == "":
            bpy.ops.hops.display_notification(info="Could not load file.")
            return

        self.json_data = None
        self.json_current_file = load_dir

        # Open file for write
        self.json_data = None 
        with open(self.json_current_file, 'r') as json_file:
            self.json_data = json.load(json_file)

        # Load data
        if self.json_data != None:
            self.setup_rig_to_match_json_data(context, self.json_data)
        else:
            bpy.ops.hops.display_notification(info=F'ERROR: Bad Data @ {self.json_current_file}')

        self.json_current_file_name = file_name
        self.rebuild_lights_group()

