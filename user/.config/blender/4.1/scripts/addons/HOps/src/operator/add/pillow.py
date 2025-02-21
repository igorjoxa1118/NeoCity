import bpy, bmesh



class HOPS_OT_ADD_pillow(bpy.types.Operator):
    bl_idname = "hops.add_pillow"
    bl_label = "Add pillow"
    bl_options = {"REGISTER", "UNDO", "GRAB_CURSOR", "BLOCKING"}
    bl_description = """Create pillow with cloth sim"""



    def execute(self, context):

        bpy.ops.object.select_all(action='DESELECT')

        pillow_mesh = bpy.data.meshes.new('Pillow')

        pillow_obj = bpy.data.objects.new('Pillow', pillow_mesh)

        bm = bmesh.new()

        bmesh.ops.create_grid(bm, x_segments = 1, y_segments = 1, size = 1)

        for f in bm.faces:
            f.smooth = True

        bmesh.ops.inset_individual(bm, faces = bm.faces, thickness = 0.6, use_relative_offset = 0, depth = 0.1)


        bmesh.ops.subdivide_edges(bm, edges = bm.edges, cuts = 1, use_grid_fill = True)

        
        bm.to_mesh(pillow_mesh)
        context.collection.objects.link(pillow_obj)
        context.view_layer.objects.active = pillow_obj
        pillow_obj.select_set(True)
        pillow_obj.matrix_world.translation = context.scene.cursor.location

        mirror = pillow_obj.modifiers.new('Mirro', 'MIRROR')
        mirror.use_axis = [False, False, True]
        mirror.use_clip = True

        subsurf = pillow_obj.modifiers.new('Subsurf', 'SUBSURF')
        subsurf.levels = subsurf.render_levels = 3
        subsurf.subdivision_type = 'SIMPLE'

        cloth = pillow_obj.modifiers.new('Cloth', 'CLOTH')
        cloth.settings.quality = 3
        cloth.settings.use_pressure = True
        cloth.settings.uniform_pressure_force = 3
        cloth.settings.shrink_min = -0.3
        cloth.settings.effector_weights.gravity = 0

        cloth.settings.bending_stiffness = 0

        bpy.ops.screen.frame_jump(end=False)

        return({'FINISHED'})