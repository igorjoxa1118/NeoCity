import bpy


def shade_smooth():
    if bpy.app.version[:2] > (3, 2):
        dic = {}
        for obj in bpy.context.selected_objects:
            dic[obj] = (obj.data.use_auto_smooth, obj.data.auto_smooth_angle)
        bpy.ops.object.shade_smooth()
        for obj in bpy.context.selected_objects:
            obj.data.use_auto_smooth = dic[obj][0]
            obj.data.auto_smooth_angle = dic[obj][1]
    else:
        bpy.ops.object.shade_smooth()
