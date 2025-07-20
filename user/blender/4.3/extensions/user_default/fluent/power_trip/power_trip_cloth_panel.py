import bpy
from bpy.types import Operator

from ..Tools.translation import translate
from ..Tools.helper import *
from ..UI.Helpers.viewport_drawing import *
import tempfile
import subprocess
import webbrowser
import platform
from ..UI.Helpers.ui_management import FLUENT_ui_management


class FLUENT_OT_ClothPanel(Operator):
    """Turn faces into cloth"""
    bl_idname = "fluent.clothpanel"
    bl_label = "Fluent cloth panel"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.object and context.object.mode == 'OBJECT':
            return True
        else:
            return False

    def polish(self, obj):
        subdiv_mod = obj.modifiers.new(type='SUBSURF', name='Subdivision')
        subdiv_mod.render_levels = 2
        subdiv_mod.levels = 2
        subdiv_mod.show_viewport = True
        subdiv_mod.show_expanded = False
        displace_mod = obj.modifiers.new(type='DISPLACE', name='Displace')
        displace_mod.strength = 0.001
        displace_mod.show_viewport = True
        displace_mod.show_expanded = False
        for m in obj.material_slots:
            m.material.use_nodes = True

    def end(self):
        bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')

    def modal(self, context, event):
        context.area.tag_redraw()

        if event.type not in ['RET', 'NUMPAD_ENTER', 'ESC'] and bpy.context.active_object and bpy.context.active_object.mode == 'EDIT':
            return {'PASS_THROUGH'}

        if self.status == 'WAIT_SELECTION' and event.type == 'ESC' and event.value == 'PRESS':
            bpy.data.objects.remove(self.copy, do_unlink=True)
            self.obj.hide_set(False)
            self.end()
            return{'FINISHED'}

        if event.type in ['RET', 'NUMPAD_ENTER'] and event.value == 'PRESS' and self.status == 'WAIT_SELECTION':
            # vérifie qu'au moins une face est sélectionnée
            face_selected = False
            bpy.ops.object.mode_set(mode='OBJECT')
            for p in self.copy.data.polygons:
                if p.select:
                    face_selected = True
                    break
            if face_selected is False:
                self.report({'ERROR'}, "At least, you have to select one face.")
                try:
                    bpy.data.objects.remove(self.cloth_obj, do_unlink=True)
                except:
                    pass
                try:
                    bpy.data.objects.remove(self.copy, do_unlink=True)
                except:
                    pass
                self.obj.hide_set(False)
                return {'FINISHED'}

            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.duplicate()
            bpy.ops.mesh.separate(type='SELECTED')
            bpy.ops.object.mode_set(mode='OBJECT')
            self.cloth_obj = bpy.context.selected_objects[1]
            active_object('SET', self.cloth_obj, True)

            if get_addon_preferences().cloth_separate_face:
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_mode(type='FACE')
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.mesh.edge_split(type='EDGE')
                bpy.ops.mesh.separate(type='LOOSE')
                bpy.ops.object.mode_set(mode='OBJECT')
                for o in bpy.context.selected_objects:
                    self.panels_list.append([o, None])
            else:
                if get_addon_preferences().cloth_remesh:
                    bpy.ops.object.mode_set(mode='EDIT')
                    bpy.ops.mesh.select_mode(type='FACE')
                    bpy.ops.mesh.select_all(action='SELECT')
                    bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
                bpy.ops.object.mode_set(mode='OBJECT')
                self.panels_list.append([self.cloth_obj, None])
            self.obj.hide_set(False)
            bpy.data.objects.remove(self.copy, do_unlink=True)

            self.status = 'FACE_EXTRACTED'

        if event.type in ['RET', 'NUMPAD_ENTER'] and event.value == 'PRESS' and self.status == 'WAIT_FOR_GATHERING':
            bpy.ops.object.mode_set(mode='OBJECT')
            # lance la simulation
            bpy.context.scene.frame_set(0)
            bpy.ops.screen.animation_play()
            self.status = 'SIMULATION_IN_PROGRESS'

        if self.status == 'FACE_EXTRACTED':
            # Remesh la/les face(s) en vue de la simulation
            for panel in self.panels_list:
                if get_addon_preferences().cloth_remesh:
                    panel[1] = Remesh_Mangement()
                    if get_addon_preferences().cloth_remesh_tool == 'QUADREMESHER':
                        panel[1].set_remesher('QUADREMESHER')
                    elif get_addon_preferences().cloth_remesh_tool == 'INSTANT_MESH':
                        panel[1].set_remesher('INSTANT_MESH')
                    panel[1].set_source_obj(panel[0])
                    panel[1].prepare_remesh(same=False)
                else:
                    area = 0
                    for p in panel[0].data.polygons:
                        area += p.area
                    self.nb_face_final = get_addon_preferences().cloth_resolution
                    if self.nb_face_final > len(panel[0].data.polygons):
                        n_final = math.log(self.nb_face_final) / math.log(4)
                        n_actuel = math.log(len(panel[0].data.polygons)) / math.log(4)
                        SUBSURF = panel[0].modifiers.new(type='SUBSURF', name='Subdivision')
                        SUBSURF.subdivision_type = 'SIMPLE'
                        SUBSURF.levels = round(n_final - n_actuel)
                        active_object('SET', panel[0], True)
                        bpy.ops.object.modifier_apply(modifier=SUBSURF.name)
            if get_addon_preferences().cloth_remesh:
                self.status = 'READY_FOR_REMESHING'
            else:
                self.status = 'REMESHING_DONE'

        if self.status == 'READY_FOR_REMESHING':
            panel = self.panels_list[0]
            if panel[1].get_status() == 'READY':
                panel[1].remesh()
                self.status = 'REMESHING_IN_PROGRESS'

        if self.status == 'REMESHING_IN_PROGRESS':
            panel = self.panels_list[0]
            self.status = panel[1].remesh_trigger()

        if self.status == 'REMESHING_DONE':
            try:
                self.cloth_obj = self.panels_list[0][1].get_remeshed_obj()
            except:
                self.cloth_obj = self.panels_list[0][0]
            self.cloth_obj.name = 'Cloth'
            active_object('SET', self.cloth_obj, True)
            bpy.ops.object.shade_smooth()
            bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')

            # retravaille le maillage
            if get_addon_preferences().cloth_topology == 'POKE':
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_mode(type='FACE')
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.mesh.poke()
                bpy.ops.object.mode_set(mode='OBJECT')
            elif get_addon_preferences().cloth_topology == 'TRIANGULATE':
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_mode(type='FACE')
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
                bpy.ops.object.mode_set(mode='OBJECT')
            elif get_addon_preferences().cloth_topology == 'GARMENT':
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_mode(type='FACE')
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.mesh.subdivide()
                bpy.ops.mesh.poke()
                bpy.ops.object.mode_set(mode='OBJECT')
                decimate = self.cloth_obj.modifiers.new(type='DECIMATE', name='Decimate')
                decimate.ratio = 0.2
                bpy.ops.object.modifier_apply(modifier=decimate.name)
                smooth = self.cloth_obj.modifiers.new(type='CORRECTIVE_SMOOTH', name='Corrective Smooth')
                smooth.factor = 1
                smooth.iterations = 200
                smooth.use_pin_boundary = True
                smooth.use_only_smooth = True
                bpy.ops.object.modifier_apply(modifier=smooth.name)

            # prépare le vertex group
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_mode(type='EDGE')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.001)
            bpy.ops.mesh.region_to_loop()
            bpy.ops.transform.edge_crease(value=1)
            bpy.ops.object.mode_set(mode='EDIT')
            for l in range(get_addon_preferences().cloth_pin_loop-1):
                bpy.ops.mesh.select_more()
            bpy.ops.object.mode_set(mode='OBJECT')
            vg = self.cloth_obj.vertex_groups.new(name="pin")
            v_selected = [v.index for v in self.cloth_obj.data.vertices if v.select]
            vg.add(v_selected, 1, 'ADD')

            # displace pour éviter l'overlapping
            displace_mod = self.cloth_obj.modifiers.new(type='DISPLACE', name='Displace')
            displace_mod.strength = 0.001
            displace_mod.show_expanded = False

            # ajout le modifier cloth
            cloth_mod = self.cloth_obj.modifiers.new(type='CLOTH', name='Cloth')
            cloth_mod.settings.quality = 6
            cloth_mod.settings.mass = 0.150
            cloth_mod.settings.tension_stiffness = get_addon_preferences().cloth_stiffness
            cloth_mod.settings.compression_stiffness = 5
            cloth_mod.settings.shear_stiffness = get_addon_preferences().cloth_stiffness
            cloth_mod.settings.bending_stiffness = 0.05
            cloth_mod.settings.tension_damping = 0
            cloth_mod.settings.compression_damping = 0
            cloth_mod.settings.shear_damping = 0
            cloth_mod.settings.air_damping = 1
            cloth_mod.settings.use_pressure = True
            cloth_mod.settings.uniform_pressure_force = get_addon_preferences().cloth_pressure
            cloth_mod.settings.vertex_group_mass = "pin"
            cloth_mod.settings.shrink_min = get_addon_preferences().cloth_shrink
            cloth_mod.settings.effector_weights.gravity = 0
            cloth_mod.collision_settings.use_self_collision = get_addon_preferences().cloth_self_collision
            cloth_mod.collision_settings.self_distance_min = .002
            cloth_mod.collision_settings.self_friction = 0
            cloth_mod.collision_settings.collision_quality = 12
            cloth_mod.show_expanded = False

            # ajoute le modifier collision à l'objet original
            if get_addon_preferences().cloth_pressure < 0:
                coll_mod = self.obj.modifiers.new(type='COLLISION', name='Collision')
                self.obj.collision.thickness_outer = 0.001

            if not get_addon_preferences().cloth_gathering:
                # lance la simulation
                bpy.context.scene.frame_set(0)
                bpy.ops.screen.animation_play()
                self.status = 'SIMULATION_IN_PROGRESS'
            else:
                self.status = 'WAIT_FOR_GATHERING'
                cloth_mod.settings.use_sewing_springs = True
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
                bpy.ops.mesh.delete(type='ONLY_FACE')
                bpy.ops.mesh.select_all(action='INVERT')
                bpy.ops.object.mode_set(mode='OBJECT')
                v_selected = [v.index for v in self.cloth_obj.data.vertices if v.select]
                vg.remove(v_selected)
                bpy.ops.object.mode_set(mode='EDIT')

        if self.status == 'SIMULATION_IN_PROGRESS' and event.type == 'TIMER':
            if event.value == 'PRESS' and event.type in {'ESC'} or bpy.context.scene.frame_current >= self.animation_range:
                self.status = 'SIMULATION_DONE'
                bpy.ops.screen.animation_cancel(restore_frame=False)
                if get_addon_preferences().cloth_freeze and self.cloth_obj:
                    apply_modifiers(self.cloth_obj)
                    if get_addon_preferences().cloth_remesh_after and get_addon_preferences().cloth_topology != 'QUAD':
                        self.panels_list_remesh_after_simulation.append([self.panels_list[0][1].get_remeshed_obj(), None])
                    else:
                        # displace_mod = self.cloth_obj.modifiers.new(type='DISPLACE', name='Displace')
                        # displace_mod.strength = 0.001
                        # displace_mod.show_expanded = False
                        subdiv_mod = self.cloth_obj.modifiers.new(type='SUBSURF', name='Subdivision')
                        subdiv_mod.render_levels = 1
                        subdiv_mod.levels = 1
                        subdiv_mod.show_viewport = True
                        subdiv_mod.show_expanded = False

        if self.status == 'SIMULATION_DONE':
            del self.panels_list[0]
            if len(self.panels_list):
                self.status = 'READY_FOR_REMESHING'
            else:
                self.status = 'ALL_REMESHING_DONE'

        if self.status == 'ALL_REMESHING_DONE':
            if len(self.panels_list_remesh_after_simulation):
                self.status = 'REMESHING_AFTER'
            else:
                self.polish(self.cloth_obj)
                self.end()
                return {'FINISHED'}

        if self.status == 'REMESHING_AFTER':
            for panel in self.panels_list_remesh_after_simulation:
                panel[1] = Remesh_Mangement()
                if get_addon_preferences().cloth_remesh_tool == 'QUADREMESHER':
                    panel[1].set_remesher('QUADREMESHER')
                elif get_addon_preferences().cloth_remesh_tool == 'INSTANT_MESH':
                    panel[1].set_remesher('INSTANT_MESH')
                panel[1].set_source_obj(panel[0])
                panel[1].prepare_remesh(same=True)
            self.status = 'REMESHING_AFTER_READY'

        if self.status == 'REMESHING_AFTER_READY' and event.type == 'TIMER':
            panel = self.panels_list_remesh_after_simulation[0]
            if panel[1].get_status() == 'READY':
                panel[1].remesh()
                self.status = 'REMESHING_IN_PROGRESS_AFTER'

        if self.status == 'REMESHING_IN_PROGRESS_AFTER' and event.type == 'TIMER':
            panel = self.panels_list_remesh_after_simulation[0]
            self.status = panel[1].remesh_trigger() + '_AFTER'

        if self.status == 'REMESHING_DONE_AFTER' and event.type == 'TIMER':
            self.panels_list_remesh_after_simulation[0][1].get_remeshed_obj().name = 'Cloth'
            self.polish(self.panels_list_remesh_after_simulation[0][1].get_remeshed_obj())
            # subdiv_mod = self.panels_list_remesh_after_simulation[0][1].get_remeshed_obj().modifiers.new(type='SUBSURF', name='Subdivision')
            # subdiv_mod.render_levels = 2
            # subdiv_mod.levels = 2
            # subdiv_mod.show_viewport = True
            # subdiv_mod.show_expanded = False
            # displace_mod = self.panels_list_remesh_after_simulation[0][1].get_remeshed_obj().modifiers.new(type='DISPLACE', name='Displace')
            # displace_mod.strength = 0.001
            # displace_mod.show_viewport = True
            # displace_mod.show_expanded = False
            del self.panels_list_remesh_after_simulation[0]
            if len(self.panels_list_remesh_after_simulation):
                self.status = 'REMESHING_AFTER_READY'
            else:
                self.end()
                return{'FINISHED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        # vérifications
        if active_object('GET'):
            bpy.ops.object.mode_set(mode='OBJECT')
        if get_addon_preferences().cloth_remesh_tool == 'QUADREMESHER':
            try:
                bpy.context.scene.qremesher.target_count = 1000
            except Exception as e:
                if str(e) == "'Scene' object has no attribute 'qremesher'":
                    make_oops([translate('quadRemesherSelectedNotActive'), translate('quadRemesherNotActive'), translate('activeQuadRemesher')], translate('howToUse'), 'ERROR')
                    return {'FINISHED'}
        elif get_addon_preferences().cloth_remesh_tool == 'INSTANT_MESH':
            exe = bpy.path.abspath(get_addon_preferences().instant_mesh_file)
            OS = platform.system()
            if OS == 'Windows' and not 'Instant Meshes.exe' in exe:
                make_oops([translate('wrongInstantMeshPath'),
                           translate('checkPreferences'),
                           translate('instantMeshWindows')], translate('howToUse'), 'ERROR')
                return {'FINISHED'}
            elif OS == 'Darwin' and not '.app/Contents/MacOS/Instant Meshes' in exe:
                make_oops([translate('wrongInstantMeshPath'),
                           translate('checkPreferences'),
                           translate('instantMeshMac')], translate('howToUse'), 'ERROR')
                return {'FINISHED'}
            elif OS == 'Linux' and not exe:
                make_oops([translate('instantMeshEmpty'), translate('checkPreferences')], translate('howToUse'), 'ERROR')
                return {'FINISHED'}

        self.obj = active_object()
        if not self.obj or not self.obj.type == 'MESH':
            make_oops([translate('selectAtLeastOneObject')], translate('howToUse'), 'ERROR')

        # création d'une copie de l'objet avec application des modifiers
        self.copy = duplicate(self.obj, '_wait_retopo')
        apply_modifiers(self.copy)
        self.obj.hide_set(True)

        # bascule en edit mode
        active_object('SET', self.copy, True)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
        bpy.ops.mesh.select_all(action='DESELECT')

        # autres variables
        self.cloth_obj = None
        self.status = 'WAIT_SELECTION'
        self.panels_list = []  # contient tous les panneaux de tissu. Chaque panneau est un tableau de 2 éléments [objet, remesh_manager]
        self.panels_list_remesh_after_simulation = []
        # self.build_step = 0
        self.animation_range = get_addon_preferences().cloth_end_frame

        if self.animation_range > bpy.context.scene.frame_end:
            bpy.context.scene.frame_end = self.animation_range + 25

        self.ui_management = FLUENT_ui_management(event)
        self.ui_management.refresh_side_infos([
            [translate('selectFaces'), ''],
            [translate('validate'), translate('enter')],
            [translate('cancel'), translate('escape')]
        ])

        bpy.context.scene.frame_set(0)
        self.timer = context.window_manager.event_timer_add(1 / 2, window=context.window)

        args = (self, context)
        self._handle = bpy.types.SpaceView3D.draw_handler_add(draw_callback_px, args, 'WINDOW', 'POST_PIXEL')
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


class Remesh_Mangement():
    def __init__(self):
        self.remesher = 'INSTANT_MESH'  # ou QUADREMESHER
        self.quadremesher_settings = {
            'adaptive_size': 0,
            'use_materials': False,
            'use_normals': False,
            'autodetect_hard_edges': False,
        }
        self.instant_mesh_data = {}
        self.source_obj = None
        self.remeshed_obj = None
        self.remeshed_obj_name = ''
        self.start_remeshing_time = None
        self.status = 'WAIT_SOURCE'

        self.nb_face_final = 0
        self.nb_vert_final = 0

    def set_source_obj(self, obj):
        obj.name = 'F_cloth_panel_wait_retopo'
        self.source_obj = obj
        self.remeshed_obj_name = 'Retopo_' + obj.name
        self.status = 'READY'

    def get_source_obj(self):
        return self.source_obj

    def set_remesher(self, type):
        self.remesher = type

    def set_quadremesher_setting(self, dico):
        self.quadremesher_settings = dico

    def get_remeshed_obj(self):
        return self.remeshed_obj

    def get_status(self):
        return self.status

    def remesh_trigger(self):
        temps_ecoule = time.time() - self.start_remeshing_time
        if self.remesher == 'INSTANT_MESH' and self.instant_mesh_data.get('exported') and self.instant_mesh_data['exported']:
            try:
                bpy.ops.wm.obj_import(
                    filepath=self.instant_mesh_data['output'],
                    use_split_objects=False,
                    forward_axis='NEGATIVE_Z',
                    up_axis='Y')
                imported_mesh = bpy.context.selected_objects[0]
                imported_mesh.name = self.remeshed_obj_name
                for edge in imported_mesh.data.edges:
                    edge.use_edge_sharp = False
                for other_obj in bpy.data.objects:
                    other_obj.select_set(state=False)
                imported_mesh.select_set(state=True)
                imported_mesh.active_material.use_nodes = False
                use_auto_smooth(imported_mesh.data, False)

                bpy.ops.mesh.customdata_custom_splitnormals_clear()

                active_object('SET', imported_mesh, True)
                os.remove(output)
                self.instant_mesh_data['exported'] = False
            except Exception as inst:
                print(inst)
                pass
        if bpy.data.objects.get(self.remeshed_obj_name):
            self.status = 'REMESHING_DONE'
            self.remeshed_obj = bpy.data.objects.get(self.remeshed_obj_name)
            bpy.data.objects.remove(self.source_obj, do_unlink=True)
            self.source_obj = None
        elif temps_ecoule > 40:
            self.status = 'ERROR_The remeshing fail.'
        return self.status

    def remesh(self):
        if self.remesher == 'QUADREMESHER':
            self.remesh_with_quadremesher()
        elif self.remesher == 'INSTANT_MESH':
            self.remesh_with_instant_mesh()

    def find_nb_vertices(self):
        try:
            n_final = round(math.log(self.nb_face_final) / math.log(4))
        except:
            n_final = 1
        u = 9
        a = 2
        for n in range(2, n_final):
            a = a + math.pow(2, n - 2)
            u = u + math.pow(2, 2 * n - 2) + a * math.pow(2, n)
        self.nb_vert_final = round(u)

    def prepare_remesh(self, same=False):
        if same:
            self.nb_face_final = len(self.source_obj.data.polygons)
            self.find_nb_vertices()
        else:
            # détermine nombre de face et vertices final
            area = 0
            for p in self.source_obj.data.polygons:
                area += p.area

            self.nb_face_final = get_addon_preferences().cloth_resolution
            self.find_nb_vertices()
            # triangule les faces
            active_object('SET', self.source_obj, True)
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_mode(type='FACE')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
            bpy.ops.object.mode_set(mode='OBJECT')

    def remesh_with_quadremesher(self):
        try:
            active_object('SET', self.source_obj, True)
            if self.nb_face_final == 0:
                self.nb_face_final = len(self.source_obj.data.polygons)
            bpy.context.scene.qremesher.target_count = round(self.nb_face_final)
            bpy.context.scene.qremesher.adaptive_size = self.quadremesher_settings['adaptive_size']
            bpy.context.scene.qremesher.use_materials = self.quadremesher_settings['use_materials']
            bpy.context.scene.qremesher.use_normals = self.quadremesher_settings['use_normals']
            bpy.context.scene.qremesher.autodetect_hard_edges = self.quadremesher_settings['autodetect_hard_edges']
            bpy.context.scene.qremesher.symmetry_x = False
            bpy.context.scene.qremesher.symmetry_y = False
            bpy.context.scene.qremesher.symmetry_z = False
            self.start_remeshing_time = time.time()
            self.status = 'REMESHING_IN_PROGRESS'
            bpy.ops.qremesher.remesh()
        except Exception as e:
            if str(e) == "'Scene' object has no attribute 'qremesher'":
                self.status = 'ERROR_You selected QuadRemesher in the preferences.#QuadRemesher seems to be desactivated.#Thanks to active it or change the remesher tool.'

    def remesh_with_instant_mesh(self):
        exe = bpy.path.abspath(get_addon_preferences().instant_mesh_file)
        projpath = bpy.data.filepath
        directory = os.path.dirname(projpath)

        orig = os.path.join(tempfile.gettempdir(), 'original.obj')
        output = os.path.join(tempfile.gettempdir(), 'out.obj')
        self.instant_mesh_data['output'] = output

        # if not self.exported:
        try:
            os.remove(orig)
        except:
            pass
        active_object('SET', self.source_obj, True)
        bpy.ops.wm.obj_export(
            filepath=orig,
            check_existing=False,
            forward_axis='NEGATIVE_Z',
            up_axis='Y',
            export_selected_objects=True,
            apply_modifiers=True)

        if self.nb_vert_final == 0:
            self.nb_face_final = len(self.source_obj.data.polygons)
            self.find_nb_vertices()
        options = ['-c', '0',
                   '-v', str(self.nb_face_final),
                   '-S', '2',
                   '-o', output,
                   '-D',
                   '-b']

        cmd = [exe] + options + [orig]

        try:
            self.start_remeshing_time = time.time()
            subprocess.run(cmd)
            self.instant_mesh_data['exported'] = True
            self.status = 'REMESHING_IN_PROGRESS'
        except:
            self.status = 'ERROR_Instant Mesh path is wrong. Check the preferences.'


class FLUENT_OT_ClothSettings(Operator):
    """Cloth simulation settings
Hold shift - Reset settings"""
    bl_idname = "fluent.clothsettings"
    bl_label = "Cloth settings"
    bl_options = {'REGISTER', 'UNDO'}

    cloth_remesh: bpy.props.BoolProperty(
        description="Remesh the selected faces",
        name="Remesh",
        default=True
    )
    cloth_topology: bpy.props.EnumProperty(
        name='Topology',
        items=(
            ("QUAD", "Quad", "Quad"),
            ("TRIANGULATE", "Triangulate", "Triangulate"),
            ("POKE", "Poke", "Poke"),
            ("GARMENT", "Garment", "Garment")
        ),
        default='QUAD'
    )
    cloth_remesh_after: bpy.props.BoolProperty(
        description="Remesh the simulation",
        name="Remesh after simulation",
        default=False
    )
    cloth_separate_face: bpy.props.BoolProperty(
        description="One panel by faces",
        name="Separate by faces",
        default=False
    )
    cloth_freeze: bpy.props.BoolProperty(
        description="Apply the simulation",
        name="Freeze",
        default=True
    )
    cloth_resolution: bpy.props.IntProperty(
        description="Face count",
        name="Face count",
        default=2000,
        min=0,
        step=10
    )
    cloth_shrink: bpy.props.FloatProperty(
        description="Shrink",
        name="Cloth shrink",
        default=-0.1,
        step=0.01
    )
    cloth_pressure: bpy.props.FloatProperty(
        description="Pressure",
        name="Cloth pressure",
        default=10,
        step=0.1
    )
    cloth_stiffness: bpy.props.FloatProperty(
        description="How much the cloth resist to the pressure",
        name="Stiffness",
        default=5,
        min=0
    )
    cloth_pin_loop: bpy.props.IntProperty(
        description="Number of edge loop from boundary edge use as pin group",
        name="Pin loop",
        min=1,
        default=2
    )
    cloth_end_frame: bpy.props.IntProperty(
        description="Simulation duration.",
        name="End frame",
        default=30,
        min=0
    )
    cloth_self_collision: bpy.props.BoolProperty(
        description="Self collision",
        name="Self collision",
        default=False
    )
    cloth_gathering: bpy.props.BoolProperty(
        description="gathering",
        name="Gathering",
        default=False
    )

    def execute(self, context):
        get_addon_preferences().cloth_remesh = self.cloth_remesh
        get_addon_preferences().cloth_triangulation = self.cloth_triangulation
        get_addon_preferences().cloth_topology = self.cloth_topology
        get_addon_preferences().cloth_remesh_after = self.cloth_remesh_after
        get_addon_preferences().cloth_freeze = self.cloth_freeze
        get_addon_preferences().cloth_resolution = self.cloth_resolution
        get_addon_preferences().cloth_shrink = self.cloth_shrink
        get_addon_preferences().cloth_pressure = self.cloth_pressure
        get_addon_preferences().cloth_stiffness = self.cloth_stiffness
        get_addon_preferences().cloth_pin_loop = self.cloth_pin_loop
        get_addon_preferences().cloth_end_frame = self.cloth_end_frame
        get_addon_preferences().cloth_separate_face = self.cloth_separate_face
        get_addon_preferences().cloth_self_collision = self.cloth_self_collision
        get_addon_preferences().cloth_gathering = self.cloth_gathering

        return {'FINISHED'}

    def invoke(self, context, event):
        if event.shift:
            get_addon_preferences().cloth_remesh = True
            get_addon_preferences().cloth_triangulation = False
            get_addon_preferences().cloth_topology = 'QUAD'
            get_addon_preferences().cloth_remesh_after = False
            get_addon_preferences().cloth_freeze = True
            get_addon_preferences().cloth_resolution = 4000
            get_addon_preferences().cloth_shrink = -0.2
            get_addon_preferences().cloth_pressure = 10
            get_addon_preferences().cloth_stiffness = 5
            get_addon_preferences().cloth_end_frame = 30
            get_addon_preferences().cloth_separate_face = False
            get_addon_preferences().cloth_self_collision = False
            get_addon_preferences().cloth_gathering = False
            return {'FINISHED'}
        else:
            self.cloth_remesh = get_addon_preferences().cloth_remesh
            self.cloth_triangulation = get_addon_preferences().cloth_triangulation
            self.cloth_topology = get_addon_preferences().cloth_topology
            self.cloth_remesh_after = get_addon_preferences().cloth_remesh_after
            self.cloth_freeze = get_addon_preferences().cloth_freeze
            self.cloth_resolution = get_addon_preferences().cloth_resolution
            self.cloth_shrink = get_addon_preferences().cloth_shrink
            self.cloth_pressure = get_addon_preferences().cloth_pressure
            self.cloth_stiffness = get_addon_preferences().cloth_stiffness
            self.cloth_pin_loop = get_addon_preferences().cloth_pin_loop
            self.cloth_end_frame = get_addon_preferences().cloth_end_frame
            self.cloth_separate_face = get_addon_preferences().cloth_separate_face
            self.cloth_self_collision = get_addon_preferences().cloth_self_collision
            self.cloth_gathering = get_addon_preferences().cloth_gathering
            return context.window_manager.invoke_props_dialog(self)


class FLUENT_OT_InstantMeshDownload(Operator):
    """Link to download Instant Mesh"""
    bl_idname = "fluent.instantmeshdownload"
    bl_label="Download Instant Mesh"

    def invoke(self, context, event):
        webbrowser.open('https://github.com/wjakob/instant-meshes')
        return {'FINISHED'}


classes = [FLUENT_OT_ClothPanel, FLUENT_OT_ClothSettings, FLUENT_OT_InstantMeshDownload]
