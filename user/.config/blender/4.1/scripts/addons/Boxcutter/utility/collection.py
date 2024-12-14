import bpy


def view_layer_unhide(collection, check=None, chain=None):
    if isinstance(chain, type(None)):
        chain = []

    view_layer_collection = bpy.context.view_layer.layer_collection
    current = view_layer_collection if not check else check

    if collection.name in current.children:
        collection.hide_viewport = False

        collection = current.children[collection.name]
        collection.exclude = False
        collection.hide_viewport = False

        for col in chain:
            col.exclude = False
            col.hide_viewport = False
            bpy.data.collections[col.name].hide_viewport = False

        return True

    for child in current.children:
        if not child.children:
            continue

        if check:
            chain.append(check)

        if view_layer_unhide(collection, check=child, chain=chain):
            child.exclude = False
            child.hide_viewport = False
            bpy.data.collections[child.name].hide_viewport = False

            return True

    return False


def find(name='Collection', parents=False, children=False):
    if parents:
        return [c for c in bpy.data.collections if name in c.children]

    if children:
        return None if name not in bpy.data.collections else bpy.data.collections[name].children[:]

    if name in bpy.data.collections:
        return bpy.data.collections[name]

    return None


def parents(name='Collection'):
    return find(name, parents=True)


def children(name='Collection'):
    return find(name, children=True)


def child_of(name='Collection', parent=None):
    if not parent:
        parent = bpy.context.scene.collection

    if name in parent.children:
        return parent.children[name]

    for sub in parent.children:
        if name in sub.children:
            return sub.children[name]

    for sub in parent.children:
        return child_of(name, sub)

    return None


def exists(name='Collection'):
    return bool(find(name))


def get(name, default=None):
    if not exists(name):
        return default

    return find(name)


def new(name='Collection', parent=None, color='', unique=True, unique_parent=False, hopscutter=False):
    color = color.lower()
    color_tags = {
        'default': 'NONE',
        'red': 'COLOR_01',
        'orange': 'COLOR_02',
        'yellow': 'COLOR_03',
        'green': 'COLOR_04',
        'blue': 'COLOR_05',
        'violet': 'COLOR_06',
        'pink': 'COLOR_07',
        'brown': 'COLOR_08',
    }

    if color not in color_tags:
        color = 'default'

    if unique and exists(name):
        collection = get(name)

        if parent:
            if unique_parent:
                for p in parents(name):
                    p.children.unlink(collection)

            if name not in parent.children:
                parent.children.link(collection)

        if hasattr(collection, 'color_tag'):
            collection.color_tag = color_tags[color]

        return collection

    collection = bpy.data.collections.new(name)
    collection.hopscutter = hopscutter

    if hasattr(collection, 'color_tag'):
        collection.color_tag = color_tags[color]

    if not parent:
        parent = bpy.context.scene.collection

    parent.children.link(collection)
    return collection

