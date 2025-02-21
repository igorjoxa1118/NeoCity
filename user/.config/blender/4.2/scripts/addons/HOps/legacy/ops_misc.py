import bpy
import bmesh
from bpy.props import BoolProperty
import bpy.utils.previews
from .. utility import addon
from ..ui_framework.operator_ui import Master


class HOPS_OT_MakeLink(bpy.types.Operator):
    bl_idname = "make.link"
    bl_label = "Make Link"
    bl_description = "Link Object Mesh Data"
    bl_options = {"REGISTER"}

    def execute(self, context):
        bpy.ops.object.make_links_data(type='OBDATA')
        bpy.ops.object.make_links_data(type='MODIFIERS')

        return {"FINISHED"}

# Solid All


class HOPS_OT_SolidAll(bpy.types.Operator):
    bl_idname = "object.solid_all"
    bl_label = "Solid All"
    bl_description = """Solid Shade

    Make Object Solid Shaded
    Ctrl or Shift + Duplicate and make solid

    """
    bl_options = {'REGISTER', 'UNDO'}

    called_ui = False

    def __init__(self):

        HOPS_OT_SolidAll.called_ui = False

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def invoke(self, context, event):
        extra_text = ""
        wm = bpy.context.window_manager

        objs = [o for o in context.selected_objects if o.type == 'MESH']

        if event.ctrl or event.shift or event.alt:
            extra_text = "Duplicate / Made solid / Moved to active collection"
            bpy.ops.object.select_all(action='DESELECT')
            context.view_layer.objects.active = None

            for obj in objs:
                obj.select_set(False)

                if obj.display_type in {'WIRE', 'BOUNDS'}:
                    obj.hide_render = False

                    new_obj = obj.copy()
                    new_obj.data = obj.data.copy()
                    new_obj.animation_data_clear()
                    context.collection.objects.link(new_obj)
                    new_obj.hops.status = "UNDEFINED"
                    new_obj.display_type = 'SOLID'
                    new_obj.show_wire = False
                    new_obj.display_type = 'TEXTURED'
                    new_obj.select_set(True)
                    context.view_layer.objects.active = new_obj

                    bpy.ops.object.mode_set(mode='EDIT')
                    bpy.ops.mesh.select_all(action='DESELECT')
                    bpy.ops.mesh.select_all(action='SELECT')
                    bpy.ops.mesh.normals_make_consistent(inside=False)
                    bpy.ops.object.mode_set(mode='OBJECT')
                    if bpy.app.version[0] >= 4:
                        bpy.ops.object.shade_flat()

                    if hasattr(new_obj, 'cycles_visibility'):
                        new_obj.cycles_visibility.shadow = True
                        new_obj.cycles_visibility.camera = True
                        new_obj.cycles_visibility.diffuse = True
                        new_obj.cycles_visibility.glossy = True
                        new_obj.cycles_visibility.transmission = True
                        new_obj.cycles_visibility.scatter = True

                    if hasattr(new_obj, 'visible_camera'):
                        new_obj.visible_camera = True
                    if hasattr(new_obj, 'visible_diffuse'):
                        new_obj.visible_diffuse = True
                    if hasattr(new_obj, 'visible_glossy'):
                        new_obj.visible_glossy = True
                    if hasattr(new_obj, 'visible_transmission'):
                        new_obj.visible_transmission = True
                    if hasattr(new_obj, 'visible_volume_scatter'):
                        new_obj.visible_volume_scatter = True
                    if hasattr(new_obj, 'visible_shadow'):
                        new_obj.visible_shadow = True

        else:
            for obj in objs:
                extra_text = "Visibility / Solid Re-enabled"

                for obj in context.selected_objects:
                    if obj.display_type == 'WIRE' or 'BOUNDS':
                        obj.display_type = 'SOLID'
                        obj.show_wire = False
                        obj.display_type = 'TEXTURED'
                        obj.hide_render = False
                        if hasattr(obj, 'cycles_visibility'):
                            obj.cycles_visibility.shadow = True
                            obj.cycles_visibility.camera = True
                            obj.cycles_visibility.diffuse = True
                            obj.cycles_visibility.glossy = True
                            obj.cycles_visibility.transmission = True
                            obj.cycles_visibility.scatter = True

                        if hasattr(obj, 'visible_camera'):
                            obj.visible_camera = True
                        if hasattr(obj, 'visible_diffuse'):
                            obj.visible_diffuse = True
                        if hasattr(obj, 'visible_glossy'):
                            obj.visible_glossy = True
                        if hasattr(obj, 'visible_transmission'):
                            obj.visible_transmission = True
                        if hasattr(obj, 'visible_volume_scatter'):
                            obj.visible_volume_scatter = True
                        if hasattr(obj, 'visible_shadow'):
                            obj.visible_shadow = True

                        if bpy.app.version[0] >= 4:
                            bpy.ops.object.shade_flat()

                    elif obj.display_type == 'SOLID':
                        obj.display_type = 'WIRE'

                    else:
                        obj.display_type = 'WIRE'

        # Operator UI
        if not HOPS_OT_SolidAll.called_ui:
            HOPS_OT_SolidAll.called_ui = True

            bpy.ops.hops.draw_wire_mesh_launcher('INVOKE_DEFAULT', target='SELECTED')

            ui = Master()
            draw_data = [
                ["SOLID Shaded"],
                ["Selection set to solid shading"],
                [extra_text]
                ]
            ui.receive_draw_data(draw_data=draw_data)
            ui.draw(draw_bg=addon.preference().ui.Hops_operator_draw_bg, draw_border=addon.preference().ui.Hops_operator_draw_border)

        return {'FINISHED'}


class HOPS_OT_ReactivateWire(bpy.types.Operator):
    bl_idname = "hops.showwire_objects"
    bl_label = "showWire"
    bl_description = """Wire Shade

    Make Object Wire Shaded

    """
    bl_options = {'REGISTER', 'UNDO'}

    noexist: BoolProperty(default=False)

    realagain: BoolProperty(default=False)

    called_ui = False

    def __init__(self):

        HOPS_OT_ReactivateWire.called_ui = False

    def draw(self, context):
        layout = self.layout

        box = layout.box()
        # DRAW YOUR PROPERTIES IN A BOX
        box.prop(self, 'noexist', text="Unrenderable")
        #box.prop(self, 'realagain', text="Make Real")

    def invoke(self, context, event):
        wm = bpy.context.window_manager

        extra_text = "Selection set to wire shading"

        for obj in [o for o in context.selected_objects if o.type == 'MESH']:
            obj.show_wire = True
            obj.display_type = 'WIRE'
            obj.show_all_edges = True
            obj.hide_render = True

            if self.noexist:
                if hasattr(obj, 'cycles_visibility'):
                    obj.cycles_visibility.camera = False
                    obj.cycles_visibility.diffuse = False
                    obj.cycles_visibility.glossy = False
                    obj.cycles_visibility.transmission = False
                    obj.cycles_visibility.scatter = False
                    obj.cycles_visibility.shadow = False

                if hasattr(obj, 'visible_camera'):
                    obj.visible_camera = False
                if hasattr(obj, 'visible_diffuse'):
                    obj.visible_diffuse = False
                if hasattr(obj, 'visible_glossy'):
                    obj.visible_glossy = False
                if hasattr(obj, 'visible_transmission'):
                    obj.visible_transmission = False
                if hasattr(obj, 'visible_volume_scatter'):
                    obj.visible_volume_scatter = False
                if hasattr(obj, 'visible_shadow'):
                    obj.visible_shadow = False

            if self.realagain:
                if hasattr(obj, 'cycles_visibility'):
                    obj.cycles_visibility.camera = True
                    obj.cycles_visibility.diffuse = True
                    obj.cycles_visibility.glossy = True
                    obj.cycles_visibility.transmission = True
                    obj.cycles_visibility.scatter = True
                    obj.cycles_visibility.shadow = True

                if hasattr(obj, 'visible_camera'):
                    obj.visible_camera = True
                if hasattr(obj, 'visible_diffuse'):
                    obj.visible_diffuse = True
                if hasattr(obj, 'visible_glossy'):
                    obj.visible_glossy = True
                if hasattr(obj, 'visible_transmission'):
                    obj.visible_transmission = True
                if hasattr(obj, 'visible_volume_scatter'):
                    obj.visible_volume_scatter = True
                if hasattr(obj, 'visible_shadow'):
                    obj.visible_shadow = True

                obj.display_type = 'WIRE'
                obj.display_type = 'TEXTURED'
                obj.show_all_edges = False
                obj.show_wire = False

            else:
                if hasattr(obj, 'cycles_visibility'):
                    obj.cycles_visibility.camera = False
                    obj.cycles_visibility.shadow = False
                    obj.cycles_visibility.transmission = False
                    obj.cycles_visibility.scatter = False
                    obj.cycles_visibility.diffuse = False
                    obj.cycles_visibility.glossy = False

                if hasattr(obj, 'visible_camera'):
                    obj.visible_camera = False
                if hasattr(obj, 'visible_diffuse'):
                    obj.visible_diffuse = False
                if hasattr(obj, 'visible_glossy'):
                    obj.visible_glossy = False
                if hasattr(obj, 'visible_transmission'):
                    obj.visible_transmission = False
                if hasattr(obj, 'visible_volume_scatter'):
                    obj.visible_volume_scatter = False
                if hasattr(obj, 'visible_shadow'):
                    obj.visible_shadow = False

        # Operator UI
        if not HOPS_OT_ReactivateWire.called_ui:
            HOPS_OT_ReactivateWire.called_ui = True

            ui = Master()
            draw_data = [
                ["WIRE Shaded"],
                ["Unrenderable", self.noexist],
                [extra_text]
                #["Make Visible", self.realagain]
                ]
            ui.receive_draw_data(draw_data=draw_data)
            ui.draw(draw_bg=addon.preference().ui.Hops_operator_draw_bg, draw_border=addon.preference().ui.Hops_operator_draw_border)

        return {'FINISHED'}

# Show Overlays


class HOPS_OT_ShowOverlays(bpy.types.Operator):
    bl_idname = "object.showoverlays"
    bl_label = "Show Overlays"
    bl_description = "Show Marked Edge Overlays"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.context.object.data.show_edge_crease = True
        bpy.context.object.data.show_edge_sharp = True
        bpy.context.object.data.show_edge_bevel_weight = True

        return {"FINISHED"}

# Hide Overlays


class HOPS_OT_HideOverlays(bpy.types.Operator):
    bl_idname = "object.hide_overlays"
    bl_label = "Hide Overlays"
    bl_description = "Hide Marked Edge Overlays"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.context.object.data.show_edge_crease = False
        bpy.context.object.data.show_edge_sharp = False
        bpy.context.object.data.show_edge_bevel_weight = False
        return {"FINISHED"}

# Place Object


class HOPS_OT_UnLinkObjects(bpy.types.Operator):
    bl_idname = "unlink.objects"
    bl_label = "UnLink_Objects"
    bl_description = "Unlink Object Mesh Data"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):

        bpy.ops.object.make_single_user(type='SELECTED_OBJECTS', object=True, obdata=True, material=False, texture=False, animation=False)
        return {"FINISHED"}

# Apply Material


class HOPS_OT_ApplyMaterial(bpy.types.Operator):
    bl_idname = "object.apply_material"
    bl_label = "Apply material"
    bl_description = "Apply scene material to object"

    mat_to_assign: bpy.props.StringProperty(default="")

    def execute(self, context):

        if context.object.mode == 'EDIT':
            obj = context.object
            bm = bmesh.from_edit_mesh(obj.data)

            selected_face = [f for f in bm.faces if f.select]  # si des faces sont sélectionnées, elles sont stockées dans la liste "selected_faces"

            mat_name = [mat.name for mat in bpy.context.object.material_slots if len(bpy.context.object.material_slots)]  # pour tout les material_slots, on stock les noms des mat de chaque slots dans la liste "mat_name"

            if self.mat_to_assign in mat_name:  # on test si le nom du mat sélectionné dans le menu est présent dans la liste "mat_name" (donc, si un des slots possède le materiau du même nom). Si oui:
                context.object.active_material_index = mat_name.index(self.mat_to_assign)  # on definit le slot portant le nom du comme comme étant le slot actif
                bpy.ops.object.material_slot_assign()  # on assigne le matériau à la sélection
            else:  # sinon
                bpy.ops.object.material_slot_add()  # on ajout un slot
                bpy.context.object.active_material = bpy.data.materials[self.mat_to_assign]  # on lui assigne le materiau choisi
                bpy.ops.object.material_slot_assign()  # on assigne le matériau à la sélection

            return {'FINISHED'}

        elif context.object.mode == 'OBJECT':

            obj_list = [obj.name for obj in context.selected_objects]

            for obj in obj_list:
                bpy.ops.object.select_all(action='DESELECT')
                bpy.data.objects[obj].select_set(True)
                bpy.context.view_layer.objects.active = bpy.data.objects[obj]
                bpy.context.object.active_material_index = 0

                if self.mat_to_assign == bpy.data.materials:
                    bpy.context.active_object.active_material = bpy.data.materials[mat_name]

                else:
                    if not len(bpy.context.object.material_slots):
                        bpy.ops.object.material_slot_add()

                    bpy.context.active_object.active_material = bpy.data.materials[self.mat_to_assign]

            for obj in obj_list:
                bpy.data.objects[obj].select_set(True)

            return {'FINISHED'}

# By: 'Sybren A. Stüvel',
class HOPS_OT_MaterialOtSimplifyNames(bpy.types.Operator):
    bl_idname = "material.simplify"
    bl_label = "Link materials to remove 00X mats"
    bl_description = "Consolidates materials to remove duplicates"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        for ob in context.selected_objects:
            for slot in ob.material_slots:
                self.fixup_slot(slot)

        return {'FINISHED'}

    def split_name(self, material):
        name = material.name

        if not '.' in name:
            return name, None

        base, suffix = name.rsplit('.', 1)
        try:
            num = int(suffix, 10)
        except ValueError:
            # Not a numeric suffix
            return name, None

        return base, suffix

    def fixup_slot(self, slot):
        if not slot.material:
            return

        base, suffix = self.split_name(slot.material)
        if suffix is None:
            return

        try:
            base_mat = bpy.data.materials[base]
        except KeyError:
            print('Base material %r not found' % base)
            return

        slot.material = base_mat
