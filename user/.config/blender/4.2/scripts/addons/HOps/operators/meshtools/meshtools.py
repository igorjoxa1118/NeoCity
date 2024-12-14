import bpy, bmesh, math, mathutils
from mathutils import Quaternion
from bpy.props import IntProperty, BoolProperty, FloatProperty
from ... utils.addons import addon_exists
#from ... utils.operations import invoke_individual_resizing
from ... utility import addon
from ... ui_framework.master import Master
from ...ui_framework.utils.mods_list import get_mods_list
from ... utility.base_modal_controls import Base_Modal_Controls

# Cursor Warp imports
from ... utils.toggle_view3d_panels import collapse_3D_view_panels
from ... utils.modal_frame_drawing import draw_modal_frame
from ... utils.cursor_warp import mouse_warp
from ... utility import method_handler


class HOPS_OT_VertcircleOperator(bpy.types.Operator):
    bl_idname = "view3d.vertcircle"
    bl_label = "Vert To Circle"
    bl_options = {"REGISTER", "UNDO", "BLOCKING"}
    bl_description = """Vert To_Circle

LMB - Convert vert to circle
LMB + Ctrl - Convert nth vert to circle
LMB + Shift - Use new circle method

req. Looptools
"""

    new_method: BoolProperty(name="Use New Method", description="Use the new method for creating circles", default=False)
    divisions: IntProperty(name="Division Count", description="Amount Of Vert divisions", default=4, min=1, max=64)
    segments: IntProperty(name="Target Segments", description="Target amount of circle segments", default=16, min=4, max=256)
    radius: FloatProperty(name="Circle Radius", description="Circle Radius", default=0.2, min=0.001)
    message = "< Default >"
    nth_mode: BoolProperty(name='Nth Mode', description='Skip every other vert', default=False)
    face_mode: BoolProperty(name='Face Mode', description='Switch to face select mode', default=False)

    @classmethod
    def poll(cls, context):
        return getattr(context.active_object, "type", "") == "MESH"


    def draw(self, context):
        layout = self.layout

        if addon_exists("mesh_looptools"):
            layout.prop(self, 'new_method')

        row = layout.row()
        row.prop(self, 'nth_mode')
        row.prop(self, 'face_mode')

        if self.new_method:
            layout.prop(self, 'segments')
            layout.prop(self, 'radius')

        else:
            layout.prop(self, 'divisions')
            layout.prop(self, 'radius')


    def execute(self, context):
        self.object = context.object
        self.bm = bmesh.from_edit_mesh(self.object.data)
        self.make_circles(context)
        toggle_mode()
        return {'FINISHED'}


    def invoke(self, context, event):

        if 'vertex_only' in bmesh.ops.bevel.__doc__:
            self.bm_bevel = bm_bevel_28
        else:
            self.bm_bevel = bm_bevel_29

        self.base_controls = Base_Modal_Controls(context=context, event=event)
        self.master = None

        self.c_offset = 40

        self.div_past = self.divisions
        self.object = context.active_object

        self.nth_mode = event.ctrl
        self.face_mode = False

        self.new_method = event.shift
        if not addon_exists("mesh_looptools"):
            self.new_method = True

        self.object.update_from_editmode()
        self.bm = bmesh.from_edit_mesh(self.object.data)
        self.backup = self.object.data.copy()

        self.make_circles(context)

        #UI System
        self.master = Master(context=context)
        self.master.only_use_fast_ui = True
        self.original_tool_shelf, self.original_n_panel = collapse_3D_view_panels()
        self.draw_handle = bpy.types.SpaceView3D.draw_handler_add(self.safe_draw_shader, (context,), 'WINDOW', 'POST_PIXEL')
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


    def modal (self, context, event):

        # Base Systems
        self.master.receive_event(event=event)
        self.base_controls.update(context, event)
        mouse_warp(context, event)

        if self.base_controls.pass_through:
            return {'PASS_THROUGH'}

        self.bm = bmesh.from_edit_mesh(self.object.data)

        if self.base_controls.scroll:
            if self.new_method:
                self.segments += self.base_controls.scroll
            else:
                self.divisions += self.base_controls.scroll

            restore(self.bm, self.backup)
            self.make_circles(context)

        elif self.base_controls.mouse:
            if addon.preference().property.modal_handedness == 'LEFT':
                self.radius -= self.base_controls.mouse
            else:
                self.radius += self.base_controls.mouse

            if self.new_method:
                restore(self.bm, self.backup)
                self.make_circles(context)
            else:
                bpy.ops.mesh.looptools_circle(custom_radius=True, radius=self.radius)

        elif event.type == 'M' and event.value == 'PRESS':
            if addon_exists("mesh_looptools"):
                self.new_method = not self.new_method
                restore(self.bm, self.backup)
                self.make_circles(context)

        if self.base_controls.confirm:
            if event.shift:
                bpy.ops.mesh.select_mode(type='FACE')
                self.face_mode = True

            bpy.data.meshes.remove(self.backup)
            self.remove_shader()
            toggle_mode()
            collapse_3D_view_panels(self.original_tool_shelf, self.original_n_panel)
            self.master.run_fade()
            return {'FINISHED'}

        if self.base_controls.cancel:
            restore(self.bm, self.backup)
            bmesh.update_edit_mesh(self.object.data, destructive=True)
            bpy.data.meshes.remove(self.backup)
            toggle_mode()
            self.remove_shader()
            collapse_3D_view_panels(self.original_tool_shelf, self.original_n_panel)
            self.master.run_fade()
            return {'CANCELLED'}

        self.draw_ui(context)
        context.area.tag_redraw()
        return {'RUNNING_MODAL'}


    def make_circles(self, context):
        '''Turn verts into circles with one of two methods'''

        if self.nth_mode:
            bpy.ops.mesh.select_mode(type='VERT')
            bpy.ops.mesh.select_nth()

        if self.new_method or not addon_exists("mesh_looptools"):
            new_circle(self.object, self.bm, self.segments, self.radius)
        else:
            setup_verts(self.object, self.bm, self.divisions, self.c_offset, self.bm_bevel)
            bpy.ops.mesh.looptools_circle(custom_radius=True, radius=self.radius)

        if self.face_mode:
            bpy.ops.mesh.select_mode(type='FACE')


    def draw_ui(self, context):

        self.master.setup()

        # -- Fast UI -- #
        if self.master.should_build_fast_ui():

            string = 'Segments' if self.new_method else 'Divisions'
            number = self.segments if self.new_method else self.divisions

            # Main
            win_list = []
            if addon.preference().ui.Hops_modal_fast_ui_loc_options != 1:
                win_list.append("{:.0f}".format(number))
                win_list.append("{:.3f}".format(self.radius))
            else:
                if self.new_method:
                    win_list.append("Circle (alt)")
                else:
                    win_list.append("Circle")
                win_list.append("{}: {:.0f}".format(string, number))
                win_list.append("Radius: {:.3f}".format(self.radius))

            # Help
            help_items = {"GLOBAL" : [], "STANDARD" : []}

            help_items["GLOBAL"] = [
                ("M", "Toggle mods list"),
                ("H", "Toggle help"),
                ("~", "Toggle UI Display Type"),
                ("O", "Toggle viewport rendering")
            ]

            help_items["STANDARD"] = [
                ("Shift + LMB", "Apply and switch to face select mode"),
                ("LMB", "Apply"),
                ("RMB", "Cancel"),
                ("Scroll", "Add divisions"),
                ("Mouse", "Adjust the radius")
            ]

            if addon_exists("mesh_looptools"):
                help_items["STANDARD"].append(["M", "Switch Circle Method"])
            else:
                help_items["STANDARD"].append([" ", "LOOPTOOLS not enabled"])

            # Mods
            mods_list = get_mods_list(mods=bpy.context.active_object.modifiers)

            self.master.receive_fast_ui(win_list=win_list, help_list=help_items, image="Tthick", mods_list=mods_list)

        self.master.finished()

    ####################################################
    #   CURSOR WARP
    ####################################################

    def safe_draw_shader(self, context):
        method_handler(self.draw_shader,
            arguments = (context,),
            identifier = 'UI Framework',
            exit_method = self.remove_shader)


    def remove_shader(self):
        '''Remove shader handle.'''

        if self.draw_handle:
            self.draw_handle = bpy.types.SpaceView3D.draw_handler_remove(self.draw_handle, "WINDOW")


    def draw_shader(self, context):
        '''Draw shader handle.'''

        draw_modal_frame(context)


def toggle_mode():
    '''Toggle to object mode and back, to fix the bmesh curse'''

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.mode_set(mode='EDIT')


def new_circle(obj, bm, segments, radius):
    '''Cut circles around selected vertices'''
    selected = [v for v in bm.verts if v.select and v.is_manifold and not v.is_boundary]
    bpy.ops.mesh.select_all(action='DESELECT')

    for vert in selected:
        edges = vert.link_edges[:]
        lengths = [e.calc_length() for e in edges]
        clamped = min(lengths + [radius])

        for edge, length in zip(edges, lengths):
            factor = clamped / length if length > 0 else 0
            bmesh.utils.edge_split(edge, vert, factor)

        for face in vert.link_faces[:]:
            loop = next(l for l in face.loops if l.vert is vert)
            vert_a = loop.link_loop_next.vert
            vert_b = loop.link_loop_prev.vert

            angle = loop.calc_angle()
            if not loop.is_convex:
                angle = math.tau - angle

            num = round(segments * angle / math.tau)
            vec = vert_a.co - vert.co
            nor = face.normal

            quats = [Quaternion(nor, angle * i / num) for i in range(1, num)]
            coords = [quats[i - 1] @ vec + vert.co for i in range(1, num)]
            bmesh.utils.face_split(face, vert_a, vert_b, coords=coords)

        for face in vert.link_faces[:]:
            face.select = True

    bmesh.update_edit_mesh(obj.data)


def setup_verts(object, bm, divisions, c_offset, bevel):
    '''Set up verts to be converted to circle by loop tools.'''

    selected_verts = [v for v in bm.verts if v.select]
    result = bevel(bm, input_geo=selected_verts, divisions=divisions, c_offset=c_offset)

    faces = result['faces']
    faces_clean = bmesh.ops.dissolve_faces(bm, faces=faces)

    for f in faces_clean['region']:
        f.select = True

    bmesh.update_edit_mesh(object.data, destructive=True)


def restore (bm, mesh):
    '''Reasign original mesh data back to the selected object.'''

    bmesh.ops.delete(bm, geom=bm.verts, context='VERTS')
    bm.from_mesh(mesh)


def bm_bevel_28(bm, input_geo=[], divisions=2, c_offset=40):
    return bmesh.ops.bevel(bm, geom=input_geo, vertex_only=True , offset=c_offset,
loop_slide=True, offset_type='PERCENT', clamp_overlap=True, segments=divisions, profile=0)

def bm_bevel_29(bm, input_geo=[], divisions=2, c_offset=40):
    return bmesh.ops.bevel(bm, geom=input_geo, affect='VERTICES', offset=c_offset,
loop_slide=True, offset_type='PERCENT', clamp_overlap=True, segments=divisions, profile=0)
