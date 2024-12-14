import bpy, bmesh
from ... utility import addon
from ... utility import modifier
from ... utility.base_modal_controls import Base_Modal_Controls
from ... ui_framework.master import Master
from ... ui_framework.utils.mods_list import get_mods_list
from ... utils.toggle_view3d_panels import collapse_3D_view_panels
from ... utils.modal_frame_drawing import draw_modal_frame
from ... utils.cursor_warp import mouse_warp
from ... utility import method_handler


class HOPS_OT_MOD_Smooth(bpy.types.Operator):
    bl_idname = 'hops.mod_smooth'
    bl_label = 'Adjust Smooth Modifier'
    bl_options = {'REGISTER', 'UNDO', 'BLOCKING', 'GRAB_CURSOR'}
    bl_description = '''LMB - Adjust Smooth Modifier
LMB + Ctrl - Create new Smooth Modifier
LMB + Shift - Auto Vertex Group
LMB + Alt - Use Laplacian Smooth

Press H for help

'''


    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'MESH' and obj.mode in {'OBJECT', 'EDIT'}


    def invoke(self, context, event):
        self.mod_keys = ('iterations', 'use_x', 'use_y', 'use_z', 'vertex_group', 'invert_vertex_group', 'show_viewport', 'show_in_editmode')

        self.create_new = event.ctrl
        self.auto_vgroup = event.shift
        self.start_laplacian = event.alt
        self.modal_scale = addon.preference().ui.Hops_modal_scale
        self.obj = context.active_object
        self.mods = [m for m in self.obj.modifiers if m.type in {'SMOOTH', 'LAPLACIANSMOOTH'}]

        if not self.mods:
            self.create_new = True

        if self.create_new:
            self.mod = self.obj.modifiers.new('Smooth', 'SMOOTH')
            self.mods.append(self.mod)
        else:
            self.mod = self.mods[-1]

        self.clean_vertex_groups()

        self.values = {m: {} for m in self.mods}
        for mod in self.mods:
            self.store(mod)

        if self.auto_vgroup:
            self.create_vgroup(self.mod)
        elif self.obj.mode == 'EDIT':
            self.create_editmode_vgroup(self.mod)

        if self.create_new and self.start_laplacian:
            self.mod = self.switch_type(self.mod)

        self.factor_buffer = self.get_factor(self.mod)
        self.setup_vertex_group_buffer()

        for mod in self.mods:
            mod.show_viewport = True
            mod.show_in_editmode = True

        self.master = Master(context=context)
        self.master.only_use_fast_ui = True
        self.base_controls = Base_Modal_Controls(context, event)
        self.original_tool_shelf, self.original_n_panel = collapse_3D_view_panels()
        self.draw_handle = bpy.types.SpaceView3D.draw_handler_add(self.safe_draw_shader, (context,), 'WINDOW', 'POST_PIXEL')

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


    def modal(self, context, event):
        self.master.receive_event(event=event)
        self.base_controls.update(context, event)
        mouse_warp(context, event)

        if self.base_controls.pass_through:
            return {'PASS_THROUGH'}

        elif event.type == 'Z' and (event.shift or event.alt):
            return {'PASS_THROUGH'}

        elif self.base_controls.confirm:
            context.area.header_text_set(text=None)
            self.report({'INFO'}, 'Finished')
            self.remove_shader()
            collapse_3D_view_panels(self.original_tool_shelf, self.original_n_panel)
            self.master.run_fade()
            return {'FINISHED'}

        elif self.base_controls.cancel:
            context.area.header_text_set(text=None)
            self.report({'INFO'}, 'Cancelled')
            self.cancel(context)
            self.remove_shader()
            collapse_3D_view_panels(self.original_tool_shelf, self.original_n_panel)
            self.master.run_fade()
            return {'CANCELLED'}

        elif self.base_controls.scroll:
            if event.shift:
                if self.base_controls.scroll == 1:
                    bpy.ops.object.modifier_move_up(modifier=self.mod.name)
                else:
                    bpy.ops.object.modifier_move_down(modifier=self.mod.name)

            elif event.ctrl:
                self.scroll(self.base_controls.scroll)

            elif event.alt and self.mod.vertex_group:
                scroll = self.base_controls.scroll
                groups = self.obj.vertex_groups
                group = self.vertex_group_buffer

                index = groups.get(group).index
                index = (index + scroll + len(groups)) % len(groups)

                self.vertex_group_buffer = groups[index].name
                self.mod.vertex_group = self.vertex_group_buffer

            else:
                self.mod.iterations += self.base_controls.scroll
                self.mod.iterations = max(self.mod.iterations, 0)

            self.factor_buffer = self.get_factor(self.mod)

        elif event.type == 'MOUSEMOVE':
            self.factor_buffer += self.base_controls.mouse
            self.factor_buffer = max(self.factor_buffer, 0)
            digits = 2 if event.ctrl and event.shift else 1 if event.ctrl else 3
            self.set_factor(self.mod,  round(self.factor_buffer, digits))

        elif event.type in ('X', 'Y', 'Z') and event.ctrl:
            if event.type == 'X' and event.value == 'PRESS':
                self.mod.use_x = not self.mod.use_x

            elif event.type == 'Y' and event.value == 'PRESS':
                self.mod.use_y = not self.mod.use_y

            elif event.type == 'Z' and event.value == 'PRESS':
                self.mod.use_z = not self.mod.use_z

        elif event.type in ('X', 'Y', 'Z'):
            if event.type == 'X' and event.value == 'PRESS':
                self.mod.use_x = True
                self.mod.use_y = False
                self.mod.use_z = False

            elif event.type == 'Y' and event.value == 'PRESS':
                self.mod.use_x = False
                self.mod.use_y = True
                self.mod.use_z = False

            elif event.type == 'Z' and event.value == 'PRESS':
                self.mod.use_x = False
                self.mod.use_y = False
                self.mod.use_z = True

        elif event.type == 'Q' and event.value == 'PRESS':
            bpy.ops.object.modifier_move_up(modifier=self.mod.name)

        elif event.type == 'W' and event.value == 'PRESS':
            bpy.ops.object.modifier_move_down(modifier=self.mod.name)

        elif event.type == 'T' and event.value == 'PRESS':
            self.mod = self.switch_type(self.mod)

        elif event.type == 'I' and event.value == 'PRESS' and self.mod.vertex_group:
            self.mod.invert_vertex_group = not self.mod.invert_vertex_group
            action = 'Enabled' if self.mod.invert_vertex_group else 'Disabled'
            bpy.ops.hops.display_notification(info=f'Smooth - {action} Invert Vertex Group')

        elif event.type == 'V' and event.value == 'PRESS':
            if self.mod.vertex_group:
                self.mod.vertex_group = ''
                bpy.ops.hops.display_notification(info=f'Smooth - Disabled Vertex Group')

            elif self.vertex_group_buffer:
                self.mod.vertex_group = self.vertex_group_buffer
                bpy.ops.hops.display_notification(info=f'Smooth - Enabled Vertex Group')

        self.draw_master(context=context)
        context.area.tag_redraw()
        return {'RUNNING_MODAL'}


    def cancel(self, context):
        for mod in self.mods:
            self.reset(mod)

        if self.create_new:
            self.obj.modifiers.remove(self.mods[-1])


    def scroll(self, direction):
        index = self.mods.index(self.mod)
        index = (index + direction + len(self.mods)) % len(self.mods)
        self.mod = self.mods[index]

        self.factor_buffer = self.get_factor(self.mod)
        self.setup_vertex_group_buffer()


    def get_factor(self, mod):
        if mod.type == 'SMOOTH':
            return mod.factor
        else:
            return mod.lambda_factor


    def set_factor(self, mod, value):
        if mod.type == 'SMOOTH':
            mod.factor = value
        else:
            mod.lambda_factor = value


    def store(self, mod):
        self.values[mod]['type'] = mod.type
        self.values[mod]['factor'] = self.get_factor(mod)

        for key in self.mod_keys:
            self.values[mod][key] = getattr(mod, key)


    def reset(self, mod):
        if self.values[mod]['type'] != mod.type:
            mod = self.switch_type(mod)

        self.set_factor(mod, self.values[mod]['factor'])

        for key in self.mod_keys:
            setattr(mod, key, self.values[mod][key])


    def switch_type(self, mod):
        kind = 'Laplacian Smooth' if mod.type == 'SMOOTH' else 'Smooth'
        bpy.ops.hops.display_notification(info=f'Smooth - Switched to {kind}')

        if mod.type == 'SMOOTH':
            new = self.obj.modifiers.new('Laplacian Smooth', 'LAPLACIANSMOOTH')
        else:
            new = self.obj.modifiers.new('Smooth', 'SMOOTH')

        self.set_factor(new, self.get_factor(mod))

        for key in self.mod_keys:
            value = getattr(mod, key)
            setattr(new, key, value)

        for index, modifier in enumerate(self.obj.modifiers):
            if modifier == mod:
                for i in range(len(self.obj.modifiers) - (index + 1)):
                    bpy.ops.object.modifier_move_up(modifier=new.name)
                break

        self.values[new] = self.values[mod]
        self.values.pop(mod)

        self.mods.insert(self.mods.index(mod), new)
        self.mods.remove(mod)

        self.obj.modifiers.remove(mod)
        return new


    def clean_vertex_groups(self):
        for mod in self.mods:
            if not self.obj.vertex_groups.get(mod.vertex_group):
                mod.vertex_group = ''


    def setup_vertex_group_buffer(self):
        if self.mod.vertex_group:
            self.vertex_group_buffer = self.mod.vertex_group
        elif self.obj.vertex_groups:
            self.vertex_group_buffer = self.obj.vertex_groups[0].name
        else:
            self.vertex_group_buffer = ''


    def create_vgroup(self, mod):
        original_mode = self.obj.mode

        if original_mode == 'EDIT':
            bpy.ops.object.mode_set(mode='OBJECT')

        vertex_group = None

        for group in self.obj.vertex_groups:
            if group.name == 'HOPS_Smooth':
                vertex_group = group

        if not vertex_group:
            vertex_group = self.obj.vertex_groups.new(name='HOPS_Smooth')

        verts = list(range(len(self.obj.data.vertices)))
        vertex_group.add(index=verts, weight=1.0, type='REPLACE')

        bm = bmesh.new()
        bm.from_mesh(self.obj.data)

        if bpy.app.version[0] >= 4:
            bevel = bm.edges.layers.float.get('bevel_weight_edge')
            if bevel is None:
                bevel = bm.edges.layers.float.new('bevel_weight_edge')
        else:
            bevel = bm.edges.layers.bevel_weight.verify()

        if bpy.app.version[0] >= 4:
            crease = bm.edges.layers.float.get('crease_edge')
            if crease is None:
                crease = bm.edges.layers.float.new('crease_edge')
        else:
            crease = bm.edges.layers.crease.verify()

        verts = []
        for v in bm.verts:
            if v.is_boundary:
                verts.append(v.index)
                continue

            for e in v.link_edges:
                if e.seam or not e.smooth or e[bevel] != 0.0 or e[crease] != 0.0:
                    verts.append(v.index)
                    continue

        vertex_group.remove(index=verts)
        bpy.ops.hops.display_notification(info='Smooth - Auto Vertex Group')
        mod.vertex_group = vertex_group.name
        bm.free()

        if original_mode == 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT')


    def create_editmode_vgroup(self, mod):
        self.obj.update_from_editmode()
        bm = bmesh.from_edit_mesh(self.obj.data)
        verts = [v.index for v in bm.verts if v.select]

        if not verts:
            return

        bpy.ops.object.mode_set(mode='OBJECT')
        vertex_group = self.obj.vertex_groups.new(name='HOPS_Edit_Smooth')
        vertex_group.add(index=verts, weight=1.0, type='ADD')
        bpy.ops.object.mode_set(mode='EDIT')

        bpy.ops.hops.display_notification(info='Smooth - Selected Vertex Group')
        mod.vertex_group = vertex_group.name


    def draw_master(self, context):
        self.master.setup()

        if self.master.should_build_fast_ui():

            # Main
            win_list = []
            axes = []
            if self.mod.use_x:
                axes.append('X')
            if self.mod.use_y:
                axes.append('Y')
            if self.mod.use_z:
                axes.append('Z')
            axes = ', '.join(axes)

            if addon.preference().ui.Hops_modal_fast_ui_loc_options != 1: #Fast Floating
                win_list.append(f'{self.mod.iterations}')
                win_list.append(f'{self.get_factor(self.mod):.3f}')
                win_list.append(f'{axes}')
            else:
                win_list.append('Smooth')
                win_list.append(f'Iterations: {self.mod.iterations}')
                win_list.append(f'Factor: {self.get_factor(self.mod):.3f}')
                win_list.append(f'Axis: {axes}')
                if self.mod.vertex_group:
                    win_list.append(f'VGroup: {self.mod.vertex_group}')
                    win_list.append(f'Invert: {self.mod.invert_vertex_group}')

            # Help
            help_items = {"GLOBAL" : [], "STANDARD" : []}

            help_items["GLOBAL"] = [
                ("M", "Toggle mods list"),
                ("H", "Toggle help"),
                ("~", "Toggle UI Display Type"),
                ("O", "Toggle viewport rendering")]

            help_items["STANDARD"] = [
                ('Scroll',         'Set iterations'),
                ('X, Y, Z',        'Set axis'),
                ('Ctrl + X, Y, Z', 'Toggle axis'),
                ('Q',              'Move mod DOWN'),
                ('W',              'Move mod UP'),
                ('T',              'Switch mod type'),
                ('V',              'Toggle use vertex group')]

            h_append = help_items["STANDARD"].append
            
            if self.mod.vertex_group:
                h_append(['I',              'Toggle invert vertex group'])
                h_append(['Alt + Scroll',   'Cycle vertex groups'])

            h_append(['Shift + Scroll', 'Move mod up/down'])
            h_append(['Ctrl + Scroll',  'Cycle smooth mods'])

            # Mods
            active_mod = ""
            if self.mod != None:
                active_mod = self.mod.name
            mods_list = get_mods_list(mods=bpy.context.active_object.modifiers)

            self.master.receive_fast_ui(win_list=win_list, help_list=help_items, image='Demote', mods_list=mods_list, active_mod_name=active_mod)

        self.master.finished()


    def safe_draw_shader(self, context):
        method_handler(self.draw_shader,
            arguments = (context,),
            identifier = 'UI Framework',
            exit_method = self.remove_shader)


    def remove_shader(self):
        if self.draw_handle:
            self.draw_handle = bpy.types.SpaceView3D.draw_handler_remove(self.draw_handle, 'WINDOW')


    def draw_shader(self, context):
        draw_modal_frame(context)
