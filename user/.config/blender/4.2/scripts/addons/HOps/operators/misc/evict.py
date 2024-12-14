import bpy
from enum import Enum
from ...utility.collections import link_obj, unlink_obj
from ... utility import addon, operator_override, context_copy
from ...ui_framework.operator_ui import Master
from os import path

# class Modes(Enum):
#     Unify = 1
#     Evict = 2
#     Sync = 3
#     Collect = 4


class HOPS_OT_EVICT(bpy.types.Operator):
    bl_idname = "hops.evict"
    bl_label = "Evict / Unify Cutters"
    bl_options = {"REGISTER", 'UNDO'}
    bl_description = """Scene/Mod Assistant

LMB - Unify all renderable shapes into active collection
CTRL - Evict cutters into cutter collection
SHIFT - Sync mod render/viewport settings
ALT - Purify unused cutters
CTRL + SHIFT - Wash invalid modifiers

"""

    called_ui = False
    text = 'none'

    def __init__(self):

        HOPS_OT_EVICT.called_ui = False

    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        self.layout.prop(self, 'mode')
        if  self.mode == 'COLLECT':
            self.layout.prop_search(self, 'collection_name', bpy.data, "collections")
            self.layout.prop(self, 'collection_link')
            self.layout.prop(self, 'collect_mode')

        elif self.mode == 'EVICT':
            self.layout.prop(self, 'wire_curve')

        elif self.mode =='WASH':
            self.layout.prop(self, "wash_disabled")

    mode: bpy.props.EnumProperty(
        name="Operation",
        description="Management operation",
        items=[
            ('UNIFY', "Unify", "Unify all renderable shapes into collection of active object"),
            ('EVICT', "Evict", "Evict cutters from selection into Cutters "),
            ('SYNC', "Sync", "Sync mod render settings to viewport settings"),
            ('COLLECT', "Collect", "Collect all renderable items into a collection"),
            ('PURIFY', "Purify", "Delete all meshes from Cutters collection that aren't Cutters"),
            ('WASH', "Wash", "Delete all mods with missing Object requrimentss"),
            ],
        default='UNIFY')

    collection_name: bpy.props.StringProperty(
        name="Name", description="Name of the collection to link to",
        default = '')

    collection_link: bpy.props.BoolProperty(
        name="Link", description="Link new collection into scene",
        default = False)

    collect_mode: bpy.props.EnumProperty(
        name="Mode", description="What type of objects are selected",
        items = [ ('Rendered', 'Rendered', 'Rendered'),
        ('Lights','Lights','Lights')
        ],
        default = 'Rendered')

    wire_curve: bpy.props.BoolProperty(
        name="Wire Curves", description="Include curves without bevel or extrusion",
        default = False
    )

    wash_disabled: bpy.props.BoolProperty(
        name="Disabled", description="Include disabled mods",
        default=False
    )

    def invoke (self, context, event):

        # Set the operation mode
        self.mode = 'UNIFY'

        if event.ctrl == True and event.shift == True:
            self.mode = 'WASH'
        elif event.ctrl == True:
            self.mode = 'EVICT'
        elif event.shift == True:
            self.mode = 'SYNC'
        elif event.alt == True:
            self.mode = 'PURIFY'

        return self.execute(context)


    def execute(self, context):

        hops_coll        = "Cutters" if not context.scene.hops.collection else context.scene.hops.collection.name
        collections      = context.scene.collection.children
        view_collections = context.view_layer.layer_collection.children

        if self.mode == 'UNIFY':
            if not context.active_object:
                self.report({'INFO'}, 'No Active object')
                return {'FINISHED'},

            def obj_filter(obj):
                if obj is context.active_object:
                    return False

                if obj.type == 'MESH':
                    return obj.display_type not in {'WIRE', 'BOUNDS'}

                elif obj.type == 'CURVE':
                    return is_geo_curve(obj)

                return False

            shape_count = 0
            shapes = [obj for obj in context.visible_objects if obj_filter(obj)]
            for shape in shapes:
                shape_count += 1
                full_unlink(shape)
                link_to_active(shape, context.active_object)

        elif self.mode == 'EVICT':

            evicted_cutters = 0
            cutters = [obj for obj in context.selected_objects if (obj.type == 'MESH' and obj.display_type in {'WIRE', 'BOUNDS'}) or (obj.type == 'EMPTY' and not obj.is_instancer) or (self.wire_curve and obj.type == 'CURVE' and not is_geo_curve(obj))]
            evicted_cutters += len(cutters)
            for cutter in cutters:
                full_unlink( cutter)
                link_obj(context, cutter)
            if hops_coll in view_collections:
                view_collections[hops_coll].hide_viewport = True
            print(F"Cutters evicted:{evicted_cutters}")

        elif self.mode == 'COLLECT':

            synced = collect(collect_mode=self.collect_mode, collection_name=self.collection_name, collection_link= self.collection_link)


        elif self.mode == 'SYNC':
            synced = 0
            mesh_objs = [o for o in context.selected_objects if o.type == 'MESH']

            # If mod visible -> Set the rendering visible
            for mesh_obj in mesh_objs:
                for mod in mesh_obj.modifiers:
                    if hasattr(mod, 'show_render'):
                        if hasattr(mod, 'show_viewport'):
                            if mod.show_render != mod.show_viewport:
                                synced += 1
                            mod.show_render = mod.show_viewport

                            # If boolean -> Get boolean and set its render settings
                            if mod.type == 'BOOLEAN':
                                if mod.object != None:
                                    target_obj = mod.object
                                    for mod in target_obj.modifiers:
                                        if hasattr(mod, 'show_render'):
                                            if hasattr(mod, 'show_viewport'):
                                                if mod.show_render != mod.show_viewport:
                                                    synced += 1
                                                mod.show_render = mod.show_viewport

                            # Setting viewport to rendering settings
                            if mod.type == 'SCREW':
                                if hasattr(mod, 'steps'):
                                    if hasattr(mod, 'render_steps'):
                                        if mod.steps != mod.render_steps:
                                            synced += 1
                                        mod.render_steps = mod.steps

                            elif mod.type == 'SUBSURF':
                                if hasattr(mod, 'levels'):
                                    if hasattr(mod, 'render_levels'):
                                        if mod.levels != mod.render_levels:
                                            synced += 1
                                        mod.render_levels = mod.levels

                            elif mod.type == 'MULTIRES':
                                if hasattr(mod, 'levels'):
                                    if hasattr(mod, 'render_levels'):
                                        if mod.levels != mod.render_levels:
                                            synced += 1
                                        mod.render_levels = mod.levels
        elif self.mode == 'PURIFY':
            purify_conut = purify(context, hops_coll)

        if self.mode == 'UNIFY':
            text = 'Unify'
            substat = shape_count
            info = 'Amount Unified'
        elif self.mode == 'EVICT':
            text = 'Evict'
            substat = evicted_cutters
            info = 'Amount Evicted'
        elif self.mode == 'SYNC':
            text = 'Sync'
            substat = synced
            info = "Synced Settings"
        elif self.mode == 'COLLECT':
            text = 'Collect'
            substat = synced
            info = "Renderable Objects Collected"

        elif self.mode == 'PURIFY':
            text = 'Purify'
            substat = purify_conut
            info = "Meshes purged"

        elif self.mode == 'WASH':
            text = 'Wash'
            substat = wash(context, disabled=self.wash_disabled)
            info = 'Modifiers washed'

        # Operator UI
        if not HOPS_OT_EVICT.called_ui:
            HOPS_OT_EVICT.called_ui = True
            ui = Master()
            draw_data = [
                [text],
                [info, substat]]
            ui.receive_draw_data(draw_data=draw_data)
            ui.draw(draw_bg=addon.preference().ui.Hops_operator_draw_bg, draw_border=addon.preference().ui.Hops_operator_draw_border)

        return {"FINISHED"}


def full_unlink (obj):
    for col in list(obj.users_collection):
        col.objects.unlink(obj)

def link_to_active(obj, active ):
    for col in active.users_collection:
        col.objects.link(obj)

def collect_filter(object):
    if object.type not in {'MESH', 'EMPTY', 'FONT', 'CURVE', 'META', 'SURFACE'}:
        return False

    if object.type == 'EMPTY' and object.instance_type != 'COLLECTION' and not object.instance_collection:
        return False

    if object.display_type not in {'TEXTURED', 'SOLID'}:
        return False

    if object.hide_viewport or object.hide_render or object.hide_get():
        return False

    return True


def collect(collect_mode = 'Rendered', collection_name = '', collection_link = False ):
    if not collection_name:
        collection_name = path.splitext( bpy.path.basename(bpy.data.filepath))[0]

    if collect_mode == 'Rendered':
        objects = list( filter ( collect_filter ,bpy.context.view_layer.objects) )

    else:
        objects = [o for o in bpy.context.view_layer.objects if o.type == 'LIGHT' and not (o.hide_viewport or o.hide_render or o.hide_get()) ]


    if collection_name in bpy.data.collections:
        new_collection = bpy.data.collections[collection_name]

    else:
        new_collection = bpy.data.collections.new(collection_name)

        if collection_link:
            bpy.context.scene.collection.children.link(new_collection)

        else:
            new_collection.use_fake_user = True

    for object in objects:
        if new_collection not in object.users_collection and new_collection is not object.instance_collection :
            new_collection.objects.link(object)

    return len(objects)

def purify(context, col_name = 'Cutters', obj_keep_names = ('Extraction', 'Slice')):
    boolean_objects = set()
    obj_keep_names = tuple(obj_keep_names)
    ret_counter = 0

    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            for mod in obj.modifiers:
                if mod.type == 'BOOLEAN' and mod.object:
                    boolean_objects.add(mod.object)
                elif mod.type == 'NODES':
                    for node in mod.node_group.nodes:
                        if node.type == 'OBJECT_INFO' and node.inputs['Object'].default_value:
                            boolean_objects.add(node.inputs['Object'].default_value)

    col = None
    def keep_check(obj, names):
        if obj.name.startswith(names):
            return True

    try:
        col = bpy.data.collections[col_name]

    except Exception:
        col = None

    ret_counter = 0
    if col:
        objects = []
        for obj in col.objects[:]:
            if obj.type == 'MESH' and not keep_check(obj, obj_keep_names) and obj not in boolean_objects:
                objects.append(obj)
                ret_counter +=1

        override = context_copy(context)
        override['active_object'] = None
        override['object'] = None
        override['selected_objects'] = objects
        operator_override(context, bpy.ops.object.delete, override, use_global=False)

    return ret_counter

def wash(context, disabled=False) -> int:
    count = 0

    for obj in context.selected_objects:
        for mod in obj.modifiers[:]:
            if disabled and not mod.show_viewport:
                obj.modifiers.remove(mod)
                count +=1

            elif mod.type == "BOOLEAN":
                operand = getattr(mod,'operand', 'OBJECT')

                if operand == 'OBJECT' and not mod.object:
                    obj.modifiers.remove(mod)
                    count += 1

                elif operand == 'COLLECTION' and not mod.collection:
                    obj.modifiers.remove(mod)
                    count += 1

            elif mod.type == 'WARP' and not mod.object_to and not mod.object_from:
                    obj.modifiers.remove(mod)
                    count += 1

            elif mod.type in {'SURFACE_DEFORM', 'VERTEX_WEIGHT_PROXIMITY', 'SHRINKWRAP'} and not mod.target:
                    obj.modifiers.remove(mod)
                    count += 1

            elif mod.type in {'ARMATURE', 'CURVE', 'HOOK', 'LATTICE', 'DATA_TRANSFER', 'VOLUME_TO_MESH', 'MESH_DEFORM', } and not mod.object:
                    obj.modifiers.remove(mod)
                    count += 1

    return count

def is_geo_curve(obj):
    if obj.data.extrude: return True

    if obj.data.bevel_mode == 'OBJECT':
        return obj.data.bevel_object
    else:
        return obj.data.bevel_depth

class HOPS_OT_COLLECT(bpy.types.Operator):
    bl_idname = "hops.collect"
    bl_label = "HOPS COLLECT"
    bl_options = {"REGISTER", 'UNDO'}
    bl_description = """COLLECT Standalone

Utilizes HOPS COLLECT to get all meshes into a collection
able to be named in the F9 panel

"""
    called_ui = False
    text = 'none'

    def __init__(self):

        HOPS_OT_COLLECT.called_ui = False

    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        self.layout.prop(self, 'collection_name')
        self.layout.prop(self, 'collection_link')
        self.layout.prop(self, 'collect_mode')

    collection_name: bpy.props.StringProperty(
        name="Name", description="Name of the collection to link to",
        default = '')

    collection_link: bpy.props.BoolProperty(
        name="Link", description="Link new collection into scene",
        default = False)

    collect_mode: bpy.props.EnumProperty(
        name="Mode", description="What type of objects are selected",
        items = [ ('Rendered', 'Rendered', 'Rendered'),
        ('Lights','Lights','Lights')
        ],
        default = 'Rendered')

    def invoke (self, context, event):

        return self.execute(context)

    def execute(self, context):

        hops_coll        = "Cutters" if not context.scene.hops.collection else context.scene.hops.collection.name
        collections      = context.scene.collection.children
        view_collections = context.view_layer.layer_collection.children

        synced = collect(collect_mode=self.collect_mode, collection_name=self.collection_name, collection_link= self.collection_link)
        collect(self.collect_mode, self.collection_name, self.collection_link)

        text = 'Collect'
        substat = synced
        info = "Renderable Objects Collected"

        # Operator UI
        if not HOPS_OT_COLLECT.called_ui:
            HOPS_OT_COLLECT.called_ui = True
            ui = Master()
            draw_data = [
                [text],
                [info, substat]]
            ui.receive_draw_data(draw_data=draw_data)
            ui.draw(draw_bg=addon.preference().ui.Hops_operator_draw_bg, draw_border=addon.preference().ui.Hops_operator_draw_border)

        return {"FINISHED"}
