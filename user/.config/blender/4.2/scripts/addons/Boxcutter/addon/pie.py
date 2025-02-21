import bpy

from bpy.types import Menu
from bpy.utils import register_class, unregister_class

from .. utility import addon, tool
from . import icon
from . import toolbar


class BC_MT_pie(Menu):
    bl_label = 'BoxCutter'

    @classmethod
    def poll(cls, context):
        active = tool.active()
        return active and active.idname == tool.name


    def draw(self, context):
        preference = addon.preference()
        op = toolbar.option()
        bc = context.scene.bc

        layout = self.layout.menu_pie()

        if preference.display.simple_pie:
            self.simple_pie(context, layout, preference, op, bc)

            return

        self.pie(context, layout, preference, op, bc)


    def simple_pie(self, context, layout, preference, op, bc):
        layout.operator('bc.circle', icon='MESH_CIRCLE')

        if op.shape_type == 'NGON':
            layout.prop(preference.shape, 'wedge', text='Wedge')
        else:
            layout.prop(preference.shape, 'wedge', text='Wedge')

        layout.operator('bc.ngon', icon='MOD_SIMPLIFY')
        if op.shape_type == 'NGON':
            layout.prop(preference.shape, 'cyclic', text='Cyclic')
        else:
            layout.prop(preference.behavior, 'draw_line', text='Draw Line')

        layout.separator()

        if op.shape_type == 'BOX':
            layout.prop(preference.shape, 'box_grid', text='Grid')
        elif op.shape_type == 'NGON':
            layout.prop(preference.shape, 'lasso', text='Lasso')
        else:
            layout.separator()

        layout.operator('bc.box', icon='MESH_PLANE')

        layout.operator('bc.custom', icon='FILE_NEW')



    def pie(self, context, layout, preference, op, bc):
        # op = None
        # for tool in context.workspace.tools:
        #     if tool.idname == tool.name and tool.mode == tool.active().mode:
        #         op = tool.operator_properties('bc.shape_draw')

        if op.shape_type != 'CIRCLE':
            layout.operator('bc.circle', icon='MESH_CIRCLE')
        else:
            layout.operator('bc.custom', icon='FILE_NEW')

        layout.separator()

        if op.shape_type != 'NGON':
            layout.operator('bc.ngon', icon='MOD_SIMPLIFY')
        else:
            layout.operator('bc.custom', icon='FILE_NEW')

        row = layout.row(align=True)
        row.scale_x = 1.5
        row.scale_y = 1.5

        icons = {
            'CUT': icon.id('red'),
            'SLICE': icon.id('yellow'),
            'INTERSECT': icon.id('orange'),
            'INSET': icon.id('purple'),
            'JOIN': icon.id('green'),
            'KNIFE': icon.id('blue'),
            'EXTRACT': icon.id('black'),
            'MAKE': icon.id('grey')}

        row.popover(panel='BC_PT_helper', text='', icon_value=icons[op.mode])
        # row.popover(panel='BC_PT_mode', text='', icon_value=icons[op.mode])
        # row.separator()

        icons = {
            'MOUSE': 'RESTRICT_SELECT_OFF',
            'CENTER': 'SNAP_FACE_CENTER',
            'BBOX': 'PIVOT_BOUNDBOX',
            'ACTIVE': 'PIVOT_ACTIVE'}

        row.popover(panel='BC_PT_set_origin', text='', icon=icons[preference.behavior.set_origin])
        row.separator()

        icons = {
            'OBJECT': 'OBJECT_DATA',
            'VIEW': 'LOCKVIEW_ON',
            'CURSOR': 'PIVOT_CURSOR',
            'WORLD': 'WORLD'}

        row.popover(panel='BC_PT_surface', text='', icon=icons[preference.surface])
        row.separator()

        row.prop(preference.snap, 'enable', text='', icon=F'SNAP_O{"N" if preference.snap.enable else "FF"}')
        row.prop(preference.snap, 'grid', text='', icon='SNAP_GRID')
        row.popover('BC_PT_snap', text='', icon='SNAP_INCREMENT')
        row.separator()

        row.popover(panel='BC_PT_settings', text='', icon='PREFERENCES')
        row.prop(op, 'live', text='', icon='PLAY' if not op.live else 'PAUSE')

        sub = row.row(align=True)
        sub.scale_x = 0.9
        sub.label(text=' ')

        layout.separator()
        row = layout.row()

        sub = row.row()
        sub.scale_x = 0.4
        for _ in range(4):
            sub.separator()

        column = row.column(align=True)
        column.scale_x = 1.1
        column.scale_y = 1.5

        for _ in range(6):
            column.label(text=' ')

        column.prop(bc, 'start_operation', text='', expand=True, icon_only=True)

        icons = {
            'NONE': 'LOCKED',
            'DRAW': 'GREASEPENCIL',
            'EXTRUDE': 'ORIENTATION_NORMAL',
            'OFFSET': 'MOD_OFFSET',
            'MOVE': 'RESTRICT_SELECT_ON',
            'ROTATE': 'DRIVER_ROTATIONAL_DIFFERENCE',
            'SCALE': 'FULLSCREEN_EXIT',
            'ARRAY': 'MOD_ARRAY',
            'SOLIDIFY': 'MOD_SOLIDIFY',
            'BEVEL': 'MOD_BEVEL',
            'DISPLACE': 'MOD_DISPLACE',
            'MIRROR': 'MOD_MIRROR',
            'TAPER': 'FULLSCREEN_ENTER',
            'GRID': 'MOD_LATTICE'}

        column.popover(panel='BC_PT_operation', text='', icon=icons[op.operation])
        column.separator()

        column.prop(op, 'origin', icon_only=True)

        if op.shape_type != 'BOX':
            layout.operator('bc.box', icon='MESH_PLANE')
        else:
            layout.operator('bc.custom', icon='FILE_NEW')


classes = [
    BC_MT_pie]


def register():

    for cls in classes:
        register_class(cls)


def unregister():

    for cls in classes:
        unregister_class(cls)
