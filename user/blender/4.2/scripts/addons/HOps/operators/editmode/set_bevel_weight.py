import bpy
import bmesh
from bpy.props import BoolProperty
from ... utility import addon


class HOPS_OT_SetEditSharpen(bpy.types.Operator):
    bl_idname = "hops.set_edit_sharpen"
    bl_label = "Hops Set Sharpen"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Mark Ssharp / Unmark Toggle"

    dont_affect_bevel: BoolProperty(name="Don't affect bevel weight",
                                    description="Don't affect bevel weight that was set manually",
                                    default=False)

    @classmethod
    def poll(cls, context):

        if context.active_object is not None:
            object = context.active_object
            return(object.type == 'MESH' and context.mode == 'EDIT_MESH')
        return False

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.prop(self, "dont_affect_bevel")

    def execute(self, context):

        # TODO move it away from bmesh to ops to speed it up

        selected_objs = bpy.context.selected_objects
        if context.active_object not in selected_objs:
            selected_objs.append(context.active_object)

        bms = {}
        for obj in selected_objs:
            if obj.mode == 'EDIT':
                bms[obj] = bmesh.from_edit_mesh(obj.data)

        mselected = []
        for obj in selected_objs:
            if obj.mode == 'EDIT':
                for edge in bms[obj].edges:
                    if edge.select:
                        mselected.append(edge)
                        break

        for obj in selected_objs:
            if obj.mode == 'EDIT':
                me = obj.data
                bm = bms[obj]

                if bpy.app.version[0] >= 4:
                    bw = bm.edges.layers.float.get('bevel_weight_edge')
                    if bw is None:
                        bw = bm.edges.layers.float.new('bevel_weight_edge')
                else:
                    bw = bm.edges.layers.bevel_weight.verify()

                if bpy.app.version[0] >= 4:
                    cr = bm.edges.layers.float.get('crease_edge')
                    if cr is None:
                        cr = bm.edges.layers.float.new('crease_edge')
                else:
                    cr = bm.edges.layers.crease.verify()

                selected = [e for e in bm.edges if e.select]

                if mselected:
                    if self.sync_apply_seam(me, selected):
                        self.update_mbs(bms)
                        return {'FINISHED'}
                    if self.sync_apply_crease(me, cr, selected):
                        self.update_mbs(bms)
                        return {'FINISHED'}
                    if self.sync_apply_sharps(me, selected):
                        self.update_mbs(bms)
                        return {'FINISHED'}

                if not mselected:
                    for e in bm.edges:
                        if e.calc_face_angle(0) >= addon.preference().property.sharpness:
                            if addon.preference().property.sharp_use_crease:
                                e[cr] = 1
                            if addon.preference().property.sharp_use_sharp:
                                e.smooth = False
                            if addon.preference().property.sharp_use_seam:
                                e.seam = True
                            if addon.preference().property.sharp_use_bweight:
                                if e[bw] == 0:
                                    e[bw] = 1
                else:
                    if any(e[bw] == 1 for e in selected):
                        for e in selected:
                            if self.dont_affect_bevel:
                                if addon.preference().property.sharp_use_bweight:
                                    if e[bw] == 1:
                                        e[bw] = 0
                                if addon.preference().property.sharp_use_crease:
                                    e[cr] = 0
                                if addon.preference().property.sharp_use_sharp:
                                    e.smooth = True
                                if addon.preference().property.sharp_use_seam:
                                    e.seam = False

                            else:
                                if addon.preference().property.sharp_use_bweight:
                                    e[bw] = 0
                                if addon.preference().property.sharp_use_crease:
                                    e[cr] = 0
                                if addon.preference().property.sharp_use_sharp:
                                    e.smooth = True
                                if addon.preference().property.sharp_use_seam:
                                    e.seam = False
                    else:
                        for e in selected:
                            if self.dont_affect_bevel:
                                if addon.preference().property.sharp_use_bweight:
                                    if e[bw] == 0:
                                        e[bw] = 1
                                    else:
                                        e[bw] = 0
                                if addon.preference().property.sharp_use_crease:
                                    if e[cr] == 1:
                                        e[cr] = 0
                                    else:
                                        e[cr] = 1
                                if addon.preference().property.sharp_use_sharp:
                                    e.smooth = not e.smooth
                                if addon.preference().property.sharp_use_seam:
                                    e.seam = not e.seam
                            else:
                                if addon.preference().property.sharp_use_bweight:
                                    e[bw] = 1
                                if addon.preference().property.sharp_use_crease:
                                    if e[cr] == 1:
                                        e[cr] = 0
                                    else:
                                        e[cr] = 1
                                if addon.preference().property.sharp_use_sharp:
                                    e.smooth = not e.smooth
                                if addon.preference().property.sharp_use_seam:
                                    e.seam = not e.seam

        self.update_mbs(bms)
        return {'FINISHED'}

    def update_mbs(self, bms):
        for obj in bms:
            bmesh.update_edit_mesh(obj.data)

    def sync_apply_seam(self, me, edges):
        '''Sync the seams instead of toggle.'''

        if not addon.preference().property.sharp_use_bweight:
            if not addon.preference().property.sharp_use_crease:
                if not addon.preference().property.sharp_use_sharp:
                    if addon.preference().property.sharp_use_seam:

                        mark_seams = True
                        if any(e for e in edges if e.seam):
                            mark_seams = False

                        if mark_seams:
                            for e in edges:
                                e.seam = True
                        else:
                            for e in edges:
                                e.seam = False
                        # bmesh.update_edit_mesh(me)
                        return True
        return False

    def sync_apply_crease(self, me, cr, edges):
        '''Sync the seams instead of toggle.'''

        if not addon.preference().property.sharp_use_bweight:
            if not addon.preference().property.sharp_use_seam:
                if not addon.preference().property.sharp_use_sharp:
                    if addon.preference().property.sharp_use_crease:

                        mark_crease = True
                        if any(e for e in edges if e[cr] == 1):
                            mark_crease = False

                        if mark_crease:
                            for e in edges:
                                e[cr] = 1
                        else:
                            for e in edges:
                                e[cr] = 0
                        # bmesh.update_edit_mesh(me)
                        return True
        return False

    def sync_apply_sharps(self, me, edges):
        '''Sync the seams instead of toggle.'''

        if not addon.preference().property.sharp_use_bweight:
            if not addon.preference().property.sharp_use_seam:
                if not addon.preference().property.sharp_use_crease:
                    if addon.preference().property.sharp_use_sharp:

                        mark_sharp = True
                        if any(e for e in edges if e.smooth == False):
                            mark_sharp = False

                        if mark_sharp:
                            for e in edges:
                                e.smooth = False
                        else:
                            for e in edges:
                                e.smooth = True
                                
                        # bmesh.update_edit_mesh(me)
                        return True
        return False
