import bpy, math
from math import degrees
from . import operator
from ... utils.objects import set_active
from ... utility import modifier
from ... utility import addon
from ...ui_framework.operator_ui import Master


class HOPS_BOOL_OPERATOR():
    operator: bpy.props.EnumProperty(name="Select faces:",
                                     items=(# ("KNIFE", "KNIFE", "KNIFE"),
                                            ("INSET", "INSET", "INSET"),
                                            ("SLASH", "SLASH", "SLASH"),
                                            ("INTERSECT", "INTERSECT", "INTERSECT"),
                                            ("UNION", "UNION", "UNION"),
                                            ("DIFFERENCE", "DIFFERENCE", "DIFFERENCE")),
                                     default="DIFFERENCE")

    boolshape: bpy.props.BoolProperty(
        name="Boolshape",
        description='Add boolshape Status',
        default=True)

    sort: bpy.props.BoolProperty(
        name="Sort",
        description="Modifier sorting for this bool operation",
        default=True)

    bstep: bpy.props.BoolProperty(
        name="Up Level",
        description="Add a new bevel modifier after this boolean operation",
        default=False)

    outset: bpy.props.BoolProperty(
        name="Outset",
        description="Set Inset to Outset",
        default=False)

    thickness: bpy.props.FloatProperty(
        name="Thickness",
        description="How deep the inset should cut",
        default=0.50,
        min=0.00,
        soft_max=10.0,
        step=1,
        precision=3)

    keep_bevels: bpy.props.BoolProperty(
        name="Keep Bevels",
        description="Keep Bevel modifiers on inset objects enabled if they don't use vertex groups or bevel weight",
        default=False)

    inset_slice: bpy.props.BoolProperty(
        name="Inset Slice",
        description="Create Slice from inset volume",
        default=False)

    called_ui = False

    def __init__(self):

        HOPS_BOOL_OPERATOR.called_ui = False
        self.inset_slice = False

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.mode == 'OBJECT' and obj.type == 'MESH'

    def operation(self):
        return "DIFFERENCE"

    def draw(self, context):
        self.layout.box().prop(self, "operator", text='')
        self.layout.separator()
        if self.operator == 'INSET':
            row = self.layout.row()
            row.prop(self, "outset")
            row.prop(self, "keep_bevels")
            row.prop(self, "inset_slice")
            self.layout.prop(self, "thickness")
            self.layout.separator()

        row = self.layout.row()
        row.prop(self, "boolshape", text = 'Set Cutter To Boolshape')
        row = self.layout.row()
        row.prop(self, 'sort', text='Sort Modifiers')
        row = self.layout.row()
        #row.prop(self, 'bstep', text='Bevel Step')
        row.prop(addon.preference().property, "parent_boolshapes", text='Parent To Target')
        if bpy.app.version > (2, 83, 0):
            row = self.layout.row()
            row.prop(addon.preference().property, "boolean_solver", text = 'Solver')

    def invoke(self, context, event):
        self.operator = self.operation()
        self.boolshape = not event.shift
        self.sort = not event.ctrl
        self.bstep = event.ctrl and addon.preference().property.bool_bstep
        return self.execute(context)

    def execute(self, context):
        if self.bstep:
            active = context.active_object
            old_objects = set(context.scene.objects)
            bpy.ops.object.shade_smooth()

        if len(context.selected_objects) == 1:
            if all(obj.hops.status == 'BOOLSHAPE'for obj in context.selected_objects):
                operator.shift(context, self.operator, boolshape=self.boolshape, sort=self.sort, outset=self.outset, thickness=self.thickness, keep_bevels=self.keep_bevels, parent=addon.preference().property.parent_boolshapes, inset_slice=self.inset_slice)
                return {'FINISHED'}
            else:
                return {'CANCELLED'}
        elif len(context.selected_objects) <= 1:
            return {'CANCELLED'}

        operator.add(context, self.operator, boolshape=self.boolshape, sort=self.sort, outset=self.outset, thickness=self.thickness, keep_bevels=self.keep_bevels, parent=addon.preference().property.parent_boolshapes, inset_slice=self.inset_slice)

        if self.bstep:
            set_active(active, only_select=True)
            new_objects = set(context.scene.objects)
            objects = new_objects - old_objects
            objects.add(active)

            for obj in objects:
                set_active(obj, select=True)
                bpy.ops.hops.bevel_half_add()
                modifier.user_sort(obj)

            bpy.ops.hops.adjust_bevel('INVOKE_DEFAULT', ignore_ctrl=True)
            return {'CANCELLED'}

        extra_title = ''
        if self.bstep:
            extra_title = ' w/ Bstep'
        elif self.sort != True and self.bstep != True:
            extra_title = ' w/ SortBypass'
        else:
            if bpy.app.version > (2, 83, 0):
                extra_title = f' ('+ addon.preference().property.boolean_solver +')'
            else:
                extra_title = ' '

        # Operator UI
        if not HOPS_BOOL_OPERATOR.called_ui:
            HOPS_BOOL_OPERATOR.called_ui = True

            ui = Master()

            draw_data = [
                [self.operator + extra_title],
                ["Parent Shapes   -   ",  (addon.preference().property.parent_boolshapes)],
                ["Sort Modifiers  -   ",  (self.sort)],
                ["Workflow        -   ",  (addon.preference().property.workflow)],
                ["Boolean Operation complete"]]

            if self.outset:
                draw_data[0][0] = "OUTSET" + extra_title
                draw_data.insert(2, ["Outset          -   ", "ON"])

            if bpy.app.version > (2, 83, 0):
                 draw_data.insert(1, ["2.9X Solver      -   ",  (addon.preference().property.boolean_solver)])

            ui.receive_draw_data(draw_data=draw_data)
            ui.draw(draw_bg=addon.preference().ui.Hops_operator_draw_bg, draw_border=addon.preference().ui.Hops_operator_draw_border)

        return {'FINISHED'}


class HOPS_OT_BoolDifference(HOPS_BOOL_OPERATOR, bpy.types.Operator):
    bl_idname = "hops.bool_difference"
    bl_label = "Hops Difference Boolean"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = """Difference Boolean

Cuts mesh using Difference Boolean

LMB - Boolean Object (DEFAULT)
LMB + Shift - Extract
LMB + CTRL - Bypass Sort / Bstep (Add Bevel)

"""

    def operation(self):
        return "DIFFERENCE"


class HOPS_OT_BoolDifference_hotkey(HOPS_BOOL_OPERATOR, bpy.types.Operator):
    bl_idname = "hops.bool_difference_hotkey"
    bl_label = "Hops Difference Boolean"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = """Cuts mesh using Difference Boolean

LMB - Boolean Object (DEFAULT)
LMB + Shift - Extract
LMB + CTRL - Bypass Sort / Bstep (Add Bevel)

"""

    def invoke(self, context, event):
        self.operator = "DIFFERENCE"
        self.boolshape = True
        return self.execute(context)


class HOPS_OT_BoolUnion(HOPS_BOOL_OPERATOR, bpy.types.Operator):
    bl_idname = "hops.bool_union"
    bl_label = "Hops Union Boolean"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = """Union Boolean

Merges mesh using Union Boolean

LMB - Boolean Object (DEFAULT)
LMB + Shift - Extract
LMB + CTRL - Bypass Sort / Bstep (Add Bevel)

"""

    def operation(self):
        return "UNION"


class HOPS_OT_BoolUnion_hotkey(HOPS_BOOL_OPERATOR, bpy.types.Operator):
    bl_idname = "hops.bool_union_hotkey"
    bl_label = "Hops Union Boolean"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = """Union Boolean

Merges mesh using Union Boolean

LMB - Boolean Object (DEFAULT)
LMB + Shift - Extract
LMB + CTRL - Bypass Sort / Bstep (Add Bevel)

"""

    def invoke(self, context, event):
        self.operator = "UNION"
        self.boolshape = True
        return self.execute(context)


class HOPS_OT_BoolIntersect(HOPS_BOOL_OPERATOR, bpy.types.Operator):
    bl_idname = "hops.bool_intersect"
    bl_label = "Hops Intersect Boolean"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = """Intersect Boolean

Cuts mesh using Intersect Boolean

LMB - Boolean Object (DEFAULT)
LMB + Shift - Extract
LMB + CTRL - Bypass Sort / Bstep (Add Bevel)

"""

    def operation(self):
        return "INTERSECT"


class HOPS_OT_BoolIntersect_hotkey(HOPS_BOOL_OPERATOR, bpy.types.Operator):
    bl_idname = "hops.bool_intersect_hotkey"
    bl_label = "Hops Intersect Boolean"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = """Intersect Boolean

Cuts mesh using Intersect Boolean

LMB - Boolean Object (DEFAULT)
LMB + Shift - Extract
LMB + CTRL - Bypass Sort / Bstep (Add Bevel)

"""

    def invoke(self, context, event):
        self.operator = "INTERSECT"
        self.boolshape = True
        return self.execute(context)


class HOPS_OT_Slash(HOPS_BOOL_OPERATOR, bpy.types.Operator):
    bl_idname = "hops.slash"
    bl_label = "Hops Slash Boolean"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = """Slash Boolean

Splits the primary mesh using the secondary mesh.

LMB - Boolean Object (DEFAULT)
LMB + Shift - Extract
LMB + CTRL - Bypass Sort / Bstep (Add Bevel)

"""

    def operation(self):
        return "SLASH"


class HOPS_OT_Slash_hotkey(HOPS_BOOL_OPERATOR, bpy.types.Operator):
    bl_idname = "hops.slash_hotkey"
    bl_label = "Hops Slash Boolean"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = """Slash Boolean

Splits the primary mesh using the secondary mesh.

LMB - Boolean Object (DEFAULT)
LMB + Shift - Extract
LMB + CTRL - Bypass Sort / Bstep (Add Bevel)

"""

    def invoke(self, context, event):
        self.operator = "SLASH"
        self.boolshape = True
        return self.execute(context)


class HOPS_OT_BoolInset(HOPS_BOOL_OPERATOR, bpy.types.Operator):
    bl_idname = "hops.bool_inset"
    bl_label = "Hops Inset Boolean"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = """Inset/Outset Boolean

Cuts mesh using Inset/Outset Boolean

LMB - Boolean Object (DEFAULT)
LMB + Shift - Outset
LMB + CTRL - Bypass Sort / Bstep (Add Bevel)

"""

    def operation(self):
        return "INSET"

    def invoke(self, context, event):
        self.operator = self.operation()
        self.outset = event.shift and not event.alt
        self.keep_bevels = event.ctrl and not event.alt
        self.sort = not event.ctrl
        return self.execute(context)


class HOPS_OT_BoolKnife(bpy.types.Operator):
    bl_idname = "hops.bool_knife"
    bl_label = "Hops Knife Boolean"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = """Knife Boolean

Cuts mesh using Knife Boolean

LMB - Boolean Knife (DEFAULT)
LMB + Shift - Knife Project

"""

    knife_project: bpy.props.BoolProperty(
        name="Knife Project",
        description="Use knife project instead of boolean intersect",
        default=False)

    cut_through: bpy.props.BoolProperty(
        name="Cut Through",
        description="Use Cut Through Mesh",
        default=True)

    projection: bpy.props.EnumProperty(
        name="Projection",
        description="Object Projection",
        items = [
            ("VIEW", "VIEW", "Project from view"),
            ("Z-", "Z-", "Project for Z- side of the object"),
            ("Z+", "Z+", "Project for Z+ side of the object"),
            ("X-", "X-", "Project for X- side of the object"),
            ("X+", "X+", "Project for X+ side of the object"),
            ("Y-", "Y-", "Project for Y- side of the object"),
            ("Y+", "Y+", "Project for Y+ side of the object"),
        ],
        default = 'VIEW',
    )

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.mode == 'OBJECT' and obj.type == 'MESH'

    def draw(self, context):
        row = self.layout.row()
        row.prop(self, "knife_project")
        if self.knife_project:
            row.prop(self, "cut_through")
            self.layout.row().prop(self, "projection")

    def invoke(self, context, event):
        self.knife_project = event.shift
        return self.execute(context)

    def execute(self, context):
        if self.knife_project:
            bpy.ops.hops.display_notification(info='Knife Project Used', name="Knife Project")
        else:
            bpy.ops.hops.display_notification(info='Knife Intersect Used', name="Knife Intersect")
        return operator.knife(context, self.knife_project, material_cut=True, cut_through=self.cut_through, projection=self.projection)
