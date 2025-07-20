import bpy, math, numpy
from bpy.props import BoolProperty
from math import radians, degrees
from . import infobar
from ... utility import addon
from ... ui_framework.master import Master
from ... utility import ops
from ... utility.base_modal_controls import Base_Modal_Controls
from ... utils.toggle_view3d_panels import collapse_3D_view_panels
from ... utils.modal_frame_drawing import draw_modal_frame
from ... utils.cursor_warp import mouse_warp
from ... utils.objects import set_bool_tagets_on_objects_to_smooth
from ... utility import method_handler


DESC = """Interactive Autosmooth Adjustment

LMB   - Adjust autosmoothing
CTRL  - Start at 60°
SHIFT - Start at 30°
ALT   - Start at 15°

Press H for help
"""


class HOPS_OT_AdjustAutoSmooth(bpy.types.Operator):
    bl_idname = 'hops.adjust_auto_smooth'
    bl_label = 'Adjust Auto Smooth'
    bl_options = {'REGISTER', 'UNDO', 'BLOCKING'}
    bl_description = DESC

    def __init__(self):
        self.master = None

        self.number_to_angle = {
            'ONE': 15,
            'TWO': 20,
            'THREE': 30,
            'FOUR': 45,
            'FIVE': 60,
            'SIX': 75,
            'SEVEN': 90,
            'EIGHT': 180,
        }


    angle: bpy.props.FloatProperty(
        name='Auto Smooth Angle',
        description='The angle at which to automatically sharpen edges',
        default=35,
        min=0,
        max=180,
    )

    flag: BoolProperty(
        name = 'Use Bevel Special Behavior',
        default = False,
        description = 'Ignore Ctrl keypress')

    @classmethod
    def poll(cls, context):
        return any(o.type == 'MESH' for o in context.selected_objects)


    def invoke(self, context, event):

        ops.shade_smooth()
        self.objects = [o for o in context.selected_objects if o.type == 'MESH']
        self.settings = {o: {} for o in self.objects}

        # if event.ctrl:
        #     self.angle = 60
        # if event.shift:
        #     self.angle = 30
        # if event.alt:
        #     self.angle = 15

        for obj in self.objects:
            self.settings[obj]['use_auto_smooth'] = obj.data.use_auto_smooth
            obj.data.use_auto_smooth = True

            self.settings[obj]['auto_smooth_angle'] = obj.data.auto_smooth_angle
            obj.data.auto_smooth_angle = math.radians(self.angle)

            bevmods = bevels(obj, angle=True)

            if self.flag:
                if bevmods:
                    for mod in bevmods:
                        mod.show_viewport = False

        self.modal_scale = addon.preference().ui.Hops_modal_scale
        self.buffer = self.angle

        # Base Systems
        self.master = Master(context=context)
        self.master.only_use_fast_ui = True
        self.base_controls = Base_Modal_Controls(context, event)
        self.original_tool_shelf, self.original_n_panel = collapse_3D_view_panels()
        self.draw_handle = bpy.types.SpaceView3D.draw_handler_add(self.safe_draw_shader, (context,), 'WINDOW', 'POST_PIXEL')

        context.area.header_text_set(text=f'Auto Smooth Angle: {self.angle:.1f}')
        context.window_manager.modal_handler_add(self)
        infobar.initiate(self)
        return {'RUNNING_MODAL'}


    def modal(self, context, event):

        # Base Systems
        self.master.receive_event(event=event)
        self.base_controls.update(context, event)
        mouse_warp(context, event)

        if self.base_controls.pass_through:
            return {'PASS_THROUGH'}

        offset = self.base_controls.mouse * 10

        if event.type == 'MOUSEMOVE':
            self.buffer = min(max(self.buffer + offset, 0), 180)
            self.angle = round(self.buffer, 0 if event.ctrl else 1)
            self.update(context)

        elif event.type == 'Z' and (event.shift or event.alt):
            return {'PASS_THROUGH'}

        elif event.type in {'ONE', 'TWO', 'THREE', 'FOUR', 'FIVE', 'SIX', 'SEVEN', 'EIGHT'} and event.value == 'PRESS':
            self.buffer = self.number_to_angle[event.type]
            self.angle = self.number_to_angle[event.type]
            self.update(context)

        elif self.base_controls.scroll:
            self.buffer += 5 * self.base_controls.scroll
            self.angle += 5 * self.base_controls.scroll
            self.update(context)

        elif self.base_controls.cancel:
            self.cancel(context)

            obj = bpy.context.object
            for mod in obj.modifiers:
                if mod.type == 'BEVEL': #and mod.limit_method == 'ANGLE':
                    mod.show_viewport = True

            context.area.header_text_set(text=None)
            self.remove_shader()
            collapse_3D_view_panels(self.original_tool_shelf, self.original_n_panel)
            self.master.run_fade()
            infobar.remove(self)
            return {'CANCELLED'}

        elif self.base_controls.confirm:
            obj = bpy.context.object

            if self.flag :
                for mod in obj.modifiers:
                    if mod.type == 'BEVEL': # and mod.limit_method == 'ANGLE':
                        mod.show_viewport = True
                self.angle = 60
                self.buffer = 60
                bpy.context.object.data.auto_smooth_angle = radians(60)
                self.flag = False
            else:
                for mod in obj.modifiers:
                    if mod.type == 'BEVEL': #and mod.limit_method == 'ANGLE':
                        mod.show_viewport = True
            context.area.header_text_set(text=None)
            self.remove_shader()
            collapse_3D_view_panels(self.original_tool_shelf, self.original_n_panel)
            self.master.run_fade()
            infobar.remove(self)
            return {'FINISHED'}

        elif event.type == 'G' and event.value == 'PRESS':
            bpy.context.object.hops.is_global = not bpy.context.object.hops.is_global

        elif event.type == 'B' and event.value == 'PRESS':
            obj = bpy.context.object

            for mod in obj.modifiers:
                if mod.type == 'BEVEL': #and mod.limit_method == 'ANGLE':
                    mod.show_viewport = not mod.show_viewport

        elif event.type == "A" and event.value == 'PRESS' and not event.shift and not event.alt:
            mod = None
            obj = bpy.context.object

            bevmods = bevels(obj, angle=True)

            if bevmods:
                for mod in bevmods:
                    mod.show_viewport = True
                    mod.angle_limit = radians(self.angle)

                    self.report({'INFO'}, F'AngleFound')
                    self.update(context)
                #_____________
                self.angle = 60
                self.buffer = 60
                context.area.header_text_set(text=None)
                self.finished = True
                self.remove_shader()
                collapse_3D_view_panels(self.original_tool_shelf, self.original_n_panel)
                self.master.run_fade()
                bpy.ops.hops.adjust_bevel('INVOKE_DEFAULT')
                return {"FINISHED"}
            else:
                context.area.header_text_set(text=None)
                self.finished = True
                self.remove_shader()
                collapse_3D_view_panels(self.original_tool_shelf, self.original_n_panel)
                self.master.run_fade()
                #_____________
                #mod.show_viewport = True
                if not bevmods:
                    add_bevel_modifier(context, obj, radians(self.angle))
                bpy.ops.hops.adjust_bevel('INVOKE_DEFAULT')
                bpy.context.object.data.auto_smooth_angle = radians(60)
                self.report({'INFO'}, F'Bevel Added')
                return {"FINISHED"}
            self.update(context)

        elif event.type == "A" and event.value == 'PRESS' and event.shift:
            bpy.context.object.data.use_auto_smooth = not bpy.context.object.data.use_auto_smooth
            self.report({'INFO'}, F'Autosmooth {bpy.context.object.data.use_auto_smooth}')

        elif event.type == 'S' and event.value == 'PRESS':
            if event.shift:
                bpy.ops.hops.sharpen(behavior='SSHARP', mode='SSHARP', additive_mode=True, auto_smooth_angle=radians(self.angle), is_global=bpy.context.object.hops.is_global)
                self.report({'INFO'}, F'Sharpen - Exit')
                self.remove_shader()
                collapse_3D_view_panels(self.original_tool_shelf, self.original_n_panel)
                self.master.run_fade()
                infobar.remove(self)
                return {'FINISHED'}

            else:
                smooth_cutters_rec(self.objects)
                bpy.ops.hops.display_notification(info=F'Boolshapes - Set Smooth')

        elif event.type == 'R' and event.value == 'PRESS':
            bpy.ops.hops.sharpen(behavior='RESHARP', mode='SSHARP', additive_mode=False, auto_smooth_angle=radians(self.angle), is_global=bpy.context.object.hops.is_global)
            self.report({'INFO'}, F'Resharpen - Exit')
            self.remove_shader()
            collapse_3D_view_panels(self.original_tool_shelf, self.original_n_panel)
            self.master.run_fade()
            infobar.remove(self)
            return {'FINISHED'}

        self.draw_master(context=context)
        context.area.tag_redraw()
        return {'RUNNING_MODAL'}


    def update(self, context):
        angle = math.radians(self.angle)

        context.area.header_text_set(text=f'Auto Smooth Angle: {self.angle:.1f}')

        for obj in self.objects:
            obj.data.auto_smooth_angle = angle


    def cancel(self, context):
        for obj in self.objects:
            # obj.data.use_auto_smooth = self.settings[obj]['use_auto_smooth'] # Commented out because mx prefers it this way
            obj.data.auto_smooth_angle = self.settings[obj]['auto_smooth_angle']


    def finish(self, context):
        context.area.header_text_set(text=None)
        self.remove_ui()
        infobar.remove(self)
        return {"FINISHED"}


    def draw_master(self, context):
        self.master.setup()
        if not self.master.should_build_fast_ui(): return

        obj = bpy.context.object

        # Main
        win_list = []
        if addon.preference().ui.Hops_modal_fast_ui_loc_options != 1: #fast
            win_list.append(f'{self.angle:.1f}')
            win_list.append(f'{bpy.context.object.hops.is_global}')
            win_list.append(f'{bpy.context.object.data.use_auto_smooth}')
        else:
            if self.flag:
                win_list.append('Auto Smooth Scan') #not fast
            else:
                win_list.append('Auto Smooth') #not fast
            win_list.append(f'{self.angle:.1f}')
            win_list.append(f'Global Sharpen :{bpy.context.object.hops.is_global}')
            if not obj.modifiers:
                win_list.append('[A] Add Bevel')
            if bpy.context.object.data.use_auto_smooth == False:
                win_list.append('Autosmooth OFF')
            if self.flag:
                win_list.append('[A] Return / [B] Toggle Bevel')
                win_list.append('[LMB] Apply')

        # Help
        help_items = {"GLOBAL" : [], "STANDARD" : []}

        help_items["GLOBAL"] = [
            ("M", "Toggle mods list"),
            ("H", "Toggle help"),
            ("~", "Toggle UI Display Type"),
            ("O", "Toggle viewport rendering")]

        help_items["STANDARD"] = [
            ('8',          'Set angle to 180°'),
            ('7',          'Set angle to 90°'),
            ('6',          'Set angle to 75°'),
            ('5',          'Set angle to 60°'),
            ('4',          'Set angle to 45°'),
            ('3',          'Set angle to 30°'),
            ('2',          'Set angle to 20°'),
            ('1',          'Set angle to 15°'),
            ('Shift S',    f'Sharpen {self.angle:.1f}° - Exit'),
            ('S',          'Set Booleans to smooth'),
            ('R',          f'Resharpen - Exit'),
            ('G',          f'Toggle Global : {bpy.context.object.hops.is_global}'),
            ('Shift + A',  f'Autosmooth Toggle {bpy.context.object.data.use_auto_smooth}'),
            ('Scroll   ',  'Increment angle by 5°'),
            ('Mouse    ',  f'Adjust angle smoothly: {self.angle:.1f}'),
            ('A',          'Transfer Autosmooth to Bevel - Exit')]

        # Mods
        mods_list = []
        for mod in reversed(context.active_object.modifiers):
            mods_list.append([mod.name, str(mod.type)])

        self.master.receive_fast_ui(win_list=win_list, help_list=help_items, image='Tthick', mods_list=mods_list)

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


def bevels(obj, angle=False, weight=False, vertex_group=False, props={}):
    if not hasattr(obj, 'modifiers'):
        return []

    bevel_mods = [mod for mod in obj.modifiers if mod.type == 'BEVEL']

    if not angle and not weight and not vertex_group and not props:
        return bevel_mods

    modifiers = []
    limit_method_in = lambda method, mod: mod not in modifiers and mod.limit_method == method

    if angle:
        for mod in bevel_mods:
            if limit_method_in('ANGLE', mod):
                modifiers.append(mod)

    if weight:
        for mod in bevel_mods:
            if limit_method_in('WEIGHT', mod):
                #modifiers.append(mod)
                break

    if vertex_group:
        for mod in bevel_mods:
            if limit_method_in('VGROUP', mod):
                #modifiers.append(mod)
                break

    if props:

        for mod in bevel_mods:
            if mod in modifiers:
                continue

            for pointer in props:
                prop = hasattr(mod, pointer) and getattr(mod, pointer) == props[pointer]
                if not prop:
                    continue

                modifiers.append(mod)

    return sorted(modifiers, key=lambda mod: bevel_mods.index(mod))


def add_bevel_modifier(context, object, angle):
    bevel_modifier = object.modifiers.new(name="Bevel", type="BEVEL")
    bevels = [mod for mod in object.modifiers if mod.type == 'BEVEL']
    if addon.preference().ui.Hops_extra_info:
        if addon.preference().property.workflow_mode == 'ANGLE':
            bpy.ops.hops.display_notification(info=f'Bevel Added {"%.1f"%(degrees(angle))}° - Total : {len(bevels)}' )
        else:
            bpy.ops.hops.display_notification(info=f'Bevel Added - Total : {len(bevels)}' )
    bevel_modifier.limit_method = addon.preference().property.workflow_mode

    bevel_modifier.angle_limit = angle
    bevel_modifier.miter_outer = addon.preference().property.bevel_miter_outer
    bevel_modifier.miter_inner = addon.preference().property.bevel_miter_inner
    bevel_modifier.width = 0.01

    if bpy.app.version > (2, 89, 0):
        bevel_modifier.affect = 'EDGES'

    bevel_modifier.profile = addon.preference().property.bevel_profile
    bevel_modifier.loop_slide = addon.preference().property.bevel_loop_slide
    bevel_modifier.use_clamp_overlap = False
    bevel_modifier.segments = addon.preference().property.default_segments
    if object.dimensions[2] == 0 or object.dimensions[1] == 0 or object.dimensions[0] == 0:
        bevel_modifier.segments = 6
        if bpy.app.version < (2, 90, 0):
            bevel_modifier.use_only_vertices = True
        else:
            bevel_modifier.affect = 'VERTICES'
        bevel_modifier.use_clamp_overlap = True
        if addon.preference().ui.Hops_extra_info:
            bpy.ops.hops.display_notification(info=f'2d Bevel Added' )
    elif object.hops.status == "BOOLSHAPE":
        bevel_modifier.harden_normals = False
    # elif addon.preference().property.use_harden_normals:
    #     bevel_modifier.harden_normals = True
    object.show_all_edges = True

    if object.type == 'MESH':
        if not object.data.use_auto_smooth:
            object.data.auto_smooth_angle = radians(60)
        object.data.use_auto_smooth = True

        if context.mode == 'EDIT_MESH':
            vg = object.vertex_groups.new(name='HardOps')
            bpy.ops.object.vertex_group_assign()
            if addon.preference().property.adjustbevel_use_1_segment:
                if context.tool_settings.mesh_select_mode[2] and object.hops.status == "BOOLSHAPE":
                    bevel_modifier.segments = 1
                    bevel_modifier.harden_normals = False
                    bpy.ops.mesh.flip_normals()
            bevel_modifier.limit_method = 'VGROUP'
            bevel_modifier.vertex_group = vg.name
            bpy.ops.mesh.faces_shade_smooth()
            if addon.preference().ui.Hops_extra_info:
                bpy.ops.hops.display_notification(info=f'Vgroup Bevel Added' )
        else:
            ops.shade_smooth()

    # self.bevel_objects.setdefault(object.name, {})["modifier"] = bevel_modifier.name
    # self.bevel_objects[object.name]["added_modifier"] = True

    return (bevel_modifier.name, True)


def smooth_cutters_rec(objects):
    '''Recursively shade smooth cutters of objects and their cutters'''
    stack = list(objects)
    filter = set()
    flag_array = []

    while stack:
        obj = stack.pop()

        for mod in obj.modifiers:
            if mod.type != 'BOOLEAN': continue

            if getattr(mod, 'operand_type', 'OBJECT') == 'OBJECT' and mod.object:
                if mod.object not in filter:
                    filter.add(mod.object)
                    stack.append(mod.object)

                    if len(mod.object.data.polygons) > len(flag_array):
                        flag_array = numpy.ones(len(mod.object.data.polygons), dtype=bool)

                    if mod.object.data.polygons:
                        mod.object.data.polygons.foreach_set('use_smooth', flag_array)
                        mod.object.data.update()

            elif mod.collection:
                meshes = [o for o in mod.collection.objects if o.type == 'MESH' and o not in filter]
                filter.update(meshes)
                stack.extend(meshes)

                for obj in meshes:
                    if len(obj.data.polygons) > len(flag_array):
                        flag_array = numpy.ones(len(obj.data.polygons), dtype=bool)

                    if mod.object.data.polygons:
                        obj.data.polygons.foreach_set('use_smooth', flag_array)
                        obj.data.update()
