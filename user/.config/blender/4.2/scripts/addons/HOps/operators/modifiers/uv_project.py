import bpy, math, pathlib
from ... utility import addon
from ...ui_framework.operator_ui import Master


class HOPS_OT_MOD_UV_Project(bpy.types.Operator):
    bl_idname = 'hops.mod_uv_project'
    bl_label = 'Add UV Project modifier'
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = '''LMB - Add a UV Project modifier and empties
Shift + LMB - Also add a grid material
Ctrl + Shift + LMB - Use a custom grid image
Ctrl + LMB  - Copy projectors from active to selected

'''


    filter_glob: bpy.props.StringProperty(default='*.png;*.jpg;*.jpeg;*.tga;*.tif;*.tiff', options={'HIDDEN'})
    filepath: bpy.props.StringProperty(options={'HIDDEN'})
    ctrl: bpy.props.BoolProperty(options={'HIDDEN'})
    shift: bpy.props.BoolProperty(options={'HIDDEN'})


    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.mode == 'OBJECT' and obj.type == 'MESH'


    def invoke(self, context, event):
        self.filepath = ''
        self.ctrl = event.ctrl
        self.shift = event.shift

        if self.ctrl and not self.shift:
            active = context.active_object
            selected = [o for o in context.selected_objects if o is not active]

            if not active or not selected:
                
                return {'CANCELLED'}

            active_uv_project = None

            for mod in reversed(active.modifiers):
                if mod.type == 'UV_PROJECT':
                    active_uv_project = mod
                    break

            if not active_uv_project:

                return {'CANCELLED'}

            for obj in selected:
                for mod in reversed(obj.modifiers):
                    if mod.type == 'UV_PROJECT':
                        mod.projector_count = active_uv_project.projector_count
                        for act_proj, s_proj in zip(active_uv_project.projectors, mod.projectors):
                            s_proj.object = act_proj.object
                        
                        break

            return {'FINISHED'}

        if self.ctrl and self.shift:
            context.window_manager.fileselect_add(self)
            return {'RUNNING_MODAL'}

        return self.execute(context)


    def execute(self, context):
        context.active_object.select_set(True)
        selected = context.selected_objects
        bpy.ops.object.select_all(action='DESELECT')

        obj = context.active_object
        size = (obj.dimensions[2] / obj.scale[2] / 2) if obj.dimensions[2] else 1

        con = self.create_empty(f'{obj.name}_triplanar_controller', 'SPHERE', size / 4, obj)
        context.view_layer.objects.active = con
        con.location.z = size * 2
        con.select_set(True)

        xp = self.create_empty(f'{obj.name}_triplanar_x+', 'SINGLE_ARROW', size, con)
        xn = self.create_empty(f'{obj.name}_triplanar_x-', 'SINGLE_ARROW', size, con)
        yp = self.create_empty(f'{obj.name}_triplanar_y+', 'SINGLE_ARROW', size, con)
        yn = self.create_empty(f'{obj.name}_triplanar_y-', 'SINGLE_ARROW', size, con)
        zp = self.create_empty(f'{obj.name}_triplanar_z+', 'SINGLE_ARROW', size, con)
        zn = self.create_empty(f'{obj.name}_triplanar_z-', 'SINGLE_ARROW', size, con)

        xp.rotation_euler = [math.radians(90), 0, math.radians(90)]
        xn.rotation_euler = [math.radians(90), 0, math.radians(-90)]
        yp.rotation_euler = [math.radians(-90), math.radians(180), 0]
        yn.rotation_euler = [math.radians(90), 0, 0]
        zp.rotation_euler = [0, 0, 0]
        zn.rotation_euler = [0, math.radians(180), 0]

        if self.shift:
            mat, width, height = self.create_material(f'{obj.name}_grid', self.filepath)

            if width > height:
                stretch = width / height

                for empty in (xp, xn, yp, yn, zp, zn):
                    empty.scale[0] = stretch

            elif height > width:
                stretch = height / width

                for empty in (xp, xn, yp, yn, zp, zn):
                    empty.scale[1] = stretch


        for obj in selected:
            if obj.type != 'MESH':
                continue

            if not obj.data.uv_layers:
                obj.data.uv_layers.new()

            mod = next((m for m in reversed(obj.modifiers) if m.type == 'UV_PROJECT'), None)
            if mod is None:
                mod = obj.modifiers.new(name='HOPS UV Project', type='UV_PROJECT')
            mod.projector_count = 6

            for index, empty in enumerate([xp, xn, yp, yn, zp, zn]):
                mod.projectors[index].object = empty

            if self.shift:
                obj.data.materials.clear()
                obj.data.materials.append(mat)

        prefs = addon.preference()
        count = len(selected)
        self.draw_ui(prefs, count)
        return {'FINISHED'}


    def create_empty(self, name, display_type, display_size, parent):
        empty = bpy.data.objects.new(name, None)
        empty.empty_display_type = display_type
        empty.empty_display_size = display_size
        empty.parent = parent

        for col in parent.users_collection:
            if col not in empty.users_collection:
                col.objects.link(empty)

        return empty


    def create_material(self, name, path):
        mat = bpy.data.materials.new(name)

        mat.use_nodes = True
        tree = mat.node_tree

        out = tree.nodes['Material Output']
        bsd = tree.nodes['Principled BSDF']

        hsv = tree.nodes.new('ShaderNodeHueSaturation')
        img = tree.nodes.new('ShaderNodeTexImage')
        mpn = tree.nodes.new('ShaderNodeMapping')
        tco = tree.nodes.new('ShaderNodeTexCoord')

        hsv.location = [-200, 300]
        img.location = [-500, 300]
        mpn.location = [-700, 300]
        tco.location = [-900, 300]

        tree.links.new(bsd.inputs['Base Color'], hsv.outputs['Color'])
        tree.links.new(hsv.inputs['Color'], img.outputs['Color'])
        tree.links.new(img.inputs['Vector'], mpn.outputs['Vector'])
        tree.links.new(mpn.inputs['Vector'], tco.outputs['UV'])

        img.image = self.get_image(path)
        width, height = img.image.size

        return mat, width, height


    def get_image(self, path):
        if path:
            path = bpy.path.abspath(path)
            path = pathlib.Path(path).resolve()

            image = bpy.data.images.get(path.name)

            if not image:
                image = bpy.data.images.new(path.name, 0, 0)
                image.source = 'FILE'
                image.filepath = str(path)

        else:
            image = bpy.data.images.get('Color Grid')

            if not image:
                image = bpy.data.images.new('Color Grid', 1024, 1024)
                image.generated_type = 'COLOR_GRID'

        return image


    def draw_ui(self, prefs, count):
        ui = Master()

        draw_data = [
            ['UV Project'],
            ['Empties created', (count * 7)],
            ['Modifiers added', (count)],
        ]

        draw_bg = prefs.ui.Hops_operator_draw_bg
        draw_border = prefs.ui.Hops_operator_draw_border

        ui.receive_draw_data(draw_data=draw_data)
        ui.draw(draw_bg=draw_bg, draw_border=draw_border)
