import bpy
from bpy.props import EnumProperty
from . utility import options, draw_panel, init_panels
from ... utility import addon
from ... utils.blender_ui import get_dpi_factor
from ... import bl_info
from .. draw import workflow, sharpening, opt_ins, booleans, mesh, bevel, general


class HOPS_OT_helper(bpy.types.Operator):
    bl_idname = 'hops.helper'
    bl_label = 'HOps Helper '
    bl_description = f'''Display HOps Helper - {bl_info['version'][0]}.{bl_info['version'][1]}.{bl_info['version'][2]}.{bl_info['version'][3]}
    
    HOPS Helper gives access to most things essential to the #b3d experience.
    Modifiers, materials and workflow options are available here.
    *protip: use the hotkey*
    
    '''

    bl_options = {'UNDO'}

    panels: dict = {}
    label: bool = False


    @classmethod
    def poll(cls, context): # need a poll for panel lookup
        return True


    def check(self, context):
        return True


    def invoke(self, context, event):
        preference = addon.preference().ui

        if options().context == '':
            options().context = 'TOOL'

        if preference.use_helper_popup:
            self.label = True
            return context.window_manager.invoke_popup(self, width=int(preference.Hops_helper_width * get_dpi_factor(force=False)))
        else:
            return context.window_manager.invoke_props_dialog(self, width=int(preference.Hops_helper_width * get_dpi_factor(force=False)))

    def execute(self, context):
        return {'FINISHED'}


    def draw(self, context):
        layout = self.layout
        option = options()

        if options().context == '':
            options().context = 'TOOL'

        if self.label:
            layout.label(text='HOps Helper')

        split = layout.split(factor=0.1, align=True)

        column = split.column(align=True)
        column.scale_y = 1.25
        column.prop(option, 'context', expand=True, icon_only=True)

        column = split.column()

        init_panels(self)

        if options().context != 'TOOL':
            for pt in self.panels[option.context]:
                draw_panel(self, pt, column)
        else:
            if context.active_object:
                draw_box(column, 'general', 'General', general.draw, context)
            draw_box(column, 'workflow', 'Workflow', workflow.draw, context)
            draw_box(column, 'sharp', 'Sharpening / Shading', sharpening.draw, context)
            draw_box(column, 'mesh', 'Mesh Clean / Dice', mesh.draw, context)
            draw_box(column, 'bevel', 'Bevel / Operators', bevel.draw, context)
            draw_box(column, 'booleans', 'Booleans', booleans.draw, context)
            draw_box(column, 'opt_ins', 'Opt In / Out', opt_ins.draw, context)


def draw_box(column, expand_prop, label_text, draw_func, context):
    box = column.box()
    row = box.row(align=True)
    row.alignment = 'LEFT'
    helper = bpy.context.window_manager.hardflow.helper
    expand = getattr(helper, expand_prop)
    row.prop(helper, expand_prop, text='', icon=f'DISCLOSURE_TRI_{"DOWN" if expand else "RIGHT"}', emboss=False)

    row.prop(helper, expand_prop, toggle=True, text=label_text, emboss=False)
    sub = row.row(align=True)
    sub.scale_x = 0.70
    sub.prop(helper, expand_prop, toggle=True, text='   ', emboss=False)

    if expand:
        content_col = box.column(align=True)
        draw_func(content_col, context)
