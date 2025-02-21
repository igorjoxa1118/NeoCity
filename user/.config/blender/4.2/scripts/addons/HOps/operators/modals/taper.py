import bpy
from mathutils import Matrix, Vector
from ...utility import math as hops_math

from ... utility import addon
from ... ui_framework.master import Master
from ... ui_framework.utils.mods_list import get_mods_list
from ... utility.base_modal_controls import Base_Modal_Controls

# Cursor Warp imports
from ... utils.toggle_view3d_panels import collapse_3D_view_panels
from ... utils.modal_frame_drawing import draw_modal_frame
from ... utils.cursor_warp import mouse_warp
from ... utility import method_handler


class wedge_pairs():
    def __init__(self):
        self.A = set()
        self.B = set()
        self.C = set()
        self.D = set()


class HOPS_OT_TaperOperator(bpy.types.Operator):
    bl_idname = "hops.taper"
    bl_label = "Taper"
    bl_options = {'REGISTER', 'UNDO', 'BLOCKING'}
    bl_description = """Taper
Taper side of an object using lattice
LMB - Create new lattice to deform the object
LMB+CTRL - Use last lattice in modifier stack
LMB+SHIFT - Use single lattice to deform multiple objects
"""

    taper_factor: bpy.props.FloatProperty(
        name = "Taper factor",
        description = "A relative value of taper",
        default = 1,
        min = 0)

    wedge_len_factor: bpy.props.FloatProperty(
        name = "Wedge length factor",
        description = "A relative value of factor",
        default = 0,
        min = -0.995,
        )

    wedge_side_factor: bpy.props.FloatProperty(
        name = "Wedge side factor",
        description = "A relative value of factor",
        default = 0,
        min = 0,
        max = 1
        )

    axis_items = [
        ('+X', "+X", "Taper on +X axis"),
        ('+Y', "+Y", "Taper on +Y axis"),
        ('+Z', "+Z", "Taper on +Z axis"),
        ('-X', "-X", "Taper on -X axis"),
        ('-Y', "-Y", "Taper on -Y axis"),
        ('-Z', "-Z", "Taper on -Z axis")
        ]

    axis: bpy.props.EnumProperty(
        name="Axis",
        description="Taper Axis",
        items=axis_items,
        default='-Z')

    wedge_type_items =[
        ('A', "A", "Wedge type A"),
        ('B', "B", "Wedge type B"),
        ('C', "C", "Wedge type C"),
        ('D', "D", "Wedge type D")]

    wedge_type: bpy.props.EnumProperty(
        name="Wedge type",
        description="Wedge type",
        items=wedge_type_items,
        default='A')

    valid_objects = {'MESH', 'CURVE', 'FONT'}

    @classmethod
    def poll(cls, context):
        return getattr(context.active_object, "type", "") in cls.valid_objects

    def invoke(self, context, event):

        self.lattice_back = []
        self.lattice_deletable = set()
        self.mods_deletable = set()
        self.lattices = set()
        self.wedge_mode = False

        objects = [o for o in context.selected_objects if o.type in self.valid_objects]

        if event.ctrl:
            for obj in objects:

                lattice = self.get_lattice(obj)

                if lattice:
                    self.lattices.add(lattice)
        elif event.shift:
            self.add_lattice_multi(objects)

        else:

            for obj in objects:
                self.add_lattice(obj)


        for lattice in self.lattices:
            if lattice in self.lattice_deletable:
                continue

            self.lattice_back.append(self.set_lattice(lattice))


        if not self.lattices:
            self.report({'INFO'}, "No lattices to work with")
            return {'CANCELLED'}

        self.sides= {
        "+X":set(),
        "+Y":set(),
        "+Z":set(),
        "-X":set(),
        "-Y":set(),
        "-Z":set(),

        }

        self.wedge_map = {
            "+X":wedge_pairs(),
            "+Y":wedge_pairs(),
            "+Z":wedge_pairs(),
            "-X":wedge_pairs(),
            "-Y":wedge_pairs(),
            "-Z":wedge_pairs(),

        }

        self.wedge_side_map = {
            'XA' : 'Y',
            'XB' : 'Z',
            'XC' : 'Y',
            'XD' : 'Z',

            'YA' : 'X',
            'YB' : 'Z',
            'YC' : 'X',
            'YD' : 'Z',

            'ZA' : 'X',
            'ZB' : 'Y',
            'ZC' : 'X',
            'ZD' : 'Y',

        }

        for index, point in enumerate(list(self.lattices)[0].data.points):
            if point.co.x > 0:
                self.sides["+X"].add(index)
                wedge = self.wedge_map["+X"]

                if point.co.y > 0:
                    wedge.A.add(index)
                else:
                    wedge.C.add(index)

                if point.co.z > 0:
                    wedge.B.add(index)
                else:
                    wedge.D.add(index)

            else:

                self.sides["-X"].add(index)
                wedge = self.wedge_map["-X"]

                if point.co.y > 0:
                    wedge.A.add(index)
                else:
                    wedge.C.add(index)

                if point.co.z > 0:
                    wedge.B.add(index)
                else:
                    wedge.D.add(index)


            if point.co.y > 0:
                self.sides["+Y"].add(index)
                wedge = self.wedge_map["+Y"]

                if point.co.x > 0:
                    wedge.A.add(index)
                else:
                    wedge.C.add(index)

                if point.co.z > 0:
                    wedge.B.add(index)
                else:
                    wedge.D.add(index)

            else:

                self.sides["-Y"].add(index)
                wedge = self.wedge_map["-Y"]

                if point.co.x > 0:
                    wedge.A.add(index)
                else:
                    wedge.C.add(index)

                if point.co.z > 0:
                    wedge.B.add(index)
                else:
                    wedge.D.add(index)



            if point.co.z > 0:
                self.sides["+Z"].add(index)
                wedge = self.wedge_map['+Z']

                if point.co.x > 0:
                    wedge.A.add(index)
                else:
                    wedge.C.add(index)

                if point.co.y > 0:
                    wedge.B.add(index)
                else:
                    wedge.D.add(index)


            else:
                self.sides["-Z"].add(index)
                wedge = self.wedge_map["-Z"]

                if point.co.x > 0:
                    wedge.A.add(index)
                else:
                    wedge.C.add(index)

                if point.co.y > 0:
                    wedge.B.add(index)
                else:
                    wedge.D.add(index)


        self.reset_lattices()
        for lattice in self.lattices:
            self.taper(lattice)

        # Base Systems
        self.master = Master(context=context)
        self.master.only_use_fast_ui = True
        self.base_controls = Base_Modal_Controls(context, event)
        self.original_tool_shelf, self.original_n_panel = collapse_3D_view_panels()
        self.draw_handle = bpy.types.SpaceView3D.draw_handler_add(self.safe_draw_shader, (context,), 'WINDOW', 'POST_PIXEL')

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


    def modal(self, context, event):

        # Base Systems
        self.master.receive_event(event=event)
        self.base_controls.update(context, event)
        mouse_warp(context, event)

        if self.base_controls.pass_through:
            return {'PASS_THROUGH'}

        elif self.base_controls.mouse:
            if self.wedge_mode:
                if event.ctrl:
                    self.wedge_side_factor += self.base_controls.mouse
                else:
                    self.wedge_len_factor += self.base_controls.mouse
            else:
                self.taper_factor += self.base_controls.mouse

        elif self.base_controls.scroll:

            if event.shift and self.wedge_mode:
                types = [item[0] for item in self.wedge_type_items]
                self.wedge_type = types[ ( types.index(self.wedge_type) + self.base_controls.scroll ) % len(types) ]
                self.report({'INFO'}, F"Wedge type:{self.wedge_type}")

            else:
                axes = [item[0] for item in self.axis_items]
                self.axis = axes[ ( axes.index(self.axis) + self.base_controls.scroll ) % len(axes) ]
                self.report({'INFO'}, F"Axis:{self.axis}")

            for lattice in self.lattices:
                for p in lattice.data.points:
                    p.co_deform = p.co


        elif event.type == 'ONE' and event.value == 'PRESS':
            if self.wedge_mode:
                self.wedge_len_factor = 0
            else:
                self.taper_factor = 1

        elif event.type == 'W' and event.value == 'PRESS':
            self.wedge_mode = not self.wedge_mode
            for lattice in self.lattices:
                for p in lattice.data.points:
                    p.co_deform = p.co

        elif event.type == 'X' and event.value == 'PRESS':
            self.reset_lattices()

            self.axis = '+X' if self.axis != '+X' else '-X'
            self.report({'INFO'}, F"Axis:{self.axis}")

        elif event.type == 'Y' and event.value == 'PRESS':
            self.reset_lattices()

            self.axis = '+Y' if self.axis != '+Y' else '-Y'
            self.report({'INFO'}, F"Axis:{self.axis}")

        elif event.type == 'Z' and event.value == 'PRESS':
            self.reset_lattices()

            self.axis = '+Z' if self.axis != '+Z' else '-Z'
            self.report({'INFO'}, F"Axis:{self.axis}")

        elif self.base_controls.confirm:

            self.remove_shader()
            collapse_3D_view_panels(self.original_tool_shelf, self.original_n_panel)
            self.master.run_fade()
            self.report({'INFO'}, "FINISHED")
            return {'FINISHED'}

        elif self.base_controls.cancel:

            for mod in self.mods_deletable:
                obj = mod.id_data
                obj.modifiers.remove(mod)

            for lattice in self.lattice_deletable:
                bpy.data.lattices.remove(lattice.data)

            for lattice, resolution , coords, interp in self.lattice_back:

                lattice.data.points_u = resolution[0]
                lattice.data.points_v = resolution[1]
                lattice.data.points_w = resolution[2]

                for point, back in zip(lattice.data.points, coords):
                    point.co_deform = back

                lattice.data.interpolation_type_u = interp[0]
                lattice.data.interpolation_type_v = interp[1]
                lattice.data.interpolation_type_w = interp[2]


            self.remove_shader()
            collapse_3D_view_panels(self.original_tool_shelf, self.original_n_panel)
            self.master.run_fade()
            self.report({'INFO'}, "CANCELLED")
            return {'CANCELLED'}

        deform = self.wedge if self.wedge_mode else self.taper

        for lat in self.lattices:
            deform(lat)

        self.draw_ui(context)
        context.area.tag_redraw()
        return {'RUNNING_MODAL'}


    def add_lattice(self, obj):
        lattice_data = bpy.data.lattices.new('Taper')
        lattice_obj = bpy.data.objects.new('Taper', lattice_data)
        collection = obj.users_collection[0]
        collection.objects.link(lattice_obj)
        lattice_obj.data.use_outside = True

        lattice_data.interpolation_type_u = 'KEY_LINEAR'
        lattice_data.interpolation_type_v = 'KEY_LINEAR'
        lattice_data.interpolation_type_w = 'KEY_LINEAR'

        eval = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())

        sca = Matrix.Diagonal(eval.dimensions).to_4x4()
        rot = obj.matrix_world.to_quaternion().to_matrix().to_4x4()
        loc = Matrix.Translation(hops_math.coords_to_center( [obj.matrix_world @ Vector(v) for v in eval.bound_box] ))

        lattice_obj.parent = obj
        lattice_obj.matrix_parent_inverse = obj.matrix_world.inverted()
        lattice_obj.matrix_world =loc @ rot @ sca
        lattice_mod = obj.modifiers.new(name ='Lattice', type = 'LATTICE')
        lattice_mod.object = lattice_obj

        self.lattices.add(lattice_obj)
        self.lattice_deletable.add(lattice_obj)
        self.mods_deletable.add(lattice_mod)

    def add_lattice_multi(self, objects):
        lattice_data = bpy.data.lattices.new('Taper')
        lattice_obj = bpy.data.objects.new('Taper', lattice_data)
        collection = bpy.context.collection
        collection.objects.link(lattice_obj)
        lattice_obj.data.use_outside = True

        lattice_data.interpolation_type_u = 'KEY_LINEAR'
        lattice_data.interpolation_type_v = 'KEY_LINEAR'
        lattice_data.interpolation_type_w = 'KEY_LINEAR'

        bounds = hops_math.coords_to_bounds( [ obj.matrix_world @ Vector(v) for obj in objects for v in obj.bound_box ] )

        loc = Matrix.Translation(hops_math.coords_to_center(bounds))
        sca = Matrix.Diagonal(hops_math.dimensions(bounds)).to_4x4()

        lattice_obj.matrix_world = loc @ sca

        for obj in objects:
            lattice_mod = obj.modifiers.new(name ='Lattice', type = 'LATTICE')
            lattice_mod.object = lattice_obj
            self.mods_deletable.add(lattice_mod)

        self.lattices.add(lattice_obj)
        self.lattice_deletable.add(lattice_obj)


    def get_lattice(self, obj):
        lattice = None
        for mod in reversed(obj.modifiers):
            if mod.type == 'LATTICE' and mod.object:
                lattice =mod.object
                break
        return lattice

    def set_lattice(self, lattice):

        resolution =(
            lattice.data.points_u,
            lattice.data.points_v,
            lattice.data.points_w
        )

        coords = tuple( tuple(p.co_deform) for p in lattice.data.points)

        interp =(
            lattice.data.interpolation_type_u,
            lattice.data.interpolation_type_v,
            lattice.data.interpolation_type_w
        )

        lattice.data.points_u = 2
        lattice.data.points_v = 2
        lattice.data.points_w = 2

        lattice.data.interpolation_type_u = 'KEY_LINEAR'
        lattice.data.interpolation_type_v = 'KEY_LINEAR'
        lattice.data.interpolation_type_w = 'KEY_LINEAR'

        return (lattice, resolution, coords, interp)

    def taper(self, lattice):
        side_indices = self.sides[self.axis]

        reset = 'XYZ'.index(self.axis[1])

        for index in side_indices:
            point = lattice.data.points[index]
            point.co_deform = point.co*self.taper_factor
            point.co_deform[reset] = point.co[reset]

    def wedge(self, lattice):
        wedge_sides = self.wedge_map[self.axis]

        wedge_axis = 'XYZ'.index(self.axis[1])

        wedge_side_axis = 'XYZ'.index(self.wedge_side_map[self.axis[1] + self.wedge_type])
        wedge_indices = getattr(wedge_sides, self.wedge_type)

        for index in wedge_indices:
            point = lattice.data.points[index]
            co = point.co.copy()
            co[wedge_axis] *= -0.99
            point.co_deform = co

        other = (self.sides[self.axis]).difference(wedge_indices)

        for index in other:
            point = lattice.data.points[index]
            point.co_deform[wedge_axis] = point.co[wedge_axis] + (point.co[wedge_axis] * 2 * self.wedge_len_factor)
            point.co_deform[wedge_side_axis] = point.co[wedge_side_axis] - (point.co[wedge_side_axis] * 2 * self.wedge_side_factor)

    def reset_lattices(self):
        for lattice in self.lattices:
            for p in lattice.data.points:
                p.co_deform = p.co

    def draw_ui(self, context):

        self.master.setup()

        # -- Fast UI -- #
        if self.master.should_build_fast_ui():

            # Main
            win_list = []
            
            if addon.preference().ui.Hops_modal_fast_ui_loc_options != 1:
                win_list.append(self.axis)
                if self.wedge_mode:
                    win_list.append(self.wedge_type)
                    win_list.append("{:.3f}".format(self.wedge_len_factor) )
                    win_list.append("{:.3f}".format(self.wedge_side_factor) )

                else:
                    win_list.append("{:.3f}".format(self.taper_factor))

            else:
                win_list.append("Wedge" if self.wedge_mode else "Taper")
                win_list.append(F"Axis: {self.axis}")
                if self.wedge_mode:
                    win_list.append(F'Type: {self.wedge_type}')
                    win_list.append("Offset: {:.3f}".format(self.wedge_len_factor))
                    win_list.append("Factor: {:.3f}".format(self.wedge_side_factor))
                else:
                    win_list.append("Factor: {:.3f}".format(self.taper_factor))

            # Help
            help_items = {"GLOBAL" : [], "STANDARD" : []}

            help_items["GLOBAL"] = [
                ("M", "Toggle mods list"),
                ("H", "Toggle help"),
                ("~", "Toggle UI Display Type"),
                ("O", "Toggle viewport rendering")]

            help_items["STANDARD"] = [
                ("Z", "Set axis to +Z/-Z"),
                ("Y", "Set axis to +Y/-Y"),
                ("X", "Set axis to +X/-X"),
                ("1", "Set factor to 1 (reset)"),
                ('W', "Toggle Wedge mode"),
                ("LMB  ", "Apply"),
                ("RMB  ", "Cancel"),
                ("Scroll  ", "Cycle Axis")]
                #("Mouse", "Adjust Taper")]

            help_append = help_items["STANDARD"].append

            if self.wedge_mode:
                help_append(['Shift+Scroll ', "Cycle Wedge"])
                help_append(["Ctrl+Mouse ", "Adjust Factor"])
                help_append(["Mouse   ", "Adjust Offset"])

            if not self.wedge_mode:
                help_append(["Mouse   ", "Adjust Taper"])

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
