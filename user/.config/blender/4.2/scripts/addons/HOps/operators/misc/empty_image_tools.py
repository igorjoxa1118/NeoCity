import bpy
from bpy.props import *
from bpy_extras import view3d_utils
from mathutils import Vector
from ... utils.objects import get_current_selected_status
from ... utils.blender_ui import get_dpi, get_dpi_factor
from ... graphics.drawing2d import set_drawing_dpi
from ... utility import addon


class HOPS_OT_EmptyToImageOperator(bpy.types.Operator):
    bl_idname = "hops.set_empty_image"
    bl_label = "Convert empty object to image"
    bl_description = "Convert empty object to image"
    bl_options = {"REGISTER", "UNDO"}

    img : bpy.props.StringProperty()

    def execute(self, context):

        active_object, other_objects, other_object = get_current_selected_status()
        active_object.empty_display_type = 'IMAGE'
        if self.img in bpy.data.images:
            active_object.data = bpy.data.images[self.img]

        return {"FINISHED"}


class HOPS_OT_CenterEmptyOperator(bpy.types.Operator):
    bl_idname = "hops.center_empty"
    bl_label = "Center image"
    bl_description = "Center the image on the empty"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):

        active_object, other_objects, other_object = get_current_selected_status()
        active_object.empty_image_offset = [-0.5, -0.5]

        return {"FINISHED"}


class HOPS_OT_EmptyTransparencyModal(bpy.types.Operator):
    bl_idname = "hops.empty_transparency_modal"
    bl_label = "Change Transparency"
    bl_description = "Modal operator to set the transparency of the image"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):

        # centerX, centerY = context.region.width / 2, context.region.height / 2
        # self.active_object.color[3] = min(self.rx / centerX, 1)
        return {'FINISHED'}

    def modal(self, context, event):

        if event.type == 'MOUSEMOVE':  # Apply
            centerX, centerY = context.region.width / 2, context.region.height / 2

            self.rx = event.mouse_region_x
            self.ry = event.mouse_region_y

            self.active_object.color[3] = min(self.rx / centerX, 1)

            self.report({'INFO'}, F'Transparency set to: {round(self.active_object.color[3], 2)}')
            return {'RUNNING_MODAL'}
            # self.execute(context)

        elif event.type == 'LEFTMOUSE':  # Confirm

            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:  # Cancel

            self.active_object.color[3] = self.init_value
            # self.finish()

            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        self.active_object, self.other_objects, self.other_object = get_current_selected_status()
        bpy.context.object.use_empty_image_alpha = True
        self.init_value = self.active_object.color[3]
        self.rx = event.mouse_region_x
        self.ry = event.mouse_region_y
        self.start_mouse_position = Vector((self.rx, self.ry))

        self.active_object.use_empty_image_alpha = True

        # args = (context, )
        # self.draw_handler = bpy.types.SpaceView3D.draw_handler_add(self.draw, args, "WINDOW", "POST_PIXEL")
        self.execute(context)
        context.window_manager.modal_handler_add(self)

        return {'RUNNING_MODAL'}

    def finish(self):
        # bpy.types.SpaceView3D.draw_handler_remove(self.draw_handler, "WINDOW")
        return {"FINISHED"}


class HOPS_OT_EmptyOffsetModal(bpy.types.Operator):
    bl_idname = "hops.empty_position_modal"
    bl_label = "Change Offset"
    bl_description = "Modal operator to set the offset of the image"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):

        region = bpy.context.region
        region3D = bpy.context.space_data.region_3d
        view_vector = view3d_utils.region_2d_to_vector_3d(region, region3D, self.mouse_pos)
        self.loc = view3d_utils.region_2d_to_location_3d(region, region3D, self.mouse_pos, view_vector)
        self.loc = self.active_object.matrix_world.inverted() @ self.loc
        self.active_object.empty_image_offset[0] = self.loc[0]/4
        self.active_object.empty_image_offset[1] = self.loc[1]/4
        #  self.active_object.empty_image_offset[1] = self.loc[1] * 1.5


    def modal(self, context, event):

        if event.type == "H" and event.value == "PRESS":
            addon.preference().property.hops_modal_help = not addon.preference().property.hops_modal_help

        if event.type == 'MOUSEMOVE':  # Apply
            self.rx = event.mouse_region_x
            self.ry = event.mouse_region_y
            self.mouse_pos = Vector((self.rx, self.ry))
            self.execute(context)

        elif event.type == 'LEFTMOUSE':  # Confirm
            return self.finish()

        elif event.type == 'C':  # Center
            bpy.ops.hops.center_empty()
            self.loc = Vector((0, 0, 0))

        elif event.type in {'RIGHTMOUSE', 'ESC'}:  # Cancel
            self.active_object.empty_image_offset = self.init_value
            self.finish()
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):

        self.active_object, self.other_objects, self.other_object = get_current_selected_status()
        self.init_value = Vector(self.active_object.empty_image_offset)
        self.rx = event.mouse_region_x
        self.ry = event.mouse_region_y
        self.mouse_pos = Vector((self.rx, self.ry))
        self.start_mouse_position = Vector((self.rx, self.ry))
        self.loc = Vector((0, 0, 0))

        args = (context, )
        #self.draw_handler = bpy.types.SpaceView3D.draw_handler_add(self.draw, args, "WINDOW", "POST_PIXEL")
        self.execute(context)
        context.window_manager.modal_handler_add(self)

        return {'RUNNING_MODAL'}

    def finish(self):
        #bpy.types.SpaceView3D.draw_handler_remove(self.draw_handler, "WINDOW")
        return {"FINISHED"}