import bpy
import bmesh
from ... utils.modifiers import apply_modifiers, remove_modifiers
from ... utils.objects import set_active
from ... utility import addon


class HOPS_OT_CutIn(bpy.types.Operator):
    bl_idname = "hops.cut_in"
    bl_label = "Cut In"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = """LMB - Destructively cuts into the primary mesh using the secondary mesh. Respects marking
Shift + LMB - Takes TWO meshes, applies modifiers and separates their intesection into sepaarate object
"""

    @classmethod
    def poll(cls, context):
        if len(cls.get_cutter_objects()) == 0: return False
        if getattr(context.active_object, "type", "") != "MESH": return False
        if getattr(context.active_object, "mode", "") != "OBJECT": return False
        return getattr(context.active_object, "type", "") == "MESH"

    def draw(self, context):
        layout = self.layout

    def invoke(self, context, event):
        self.merge = True if event.shift else False

        return self.execute(context)

    def execute(self, context):

        if self.merge:
            self.merge_in(context)
            bpy.ops.hops.display_notification(info=f'Merge' )
            return {'FINISHED'}

        active = bpy.context.active_object
        active.select_set(False)
        bpy.ops.object.duplicate()
        duplicate = bpy.context.active_object
        boolobjects = bpy.context.selected_objects

        if not addon.preference().property.keep_cutin_bevel:
            remove_modifiers(boolobjects, "BEVEL")

        active.select_set(True)
        bpy.ops.hops.bool_difference()

        set_active(active, True, True)

        bpy.ops.hops.soft_sharpen()

        active.select_set(False)
        for obj in boolobjects:
            # print(obj)
            obj.select_set(True)

        # createdobj = bpy.context.selected_objects
        duplicates = bpy.context.selected_objects

        for a in duplicates:
            duplicate = a
        set_active(duplicate, True, True)
        apply_modifiers(duplicates, "BEVEL")

        obj = bpy.context.active_object
        me = obj.data

        bm = bmesh.new()
        bm.from_mesh(me)

        if bpy.app.version[0] >= 4:
            cr = bm.edges.layers.float.get('crease_edge')
            if cr is None:
                cr = bm.edges.layers.float.new('crease_edge')
        else:
            cr = bm.edges.layers.crease.verify()

        if bpy.app.version[0] >= 4:
            bw = bm.edges.layers.float.get('bevel_weight_edge')
            if bw is None:
                bw = bm.edges.layers.float.new('bevel_weight_edge')
        else:
            bw = bm.edges.layers.bevel_weight.verify()

        alledges = [e for e in bm.edges if len(e.link_faces) == 2]

        for e in alledges:
            e[cr] = 0
            e.smooth = True
            e.seam = False
            e[bw] = 0

        bm.to_mesh(me)
        bm.free()

        set_active(active, True, True)
        selection = bpy.context.selected_objects
        apply_modifiers(selection, "BOOLEAN")
        bpy.ops.hops.soft_sharpen()

        set_active(duplicate, True, True)
        bpy.ops.object.delete()

        bpy.ops.hops.display_notification(info=f'Cut-In' )

        return {'FINISHED'}

    @staticmethod
    def get_cutter_objects():
        selection = bpy.context.selected_objects
        active = bpy.context.active_object
        return [object for object in selection if object != active and object.type == "MESH"]

    def merge_in (self, context):
        selection = context.selected_objects

        if len(selection) != 2 :
            self.report({'INFO'}, 'Two mesh objects must be selected')
            bpy.ops.hops.display_notification(info=f'Select Two Objects!' )
            
            return {'CANCELLED'}

        obj_a, obj_b = selection

        # third piece
        obj_c = obj_a.copy()

        context.collection.objects.link(obj_c)

        intersect = obj_c.modifiers.new(type = 'BOOLEAN', name= 'bool')
        intersect.object = obj_b
        intersect.operation = 'INTERSECT'

        obj_c.data = bpy.data.meshes.new_from_object(obj_c.evaluated_get(context.evaluated_depsgraph_get()))
        obj_c.modifiers.clear()

        #new obj_a data
        difference = obj_a.modifiers.new(type = 'BOOLEAN', name= 'bool')
        difference.object = obj_b
        difference.operation = 'DIFFERENCE'

        obj_a_data = bpy.data.meshes.new_from_object(obj_a.evaluated_get(context.evaluated_depsgraph_get()))
        obj_a.modifiers.remove(difference)

        #new obj_b data
        difference = obj_b.modifiers.new(type = 'BOOLEAN', name= 'bool')
        difference.object = obj_a
        difference.operation = 'DIFFERENCE'

        obj_b_data = bpy.data.meshes.new_from_object(obj_b.evaluated_get(context.evaluated_depsgraph_get()))
        obj_b.modifiers.remove(difference)

        #feed new data
        obj_a.data = obj_a_data
        obj_a.modifiers.clear()

        obj_b.data = obj_b_data
        obj_b.modifiers.clear()