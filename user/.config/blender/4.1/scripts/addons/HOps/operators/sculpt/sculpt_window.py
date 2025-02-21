import bpy
from ... utils.addons import addon_exists
from ... ui_framework.master import Master
from ... utility import addon
from ... utility.base_modal_controls import Base_Modal_Controls


class Brush_Form:

    def __init__(self):
        self.name = ""
        self.hot_key_display = ""
        self.call_args = None
        self.call_back = None


class HOPS_OT_Sculpt_Ops_Window(bpy.types.Operator):
    """Sculpt Ops Window"""
    bl_idname = "view3d.sculpt_ops_window"
    bl_label = "Sculpt Ops Window"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = """Sculpt Ops"""


    @classmethod
    def poll(cls, context):
        if context.active_object != None:
            if context.active_object.type == 'MESH':
                return True
        return False


    def invoke(self, context, event):

        if context.mode != 'SCULPT':
            bpy.ops.object.mode_set(mode='SCULPT', toggle=False)

        self.exit = False
        self.brushes = []

        # KEY -> Name of brush to call on self.set_op_call
        # VAL -> HotkeyDisplay, Location, Shift, Ctrl, Keys

        self.builtin_brushes = {
            'Draw Sharp'         : ['1',        'builtin_brush', False, False, {'NUMPAD_1', 'ONE'}],
            'Clay'               : ['C',        'builtin_brush', False, False, {'C'}],
            'Clay Thumb'         : ['3',        'builtin_brush', False, False, {'NUMPAD_3', 'THREE'}],
            'Layer'              : ['L',        'builtin_brush', False, False, {'L'}],
            'Blob'               : ['4',        'builtin_brush', False, False, {'NUMPAD_4', 'FOUR'}],
            'Crease'             : ['Shift C',  'builtin_brush', True,  False, {'C'}],
            'Smooth'             : ['S',        'builtin_brush', False, False, {'S'}],
            'Flatten'            : ['Shift T',  'builtin_brush', True,  False, {'T'}],
            'Fill'               : ['5',        'builtin_brush', False, False, {'NUMPAD_5', 'FIVE'}],
            'Multi-plane Scrape' : ['7',        'builtin_brush', False, False, {'NUMPAD_7', 'SEVEN'}],
            'Elastic Deform'     : ['8',        'builtin_brush', False, False, {'NUMPAD_8', 'EIGHT'}],
            'Snake Hook'         : ['K',        'builtin_brush', False, False, {'K'}],
            'Thumb'              : ['9',        'builtin_brush', False, False, {'NUMPAD_9', 'NINE'}],
            'Pose'               : ['0',        'builtin_brush', False, False, {'NUMPAD_0', 'ZERO'}],
            'Nudge'              : ['Shift 1',  'builtin_brush', True,  False, {'NUMPAD_1', 'ONE'}],
            'Rotate'             : ['Shift 2',  'builtin_brush', True,  False, {'NUMPAD_2', 'TWO'}],
            'Slide Relax'        : ['Shift 3',  'builtin_brush', True,  False, {'NUMPAD_3', 'THREE'}],
            'Mask'               : ['Shift 6',  'builtin_brush', True,  False, {'NUMPAD_6', 'SIX'}],
            'Draw Face Sets'     : ['Shift 7',  'builtin_brush', True,  False, {'NUMPAD_7', 'SEVEN'}],
            'box_mask'           : ['B',        'builtin',       False, False, {'B'}],
            'box_hide'           : ['Shift 9',  'builtin',       True,  False, {'NUMPAD_9', 'NINE'}],
            'Clay Strips'        : ['2',        'builtin_brush', False, False, {'NUMPAD_2', 'TWO'}],
            'Cloth'              : ['Shift 4',  'builtin_brush', True,  False, {'NUMPAD_4', 'FOUR'}],
            'Draw'               : ['X',        'builtin_brush', False, False, {'X'}],
            'Grab'               : ['G',        'builtin_brush', False, False, {'G'}],
            'Pinch'              : ['P',        'builtin_brush', False, False, {'P'}],
            'Scrape'             : ['6',        'builtin_brush', False, False, {'NUMPAD_6', 'SIX'}],
            'Inflate'            : ['I',        'builtin_brush', False, False, {'I'}],
            'mesh_filter'        : ['Shift 0',  'builtin',       True,  False, {'NUMPAD_0', 'ZERO'}],
            'cloth_filter'       : ['Y',        'builtin',       True,  False, {'Y'}],
            'Simplify'           : ['Shift 5',  'builtin_brush', True,  False, {'NUMPAD_5', 'FIVE'}],
            'move'               : ['Ctrl 1',   'builtin',       False, True,  {'NUMPAD_1', 'ONE'}],
            'rotate'             : ['R',        'builtin',       False, False, {'R'}],
            'scale'              : ['Ctrl 2',   'builtin',       False, True,  {'NUMPAD_2', 'TWO'}],
            'transform'          : ['T',        'builtin',       False, False, {'T'}],
            'lasso_mask'         : ['Shift B',  'builtin',       True,  False, {'B'}],
            'annotate'           : ['D',        'builtin',       False, False, {'D'}]
            }

        for key, val in self.builtin_brushes.items():
            brush_form = Brush_Form()
            brush_form.name = key.replace('_', ' ').title()
            brush_form.hot_key_display = val[0]
            brush_form.call_args = (val[1], key)
            brush_form.call_back = self.set_op_call
            self.brushes.append(brush_form)

        # Operations
        self.ops = [
            ['Toggle Floor', self.toggle_floor, None],
            ['Toggle Dyno', self.toggle_dyno, None],
            ['Hide Unselected', self.hide_unselected, None],
            ['Unhide All', self.unhide, None]
        ]

        # Base Systems
        self.master = Master(context=context, custom_preset="brush_ops", show_fast_ui=False)
        self.base_controls = Base_Modal_Controls(context, event)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


    def modal(self, context, event):

        if self.exit == True:
            self.master.run_fade()
            return {'FINISHED'}        

        #######################
        #   Base Systems
        #######################

        self.master.receive_event(event=event)
        self.base_controls.update(context, event)

        #######################
        #   Base Controls
        #######################

        if self.base_controls.pass_through:
            if not self.master.is_mouse_over_ui():
                return {'PASS_THROUGH'}
        elif self.base_controls.cancel:
            if not self.master.is_mouse_over_ui():
                self.master.run_fade()
                return {'CANCELLED'}
        elif self.base_controls.confirm:
            if not self.master.is_mouse_over_ui():
                self.master.run_fade()
                return {'FINISHED'}

        #######################
        #   Brush Events
        #######################
        if event.type != 'TIMER':
            for key, val in self.builtin_brushes.items():
                if event.value == 'PRESS':
                    if event.type in val[4]:
                        if event.shift == val[2]:
                            if event.ctrl == val[3]:
                                self.set_op_call(val[1], key)
                                break

        self.draw_window(context=context)
        context.area.tag_redraw()
        return {'RUNNING_MODAL'}


    def draw_window(self, context):

        self.master.setup()

        menus = {
            'brushes' : self.brushes,
            'header' : [self.toggle_modes, (context,)],
            'ops' : self.ops
        }

        self.master.receive_main(win_dict=menus)
        self.master.finished()


    def set_op_call(self, location="", brush_name=""):
        '''Calls the wm op and tells modal to exit.'''

        call_string = f"{location}.{brush_name}"
        bpy.ops.wm.tool_set_by_id('INVOKE_DEFAULT', name=call_string)
        self.exit = True


    def toggle_modes(self, context):

        if context.mode == 'SCULPT':
            bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
        else:
            bpy.ops.object.mode_set(mode='SCULPT', toggle=False)

    ########################
    #   Operations
    ########################

    def toggle_floor(self):
        if bpy.context.space_data.overlay.show_floor == True:
            bpy.context.space_data.overlay.show_floor = False
            bpy.context.space_data.overlay.show_axis_x = False
            bpy.context.space_data.overlay.show_axis_y = False
        else:
            bpy.context.space_data.overlay.show_floor = True
            bpy.context.space_data.overlay.show_axis_x = True
            bpy.context.space_data.overlay.show_axis_y = True


    def toggle_dyno(self):
        bpy.ops.sculpt.dynamic_topology_toggle()


    def hide_unselected(self):
        bpy.ops.object.hide_view_set(unselected=True)


    def unhide(self):
        bpy.ops.object.hide_view_clear()


