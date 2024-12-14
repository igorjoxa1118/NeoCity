import bpy

from bpy.types import Panel

from ... utility import addon, tool
from .. property.utility import names
from . utility import preset
from .. import toolbar


class BC_PT_snap(Panel):
    bl_label = 'Snap'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'BoxCutter'


    @classmethod
    def poll(cls, context):
        active = tool.active()
        return active and active.idname == tool.name


    def draw(self, context):
        layout = self.layout
        preference = addon.preference()
        op = toolbar.option()

        snap = preference.snap.enable and True in [preference.snap.grid, preference.snap.verts, preference.snap.edges, preference.snap.faces]
        snap_grid = snap and preference.snap.grid
        # tool = tool.active().operator_properties('bc.shape_draw')

        snap_row = layout.row(align=True)
        snap_row.scale_x = 1.5
        snap_row.scale_y = 1.5

        # row = snap.row(align=True)
        # row.prop(preference.behavior, "pivot_point", text="", icon_only=True)

        row = snap_row.row(align=True)
        row.active = preference.snap.enable

        row = snap_row.row(align=True)
        if not self.is_popover:
            row.prop(preference.snap, 'enable', text='', icon=F'SNAP_O{"N" if preference.snap.enable else "FF"}')
        row.prop(preference.snap, 'incremental', text='', icon='SNAP_INCREMENT')

        sub = row.row(align=True)

        if preference.snap.incremental or snap_grid:
            sub.prop(preference.snap, 'increment', text='')
            sub.prop(preference.snap, 'increment_lock', text='', icon=F'{"" if preference.snap.increment_lock else "UN"}LOCKED')

            if snap_grid:
                sub = row.row(align=True)
                sub.scale_x = 1.2
                sub.popover('BC_PT_grid', text='', icon='SNAP_GRID')

            row = layout.row(align=True)
            row.alignment = 'RIGHT'
            row.scale_x = 1.5
            row.scale_y = 1.5

            sub = row.row(align=True)
            sub.active = preference.snap.enable

            sub.prop(preference.snap, 'grid', text='', icon='SNAP_GRID')
            sub.prop(preference.snap, 'verts', text='', icon='VERTEXSEL')
            sub.prop(preference.snap, 'edges', text='', icon='EDGESEL')
            sub.prop(preference.snap, 'faces', text='', icon='FACESEL')

            if op.shape_type == 'NGON' or preference.behavior.draw_line:
                sub = row.row(align=True)
                sub.separator()
                sub.active = not preference.snap.incremental or not preference.snap.increment_lock
                sub.prop(preference.snap, 'angle_lock', text='', icon='DRIVER_ROTATIONAL_DIFFERENCE')

            row = layout.row(align=True)
            row.scale_x = 1.22
            row.scale_y = 1.5

            row.label(text='Static')
            row.prop(preference.snap, 'static_grid', text='', icon='MESH_GRID')
            dot_icon = 'LIGHTPROBE_GRID' if bpy.app.version < (4, 1) else 'LIGHTPROBE_VOLUME'
            row.prop(preference.snap, 'static_dot', text='', icon=dot_icon)

            layout.separator()

        else:
            subsub = sub.row(align=True)
            subsub.active = preference.snap.enable

            separators = 10 if op.shape_type != 'NGON' else 6
            for _ in range(2 if not self.is_popover else separators):
                subsub.separator()

            subsub.prop(preference.snap, 'grid', text='', icon='SNAP_GRID')
            subsub.prop(preference.snap, 'verts', text='', icon='VERTEXSEL')
            subsub.prop(preference.snap, 'edges', text='', icon='EDGESEL')
            subsub.prop(preference.snap, 'faces', text='', icon='FACESEL')

            if op.shape_type == 'NGON' or preference.behavior.draw_line: # or op.shape_type == 'BOX' and preference.behavior.draw_line:
                sub.separator()
                sub.prop(preference.snap, 'angle_lock', text='', icon='DRIVER_ROTATIONAL_DIFFERENCE')

            if snap:
                row = layout.row(align=True)
                row.scale_x = 1.22
                row.scale_y = 1.5

                row.label(text='Static')
                row.prop(preference.snap, 'static_grid', text='', icon='MESH_GRID')
                dot_icon = 'LIGHTPROBE_GRID' if bpy.app.version < (4, 1) else 'LIGHTPROBE_VOLUME'
                row.prop(preference.snap, 'static_dot', text='', icon=dot_icon)

                layout.separator()

        row = layout.row()
        self.label_row(row, preference.snap, 'mesh_element')
        row.prop(preference.snap, 'mesh_element_exact', text='')

        if op.shape_type == 'NGON':
            self.label_row(layout.row(), preference.snap, 'ngon_angle', label='Ngon Angle')
            self.label_row(layout.row(), preference.snap, 'ngon_previous_edge')

        # elif op.shape_type == 'BOX' and preference.behavior.draw_line:
        elif preference.behavior.draw_line:
            self.label_row(layout.row(), preference.snap, 'draw_line_angle')

        self.label_row(layout.row(), preference.snap, 'rotate_angle', 'Rotate Angle')

        layout.separator()

        if snap:
            if snap_grid:
                # self.label_row(layout.row(), preference.snap, 'grid_type', 'Grid Type')

                if preference.snap.static_grid:
                    self.label_row(layout.row(), preference.display, 'grid_mode')
                    self.label_row(layout.row(), preference.snap, 'toggle_ortho_grid', 'Toggle Grid Overlay')
                    self.label_row(layout.row(), preference.snap, 'toggle_floor', 'Toggle Floor Overlay')
                    self.label_row(layout.row(), preference.snap, 'front_draw', 'Always in Front')
                    self.label_row(layout.row(), preference.snap, 'auto_transparency', 'Auto Transparency')

                # else:
                #     self.label_row(layout.row(), preference.snap, 'adaptive', 'Adaptive')
            else:
                # self.label_row(layout.row(), preference.snap, 'dot_type', 'Dot Type')

                if preference.snap.static_dot:
                    self.label_row(layout.row(), preference.snap, 'dot_dot_snap', 'Dot to Dot Snap')
                    self.label_row(layout.row(), preference.snap, 'dot_show_subdivision', 'Subdivision Preview')
                    self.label_row(layout.row(), preference.snap, 'dot_alt_draw', 'Alt Draw')
                    self.label_row(layout.row(), preference.snap, 'dot_preview', 'Alignment Preview')
                    self.label_row(layout.row(), preference.snap, 'dot_preview_scale', 'Preview scale')

            if (not preference.snap.static_dot and not snap_grid) or (snap_grid and not preference.snap.static_grid):
                layout.separator()
                row = layout.row()
                row.alignment = 'CENTER'
                row.label(text='Fade Timing')
                layout.separator()

                if not preference.snap.static_grid and snap_grid:
                    row = layout.row(align=True)
                    self.label_row(row, preference.display, 'grid_fade_time_in', 'Grid')
                    row.prop(preference.display, 'grid_fade_time_out', text='')

                if not preference.snap.static_dot:
                    row = layout.row(align=True)
                    self.label_row(row, preference.display, 'dot_fade_time_in', 'Dot')
                    row.prop(preference.display, 'dot_fade_time_out', text='')


    def label_row(self, row, path, prop, label=''):
        if prop in {'draw_line_angle', 'ngon_angle', 'rotate_angle'}:
            column = self.layout.column(align=True)
            row = column.row(align=True)

        row.label(text=label if label else names[prop])
        row.prop(path, prop, text='')

        values = {
            'draw_line_angle': preset.line_angle,
            'ngon_angle': preset.angle,
            'rotate_angle': preset.angle}

        if prop in {'draw_line_angle', 'ngon_angle', 'rotate_angle'}:
            row = column.row(align=True)
            split = row.split(factor=0.48, align=True)
            sub = split.row(align=True)
            sub = split.row(align=True)

            # pointer = '.shape.' if prop == 'ngon_snap_angle' else '.shape.'
            pointer = '.snap.'
            for value in values[prop]:
                ot = sub.operator('wm.context_set_int', text=str(value))
                ot.data_path = F'preferences.addons[\"{__name__.partition(".")[0]}\"].preferences{pointer}{prop}'
                ot.value = value
