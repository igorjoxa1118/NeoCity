import bpy
from bpy.props import EnumProperty
from ... utility import addon, modifier, operator_override, context_copy
from ...ui_framework.operator_ui import Master


class HOPS_OT_LateParen_t(bpy.types.Operator):
    bl_idname = "hops.late_paren_t"
    bl_label = "Late Parent "
    bl_description = '\n Connects cutters as children to parent'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {"REGISTER", "UNDO"}


    def execute(self, context):
        targets = {}

        for obj in context.visible_objects:
            for mod in obj.modifiers:
                if mod.type == 'BOOLEAN' and mod.object and mod.object.select_get():
                    if obj not in targets:
                        targets[obj] = [mod.object]
                    elif mod.object not in targets[obj]:
                        targets[obj].append(mod.object)

        count = 0
        for obj in targets:
            context_override = context_copy(context)
            context_override['object'] = obj
            operator_override(context, bpy.ops.object.parent_set, context_override, keep_transform=True)

            for _ in targets[obj]:
                count += 1

        del targets

        self.report({'INFO'}, F'{str(count) + " " if count > 0 else ""}Cutter{"s" if count > 1 else ""} Parented')

        return {'FINISHED'}


class HOPS_OT_LateParent(bpy.types.Operator):
    bl_idname = "hops.late_parent"
    bl_label = "Late Parent "
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {"REGISTER", "UNDO"}
    bl_description = '''Late Parent

    Connects cutters as children to parent.
    *Used to retroactively connect cutters to parent*
    Now supporting recursion. (cutters of cutters)

    '''

    called_ui = False

    def __init__(self):

        HOPS_OT_LateParent.called_ui = False

    def execute(self, context):

        lst = late_parent(context)
        self.report({'INFO'}, F'Cutters Parented')
        # Operator UI
        if not HOPS_OT_LateParent.called_ui:
            HOPS_OT_LateParent.called_ui = True

            ui = Master()
            draw_data = [
                ["Late Parent"],
                ["Selected Objects", lst[0]],
                ["Cutters Parented", lst[1]],
                ["Booleans Total", lst[2]]
                ]
            ui.receive_draw_data(draw_data=draw_data)
            ui.draw(draw_bg=addon.preference().ui.Hops_operator_draw_bg, draw_border=addon.preference().ui.Hops_operator_draw_border)

        return {"FINISHED"}


def late_parent(context):

    cutters = 0
    bools = 0

    if len (context.selected_objects) == 1:
        return  late_parent_recursive(context.selected_objects[0], out= [0, 0, 0], process_parents=True)

    for obj in context.selected_objects:

        for mod in obj.modifiers:
            if mod.type == 'BOOLEAN' and mod.object != None:
                bools +=1

                if  mod.object.parent == None:
                    cutters+=1
                    mod.object.parent = obj
                    mod.object.matrix_parent_inverse = obj.matrix_world.inverted()


    return [len(context.selected_objects), cutters , bools]


def late_parent_recursive(obj, out = [0,0,0], process_parents = False, rec_filter = None):
    if not rec_filter:
        rec_filter = set()

    if obj in rec_filter: return
    rec_filter.add(obj)

    for mod in obj.modifiers:
        if mod.type in mod_object_map:
            mod_obj = getattr(mod, mod_object_map[mod.type], None)

            if mod_obj:
                out[2] +=1

                if  mod_obj.parent == None:
                    out[1] +=1
                    mod_obj.parent = obj
                    mod_obj.matrix_parent_inverse = obj.matrix_world.inverted()
                    out[0] = 1
                    out[1] += 1

                elif process_parents:
                    parent_mod = mod_obj.parent
                    current = mod_obj

                    while parent_mod:
                        current = parent_mod
                        parent_mod = current.parent

                    if current is not obj:
                        current.parent = obj
                        current.matrix_parent_inverse = obj.matrix_world.inverted()

                if mod_obj.modifiers:
                    late_parent_recursive(mod_obj, out, rec_filter=rec_filter)
    return out

mod_object_map = {
    'BOOLEAN': 'object',
    'CURVE': 'object',
    'LATTICE': 'object',
    'MIRROR': 'mirror_object',

}
