import time
import bpy

from bpy.types import Panel

from .... utility import tool, addon
from ... import toolbar
from ... operator.shape.utility import tracked_events, tracked_states


# TODO: ctrl, alt, shift modifier key bahavior states
class BC_PT_help_general(Panel):
    bl_label = F'Help{" " * 44}{toolbar.version}'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = '.workspace'
    bl_options = {'HIDE_HEADER'}
    bl_parent_id = 'BC_PT_help'


    def draw(self, context):
        preference = addon.preference()
        bc = context.scene.bc
        op = toolbar.option()
        snap = bc.snap.operator if bc.snap.operator and hasattr(bc.snap.operator, 'handler') else None

        unmodified = tracked_states.operation in {'DRAW', 'EXTRUDE'} and not tracked_states.modified
        indentation = '           '
        sep = '-   '
        nav_type = 'Rotate' if not tracked_events.shift else 'Pan'
        cut = 'Lazorcut' if tracked_states.thin else 'Cut'
        single_selected = len(context.selected_objects) == 1

        layout = self.layout

        row = layout.row()
        if not self.is_popover:
            row.label(text=F'{indentation * 3}{toolbar.version}')

        sub = row.row()
        sub.alignment = 'RIGHT'
        ot = sub.operator('bc.help_link', text='', icon='QUESTION', emboss=False)

        if self.is_popover or context.region.type == 'UI':
            ot.use_url = True

        if not bc.running:
            edit_mode = tool.active().mode == 'EDIT_MESH'
            use_make = not context.selected_objects[:] and not edit_mode

            if use_make:
                row = layout.row()
                row.alert = True if tracked_states.mode != 'MAKE' else False
                row.label(text=F'Select Mesh to {"Cut" if tracked_states.mode != "MAKE" else "Align"}', icon='INFO') # icon='ERROR')

                # row = layout.row()
                # row.alert = True if tracked_states.mode != 'MAKE' else False
                # row.label(text='  Using make & Aligning to floor')

            elif preference.surface == 'OBJECT' and not tracked_states.active_only:
                layout.label(text=F'Draw On{" the" if single_selected else ""} Mesh{"" if single_selected else "es"} to {"Cut" if tracked_states.mode != "MAKE" else "Align"}', icon='INFO')
                layout.label(text='           Off Mesh: View Align')

            elif preference.surface == 'VIEW':
                layout.label(text=F'{"Cutting" if tracked_states.mode != "MAKE" else "Aligning to"} View-Aligned Only', icon='INFO')

            elif not tracked_states.active_only:
                layout.label(text='Adjust Surface Options', icon='INFO')

            else:
                layout.label(text=F'{"Cutting" if tracked_states.mode != "MAKE" else "Aligning to"} Only Active', icon='INFO')

            layout.separator()

            make = tracked_states.mode == 'MAKE'
            layout.label(text=F'{sep}{tracked_states.mode.title() if not use_make else "Make"} {"Object" if single_selected or tracked_states.active_only else "Selected" if not make and not use_make else ""}', icon='MOUSE_LMB_DRAG')

            layout.separator()

            if addon.preference().snap.enable and not bc.snap.operator:
                layout.label(text='Enable Snapping', icon='EVENT_CTRL')
            elif bc.snap.operator and preference.snap.grid:
                layout.label(text=f'Change Unit Size: {preference.snap.increment:.2f}', icon='MOUSE_MMB')
            if snap and preference.snap.grid and preference.snap.increment_lock and snap.handler.grid.display:
                layout.label(text=F'{sep}Disable Snapping', icon='EVENT_ESC')
                layout.separator()

            if bc.snap.operator and hasattr(bc.snap.operator, 'grid_handler'):
                grid_handler = bc.snap.operator.grid_handler

                row = layout.row(align=True)
                row.alignment = 'LEFT'
                row.label(text='/', icon='EVENT_TAB')
                row.label(text=F'{sep}{"Freeze" if not grid_handler.frozen else "Unfreeze"}', icon='EVENT_SPACEKEY')

                if grid_handler.mode != 'EXTEND' and grid_handler.snap_type != 'DOTS':
                    row = layout.row(align=True)
                    row.alignment = 'LEFT'
                    row.label(text='', icon='EVENT_CTRL')
                    row.label(text='/', icon='MOUSE_RMB')
                    row.label(text=F'{sep}Extend', icon='EVENT_E')

                row = layout.row(align=True)
                row.label(text='', icon='EVENT_SHIFT')
                row.label(text='Subdivide', icon='MOUSE_MMB')

                if grid_handler.frozen:
                    layout.label(text=F'{sep}Disable Snapping', icon='EVENT_ESC')

                if grid_handler.snap_type == 'DOTS':
                    if grid_handler.nearest_dot:
                        row = layout.row(align=True)
                        row.label(text='', icon='EVENT_CTRL')
                        row.label(text='Cycle Dot alignment', icon='MOUSE_MMB')

                        layout.label(text='Switch to Grid', icon='EVENT_G')

                    # row = layout.row(align=True)
                    # row.label(text='', icon='EVENT_SHIFT')
                    # row.label(text='Subdivide face', icon='MOUSE_MMB')

                else:
                    # if grid_handler.mode != 'NONE' or (grid_handler.mode == 'MOVE' and not grid_handler.mode.frozen):
                    #     layout.label(text='Confirm operation', icon='MOUSE_LMB')
                    #     layout.label(text='Cancel operation', icon='MOUSE_RMB')

                    if grid_handler.mode != 'MOVE':
                        layout.label(text=F'{sep}Move', icon='EVENT_G')

                    if grid_handler.mode != 'SCALE':
                        layout.label(text=F'{sep}Scale', icon='EVENT_S')

                    if grid_handler.mode != 'ROTATE':
                        layout.label(text=F'{sep}Rotate', icon='EVENT_R')

                    else:
                        row = layout.row(align=True)

                        if grid_handler.rotation_axis != 'X':
                            row.label(text='', icon='EVENT_X')

                        if grid_handler.rotation_axis != 'Y':
                            row.label(text='', icon='EVENT_Y')

                        if grid_handler.rotation_axis != 'Z':
                            row.label(text='', icon='EVENT_Z')

                        row.label(text=F'{sep}Change Axis')

                    row = layout.row(align=True)
                    row.alignment = 'LEFT'
                    row.label(text='', icon='EVENT_SHIFT')
                    row.label(text=F'{sep}Knife Project', icon='EVENT_K')

                if grid_handler.snap_type != 'DOTS' and grid_handler.frozen:
                    layout.label(text=F'{sep}Align', icon='EVENT_A')

                layout.separator()

            layout.label(text=F'{sep}Box Helper' if preference.keymap.d_helper else F'{sep}Pie Menu', icon='EVENT_D')

            if preference.keymap.alt_scroll_shape_type:
                row = layout.row(align=True)
                row.label(text='', icon='EVENT_ALT')
                row.label(text=F'{sep}Change Shape Type', icon='MOUSE_MMB')

            row = layout.row(align=True)
            row.label(text='', icon='EVENT_CTRL')
            row.label(text=F'{sep}Pie Menu' if preference.keymap.d_helper else F'{sep}Box Helper', icon='EVENT_D')

            row = layout.row(align=True)
            row.label(text='', icon='EVENT_SHIFT')
            row.label(text=F'{sep}Surface Options', icon='EVENT_V')

            if tracked_states.shape_type == 'CUSTOM':
                layout.separator()
                layout.label(text=F'{sep}Active Object to Custom', icon='EVENT_C')

            return

        if tracked_events.mmb:
            layout.label(text=F'{sep}Confirm {nav_type}', icon='MOUSE_MMB')

            if not tracked_events.shift:
                layout.separator()

                layout.label(text=F'{sep}Axis Snap', icon='EVENT_ALT')

            return

        if tracked_states.operation != 'NONE':
            icon = 'MOUSE_LMB_DRAG' if tracked_events.lmb else 'MOUSE_MOVE'
            layout.label(text=F'{sep}Adjust {tracked_states.operation.title()}', icon=icon)

        if tracked_states.shape_type == 'NGON' and tracked_states.operation == 'DRAW':
            layout.label(text=F'{sep}Confirm Point', icon='MOUSE_LMB')

        elif tracked_events.lmb and tracked_states.operation == 'NONE' and not tracked_states.rmb_lock:
            cut_type = cut if tracked_states.operation != 'MAKE' else 'Shape'
            layout.label(text=F'{sep}Confirm {cut_type if tracked_states.operation != "JOIN" else "Join"}', icon='MOUSE_LMB')

        elif tracked_events.lmb and not tracked_states.rmb_lock:
            if unmodified and tracked_states.operation == 'EXTRUDE':
                cut_type = cut if tracked_states.operation != 'MAKE' else 'Shape'
                layout.label(text=F'{sep}Confirm {cut_type if tracked_states.operation != "JOIN" else "Join"}', icon='MOUSE_LMB')
            else:
                layout.label(text=F'{sep}Confirm {tracked_states.operation.title()}', icon='MOUSE_LMB')

        elif tracked_states.operation != 'NONE' and not tracked_states.thin:
            layout.label(text=F'{sep}Confirm {tracked_states.operation.title()}', icon='MOUSE_LMB')

        elif not tracked_states.rmb_lock:
            cut_type = cut if tracked_states.operation != 'MAKE' else 'Shape'
            layout.label(text=F'{sep}Confirm {cut_type if tracked_states.operation != "JOIN" else "Join"}', icon='MOUSE_LMB')

        layout.label(text=F'{sep}{nav_type} View', icon='MOUSE_MMB')

        if (tracked_states.shape_type in {'NGON','BOX'} or bc.operator.ngon_fit) and not tracked_states.extruded and tracked_states.operation in {'NONE', 'DRAW'}:
            if len(bc.shape.data.vertices) > 2:
                layout.label(text=F'{sep}{"Lock Shape" if tracked_states.operation == "DRAW" else "Adjust Point"}', icon='MOUSE_RMB')
                if tracked_states.shape_type == 'NGON':
                    layout.label(text=F'{sep}Backspace Point', icon='BACK')

                if bc.shader and bc.shader.widgets and bc.shader.widgets.active and bc.shader.widgets.active.operation == 'DRAW':
                    row = layout.row(align=True)
                    row.alignment = 'LEFT'
                    row.label(text='', icon='EVENT_SHIFT')
                    row.label(text='/', icon='MOUSE_LMB')
                    row.label(text=F'{sep}BWeight/Bevel', icon='MOUSE_MMB')

            else:
                layout.label(text=F'{sep}Cancel', icon='MOUSE_RMB')

        else:
            cancel_type = '' if tracked_states.operation == 'NONE' or not tracked_states.modified else F' {tracked_states.operation.title()}'
            layout.label(text=F'{sep}Lock Shape' if tracked_events.lmb and tracked_states.operation != 'NONE' else F'{sep}Cancel{cancel_type}', icon='MOUSE_RMB')

        layout.separator()

        if tracked_states.operation in {'MOVE', 'ROTATE', 'SCALE', 'ARRAY'}:
            layout.separator()

            row = layout.row(align=True)

            if bc.axis != 'X':
                row.label(text='', icon='EVENT_X')

            if bc.axis != 'Y':
                row.label(text='', icon='EVENT_Y')

            if bc.axis != 'Z':
                row.label(text='', icon='EVENT_Z')

            row.label(text=F'{sep}Change Axis')

        if tracked_states.operation in {'SOLIDIFY', 'BEVEL', 'TAPER'}:
            row = layout.row(align=True)
            row.label(text='', icon='EVENT_SHIFT')
            row.label(text=F'{sep}Reset Adjustment', icon='EVENT_R')

        layout.separator()

        if tracked_states.operation != 'NONE':
            layout.label(text=F'{sep}Lock Shape', icon='EVENT_TAB')

        layout.label(text=F'{sep}{"Disable " if preference.display.wire_only else ""}Wire', icon='EVENT_H')

        layout.separator()

        if tracked_states.operation != 'MOVE':
            layout.label(text=F'{sep}Move', icon='EVENT_G')

        if tracked_states.operation != 'SCALE':
            layout.label(text=F'{sep}Scale', icon='EVENT_S')

        if tracked_states.operation != 'ROTATE':
            layout.label(text=F'{sep}Rotate', icon='EVENT_R')

        if tracked_states.operation == 'NONE':
            row = layout.row(align=True)
            row.label(text='', icon='EVENT_CTRL')
            row.label(text=F'{sep}Rotate by 90\u00b0', icon='EVENT_R')

        if tracked_states.shape_type == 'CUSTOM' or bc.shape.bc.applied or bc.shape.bc.applied_cycle or bc.operator.ngon_fit:
            row = layout.row(align=True)
            row.label(text='', icon='EVENT_SHIFT')
            row.label(text=F'{sep}Rotate 90\u00b0 in Bounds', icon='EVENT_R')

        layout.separator()

        if tracked_states.operation != 'EXTRUDE':
            operation = 'Extrude' if tracked_states.operation != 'EXTRUDE' else 'Offset'
            layout.label(text=F'{sep}{operation}', icon='EVENT_E')

        if tracked_states.operation != 'OFFSET':
            row = layout.row(align=True)
            row.label(text=F'{sep}Offset', icon='EVENT_O')

        if tracked_states.operation in {'EXTRUDE','OFFSET'} and preference.keymap.alt_double_extrude:
            layout.label(text=F'{sep}{tracked_states.operation.capitalize()} Both Ways', icon='EVENT_ALT')

        #if preference.shape.wedge:
        row = layout.row(align=True)
        #row.label(text='', icon='EVENT_SHIFT')
        row.label(text=F'{sep}{"Wedge"}', icon='EVENT_W')

        if tracked_states.operation != 'TAPER':
            row = layout.row(align=True)
            row.label(text='', icon='EVENT_SHIFT')

            if preference.keymap.shift_operation_enable and preference.keymap.shift_operation == 'TAPER':
                row.label(text=F'{sep}Taper')
            else:
                row.label(text=F'{sep}Taper', icon='EVENT_T')

        else:
            row = layout.row(align=True)
            row.label(text='', icon='EVENT_SHIFT')
            row.label(text=F'{sep}Reset & Exit Taper', icon='EVENT_T')

        if tracked_states.shape_type == 'BOX':
            row = layout.row(align=True)
            row.label(text='', icon='EVENT_SHIFT')
            row.label(text=F'{sep}Grid Adjust', icon='EVENT_G')

        layout.separator()

        row = layout.row(align=True)
        row.label(text='', icon='EVENT_ALT')
        row.label(text=F'{sep}Switch Solver ({preference.behavior.boolean_solver.capitalize()})', icon='EVENT_E')

        if tracked_states.operation in {'NONE', 'EXTRUDE', 'OFFSET'}:
            row = layout.row(align=True)
            row.label(text='', icon='EVENT_SHIFT')
            row.label(text=F'{sep}Move boolean mod', icon='MOUSE_MMB')

        row = layout.row(align=True)
        row.label(text='', icon='EVENT_ALT')
        row.label(text=F'{sep}Scroll Cutter History', icon='MOUSE_MMB')

        row = layout.row(align=True)
        row.label(text='', icon='EVENT_SHIFT')
        row.label(text=F'{sep}Flip Shape Z', icon='EVENT_F')

        if tracked_states.operation != 'INSET' or not preference.behavior.inset_bevel:
            row = layout.row(align=True)
            row.label(text=F'{sep}Cycle Cutters', icon='EVENT_C')

        layout.label(text=F'{sep}Live', icon='EVENT_L')

        layout.separator()

        if tracked_states.operation != 'BEVEL':
            layout.label(text=F'{sep}Bevel', icon='EVENT_B')

        elif not bc.bevel:
            layout.label(text=F'{sep}Contour Bevel', icon='EVENT_Q')
            row = layout.row(align=True)
            row.label(text='', icon='EVENT_SHIFT')
            row.label(text=F'{sep}Backface Bevel', icon='EVENT_Q')

        if tracked_states.operation != 'SOLIDIFY':
            name = 'Solidify' if not bc.bevel else 'Bevel'
            layout.label(text=F'{sep}{name}', icon='EVENT_T')

        if tracked_states.operation != 'ARRAY':
            layout.label(text=F'{sep}Array', icon='EVENT_V')

        elif tracked_states.operation == 'ARRAY' and not bc.shape.bc.array_circle:
            layout.label(text=F'{sep}Radial Array', icon='EVENT_V')

        layout.separator()

        if tracked_states.mode == 'CUT':
            layout.label(text=F'{sep}Slice', icon='EVENT_X')

        elif tracked_states.mode == 'SLICE':
            layout.label(text=F'{sep}Intersect', icon='EVENT_X')

        elif tracked_states.mode == 'INTERSECT':
            layout.label(text=F'{sep}Inset', icon='EVENT_X')

        else:
            layout.label(text=F'{sep}Cut', icon='EVENT_X')

        if tracked_states.mode == 'SLICE':
            row = layout.row(align=True)
            row.label(text='', icon='EVENT_ALT')
            row.label(text=F'{sep}{"Disable " if preference.behavior.recut else ""}Recut', icon='EVENT_X')

        if tracked_states.mode == 'INSET' and not bc.bevel:
            row = layout.row(align=True)
            row.label(text='', icon='EVENT_ALT')
            row.label(text=F'{sep}{"Disable " if preference.behavior.inset_slice else ""}Inset Slice', icon='EVENT_X')

        if context.selected_objects or tool.active().mode == 'EDIT_MESH':
            layout.label(text=F'{sep}{"Knife" if tracked_states.mode != "KNIFE" else "Cut"}', icon='EVENT_K')
            layout.label(text=F'{sep}{"Join" if tracked_states.mode != "JOIN" else "Cut"}', icon='EVENT_J')
            layout.label(text=F'{sep}{"Inset" if tracked_states.mode != "INSET" else "Cut"}', icon='EVENT_I')
            layout.label(text=F'{sep}{"Extract" if tracked_states.mode != "EXTRACT" else "Cut"}', icon='EVENT_Y')
            layout.label(text=F'{sep}{"Make" if tracked_states.mode != "MAKE" else "Cut"}', icon='EVENT_A')

        layout.separator()

        if tracked_states.operation == 'NONE':
            layout.label(text=F'{sep}Box Helper' if preference.keymap.d_helper else F'{sep}Pie Menu', icon='EVENT_D')

            row = layout.row(align=True)
            row.label(text='', icon='EVENT_CTRL')
            row.label(text=F'{sep}Box Helper' if not preference.keymap.d_helper else F'{sep}Pie Menu', icon='EVENT_D')

            row = layout.row(align=True)
            row.label(text='', icon='EVENT_ALT')
            row.label(text=F'{sep}Toggle Dots', icon='EVENT_D')

            # elif tracked_states.shape_type == 'CUSTOM':
                # layout.separator()
                # layout.label(text='Active Object as Custom Cutter', icon='EVENT_C')

        if tracked_states.operation != 'NONE' and tracked_states.operation == 'SOLIDIFY':
            if not tracked_states.mode == 'INSET':
                layout.label(text=F'1 2 3   Solidify Type')
        else:
            layout.label(text=F'1 2 3   Mirror Axis (shift - flip)')

            row = layout.row(align=True)
            row.label(text=F'; (SEMI COLON) {sep}Mirror Gizmo')

        layout.label(text='. (PERIOD)    Change origin')


class BC_PT_help_general_npanel_tool(Panel):
    bl_label = 'Interaction'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'
    bl_parent_id = 'BC_PT_help_npanel_tool'
    bl_options = {'HIDE_HEADER'}


    def draw(self, context):
        BC_PT_help_general.draw(self, context)


class BC_PT_help_general_npanel(Panel):
    bl_label = 'Interaction'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'BoxCutter'
    bl_parent_id = 'BC_PT_help_npanel'
    bl_options = {'HIDE_HEADER'}


    def draw(self, context):
        BC_PT_help_general.draw(self, context)
