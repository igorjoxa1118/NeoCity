import importlib

from copy import deepcopy as copy

import bpy

from bpy.types import Operator
from bpy.props import StringProperty
from bpy.utils import register_class, unregister_class
from ... utility import addon
from ... ui_framework.operator_ui import Master

# tracked_events = None
tracked_states = None


class HOPS_OT_bc_notifications(Operator):
    bl_idname = 'hops.bc_notifications'
    bl_label = 'BoxCutter Notifications'
    bl_options = {'INTERNAL'}

    info: StringProperty(default='Notification')


    def notifications(self, prop_name):
        notification = 'Notification'
        prop = getattr(self, prop_name)

        if prop_name in self.exclude_notifications:
            return notification

        if prop_name == 'mode':
            value = self.mode
            notification = F'{value.title()[:-1 if value in {"SLICE", "MAKE"} else len(value)] if value != "KNIFE" else "Using Knife"}{"t" if value in {"CUT", "INSET"} else ""}{"ing" if value != "KNIFE" else ""}'

        elif prop_name == 'operation':
            if self.operation == 'NONE':
                notification = 'Shape Locked'
            else:
                value = self.operation
                notification = F'{"Added " if value == "ARRAY" else ""}{value.title()[:-1 if value in {"MOVE", "ROTATE", "SCALE", "EXTRUDE", "DISPLACE"} else len(value)]}{"ing" if value != "ARRAY" else ""}'

        elif prop_name == 'boolean_solver':
            notification = F'Solver: {prop}'

        elif isinstance(prop, str):
            notification = F'{prop_name.replace("_", " ").title()}: {prop}'

        elif isinstance(prop, float):
            notification = F'{self.operation.title()} {prop_name.partition("_")[-1].title()}: {getattr(self, prop_name):.3f}'

        elif isinstance(prop, bool):
            notification = F'{prop_name.replace("_", " ").title()} is {"En" if prop else "Dis"}abled'

        elif isinstance(prop, int):
            notification = F'{self.operation.title()} {prop_name.partition("_")[-1].title()}: {getattr(self, prop_name)}'

        return notification


    def execute(self, context):
        # global tracked_events
        global tracked_states

        if not tracked_states:
            BC = importlib.import_module(context.window_manager.bc.addon)

            # tracked_events = BC.addon.operator.shape.utility.tracked_events
            tracked_states = BC.addon.operator.shape.utility.tracked_states

        preference = addon.bc()

        self.shape_name = ''
        self.tracked_props = {
            'active_material': context.window_manager.Hard_Ops_material_options,
            'mode': tracked_states,
            'operation': tracked_states,
            'shape_type': tracked_states,
            'array_distance': tracked_states,
            'modified': tracked_states,
            'cancelled': tracked_states,
            'axis': context.scene.bc,
            'mirror_axis': context.scene.bc,
            'solidify_thickness': preference.shape,
            'inset_thickness': preference.shape,
            'circle_vertices': preference.shape,
            'bevel_segments': preference.shape,
            'bevel_width': preference.shape,
            'array_count': preference.shape,
            'show_shape': preference.behavior,
            'hops_mark': preference.behavior,
            'q_bevel': context.scene.bc,
            'wedge': preference.shape, #new additions
            'grid_units': preference.snap,
            'set_origin': preference.behavior,
            'show_shape': preference.behavior,
            'boolean_solver': preference.behavior,
            #'inset_slice': preference.behavior,
            'recut': preference.behavior,
            'origin': tracked_states,
        }

        self.forced = [
            'active_material',
            'mirror_axis',
            'dimensions',
            'boolean_solver',
        ]

        self.iter = [
            'mirror_axis',
        ]

        self.array_axis = 'X'

        self.exclude_notifications = [
            'modified',
            # 'cancelled',
        ]

        for prop_name, value in self.tracked_props.items():
            if prop_name not in self.iter:
                setattr(self, prop_name, copy(getattr(value, prop_name)) if value else None)
                continue

            setattr(self, prop_name, [copy(i) for i in getattr(value, prop_name)] if value else [])

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


    def modal(self, context, event):
        bc = context.scene.bc
        self.force = False

        default = 'Notification'
        info = default

        if bc.shape:
            if 'array_axis' not in self.tracked_props.keys():
                self.tracked_props['array_axis'] = bc.shape.bc

            elif 'dimensions' not in self.tracked_props.keys():
                self.tracked_props['dimensions'] = bc.shape
                self.dimensions = list(bc.shape.dimensions[:])
                self.iter.append('dimensions')

        for prop_name, value in self.tracked_props.items():
            if prop_name not in self.iter and getattr(self, prop_name) != getattr(value, prop_name):
                if bc.running:
                    setattr(self, prop_name, getattr(value, prop_name))

                info = self.notifications(prop_name)
                self.force = prop_name in self.forced
                continue

            elif prop_name not in self.iter:
                continue

            it = getattr(self, prop_name)
            for i in range(len(it)):
                if 'dimension' in prop_name and not bc.running:
                    break

                try: prop = getattr(value, prop_name)
                except: continue

                if it[i] != prop[i]:
                    getattr(self, prop_name)[i] = prop[i]

                    # axis = {
                    #     0: 'X',
                    #     1: 'Y',
                    #     2: 'Z',}

                    if 'axis' in prop_name:
                        if not it[i]:
                            continue

                        if info == default:
                            self.force = prop_name in self.forced
                            info = F'{prop_name.replace("_", " ").title()}  {"XYZ"[i]}'

                        # info += axis[i]+

                    elif self.operation == 'DRAW' and self.shape_type == 'NGON' and len(bc.shape.data.vertices) > 1:
                        self.force = True

                        delta = bc.shape.data.vertices[-1].co - bc.shape.data.vertices[-2].co
                        info = F'Edge Length: {dims_converter(delta.length):.3f}'
                        self.dimensions[0] = self.dimensions[1] = -1
                        continue

                    elif 'dimension' in prop_name and self.operation in {'DRAW', 'EXTRUDE', 'OFFSET'}:
                        if not it[i]:
                            continue

                        if info == default:
                            self.force = prop_name in self.forced

                            if i in {0, 1}:
                                x_dim = dims_converter(getattr(value, prop_name)[0])
                                y_dim = dims_converter(getattr(value, prop_name)[1])

                                info = F'{self.operation.title()}  X: {x_dim:.3f} Y: {y_dim:.3f}'
                                continue

                            elif self.operation != 'DRAW':
                                z_dim = dims_converter(getattr(value, prop_name)[i])
                                info = F'{"Extrude" if self.operation != "OFFSET" else "Dimension Z"}: {z_dim:.3f}'

                    elif self.operation in {'ROTATE', 'SCALE', 'MOVE'}:
                        if not it[i]:
                            continue

                        if info == default:
                            self.force = prop_name in self.forced
                            info = F'{self.operation.title()}'

        if not bc.running:
            info = 'Finished'

        if info != default and info != self.info and (self.modified or self.force):
            self.info = info

            new_notification(self.info)

        return {'PASS_THROUGH' if bc.running else 'FINISHED'}


def new_notification(header):
    ui = Master()

    preference = addon.bc()
    bc = bpy.context.scene.bc
    orient_method = preference.behavior.orient_method
    surface = preference.surface
    shape_type = ''
    behavior = ''
    mode = ''

    orientation = f' ({orient_method.capitalize()})' if surface == 'OBJECT' else ''
    modinfo = f'Modifiers: {len(bpy.context.active_object.modifiers[:])}' if bpy.context.active_object and len(bpy.context.selected_objects)==1 else ''

    if hasattr(bpy.context.scene, 'bc') and bpy.context.scene.bc.operator:
        ot = bpy.context.scene.bc.operator
        behavior = ot.behavior
        shape_type = f'{bc.operator.shape_type}'
        mode = f'{ot.mode}'

    draw_data = [
        [header.replace('None ', '')]]

    if addon.preference().display.bc_extra_notifications:
        ot = bpy.context.scene.bc.operator
        if bpy.app.version[:2] >= (2, 91) and hasattr(ot, 'datablock'):
            solver = 'FAST'
            for o in ot.datablock['targets']:
                for m in o.modifiers:
                    if m.type != 'BOOLEAN' or m.object != bc.shape:
                        continue

                    solver = m.solver
                    break

                break

            draw_data.insert(1, [f'Solver: {solver.capitalize()} (Alt + E)' if bpy.app.version[:2] >= (2, 91) else '', modinfo])
        draw_data.insert(2, [f'Orientation: {surface.capitalize()}{orientation}', f'{behavior.capitalize()} {mode.capitalize()} '])

    ui.receive_draw_data(draw_data=draw_data)
    ui.draw(draw_bg=addon.preference().ui.Hops_operator_draw_bg, draw_border=addon.preference().ui.Hops_operator_draw_border, compact_mode=True)


def dims_converter(dim):

    length = addon.preference().property.bc_dimensions_converter
    factor = 1

    if length == 'Kilometers':
        factor = 0.001
    elif length == 'Meters':
        factor = 1
    elif length == 'Centimeters':
        factor = 100
    elif length == 'Millimeters':
        factor = 1000
    elif length == 'Micrometers':
        factor = 1000000
    elif length == 'Miles':
        factor = 0.000621371
    elif length == 'Feet':
        factor = 3.28084
    elif length == 'Inches':
        factor = 39.37008
    elif length == 'Thousandth':
        factor = 39370.1

    return dim * factor



def register():
    register_class(HOPS_OT_bc_notifications)


def unregister():
    unregister_class(HOPS_OT_bc_notifications)
