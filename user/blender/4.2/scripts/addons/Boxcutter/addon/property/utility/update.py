from ... import toolbar
from .... utility import modifier, translate
from .... utility.geomerty_nodes import SmoothByAngle


def use_auto_smooth(mesh, context):
    import bmesh

    objects = [o for o in context.visible_objects if o.data == mesh]

    for obj in objects:
        auto_smooth_mods = list(filter(SmoothByAngle.is_valid_modifier, obj.modifiers))

        if mesh.use_auto_smooth and not auto_smooth_mods:
            mod = SmoothByAngle.from_object(obj)
            mod.name = F'{modifier.sort_last_flag*2}{mod.name}'
            mod.angle = obj.data.auto_smooth_angle

        elif not mesh.use_auto_smooth:
            for mod in auto_smooth_mods:
                obj.modifiers.remove(obj)

            if obj.mode == 'EDIT':
                bm = bmesh.from_edit_mesh(obj.data)

                for edge in bm.edges:
                    edge.smooth = False

                bmesh.update_edit_mesh(obj.data, False, False)

            else:
                for edge in obj.data.edges:
                    edge.use_edge_sharp = False


def auto_smooth_angle(mesh, context):
    objects = [o for o in context.visible_objects if o.data == mesh]

    for obj in objects:
        auto_smooth_mods = list(filter(SmoothByAngle.is_valid_modifier, obj.modifiers))

        if not auto_smooth_mods: continue

        mod = SmoothByAngle.new(auto_smooth_mods[-1])
        mod.angle = mesh.auto_smooth_angle


def change_start_operation(option, context):
    toolbar.option().operation = option.start_operation

    context.workspace.tools.update()


def store_collection(option, context):
    bc = context.scene.bc

    if not bc.running:
        main = 'Cutters'
        if option.collection and option.stored_collection != option.collection and main != option.collection.name:
            option.stored_collection = option.collection

            if option.collection and option.shape and option.shape.name not in option.collection.objects:
                option.shape = option.stored_shape if option.stored_shape and option.stored_shape.name in option.collection.objects else None

            if option.collection and not option.shape and len(option.collection.objects):
                option.shape = option.collection.objects[0]


def store_shape(option, context):
    bc = context.scene.bc

    if not bc.running:
        if option.shape and option.stored_shape != option.shape:
            option.stored_shape = option.shape
