import bpy
import blf
import time

class HOPS_OT_Timer(bpy.types.Operator):
    bl_idname = "hops.timer"
    bl_label = "Hops Timer"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Draw 3D timer"

    _timer: float = None
    _start_time: float = None
    _handle: int = None
    _fade_start_time: float = None
    _fade_alpha: float = 1.0
    _time_stop: float = 0.0

    # Poperty updates
    def timer_position_x_upd(self, context):
        HOPS_OT_Timer._timer_position_x = self.timer_position_x

    def timer_position_y_upd(self, context):
        HOPS_OT_Timer._timer_position_y = self.timer_position_y

    def timer_text_size_upd(self, context):
        HOPS_OT_Timer._timer_text_size = self.timer_text_size

    def timer_fade_time_upd(self, context):
        HOPS_OT_Timer._timer_fade_time = self.timer_fade_time

    def timer_text_color_upd(self, context):
        HOPS_OT_Timer._timer_text_color = self.timer_text_color
    # Properties

    timer_position_x: bpy.props.IntProperty(name="X Position", default=37, min=0, max=100, update=timer_position_x_upd)
    timer_position_y: bpy.props.IntProperty(name="Y Position", default=86, min=0, max=100, update=timer_position_y_upd)
    timer_text_size: bpy.props.IntProperty(name="Text Size", default=120, min=10, update=timer_text_size_upd)
    timer_fade_time: bpy.props.FloatProperty(name="Fade Time", default=3.0, min=0.1, max=10.0, update=timer_fade_time_upd)
    timer_text_color: bpy.props.FloatVectorProperty(name="Text Color", subtype='COLOR', default=(1.0, 1.0, 1.0), min=0.0, max=1.0, update=timer_text_color_upd)

    _timer_position_x = 50
    _timer_position_y = 50
    _timer_text_size = 120
    _timer_fade_time = 3.0
    _timer_text_color = [1.0, 1.0, 1.0]

    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'timer_position_x', slider=True)
        layout.prop(self, 'timer_position_y', slider=True)
        layout.prop(self, 'timer_text_size')
        layout.prop(self, 'timer_fade_time')
        layout.prop(self, 'timer_text_color')

    def execute(self, context):
        return {'FINISHED'}

    def modal(self, context, event):
        if event.type == 'ESC' and event.value == 'PRESS':
            context.scene.hops.timer_running = False

        if event.type == 'TIMER':
            if context.area:
                context.area.tag_redraw()
            else:
                self.cancel(context)
                return {'CANCELLED'}

        if not context.scene.hops.timer_running:
            if self._fade_start_time is None:
                self._fade_start_time = time.time()
            else:
                elapsed_fade_time = time.time() - self._fade_start_time
                self._fade_alpha = max(0.0, 1.0 - elapsed_fade_time / self.__class__._timer_fade_time)
                if self._fade_alpha <= 0.0:
                    self.cancel(context)
                    return {'CANCELLED'}

        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        if event.ctrl:
            return context.window_manager.invoke_props_dialog(self)

        if context.scene.hops.timer_running:
            context.scene.hops.timer_running = False
            return {'CANCELLED'}

        self.__class__._timer_position_x = self.timer_position_x
        self.__class__._timer_position_y = self.timer_position_y
        self.__class__._timer_text_size = self.timer_text_size
        self.__class__._timer_fade_time = self.timer_fade_time
        self.__class__._timer_text_color = self.timer_text_color

        context.scene.hops.timer_running = True
        self._start_time = time.time()
        self._fade_start_time = None
        self._fade_alpha = 1.0
        self._timer = context.window_manager.event_timer_add(0.01, window=context.window)
        self._handle = bpy.types.SpaceView3D.draw_handler_add(self.draw_timer, (context,), 'WINDOW', 'POST_PIXEL')
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        if self._handle is not None:
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
        if self._timer is not None:
            context.window_manager.event_timer_remove(self._timer)
        if context.area: context.area.tag_redraw()
        return None

    def draw_timer(self, context):
        if self._fade_start_time is None:
            elapsed_time = time.time() - self._start_time
            time_text = "{:.2f}".format(elapsed_time)
            self._time_stop = elapsed_time
        else:
            time_text = "{:.2f}".format(self._time_stop)

        # Set position and size
        region = context.region
        width = region.width
        height = region.height
        x = width * (self.__class__._timer_position_x / 100)
        y = height * (self.__class__._timer_position_y / 100)

        # Draw the text with GPU shaders
        font_id = 0
        blf.position(font_id, x, y, 0)
        blf.size(font_id, self.__class__._timer_text_size)
        blf.enable(font_id, blf.SHADOW)
        blf.shadow(font_id, 5, 0, 0, 0, self._fade_alpha * 1)
        blf.color(font_id, *self.__class__._timer_text_color, self._fade_alpha * 0.3)
        blf.draw(font_id, time_text)
