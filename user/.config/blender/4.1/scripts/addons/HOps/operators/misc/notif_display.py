import bpy
import bmesh

from bpy.props import StringProperty

from ... utility import addon
from ...ui_framework.operator_ui import Master


class HOPS_OT_DisplayNotification(bpy.types.Operator):
    bl_idname = "hops.display_notification"
    bl_label = 'Display Notification'
    bl_options = {'INTERNAL'}

    called_ui = False

    info: StringProperty(default='Insert Notification Here') 
    subtext: StringProperty(default='Default Subtext')

    name: StringProperty(default='NoName')

    def __init__(self):
        HOPS_OT_DisplayNotification.called_ui = False


    def execute(self, context):
        if not HOPS_OT_DisplayNotification.called_ui:
            HOPS_OT_DisplayNotification.called_ui = True

            ui = Master()

            draw_data = [
                [self.info]
                ]

            if self.subtext != 'Default Subtext':
                draw_data.insert(1, [self.subtext])

            if self.name != 'NoName' or '': 
                draw_data.insert(-2, [self.name])

            ui.receive_draw_data(draw_data=draw_data)
            ui.draw(draw_bg=addon.preference().ui.Hops_operator_draw_bg, draw_border=addon.preference().ui.Hops_operator_draw_border)

        return {'FINISHED'}
