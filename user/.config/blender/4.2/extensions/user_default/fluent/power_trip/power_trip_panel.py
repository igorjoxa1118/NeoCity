import bpy

from ..Tools.translation import translate
from ..Tools.helper import *

class FLUENT_PT_PowerTrip_Panel(bpy.types.Panel):
    "Fluent tool box"
    bl_label = "Power Trip"
    bl_name = "Power Trip"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = 'Fluent'
    bl_parent_id = "FLUENT_PT_Basic_Panel"

    def draw(self, context):
        icons = load_icons()
        wire_ico = icons.get("wire").get('previews')
        pipe_ico = icons.get("pipe").get('previews')
        plate_ico = icons.get("plate").get('previews')
        grid_ico = icons.get("grid").get('previews')
        cloth_ico = icons.get("cloth").get('previews')
        screw_ico = icons.get("screw").get('previews')

        layout = self.layout
        box = layout.column(align=True)
        line_01 = box.row(align=True)
        line_01.scale_x = 1.2
        line_01.scale_y = 1.5
        line_01.operator("fluent.plates", text=translate('plate'), icon_value=plate_ico.icon_id)
        line_01.operator("fluent.grids", text=translate('grid'), icon_value=grid_ico.icon_id).operation = 'ADD'
        line_01.operator("fluent.screw", text=translate('screws'), icon_value=screw_ico.icon_id).operation = 'ADD'

        line_02 = box.row(align=True)
        line_02.scale_x = 1.2
        line_02.scale_y = 1.5
        line_02.operator("fluent.wire", text=translate('wire'), icon_value=wire_ico.icon_id).operation = 'ADD'
        line_02.operator("fluent.pipe", text=translate('pipe'), icon_value=pipe_ico.icon_id).operation = 'ADD'

        line_03 = box.row(align=True)
        line_03.scale_x = 1.2
        line_03.scale_y = 1.5
        line_03.operator("fluent.clothpanel", text=translate('cloth'), icon_value=cloth_ico.icon_id)
        line_03.operator("fluent.clothsettings", text=translate('clothSettings'))

classes = FLUENT_PT_PowerTrip_Panel