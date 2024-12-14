import bpy

from bpy.types import Panel
from bpy.props import StringProperty, BoolProperty

from .. toolbar import version
from ... import utility


class BC_PT_error_log(Panel):
    bl_label = 'Error Encountered'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'


    @classmethod
    def poll(cls, context):
        active = utility.tool.active()
        return active and active.idname == utility.tool.name


    def draw(self, context):
        layout = self.layout

        primary = True
        secondary = False

        # UI Width
        units_x = 30
        layout.ui_units_x = units_x

        column = layout.column()
        row = column.row()

        sub = row.row()
        sub.alignment = 'LEFT'
        sub.label(text=utility.name.upper())

        sub = row.row()
        sub.alert = True
        sub.alignment = 'CENTER'
        sub.label(text=F'Error Report')

        sub = row.row()
        sub.enabled = False
        sub.alignment = 'RIGHT'
        sub.label(text=version)

        column.separator()

        row = column.row()
        for error, elem in utility.error_elem.items():
            if primary:
                sub = row.row()
                sub.alignment = 'LEFT'
                sub.label(text='Failure:')
                primary = False

            elif not secondary:
                row = column.row()
                sub = row.row()
                sub.alignment = 'LEFT'
                sub.label(text='Resulting in:')
                secondary = True

            row = column.row()
            for i, e in enumerate(elem['header'].split(':')):
                sub = row.row()
                sub.alignment = 'LEFT' if i == 0 else 'CENTER'
                sub.alert = i == 0
                sub.label(text=F'  {e}{":" if i == 0 else ""}')

            # UI Width
            # _units_x = len(elem['header'] + str(elem['count'])) / 2
            # if _units_x > units_x:
            #     units_x = _units_x

            sub = row.row()
            sub.alignment = 'RIGHT'
            sub.alert = True
            sub.label(text=F'    Count: {elem["count"]}')

            line = elem['body'].split('\n')[-3]
            strip_leading_quote = line.split('"')[1] if line.startswith('"') else line

            path_type = '\\' # could probably use a lib but this is easy enough
            if strip_leading_quote.split(path_type)[0] == strip_leading_quote:
                path_type = '/'

            name_split = strip_leading_quote.split(F'{utility.name}{path_type}')[-1]
            path_split = name_split[:-3].split(path_type)

            row = column.row()
            sub = row.row()
            sub.alignment = 'RIGHT'

            ssub = sub.row()
            ssub.active = False
            ssub.alignment = 'RIGHT'
            ssub.label(text='')
            for i, module in enumerate(path_split):
                # if not module:
                #     continue

                arrow = u'   \N{RIGHTWARDS ARROW}'
                if i + 1 == len(path_split):
                    arrow = ''

                if i:
                    module = module.split('"')[0]

                if module.endswith('.py'):
                    module = module[:-3]

                ssub.label(text=F'{module}{arrow}')

            ulambda = u'\N{GREEK SMALL LETTER LAMDA}'
            split = line.split(',')[-1][1:]

            if 'in ' not in split:
                continue

            sub.label(text=F'{ulambda}   {split.split("in ")[1]}')

            ssub = sub.row()
            ssub.alignment = 'RIGHT'
            ssub.alert = True
            ssub.label(text=line.split(',')[1][1:])

        column.separator()

        row = column.row()
        row.enabled = False
        row.label(text=F'    Blender:  {bpy.app.version_string}')
