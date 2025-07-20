import bpy
import bmesh
from ... utility import addon
from ...ui_framework.operator_ui import Master

class HOPS_OT_MOD_Cloth(bpy.types.Operator):
    bl_idname = "hops.mod_cloth"
    bl_label = "Add Cloth Modifier"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = """Adds Cloth Modifier

LMB - Add Cloth Modifier
Shift - Only Operator
Ctrl - Subd/Cloth/Subd

"""
    called_ui = False

    def __init__(self):

        HOPS_OT_MOD_Cloth.called_ui = False

    @classmethod
    def poll(cls, context):
        return any(o.type == 'MESH' for o in context.selected_objects)

    def invoke(self, context, event):
        self.obj = context.active_object

        self.added_mods = []
        self.found_mods = []

        for object in [o for o in context.selected_objects if o.type == 'MESH']:
            cloth_mods = self.cloth_modifiers(object)
            if cloth_mods:
                self.found_mods.extend(cloth_mods)
            else:
                if event.ctrl:
                    object.modifiers.new(name="Subd1", type="SUBSURF")
                    self.add_cloth_modifier(object)
                    object.modifiers.new(name="Subd2", type="SUBSURF")
                else:
                    self.add_cloth_modifier(object)
            # create_vgroup(self, self.cloth_mod) # needs to make smart vgroup here based on mesh boundary
            # return {"CANCELLED"}
            

        # Operator UI
        if not HOPS_OT_MOD_Cloth.called_ui:
            HOPS_OT_MOD_Cloth.called_ui = True

            ui = Master()
            draw_data = [
                ["Cloth"],
               ]
            if self.added_mods:
                draw_data.append( ["Quality Level : ", self.cloth_mod.settings.quality])
                bpy.ops.screen.frame_jump(end=False)
            else:
                draw_data.append(['Cloth Modifier(s) already exist'])
            ui.receive_draw_data(draw_data=draw_data)
            ui.draw(draw_bg=addon.preference().ui.Hops_operator_draw_bg, draw_border=addon.preference().ui.Hops_operator_draw_border)

        if not event.shift:
            bpy.ops.hops.adjust_cloth('INVOKE_DEFAULT')
            
        return {"FINISHED"}


    def create_vgroup(self, mod):
        original_mode = self.obj.mode

        if original_mode == 'EDIT':
            bpy.ops.object.mode_set(mode='OBJECT')

        vertex_group = None

        for group in self.obj.vertex_groups:
            if group.name == 'HOPS_Cloth':
                vertex_group = group

        if not vertex_group:
            vertex_group = self.obj.vertex_groups.new(name='HOPS_Cloth')

        bm = bmesh.new()
        bm.from_mesh(self.obj.data)

        verts = [v.index for v in bm.verts if v.is_boundary]
        vertex_group.add(index=verts, weight=1.0, type='REPLACE')
        verts1 = [e.verts[0].index for e in bm.edges if e.seam]
        verts2 = [e.verts[0].index for e in bm.edges if e.seam]
        verts = verts1 + verts2
        vertex_group.add(index=verts, weight=1.0, type='REPLACE')

        mod.settings.vertex_group_mass = vertex_group.name
        bm.free()


    @staticmethod
    def cloth_modifiers(object):
        return [modifier for modifier in object.modifiers if modifier.type == "CLOTH"]

    def add_cloth_modifier(self, object):
        self.cloth_mod = object.modifiers.new(name="Cloth", type='CLOTH')
        self.cloth_mod.settings.use_pressure = True
        self.cloth_mod.settings.uniform_pressure_force = 15
        self.cloth_mod.settings.quality = 3
        self.cloth_mod.settings.time_scale = 0.5
        self.cloth_mod.settings.shrink_min = -0.3
        self.create_vgroup(self.cloth_mod)
        self.added_mods.append(self.cloth_mod)
