import bpy
from .. utility import addon


def unlink_obj(context, obj):
    # for coll in context.scene.collection.children:
    #     for ob in bpy.data.collections[coll.name].objects:
    #         if obj == bpy.data.collections[coll.name].objects[ob.name]:
    #             bpy.data.collections[coll.name].objects.unlink(obj)
    for col in obj.users_collection[:]:
        col.objects.unlink(obj)


def link_obj(context, obj, name="Cutters"):
    '''Link object to Hops collection of active scene'''
    # for col in obj.users_collection:
    #     if col.name == name:
    #         return

    # if name not in bpy.data.collections:
    #     new_col = bpy.data.collections.new(name='Cutters')
    #     if hasattr(new_col, 'color_tag'):
    #         new_col.color_tag = addon.preference().color.colection_color
    #     context.scene.collection.children.link(new_col)

    # bpy.data.collections[name].objects.link(obj)

    hops_col = hops_col_get(context)

    for col in obj.users_collection:
        if col is hops_col: return

    hops_col.objects.link(obj)


def find_collection(context, item, must_be_in_view_layer=False):
    if len(item.users_collection) > 0:

        if must_be_in_view_layer:
            collections_in_view = all_collections_in_view_layer(context)
            for coll in item.users_collection:
                if coll in collections_in_view: return coll
            return context.scene.collection

        return item.users_collection[0]
    return context.scene.collection


def all_collections_in_view_layer(context):
    chain = []

    def collect(coll, chain):
        for child in coll.children:
            if child.children:
                collect(child, chain)
            else:
                chain.append(child)
        chain.append(coll)

    for coll in context.scene.collection.children:
        collect(coll, chain)
    return chain


def hide_all_objects_in_collection(coll):
    '''Hide all objects in the collection passed in.'''

    for obj in coll.objects:
        if hasattr(obj, 'hide_set'):
            obj.hide_set(True)


def turn_on_parent_collections(obj, start_coll):
    '''Recursively turn on all parent collections that the object is in.'''

    for child in start_coll.children:
        if type(child) == bpy.types.Collection:
            turn_on_parent_collections(obj, child)
            if obj.name in child.objects:
                view_layer_unhide(child, enable=True)
                return True
    return False


def view_layer_unhide(collection, check=None, chain=None, enable=False):
    '''Recursively unhide collections until reaching passed in collection.'''

    if chain is None: chain = []

    view_layer_collection = bpy.context.view_layer.layer_collection
    current = view_layer_collection if not check else check

    if collection.name in current.children:
        collection.hide_viewport = False

        collection = current.children[collection.name]
        collection.hide_viewport = False

        if enable:
            collection.exclude = False

        for col in chain:
            col.hide_viewport = False
            bpy.data.collections[col.name].hide_viewport = False

            if enable:
                col.exclude = False

        return True

    for child in current.children:
        if not child.children:
            continue

        if check:
            chain.append(check)

        if view_layer_unhide(collection, check=child, chain=chain, enable=enable):
            child.hide_viewport = False
            bpy.data.collections[child.name].hide_viewport = False

            if enable:
                child.exclude = False

            return True

    return False


def unhide_layers(obj):

    def obj_in_coll(obj, coll):
        if obj.name in coll.collection.objects: return True
        return False

    def search(obj, coll, chain):
        if obj_in_coll(obj, coll):
            chain.append(coll)
            return True

        for child in coll.children:
            if search(obj, child, chain):
                chain.append(coll)
                return True

        return False

    chain = []
    search(obj, bpy.context.view_layer.layer_collection, chain)
    chain = list(set(chain))

    for coll in chain:
        if coll.exclude:
            coll.exclude = False
        if coll.hide_viewport:
            coll.hide_viewport = False
        if coll.collection.hide_viewport:
            coll.collection.hide_viewport = False


def hops_col_get(context):
    '''Get Cutters collection of active scene or create new one'''

    col_name = 'Cutters'
    if context.scene.hops.collection:
        col_name = context.scene.hops.collection.name

    def check_link(col, name):
        if name in col.children: return col.children[name]

        for child in col.children:
            res = check_link(child, name)
            if res: return res

        return None

    hops_col = check_link(context.scene.collection, col_name)

    if hops_col:
        context.scene.hops.collection = hops_col
        return hops_col

    new_col = bpy.data.collections.new(col_name)
    context.scene.hops.collection = new_col
    context.scene.collection.children.link(new_col)

    if hasattr(new_col, 'color_tag'):
        new_col.color_tag = addon.preference().color.colection_color

    return new_col

