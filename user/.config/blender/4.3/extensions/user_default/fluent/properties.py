import bpy
from .Tools.independant_helper import get_addon_preferences
from .Tools.helper import auto_bevel_segments
from .Tools.constants import *
from .bevels import F_outer_bevel
import math
from .UI.menus import get_init_pref


class fluentProp(bpy.types.PropertyGroup):

    def latestBevelUpdate(self, context):
        if get_init_pref():
            for obj in bpy.context.selected_objects:
                if obj.type == 'MESH':
                    outer_bevel = F_outer_bevel(obj)
                    if get_addon_preferences().bevel_system == 'SIMPLE':
                        a = outer_bevel.find_last()
                        if a:
                            outer_bevel.last_as_current()
                    else:
                        a = outer_bevel.find_first()
                        if a:
                            outer_bevel.first_as_current()
                    if a:
                        outer_bevel.set_width(b_width=bpy.context.scene.fluentProp.width, same=None, first=None)

    def latestBevelUniversalUpdate(self, context):
        for obj in bpy.context.scene.objects:
            if obj.type == 'MESH':
                for m in obj.modifiers:
                    if fluent_modifiers_name['outer_bevel'] in m.name:
                        m.width = m.width * float(bpy.context.scene.fluentProp.width_amount)

    def bevelResolutionUpdate(self, context):
        if get_init_pref():
            for obj in bpy.context.scene.objects:
                if obj.type == 'MESH' and obj.get('fluent_type') not in [None, 'unknow']:
                    if len(obj.modifiers):
                        for mod in obj.modifiers:
                            if mod.type == 'BEVEL':
                                if mod.segments > 1 and mod.profile != 0.25:
                                    angle = math.sqrt(math.asin(min(mod.width, 1)))
                                    segments = int(
                                        bpy.context.scene.fluentProp.bevel_resolution * (angle + (1 - math.cos(angle))))
                                    if segments < 4:
                                        segments = 4
                                    mod.segments = segments

    def bevelProfilUpdate(self, context):
        for obj in bpy.context.scene.objects:
            if obj.type == 'MESH' and obj.get('fluent_object'):
                if len(obj.modifiers):
                    for mod in obj.modifiers:
                        if mod.type == 'BEVEL':
                            if mod.segments > 1 and mod.profile != 0.25:
                                mod.profile = bpy.context.scene.fluentProp.bevel_profile

    def outer_bevel_update(self, context):
        for obj in bpy.context.scene.objects:
            if obj.type == 'MESH':
                if len(obj.modifiers):
                    for mod in obj.modifiers:
                        if mod.type == 'BEVEL' and fluent_modifiers_name['outer_bevel'] in mod.name:
                            if bpy.context.scene.fluentProp.outer_bevel_segments == 0:
                                mod.segments = auto_bevel_segments(mod)
                            else:
                                mod.segments = bpy.context.scene.fluentProp.outer_bevel_segments

    def loop_slide_update(self, context):
        for o in bpy.context.selected_objects:
            if o.type == 'MESH':
                bevel = F_outer_bevel()
                bevel.set_target(o)
                b = bevel.find_last()
                if b:
                    b.loop_slide = bpy.context.scene.fluentProp.loop_slide

    def limit_angle_update(self, context):
        for o in bpy.context.selected_objects:
            if o.type == 'MESH':
                bevel = F_outer_bevel()
                bevel.set_target(o)
                b = bevel.find_last()
                if b:
                    b.angle_limit = math.radians(bpy.context.scene.fluentProp.bevel_angle_limit)

    def update_resolution(self, context):
        if get_init_pref():
            # mise à jour de tous les bevels, les cylindres et spheres
            for o in bpy.data.objects:
                if o.type == 'MESH' and o.get('fluent_type'):
                    for m in o.modifiers:
                        if fluent_modifiers_name['outer_bevel'] in m.name and bpy.context.scene.fluentProp.outer_bevel_segments == 0:
                            m.segments = auto_bevel_segments(bevel=m)
                        if fluent_modifiers_name['first_bevel'] in m.name:
                            if m.profile != 0.25:
                                m.segments = auto_bevel_segments(bevel=m)
                        if fluent_modifiers_name['second_bevel_top'] in m.name or fluent_modifiers_name['second_bevel_bottom'] in m.name:
                            if m.profile != 0.25:
                                m.segments = auto_bevel_segments(bevel=m, obj=o)
                        if fluent_modifiers_name['chamfer'] in m.name:
                            if m.profile != 0.25:
                                m.segments = auto_bevel_segments(bevel=m)
                        if o.get('fluent_type') == 'prism' and (o.get('fluent_auto_res') == 'ENABLE' or not o.get('fluent_auto_res')):
                            if fluent_modifiers_name['screw'] in m.name:
                                m.steps = m.render_steps = auto_bevel_segments(
                                    displace=o.modifiers[fluent_modifiers_name['radius']])
                        if o.get('fluent_type') == 'revolver' and (o.get('fluent_auto_res') == 'ENABLE' or not o.get('fluent_auto_res')):
                            if fluent_modifiers_name['screw'] in m.name:
                                m.steps = m.render_steps = auto_bevel_segments(revolver_obj=o)
                    if o.get('fluent_type') == 'sphere' and (o.get('fluent_auto_res') == 'ENABLE' or not o.get('fluent_auto_res')):
                        if fluent_modifiers_name['screw'] in m.name:
                            screw_2 = o.modifiers[fluent_modifiers_name['screw_2']]
                            screw_2.steps = screw_2.render_steps = auto_bevel_segments(
                                displace=o.modifiers[fluent_modifiers_name['radius']]) / 2
                            screw = o.modifiers[fluent_modifiers_name['screw']]
                            screw.steps = screw.render_steps = screw_2.steps / 3

    width: bpy.props.FloatProperty(
        description="Latest Bevel Width",
        name="Latest bevel width",
        default=0.002,
        min=0.0001,
        step=0.01,
        precision=4,
        update=latestBevelUpdate
    )
    width_amount: bpy.props.StringProperty(
        description="Global factor of width of the latest bevel",
        name="Latest Bevel Global",
        default="1",
        update=latestBevelUniversalUpdate
    )
    corner: bpy.props.FloatProperty(
        description="Default first bevel width",
        name="Default first bevel width",
        default=0,
        min=0,
        max=10,
        step=0.01,
        precision=3
    )
    bevel_width: bpy.props.StringProperty(
        description="Default bevel width",
        name='Default bevel width',
        default=''
    )
    # segments: bpy.props.FloatProperty(
    #     description="Segments of latestest bevel",
    #     name="Segments",
    #     default=4,
    #     min=0,
    #     max=10,
    #     step=0.01,
    #     precision=3
    # )
    bevel_angle_limit: bpy.props.FloatProperty(
        description="Limit angle of the latest bevel",
        name="Limit angle",
        default=35,
        min=0,
        max=180,
        step=1,
        precision=3,
        update=limit_angle_update
    )
    model_resolution: bpy.props.IntProperty(
        description='Resolution of bevels, cylinders and spheres (segments/m)',
        name='Model resolution',
        default=16,
        min=1,
        max=512,
        update=update_resolution
    )
    min_auto_bevel_segments: bpy.props.IntProperty(
        description='Minimum resolution of bevels (segments/m)',
        name='Minimum of segments for auto-bevel',
        default=1,
        min=1,
        max=64,
        update=update_resolution
    )
    min_auto_cylinder_segments: bpy.props.IntProperty(
        description='Minimum resolution of cylinders and spheres (segments/m)',
        name='Minimum of segments for auto-resolution',
        default=16,
        min=3,
        max=64,
        update=update_resolution
    )
    # latest_bevel_segments: bpy.props.IntProperty(
    #     description="Latest Bevel Segments",
    #     name="Latest Bevel Segments",
    #     default=4,
    #     min=0,
    #     max=64,
    #     step=1,
    #     update=latestBevelUpdate
    # )
    depth: bpy.props.FloatProperty(
        description="Default Depth",
        name="Default Depth",
        default=0,
        min=-100,
        max=100,
        step=0.01,
        precision=3
    )
    solidify_offset: bpy.props.FloatProperty(
        description="solidify offset",
        name="solidify_offset",
        default=0,
        min=-1,
        max=1,
        precision=4
    )
    # prism_segments: bpy.props.IntProperty(
    #     description="Default Prism Segment",
    #     name="Default Prism Segment",
    #     default=64,
    #     min=0,
    #     step=1,
    #     update=prismResolutionUpdate
    # )
    # bevel_resolution: bpy.props.IntProperty(
    #     description="Bevel Resolution",
    #     name="Bevel resolution",
    #     default=32,
    #     min=0,
    #     step=1,
    #     update=bevelResolutionUpdate
    # )
    # sphere_segments: bpy.props.IntProperty(
    #     description="Default sphere Segment",
    #     name="Sphere segements",
    #     default=17,
    #     min=0,
    #     step=1,
    #     update=sphereResolutionUpdate
    # )
    bevel_profile: bpy.props.FloatProperty(
        description="Bevel profile",
        name="Bevel profile",
        default=0.50,
        min=0,
        max=1,
        step=0.01,
        update=bevelProfilUpdate
    )
    auto_mirror_x: bpy.props.BoolProperty(
        description="Auto Mirror X",
        name="X",
        default=False
    )
    auto_mirror_y: bpy.props.BoolProperty(
        description="Auto Mirror Y",
        name="Y",
        default=False
    )
    auto_mirror_z: bpy.props.BoolProperty(
        description="Auto Mirror Z",
        name="Z",
        default=False
    )
    straight_bevel: bpy.props.BoolProperty(
        description="straight_bevel",
        name="straight_bevel",
        default=False
    )
    second_bevel_width: bpy.props.FloatProperty(
        description="second_bevel_width",
        name="second_bevel_width",
        default=0,
        min=0,
        max=100
    )
    second_bevel_straight: bpy.props.BoolProperty(
        description="second_bevel_straight",
        name="second_bevel_straight",
        default=False
    )
    grid_resolution: bpy.props.IntProperty(
        description="Default Prism Segment",
        name="Default Prism Segment",
        default=5,
        min=0,
        step=1
    )
    grid_size: bpy.props.FloatProperty(
        description="grid size",
        name="Grid Size",
        default=2,
        min=0,
        step=0.01,
        precision=2
    )
    last_tool: bpy.props.StringProperty(
        description="last toole used",
        name='last_tool',
        default='box'
    )
    plate_bevel_width: bpy.props.FloatProperty(
        description="plate bevel width",
        name="plate_bevel_width",
        default=0
    )
    plate_solidify_thickness: bpy.props.FloatProperty(
        description="plate bevel width",
        name="plate_bevel_width",
        default=0
    )
    centered_array: bpy.props.BoolProperty(
        description="Draw array from the center",
        name="Centered array",
        default=True
    )
    loop_slide: bpy.props.BoolProperty(
        description="Use the loop slide option",
        name="Loop Slide",
        default=False,
        update=loop_slide_update
    )
    outer_bevel_segments: bpy.props.IntProperty(
        description="0 = automatic",
        name="Outer bevel segments",
        default=4,
        min=0,
        step=1,
        update=outer_bevel_update
    )
    screw_scale: bpy.props.FloatProperty(
        description="Head screw scale",
        name="screw_scale",
        default=.1
    )

    screw_offset: bpy.props.FloatProperty(
        description="Head screw offset",
        name="screw_offset",
        default=.1
    )

    anim_speed: bpy.props.IntProperty(
        default= 1,
        name= 'Animation speed'
    )