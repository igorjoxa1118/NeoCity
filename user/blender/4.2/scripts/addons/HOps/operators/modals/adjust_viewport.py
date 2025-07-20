import bpy
from math import radians
import math
from . import infobar
from ... utility import addon
from ... ui_framework.master import Master
from ... utility.base_modal_controls import Base_Modal_Controls

# Cursor Warp imports
from ... utils.toggle_view3d_panels import collapse_3D_view_panels
from ... utils.modal_frame_drawing import draw_modal_frame
from ... utils.cursor_warp import mouse_warp
from ... utility import method_handler


class HOPS_OT_AdjustViewport(bpy.types.Operator):
    bl_idname = 'hops.adjust_viewport'
    bl_label = 'Adjust Viewport'
    bl_description = """Interactive Lookdev Adjustment

    Adjust the viewport settings
    R to set Lookdev to_render on apply

    Shift + LMB - Copy active lookdev settings to render world
    """
    bl_options = {'REGISTER', 'UNDO', 'BLOCKING'}

    eeveeHQ = 'None'
    to_render = 'None'
    to_light = 'None'

    @classmethod
    def poll(cls, context):
        return context.space_data.type == 'VIEW_3D'

#alright this thing is pretty close to being done. I don't need corrections. Just completions
#improve it if you want but the goals are the same with this modal.

    def invoke(self, context, event):
        self.notify = lambda val: bpy.ops.hops.display_notification(info=val) if addon.preference().ui.Hops_extra_info else lambda val: None
        self.shading = context.space_data.shading
        wm = bpy.context.window_manager
        # if hasattr(obj, 'cycles_visibility'):
        #     bpy.context.scene.render.engine = 'BLENDER_EEVEE'

        if (2, 83, 0) < bpy.app.version:
            self.shading_args = {'type', 'studio_light', 'studiolight_rotate_z', 'studiolight_intensity', 'studiolight_background_alpha', 'studiolight_background_blur'}
        else:
            self.shading_args = {'type', 'studio_light', 'studiolight_rotate_z', 'studiolight_intensity', 'studiolight_background_alpha'}
        self.shading_dict = self.save(self.shading, self.shading_args)
        self.envs = [img.name for img in context.preferences.studio_lights if img.type == 'WORLD']
        self.original_opacity = self.shading.studiolight_background_alpha
        self.original_viewport = bpy.context.space_data.overlay.show_overlays
        self.original_mode = self.shading.type
        self.original_exr = self.shading.studio_light

        if event.shift:
            set_render(self, context)
            self.notify('Copied World shading from Lookdev')
            return {'FINISHED'}

        #type has to change before indexing or it bricks
        self.shading.type = 'MATERIAL'
        self.shading.use_scene_world = False
        self.shading.studiolight_background_alpha = 1
        self.hdri_index = self.envs.index(self.shading.studio_light)
        self.hdri_index_max = len(self.envs) -1
        if bpy.context.region_data.is_perspective:
            self.viewmode = False
        else:
            self.viewmode = True
            bpy.ops.view3d.view_persportho()

        if addon.preference().property.to_render_jump:
            self.to_render = True
        else:
            self.to_render = 'None'

        self.modes = ('Background Rotate', 'Background Blur', 'Background Strength', 'Background Opacity')

        self.mode = self.modes[0]

        # FORCE UPDATE
        self.update_val = True

        # Base Systems
        self.master = Master(context=context, start_mod_hidden=True)
        self.master.only_use_fast_ui = True
        self.base_controls = Base_Modal_Controls(context, event)
        self.original_tool_shelf, self.original_n_panel = collapse_3D_view_panels()
        self.draw_handle = bpy.types.SpaceView3D.draw_handler_add(self.safe_draw_shader, (context,), 'WINDOW', 'POST_PIXEL')

        context.area.header_text_set(text='Adjust Viewport')
        context.window_manager.modal_handler_add(self)
        infobar.initiate(self)
        return {'RUNNING_MODAL'}


    def modal(self, context, event):

        # Base Systems
        self.master.receive_event(event=event)
        self.base_controls.update(context, event)
        mouse_warp(context, event)

        if self.base_controls.mouse:
            offset = self.base_controls.mouse * 10
            # TODO: Use buffer variables and rounding
            if self.mode == 'Background Rotate':
                if self.shading.studiolight_rotate_z + offset > radians(180):
                    self.shading.studiolight_rotate_z = radians(-180)
                elif self.shading.studiolight_rotate_z + offset < radians(-180):
                    self.shading.studiolight_rotate_z = radians(180)
                self.shading.studiolight_rotate_z += offset
            elif self.mode == 'Background Strength':
                self.shading.studiolight_intensity += offset# / 2
            elif self.mode == 'Background Opacity':
                self.shading.studiolight_background_alpha += offset# / 5
            elif self.mode == 'Background Blur':
                self.shading.studiolight_background_blur += offset# / 5

        elif self.base_controls.pass_through:
            return {'PASS_THROUGH'}

        elif event.type == 'Z' and (event.shift or event.alt):
            return {'PASS_THROUGH'}

        elif event.type == 'X' and event.value == 'PRESS':
            index = self.modes.index(self.mode)
            index = (index + 1) % len(self.modes)
            self.mode = self.modes[index]

        elif event.type == 'W' and event.value == 'PRESS' and (event.shift or event.alt):
            context.space_data.overlay.show_overlays = False
            self.shading.studiolight_intensity = 1
            self.shading.studiolight_background_alpha = 1

            if (2, 83, 0) < bpy.app.version:
                self.shading.studiolight_background_blur = 0
            self.mode = self.modes[0]

        elif event.type == 'W' and event.value == 'PRESS':
            context.space_data.overlay.show_overlays = False
            self.shading.studiolight_intensity = 1
            self.shading.studiolight_background_alpha = 1
            #if (2, 83, 0) < bpy.app.version:
            #    self.shading.studiolight_background_blur = 0
            self.mode = self.modes[0]
            if self.eeveeHQ:
                bpy.ops.render.setup()
                self.eeveeHQ = True
            else:
                bpy.ops.hops.renderb_setup()
                self.eeveeHQ = False
            self.eeveeHQ = not self.eeveeHQ

        elif (event.type == 'WHEELUPMOUSE' and event.shift) or (event.type in {'NUMPAD_PLUS', 'EQUAL', 'S' , 'UP_ARROW'} and event.value == 'PRESS'):
            if event.ctrl:
                index = self.modes.index(self.mode)
                index = (index - 1) % len(self.modes)
                self.mode = self.modes[index]

            else:
                self.hdri_index = self.hdri_index +1 if self.hdri_index != self.hdri_index_max else 0
                #self.shading.studio_light = next_list_item(self.envs, self.shading.studio_light)
                self.shading.studio_light = self.envs[self.hdri_index]

        elif (event.type == 'WHEELDOWNMOUSE' and event.shift) or (event.type in {'NUMPAD_MINUS', 'MINUS', 'A', 'DOWN_ARROW'} and event.value == 'PRESS'):
            if event.ctrl:
                index = self.modes.index(self.mode)
                index = (index + 1) % len(self.modes)
                self.mode = self.modes[index]

            else:
                self.hdri_index = self.hdri_index -1 if self.hdri_index !=0 else self.hdri_index_max
               # self.shading.studio_light = previous_list_item(self.envs, self.shading.studio_light)
                self.shading.studio_light = self.envs[self.hdri_index]

        elif event.type in {'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            return {'PASS_THROUGH'}

        #there could probably be more states saved for restoring on start and cancel.
        #dont integrate random ideas at this time. Lets get it ready and plan for the future.
        elif self.base_controls.cancel:
            #mode has to be restored before hdri it it breaks
            bpy.context.space_data.shading.type = self.original_mode
            self.load(self.shading, self.shading_dict)
            bpy.context.space_data.overlay.show_overlays = self.original_viewport
            # bpy.context.space_data.shading.studio_light = self.original_exr
            # self.shading.studiolight_background_alpha = self.original_opacity
            #bpy.context.space_data.shading.type = 'SOLID'
            if self.viewmode:
                bpy.ops.view3d.view_persportho()
            context.area.header_text_set(text=None)
            self.remove_shader()
            collapse_3D_view_panels(self.original_tool_shelf, self.original_n_panel)
            self.master.run_fade()
            infobar.remove(self)
            return {'CANCELLED'}

        elif self.base_controls.confirm:
            context.area.header_text_set(text=None)
            #self.shading.studiolight_background_alpha = self.original_opacity
            #bpy.context.space_data.overlay.show_overlays = self.original_viewport
            #if self.viewmode:
            #    bpy.ops.view3d.view_persportho()
            if self.to_render == True:
                set_render(self,context)
                self.report({'INFO'}, F'Render Set To Lookdev')

            self.remove_shader()
            collapse_3D_view_panels(self.original_tool_shelf, self.original_n_panel)
            self.master.run_fade()
            infobar.remove(self)

            if self.to_light == True:
                self.report({'INFO'}, F'To_Light')
                bpy.ops.hops.blank_light('INVOKE_DEFAULT')

            return {'FINISHED'}

        elif (event.type == 'P' or event.type == 'NUMPAD_5') and event.value == 'PRESS':
            bpy.ops.view3d.view_persportho()

        elif event.type == 'Z' and event.value == 'PRESS':
            bpy.context.space_data.overlay.show_wireframes = not bpy.context.space_data.overlay.show_wireframes
            bpy.context.space_data.overlay.wireframe_threshold = 1

        elif event.type == 'B' and event.value == 'PRESS' and not event.ctrl:
            self.shading.studiolight_background_blur = 0 if self.shading.studiolight_background_blur > 0 else 0.501

        elif event.type == 'T' and event.value == 'PRESS':
            if self.to_light == 'None':
                self.to_light = True
                self.report({'INFO'}, F'To_Light : {self.to_light}')
            else:
                self.to_light = not self.to_light
                self.report({'INFO'}, F'To_Light : {self.to_light}')

        elif event.type == 'V' and event.value == 'PRESS':
            self.shading.studiolight_background_alpha = 0 if self.shading.studiolight_background_alpha > 0 else 1

        elif event.type == 'C' and event.value == 'PRESS':
            self.shading.studiolight_intensity = 0 if self.shading.studiolight_intensity > 0 else 1

        elif event.type == 'R' and event.value == 'PRESS':
            if self.to_render == 'None':
                self.to_render = True
                self.report({'INFO'}, F'Render Set To {self.to_render}')
            else:
                self.to_render = not self.to_render
                self.report({'INFO'}, F'Render Set To {self.to_render}')

        elif event.type == 'M' and event.value == 'PRESS' and event.ctrl:
            if bpy.context.selected_objects:
                context.area.header_text_set(text=None)
                self.shading.studiolight_background_alpha = self.original_opacity
                bpy.context.space_data.overlay.show_overlays = self.original_viewport
                if self.viewmode:
                    bpy.ops.view3d.view_persportho()
                bpy.ops.hops.material_scroll('INVOKE_DEFAULT')
                self.remove_shader()
                collapse_3D_view_panels(self.original_tool_shelf, self.original_n_panel)
                self.master.run_fade()
                infobar.remove(self)
                return {'FINISHED'}
            else:
                self.report({'INFO'}, F'No selection bud')

        elif event.type == 'Q' and event.value == 'PRESS':
            bpy.context.scene.eevee.use_bloom = not bpy.context.scene.eevee.use_bloom
            bpy.context.scene.eevee.bloom_intensity = 1.04762
            bpy.context.scene.eevee.bloom_threshold = 1.94286
            self.report({'INFO'}, F'Bloom: {bpy.context.scene.eevee.use_bloom}')

        # Toggle volumetrics
        elif event.type == 'F' and event.value == 'PRESS':
            bpy.context.space_data.shading.use_scene_lights = True
            bpy.context.space_data.shading.use_scene_world = not bpy.context.space_data.shading.use_scene_world

        # Force Update
        # NOTE : Remove this after blender fixes
        if bpy.app.version >= (2, 92, 0):
            if self.update_val:
                bpy.ops.view3d.view_orbit(angle=.001, type='ORBITLEFT')
            else:
                bpy.ops.view3d.view_orbit(angle=.001, type='ORBITRIGHT')
            self.update_val = not self.update_val

        self.draw_master(context=context)
        context.area.tag_redraw()
        return {'RUNNING_MODAL'}


    def save(self, data, args: set):
        return {arg: getattr(data, arg) for arg in args}


    def load(self, data, args: dict):
        for key, value in args.items():
            setattr(data, key, value)


    def finish(self, context):
        context.area.header_text_set(text=None)
        self.remove_ui()
        infobar.remove(self)
        return {"FINISHED"}


    def draw_master(self, context):
        self.master.setup()

        if self.master.should_build_fast_ui():

            # Micro UI
            win_list = []
            if addon.preference().ui.Hops_modal_fast_ui_loc_options != 1:
                win_list.append(f'{self.mode[11:]}')

                if self.mode == 'Background Rotate':
                    win_list.append(f'{math.degrees(self.shading.studiolight_rotate_z):.0f}°')
                elif self.mode == 'Background Strength':
                    win_list.append(f'{self.shading.studiolight_intensity:.3f}')
                elif self.mode == 'Background Opacity':
                    win_list.append(f'{self.shading.studiolight_background_alpha:.3f}')
                elif self.mode == 'Background Blur':
                    win_list.append(f'{self.shading.studiolight_background_blur:.3f}')

                if self.eeveeHQ == 'None':
                    pass
                    #win_list.append(f'General')
                elif self.eeveeHQ != False:
                    win_list.append(f'LQ')
                elif self.eeveeHQ == False:
                    win_list.append(f'HQ')

                if self.to_render != 'None':
                    win_list.append(f'[R] To_Render {self.to_render}')
                if self.to_light != 'None':
                    win_list.append(f'To_Light {self.to_light}')
            # Full UI
            else:
                win_list.append('Viewport')

                win_list.append(f'Mode: {self.mode}')

                if self.mode == 'Background Rotate':
                    win_list.append(f'Angle: {math.degrees(self.shading.studiolight_rotate_z):.0f}')
                elif self.mode == 'Background Strength':
                    win_list.append(f'Strength: {self.shading.studiolight_intensity:.3f}')
                elif self.mode == 'Background Opacity':
                    win_list.append(f'Opacity: {self.shading.studiolight_background_alpha:.3f}')
                elif self.mode == 'Background Blur':
                    win_list.append(f'Blur: {self.shading.studiolight_background_blur:.3f}')

                if self.eeveeHQ == 'None':
                    win_list.append(f'[W] General')
                elif self.eeveeHQ != False:
                    win_list.append(f'[W] Eevee LQ')
                elif self.eeveeHQ == False:
                    win_list.append(f'[W] Eevee HQ')

                if self.to_render != 'None':
                    win_list.append(f'[R] To_Render {self.to_render}')
                if self.to_light != 'None':
                    win_list.append(f'[T] To_Light {self.to_light}')


            # Help
            help_items = {"GLOBAL" : [], "STANDARD" : []}

            help_items["GLOBAL"] = [
                ("M", "Toggle mods list"),
                ("H", "Toggle help"),
                ("~", "Toggle UI Display Type"),
                ("O", "Toggle viewport rendering")]

            help_items["STANDARD"] = [
                ('T',         f'To_Light: {self.to_light}'),
                ('NUM 5 / P',  'Toggle Persp/Ortho'),
                ('V',          'Background Alpha'),
                ('C',          'Intensity'),
                ('B',          'Blur'),
                ('Q',          'Bloom'),
                ('X',          'Cycle adjust mode'),
                ('W',          f'Eevee LQ / HQ '),
                ('RMB/ESC',    'Cancel'),
                ('Shift + W',  f'Reset View '),
                ('-/+ / A/S',  'Scroll Environment'),
                ('Shift + MMB','Scroll Environment'),
                ('R',          f'To_Render: {self.to_render}'),
                ('F',          'Toggle Fog')]

            h_append = help_items["STANDARD"].append

            if bpy.context.selected_objects:
                h_append(['Ctrl + M',   'Blank Material - Exit'])
            else:
                h_append(['',       'No Selection Active'])

            # Mods
            mods_list = [[e,""] for e in self.envs]

            self.master.receive_fast_ui(win_list=win_list, help_list=help_items, image='WireMode', mods_list=mods_list,  active_mod_name=self.shading.studio_light)

        self.master.finished()

    ####################################################
    #   CURSOR WARP
    ####################################################

    def safe_draw_shader(self, context):
        method_handler(self.draw_shader,
            arguments = (context,),
            identifier = 'UI Framework',
            exit_method = self.remove_shader)


    def remove_shader(self):
        '''Remove shader handle.'''

        if self.draw_handle:
            self.draw_handle = bpy.types.SpaceView3D.draw_handler_remove(self.draw_handle, "WINDOW")


    def draw_shader(self, context):
        '''Draw shader handle.'''

        draw_modal_frame(context)


def next_list_item(list, current):
    index = list.index(current)
    return list[0] if index + 1 > len(list) - 1 else list[index + 1]


def previous_list_item(list, current):
    index = list.index(current)
    return list[-1] if index - 1 < 0 else list[index - 1]


def set_render(self, context):

    self.shading = context.space_data.shading
    active_hdri_name = self.shading.studio_light

    if self.shading.type != 'MATERIAL':
        shade_type = self.shading.type
        self.shading.type = 'MATERIAL'
        active_hdri_name = self.shading.studio_light
        self.shading.type = shade_type

    img_path = bpy.context.preferences.studio_lights[active_hdri_name].path

    img = bpy.data.images.load(img_path, check_existing =True )

    world = bpy.data.worlds.new(active_hdri_name)
    world.use_nodes = True
    bpy.context.scene.world = world

    node_tree = bpy.context.scene.world.node_tree
    node_tree.nodes.clear()

    Mapping = node_tree.nodes.new("ShaderNodeMapping")
    Mapping.location = [-800, 0]
    Mapping.name = "Mapping"
    Mapping.inputs["Location"].default_value = [0.0, 0.0, 0.0]
    Mapping.inputs["Rotation"].default_value = [0.0, 0.0, self.shading.studiolight_rotate_z]
    Mapping.inputs["Scale"].default_value = [1.0, 1.0, 1.0]

    Texture_Coordinate = node_tree.nodes.new("ShaderNodeTexCoord")
    Texture_Coordinate.location = [-1000, 0]
    Texture_Coordinate.name = "Texture_Coordinate"


    World_Output = node_tree.nodes.new("ShaderNodeOutputWorld")
    World_Output.location = [272, 51]
    World_Output.name = "World_Output"


    Light_Path = node_tree.nodes.new("ShaderNodeLightPath")
    Light_Path.location = [-388, 378]
    Light_Path.name = "Light_Path"


    Alpha = node_tree.nodes.new("ShaderNodeMixRGB")
    Alpha.location = [-273, -36]
    Alpha.name = "Alpha"
    Alpha.label = "Alpha"
    Alpha.blend_type = "MIX"
    Alpha.use_clamp = False
    Alpha.inputs["Fac"].default_value = self.shading.studiolight_background_alpha
    Alpha.inputs["Color1"].default_value = [0.0500, 0.0500, 0.0500, 0.0]

    Alpha_Mix = node_tree.nodes.new("ShaderNodeMixRGB")
    Alpha_Mix.location = [-107, 112]
    Alpha_Mix.name = "Alpha_Mix"
    Alpha_Mix.label = "Alpha_Mix"
    Alpha_Mix.blend_type = "MIX"
    Alpha_Mix.use_clamp = False


    Background = node_tree.nodes.new("ShaderNodeBackground")
    Background.location = [71, 39]
    Background.name = "Background"
    Background.inputs["Strength"].default_value = self.shading.studiolight_intensity

    hdri_node = node_tree.nodes.new("ShaderNodeTexEnvironment")
    hdri_node.location = [-600, 0]
    hdri_node.name = "hdri_node"
    hdri_node.image = img

    node_tree.links.new(Background.outputs["Background"], World_Output.inputs["Surface"])
    node_tree.links.new(hdri_node.outputs["Color"], Alpha_Mix.inputs["Color1"])
    node_tree.links.new(Mapping.outputs["Vector"], hdri_node.inputs["Vector"])
    node_tree.links.new(Texture_Coordinate.outputs["Generated"], Mapping.inputs["Vector"])
    node_tree.links.new(Alpha_Mix.outputs["Color"], Background.inputs["Color"])
    node_tree.links.new(Light_Path.outputs["Is Camera Ray"], Alpha_Mix.inputs["Fac"])
    node_tree.links.new(hdri_node.outputs["Color"], Alpha.inputs["Color2"])
    node_tree.links.new(Alpha.outputs["Color"], Alpha_Mix.inputs["Color2"])

