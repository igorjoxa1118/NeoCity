import bpy
import time
from ... utility import method_handler


class Shader():

    def __init__(self, context, db):

        self.context = context
        self.db = db
        self.handle = None
        self.remove_shader = False

        # Override
        self.draw_shader = True

        # Fade in switches
        # self.fade_in = True
        self.has_faded_for_tab = False
        self.started_fade_out = False

        # Space
        self.active_ui_type = context.area.ui_type
        self.space = bpy.types.SpaceView3D

        if context.area.ui_type in {'GeometryNodeTree', 'ShaderNodeTree'}:
            self.space = bpy.types.SpaceNodeEditor

        self.handle = self.space.draw_handler_add(self.safe_render, (context, ), "WINDOW", "POST_PIXEL")
    

    def safe_render(self, context):
        method_handler(self.draw,
            arguments = (context,),
            identifier = 'UI Framework',
            exit_method = self.remove_handle)


    def draw(self, context):

        if context.area.ui_type != self.active_ui_type:
            return

        # Check for color changes
        # if not self.fade_in and not self.remove_shader:
        #     self.db.colors.check_color_changes()
        if self.remove_shader == False:
            self.db.colors.check_color_changes()

        # # Fade in
        # if self.fade_in == True:
        #     self.fade_in = not self.db.colors.fade_in_colors()

        # Draw fast UI
        if self.draw_shader:
            if self.db.fast_ui.show == True:
                self.db.fast_ui.draw(context)

            # Draw expanded UI
            elif self.db.fast_ui.show == False:

                # Setup for fade in on TAB key switch
                # if self.has_faded_for_tab == False:
                #     self.has_faded_for_tab = True
                #     self.db.colors.capture_start_time = True
                #     self.db.colors.set_colors_alpha_to_zero()
                    # self.fade_in = True

                # Draw the expanded UI
                for key, val in self.db.windows.items():
                    if val.visible:
                        val.draw()

        # Start the fade out
        if self.remove_shader == True:

            # Fade out complete
            if self.db.colors.fade_completed == True:
                self.destroy()

            # Fade out
            else:
                if self.started_fade_out == False:
                    self.started_fade_out = True
                    self.db.colors.capture_start_time = True
                self.db.colors.fade_out_colors()


    def remove_handle(self):
        '''Setup for fading out.'''

        # Start calling fade on colors
        self.remove_shader = True

        # For images
        self.db.ui_event.images_remove = True


    def destroy(self):
        '''Final call to remove the drawing handle.'''

        if self.handle:
            self.handle = self.space.draw_handler_remove(self.handle, "WINDOW")
            return True
        return False
