from .utils import *


class Select:
    def setup(self):
        self.gizmo_radius = 30
        self.started_selection = False
        self.vert_count_draw = 0
        self.locked_bevel = False


    def update(self, context, event, data, op):

        # LOCKED : Bevel
        if self.locked_bevel == True:
            data.mouse_accumulation -= op.base_controls.mouse

            # Cancel
            if event.type == 'C' and event.value == "PRESS":
                self.locked_bevel = False
                data.modal_mesh_cancel()
                return

            # Unlock / Remove backup
            elif event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
                self.locked_bevel = False
                data.modal_mesh_confirm()
                return

            data.modal_mesh_update(context, event, with_mouse_warp=True)

            # --- BMESH --- #
            # Bevel
            edges = [e for e in data.bm.edges if e.select == True]

            if bpy.app.version < (2, 90, 0):
                bmesh.ops.bevel(
                    data.bm,
                    geom=edges,
                    offset=data.mouse_accumulation,
                    offset_type='OFFSET',
                    segments=2,
                    profile=1,
                    vertex_only=False,
                    clamp_overlap=False,
                    material=-1,
                    loop_slide=False,
                    mark_seam=False,
                    mark_sharp=False,
                    harden_normals=False)

            elif bpy.app.version >= (2, 90, 0):
                bmesh.ops.bevel(
                    data.bm,
                    geom=edges,
                    offset=data.mouse_accumulation,
                    offset_type='OFFSET',
                    segments=2,
                    profile=1,
                    affect='EDGES',
                    clamp_overlap=False,
                    material=-1,
                    loop_slide=False,
                    mark_seam=False,
                    mark_sharp=False,
                    harden_normals=False)
            return

        # Vert mode
        if event.type == 'ONE' and event.value == "PRESS":
            extend = True if event.shift else False
            bpy.ops.mesh.select_mode(use_extend=extend, type="VERT")

        # Edge mode
        elif event.type == 'TWO' and event.value == "PRESS":
            extend = True if event.shift else False
            bpy.ops.mesh.select_mode(use_extend=extend, type="EDGE")

        # Face mode
        elif event.type == 'THREE' and event.value == "PRESS":
            extend = True if event.shift else False
            bpy.ops.mesh.select_mode(use_extend=extend, type="FACE")

        # Select all
        elif event.type == 'A' and event.value == "PRESS" and event.alt == False and event.shift == False:
            bpy.ops.mesh.select_all(action='SELECT')
            data.save()

        # Deselect all
        elif event.type == 'A' and event.value == "PRESS" and event.alt == True and event.shift == False:
            bpy.ops.mesh.select_all(action='DESELECT')
            data.save()

        # Mark edges sharp
        elif event.type == 'E' and event.value == "PRESS":
            bpy.ops.hops.set_edit_sharpen()
            data.save()

        # Clean faces
        elif event.type == 'C' and event.value == "PRESS":
            bpy.ops.mesh.remove_doubles(threshold=addon.preference().property.meshclean_remove_threshold)
            bpy.ops.mesh.dissolve_limited(angle_limit=addon.preference().property.meshclean_dissolve_angle)

        # LOCK STATE : Boundary bevel
        elif event.type == 'B' and event.value == "PRESS":

            bpy.ops.mesh.region_to_loop()

            # If edge count is 0
            edge_count = len([e for e in data.bm.edges if e.select == True])
            if edge_count == 0:
                bpy.ops.hops.display_notification(info="Select an edge / edges")
                return
                    
            self.locked_bevel = True
            data.modal_mesh_start()

        # Edge loop
        elif event.type == 'L' and event.value == "PRESS" and event.shift == False:
            bpy.ops.mesh.loop_multi_select(ring=False)
            data.save()

        # Edge loop ring
        elif event.type == 'L' and event.value == "PRESS" and event.shift == True:
            bpy.ops.mesh.loop_multi_select(ring=True)
            data.save()

        # Quad
        elif event.type == 'Q' and event.value == "PRESS":
            bpy.ops.mesh.tris_convert_to_quads()
            data.save()

        # Tri
        elif event.type == 'T' and event.value == "PRESS":
            bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
            data.save()

        # Dissolve Selection
        elif event.type == 'X' and event.value == 'PRESS' and event.ctrl:
            bpy.ops.mesh.dissolve_mode(use_verts=True)
            data.save()

        # Face
        elif event.type == 'F' and event.value == "PRESS":
            bpy.ops.mesh.edge_face_add()
            data.save()

        # Grow / Shrink Selection
        elif event.ctrl == True:
            if op.base_controls.scroll > 0:
                bpy.ops.mesh.select_more(use_face_step=True)
                data.save()
            elif op.base_controls.scroll < 0:
                bpy.ops.mesh.select_less(use_face_step=True)
                data.save()

        # Increse / Decrease brush size
        if op.base_controls.scroll:
            if data.locked == False:
                if op.base_controls.scroll > 0:
                    if self.gizmo_radius + 5 < context.area.width * .25:
                        self.gizmo_radius += 5
                if op.base_controls.scroll < 0:
                    if self.gizmo_radius - 5 > 5:
                        self.gizmo_radius -= 5

        # Circle select
        if data.left_click_down:                            
            self.started_selection = True

            if op.base_controls.is_industry_standard:
                if event.alt:
                    self.started_selection = False
                    data.left_click_down = False
                    return

            # Click select
            if event.shift == False and event.ctrl == False:
                bpy.ops.mesh.select_all(action='DESELECT')
                bpy.ops.view3d.select_circle(
                    x=data.mouse_pos[0],
                    y=data.mouse_pos[1],
                    radius=self.gizmo_radius,
                    wait_for_input=True,
                    mode='ADD')

            # Append select
            elif event.shift == True and event.ctrl == False:
                bpy.ops.view3d.select_circle(
                    x=data.mouse_pos[0],
                    y=data.mouse_pos[1],
                    radius=self.gizmo_radius,
                    wait_for_input=True,
                    mode='ADD')

            # Subtract select
            elif event.ctrl == True:
                bpy.ops.view3d.select_circle(
                    x=data.mouse_pos[0],
                    y=data.mouse_pos[1],
                    radius=self.gizmo_radius,
                    wait_for_input=True,
                    mode='SUB')

        # Save undo after selection is over
        else:
            if self.started_selection == True:
                self.started_selection = False
                data.save()

        self.vert_count_draw = len( [v for v in data.bm.verts if v.select == True] )


    def help(self):
        return [
            ("Shift + L",     "Select loop ring"),
            ("L",             "Select Loop"),
            ("B",             "Boundary Bevel"),
            ("E",             "Toggle mark sharp"),
            ("Alt + A",       "Deselect all"),
            ("A",             "Select all"),
            ("C",             "Clean selection"),
            ("Q",             "Selection to Quads"),
            ("T",             "Selection to Tris"),
            ("F",             "Selection to Face"),
            ("Ctrl X",        "Dissolve Selection"),
            ("Ctrl + Scroll", "Grow / Shrink Selection"),
            ("3 / Shift",     "Select Faces / Append"),
            ("2 / Shift",     "Select Edges / Append"),
            ("1 / Shift",     "Select Verts / Append"),
            ("Scroll",        "Increase brush size"),
            ("Ctrl Click",    "Subtract Select"),
            ("Shift Click",   "Append Select"),
            ("Click",         "Select"),
            ("", "________SELECT________")]


    def draw_2d(self, context, data, op):

        draw_gizmo_circle(data, self.gizmo_radius)

        # Bevel locked
        if self.locked_bevel == True:
            draw_modal_mesh_label_2d(
                context,
                (context.area.width * .5, context.area.height * .5),
                data.mouse_accumulation,
                self.gizmo_radius)


    def draw_3d(self, context, data, op):
        pass