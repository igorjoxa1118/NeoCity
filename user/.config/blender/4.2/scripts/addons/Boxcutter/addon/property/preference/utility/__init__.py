from .... property.utility import names


def extra_space_prefix(row):
    sub = row.row()
    sub.alignment = 'LEFT'
    sub.scale_x = 0.64
    sub.label(text='')


def label_split(column, text):
    split = column.row().split(align=True, factor=0.5)
    left = split.row()
    right = split.row()
    right.alignment = 'CENTER'
    right.label(text=text)


def label_row(path, prop, row, label='', toggle=False, header=''):
    if toggle:
        sub = row.row()
        sub.alignment = 'LEFT'

        if header:
            sub.prop(path, prop, text=label if label else names[prop], icon='TRIA_DOWN' if getattr(path, prop) else 'TRIA_RIGHT', emboss=False)
        else:
            sub.active = getattr(path, prop)
            sub.prop(path, prop, text=label if label else names[prop], emboss=False)

        row.prop(path, prop, text=' ', emboss=False)

    else:
        extra_space_prefix(row)
        row.label(text=label if label else names[prop])

    if not header:
        row.prop(path, prop, text='')


def header(preference, layout, prop):
    _header = layout.column(align=True)
    label_row(preference.expand, prop, _header.row(align=True), toggle=True, header=True)
