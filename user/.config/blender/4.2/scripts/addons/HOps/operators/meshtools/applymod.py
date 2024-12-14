import bpy
# from ... utility import modifier
from ... utility import modifier
from bpy.props import EnumProperty
from ... utils.objects import get_current_selected_status
from ... utils.context import ExecutionContext

from ... utils.modifiers import apply_modifiers
from ... utility import addon
from ...ui_framework.operator_ui import Master

def iterate_titled_as_string(iter, separator=','):
    applied_types = ''
    separator = f'{separator} '
    for i in iter:
        applied_types += i.title() + separator
    return applied_types[:-len(separator)]

class HOPS_OT_ApplyModifiers(bpy.types.Operator):
    bl_idname = "hops.apply_modifiers"
    bl_label = "Apply Modifiers"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {"REGISTER", "UNDO"}
    bl_description = """Smart Apply

LMB - Smart Apply Modifiers (keeps last BVL and WN)
SHIFT - Smart Apply Duplicate (w/ clear last BVL and WN)
CTRL - Convert to curve (edge / face)
ALT - Step

Last refers to mods within 3 modifiers of the end of stack

"""

    modifier_types: EnumProperty(
        name='Modifier Types',
        description='Settings to display',
        items=[
            ('NONE', 'All', ''),
            ('BOOLEAN', 'Boolean', ''),
            ('MIRROR', 'Mirror', ''),
            ('BEVEL', 'Bevel', ''),
            ('SOLIDIFY', 'Solidify', ''),
            ('ARRAY', 'Array', '')],
        default='BOOLEAN')

    called_ui = False

    def __init__(self):

        self.text_header = "nothing"
        self.extra_text = "nothing"
        HOPS_OT_ApplyModifiers.called_ui = False

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.label(text="Modifiers Applied")
        colrow = col.row(align=True)
        colrow.prop(self, "modifier_types", expand=True)

    def invoke(self, context, event):

        applied = None
        original_remove_setting = addon.preference().property.Hops_smartapply_remove_cutters

        if event.shift and not event.ctrl and not event.alt:
            bpy.ops.object.duplicate()
            extra_text = "Unapplied modifiers removed"
            #Selected Must be here
            selected = context.selected_objects
            for obj in selected:
                if obj.type != 'MESH':
                    continue

                if original_remove_setting:
                    addon.preference().property.Hops_smartapply_remove_cutters = False
                applied = apply_mod(self, obj, clear_last=event.shift)
            addon.preference().property.Hops_smartapply_remove_cutters = original_remove_setting
            self.text_header = "Clone Smart Apply"

        elif event.ctrl and not event.shift and not event.alt:
            applied = 0
            bpy.ops.object.convert(target='CURVE')
            self.report({'INFO'}, F'Converted to Curve')
            self.text_header = "Converted To Curve"
            try:
                bpy.ops.hops.adjust_curve('INVOKE_DEFAULT')
                extra_text = "Mesh Converted to curve"
            except:
                self.text_header = "Nice Try Bud"
                self.extra_text = "This will not convert to curve. Sorry."
                pass

        elif event.alt and not event.shift and not event.ctrl:
            selected = context.selected_objects
            for obj in selected:
                #applied = apply_mod(self, obj, clear_last=False)
                bpy.ops.hops.step()
                self.report({'INFO'}, F'Smart Apply - Step')
                self.text_header = "Object Stepped"
                return {"FINISHED"}

        elif event.ctrl and event.shift and not event.alt:
            self.text_header = "Mod Render Visibility"
            selected = context.selected_objects
            try:
                for obj in selected:
                    for mod in context.object.modifiers:
                        mod.show_render = True
                self.text_header = "Success"
            except:
                self.text_header = "A complication has occured"

        elif event.ctrl and event.alt and not event.shift:
            self.text_header = "nothing"

        elif event.shift and event.alt and not event.ctrl:
            self.text_header = "nothing"

        else:
            selected = context.selected_objects
            for obj in selected:
                if obj.type != 'MESH':
                    continue

                before_mod_count = len(context.active_object.modifiers[:])
                if len(selected) > 1:
                    if original_remove_setting:
                        addon.preference().property.Hops_smartapply_remove_cutters = False
                    self.extra_text = "Remove cutters bypassed for multi-selection"
                applied = apply_mod(self, obj, clear_last=event.shift)
                addon.preference().property.Hops_smartapply_remove_cutters = original_remove_setting
                self.report({'INFO'}, F'Modifiers Applied')
                self.text_header = "Smart Apply"

        # Operator UI
        if not HOPS_OT_ApplyModifiers.called_ui:
            HOPS_OT_ApplyModifiers.called_ui = True

            bpy.ops.hops.draw_wire_mesh_launcher('INVOKE_DEFAULT', target='SELECTED')

            ui = Master()
            ob = [mod.name for mod in context.active_object.modifiers]
            selected = context.selected_objects

            try:
                draw_data = [
                    [self.text_header],
                    [f"Modifiers Applied ", f"{before_mod_count - len(context.active_object.modifiers[:])}"]
                ]
                if len(context.active_object.modifiers[:]) >= 1:
                    draw_data.insert(-1, ["Remaining Modifiers ", len(context.active_object.modifiers[:])]),
                    for mod in reversed(context.active_object.modifiers):
                        draw_data.insert(-2, [" ", mod.name]),

                else:
                    draw_data.insert(-1, ["Remaining Modifiers ", "0"]),
                if len(selected[:]) == 1:
                    if addon.preference().property.Hops_smartapply_remove_cutters:
                        #draw_data.insert(-2, ["Cutters Removed", f'{(len[cutters])}']),
                        draw_data.insert(-2, ["Cutters Removed", (addon.preference().property.Hops_smartapply_remove_cutters)]),
                else:
                    draw_data.insert(-2, ["Cutters Removed", "False / multi-select"]),

            except:
                draw_data = [
                    [self.text_header],
                    [self.extra_text, ""],
                    ["No additional info", ""]
                ]

            ui.receive_draw_data(draw_data=draw_data)
            ui.draw(draw_bg=addon.preference().ui.Hops_operator_draw_bg, draw_border=addon.preference().ui.Hops_operator_draw_border)

        del applied
        return {"FINISHED"}


def apply_mod(self, obj, clear_last=False):

    mod = None

    mods = [mod for mod in obj.modifiers]
    bevels = [mod for mod in obj.modifiers if mod.type == 'BEVEL']
    mirrors = [mod for mod in obj.modifiers if mod.type == 'MIRROR']
    excluded = [mod for mod in obj.modifiers if mod.type == 'WEIGHTED_NORMAL']

    if len(bevels) > 1 or (len(bevels) and bevels[0].limit_method in {'WEIGHT', 'ANGLE',}):
        if not mods.index(bevels[-1]) < len(mods) - 3:
            excluded.append(bevels[-1])

    if len(mirrors) > 1:
        excluded.append(mirrors[-1])

    # if len(bevels) > 1:
    #     for mod in bevels:
    #         if mod not in excluded:
    #             if mod.limit_method == 'VGROUP':
    #                 excluded.append(mod)

    if addon.preference().property.Hops_smartapply_remove_cutters:
        cutters = [mod.object for mod in obj.modifiers if mod.type == 'BOOLEAN']

    modifier.apply(obj, ignore=excluded)

    if addon.preference().property.Hops_smartapply_remove_cutters:
        for cutter in cutters:
            try:
                bpy.data.objects.remove(cutter)
            except:
                addon.preference().property.Hops_smartapply_remove_cutters = False
                self.report({'ERROR_INVALID_INPUT'}, F'Cannot remove same Cutter from multiple objects')

    if clear_last:
        #bpy.ops.object.duplicate()
        for mod in obj.modifiers:
            if mod.type in {'WEIGHTED_NORMAL', 'BEVEL'}:
                obj.modifiers.remove(mod)

    for mod in excluded:
        mods.remove(mod)

    return mods
